# Change Spec — a project's Summary view, counts as plain numbers

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing
**Request:** Give each project a Summary view beside its task list. A project's Tasks and Summary pages each carry a Tasks and a Summary link to the other, and each page's title names its view: `Alpha: Tasks - tracker17` and `Alpha: Summary - tracker17` (CONTENT.md page titles). The summary shows, as plain numbers, the total number of tasks, the count for each of the four statuses and each of the four priorities (`low`, `medium`, `high`, `critical`) with zero counts shown, the overdue count, the count of tasks with no due date, and the open tasks (neither `done` nor `cancelled`) per assignee: one row for every name on the assignee list with zeros included, one more row for each name not on the list that an open task in the project still carries, and always one row for "(unassigned)" (SRS FR-38). A project with no tasks shows zeros and invites a first task (UXD UX-S5). The rules live in a new `products/tracker17/domain/summary.py`, which reuses `domain/filtering.py` and the existing overdue marking for the overdue count rather than copying either. Done when `products/tracker17/domain/summary.py` exists; `pytest products/tracker17/tests/` exits 0 and the suite holds a summary test that builds one project exercising each row (tasks across every status and priority, an overdue task, a task with no due date, a listed assignee, an unlisted name on an open task, and an unassigned task) and asserts every count the summary shows; opening `Alpha`'s Summary in the running app shows the total, each status and priority count with zeros, the overdue count, the no-due-date count and the per-assignee rows as plain numbers, and an empty project shows zeros and the first-task invitation; and the task list and the summary each carry the Tasks and Summary links with the titles above. Sizing: the acceptance boundary is one capability, opening a project's summary and reading its counts (station reached-when 1 to 4, SDD § 6 S-6, SRS FR-38), and it maps to one merge, because it adds one computation module and one page and the counts do no navigation. What must not be weakened: the counts stay plain numbers with no count linking anywhere, since the links into filtered lists are the next station (`linked-counts`); no second copy of the overdue, filter or sort rules; no summary across projects, which the PRD places out of scope; existing pages, strings and the timed actions in `tests/timed_run.py` keep working, and the timed run is extended at the next station, not here.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened

---

## Change Summary

A project gains a Summary view beside its Tasks view: both carry a Tasks and a Summary link and a title naming the view, and the Summary shows the project's counts (FDR R-96 to R-99) as plain numbers, an empty project showing zeros and inviting a first task. The counts are computed in a new `domain/summary.py`.

Sizing (`pm_right_size.md`): one capability, opening a project's summary and reading its counts, accepted by FDR R-96 to R-99, SRS FR-38 and UXD UX-F6/UX-S5 less the linked counts. The title, the link pair and the tests the records require (CP-507 to CP-510) are that capability's own entry point and proof. One merge.

---

## Rules

The product's location is `project.md` `Product path:`; paths below are relative to it.

### The two views
- **CP-490:** A project has two views. **Tasks** is the project page the tracker shows today, at the address it has today. **Summary** is a page of its own, with an address of its own (SDD § 4 EX-3). The address's form is not fixed here.
- **CP-491:** Both views show the project's name, exactly as saved, as the page heading. Under the heading sit two links, `Tasks` then `Summary` (UXD § 4: "switched by a link pair under the project's name"). `Tasks` opens the project's Tasks view with no filter or sort chosen. `Summary` opens its Summary view. Both links appear on every page either view shows: the plain list, an empty project, a filtered or sorted list, the page after an action, a refusal, and a move confirmation.
- **CP-492:** Every page of the Tasks view is titled `{name}: Tasks - tracker17`. The Summary view is titled `{name}: Summary - tracker17`. `{name}` is the project name exactly as saved, surrounding spaces included (FDR R-80). Every other page keeps its title as it is today: a task page stays `{task title} - tracker17`.
- **CP-493:** After a rename, both views keep their addresses and show the new name in heading and title (FDR R-35).
- **CP-494:** The Summary view has the header every page carries (SDD § 4 EX-12). It has no form and no control that changes data: no add-task form, no filter or sort controls, and no rename or delete control. Opening it, following its links or reloading it changes nothing (FDR R-106). It shows the data as it was when the page loaded and never updates itself (FDR R-101). Reached by a link, it opens at its start (SDD § 4 EX-5).
- **CP-495:** A Summary address for a project that does not exist shows the not-found page that a missing project's Tasks address shows today, titled `Not found - tracker17` (FDR R-105; UXD UX-S5 Error).

