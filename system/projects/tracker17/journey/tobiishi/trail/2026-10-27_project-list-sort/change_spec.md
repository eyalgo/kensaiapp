# Change Spec — a project's task list sorts by one field

**Date:** 2026-10-27
**Category:** feature
**Behaviour:** changing
**Request:** Let the operator sort a project's task list by one field. Beside the filter controls the list gains a sort field (due date, priority, created time, title) and a direction (ascending or descending, ascending when none is chosen). Apply shows the matches sorted, with their count and the choices still shown, and the sort choice appears in the address together with any filter, so a reload shows the same list; a sort applied over a filter keeps the filter's matches. Clear returns to every task in due-date ascending order. The rules live in a new `domain/sorting.py` (SDD § 4 TS-3): priority ascending runs `low`, `medium`, `high`, `critical` and descending the reverse (R-90); undated tasks come last in a due-date sort in either direction (R-91); title is alphabetical and ignores letter case (R-92); tasks equal on the chosen field keep creation order, and a created-time sort follows it, so tasks with the same recorded creation time come out in the same order on every request (R-93, FR-36). Extend `tests/timed_run.py` to time one sort, in the run's existing manner and beside the existing `filter total at 1000 tasks` line (the 1,000-task fixture, a failure on a refused or failed action, POST/GET and total each under `LIMIT_SECONDS`, 1.0 second), and print the fixture used. Done when `domain/sorting.py` exists; in a browser or through `web` each sort field in each direction shows the tasks in the order FR-36 defines, with the count and the choice still shown, and no direction chosen sorts ascending; the choice rides the address with the filter and a reload keeps the list; Clear shows every task in due-date ascending order; `pytest products/tracker17/tests/` exits 0, including SRS AC-14's sort tests (each field in both directions, the priority order, undated last, the tie and created-time cases); and `python3 products/tracker17/tests/timed_run.py` exits 0 and shows a timed sort under 1.0 second. Sizing: the acceptance boundary is one capability, sorting a project's list (station reached-when 1–6, SRS FR-36, FDR R-90 to R-93), and it maps to one merge that rides the filter's Apply, Clear and address; the All tasks list and the project summary are later stations and are not here. What must not be weakened: no All tasks list or header link and no summary; the filter's rules and behaviour stay as they are; the limit and every existing timed action and test stay as they are; the list sorts by one field only, and the choice lives in the address and is not remembered between sittings (UX-I7).
**Language resolution:** Python — step 1 (`project.md` `Languages:`) — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with every concern it routes

---

## Change Summary

A project's task list gains a sort field and a direction beside the filter controls. Apply orders the
list, filtered or not, by the field chosen, keeps the choice in the controls and the address, and Clear
returns to the default order. The timed run times one sort.

Paths below are relative to the product root, which `system/projects/tracker17/project.md`
`Product path:` names. `SRS`, `SDD`, `UXD`, `FDR`, `NFDR` and `CONTENT.md` are the product's
documents under `docs/`.

**Sizing.** One capability, sorting one project's list (SRS FR-36; SDD § 6 S-5, its sorting half).
Every rule below is that capability, its refusals, its effect on a move pressed on a sorted list, or a
check a record requires of it. One merge.

---

## Rules

### The sort controls

- **CP-426:** A project's page whose project has at least one task shows two more controls with the
  filter's, after its seven fields and before Apply and Clear: Sort by, offering Due date, Priority,
  Created time and Title; and Direction, offering Ascending and Descending. Each has a visible label.
  One Apply applies the filter and the sort together, and one Clear clears both. A project with no tasks
  shows no controls, as today (CP-393). *(SRS FR-36; FDR R-89; UXD UX-F5, UX-S4)*
