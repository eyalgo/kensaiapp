# Change Spec — A project holds tasks the operator adds and reads back

**Date:** 2026-10-11
**Category:** feature
**Behaviour:** changing
**Request:** Let the operator put tasks in a project and see them. Run from `products/tracker17/` under `python3 main.py`. The project's page gains an add-task form: a title, a priority with `medium` chosen, an assignee control offering the names on the People list plus none, and an optional due date picked from a date picker. A project with no tasks shows an invitation to add a first task. Adding a task lands on that task's own page, which here only shows the task's title, priority, assignee and due date and changes nothing. Adding with only a title saves the task as `medium`, unassigned, undated, status `todo`. A blank title is refused on the project page where it was entered, with the typed text kept and the saved data unchanged (SRS FR-15; UXD UX-I3). The project's list shows one row per task with its title, status, priority, assignee or "unassigned", labels and due date, earliest due date first and undated last; the labels column shows what a task carries, which is none yet. An open task due before today shows the word "Overdue" beside its due date and a task due today does not (SRS FR-15, FR-24 to FR-26, AC-13 first two cases; SDD § 6 S-2; UXD UX-F3, UX-F5, UX-S4, UX-A4). A task is saved in the form every later slice acts on, so this change fixes it, following the SDD. The rules live in new `domain/tasks.py`, `domain/priorities.py` and `domain/due_dates.py`; the web and application parts call them (SDD § 4 TS-3). Every string comes from the product's content record, none invented in code.

Tests ship with it: unit tests for the three domain modules; integration tests through the real server for the form with `medium` chosen and the assignee choices, the first-task invitation, add with all four fields, add with a title only, the blank-title refusal, the list columns, the due-date order and the "Overdue" marking with today's date set by the test. `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/` each exit 0 (run on a `git archive HEAD` copy that is `git init`-ed, since the repository-ignore test needs a git repo), and `python3 products/tracker17/tests/timed_run.py` still exits 0.

**Must not be weakened or added:** `domain/labels.py` is not created and no label can be added or removed. The task page changes nothing: no edit form, and no left-the-list assignee rules (SDD § 4 RT-7, SRS AC-19). No status move, delete, filter, sort control, summary or comment is added. The saved form of the People list must not change, and no existing test is weakened to fit.

---

## Change Summary

A project's page gains an add-task form and lists the project's tasks, earliest due first, with open tasks due before today marked "Overdue". Adding a task saves it and opens the task's own page, which shows the task and changes nothing. This change realizes FDR R-39 to R-44, R-51 and R-67 to R-70 for adding and listing, and R-95's first-task invitation.

Every place below that says "the content step's words" means the wording is written in this change's text record under `products/tracker17/docs/CONTENT.md`. This spec states what each string must say. It fixes the words only where the request or CONTENT.md's terminology already fixes them: `todo`, `low`, `medium`, `high`, `critical`, "unassigned" and "Overdue".

---

## Rules

### The add-task form

- **CP-106:** A project's page shows an add-task form with four fields: a title, a priority, an assignee and a due date, and an Add button. The form is on the page whether or not the project holds tasks. *(SRS FR-15; UXD UX-F3, UX-S4)*
- **CP-107:** The title field lets in at most 200 characters. *(SRS FR-40; FDR R-76, R-79; SDD § 4 RT-10)*
- **CP-108:** The priority control offers exactly `low`, `medium`, `high` and `critical`, each written as that word, and `medium` is chosen when the page opens. The order of the four in the control is development-design's. *(SRS FR-15; FDR R-42, R-51; UXD UX-F3; CONTENT.md § Terminology)*
- **CP-109:** The assignee control offers none, and every name on the assignee list as saved when the page was built, each exactly as saved, in the list's order. None is chosen when the page opens. When the assignee list is empty, the control offers only none, and a link to People sits beside it so the operator can see why there is no one to pick. *(SRS FR-21; UXD UX-F3, decision point; SDD § 4 EX-12)*
- **CP-110:** The due-date field is filled by picking a calendar date from the browser's own date picker, or left empty. Empty is how it opens. It holds a date with no time of day. The page runs no script. *(SRS FR-24; FDR R-67; UXD UX-F3; SDD § 4 EX-2)*

