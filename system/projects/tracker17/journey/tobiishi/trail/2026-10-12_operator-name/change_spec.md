# Change Spec — Your name on People

**Date:** 2026-10-12
**Category:** feature
**Behaviour:** changing
**Request:** Let the operator set and change their own name on the People page. People gains a **Your name** section with a text field and a Save button, and a sentence beside the field saying that comments already written keep their name (SRS FR-27; UXD UX-F8). Saving a name stores it as the one operator name, and saving a different one replaces it; the name is stored exactly as typed. A blank name, whether empty or only whitespace, and a name over the length FR-40 sets for the operator's name are each refused on People with the reason, the typed text kept in the field and the saved name unchanged (SRS FR-27, FR-39, FR-40; UXD UX-F8, UX-I3). The operator name is part of the saved data (SRS DR-5, AC-17): it survives a stop and a start, and a start on data saved before this change loads with no name set and keeps its projects, tasks, labels and people. The name rule lives in the domain and the set action in the application part, not the web part (SDD § 4 TS-3), and saved data holding a blank or over-long operator name is reported as unreadable at start (SDD § 4 SD-5; SRS DR-6). Every string comes from the product's content record, none invented in code ("your name", CONTENT.md § 158). Nothing about comments is built here; the saved name is what the next station's comment form will write under. Tests ship with it: unit tests for the name rule; integration tests through the real server that `GET /people` shows the Your name field and the keep-their-name sentence, that a submitted name is saved and a different one replaces it, including after a real save and restart as `test_people_survives_real_save_and_restart` does for the list, and that a blank name (empty and whitespace only) is refused with the saved name unchanged, the refusal shown and the typed text kept, starting from a saved name and from none; a start-check test that saved data with a blank operator name is reported as unreadable, and one that saved data from before this change still loads. An end-to-end test in `tests/e2e/test_people.py` sets the name in the browser, sees it again after reload, and sees a blank one refused with the typed text kept. The two absence checks in `tests/integration/test_people_pages.py` (L115 and L441) drop `"your name"` from their lists, the one existing-test change this makes true. `pytest products/tracker17/tests/` exits 0, run on a `git archive HEAD` copy that is `git init`-ed, since the repository-ignore test needs a git repo.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `core/doctrine/engineering/languages/python/README.md` opened, and every concern it routes read

---

## Change Summary

The operator can set their own name on People, and change it later. The name is saved, survives a restart, and a start refuses saved data whose name breaks the rule. Until now the product had no operator name: the state holds none and People shows nothing about one.

Paths below are relative to the product root, which `system/projects/tracker17/project.md` `Product path:` names. `SRS`, `SDD`, `UXD`, `FDR`, `NFDR` and `CONTENT.md` are the product's documents under `docs/`. The versions cited are SRS 6, SDD 9, UXD 6, NFDR 11, FDR 4 and CONTENT 10.

---

## Rules

### The Your name section on People

- **CP-211:** People shows a Your name section above the Assignees section. It holds a text field with a visible label, then a Save button. Beside the field is a sentence saying that comments already written keep the name they were written under. The page title stays "People - tracker17". *(SRS FR-27, FR-30; UXD UX-F8, UX-S8; SDD § 6 S-3 *Behaviour*; SDD § 4 EX-9)*
- **CP-212:** When a name is saved, People opens with the field holding that name exactly as saved. When none is saved, the field is empty and the section says that no name is set and that a name is needed to comment. *(UXD UX-S8, the no-name state and "The current name"; FDR R-95; `CONTENT.md` § Empty)*
- **CP-213:** Every word the section, its refusals, its failure line and its completion line show follows `docs/CONTENT.md` (SDD § 4 EX-11). The concept is called "your name", and the section is "Your name". It is never "username", "account", "profile" or "login" (`CONTENT.md` terminology row "The reader's own name, set in the tracker"). The button reads `Save` (UXD UX-F8). This spec fixes what each line must say, and the content stage writes the wording.
- **CP-214:** The field's `maxlength` is the short-text maximum, 200 characters, written from the one place in `domain` that states it. No sentence beside the field states a maximum. *(NFDR QC-9; SDD § 4 RT-10; ADR-0007; UXD UX-F2, UX-F7: only the description and comment fields state one)*
- **CP-215:** The Assignees section keeps everything it does today: its list, Add, each Remove, its empty state, its refusals, its completion lines and where each places focus. *(Request, "the assignee list behaves as before")*

