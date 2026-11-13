# Change Spec — a project's summary shows the due-on-date count

**Date:** 2026-11-13
**Category:** feature
**Behaviour:** changing
**Request:** Make a project's summary show how many open tasks are due on the summary's one date. The count goes in a row labelled "Due on {date}" (date as `YYYY-MM-DD`, the same date "Overdue" is worked out against), directly after the "Overdue" row, as a plain number and not a link; an empty project shows 0. A task due on that date that is neither `done` nor `cancelled` counts as due-on-date and not as overdue; a `done` or `cancelled` task is in neither count. This is one path through `domain/summary.py` (`ProjectSummary` has `overdue` and no due-today field) to the page. New tests carry it and fail on `main` before the work: AC-13's due-today side, and the summary test's count row on an empty project and on a built one. Both commands of the card's test command must pass, and `python3 tests/timed_run.py`, run from the product root, must exit 0. Before the work `grep -rniE 'due.today|due_today' domain application web --include='*.py' --include='*.html'` prints nothing; after it, it prints the field and its use. The count must stay a plain number labelled "Due on {date}" (no link, no "Due today" wording on the page). Overdue's meaning and its existing tests must not be weakened, and one "today" must serve both counts. Nothing may be added to the list (no "Due on" marker on rows, no due-today filter, no summary across projects). The document folds (SRS, UXD, SDD, CONTENT) are not part of this change.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened

---

## Change Summary

A project's Summary gains one row, `Due on {date}`, directly after `Overdue`: the number of the project's open tasks due on the date the summary's counts are worked out against. It builds what FDR R-129 to R-131, SRS FR-38 and AC-13, UXD UX-F6 and UX-S5, SDD § 6 S-6 and CONTENT § Terminology already state and the product does not do yet.

Paths below are relative to the product root, which `system/projects/tracker17/project.md` `Product path:` names.

---

## Rules

### The count

- **CP-808:** For one project, the Summary shows the due-on-date count: the number of the project's tasks whose due date is the summary's date (CP-809) and whose status is `todo` or `in-progress`. A task in `done` or `cancelled`, a task with no due date, a task due before the date and a task due after it are not in the count. A task of another project is never in it. *(FDR R-129; SRS FR-38)*
- **CP-809:** The summary's date is the machine's local calendar date at the moment the tracker produces the summary (FDR R-69). One summary works out its Overdue count and its due-on-date count against that one date, even when the date changes while the summary is produced, so an open task due on that date is in exactly one of the two counts (FDR R-131).
- **CP-810:** An open task due on the summary's date is in the due-on-date count and not in the Overdue count. A task due on that date in `done` or `cancelled` is in neither count. *(FDR R-130; SRS AC-13)*

### The row on the page

- **CP-811:** The Summary's "Due dates" group shows three rows, in this order: `Overdue`, then `Due on {date}`, then `No due date`. `{date}` is the summary's date of CP-809, written `YYYY-MM-DD` — e.g. `Due on 2026-11-13`. The label's words are CONTENT § Terminology's (SDD § 4 EX-11). No text on the Summary page reads "Due today" or "Today".
- **CP-812:** The due-on-date count is shown as a bare numeral, `0` included. Its cell holds no link and carries no accessible name of its own. The label alone names what it counts (CONTENT § Accessibility of text). The Summary's links stay the nine they are today — the four status counts, the four priority counts and the Overdue count — each with its address and its name unchanged.
- **CP-813:** A project with no tasks shows the row `Due on {date}` with `0`, among its other zero rows and beside the invitation to add a first task. *(FDR R-129; UXD UX-F6)*
- **CP-814:** The Overdue count keeps its meaning under FDR R-68, its value, its place first in the "Due dates" group and its link. The `No due date` row keeps its count and stays a plain number. The tests that assert these today keep passing unchanged, apart from the two rows-list assertions *Locked Answers* Gap 6 names, which keep every row they assert and add the new one.

### Tests and checks

