# Change Spec — an All tasks list across every project, with the filter and sort controls

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing
**Request:** Add an All tasks page that lists every task across every project. The header on every page gains an All tasks link, and the not-found page links to both Projects and All tasks (UXD UX-S10). All tasks (UX-S7) shows each task with a project column linking to that task's project, and the same status moves on each row that a project's rows offer; moving a task there changes its status as it does in its project and shows All tasks again. The page has no add-task form, since a task is created in a project. With no tasks anywhere the page says there are no tasks yet and links to Projects. The filter and sort controls the two earlier stations built for a project's list sit above it and work across all projects, by reusing `domain/filtering.py` and `domain/sorting.py` rather than copying them: Apply with a filter, a sort or both shows only the matches in the order FR-36 defines, with the match count and the choices still shown; the choices appear in the address so a reload shows the same list; Clear returns every task in due-date ascending order; a from-date after the to-date is refused with FR-34's reason; a filter matching nothing says so and shows Clear. The assignee filter offers the names on the list and the label filter the labels carried by tasks in any project. A task moved out of a filtered status leaves All tasks with the completion line naming it (UX-F4). Done when `grep -rn -i 'all tasks' products/tracker17/web` matches in `web/pages.py` and a page test shows the header link and the not-found links; All tasks shows every task of every project with a project column and working moves, and shows the empty state when there are none; Apply, Clear, the count, the address, the reversed-range refusal and the no-match line work across projects; `pytest products/tracker17/tests/` exits 0, with tests for these lines including AC-14's filter and sort tests run across projects; and `python3 products/tracker17/tests/timed_run.py` exits 0 and its output still shows the `filter total at 1000 tasks` and `sort total at 1000 tasks` lines under `LIMIT_SECONDS`. Sizing: the acceptance boundary is one capability, listing, filtering and sorting tasks across all projects (station reached-when 1 to 6, SDD § 6 S-5, SRS FR-31 to FR-37), and it maps to one merge, because the page only reuses the filter and sort the two earlier stations built and adds no rule. The project summary and its links into a filtered list are a later seed and are not here. What must not be weakened: no project summary, no links into a filtered list and no summary across projects, and no add-task form on All tasks; the filter's and sort's rules stay as `domain/filtering.py` and `domain/sorting.py` hold them, with no second copy; one value per filter field and one sort field, with the choice in the address and not remembered between sittings (UX-I7); the limit and every existing timed action and test stay as they are.
**Language resolution:** Python — step 1 (`project.md` `Languages:`) — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with every concern it routes

---

## Change Summary

The tracker gains an All tasks page that lists every task of every project with a project column, the
moves each row offers, and the filter and sort controls a project's list already has, working across
projects. Every page's header gains an All tasks link, and the not-found page links to it after
Projects.

Paths below are relative to the product root, which `system/projects/tracker17/project.md`
`Product path:` names. `SRS`, `SDD`, `UXD`, `FDR`, `NFDR`, `CONTENT.md` and `DESIGN.md` are the
product's documents under `docs/`. CP-393 to CP-458 are the project's earlier rules, in the sealed
specs of the two stations before this one.

**Sizing.** One capability: listing, filtering and sorting tasks across every project (SRS FR-31 to
FR-37; UXD UX-S7; SDD § 6 S-5, its All tasks half). The header link and the not-found link are that
list's way in, which SDD § 4 EX-12 says arrive with it. Every rule below is that list, its controls,
its moves, its refusals, or a check a record requires of it. One merge.

---

## Rules

### The way in

- **CP-459:** Every page that has the header shows three links in it, after the product name, in this
  order: Projects, All tasks, People. All tasks opens the All tasks page. The page for saved data that
  can't be read keeps having no header. *(SDD § 4 EX-12, § 6 S-5; UXD § 4, UX-S7; DESIGN.md § Layout,
  Header)*
- **CP-460:** The not-found page, in each of its two forms (no project at this address, no task at this
  address), keeps its one heading and gives one paragraph after it that links to Projects first and
  All tasks after. It is still answered 404 and holds no form. Every address that shows it today still
  shows it, apart from the one address All tasks takes. The wording follows `CONTENT.md` § Error, "An
  address with nothing at it" ("There's no project at this address. Open Projects or All tasks.").
  *(UXD UX-S10; SDD § 4 EX-12, EX-13; FDR R-105)*
- **CP-461:** All tasks has an address of its own. The form of that address is development-design's.
  Opening it changes nothing and is answered with the page, 200, with no redirect. *(SDD § 4 EX-3,
  RT-8; FDR R-101, R-106)*

