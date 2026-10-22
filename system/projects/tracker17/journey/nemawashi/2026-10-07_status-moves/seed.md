# 根回し Nemawashi seed — moving a task through its workflow

## What it is

Serves the Way `fit-to-publish`: the Status workflow is a Core Feature a reader traces to its code (`products/tracker17/README.md:L3-L5`). After this, the operator can move a task through its status workflow from any list row or from the task's page, and a move the workflow does not allow is refused with its reason. Completes Key Use Case 3 toward the Agari's **Works** bar, and adds the Status workflow's entry point (`domain/workflow.py`) toward **Simple to read**.

Rests on SDD § 4 EX-5, EX-6 and EX-7. Its bar is SDD § 6 S-4 *Reached when*: exactly the allowed moves offered as buttons; a move to `cancelled` behind the in-place confirmation, with focus where UX-I2 puts it and a double press that never confirms, also on a scrolled list; an out-of-date move refused; a test for every allowed and refused move, SRS AC-12's out-of-date move and AC-13's third case; the end-to-end focus tests; `tests/timed_run.py` covers a move.

**Why it is here.** It is the first use of the in-place confirmation, which is the interaction most exposed to pages that run no script (§ 9 TO-2, ADR-0003). A failure found here costs the pages of one action, and `delete-and-rename` reuses what is built (SDD § 7, `hands_off_to`).

## Source

Cut from `products/tracker17/docs/SDD.md` § 6 S-4, slug `status-moves` ("After this, the operator can move a task through its status workflow from any list row or from the task's page"). Product re-checked on 2026-10-12, after `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project` was walked: `domain/workflow.py` does not exist (`ls products/tracker17/domain` lists `__init__.py assignees.py due_dates.py labels.py priorities.py projects.py refusals.py state.py tasks.py text.py`). The work is still owed.

## Stations — dynamic checklist

- [x] allowed-moves — `domain/workflow.py` exists and each row and the task page offer, as buttons named by the status they lead to, the allowed moves other than `cancelled`; a press saves the move, shows the new status and one line naming what changed, and a task moved to `done` is no longer marked overdue (AC-13's third case); a test for every allowed move and every refused move, the same-status move too (FR-18); `pytest products/tracker17/tests/` exits 0
- [x] cancel-confirmation — a `cancelled` button on a row and the task page whose first press opens the in-place confirmation in view, sentence then confirm then back-out, focus where UX-I2 puts it; backing out returns focus to the restored button; a first press for a move the task no longer allows opens none; `web/pages.py` withholds no allowed move, so the moves a page offers come from the workflow rule alone (SDD § 3 `web`); end-to-end tests show the focus, and that a double press on the first button never confirms on a list scrolled part-way; `pytest products/tracker17/tests/e2e/`, the whole folder with `tests/e2e/test_moves.py`, exits 0 where layer 5 runs (NFDR § 9); `pytest products/tracker17/tests/` exits 0
- [x] out-of-date-move — a move made from a page whose task has since changed is refused, says the status has changed and names the moves the page now shows, or none for a final status, and offers no reload (UX-I3, UX-F4); a move refusal reached by an address with no press states its reason as a fact about the task, names the move the address asks for, and gives no action and no reload (CONTENT RN-26, UX-I3), where `web/pages.py:760` says "the move you pressed" today; the saved data is the same before and after each (AC-12); the integration tests pass
- [ ] move-timed-run — `python3 tests/timed_run.py` exits 0 with a status move and its landing page each under the limit on the existing 1,000 × 20 fixture (NFDR QC-48), checked by `tests/integration/test_timed_run.py`; both suites pass

2026-10-12, shukuba-refine after `tracker17` unit `edit-task-fields`: § Relation and § Out name `narrow-and-sort` and `delete-and-rename` by their seeds in `unpicked/`, which are now cut.

2026-10-19, stations-from-seed: three stations became four, the same order. `allowed-moves` holds the `cancelled` button back for `cancel-confirmation`, because a move to `cancelled` must never save unconfirmed (SDD § 4 EX-6) and no page shows a control before its slice (EX-12); the workflow rule itself keeps every move.
2026-10-19, stations-from-seed: the no-longer-overdue rule moved from `out-of-date-move` to `allowed-moves`, the first station where a task can reach `done`; leaving it later would ship a finished task marked overdue.
2026-10-19, stations-from-seed: the timed run split from `out-of-date-move` into `move-timed-run`, last, because a stale-page refusal and a timing under the limit are two merges; the last station carries the seed's bar (both suites and the timed run).
2026-10-19, shukuba-refine after `tracker17 · tobiishi · 2026-10-19_allowed-moves`: `cancel-confirmation` now also removes the pages' withholding of `cancelled` (`web/pages.py:603`), so no page keeps a second rule about which moves are offered once the button exists; and it requires the whole browser folder to exit 0 where layer 5 runs, because `tests/e2e/test_moves.py` landed without ever running (that unit's code-integrity report, § Not verified).
2026-10-20, shukuba-refine after `tracker17 · tobiishi · 2026-10-20_history-after-confirm`: `out-of-date-move` no longer offers a reload, because UXD version 8 (UX-I3, UX-F4) says the overtaken move lands on a page built after the refusal and names its moves instead; it also takes the refusal reached with no press (CONTENT RN-26), handed on by that unit with no owner, because it is the same move refusal page (`web/pages.py:760`). SDD § 6 S-4 still says "offers a reload"; raised on its companion.
2026-10-21, shukuba-refine after `tracker17 · tobiishi · 2026-10-21_out-of-date-move`: the line above no longer holds — SDD version 11 folded that companion item, and § 6 S-4 now has the out-of-date move offer no reload and names the refusal reached with no press.

## Relation to existing work

Rests on `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`. It also tests `tracker17 · nemawashi · 2026-10-07_first-project`: its confirmation tests show whether pages with no script can carry UX-I2 (SDD § 7, `validates`). `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` rests on it, and `tracker17 · nemawashi · 2026-10-11_delete-and-rename` reuses its confirmation.

## Out (later / elsewhere)

The confirmations on deleting a task and a project (`tracker17 · nemawashi · 2026-10-11_delete-and-rename`). A moved task leaving a list filtered by status (`tracker17 · nemawashi · 2026-10-11_narrow-and-sort`).
