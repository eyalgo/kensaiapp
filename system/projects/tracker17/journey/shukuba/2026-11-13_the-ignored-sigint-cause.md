# 宿場 Shukuba — the ignored-SIGINT proof test no longer fails a full run

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-11-13_the-ignored-sigint-test-holds-in-a-full-run`. Slug: `the-ignored-sigint-cause`.*

## What it is

`test_real_start_stops_when_pytest_launch_ignores_sigint` (`products/tracker17/tests/integration/test_sigint_launch.py`) hands a start case to a pytest launched with SIGINT ignored; that case waits a fixed 30 seconds for the tracker to stop. It failed in a full run of the card's suite and passed alone, twice (2026-10-29, and the base of `tracker17 · tobiishi · 2026-11-13_walk-skips-by-name`). This station finds the timing dependence that is left, measures it so the failure can be made to happen on demand, and removes it in the product. One station: a separate find-the-cause leg would serve only the fix.

## Reached when

1. A measurement exists in the change's tests that fails on the base commit and passes after the change. It reproduces the timing dependence on demand, without needing a full run to hit it by luck. The cause it shows is named in the change's commit body or test docstring.
2. `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_sigint_launch.py::test_real_start_stops_when_pytest_launch_ignores_sigint` passes when run alone.
3. Both commands of the card's `Test command:` exit 0, run from the change worktree root: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`.
4. `git diff <base>..HEAD` over `products/tracker17/` adds no `pytest.mark.skip`, `skipif`, `xfail`, retry plugin or decorator, and does not raise the 30-second wait at `tests/integration/test_start.py:L707-L708` or `tests/integration/test_sigint_launch.py:L36-L38`. Checked with `git diff <base>..HEAD -- products/tracker17 | grep -nE '^\+.*(mark\.(skip|skipif|xfail)|xfail|retry|flaky|reruns)'`, case-sensitive, extended regex; it prints nothing, and the diff touches the two wait lines only to remove the dependence, not to enlarge the limit.

## Guardrail

- The proof test keeps proving what it proved: a start launched with SIGINT ignored stops. The fix may not weaken what it asserts.
- No wait limit is raised, no test is skipped, retried or marked expected-to-fail — each hides the failure.
- The two suites of the card's test command must pass in full, not the one test alone.
- **Not here:** `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` owns the fakes and contract suites; `tracker17 · tobiishi · 2026-10-29_the-start-is-stoppable-from-its-ready-line` closed the ready-line gap and stays closed.
