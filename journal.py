# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import datetime

from pyramid.config import Configurator
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import remember, forget
from waitress import serve
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import scoped_session, sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension
from cryptacular.bcrypt import BCRYPTPasswordManager

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
        row.created = datetime.datetime.utcnow
        session.commit(row)
        # return instance

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
    return {'data': data, 'current': 'entry'}


@view_config(route_name='entry_form', renderer='templates/entry_form.jinja2')
@view_config(
    route_name='entry_form:entry_id',
    renderer='templates/entry_form.jinja2')
def entry_form_view(request):

    try:
        entry_id = request.matchdict['entry_id']
        data = Entry.get_entry(entry_id)
    except:
        data = {}

    return {'data': data, 'current': 'add'}


@view_config(route_name='add', request_method='POST')
def add_entry(request):
    title = request.params.get('title')
    text = request.params.get('text')
    Entry.write(title=title, text=text)
    return HTTPFound(request.route_url('home'))


@view_config(route_name='update', request_method='POST')
def update_entry(request):
    entry_id = request.params.get('entry_id')
    title = request.params.get('title')
    text = request.params.get('text')
    Entry.update(id=entry_id, title=title, text=text)
    return HTTPFound(request.route_url('home'))


@view_config(context=DBAPIError)
def db_exception(context, request):
    from pyramid.response import Response
    response = Response(context.message)
    response.status_int = 500
    return response


@view_config(route_name='login', renderer="templates/login.jinja2")
@view_config(route_name='login:page', renderer="templates/login.jinja2")
def login(request):
    """authenticate a user by username/password"""
    username = request.params.get('username', '')
    error = ''

    try:
        next_page = request.matchdict['page']
    except:
        next_page = request.params.get('next_page', 'home')

    if request.method == 'POST':
        error = "Login Failed"
        authenticated = False
        try:
            authenticated = do_login(request)
        except ValueError as e:
            error = str(e)

        if authenticated:
            headers = remember(request, username)
            return HTTPFound(request.route_url(next_page), headers=headers)

    return {'error': error, 'username': username, 'next_page': next_page, 'current': 'login'}


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

    # routes for viewing the form
    config.add_route('entry_form', '/entry_form')
    config.add_route('entry_form:entry_id', '/entry_form/{entry_id}')

    # routes to process add / update
    config.add_route('add', '/add')
    config.add_route('update', '/update')

    config.add_route('login', '/login')
    config.add_route('login:page', '/login/{page}')
    config.add_route('logout', '/logout')
    config.scan()
    app = config.make_wsgi_app()
    return app


if __name__ == '__main__':
    app = main()
    port = os.environ.get('PORT', 5000)
    serve(app, host='0.0.0.0', port=port)
