# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-10-27_project-list-sort` — the one change for station `2026-10-27_project-list-sort` (seed `2026-10-11_narrow-and-sort`, item 2). Reaches all six reached-when items: `domain/sorting.py` exists; Apply with each sort field in each direction shows the order FR-36 defines, with count and choice shown, ascending by default; the sort rides the address with the filter and Clear returns due-date ascending; ties and equal creation times order the same on every request; `pytest products/tracker17/tests/` exits 0 with AC-14's sort tests; `tests/timed_run.py` exits 0 with a timed sort under `LIMIT_SECONDS`. Sizing: one capability (sorting a project's list), one merge. Scope boundary: no All tasks list or header link, no summary; the filter's rules stay; the limit and every existing timed action stay; one sort field, not remembered between sittings. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: SRS FR-36 and FDR R-90 to R-93 add sort behaviour and a new module.
