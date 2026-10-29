# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-10-29_ignored-sigint-proof-test` — the last change for station `2026-10-29_start-tests-under-ignored-sigint` (seed `2026-10-29_start-tests-under-ignored-sigint`, item 1 of 1). The signal half is in place at `3b2c0dd28` (session SIGINT fixture in `products/tracker17/tests/conftest.py`; both suites exit 0 foreground and under ignored SIGINT). This change adds the proof test the first unit deferred: one test that passes in the foreground at the commit under test and fails in the foreground on `970f6a4ca`, plus the reflow of `conftest.py` line 1 (101 columns against the Python packet's 100). Run in a disposable clone. Sizing: one capability, one merge; the acceptance boundary is the station's reached-when. Scope boundary: Ctrl-C behaviour for an operator unchanged; no test deleted, skipped or marked expected-to-fail; the start tests keep driving the real start in a child process; no document edited unless a sentence this change makes false requires it. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `bug` / `preserving`: a violated suite-passes contract, no operator-visible behaviour moves.
