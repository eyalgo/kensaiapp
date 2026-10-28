# Change Spec — Rename a project from its Tasks view

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing
**Request:** Let the operator rename a project from its Tasks view. Below the project's list, a Rename field holds the project's current name; Save renames the project, and the operator sees the new name as the project's page title and in the Projects list, with the old name in neither (UXD UX-F10; SDD § 6 S-7). A blank name, or a name another project already uses, is refused under UX-I3 through the same refusal path and naming rules project creation uses (FR-10), and the saved data is unchanged; saving the project's own current name is accepted (FR-12). Renaming leaves the project's tasks the same tasks, with the same identities, fields and comments (FR-12). The timed run gains a project rename (NFDR QC-48). Tests: one that a rename leaves the project's tasks unchanged, and a layer-3 test per refusal, each asserting unchanged saved data. The project-creation validation and refusal wording must not be duplicated or replaced by a second scheme. Deleting a project, the `domain/projects.py` / `domain/tasks.py` docstring bar, changing a project's description (UXD § 10) and moving a task between projects (SRS FR-14) are not part of this change, and existing pages and timed actions must keep working.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, and every concern it routes read

---

## Change Summary

The operator can rename a project from the bottom of its Tasks view. The new name goes through the
same rules and the same refusals project creation uses. It replaces the old name everywhere the
project's name shows, and it changes nothing else: not the project's tasks, its comments, its
description or its addresses. The behaviour contract already states this action
(`docs/fdr.md` R-34, R-35). The product does not have it yet. The product's location is
`project.md` `Product path:`, and every product file named below is relative to it. `SRS`, `SDD`,
`UXD`, `FDR`, `NFDR` and `CONTENT.md` are the product's documents under `docs/`, read at SRS 6,
SDD 13, UXD 11, NFDR 17, FDR 4 and CONTENT 17.

---

## Rules

### The Rename control

- **CP-546:** A project's Tasks view shows a **Rename** area below the list (UXD UX-F10, § 4,
  UX-S4). It holds, in this order:
  1. a text field with a visible label, holding the project's name exactly as saved when the page is
     built, surrounding spaces and letter case included;
  2. a button labelled `Save`.

  The area shows in every state the Tasks view has: with tasks listed, with no tasks yet, when the
  filter matches nothing, when a filter or sort choice is refused, and whatever completion line,
  refusal or failure the page carries. A state a later change adds to the view shows it too. No
  other page offers a rename: not Projects, not the Summary, not All tasks, not a task's page.
- **CP-547:** The Rename field's `maxlength` is the short-text maximum, 200 characters, written from
  the one place in `domain` that states it. No sentence beside the field states a maximum. *(NFDR
  QC-9; SDD § 4 RT-10; ADR-0007; UXD UX-F2: only the description and comment fields state one)*
- **CP-548:** Every word the area, its completion line, its refusals and its failure line show
  follows `docs/CONTENT.md` (SDD § 4 EX-11). The completion verb is "renamed" (`CONTENT.md`
  § Completed). The field's label is the content stage's. This spec fixes what each line must say,
  and the content stage writes any wording it does not quote. The refusal reasons are not new
  wording: they are creation's (CP-555).
