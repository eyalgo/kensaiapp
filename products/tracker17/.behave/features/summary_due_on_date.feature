Feature: A project's Summary counts the open tasks due on its date

  The Summary's "Due dates" group shows how many of the project's open tasks are due on the
  date its counts are worked out against: the machine's local date at the moment the Summary
  is shown. In these scenarios, {today} stands for that date, {yesterday} for the day before
  it and {tomorrow} for the day after it, each written YYYY-MM-DD. A due of "none" is a task
  with no due date. Every task is added and moved through the tracker's own pages.

  Scenario: The due-on-date count holds only this project's open tasks due on the date
    Given the tracker is running on no saved data
    And the project "Alpha" holds these tasks:
      | title           | due         | status      |
      | due-todo        | {today}     | todo        |
      | due-in-progress | {today}     | in-progress |
      | due-done        | {today}     | done        |
      | due-later       | {tomorrow}  | todo        |
      | due-before      | {yesterday} | todo        |
      | undated         | none        | todo        |
    And the project "Beta" holds these tasks:
      | title     | due     | status |
      | elsewhere | {today} | todo   |
    When the Summary of the project "Alpha" is opened
    Then the row "Due on {today}" shows 2

  Scenario: An open task due on the date is counted as due and not as overdue
    Given the tracker is running on no saved data
    And the project "Alpha" holds these tasks:
      | title    | due         | status      |
      | open     | {today}     | todo        |
      | dropped  | {today}     | cancelled   |
      | finished | {today}     | done        |
      | late     | {yesterday} | in-progress |
    When the Summary of the project "Alpha" is opened
    Then the row "Due on {today}" shows 1
    And the row "Overdue" shows 1

  Scenario: The Due dates group shows Overdue, then Due on the date, then No due date
    Given the tracker is running on no saved data
    And the project "Alpha" holds these tasks:
      | title   | due         | status |
      | open    | {today}     | todo   |
      | late    | {yesterday} | todo   |
      | undated | none        | todo   |
    When the Summary of the project "Alpha" is opened
    Then the "Due dates" group shows these rows, in this order:
      | label          | count |
      | Overdue        | 1     |
      | Due on {today} | 1     |
      | No due date    | 1     |
    And no text on the page reads "Due today" or "Today"

  Scenario: The due-on-date count is a plain number, and the Summary keeps its nine count links
    Given the tracker is running on no saved data
    And the project "Alpha" holds these tasks:
      | title | due         | status |
      | open  | {today}     | todo   |
      | late  | {yesterday} | todo   |
    When the Summary of the project "Alpha" is opened
    Then the row "Due on {today}" shows 1 as plain text, with no link and no name of its own
    And the page's counts carry exactly 9 links

  Scenario: A project with no tasks shows a due-on-date count of 0
    Given the tracker is running on no saved data
    And the project "Empty" is created
    When the Summary of the project "Empty" is opened
    Then the "Due dates" group shows these rows, in this order:
      | label          | count |
      | Overdue        | 0     |
      | Due on {today} | 0     |
      | No due date    | 0     |
    And the page shows "This project has no tasks yet. Open Tasks to add the first task."

  Scenario: Overdue keeps its meaning, its link and its first place, and No due date stays plain
    Given the tracker is running on no saved data
    And the project "Alpha" holds these tasks:
      | title    | due         | status |
      | late     | {yesterday} | todo   |
      | open     | {today}     | todo   |
      | finished | {yesterday} | done   |
      | undated  | none        | todo   |
    When the Summary of the project "Alpha" is opened
    Then the first row of the "Due dates" group is "Overdue"
    And the row "Overdue" shows 1 as a link named "1 overdue task" to the project's overdue tasks
    And the row "No due date" shows 1 as plain text, with no link and no name of its own
