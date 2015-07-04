Feature: Add
    Add an entry to the database


Scenario: Anon user tries to add an entry
    Given an anonymous user
    When the user visits the add page
    Then they are redirected to the login screen with a 401 Unauthorized

Scenario: Authorized user tries to add an entry
    Given an authorized user
    When the user visits the add page
    Then they are shown the add form