- **CP-549:** Save renames on the first press. There is no confirmation step (UXD UX-I2, "Every
  other action … takes effect on the first press").

### Renaming

- **CP-550:** Pressing Save with a name that CP-555 accepts, and that differs exactly from the
  project's name as saved at that moment, saves that name as the project's name. The browser is
  sent to the project's Tasks view:
  - at the project's unchanged address, `/projects/{id}`, with no filter or sort chosen;
  - with the new name as the page's heading and in its document title, `{new name}: Tasks - tracker17`;
  - with one completion line that uses the verb "renamed" and quotes the new name as typed. Whether
    it also names the old name is the content stage's.

  Keyboard focus is in the Rename area, on the field or on an element showing the new name, and the
  completion line is the focused element's accessible description. Development-design chooses which
  element. Reloading that page, or returning to it through Back or Forward, shows the same line again
  and saves nothing. *(SRS FR-12; FDR R-34, R-35, R-106, PD-11; UXD UX-I4; SDD § 4 EX-5, EX-14,
  RT-8, RT-9)*
- **CP-551:** After a rename, every page that shows the project's name shows the new name, and none
  shows the old name as that project's name. Today those are:
  - the project's Tasks view, its heading and its document title;
  - the project's entry on Projects;
  - the project's Summary, its heading and its document title, `{new name}: Summary - tracker17`;
  - the Project column of All tasks, for each of the project's tasks;
  - the Project shown on each of the project's tasks' pages.

  A page a later change adds that shows a project's name falls under the same rule. On Projects the
  project takes the place its new name gives it in the order the list already uses: by name with
  letter case ignored, the exact name breaking a tie (UXD UX-S3). The project's addresses do not
  change: `/projects/{id}`, `/projects/{id}/summary` and every `/tasks/{id}` of its tasks open as
  before. *(SRS FR-11, FR-12; FDR R-33, R-35)*
- **CP-552:** The name is saved and shown exactly as typed. Surrounding spaces and letter case are
  kept, and names are compared exactly, so `Alpha` renamed to `alpha` is a rename. Its length is
  counted in Unicode code points on the value as saved, spaces included, so a name of exactly 200
  code points is accepted, a character outside the Basic Multilingual Plane included. The name is
  changed in no way other than SDD § 4 RT-10's line-break normalization. *(SRS FR-10, FR-40; FDR
  R-32, R-76, R-77, R-80; ADR-0007)*
- **CP-553:** Pressing Save with exactly the name the project has saved at that moment is not
  refused and changes nothing. No save is made. The browser is sent to the project's Tasks view,
  which shows no completion line and no refusal and opens at its start, as a page reached by a link
  does. `Alpha ` saved over `Alpha` is a different name and is a rename under CP-550. *(SRS FR-12;
  FDR R-34 and its Examples row "Project `Alpha` renamed to `Alpha`"; NFDR QC-21; SDD § 4 EX-5)*
- **CP-554:** A rename changes the project's name and nothing else, in the saved data and on every
  page:
  - the project's tasks are the same tasks, with the same identities, titles, statuses, priorities,
    assignees, labels, due dates, created times and order, and the same comments with their text,
    author and time;
  - the project keeps its identity and its description;
  - every other project and its tasks, the assignee list, the operator's name and the two identity
    counters are unchanged, and no identity is issued;
  - the saved data gains no field.

  After the tracker is stopped and started again on the same saved data, the project has its new
  name. *(SRS FR-5, FR-12, NFR-6; FDR R-15, R-35, R-36, R-29; NFDR QC-46)*

### Refusals and failures

- **CP-555:** The new name follows the rules project creation applies to a name, through the same
  refusal path and with the same reasons. The request: "The project-creation validation and refusal
  wording must not be duplicated or replaced by a second scheme". The rules are checked against the
  saved data at the moment the rename is applied, in creation's order, and the first that fails
  gives the refusal:
  1. **too long**: more than 200 code points. Reason: `A project name can't be longer than 200 characters. Type a shorter one.`
  2. **blank**: empty, or every character in it is whitespace, the same set of characters creation
     treats as blank. Reason: `A project needs a name. Type one.`
  3. **in use**: another project's name is exactly equal to it, including one another tab created
     after this page loaded. Reason: `A project named '{typed name}' already exists. Choose a different name.`

  So 201 spaces get the too-long reason. The project's own name is never "in use" (CP-553). *(SRS
  FR-10, FR-12, FR-39, FR-40, NFR-3; FDR R-31, R-32, R-34, R-78, R-102; RN-1)*
