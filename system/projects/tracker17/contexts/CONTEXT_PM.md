# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-10-28_all-tasks-list` — the one change for station `2026-10-28_all-tasks-list` (seed `2026-10-11_narrow-and-sort`, item 3, the seed's last). Reaches all six reached-when items: header All tasks link and the not-found links to Projects and All tasks; All tasks lists every task across projects with a project column, the status moves and no add-task form; the empty state links to Projects; the filter and sort controls work across projects (Apply, Clear, count, address, reversed-range refusal, no-match line, assignee and label choices from all projects); `pytest products/tracker17/tests/` exits 0 with AC-14 run across projects and UX-F4's completion line; `tests/timed_run.py` exits 0 with the filter and sort timed lines under `LIMIT_SECONDS`. Sizing: one capability (tasks across all projects, listed, filtered and sorted), one merge, reusing `domain/filtering.py` and `domain/sorting.py`. Scope boundary: no project summary or links into a filtered list, no summary across projects, no add-task form; no second copy of the filter or sort rules; the limit and every existing timed action stay. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: SDD § 6 S-5 and UXD UX-S7, UX-S10 add a page and links.
