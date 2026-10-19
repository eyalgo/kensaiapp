# Change request — 2026-10-19_allowed-moves

---

**Request:** Let the operator move a task through its status workflow from any list row or from the task's own page. Add `products/tracker17/domain/workflow.py` as the one home of the status workflow (SRS FR-18, FR-19): the allowed moves from each status (`todo`→`in-progress`, `todo`→`cancelled`, `in-progress`→`done`, `in-progress`→`cancelled`, `in-progress`→`todo`; `done` and `cancelled` offer none) and, for any other move, a refusal with its reason, a move to the status the task already has included. Every list row and the task's page then offer the allowed moves other than `cancelled` as buttons named by the status they lead to. A press saves the move and leaves the operator at the moved task's row (or at the task's moves on its page), with the new status shown and one line naming what changed (SDD § 4 EX-5, EX-7). A task moved to `done` is no longer marked overdue (AC-13's third case), also for the overdue filter and the summary count where those exist at this point.

Tests: a unit test per allowed move and per refused move (every other from/to pair among the four statuses, the same-status move for each status included), each asserting the refusal reason or the saved result; an integration test that a row and the task's page offer the right buttons per status (`todo`: `in-progress`; `in-progress`: `done` and `todo`; `done` and `cancelled`: none; no `cancelled` button anywhere) and that a press saves the move, shows the new status and one line naming what changed; a test, with today's date set by the test, that a task due yesterday and moved to `done` is not marked overdue on its row. `pytest products/tracker17/tests/` must exit 0 from the repository root.

What must not be weakened: the workflow rule is written once, in `domain/workflow.py`, and no page, route or test restates the table. No `cancelled` button appears on any page and no confirmation is built here, because a move to `cancelled` must never save unconfirmed (EX-6) and no page shows a control before its slice (EX-12); the workflow rule itself keeps every move. No out-of-date-move handling and no change to `tests/timed_run.py`. The saved data format must not change except for the status. Files other than `domain/workflow.py`, the pages and routes that offer the moves, and their tests stay as they are.

**Sizing:** one honest merge. The acceptance boundary is the operator moving a task along the allowed status moves (FR-18, FR-19, EX-5, EX-7, AC-13's third case), from the open station `2026-10-19_allowed-moves`. The rule, the buttons that offer it and the overdue effect only mean something together, so they stay in one change; the `cancelled` button, the stale-page refusal and the timed run are separate capabilities that the later stations of seed `2026-10-07_status-moves` own (`cancel-confirmation`, `out-of-date-move`, `move-timed-run`).
**Category:** feature
**Behaviour:** changing
**Classified because:** the station adds a new operator behaviour — moving a task between statuses by buttons on rows and pages, with refusals — and a new public module `domain/workflow.py`, which adds to the FDR-level contract.

**Sealed:** 2026-10-19 — accepted; merged to `main` via `--no-ff`.
Environment: owners-mac — no CI
