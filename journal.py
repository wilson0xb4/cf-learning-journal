# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
import os
import datetime

from cryptacular.bcrypt import BCRYPTPasswordManager
from markdown import markdown
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
    HTTPForbidden
)
from pyramid.response import Response
from pyramid.security import remember, forget
from pyramid.view import (
    view_config,
    notfound_view_config,
    forbidden_view_config
)
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import scoped_session, sessionmaker
from waitress import serve
from zope.sqlalchemy import ZopeTransactionExtension


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

# make a module-level constant for the connection URI
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://ajw@localhost:5432/learning-journal')

HERE = os.path.dirname(os.path.abspath(__file__))


class Entry(Base):
    __tablename__ = 'entries'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    title = sa.Column(sa.Unicode(127), nullable=False)
    text = sa.Column(sa.UnicodeText, nullable=False)
    created = sa.Column(
        sa.DateTime, nullable=False, default=datetime.datetime.utcnow
    )

    @classmethod
    def write(cls, title=None, text=None, session=None):
        if session is None:
            session = DBSession
        instance = cls(title=title, text=text)
        session.add(instance)
        return instance

    @classmethod
    def update_entry(cls, entry_id, title, text, session=None):
        if session is None:
            session = DBSession
        row = session.query(cls).get(entry_id)

        row.title = title
        row.text = text
        # breaks it? TODO: eventually figure out how to update the date
        # row.created = datetime.datetime.utcnow

    @classmethod
    def all(cls, session=None):
        if session is None:
            session = DBSession
        return session.query(cls).order_by(cls.created.desc()).all()

    @classmethod
    def get_entry(cls, entry_id, session=None):
        """get single entry"""
        if session is None:
            session = DBSession
        return session.query(cls).get(entry_id)

    @classmethod
    def make_md(cls, text):
        return markdown(
            text,
            output_format='html5',
            extensions=['codehilite', 'fenced_code']
        )


def init_db():
    engine = sa.create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)


@view_config(route_name='home', renderer='templates/list.jinja2')
def list_view(request):
    entries = Entry.all()
    return {'entries': entries, 'current': 'list'}


@view_config(route_name='entry', renderer='templates/entry.jinja2')
def entry_view(request):

    entry_id = request.matchdict['entry_id']
    data = Entry.get_entry(entry_id)

    if data is None:
        raise HTTPNotFound

    return {'data': data}


@view_config(route_name='add', renderer='templates/entry_form.jinja2')
def add_entry(request):

    if not request.authenticated_userid:
        raise HTTPForbidden

    if request.method == 'POST':
        title = request.params.get('title')
        text = request.params.get('text')
        Entry.write(title=title, text=text)
        return HTTPFound(request.route_url('home'))

    return {'data': {}, 'current': 'add'}


@view_config(
    route_name='update',
    renderer='templates/entry_form.jinja2')
def update_entry(request):

    if not request.authenticated_userid:
        raise HTTPForbidden

    entry_id = request.matchdict['entry_id']
    data = Entry.get_entry(entry_id)

    if data is None:
        raise HTTPNotFound

    if request.method == 'POST':
        entry_id = request.params.get('entry_id')
        title = request.params.get('title', 'not provided?')
        text = request.params.get('text', 'not provided?')
        Entry.update_entry(entry_id=entry_id, title=title, text=text)
        return HTTPFound(request.route_url('home'))

    return {'data': data, 'current': 'update'}


@notfound_view_config(renderer='templates/404.jinja2')
def notfound(request):
    """custom 404 view"""
    request.response.status = 404
    return {}


@forbidden_view_config(renderer='templates/login.jinja2')
def forbidden(request):
    """custom 401 view"""
    request.response.status = 401
    error = '401 Unauthorized'
    return {'error': error}


@view_config(context=DBAPIError)
def db_exception(context, request):
    response = Response(context.message)
    response.status_int = 500
    return response


@view_config(route_name='login', renderer="templates/login.jinja2")
def login(request):
    """authenticate a user by username/password"""
    username = request.params.get('username', '')
    error = ''

    if request.method == 'POST':
        error = "Login Failed"
        authenticated = False
        try:
            authenticated = do_login(request)
        except ValueError as e:
            error = str(e)

        if authenticated:
            headers = remember(request, username)
            return HTTPFound(request.route_url('home'), headers=headers)

    return {'error': error, 'username': username, 'current': 'login'}


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(request.route_url('home'), headers=headers)


def do_login(request):
    username = request.params.get('username', None)
    password = request.params.get('password', None)
    if not (username and password):
        raise ValueError('both username and password are required')

    settings = request.registry.settings

    manager = BCRYPTPasswordManager()
    if username == settings.get('auth.username', ''):
        hashed = settings.get('auth.password', '')
        return manager.check(hashed, password)
    return False


def main():
    """Create a configured wsgi app"""
    settings = {}
    debug = os.environ.get('DEBUG', True)
    settings['reload_all'] = debug
    settings['debug_all'] = debug

    settings['auth.username'] = os.environ.get('AUTH_USERNAME', 'admin')
    manager = BCRYPTPasswordManager()
    settings['auth.password'] = os.environ.get(
        'AUTH_PASSWORD', manager.encode('secret')
    )

    if not os.environ.get('TESTING', False):
        # only bind the session if we are not testing
        engine = sa.create_engine(DATABASE_URL)
        DBSession.configure(bind=engine)

    auth_secret = os.environ.get('JOURNAL_AUTH_SECRET', 'itsaseekrit')

    # configuration setup
    config = Configurator(
        settings=settings,
        authentication_policy=AuthTktAuthenticationPolicy(
            secret=auth_secret,
            hashalg='sha512'
        ),
        authorization_policy=ACLAuthorizationPolicy()
    )
    config.include('pyramid_tm')
    config.include('pyramid_jinja2')
    config.add_static_view('static', os.path.join(HERE, 'static'))
    config.add_route('home', '/')
    config.add_route('entry', '/entry/{entry_id}')

    # routes to process add / update
    config.add_route('add', '/add')
    config.add_route('update', '/update/{entry_id}')

    config.add_route('login', '/login')
    config.add_route('logout', '/logout')

    config.scan()
    app = config.make_wsgi_app()
    return app


if __name__ == '__main__':
    app = main()
    port = os.environ.get('PORT', 5000)
    serve(app, host='0.0.0.0', port=port)
