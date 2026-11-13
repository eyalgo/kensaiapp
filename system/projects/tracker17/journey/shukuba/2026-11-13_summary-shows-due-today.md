# 宿場 Shukuba — a project's summary shows the due-today count

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-11-13_the-summary-shows-the-due-today-count`. Slug: `summary-shows-due-today`.*

## What it is

Build the count the definition documents already state (SDD § 6 S-6, SRS AC-13): a project's summary shows how many open tasks are due on the summary's one date, directly after "Overdue", as a plain number, labelled "Due on {date}" (CONTENT § Terminology). It is one path through `domain/summary.py` (`ProjectSummary` has `overdue` and no due-today field) to the page, with its AC-13 tests, so it is one station and not two merges.

## Reached when

Run from `products/tracker17`:

1. Opening a project's summary shows a row labelled "Due on {date}" (date `YYYY-MM-DD`, the same date "Overdue" is worked out against), directly after the "Overdue" row, with the count as a plain number and not a link. An empty project shows 0.
2. A task due on that date, neither `done` nor `cancelled`, is in the due-today count and not in the overdue count; one that is `done` or `cancelled` is in neither.
3. New tests carry it: AC-13's due-today side, and the summary test's count row on an empty project and on a built one. They fail on `main` at the commit the station opens from, and pass after. Before the work, `grep -rniE 'due.today|due_today' domain application web --include='*.py' --include='*.html'` (run from the product root, case-insensitive, extended regex) prints nothing; after it, it prints the field and its use.
4. Both commands of the card's test command pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`.
5. `python3 tests/timed_run.py`, run from the product root, exits 0.

## Guardrail

- The count stays a plain number with the label "Due on {date}"; no link, no "Due today" wording on the page (CONTENT § Terminology).
- Overdue's meaning and its existing tests are not weakened; one "today" serves both counts.
- Nothing is added to the list: no "Due on" marker on rows, no due-today filter, no summary across projects (SDD § 6 S-6 *Not in this slice*).
- **Not here:** the document folds — `tracker17 · nemawashi · 2026-11-13_the-srs-carries-the-due-today-count`, `tracker17 · nemawashi · 2026-11-13_the-uxd-carries-the-due-today-count`, `tracker17 · nemawashi · 2026-11-13_the-sdd-carries-the-due-today-count`, `tracker17 · nemawashi · 2026-11-13_the-content-carries-the-due-today-count`.
