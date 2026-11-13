# Change request — 2026-11-13_summary-shows-due-today

---

**Request:** Make a project's summary show how many open tasks are due on the summary's one date. The count goes in a row labelled "Due on {date}" (date as `YYYY-MM-DD`, the same date "Overdue" is worked out against), directly after the "Overdue" row, as a plain number and not a link; an empty project shows 0. A task due on that date that is neither `done` nor `cancelled` counts as due-on-date and not as overdue; a `done` or `cancelled` task is in neither count. This is one path through `domain/summary.py` (`ProjectSummary` has `overdue` and no due-today field) to the page. New tests carry it and fail on `main` before the work: AC-13's due-today side, and the summary test's count row on an empty project and on a built one. Both commands of the card's test command must pass, and `python3 tests/timed_run.py`, run from the product root, must exit 0. Before the work `grep -rniE 'due.today|due_today' domain application web --include='*.py' --include='*.html'` prints nothing; after it, it prints the field and its use. The count must stay a plain number labelled "Due on {date}" (no link, no "Due today" wording on the page). Overdue's meaning and its existing tests must not be weakened, and one "today" must serve both counts. Nothing may be added to the list (no "Due on" marker on rows, no due-today filter, no summary across projects). The document folds (SRS, UXD, SDD, CONTENT) are not part of this change.
**Category:** feature
**Behaviour:** changing
**Classified because:** the station's reached-when 1 adds a new row, "Due on {date}", to the summary page, and 2 adds a count whose meaning the existing suite does not pin, so the contract grows (SDD § 6 S-6, SRS AC-13); a change that adds behaviour is `feature` and `changing`.

**Sizing:** one capability, one honest merge. The acceptance boundary is the station's reached-when 1 to 5, sourced from SDD § 6 S-6 and SRS AC-13: the count, its label and its AC-13 tests are one path through `domain/summary.py` to the page, so they are not split. The seed's own cut kept it as one station for the same reason.

**Sealed:** 2026-11-13 — accepted; merged to `main` via `--no-ff`.
Environment: owners-mac — no CI
