# Change Spec — The People page keeps the assignee list

**Date:** 2026-10-11
**Category:** feature
**Behaviour:** changing
**Request:** Give the operator a People page for keeping the list of names tasks can be assigned to. Run from `products/tracker17/` under `python3 main.py`. The header of every page that carries it gains a People link (SDD § 4 EX-12). `GET` of the People address shows the assignee list, in the order names were added, with an Add form and a Remove beside each name; the page says nothing of the operator's name and has no comment. Adding a name puts it at the end of the list. A blank name, and a name already on the list (compared exactly), are each refused on the People page where it was entered, with the typed text kept and the saved data unchanged (SRS FR-20; UXD UX-I3, UX-F8). Removing a name removes it with no confirmation step, and its completion line says the name stays on the tasks that carry it (SRS FR-22; UXD UX-S8). After an add the page opens with keyboard focus on the added name and the completion line as that element's accessible description, with no script (SDD § 4 EX-5, EX-14, RT-9). The rules live in `domain/assignees.py`, new here, and the web and application parts call them (SDD § 4 TS-3). The list is stored as the SDD's DR-4 already states, and every string on the page comes from the product's content record, none invented in code.

Tests ship with it: unit tests for `domain/assignees.py`; integration tests through the real server for the header link, the list page, add, both refusals and remove; and an end-to-end test under `products/tracker17/tests/e2e/` that adds a name in a real browser and asserts the focus and accessible-description behaviour above. This is the seed's first focus test on an element that is not a control (SDD § 11 R-2). `pytest products/tracker17/tests/` exits 0 with the unit, integration, end-to-end and architecture layers collected, and `python3 products/tracker17/tests/timed_run.py` still exits 0.

**Must not be weakened or added:** no task, priority, due date or label, and `domain/tasks.py`, `priorities.py`, `due_dates.py` and `labels.py` are not created; the saved form of a task is not changed and no state migration is written; People carries no Your name field and no comment; every test and page that passed before still passes, and no existing test is weakened to fit.

---

## Change Summary

The tracker gains People, a page reached from the header, where the operator sees the assignee list, adds a name to its end and removes a name in one press. The list is saved with the rest of the tracker's data. This change realizes FDR R-57 to R-59 and R-61 for the list itself. Nothing yet uses the list on a task.

Every place below that says "the content step's words" means the wording is written in this change's text record under `products/tracker17/docs/CONTENT.md`. This spec states what each string must say, and never its words.

---

## Rules

### The header

- **CP-80:** Every page the tracker serves carries the People link in its one header, beside the Projects link it carries today. That covers the Projects page, a project's page, the not-found page and the People page itself. The link's text is "People", the area's name (UXD § 4; CONTENT.md § Accessibility of text, link text). Following it opens the People page, and opening People changes no data (FDR R-106). The link order and how the links look are the UXD's and `DESIGN.md`'s to set. *(SDD § 4 EX-12; UXD § 4)*

### The People page

- **CP-81:** A `GET` of the People page's address opens the People page. Its title follows CONTENT.md's page-title pattern, which gives "People - tracker17". The page shows the assignee list and an Add form holding one name field and an Add button. The address is development-design's to choose. *(SRS FR-20; UXD UX-S8; CONTENT.md § Accessibility of text)*
- **CP-82:** The list shows every name on the assignee list exactly as it is saved, surrounding spaces included, in the order the names were added, the earliest first. A name that was removed and then added again shows at the end. A name holding `<` or `&` shows as typed and changes nothing around it (FDR R-112). *(SRS FR-20; SDD § 3, What the system holds, DR-4: "in the order added")*
- **CP-83:** Each listed name has one Remove control beside it. Its visible label is "Remove". Its accessible name holds "Remove" as one unbroken string and names the name it removes, so that two Remove controls never share an accessible name. The content step's words. *(UXD UX-F8; CONTENT.md § Accessibility of text, the label-in-name rule)*
- **CP-84:** When the list holds no name, the list area says there are no assignees yet and that tasks can be assigned only to names on this list, in the content step's words. It never shows a blank list, and the Add form stays in view. *(UXD UX-S8, empty state; CONTENT.md § Message patterns, Empty)*
- **CP-85:** People shows nothing about the operator's name: no Your name field and no sentence about a name being set or needed. It shows no comment. No word on the page points at a task, an assignment or any other control or area the tracker does not have yet. *(SDD § 4 EX-12; § 6 S-2, "nothing yet about the operator's name")*

