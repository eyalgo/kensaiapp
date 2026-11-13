# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-11-13_ignored-sigint-timing` — the change for station `2026-11-13_the-ignored-sigint-cause` (seed `2026-11-13_the-ignored-sigint-test-holds-in-a-full-run`, item 1 of 1), derived from the station's reached-when, 2026-11-13. Finds the timing dependence that makes the ignored-SIGINT proof test fail in a full run, adds a measurement that fails on the base commit and passes after, and removes the dependence where it sits (the start's stop path or the test's setup). Sizing: one capability, one merge; the acceptance boundary is the station's reached-when 1 to 4. Scope boundary: no raised wait limit, no skip, retry or expected-fail mark; the proof test asserts no less; the fakes and contract suites belong to the other seed. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `bug` / `preserving`: the existing stop contract is made to hold in a full run and no public name, input or return changes.