### Saving a name

- **CP-216:** Pressing Save with a name that is not blank (CP-220) and is at most 200 code points saves that name as the one operator name, replacing any name saved before. The browser is sent to People, which shows the new name in the field and one completion line naming the saved name, quoted. Keyboard focus is in the Your name section, on the field or on an element showing the saved name, and the completion line is the focused element's accessible description. Development-design chooses which element. A reload of that page, or a return to it through back or forward, saves nothing again. *(SRS FR-27, DR-5; FDR R-62, R-106; UXD UX-I4; SDD § 4 EX-5, EX-14, RT-8, RT-9)*
- **CP-217:** The name is saved and shown exactly as typed: surrounding spaces and letter case are kept. Its length is counted in Unicode code points on the value as saved, spaces included, so a name of exactly 200 code points is accepted, including one holding a character outside the Basic Multilingual Plane. The name is changed in no way other than SDD § 4 RT-10's line-break normalization. *(FDR R-76, R-77, R-80; SRS FR-40; SDD § 4 RT-10; ADR-0007)*
- **CP-218:** Pressing Save with exactly the name already saved at that moment is not refused and changes nothing. No save is made, and People shows no completion line and no refusal. Names are compared exactly, so `Sam ` saved over `Sam` is a different name and replaces it under CP-216. *(FDR R-116, R-65 and R-34, which refuse no action that changes nothing; NFDR QC-21; UXD UX-I4)*
- **CP-219:** No action removes the operator name. Once a name is saved, the operator name is never empty again. *(FDR R-62; SRS DR-5)*

### Refusals and failures

- **CP-220:** A blank name is refused. A name is blank when it is empty, or when every character in it is whitespace. Whitespace is the same set of characters the product already treats as blank in a project name and an assignee name, so a name refused as blank there is refused here, and the other way round. The space, the tab, U+00A0 (no-break space) and U+3000 (ideographic space) are in that set, and U+200B (zero-width space) is not (Verified Claims). The saved name is unchanged, whether a name was saved or none. People opens with keyboard focus in the Your name field, the reason beside it as the field's accessible description, and the field holding what was typed. *(SRS FR-27, FR-39; FDR R-62, R-100; UXD UX-F8, UX-I3; SDD § 4 EX-4, EX-14)*
- **CP-221:** A name longer than 200 code points is refused, and the saved name is unchanged. Only a request that no page of the tracker sends can carry one, because CP-214's field stops at 200. The page that answers opens at the Your name field and gives the reason beside it. It holds none of the text that was sent: the field shows the saved name, or nothing when none is saved. Length is checked before blankness, so 201 spaces get the too-long reason. *(SRS FR-39, FR-40; FDR R-78, R-79, PD-11; SDD § 4 RT-8, RT-10; ADR-0006)*
- **CP-222:** When a save fails for a reason that is not a refusal, the saved data and the current name stay as they were. People says in plain words that the save did not happen and that nothing was changed, and shows no error text from Python. The typed text is still in the field, and keyboard focus is on Save with the failure line as its accessible description. The console shows a message naming the action, then the error. *(FDR R-18, R-107, R-108; UXD UX-I5; SDD § 4 OB-3, EX-4; NFDR QC-49, QC-56, QC-57)*
- **CP-223:** A save that does not come from the tracker's own pages is refused and changes nothing, under the check every submission passes today. That covers one marked `cross-site` or `same-site`, and one not marked `same-origin`, a submission with no mark included. *(FDR R-110; SDD § 4 SEC-2; NFDR QC-32)*

### Use of the section

