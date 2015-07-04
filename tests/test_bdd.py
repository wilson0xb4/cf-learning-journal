# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pytest_bdd import scenario, given, when, then
import journal


@scenario(
    'features/homepage.feature',
    'The Homepage lists entries for anonymous users'
)
def test_home_listing_as_anon():
    pass


@given('an anonymous user')
def an_anonymous_user(app):
    pass


@given("a list of three entries")
def create_entries(db_session):
    title_template = "Title {}"
    text_template = "Entry Text {}"
    for x in range(3):
        journal.Entry.write(
            title=title_template.format(x),
            text=text_template.format(x),
            session=db_session
        )
        db_session.flush()


@when('the user visits the homepage')
def go_to_homepage(homepage):
    pass


@then('they see a list of 3 entries')
def check_entry_list(homepage):
    html = homepage.html
    entries = html.find_all('article', class_='entry')
    assert len(entries) == 3


@scenario('features/add.feature', 'Anon user tries to add an entry')
def test_add_as_anon():
    pass


@when('the user visits the add page')
def go_to_add_page(add_page):
    pass


@then('they are redirected to the login screen with a 401 Unauthorized')
def redirect_to_login(add_page):
    # response = app.post('/add', status='401 Unauthorized')
    assert add_page.status_code == 401
    actual = add_page.body
    assert '<h2>Login</h2>' in actual


@scenario('features/add.feature', 'Authorized user tries to add an entry')
def test_add_as_authorized():
    pass


@given('an authorized user')
def an_authorized_user():
    pass


@given('the user has an entry')
def user_has_entry():
    pass


@then('they are shown the add form')
def see_add_form():
    pass


@scenario('features/edit.feature', 'Anon user tries to edit an entry')
def test_edit_as_anon():
    pass


@when('the user visits the update page')
def visit_update_page():
    pass


@scenario('features/edit.feature', 'Authorized user tries to edit an entry')
def test_test_edit_as_authorized():
    pass


@then('they are shown the update form')
def show_update_form():
    pass
