# 宿場 Shukuba refine — recommendations to the Principal PM — `2026-11-13_summary-shows-due-today`

*From the review of unit `2026-11-13_summary-shows-due-today`, 2026-11-13. The report beside this file carries what the run
did; this file carries what it could not do and no companion can carry.*

## To the Principal PM

### 1. Retire `tracker17 · nemawashi · 2026-11-13_the-summary-shows-the-due-today-count` once its station is closed

- **Kind:** a seed to retire
- **Why:** Its only station's reached-when holds on `main`, so after the Scrum Master's close the checklist is fully walked.
- **Source:** report § Considered, not moved, row 1: `tests/` `3383 passed, 2 skipped`, `tests/e2e/` `122 passed` and `timed_run.py` exit 0, in a clone at `e4209621a`.
- **Why no companion carries it:** it is a seed's retire, not something a document should state.

### 2. Decide the four due-today fold seeds: their work is on disk

- **Kind:** a seed to drop
- **Why:** SRS version 8, UXD version 12, SDD version 23 and CONTENT version 22 are all Settled and carry the count, no companion is live, and the count is built. Each seed's checklist asks only for a fold that has happened. Picking each just to close it would cost four walks for nothing. Whether to drop them or retire them is your call.
- **Source:** `**Version:**`/`Status:` lines of `products/tracker17/docs/{SRS,UXD,SDD,CONTENT}.md` (8/12/23/22, all Settled; `grep -ciE 'due.today|Due on'` → 15, 20, 31, 5); `ls products/tracker17/docs/*open_issues*` → no match; `tracker17 · nemawashi · 2026-11-13_the-srs-carries-the-due-today-count`, `tracker17 · nemawashi · 2026-11-13_the-uxd-carries-the-due-today-count`, `tracker17 · nemawashi · 2026-11-13_the-sdd-carries-the-due-today-count`, `tracker17 · nemawashi · 2026-11-13_the-content-carries-the-due-today-count`.
- **Why no companion carries it:** it decides whether the project walks four seeds at all, which is the route and not something a document should state.
