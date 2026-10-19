# 宿場 Shukuba — The task page changes a task's fields, and shows its project

*Item 3 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`. Slug: `edit-task-fields`.*

## What it is

The third leg of the seed: a task can be changed. The task page, which today only shows the task, gains the edit form for title, priority, assignee and due date, and shows the task's project as text (UXD UX-S6). A save writes only the fields the operator changed, a field counting as changed when its submitted value differs from the value the page showed; the form carries the values the page showed, because the tracker keeps nothing between requests (SDD § 4 RT-7). So an assignee whose name has left the People list stays as the control's current choice, with UX-F9's sentence beside it, until the operator replaces it; a change to a name that left the list after the page loaded is refused as out of date (UXD UX-I3); and a plain field edit from a page loaded before another tab saved a different value replaces that value (SRS AC-19). Fields and labels are separate stations; this one adds no label. The edit and its rules live in the domain and application parts, not the web part (SDD § 4 TS-3).

## Reached when

1. Run through the real server by an integration test, the task page shows the edit form holding the task's title, priority, assignee (or none) and due date as saved, and shows the task's project's name as text.
2. Saving the form with a changed title, priority, assignee and due date redirects to the task's page, which shows each new value; a save changing one field leaves the other three as saved.
3. A blank title is refused on the task page where it was entered, with the typed text kept and the saved data unchanged.
4. A task whose assignee has left the People list shows that name as the assignee control's current choice with the sentence saying it is no longer on the list; a save that leaves the control as shown keeps the name (SDD § 4 RT-7 test).
5. An assignee changed to a name that left the list after the page was loaded is refused as out of date, saying so, with the saved data unchanged (SDD § 4 RT-7 test).
6. A test loads the edit form, saves a different title through a second submission, then submits the first form with a changed title: the first submission's title is saved and not refused (SRS AC-19).
7. `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/` each exit 0, and `python3 products/tracker17/tests/timed_run.py` exits 0 with 1,000 tasks loaded and a field edit among the actions it times (NFDR QC-48). Run on a `git archive HEAD` copy that is `git init`-ed, since the repository-ignore test needs a git repo.
8. An end-to-end test edits a task's title to one holding `<`, `&` and `"` and finds the task's page and the project's list showing it as typed (NFDR QC-36).

## Guardrail

- No label module: `domain/labels.py` is not created and no label is added or removed; the label check on saved data stays with the next station.
- No status move, delete, filter, sort control, summary or comment is added.
- The saved form of a task and of the People list is not changed, and no existing test is weakened to fit.
- **Not here:** labels and the start check for a saved label (`tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`, item 4, `task-labels`); status moves (`tracker17 · nemawashi · 2026-10-07_status-moves`); comments (`tracker17 · nemawashi · 2026-10-07_comment-on-a-task`).
