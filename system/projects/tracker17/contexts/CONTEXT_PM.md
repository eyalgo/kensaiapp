# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-10-27_project-list-filter` — the one change for station `2026-10-27_project-list-filter` (seed `2026-10-11_narrow-and-sort`, item 1). Reaches all six reached-when items: `domain/filtering.py` exists; Apply with each of status, priority, assignee, label, due-date range and overdue shows only matching tasks with their count and the choices in the address, and Clear returns every task; a reversed range is refused with FR-34's reason and a filter matching nothing says so; a moved-out task leaves a filtered list with its completion line (UX-F4); `pytest products/tracker17/tests/` exits 0 with AC-14's filter tests, AC-12's reversed range and AC-13's overdue agreement; `tests/timed_run.py` exits 0 with a timed filter under `LIMIT_SECONDS`. Sizing: one capability (filtering a project's list), one merge. Scope boundary: no sorting, no All tasks list or header link, no summary; list order unchanged; the limit and every existing timed action stay; one value per filter field. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: SRS FR-32 to FR-35 add filter behaviour and a new module.
