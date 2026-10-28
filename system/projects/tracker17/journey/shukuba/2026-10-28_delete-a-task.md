# 宿場 Shukuba — a task can be deleted from its page, behind the in-place confirmation

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-11_delete-and-rename`. Slug: `delete-a-task`.*

## What it is

Delete task on a task's page opens the in-place confirmation (the `confirm_strip` built for `status-moves`), and confirming removes the task together with its comments, then lands on the task's project with a line naming the deleted task (SDD § 6 S-7; UXD UX-F9, UX-S6). The deleted task's address shows the not-found page (UX-S10), and an action sent from another tab for it is refused and changes nothing (AC-12). Its identity is never issued again (FR-15). The timed run gains a task delete (NFDR QC-48). Rename and delete of a project are the next two stations; this one is one operation and one merge.

## Reached when

1. In the running app, on a task's page, Delete task shows the in-place confirmation; confirming lands on the task's project with a line naming the deleted task, and that task is in no list of the project or of all projects.
2. The deleted task's address shows the not-found page, and a comment-add, edit or status move sent for it from another tab is refused with the saved data unchanged.
3. After deleting the task with the highest identity, a task added next receives a new identity that is not the deleted one (FR-15), and the deleted task's comments are gone from the saved data (FR-17).
4. `pytest products/tracker17/tests/` exits 0, including a layer-3 test per deleted-target refusal of AC-12 for a task, each asserting unchanged saved data, and a test that the identity is not reissued.
5. `python3 products/tracker17/tests/timed_run.py` exits 0 and its listed actions include a task delete (QC-48).

## Guardrail

- Reuse `confirm_strip` and the existing refusal path; no second confirmation mechanism and no new refusal wording scheme.
- Rename and delete of a project, and the `domain/projects.py` / `domain/tasks.py` docstring bar, stay with the later stations; existing pages and timed actions keep working.
- Moving a task to another project stays out (SRS FR-14).

- **Not here:** renaming a project, `tracker17 · nemawashi · 2026-10-11_delete-and-rename` item 2; deleting a project, item 3 of the same seed.
