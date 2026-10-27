# Change Spec — a project's task list narrows by filter

**Date:** 2026-10-27
**Category:** feature
**Behaviour:** changing
**Request:** Let the operator narrow a project's task list by filter. The list gains controls for status, priority, assignee, label, a due-date range (from and to, either optional) and overdue, each taking one value. Apply shows only the tasks that match all the fields set (AND, FR-32 to FR-35), with the count of matches and the choices still shown. The choices appear in the address, so a reload shows the same list. Clear returns to every task. The rules live in a new `domain/filtering.py` (SDD § 4 TS-3). A from-date later than the to-date is refused with FR-34's reason and the saved data is unchanged; an assignee not on the current list is refused under FR-33; a filter that matches nothing says so and shows Clear. A task moved out of a status the list is filtered by leaves the list, and the completion line names it (UX-F4). The overdue filter must agree with the list's overdue marking on AC-13's three cases. Extend `tests/timed_run.py` to time one filter, in the run's existing manner (the 1,000-task fixture, a failure on a refused or failed action, POST/GET and total each under `LIMIT_SECONDS`, 1.0 second), and print the fixture used. Done when `domain/filtering.py` exists; in a browser or through `web` each of the six filters shows only matching tasks with the count and the choices still shown, a reload keeps the list, and Clear shows every task; the reversed range and the no-match case behave as above; the moved-out task leaves a filtered list with its completion line; `pytest products/tracker17/tests/` exits 0, including SRS AC-14's filter tests (each field, the AND combination, both range ends), AC-12's reversed-range test and the overdue-agreement test on AC-13's three cases; and `python3 products/tracker17/tests/timed_run.py` exits 0 and shows a timed filter under 1.0 second. Sizing: the acceptance boundary is one capability, filtering a project's list (station reached-when 1–6, SRS FR-32 to FR-35), and it maps to one merge; sorting and the All tasks list are the next two stations and are not here. What must not be weakened: no sorting, no All tasks list or header link and no summary; the list's order stays as it is today; the limit and every existing timed action and test stay as they are; each filter field accepts one value only.
**Language resolution:** Python — step 1 (`project.md` `Languages:`) — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with every concern it routes

---

## Change Summary

A project's task list gains filter controls. Apply narrows the list to the tasks matching every field
set, shows the count and keeps the choices in the controls and the address, and Clear shows every task
again. A reversed date range and an assignee off the list are refused, and a task moved out of a
filtered list leaves it with a line that says so. The timed run times one filter.

Paths below are relative to the product root, which `system/projects/tracker17/project.md`
`Product path:` names. `SRS`, `SDD`, `UXD`, `FDR`, `NFDR` and `CONTENT.md` are the product's
documents under `docs/`.

**Sizing.** One capability, filtering one project's list (SRS FR-32 to FR-35; SDD § 6 S-5, its
filtering half). Every rule below is that capability, its refusals, its effect on a move pressed on a
filtered list, or a check a record requires of it. One merge.

---

## Rules

### The filter controls

- **CP-393:** A project's page whose project has at least one task shows filter controls above its task
  list: Status, Priority, Assignee, Label, Due from, Due to and Overdue, then Apply and Clear. Each
  field has a visible label. A project with no tasks shows its page as today, the first-task
  invitation and the add-task form, with no filter controls, whatever its address carries.
  *(SRS FR-32; UXD UX-F5, UX-S4; SDD § 4 EX-9)*
- **CP-394:** Each field takes one value, or none (Request; FDR R-82; FDR OOS-8). The choices offered:
  - Status: the four statuses. Priority: the four priorities.
  - Assignee: the names on the current assignee list, in the list's order, earliest added first,
    as the People page shows them. (SRS FR-33; UXD UX-F5)
  - Label: each distinct label the project's tasks carry, once, in code-point order compared exactly.
    (UXD UX-F5, RN-11)
  - Due from and Due to: a calendar date each.
  - Overdue: on or off.
