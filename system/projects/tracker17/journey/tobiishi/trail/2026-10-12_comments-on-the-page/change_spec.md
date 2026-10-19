# Change Spec — Comments on a task's page

**Date:** 2026-10-12
**Category:** feature
**Behaviour:** changing
**Request:** Let the operator write comments on a task and read them on the task's page. The page lists the task's comments oldest first, each with its author and the time it was written in the machine's local time, and shows a form below the newest comment with a sentence beside the text field naming the most characters a comment holds, the same number as the field's `maxlength` (SDD § 6 S-3; UXD UX-F7, UX-F8). Adding a comment saves it under the saved operator name, and after Add the page opens with the new comment in view and keyboard focus on it. After the name is changed on People, earlier comments keep the name they were written under and a new one carries the new name. With no name set, a notice above the form says a name is needed and links to People; a comment with no name set, and a blank comment (empty or whitespace only), are each refused with the reason shown, nothing saved and the typed text kept in the field. No control edits or deletes a comment. The Comment entity is part of the saved data as SDD § 3 states it, and saved data holding a comment that breaks a comment rule is reported unreadable at start (SDD § 4 SD-5), not repaired or dropped. `domain/comments.py` is the Comments feature's entry point (SDD § 4 TS-3): the comment rules live in the domain and the add action in the application part, not the web part. Every string comes from the product's content record, none invented in code. Tests ship with it: unit tests for the comment rules; integration tests through the real server that a task's page lists comments oldest first with author and local time and shows the form below the newest with the maximum-length sentence equal to the field's `maxlength`; that adding a comment saves it under the saved name and shows it, read back from the saved data; that after a rename earlier comments keep the earlier name and a new one the new name; that with no name set the notice and the People link show and a comment is refused, and that a blank comment (empty and whitespace only) is refused, each with nothing saved and the typed text kept; that no edit or delete control for a comment is in the built page, on a page that has comments; and a start-check test, in `tests/integration/test_saved_data.py` or beside it, that saved data holding a comment that breaks a comment rule is reported unreadable at start and that data saved before this change still loads with its projects, tasks, people and name. End-to-end tests in `tests/e2e/` add a comment to a task whose comments fill more than the window and find the new comment in view with keyboard focus on it, and fill a comment to its maximum with line breaks and find it saved whole (SRS AC-20). `pytest products/tracker17/tests/` exits 0, run in a fresh clone checked out at the commit under test (`core/roles/CROSS_ROLE.md` § *Every seat*). **Must not be weakened or added:** the timed run is not extended: `tests/timed_run.py` and its test stay byte-identical. No existing People or task-page test is deleted, skipped or loosened, and the operator-name behaviour is unchanged. No threaded replies, no deleting a comment with its task, and no wording change outside the comment text the content record names. The saved-data shape changes only as SDD § 3's Comment entity states. **Left to later stations:** the 1,000 × 20 timed run and the assignee timing (`tracker17 · nemawashi · 2026-10-07_comment-on-a-task`, item 3 `full-volume-run`); deleting a task with its comments (`tracker17 · nemawashi · 2026-10-11_delete-and-rename`); the unreadable-data pages (`tracker17 · nemawashi · 2026-10-11_protect-saved-data`).
**Language resolution:** Python — step 1, `project.md` `Languages:` — `core/doctrine/engineering/languages/python/README.md` opened, and every concern it routes read (`toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `testing_python.md`)

---

## Change Summary

The operator can write a comment on a task and read the task's comments on its page, each under the name it was written with and the time it was written. Comments are saved with the task, and a start refuses saved data holding a comment that breaks a comment rule. Until now a task's page shows nothing about comments, no action adds one, and the saved data carries comments with no rule over their content.

Paths below are relative to the product root, which `system/projects/tracker17/project.md` `Product path:` names. `SRS`, `SDD`, `UXD`, `FDR`, `NFDR`, `DESIGN.md` and `CONTENT.md` are the product's documents under `docs/`. The versions cited are SRS 6, SDD 10, UXD 6, NFDR 12, FDR 4, DESIGN 3 and CONTENT 10.

---

## Rules

### The comments area on a task's page

- **CP-240:** A task's page gains a Comments area below the task's fields and its labels. It holds a heading, then the task's comments, then the add-comment form below the newest comment. The form has a multi-line text field with a visible label, and an Add button. *(UXD UX-F7, UX-S6; FDR R-73; SDD § 4 EX-9; DESIGN.md § Components, the comment textarea)*
- **CP-241:** The comments show as one flat list, oldest first, realized as the order they were added: a comment added later shows below every comment added before it, whatever times they show. Each comment shows its author, the time it was written, and its text. No comment is shown as a reply to another. *(SRS FR-29; FDR R-73; OOS-7)*
- **CP-242:** A comment's time is the moment it was written, shown in the machine's local time as `YYYY-MM-DD HH:MM`, on a 24-hour clock, with no seconds, no AM or PM, no time zone and no relative word such as "today" or "ago". A comment written at `2026-10-12T12:32:00Z` on a machine whose local time is two hours ahead of UTC shows `2026-10-12 14:32`. *(SRS NFR-14; FDR R-73; `CONTENT.md` § Grammar and mechanics, Dates and times)*
- **CP-243:** A comment's text and author show exactly as saved, as text. A line break in the text shows as a line break, surrounding spaces are kept, and `<`, `&` and `"` show as typed and change nothing around them. *(FDR R-80, R-112; SDD § 4 SEC-4; DESIGN.md § Typography, "A comment keeps the line breaks the operator typed"; NFDR QC-36)*
- **CP-244:** A task with no comments shows, in the Comments area, a line saying there are none yet, with the form in view. *(UXD UX-S6, the no-comments state; FDR R-95; `CONTENT.md` § Empty, the UX-S6 row)*
- **CP-245:** The comment field's `maxlength` is the long-text maximum, 4,000 characters, written from the one place in `domain` that states it. A sentence beside the field states the most characters a comment can hold, and the number it states is that same value, so it equals the field's `maxlength`. *(UXD UX-F7; SDD § 4 RT-10; ADR-0007; NFDR QC-9)*
- **CP-246:** When no operator name is saved, a notice above the add-comment form says a name is needed to comment, and links to People. When a name is saved, the page shows no such notice. The form is shown in both cases. *(UXD UX-F7, the decision point; UX-S6, the no-name state; SDD § 6 S-3 *Behaviour*)*
- **CP-247:** No control on any page edits or deletes a comment: no button, link or form acts on a comment already written, on a page that has comments. *(SRS FR-29; FDR R-74)*
- **CP-248:** Every word the Comments area, the notice, the form, its refusals, its failure line and its completion line show follows `docs/CONTENT.md` (SDD § 4 EX-11). Text on a task is a "comment", never a note, reply, message or remark, and the form's button reads `Add` (`CONTENT.md` § Terminology, the "Text on a task" and "Putting something into a thing that holds it" rows). This spec fixes what each line must say, and the content stage writes the wording.

### Adding a comment

- **CP-249:** Pressing Add with text that is not blank (CP-256) and is at most 4,000 code points, while an operator name is saved, saves one comment on that task. The comment holds the text exactly as typed, changed only by SDD § 4 RT-10's line-break normalization; as its author, the operator name saved at the moment the add is applied; and as its written time, that moment. The task's other fields, its labels and its earlier comments, every other task and project, the assignee list and the operator name are unchanged. *(SRS FR-28, DR-3; FDR R-71, R-72, R-80, R-102; SDD § 4 SD-2)*
- **CP-250:** After a comment is added, the browser is sent to the task's page. The new comment is last in the list. The page opens with the new comment in view and keyboard focus on it, and one completion line naming what changed is the focused element's accessible description. The completion line itself does not take focus. A reload of that page, or a return to it through back or forward, adds nothing again. *(UXD UX-I4; SDD § 4 EX-5, EX-14, RT-8, RT-9; FDR R-106)*
- **CP-251:** The author is the name saved when the add is applied, not the name saved when the page loaded. A page loaded while `Sam` was saved, after the name changed to `Lee` in another tab, adds a comment by `Lee`. A page loaded with no name saved, which shows the CP-246 notice, adds a comment when a name has been saved in another tab since. *(FDR R-72, R-102; SRS NFR-3)*
- **CP-252:** After the operator name changes on People, every comment already written still shows the name it was written under, and a comment added after the change shows the new name. *(SRS FR-30; FDR R-72)*
- **CP-253:** A comment can be added to a task in any status, `done` and `cancelled` included. *(FDR R-75)*
- **CP-254:** A comment's length is its number of Unicode code points on the value as saved, spaces included, with a line break counting one. A comment of exactly 4,000 code points is accepted and saved whole, one holding line breaks and one holding a character outside the Basic Multilingual Plane included, and it is never shortened. *(FDR R-76, R-77, R-79; SRS FR-40, AC-20; ADR-0007)*

### Refusals and failures

- **CP-255:** A comment added while no operator name is saved is refused, and nothing is saved. The task's page opens at the comment field: keyboard focus is in the field, the reason is beside it as the field's accessible description, and the field holds what was typed. The reason says a name is needed and names what to do: set it on the People page. *(SRS FR-28, FR-39; FDR R-71, R-100; UXD UX-F7, UX-I3; SDD § 4 EX-4, EX-14)*
- **CP-256:** A blank comment is refused, and nothing is saved. A comment is blank when it is empty, or when every character in it is whitespace. Whitespace is the same set of characters the product already treats as blank in a project name, an assignee name and the operator name, line breaks included: the space, the tab, a line break, U+00A0 and U+3000 are in that set, and U+200B is not (Verified Claims). The page opens as CP-255 describes, with this rule's reason beside the field and the field holding what was typed, line breaks included. *(SRS FR-28, FR-39; FDR R-71, R-100; UXD UX-I3; SDD § 4 EX-4, EX-14)*
- **CP-257:** A comment longer than 4,000 code points is refused, and nothing is saved. Only a request that no page of the tracker sends can carry one, because CP-245's field stops at 4,000. The page that answers opens at the comment field with the reason beside it, and holds none of the text that was sent. *(SRS FR-39, FR-40; FDR R-78, PD-11; SDD § 4 RT-8, RT-10; ADR-0006, ADR-0007)*
- **CP-258:** When a comment breaks more than one rule, exactly one reason shows, chosen in this order: too long, then blank, then no name saved. 4,001 spaces with no name saved get the too-long reason, and an empty comment with no name saved gets the blank reason.
- **CP-259:** An add naming a task that the tracker does not hold changes nothing, whatever its text and whether a name is saved, and is answered with the page for a task address with nothing at it, as an add of a label to such a task is today (Verified Claims). *(FDR R-103, R-105; UXD UX-S10; SDD § 4 EX-13)*
- **CP-260:** When an add fails for a reason that is not a refusal, the saved data and the task's comments stay as they were. The task's page says in plain words that the comment was not added and that nothing was changed, and shows no error text from Python. The field still holds what was typed, and keyboard focus is on Add with the failure line as its accessible description. The console shows a message naming the action, then the error. *(FDR R-18, R-107, R-108; UXD UX-I5; SDD § 4 OB-3, EX-4; NFDR QC-49, QC-56, QC-57)*
- **CP-261:** An add that does not come from the tracker's own pages is refused and changes nothing, under the check every submission passes today: one marked `cross-site` or `same-site`, and one not marked `same-origin`, a submission with no mark included. *(FDR R-110; SDD § 4 SEC-2; NFDR QC-32)*
- **CP-262:** Adding a comment can be done from the keyboard alone, with the browser's own keys. *(FDR R-113, Key Use Case 5; SDD § 4 EX-8; UXD UX-I6)*

### Saved data

- **CP-263:** A comment is part of the saved data, held with its task as its text, its author and its written instant. The saved data gains nothing else: a comment carries no field beyond those three, and the task, the state and the counters keep the saved form they have today. After a stop and a start, the task's page shows the same comments with the same text, author, time and order. *(SRS DR-3, FR-5, NFR-6, AC-6, AC-17; SDD § 3 Comment; FDR R-15, R-29; NFDR QC-46; Request, "The saved-data shape changes only as SDD § 3's Comment entity states")*
- **CP-264:** At start, saved data is unreadable when a saved comment's text is blank (CP-256's set) or longer than 4,000 code points, or its author is blank (the same set) or longer than 200 code points, as well as in every case it is unreadable today. In each case:
  - the console says the data is unreadable and names its location;
  - the start refuses as it does today for any other unreadable data: the tracker does not start and exits non-zero (`main.py:39-48`);
  - nothing of the data is loaded;
  - the saved data's bytes are unchanged.

  Saved data loads when a comment's text is 4,000 code points or its author 200, when an author differs from the saved operator name, and when comments are saved with no operator name. *(SRS DR-6; FDR R-21, R-22, R-23, R-24, R-27, R-76; SDD § 4 SD-4, SD-5; NFDR QC-22, QC-37, QC-51)*
