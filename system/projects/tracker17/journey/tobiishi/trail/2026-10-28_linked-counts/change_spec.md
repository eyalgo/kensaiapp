# Change Spec — a project's Summary counts as links into its filtered task list

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing
**Request:** On a project's Summary page, make each status count, each priority count and the overdue count a link that opens that project's task list filtered to exactly that value, so the list's match count equals the number the link showed. The no-due-date count, the per-assignee counts and "(unassigned)" stay plain numbers. A linked count's accessible name starts with its number and says what it counts ("12 tasks in todo", "3 overdue tasks"), and no two links on the page share their text. A zero count is still shown as a number; if it carries a link, the link opens the list's no-match state, never an error. The links reuse the existing filter parameters and `domain/filtering.py`: no second copy of the filter, overdue or sort rules, and no new filter field. The summary test (AC-14), on a project built to exercise each row, is extended to assert every status, priority and overdue link's target, that the list it opens holds exactly the counted tasks, and that the no-due-date and assignee counts carry no link. The counts, rows and page titles `summary-page` landed must keep their values and wording, the AC-13 agreement test and the timed summary run must still pass, and existing pages and timed actions must keep working. `pytest products/tracker17/tests/` must exit 0.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened

---

## Change Summary

On a project's Summary, the four status counts, the four priority counts and the overdue count become links. Each opens that project's Tasks view filtered to that one value, so the list shows exactly the tasks the number counted (UXD UX-F6, UX-S5; SDD § 6 S-6). Every other count, and every row label, page title and word the Summary shows today, stays as it is.

Sizing (`pm_right_size.md`): one capability, stepping from a Summary count into the list of the tasks it counts. Its acceptance boundary is UXD UX-F6's linked-counts paragraph, UX-S5, CONTENT.md § Accessibility of text on number links, and SDD § 6 S-6's linked-counts sentence and *Command*. The link markup, the link names, the AC-14 test extension, and the repairs to the tests that pin today's plain numbers are that capability and its proof. One merge.

---

## Rules

The product's location is `project.md` `Product path:`. Paths below are relative to it.

### Which counts are links
- **CP-513:** On a project's Summary, nine counts are links: each of the four status counts (`todo`, `in-progress`, `done`, `cancelled`), each of the four priority counts (`low`, `medium`, `high`, `critical`), and the overdue count (UXD UX-F6, UX-S5; SDD § 6 S-6). A count is a link whatever its value, `0` included (UXD UX-F6: "Every status count, priority count and the overdue count is a link").
- **CP-514:** These stay plain numbers, with no link: the total, the no-due-date count, every per-assignee count, and the `(unassigned)` count (UXD UX-F6). No row label is a link or sits inside one. That covers the status and priority words, `Total`, `Overdue`, `No due date`, the assignee names and `(unassigned)`.
- **CP-515:** A linked count's visible text is exactly the numeral the Summary shows for that row today, and nothing else. Every count keeps its value. Every row keeps its label, its group, its place and its order. The four group headings, the column headers, the page title `{name}: Summary - tracker17`, the heading, the `Tasks` and `Summary` links, and the empty project's invitation line `This project has no tasks yet. Open Tasks to add the first task.` keep their wording and their targets.

### Where a link goes
- **CP-516:** Each link opens the same project's Tasks view, with exactly one filter choice set and no sort chosen. It uses the filter's existing address parameters and adds none:
  - a status count opens `/projects/{id}?filter_status={status}`;
  - a priority count opens `/projects/{id}?filter_priority={priority}`;
  - the overdue count opens `/projects/{id}?filter_overdue=on`.

  `{id}` is the project's identity, as in its Summary address, and `{status}` and `{priority}` are the row's word exactly as the row label shows it. The address carries no other filter field and no sort field.
