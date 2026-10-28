# Change request — 2026-10-28_linked-counts

---

**Request:** On a project's Summary page, make each status count, each priority count and the overdue count a link that opens that project's task list filtered to exactly that value, so the list's match count equals the number the link showed. The no-due-date count, the per-assignee counts and "(unassigned)" stay plain numbers. A linked count's accessible name starts with its number and says what it counts ("12 tasks in todo", "3 overdue tasks"), and no two links on the page share their text. A zero count is still shown as a number; if it carries a link, the link opens the list's no-match state, never an error. The links reuse the existing filter parameters and `domain/filtering.py`: no second copy of the filter, overdue or sort rules, and no new filter field. The summary test (AC-14), on a project built to exercise each row, is extended to assert every status, priority and overdue link's target, that the list it opens holds exactly the counted tasks, and that the no-due-date and assignee counts carry no link. The counts, rows and page titles `summary-page` landed must keep their values and wording, the AC-13 agreement test and the timed summary run must still pass, and existing pages and timed actions must keep working. `pytest products/tracker17/tests/` must exit 0.

Sizing: one capability (the summary's counts as links into the filtered list), one merge. The acceptance boundary is station `2026-10-28_linked-counts` (seed `2026-10-11_project-summary`, item 2 of 2; SDD § 6 S-6, UXD UX-F6 and UX-S5, CONTENT number-link name). The filters the links open already exist, so this is the summary page's markup plus the AC-14 test extension. Out of scope: a summary across projects, and the unreadable-data page (`protect-saved-data`).

**Category:** feature
**Behaviour:** changing
**Classified because:** the station's reached-when 1 turns existing plain counts into links to filtered lists, adding navigation behaviour and a link accessible-name contract to the Summary page.