- **CP-427:** Each sort control takes one value, or none (FDR OOS-8). Its words follow `docs/CONTENT.md`
  (SDD § 4 EX-11), and applying a sort shows no message (`CONTENT.md` § Voice, "A reading action, such
  as applying a filter … produces no message"). The wording belongs to the content stage.

### The order

- **CP-428:** With no Sort by chosen the field is due date, and with no Direction chosen the direction is
  ascending. A list whose address carries no sort choice shows in due-date ascending order, which is the
  order the list shows today. *(SRS FR-36; FDR R-89; UXD UX-F5 Defaults)*
- **CP-429:** Due date: ascending puts the earliest due first, descending the latest due first. Tasks with
  no due date come last in both directions. *(FDR R-91)*
- **CP-430:** Priority: ascending runs `low`, `medium`, `high`, `critical`, and descending runs
  `critical`, `high`, `medium`, `low`. *(FDR R-90)*
- **CP-431:** Title: titles are compared with letter case set aside by Unicode case folding, so `Alpha`,
  `alpha` and `ALPHA` are equal, and so are `Straße` and `STRASSE`, and otherwise character by character
  in Unicode code-point order. Ascending runs that order,
  descending its reverse. Digits compare as characters: ascending puts `Task 10` before `Task 2`.
  *(FDR R-92)*
- **CP-432:** Created time: ascending runs in creation order, oldest first, and descending newest first,
  realized as ascending and descending task number in each title link's address. The order is creation
  order, never the recorded creation time: two tasks with the same recorded time, or with recorded times
  out of step with the order they were created in, still come out in creation order. *(SRS FR-36; FDR
  R-43, R-93; ADR-0008)*
- **CP-433:** Tasks equal on the chosen field keep creation order, oldest first, realized as ascending
  task number, in both directions. Equal means the same due date, or both undated; the same priority;
  or titles equal under CP-431. The same address against the same saved data shows the same order on
  every request. *(SRS FR-36, AC-14; FDR R-93)*
- **CP-434:** A sort applied with a filter lists exactly the tasks the filter matches (CP-396, unchanged),
  in the sort's order. A sort never adds or removes a task. *(Request; UXD UX-F5)*

### The count, the address and Clear

- **CP-435:** A sort choice is a Sort by or Direction value in the list page's address that is not empty.
  With a filter field set or a sort choice, the page shows the number of tasks it lists, and every
  control shows the choice applied. The page opens at its start. With a sort choice and no filter field
  set, the number is every task of the project, and its words do not say a filter is applied. The
  wording belongs to the content stage. *(Request; UXD UX-F5, UX-S4; SDD § 4 EX-5)*
- **CP-436:** With no sort choice, Sort by shows Due date and Direction shows Ascending, the order the
  list is in. With a Direction chosen and no Sort by, Sort by shows Due date. *(UXD UX-F5 Defaults)*
- **CP-437:** The sort choices are carried in the list page's address with the filter's and stored
  nowhere else. Opening that address again — a reload, Back, a bookmark — shows the same list in the
  same order, worked out against the saved data at that moment. Apply, its reload and Clear are reads,
  each answered with the page, 200, and no redirect, and none changes the saved data. *(FDR R-94, R-101,
  R-106; UXD UX-I7; SDD § 4 EX-3; ADR-0011; NFDR QC-7)*
- **CP-438:** Clear shows every task of the project in due-date ascending order (CP-428, CP-429,
  CP-433), the filter controls at no value, the sort controls as CP-436 states, no count, and an address
  carrying no choice. *(Request; UXD UX-F5)*

### A move pressed on a sorted list

- **CP-439:** Every move interaction CP-407 names, pressed in a row of a list whose address carries a sort
  choice, lands on that list with the same filter and sort choices, shown in the controls and carried in
  the address, in the same order. On a list with no sort choice each behaves as today. These landings
  keep NFDR QC-63's response contract: 202 for a page showing a pending confirmation, 200 for every
  other, each with `Cache-Control: no-store`. CP-408 and CP-409 are unchanged. *(UXD UX-F4, UX-I7; NFDR
  QC-63; SDD § 4 RT-11)*
- **CP-440:** A move pressed on a list whose sort choice would be refused under CP-441 saves nothing and
  opens no confirmation, and lands on that list showing the refusal, as a move on a list with a refused
  filter choice does today (`web/routes.py:799-806`). *(FDR R-100; NFDR QC-38)*

### Refusals

- **CP-441:** A Sort by or Direction value no control sends is refused with a reason at its field. The
  class is closed by field: a value outside the ones the control offers, and a field given more than one
  value. *(Request, "the list sorts by one field only"; FDR R-100; SRS FR-39)*
- **CP-442:** On a refusal of CP-441, alone or with a filter refusal, CP-405 applies: the saved data is
  unchanged and no task list result is shown; the controls hold the choices as sent, and each refused
  field shows its own reason beside it; the page opens with keyboard focus on the first refused field in
  the controls' order — the filter's seven fields, then Sort by, then Direction — with its reason as the
  field's accessible description; Clear is in view. *(SRS FR-39; FDR R-100; SDD § 4 EX-4, EX-14; UXD
  UX-I3)*
