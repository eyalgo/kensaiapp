# Change Spec — Labels on a task

**Date:** 2026-10-12
**Category:** feature
**Behaviour:** changing
**Request:** Let the operator put labels on a task and take them off. The task page gains a label area: each label the task carries shows with a Remove button, and a text field with Add puts on one more, one at a time (SRS FR-23; UXD UX-F9). A task with no labels says so in a sentence, with Add in view (UXD UX-S6). A label is free text, must not be empty, is stored exactly as typed and compared exactly, and takes at most 200 characters (SRS FR-23, FR-40). Adding a label redirects to the task's page, which shows it, and puts the page's focus on the added label (SDD § 11 R-2). Adding a label the task already carries leaves the task as saved. Removing a label leaves the others. The task list row shows the labels the task holds. An empty label and a label over 200 characters are each refused on the task page where it was entered, with the typed text kept and the saved data unchanged. The label rules live in a new `domain/labels.py`, and the add and remove in the domain and application parts, not the web part (SDD § 4 TS-3). The saved data already holds each task's labels; this change adds the check that the data keeps the rule: saved data in which a task carries an empty label, a label over 200 characters or a repeated label is reported as unreadable at start, and none of it is loaded (SDD § 4 SD-5; SRS DR-6). Every string comes from the product's content record, none invented in code. Tests ship with it: unit tests for the label rules; integration tests through the real server for the label area as shown (labels with Remove and Add, and the no-labels sentence with Add in view), an add, a repeated add, a remove that leaves the others, the list row showing the labels, and the two refusals with the typed text kept; a start-check test that writes saved data with an empty label, one over 200 characters and a repeated label, one case at a time, and finds the start reporting each as unreadable and loading none of it. An end-to-end test adds a label and finds the page's focus on the added label (SDD § 11 R-2, `SDD.md:L755`). An end-to-end test enters a label holding `<`, `&` and `"` and finds the task's page and the project's list showing it as typed (NFDR QC-36). `python3 products/tracker17/tests/timed_run.py` times a label add among its actions at 1,000 tasks and exits 0 (NFDR QC-48). `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/` each exit 0, run on a `git archive HEAD` copy that is `git init`-ed, since the repository-ignore test needs a git repo.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `core/doctrine/engineering/languages/python/README.md` opened, and every concern it routes read

---

## Change Summary

The operator can add labels to a task and remove them, one at a time, from the task's page. The project's list shows each task's labels. A start now refuses saved data that breaks the label rule. Until now, labels existed only in the saved form and the list row, with no action and no rule.

Paths below are relative to the product root, which `system/projects/tracker17/project.md` `Product path:` names. `SRS`, `SDD`, `UXD`, `FDR`, `NFDR` and `CONTENT.md` are the product's documents under `docs/`. Every SRS item cited is version 6, the SDD version 9, the NFDR version 11 and the FDR version 4.

---

## Rules

### The label area on the task page

- **CP-182:** The task's page shows a label area. Each label the task carries is shown as typed, in the order it was added, with a Remove button beside it. A text field with a visible label, followed by an Add button, puts on one more label. *(SRS FR-23; UXD UX-F9, UX-S6; SDD § 4 EX-9)*
- **CP-183:** For a task that carries no labels, the label area shows a sentence saying the task has no labels, with the label field and Add in view. No empty list shows as a blank space. *(UXD UX-S6; FDR R-95)*
- **CP-184:** Every word the label area, its refusals and its completion lines show follows `docs/CONTENT.md` (SDD § 4 EX-11). The thing is called a label. The two buttons read `Add` and `Remove` (`CONTENT.md` terminology rows "A word attached to a task", "Putting something into a thing that holds it" and "Taking a name or a label off"). This spec fixes what each line must say. Its wording belongs to the content stage.
- **CP-185:** Each Remove button's accessible name contains its visible word as one unbroken string, and names the label and the task, as `CONTENT.md` § Accessibility of text requires. That section gives "Remove label 'bug' from 'Set up CI'" as its example. *(UXD UX-A5; SDD § 4 EX-9)*
- **CP-186:** The label field's `maxlength` is the label maximum, 200 characters, and is written from the one place in `domain` that states the maximum. The field states no maximum beside it. *(NFDR QC-9; SDD § 4 RT-10; ADR-0007; UXD version 4 header: "the comment field and the project-description field each state their maximum length beside the field, and no other field does")*