### Adding a task

- **CP-111:** An add with a title that has at least one character other than whitespace and is at most 200 characters long saves a new task in that project. It saves the title exactly as typed, surrounding spaces included, with the priority, assignee and due date the form sent. Titles need not be unique, so two tasks in one project may share a title. *(SRS FR-15; FDR R-39, R-40, R-80)*
- **CP-112:** Every new task starts in status `todo`. An add that sends no priority, or an empty one, saves `medium`. One whose assignee is none, or absent, saves the task unassigned. One whose due date is empty, or absent, saves it undated. *(SRS FR-15; FDR R-41, R-42)*
- **CP-113:** Each task gets its own page address, unique across all projects. No address is given to a second task, and that holds across a stop and start of the tracker. Two tasks with the same title have different addresses. The form of the address is development-design's. *(SRS FR-15; FDR R-44; SDD § 4 EX-3)*
- **CP-114:** The tracker answers an add by sending the browser to the new task's page. Reloading that page, or reaching it again with back or forward, adds nothing. *(FDR R-106; SDD § 4 RT-8)*
- **CP-115:** The task page that answers an add carries a completion line naming the added task's title, quoted, in the content step's words. It is shown only once the task is saved. The page opens at its start, with keyboard focus on its heading, which is the task's title, as a newly created project's page does today. The completion line is the heading's accessible description, and the line itself never takes focus. *(UXD UX-I4, UX-A5; SDD § 4 EX-5, EX-14, RT-9; CONTENT.md § Message patterns, Completed)*
- **CP-116:** An add is checked against the saved data at the moment it is applied, not against what the page showed. *(FDR R-102)*

### Refusals and failures of an add

- **CP-117:** A title with no character other than whitespace, the empty title included, is refused. The saved data does not change. The project's page opens with keyboard focus in the title field. What was typed and chosen in all four fields is still there. The reason sits beside the title field and is the field's accessible description. It says a task needs a title and what to do, in the content step's words. *(SRS FR-15, FR-39; FDR R-40, R-100; UXD UX-I3, UX-A3; SDD § 4 EX-4, EX-14)*
- **CP-118:** Only a request that no page of the tracker sends can carry a title longer than 200 characters, and that title is refused. The saved data does not change. The project's page opens with keyboard focus in the title field and the reason beside it, and neither the page nor its address holds any of the sent text. A title that is too long and also blank, such as 201 spaces, gets the too-long reason. That is the order of reasons a project name and an assignee name already get (CP-20, CP-91). *(SRS FR-40; FDR R-76 to R-79; PD-11; SDD § 4 RT-8, RT-10)*
- **CP-119:** An add naming an assignee that is not on the assignee list when the add is applied is refused, and the saved data does not change. From the tracker's own form this arises only when another tab removed the name after the page loaded. The reason says the name is no longer on the assignee list and offers a reload, in the content step's words. It sits beside the assignee control, and keyboard focus is on that control. The title, priority and due date are still as entered. *(SRS FR-21; FDR R-60, R-102; UXD UX-F3, failure; UX-I3, the out-of-date refusal)*
- **CP-120:** An add sending a priority other than `low`, `medium`, `high` or `critical`, or a due date that is not a valid calendar date, is refused, and the saved data does not change. No form of the tracker's own sends either. The reason sits beside the control concerned and says what is wrong, in the content step's words. *(SRS FR-15; FDR R-51, R-100; FDR RN-6)*
- **CP-121:** An add to a project that does not exist saves nothing and is answered by the not-found page. *(FDR R-103, R-105; UXD UX-S4, error; SDD § 4 EX-13)*
- **CP-122:** When an add fails for a reason that is not a refusal, such as the save failing, the saved data and the project's tasks stay as they were. The project's page says in plain words that the add did not happen and that nothing was changed, in the content step's words, and it shows no error text from Python. What was typed and chosen is still in the form, and keyboard focus is on the Add form. The console shows a message naming the action, then the error. *(FDR R-18, R-107, R-108; UXD UX-I5; SDD § 4 OB-3)*
- **CP-123:** An add that does not come from the tracker's own pages is refused and changes nothing, under the same check every submission passes today. That covers one marked `cross-site` or `same-site`, and one not marked `same-origin`, a submission with no mark included. *(FDR R-110; SDD § 4 SEC-2)*

