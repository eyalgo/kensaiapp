# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-11-14_clock-fake-and-suite` — the change for station `2026-11-13_clock-fake-and-suite` (seed `2026-11-13_one-fake-and-one-contract-suite-per-contract`, item 2 of 3), derived from the station's reached-when, 2026-11-14. Adds the `Clock` fake to `tests/fakes.py` beside the `Saver` fake, a layer-2 contract suite for `now` run handed `main.SystemClock` and handed the fake, with a case that fails a fake returning a naive datetime, and moves all 24 test files' own `now` stand-ins onto the fake so the grep matches one file. Sizing: one capability, one merge; the acceptance boundary is the station's reached-when 1 to 4. Scope boundary: production code unchanged, the `Saver` fake and suite untouched, no layer-6 walk (item 3), fake never loosened, no inheritance from `Clock`, `SystemClock` not subclassed or patched. FDR fit: in-scope (a test-support change driven by NFDR QC-64, no product behaviour moves); `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `nfdr` / `preserving`: test code only, no enforcement command's verdict changes yet.
