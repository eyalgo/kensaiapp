# Change request — 2026-10-21_out-of-date-move

---

**Request:** Fix how the tracker refuses a move in two cases, both on the move refusal page. (1) When someone presses a move from a page whose task has since changed status, nothing is saved, and the page they land on says the status has changed, names the moves that page now shows (or none when the status is done or cancelled), and offers no reload; it is built after the refusal. (2) When the refusal is reached by an address with no press, it states the task's status as a fact about what that status allows, names the move the address asks for, and gives no action and no reload. Today's words, "the move you pressed" (`web/pages.py:760`), claim a press the tracker never saw, so they go, and the tests that quote them (`tests/integration/test_move_routes.py`, `tests/e2e/test_moves.py`) are changed to the new words rather than removed. The words come from CONTENT RN-26 and UX-I3/UX-F4. Saved data must be byte-identical before and after each refusal (AC-12), checked by a test that compares it. Both refusals are one capability: the same refusal page and the same words, so they are one merge. The workflow rule must stay written once in `domain/workflow.py`; the history mechanism and confirmation from the earlier units, `tests/timed_run.py`, the saved data format and every other refusal's words must not change, and no page script is added (ADR-0003). Done when `pytest products/tracker17/tests/integration/` and `pytest products/tracker17/tests/` both exit 0 from the repository root, and `grep -rn "the move you pressed" products/tracker17/web` prints nothing.
**Category:** feature
**Behaviour:** changing
**Classified because:** the station's reached-when 1 and 2 change what the move refusal page says and add a new status-changed refusal, which alters the product's observable contract (UXD UX-I3, UX-F4; CONTENT RN-26), so Behaviour is changing and Category is feature.

**Sealed:** 2026-10-21 — accepted; merged to `main` via `--no-ff`.
Environment: owners-mac — no CI