- **CP-556:** A refused rename leaves the saved data unchanged. The browser is sent to the
  project's Tasks view, which still shows the saved name as its heading and title. The view opens at
  the Rename field, with keyboard focus on it and the reason beside it as its accessible
  description:
  - for a blank name and a name in use, the field holds what was typed;
  - for a name too long, the field holds the project's saved name, and neither the page nor its
    address holds any of the text that was sent. Only a request that no page of the tracker sends can
    carry such a name, because CP-547's field stops at 200.

  Reloading the page shows the same refusal and changes nothing. *(SRS FR-39; FDR R-79, R-100,
  PD-11; UXD UX-F10, UX-I3, UX-A3; SDD § 4 EX-4, EX-14, RT-8)*
- **CP-557:** When the save of a rename fails for a reason that is not a refusal:
  - the saved data and the project's name stay as they were, on every page;
  - the console shows a message naming the rename and the error;
  - the Tasks view opens at Save, with keyboard focus on it and the failure line as its accessible
    description. The line follows `CONTENT.md` § Error's failure formula and its rename example:
    the tracker couldn't rename the project, nothing was changed, what was typed is still in the
    form, try again. The field holds what was typed. No error text from Python shows.

  *(SRS FR-9, NFR-8, AC-18; FDR R-18, R-107, R-108; UXD UX-I5; SDD § 4 OB-3, EX-4; NFDR QC-49,
  QC-56, QC-57)*
- **CP-558:** A rename sent for a project identity no project holds changes nothing. It is answered
  with the not-found page, headed `There's no project at this address`, with HTTP status 404, which
  is the answer the tracker gives today to a project submission for such an identity (Verified
  Claims). It adds no refusal wording. *(FDR R-103, R-105; SRS NFR-3; SDD § 4 EX-13)*
- **CP-559:** A rename that does not come from the tracker's own pages is refused and changes
  nothing, under the check every submission passes today: one marked `cross-site` or `same-site`,
  and one not marked `same-origin`, a submission with no mark included. *(FDR R-110; SDD § 4 SEC-2;
  NFDR QC-32)*

### Use of the control

- **CP-560:** A rename can be done from the keyboard alone, with the browser's own keys: Tab reaches
  the field and Save, and Enter in the field submits the rename. The field has a visible label, each
  control shows when it has focus, and Save meets UXD UX-A6's pointer-target floor. *(SDD § 4 EX-8,
  EX-9; UXD UX-I6, UX-A1, UX-A2, UX-A5, UX-A6)*
- **CP-561:** A name holding `<`, `&` or `"` shows exactly as typed wherever CP-546, CP-550, CP-551
  and CP-555 show it: in the field, the heading, the document title, the Projects list, the
  completion line and the in-use reason. It changes nothing around it. *(FDR R-112; SDD § 4 SEC-4;
  NFDR QC-36)*

### Checks this change carries

- **CP-562:** A test renames a project that holds several tasks: tasks in different statuses, with
  comments, labels, an assignee and a due date set on some, and another project beside it. It
  asserts CP-554: the project's tasks before and after are equal, field by field and comment by
  comment, both in the tracker and in the saved data read back from disk. It also asserts that the
  project's identity and description and the other project are unchanged. *(Request; SRS FR-12; SDD
  § 6 S-7 *Command*, "a rename leaves the project's tasks unchanged (FR-12)")*
- **CP-563:** Application-layer tests (layer 3) hold one test per refusal, each asserting the reason
  shown and the saved data the same before and after:
  - a blank name, both empty and whitespace only, with the typed text kept;
  - a name another project already has, with the typed text kept;
  - a name of 201 code points, sent in a request no page sends, with none of the sent text on the
    page or in its address;
  - a rename sent for a project identity no project holds (CP-558).

  A further test at the same layer saves the project's own name and asserts no save and no line
  (CP-553). *(Request; SRS AC-12; NFDR QC-5, QC-9, QC-21, QC-38)*