### The counts
- **CP-496:** The Summary counts only this project's tasks. It shows these rows, in this order: the total; one row per status in the order `todo`, `in-progress`, `done`, `cancelled`; one row per priority in the order `low`, `medium`, `high`, `critical`; the overdue count; and the count of tasks with no due date. Every status and priority row appears, even with a count of zero (FDR R-96). A status or priority row is labelled with its word exactly as written. The labels of the total, overdue and no-due-date rows are written to `docs/CONTENT.md` and are not fixed here. Every count is a numeral, and zero shows as `0` (CONTENT.md § Numbers). The total equals the sum of the four status counts and also the sum of the four priority counts.
- **CP-497:** The overdue count is the number of this project's tasks that are overdue under FDR R-68. "Today" is the machine's local date when the tracker builds the Summary (FDR R-69). For the same task on the same day, the Summary counts it as overdue exactly when the list marks it `Overdue` and the overdue filter returns it (FDR R-99).
- **CP-498:** The no-due-date count is the number of this project's tasks that have no due date, whatever their status.

### Open tasks per assignee
- **CP-499:** An open task is one whose status is neither `done` nor `cancelled`. The per-assignee part has exactly these rows (FDR R-97, R-98):
  - one row for each name on the current assignee list, including a name with no open task here (its count is `0`);
  - one row for each name **not** on the list that at least one open task in **this** project carries;
  - always one row labelled `(unassigned)`, counting this project's open tasks that have no assignee.

  An unlisted name gets no row when only `done` or `cancelled` tasks of this project carry it, or only tasks in other projects. A row's count is the number of this project's open tasks carrying that exact name, compared exactly as FDR R-58 compares names. A name row is labelled with the name exactly as saved.
- **CP-500:** The order of the per-assignee rows: first the listed names, in the order the People page lists them; then the unlisted names, alphabetically ignoring letter case, with names that differ only in case ordered by their exact text; and `(unassigned)` last.
- **CP-501:** Text the operator typed shows as text on the Summary and in its title. A project name or an assignee name containing `<`, `&` or `"` displays exactly as typed and changes nothing around it (FDR R-112).

### A project with no tasks
- **CP-502:** On a project with no tasks, the Summary shows every row CP-496 and CP-499 name with `0`: the total, the four statuses, the four priorities, overdue, no due date, each listed name, and `(unassigned)`. Beside them it shows a line saying the project has no tasks yet. The line invites a first task and links to the project's Tasks view, where tasks are added (UXD UX-S5 Empty). Its words are written to CONTENT.md § Empty. The Tasks view's own no-tasks line, `This project has no tasks yet. Give the first task a title and press Add.`, stays as it is.

### Plain numbers
- **CP-503:** No count and no row label on the Summary is a link. The Summary's only links are the header's links, the `Tasks` and `Summary` links of CP-491, and, on a project with no tasks, CP-502's link to the Tasks view.

### Where the rule lives, and the fences on it
- **CP-504:** The counts are computed in `domain/summary.py`, the Project summary entry point named by SDD § 4 TS-3's `summary` row and required by NFDR QC-11. Its opening docstring names SRS FR-38 and the other requirements it realizes, every `application` and `web` module that takes part, and the test modules that check it. `summary` is listed as landed in the pointer test (SDD § 4 TS-4; NFDR QC-11). Every test module the change adds names the requirements or acceptance criteria it checks (NFDR QC-11).
- **CP-505:** No second copy of the overdue, filter or sort rules. The Summary's overdue count is decided by the overdue rule that the list marking and the overdue filter already use, and its counts reuse the rules `domain/filtering.py` holds rather than restating them (the request; SDD § 2, whose rejected "one module per screen" option names the cost: "Each copy can drift from the others").
- **CP-506:** `domain/summary.py` stays inside the fences checked over `domain/` at layer 6. It imports only `domain`, `errors` and the standard library (NFDR QC-13). It does no input or output and reads no clock, so today arrives as an argument (NFDR QC-20, QC-44). It builds no HTML and holds no wording shown to the operator (NFDR QC-20). Each of its dataclasses is frozen (NFDR QC-6). The change passes NFDR QC-62's Ruff format check, Ruff lint and mypy.