- **CP-815:** New tests carry SRS AC-13's due-today side, with the date set by the test through a clock handed in and no name inside a product module patched (SDD § 4 TS-2; NFDR QC-28): an open task due on the date is in the due-on-date count and not in the Overdue count, and a task due on the date in `done` and one in `cancelled` are in neither count.
- **CP-816:** New tests pin the Summary page's `Due on {date}` row on a project with no tasks (count `0`) and on a built project whose count is not zero and that also holds tasks outside it, the row in its CP-811 place with the count CP-808 gives. Each new test of CP-815 and this rule fails on the base commit and passes after the change.
- **CP-817:** The Summary feature's trace covers the count (SDD § 4 TS-3, TS-4; NFDR QC-11): `domain/summary.py`'s opening docstring names the requirements it realizes with the count among them (SRS FR-38, AC-13), every `application` and `web` module that takes part, and the test modules that check it, and every new or changed test module names the requirements or acceptance criteria it checks. `tests/architecture/test_trace.py` passes.
- **CP-818:** The change adds no class that stands in for the clock or the saver anywhere under `tests/` outside the test-support module `tests/fakes.py` (SDD § 4 TS-6; NFDR QC-64). A new test that needs a set date hands the date in as a value, or uses a clock stand-in the suite already has.
- **CP-819:** The words `Due on` are not held in `domain/`, which keeps no wording shown to the operator (NFDR QC-20).
- **CP-820:** Both commands of the card's `Test command:` pass, and so do NFDR QC-62's three gates, run from the product root through `uv run`: `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web` (NFDR QC-62).
- **CP-821:** `python3 tests/timed_run.py`, run from the product root, exits 0, and its Summary check holds the page to every row, the `Due on {date}` row among them (SDD § 4 TS-5; NFDR QC-48).
- **CP-822:** Run from the product root, `grep -rniE 'due.today|due_today' domain application web --include='*.py' --include='*.html'` prints nothing on the base commit and, after the change, prints the count's field in `domain/summary.py` and at least one line where that field is used. (The request's own acceptance check.)

---

## Examples

