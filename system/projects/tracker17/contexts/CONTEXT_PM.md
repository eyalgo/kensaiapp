# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-11-13_pins-test-reads-behave-lock` — the change for station `2026-11-13_pins-over-behave` (seed `2026-11-13_the-pins-test-reads-the-behave-lock`, item 1 of 1), derived from the station's reached-when, 2026-11-13. Makes `tests/architecture/test_pins.py` read `.behave/pyproject.toml` and `.behave/uv.lock` by QC-39's three checks, with a test per case (unpinned dependency, no manifest, no lock, lock not fixing the declared version fail; absent folder passes) and the `playwright` pin mutation failing it. Test file only; production code untouched. Sizing: one capability, one merge; the acceptance boundary is the station's reached-when 1 to 4. Scope boundary: root checks stay as they are, `.behave/` files stay byte-identical, `uv lock --check --project .behave` stays a review bar. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `nfdr` / `changing`: a check gaining rules changes what the enforcement command reports.