### Adding a label

- **CP-187:** Pressing Add with a label that is not empty, is at most 200 characters, and is not already on the task adds that label after the task's existing labels. The task is saved, and the browser is sent to the task's page. That page shows the label in the label area, plus one completion line naming the added label. Keyboard focus is on the added label, and the completion line is its accessible description. *(SRS FR-23; SDD § 4 EX-5, EX-14, RT-8, RT-9; SDD § 6 S-2 *Command*; SDD § 11 R-2)*
- **CP-188:** A label is saved and shown exactly as typed: surrounding spaces and letter case are kept. A label of spaces only is accepted. Length is counted in Unicode code points on the value as saved, spaces included. So a label of exactly 200 code points is accepted, including one holding characters outside the Basic Multilingual Plane. *(FDR R-64, R-77, R-80; SRS FR-23, FR-40; ADR-0007)*
- **CP-189:** Adding a label that the task already carries, compared exactly, is not refused. It changes nothing: the task still carries the label once, the saved data is unchanged, and no save is made. The task's page that answers shows no completion line and no refusal. `Bug` added to a task carrying `bug` is a different label and is added under CP-187. *(SRS FR-23; FDR R-65; NFDR QC-21; SDD § 3 `application` row)*
- **CP-190:** An empty label, which is the label holding no character at all, is refused. The saved data is unchanged. The task's page opens with keyboard focus in the label field and the reason beside the field as its accessible description, and the field holds what was typed. *(SRS FR-39; FDR R-64, R-100; UXD UX-I3; SDD § 4 EX-4, EX-14)*
- **CP-191:** A label longer than 200 code points is refused, and the saved data is unchanged. Only a request that no page of the tracker sends can carry such a label, because CP-186's field stops at 200. The page that answers opens at the label field, gives the reason beside it, and holds none of the text that was sent. *(SRS FR-39, FR-40; FDR R-78, R-79, PD-11; SDD § 4 RT-8, RT-10; ADR-0006)*

### Removing a label

- **CP-192:** Pressing a label's Remove button takes that one label off the task. The task's other labels stay, in their order. The task is saved, and the browser is sent to the task's page, which shows one completion line naming the removed label. The thing acted on is no longer on the page, so the page opens "at the top of the sheet the thing was on, where the completion line sits" (SDD § 4 EX-5). The completion line is the accessible description of the element the page opens on (SDD § 4 EX-14). *(SRS FR-23; FDR R-63; SDD § 4 RT-8, RT-9)*
- **CP-193:** Removing a label the task does not carry, compared exactly, is refused. One way this happens is a page shown before another tab removed the label. The saved data is unchanged. The task's page opens at the label area with keyboard focus there, and the reason in the label area is the focused element's accessible description. *(FDR R-66, R-100, R-102; SRS FR-39, NFR-3; SDD § 4 EX-4, EX-14)*

### Either action

- **CP-194:** An add or a remove sent for a task that does not exist is answered with the not-found page that speaks of a task, and changes nothing. *(FDR R-103, R-105; UXD UX-S6, UX-S10; SDD § 4 EX-13)*
- **CP-195:** Adding a label and removing one can each be done from the keyboard alone, with the browser's own keys. *(SDD § 4 EX-8; UXD UX-I6)*

### The task list

- **CP-196:** Each row of a project's task list shows, in its Labels column, the labels the task carries. Each label shows as typed, in the order it was added. This change does not alter how that cell is rendered: today it joins the labels with `, ` and shows `none` for a task with none (Verified Claims). *(UXD UX-S4; SDD § 6 S-2 *Behaviour*)*

### Saved data at start

