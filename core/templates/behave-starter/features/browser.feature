Feature: The browser way in opens a page

  This scenario proves that the browser way in works.
  It tests nothing of a product.

  Scenario: A page opened through the browser way in shows what the server sent
    Given a local server that serves a page headed "Served by the scenario"
    When the page is opened through the browser way in
    Then the browser shows the heading "Served by the scenario"
