# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-11-13_walk-skips-by-name` — the change for station `2026-11-13_walk-skips-by-name` (seed `2026-11-13_the-source-walk-sees-the-behave-folder`, item 1 of 2), derived from the station's reached-when, 2026-11-13. Makes `SourceWalk._all` in `products/tracker17/tests/conftest.py` skip `tests/`, `.behave/` and `.venv/` by name and `__pycache__` anywhere, not every dot piece, with a test that a module in another dot-folder at the root fails the QC-1 comparison (red at `97603d4f3`) and a second case showing the three named folders stay skipped. Sizing: one capability, one merge; the acceptance boundary is the station's reached-when 1 to 4. Scope boundary: no product code, document or `.behave/` file changes; the `.behave/` walk is item 2 of the seed. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `nfdr` / `changing`: the walk's verdict basis changes, so a check reports differently.
