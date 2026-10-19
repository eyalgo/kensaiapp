# 宿場 Shukuba — a task's allowed moves, pressed from a row or its page

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-07_status-moves`. Slug: `allowed-moves`.*

## What it is

Adds `products/tracker17/domain/workflow.py`, the one home of the status workflow (SRS FR-18, FR-19): the allowed moves from each status and the refusal, with its reason, for any other move, a move to the status the task already has included. Every list row and the task's page then offer the allowed moves other than `cancelled` as buttons named by the status they lead to. A press saves the move and leaves the operator at the moved task's row (or at the task's moves on the task's page) with the new status shown and one line naming what changed (SDD § 4 EX-5, EX-7). A task moved to `done` is no longer marked overdue (AC-13's third case). The `cancelled` button waits for `cancel-confirmation`, because a move to `cancelled` must never save unconfirmed (EX-6) and no page shows a control before its slice (EX-12); the workflow rule itself keeps every move. It is one station because it is the first where a task can reach `done`, and the rule, its pages and the overdue effect only mean something together.

## Reached when

All of these hold, each checkable by a fresh session:

1. `products/tracker17/domain/workflow.py` exists (absent today: `ls products/tracker17/domain` lists no `workflow.py`).
2. A unit test per allowed move (`todo`→`in-progress`, `todo`→`cancelled`, `in-progress`→`done`, `in-progress`→`cancelled`, `in-progress`→`todo`) and per refused move (every other from/to pair among the four statuses, `done` and `cancelled` offering none), the same-status move for each status included, each asserting the refusal reason or the saved result.
3. An integration test shows that a row and the task's page for a task in `todo` offer buttons named `in-progress` and no `cancelled` button; in `in-progress`, buttons named `done` and `todo` and no `cancelled` button; in `done` and `cancelled`, none. A test shows that a press saves the move, shows the new status and one line naming what changed.
4. A test with today's date set by the test shows a task due yesterday, moved to `done`, is not marked overdue on its row, and agrees with AC-13's third case for the overdue filter and the summary count where those exist at this point.
5. `pytest products/tracker17/tests/` exits 0 from the repository root.

## Guardrail

- The workflow rule is written once, in `domain/workflow.py`; no page, route or test restates the table.
- No `cancelled` button appears on any page, and no confirmation is built here; a move to `cancelled` is not reachable from the pages.
- No out-of-date-move handling and no `tests/timed_run.py` change; the saved data format is unchanged except for the status.
- Files other than `domain/workflow.py`, the pages and routes that offer the moves, and their tests stay as they are.
- **Not here:** `tracker17 · nemawashi · 2026-10-07_status-moves` items 2 to 4 (`cancel-confirmation`, `out-of-date-move`, `move-timed-run`) own the confirmation, the stale-page refusal and the timed run; the confirmations on deleting are `tracker17 · nemawashi · 2026-10-11_delete-and-rename`; a moved task leaving a status-filtered list is `tracker17 · nemawashi · 2026-10-11_narrow-and-sort`.