### Adding a name

- **CP-86:** A name is added when it has at least one character other than whitespace, is not already on the list, and is at most 200 characters long. It goes at the end of the list and is saved, and the People page answers the submission. Reloading that page, or reaching it again with back or forward, adds nothing. *(SRS FR-20; FDR R-57, R-106; SDD § 4 RT-8)*
- **CP-87:** After an add, the People page opens with keyboard focus on the added name in the list, with that name in view. The completion line names the added name, quoted, in the content step's words. It is the accessible description of the focused name, and the line itself never takes focus. The added name is not a stop in the Tab order. The next Tab press moves to the first control after the added name in reading order. The page runs no script. *(SDD § 4 EX-5, EX-14, RT-9, EX-2; UXD UX-I4, UX-A5)*
- **CP-88:** Names are saved exactly as typed and compared exactly. `Dana`, `dana` and `Dana ` are three different names, and each can be on the list together with the others. *(SRS FR-20, DR-4; FDR R-58, R-80)*
- **CP-89:** A name with no character other than whitespace, the empty name included, is refused. The saved data does not change. The People page opens with keyboard focus in the Add form's name field, and the text that was typed is still in it. The reason sits beside the field and is the field's accessible description. It says a name is needed and what to do, in the content step's words. *(SRS FR-20, FR-39; FDR R-58, R-100; UXD UX-I3; SDD § 4 EX-4, EX-14)*
- **CP-90:** A name that is already on the list, compared exactly, is refused in the same way as CP-89. The typed text is kept, focus is in the name field, and the saved data does not change. The reason quotes the typed name, says it is already on the list, and says what to do. *(SRS FR-20, FR-39; FDR R-58; UXD UX-I3)*
- **CP-91:** The Add form's name field lets in at most 200 characters, and a name of exactly 200 characters is added. One character is one Unicode code point (FDR R-77). Only a request that no page of the tracker sends can carry a longer name, and that name is refused. The saved data does not change. The People page opens with focus in the name field and the reason beside it, and neither the page nor its address holds any of the sent text. A name that is too long and also blank, such as 201 spaces, gets the too-long reason. That is the same order of reasons a project name gets (CP-20). *(SRS FR-40; FDR R-76 to R-79; PD-11; SDD § 4 RT-8, RT-10)*
- **CP-92:** An add is checked against the list as saved at the moment it is applied. If another tab added a name after this page loaded, adding the same name here is refused under CP-90. *(FDR R-102)*

### Removing a name

- **CP-93:** Pressing a name's Remove control takes that name off the list and saves the change. There is no confirmation step, and the People page answers. Reloading that page, or reaching it again with back or forward, removes nothing. *(SRS FR-20; FDR R-57, R-106; UXD UX-F8, UX-S8)*
- **CP-94:** After a remove, the completion line names the removed name, quoted, and says that tasks already carrying the name keep it, in the content step's words. The removed name has left the page, so the page opens at the top of the area that held the list, where the completion line sits. Keyboard focus is there, and the line is the accessible description of the element that has focus. Development-design chooses which element that is. *(SRS FR-22; FDR R-61; UXD UX-S8; SDD § 4 EX-5, EX-14)*
- **CP-95:** A remove matches the name exactly, so removing `Dana` leaves `dana` and `Dana ` on the list. *(FDR R-58)*
- **CP-96:** A remove is checked against the list as saved at the moment it is applied. If the name is no longer on the list, because another tab removed it, the remove is refused and the saved data does not change. The reason says the name is no longer on the list and offers a reload, in the content step's words. The People page shows the list as saved, and it opens as CP-94 places it, with the reason in place of the completion line. If another tab removed the name and then added it again, the remove takes it off, because the name is on the list. *(FDR R-59, R-100, R-102; UXD UX-I3, the out-of-date refusal)*

