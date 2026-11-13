# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-11-13_summary-shows-due-today` — the change for station `2026-11-13_summary-shows-due-today` (seed `2026-11-13_the-summary-shows-the-due-today-count`, item 1 of 1), derived from the station's reached-when, 2026-11-13. Adds the due-today count to a project's summary: a row "Due on {date}" directly after "Overdue", a plain number, 0 on an empty project, one "today" for both counts, through `domain/summary.py` to the page, with AC-13's due-today tests and the summary test's count row failing on `main` first. Sizing: one capability, one merge; the acceptance boundary is the station's reached-when 1 to 5. Scope boundary: no "Due on" marker on list rows, no due-today filter, no summary across projects, no link, no "Due today" wording, Overdue's meaning and tests unchanged, no document folds. FDR fit: in-scope (FDR version 8 states the count at R-129 to R-131); `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: the summary gains a row the suite does not pin.
