# 宿場 Shukuba — the browser suite passes on every run

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-12_browser-suite-every-run`. Slug: `browser-suite-every-run`.*

## What it is

`pytest products/tracker17/tests/e2e/` fails on some runs of `main` and passes on others. The failures are focus tests in `tests/e2e/test_first_project.py` and `tests/e2e/test_people.py`. This station names the cause and fixes it in the tests or in what they measure. Diagnosis and fix are one station, because a named cause with no fix leaves the suite as flaky as before. A retry or rerun plugin hides a failure rather than fixing it, so it is not a fix.

## Reached when

1. The cause is written in the closing commit's body: which tests, what raced or varied, and why the fix removes it.
2. No retry or rerun plugin or option is added: `git diff <station-open SHA>..HEAD -- products/tracker17 | grep -inE 'rerun|flaky|retry|retries'` prints nothing on added lines. The same grep over the diff, run before the work, also prints nothing, so it can only fail if the fix adds one.
3. On a `git archive <HEAD SHA> products/tracker17` copy, `git init`-ed, with the README's `.venv`, `pytest products/tracker17/tests/e2e/` (the whole folder as it stands on `main`, not a subset) exits 0 on 20 consecutive runs. The run log shows 20 exit codes of 0.

## Guardrail

- No new end-to-end tests, and no behaviour change the fix does not need.
- No test is deleted, skipped, or loosened so that it cannot fail; the focus checks still assert focus.
- **Not here:** later stations of seeds that set a "both suites pass" bar; this station is what lets them meet it.
