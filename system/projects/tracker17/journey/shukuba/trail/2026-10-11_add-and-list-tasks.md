# 宿場 Shukuba — The project page adds a task and lists its tasks, overdue marked

*Item 2 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`. Slug: `add-and-list-tasks`.*

## What it is

The second leg of the seed: a project holds tasks. The project's page gains the add-task form (title, priority with `medium` chosen, an assignee offered from the People list or none, an optional due date picked from a date picker), and its no-tasks state now invites a first task. Adding lands on the new task's own page, which here only shows the task; changing it is the next station. The project's list shows one row per task with its title, status, priority, assignee or "unassigned", labels and due date, in due-date order, earliest first and undated last, with the word "Overdue" beside the due date of an open task due before today (SRS FR-15, FR-24 to FR-26; SDD § 6 S-2; UXD UX-F3, UX-F5, UX-S4, UX-A4). A blank title is refused where it was entered. A task is saved in the form every later slice acts on, so this is the station that fixes it. The rules live in `domain/tasks.py`, `domain/priorities.py` and `domain/due_dates.py`; the web and application parts call them (SDD § 4 TS-3).

## Reached when

1. `ls products/tracker17/domain/tasks.py products/tracker17/domain/priorities.py products/tracker17/domain/due_dates.py` finds all three (none exists before this station).
2. Run through the real server by an integration test, the project page shows the add-task form with `medium` chosen and the assignee control offering the names on the People list plus none; a project with no tasks shows the invitation to add a first task.
3. Adding a task with a title, a priority, an assignee and a due date redirects to that task's page, which shows each of the four; adding with only a title saves it as `medium`, unassigned, undated, status `todo`.
4. Adding a task with a blank title is refused on the project page with the typed text kept and the saved data unchanged (SRS FR-15; UXD UX-I3).
5. The project's list shows one row per task with title, status, priority, assignee or "unassigned", labels and due date; a project holding tasks due in a later month, an earlier day, and none lists them earliest first with the undated last.
6. With today's date set by the test, an open task due yesterday shows "Overdue" beside its due date and a task due today does not (SRS AC-13, first two cases, for the list marking).
7. `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/` each exit 0, and `python3 products/tracker17/tests/timed_run.py` exits 0 with 1,000 tasks loaded and adding a task among the actions it times (NFDR QC-48; SDD § 4 TS-5). Run on a `git archive HEAD` copy that is `git init`-ed, since the repository-ignore test needs a git repo.
8. An end-to-end test enters `<`, `&` and `"` in a new task's title and finds the task's page and the project's list showing them as typed (NFDR QC-36; SDD § 11 R-3).

## Guardrail

- The station adds no label module: `domain/labels.py` is not created and no label can be added or removed. The list's labels column shows what a task carries, which is none yet.
- A task page here shows the task and changes nothing; the edit form, the left-the-list assignee rules of SDD § 4 RT-7 and AC-19 stay with the next station.
- No status move, delete, filter, sort control or summary is added; no comment is added.
- The saved form of the People list is not changed, and no existing test is weakened to fit.
- **Not here:** changing a task's fields and its assignee rules (`tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`, item 3, `edit-task-fields`); labels (item 4, `task-labels`); status moves (`tracker17 · nemawashi · 2026-10-07_status-moves`); comments (`tracker17 · nemawashi · 2026-10-07_comment-on-a-task`).

*2026-10-11, shukuba-refine: reached-when 7 re-aimed and 8 added — the timed-run and title-escaping obligations of NFDR QC-48 and QC-36 land with this station, not a later one.*