- **CP-197:** At start, saved data is unreadable when any task in it carries an empty label, a label longer than 200 code points, or the same label twice, compared exactly. In each case:
  - the console says the data is unreadable and names its location;
  - the start refuses as it does today for any other unreadable data: the tracker does not start and exits non-zero (`main.py:39-48`);
  - nothing of the data is loaded;
  - the saved data's bytes are unchanged.

  Labels of spaces only, labels of exactly 200 code points, and one label carried by two different tasks all still load. Today all three breaks load: `restore_task`'s docstring at `domain/tasks.py:275-276` reads "label and comment content carries no rule here", and the probe in Verified Claims loaded each break. *(SRS DR-6; FDR R-21, R-22, R-23, R-24, R-27; SDD § 4 SD-4, SD-5)*
- **CP-198:** The saved form of a task and of the People list does not change. A task keeps its `labels` list as it is saved today, and no key is added. *(Request, "Must not be weakened or added"; NFDR QC-46)*

### What does not move

- **CP-199:** The edit form for title, priority, assignee and due date stays as `edit-task-fields` left it. An add, a remove or a refused label action changes no field of the task other than its labels. *(Request, "Must not be weakened or added"; FDR R-47)*

### Where the code lives (fixed by the records)

- **CP-200:** The label rules live in a new module, `domain/labels.py`. The add and the remove are applied in `domain` and `application`, and `web` holds no label rule (SDD § 4 TS-3; NFDR QC-11, QC-20, QC-21, QC-23). The opening docstring of `domain/labels.py` names SRS FR-23 and FR-40, every `application` and `web` module that takes part, and the test modules that check it (SDD § 4 TS-3; NFDR QC-11). The word `labels` is listed as landed in the pointer test, `tests/architecture/test_trace.py` (SDD § 4 TS-4; NFDR QC-11). Every test module the change adds names the requirements or acceptance criteria it checks (SDD § 4 TS-3).
- **CP-201:** Each refused condition this change adds has its own refusal type, defined and raised in `domain` and handed to `web` through `application`. `web` maps each type to its reason, and no part tells one refusal from another by reading its message. *(NFDR QC-5, QC-16; SDD § 4 OB-4)*

### Tests (named in the request, or required by the records)

- **CP-202:** Unit tests cover the label rules in `domain` with no file and no clock: the empty refusal, the over-long refusal, the 200-code-point boundary, the spaces-only label, the exact comparison, the repeated add that changes nothing, the remove that keeps the others in order, and the remove of a label not carried. *(Request; SDD § 4 TS-1)*
- **CP-203:** Layer-3 and layer-4 tests run in one process with the clock and the saver handed in, and cover:
  - the label area as shown, with labels, Remove and Add;
  - the no-labels sentence with Add in view;
  - an add;
  - a repeated add;
  - a remove that leaves the others;
  - the list row showing the labels;
  - the label field's `maxlength` equal to the maximum `domain` states (CP-186);
  - one test per refusal, each asserting the reason shown and the saved data unchanged: the empty label (field kept), the over-long label sent in a request no page sends (the answer holds none of the sent text), the remove of a label not carried, and an add and a remove for a task that does not exist.

  *(Request; SRS AC-12; NFDR QC-5, QC-9, QC-38; SDD § 6 S-1 *Command*, the over-long pattern)*
- **CP-204:** A layer-3 test finds that a repeated add hands the saver nothing. *(NFDR QC-21)*
- **CP-205:** Start tests write saved data with an empty label, with a label of 201 code points, and with a label repeated on one task, one case per test. Each test finds the start reporting the data unreadable, loading none of it, and leaving its bytes unchanged. *(Request; SRS AC-7; SDD § 4 SD-5; NFDR QC-22, QC-37, QC-51)*
- **CP-206:** Three existing tests cover the new actions:
  - the route test of NFDR QC-7 covers each submission route this change adds;
  - the outbound-connection test of NFDR QC-35, which drives actions through `web` under the audit hook, drives a label add and a label remove;
  - a recording-saver test under NFDR QC-54 runs a label add and a label remove, and finds that the saver received only saves.

  *(NFDR QC-7, QC-8, QC-34, QC-35, QC-54)*
