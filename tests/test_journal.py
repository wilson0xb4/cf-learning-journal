# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
import os
import pytest
from sqlalchemy.exc import IntegrityError
from pyramid import testing
from cryptacular.bcrypt import BCRYPTPasswordManager

import journal

os.environ['TESTING'] = "True"


@pytest.fixture()
def entry(db_session):
    entry = journal.Entry.write(
        title='Test Title',
        text='Test Entry Text',
        session=db_session
    )
    db_session.flush()
    return entry


@pytest.fixture(scope='function')
def auth_req(request):
    manager = BCRYPTPasswordManager()
    settings = {
        'auth.username': 'admin',
        'auth.password': manager.encode('secret')
    }
    testing.setUp(settings=settings)
    req = testing.DummyRequest()

    def cleanup():
        testing.tearDown()

    request.addfinalizer(cleanup)

    return req


def test_write_entry(db_session):
    kwargs = {'title': "Test Title", 'text': "Test entry text"}
    kwargs['session'] = db_session

    # first, assert that there are no entries in the database:
    assert db_session.query(journal.Entry).count() == 0

    # second, create and entry using the 'write' class method
    entry = journal.Entry.write(**kwargs)

    # the entry we get back ought to be an instance of Entry
    assert isinstance(entry, journal.Entry)

    # id and created are generated automatically, but only on writing
    # to the database
    auto_fields = ['id', 'created']
    for field in auto_fields:
        assert getattr(entry, field, None) is None

    # flush the session to "write" the data to the database
    db_session.flush()

    # we should have one entry:
    assert db_session.query(journal.Entry).count() == 1
    for field in kwargs:
        if field != 'session':
            assert getattr(entry, field, '') == kwargs[field]

    # id and created should be set automatically upon writing to db:
    for auto in ['id', 'created']:
        assert getattr(entry, auto, None) is not None


def test_entry_no_title_fails(db_session):
    bad_data = {'text': 'test text'}
    journal.Entry.write(session=db_session, **bad_data)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_entry_no_text_fails(db_session):
    bad_data = {'title': 'test title'}
    journal.Entry.write(session=db_session, **bad_data)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_read_entries_none(db_session):
    entries = journal.Entry.all()
    assert len(entries) == 0


def test_read_entries_one(db_session):
    title_template = "Title {}"
    text_template = "Entry Text {}"

    # write three entries, with order clear in the title and text
    for x in range(3):
        journal.Entry.write(
            title=title_template.format(x),
            text=text_template.format(x),
            session=db_session
        )
        db_session.flush()
    entries = journal.Entry.all()
    assert len(entries) == 3
    assert entries[0].title > entries[1].title > entries[2].title
    for entry in entries:
        assert isinstance(entry, journal.Entry)


def test_empty_listing(app):
    response = app.get('/')
    assert response.status_code == 200
    actual = response.body
    expected = 'No entries here so far'
    assert expected in actual


def test_listing(app, entry):
    response = app.get('/')
    assert response.status_code == 200
    actual = response.body
    for field in ['title', 'text']:
        expected = getattr(entry, field, 'absent')
        assert expected in actual


def test_post_to_add_view_no_auth(app):
    """Try to add a post without being authenticated."""
    test_start_as_anonymous(app)
    entry_data = {
        'title': 'Hello there',
        'text': 'This is a post'
    }
    response = app.post('/add', params=entry_data, status='3*')
    assert response.status_code == 302
    redirected = response.follow()
    actual = redirected.body
    assert '<h2>Login</h2>' in actual
    for expected in entry_data.values():
        assert expected not in actual


def test_post_to_add_view(app):
    test_login_success(app)
    entry_data = {
        'title': 'Hello there',
        'text': 'This is a post'
    }
    response = app.post('/add', params=entry_data, status='3*')
    redirected = response.follow()
    actual = redirected.body
    for expected in entry_data.values():
        assert expected in actual


def test_add_no_params(app):
    test_login_success(app)
    response = app.post('/add', status=500)
    assert 'IntegrityError' in response.body


def test_do_login_success(auth_req):
    from journal import do_login
    auth_req.params = {'username': 'admin', 'password': 'secret'}
    assert do_login(auth_req)


def test_do_login_bad_pass(auth_req):
    from journal import do_login
    auth_req.params = {'username': 'admin', 'password': 'wrong'}
    assert not do_login(auth_req)


def test_do_login_bad_user(auth_req):
    from journal import do_login
    auth_req.params = {'username': 'bad', 'password': 'secret'}
    assert not do_login(auth_req)


def test_do_login_missing_params(auth_req):
    from journal import do_login
    for params in ({'username': 'admin'}, {'password': 'secret'}):
        auth_req.params = params
        with pytest.raises(ValueError):
            do_login(auth_req)


INPUT_BTN = 'log out</a></li>'


def login_helper(username, password, app):
    """encapsulate app login for reuse in test

    Accept all status codes so that we can make assertions in tests
    """
    login_data = {'username': username, 'password': password}
    return app.post('/login', params=login_data, status='*')


def test_start_as_anonymous(app):
    response = app.get('/', status=200)
    actual = response.body
    assert INPUT_BTN not in actual


def test_login_success(app):
    username, password = ('admin', 'secret')
    redirect = login_helper(username, password, app)
    assert redirect.status_code == 302
    response = redirect.follow()
    assert response.status_code == 200
    actual = response.body
    print(actual)
    assert INPUT_BTN in actual


def test_login_fails(app):
    username, password = ('admin', 'wrong')
    response = login_helper(username, password, app)
    assert response.status_code == 200
    actual = response.body
    assert "Login Failed" in actual
    assert INPUT_BTN not in actual


def test_logout(app):
    test_login_success(app)
    redirect = app.get('/logout', status="3*")
    response = redirect.follow()
    assert response.status_code == 200
    actual = response.body
    assert INPUT_BTN not in actual


def test_view_entry_valid(app, entry):
    """View entry that exists."""
    response = app.get('/entry/' + unicode(entry.id), status=200)
    assert response.status_code == 200
    actual = response.body
    expected = 'Test Title'
    assert expected in actual


def test_view_entry_invalid(app):
    """View entry that does not exist."""
    response = app.get('/entry/999', status=404)
    assert response.status_code == 404
    actual = response.body
    expected = 'Test Title'
    assert expected not in actual


def test_view_update_form_valid(app, entry):
    """Check if the update form is correctly populated with the entry"""
    test_login_success(app)
    response = app.get('/update/' + unicode(entry.id))
    assert response.status_code == 200
    actual = response.body
    expected = '<input type="text" id="title" name="title" value="Test Title">'
    assert expected in actual


def test_view_update_invalid_entry(app):
    """Try to update an entry that doesn't exist."""
    test_login_success(app)
    response = app.get('/update/999', status=404)
    assert response.status_code == 404
    actual = response.body
    expected = '<input type="text" id="title" name="title" value="Test Title">'
    assert expected not in actual


def test_make_md():
    """simple test of make_md, just checking for <li> elements"""
    submitted_text = '* one\r* two\r* three'
    md_text = journal.Entry.make_md(submitted_text)
    expected_md = '<ul>\n<li>one</li>\n<li>two</li>\n<li>three</li>\n</ul>'
    assert expected_md == md_text


def test_get_entry(db_session, entry):
    """test return of getting a single entry by its id"""
    entry = journal.Entry.get_entry(entry.id, session=db_session)
    assert entry.title == 'Test Title'
    assert entry.text == 'Test Entry Text'
