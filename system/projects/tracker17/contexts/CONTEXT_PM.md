# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-11-13_saver-fake-and-suite` — the change for station `2026-11-13_saver-fake-and-suite` (seed `2026-11-13_one-fake-and-one-contract-suite-per-contract`, item 1 of 3), derived from the station's reached-when, 2026-11-13. Creates the one test-support module under `tests/` with the `Saver` fake, a layer-2 contract suite for `save` that runs handed `SavedData` and handed the fake, and moves every test's own `save` stand-in onto the fake (20 files, 44 lines at `22365380e`), so the `def save(` grep matches one file. Sizing: one capability, one merge; the acceptance boundary is the station's reached-when 1 to 4. Scope boundary: no `Clock` stand-in moves, no layer-6 walk, production code unchanged, the fake is never loosened to pass a test, no inheritance from `Saver` (QC-3). FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `nfdr` / `preserving`: NFDR QC-64 drives it, test code only, no enforcement verdict changes until the seed's walk station.