- **CP-443:** Each refused condition this change adds has its own refusal type, defined and raised in
  `domain` and handed to `web` through `application`. `web` maps each type to its reason, and no part
  tells one refusal from another by reading its message. *(NFDR QC-5, QC-16; SDD § 4 OB-4)*

### Either way in

- **CP-444:** A sort address for a project that does not exist shows the not-found page, as an address
  for a missing project does today. *(FDR R-105; SDD § 4 EX-13)*
- **CP-445:** Choosing a sort and applying it can be done from the keyboard alone with the browser's own
  keys, on a page that runs no script. A title holding `<`, `&` or `"` shows as typed in a sorted list
  and takes its place by CP-431. *(FDR R-112, R-113; SDD § 4 EX-2, EX-8; ADR-0003; NFDR QC-34, QC-36)*

### Where the code lives (fixed by the records)

- **CP-446:** The sort rules — the order of CP-428 to CP-433 and the refusals of CP-441 — live in a new
  module, `domain/sorting.py`. `application` applies them and holds no rule of its own, and `web` holds
  no sort rule (SDD § 4 TS-3; NFDR QC-11, QC-20, QC-21, QC-23). The opening docstring of
  `domain/sorting.py` names the SRS requirements it realizes, FR-36 among them, every `application` and
  `web` module that takes part, and the test modules that check it. The word `sorting` is listed as
  landed in the pointer test, `tests/architecture/test_trace.py`. Every test module the change adds
  names the requirements or acceptance criteria it checks. *(SDD § 4 TS-3, TS-4; NFDR QC-11)*
- **CP-447:** The change adds no saved field and no cookie. Applying, reloading or clearing a sort never
  reaches the saver. *(FDR R-94; NFDR QC-8, QC-21, QC-46, QC-54)*

### Tests (named in the request, or required by the records)

- **CP-448:** Unit tests cover `domain/sorting.py` with no file and no clock: each field in both
  directions; the priority order; undated tasks last by due date in both directions; titles ignoring
  case, FDR's `beta`, `Alpha`, `alpha` example among them, in both directions; a tie on each field in
  both directions; a created-time sort over two tasks with the same recorded creation time, and over two
  whose recorded times are out of step with their creation order; no Sort by and no Direction; and each
  kind of CP-441 refusal. *(SRS AC-14, AC-12; SDD § 4 TS-1)*
- **CP-449:** Layer-3 and layer-4 tests run in one process with the clock and the saver handed in, and
  cover:
  - the sort controls and their offered choices on a project with tasks, and none on a project with
    none (CP-426);
  - each field in both directions through `web`, with the count and the choices shown (CP-429 to
    CP-433, CP-435);
  - a sort with no field or no direction chosen (CP-428, CP-436);
  - a sort over a filter (CP-434);
  - the same list from the same address opened again, and Clear (CP-437, CP-438);
  - one test per refusal kind of CP-441, each asserting the reason shown, the focus, and the saved data
    unchanged (CP-442);
  - a move from a sorted list keeping the choices, for each interaction CP-439 names, with its status
    code and `Cache-Control: no-store`, and a move from a list with a refused sort choice (CP-440);
  - a title holding `<`, `&` and `"` in a sorted list (CP-445).

  *(Request; SRS AC-12, AC-14; NFDR QC-5, QC-38, QC-63)*