- **CP-207:** Two end-to-end tests drive Chromium against a tracker started by `main`:
  - one adds a label and finds keyboard focus on the added label, with the completion line as its computed accessible description (SDD § 6 S-2 *Command*; SDD § 11 R-2; SDD § 4 RT-9, EX-14);
  - one enters a label holding `<`, `&` and `"` and finds the task's page and the project's list showing it as typed (NFDR QC-36; SDD § 11 R-3; FDR R-112).
- **CP-208:** `python3 tests/timed_run.py`, run from the product root at 1,000 tasks, times a label add and a label remove among its actions. Each shows its result within 1 second, each is sent marked `same-origin`, and the run exits 0. It fails when a timed action is refused or fails. *(SRS NFR-1, "every operator action", AC-15; NFDR QC-48, QC-32; SDD § 4 TS-5)*
- **CP-209:** Four existing tests encode the state this change reverses. They change only in what they assert about labels, and each keeps every other assertion:
  - `test_only_the_task_features_are_added_to_domain` in `tests/architecture/test_shapes.py` asserts at line 181 that `domain/labels.py` does not exist;
  - `test_no_labels_module_or_excluded_feature_entry_exists` in `tests/architecture/test_trace.py` asserts the same at line 332, and that the landed list is the five present words;
  - `test_historical_assignee_and_structural_label_comment_values_load` in `tests/integration/test_saved_data.py` loads the labels `["", "x", "x"]` at line 837. Its assertions that an off-list assignee and comment content load stay;
  - `_state_holding_every_field` in the same file builds a task carrying `["bug", "ui", "bug"]` at line 571, which CP-197 makes unreadable.

  No other existing test is changed to fit. *(Request, "no existing test is weakened to fit")*
- **CP-210:** Two sets of commands exit 0:
  - `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/`, run on a `git archive HEAD` copy that is `git init`-ed, so `test_data_is_ignored_by_version_control` has its repository (NFDR QC-47; `CROSS_ROLE.md` § Every seat);
  - from the product root, `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web` (NFDR QC-62).

---

## Examples

