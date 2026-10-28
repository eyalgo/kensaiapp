# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-10-28_linked-counts` — the one change for station `2026-10-28_linked-counts` (seed `2026-10-11_project-summary`, item 2 of 2). Reaches all five reached-when items: each status, priority and overdue count on a project's Summary is a link to that project's task list filtered to that value, with the list's match count equal to the number shown; linked counts carry an accessible name starting with the number and no two links share text; zero counts show as numbers and any link opens the no-match state; `pytest products/tracker17/tests/` exits 0 with the AC-14 summary test asserting every link's target and the counted tasks, and no link on no-due-date or assignee counts; `timed_run.py` exits 0 and the AC-13 agreement test still passes. Sizing: one capability, one merge, reusing `domain/filtering.py` and the existing filter parameters. Scope boundary: no summary across projects, no unreadable-data page, no new filter field. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: adds links and a link accessible-name contract to the Summary page.