- **CP-450:** The tests NFDR QC-7, QC-35 and QC-54 name cover a sort: the route test's Apply, reload and
  Clear carry a sort choice and find 200, nothing saved and no `Set-Cookie`; the outbound-connection
  test drives an Apply with a sort choice; and a recording-saver test applies a sort and finds the saver
  received nothing. *(NFDR QC-7, QC-8, QC-35, QC-54)*
- **CP-451:** `python3 tests/timed_run.py`, run from the product root, times one sort on a fixture of its
  own: 1,000 tasks in one project with 20 comments on every task, at ordinary text lengths, saved in a
  location of its own inside the run's temporary directory and distinct from every other fixture. The
  sort is Priority, Descending, with no filter field set, so it lists all 1,000 tasks. Its requests are
  marked `Sec-Fetch-Site: same-origin`, as a press on the page is. The product's own `data/` is as the
  run found it. *(Request; NFDR QC-48, QC-32; SDD § 4 TS-5)*
- **CP-452:** The run prints every line it prints today, unchanged and in today's order, the last being
  the `filter total at 1000 tasks: …` row. After them it prints exactly four more, in this order, and
  nothing after them:
  1. `sort fixture: {tasks} tasks, {per task} comments each ({all} in all); title of {T} characters, comment of {C} characters; sort priority descending, {N} listed`
  2. `sort a task list at 1000 tasks: {ms} ms{problems}`
  3. `sort landing page at 1000 tasks: {ms} ms{problems}`
  4. `sort total at 1000 tasks: {ms} ms{problems}`

  `{tasks}`, `{per task}` and `{all}` are read from the fixture as loaded, as the filter's fixture line
  reads them. `{T}` and `{C}` are the lengths, in code points, of the title and the first comment of the
  first task the sorted list shows. `{N}` is the number of the fixture's tasks in the project. `{ms}` and
  `{problems}` are written as every existing row writes them.
- **CP-453:** Row 2 times the request the Apply press sends. Row 3 times a request for the sorted list's
  address, the one a reload opens. Row 4 is their sum. Each must be under `LIMIT_SECONDS`, 1.0 second,
  which stays as it is.