### The task page

- **CP-124:** A task's page shows its title, its priority, its assignee and its due date. A task with no assignee shows "unassigned", and a task with no due date shows that it has none, in the content step's words. The page has no form and no control that changes anything, and it shows nothing else of the task. Opening it changes no data. Its title follows CONTENT.md's page-title pattern, which gives "Set up CI - tracker17" for a task titled `Set up CI`. *(UXD UX-S6, narrowed by the request; FDR R-106; CONTENT.md § Accessibility of text)*
- **CP-125:** An address in the form of a task's address that names no task shows the not-found page. That page says there is no task at this address and links to Projects, in the content step's words. It offers no link to an area the tracker does not have yet. Every other address with nothing at it keeps the page it shows today. *(FDR R-105; SDD § 4 EX-12, EX-13; UXD UX-S10; CONTENT.md § Message patterns, Error)*

### The project's task list

- **CP-126:** A project that holds no task shows, in its list area, that the project has no tasks yet and an invitation to add a first one, in the content step's words, with the add-task form in view. It never shows a blank list. A project that holds at least one task shows its list and no invitation. *(SRS FR-37; FDR R-95; UXD UX-S4, empty state; CONTENT.md § Message patterns, Empty)*
- **CP-127:** The list shows one row for each task in that project and no task of any other project. Each row shows, in this order: the title, which links to the task's page; the status, written as its word; the priority, written as its word; the assignee exactly as saved, or "unassigned"; the labels the task carries; and the due date. Every task is shown with every row in full: no pagination and no row limit. *(SRS FR-15, FR-31; UXD UX-S4; CONTENT.md § Terminology)*
- **CP-128:** The labels cell shows each label the task carries. No action adds a label yet, so every task's cell holds none. Whether an empty labels cell shows a word for none is the content step's. *(UXD UX-S4; the request)*
- **CP-129:** A due date shows as a calendar date with no time of day, written `YYYY-MM-DD` as CONTENT.md § Grammar and mechanics sets it. A task with no due date shows no date, and whether its cell shows a word for none is the content step's. *(SRS FR-24; FDR R-114; CONTENT.md § Grammar and mechanics, Dates and times)*
- **CP-130:** The list is in due-date order, the earliest due date first, and every task with no due date comes after every task that has one. Tasks with the same due date, and the tasks with no due date, stand in the order they were added, the one added first on top. *(SRS FR-36; FDR R-91, R-93; UXD UX-F5, Defaults)*
- **CP-131:** A task is overdue when its due date is before today and its status is neither `done` nor `cancelled`. A task due today is not overdue, and a task with no due date is never overdue. "Today" is the machine's local calendar date at the moment the tracker builds the page. *(SRS FR-25; FDR R-68, R-69)*
- **CP-132:** Every overdue task in the list shows the word "Overdue" beside its due date. A task that is not overdue shows no marker. The overdue state is carried by that word, never by colour alone. *(SRS FR-26; FDR R-70; UXD UX-A4; CONTENT.md § Terminology, Overdue)*
- **CP-133:** A title, an assignee name or any other typed value holding `<` or `&` shows as typed, on the project's page and the task's page, and changes nothing around it. *(FDR R-112)*

### What is saved

