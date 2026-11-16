Feature: The server way in sends a request to a server

  This scenario proves that the server way in works.
  It tests nothing of a product.

  Scenario: A request sent through the server way in gives back the server's response
    Given a local server that serves a page headed "Served by the scenario"
    When the page is requested through the server way in
    Then the response status is 200
    And the response holds the heading "Served by the scenario"
