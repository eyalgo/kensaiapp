# 宿場 Shukuba — a move from a stale page, and a move reached by an address, are refused as facts

*Item 3 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-07_status-moves`. Slug: `out-of-date-move`.*

## What it is

Two refusals of one move, both on the move refusal page. (1) A press made from a page whose task has since changed is refused: the page says the status has changed, names the moves the page now shows, or none for a final status, and offers no reload; it lands on a page built after the refusal (UXD UX-I3, UX-F4). (2) A refusal reached by an address with no press states its reason as a fact about the task and what its status allows, names the move the address asks for, and gives no action and no reload (CONTENT RN-26, UX-I3). Its words today are "the move you pressed" (`products/tracker17/web/pages.py:760`), which claims a press the tracker did not establish. One station because both are the same refusal page and the same words. Nothing about saved data may change: SRS AC-12.

## Reached when

1. A move pressed from a page whose task has since moved to another status saves nothing, and the page it lands on says the status has changed and names the moves that page now shows, or none when the status is `done` or `cancelled`, and offers no reload (integration tests over a task changed between the page and the press, one per final and one per non-final status).
2. A move refusal reached by an address with no press states the task's status as a fact, names the move the address asks for, and offers no action and no reload; `grep -rn "the move you pressed" products/tracker17/web` prints nothing (today it prints `web/pages.py:760`) (integration tests for each of the four statuses).
3. For each of the two refusals, the saved data is byte-identical before and after (AC-12), checked by a test that compares it.
4. `pytest products/tracker17/tests/integration/` exits 0 and `pytest products/tracker17/tests/` exits 0 from the repository root; the assertions in `tests/integration/test_move_routes.py` and `tests/e2e/test_moves.py` that quote "the move you pressed" are changed to the new words, not removed.

## Guardrail

- The workflow rule stays written once, in `domain/workflow.py`; no page, route or test restates the table.
- The history mechanism the previous unit settled (`web/routes.py` response status and cache headers) and the confirmation are left as they are; no page script (ADR-0003).
- No change to `tests/timed_run.py`, and no change to the saved data format.
- Every other refusal's words stay as they are; the words of this one come from CONTENT RN-26 and the change's text, not from this station.
- **Not here:** `tracker17 · nemawashi · 2026-10-07_status-moves` item 4 (`move-timed-run`) owns the timed run; SDD § 6 S-4 already offers no reload (SDD version 11), so no SDD wording is owed here.
