# Change Spec — The task page changes a task's four fields and shows its project

**Date:** 2026-10-11
**Category:** feature
**Behaviour:** changing
**Request:** Let the operator change a task. The task page, which today only shows the task, gains an edit form holding the task's title, priority, assignee (or none) and due date as saved, and shows the name of the task's project as text (UXD UX-S6). Saving with changed values redirects to the task's page showing each new value; a save changing one field leaves the other three as saved. A field counts as changed when its submitted value differs from the value the page showed, and a save writes only the changed fields; the form carries the values the page showed, because the tracker keeps nothing between requests (SDD § 4 RT-7). A blank title is refused on the task page where it was entered, with the typed text kept and the saved data unchanged (SRS FR-15; UXD UX-I3). A task whose assignee has left the People list shows that name as the assignee control's current choice with UX-F9's sentence beside it, and a save that leaves the control as shown keeps the name until the operator replaces it. An assignee changed to a name that left the list after the page loaded is refused as out of date, saying so, with the saved data unchanged (UXD UX-I3). A plain field edit from a page loaded before another tab saved a different value replaces that value (SRS AC-19). The edit and its rules live in the domain and application parts, not the web part (SDD § 4 TS-3). Every string comes from the product's content record, none invented in code.

Tests ship with it: unit tests for the edit rules; integration tests through the real server for the form as saved, the project shown as text, a four-field save, a one-field save, the blank-title refusal, the left-the-list assignee kept, the out-of-date assignee refusal, and the stale-page test (load the form, save a different title through a second submission, submit the first form with a changed title: the first title is saved, not refused). An end-to-end test edits a title to one holding `<`, `&` and `"` and finds the task's page and the project's list showing it as typed (NFDR QC-36). `python3 products/tracker17/tests/timed_run.py` times a field edit among its actions at 1,000 tasks and exits 0 (NFDR QC-48). `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/` each exit 0, run on a `git archive HEAD` copy that is `git init`-ed, since the repository-ignore test needs a git repo.