### The tests the records require
- **CP-507:** A summary test checks SRS AC-14's summary half and SDD § 6 S-6. It runs at layer 1, with no file and no clock (SDD § 4 TS-1). It builds one project with tasks in each of the four statuses and each of the four priorities, an overdue task, a task with no due date, an open task assigned to a listed name, a listed name with no open task, an open task carrying a name no longer on the list, and an unassigned open task. A second project holds tasks too. The test asserts every count and every per-assignee row the Summary shows, and their order, and that the second project's tasks are counted nowhere.
- **CP-508:** An overdue-agreement test covers SRS AC-13's three cases for the Summary (SDD § 6 S-6 *Command*). Today's date is set by a clock handed in, never by patching a product module (NFDR QC-28). The project holds an open task due yesterday, an open task due today, and one task due yesterday in each of `done` and `cancelled`. The list marks only the first `Overdue`, the overdue filter returns only the first, and the Summary's overdue count is `1`.
- **CP-509:** `python3 tests/timed_run.py` times opening a project's Summary at NFDR QC-48's volume (1,000 tasks, 20 comments each). It appends the Summary's lines after every existing line, and each existing line keeps its label and its place. The run exits 0 only when the Summary shows its result within 1 second, the page answered is that project's Summary, and the saved data is unchanged (NFDR QC-48; SDD § 4 TS-5; SRS NFR-1 lists "opening a summary").
- **CP-510:** The route test of NFDR QC-7 (`tests/integration/test_routes.py`, `test_every_route_leaves_state_and_headers_as_the_rules_say`) covers the Summary's address. It is answered as a page, leaves the state unchanged and sets no cookie (NFDR QC-7, QC-8). It carries the `Content-Security-Policy` header with `frame-ancestors 'none'` (NFDR QC-33) and the policy that loads only from the tracker's own address and runs no script (NFDR QC-34; ADR-0003).
- **CP-511:** One end-to-end test drives the running tracker in the browser (SDD § 4 TS-1, layer 5). On `Alpha`'s Tasks view it follows `Summary`. There it finds the title `Alpha: Summary - tracker17`, the counts as plain numbers and both links, and it follows `Tasks` back to the title `Alpha: Tasks - tracker17`. It also opens an empty project's Summary and finds the zeros and the first-task line.

### Use of the page
- **CP-512:** The Summary meets SDD § 4 EX-9. It has a title and the page language, and status, priority and the overdue count are words and numerals. At 400% zoom of a 1280-pixel-wide window it reads without scrolling in two directions (UXD UX-A7 names the summary as not exempt). The `Tasks` and `Summary` links work from the keyboard and show when they have focus (SDD § 4 EX-8). They meet UXD UX-A6's 24 by 24 CSS pixel target floor or an exception WCAG 2.2 SC 2.5.8 names.

---

## Examples