- **CP-564:** A UI-layer test (layer 4) builds the Tasks view and asserts that the Rename field's
  `maxlength` equals the maximum `domain` states, that no maximum is stated beside it, and that the
  field holds the project's saved name exactly. *(NFDR QC-9)*
- **CP-565:** An end-to-end test (layer 5) types a name holding `<`, `&` and `"` into the Rename
  field in Chromium, saves it, and asserts that the heading, the document title and the project's
  entry on Projects show it as typed. *(NFDR QC-36; SDD § 11 R-3)*
- **CP-566:** `python3 tests/timed_run.py` adds a project rename to its listed actions (NFDR QC-48;
  SDD § 4 TS-5; SRS NFR-1). The fixture is SRS NFR-1's volume, 1,000 tasks with 20 comments each, at
  ordinary text lengths, and the project renamed holds tasks. The run times the Save submission and
  the page it lands on, apart and as a total. Each must be under 1 second. The run marks the
  submission `same-origin` (NFDR QC-32). The rename counts only when both of these hold:
  - the saved data is the fixture with that project's name replaced, and nothing else changed;
  - the landing page shows CP-550's completion line under the new name.

  A refused or failed rename fails the run. Every action the run timed before this change is still
  timed and still passes. The run exits 0.
- **CP-567:** The tests that already walk every route or every action cover what this change adds:
  - the route test of NFDR QC-7 covers every address and submission this change adds, and checks
    each for QC-8 (no cookie) and QC-33 and QC-34 (the page policy as a response header);
  - the no-outbound-connection test of NFDR QC-35 also drives a rename and its landing;
  - NFDR QC-54's read-once check covers the rename: a test runs a rename against an `application`
    built with a recording saver and asserts that the saver received only saves.
- **CP-568:** This change also meets NFDR QC-11:
  - the pointer test passes;
  - every test module this change adds names the SRS requirements or acceptance criteria it checks;
  - the Projects feature's entry module `domain/projects.py` keeps its opening docstring true for
    this change. It names the SRS requirements it now realizes (FR-12 among them, if the rename rule
    lives there), every `application` and `web` module that takes part, and every test module that
    checks it.

---

## Examples

