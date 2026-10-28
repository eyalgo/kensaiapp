# 宿場 Shukuba — the summary's status, priority and overdue counts link into the filtered list

*Item 2 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-11_project-summary`. Slug: `linked-counts`.*

## What it is

On a project's Summary, each status count, each priority count and the overdue count becomes a link to that project's task list filtered to exactly that value (SDD § 6 S-6; UXD UX-F6, UX-S5). The no-due-date count, the per-assignee counts and "(unassigned)" stay plain numbers. A linked number's accessible name starts with the number and says what it counts, such as "12 tasks in todo" or "3 overdue tasks" (UXD link-text rule; `products/tracker17/docs/CONTENT.md` number-link name). The filters the links open already exist (`narrow-and-sort`, `all-tasks-list`), so this is one capability and one merge: the summary page's markup plus AC-14's summary test extended to the links. The AC-13 agreement test and the timed summary landed with `summary-page` and are checks that must still pass here, not new work.

## Reached when

1. In the running app, on `Alpha`'s Summary, each status count, each priority count and the overdue count is a link. Following one opens `Alpha`'s task list filtered to that value, and the list's match count equals the number the link showed. The no-due-date count, each per-assignee count and "(unassigned)" are not links.
2. A linked count's accessible name starts with its number and names what it counts (for example "12 tasks in todo", "3 overdue tasks"), and no two links on the page share their text.
3. A zero count is shown as a number, and its link, if present, opens the list's no-match state rather than an error.
4. `pytest products/tracker17/tests/` exits 0, and the suite's summary test (AC-14), on a project built to exercise each row, asserts for every status, priority and overdue link its target and that the list it opens holds exactly the counted tasks; and asserts that the no-due-date and assignee counts carry no link.
5. `python3 products/tracker17/tests/timed_run.py` exits 0, still covering opening a summary, and the AC-13 agreement test (`tests/integration/test_summary_routes.py`) still passes within item 4's run.

## Guardrail

- The link targets reuse the existing filter parameters and `domain/filtering.py`; no second copy of the filter, overdue or sort rules, and no new filter field.
- The no-due-date count, per-assignee counts and "(unassigned)" stay plain numbers.
- Counts, rows and page titles `summary-page` landed keep their values and wording; existing pages and timed actions keep working.

- **Not here:** a summary across projects, which the PRD places out of scope; the unreadable-data page, which is `tracker17 · nemawashi · 2026-10-11_protect-saved-data`.
