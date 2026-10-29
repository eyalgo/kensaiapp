# 宿場 Shukuba — the start tests pass when the suite is launched with SIGINT ignored

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-29_start-tests-under-ignored-sigint`. Slug: `start-tests-under-ignored-sigint`.*

## What it is

The tests in `products/tracker17/tests/integration/test_start.py` start the real tracker in a child process (`_run_real_start`) and stop it with SIGINT, waiting 30 seconds. Launched as a background job the child inherits an ignored SIGINT, never stops, and the wait times out. This station makes the suite pass the same way whether SIGINT is ignored or not. Whether the fix sits in the tests or in the start they drive is the walk's call. It is one capability with one acceptance boundary, so one station.

## Reached when

From the repository root, the full suite run with SIGINT ignored exits 0:

`sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/ -q'`

and the same suite run in the foreground, `python -m pytest products/tracker17/tests/ -q`, also exits 0. Both runs cover the `unit`, `integration`, `e2e` and `architecture` folders under `products/tracker17/tests/`, and neither reports a `test_start.py` failure or timeout. Before the work the first command fails: `_run_real_start` has four callers in `test_start.py`, some parametrized, and the refine's full-suite run counted 12 failures. Run both in a disposable clone of the commit under test.

## Guardrail

- Ctrl-C at a terminal still stops the tracker for an operator; the foreground run keeps passing.
- No test is deleted, skipped or marked expected-to-fail to make the run pass; the start tests keep exercising the real start in a child process.
- No product document is edited unless a sentence this change makes false requires it.
- **Not here:** any change to what Ctrl-C does for an operator at a terminal (named Out in the seed `tracker17 · nemawashi · 2026-10-29_start-tests-under-ignored-sigint`).