- **CP-134:** A task added is still there, with every field it was saved with, after the tracker is stopped and started again. The list order of CP-130 is the same after a start as before it. *(SRS FR-15; FDR R-15, R-43)*
- **CP-135:** The saved data holds each task in the shape SDD § 3, What the system holds, sets for a Task: its identity, its project's identity, title, status, priority, an assignee name or none, its labels, a due date or none, the instant it was created, and its comments. It also holds the counter that issues task identities (fixed by SDD § 3, "The two counters that issue identities are part of the state"). Nothing adds a label or a comment yet, so each task saves with none. How the file lays them out is development-design's. *(SRS DR-2; SDD § 3; the request)*
- **CP-136:** Saved data written before this change, which holds no tasks, still reads. That covers data that holds an assignee list and data from before the assignee list, which CP-100 already reads. A tracker started on either starts normally, with every project and the assignee list present and no tasks. The start does not report the data as unreadable, and it leaves the file's bytes unchanged. The first save after that saves the tasks with the rest. The assignee list is saved as it is today. *(FDR R-15, R-21; the request, "The saved form of the People list must not change"; see Locked Answers, Gap 1)*
- **CP-137:** At start, saved data counts as unreadable when a saved task breaks one of the task rules this change adds. Those breaks are: a status other than `todo`, `in-progress`, `done` or `cancelled`; a priority other than the four; a project identity no saved project holds; two tasks with one identity, or an identity the task counter has not yet issued; a title with no character other than whitespace, or over 200 characters; a due date that is not a calendar date; and an assignee name with no character other than whitespace, or over 200 characters. An assignee name that is not on the assignee list does not make the data unreadable. The start handles each break as it handles any other unreadable saved data, and the data's bytes are unchanged. What a saved label or comment must hold to be readable is not fixed here: the domain those checks span is a label's and a comment's own rules, and they arrive with the changes that add labels and comments. *(FDR R-21 to R-23, R-27; FDR RN-10; SRS FR-22; SDD § 4 SD-5)*

### The code and its trace

- **CP-138:** The Tasks, Priorities and Due dates features' entry points are `domain/tasks.py`, `domain/priorities.py` and `domain/due_dates.py`, fixed by SDD § 4 TS-3's table. Each opening docstring names the SRS requirements the module realizes in this change, every `application` and `web` module that takes part, and the test modules that check it. Every new test module names the requirements or CP rules it checks. The trace check lists `tasks`, `priorities` and `due_dates` as landed feature words (SDD § 4 TS-4). Today it lists `projects` and `assignees` (`products/tracker17/tests/architecture/test_trace.py:24`). It fails once the three modules exist unless the three words are added (see Verified Claims). *(SRS NFR-9; SDD § 4 TS-3, TS-4)*
- **CP-139:** The change creates no `domain/labels.py`, adds no way to add or remove a label, and adds no status move, task edit, task delete, filter, sort control, summary or comment. The task's page and the list carry no control for any of them. *(the request, "Must not be weakened or added"; SDD § 4 EX-12)*

### Tests and the suites

- **CP-140:** The tests ship with the change:
  - Unit tests check `domain/tasks.py`, `domain/priorities.py` and `domain/due_dates.py` with no file and no clock. They cover CP-111, CP-112, CP-117 to CP-120, CP-130, CP-131 and CP-137's rules. CP-131 is covered for all four statuses and for a task with no due date.
  - Integration tests run the tracker's whole request path in one process, as SDD § 4 TS-1 sets out. They check the form with `medium` chosen and the assignee choices, the empty-list case included (CP-106 to CP-110), the first-task invitation (CP-126), add with all four fields and add with a title only (CP-111, CP-112, CP-114, CP-115, CP-124), the blank-title refusal (CP-117), the too-long title (CP-118), the stale assignee (CP-119), the hand-built priority and due date (CP-120), the add to a missing project (CP-121), a failed save (CP-122), the cross-site refusal (CP-123), the missing-task address (CP-125), the list columns (CP-127 to CP-129), the due-date order (CP-130), the "Overdue" marking with today's date set by the test (CP-131, CP-132), typed `<` and `&` (CP-133), a task surviving a stop and a start (CP-134), the start on data from before this change (CP-136), and each break CP-137 names.
  - The test sets today's date by handing the tracker its clock, and patches no name inside a part. *(SDD § 4 TS-2)*
- **CP-141:** In a disposable copy made by `git archive HEAD` and then `git init`-ed, `pytest products/tracker17/tests/` exits 0, `pytest products/tracker17/tests/e2e/` exits 0, and `python3 products/tracker17/tests/timed_run.py` exits 0. Every test that passed before this change still passes, and no existing test is weakened or removed to make it pass. *(SDD § 4 TS-1, TS-5; the request)*
- **CP-142:** An end-to-end test enters `<`, `&` and `"` in a new task's title and finds the task's page and the project's list showing the title exactly as typed. *(NFDR QC-36; SDD § 11 R-3)*
- **CP-143:** `python3 products/tracker17/tests/timed_run.py` loads 1,000 tasks and times adding a task and the page it lands on, with each under 1 second, at the text lengths the run states. *(NFDR QC-48; SDD § 4 TS-5; SRS NFR-1, "creating")*

