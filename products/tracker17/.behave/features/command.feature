Feature: The command way in runs a program

  This scenario proves that the command way in works.
  It tests nothing of a product.

  Scenario: A program run through the command way in gives back its exit status and output
    Given a program that prints "ready" and exits with status 0
    When the program is run through the command way in
    Then the exit status is 0
    And the output is "ready"
