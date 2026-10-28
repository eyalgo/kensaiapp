# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-10-28_summary-page` — the one change for station `2026-10-28_summary-page` (seed `2026-10-11_project-summary`, item 1 of 2). Reaches all four reached-when items: `domain/summary.py` exists; `pytest products/tracker17/tests/` exits 0 with a summary test on a project built to exercise each row; the running app's Summary shows total, status and priority counts with zeros, overdue, no-due-date and per-assignee rows as plain numbers, with the empty project showing zeros and the first-task invitation; the task list and the summary carry Tasks and Summary links and the titles `Alpha: Tasks - tracker17` and `Alpha: Summary - tracker17`. Sizing: one capability (a project's summary), one merge, reusing `domain/filtering.py` and the existing overdue marking. Scope boundary: no count links (`linked-counts` is next), no summary across projects, no timed-run extension here. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: SDD § 6 S-6, SRS FR-38 and UXD UX-S5 add a page, links and per-view titles.