| Scenario | Expected behavior | Rule |
|---|---|---|
| Task `Set up CI` carries `bug` then `ui`; its page is opened | The label area shows `bug` then `ui`, each with a Remove button, then the label field and Add. Remove beside `bug` has an accessible name naming `bug` and `Set up CI` and containing "Remove". | CP-182, CP-185 |
| A task with no labels; its page is opened | The label area shows a sentence saying the task has no labels, with the field and Add in view. | CP-183 |
| The task page's label area | The buttons read `Add` and `Remove`. Every line follows `CONTENT.md`. | CP-184 |
| The task page's label field | `maxlength` equals the label maximum `domain` states (200). No sentence states a maximum beside it. | CP-186 |
| Task carries `bug`; the operator adds `ui` | Saved. The task's page shows `bug` then `ui` and one completion line naming `ui`. Focus is on `ui`, described by that line. | CP-187 |
| The operator adds ` Ops ` (surrounding spaces) | Saved and shown as ` Ops `, spaces kept. | CP-188 |
| The operator adds `   ` (three spaces) | Accepted and saved as typed. | CP-188 |
| The operator adds a label of 200 code points, one of them `😀` | Accepted. | CP-188 |
| Task carries `bug`; the operator adds `bug` | Not refused. The task still carries `bug` once. No save is made, and the page shows no completion line and no refusal. | CP-189, CP-204 |
| Task carries `bug`; the operator adds `Bug` | Added. The task carries `bug` then `Bug`. | CP-187, CP-189 |
| The operator presses Add with the field empty | Refused. The saved data is unchanged. The page opens with focus in the label field, and the reason is its accessible description. | CP-190 |
| A request with no page behind it sends a 201-code-point label | Refused. The saved data is unchanged. The page gives the reason at the label field and holds none of the sent text. | CP-191, CP-203 |
| Task carries `bug`, `ui`, `ops`; the operator removes `ui` | Saved. The task carries `bug` then `ops`. One completion line names `ui`, and the page opens at the top of the sheet `ui` was on, where that line sits. | CP-192 |
| Tab 1 shows the task with `ui`. Tab 2 removes `ui`. Tab 1 presses Remove beside `ui` | Refused with the reason in the label area. The page opens there. The saved data is unchanged. | CP-193 |
| An add sent for task 99, which does not exist | The not-found page that speaks of a task. Nothing changes. | CP-194 |
| The operator tabs to the label field, types `bug` and presses Enter, then tabs to Remove beside `bug` and presses Enter | `bug` is added, then removed, with no pointer used. | CP-195 |
| Project list where task T carries `bug` then `ui` | T's Labels cell shows `bug, ui`. A task with no labels shows `none`, as today. | CP-196 |
| Saved data in which one task carries `""` | The start reports the data unreadable, names its location and does not start. Nothing loads, and the bytes are unchanged. | CP-197, CP-205 |
| Saved data in which one task carries a 201-code-point label | Same as the row above. | CP-197, CP-205 |
| Saved data in which one task carries `["bug", "bug"]` | Same as the row above. | CP-197, CP-205 |
| Saved data in which task 1 carries `bug` and task 2 carries `bug` | Loads. | CP-197 |
| Saved data in which a task carries `["   "]` or one 200-code-point label | Loads. | CP-197 |
| A label is added, then the tracker is restarted | The saved task has the same keys as before the change, and its `labels` list holds the added label. | CP-198 |
| A label is added to a task whose priority is `high` | The task's title, priority, assignee and due date are unchanged. The edit form behaves as before. | CP-199 |
| The suite runs after the change | `domain/labels.py` exists, its docstring names FR-23, FR-40, the taking-part modules and the tests, and `labels` is listed as landed. The pointer test passes. | CP-200 |
| A refused label action of each kind | Each has its own refusal type from `domain`, mapped to its reason by type in `web`. | CP-201 |
| The suite runs after the change | The unit, layer-3/4, start, route, audit-hook and recording-saver tests named in CP-202 to CP-206 are present and pass. | CP-202 to CP-206 |
| The end-to-end suite runs | The focus test and the `<`, `&`, `"` test pass. | CP-207 |
| `python3 tests/timed_run.py` at 1,000 tasks | Lists a label add and a label remove, each under 1 second, and exits 0. | CP-208 |
| The four existing tests named in CP-209 after the change | Each asserts the new label state and keeps its other assertions. No other existing test changed to fit. | CP-209 |
| The gates of CP-210, on a `git init`-ed `git archive HEAD` copy | Each exits 0. | CP-210 |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| Today a start loads saved data whose task carries an empty label, a 201-character label or a repeated label (CP-197's present defect). | `domain/tasks.py:259-292` read: `restore_task` checks title, status, priority and assignee, and its docstring reads "label and comment content carries no rule here". Then, in a disposable copy (`git archive HEAD products/tracker17`, HEAD `41af4dbab`), a probe wrote saved data through the suite's own `_write` / `_full_document` / `_task_entry` helpers and called `SavedData(...).load()` on each case. The conditions are the real reader on a real file. | `empty LOADS [0]`, `over200 LOADS [201]`, `repeated LOADS [3, 3]`, `spaces LOADS [3]`, `exactly200 LOADS [200]`. |
| `tests/integration/test_saved_data.py::test_historical_assignee_and_structural_label_comment_values_load` asserts today that labels `["", "x", "x"]` load (CP-209). | Lines 834-846 read; the test was run with `pytest -q` in the same copy. | `1 passed`. Its docstring reads "no label or comment content rule exists yet". |
| `_state_holding_every_field` builds a task carrying a repeated label (CP-209). | `tests/integration/test_saved_data.py:567-575` read. | `labels=["bug", "ui", "bug"]` at line 571. |
| Adding `domain/labels.py` fails three existing architecture tests until they change (CP-200, CP-209). | In the disposable copy, `pytest tests/architecture/` ran with the probe file `domain/labels.py` holding only a docstring. It also ran without the file. | Without the file: `test_trace.py` 22 passed. With the file: `3 failed, 49 passed`. The three were `test_shapes.py::test_only_the_task_features_are_added_to_domain`, `test_trace.py::test_each_feature_word_with_its_domain_module_is_listed_as_landed` and `test_trace.py::test_no_labels_module_or_excluded_feature_entry_exists`. |
| The pointer test's landed list lacks `labels` (CP-200). | `tests/architecture/test_trace.py:24` read. | `LANDED_FEATURE_WORDS = ["projects", "assignees", "tasks", "priorities", "due_dates"]`. |
| A project's list row already shows a task's labels (CP-196). | `web/pages.py:438-456` read. | The labels are joined with `", "`, or `"none"` when there are none, escaped, in the `Labels` column of `_TASK_COLUMNS`. |
| The task's page has no label area today (CP-182). | `web/pages.py:659-695` read. | `task_page` builds the heading, an optional completion line, the project fact and the edit form, and no labels. |
| An edit for a task that does not exist is answered with the task not-found page (CP-194 follows it). | `web/routes.py:410-413` read. | `_edit_task` returns `pages.task_not_found_page()` with `HTTPStatus.NOT_FOUND`. |
| The QC-35 outbound-connection test lists the actions it drives by hand (CP-206). | `tests/integration/test_routes.py:406-427` read. | It sends each request explicitly: project create, assignee add and remove, task add, task edit and pages. No label action exists yet. |
| The project's highest rule identifier is CP-181 (numbering starts at CP-182). | `grep -rhoE "CP-[0-9]+"` over `system/projects/tracker17/journey/tobiishi/trail` and the product tree, sorted. | `CP-181` is the highest. |

No rule pins output that renders a language-level fact. Every pinned output is text the product chooses, so no language-rendering row is owed.

---

## Out of Scope

- The filter that narrows a list by label, and the label filter's offered values. These belong to `tracker17 · nemawashi · 2026-10-11_narrow-and-sort`.
- Status moves, deleting a task, a project summary, sort controls and comments, including the saved-comment start check. Comment content stays without a rule, as `test_historical_assignee_and_structural_label_comment_values_load` keeps asserting.
- Renaming or editing a label in place, and adding or removing several labels in one action (FDR R-63: one at a time).
- A sentence beside the label field stating its maximum (UXD UX-F2, UX-F7: only the description and comment fields state one).
- Any change to how the list row's Labels cell renders (CP-196).
- Any change to the saved form of a task or of the People list (CP-198).
- The wording of the label area's lines. The content stage writes it to `CONTENT.md`'s rules (CP-184).
- Pages served while the saved data is unreadable (FDR R-25, R-26). The product has none today for any unreadable data: the start returns before a listener exists (`main.py:39-48`), and `test_an_unreadable_start_writes_exactly_the_one_line_with_the_closing_sentence` (`tests/integration/test_start.py:83-95`) holds that. A label break joins the same refusal. The gap between those FDR lines and the product is the product's, not this change's (Gap 17).

---

## Locked Answers (the divergence record — self-review 2026-10-12)

- **Gap 1, the typed text after an over-long refusal (a):** CP-191 holds none of the sent text, where the request says both refusals keep "the typed text". *Because* FDR PD-11 reads "After a refusal for an over-long value, the page gives the reason and not the typed text". SDD § 4 RT-8 and ADR-0006 say the same, and RT-8 adds that "No form of the tracker's own can reach that refusal", so keeping typed text holds on every form the operator uses. The empty-label refusal keeps what was typed (CP-190). Both refusals still change nothing and show the reason at the label field, which is the request's intent. The departure follows the locked FDR decision, so it is not a scope change.
- **Gap 2, what a repeated add shows (b):** no save, no completion line, no refusal (CP-189). *Because* UXD UX-I4 shows a result only once it is saved, NFDR QC-21 saves nothing for an outcome reporting no change, and SDD RN-45 (`SDD.md` § SDD Review Notes) names "FDR R-65's label already carried" as an action reporting none. The request's "leaves the task as saved" fixes the data, and the record fixes the page.
- **Gap 3, removing a label the task does not carry (b):** refused (CP-193). The request is silent on this, and FDR R-66 states it. The page opens at the label area. *Because* SDD § 4 EX-4 opens a refused page at the control used, and that label's Remove button is no longer on a fresh page. The label area is where the control stood. This choice is reversible and is confined to where focus lands.
- **Gap 4, where a removal's page opens (b):** CP-192 follows SDD § 4 EX-5's case for a thing no longer on the page. The request says only "leaves the others".
- **Gap 5, an action on a missing task (b):** CP-194 answers with the task not-found page. *Because* UXD UX-S6 says "A task that no longer exists shows UX-S10", and the edit already answers that way (Verified Claims).
- **Gap 6, label order (b):** labels show in the order they were added (CP-182, CP-187, CP-196). The request is silent on order. This is the order the operator produced, and a test can see it on the page.
- **Gap 7, the keyboard and the Remove button's accessible name (b):** CP-195 and CP-185. The request is silent on both. SDD § 4 EX-8 and EX-9, and `CONTENT.md` § Accessibility of text, bind every control.
- **Gap 8, the pointer test and the entry docstring (e):** CP-200 lists `labels` as landed and fixes the docstring's content. The request names only the module. Both are required by SDD § 4 TS-3 and TS-4 and NFDR QC-11, and the Verified Claims probe shows the suite failing without the listing.
- **Gap 9, the field's `maxlength` (e):** CP-186 and CP-203. The request is silent. NFDR QC-9, SDD § 4 RT-10 and ADR-0007 say "A slice that adds a text field must write its `maxlength` and test a longer value".
- **Gap 10, one test per refusal (e):** CP-203 adds the remove-not-carried and missing-task refusals to the two the request names. *Because* SRS AC-12 asks for tests "one per refusal" and NFDR QC-5 and QC-38 verify through them.
- **Gap 11, a repeated add saves nothing, tested (e):** CP-204, from NFDR QC-21.
- **Gap 12, the route, audit-hook and recording-saver tests (e):** CP-206, from NFDR QC-7, QC-35 and QC-54. Each states its check over every route or action, and QC-35's test lists its actions by hand (Verified Claims).
- **Gap 13, the completion line in the focus test (e):** CP-207 also asserts the completion line as the accessible description. The request names focus only. *Because* SDD § 6 S-2 *Command* states "keyboard focus on the added name or label and the completion line as its accessible description".
- **Gap 14, timing the remove (e):** CP-208 times a label remove beside the add the request names. *Because* NFDR QC-48 covers "every action SRS NFR-1 lists", and NFR-1 reads "every operator action". SRS FR-16 makes the labels an editable field, so a remove is an edit just as an add is.
- **Gap 15, Ruff and mypy (e):** CP-210 adds NFDR QC-62's three commands. NFDR § 10 gates them at the suite.
- **Gap 16, the existing tests that change (reconciling the request's "no existing test is weakened"):** CP-209 names the four. Each asserts the pre-change state that the request itself reverses: no `domain/labels.py`, and label content without a rule. Replacing those label assertions carries out the request's own rule. Every other assertion in them stays, the off-list assignee and comment-content loads among them.
- **Gap 17, unreadable-data pages (owner's answer to the design halt, 2026-10-12):** CP-197 keeps the start refusal the product already makes and no longer requires every page to say the saved data could not be read. *Because* FDR R-25 and R-26 describe a mode the product has never had for any unreadable data (`main.py:39-48`), the request asks only for an unreadable start with nothing loaded, and building that mode would change the protected start test CP-209 does not list. The design halt (`d22ab398d`) put the choice to the owner, who chose to keep the refusal. The R-25/R-26 gap is handed on through Out of Scope for `shukuba-refine` to place.