**Must not be weakened or added:** `domain/labels.py` is not created and no label is added or removed; the label check on saved data stays with the next station. No status move, delete, filter, sort control, summary or comment is added. The saved form of a task and of the People list must not change, and no existing test is weakened to fit.
**Language resolution:** Python — step 1, `system/projects/tracker17/project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with the five files it routes and `testing_python.md`

---

## Change Summary

A task's page gains one edit form for its title, priority, assignee and due date, and shows the task's project by name. A save writes only the fields that differ from what the form showed, keeps a left-the-list assignee until it is replaced, and refuses a blank title or an out-of-date assignee with nothing changed. This change realizes FDR R-45 to R-48, R-104 and R-115 to R-118 for the four fields (labels wait for `task-labels`), and it replaces the read-only task page that CP-124 set.

Every place below that says "the content step's words" means the wording is written in this change's text record under `docs/CONTENT.md`. This spec states what each string must say. It fixes words only where CONTENT.md or the request already fixes them: `low`, `medium`, `high`, `critical`, and the completion verb "saved changes to" (CONTENT.md § Message patterns, Completed). Paths to code are relative to the product root, which `system/projects/tracker17/project.md` `Product path:` names.

---

## Rules

### The edit form on the task page

- **CP-144:** A task's page shows one edit form with four fields, a title, a priority, an assignee and a due date, and a Save button. Every task's page has it, whatever the task's status. No field in the form sets the status. *(SRS FR-16; FDR R-45, R-46; UXD UX-F9, UX-S6)*
- **CP-145:** When the page opens, each field holds the task's value as saved when the page was built. The title field holds the title exactly as saved, surrounding spaces included. The priority control offers exactly `low`, `medium`, `high` and `critical`, each written as that word, with the task's priority chosen. The due-date field holds the task's due date, or is empty when the task has none, and the operator sets, changes or clears it with the browser's own date picker. The page runs no script. *(SRS FR-16; FDR R-45, R-51, R-114; UXD UX-F9; SDD § 4 EX-2)*
- **CP-146:** The edit form's title field lets in at most 200 characters. *(SRS FR-40; FDR R-76, R-79; SDD § 4 RT-10; NFDR QC-9)*
- **CP-147:** When the task is unassigned, or carries a name on the assignee list, the assignee control offers none and every name on the list as saved when the page was built, each exactly as saved, in the list's order, with the task's assignee, or none, chosen. *(SRS FR-16, FR-21; UXD UX-F9)*
- **CP-148:** When the task carries a name that is not on the assignee list when the page is built, the assignee control shows that name as its chosen option, and also offers none and every name on the list. Beside the control, never inside the option, a sentence says the name is no longer on the list, and that choosing another assignee or none replaces it, after which it can be set again only once it is added back on People, in the content step's words. A task whose assignee is on the list, or who has none, shows no such sentence. *(SRS FR-22; FDR R-48, R-61; UXD UX-F9, UX-S6; SDD § 6 S-2, *Reached when*)*
- **CP-149:** The task's page shows the name of the task's project as text, exactly as saved. No control on the page changes the task's project. Whether that name links to the project's page is development-design's. *(FDR R-49; UXD UX-F9, UX-S6)*
- **CP-150:** Opening a task's page changes no data. The page carries no control that moves a status, deletes, or adds or removes a label or a comment. *(FDR R-106; the request, "Must not be weakened or added")*

### Saving the form

- **CP-151:** In a save of the edit form, a field counts as changed when the value submitted for it differs from the value the form showed for it. It is never compared with the value saved at the moment the save is applied. The two are compared exactly, after the line-break normalization every submitted value already receives (SDD § 4 RT-10). The shown values travel in the form itself, which SDD § 4 RT-7 fixes, and this spec chooses nothing further about how. A field whose submitted value, or whose shown value, the submission does not carry counts as unchanged. *(FDR R-115; SDD § 4 RT-7; see Locked Answers, Gap 3)*
- **CP-152:** A save writes every changed field and no other. A field left as the form showed it keeps whatever value is saved at the moment the save is applied, including a value another tab saved after this page loaded. *(SRS FR-16; FDR R-47)*
- **CP-153:** A changed field is saved as submitted. The title is saved exactly as typed, surrounding spaces included. The priority is saved as the chosen word. The assignee is saved as the chosen listed name, or cleared when none is chosen. The due date is saved as the chosen calendar date, or cleared when the field is empty. *(SRS FR-16; FDR R-45, R-80)*
- **CP-154:** A plain field edit from a page loaded before another tab saved a different value for that field replaces that value, and is not refused. *(SRS NFR-3, AC-19; FDR R-104)*
- **CP-155:** A save with at least one changed field and no refusal is answered by sending the browser to the task's page. That page shows each changed field's new value and every other field as saved. Reloading that page, or reaching it again with back or forward, saves nothing. *(FDR R-106; SDD § 4 RT-8)*
- **CP-156:** The task's page that answers a save under CP-155 carries one completion line naming the task by its title as now saved, quoted, in the content step's words, with the verb "saved changes to". It is shown only once the save is on disk. The page opens with keyboard focus on its heading, which is the task's title, as the page that answers an add does today (CP-115). The line is the heading's accessible description and never takes focus. *(UXD UX-I4, UX-A5; SDD § 4 EX-5, EX-14, RT-9; CONTENT.md § Message patterns, Completed)*
- **CP-157:** A save in which no field changed changes nothing and is not refused. The saved data is unchanged. It is answered by the task's page as saved, with no completion line. *(FDR R-116; see Locked Answers, Gap 2)*
- **CP-158:** A save is checked against the saved data at the moment it is applied, and only its changed fields are checked. An unchanged field is never refused for its value. An assignee left as the form showed it is kept, and not refused, even when that name is not on the list when the save is applied. *(FDR R-48, R-102; SDD § 4 RT-7; UXD UX-F9)*
- **CP-159:** When a task carries a name that is not on the list, a save that changes the assignee to a listed name or to none replaces that name. The task's page then shows the new choice, no longer offers the replaced name, and shows no CP-148 sentence. A later save that chooses the replaced name while it is off the list is refused under CP-163. *(FDR R-118; UXD UX-F9)*

### Refusals and failures of a save

- **CP-160:** When any changed field in a save is refused, the save changes no field. The saved data is unchanged, and a changed field that would have been accepted on its own is not saved either. *(SRS FR-39; FDR R-100, R-117)*
- **CP-161:** A changed title with no character other than whitespace, the empty title included, is refused. The task's page opens with keyboard focus in the title field. What was typed and chosen in all four fields is still there. The reason sits beside the title field and is its accessible description. It says a task needs a title and what to do, in the content step's words. *(SRS FR-15, FR-39; FDR R-40, R-100; UXD UX-I3, UX-A3; SDD § 4 EX-4, EX-14)*
- **CP-162:** Only a request that no page of the tracker sends can carry a changed title longer than 200 characters, and that title is refused. The task's page opens with keyboard focus in the title field and the reason beside it. Neither the page nor its address holds any of the sent text, and the four fields show the task as saved. A title that is too long and also blank, such as 201 spaces, gets the too-long reason, as an added task's title does (CP-118). *(SRS FR-40; FDR R-76 to R-79; PD-11; SDD § 4 RT-8, RT-10; NFDR QC-9)*
- **CP-163:** A changed assignee naming a name that is not on the assignee list when the save is applied is refused. From the tracker's own form this arises when another tab removed the name after the page loaded. The reason says the page is out of date because the name is no longer on the assignee list, and offers a reload, in the content step's words. It sits beside the assignee control, keyboard focus is on that control, and the other three fields are still as entered. *(SRS FR-21, NFR-3; FDR R-60, R-102; UXD UX-F9, UX-I3)*
- **CP-164:** A changed priority other than `low`, `medium`, `high` or `critical`, or a changed due date that is not a valid calendar date, is refused. No form of the tracker's own sends either. The reason sits beside the control concerned and says what is wrong, in the content step's words. *(SRS FR-15; FDR R-51, R-100; FDR RN-6)*
- **CP-165:** When more than one changed field in one save is refused, the page shows one reason, for the first refused field in this order: the title too long, the title blank, the priority, the assignee, the due date. Keyboard focus is on that field. This is the order an add checks in today. *(FDR R-117; UXD UX-I3; see Locked Answers, Gap 4)*
- **CP-166:** After a refusal that keeps what was typed (CP-161, CP-163, CP-164) or a failure (CP-168), the next save from that page counts a field as changed when it differs from the value the form showed before the refused or failed submission. A change kept through a refusal is therefore saved by the next save, and a field the operator never changed still keeps whatever is saved when that save is applied. After the too-long refusal of CP-162 the form shows the task as saved, and a save from it compares with those values. *(FDR R-47, R-115; UXD UX-I3; see Locked Answers, Gap 3)*
- **CP-167:** A save for a task identity that no task holds saves nothing and is answered by the not-found page that says there is no task at this address, the page CP-125 set. *(FDR R-103, R-105; UXD UX-F9, failure; SDD § 4 EX-13)*
- **CP-168:** When a save fails for a reason that is not a refusal, such as the save to disk failing, the saved data and the task stay as they were. The task's page says in plain words that the save did not happen and nothing was changed, in the content step's words, and shows no error text from Python. What was typed and chosen is still in the form, and keyboard focus is on the edit form. The console shows a message naming the action, then the error. *(FDR R-18, R-107, R-108; UXD UX-I5; SDD § 4 OB-3; NFDR QC-56, QC-57)*
- **CP-169:** A save that does not come from the tracker's own pages is refused before any action and changes nothing. That covers one marked `Sec-Fetch-Site: cross-site` or `same-site`, one not marked `same-origin`, a submission marked `none` or carrying no mark included, and one whose `Host` does not name the tracker's address. *(FDR R-110; SDD § 4 SEC-2; NFDR QC-31, QC-32)*

### What is saved

- **CP-170:** The saved form of a task and of the assignee list does not change. A saved task holds the same fields it holds today and no other, and an edit adds no field to the saved data. Saved data written before this change reads, and starts, as it does today. *(the request, "Must not be weakened or added"; SDD § 3, What the system holds; NFDR QC-46)*
- **CP-171:** An edit leaves the task's identity, its project, its status, its labels, its created instant and its comments as they were. After a stop and a start, the task shows every field as edited, and stands in the project's list where its due date and creation order put it. *(FDR R-15, R-43, R-49)*

### The code and its trace

- **CP-172:** The edit's rules live in `domain`. `application` applies them and saves, and `web` reads the form and builds the page. The checks that hold this are development-design's review of NFDR QC-21 and QC-23, which says neither `application` nor `web` owns a rule, and of QC-5's by-type half for each refusal the edit hands to `web`. Each passes for this change. *(the request; SDD § 3, the parts; § 4 TS-3, OB-4; NFDR QC-5, QC-21, QC-23)*
- **CP-173:** `domain/tasks.py`'s opening docstring names SRS FR-16 among the requirements it realizes, every `application` and `web` module that takes part in the edit, and the test modules that check it. Every new test module names the requirements or CP rules it checks. `tasks` is already a landed feature word, so the trace check's list does not change. *(SRS NFR-9; SDD § 4 TS-3, TS-4; NFDR QC-11)*
- **CP-174:** The change creates no `domain/labels.py`, and adds no way to add or remove a label, no status move, no task or project delete, no filter or sort control, no summary and no comment. *(the request, "Must not be weakened or added"; SDD § 4 EX-12)*

### Tests and the suites

- **CP-175:** The tests ship with the change:
  - Unit tests check the edit's rules in `domain` with no file and no clock. They cover CP-151 to CP-154, CP-157 to CP-160 and CP-162 to CP-165.
  - Integration tests run the tracker's whole request path in one process, as SDD § 4 TS-1 sets out. They check the form as saved, a listed assignee and none included (CP-144 to CP-147), the left-the-list control and sentence (CP-148), the project shown as text (CP-149), a four-field save and a one-field save (CP-152, CP-153, CP-155, CP-156), a save with nothing changed (CP-157), the left-the-list name kept by a save that leaves it (CP-158), and replaced by one that changes it (CP-159), each refusal of CP-161 to CP-165, the carry-over of CP-166, the missing task (CP-167), a failed save (CP-168), each origin refusal (CP-169), a task edited and then read back after a stop and a start (CP-171), and a typed title holding `<` or `&` shown as text on the task's page (FDR R-112).
  - The stale-page test loads the edit form, saves a different title through a second submission, then submits the first form with a changed title, and finds the first form's title saved and not refused (CP-154; SRS AC-19). A second stale test changes only the title from a page whose priority another tab has since changed, and finds the new title and the other tab's priority (CP-152).
  - No test patches a name inside a part. *(SDD § 4 TS-2; NFDR QC-28)*
- **CP-176:** Each refusal a save can meet, CP-161 to CP-164 and CP-167, has its own test that asserts its reason and that the saved data is the same before and after. CP-162's test sends the over-long title in a request no page of the tracker sends. *(SRS AC-12; NFDR QC-5, QC-9, QC-38; SDD § 4 RT-10)*
- **CP-177:** The checks that every route and every action meet cover the edit. The route test sends an edit save that is accepted and saved once, and asserts the redirect, the page policy header and no `Set-Cookie` (NFDR QC-7, QC-8, QC-34). The no-outbound-connection test drives an edit save (NFDR QC-35). An edit run against a tracker given a saver that records what it receives hands that saver only saves (NFDR QC-54). *(SDD § 4 RT-7, RT-8, SEC-3, SD-1)*
- **CP-178:** An end-to-end test edits a task's title to one holding `<`, `&` and `"`, and finds the task's page and the project's list showing the title exactly as typed. *(NFDR QC-36; SDD § 11 R-3)*
- **CP-179:** `python3 products/tracker17/tests/timed_run.py` loads 1,000 tasks with 20 comments each and times a field edit through the request path, and the task's page it lands on, at the text lengths the run states. Each is under 1 second, and the run fails when the edit is refused or fails. *(NFDR QC-48; SDD § 4 TS-5; SRS NFR-1, "editing")*
- **CP-180:** In a disposable copy made by `git archive HEAD` and then `git init`-ed, `pytest products/tracker17/tests/` exits 0 and `pytest products/tracker17/tests/e2e/` exits 0, with `python3 products/tracker17/tests/timed_run.py` exiting 0 as CP-179 states. Every test that passed before this change still passes, and no existing test is weakened or removed to make it pass. *(SDD § 4 TS-1, TS-5; NFDR QC-47; the request)*
- **CP-181:** From the product root, `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web` each exit 0. *(NFDR QC-62)*