- **CP-517:** The list a link opens is that filter's result as the Tasks view shows it today. Its filter controls show the one choice set and every other filter control empty. The list is in the default sort, and its rows are this project's tasks only. For the same saved data on the same local day, it holds exactly the tasks the count counted (FDR R-99 for overdue). For a count `N` of 1 or more, the Tasks view's match line states `N`: `1 task matches this filter.` or `{N} tasks match this filter.`
- **CP-518:** A zero count's link never opens an error, a refusal or a not-found page. On a project that has tasks, it opens the no-match state: `No tasks match this filter. Press Clear to see every task.`, with the choice shown in the controls (UXD UX-S4 No match). On a project with no tasks, it opens what that address shows today, the Tasks view's no-tasks state `This project has no tasks yet. Give the first task a title and press Add.` (UXD UX-S4 No tasks yet; CONTENT.md § Empty, "The no-match state never says "no tasks", and the no-tasks state never mentions a filter").
- **CP-519:** The equality in CP-517 holds when the counts and the list come from the same saved data on the same local day. The Summary is the data as of its load and never updates itself (FDR R-101). A list opened after another tab changed a task, or after local midnight, shows the list as of its own load. Its count may then differ from the number the link showed, and that is not a failure.
- **CP-520:** Following a count link, reloading the list it opens, or going back changes nothing and saves nothing (FDR R-106). Every link is a plain link that works with no script (ADR-0003).

### The link's name
- **CP-521:** Each linked count's accessible name starts with the numeral the link shows, so the visible text is one unbroken string inside the name (CONTENT.md § Accessibility of text; WCAG 2.2 SC 2.5.3). The name then says what the number counts: the status, the priority, or overdue. CONTENT.md fixes two names: `12 tasks in todo` and `3 overdue tasks`. Every other name is written to CONTENT.md and is not fixed here, its noun agreeing with the number as CONTENT.md § Numbers writes counts (`1 task`, `12 tasks`).
- **CP-522:** No two links on the Summary that open different addresses share an accessible name. That covers all nine count links, the header's links, the `Tasks` and `Summary` links, and the empty project's invitation link (CONTENT.md § Accessibility of text, "Two links to different places never share their text"). Nine counts can show the same numeral, `0` on an empty project for one, and their names still differ. Two links that share a label and an address may share a name (CONTENT.md RN-20). The empty project's two `Tasks` links, which both open `/projects/{id}`, stay as they are.

### The rules the links reuse
- **CP-523:** The list a link opens is decided by the filter and sort rules the Tasks view already applies, in `domain/filtering.py` and `domain/sorting.py`. Its overdue result comes from the overdue rule the marking, the filter and the Summary already share. No rule is restated in a second place. The filter keeps its seven fields, and none is added (the request; FDR R-82).

### Use of the page
- **CP-524:** The nine count links meet SDD § 4 EX-8 and EX-9. Each can be reached with Tab and opened with Enter, and each shows when it has focus (UXD UX-A1, UX-A2). Each meets UXD UX-A6's 24 by 24 CSS pixel target floor or an exception WCAG 2.2 SC 2.5.8 names. At 400% zoom of a 1280-pixel-wide window the Summary still reads without scrolling in two directions (UXD UX-A7 names the summary as not exempt).

### The tests the request and the records require
- **CP-525:** The AC-14 summary test is extended (SRS AC-14; SDD § 6 S-6 *Command*). It runs through the real page and the real list, at the layer where both are served in one process (SDD § 4 TS-1). It uses a project built to exercise each row, the shape CP-507 fixed: tasks in every status and every priority, an overdue task, a task with no due date, a listed assignee, a listed name with no open task, an unlisted name on an open task, and an unassigned open task. A second project holds tasks too. For each of the nine linked counts, the test asserts:
  - the link's target (CP-516);
  - that the list the target opens holds exactly the tasks counted, and no task of the second project;
  - that its match line states the count, or that it shows the no-match state for a zero (CP-517, CP-518).

  It also asserts that the total, the no-due-date count, every per-assignee count and the `(unassigned)` count carry no link (CP-514). And it asserts that every count link's name is distinct (CP-522). The project must have at least one zero status or priority count, so CP-518's no-match case is exercised.
