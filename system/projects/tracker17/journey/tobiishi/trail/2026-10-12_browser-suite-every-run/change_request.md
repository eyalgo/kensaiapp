# Change request — 2026-10-12_browser-suite-every-run

**Request:** Find why the focus tests in `products/tracker17/tests/e2e/test_first_project.py` and `tests/e2e/test_people.py` fail on some runs of `main` and pass on others, and fix it in the tests or in what they measure, so `pytest products/tracker17/tests/e2e/` (the whole folder as it stands on `main`) exits 0 run after run. Name the cause in the closing commit's body: which tests, what raced or varied, and why the fix removes it. A retry or rerun plugin or option is not a fix and must not be added. The focus checks must still assert focus, and no test may be deleted, skipped or loosened so that it cannot fail. No new end-to-end tests, and no behaviour change the fix does not need. Diagnosis and fix are one change: a named cause with no fix leaves the suite as flaky as before.

Sizing: the acceptance boundary is one capability, a deterministic e2e suite, from the station's reached-when 1 to 3 (`journey/shukuba/2026-10-12_browser-suite-every-run.md`). It is the only change the station is expected to take. It fits one flow because diagnosis, fix and the 20-run proof are one merge.

**Category:** nfdr
**Behaviour:** preserving
**Classified because:** the station's guardrail (`No new end-to-end tests, and no behaviour change the fix does not need`) and its "fixes it in the tests or in what they measure" make this suite tooling: it adds no behaviour or public name, and no check gains a rule.

**Sealed:** 2026-10-12 — accepted; merged to `main` via `--no-ff`.
