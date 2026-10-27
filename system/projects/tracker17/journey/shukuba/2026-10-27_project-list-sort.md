# 宿場 Shukuba — a project's task list sorts by one field

*Item 2 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-11_narrow-and-sort`. Slug: `project-list-sort`.*

## What it is

The project's task list gains a sort field (due date, priority, created time, title) and a direction (ascending or descending, ascending when none is chosen) beside the filter controls. Apply shows the matches sorted, with their count and the choices still shown; the choices live in the address with the filter's; Clear returns to every task in due-date ascending order. The rules sit in `domain/sorting.py` (SDD § 4 TS-3): priority ascending runs `low`, `medium`, `high`, `critical` (R-90); undated tasks come last in a due-date sort in either direction (R-91); title ignores letter case (R-92); tasks equal on the field keep creation order, and a created-time sort follows it (R-93). `tests/timed_run.py` times a sort. One capability, one merge, riding the filter's Apply, Clear and address; All tasks is the next station.

## Reached when

1. `domain/sorting.py` exists: `ls products/tracker17/domain/sorting.py` (reports it missing before this station).
2. In a browser or through `web`, on a project's list: Apply with each sort field in each direction shows the tasks in the order FR-36 defines (priority `low`, `medium`, `high`, `critical` ascending and the reverse descending; undated tasks last by due date in both directions; title alphabetical ignoring case), with the match count and the choice still shown; no direction chosen sorts ascending.
3. The sort choice appears in the address together with any filter, so a reload shows the same list; a sort applied over a filter keeps the filter's matches; Clear shows every task in due-date ascending order.
4. Tasks equal on the chosen field, and tasks with the same recorded creation time, come out in the same order on every request.
5. `pytest products/tracker17/tests/` exits 0, including SRS AC-14's sort tests (each field in both directions, the priority order, undated last, the tie and created-time cases).
6. `python3 products/tracker17/tests/timed_run.py` exits 0 and its output shows a timed sort under `LIMIT_SECONDS`, beside the existing `filter total at 1000 tasks` line.

## Guardrail

- Sorting only: no All tasks list or header link, no summary; the filter's rules and behaviour stay as they are.
- The limit and every existing timed action stay as they are; the run only gains the sort.
- Sorts by one field only (the PRD puts more out of scope); the choice is carried in the address and not remembered between sittings (UX-I7).

- **Not here:** `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` item 3 (`all-tasks-list`); the project summary and its links into a filtered list, `tracker17 · nemawashi · 2026-10-11_project-summary`.