- **CP-265:** Saved data written before this change, in each form the tracker reads today, loads. It keeps its projects, its tasks with their labels, its assignee list and its operator name or the absence of one, and loading it writes nothing. *(Request; FDR R-15, R-23; Verified Claims, the four forms read today)*

### Where the code lives (fixed by the records)

- **CP-266:** The comment rules — blank text, too long, no name saved, and the start checks of CP-264 — live in `domain`, whose entry module for the Comments feature is `domain/comments.py`. The add is applied in `application`, and `web` holds no comment rule (SDD § 3 parts table; SDD § 4 TS-3; NFDR QC-20, QC-21, QC-23, QC-38). Each refusal reaches `web` as a refusal type from `domain`, handed on through `application`, and `web` maps it to its reason by type, never by reading a message (SDD § 4 OB-4; NFDR QC-5, QC-16). `domain` holds no wording shown to the operator (NFDR QC-20). The module's opening docstring names the SRS requirements it realizes, every `application` and `web` module that takes part, and the test modules that check it; every test module the change adds names the requirements or acceptance criteria it checks; and `comments` is listed as landed in the pointer test (SDD § 4 TS-3, TS-4; NFDR QC-11).

### Tests (named in the request, or required by the records)

- **CP-267:** Unit tests cover the comment rules in `domain`, with no file and no clock: an empty comment, a spaces-only one, one of other whitespace only (a tab, line breaks, U+00A0), 4,000 code points accepted with line breaks and a character outside the Basic Multilingual Plane, 4,001 refused, 4,001 spaces getting the too-long refusal, no name saved refused, the CP-258 order, the author being the saved name and the written time the instant handed in, a new comment placed after the task's existing ones, and the restore checks of CP-264. *(Request; SDD § 4 TS-1)*
- **CP-268:** Layer-3 and layer-4 tests run `web` with `application` in one process, with the clock and the saver handed in (SDD § 4 TS-1). They cover:
  - a task's page listing its comments oldest first, each with its author and its time in local time, with the form below the newest (CP-240 to CP-242);
  - the add-comment form, finding the number its sentence states equal to the field's `maxlength` (CP-245; NFDR QC-9);
  - the no-comments state, the no-name notice with its link to People, and no notice once a name is saved (CP-244, CP-246);
  - an add saving the comment under the saved name and showing it, read back from a real `SavedData` (CP-249, CP-250);
  - a rename, after which earlier comments keep the earlier name and a new one carries the new name (CP-252);
  - a comment added to a task in `done` (CP-253);
  - one test per refusal, each asserting the reason shown and the saved data unchanged: no name saved, and a blank comment both empty and whitespace only, each with the typed text kept; the over-long comment, sent in a request no page sends, with none of the sent text on the page; and the add naming a task the tracker does not hold (CP-255 to CP-259);
  - a failed add (CP-260);
  - no control acting on a written comment, on a page that has comments (CP-247).

  *(Request; SRS AC-12, AC-18; NFDR QC-5, QC-9, QC-38, QC-56)*
