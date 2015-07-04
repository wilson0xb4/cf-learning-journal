Feature: Edit
    Edit an entry


Scenario: Anon user tries to edit an entry
    Given an anonymous user
    And the user has an entry
    When the user visits the update page
    Then they are redirected to the login screen with a 401 Unauthorized

Scenario: Authorized user tries to edit an entry
    Given an authorized user
    And the user has an entry
    When the user visits the update page
    Then they are shown the update form