---

## Examples

The assignee list holds `Dana` and `Ari`, in that order, and project `Alpha` holds task `Set up CI`, `high`, `Dana`, due 2026-10-20, in `todo`, unless a row says otherwise.

| Scenario | Expected behavior | Rule |
|---|---|---|
| Open `Set up CI`'s page | One form with Title, Priority, Assignee, Due date and Save. No status field. | CP-144 |
| Open the page of a task in `done` | The same form is there. | CP-144 |
| Read the form as it opens | Title `Set up CI`; priority offers `low`, `medium`, `high`, `critical` with `high` chosen; due date 2026-10-20. | CP-145 |
| Open the page of an undated task | The due-date field is empty. | CP-145 |
| Type into the title field past 200 characters | The field takes 200 and stops. | CP-146 |
| Open the assignee control | It offers none, `Dana`, `Ari`, with `Dana` chosen. | CP-147 |
| Open an unassigned task's page | None is chosen. | CP-147 |
| Remove `Dana` on People, then open `Set up CI` | The control shows `Dana` chosen and offers none and `Ari`. A sentence beside it says `Dana` is no longer on the list and choosing another replaces it. | CP-148 |
| Open a task assigned to `Ari` | No left-the-list sentence. | CP-148 |
| Open `Set up CI`'s page | It shows `Alpha` as text, and nothing on the page changes the project. | CP-149 |
| Open the page twice and compare the saved data | Unchanged. No move, delete, label or comment control on the page. | CP-150 |
| Submit with title `Set up CI` unchanged and priority `low` | Only the priority counts as changed. | CP-151 |
| A hand-built save carries `title=New` and no shown values | Nothing counts as changed; nothing is saved. | CP-151, CP-157 |
| Change only the priority to `low` and save | Priority `low`. Title, assignee and due date as saved. | CP-152 |
| Change all four: title ` Ship it `, `critical`, `Ari`, 2026-11-01, and save | All four saved, the title with both spaces. | CP-153 |
| Clear the due date and choose none for the assignee, and save | The task is undated and unassigned. | CP-153 |
| Tab 1 shows `low`. Tab 2 saves `high`. Tab 1 changes the priority to `medium` and saves | Accepted. Priority `medium`. | CP-154 |
| Save with a changed title | The browser lands on the task's page showing the new title and the rest as saved. A reload saves nothing. | CP-155 |
| Save with title changed to `Ship it` | One line naming `'Ship it'` with "saved changes to". Focus on the heading; the line is its accessible description. | CP-156 |
| Press Save without changing anything | Not refused. Saved data unchanged. The task's page, with no completion line. | CP-157 |
| `Dana` removed from the list; change only the title and save | Accepted. The task keeps `Dana`. | CP-158 |
| `Dana` removed from the list; change the assignee to `Ari` and save | The task carries `Ari`. The control no longer offers `Dana` and shows no sentence. A hand-built save choosing `Dana` then is refused. | CP-159 |
| Blank the title and change the priority to `low` in one save | Refused. Neither field changes. | CP-160, CP-161 |
| Blank the title, with `low`, `Ari`, 2026-11-01 chosen, and save | Refused. Focus in the title field, the reason beside it, and the blank title, `low`, `Ari`, 2026-11-01 still there. Saved data unchanged. | CP-161 |
| A hand-built save sends a 201-character title, then 201 spaces | Each refused with the too-long reason. None of the sent text is on the page or in its address; the form shows the task as saved. | CP-162 |
| Tab 1 loads the page. Tab 2 removes `Ari`. Tab 1 changes the assignee to `Ari` and saves | Refused as out of date, with a reload offered. Focus on the assignee control; the other fields as entered. Saved data unchanged. | CP-163 |
| A hand-built save changes the priority to `urgent`, then the due date to `2026-02-30` | Each refused with its reason beside its control. Saved data unchanged. | CP-164 |
| A hand-built save blanks the title and changes the priority to `urgent` | One reason, the blank title's, with focus in the title field. Nothing saved. | CP-165 |
| Change the priority to `low` and blank the title; refused; type a title and save | The new title and `low` are both saved. | CP-166 |
| Tab 1 shows `high`; tab 2 saves `medium`; tab 1 blanks the title, is refused, types a title and saves | The new title is saved and the priority stays `medium`. | CP-166 |
| A hand-built save names a task identity no task holds | The not-found page about a task. Nothing saved. | CP-167 |
| The save to disk fails while saving a changed title | The page says the save didn't happen and nothing changed, with no Python error text. The typed title is still in the form and focus is on the form. The console names the action, then the error. The task is unchanged. | CP-168 |
| An edit save marked `cross-site`, `same-site`, `none`, with no mark, or with another `Host` | Refused before any action. Saved data unchanged. | CP-169 |
| Read the saved data after an edit | The task holds the same fields as before the change. | CP-170 |
| Start on saved data written before this change | It reads, and the tasks show as saved. | CP-170 |
| Edit the title and due date, stop, start | The task shows both edits, its status, project and creation order as before, in its due-date place in the list. | CP-171 |
| Read the edit's code | Its rules are in `domain`. Development-design's QC-21, QC-23 and QC-5 review passes. | CP-172 |
| Read `domain/tasks.py`'s opening docstring | It names FR-16, the modules taking part, and the edit's test modules. The trace check passes. | CP-173 |
| `ls domain` after the change, and the task's page | No `labels.py`; no label, move, delete, filter, sort, summary or comment control. | CP-174 |
| Run the unit and integration tests | They cover every case CP-175 lists, the two stale tests included. | CP-175 |
| Run the refusal tests | One per refusal, each asserting its reason and unchanged saved data. | CP-176 |
| Run the route test and the no-outbound-connection test | Both include an edit save; it redirects with the policy header and no cookie, saves once and connects nowhere. | CP-177 |
| In a browser, edit a title to `<b>A&B</b> "Q"` | The task's page and `Alpha`'s list show `<b>A&B</b> "Q"` as text. | CP-178 |
| Run `timed_run.py` | It reports a field edit and its landing page at 1,000 tasks, each under 1 second, and exits 0. | CP-179 |
| The suites in a `git archive HEAD` copy that is `git init`-ed | Each exits 0, and no earlier test is weakened. | CP-180 |
| Ruff's format check, Ruff's lint and mypy, from the product root | Each exits 0. | CP-181 |