| Scenario | Expected behavior |
|---|---|
| Today is 2026-10-06. Task A due 2026-10-06 in `todo`, task B due 2026-10-06 in `cancelled`, task C due 2026-10-05 in `in-progress` (FDR § Examples) | `Overdue` 1, `Due on 2026-10-06` 1. A is due on the date and not overdue, C is overdue, B is in neither. *(CP-808, CP-810, CP-811, CP-815)* |
| Today is 2026-10-06. Task A due 2026-10-06 in `in-progress`, task B due 2026-10-06 in `done` | `Due on 2026-10-06` 1, `Overdue` 0. *(CP-808, CP-810, CP-815)* |
| Today is 2026-10-06. Tasks due 2026-10-07 in `todo`, and with no due date in `todo` | `Due on 2026-10-06` 0, `Overdue` 0, `No due date` 1. *(CP-808, CP-814)* |
| Today is 2026-10-06; another project has an open task due 2026-10-06 | This project's `Due on 2026-10-06` is 0. *(CP-808)* |
| A project with no tasks, summary date 2026-11-13 | The "Due dates" group reads `Overdue` 0, `Due on 2026-11-13` 0, `No due date` 0; the invitation to add a first task shows. *(CP-811, CP-813, CP-816)* |
| An open task due 2026-10-06; the date changes from 2026-10-06 to 2026-10-07 while the summary is produced (FDR § Examples) | The task is in exactly one count: `Due on 2026-10-06` 1 and `Overdue` 0 when the summary's date is 2026-10-06; `Due on 2026-10-07` 0 and `Overdue` 1 when it is 2026-10-07. The label's date is the one both counts used. *(CP-809)* |
| A populated project's Summary | The `Due on {date}` cell is a numeral with no link; the page's count links are the same nine as before; no "Due today" or "Today" text on the page. *(CP-811, CP-812, CP-814)* |
| The suites, the gates and the timed run after the change | Both test commands pass; the three QC-62 gates pass; `python3 tests/timed_run.py` exits 0; the pointer test passes. *(CP-817, CP-818, CP-819, CP-820, CP-821)* |
| The grep of CP-822 before and after | Before: no output. After: the field's line in `domain/summary.py` and a line that uses it. *(CP-822)* |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| `ProjectSummary` has `overdue` and no due-today field (request) | read `domain/summary.py`, `ProjectSummary` | at `<a commit not in the public history>`: fields `project, total, status_counts, priority_counts, overdue, no_due_date, assignee_counts` |
| The "Due dates" group today shows `Overdue` (a link) then `No due date` (plain) | read `web/pages.py` `summary_page`; `tests/integration/test_summary_pages.py::test_summary_has_all_ordered_plain_rows_and_only_allowed_links`, which asserts `rows_of(due) == [("Overdue", "1"), ("No due date", "2")]` | `<a commit not in the public history>`: 1 passed |
| CP-822's before half: the grep prints nothing | the grep, run from the product root | `<a commit not in the public history>`: no output, exit 1 |
| CP-811: no "today" text on the Summary page today | `grep -n -i 'today' web/pages.py` | `<a commit not in the public history>`: no output |
| CP-814 (left unchanged): Overdue's meaning against the supplied date | `tests/unit/test_summary.py::test_summary_overdue_uses_the_supplied_date`, by itself | `<a commit not in the public history>`: 1 passed |
| CP-814 (left unchanged): Overdue count agrees with the marking and the filter (AC-13) | `tests/integration/test_summary_routes.py::test_overdue_mark_filter_and_summary_agree`, by itself | `<a commit not in the public history>`: 1 passed |
| CP-814 (left unchanged): the list marking and the overdue filter agree (AC-13) | `tests/integration/test_filter_tracker.py::test_overdue_filter_and_row_marking_agree`, by itself | `<a commit not in the public history>`: 1 passed |
| CP-812, CP-814 (left unchanged): the Summary's nine count links, in the browser | `tests/e2e/test_summary.py::test_browser_can_open_summary_and_return_to_tasks`, by itself | `<a commit not in the public history>`: 1 passed |
| CP-813 base: an empty project's Summary shows all-zero rows and the invitation | `tests/integration/test_summary_pages.py::test_empty_summary_invites_first_task_beside_all_zero_rows`, by itself | `<a commit not in the public history>`: 1 passed |
| CP-820: QC-62's three gates pass on the base | `uv run --locked ruff format --check .`; `uv run --locked ruff check .`; `uv run --locked mypy main.py errors.py domain application persistence web`, from the product root | `<a commit not in the public history>`: "372 files already formatted"; "All checks passed!"; "Success: no issues found in 28 source files" |
| Gap 6: the timed run's Summary check refuses a page that carries a `Due on {date}` row it does not expect | built an empty project's real Summary page with `web.pages.summary_page`, then the same page with a `Due on 2026-11-13` / `0` row inserted before `No due date`, and ran `tests/timed_run.py`'s `_summary_landing_shows` on each, in a scratch script outside the tree | `<a commit not in the public history>`: real page `True`; page with the row `False` (rows parsed as `Overdue 0`, `Due on 2026-11-13 0`, `No due date 0`) |
| CP-818: the test-support module holds no clock stand-in today, and the summary's route tests use one the suite already has | read `tests/fakes.py`; `grep -rlE '^class \w*Clock' tests \| wc -l`; read the imports of `tests/integration/test_summary_routes.py` | `<a commit not in the public history>`: `tests/fakes.py` defines `FakeSaver` only; 24 files under `tests/` define a class whose name ends in `Clock`; the summary route tests import `MovableClock` from `tests/integration/test_task_routes.py` |
| The summary works its counts out from one date | read `application/tracker.py` `project_summary` and `domain/summary.py` `summarize_project` | `<a commit not in the public history>`: one clock read gives one date, passed to every count |

