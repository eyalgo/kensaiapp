# 宿場 Shukuba — The task page adds and removes a task's labels

*Item 4 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`. Slug: `task-labels`.*

## What it is

The last leg of the seed: a task can carry labels. The task page gains a label area: each label shows with a Remove button and a text field with Add puts on one more, one at a time (SRS FR-23, UXD UX-F9). A label is free text, must not be empty, is stored exactly as typed and compared exactly, and takes at most 200 characters (FR-23, FR-40); adding one the task already carries leaves the task unchanged. A task with no labels says so, with Add in view (UXD UX-S6). The label rules live in a new `domain/labels.py`, and the label add and remove in the domain and application parts, not the web part (SDD § 4 TS-3). The saved data already holds each task's labels, so this leg adds the rule and the check that the data keeps it: saved data breaking a label rule is reported as unreadable at start (SDD § 4 SD-5; SRS DR-6). It also owes the two checks the pipeline puts on every change that adds a typed-text field and a listed action: QC-36's typed-text test and QC-48's timing at 1,000 tasks.

## Reached when

1. `products/tracker17/domain/labels.py` exists.
2. Run through the real server by an integration test, the task page shows the task's labels each with a Remove control and a text field with Add; a task with none shows a sentence saying so, with Add in view.
3. Adding a label redirects to the task's page, which shows it; adding one the task already carries leaves the task as saved; removing a label leaves the others; the task list row shows the labels held.
4. An empty label, and a label over 200 characters, are each refused on the task page where it was entered, with the saved data unchanged; the empty refusal keeps the typed text, and the over-long one gives the reason and not the typed text (FDR PD-11).
5. A test writes saved data in which a task carries an empty label, one over 200 characters and a repeated label, one case at a time, and the tracker's start reports each as unreadable and loads none of the data (SDD § 4 SD-5, SRS DR-6).
6. An end-to-end test adds a label, and after the add the page has focus on the added label (SDD § 11 R-2, `SDD.md:L755`).
7. An end-to-end test enters a label holding `<`, `&` and `"` and finds the task's page and the project's list showing it as typed (NFDR QC-36).
8. `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/` each exit 0, and `python3 products/tracker17/tests/timed_run.py` exits 0 with 1,000 tasks loaded and adding a label among the actions it times (NFDR QC-48). Run on a `git archive HEAD` copy that is `git init`-ed, since the repository-ignore test needs a git repo.

2026-10-12, shukuba-refine after sealed `task-labels`: item 4 no longer asks the over-long refusal to keep the typed text. FDR PD-11 says that refusal gives "the reason and not the typed text" (`products/tracker17/docs/fdr.md:L388-L389`), so the old bar could not be met.

## Guardrail

- No status move, delete, filter or sort control, summary or comment is added; the label filter belongs to the filter's station.
- The saved form of a task and of the People list is not changed (the `labels` list already saved stays as it is), and no existing test is weakened to fit.
- No edit-form field changes: the edit form of title, priority, assignee and due date stays as `edit-task-fields` left it.
- **Not here:** the filter that narrows by label (`tracker17 · nemawashi · 2026-10-11_narrow-and-sort`); status moves (`tracker17 · nemawashi · 2026-10-07_status-moves`); comments and their saved-comment start check (`tracker17 · nemawashi · 2026-10-07_comment-on-a-task`); making the browser suite pass on every run (no seed yet carries it).