### The list

- **CP-462:** All tasks lists every task of every project, each exactly once. Its title is "All tasks -
  tracker17" and its one `h1` is "All tasks" (`CONTENT.md` § Accessibility of text; DESIGN.md
  § Typography, {typography.page-title}). Each row carries everything a project's row carries today: the title as a
  link to the task, status, priority, the assignee or "unassigned", labels, the due date with the
  "Overdue" marker when it applies, and the moves allowed from the task's status. It also carries a
  project column, which stands after the title. *(FDR R-81; SRS FR-31; UXD UX-S7; SDD § 6 S-5;
  DESIGN.md § Layout, the task table)*
- **CP-463:** The project column shows the name of the task's project, as typed, as a link to that
  project's page with no filter or sort choice in its address. *(FDR R-81, R-112; UXD UX-S7)*
- **CP-464:** All tasks has no add-task form and no rename, delete or summary control. *(UXD UX-S7;
  Request)*
- **CP-465:** With no choice in its address, All tasks lists in due-date ascending order across every
  project: earliest due first, tasks with no due date last, and tasks equal on due date in creation
  order, realized as ascending task number in each title link's address. A task's project plays no
  part in the order, so tasks of different projects interleave. *(UXD UX-F5 Defaults; FDR R-91, R-93,
  R-44; ADR-0008)*
- **CP-466:** When no project holds a task — no project at all, or only projects with no tasks — All
  tasks says there are no tasks yet and links to Projects. It shows no table, no filter or sort
  control, no count and no blank space, whatever its address carries, and it never mentions a filter.
  The wording belongs to the content stage. *(UXD UX-S7; SRS FR-37; FDR R-95; `CONTENT.md` § Empty)*

### The filter and the sort across projects

- **CP-467:** When at least one task exists, All tasks shows above its list the controls a project's
  list shows today, in the same order, each with a visible label: Status, Priority, Assignee, Label,
  Due from, Due to and Overdue, then Sort by and Direction, then Apply and Clear. One Apply applies
  the filter and the sort together and one Clear clears both. Each control takes one value, or none.
  Applying a choice shows no message. *(UXD UX-F5, UX-S7; SRS FR-32, FR-36; FDR R-82, R-89, OOS-8;
  `CONTENT.md` § Voice)*