---

## Examples

Today is 2026-10-11 in every row that depends on it. The assignee list holds `Dana` and `Ari`, in that order, unless a row says otherwise.

| Scenario | Expected behavior | Rule |
|---|---|---|
| Open project `Alpha`'s page | The add-task form shows title, priority, assignee and due date, with an Add button. | CP-106 |
| Type 200 characters into the title field, then try a 201st | The field takes 200 and stops. | CP-107 |
| Open the priority control | It offers `low`, `medium`, `high`, `critical`, with `medium` chosen. | CP-108 |
| Open the assignee control | It offers none, `Dana`, `Ari`, with none chosen. | CP-109 |
| The assignee list is empty, open the project's page | The assignee control offers only none, with a link to People beside it. | CP-109 |
| Open the due-date field | It is empty, and picking a day from the browser's date picker fills a date. | CP-110 |
| Add `Set up CI`, `high`, `Dana`, 2026-10-20 | The task is saved with those four and status `todo`. The browser lands on its page, which shows `Set up CI`, `high`, `Dana`, `2026-10-20`, and a completion line naming `'Set up CI'`. Focus is on the heading, and the line is its accessible description. | CP-111, CP-114, CP-115, CP-124 |
| Add `Write notes` with only the title | Saved as `medium`, unassigned, undated, `todo`. Its page shows `medium`, "unassigned", and that it has no due date. | CP-112, CP-124 |
| Add ` Notes ` with a space at each end | Saved and shown with both spaces. | CP-111 |
| Add `Set up CI` twice in `Alpha` | Two tasks, two rows, two different page addresses. | CP-111, CP-113 |
| Add a task, stop, start, add another | The second task's address is not the first task's. | CP-113 |
| Reload the page that answered an add | No second task is added. | CP-114 |
| Add with a blank title, `high`, `Ari`, 2026-10-20 | Refused. The page opens with focus in the title field, the reason beside it, and `high`, `Ari`, 2026-10-20 still chosen. The saved data is unchanged. | CP-117 |
| A hand-built add sends a 201-character title, then 201 spaces | Each is refused with the too-long reason beside the title field. None of the sent text is on the page or in its address. The saved data is unchanged. | CP-118 |
| Tab 1 loads `Alpha`. Tab 2 removes `Dana` on People. Tab 1 adds `Plan` with `Dana` | Refused. The reason says `Dana` is no longer on the assignee list and offers a reload. `Plan` is still in the title field. The saved data is unchanged. | CP-116, CP-119 |
| A hand-built add sends priority `urgent`, then due date `2026-02-30` | Each is refused with its reason. The saved data is unchanged. | CP-120 |
| A hand-built add names a project identity no project holds | The not-found page answers. Nothing is saved. | CP-121 |
| The save fails while adding `Set up CI` | The project's page says the add didn't happen and nothing changed. The four fields are still filled and focus is on the Add form. The console names the action and the error. No task is added. | CP-122 |
| An add submission marked `Sec-Fetch-Site: cross-site` | Refused. The saved data is unchanged. | CP-123 |
| Open a task's page | It shows title, priority, assignee and due date, and no form, button or status. | CP-124 |
| Open a task-shaped address that names no task | The not-found page says there is no task at this address and links to Projects. | CP-125 |
| Open `Alpha` with no tasks | The list area says `Alpha` has no tasks yet and invites a first one. The add-task form is in view. | CP-126 |
| `Alpha` holds one task; open `Alpha` | The list shows the task's row and no invitation. | CP-126 |
| `Alpha` holds `A`, `Beta` holds `B`; open `Alpha` | Only `A`'s row shows. | CP-127 |
| A task `Plan`, `todo`, `low`, unassigned, due 2026-11-02 | Its row reads, in order: `Plan` (a link to its page), `todo`, `low`, "unassigned", no label, `2026-11-02`. | CP-127, CP-128, CP-129 |
| Added in this order: `Later` due 2026-11-02, `Undated` with none, `Earlier` due 2026-10-10 | The list reads `Earlier`, `Later`, `Undated`. | CP-130 |
| Added in this order: `P` due 2026-10-20, `Q` due 2026-10-20, `R` undated, `S` undated | The list reads `P`, `Q`, `R`, `S`. | CP-130 |
| `Y` due 2026-10-10 in `todo`; `T` due 2026-10-11 in `todo` | `Y` shows "Overdue" beside `2026-10-10`. `T` shows no marker. | CP-131, CP-132 |
| Saved data holds `D` due 2026-10-10 in `done` and `C` due 2026-10-10 in `cancelled` (unit test of the overdue rule) | Neither is overdue. | CP-131 |
| Add a task titled `<b>A&B</b>` assigned to `Dana` | The row and the task's page show `<b>A&B</b>` as typed. | CP-133 |
| Add `Plan` due 2026-10-20 to `Dana`, stop, start | `Plan` is listed with `todo`, `medium`, `Dana`, `2026-10-20`, in the same place in the order. | CP-134 |
| Read the saved data after one add | It holds the task with each SDD § 3 Task field, no label, no comment, and the task counter. | CP-135 |
| Start on saved data written before this change, holding two projects and `Dana` | Both projects are there with no tasks, and People lists `Dana`. The file's bytes are unchanged until the first save. | CP-136 |
| Start on saved data holding a task whose priority is `urgent`, or whose project does not exist, or two tasks with one identity | The start reports the saved data as unreadable, naming its location. The bytes are unchanged. | CP-137 |
| Start on saved data holding a task assigned to `Carol`, who is not on the assignee list | The start is normal, and the row shows `Carol`. | CP-137 |
| Read the three new modules' opening docstrings | Each names its SRS requirements, its `application` and `web` modules, and its test modules. The trace check lists `tasks`, `priorities` and `due_dates` as landed and passes. | CP-138 |
| `ls products/tracker17/domain` after the change | It holds `tasks.py`, `priorities.py` and `due_dates.py`, and no `labels.py`. | CP-138, CP-139 |
| The task's page and a row in the list | Neither carries a move, edit, delete, label or comment control. | CP-139 |
| Run the unit and integration tests | They cover every case CP-140 lists. | CP-140 |
| The three commands, in a `git archive HEAD` copy that is `git init`-ed | Each exits 0, and no earlier test is weakened. | CP-141 |
| In a browser, add a task titled `<b>A&B</b> "Q"` | The task's page and the project's list show `<b>A&B</b> "Q"` as text, not bold. | CP-142 |
| Run `timed_run.py` | It reports adding a task at 1,000 tasks under 1 second and exits 0. | CP-143 |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| None of `domain/tasks.py`, `domain/priorities.py`, `domain/due_dates.py` or `domain/labels.py` exists today (CP-138, CP-139). | `ls products/tracker17/domain` | `__init__.py assignees.py projects.py refusals.py state.py text.py` |
| A project's page with no tasks today says only "This project has no tasks yet.", with no form (CP-106, CP-126). | In a disposable copy (`git archive HEAD products/tracker17`, `git init`-ed), the real `Site` with the real `Tracker` and `SavedData` handled `GET /projects/1` after a create. | 200. `<h1>` `Alpha`, and `<p class="no-tasks">This project has no tasks yet.</p>`. |
| Today any address with nothing at it shows the not-found page about a project (CP-125). | The same copy and setup, `GET /projects/1/tasks/1` and `GET /tasks/1`. | 404 for both, with `<h1>` "There's no project at this address". |
| A created project's page today opens with focus on its heading and the created line as the heading's description (CP-115's "as a newly created project's page does today"). | Read `products/tracker17/web/pages.py:213-216`. | `heading_attributes += f' autofocus aria-describedby="{_CREATED_LINE_ID}"'`. |
| The saved data written today holds `assignees`, `next_project_id` and `projects` (CP-136). | The same copy. `SavedData(loc)` saved a state after one create, and `tracker.json`'s keys were read back. | `['assignees', 'next_project_id', 'projects']` |
| Today's loader refuses a document holding any other top-level key, so adding tasks to the saved form with nothing else would leave earlier data readable only if the loader takes both forms (CP-136). | The same copy. A `tasks` key was added to the written file and `SavedData.load()` ran on it. | `UnreadableData` was raised. The accepted key sets are `products/tracker17/persistence/saved_data.py:22-23` and `:81`. |
| The trace check fails once the three new modules exist unless their words are listed as landed (CP-138). | The same copy, a post-change tree made by writing a stub `domain/tasks.py`, `domain/priorities.py` and `domain/due_dates.py`, then `python3 -m pytest -q tests/architecture/test_trace.py`. | `FAILED test_each_feature_word_with_its_domain_module_is_listed_as_landed`, 1 failed and 19 passed. |
| Every submission today is refused unless marked `same-origin` (CP-123's "the same check every submission passes today"). | Read `products/tracker17/web/routes.py:44` and `:151`. | `REFUSED_FROM_ANOTHER_SITE = {"cross-site", "same-site"}`, and `if route.kind == SUBMISSION and fetch_site != SAME_ORIGIN:` answers 403. |
| A project name's too-long check runs before its blank check (CP-118's order). | Read `products/tracker17/domain/projects.py:42-45`. | `ensure_within(TextField.NAME, …)` and `ensure_within(TextField.DESCRIPTION, …)` come before `raise BlankName()`. |
| The baseline suites. | The same copy, with the system's `pytest 9.0.3`. Ran `python3 -m pytest -q products/tracker17/tests/`, `python3 -m pytest -q products/tracker17/tests/e2e/` and `python3 products/tracker17/tests/timed_run.py`. | `356 passed`, exit 0. The e2e run exited 4 with `ModuleNotFoundError: No module named 'playwright'`, because the test dependencies are not installed on this machine and the product has no `.venv`. That says nothing about the product. `timed_run.py` exited 0. `pytest tests/` leaves out `tests/e2e/` by the rule in `products/tracker17/tests/conftest.py:7-9`. |

---

## Out of Scope

- **Changing a task.** The edit form, the left-the-list assignee rules of SDD § 4 RT-7, FDR R-47, R-48 and R-115 to R-118, and SRS AC-19 belong to `edit-task-fields`. The rest of UXD UX-S6 waits as well: the task's status with its moves, its project, labels, comments and Delete.
- **Labels.** Adding and removing a label, `domain/labels.py`, and the start-time checks on a saved label's content belong to `task-labels`.
- **Status moves, deleting a task, filter and sort controls, the list across all projects, and the summary.** Those are later stations and seeds. The list here has one fixed order (CP-130) and no control to change it.
- **Comments.** They belong to the `comment-on-a-task` seed, along with the start-time checks on a saved comment.
- **The project page's title.** It stays as it is today. CONTENT.md's "Alpha: Tasks - tracker17" example belongs with the Tasks and Summary links, which arrive with the summary.
- **README § Status and `products/tracker17/docs/what_left.md`.** Both shrink after the station closes, in the `readme-status` run (`<CORE>/doctrine/setup/kensaiapp_structure.md` § The what-left file). This change edits neither.

---

## Locked Answers (the divergence record — self-review 2026-10-11)

- **Gap 1 — saved data from before this change (CP-136):** it loads with no tasks and is not reported as unreadable. The request says the People list's saved form must not change, and it gives no reading rule for data that predates tasks. Today's loader refuses any top-level key set other than its own (see Verified Claims). Adding tasks to the saved form with nothing else would make the operator's earlier projects and assignees unreadable, which breaks FDR R-15. CP-100 took the same course when the assignee list arrived. Reading missing tasks as none writes nothing and converts nothing. It is the additive, reversible choice. *(b: an implicit behaviour, locked conservatively)*
- **Gap 2 — the refusals and failures the request does not name (CP-118 to CP-123):** stated. The request names only the blank title. SDD § 4 RT-10 says "A slice that adds a text field writes the field's `maxlength` and adds a test that a longer value is refused". FDR R-51, R-60, R-102, R-103, R-107 and R-110 bind every action, and the add is a new action. UXD UX-F3 names the stale assignee as the add form's one other refusal. *(b)*
- **Gap 3 — what the blank-title refusal keeps (CP-117):** all four fields as entered, not the title alone. The request says "the typed text kept". UXD UX-I3 says "Everything the operator typed stays in the form", and a choice made in a control is part of what the form held. *(b)*
- **Gap 4 — a completion line on the task page (CP-115):** added. The request says the task page "only shows" four fields. UXD UX-I4 and SDD § 4 EX-5 confirm every completed action in one line on the page it leaves the operator on. That page is the task's. The line reports the add and shows nothing more of the task. The word "only" is read as excluding the rest of the task and any control, which CP-124 states. *(a: the request read against the UXD)*
- **Gap 5 — the task page shows no status (CP-124):** the request is followed. UXD UX-S6 shows the status with its moves, and the request lists four fields. The list row shows the status (CP-127), so `todo` stays visible. *(b)*
- **Gap 6 — the title links to the task's page (CP-127):** added. The request does not say how a listed task is reached. UXD UX-S4 makes the title "a link to the task", and without it a task's page could be reached only straight after its add. *(b)*
- **Gap 7 — the empty assignee list (CP-109):** the control offers only none and a link to People. The request says "the names on the People list plus none". UXD UX-F3's decision point adds the link, and People already exists (SDD § 4 EX-12). *(b)*
- **Gap 8 — the order within one due date, and among undated tasks (CP-130):** the order they were added, the first added on top. The request fixes earliest due first and undated last. FDR R-93 keeps creation order for ties, and UXD UX-F5 shows an all-undated list "in creation order, oldest first". The order is seen by adding tasks in sequence and reading the list. *(b)*
- **Gap 9 — the missing-task address (CP-125):** the not-found page speaks of a task. The request does not name it. SDD § 6 S-2 says "The not-found page now also speaks of a task (UX-S10)", and FDR R-105 needs a not-found page for a task address. The page offers only Projects, because All tasks does not exist yet (SDD § 4 EX-12; CONTENT.md § Error, the form with one place). *(b)*
- **Gap 10 — the saved-data breaks (CP-137):** stated for the task rules this change adds, with the label and comment checks left to their changes. SDD § 4 SD-5 says "A slice that adds a data rule adds a test that saved data breaking the rule is reported as unreadable". FDR R-21 names an unknown status or priority, a task whose project does not exist and a reused task identity. FDR RN-10 leaves an unlisted assignee readable. A saved status may be any of the four even though only `todo` can be reached here, because the saved form is the one later slices write (the request). *(b)*
- **Gap 11 — the overdue rule's statuses (CP-131, CP-140):** stated in full and unit-tested for all four statuses. The request names AC-13's first two cases for the list marking, and those stay the integration cases. Only `todo` can be reached through a page, so the `done` and `cancelled` cases are checked on the domain rule alone. *(b)*
- **Gap 12 — "integration tests through the real server" (CP-140):** read as the tracker's whole request path in one process, with no socket. SDD § 4 TS-1 fixes the integration layer as "`web` with `application` in one process with no socket". The People change read the same words the same way (its Gap 7). *(a)*
- **Gap 13 — the module and file names (CP-135, CP-138):** named, because a record above the change fixes them. SDD § 4 TS-3's table fixes the three entry points, and SDD § 3 fixes the Task's fields and the task counter. CP-135 names the fields and leaves the file's layout to development-design. *(b)*
- **Gap 14 — the checks the records require (CP-142, CP-143):** stated, over the request. *(e)* The request names no end-to-end test and leaves adding to the timed run to a later station, but NFDR QC-36 has each change's end-to-end tests enter `<`, `&` and `"` in every text field it adds, and QC-48 with SDD § 4 TS-5 has a change that adds an action SRS NFR-1 lists add it to the timed run. The title is a new text field and creating is a listed action. Development-design halted on the conflict (`fc2f59593`); the owner answered "include" on 2026-10-11.