- **CP-454:** The sort counts only when it happened. Row 2 fails when Apply is answered with a refusal or
  a failure. Row 3 fails unless its page answers 200 and lists each of the `{N}` tasks exactly once, in
  the order CP-430 and CP-433 give for priority descending, with the count `{N}`; that order is worked
  out in the run from the loaded fixture by a plain comparison of priority and task number, never by the
  product's sort. Row 4 fails when either does. When Row 2 fails, Row 3 is not requested, reads `0.0 ms —
  refused or failed`, and Row 4 is Row 2's time with the same problem. The run fails, non-zero, on any
  failing row, and when the fixture's saved data is not byte for byte what it was before the sort.
  *(Request; NFDR QC-48)*
- **CP-455:** Tests in `tests/integration/test_timed_run.py` feed the sort harness a refused Apply, a
  landing listing every task with two out of order, and a landing missing one task, and find each verdict
  non-zero; a slow Apply, a slow landing, and a total at 1.0 second with both parts under it, each
  failing its rows; and a test on the CP-452 fixture line, read from a fixture other than the run's own.
  *(SDD § 4 TS-1; SRS C-6)*
- **CP-456:** Existing tests that encode what this change reverses change only there, and each keeps
  every other assertion:
  - `test_only_the_task_features_are_added_to_domain` in `tests/architecture/test_shapes.py` stops
    asserting that `domain/sorting.py` does not exist. Its `summary` absence, its landed modules and its
    `TrackerState` fields stay.
  - The 28 tests in `tests/integration/test_timed_run.py` that Verified Claims lists change by the
    readings the sort takes: 21 hand `main` a fixed list of timer readings, and 7 use the `whole_run`
    fixture. Of those 7, the two that assert the whole run's lines in order,
    `test_timed_run_appends_exactly_three_ordered_action_blocks` and
    `test_timed_run_appends_exact_move_block_and_nothing_after`, also change by the four lines of CP-452
    after the filter block.

  No other existing test is changed to fit, and no existing timed action, bar or test is loosened,
  deleted or skipped. *(Request, "every existing timed action and test stay as they are")*
- **CP-457:** These exit 0:
  - `pytest products/tracker17/tests/`, run in a fresh clone checked out at the commit under test
    (`<CORE>/roles/CROSS_ROLE.md` § Every seat; NFDR QC-47);
  - `pytest products/tracker17/tests/e2e/`, where layer 5 runs (NFDR § 9; SDD § 4 TS-1);
  - `python3 tests/timed_run.py` from the product root (NFDR QC-48);
  - from the product root, `ruff format --check .`, `ruff check .` and
    `mypy main.py errors.py domain application persistence web` (NFDR QC-62).
- **CP-458:** The code and tests this change writes run on Python 3.11. *(NFDR QC-60; SDD § 4 RT-1)*

---

## Examples

| Scenario | Expected behavior | Rule |
|---|---|---|
| Project with 3 tasks; its page is opened | The filter's seven fields, then Sort by and Direction, then Apply and Clear, each labelled. Sort by shows Due date, Direction Ascending. No count. | CP-426, CP-436 |
| Project with no tasks; its address carries a sort choice | Today's page: the first-task invitation and the add form. No controls. | CP-426 |
| A sort is applied | No "applied" message. | CP-427 |
| Address carries Sort by Priority and no Direction | Priority ascending, Direction shows Ascending. | CP-428, CP-430 |
| Address carries Direction Descending and no Sort by | Due date descending, Sort by shows Due date. | CP-428, CP-436 |
| Due date descending; tasks due 2026-10-01, 2026-10-09 and none | 2026-10-09, then 2026-10-01, then the undated task. | CP-429 |
| Due date ascending; same tasks | 2026-10-01, then 2026-10-09, then the undated task. | CP-429 |
| Priority ascending; tasks `high`, `low`, `critical`, `medium` | `low`, `medium`, `high`, `critical`. Descending: `critical`, `high`, `medium`, `low`. | CP-430 |
| Title ascending; `beta`, `Alpha`, `alpha` created in that order | `Alpha`, `alpha`, `beta`. Descending: `beta`, `Alpha`, `alpha`. | CP-431, CP-433 |
| Title ascending; `Task 2`, `Task 10` | `Task 10`, then `Task 2`. | CP-431 |
| Created time ascending; tasks 4 and 5 carry the same recorded time, task 6 an earlier recorded time than task 5 | 4, 5, 6. Descending: 6, 5, 4. | CP-432 |
| Priority descending; tasks 2 and 7 both `high` | 2 before 7, in both directions. | CP-433 |
| The same sorted address requested twice | The same order both times. | CP-433 |
| Status `todo` and Priority descending | Only `todo` tasks, `critical` first. | CP-434 |
| Sort by Title, no filter field set | Every task, title order, the count of every task, worded without claiming a filter. | CP-435 |
| The sorted page is reloaded, or reopened from a bookmark | The same list in the same order. 200, no redirect. Saved data unchanged. | CP-437 |
| Clear after a filter and a sort | Every task, due-date ascending, no count, no choice in the address. | CP-438 |
| List sorted by Title; `in-progress` pressed on a row | Lands on the same sorted list, choices in controls and address. 200, `no-store`. | CP-439 |
| List sorted by Priority; `cancelled` pressed on a row | The confirmation on the same sorted list, 202, `no-store`. | CP-439 |
| Address carries Sort by `colour`; a move is pressed in a row | Nothing saved; the list shows the Sort by refusal. | CP-440 |
| Address carries Sort by `colour`, or Direction `sideways`, or Sort by twice | Refused at that field with a reason. | CP-441, CP-442 |
| Due from after Due to, and Direction `sideways` | Both reasons. Focus on Due from. No list. Saved data unchanged. | CP-442 |
| Each refusal kind | Its own refusal type from `domain`, mapped by type in `web`. | CP-443 |
| `/projects/99` with a sort choice | The not-found page. | CP-444 |
| Tab to Sort by, choose with arrow keys, Tab to Apply, Enter, scripting off | The sorted list, with no pointer used. | CP-445 |
| Title `<b>&"x"` in a title-sorted list | Shown as typed, in its CP-431 place. | CP-445 |
| The suite after the change | `domain/sorting.py` exists with its docstring, `sorting` is listed as landed, and the pointer test passes. | CP-446 |
| A sort applied under a recording saver | The saver receives nothing. No saved field is added. | CP-447, CP-450 |
| Unit suite | Each field, both directions, ties, the created-time cases, the defaults, each refusal. | CP-448 |
| Layer-3/4 suite | Each case CP-449 lists is present and passes. | CP-449 |
| Route, audit-hook and recording-saver tests | Each covers a sort. | CP-450 |
| `python3 tests/timed_run.py` | Today's lines, then `sort fixture: 1000 tasks, 20 comments each (20000 in all); title of … characters, comment of … characters; sort priority descending, 1000 listed` and three rows under 1.0 s. Exit 0. | CP-451, CP-452, CP-453 |
| The harness gets a landing with two tasks swapped | Row 3 and Row 4 fail. Exit 1. | CP-454, CP-455 |
| The 28 timed-run tests and the shape test after the change | Each asserts the new readings, lines or module, and keeps its other assertions. | CP-456 |
| The commands of CP-457 | Each exits 0. | CP-457 |
| A Python 3.11 interpreter | Runs the code and tests this change writes. | CP-458 |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| Today a project's page ignores sort-like keys in its address and shows the default order (the behaviour CP-428 to CP-435 replace). | In a fresh clone at `614eca038`, a probe built the timed run's 1,000-task fixture through the real saved data and `Site`, and requested `/projects/1`, `/projects/1?sort=priority&direction=descending` and `/projects/1?sort_field=title&sort_direction=descending&filter_status=in-progress`. | 200 each; the first two list 1,000 tasks starting `1, 61, 121, 181`, the third 250 in the same order. No sort control on any page. |
| The fixture holds 250 tasks of each priority, 200 undated (CP-451). | The same probe counted the loaded fixture. | `low`, `medium`, `high`, `critical`: 250 each; undated: 200. |
| Today's list order is earliest due first, undated last, ties by identity (CP-428). | `domain/tasks.py:372-380` read. | `_due_then_identity` returns `(due_date is None, due_date or date.min, id)`; `list_project_tasks` sorts by it. |
| The page holds exactly one `get` form, so the sort controls share the filter's form and Apply (CP-426). | `tests/integration/test_filter_pages.py:52` read. | `(form,) = [f for f in root.find_all("form") if f.attrs.get("method") == "get"]`. |
| An address with every filter key empty shows no count today, and keeps that under CP-435 (it carries no sort choice). | `tests/integration/test_filter_pages.py:139-150` read. | Its three queries carry no sort key and assert `"this filter" not in root.text()`. |
| A move on a list with a refused filter choice saves nothing today (CP-440). | `web/routes.py:799-806` read. | `# A malformed filter stops the move before it can save or open a confirmation (CP-405).`, then a redirect to the list with the carried choices. |
| A move carries only filter keys back today, and a move from a list with no sort choice still does under CP-439. | `tests/integration/test_filter_move_routes.py:325-334` read. | `set(query_of(response)) == {"filter_priority", "moved", "move_task"}` on a press carrying no sort key. |
| Adding `domain/sorting.py` breaks exactly one existing architecture test once `sorting` is listed as landed (CP-446, CP-456). | In the clone, `pytest tests/architecture` with a probe `domain/sorting.py` (docstring naming FR-36, two taking-part modules and a test module), run without and then with `"sorting"` in `LANDED_FEATURE_WORDS`. At the untouched commit the same tests with `tests/integration/test_timed_run.py` gave `209 passed`. | Without the word: 3 failed (`test_only_the_task_features_are_added_to_domain`, `test_each_feature_word_with_its_domain_module_is_listed_as_landed`, `test_no_excluded_feature_entry_exists`). With it: `1 failed, 57 passed`, the failure `test_only_the_task_features_are_added_to_domain`. |
| 28 existing timed-run tests cannot stay unchanged under any run that times a sort with the timer it is handed (CP-456). | In the clone, `tests/timed_run.py` got a stand-in sort block after the filter's, reading the handed timer four times and printing a fixture line and three rows. `python3 tests/timed_run.py` and `pytest tests/integration/test_timed_run.py` were run. | The run: exit 0, `sort total at 1000 tasks: 8.5 ms`. The tests: `21 failed, 123 passed, 7 errors`. Failed: `test_timed_run_fails_when_only_the_edit_fails`, `test_timed_run_fails_when_only_a_label_action_fails`, `test_full_timed_run_fails_when_only_name_measurement_fails`, the `[comment]`, `[assignee add]`, `[assignee remove]` cases of `test_timed_run_fails_when_only_a_new_action_total_reaches_limit` and of `test_timed_run_propagates_new_submission_and_landing_timing_failures`, the two cases of `test_timed_run_fails_when_only_move_total_reaches_limit`, the four of `test_timed_run_propagates_move_submission_and_landing_timing_failures`, the three of `test_timed_run_propagates_filter_timing_failures`, the three of `test_timed_filter_failures_reach_main_verdict`. Errors (the `whole_run` users): `test_timed_run_appends_exactly_three_ordered_action_blocks`, `test_new_timed_fixtures_are_independent_and_preserve_name_save_precondition`, `test_new_timed_actions_leave_product_data_unchanged`, `test_timed_run_reports_actual_fixture_lengths_for_all_three_actions`, `test_timed_run_appends_exact_move_block_and_nothing_after`, `test_timed_move_fixture_is_independent_and_product_data_unchanged`, `test_timed_filter_uses_independent_loaded_fixture`. |
| The run's last line today is `filter total at 1000 tasks` (CP-452). | `tests/integration/test_timed_run.py:2823-2845` read. | `lines[-4:]` is the filter fixture line and its three rows. |
| The project's highest rule identifier is CP-425 (numbering starts at CP-426). | `grep -rhoE 'CP-[0-9]+'` over `system/projects/tracker17/journey/tobiishi/trail/` and the product tree, numbers sorted. | `425`. |