| Scenario | Expected behavior | Rule |
|---|---|---|
| Project `Alpha` (id 1), the operator opens its Tasks view | Heading `Alpha`, links `Tasks` then `Summary` under it, title `Alpha: Tasks - tracker17` | CP-490, CP-491, CP-492 |
| On `Alpha`'s Tasks view with status filter `todo` applied, the operator follows `Tasks` | The Tasks view opens with no filter or sort chosen | CP-491 |
| The operator follows `Summary` on `Alpha` | Title `Alpha: Summary - tracker17`, heading `Alpha`, both links, the header, no form, opened at its start | CP-491, CP-492, CP-494 |
| Project named `  Alpha  ` (two spaces each side) | Titles `  Alpha  : Tasks - tracker17` and `  Alpha  : Summary - tracker17` | CP-492 |
| A task page | Title unchanged, `{task title} - tracker17` | CP-492 |
| `Alpha` renamed to `Beta`, the operator reloads the old Summary address | The same project's Summary, heading `Beta`, title `Beta: Summary - tracker17` | CP-493 |
| The operator reloads the Summary three times | Nothing saved, nothing changes | CP-494, CP-510 |
| Summary address for a project id nothing holds | The not-found page, `Not found - tracker17` | CP-495 |
| Today 2026-10-28. `Alpha` holds: T1 `todo`/`low` due 2026-10-27, unassigned; T2 `in-progress`/`medium` no due date, `ari` (listed); T3 `done`/`high` due 2026-10-01, `ari`; T4 `cancelled`/`critical` no due date, `dan` (removed from the list); T5 `todo`/`critical` due 2026-10-28, `eve` (removed from the list). List: `ari`, `bo`. `Beta` holds one `todo` task assigned to `bo` | Total 5 · `todo` 2, `in-progress` 1, `done` 1, `cancelled` 1 · `low` 1, `medium` 1, `high` 1, `critical` 2 · overdue 1 (T1) · no due date 2 (T2, T4) · rows: `ari` 1, `bo` 0, `eve` 1, `(unassigned)` 1. No `dan` row, because only a cancelled task carries `dan`. `Beta`'s task counts nowhere | CP-496, CP-497, CP-498, CP-499, CP-507 |
| The same `Alpha` | Total 5 = 2+1+1+1 (statuses) = 1+1+1+2 (priorities) | CP-496 |
| Unlisted names `zed`, `Amy`, `amy` on open tasks; list `ari`, `bo` in that order on People | Row order `ari`, `bo`, `Amy`, `amy`, `zed`, `(unassigned)` | CP-500 |
| Today 2026-10-28: open A due 2026-10-27, open B due 2026-10-28, C `done` and D `cancelled` both due 2026-10-27 | The list marks only A, the overdue filter returns only A, and the Summary shows overdue `1` | CP-497, CP-508 |
| Assignee `<b>&"x"` on an open task, project named `a&b` | Row label `<b>&"x"` as typed, title `a&b: Summary - tracker17` as typed | CP-501 |
| Empty project `Gamma`, list `ari` | Every status, priority, total, overdue and no-due-date row `0`; rows `ari` 0 and `(unassigned)` 0; a no-tasks line with a link to the Tasks view | CP-502 |
| Empty project's Tasks view | Unchanged no-tasks line `This project has no tasks yet. Give the first task a title and press Add.` | CP-502 |
| Any Summary | No count or row label is a link | CP-503 |
| `pytest products/tracker17/tests/` after the change | Exits 0, and the pointer test lists `summary` as landed | CP-504, CP-506, CP-507, CP-508, CP-510, CP-511 |
| The overdue count and the list marking for one task on one day | Decided by the one overdue rule, so they cannot disagree | CP-505, CP-497 |
| `python3 tests/timed_run.py` | Every earlier line in its place, then the Summary lines; exits 0 under 1 second | CP-509 |
| Browser at 400% zoom, 1280-pixel window, on a Summary | Reads without two-direction scrolling | CP-512 |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| The project page is titled `{project.name} - tracker17` today (CP-492) | Read `web/pages.py:1506` | `return _document(f"{project.name} - tracker17", body)` |
| The project page carries no Tasks or Summary link today (CP-491) | `grep -n -i summary web/pages.py` | No match |
| The Tasks view's no-tasks line today (CP-502) | Read `web/pages.py:1008-1009` | `This project has no tasks yet. ` `Give the first task a title and press Add.` |
| The overdue rule exists once. The list marking and the filter both use it (CP-505) | Read `domain/due_dates.py:44-46`, `application/tracker.py:253,325`, `domain/filtering.py:33` | `is_overdue(due_date, status, today)`. The tracker's list rows call it, and filtering imports it |
| The People page lists names earliest added first (CP-500) | Read `domain/assignees.py:52-66` and `application/tracker.py:140-142` | `add_assignee` appends at the end. `list_assignees` returns them "earliest added first" |
| Two tests pin the project page's title (Locked Answer f-1) | `grep -rn -- '- tracker17' tests`, each hit read in place | `tests/integration/test_pages.py:224` (`test_a_project_page_shows_name_description_the_invitation_and_only_the_add_form`, `"  Alpha   - tracker17"`) and `tests/integration/test_task_pages.py:145` (`test_form_is_present_for_empty_and_populated_projects`, `"Alpha - tracker17"`). The other title hits (`test_task_pages.py:293,382`, `tests/e2e/test_tasks.py:93,128`) are task pages, which CP-492 leaves unchanged |
| The every-page header test allows only four link targets (Locked Answer f-2) | Read `tests/integration/test_pages.py:159-174` | Every link's `href` must fullmatch `/|/tasks|/people|/projects/\d+` |
| The route test's sample addresses must equal the route set (Locked Answer f-3) | Read `tests/integration/test_routes.py:268-305` | `assert {route.pattern for route in ROUTES} == set(SAMPLE_ADDRESS)` |
| The whole timed run pins its exact label list (Locked Answer f-4) | Read `tests/integration/test_timed_run.py:2112-2123`; `tests/timed_run.py:1-5` | Labels must equal the old, new, move, filter and sort blocks, no more. The run times no summary |
| Adding `domain/summary.py` fails three architecture tests, and listing `summary` as landed clears two of them (CP-504, Locked Answer f-5) | Disposable clone at `48322fde7`, `pytest -q products/tracker17/tests/architecture`, on the real tree with no harness swapped in | Baseline: 60 passed. With a stand-in `domain/summary.py`: 3 failed (`test_shapes.py::test_only_the_task_features_are_added_to_domain`, `test_trace.py::test_each_feature_word_with_its_domain_module_is_listed_as_landed`, `test_trace.py::test_no_excluded_feature_entry_exists`). With `summary` added to `LANDED_FEATURE_WORDS` and a docstring that names real paths and FR-38: 1 failed, `test_only_the_task_features_are_added_to_domain`, which asserts `not (domain / "summary.py").exists()` at `tests/architecture/test_shapes.py:193` |
| The browser tests' link locators do not collide with the new `Tasks` and `Summary` links (CP-491) | `grep -rhn 'get_by_role("link"' tests/e2e` | Only `name="All tasks"`, `name="Alpha"` and `name="Projects"`. None is a substring of `Tasks` or `Summary` |
| The All tasks page shows no "summary" text (Out of Scope, summary across projects) | Read `tests/integration/test_sort_pages.py:397-399` | Asserts `summary` is absent from All tasks. The test stays as it is |
| With unreadable saved data the tracker serves no page (Out of Scope, record gap) | Read `main.py:39-48` | On `UnreadableData` it prints the message and `return 1`. The tracker never starts |

Language rendering: no rule pins output that renders a language-level fact. Status and priority words, counts, names and titles are values the product chooses, so no rendering row is owed.

---

## Out of Scope

- **Counts as links into filtered lists.** UXD UX-F6 and UX-S5 make every status count, priority count and the overdue count a link to the project's list filtered to that value. SDD § 6 S-6 *Reached when* says the same, and CONTENT.md gives a number link its accessible name ("12 tasks in todo"). The request rules this out: "the counts stay plain numbers with no count linking anywhere, since the links into filtered lists are the next station (`linked-counts`)". The product has no Summary today (`grep -n -i summary web/pages.py`, no match). Parked in `deferred_decisions.md` as a record gap.
- **The unreadable-saved-data page for the Summary.** FDR R-25 and R-26 and UXD UX-S9 have every page say the saved data could not be read. Today the tracker refuses to start on unreadable data and serves no page (`main.py:39-48`). That is a mode the product never enters, and this change leaves it as it is. Parked in `deferred_decisions.md` as a record gap.
- A summary across projects (FDR OOS-10). All tasks gains no Summary link and no summary.
- Any change to the assignee name rules. A listed name typed as `(unassigned)` stays allowed (Locked Answer b-5).
- Sorting, filtering or choosing a date for the Summary. Its overdue count is always as of today.
- Any page title other than the two views' titles, and any existing page's strings beyond those titles and the new link pair.

---

## Locked Answers (the divergence record — self-review 2026-10-28)

- **(e-1) CP-508, the AC-13 agreement test.** The request is silent on it, and the station puts it on `linked-counts`. SDD § 6 S-6 *Command* requires "the overdue count agreeing with the marking and the filter on AC-13's three cases", and NFDR QC-28 says those tests set today through a clock handed in. The subject is the Summary's overdue count, which this change adds, so the check binds this change now.
- **(e-2) CP-509, the timed run.** The request defers it explicitly: "the timed run is extended at the next station, not here". NFDR QC-48 and SDD § 4 TS-5 say "a change that adds a listed action adds it to the run", and SRS NFR-1 lists "opening a summary". This change adds that action, so the check folds in against the deferral. The request's own guardrail still holds, because every existing timed action keeps its label and place.
- **(e-3) CP-504, CP-506, CP-510, CP-512, the record checks on the new module and page.** The request names none of them. NFDR QC-6, QC-11, QC-13, QC-20, QC-44 and QC-62, the route checks QC-7, QC-8, QC-33 and QC-34, and SDD § 4 EX-8 and EX-9 with UXD UX-A6 and UX-A7 each bind a module or page this change adds.
- **(b-1) CP-491, link order and target.** The request says "a Tasks and a Summary link". The order is locked as `Tasks` then `Summary`, Tasks being the default view (UXD § 4). `Tasks` opens the list with no filter or sort chosen. Both choices are reversible and change no data. They match the All tasks project links, which open a project with no choice in the address.
- **(b-2) CP-496, CP-500, row order.** The request fixes the rows and not their order. Statuses follow the workflow's order from `todo` to the final statuses, as the request lists the four. Priorities follow the request's own order, which is FDR R-90's ascending order. For assignees, the listed names come in the order the People page shows the operator, then the unlisted names alphabetically ignoring case, with exact text breaking a tie so the order is the same every time, and `(unassigned)` last. Every key is something the page prints, and each choice can be changed later without touching data.
- **(b-3) CP-498, the no-due-date count counts every status.** FR-38 says "the count of tasks with no due date" with no "open" qualifier, while it qualifies the per-assignee part with "open". The rule reads it as written.
- **(b-4) CP-511, one browser test.** The request's done-when is the running app ("opening `Alpha`'s Summary in the running app shows…"), and SRS NFR-11 with SDD § 4 TS-1 puts that check at the end-to-end layer. The test is additive.
- **(b-5) A listed name typed `(unassigned)`.** Assignee names allow it (FDR R-58), so the Summary may show two rows that read `(unassigned)`. The rule keeps both rows, because FR-38 requires each, and the real unassigned row is always last (CP-500). Refusing that name would change the assignee rules, which this change leaves alone.
- **(f-1) `tests/integration/test_pages.py::test_a_project_page_shows_name_description_the_invitation_and_only_the_add_form` and `tests/integration/test_task_pages.py::test_form_is_present_for_empty_and_populated_projects` change.** CP-492, which the request asks for, retitles the project page. Each test keeps asserting exactly one `<title>`, now `  Alpha  : Tasks - tracker17` and `Alpha: Tasks - tracker17`, with the name's spaces kept.
- **(f-2) `tests/integration/test_pages.py::test_every_page_has_a_header_with_the_projects_and_people_links` changes.** CP-491's Summary link has an address outside the four the test allows. The test keeps asserting the header's three links on every page it builds, that every link opens one of the tracker's own addresses (now including the project's Summary address), and that no page says "rename" or "delete".
- **(f-3) `tests/integration/test_routes.py::test_every_route_leaves_state_and_headers_as_the_rules_say` changes when the Summary has a route of its own.** It gains a sample address for that route. It keeps asserting that the route set equals the sample set and every header and state rule it checks today (CP-510).
- **(f-4) `tests/integration/test_timed_run.py::test_timed_run_appends_exactly_three_ordered_action_blocks` changes.** CP-509, folded in under (e-2), adds the Summary block. The test keeps asserting status 0, every earlier block's labels in their places followed by the Summary's, and no "over" or "refused" line.
- **(f-5) `tests/architecture/test_shapes.py::test_only_the_task_features_are_added_to_domain` changes.** The request's `domain/summary.py` breaks its `assert not (domain / "summary.py").exists()`. The test keeps asserting that every landed feature module exists, now with `summary` among them, that no later feature module exists, and that the state holds exactly its saved fields. `LANDED_FEATURE_WORDS` in `tests/architecture/test_trace.py` gains `summary` (CP-504).
