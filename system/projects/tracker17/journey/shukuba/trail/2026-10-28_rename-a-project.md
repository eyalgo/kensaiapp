# 宿場 Shukuba — a project can be renamed from its Tasks view

*Item 2 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-11_delete-and-rename`. Slug: `rename-a-project`.*

## What it is

Below a project's list, a Rename field holds the project's current name; Save renames the project and the operator sees the new name on the project's page (UXD UX-F10; SDD § 6 S-7). A blank name, or one another project already uses, is refused under UX-I3 and nothing changes; saving the project's own current name is not refused (FDR, FR-12). Renaming leaves the project's tasks, and their identities, unchanged (SRS FR-12). The timed run gains a project rename (NFDR QC-48). Delete project is the next station; this one is one operation and one merge.

## Reached when

1. In the running app, on a project's Tasks view, below the list, a Rename field holds the project's current name; saving a new name shows that name as the project's page title and in the Projects list, and the old name is in neither.
2. Saving a blank name, or a name another project uses, is refused with the UX-I3 refusal and the saved data is unchanged; saving the project's own current name is accepted.
3. After a rename, the project's tasks are the same tasks with the same identities, fields and comments as before (FR-12).
4. `pytest products/tracker17/tests/` exits 0, including a test that a rename leaves the project's tasks unchanged (FR-12) and a layer-3 test per refusal of item 2 asserting unchanged saved data.
5. `python3 products/tracker17/tests/timed_run.py` exits 0 and its listed actions include a project rename (QC-48).

## Guardrail

- Reuse the existing refusal path and naming rules of project creation (FR-10); no second validation scheme or refusal wording scheme.
- Delete project and the `domain/projects.py` / `domain/tasks.py` docstring bar stay with the later station; existing pages and timed actions keep working.
- A project's description is not changed here (UXD § 10), and no task moves between projects (SRS FR-14).

- **Not here:** deleting a project, `tracker17 · nemawashi · 2026-10-11_delete-and-rename` item 3; deleting a task, item 1, already walked.