- **CP-468:** The choices offered are those of a project's list (CP-394, CP-426), with two scoped to
  every project:
  - Assignee: the names on the current assignee list, in the list's order.
  - Label: each distinct label that any task of any project carries, once, in code-point order,
    compared exactly. The choices come from every task, never from the tasks a filter leaves, so
    filtering a labelled task out does not remove its label.

  *(SRS FR-33; UXD UX-F5, "one project or all"; SDD § 6 S-5, "the labels carried in the list's
  scope")*
- **CP-469:** Apply lists only the tasks, from every project, that match every field set, and orders
  them by the sort chosen. Which tasks match is what CP-396 states for a project's list. The order is
  what CP-428 to CP-433 state, with no Sort by meaning due date and no Direction meaning ascending.
  Tasks equal on the chosen field, and a created-time sort, follow creation order across projects,
  realized as ascending task number. A sort never adds or removes a task. *(SRS FR-32 to FR-36, AC-14;
  FDR R-82 to R-93; UXD UX-F5)*
- **CP-470:** With a filter field set or a sort choice, and at least one task listed, the page shows
  the number of tasks it lists, and every control shows the choice applied. With a sort choice and no
  filter field set, that number is every task of every project, and its words do not say a filter is
  applied. The page opens at its start. The wording belongs to the content stage. *(Request; UXD UX-F5,
  UX-S4; SDD § 4 EX-5)*
- **CP-471:** When at least one task exists and none matches, All tasks says nothing matched and names
  the filter as the reason, never "no tasks", with Clear in view and the controls showing the choices.
  It shows no table, no count and no blank space. *(SRS FR-37; FDR R-95; UXD UX-S7, "No match: as
  UX-S4")*
- **CP-472:** The choices are carried in the All tasks address and stored nowhere else. Opening that
  address again — a reload, Back, a bookmark — shows the same list in the same order, worked out
  against the saved data and the local date at that moment. A visit to the All tasks address with no
  choice shows every task in the CP-465 order. Apply, its reload and Clear are reads, each answered
  with the page, 200, and no redirect, and none changes the saved data. *(FDR R-94, R-101, R-106; UXD
  UX-I7; SDD § 4 EX-3, RT-8; ADR-0006, ADR-0011; NFDR QC-7)*
- **CP-473:** Clear shows every task of every project in the CP-465 order, the filter controls at no
  value, Sort by at Due date and Direction at Ascending, no count, and an address carrying no choice.
  *(Request; UXD UX-F5)*

### Refusals

- **CP-474:** Every choice a project's list refuses today, All tasks refuses with the same reason at the
  same field: a Due from later than Due to, with the reason that the dates are the wrong way round
  (CP-402); an Assignee not on the current assignee list (CP-403); a value no control sends, of each
  kind CP-404 and CP-441 name. A single Label value is never refused. On a refusal the saved data is
  unchanged and no task list result is shown; the controls hold the choices as sent and each refused
  field shows its own reason beside it; the page opens with keyboard focus on the first refused field
  in the controls' order, its reason as the field's accessible description; Clear is in view.
  *(Request; SRS FR-33, FR-34, FR-39, AC-12; FDR R-84, R-87, R-100; SDD § 4 EX-4, EX-14, RT-8; UXD
  UX-I3)*

### Moves on All tasks

- **CP-475:** The moves on an All tasks row are the ones offered for the task's current status, and a
  press changes the task's status exactly as the same press on its project's list does. Every move
  interaction pressed on an All tasks row lands on All tasks, never on the project's list or the
  task's page, with the same filter and sort choices shown in the controls and carried in the address:
  a move, the confirmation of a move to `cancelled` in place in the row, its back out, the confirming
  press, a refused move, and a failed move. The confirmation and back-out addresses opened again once
  the task is in a final status show the refusal beside the task's status in its row. The completion,
  refusal and failure lines, and where the page opens, are those of a project's list (CP-407, CP-409;
  SDD § 4 EX-5, EX-6, EX-14). A confirmation shows only on a row the page lists. These landings keep
  NFDR QC-63's response contract: 202 for a page showing a pending confirmation, 200 for every other,
  each with `Cache-Control: no-store`. *(Request; UXD UX-F4, UX-I2, UX-I7, UX-S7 "As UX-S4"; SDD § 6
  S-5, § 4 EX-7, RT-11; NFDR QC-63)*
- **CP-476:** A move pressed on All tasks after which the task no longer matches its choices — out of
  the status it is filtered by, or to `done` or `cancelled` under the Overdue filter — lands on All
  tasks without that task. One completion line names the task and its new status and says it no longer
  matches the filter and has left this list. The line sits above the task list, and the page opens
  there, with keyboard focus on the element the line describes. When no task is left matching, the
  page shows the CP-471 state with the line above it. *(Request; UXD UX-F4; SDD § 6 S-5, § 4 EX-5,
  EX-14; `CONTENT.md` § Completed, "You moved 'Set up CI' to done, so it no longer matches the status
  filter and has left this list.")*
- **CP-477:** A move pressed on an All tasks list whose filter or sort choice CP-474 would refuse saves
  nothing, opens no confirmation, and lands on All tasks showing the refusal. *(FDR R-100; NFDR QC-38)*
- **CP-478:** A move pressed on a project's list or on a task's page lands where it lands today. A
  move pressed on All tasks for a task that no longer exists answers as the same press on a project's
  list does today. *(Request; FDR R-103, R-105)*

### Either way in

- **CP-479:** Reaching All tasks from the header, applying and clearing a choice, and pressing a move
  there can each be done from the keyboard alone with the browser's own keys, on a page that runs no
  script. A project name, task title, label or assignee name holding `<`, `&` or `"` shows as typed on
  All tasks, in the project column too. *(FDR R-112, R-113; SDD § 4 EX-2, EX-8, SEC-4; ADR-0003; NFDR
  QC-34, QC-36)*

### Where the code lives (fixed by the records)

- **CP-480:** The matching, ordering and refusals All tasks applies are the rules `domain/filtering.py`
  and `domain/sorting.py` hold, applied to every project's tasks. No second copy of any of them exists
  anywhere, and `application` and `web` hold none: a rule changed in one of those two modules changes a
  project's list and All tasks alike. The Overdue verdict comes from the one overdue rule the row
  marking uses. *(Request; SDD § 4 TS-3; NFDR QC-11, QC-20, QC-21, QC-23; ADR-0001, "each copy could
  drift")*
- **CP-481:** The opening docstrings of `domain/filtering.py` and `domain/sorting.py` name every
  `application` and `web` module that takes part in All tasks and every test module this change adds
  that checks them. The docstring of `domain/filtering.py` names FR-31 among the requirements it
  realizes, the row SDD § 4 TS-3's table gives `filtering`. Every test module the change adds names
  the requirements or acceptance criteria it checks. *(SDD § 4 TS-3, TS-4; NFDR QC-11)*
- **CP-482:** The change adds no saved field and no cookie. Opening, applying, reloading or clearing
  All tasks never reaches the saver. *(FDR R-94; NFDR QC-8, QC-21, QC-46, QC-54)*

### Tests (named in the request, or required by the records)

- **CP-483:** Layer-3 and layer-4 tests run in one process with the clock and the saver handed in, over
  tasks in at least two projects, and cover:
  - the header's three links on every kind of page, and the not-found page's two links in both forms
    (CP-459, CP-460);
  - every task of every project listed once, the project column's text and link, and no add-task form
    (CP-462 to CP-464);
  - the default order with tasks of two projects interleaved (CP-465);
  - the no-tasks state with no project, with only empty projects, and with a choice in the address
    (CP-466);
  - the controls and their choices, with a label carried only in a second project and one carried only
    by a task the filter leaves out (CP-467, CP-468);
  - SRS AC-14's filter and sort tests run across projects: each filter field alone, the AND
    combination, Due from alone, Due to alone, both and both equal, a task with no due date against
    each range shape, the Overdue filter on AC-13's three cases with today's date set through the
    clock handed in, each sort field in both directions, the priority order, undated last, letter case
    in a title sort, a tie on each field between tasks of two projects, and a created-time sort and a
    tie over two tasks of two projects carrying the same recorded creation time (CP-469);
  - the count, with a filter and with a sort alone, and the no-match state (CP-470, CP-471);
  - the same list from the same address opened again, and Clear (CP-472, CP-473);
  - one test per refusal kind of CP-474, each asserting the reason shown, the focus and the saved data
    unchanged;
  - each move interaction CP-475 names, pressed on an All tasks list with and without choices, with
    its landing, status code and `Cache-Control: no-store`;
  - a task moved out of a filtered status, and one moved to `done` under the Overdue filter, each
    leaving All tasks with the CP-476 line;
  - a move on a list with a refused choice (CP-477);
  - a move pressed on a project's list and on a task's page landing as today, and a move pressed on
    All tasks for a task another tab deleted (CP-478);
  - `<`, `&` and `"` in a project name, a title, a label and an assignee name (CP-479).

  *(Request; SRS AC-12, AC-13, AC-14; SDD § 4 TS-1, TS-2; NFDR QC-5, QC-28, QC-38, QC-63)*
- **CP-484:** A layer-5 test drives Chromium from the keyboard alone: from a project's page it reaches
  All tasks through the header link, applies a filter, and presses a move on a row (CP-479). *(SDD
  § 4 EX-8, TS-1; UXD UX-I6)*
- **CP-485:** The tests NFDR QC-7, QC-35 and QC-54 name cover All tasks: the route test's enumeration
  holds every route this change adds, and a route test sends the All tasks address with no choice, an
  Apply, its reload, Clear and a refused choice, and finds 200, no redirect, nothing saved, the page
  policy header and no `Set-Cookie`; the outbound-connection test drives an All tasks Apply and a move
  pressed on All tasks; and a recording-saver test opens and applies All tasks and finds the saver
  received nothing. *(NFDR QC-7, QC-8, QC-33, QC-34, QC-35, QC-54)*
- **CP-486:** The change adds no row to `tests/timed_run.py` and changes none. The run still prints
  every line it prints today, in today's order, the `filter total at 1000 tasks` and `sort total at
  1000 tasks` rows among them, each under `LIMIT_SECONDS`, which stays 1.0 second. *(Request; NFDR
  QC-48; SDD § 4 TS-5)*
- **CP-487:** Existing tests that encode what this change reverses change only there, and each keeps
  every other assertion:
  - `tests/integration/test_pages.py`: `test_every_page_has_a_header_with_the_projects_and_people_links`
    expects the three links of CP-459, admits the All tasks address among the page's links, and drops
    "all tasks" from its forbidden words, keeping "rename" and "delete";
    `test_values_are_escaped_everywhere` reads the project link one position later;
    `test_the_not_found_page_has_one_heading_and_one_link_to_projects` expects Projects then All tasks
    in `main`, three header links and five links in all;
    `test_the_not_found_page_gives_projects_in_a_paragraph_after_its_heading` expects both links in
    the one paragraph; `test_the_not_found_page_says_nothing_of_a_task` reads its sentence without the
    All tasks link's own words.
  - `tests/integration/test_people_pages.py`: `test_the_people_header_has_projects_then_people_on_the_people_page`
    and `test_people_shows_your_name_above_unchanged_assignees` expect the three links;
    `test_no_people_state_offers_an_absent_area_or_a_second_assignee_field` (nine cases) admits the
    All tasks address, and still finds no "all tasks" in `main`.
  - `tests/integration/test_people_routes.py`: `test_people_get_and_header_navigation_write_nothing`
    expects the three links and opens People from its new position.
  - `tests/integration/test_task_pages.py`: `test_task_page_shows_the_four_fields_in_the_one_authorized_form`
    expects the three header links.
  - `tests/integration/test_task_routes.py`: `test_missing_task_addresses_get_the_task_not_found_page`
    (four cases) expects Projects then All tasks in `main`; and, only if the All tasks address
    development-design picks is one of the five `test_other_unknown_paths_keep_the_project_not_found_page`
    lists, that one case leaves the list.
  - `tests/integration/test_routes.py`: `test_every_route_leaves_state_and_headers_as_the_rules_say`
    gains a sample address for each route this change adds, and a sample body for a submission route.
  - `tests/e2e/test_first_project.py`: `test_an_address_with_no_project_shows_the_not_found_page`
    expects the three header links and Projects then All tasks in `main`, and presses the Projects link
    by name.

  No other existing test is changed to fit, and no existing timed action, bar or test is loosened,
  deleted or skipped. *(Request, "every existing timed action and test stay as they are")*
- **CP-488:** These exit 0:
  - `pytest products/tracker17/tests/`, run in a fresh clone checked out at the commit under test
    (`<CORE>/roles/CROSS_ROLE.md` § Every seat; NFDR QC-47);
  - `pytest products/tracker17/tests/e2e/`, where layer 5 runs (NFDR § 9; SDD § 4 TS-1);
  - `python3 tests/timed_run.py` from the product root (NFDR QC-48);
  - from the product root, `ruff format --check .`, `ruff check .` and
    `mypy main.py errors.py domain application persistence web` (NFDR QC-62).
- **CP-489:** The code and tests this change writes run on Python 3.11. *(NFDR QC-60; SDD § 4 RT-1)*

---

## Examples

Alpha holds tasks 1 (`Fix bug`, due 2026-10-09) and 3 (`Ship`, no due date); Beta holds task 2
(`Write docs`, due 2026-10-01) and task 4 (`Plan`, due 2026-10-09), unless a row says otherwise.

| Scenario | Expected behavior | Rule |
|---|---|---|
| Any page with a header, the not-found page included | Product name, then Projects, All tasks, People. | CP-459 |
| The saved data can't be read | Its page, with no header, as today. | CP-459 |
| `/projects/99` | 404; "There's no project at this address", then a paragraph linking Projects, then All tasks. No form. | CP-460 |
| `/tasks/99` | 404; the no-task sentence, then Projects, then All tasks. | CP-460 |
| An address with nothing at it other than All tasks' own | The not-found page, as today, with both links. | CP-460, CP-461 |
| The header's All tasks link is followed | The All tasks page, 200, no redirect, nothing saved. | CP-461 |
| All tasks with no choice | Title "All tasks - tracker17", `h1` "All tasks". Rows 2, 1, 4, 3: `Write docs` (Beta), `Fix bug` (Alpha), `Plan` (Beta), `Ship` (Alpha). Each row's project column links to its project. | CP-462, CP-463, CP-465 |
| Project named `<b>&"x"` | Shown as typed in the project column. | CP-463, CP-479 |
| All tasks is read for an add-task form | None, and no rename, delete or summary control. | CP-464 |
| No project at all; or Alpha and Beta with no tasks; or either with `?filter_status=blocked` in the address | "No tasks yet" and a link to Projects. No table, no controls, no count. | CP-466 |
| All tasks with tasks | Status, Priority, Assignee, Label, Due from, Due to, Overdue, Sort by, Direction, Apply, Clear, each labelled. No message after Apply. | CP-467 |
| Label `ui` on task 2 in Beta only, `bug` on task 1 in Alpha; Status `done` applied | Label offers `bug` and `ui`, though neither task is listed. Assignee offers the current list in its order. | CP-468 |
| Priority `high` applied; tasks 1 (Alpha) and 4 (Beta) are `high` | Tasks 1 and 4, in due-date order with ties by task number. | CP-469 |
| Sort by Due date, Descending | 1 and 4 (both 2026-10-09, task 1 first), then 2, then 3 (undated last). | CP-469 |
| Sort by Created time, Descending; tasks 2 and 3 carry the same recorded creation time | 4, 3, 2, 1. | CP-469 |
| Sort by Title, no filter | Every task in title order, with the count of every task, worded without claiming a filter. | CP-470 |
| Status `in-progress`, with no task in it | Nothing matched, the filter named as the reason, Clear in view. No table, no count. | CP-471 |
| A filtered and sorted All tasks address is reloaded or opened from a bookmark | The same list in the same order. 200, no redirect. Saved data unchanged. | CP-472 |
| A fresh visit to the All tasks address | Every task, default order, no choice. | CP-472 |
| Clear after a filter and a sort | Every task, CP-465 order, Sort by Due date, Direction Ascending, no count, no choice in the address. | CP-473 |
| Due from 2026-10-09, Due to 2026-10-01 | The wrong-way-round reason at Due from. Focus on Due from. No list. Saved data unchanged. | CP-474 |
| Assignee `Zed`, not on the list; or Status `blocked`; or Sort by `colour`; or Status sent twice | Refused at that field, with the reason a project's list gives. | CP-474 |
| Label `nothing-carries-this` | Not refused: the no-match state. | CP-474, CP-471 |
| `in-progress` pressed on task 1's row, list sorted by Title | Task 1 now `in-progress`; lands on All tasks with the Title sort kept, the completion line, 200, `no-store`. | CP-475 |
| `cancelled` pressed on task 4's row | The confirmation in place in that row on All tasks, 202, `no-store`. Back out, and the confirming press, each land on All tasks. | CP-475 |
| A move pressed after another tab moved the task | The refusal on All tasks naming the moves the task now allows. | CP-475 |
| The confirmation address reopened after the task reached `cancelled` | The refusal beside the task's status in its All tasks row. | CP-475 |
| Status `todo` applied; `in-progress` pressed on task 2 | Task 2 leaves the list. "You moved 'Write docs' to in-progress, so it no longer matches the status filter and has left this list." above the list, focus there. | CP-476 |
| Overdue on; `done` pressed on the only overdue task | It leaves the list; the line above the no-match state. | CP-476 |
| Address carries Sort by `colour`; a move is pressed in a row | Nothing saved, no confirmation; All tasks shows the Sort by refusal. | CP-477 |
| A move pressed on Alpha's list, or on a task's page | Lands where it lands today. | CP-478 |
| A move pressed on All tasks for a task another tab deleted | The task not-found page, as from a project's list today. | CP-478 |
| Tab to the header's All tasks, Enter; Tab to Status, choose, Enter on Apply; Tab to a move, Space; scripting off | Each done with no pointer. | CP-479, CP-484 |
| The suite after the change | No copy of a filter or sort rule outside the two domain modules. | CP-480 |
| The two domain docstrings and the pointer test | Name the All tasks participants and checks, FR-31 in `filtering`; the pointer test passes. | CP-481 |
| All tasks applied under a recording saver | The saver receives nothing. No saved field added. | CP-482, CP-485 |
| Layer-3/4 suite | Each case CP-483 lists is present and passes. | CP-483 |
| Layer-5 suite | The keyboard test of CP-484 passes. | CP-484 |
| Route, audit-hook and recording-saver tests | Each covers All tasks. | CP-485 |
| `python3 tests/timed_run.py` | Today's lines, unchanged, with the filter and sort totals under 1.0 s. Exit 0. | CP-486 |
| The tests CP-487 names, after the change | Each asserts the new links or position and keeps its other assertions. | CP-487 |
| The commands of CP-488 | Each exits 0. | CP-488 |
| A Python 3.11 interpreter | Runs the code and tests this change writes. | CP-489 |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| Today no address answers an All tasks page, and the header holds Projects and People only (CP-459, CP-461). | In a fresh clone at `3dad1af9a`, a probe built two projects with one task each through the real `Site` and requested `/tasks`, `/all-tasks`, `/tasks?filter_status=todo`, `/projects/1` and `/nothing`. | `/projects/1` 200; each other 404 with "There's no project at this address" and one `main` link, to `/`; every header `<nav><a href="/">Projects</a><a href="/people">People</a></nav>`. |
| The All tasks link in the header and the not-found link break exactly the existing tests CP-487 names under `tests/integration/` (CP-487). | In the same clone, `pytest products/tracker17/tests/` at the untouched commit, then again with `web/pages.py` given a stand-in third header link (`/tasks`, between Projects and People) and "Open Projects or All tasks." on both not-found pages. | Untouched: `1846 passed`. Stand-in: `22 failed, 1824 passed` — the five `test_pages.py` tests, the three `test_people_pages.py` tests (nine cases of one), the `test_people_routes.py`, `test_task_pages.py` tests and the four cases of `test_missing_task_addresses_get_the_task_not_found_page` CP-487 names. |
| The not-found end-to-end test pins the two header links and one `main` link, and clicks `main a` (CP-487). | `tests/e2e/test_first_project.py:196-211` read; the end-to-end suite was not run, as no Playwright install is on this machine. | `assert header == [tracker.address + "/", tracker.address + "/people"]`, `assert body == [tracker.address + "/"]`, `page.locator("main a").click()`. |
| The route test requires every route to have a sample address (CP-485, CP-487). | `tests/integration/test_routes.py:304` read. | `assert {route.pattern for route in ROUTES} == set(SAMPLE_ADDRESS)`. |
| `/tasks` is one of five addresses a test holds to the project not-found page (CP-487). | `tests/integration/test_task_routes.py:431-433` read. | `["/tasks/abc", "/tasks/", "/tasks", "/projects/1/tasks", "/tasks/1/x"]`. |
| The timed run today exits 0 with the filter and sort totals under the limit (CP-486). | `python3 tests/timed_run.py` from the product root of the same clone, untouched. | Exit 0; last lines `filter total at 1000 tasks: 6.3 ms` … `sort total at 1000 tasks: 14.4 ms`. |
| Task numbers come from one counter for every project, so ascending task number is creation order across projects (CP-465, CP-469). | `domain/state.py:32` read; ADR-0008. | One `next_task_id: int = 1` in the state; no per-project counter. |
| A project's label choices come from every task of the project, never from the matches (CP-468). | `domain/filtering.py:126-134` read. | "Labels come from every task of the project, never from the matches, so filtering a labelled task out does not remove its choice." |
| A project's list with no tasks checks no choice in its address today (CP-466 follows it). | `domain/sorting.py:177-181` and `domain/filtering.py:146-148` read. | `if options.task_count == 0:` returns the empty selection before either input is checked. |
| A project's no-match state shows the sentence and Clear, with no count (CP-471). | `tests/integration/test_filter_pages.py:162-176` read. | Asserts the no-match sentence, no table, no "no tasks yet", and "this filter" nowhere else on the page. |
| A project's row today carries the title link, status, priority, the assignee or "unassigned", labels, the due date and the moves (CP-462). | `web/pages.py:926-931` and `:943` read. | `"unassigned"` when no assignee; the title links to `/tasks/{task.id}`; `_TASK_COLUMNS = ("Title", "Status", "Priority", "Assignee", "Labels", "Due date", "Moves")`. |
| A move pressed on a list lands on the project's list, and one for a missing task goes to the task's address (CP-475, CP-478). | `web/routes.py:814-827` read. | `if task is None: return self._redirect(task_address)`; `place` is `/projects/{task.project_id}` for `place=list`, else the task's address. |
| The project's highest rule identifier is CP-458 (numbering starts at CP-459). | `grep -rhoE 'CP-[0-9]+'` over `system/projects/tracker17/journey/tobiishi/trail/` and the product tree, numbers sorted. | `458`. |

No rule pins output that renders a language-level fact. Every pinned output is text, a number, a link or
an order the product chooses, so no language-rendering row is owed.

---

## Out of Scope

- The project summary and its links into a filtered list (UXD UX-F6, UX-S5; SRS FR-38; FDR R-96 to
  R-99). The request: "The project summary and its links into a filtered list are a later seed and are
  not here." The product has no summary page or route (`web/routes.py:105-123`). Handed on in
  `deferred_decisions.md`.
- A summary across projects (FDR OOS-10; UXD § 4, "It has no summary").
- Adding a task from All tasks. A task is created in a project, as today.
- More than one value in a filter field, or sorting by more than one field (FDR OOS-8).
- Any change to what a filter matches, how a sort orders or what either refuses (CP-393 to CP-445
  stand), and to a project's list, its controls and its move landings.
- Remembering choices between sittings (UXD UX-I7).
- A new timed action, or any change to `LIMIT_SECONDS`.
- The form of the All tasks address (CP-461). It is development-design's.
- The wording of every line. The content stage writes it to `CONTENT.md`'s rules.
- How the page looks. The design stage takes it from `docs/DESIGN.md` (SDD § 4 EX-10).
- Renaming and deleting a project or a task (SDD § 6 S-7).

---

## Locked Answers (the divergence record — self-review 2026-10-28)

- **Gap 1 — the header's link order (b):** Projects, All tasks, People (CP-459). The request says only
  that the header gains the link. DESIGN.md § Layout fixes that order for the three links.
- **Gap 2 — the not-found page's two forms (b):** both the project and the task form gain the All tasks
  link (CP-460). UXD UX-S10 covers both, and `CONTENT.md` § Error gives both two-place sentences.
- **Gap 3 — the All tasks address (b):** a page of its own, its form left to development-design
  (CP-461), as CP-113 left a task's address. Every other address with nothing at it keeps the
  not-found page, so no existing address changes meaning beyond the one All tasks takes.
- **Gap 4 — what the project column shows (b):** the project's name as a link to its page with no
  choice (CP-463). FDR R-81 asks for the task's project; the name is how every other page shows a
  project, and a link carrying no choice opens the project's list in its default state, which UXD
  UX-I7 gives every fresh visit.
- **Gap 5 — the order across projects (b):** one order over every task, with the project playing no
  part (CP-465). FR-36 and UXD UX-F5 define the order by the sort field alone, and grouping by project
  would add a sort key the records do not have. Task numbers are unique across every project and
  rise in the order tasks are created (FDR R-44; ADR-0008), so ascending task number is creation order
  across projects.
- **Gap 6 — the empty All tasks (b):** no controls and no refusal, whatever the address carries
  (CP-466). A project with no tasks shows no controls and checks no choice today (CP-393), and with no
  task there is no list for a choice to narrow.
- **Gap 7 — the label and assignee choices (b):** labels from every task of every project, never only
  the matches; assignees from the current list (CP-468). SDD § 6 S-5 says "the labels carried in the
  list's scope", and the project list already keeps a filtered-out label among its choices.
- **Gap 8 — the count and the no-match state (b):** as a project's list shows them (CP-470, CP-471):
  a count when a choice is applied and a task is listed, and the no-match sentence with no count. The
  request asks for "the match count" and that "a filter matching nothing says so", and UXD UX-S7 says
  "No match: as UX-S4".
- **Gap 9 — every move interaction lands on All tasks (b):** CP-475 to CP-477. The request says a move
  "shows All tasks again"; UXD UX-F4 says "the operator stays where they were" and UX-S7's error state
  is "As UX-S4", which takes in the confirmation, back out, refused, failed and address-reached cases.
- **Gap 10 — no timed row for All tasks (b):** CP-486. NFDR QC-48 asks the run to time each action
  SRS NFR-1 lists. Filtering and sorting are those actions, and the run already times each over its
  1,000-task volume. All tasks adds a place to filter and sort, not a new action, and the request
  keeps every existing timed action as it is.
- **Gap 11 — refusals on All tasks, one test each (e):** CP-474 and CP-483. The request names only the
  reversed range. SRS AC-12 asks for one test per refusal, and NFDR QC-5 and QC-38 bind each refusal
  wherever a request can reach it; All tasks is a new way to reach each.
- **Gap 12 — AC-13's overdue cases across projects (e):** CP-483. The request names AC-14. SDD § 6
  S-5's *Command* adds AC-13's agreement between the overdue filter and the marking, and NFDR QC-28
  sets today's date through the clock handed in.
- **Gap 13 — the docstrings, the route, audit-hook and recording-saver tests (e):** CP-481 and CP-485,
  from SDD § 4 TS-3 and TS-4, NFDR QC-11, QC-7, QC-35 and QC-54, each stated over every participating
  module, route or action.
- **Gap 14 — the move pages' response contract (e):** CP-475. NFDR QC-63 covers every page a move
  lands on, and All tasks adds such pages.
- **Gap 15 — the end-to-end keyboard test (b):** CP-484. The request asks for page tests. SDD § 4 EX-8
  requires every action to work from the keyboard alone, and only a browser presses keys; one test
  covers the way in, a choice and a move.
- **Gap 16 — Ruff, mypy, the end-to-end suite and Python 3.11 (e):** CP-488 and CP-489, from NFDR
  QC-62, § 9, QC-60 and SDD § 4 TS-1. The request names only `pytest products/tracker17/tests/` and the
  timed run.
- **Gap 17 — no text field, so QC-9 and QC-36's text-field checks have nothing to bind:** All tasks adds
  no text field. CP-479 still holds typed names, titles and labels to FDR R-112 where they show.
- **Gap 18 — existing tests named as changing (f):** CP-487. The request says every existing test
  stays as it is. The probe in Verified Claims shows that no header carrying All tasks, and no
  not-found page linking to it, leaves those tests unchanged; the route test's equality and the
  end-to-end not-found test were read. Each keeps its name and every assertion beyond the links, their
  position, or the route it lists.