### Failures and protection

- **CP-97:** When an add or a remove fails for a reason that is not a refusal, such as the save failing, the saved data and the list stay as they were. The People page says in plain words that the action did not happen and that nothing was changed, in the content step's words, and it shows no error text from Python. After a failed add, the typed text is still in the name field and focus is on the Add form. After a failed remove, the name is still listed and focus is on its Remove control. The console shows a message naming the action, then the error. *(FDR R-18, R-107, R-108; UXD UX-I5; SDD § 4 OB-3)*
- **CP-98:** An add or a remove that does not come from the tracker's own pages is refused and changes nothing, under the same check every submission passes today. That covers one marked `cross-site` or `same-site`, and one not marked `same-origin`, a submission with no mark included. *(FDR R-110; SDD § 4 SEC-2)*

### Saved data

- **CP-99:** The assignee list, in its order, is still there after the tracker is stopped and started again. *(FDR R-15; SRS DR-4)*
- **CP-100:** Some saved data was written before this change and holds the projects and the project counter but no assignee list. A tracker started on it starts normally, with every project present and an empty assignee list. The start does not report the data as unreadable and leaves the file's bytes unchanged. The first add or remove after that saves the list with the rest. *(FDR R-15, R-21; see Locked Answers, Gap 1)*
- **CP-101:** Saved data counts as unreadable when its assignee list holds a blank name, two names that are the same compared exactly, a name over 200 characters, or anything that is not a list of text. The start handles it as it handles any other unreadable saved data: it shows the console message saying it couldn't read the saved data and naming its location, and the data's bytes are unchanged. *(FDR R-21, R-22, R-24, R-27; SDD § 4 SD-5)*

### Where the feature lives, and its proof

- **CP-102:** The Assignees feature's entry point is `domain/assignees.py`, fixed by SDD § 4 TS-3's table. Its opening docstring names the SRS requirements the module realizes in this change, every `application` and `web` module that takes part, and the test modules that check it. Every new test module names the requirements or CP rules it checks. The trace check lists `assignees` as a landed feature word (SDD § 4 TS-4). Today it lists only `projects` (`products/tracker17/tests/architecture/test_trace.py:24`), and it fails once `domain/assignees.py` exists unless the word is added (see Verified Claims). *(SRS NFR-9; SDD § 4 TS-3, TS-4)*
- **CP-103:** The tests ship with the change:
  - Unit tests check `domain/assignees.py` with no file and no clock. They cover CP-86, CP-88 to CP-92, CP-95, CP-96 and CP-101's rules.
  - Integration tests run the tracker's whole request path in one process, as SDD § 4 TS-1 sets out. They check the header link (CP-80), the People page and its empty state (CP-81 to CP-85), add (CP-86) and both of its refusals (CP-89, CP-90), the too-long name (CP-91), remove (CP-93, CP-94), the stale remove (CP-96), a failed save (CP-97) and the cross-site refusal (CP-98). They also check that the list survives a stop and a start (CP-99), the start on data from before this change (CP-100), and each break CP-101 names.
  - One end-to-end test under `products/tracker17/tests/e2e/` runs in Chromium against a tracker started by `main`. It adds a name holding `<` and `&`, and asserts three things: the name shows as typed, keyboard focus is on the added name, and the completion line is that name's accessible description (CP-87). *(SDD § 4 TS-1; § 11 R-2, R-3)*
- **CP-104:** `pytest products/tracker17/tests/` exits 0 with the unit, integration, end-to-end and architecture layers collected, and `python3 products/tracker17/tests/timed_run.py` exits 0. Every test that passed before this change still passes, and no existing test is weakened or removed to make it pass. *(SDD § 4 TS-1, TS-5; the request)*
- **CP-105:** The change creates none of `domain/tasks.py`, `domain/priorities.py`, `domain/due_dates.py` or `domain/labels.py`. It adds no task, priority, due date or label anywhere. It writes no step that converts saved data from one form to another, so the saved data from before this change is read as CP-100 states. *(the request, "Must not be weakened or added")*

