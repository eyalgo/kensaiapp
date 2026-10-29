# 宿場 Shukuba — the start tests pass when the suite is launched with SIGINT ignored

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-29_start-tests-under-ignored-sigint`. Slug: `start-tests-under-ignored-sigint`.*

## What it is

The tests in `products/tracker17/tests/integration/test_start.py` start the real tracker in a child process (`_run_real_start`) and stop it with SIGINT, waiting 30 seconds. Launched as a background job the child inherits an ignored SIGINT, never stops, and the wait times out. This station makes the suite pass the same way whether SIGINT is ignored or not. Whether the fix sits in the tests or in the start they drive is the walk's call. It is one capability with one acceptance boundary, so one station.

The signal half is in place: a session fixture in `products/tracker17/tests/conftest.py` gives the suite's own children default SIGINT. What is left is the proof test, and reflowing that file's line 1, which is 101 columns against the Python packet's 100 (`conventions.md:17`).

## Reached when

From the repository root, the product's two suites each exit 0 both in the foreground and with SIGINT ignored (`sh -c 'trap "" INT; exec <command>'`), with no `test_start.py` failure or timeout:

- `python -m pytest products/tracker17/tests/ -q` — `unit`, `integration` and `architecture`; its collection leaves `e2e` out unless named (`products/tracker17/tests/conftest.py`, `pytest_ignore_collect`);
- `python -m pytest products/tracker17/tests/e2e/ -q` — the end-to-end suite, the second suite `products/tracker17/docs/nfdr.md` § 10 names.

And one test in the suite, named by the change, passes in the foreground at the commit under test and fails in the foreground on `970f6a4ca`, because the start tests' SIGINT did not stop a tracker when the suite was launched with SIGINT ignored. Run all of it in a disposable clone of the commit under test.

*Amended 2026-10-29 by the shukuba-refine of `tracker17 · tobiishi · 2026-10-29_start-tests-under-ignored-sigint`: the bar names the product's two suites, because its collection rule and five basenames shared by `unit/` and `e2e/` keep one run from holding all four folders, and it adds the proof test. Measured at `3b2c0dd28`: all four suite runs exit 0 (2651 and 121 passed); the proof test is this station's remaining work.*

## Guardrail

- Ctrl-C at a terminal still stops the tracker for an operator; the foreground run keeps passing.
- No test is deleted, skipped or marked expected-to-fail to make the run pass; the start tests keep exercising the real start in a child process.
- No product document is edited unless a sentence this change makes false requires it.
- **Not here:** any change to what Ctrl-C does for an operator at a terminal (named Out in the seed `tracker17 · nemawashi · 2026-10-29_start-tests-under-ignored-sigint`).