No rule pins output that renders a language-level fact: the `YYYY-MM-DD` date is CONTENT § Terminology's format, a value the product chooses, so the Python packet decides nothing here.

---

## Out of Scope

- No due-on-date marker on any list row, no due-on-date filter, and no summary across projects (SDD § 6 S-6 *Not in this slice*; FDR OOS-17).
- No change to the Overdue rule (FDR R-68), to what "today" means (FDR R-69), or to the overdue marking and the overdue filter.
- No link from the due-on-date count to a list.
- No change to the saved data: the count is worked out from the tasks, and saved data written before this change loads unchanged (SRS RN-26).
- No edit to any product document — SRS, UXD, SDD, CONTENT, FDR, NFDR or ADR (the request: "The document folds (SRS, UXD, SDD, CONTENT) are not part of this change").

---

## Locked Answers (the divergence record — self-review 2026-11-13)

- **Gap 1 — (b) the row's place in its group:** the request says "directly after the 'Overdue' row"; CP-811 locks the "Due dates" group to `Overdue`, `Due on {date}`, `No due date`. — SDD § 6 S-6 lists "the overdue count, directly after it the due-today count, the count with no due date", and "directly after" in the same group is the only reading where the two counts sit together, as UXD UX-F6 asks.
- **Gap 2 — (b) the count's accessible name:** the request says "a plain number and not a link"; CP-812 adds that the cell carries no accessible name of its own. — CONTENT § Accessibility of text: "A plain count that is not a link, such as the summary's 'Due on 2026-11-13' count, takes no accessible name of its own".
- **Gap 3 — (b) one date across midnight:** the request says "one 'today' must serve both counts"; CP-809 states FDR R-131's "even when the date changes while the summary is produced", and the label shows that same date. — Without it, a summary produced across midnight could count one task as both or neither, and the label could name a date the counts were not worked out on.
- **Gap 4 — (b) "no 'Due today' wording":** CP-811 reads it as no "Due today" and no "Today" text on the Summary page. — CONTENT § Terminology bars both for this count; the page today carries neither (Verified Claims).
- **Gap 5 — (e) checks the records require that the request leaves out:** CP-815's clock handed in (SDD § 4 TS-2, NFDR QC-28), CP-817's trace (SDD § 4 TS-3, TS-4, NFDR QC-11), CP-818's one clock fake (SDD § 4 TS-6, NFDR QC-64), CP-819's no wording in `domain` (NFDR QC-20) and CP-820's three gates (NFDR QC-62). — Each binds what this change adds: a new count tested with a set date, new tests, and a new label on a page. The records require them of every change that adds those.
- **Gap 6 — (f) existing tests named as changing:** (1) `tests/integration/test_summary_pages.py::test_summary_has_all_ordered_plain_rows_and_only_allowed_links` asserts the "Due dates" rows are exactly `Overdue`, `No due date`; it changes to `Overdue`, `Due on {date}`, `No due date`, and keeps asserting every other group's rows, the nine count links, the headings and that the page holds no form or script. (2) `tests/timed_run.py`'s Summary check holds the page to an exact list of rows that has no `Due on {date}` row (Verified Claims), so CP-821 cannot pass without it gaining that row; `tests/integration/test_timed_run.py`, which checks that harness against its own copy of the rows, follows it. Both keep asserting every row they assert today, the nine linked cells and the four group headings. — CP-811 and CP-821 together cannot be met without these changes.
- **Gap 7 — QC-64's reach on this change:** NFDR QC-64 starts unmet: the base has no clock fake in `tests/fakes.py` and no clock contract suite (Verified Claims), and NFDR RN-65 says the entry "lands with" the change that moves the existing stand-ins and writes the suites. CP-818 binds what this change adds — no new stand-in class outside `tests/fakes.py` — and does not move the existing stand-ins. — Moving them and writing the clock's suite is the change RN-65 names, a separate capability under the sizing test; the part of the check this change can break, adding a stand-in, is folded in.