- **CP-224:** Setting the name can be done from the keyboard alone, with the browser's own keys. *(SDD § 4 EX-8; UXD UX-I6)*
- **CP-225:** A name holding `<`, `&` or `"` is shown as typed, in the field and in the completion line, and changes nothing around it. *(FDR R-112; SDD § 4 SEC-4; NFDR QC-36)*

### Saved data

- **CP-226:** The operator name is part of the saved data. After a stop and a start, People shows the saved name in the field. The saved data changes only by the one operator name SRS DR-5 allows: projects, tasks, their labels and comments, the assignee list and the two identity counters keep the saved form they have today, and nothing else about any person is added. *(SRS FR-5, DR-5, NFR-6, AC-6, AC-17; FDR R-15, R-29; NFDR QC-46)*
- **CP-227:** Saved data written before this change, in each form the tracker reads today, loads with no name set. It keeps its projects, its tasks with their labels and comments, and its assignee list, and loading it writes nothing. *(Request; FDR R-15, R-23; Verified Claims, the three forms read today)*
- **CP-228:** At start, saved data is unreadable when its operator name is blank (CP-220's set), longer than 200 code points, or present in a form that is neither text nor the saved form's way of saying no name is set. In each case:
  - the console says the data is unreadable and names its location;
  - the start refuses as it does today for any other unreadable data: the tracker does not start and exits non-zero (`main.py:39-48`);
  - nothing of the data is loaded;
  - the saved data's bytes are unchanged.

  Saved data with a name of exactly 200 code points, a name with surrounding spaces, or no name loads. *(SRS DR-6; FDR R-21, R-22, R-23, R-24, R-27; SDD § 4 SD-4, SD-5; NFDR QC-22, QC-37, QC-51)*

### What does not move

- **CP-229:** No comment is written, listed or refused. The task page is unchanged: no comment form, no no-name notice. `domain/comments.py` does not exist, and comments already in saved data are carried as they are. Saving a name changes no project, task, label or assignee. *(Request, "Must not be weakened or added")*

### Where the code lives (fixed by the records)

- **CP-230:** The name rules, blank and too long, live in `domain`. The save is applied in `application`, and `web` holds no name rule (SDD § 3 parts table; SDD § 4 TS-3, as the request cites it; NFDR QC-20, QC-21, QC-23, QC-38). Each refusal reaches `web` as a refusal type from `domain`, handed on through `application`, and `web` maps it to its reason by type, never by reading a message (SDD § 4 OB-4; NFDR QC-5, QC-16). `domain` holds no wording shown to the operator (NFDR QC-20). Every test module the change adds names the requirements or acceptance criteria it checks (SDD § 4 TS-3; NFDR QC-11). The feature word `comments` is not listed as landed.

### Tests (named in the request, or required by the records)

- **CP-231:** Unit tests cover the name rules in `domain` with no file and no clock: the empty name, a spaces-only name, a name of other whitespace only (a tab, U+00A0), 200 code points accepted, 201 refused, 201 spaces getting the too-long refusal, surrounding spaces kept, a first name saved, a different name replacing it, the same name changing nothing, and the restore checks of CP-228. *(Request; SDD § 4 TS-1)*
- **CP-232:** Layer-3 and layer-4 tests run `web` with `application` in one process, with the clock and the saver handed in (SDD § 4 TS-1). They cover:
  - `GET /people` showing the Your name field, its label, Save and the keep-their-name sentence, and the field's `maxlength` equal to the maximum `domain` states (CP-211, CP-214);
  - the no-name state, and the field holding a saved name (CP-212);
  - a save, and a different name replacing it (CP-216);
  - a save, then a restart on a real `SavedData`, as `test_people_survives_real_save_and_restart` does for the list (CP-226);
  - the same name saving nothing (CP-218);
  - one test per refusal, each asserting the reason shown and the saved data unchanged: the empty name and the whitespace-only name, each starting from a saved name and from none, with the typed text kept; and the over-long name sent in a request no page sends, with none of the sent text on the page;
  - a failed save (CP-222).

  *(Request; SRS AC-12, AC-18; NFDR QC-5, QC-9, QC-38, QC-56)*
- **CP-233:** Start tests write saved data with an empty operator name, a whitespace-only one, one of 201 code points, and one that is a number, one case per test. Each finds the start reporting the data unreadable, loading none of it, and leaving its bytes unchanged. Further start tests load each form of saved data the tracker reads today and find no name set, with the projects, tasks, labels, comments and assignees kept. *(Request; SRS AC-7; SDD § 4 SD-5; NFDR QC-22, QC-37, QC-51)*
- **CP-234:** A layer-2 test saves a state carrying an operator name and finds nothing in the saved file outside what SRS DR-1 to DR-5 describe and the two identity counters. *(NFDR QC-46; SRS AC-17)*
- **CP-235:** Three existing tests cover the new action:
  - the route test of NFDR QC-7 covers the submission route this change adds;
  - the outbound-connection test of NFDR QC-35, which drives actions through `web` under the audit hook, drives a name save;
  - a recording-saver test under NFDR QC-54 runs a name save and finds that the saver received only saves.

  *(NFDR QC-7, QC-8, QC-34, QC-35, QC-54)*
- **CP-236:** End-to-end tests in `tests/e2e/test_people.py` drive Chromium against a tracker started by `main`:
  - one sets the name, reloads, and sees it again; then submits a blank name and finds it refused with the typed text kept (Request);
  - one saves a name holding `<`, `&` and `"` and finds People showing it as typed (NFDR QC-36; SDD § 11 R-3; FDR R-112).
- **CP-237:** `python3 tests/timed_run.py`, run from the product root at the volume it builds today (1,000 tasks with 20 comments each), times a name save and its landing page. Each shows its result within 1 second, the save is sent marked `same-origin`, and the run fails when the save is refused or fails. *(SRS NFR-1, "every operator action", AC-15; NFDR QC-48, QC-32; SDD § 4 TS-5)*
- **CP-238:** Existing tests that assert the state this change reverses change only in what they assert about People's single section or the state's fields. Each keeps every other assertion, and none is deleted or skipped:
  - `tests/integration/test_people_pages.py`: the absence lists at lines 115 and 441 drop `"your name"` and `"comment"` and keep `"all tasks"`, `"operator"` and `"assign to"`. The helpers and assertions that assume People holds one section and one form field are scoped to the Assignees section: `name_input` (line 51), `heading` (line 75), the single label, input and button at lines 108, 111 and 112, the no-paragraph check at line 308, the single section at line 381 and the single text field at line 444. Each still asserts what it asserts about the assignee list, its form, its focus and its lines;
  - `tests/integration/test_people_routes.py`: the single text field at line 315 is scoped to the Assignees form, and still asserts the kept text " Cy ";
  - `tests/architecture/test_shapes.py`: the tracker state's fields at line 185 admit the operator name and nothing else. Lines 180 to 183 stay, so `domain/comments.py` still must not exist;
  - `tests/integration/test_saved_data.py`: where the design's saved form makes a `FULL_KEYS` assertion false (lines 330, 338, 395, 666, 682, 1028, 1091), it changes only by admitting the one operator name.

  The probe in Verified Claims found 21 tests failing without these changes. No other existing test changes to fit. *(Request, "No existing People test is deleted, skipped or loosened"; SDD § 3, What the system holds)*
- **CP-239:** Two sets of commands exit 0:
  - `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/`, run on a `git archive HEAD` copy that is `git init`-ed, so `test_data_is_ignored_by_version_control` has its repository (NFDR QC-47; `CROSS_ROLE.md` § Every seat);
  - from the product root, `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web` (NFDR QC-62).

---

## Examples

| Scenario | Expected behavior | Rule |
|---|---|---|
| No name saved; People is opened | Above Assignees, the Your name section: the labelled field, empty, then Save, with the keep-their-name sentence beside the field and a line saying no name is set and a name is needed to comment. The Assignees section is as before. | CP-211, CP-212, CP-215 |
| `Sam` saved; People is opened | The field holds `Sam`. No no-name line. | CP-212 |
| The section's words | "Your name" names the section, the button reads `Save`, and every line follows `CONTENT.md`. | CP-213 |
| The Your name field | `maxlength` equals the short-text maximum `domain` states (200). No sentence states a maximum. | CP-214 |
| No name saved; the operator types `Sam` and presses Save | Saved. People shows `Sam` in the field and one completion line naming `'Sam'`. Focus is in the Your name section, described by that line. Reloading saves nothing. | CP-216 |
| `Sam` saved; the operator saves `Sam Lee` | `Sam Lee` replaces `Sam`. | CP-216 |
| The operator saves ` Sam ` (surrounding spaces) | Saved and shown as ` Sam `. | CP-217 |
| The operator saves a name of 200 code points, one of them `😀` | Accepted. | CP-217 |
| `Sam` saved; the operator saves `Sam` | Not refused. No save, no completion line, no refusal. | CP-218 |
| `Sam` saved; the operator saves `Sam ` | Replaces `Sam`. | CP-218, CP-216 |
| `Sam` saved; the operator clears the field and presses Save | Refused as blank. `Sam` is still the saved name, the field holds what was typed (empty), and focus is in the field with the reason as its description. | CP-219, CP-220 |
| No name saved; the operator saves `   ` | Refused as blank. No name is saved, and the field holds `   `. | CP-220 |
| The operator saves a tab, or U+00A0, alone | Refused as blank. | CP-220 |
| The operator saves U+200B alone | Accepted, as it would be for a project or assignee name. | CP-220 |
| A request with no page behind it sends 201 code points | Refused. The saved name is unchanged. The page gives the reason at the field and holds none of the sent text. | CP-221 |
| A request sends 201 spaces | Refused with the too-long reason. | CP-221 |
| The save fails while saving `Sam` | People says the save didn't happen and nothing changed. `Sam` is still in the field, focus is on Save, and the console names the action and the error. | CP-222 |
| A save marked `Sec-Fetch-Site: cross-site` | Refused. Nothing changes. | CP-223 |
| The operator tabs to the field, types `Sam` and presses Enter | `Sam` is saved, with no pointer used. | CP-224 |
| The operator saves `<b>A&B</b> "x"` | The field and the completion line show it as typed. | CP-225 |
| `Sam` saved; stop; start | People shows `Sam` in the field. | CP-226 |
| A name is saved; the saved file is read | It holds the operator name, and nothing else is added. | CP-226, CP-234 |
| A start on data saved before this change, in any of the three forms read today | Loads with no name set. Projects, tasks, labels, comments and assignees are kept, and the file's bytes are unchanged by the load. | CP-227, CP-233 |
| Saved data whose operator name is `""`, `"   "`, 201 code points, or a number | The start reports the data unreadable, names its location and does not start. Nothing loads, and the bytes are unchanged. | CP-228, CP-233 |
| Saved data with no name, a 200-code-point name, or ` Sam ` | Loads. | CP-228 |
| A name is saved | No comment is written. The task page shows no comment form and no no-name notice. `domain/comments.py` does not exist. | CP-229 |
| A refused save of each kind | Each refusal comes from `domain` as a type, through `application`, mapped by type in `web`. | CP-230 |
| The suite runs after the change | The unit, layer-3/4, start and saved-key tests of CP-231 to CP-234, and the route, audit-hook and recording-saver coverage of CP-235, are present and pass. | CP-231 to CP-235 |
| The end-to-end suite runs | The set-reload-refuse test and the `<`, `&`, `"` test pass. | CP-236 |
| `python3 tests/timed_run.py` | Lists a name save and its landing, each under 1 second, and exits 0. | CP-237 |
| The existing tests named in CP-238 after the change | Each changes only as CP-238 states and keeps every other assertion. | CP-238 |
| The gates of CP-239, on a `git init`-ed `git archive HEAD` copy | Each exits 0. | CP-239 |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| The product has no operator name today: the state holds none and the saved file writes none (Change Summary). | `domain/state.py:26-30` and `persistence/saved_data.py:102-111` read. | `TrackerState` holds `projects`, `next_project_id`, `assignees`, `tasks`, `next_task_id`. The saved document holds those five keys. |
| The tracker reads three forms of saved data today (CP-227, CP-233). | `persistence/saved_data.py:26-29` read. | `SUPPORTED_STATE_KEYS = (LEGACY_STATE_KEYS, PEOPLE_STATE_KEYS, STATE_KEYS)`: the projects-only form, the form with assignees, and the full form with tasks. |
| Blank project and assignee names are refused by one whitespace test (CP-220). | `domain/projects.py:44`, `domain/assignees.py:43` read; the set was then probed with `python3 -c` on `str.isspace`. | Both use `all(character.isspace() for character in name)`. `' '`, `'\t'`, `'\n'`, U+00A0, U+3000 and U+2003 are whitespace; U+200B and U+FEFF are not. |
| An over-long value is checked before blankness for names today (CP-221). | `domain/assignees.py:42-44` and `domain/projects.py:42-45` read. | `ensure_within(...)` runs before the whitespace test. |
| A start on unreadable data writes one line and returns 1 (CP-228). | `main.py:30-48` read. | On `UnreadableData` it prints the location message to stderr and returns `1` before any listener exists. |
| A no-change outcome saves nothing and shows no completion line today (CP-218 follows it). | `application/tracker.py:108-139` and `web/routes.py:469` read. | `edit_task` and the label actions save only on `outcome.changed`; an unchanged edit redirects with no `saved` flag. |
| People has one section, one text field, one label and one button, and the two named tests assert more than `"your name"` (CP-238). | `tests/integration/test_people_pages.py:50-52, 74-76, 108-115, 308, 381, 441-444` and `tests/integration/test_people_routes.py:315` read. | The absence lists also hold `"comment"`, and helpers unpack exactly one text input, one `h2` and one `section`. |
| Adding a Your name section and an operator-name state field fails 21 existing tests (CP-238). | In a disposable copy (`git archive b11ab3fdb products/tracker17`, `git init`-ed), the system's `pytest 9.0.3` first ran `pytest -q tests --ignore=tests/e2e` unchanged. Then a probe appended to `people_page` a section holding a labelled text field, a Save button, the keep-their-name sentence and the no-name sentence, dropped `"your name"` from the two lists the request names, added `operator_name: str \| None = None` to `TrackerState`, and ran the same command. The conditions are the real page builder and the real tests. | Unchanged: `813 passed`. Probe: `21 failed, 792 passed`, being 18 in `test_people_pages.py` (on `"comment"` at line 442, the unpacks at lines 51, 75, 108 and 381, and line 308), 2 in `test_people_routes.py` (line 315) and `test_shapes.py::test_only_the_task_features_are_added_to_domain` (line 185). |
| The e2e People tests are not part of that verdict. | `python3 -c "import playwright"` in the same environment. | `ModuleNotFoundError`. The e2e suite was not run, and CP-239 still requires it to exit 0. `tests/e2e/test_people.py` locates by element id (`#assignee-name`, `#assignees-heading`), so reading finds no single-field assumption there, but that is not a verdict. |
| The seven `FULL_KEYS` assertions (CP-238). | `grep -n 'FULL_KEYS\|set(document)' tests/integration/test_saved_data.py`. | `FULL_KEYS` at line 319, asserted at lines 330, 338, 395, 666, 682, 1028 and 1091. |
| `test_shapes.py` forbids `domain/comments.py` and fixes the state's fields (CP-229, CP-238). | `tests/architecture/test_shapes.py:180-185` read. | `"comments"` is in the `later` tuple at line 182, and line 185 asserts the five fields. |
| The timed run already builds 1,000 tasks with 20 comments each (CP-237). | `tests/timed_run.py:1-17, 59` read. | `TASK_VOLUME = 1000`; the docstring reads "seeds 1,000 tasks of 20 comments each". It times no People action today. |
| The QC-7 route test and the QC-35 test list their routes and actions by hand (CP-235). | `tests/integration/test_routes.py:288-326, 412-438` read. | The route test asserts `{route.pattern for route in ROUTES} == set(SAMPLE_ADDRESS)`. The audit-hook test sends each request explicitly. |
| The Save button word exists in the product today. | `web/pages.py:686` read. | The task edit form's button reads `Save`. |
| The project's highest rule identifier is CP-210 (numbering starts at CP-211). | `grep -rhoE "CP-[0-9]+"` over `system/projects/tracker17/journey/tobiishi/` and `products/tracker17`, sorted numerically. | `CP-210` is the highest. |

No rule pins output that renders a language-level fact. Every pinned output is text or a value the product chooses, so no language-rendering row is owed.

---

## Out of Scope

- The comment form, the no-name notice above it on a task's page, comments written under the saved name, and earlier comments keeping an earlier name. These belong to `tracker17 · nemawashi · 2026-10-07_comment-on-a-task`, item 2 `comments-on-the-page`.
- Timing adding a comment at full volume, which is item 3, `full-volume-run`, of the same seed. CP-237 times only the name save.
- Any rule over comment content, and `domain/comments.py`. The request rules them out: "Nothing about comments is built here". FDR R-71 to R-75 bind the task page, which this change leaves as it is. They are parked in `deferred_decisions.md`, already placed at item 2 of the seed.
- A sentence beside the Your name field stating its maximum (UXD UX-F2, UX-F7: only the description and comment fields state one).
- Any change to the Assignees section's behaviour (CP-215).
- The wording of the section's lines. The content stage writes it to `CONTENT.md`'s rules (CP-213).
- Pages served while the saved data is unreadable (FDR R-25, R-26). The product has none today for any unreadable data: the start returns before a listener exists (`main.py:39-48`). A broken operator name joins that same refusal. The gap between those FDR lines and the product is the product's, not this change's, and it is parked in `deferred_decisions.md`.
- Timing the assignee add and remove in `tests/timed_run.py`, which times no People action today (`tests/timed_run.py:1-17`). This change adds no assignee action. It is parked in `deferred_decisions.md`.

---

## Locked Answers (the divergence record — self-review 2026-10-12)

- **Gap 1, the typed text after an over-long refusal (a):** CP-221 holds none of the sent text, where the request says both refusals keep "the typed text kept in the field". *Because* FDR PD-11 reads "After a refusal for an over-long value, the page gives the reason and not the typed text", and SDD § 4 RT-8 and ADR-0006 say the same. RT-8 adds that "No form of the tracker's own can reach that refusal", so the typed text is kept on every form the operator uses. The blank refusal keeps what was typed (CP-220). The field then shows the saved name, as People does on any load (CP-212). The departure follows the locked FDR decision, so it is not a scope change. This is the same reading the labels change took (`2026-10-12_task-labels`, CP-191).
- **Gap 2, the no-name state on People (b):** CP-212 has the section say that no name is set and that a name is needed to comment. The request is silent on the empty state. UXD UX-S8 states it for the section this change adds, and `CONTENT.md` § Empty carries it. The request's "no-name notice" left for later is the notice above the comment form (station *Not here*; UXD UX-F7), which CP-229 keeps out.
- **Gap 3, saving the name already saved (b):** not refused, no save, no completion line (CP-218). The request names only a different name replacing it. *Because* the product refuses no action that changes nothing (FDR R-34, R-65, R-116), and the product's other no-change outcomes save nothing and show no line (Verified Claims). This choice is reversible.
- **Gap 4, which characters are whitespace (b):** CP-220 closes the set by its domain, the set the product already applies to project and assignee names, and names members only as examples. The request says "only whitespace" and names no set. One rule across the three names means a name refused in one place is refused in the others.
- **Gap 5, too long before blank (b):** 201 spaces get the too-long reason (CP-221). The request is silent. Project and assignee names check length first today (Verified Claims).
- **Gap 6, focus and the section's place (b):** CP-216, CP-220, CP-221 and CP-222 place focus as SDD § 4 EX-4, EX-5 and EX-14 do for every action. CP-211 puts Your name above Assignees, in the order UXD UX-F8 and UX-S8 name them. The request is silent on both.
- **Gap 7, a failed save, the cross-site refusal and the keyboard (b):** CP-222, CP-223 and CP-224. The request names none. FDR R-107 and R-110 and SDD § 4 EX-8 bind every action, and the save is a new action.
- **Gap 8, a saved name that is not text (b):** unreadable at start (CP-228), unless it is the saved form's own way of saying no name is set, which development-design chooses. The request names blank and over-long. FDR R-21 counts saved data the tracker cannot read in full as unreadable.
- **Gap 9, the field's `maxlength` and the over-long test (e):** CP-214 and CP-232. The request names the over-long refusal but no field bound or test. NFDR QC-9, SDD § 4 RT-10 and ADR-0007 say "A slice that adds a text field must write its `maxlength` and test a longer value".
- **Gap 10, one test per refusal, the failure test and the over-long start check (e):** CP-232 adds the over-long refusal and the failed save to the blank refusals the request names, and CP-233 adds the over-long and non-text start checks to the blank one. *Because* SRS AC-12 asks for tests "one per refusal", AC-7 for "one per kind of break DR-6 names", and NFDR QC-5, QC-22, QC-38 and QC-56 verify through them.
- **Gap 11, the saved-key test (e):** CP-234, from NFDR QC-46, whose layer-2 test "fails on any key in the saved file outside that set". The request's "saved data changes only by the one operator name" is checked this way.
- **Gap 12, the route, audit-hook and recording-saver tests (e):** CP-235, from NFDR QC-7, QC-35 and QC-54. Each states its check over every route or action, and the first two list theirs by hand (Verified Claims).
- **Gap 13, typed text shown as text, end to end (e):** CP-236's second test, from NFDR QC-36, which asks for "the end-to-end tests at layer 5 that enter `<`, `&` and `"` in every text field a change adds".
- **Gap 14, timing the name save (e):** CP-237, against the request's "Left to later stations: … the 1,000 × 20 timed run". *Because* NFDR QC-48 reads "a change that adds a listed action adds it to the run", and SRS NFR-1 covers "every operator action". The run already builds 1,000 tasks with 20 comments each (Verified Claims), so the save is timed at full volume today. Item 3, `full-volume-run`, keeps the comment add at that volume.
- **Gap 15, Ruff and mypy (e):** CP-239 adds NFDR QC-62's three commands. NFDR § 10 gates them at the suite.
- **Gap 16, the existing tests that change (f), against the request's "the one existing-test change this makes true":** CP-238 names 21 failing tests in three files, and conditional assertions in a fourth, where the request names two list edits. The probe in Verified Claims shows the request's claim is false. The two absence lists also hold `"comment"`, which the keep-their-name sentence the request asks for contains. Eighteen tests in `test_people_pages.py` and two in `test_people_routes.py` assume People has one section, one text field, one label and one button. `test_shapes.py` fixes the state's fields at five, and SDD § 3 makes the operator name part of the one tracker state. Each assertion changes only in scope, from the page to the Assignees section, or by admitting the operator name. Every assertion about the assignee list, the forbidden `domain/comments.py` and the saved shape stays, so the request's intent, no assignee test loosened, holds. SDD § 4 EX-12 forbids words pointing at an area "Until the slice that delivers" it. The sentence about comments, which the request asks for, is part of SDD § 6 S-3, the slice that delivers both Your name and comments.
- **Gap 17, the `FULL_KEYS` assertions (f), conditional:** CP-238's last item. Whether the saved file always writes the operator name, or only once one is set, is development-design's choice. Where that choice makes a `FULL_KEYS` assertion false, the assertion admits the one name and nothing more. The request's "the saved data changes only by the one operator name" bounds it.
