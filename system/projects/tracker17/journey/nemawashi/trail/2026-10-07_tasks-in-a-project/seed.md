# 根回し Nemawashi seed — tasks in a project

## What it is

Serves the Way `fit-to-publish`: the reader of tracker17 meets its task rules here (`products/tracker17/README.md:L3-L5`). After this, the operator can keep the list of people tasks are assigned to, add tasks to a project with a priority, a due date and an assignee, see them in the project's list with overdue tasks marked, and open a task to change its fields and its labels. Moves the Agari toward **Works** for the first half of Key Use Case 3 and toward **Simple to read** for Tasks, Priorities, Assignees, Labels and Due dates, whose entry points (`domain/<feature word>.py`, SDD § 4 TS-3) this slice adds.

Rests on SDD §§ 3 and 4. Its bar is SDD § 6 S-2 *Reached when*: People with Add and Remove; the add-task form; the project's list in due-date order with "Overdue"; the task page changing title, priority, assignee, due date and labels; an assignee who left the list kept as the current choice until replaced (§ 4 RT-7); refusals where entered; both suites pass, including SRS AC-19 and AC-13's first two cases; `python3 tests/timed_run.py` exits 0 with 1,000 tasks.

**Why it is early.** Every later slice except `protect-saved-data` acts on a task (§ 6 S-2, *Why here in the order*), and it fixes the saved form of a task. Its People focus test was the first on an element that is not a control, a case § 11 R-2 no longer counts as unverified (RN-41).

## Source

Cut from `products/tracker17/docs/SDD.md` § 6 S-2, slug `tasks-in-a-project` ("After this, the operator can keep the list of people tasks can be assigned to, add tasks to a project"). Product re-checked on 2026-10-11, after `add-and-list-tasks` landed: `ls products/tracker17/domain` lists `assignees.py`, `tasks.py`, `priorities.py` and `due_dates.py` among its files, and `labels.py` is still missing. The edit form and labels are still owed.

## Stations — dynamic checklist

- [x] people-and-assignees — People in the header lists names with Add and Remove, refusing a blank or repeated name; after an add the page opens focused on the name (e2e test); `domain/assignees.py` exists
- [x] add-and-list-tasks — the project page adds a task (title, priority, assignee, due date) and lands on its page; the list is in due-date order with "Overdue" (SRS AC-13 first two cases); `domain/tasks.py`, `priorities.py`, `due_dates.py` exist; the end-to-end test enters `<`, `&` and `"` in the title and sees them shown as typed (NFDR QC-36); `tests/timed_run.py` loads 1,000 tasks and times adding one (QC-48, SDD § 4 TS-5)
- [x] edit-task-fields — the task page changes title, priority, assignee and due date; a left-the-list assignee stays as the current choice until replaced, and a change to a name that left after the page loaded is refused as out of date (§ 4 RT-7 tests); a plain field edit from a page loaded before another tab saved replaces that value (SRS AC-19); the timed run times a field edit (QC-48); the task page shows its project as text (UXD UX-S6)
- [x] task-labels — the task page adds and removes one label at a time, focus on the added label (e2e test); `domain/labels.py` exists; saved data breaking a label rule is reported as unreadable at start (SDD § 5 SD-5); the end-to-end test enters `<`, `&` and `"` in a label and sees it shown as typed (NFDR QC-36); `tests/timed_run.py` times adding a label at 1,000 tasks (QC-48)

Re-cut from the proposal's four: `edit-a-task` split into `edit-task-fields` and `task-labels` — fields and labels are separate Core Features with their own acceptance and focus test, and bundled they made one merge too large. The two focus tests moved onto the stations that add the name and the label, so each reached-when is met where it stands and the non-control focus risk (§ 11 R-2) surfaces at the first station. `timed-run` reworded: `tests/timed_run.py` already exists from `first-project`, so the station extends it to 1,000 tasks rather than writing it. Reached-whens made checkable; the order stands on real dependencies (the add form offers the list; edit and labels need a task).

2026-10-11, shukuba-refine after `people-page-assignee-list`: SRS AC-19 moved from `add-and-list-tasks` to `edit-task-fields` — AC-19 is a stale plain field edit (`products/tracker17/docs/SRS.md:L532-L534`), and no field edit exists until `edit-task-fields` builds the task page's edit, so the earlier bar could not be met where it stood.

2026-10-11, shukuba-refine after halted `add-and-list-tasks`: `timed-run` removed and its work moved onto the stations that add each action, with QC-36's title test on `add-and-list-tasks`. NFDR QC-48 and SDD § 4 TS-5 have each change that adds a listed action add it to the timed run, and QC-36 has each change test the text fields it adds (`products/tracker17/docs/nfdr.md:L270-L275,L396-L403`; `products/tracker17/docs/SDD.md:L461-L464`). A trailing station left both owed past the station that lands them, and the unit's design halted on it (`fc2f59593`).

2026-10-11, shukuba-refine after sealed `add-and-list-tasks`: `edit-task-fields` gains the task's project as text, and `task-labels` gains SD-5's start check for a saved label. The unit's spec handed both on: the project as text to no station, and the label check to `task-labels`. UXD UX-S6 lists the project on the task page (`products/tracker17/docs/UXD.md:L312`), and `web/pages.py:L470-L493` does not show it. SD-5 has each slice that adds a data rule test it at start (`products/tracker17/docs/SDD.md:L392-L395`).

2026-10-12, shukuba-refine after sealed `edit-task-fields`: `task-labels` gains QC-36's typed-text test for a label and QC-48's timing of a label add. A label is free text stored as typed (`products/tracker17/docs/SRS.md:L189-L191`), and QC-36 has each change test the text fields it adds (`products/tracker17/docs/nfdr.md:L270-L276`). Labels are an edited field (SRS FR-16, `SRS.md:L153-L155`), editing is an NFR-1 action, and QC-48 has the change that adds one time it (`nfdr.md:L396-L398`). Left off, the station's design meets the same gap that halted `add-and-list-tasks` (`fc2f59593`). Prose: § 11 R-2's focus case follows SDD v8 (`SDD.md:L774-L777`), and the three slices once "not yet cut" are named by their seeds in `unpicked/`.

## Relation to existing work

Rests on `tracker17 · nemawashi · 2026-10-07_first-project`. `tracker17 · nemawashi · 2026-10-07_comment-on-a-task` and `tracker17 · nemawashi · 2026-10-07_status-moves` rest on it. `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` and `tracker17 · nemawashi · 2026-10-11_delete-and-rename` rest on it too.

## Out (later / elsewhere)

Moving a task's status (`tracker17 · nemawashi · 2026-10-07_status-moves`). Deleting a task (`tracker17 · nemawashi · 2026-10-11_delete-and-rename`). The filter and sort controls and the list across all projects (`tracker17 · nemawashi · 2026-10-11_narrow-and-sort`). The Summary view (`tracker17 · nemawashi · 2026-10-11_project-summary`). Comments and the Your name half of People (`tracker17 · nemawashi · 2026-10-07_comment-on-a-task`).