---

## Verified Claims

All runs below used a disposable copy made with `git archive HEAD products/tracker17` from this change's worktree at `5cd99bd71` and `git init`-ed, never the main checkout. The probes used the real `Site`, `Tracker` and `SavedData`.

| Claim | Verified by | What came back |
|---|---|---|
| Today a task's page has no form and does not show its project (CP-144, CP-149, Change Summary). | Probe: create `Alpha`, add `Dana`, add `Set up CI` / `high` / `Dana` / 2026-10-20, remove `Dana`, then `GET /tasks/1`. | 200. The `<main>` holds only `<h1>` `Set up CI` and a `<dl>` of Priority `high`, Assignee `Dana`, Due date `2026-10-20`. No `<form>`, and `Alpha` appears nowhere in it. |
| Today nothing answers a submission to a task's address (CP-155). | The same probe, `POST /tasks/1` marked `same-origin` with body `title=New`. | 404 with an empty body. |
| A task's saved fields and the saved file's keys today (CP-170). | The same probe, reading `tracker.json` back after the add. | File keys `assignees`, `next_project_id`, `next_task_id`, `projects`, `tasks`. Task keys `assignee`, `comments`, `created_at`, `due_date`, `id`, `labels`, `priority`, `project_id`, `status`, `title`. |
| The route test fails on a new submission route until it is given an accepted sample (CP-177). | A post-change tree, made by adding `Route("POST", "/tasks/[0-9]+", SUBMISSION)` to `web/routes.py` `ROUTES` in a second copy, then `python3 -m pytest -q tests/integration/test_routes.py -k every_route`. | `FAILED test_every_route_leaves_state_and_headers_as_the_rules_say`, a `KeyError` at `tests/integration/test_routes.py:298`, where `SUBMITTED_BODY` has no body for `/tasks/1`. |
| The no-outbound-connection test drives a hand-listed set of actions, so a new action is covered only when added (CP-177). | Read `tests/integration/test_routes.py:404-415`. | `test_no_socket_connection_is_made` calls `post`, `get` and `site.handle` on named addresses: project create, the assignee add and remove, and a task add. No edit. |
| `domain/tasks.py`'s docstring names FR-15 and not FR-16 today, and `tasks` is already a landed word (CP-173). | Read `domain/tasks.py:3-5` and `tests/architecture/test_trace.py:24`. | "Realizes SRS FR-15 (creating a task …), FR-39 and FR-40 …, FR-36 … and DR-2". `LANDED_FEATURE_WORDS = ["projects", "assignees", "tasks", "priorities", "due_dates"]`. |
| An add checks in the order CP-165 states. | Read `domain/tasks.py:117-126`. | The docstring says "project, title length, title blankness, priority, assignee, due date", and the code runs `find_project`, `_check_title` (length, then blank, `:85-89`), `parse_priority`, the assignee check, `parse_calendar_date`, in that order. |
| An add's landing page opens with focus on its heading and the line as its description (CP-156's "as the page that answers an add does today"). | Read `web/pages.py:475-481`. | `heading_attributes += f' autofocus aria-describedby="{_ADDED_LINE_ID}"'`, with the line in `<p class="added" id=…>`. |
| The not-found page CP-167 names exists and speaks of a task. | Read `web/pages.py:508-514`. | `task_not_found_page()` builds "There's no task at this address" with a link to Projects. |
| The baseline suite and timed run pass today (CP-180). | In the copy, `python3 -m pytest -q tests/` and `python3 tests/timed_run.py` from the product root, with the system's Python 3.14 and pytest. | `574 passed`, exit 0. The timed run exited 0, with "add a task at 1000 tasks: 28.8 ms". `pytest tests/e2e/` was not run: `python3 -c "import playwright"` gives `ModuleNotFoundError`, and the product has no `.venv` on this machine. That says nothing about the product. |
| The QC-62 gate's state today (CP-181). | `python3 -m ruff --version` and `python3 -m mypy --version` on this machine, and the last sealed change's report, `system/projects/tracker17/journey/tobiishi/trail/2026-10-11_add-and-list-tasks/code-integrity-report.md:72`. | Neither tool is installed here ("No module named ruff", "No module named mypy"), so this run could not produce the verdict. The report records "`ruff format --check .`, `ruff check .`, `mypy`, `compileall` — each exits 0" at that seal. |
| No rule pins output that renders a language-level fact. | Walked every rule. | Each pinned output is product-chosen: the priority words, the `YYYY-MM-DD` dates (CONTENT.md § Grammar and mechanics) and the content step's words. No rendering row is owed. |