No rule pins output that renders a language-level fact. Every pinned output is text, a number or an
order the product chooses, so no language-rendering row is owed.

---

## Out of Scope

- The All tasks list, its filter and sort controls, its header link and its project column (FDR R-81,
  second sentence; UXD UX-S7; SDD § 4 EX-12). The request: "no All tasks list or header link". Handed on
  in `deferred_decisions.md`.
- The project summary and its links into a filtered list (UXD UX-F6). The request: "no summary". Handed
  on.
- Sorting by more than one field (FDR OOS-8).
- Any change to the filter's rules: which tasks match, its refusals and its count's words when a filter
  field is set (CP-393 to CP-425 stand).
- The add-task form's answers. An add lands on the new task's page, and a refused or failed add lands on
  the project's list without the filter or sort choices, both as today.
- Remembering sort choices between sittings (UXD UX-I7).
- The wording of every line. The content stage writes it to `CONTENT.md`'s rules (CP-427, CP-435).
- How the controls look. The design stage takes it from `docs/DESIGN.md` (SDD § 4 EX-10).

---

## Locked Answers (the divergence record — self-review 2026-10-27)

- **Gap 1 — where the sort controls stand (b):** in the filter's controls, after its seven fields and
  before Apply (CP-426). The request says "beside the filter controls" and that a sort over a filter
  keeps the filter's matches, which one Apply gives on a page with no script. The page's one `get` form
  is pinned by an existing test (Verified Claims). The place fixes the focus order of CP-442.