| Scenario | Expected behavior |
|---|---|
| Project 1 `Alpha` with three tasks; the operator opens `/projects/1` | Below the list: Rename, a labelled field holding `Alpha`, then `Save` (CP-546). |
| Project 1 has no tasks yet, or the filter matches nothing | The Rename area is still below the empty or no-match state (CP-546). |
| The operator opens Projects, Alpha's Summary, All tasks, or a task's page | None offers a rename (CP-546). |
| The Tasks view's Rename field | `maxlength="200"`, from `domain`'s value. No sentence states a maximum (CP-547, CP-564). |
| The operator types `Beta` and presses Save | One save. The browser lands on `/projects/1`, unfiltered, with heading `Beta`, title `Beta: Tasks - tracker17`, one line using "renamed" and quoting `Beta`, and focus in the Rename area. No confirmation was asked (CP-548, CP-549, CP-550). |
| The operator reloads that page | The same line again. Nothing is saved (CP-550). |
| Projects `Alpha`, `Gamma`, `delta`; Alpha is renamed `Zed` | Projects lists `delta`, `Gamma`, `Zed`, and no `Alpha` (CP-551). |
| Alpha renamed `Beta`; the operator opens `/projects/1/summary`, All tasks and `/tasks/3`, a task of Beta | The Summary's heading is `Beta` and its title `Beta: Summary - tracker17`; All tasks shows `Beta` in task 3's Project column; task 3's page shows Project `Beta`. Every address opens as before (CP-551). |
| `Alpha` renamed `alpha` | Accepted as a rename. The name is saved as `alpha` (CP-552). |
| `Alpha` renamed `Alpha` | Not refused. No save, no line, no refusal. The Tasks view opens at its start (CP-553). |
| `Alpha` renamed `Alpha ` (trailing space) | Accepted as a rename. Saved with its trailing space (CP-552, CP-553). |
| A name of exactly 200 code points, one of them outside the Basic Multilingual Plane | Accepted (CP-552). |
| Alpha holds task 3 with two comments, label `ui`, assignee `Dana`, due date `2026-11-01`, status `in-progress`; Alpha is renamed `Beta` | Task 3 is unchanged in every field and comment, in the tracker and in the saved data. Alpha's identity and description, the other projects, the assignee list, the operator's name and both counters are unchanged (CP-554, CP-562). |
| Alpha renamed `Beta`; the tracker is stopped and started | The project is `Beta` (CP-554). |
| The operator blanks the field, or types three spaces, and presses Save | Refused with `A project needs a name. Type one.` beside the field, focus on it, the typed text kept. Saved data unchanged, heading still `Alpha` (CP-555, CP-556, CP-563). |
| Projects `Alpha` and `Beta`; Alpha is renamed `Beta` | Refused with `A project named 'Beta' already exists. Choose a different name.`, the field holding `Beta`. Saved data unchanged (CP-555, CP-556, CP-563). |
| Tab 2 creates project `Gamma` after tab 1 loaded Alpha's page; tab 1 renames Alpha to `Gamma` | Refused as in use (CP-555). |
| Tab 2 renames Alpha to `Beta`; tab 1, still showing `Alpha` in its field, types `Gamma` and saves | Accepted. The project is `Gamma` (CP-550, CP-555; FDR R-104). |
| Tab 2 renames Alpha to `Beta`; tab 1, still showing `Alpha` in its field, presses Save unchanged | `Alpha` differs from the saved `Beta` and is not in use, so the project is renamed back to `Alpha` (CP-550, CP-553; FDR R-102, R-104). |
| A request no page sends carries a name of 201 code points, or of 201 spaces | Refused with `A project name can't be longer than 200 characters. Type a shorter one.` The field holds the saved name, and no sent text is on the page or in its address. Saved data unchanged (CP-555, CP-556, CP-563). |
| The save fails when the operator renames Alpha to `Beta` | Alpha is unchanged everywhere. The console names the rename and the error. The Tasks view opens at Save with the failure line, and the field holds `Beta` (CP-557). |
| A rename is sent for `/projects/99`, an identity no project holds | The not-found page, `There's no project at this address`, 404. Nothing is saved (CP-558, CP-563). |
| A rename sent marked `cross-site`, or with no mark | Refused. Nothing changes (CP-559). |
| The operator Tabs to the field, types `Beta` and presses Enter | The project is renamed `Beta` (CP-560). |
| Alpha renamed `<b>R&D "x"</b>` in Chromium | The heading, the title, the Projects entry, the field and the line show `<b>R&D "x"</b>` as typed text (CP-561, CP-565). |
| The timed run at 1,000 tasks with 20 comments each | It renames a project that holds tasks. The submission and the landing are each under 1 second, and they count only on the exact saved delta and the completion line. The run exits 0 (CP-566). |
| The route test, the no-outbound test and the read-once test run | Each covers the rename's addresses or the rename (CP-567). |
| `pytest tests/` runs with this change's tests added | The pointer test passes. Each new test module names what it checks. `domain/projects.py`'s docstring is true for this change (CP-568). |

---

## Verified Claims

No rule here pins output that renders a language-level fact. Every rendering a rule states is a name
the operator typed or a value the product chooses, so no language-rendering row is owed. Each claim
below is about existing code.

