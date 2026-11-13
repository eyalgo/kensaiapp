# QA record — 2026-11-13_summary-shows-due-today

Change: 2026-11-13_summary-shows-due-today

Way in: browser

Base commit: <a commit not in the public history>

Red commit: 8b0c83732af75312a6ebcf0be25e83b8e8c291d7

Scenario: features/summary_due_on_date.feature:9 — new or changed — CP-808 — failed

Scenario: features/summary_due_on_date.feature:25 — new or changed — CP-810 — failed

Scenario: features/summary_due_on_date.feature:37 — new or changed — CP-811 — failed

Scenario: features/summary_due_on_date.feature:52 — new or changed — CP-812 — failed

Scenario: features/summary_due_on_date.feature:62 — new or changed — CP-813 — failed

Scenario: features/summary_due_on_date.feature:73 — kept — CP-814 — passed

Review notes: (1) CP-809's half about a date that changes while the Summary is produced is not shown: the browser way in cannot set the tracker's clock, so the scenarios show only that the label's date is the date the counts were worked out on (scenarios 2 and 3), and CP-815's tests, with a clock handed in, carry the midnight case. (2) CP-815 to CP-822 are sorted untouched: they state the Developer's tests, the trace, the gates, the timed run and a grep, none of which a person sees through the browser. (3) Scenario 1 adds the exclusions CP-808 names and its example rows leave out: a task due tomorrow, one due yesterday, one with no due date, one in done, and another project's open task due on the date. (4) CP-812's kept half is folded into scenario 4 as the count of the Summary's count links, nine, and scenario 6 checks one of them, Overdue, by name and address; the other eight links' names and addresses are not re-checked here. (5) CP-811's "no Due today or Today text" is checked as the whole word "today", in any case, anywhere on the page; it already holds before the change, so scenario 3 fails before the change on the row order alone. (6) Every date is the machine's local date when the scenario starts; a run that crosses local midnight between adding the tasks and opening the Summary would fail, a limit of driving the real clock, not a fault of the product. (7) The scenarios start the real tracker with its own start command, from a copy of its directory with no saved data, so a run never touches saved data; the tracker's fixed address, 127.0.0.1:8017, must be free while they run. The browser way in gained a page kept open across steps, beside the starter's one-heading read, which is unchanged in what it does. No rule needed a question for the Product Owner.