- **CP-269:** A test runs SRS AC-6's sequence through the tracker's actions — a project, a task with every field set, an assignee, a label, the operator's own name and a comment — then starts again on the same real saved data, and finds all of them unchanged. The same test finds nothing in the saved file outside what SRS DR-1 to DR-5 describe and the two identity counters. *(SDD § 6 S-3 *Command*, "SRS AC-6 with every field it lists"; SRS AC-6, AC-17; NFDR QC-46)*
- **CP-270:** Start tests, in `tests/integration/test_saved_data.py` or beside it, write saved data with a comment whose text is empty, whitespace only, or 4,001 code points, and one whose author is empty, whitespace only, or 201 code points, one case per test. Each finds the start reporting the data unreadable, loading none of it, and leaving its bytes unchanged. Further start tests load each form of saved data the tracker reads today and find its projects, tasks, labels, assignees and operator name kept, and load the readable cases CP-264 names. *(Request; SRS AC-7; SDD § 4 SD-5; NFDR QC-22, QC-37, QC-51)*
- **CP-271:** Three existing tests cover the new action:
  - the route test of NFDR QC-7 covers the submission this change adds;
  - the outbound-connection test of NFDR QC-35, which drives actions through `web` under the audit hook, drives a comment add;
  - a recording-saver test under NFDR QC-54 runs a comment add and finds that the saver received only saves.

  *(NFDR QC-7, QC-8, QC-33, QC-34, QC-35, QC-54)*
