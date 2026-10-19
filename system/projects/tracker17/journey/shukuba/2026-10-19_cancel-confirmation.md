# 宿場 Shukuba — the `cancelled` button and its in-place confirmation

*Item 2 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-07_status-moves`. Slug: `cancel-confirmation`.*

## What it is

Adds the `cancelled` button to every list row and the task's page, wherever the workflow rule allows that move, and the in-place confirmation a first press opens (SDD § 4 EX-6, UXD UX-I2): in view, with its sentence, its confirming control and its back-out control in that order, and focus where UX-I2 places it. Confirming saves the move; backing out restores the button and returns focus to it. A first press for a move the task no longer allows opens no confirmation. It also removes the pages' own withholding of `cancelled` (`products/tracker17/web/pages.py`, `_WITHHELD_MOVES` and its filter in `_move_forms`), so the moves a page offers come from `domain/workflow.py` alone (SDD § 3 `web`). It runs the browser tests the previous station landed unrun (`tests/e2e/test_moves.py`) and adds the focus and double-press tests. One station because the button, its confirmation and its focus rules mean nothing apart, and the confirmation is what lets the withholding go.

## Reached when

All of these hold, each checkable by a fresh session:

1. A task in `todo` or `in-progress` offers a button named `cancelled` on its list row and on its page; a task in `done` or `cancelled` offers none (integration test over the rendered pages).
2. `_WITHHELD_MOVES` is gone: `grep -n "_WITHHELD_MOVES" products/tracker17/web/pages.py` prints nothing (today it prints the definition and its use), and a test shows the moves a page offers equal the workflow rule's allowed moves for each status.
3. A first press on `cancelled` saves nothing and shows the confirmation (sentence, then confirming control, then back-out control); the confirming control saves the move to `cancelled` and shows the new status with one line naming what changed; a first press for a move the task no longer allows opens no confirmation and saves nothing (integration tests).
4. End-to-end tests in `products/tracker17/tests/e2e/` show: focus lands where UX-I2 places it when the confirmation opens; backing out restores the button and returns focus to it; a double press on the first button of a row far down a list scrolled part-way never confirms.
5. `pytest products/tracker17/tests/e2e/` (the whole folder, including `test_moves.py`) exits 0 on a machine where layer 5 runs (NFDR § 9: macOS, or the Debian/Ubuntu releases SDD § 4 RT-4 lists, with the browser libraries installed). On a machine where it does not run, that folder is a missing prerequisite and this item is checked on one that does.
6. `pytest products/tracker17/tests/` exits 0 from the repository root.

## Guardrail

- The workflow rule stays written once, in `domain/workflow.py`; no page, route or test restates the table.
- No out-of-date-move handling and no `tests/timed_run.py` change; the saved data format is unchanged except for the status.
- No confirmation on deleting a task or project; the confirmation built here must be reusable by that work but is not extended to it.
- Files other than the pages and routes that offer or confirm moves, `domain/workflow.py` if a gap shows, and their tests stay as they are.
- **Not here:** `tracker17 · nemawashi · 2026-10-07_status-moves` items 3 and 4 (`out-of-date-move`, `move-timed-run`) own the stale-page refusal and the timed run; deleting confirmations are `tracker17 · nemawashi · 2026-10-11_delete-and-rename`.
