# 宿場 Shukuba — a project's task list narrows by filter

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-11_narrow-and-sort`. Slug: `project-list-filter`.*

## What it is

The project's task list gains filter controls: status, priority, assignee, label, due-date range and overdue. Apply shows only the matches with their count and the choices still shown; the choices live in the address; Clear returns to every task. The rules sit in `domain/filtering.py` (SDD § 4 TS-3). A reversed date range is refused with FR-34's reason, a filter matching nothing says so and shows Clear, and a task moved out of a status the list is filtered by leaves the list while the completion line names it. `tests/timed_run.py` times a filter. One capability, one merge; sort and All tasks are the next two stations.

## Reached when

1. `domain/filtering.py` exists: `ls products/tracker17/domain/filtering.py` (reports it missing before this station).
2. In a browser or through `web`, on a project's list: Apply with each of status, priority, assignee, label, due-date range and overdue shows only matching tasks (AND across fields, FR-32 to FR-35) with the count of matches and the choices still shown; the choices appear in the address, so a reload shows the same list; Clear shows every task again.
3. A from-date later than the to-date is refused with FR-34's reason and the saved data is unchanged; a filter matching nothing says so and shows Clear.
4. A task moved out of a status the list is filtered by leaves the list, and the completion line names it (UX-F4).
5. `pytest products/tracker17/tests/` exits 0, including SRS AC-14's filter tests (each field, the AND combination, both range ends), AC-12's reversed-range test, and a test that the overdue filter agrees with the list marking on AC-13's three cases.
6. `python3 products/tracker17/tests/timed_run.py` exits 0 and its output shows a timed filter under `LIMIT_SECONDS`.

## Guardrail

- Filtering only: no sorting, no All tasks list or header link, no summary; the list's order stays as it is today.
- The limit and every existing timed action stay as they are; the run only gains the filter.
- Accepts one value per filter field (the PRD puts more out of scope).

- **Not here:** `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` items 2 and 3 (`project-list-sort`, `all-tasks-list`); the project summary and its links into a filtered list, `tracker17 · nemawashi · 2026-10-11_project-summary`.