| Claim | Verified by | What came back |
|---|---|---|
| Creation's three name reasons are the wording CP-555 quotes. | Read `products/tracker17/web/pages.py:444-454` (`_name_reason`). | `"A project needs a name. Type one."`; `f"A project named '{_escape(name)}' already exists. Choose a different name."`; `f"A project name can't be longer than {_characters(SHORT_TEXT_MAX)}. " "Type a shorter one."`, with `SHORT_TEXT_MAX` 200. |
| Creation checks too long, then blank, then in use (CP-555's order). | Read `products/tracker17/domain/projects.py:36-54`. | `ensure_within(TextField.NAME, …)` at :42, `raise BlankName()` at :45, then in `create_project` `raise NameInUse()` at :54. |
| A project submission for an identity no project holds is answered with the not-found page, 404, and saves nothing today (CP-558). | Ran a scratch probe under `/tmp`, outside the tree, against the branch at `2f9cedf87`. It used `web.Site` with `application.Tracker` in one process, a recording saver and `same-origin` marks, the conditions layer 3 runs under. It created project 1, then sent `POST /projects/99/tasks` and `GET /projects/99`. | `POST /projects/99/tasks`: 404, no `Location`, heading `There's no project at this address`, 0 saves. `GET /projects/99`: 404, the same heading. |
| The Tasks view and the Summary carry the project's name in their document titles (CP-550, CP-551). | Same probe: `GET /projects/1` and `GET /projects/1/summary`. Read `products/tracker17/web/pages.py:1760` and `:1678`. | `Alpha: Tasks - tracker17` and `Alpha: Summary - tracker17`. |
| The Tasks view offers no rename today, and its list section is the last part of its body. | Same probe, the forms on `GET /projects/1` with one task. Read `products/tracker17/web/pages.py:1752-1760`. | Forms: `post /projects/1/tasks`, `get /projects/1`, two `post /tasks/1/move`. Body order: heading, views, line, description, add-task form, then the list section. |
| Projects lists by name with letter case ignored, the exact name breaking a tie (CP-551). | Read `products/tracker17/domain/projects.py:64-67`. | `sorted(…, key=lambda project: (project.name.casefold(), project.name))`. |
| `CONTENT.md` fixes the rename verb and gives a rename failure example (CP-548, CP-557). | Read `products/tracker17/docs/CONTENT.md:236` and `:312`. | `"The tracker couldn't rename 'Alpha', and nothing was changed. What you typed is still in the form. Try again."`; "The verbs are fixed by the action: … renamed, …". No rename completion example. |
| Four page tests pin the Tasks view's controls in a way the Rename area breaks. | Read `products/tracker17/tests/integration/test_pages.py:177-194` and `:226-242`, `tests/integration/test_filter_pages.py:126-136`, and `tests/integration/test_sort_pages.py:90-103`. | `:193-194` asserts "rename" is absent from every sample page, the project page and the created page included. `:236` `(form,) = root.find_all("form")` and `:241` `(button,) = root.find_all("button")`. Filter `:133` and sort `:100` assert the empty project's forms are exactly `["post"]`. |
| The route test requires its samples to equal the route set and every submission sample to save once. | Read `products/tracker17/tests/integration/test_routes.py:268-334`. | `assert {route.pattern for route in ROUTES} == set(SAMPLE_ADDRESS)` at :312; `SUBMITTED_BODY` is keyed by sample address; saves checked at :334. |
| The no-outbound test drives a hand-written list of actions. | Read `products/tracker17/tests/integration/test_routes.py:481-546`. | A literal sequence of `site.handle` and `get` calls with no rename. A new action is covered only once it is added there (CP-567). |
| The timed-run harness tests feed a fixed, ordered sequence of readings and labels. | Read `products/tracker17/tests/integration/test_timed_run.py:2089-2104` and `:2130-2140`. | `_run_readings` orders the comment, assignee add and remove, move, filter and sort, then the Summary, then the deletion. The label test lists every block in order. A new timed action changes both (Locked Answer Gap 10). |

---

## Out of Scope

- Deleting a project. The request: "Deleting a project … not part of this change". It is item 3 of
  the same seed, and its control sits in the same area (UXD UX-F10, UX-S4). The product has no
  project deletion today: the route table at `products/tracker17/web/routes.py:114-133` holds no
  project deletion route. Parked in `deferred_decisions.md` as a record gap.
- S-7's slice-level artifact bar, that the opening docstrings of `domain/projects.py` and
  `domain/tasks.py` name every test the slice adds (SDD § 6 S-7, *Artifact*). The request: "the
  `domain/projects.py` / `domain/tasks.py` docstring bar … not part of this change". Only that bar is
  left out. The NFDR QC-11 check stays in for what this change itself adds (CP-568). Parked in
  `deferred_decisions.md` as a record gap.
- Changing a project's description (FDR R-36, OOS-15; UXD § 10). The request rules it out, and a
  rename keeps the description (CP-554).
- Moving a task between projects (SRS FR-14; FDR R-49, OOS-9). The request rules it out.
- Renaming from any page other than the project's Tasks view (CP-546).
- Undoing a rename. Nothing is undoable (UXD UX-I2). Renaming again is the way back.
- Carrying the list's filter and sort choices through a rename (Locked Answer Gap 3).
- The wording of the field's label, of the completion line and of the failure line, beyond what
  CP-548, CP-550 and CP-557 fix. That wording is `CONTENT.md`'s and the content stage's.

---

## Locked Answers (the divergence record — self-review 2026-10-28)

- **Gap 1 — The area holds a label and Save, and shows in every state of the view (b):** CP-546
  fixes the area's parts and says it shows whatever state the Tasks view is in. *Reason:* UXD UX-F10
  gives "Rename with the current name in a field → Save", and UX-S4 lists the rename control among
  the view's parts with no state condition. SDD § 4 EX-9 gives every field a label. Showing it only
  when the project has tasks would leave a project with no tasks un-renamable, which FDR R-34 does
  not allow.
- **Gap 2 — Where a rename lands and where focus goes (b):** CP-550 lands on the project's own
  address with the line, and puts focus in the Rename area. *Reason:* the request says only that
  the operator sees the new name. SDD § 4 EX-5 opens a page that is the page the form was on "at the
  thing acted on", and the Rename area is where the operator acted. Focus is left to
  development-design between the field and an element showing the new name, as the Your name
  section's spec left it (`tracker17 · tobiishi · 2026-10-12_operator-name`, its spec's CP-216). Either choice can
  be changed later without changing what is saved.
