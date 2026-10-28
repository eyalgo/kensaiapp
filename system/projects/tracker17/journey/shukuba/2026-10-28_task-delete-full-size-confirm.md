# 宿場 Shukuba — Delete task's confirmation takes the full-size first press's height

*Item 5 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-11_delete-and-rename`. Slug: `task-delete-full-size-confirm`.*

## What it is

DESIGN.md `components.confirm-strip` says the sentence and the confirming button take the height of the button the strip replaces: `spacing.row-control` for a status move, `spacing.control` for a full-size secondary button, which Delete task's first press is. Today the task strip is built with `size=TRIGGER_SIZE` (`row-control`) in `_delete_strip` (`products/tracker17/web/pages.py`), so its confirming button is 28px (`.strip-row-control button.button-confirm`, `products/tracker17/web/style.css`) against the 36px first press it replaces. This station makes Delete task's strip take the full-size (`spacing.control`) sizing Delete project's strip already uses (`size=FULL_SIZE`), leaving status-move strips at `row-control`. One capability, one merge. The existing assertion in `tests/e2e/test_delete_project.py` that Delete task's confirming button is `ROW_CONTROL_HEIGHT` is made false by this change and is corrected here.

## Reached when

1. In the running app, at `/tasks/<id>?delete_confirm`, the confirming button measures `spacing.control` (36px, ±0.5) tall, equal to Delete task's first press at `/tasks/<id>`, and the sentence is at least that tall. The status-move confirmation at `/projects/<id>?move_task=<id>&move_confirm=cancelled` still measures `spacing.row-control` (28px, ±0.5).
2. An end-to-end test in `products/tracker17/tests/e2e/` measures Delete task's confirming button against Delete task's first press (bounding boxes, same invocation as the neighbouring tests) and fails on `main` today, where the button is 28px and the first press 36px.
3. `git grep -n 'ROW_CONTROL_HEIGHT' -- products/tracker17/tests/e2e/test_delete_project.py` shows no assertion on the `/tasks/1?delete_confirm` confirming button (`task_confirm`); the status-move assertion remains.
4. Delete task otherwise behaves as walked: the existing Delete task tests pass unchanged apart from item 3.
5. `pytest products/tracker17/tests/` exits 0, and `pytest products/tracker17/tests/e2e/` exits 0 (the card's `Test command:` skips `tests/e2e/`, so it is run on its own).

## Guardrail

- Status-move confirmations keep `spacing.row-control`; the back-out control stays full-size everywhere (RN-25).
- No change to the wording of any page, to focus behaviour, to the order of the strip's parts, or to Delete project's strip.
- Task deletion itself (what is saved, redirects, failure line) stays as walked.
- No moving of tasks between projects (SRS FR-14) and no change of a project's description (UXD § 10).

- **Not here:** deleting a task, renaming a project, deleting a project and the deleted-project redirect, `tracker17 · nemawashi · 2026-10-11_delete-and-rename` items 1 to 4, already walked.