- **CP-272:** End-to-end tests in `tests/e2e/` drive Chromium against a tracker started by `main`:
  - one adds a comment to a task whose comments fill more than the window, and finds the new comment in view with keyboard focus on it (Request; SDD § 4 EX-5, RT-9; ADR-0003, *Dependence*);
  - one fills a comment to its maximum with line breaks in it, adds it, and finds it saved whole, neither refused nor shortened (Request; SRS AC-20);
  - one adds a comment holding `<`, `&` and `"` and finds the page showing it as typed (NFDR QC-36; SDD § 11 R-3; FDR R-112).
- **CP-273:** `python3 tests/timed_run.py`, run from the product root at the volume it builds today (1,000 tasks with 20 comments each), times a comment add at an ordinary length it states, and that add's landing page. Each shows its result within 1 second. The add is sent marked `same-origin`, and the run fails when the add is refused or fails, or when the landing is not the task's page showing the added comment. The run exits 0. *(SRS NFR-1, "adding a comment", AC-15; NFDR QC-48, QC-32; SDD § 4 TS-5)*
- **CP-274:** Existing tests that assert the state this change reverses change only in what they assert about comments, and each keeps every other assertion. None is deleted or skipped:
  - `tests/architecture/test_shapes.py::test_only_the_task_features_are_added_to_domain`: `comments` moves from the words that must have no module (line 182) to the landed ones (line 180). `workflow`, `filtering`, `sorting` and `summary` stay forbidden, and the state's fields stay the six of line 185;
  - `tests/architecture/test_trace.py`: `LANDED_FEATURE_WORDS` (line 24) gains `comments`, which `test_each_feature_word_with_its_domain_module_is_listed_as_landed` and `test_no_excluded_feature_entry_exists` then pass on (CP-266);
  - `tests/integration/test_routes.py`: `SAMPLE_ADDRESS` (line 265) gains a sample address for the add-comment submission, so line 293's route set still equals it;
  - `tests/integration/test_saved_data.py`: in `_state_holding_every_field` (line 566) the second comment's author changes from `""` to a non-blank name, which six tests use (lines 595, 913, 1062, 1085, 1142, 1160), each keeping every assertion. `test_historical_assignee_and_structural_label_comment_values_load` (line 838) keeps its off-list assignee and its labels, and its two comments become comments that keep CP-264's rules; the blank-text and blank-author cases it loaded move to CP-270's unreadable start tests;
  - `tests/unit/test_tasks.py::test_restore_task_checks_saved_label_rules`: line 804, which restores a comment with empty text and author, asserts that comment refused instead. Every label assertion stays;
  - `tests/integration/test_task_pages.py`: the lists of the forms on a task's page (lines 310 to 313, and 413 to 416) gain the add-comment form after the label form. The absence list at line 318 drops `"comment"` and keeps `"status"`, `"todo"`, `"overdue"` and `"delete"`. The no-link assertions at lines 320 and 447 admit exactly one link in the task's main area, the CP-246 notice's link to People, when no operator name is saved, and none when one is. Every assertion about the edit form, the labels, the facts list and the absence of scripts and tables stays.

  The probe in Verified Claims found these 14 tests failing, and the further task-page lines named above behind them, and no other test in `pytest tests/ --ignore=tests/e2e`. *(Request, "No existing People or task-page test is deleted, skipped or loosened"; SDD § 4 TS-4, SD-5)*
