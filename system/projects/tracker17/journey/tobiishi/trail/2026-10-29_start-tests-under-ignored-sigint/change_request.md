# Change request — 2026-10-29_start-tests-under-ignored-sigint

---

**Request:** The tests that start the real tracker in a child process and stop it with SIGINT (the four callers of `_run_real_start` in `products/tracker17/tests/integration/test_start.py`, some parametrized) should pass the same way whether the suite is launched in the foreground or as a background job with SIGINT ignored. Today, when SIGINT is ignored, the child inherits that and never stops, so the 30-second wait times out; the refine's full-suite run counted 12 failures. After this change both `sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/ -q'` and `python -m pytest products/tracker17/tests/ -q` exit 0 from the repository root, covering the `unit`, `integration`, `e2e` and `architecture` folders, with no `test_start.py` failure or timeout. The new proof is one test run under ignored SIGINT that fails on the starting commit. Where the fix sits (the tests or the start they drive) is for the spec and design to decide, but what Ctrl-C does for an operator at a terminal must not change, no test may be deleted, skipped or marked expected-to-fail, the start tests must keep exercising the real start in a child process, and no product document is edited unless a sentence this change makes false requires it.
**Category:** bug
**Behaviour:** preserving
**Classified because:** the station's reached-when says the suite must exit 0 under both launches while it fails today under ignored SIGINT, which is a violated pass-the-suite contract (the Agari's Works bar), and its guardrail fixes Ctrl-C behaviour for an operator as unchanged, so no public name or FDR-level behaviour moves; a fix that would alter what the start does for an operator is outside this request and goes back to the PM.

**Sealed:** 2026-10-29 — sealed with deferrals; merged to `main` via `--no-ff`.
Environment: owners-mac — no CI
Deferred: task 1 — the outer whole-directory collection of all four folders cannot be built: the unit and e2e folders hold five files with one basename each and no __init__.py, so one pytest process cannot collect both — system/projects/tracker17/journey/tobiishi/2026-10-29_start-tests-under-ignored-sigint/change_spec.md § Invariants
Deferred: task 2 — depends on task 1 — system/projects/tracker17/journey/tobiishi/2026-10-29_start-tests-under-ignored-sigint/change_spec.md § Invariants