- **Gap 2 — no Sort by chosen (b):** due date (CP-428). FR-36 fixes only the default direction; UXD
  UX-F5 makes due date the list's default field. A Direction with no field then has an order to apply to.
- **Gap 3 — what "alphabetical, ignoring letter case" means for every title (b):** case set aside, then
  code-point order (CP-431). Titles are any text, so the order has to span every character. Code-point
  order gives one answer on every machine and is testable, where a language-aware order would vary with
  the machine's settings. It agrees with FDR R-92's example, and changing it later moves no other rule.
- **Gap 4 — ties in a descending sort (b):** creation order, oldest first, in both directions (CP-433).
  FDR R-93 and SRS FR-36 state the tie rule with no direction, and FDR's `Alpha`, `alpha` example holds
  it in ascending.
- **Gap 5 — created time is creation order (b):** by task number, not by the recorded time (CP-432).
  SRS FR-36 says a created-time sort "follow[s] the creation order FR-15 keeps", and FDR R-43 keeps that
  order "independently of that recorded time".
- **Gap 6 — the count with a sort and no filter (b):** shown, as every task of the project (CP-435). The
  request asks for the count after Apply. Today's count words speak of a filter, so the rule keeps them
  from claiming one that is not set; the words are the content stage's.
- **Gap 7 — what the sort controls show with no choice (b):** Due date and Ascending (CP-436), so the
  controls always say what order the list is in. An address with no choice stays the page it is today,
  with no count.
