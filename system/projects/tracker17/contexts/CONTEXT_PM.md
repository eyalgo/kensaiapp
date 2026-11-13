# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-11-13_behave-import-walk` — the change for station `2026-11-13_behave-import-walk` (seed `2026-11-13_the-source-walk-sees-the-behave-folder`, item 2 of 2), derived from the station's reached-when, 2026-11-13. Adds a layer-6 test in `products/tracker17/tests/architecture/` that walks `.behave/` as its own root with `SourceWalk` and `Module.imported()`: it fails on an import from `tests` and on an existing `.behave/` holding no module, and reads nothing when the folder is absent. Sizing: one capability, one merge; the acceptance boundary is the station's reached-when 1 to 4. Scope boundary: no product code, `.behave/` file or document changes; the root walk's by-name skip is the sealed item 1. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `nfdr` / `changing`: a new check changes what an enforcement command reports.
