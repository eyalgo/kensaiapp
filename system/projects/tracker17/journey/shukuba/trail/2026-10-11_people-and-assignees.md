# 宿場 Shukuba — People in the header: the assignee list, added to and removed from

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`. Slug: `people-and-assignees`.*

## What it is

The first leg of the seed: the operator keeps the list of names tasks can be assigned to. The header gains People (SDD § 4 EX-12). The People page shows the assignee list (SRS DR-4: unique names, compared exactly, in the order added) with an Add form and a Remove beside each name, and nothing yet about the operator's name. Add refuses a blank name and a repeated name where it was entered. Remove needs no confirmation, and its completion line says the name stays on the tasks that carry it (SRS FR-20, FR-22; UXD UX-F8, UX-S8). After an add the page opens with keyboard focus on the added name and the completion line as its accessible description (SDD § 4 EX-5, EX-14, RT-9). This is the seed's first focus test on an element that is not a control (SDD § 11 R-2), so it comes first. The rules live in `domain/assignees.py`; the web and application parts call them (SDD § 4 TS-3).

## Reached when

1. `ls products/tracker17/domain/assignees.py` finds the file (it does not exist before this station).
2. Run through the real server by an integration test, the header of every page that carries it has a People link, and `GET` of its address shows the assignee list with an Add form and a Remove beside each name. The page says nothing of the operator's name.
3. Adding a name puts it at the end of the list; adding a blank name, and adding a name already on the list (compared exactly), are each refused on the People page with the typed text kept and the saved data unchanged (SRS FR-20; UXD UX-I3).
4. Removing a name removes it from the list without a confirmation step; its completion line says the name stays on the tasks that carry it (SRS FR-22).
5. An end-to-end test under `products/tracker17/tests/e2e/` adds a name in a real browser and asserts that the page opens with keyboard focus on the added name and the completion line as that element's accessible description.
6. `pytest products/tracker17/tests/` (unit, integration and architecture layers) and `pytest products/tracker17/tests/e2e/` (the end-to-end layer, which the collection rule keeps out of the first run, `products/tracker17/tests/conftest.py:L7-L9`) each exit 0, and `python3 products/tracker17/tests/timed_run.py` still exits 0.

## Guardrail

- The station adds no task, priority, due date or label, and `domain/tasks.py`, `domain/priorities.py`, `domain/due_dates.py` and `domain/labels.py` are not created here.
- The saved form of a task is not changed; the assignee list is stored as the SDD's DR-4 already states, and no state migration is written.
- People carries no Your name field and no comment.
- Every test and page that passed before still passes; no existing test is weakened to fit.
- **Not here:** adding and listing tasks (`tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`, item 2, `add-and-list-tasks`); changing a task's assignee and the left-the-list rules of SDD § 4 RT-7 (item 3, `edit-task-fields`); the operator's name and comments (`tracker17 · nemawashi · 2026-10-07_comment-on-a-task`).

*Amended 2026-10-11 by shukuba-refine after `people-page-assignee-list`: reached-when 6 named one `pytest products/tracker17/tests/` run with the end-to-end layer collected; the collection rule keeps that layer out, so it now names the two runs the product uses.*
