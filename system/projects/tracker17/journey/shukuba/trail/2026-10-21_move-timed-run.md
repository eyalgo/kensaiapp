# 宿場 Shukuba — The timed run covers a status move at full volume

*Item 4 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-07_status-moves`. Slug: `move-timed-run`.*

## What it is

NFDR QC-48 has every action SRS NFR-1 lists shown within 1 second at 1,000 tasks of 20 comments each, and has a change that adds a listed action add it to the timed run. `tests/timed_run.py` times project creation, task add, field edit, label add and remove, the name save, the comment add and the assignee add and remove; it does not time a status move, which `allowed-moves` added and the unit left out of the run (CP-315 was set aside for this station). This station adds the status move, with the page it lands on, in the run's existing manner: its own 1,000 × 20 fixture, a same-origin submission, a failure on a refused or failed action, and the POST and its landing GET timed apart and as a total. The run states the text lengths it uses. It is one station because it is one claim: the run times every listed action that exists, and the move is the last one missing.

## Reached when

1. `python3 tests/timed_run.py`, run from `products/tracker17` in a fresh clone checked out at the commit under test (`core/roles/CROSS_ROLE.md` § *Every seat*), exits 0 and prints a timed POST, a timed landing GET and a total for a status move, each under `LIMIT_SECONDS` (1.0). Before the work the run prints none of these for a move.
2. The move counts only when it happened: the run fails (non-zero) if the task's saved status is not the one moved to, or if the landing page does not show the move's result. Checked by tests in `tests/integration/test_timed_run.py` that feed the harness a refused move and a landing that does not show the result, and find the non-zero verdict.
3. The run prints the fixture it used for the move, with the 1,000 tasks, the 20 comments each and the text lengths. Checked by an integration test on the printed report.
4. `pytest products/tracker17/tests/` exits 0 in the same fresh clone, with every existing test in `tests/integration/test_timed_run.py` still present and passing; and `pytest products/tracker17/tests/e2e/` exits 0 where layer 5 runs (NFDR § 9), as the seed's bar asks both suites.

## Guardrail

- No product code under `domain/`, `application/`, `persistence/` or `web/` changes to make a timing pass. A timing over the limit is a finding about the saved data's design, not edited away here.
- The limit stays 1.0 second; no existing timed action's bar or its test is loosened, deleted or skipped.
- No action beyond the status move is added; the move to `cancelled` with its confirmation is not timed here unless the move's own press path is the one a plain move uses.
- **Not here:** deleting a task with its comments — `tracker17 · nemawashi · 2026-10-11_delete-and-rename`; the unreadable-data pages — `tracker17 · nemawashi · 2026-10-11_protect-saved-data`.