---

## Out of Scope

- **Labels.** Showing, adding and removing a task's labels on its page, `domain/labels.py`, and the start-time check on a saved label belong to `task-labels`. FDR R-45's labels half waits for it.
- **The rest of UXD UX-S6.** The task's status and its moves, Delete task, and the comments list and form belong to the `status-moves`, `delete-and-rename` and `comment-on-a-task` seeds. The page shows no status, as it does today.
- **Status moves, deletes, filter and sort controls, the list across all projects, and the summary.** Those are later stations and seeds.
- **A not-found page that links to All tasks.** All tasks arrives with `narrow-and-sort`. The task not-found page keeps its one link (CP-125).
- **README § Status and `docs/what_left.md`.** Both are brought up to date after the station closes, in the `readme-status` run (`<CORE>/doctrine/setup/kensaiapp_structure.md` § The what-left file). This change edits neither.

---

## Locked Answers (the divergence record — self-review 2026-10-11)

- **Gap 1 — what the request leaves out of the form, and the refusals it does not name (CP-145, CP-147, CP-162, CP-164, CP-167 to CP-169):** stated. The request names the four fields, the blank title and the out-of-date assignee. The form's contents follow UXD UX-F9 and the add form's (CP-108, CP-109). FDR R-51, R-103, R-107 and R-110 bind every action, and a save is a new action. CP-162 is under (e), Gap 9. *(b)*
- **Gap 2 — a save with nothing changed shows no completion line (CP-157):** FDR R-116 says it changes nothing and is not refused, and says nothing about the page. UXD UX-I4's line "names what changed", and nothing did, so a line using "saved changes to" would claim a change that did not happen. Showing no line claims nothing and can be reversed without touching saved data. *(b)*
- **Gap 3 — what "the value the page showed" means across a refusal, and when a value is missing (CP-151, CP-166):** a refused or failed save keeps the values the form showed before it, and a field with a missing submitted or shown value is unchanged. A refusal reopens the form holding what was typed (UXD UX-I3). If those typed values became the new "shown" values, a change kept through the refusal would compare as unchanged and never be saved. Taking the saved values at that moment instead would overwrite another tab's value in a field the operator never touched, which breaks FDR R-47. Both points can only skip a write. Neither invents one, and both are reversible. *(b)*
- **Gap 4 — which reason shows when several changed fields are refused (CP-165):** the first in the order an add checks today. FDR R-117 fixes that nothing changes, and UXD UX-I3 puts the reason beside the control used. Using one order for the add and the edit means a field gets the same reason on both forms. *(b)*
- **Gap 5 — the completion line and where the page opens (CP-156):** one line naming the task, with focus on the heading. The request says only "redirects to the task's page showing each new value". UXD UX-I4 and SDD § 4 EX-5 confirm every completed action in one line on the page it leaves the operator on, and EX-5 opens that page at the thing acted on, which is the task. CONTENT.md fixes the verb. *(b)*
- **Gap 6 — the project shown as text, and whether it links (CP-149):** text, with the link left to development-design. UXD UX-F9 says it "shows as text and cannot be changed", and no upstream line asks for a link. *(b)*
- **Gap 7 — a replaced left-the-list name (CP-159):** the page stops offering it and a save choosing it is refused. FDR R-118 says it "cannot be set on any task again while it is off the list". UXD UX-F9 offers only listed names beside the carried one, so once the task no longer carries the name, nothing offers it. *(b)*
- **Gap 8 — a failed save, the stale-title test with another tab's priority, and a read-back after restart (CP-168, CP-171, CP-175):** stated and tested. FDR R-18 and R-107 bind every action. The request names one stale test, and FDR R-47's own example, a title change keeping another tab's priority, is the other half of CP-152. *(b)*
- **Gap 9 — the checks the records above require (CP-146, CP-162, CP-172, CP-173, CP-176, CP-177, CP-181):** stated, over the request's silence. *(e)* SDD § 4 RT-10 and NFDR QC-9 say a change that adds a text field writes its `maxlength` and a test that a longer value is refused, and the edit form's title is a new text field. SRS AC-12 with NFDR QC-5 and QC-38 has one test per refusal, each asserting unchanged saved data. NFDR QC-7, QC-8, QC-34, QC-35 and QC-54 are checked by tests that run every route or every action, and the edit is a new one. QC-7's route test fails until the new route is sampled (Verified Claims). NFDR QC-11 and SDD § 4 TS-3 have the entry module's docstring name what it realizes and the test modules name what they check. NFDR QC-62's three commands gate every change. NFDR QC-5, QC-21 and QC-23 give development-design a review for a change that adds a refusal or touches `application` or `web`. The request's "The edit and its rules live in the domain and application parts" is the behaviour those reviews hold.
- **Gap 10 — CP-124 is replaced in part:** CP-124, from `add-and-list-tasks`, said the task page "has no form and no control that changes anything". The request gives it the edit form, and CP-144 to CP-150 state the page from here on. CP-124's other lines stand: the title, "unassigned", the page title, and no status. *(b: an earlier rule this change replaces, stated so a reader of CP-124 finds what moved)*