---

## Examples

| Scenario | Expected behavior | Rule |
|---|---|---|
| Any page the tracker serves, Projects, a project, not-found or People | The header holds a link to Projects and a link reading "People". Following "People" opens the People page and changes nothing. | CP-80 |
| `GET` People, list empty | Title "People - tracker17". The list area says there are no assignees yet and that tasks can be assigned only to names on this list. The Add form is in view. No Your name field and no comment. | CP-81, CP-84, CP-85 |
| Add `Dana`, then `Ari`, then `Bo` | The list shows `Dana`, `Ari`, `Bo` in that order, each with one Remove control. Each Remove's accessible name names its own name. | CP-82, CP-83, CP-86 |
| Add `Dana`, remove `Dana`, add `Ari`, add `Dana` | The list shows `Ari`, `Dana`. | CP-82 |
| Add `Cy` | The page opens with focus on `Cy` in the list and `Cy` in view. The completion line names `'Cy'` and is `Cy`'s accessible description. One Tab moves to the next control after `Cy`. Reloading adds nothing. | CP-86, CP-87 |
| `Dana` is on the list, add `dana`, then `Dana ` | Both are added. The list holds three names. | CP-88 |
| Add an empty name, then `   ` | Each is refused. Focus is in the name field, the typed text is still in it, and the reason is beside it. The saved data is unchanged. | CP-89 |
| `Dana` is on the list, add `Dana` | Refused. The reason quotes `'Dana'` and says it is already on the list. `Dana` stays in the field, and the saved data is unchanged. | CP-90 |
| Add a name of 200 characters | Added. | CP-91 |
| A hand-built request adds a 201-character name, then 201 spaces | Each is refused with the too-long reason beside the name field. None of the sent text is on the page or in its address. The saved data is unchanged. | CP-91 |
| Tab 1 loads People. Tab 2 adds `Eve`. Tab 1 adds `Eve` | Tab 1's add is refused as already on the list. | CP-92 |
| `Dana` is on the list, press `Dana`'s Remove | `Dana` leaves the list at once, with no confirmation. The completion line names `'Dana'` and says tasks that carry the name keep it. The page opens at the top of the list's area, with focus on the element the line describes. Reloading removes nothing. | CP-93, CP-94 |
| `Dana`, `dana` and `Dana ` are on the list, remove `Dana` | `dana` and `Dana ` remain. | CP-95 |
| Tab 1 shows `Dana`. Tab 2 removes `Dana`. Tab 1 presses `Dana`'s Remove | Refused. The reason says `Dana` is no longer on the list and offers a reload. The saved data is unchanged. | CP-96 |
| Tab 1 shows `Dana`. Tab 2 removes `Dana` and adds it again. Tab 1 presses `Dana`'s Remove | `Dana` is removed. | CP-96 |
| The save fails while adding `Cy` | The page says the add didn't happen and nothing changed. `Cy` is still in the field and focus is on the Add form. The console names the action and the error. The list is unchanged. | CP-97 |
| The save fails while removing `Dana` | The page says the remove didn't happen and nothing changed. `Dana` is still listed and focus is on its Remove. The console names the action and the error. | CP-97 |
| An add submission marked `Sec-Fetch-Site: cross-site` | Refused. The saved data is unchanged. | CP-98 |
| Add `Dana` and `Ari`, stop, start | The list shows `Dana`, `Ari`. | CP-99 |
| Start on a saved file holding only `next_project_id` and `projects`, written before this change | The tracker starts with every project and an empty assignee list. The file's bytes are unchanged until the first add or remove. | CP-100 |
| Start on saved data whose assignee list holds `Dana` twice | The start shows the console message saying the saved data couldn't be read, with its location. The bytes are unchanged. | CP-101 |
| Start on saved data whose assignee list holds `"   "`, a 201-character name, or a number | The same as the row above. | CP-101 |
| Read `domain/assignees.py`'s opening docstring | It names the SRS requirements, the `application` and `web` modules, and the test modules. The trace check lists `assignees` as landed and passes. | CP-102 |
| Run the e2e test | It adds `<b>A&B</b>`, sees it shown as typed, focus on it, and the completion line as its accessible description. | CP-103 |
| `pytest products/tracker17/tests/` and `python3 products/tracker17/tests/timed_run.py` | Both exit 0. The four layers are collected and no earlier test is weakened. | CP-104 |
| `ls products/tracker17/domain` after the change | It holds `assignees.py`, and none of `tasks.py`, `priorities.py`, `due_dates.py` or `labels.py`. | CP-105 |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| The header today holds one link, to Projects (CP-80's "beside the Projects link it carries today"). | Read `products/tracker17/web/pages.py:51-53`. | `<header class="site-header">` … `<nav><a href="{PROJECTS_ADDRESS}">Projects</a></nav>`. That is the only link. |
| `domain/assignees.py` does not exist today (CP-102, CP-105). | `ls products/tracker17/domain` | `__init__.py projects.py refusals.py state.py text.py` |
| Saved data written today holds the project counter and the projects and no assignee list (CP-100). | In a disposable copy (`git archive HEAD products/tracker17`), `SavedData(loc).save()` ran on a state with one project and the written `tracker.json` was read back. The real `persistence` code wrote to a real file. | Its keys were `['next_project_id', 'projects']`. |
| Today's loader refuses a document whose top-level keys are not exactly those two (`products/tracker17/persistence/saved_data.py:20`, `:77`). This is why CP-100 is stated: adding the list to the saved form without it would leave earlier data unreadable. | The same copy. An `assignees` key was added to the written file and `SavedData.load()` ran on it. | `UnreadableData` was raised. |
| The trace check fails once `domain/assignees.py` exists unless `assignees` is listed as landed (CP-102). | The same copy, a post-change tree made by writing a stub `domain/assignees.py`, then `python3 -m pytest tests/architecture/test_trace.py`. | `FAILED test_each_feature_word_with_its_domain_module_is_listed_as_landed`, 1 failed and 17 passed. |
| Unreadable saved data today stops the start with one console message naming the location (CP-101). | Read `products/tracker17/main.py:41-45`. | `except UnreadableData:` prints "The tracker didn't start, because it couldn't read its saved data at {location}. Nothing in it was changed. …" |
| Too-long before blank is the order of reasons projects already use (CP-91). | Read `products/tracker17/domain/projects.py:37-45` and the sealed CP-20 (`journey/tobiishi/trail/2026-10-07_create-a-project-that-stays/change_spec.md:55`). | "Over-long comes before blank … (CP-20)." |
| The baseline suite passes, apart from layers that need a git checkout or a browser. | The same copy, with the system's `pytest 9.0.3`, ran `pytest -q products/tracker17/tests/unit …/integration …/architecture`. `python3 products/tracker17/tests/timed_run.py` ran too. | 223 passed and 1 failed: `test_data_is_ignored_by_version_control`, with "fatal: not a git repository", because the archive copy is no git checkout (SDD § 6 S-1). `timed_run.py` exited 0. The e2e layer was not run, because Playwright is not installed on this machine and the product has no `.venv`. |
| The request says this is "the seed's first focus test on an element that is not a control". This is partly contradicted. | Read `products/tracker17/tests/e2e/test_first_project.py:70`. | An existing e2e test already asserts `document.activeElement.tagName == "H1"` after a create, which is a non-control taking focus. No existing test asserts a non-control's **accessible description**. CP-87's test is the first to do that. No rule rests on the request's wording. |

---

## Out of Scope

- **Any use of the list on a task.** Adding and listing tasks, assigning a task, the add-task form's assignee choice, and the left-the-list rules of SDD § 4 RT-7 and FDR R-48 and R-118 belong to later stations (`add-and-list-tasks`, `edit-task-fields`).
- **The operator's name and comments.** The Your name half of People, UXD UX-S8's "no name set" state, and comments belong to the `comment-on-a-task` seed.
- **The assignee filter (FDR R-84) and the summary's per-assignee rows (FDR R-97, R-98).** Those slices are later.
- **The not-found page's body.** It gains the header's People link under CP-80 and nothing else. CONTENT.md § Error names the places that page offers, and People is not among them.
- **The unreadable-data page.** It does not exist yet (`products/tracker17/main.py:41-45` stops the start instead). When the slice that adds it lands, that page carries no header (SDD § 4 EX-12), so CP-80 does not reach it.
- **README § Status and `products/tracker17/docs/what_left.md`.** Both shrink after the station closes, in the `readme-status` run, the only run that removes a what-left entry (`<CORE>/doctrine/setup/kensaiapp_structure.md` § The what-left file). This change edits neither.
- **Adding assignee actions to `tests/timed_run.py`.** The request asks only that the run still exits 0 (CP-104).
- **The SDD's Open Question and § 11 R-2's fallback.** If CP-87's end-to-end test cannot pass without script, the change does not fall back to anything. That outcome is a finding for the Principal Architect. Closing the SDD's Open Question is that seat's job as well.

---

## Locked Answers (the divergence record — self-review 2026-10-11)

- **Gap 1 — saved data from before this change (CP-100):** it loads with an empty assignee list and is not reported as unreadable. The request says "no state migration is written" and gives no reading rule for data that predates the list. Today's loader refuses any top-level key set other than its two (see Verified Claims). Adding the list to the saved form with nothing else would therefore make the operator's earlier projects read as unreadable, which breaks FDR R-15 ("Everything the operator enters is still present after the tracker is stopped and started again"). Reading a missing list as empty writes nothing and converts nothing, so it keeps "no migration". It is the additive, reversible choice. *(b: an implicit behaviour, locked conservatively)*
- **Gap 2 — the stale remove (CP-96):** refused with a reason, as FDR R-59 states. The request names only the successful remove. The control that was used is gone, so EX-4's "opens at the control that was used" cannot apply. The page opens where CP-94 places a completion line, the top of the list's area, which is the place SDD § 4 EX-5 gives an action whose subject has left the page. *(b)*
- **Gap 3 — the too-long name (CP-91):** a field limit of 200, a refusal, and a reason that holds none of the sent text. The request names two refusals. SDD § 4 RT-10 says "A slice that adds a text field writes the field's `maxlength` and adds a test that a longer value is refused", and PD-11 keeps the typed text out of the page for this refusal alone. When a name is too long and also blank, the too-long reason wins, matching the order project names already have (CP-20), so that the same input gets the same answer on both forms. *(b)*
- **Gap 4 — a failed add or remove (CP-97) and the cross-site refusal (CP-98):** stated for the new actions. The request names neither. FDR R-107 and R-110 bind every action, and the two new submissions are new actions. *(b)*
- **Gap 5 — focus after a remove and after a refusal (CP-89, CP-90, CP-94):** pinned. The request pins focus only after an add. SDD § 4 EX-4, EX-5 and EX-14 state these for every action, so leaving them out would hand development-design a choice the SDD has already made. *(b)*
- **Gap 6 — the e2e test enters `<` and `&` (CP-103):** this is added to the request's end-to-end test. SDD § 11 R-3's response is that "each slice's end-to-end test enters such text in the fields the slice adds". *(b)*
- **Gap 7 — "integration tests through the real server" (CP-103):** read as the tracker's whole request path in one process, with no socket. SDD § 4 TS-1 fixes the integration layer as "`web` with `application` in one process with no socket", and the existing integration tests drive the request path that way. A test that starts the real process and drives it over a socket is the end-to-end layer, which CP-103 already has. *(a: the request read against the SDD)*
- **Gap 8 — the saved-data breaks (CP-101):** stated. The request says only that the list is stored "as the SDD's DR-4 already states". SDD § 4 SD-5 says "A slice that adds a data rule adds a test that saved data breaking the rule is reported as unreadable", and FDR R-22 names a blank or duplicate assignee name among those breaks. *(b)*
- **Gap 9 — "the seed's first focus test on an element that is not a control":** CP-103 does not repeat this. An existing test already moves focus to a heading (see Verified Claims). What this change's test adds first is the accessible description of an element that is not a control. *(a: a claim in the request corrected against the tree)*