- **CP-395:** Every word the controls, the count, the no-match state, the refusals and the lines of
  CP-408 show follows `docs/CONTENT.md` (SDD § 4 EX-11). The field names are "Due from", "Due to" and
  "Overdue" (`CONTENT.md` terminology rows for a due date and for overdue). Applying or clearing a
  filter shows no message (`CONTENT.md` § Voice, "A reading action, such as applying a filter …
  produces no message"). The wording belongs to the content stage.

### Applying a filter

- **CP-396:** Apply shows only the project's tasks that match every field set. A field with no value
  narrows nothing. A task matches:
  - Status, Priority: when it holds that value.
  - Assignee: when it carries exactly that name.
  - Label: when it carries exactly that label, compared exactly (FDR R-83).
  - Due from / Due to: when its due date is on or after Due from and on or before Due to, either end
    optional. A task with no due date matches no range with an end set (FDR R-85, R-86).
  - Overdue on: when it is overdue under FDR R-68, as of the machine's local date at the moment the
    page is built — the same verdict as the row's Overdue marker on that page (FDR R-69, R-99).
- **CP-397:** The matching tasks show in the order the unfiltered list shows them today: earliest due
  date first, tasks with no due date last, ties in creation order, realized as ascending task number
  in each title link's address. Each row is as today: its columns,
  its Overdue marker and its moves. *(Request, "the list's order stays as it is today"; UXD UX-F5
  Defaults)*
- **CP-398:** With at least one field set, the page shows the number of matching tasks, and every
  control shows the choice applied, a label no task carries included. The page opens at its start.
  *(Request; UXD UX-F5, UX-S4; SDD § 4 EX-5)*
- **CP-399:** The choices are carried in the list page's address and stored nowhere else. Opening that
  address again — a reload, Back, a bookmark — shows the same filtered list, worked out against the
  saved data and the local date at that moment. A visit to the project's address with no choices
  shows every task. Applying, reloading or clearing a filter never changes the saved data.
  *(FDR R-94, R-101, R-106; UXD UX-I7; SDD § 4 EX-3; ADR-0006)*
- **CP-400:** Clear shows every task of the project in the CP-397 order, every control at no value,
  and an address carrying no choice. *(Request; UXD UX-F5)*
- **CP-401:** When the project has tasks and none matches, the page says nothing matched and names the
  filter as the reason, never "no tasks", with Clear in view and the controls showing the choices. It
  shows no table and no blank space. *(SRS FR-37; FDR R-95; UXD UX-S4; `CONTENT.md` § Empty)*

### Refusals

- **CP-402:** A Due from later than Due to is refused, with a reason saying the dates are the wrong way
  round. No result and no no-match line is shown in its place. Due from equal to Due to is accepted
  and matches tasks due that day. *(SRS FR-34; FDR R-87)*
- **CP-403:** An Assignee value that is not a name on the current assignee list, compared exactly, is
  refused with the reason. This covers a name removed after the page was loaded and a name typed into
  the address. A task carrying a removed name cannot be found by its assignee. *(SRS FR-33; FDR R-84)*
- **CP-404:** A value no control sends is refused with a reason at its field. The class is closed by
  field: a Status or Priority value outside the four, a Due from or Due to that is not a calendar
  date, an Overdue value other than the one its control sends, and any field given more than one value,
  Label included. A single Label value is never refused: a label no task carries matches nothing
  (FDR R-83, CP-401). *(Request, "each filter field accepts one value only"; FDR R-51, R-100)*
- **CP-405:** On every refusal of CP-402 to CP-404:
  - the saved data is unchanged, and no task list result is shown;
  - the controls hold the choices as sent, and each refused field shows its own reason beside it;
  - the page opens with keyboard focus on the first refused field in the controls' order, its reason
    as the field's accessible description;
  - Clear is in view.

  *(SRS FR-39; FDR R-100; SDD § 4 EX-4, EX-14; UXD UX-I3)*
- **CP-406:** Each refused condition this change adds has its own refusal type, defined and raised in
  `domain` and handed to `web` through `application`. `web` maps each type to its reason, and no part
  tells one refusal from another by reading its message. *(NFDR QC-5, QC-16; SDD § 4 OB-4)*

### A move pressed on a filtered list

- **CP-407:** Every move interaction pressed in a row of a filtered list lands on that list with the
  same choices applied, shown in the controls and carried in the address: a move, the confirmation of
  a move to `cancelled`, its back out, the confirming press, and a refused or failed move. On an
  unfiltered list each behaves as today. These landings keep NFDR QC-63's response contract: 202 for
  a page showing a pending confirmation, 200 for every other, each with `Cache-Control: no-store`.
  *(UXD UX-F4, UX-I7; NFDR QC-63; SDD § 4 RT-11)*
- **CP-408:** A move after which the task no longer matches the list's choices — out of the status
  filtered by, or to `done` or `cancelled` under the Overdue filter — lands on a list without that
  task. One completion line names the task and its new status, and says it no longer matches the
  filter and has left this list. The line sits above the task list, and the page opens there, with
  keyboard focus on the element the line describes. When no task is left matching, the page shows the
  CP-401 state with the line above it. *(Request; UXD UX-F4; SDD § 4 EX-5, EX-14; `CONTENT.md`
  § Completed, "You moved 'Set up CI' to done, so it no longer matches the status filter and has left
  this list.")*
- **CP-409:** A refusal or failure line about a move whose task is not in the filtered list the page
  shows — for example, a task another tab moved out of the filtered status — sits in the place CP-408
  names, and the page opens there. *(SDD § 4 EX-4, EX-5; UXD UX-I3)*

### Either way in

- **CP-410:** A filter address for a project that does not exist shows the not-found page, as an
  address for a missing project does today. *(FDR R-105; SDD § 4 EX-13)*
- **CP-411:** Applying and clearing a filter can each be done from the keyboard alone with the
  browser's own keys, and work on a page that runs no script. A label or an assignee name holding
  `<`, `&` or `"`, or surrounding spaces, shows as typed among the choices and in the controls after
  Apply, and a filter on it matches the tasks carrying it. *(FDR R-112, R-113; SDD § 4 EX-2, EX-8;
  ADR-0003; NFDR QC-34, QC-36)*

### Where the code lives (fixed by the records)

- **CP-412:** The filter rules — matching and the refusals of CP-402 to CP-404 — live in a new module,
  `domain/filtering.py`. `application` applies them and holds no rule of its own, and `web` holds no
  filter rule (SDD § 4 TS-3; NFDR QC-11, QC-20, QC-21, QC-23). The Overdue filter's verdict comes
  from the one overdue rule the list marking uses (ADR-0001, "the overdue rule appears on two lists, a
  filter and the summary … each copy could drift"). The opening docstring of `domain/filtering.py`
  names the SRS requirements it realizes, FR-32 to FR-35 among them, every `application` and `web`
  module that takes part, and the test modules that check it. The word `filtering` is listed as landed
  in the pointer test, `tests/architecture/test_trace.py`. Every test module the change adds names the
  requirements or acceptance criteria it checks. *(SDD § 4 TS-3, TS-4; NFDR QC-11)*
- **CP-413:** The change adds no saved field and no cookie. Applying, reloading or clearing a filter
  never reaches the saver. *(FDR R-94; NFDR QC-8, QC-21, QC-46, QC-54)*

### Tests (named in the request, or required by the records)

- **CP-414:** Unit tests cover `domain/filtering.py` with no file and no clock: each field alone; the
  AND combination; Due from alone, Due to alone, both, and both equal; a task with no due date against
  each range shape; exact label comparison; a list with no field set; the reversed range; the unlisted
  assignee; and each kind of CP-404 refusal. *(SRS AC-14, AC-12; SDD § 4 TS-1)*
- **CP-415:** A test sets today's date through a clock handed in, with no name patched in a product
  module, and checks AC-13's three cases: an open task due yesterday is overdue, a task due today is
  not, a task due yesterday in `done` or in `cancelled` is not. The list's Overdue marker and the
  Overdue filter agree on all three. *(SRS AC-13; FDR R-99; NFDR QC-28; SDD § 4 TS-2)*
- **CP-416:** Layer-3 and layer-4 tests run in one process with the clock and the saver handed in, and
  cover:
  - the controls and their offered choices on a project with tasks, and no controls on a project with
    none (CP-393, CP-394);
  - each field through `web`, the AND combination and both range ends, with the count and the choices
    shown (CP-396 to CP-398);
  - the same list from the same address opened again, and Clear (CP-399, CP-400);
  - the no-match state (CP-401);
  - one test per refusal — the reversed range, the unlisted assignee and each CP-404 kind — each
    asserting the reason shown, the focus, and the saved data unchanged (CP-402 to CP-405);
  - a move from a filtered list keeping the choices, for each interaction CP-407 names, with its
    status code and `Cache-Control: no-store`;
  - a task moved out of a filtered status, and one moved to `done` under the Overdue filter, each
    leaving the list with the CP-408 line;
  - a label and a name holding `<`, `&` and `"` (CP-411).

  *(Request; SRS AC-12, AC-14; NFDR QC-5, QC-38, QC-63)*
- **CP-417:** Three existing tests cover the filter: the route test of NFDR QC-7 covers any route this
  change adds and finds a filter request leaves the state unchanged; the outbound-connection test of
  NFDR QC-35 drives an Apply; and a recording-saver test under NFDR QC-54 applies a filter and finds
  the saver received nothing. *(NFDR QC-7, QC-8, QC-34, QC-35, QC-54)*
- **CP-418:** `python3 tests/timed_run.py`, run from the product root, times one filter on a fixture of
  its own: 1,000 tasks in one project with 20 comments on every task, at ordinary text lengths, saved in
  a location of its own inside the run's temporary directory and distinct from every other fixture. The
  filter is Status `in-progress`. Its requests are marked `Sec-Fetch-Site: same-origin`, as a press on
  the page is. The product's own `data/` is as the run found it. *(Request; NFDR QC-48, QC-32; SDD
  § 4 TS-5)*
- **CP-419:** The run prints every line it prints today, unchanged and in today's order, the last being
  the `move total at 1000 tasks: …` row. After them it prints exactly four more, in this order, and
  nothing after them:
  1. `filter fixture: {tasks} tasks, {per task} comments each ({all} in all); title of {T} characters, comment of {C} characters; status {status}, {M} matching`
  2. `filter a task list at 1000 tasks: {ms} ms{problems}`
  3. `filter landing page at 1000 tasks: {ms} ms{problems}`
  4. `filter total at 1000 tasks: {ms} ms{problems}`

  `{tasks}`, `{per task}` and `{all}` are read from the fixture as loaded, as the move's fixture line
  reads them. `{T}` and `{C}` are the lengths, in code points, of the title and the first comment of the
  first task the filtered list shows. `{status}` is the status filtered by and `{M}` the number of the
  fixture's tasks holding it. `{ms}` and `{problems}` are written as every existing row writes them.
- **CP-420:** Row 2 times the request the Apply press sends. Row 3 times a request for the filtered
  list's address, the one a reload opens: where Apply is answered by a redirect, the address it sends
  the browser to; otherwise, the address Apply's own request asked for. Row 4 is their sum. Each must
  be under `LIMIT_SECONDS`, 1.0 second, which stays as it is.
- **CP-421:** The filter counts only when it happened. Row 2 fails when Apply is answered with a
  refusal or a failure. Row 3 fails unless its page answers 200 and lists exactly the `{M}` tasks
  holding the filtered status, every one and no other, with the count `{M}`. Row 4 fails when either
  does. When Row 2 fails, Row 3 is not requested, reads `0.0 ms — refused or failed`, and Row 4 is
  Row 2's time with the same problem. The run fails, non-zero, on any failing row, and when the
  fixture's saved data is not byte for byte what it was before the filter. *(Request; NFDR QC-48)*
- **CP-422:** Tests in `tests/integration/test_timed_run.py` feed the filter harness a refused Apply, a
  landing listing a task that does not match, and a landing missing one that does, and find each
  verdict non-zero; a slow Apply, a slow landing, and a total at 1.0 second with both parts under it,
  each failing its rows; and a test on the CP-419 fixture line, read from a fixture other than the
  run's own. *(SDD § 4 TS-1; SRS C-6)*
- **CP-423:** Existing tests that encode what this change reverses change only there, and each keeps
  every other assertion:
  - `test_only_the_task_features_are_added_to_domain` in `tests/architecture/test_shapes.py` stops
    asserting that `domain/filtering.py` does not exist. Its `sorting` and `summary` absences and its
    `TrackerState` fields stay.
  - The tests in `tests/integration/test_timed_run.py` that hand `main` a fixed list of timer readings,
    and the six that use the `whole_run` fixture, change by the readings the filter takes. The two that
    assert the whole run's lines in order, `test_timed_run_appends_exactly_three_ordered_action_blocks`
    and `test_timed_run_appends_exact_move_block_and_nothing_after`, also change by the four lines of
    CP-419 after the move block. Verified Claims lists the 21.

  No other existing test is changed to fit, and no existing timed action, bar or test is loosened,
  deleted or skipped. *(Request, "every existing timed action and test stay as they are")*
- **CP-424:** These exit 0:
  - `pytest products/tracker17/tests/`, run in a fresh clone checked out at the commit under test
    (`<CORE>/roles/CROSS_ROLE.md` § Every seat; NFDR QC-47);
  - `pytest products/tracker17/tests/e2e/`, where layer 5 runs (NFDR § 9; SDD § 4 TS-1);
  - `python3 tests/timed_run.py` from the product root (NFDR QC-48);
  - from the product root, `ruff format --check .`, `ruff check .` and
    `mypy main.py errors.py domain application persistence web` (NFDR QC-62).
- **CP-425:** The code and tests this change writes run on Python 3.11. *(NFDR QC-60; SDD § 4 RT-1)*

---

## Examples

| Scenario | Expected behavior | Rule |
|---|---|---|
| Project with 3 tasks; its page is opened | Controls Status, Priority, Assignee, Label, Due from, Due to, Overdue, Apply, Clear above the list, each field labelled. | CP-393 |
| Project with no tasks; its address carries a Status choice | Today's page: the first-task invitation and the add form. No controls. | CP-393 |
| Assignee list `dana`, `ali` (added in that order); tasks carry labels `ui`, `Bug`, `bug` | Assignee offers `dana`, `ali`. Label offers `Bug`, `bug`, `ui`, each once. | CP-394 |
| A filter is applied | No "applied" message. Field names read "Due from", "Due to", "Overdue". | CP-395 |
| Status `todo` and Priority `high` | Only tasks in `todo` with priority `high`, in today's list order, with their count. | CP-396, CP-397, CP-398 |
| Label `Bug` where tasks carry `bug` | The no-match state: says nothing matched, names the filter, shows Clear. | CP-396, CP-401 |
| Due from 2026-10-01, no Due to; one task undated, one due 2026-10-05 | Only the task due 2026-10-05. | CP-396 |
| Today 2026-10-06; A due 10-05 `todo`, B due 10-06 `todo`, C due 10-05 `done`; Overdue on | Only A, and only A carries the Overdue marker. | CP-396, CP-415 |
| The filtered page is reloaded, or reopened from a bookmark | The same filtered list, choices still shown. The saved data is unchanged. | CP-399 |
| Clear | Every task in today's order, every control at no value, no choice in the address. | CP-400 |
| Due from 2026-10-10, Due to 2026-10-01 | Refused: the dates are the wrong way round. No result and no no-match line. Focus on Due from. Saved data unchanged. | CP-402, CP-405 |
| Due from and Due to both 2026-10-05 | Tasks due 2026-10-05. | CP-402 |
| `carol` removed from the list in another tab; Apply with Assignee `carol` | Refused at Assignee with the reason. | CP-403, CP-405 |
| Address carries Status `blocked`, or Status twice, or Due to `2026-02-30` | Refused at that field with a reason. | CP-404, CP-405 |
| Reversed range and Status `blocked` together | Both fields show their reasons. Focus on Status, the first in order. | CP-405 |
| Each refusal kind | Its own refusal type from `domain`, mapped by type in `web`. | CP-406 |
| List filtered by Priority `high`; `in-progress` pressed on a row | Lands on the same filtered list, choices in controls and address, the row showing its new status. 200, `no-store`. | CP-407 |
| List filtered by Status `todo`; `cancelled` pressed on a row | The confirmation shows on the same filtered list, answered 202 with `no-store`. | CP-407 |
| List filtered by Status `todo`; `in-progress` pressed on `Set up CI` | `Set up CI` is not in the list. A line above the list names it, its new status, and that it left the list. Focus there. | CP-408 |
| Same, and `Set up CI` was the only `todo` task | The no-match state, with the line above it. | CP-408 |
| Overdue on; an overdue task moved to `done` | It leaves the list, with the CP-408 line. | CP-408 |
| List filtered by `todo`; another tab moved task T to `in-progress`; this tab presses `cancelled` on T | The refusal line about T sits above the list, where CP-408's line goes. | CP-409 |
| `/projects/99` with a filter choice | The not-found page. | CP-410 |
| Tab to Status, choose with arrow keys, Tab to Apply, Enter | The filtered list, with no pointer used. | CP-411 |
| A label `<b>&"x"` on a task; filter by it | Shown as typed among the choices and after Apply. The task matches. | CP-411 |
| The suite after the change | `domain/filtering.py` exists with its docstring, and `filtering` is listed as landed. The pointer test passes. | CP-412 |
| A filter applied under a recording saver | The saver receives nothing. No saved field is added. | CP-413, CP-417 |
| Unit suite | Each field, AND, every range shape, each refusal. | CP-414 |
| Route, audit-hook and recording-saver tests | Each covers the filter. | CP-417 |
| Layer-3/4 suite | Each case CP-416 lists is present and passes. | CP-416 |
| `python3 tests/timed_run.py` | Today's lines, then `filter fixture: 1000 tasks, 20 comments each (20000 in all); title of … characters, comment of … characters; status in-progress, 250 matching` and three rows under 1.0 s. Exit 0. | CP-418, CP-419, CP-420 |
| The harness gets a landing missing one `in-progress` task | Row 3 and Row 4 fail. Exit 1. | CP-421, CP-422 |
| The 21 timed-run tests and the shape test after the change | Each asserts the new readings, lines or module, and keeps its other assertions. | CP-423 |
| The commands of CP-424 | Each exits 0. | CP-424 |
| A Python 3.11 interpreter | Runs the code and tests this change writes. | CP-425 |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| Today a project's page ignores filter-like choices in its address and shows every task (the behaviour CP-396 replaces). | In a fresh clone at `3cff55048`, a probe built the timed run's 1,000-task fixture through the real saved data and `Site`, and requested `/projects/1`, `/projects/1?status=in-progress` and `/projects/1?status=nonsense&due_from=2026-12-01&due_to=2026-11-01`. | Each 200 with 1,000 rows, and no Apply or Clear on the page. |
| The fixture holds 250 `in-progress` tasks (CP-419's `{M}`). | The same probe counted the loaded fixture. | `in-progress in fixture: 250`. |
| Today's list order is earliest due first, undated last, ties by identity (CP-397). | `domain/tasks.py:372-380` read. | `_due_then_identity` returns `(due_date is None, due_date or date.min, id)`; `list_project_tasks` sorts by it. |
| Today a move pressed on a list lands on the project's address with no other choice (CP-407 changes this only for a filtered list). | `web/routes.py:719-768` read; the probe sent a list-row move of task 4. | `303 /projects/1?moved=in-progress&move_task=4`. |
| The assignee list shows earliest added first (CP-394). | `application/tracker.py:91-93`, `web/pages.py` `_assignee_list` read. | "Every assignee name, earliest added first"; the People list is "in the order given". |
| Adding `domain/filtering.py` breaks exactly one existing test once `filtering` is listed as landed (CP-412, CP-423). | In the clone, `pytest tests/architecture/` with a probe `domain/filtering.py` (docstring naming FR-32 to FR-35, three taking-part modules and a test module) and `"filtering"` added to `LANDED_FEATURE_WORDS`. Run also without the word, and at the untouched commit. | Untouched: `57 passed`. Probe without the word: 3 failed (`test_only_the_task_features_are_added_to_domain`, `test_each_feature_word_with_its_domain_module_is_listed_as_landed`, `test_no_excluded_feature_entry_exists`). Probe with the word: `1 failed, 56 passed`, the failure `test_only_the_task_features_are_added_to_domain`. |
| 21 existing timed-run tests cannot stay unchanged under any run that times a filter with the timer it is handed (CP-423). | In the clone, `tests/timed_run.py` got a stand-in filter block after the move, reading the handed timer four times and printing a fixture line and three rows. `python3 tests/timed_run.py` and `pytest tests/integration/test_timed_run.py` were run. At the untouched commit the same test file gave `128 passed`. | The run: exit 0, `filter total at 1000 tasks: 5.7 ms`. The tests: `15 failed, 107 passed, 6 errors`. The failures are `test_timed_run_fails_when_only_the_edit_fails`, `test_timed_run_fails_when_only_a_label_action_fails`, `test_full_timed_run_fails_when_only_name_measurement_fails`, the three `[comment]`, `[assignee add]`, `[assignee remove]` cases of each of `test_timed_run_fails_when_only_a_new_action_total_reaches_limit` and `test_timed_run_propagates_new_submission_and_landing_timing_failures`, the two cases of `test_timed_run_fails_when_only_move_total_reaches_limit`, and the four of `test_timed_run_propagates_move_submission_and_landing_timing_failures`. The six errors are the `whole_run` users: `test_timed_run_appends_exactly_three_ordered_action_blocks`, `test_new_timed_fixtures_are_independent_and_preserve_name_save_precondition`, `test_new_timed_actions_leave_product_data_unchanged`, `test_timed_run_reports_actual_fixture_lengths_for_all_three_actions`, `test_timed_run_appends_exact_move_block_and_nothing_after`, `test_timed_move_fixture_is_independent_and_product_data_unchanged`. |
| Two existing page tests pin a project with no tasks to one form (CP-393 keeps them). | `tests/integration/test_pages.py:205-222` and `tests/e2e/test_first_project.py:71-80` read. | `(form,) = root.find_all("form")` and `page.locator("main form").count() == 1`, each on a project with no tasks. |
| The project's highest rule identifier is CP-392 (numbering starts at CP-393). | `grep -rhoE 'CP-[0-9]+'` over `system/projects/tracker17/journey/tobiishi/trail/` and the product tree, numbers sorted. | `392`. |

No rule pins output that renders a language-level fact. Every pinned output is text or a number the
product chooses, so no language-rendering row is owed.

---

## Out of Scope

- Sorting a list, its controls and its default (FDR R-89 to R-93; SRS FR-36). The request: "no
  sorting". The list keeps today's order (CP-397). Handed on in `deferred_decisions.md`.
- The All tasks list, its header link and its project column (FDR R-81, second sentence; UXD UX-S7;
  SDD § 4 EX-12). The request: "no All tasks list or header link". Handed on.
- The project summary, its overdue count's agreement with the filter (FDR R-99's third leg; SRS AC-13)
  and its links into a filtered list (UXD UX-F6). The request: "no summary". The product has no
  summary today (`web/routes.py:98-116`, no summary route). Handed on.
- More than one value in a filter field (FDR OOS-8), and a filter for "no due date", "open" or
  "unassigned", which no field expresses (UXD UX-F6).
- The add-task form's answers. An add lands on the new task's page, and a refused or failed add lands
  on the project's list without the filter choices, both as today.
- Remembering filter choices between sittings (UXD UX-I7).
- The wording of every line. The content stage writes it to `CONTENT.md`'s rules (CP-395).
- How the controls look. The design stage takes it from `docs/DESIGN.md` (SDD § 4 EX-10).

---

## Locked Answers (the divergence record — self-review 2026-10-27)

- **Gap 1 — controls on a project with no tasks (b):** none; the page stays as today (CP-393). The
  request says "the list gains controls", and a project with no tasks shows no list.
  `CONTENT.md` § Empty keeps the no-tasks state free of any filter, and two existing tests pin that
  page to one form (Verified Claims).
- **Gap 2 — what each control offers, and the order (b):** CP-394. The request names the fields only.
  SDD § 6 S-5 and UXD UX-F5 bind the assignee and label choices. The label order is the one choice no
  record fixes: code-point order is deterministic and testable, and changing it later moves no rule
  elsewhere.
- **Gap 3 — the count only when a filter is set (b):** CP-398. With no field set there is nothing to
  count matches against, and leaving the unfiltered page as today keeps every existing page test true.
- **Gap 4 — values no control sends are refused (b):** CP-404. The request's "each filter field
  accepts one value only" leaves open what happens to a second value or a value outside the choices.
  Refusing states what is wrong. Ignoring the value would show a list that does not match the address.
  The product already refuses a move to a status that is not one (`web/routes.py:758-761`). A single
  label value is never refused, because FDR R-83's example has an unmatched label match nothing.
- **Gap 5 — the refused page (b):** CP-405. FDR R-87 shows no result in the refused range's place, and
  CP-405 applies the same to every refusal. Focus goes to the first refused field, following SDD § 4
  EX-4 ("opens at the control that was used"). The reversed range has two fields, and Due from comes
  first.
- **Gap 6 — the choices survive every move interaction (b):** CP-407. The request names only the
  moved-out case. Without this rule a move pressed on a filtered list would land on the unfiltered
  list, where "leaves the list" cannot be seen. UXD UX-F4 says "the operator stays where they were".
- **Gap 7 — the Overdue filter in CP-408 (b):** a move to `done` or `cancelled` takes a task out of an
  Overdue list too (FDR R-68), and it gets the same line. The request names the status filter. The
  only alternative is a task that disappears with no line.
- **Gap 8 — where the line goes when the row is gone (b):** above the list (CP-408, CP-409). Today the
  line sits in the row. SDD § 4 EX-5 sends a page whose thing "is no longer on the page" to "the top
  of the sheet the thing was on, where the completion line sits".
- **Gap 9 — which filter is timed, and the rows (b):** Status `in-progress` (CP-418), because status
  matches do not depend on today's date. The rows are named for the press and the address a reload
  opens (CP-420), not for "POST" and "GET". The request says "POST/GET and total". Which method Apply
  uses is the design's to choose, and the two rows time the press and the reload whichever it chooses.
- **Gap 10 — the fixture line and what "happened" means (b):** CP-419 and CP-421. They follow the move's
  fixture line and its readback. The landing must list exactly the matching tasks, and the saved data
  must be unchanged, because a filter that saved something would break FDR R-94.
- **Gap 11 — the harness tests (e):** CP-422. The request does not ask for them. SDD § 4 TS-1 builds
  every slice test-first, and the timed run's docstring says its harness is checked by
  `tests/integration/test_timed_run.py`.
- **Gap 12 — refusal types, the entry module's docstring and the pointer test (e):** CP-406 and CP-412.
  The request names only the module. NFDR QC-5 and QC-11 and SDD § 4 TS-3 and TS-4 require them.
- **Gap 13 — the route, audit-hook and recording-saver tests (e):** CP-417, from NFDR QC-7, QC-35 and
  QC-54, each stated over every route or action.
- **Gap 14 — one test per refusal, and the move pages' response contract (e):** CP-416. SRS AC-12 asks
  for one test per refusal. NFDR QC-63 covers every page a move lands on, and CP-407 adds those pages.
- **Gap 15 — Ruff, mypy, the end-to-end suite and Python 3.11 (e):** CP-424 and CP-425, from NFDR QC-62,
  § 9, QC-60 and SDD § 4 TS-1. The request names only `pytest products/tracker17/tests/` and the timed
  run.
- **Gap 16 — no text field, so QC-9 and QC-36's text-field checks have nothing to bind:** the controls
  offer choices, dates and a switch (CP-394; UXD RN-11). CP-411 still holds typed labels and names to
  FDR R-112 where they show.
- **Gap 17 — existing tests named as changing (f):** CP-423. The request says every existing test stays
  as it is. The probes in Verified Claims show that no `domain/filtering.py` leaves the shape test
  unchanged, and no run that times a filter with the timer it is handed leaves the 21 timed-run tests
  unchanged. Each keeps its name and every assertion beyond the readings, lines or module the change
  adds, so none is loosened or removed.