- **CP-275:** Two sets of commands exit 0:
  - `pytest products/tracker17/tests/`, which collects the end-to-end tests under `tests/e2e/` as well (`pyproject.toml` `testpaths = ["tests"]`), run in a fresh clone of the repository checked out at the commit under test (Request; `core/roles/CROSS_ROLE.md` § *Every seat*; NFDR QC-47);
  - from the product root, `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web` (NFDR QC-62).

---

## Examples

| Scenario | Expected behavior | Rule |
|---|---|---|
| A task with no comments, `Sam` saved; its page is opened | Below the fields and labels, the Comments area says there are none yet, with the labelled multi-line field, the maximum sentence and Add in view. No no-name notice. | CP-240, CP-244, CP-246 |
| A task with comments by `Sam` at 09:05 and `Lee` at 09:40, added in that order | `Sam`'s comment, then `Lee`'s, each with author, time and text, then the form. | CP-240, CP-241 |
| Two comments added in that order, the second showing an earlier time than the first (the machine's clock moved back between them) | The first-added still shows first. | CP-241 |
| A comment written at `2026-10-12T12:32:00Z`, machine local time UTC+2 | Shows `2026-10-12 14:32`. | CP-242 |
| A saved comment `line one⏎line two`, with surrounding spaces | Shows on two lines, spaces kept. | CP-243 |
| A comment `<b>A&B</b> "x"` | Shown as typed. Nothing on the page changes. | CP-243 |
| The add-comment form is built | `maxlength` is 4000, and the sentence beside the field states 4,000 or 4000 characters, the number equal to `maxlength`. | CP-245 |
| No name saved; a task's page is opened | A notice above the form says a name is needed and links to People. The form is shown. | CP-246 |
| A task's page with three comments | No control edits or deletes any of them. | CP-247 |
| The area's words | "comment", `Add`, and lines that follow `CONTENT.md`. | CP-248 |
| `Sam` saved; the operator types `Looks good` and presses Add | Saved as `Looks good`, by `Sam`, at the moment of the add. The task's fields, labels and earlier comments are unchanged. | CP-249 |
| After that add | The task's page, with `Looks good` last, in view and focused, described by one completion line. Reloading adds nothing. | CP-250 |
| Page loaded with `Sam` saved; another tab renames to `Lee`; this page adds a comment | The comment's author is `Lee`. | CP-251 |
| Page loaded with no name (notice shown); another tab saves `Sam`; this page adds `Hi` | Accepted, by `Sam`. | CP-251 |
| Comments written as `Sam`; the name changes to `Lee`; a new comment is added | Earlier comments show `Sam`, the new one `Lee`. | CP-252 |
| A task restored from saved data in `done`; a comment is added | Accepted. | CP-253 |
| A comment of 4,000 code points with line breaks and one `😀` | Saved whole. Not refused, not shortened. | CP-254 |
| No name saved; the operator types `Hi` and presses Add | Refused. Nothing saved. Focus in the field holding `Hi`, the reason beside it saying a name is needed and to set it on People. | CP-255 |
| `Sam` saved; the operator submits an empty comment, then `   ⏎ ` | Each refused as blank. Nothing saved. The field holds what was typed. | CP-256 |
| A comment of only a tab, or U+00A0 | Refused as blank. | CP-256 |
| A comment of only U+200B | Accepted, as it would be for a project, assignee or operator name. | CP-256 |
| A request with no page behind it sends 4,001 code points | Refused. Nothing saved. The page gives the reason at the field and holds none of the sent text. | CP-257 |
| No name saved; 4,001 spaces sent | The too-long reason only. | CP-258 |
| No name saved; an empty comment submitted | The blank reason only. | CP-258 |
| An add naming a task identity the tracker does not hold | Nothing changes. The task not-found page answers. | CP-259 |
| The save fails while adding `Hi` | The page says the comment wasn't added and nothing changed. `Hi` is still in the field, focus is on Add, and the console names the action and the error. | CP-260 |
| An add marked `Sec-Fetch-Site: cross-site` | Refused. Nothing changes. | CP-261 |
| The operator tabs to the comment field, types, tabs to Add and presses Enter | The comment is added with no pointer used. | CP-262 |
| A comment added; stop; start | The task's page shows it with the same text, author, time and place. The saved comment holds text, author and written instant and nothing else. | CP-263 |
| Saved data with a comment whose text is `""`, `"   "` or 4,001 code points, or whose author is `""`, `"  "` or 201 code points | The start reports the data unreadable, names its location and does not start. Nothing loads, and the bytes are unchanged. | CP-264 |
| Saved data with a 4,000-code-point comment, a 200-code-point author, an author other than the saved name, or comments and no saved name | Loads. | CP-264 |
| A start on data saved before this change, in any of the four forms read today | Loads, keeping projects, tasks, labels, assignees and the name or its absence. The file's bytes are unchanged by the load. | CP-265 |
| A refused or added comment of each kind | Each refusal comes from `domain` as a type, through `application`, mapped by type in `web`. `domain/comments.py` names its requirements, participants and tests, and `comments` is listed as landed. | CP-266 |
| The unit suite runs | The CP-267 cases are present and pass. | CP-267 |
| The layer-3/4 suite runs | The CP-268 cases are present and pass. | CP-268 |
| AC-6's sequence, then a restart on the same saved data | Everything entered is unchanged, and the saved file holds no key outside DR-1 to DR-5 and the two counters. | CP-269 |
| The start tests run | Each CP-270 case is unreadable with bytes unchanged, and each earlier form and readable case loads. | CP-270 |
| The route, audit-hook and recording-saver tests run | Each covers the comment add. | CP-271 |
| The end-to-end suite runs | The in-view-with-focus, full-length and `<`, `&`, `"` tests pass. | CP-272 |
| `python3 tests/timed_run.py` | Lists a comment add and its landing at 1,000 tasks of 20 comments, each under 1 second, and exits 0. | CP-273 |
| The existing tests named in CP-274 after the change | Each changes only as CP-274 states and keeps every other assertion. | CP-274 |
| The commands of CP-275, in a fresh clone at the commit under test | Each exits 0. | CP-275 |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| The saved data already carries comments, as text, author and an instant, with no rule over their content (Change Summary, CP-263, CP-264). | `persistence/saved_data.py:46`, `:144-151`, `:219-231` and `domain/tasks.py:66-72`, `:331-332` read. | `COMMENT_KEYS = {"text", "author", "created_at"}`; `_decode_comment` checks only shape and types; `Comment` is "Carried as a structural value; no rule over its content yet", and `restore_task` says "Comment content carries no rule here." |
| No action adds a comment today, so no data the tracker saved holds one (CP-265). | `grep -n -i comment application/tracker.py` (no match); `tests/integration/test_saved_data.py:616-624` read. | `application/tracker.py` names no comment. The test asserts "nothing adds a label or a comment yet". |
| A task's page shows nothing about comments today (Change Summary). | `web/pages.py:893-902` read. | The body is the title, the Project fact, the edit form and the label section. |
| The tracker reads four forms of saved data today (CP-265, CP-270). | `persistence/saved_data.py:28-32` read. | `SUPPORTED_STATE_KEYS = (LEGACY_STATE_KEYS, PEOPLE_STATE_KEYS, TASK_STATE_KEYS, STATE_KEYS)`. |
| The blank test the product applies to names is one whitespace set (CP-256). | `grep -n isspace domain/*.py`; then `python3 -c` printing `str.isspace` for `' '`, `'\t'`, `'\n'`, U+00A0, U+3000 and U+200B. | `domain/projects.py:44`, `domain/assignees.py:43` and `domain/operator_name.py:47` use the one test `all(character.isspace() for character in name)`. It printed `[True, True, True, True, True, False]`. |
| An add of a label to a task the tracker does not hold changes nothing and lands on that task's address, which answers with the task not-found page (CP-259). | `web/routes.py:507-508` and `:263-265` read. | `except TaskNotFound: return self._redirect(address)`; `_task_page` returns `task_not_found_page()` with 404 when no task matches. |
| No action deletes a task or a project (Out of Scope). | `web/routes.py:87-101` read. | `ROUTES` holds no delete route. |
| A start on unreadable data writes one line and returns 1 (CP-264). | `main.py:39-48` read. | On `UnreadableData` it prints the location message to stderr and returns `1` before any listener exists. |
| The timed run already builds 1,000 tasks with 20 comments each, and times no comment add (CP-273). | `tests/timed_run.py:61-62`, `:156-167`, `:525-555` read. | `TASK_VOLUME = 1000`, `COMMENTS_PER_TASK = 20`; `main` times creates, the task add, the edit, the label add and remove, and the name save. |
| The timed run's seeded comments keep CP-264's rules, so the run still loads its fixture (CP-273). | In the probe copy below, `python3 tests/timed_run.py > out.txt; echo $?`, with the probe's comment rules in `restore_task`. | `exit=0`; no line reports "refused or failed" or "at or over". Seeded comments are by `Seed Author` with ordinary text (`tests/timed_run.py:161`). |
| CP-274's tests, and only those, fail on the post-change shape (CP-274). | A fresh clone of the repository at `3b5746f91` (`git clone --sparse`, then `checkout` and `sparse-checkout set products/tracker17`), in `/private/tmp`. The system's `pytest` first ran `python3 -m pytest -q -p no:cacheprovider tests --ignore=tests/e2e` unchanged. A probe then: refused a restored comment with blank or over-long text or author in `restore_task`; added `domain/comments.py`; added to `task_page`, after the label section, a Comments section with an `h2`, a no-comments line, the no-name notice with a link to `/people`, and a form holding a labelled `textarea` with `maxlength="4000"`, a maximum sentence and an Add button; and added an add-comment submission route. The same command ran again. The page builder, the routes, the saved data and the tests are the real ones. | Unchanged: `937 passed`. Probe: `14 failed, 923 passed` — `test_shapes.py` (1), `test_trace.py` (2), `test_routes.py::test_every_route_leaves_state_and_headers_as_the_rules_say` (1), `test_saved_data.py` (7), `test_task_pages.py` (2), `test_tasks.py::test_restore_task_checks_saved_label_rules` (1). Patching the task-page form lists then surfaced line 318 (`"comment"`), then the no-link assertions at lines 320 and 447 (a link in main); with those patched, `test_task_pages.py` passed. |
| The end-to-end tests are not part of that verdict. | `python3 -c "import playwright"` in the same environment. | `ModuleNotFoundError`. The e2e suite was not run, and CP-275 still requires it to exit 0. Reading finds no task-page form, button or textarea count in `tests/e2e/test_tasks.py` or `test_labels.py`; `tests/e2e/test_first_project.py:81` counts textareas on the project page and `:203` on the not-found page, neither of which this change touches. That reading is not a verdict. |
| The QC-7 route test fixes the route set by hand (CP-271, CP-274). | `tests/integration/test_routes.py:265`, `:293` read. | `assert {route.pattern for route in ROUTES} == set(SAMPLE_ADDRESS)`. |
| `pytest products/tracker17/tests/` collects the end-to-end tests (CP-275). | `pyproject.toml` `[tool.pytest.ini_options]` read; `tests/e2e/conftest.py` grepped for `skip`. | `testpaths = ["tests"]`, and the e2e conftest skips nothing. |
| The project's highest rule identifier is CP-239 (numbering starts at CP-240). | `grep -rhoE "CP-[0-9]+"` over `system/projects/tracker17/journey/tobiishi/trail/` and `products/tracker17`, sorted numerically. | `CP-239` is the highest. |

No rule pins output that renders a language-level fact. The comment's time format is the product's choice (`CONTENT.md` § Grammar and mechanics), and every other pinned output is text or a value the product chooses, so no language-rendering row is owed.

---

## Out of Scope

- Timing the People assignee add and remove in `tests/timed_run.py`. It binds the assignee actions, which this change leaves as they are, and `tracker17 · nemawashi · 2026-10-07_comment-on-a-task` item 3 `full-volume-run` already holds it. CP-273 times only the comment add.
- New tests in `tests/integration/test_timed_run.py`. Its existing tests keep passing, and no record requires one for the comment add.
- Deleting a task together with its comments, and a project together with its tasks and their comments (FDR R-37, R-50). The product has no delete action (`web/routes.py:87-101`), and the request rules it out: "no deleting a comment with its task". Parked in `deferred_decisions.md`.
- Pages served while the saved data is unreadable (FDR R-25, R-26). The product serves none for any unreadable data: the start returns before a listener exists (`main.py:39-48`). A broken comment joins that same refusal (CP-264). The request leaves these pages to a later station. Parked in `deferred_decisions.md`.
- Threaded replies to a comment (FDR OOS-7; Request).
- The task's status and its moves on the task's page (UXD UX-S6; FDR R-56). The task's page shows no status today (`web/pages.py:893-902`), and the request does not ask for it. `tracker17 · nemawashi · 2026-10-07_status-moves` cuts it. Parked in `deferred_decisions.md`.
- Editing or deleting a comment, which no page offers (CP-247).
- The wording of the area's lines. The content stage writes it to `CONTENT.md`'s rules (CP-248).
- Any change to the Your name section, the assignee list or the operator-name rules (Request, "the operator-name behaviour is unchanged").

---

## Locked Answers (the divergence record — self-review 2026-10-12)

- **Gap 1, the no-comments state (b):** CP-244 says there are none yet, with the form in view. The request is silent. UXD UX-S6 states it for the area this change adds, and `CONTENT.md` § Empty lists it.
- **Gap 2, what "oldest first" is keyed to (b):** CP-241 realizes it as the order comments were added, visible as their place in the list, not by re-sorting on the shown time. The request says "oldest first". SDD § 3 holds a task's comments "in the order they were written", and the shown time can disagree with that order if the machine's clock moves, while the order of adding cannot. This choice is reversible.
- **Gap 3, how the time is written (b):** CP-242 uses `YYYY-MM-DD HH:MM`, 24-hour, local. The request says only "the machine's local time". `CONTENT.md` § Grammar and mechanics fixes the form for every time the tracker writes.
- **Gap 4, how the text shows (b):** CP-243 keeps line breaks and shows typed text as text. The request is silent. DESIGN.md says a comment keeps its line breaks, and FDR R-112 binds every typed value on every page.
- **Gap 5, which name is the author (b):** CP-251 takes the name saved when the add is applied. The request says "under the saved operator name". FDR R-102 checks every action against the saved data at that moment, and R-72 records "the operator's current name".
- **Gap 6, which characters are whitespace (b):** CP-256 uses the set the product already applies to the three names, closed by that domain and illustrated with examples. The request says "whitespace only" and names no set.
- **Gap 7, which reason shows when several apply (b):** CP-258, too long, then blank, then no name. The request is silent. Length comes first because the over-long page holds no typed text (FDR PD-11). The two value rules come before the saved-state condition, as the name rules check length then blankness today (`domain/operator_name.py:46-48`). This choice is reversible.
- **Gap 8, a task the tracker does not hold (b):** CP-259 follows the label add today. The request is silent. FDR R-103 refuses an action on a task that no longer exists, and nothing deletes a task yet, so only a request no page sends reaches it.
- **Gap 9, a task in any status (b):** CP-253. The request is silent. FDR R-75 binds the add this change makes.
- **Gap 10, the author in saved data (b):** CP-264 makes a blank or over-long author unreadable. The request says "a comment that breaks a comment rule". FDR R-22 counts "a blank required name" and "an over-long value" as unreadable, and an author is the operator's name as it stood, which FDR R-62 and R-76 hold to non-blank and 200 characters. What still loads — an author other than the saved name, or comments with no saved name — is stated so the start check adds no rule FDR R-72 does not have. CP-274 names the one fixture value this changes.
- **Gap 11, focus, failure, cross-site and keyboard (b):** CP-250, CP-255, CP-260, CP-261 and CP-262. The request names focus after Add only. SDD § 4 EX-4, EX-5, EX-8 and EX-14 and FDR R-107, R-110 and R-113 bind every action, and the add is a new action.
- **Gap 12, the over-long refusal (e):** CP-257 and its test in CP-268. The request names the field's `maxlength` but no over-long refusal. NFDR QC-9, SDD § 4 RT-10 and ADR-0007 say a change that adds a text field writes its `maxlength` "and a test that a longer value is refused". The page holds none of the sent text, where the request keeps the typed text for its two refusals, because FDR PD-11 and SDD § 4 RT-8 say so for an over-long value, and no page of the tracker can send one.
- **Gap 13, one test per refusal and the failure test (e):** CP-268 adds the over-long refusal, the missing task and the failed add to the two refusals the request names. SRS AC-12 asks for tests "one per refusal" and AC-18 for the failure, and NFDR QC-5, QC-38 and QC-56 verify through them.
- **Gap 14, AC-6 with every field, and the saved keys (e):** CP-269. SDD § 6 S-3 *Command* names "SRS AC-6 with every field it lists", and NFDR QC-46's layer-2 test "fails on any key in the saved file outside that set".
- **Gap 15, the route, audit-hook and recording-saver tests (e):** CP-271, from NFDR QC-7, QC-35 and QC-54, each stated over every route or action. The route test lists routes by hand (Verified Claims).
- **Gap 16, typed text shown as text, end to end (e):** CP-272's third test, from NFDR QC-36: "the end-to-end tests at layer 5 that enter `<`, `&` and `"` in every text field a change adds".
- **Gap 17, the entry module's docstring and the landed word (e):** CP-266 and CP-274's `test_trace.py` item. The request names the entry module. NFDR QC-11 and SDD § 4 TS-4 add that "Each slice that delivers a feature adds its word to the test".
- **Gap 18, timing the comment add (e), against the request's "the timed run is not extended: `tests/timed_run.py` and its test stay byte-identical":** CP-273 changes `tests/timed_run.py`. NFDR QC-48 reads "a change that adds a listed action adds it to the run", SDD § 4 TS-5 reads "A slice that adds a listed action adds it to the run", and SRS NFR-1 lists "adding a comment". The run already builds 1,000 tasks with 20 comments each (Verified Claims), so the add is timed at full volume. `tests/integration/test_timed_run.py` stays byte-identical, because no record requires a test of it. Item 3 `full-volume-run` keeps the assignee timing. The previous unit took the same reading for the name save (`2026-10-12_operator-name`, CP-237).
- **Gap 19, the end-to-end suite and the Ruff and mypy gates (e):** CP-275. The request's command already collects `tests/e2e/` (Verified Claims), and SDD § 6 says "Both suites pass". NFDR QC-62 adds the three commands, and NFDR § 10 gates them at the suite.
- **Gap 20, the existing tests that change (f):** CP-274 names 14 tests in six files, where the request names none. The probe in Verified Claims shows each fails on the post-change shape. Each change follows from a record or the request: SDD § 4 TS-4 lands the `comments` word; NFDR QC-7 covers every route; SDD § 4 SD-5 and FDR R-22 make a blank comment or author unreadable, which reverses the "comment content has no rule" assertions; and the comment area and its People link are what the request asks the task's page to show. Each test keeps every other assertion, so the request's "No existing People or task-page test is deleted, skipped or loosened" holds for everything those tests assert besides the absence of comments.