- **CP-526:** The AC-13 agreement test (`tests/integration/test_summary_routes.py::test_overdue_mark_filter_and_summary_agree`, CP-508) still passes. Its clock is handed in and no product module is patched (NFDR QC-28).
- **CP-527:** `python3 tests/timed_run.py` exits 0 (NFDR QC-48; SDD § 6 S-6 *Command*). Every line keeps its label and its place, and the Summary line is still last. The run still times only the one Summary request, and it still counts it only when that page shows the fixture's counts. Following a count link opens a filtered list, which is NFR-1's filtering action and is timed already, so the change adds no timed action (NFDR QC-48).
- **CP-528:** Both suites pass: `pytest products/tracker17/tests/` and the end-to-end suite `pytest products/tracker17/tests/e2e/` (SDD § 6 S-6 *Command*, "Both suites pass"; SDD § 4 TS-1). The checks of NFDR QC-62 pass on the change: Ruff's format check, Ruff's lint and mypy. Every test module the change adds names the requirements or acceptance criteria it checks. A module added among those `domain/summary.py` names as checking the feature is named in its opening docstring (NFDR QC-11).

---

## Examples

Fixture A (CP-507's shape). Today is 2026-10-28. Project `Alpha` (id 1) holds:
- T1: `todo`, `low`, due 2026-10-27, unassigned;
- T2: `in-progress`, `medium`, no due date, `ari` (listed);
- T3: `done`, `high`, due 2026-10-01, `ari`;
- T4: `cancelled`, `critical`, no due date, `dan` (removed from the list);
- T5: `todo`, `critical`, due 2026-10-28, `eve` (removed from the list).

The list holds `ari` and `bo`. Project `Beta` (id 2) holds one `todo` task assigned to `bo`. Project `Gamma` (id 3) has no tasks.

| Scenario | Expected behavior | Rule |
|---|---|---|
| `Alpha`'s Summary | `todo` 2, `in-progress` 1, `done` 1, `cancelled` 1, `low` 1, `medium` 1, `high` 1, `critical` 2 and overdue 1 are links. Total 5, no due date 2, `ari` 1, `bo` 0, `eve` 1 and `(unassigned)` 1 are plain. Every value, label and order is as before | CP-513, CP-514, CP-515 |
| `Alpha`'s `todo` count `2` | Link text `2`, target `/projects/1?filter_status=todo`. The list shows T1 and T5 only, with `2 tasks match this filter.` and Status showing `todo` | CP-516, CP-517, CP-525 |
| `Alpha`'s `in-progress` count `1` | Target `/projects/1?filter_status=in-progress`. The list shows T2, with `1 task matches this filter.` | CP-516, CP-517 |
| `Alpha`'s `critical` count `2` | Target `/projects/1?filter_priority=critical`. The list shows T4 and T5 | CP-516, CP-517 |
| `Alpha`'s overdue count `1` | Target `/projects/1?filter_overdue=on`. The list shows T1 only: T5, due today, and T3, `done`, are not overdue | CP-516, CP-517, CP-523 |
| `Beta`'s `done` count `0` | Target `/projects/2?filter_status=done`. The list shows `No tasks match this filter. Press Clear to see every task.`, with Status showing `done` | CP-513, CP-518 |
| `Gamma`'s Summary | All nine counts are `0` links. Following `todo` opens `/projects/3?filter_status=todo`, which shows `This project has no tasks yet. Give the first task a title and press Add.` The invitation line and both `Tasks` links are unchanged | CP-513, CP-515, CP-518, CP-522 |
| `Alpha`'s linked-count names | Each starts with its numeral and names what it counts. The `todo` link reads like `2 tasks in todo`, and a `12` todo count reads `12 tasks in todo`. No two of the nine share a name, nor does any share a name with `Projects`, `All tasks`, `People`, `Tasks` or `Summary` | CP-521, CP-522 |
| An overdue count of 3 | Name `3 overdue tasks` | CP-521 |
| `Alpha`'s Summary loaded, then another tab moves T1 to `in-progress`, then `todo` `2` is followed | The list shows T5 only, with `1 task matches this filter.` That is the list as of its load, and not a failure | CP-519 |
| The Summary is loaded on 2026-10-28 and its overdue link is followed after midnight | The list is the overdue result for 2026-10-29 | CP-519 |
| Following a count link, then reload, then back | Nothing saved, nothing changed | CP-520 |
| The filter after the change | Still exactly seven fields. A summary link opens nothing the filter form couldn't | CP-516, CP-523 |
| Tab through `Alpha`'s Summary | Each of the nine links takes focus with a visible ring and opens on Enter. Each meets the 24 by 24 floor or an SC 2.5.8 exception | CP-524 |
| 400% zoom of a 1280-pixel window on a Summary | Reads without two-direction scrolling | CP-524 |
| `pytest products/tracker17/tests/` | Exits 0, including the extended AC-14 test and the AC-13 agreement test | CP-525, CP-526, CP-528 |
| `pytest products/tracker17/tests/e2e/` | Exits 0 | CP-528 |
| `python3 tests/timed_run.py` | Exits 0, every line in its place, Summary last | CP-527 |

Rule-to-Example walk: every rule CP-513 to CP-528 has a row above.

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| Every Summary count is a plain number today, and the previous change's CP-503 said so | Read `web/pages.py:1462-1509`. Read the trail spec `2026-10-28_summary-page/change_spec.md` CP-503 | `_summary_group` writes `<td>{count}</td>`. CP-503: "No count and no row label on the Summary is a link." This change replaces CP-503. The number isn't reused |
| The filter's address parameters are `filter_status`, `filter_priority` and `filter_overdue`, and the overdue box sends `on` (CP-516) | Ran the real `Site` and `Tracker` in process, with a clock handed in, on the worktree at `6cfcf5343`, and read the filter form `/projects/1` returns. Read `web/routes.py:81,183-190` and `domain/refusals.py:26-39` | The form's fields are `filter_assignee`, `filter_due_from`, `filter_due_to`, `filter_label`, `filter_overdue`, `filter_priority`, `filter_status`, `sort_direction` and `sort_field`. Overdue is `<input type="checkbox" … name="filter_overdue" value="on">`. `FilterField` has seven members |
| An address carrying one filter choice and nothing else opens the filtered list, with its match line (CP-516, CP-517) | The same run, today 2026-10-28. `Alpha` holds three tasks, all `todo`: `low` overdue, `high` undated, and `critical` due 2026-11-01 | `?filter_status=todo` gave `3 tasks match this filter.` `?filter_priority=critical` and `?filter_priority=low` gave `1 task matches this filter.` `?filter_overdue=on` gave `1 task matches this filter.`, with the box checked. In every case the one choice showed in its control and the sort read `due_date`/`ascending` |
| A zero filter on a project with tasks opens the no-match state (CP-518) | The same run: `?filter_status=done`, `?filter_status=in-progress` and `?filter_priority=medium` on `Alpha` | `No tasks match this filter. Press Clear to see every task.` |
| A filter on a project with no tasks opens the no-tasks state, not no-match (CP-518, Locked Answer a-1) | The same run: `/projects/2?filter_status=todo` and `/projects/2?filter_overdue=on` on an empty project | `This project has no tasks yet. Give the first task a title and press Add.`, the same as `/projects/2`. Read `web/pages.py:1006-1010`: `_task_list` answers no rows with that line |
| The Summary's counts are already taken through the project filter (CP-523) | Read `domain/summary.py:1-15,94-120` | Status, priority, total and overdue go through `filter_project_tasks(…, FilterInput(…), today)`, and overdue uses `OVERDUE_ON` |
| The suite is green before the change | Disposable clone at `6cfcf5343`: `pytest -q products/tracker17/tests/` | `2046 passed` |
| Linking the nine counts fails 27 tests in five places and breaks the timed run (Locked Answers f-1 to f-4) | Same clone with a stand-in `summary_page` that wraps the nine counts in `<a href="/projects/1?filter_…">`, on the real tree with no harness swapped in. Ran `pytest -q products/tracker17/tests/`, then `python3 tests/timed_run.py` | `27 failed, 2019 passed`. The failures: `test_pages.py::test_every_page_has_a_header_with_the_projects_and_people_links`; `test_summary_pages.py::test_summary_has_all_ordered_plain_rows_and_only_allowed_links` and `::test_empty_summary_invites_first_task_beside_all_zero_rows`; and 24 tests in `test_timed_run.py`. The timed run printed `open a project summary at 1000 tasks: 3.5 ms — refused or failed` and exited 1. The same command on the clean clone exited 0 |
| Why the timed run rejects a linked Summary (f-3) | Read `tests/timed_run.py:146,1232` and `tests/integration/test_timed_run.py:3693,3757` | Both read the rows with `SUMMARY_ROW = …<td>([0-9]+)</td></tr>`, which matches no linked count |
| Why the header test fails (f-1) | Read `tests/integration/test_pages.py:145-146,181-183` | Its Summary page has an overdue count of `0`, and every `href` must fullmatch `/|/tasks|/people|/projects/\d+(/summary)?` |
| The browser test pins the Summary's links to the pair (f-4) | Read `tests/e2e/test_summary.py:89`. Not run: `playwright` isn't installed for this run's `python3` (`ModuleNotFoundError`) | `assert page.locator("main a").all_inner_texts() == ["Tasks", "Summary"]` |
| The AC-13 agreement test exists and passes today (CP-526) | Read `tests/integration/test_summary_routes.py:76`. It is in the clean clone's 2046 passes | `test_overdue_mark_filter_and_summary_agree` |
| The AC-14 summary test today is a domain test with no page (CP-525, Locked Answer b-3) | Read `tests/unit/test_summary.py:1-8,117-123` | `test_summary_counts_only_the_requested_project`, CP-507, layer 1 |
| The highest CP in the project's record is CP-512 | `grep -rhoE "CP-[0-9]+"` over `system/projects/tracker17/journey/` and the product, sorted | `CP-512` |

Language rendering: no rule pins output that renders a language-level fact. Counts, status and priority words, addresses and link names are values the product chooses, so no rendering row is owed.

---

## Out of Scope

- **The unreadable-saved-data page for the Summary and the lists it links to.** FDR R-25 and R-26 have every page say the saved data couldn't be read and offer no navigation. Today the tracker refuses to start on unreadable data and serves no page (`main.py:39-48`), and the request rules this out: "Out of scope: … the unreadable-data page (`protect-saved-data`)". Parked in `deferred_decisions.md` as a record gap.
- A summary across projects (FDR OOS-10). All tasks gains no Summary and no count links.
- Links from the total, the no-due-date count, the per-assignee counts or `(unassigned)` (UXD UX-F6, RN-13: the filter can't express them).
- Any change to the filter, the sort, the overdue rule, the Tasks view or its strings. A count link opens the Tasks view exactly as that address shows it today. That includes the no-tasks state on an empty project.
- Any change to the Summary's counts, rows, labels, headings, title or invitation (CP-515).
- Multi-value filters (FDR OOS-8). Each link sets one field.

---

## Locked Answers (the divergence record — self-review 2026-10-28)

- **(a-1) CP-518, a zero count on a project with no tasks.** The request says a zero link "opens the list's no-match state". On a project with no tasks, the Tasks view answers a filtered address with its no-tasks state instead (Verified Claims). UXD UX-S4 and CONTENT.md § Empty keep the two states apart as "different facts". On an empty project the fact is "no tasks", and FDR R-95 has an empty project invite a first task. Making it say "no match" would change the Tasks view, which the request says keeps working and leaves out ("this is the summary page's markup plus the AC-14 test extension"). The rule keeps the request's own aim, "never an error". On a project with tasks it is the no-match state, and on an empty project it is the no-tasks state the address shows today.
- **(b-1) CP-513, a zero count carries a link.** The request leaves this open ("if it carries a link"). UXD UX-F6 and SDD § 6 S-6 say every status, priority and overdue count is a link, and the subject is the links this change adds, so the record's "every" is the rule. CP-518 makes every such link safe.
- **(b-2) CP-516, the exact target address.** The request says "reuse the existing filter parameters". The rule picks the shortest address that sets one field and no sort. It opens the same list as the filter form's own Apply for that one choice. It is reversible, changes no data, and gives the test one exact target to assert.
- **(b-3) CP-525, where the AC-14 extension runs.** The AC-14 summary test today runs at layer 1, which builds no page and no list. A link's target and the list it opens exist only where `web` serves both, at the integration layer (SDD § 4 TS-1). Which module holds the extension is the design's call.
- **(b-4) CP-514, the total stays plain.** The request and UXD UX-F6 name the links and leave the total out of both lists. Plain is what it is today, and the project's unfiltered list is already one link away, under `Tasks`.
- **(b-5) CP-522, "no two links on the page share their text".** This is read as CONTENT.md's rule, that links to different places never share a name, and RN-20 allows two links with one label and one address. Read literally, the request would forbid two things. Nine `0` numerals on an empty project would share their visible text, which CP-521's names keep apart. And the empty project's two `Tasks` links, from `summary-page`, would have to change, against CP-515 and the request's own "keep their … wording".
- **(e-1) CP-528, the end-to-end suite and QC-62.** The request names only `pytest products/tracker17/tests/`, which doesn't collect `tests/e2e/`. SDD § 6 S-6 *Command* says "Both suites pass". NFDR QC-62 binds the code the change touches, and QC-11 binds any test module it adds.
- **(e-2) CP-524, keyboard, focus, target size and reflow.** The request is silent. SDD § 4 EX-8 and EX-9, with UXD UX-A1, UX-A2, UX-A6 and UX-A7, bind every control and page, and these nine links are new controls.
- **(e-3) CP-527, the timed run.** The request asks only that it "still pass". NFDR QC-48 adds an action only when the change adds a listed one. Following a link is filtering, which is already timed, so the rule pins that no line moves.
- **(f-1) `tests/integration/test_pages.py::test_every_page_has_a_header_with_the_projects_and_people_links` changes.** Its Summary page now links its overdue `0` to `/projects/1?filter_overdue=on`. It keeps asserting the header's three links on every page, that every link opens one of the tracker's own addresses (now also a project's Tasks address carrying one filter choice, CP-516), and that no page says "rename" or "delete".
- **(f-2) Two tests in `tests/integration/test_summary_pages.py` change: `::test_summary_has_all_ordered_plain_rows_and_only_allowed_links` and `::test_empty_summary_invites_first_task_beside_all_zero_rows`.** Both pin the main area's links to the pair, plus the invitation on an empty project. They keep asserting the title, the heading, every group, header, row, value and order, the invitation's words and link, and no form, script or refresh. They also keep asserting that no row label is inside a link. Their link lists gain the nine count links, and they assert that the total, the no-due-date, per-assignee and `(unassigned)` cells hold no link.
- **(f-3) `tests/timed_run.py`'s Summary check and its copy in `tests/integration/test_timed_run.py` change.** Both read the counts from plain cells. The 24 failing tests in `test_timed_run.py` all reach that check. The check keeps counting the Summary only when its title, heading, four headings and every row's label and value match the fixture for the day. The test file keeps every assertion it makes today.
- **(f-4) `tests/e2e/test_summary.py::test_browser_can_open_summary_and_return_to_tasks` changes.** Its `main a` list gains the nine count links. It keeps asserting the titles, the pair, every count it reads, no form or control, the empty project's zeros and invitation, and the round trip. This was read and not run (Verified Claims).
- **(f-5) CP-503 of `2026-10-28_summary-page` is withdrawn.** "No count and no row label on the Summary is a link" was that station's fence. The station after it, which UXD UX-F6 and SDD § 6 S-6 call for, is this one. Row labels still aren't links (CP-514), and the number 503 stays retired.