- **Gap 3 — The landing carries no filter or sort (b):** CP-550 and CP-556 land with no list choices.
  *Reason:* the request is silent. The Rename area acts on the project, not on the list, so a list
  choice has no part in what it does. Leaving the choices out adds nothing for the form to carry,
  and it is reversible: the operator applies the filter again. Out of Scope records it.
- **Gap 4 — Every page showing the name, and the Projects order (b):** CP-551 reaches past the
  request's "page title and … the Projects list". It also names the Summary, All tasks and each
  task's page, and the project's new place in the Projects order. *Reason:* FDR R-34's rename is of
  the project's one name, so a page still showing the old name would contradict it. The order is the
  one UXD UX-S3 already gives the list. Naming each page makes the rename checkable on every page
  that shows the name.
- **Gap 5 — The own name saves nothing and shows nothing (b):** CP-553 makes "accepted" mean no save,
  no line and no refusal. *Reason:* FDR R-34's Examples row says "Not refused. Nothing changes".
  NFDR QC-21 has an action whose outcome reports no change save nothing. Saving your name on People
  already answers this way (`tracker17 · tobiishi · 2026-10-12_operator-name`, its spec's CP-218). A completion line
  would claim a change that did not happen (UXD UX-I4).
- **Gap 6 — Checked against the saved name, not the shown one (b):** CP-550, CP-553 and CP-555
  compare the typed name with the name saved at the moment of the rename. A stale tab's unchanged
  field can therefore rename the project back. *Reason:* FDR R-102 checks every action against the
  saved data at that moment, and R-104 lets a plain field edit from a stale page replace what another
  tab saved. NFDR QC-21 limits the compare-with-what-was-shown save to the task edit form.
- **Gap 7 — The too-long refusal keeps no typed text (b):** CP-556 has the field show the saved name
  after a too-long refusal. *Reason:* FDR PD-11 and SDD § 4 RT-8 give an over-long refusal "the
  reason and not the typed text", which creation already does. With no typed text to show, the
  saved name is what the field holds on every other load of this page.
- **Gap 8 — A rename for a project no project holds (b):** CP-558 is not in the request. *Reason:*
  FDR R-103 and R-105 bind every action on a project that no longer exists, this new one included.
  Today the case is reached only by a typed request, because no project can be deleted yet. The
  answer is the one the tracker already gives (Verified Claims), so no wording is added. The case of
  a project another tab deleted is `delete-a-project`'s.
- **Gap 9 — Checks the records require (e):** CP-547, CP-563's over-long test, CP-564, CP-565,
  CP-566's conditions, CP-567 and CP-568 are not in the request. *Reason:*
  - NFDR QC-9 says "A change that adds a text field writes its `maxlength` and a test that a longer
    value is refused", and SDD § 4 RT-10 says the same.
  - NFDR QC-36 asks for end-to-end tests that "enter `<`, `&` and `"` in every text field a change
    adds".
  - NFDR QC-48 has the timed run mark every submission `same-origin` and fail on a refused or failed
    action. The exact-delta and landing-line conditions are the bar every timed action already meets.
  - NFDR QC-7 verifies through a route test that walks every route, QC-35 through a test that
    "drives every action through `web`", and QC-54 through "a test that runs every action against an
    `application` built with a recording saver".
  - NFDR QC-11 is a check the NFDR requires of every change. The request's exclusion is read as S-7's
    slice artifact bar, as the task-deletion spec read the same words
    (`tracker17 · tobiishi · 2026-10-28_delete-a-task`, its spec's Gap 10). Out of Scope keeps that bar out.
- **Gap 10 — Existing tests that change (f):** these existing tests pin what this change alters, and
  they change. Each keeps asserting everything else it asserts today.
  - `tests/integration/test_pages.py::test_every_page_has_a_header_with_the_projects_and_people_links`.
    It admits "rename" on the project page and the created page samples. It keeps asserting the
    header's three links, every link's address, and "delete" absent.
  - `tests/integration/test_pages.py::test_a_project_page_shows_name_description_the_invitation_and_only_the_add_form`.
    It admits the Rename form and its Save. It keeps asserting the heading, the description, the
    invitation, the add form's action and fields, the Add button and the document title.
  - `tests/integration/test_filter_pages.py::test_empty_project_retains_first_task_page_without_filters`
    and `tests/integration/test_sort_pages.py::test_an_empty_project_has_no_controls_even_with_malformed_sort_choices`.
    They admit the Rename form among the empty project's `post` forms. They keep asserting no `get`
    form, no table, the no-tasks invitation, and no filter or sort control.
  - `tests/integration/test_routes.py::test_every_route_leaves_state_and_headers_as_the_rules_say`.
    It gains samples for the addresses and submission this change adds. It keeps asserting that a
    page request changes nothing, that a submission redirects and saves once, that no cookie is set,
    and that the policy is on every response.
  - `tests/integration/test_routes.py::test_no_socket_connection_is_made`. It gains the rename and
    its landing. It keeps every action it drives today.
  - The `tests/integration/test_timed_run.py` tests that drive the whole run through `_run_readings`
    or a fixed reading sequence, and those that list the run's labels in order. They gain the
    rename's readings and label. They keep asserting each earlier action's verdict and the run's
    exit status.
  - Any other test that pins the Tasks view's full set of forms, buttons or fields admits the Rename
    area and keeps asserting the rest. Development-design names any it finds.

  *Reason:* the request asks for the control, the action and the timed rename. NFDR QC-7, QC-35 and
  QC-48 require the route coverage and the timing. None of these can be met with these tests
  unchanged.