- **Gap 8 — sort values no control sends are refused (b):** CP-441, the same treatment CP-404 gives the
  filter's fields. Ignoring the value would show an order that does not match the address.
- **Gap 9 — the choices survive every move interaction (b):** CP-439 and CP-440, as CP-407 does for a
  filter. UXD UX-F4 says "the operator stays where they were", and a move landing on an unsorted list
  would lose the operator's place.
- **Gap 10 — which sort is timed, and the rows (b):** Priority descending over all 1,000 tasks (CP-451),
  because it lists every task and puts each of the fixture's priority ties to the test. The rows are
  named for the press and the address a reload opens (CP-453), as the filter's are. The request says
  "POST/GET and total"; ADR-0011 makes Apply a read, so both rows time a `GET`.
- **Gap 11 — what "happened" means for a sort (b):** CP-454. The landing must list every task once in
  FR-36's order, worked out by the run itself, because a landing in the wrong order would time a list
  that is not the sort. The saved data must be unchanged, because a sort that saved something would
  break FDR R-94.
- **Gap 12 — the harness tests (e):** CP-455. The request does not ask for them. SDD § 4 TS-1 builds
  every slice test-first, and the timed run's docstring says its harness is checked by
  `tests/integration/test_timed_run.py`.
- **Gap 13 — refusal types, the entry module's docstring and the pointer test (e):** CP-443 and CP-446.
  The request names only the module. NFDR QC-5 and QC-11 and SDD § 4 TS-3 and TS-4 require them.
- **Gap 14 — the route, audit-hook and recording-saver tests (e):** CP-450, from NFDR QC-7, QC-35 and
  QC-54, each stated over every route or action.
- **Gap 15 — one test per refusal, and the move pages' response contract (e):** CP-449. SRS AC-12 asks
  for one test per refusal. NFDR QC-63 covers every page a move lands on, and CP-439 adds those pages.
- **Gap 16 — Ruff, mypy, the end-to-end suite and Python 3.11 (e):** CP-457 and CP-458, from NFDR
  QC-62, § 9, QC-60 and SDD § 4 TS-1. The request names only `pytest products/tracker17/tests/` and the
  timed run.
- **Gap 17 — no text field, so QC-9 and QC-36's text-field checks have nothing to bind:** the sort
  controls offer choices (CP-426). CP-445 still holds typed titles to FDR R-112 where they show.
- **Gap 18 — existing tests named as changing (f):** CP-456. The request says every existing test stays
  as it is. The probes in Verified Claims show that no `domain/sorting.py` leaves the shape test
  unchanged, and no run that times a sort with the timer it is handed leaves the 28 timed-run tests
  unchanged. Each keeps its name and every assertion beyond the readings, lines or module the change
  adds, so none is loosened or removed.
