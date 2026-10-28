# Change Spec — Delete a task from its page

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing
**Request:** Let the operator delete a task from its page. Delete task on a task's page opens the in-place confirmation (the existing `confirm_strip`), and confirming removes the task together with its comments, then lands on the task's project with a line naming the deleted task (SDD § 6 S-7; UXD UX-F9, UX-S6). The deleted task is in no list of its project or of all projects, and its address shows the not-found page (UX-S10). A comment-add, edit or status move sent for it from another tab is refused through the existing refusal path and changes nothing in the saved data (AC-12). A deleted task's identity is never issued again (FR-15), so after deleting the task with the highest identity the next task added gets a new one, and its comments are gone from the saved data (FR-17). The timed run gains a task delete (NFDR QC-48). Tests: a layer-3 test per deleted-target refusal of AC-12 for a task, each asserting unchanged saved data, and a test that the identity is not reissued. The existing confirmation mechanism and refusal wording must not be duplicated or replaced. Renaming a project, deleting a project, the `domain/projects.py` / `domain/tasks.py` docstring bar, and moving a task to another project (SRS FR-14) are not part of this change, and existing pages and timed actions must keep working.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened

---

## Change Summary

The operator can delete a task from its page, behind the same in-place confirmation a move to
`cancelled` already uses. Deleting removes the task and its comments in one change, lands on the
task's project with a line naming it, retires its identity for good, and every later action sent for
it is refused with the not-found page the tracker already gives for a task no task holds. The
product's behaviour contract already states this action (`products/tracker17/docs/fdr.md` R-50,
R-44, R-103, R-105). The product does not have it yet. The product's location is `project.md`
`Product path:`. Every product file named below is relative to it.

---

## Rules

### The control and its confirmation

- **CP-529:** A task's page offers a **Delete task** control, whatever the task's status: `todo`,
  `in-progress`, `done` and `cancelled` all show it (UXD UX-S6; FDR R-50). No other page offers a
  task deletion: no row of a project's Tasks view and no row of All tasks.
- **CP-530:** Pressing Delete task deletes nothing and saves nothing. It opens the task's page again
  with the in-place confirmation in that control's place. The confirmation has three parts, in this
  order:
  1. the sentence `Delete '{title}'? You can't undo this.`;
  2. a confirming control labelled `Delete task`;
  3. a back-out control labelled `Back out`.

  `{title}` is the task's title as saved when that page is built (CONTENT.md § Needs confirming).
- **CP-531:** The delete confirmation behaves exactly as the move-to-`cancelled` confirmation does
  today (UXD UX-I2; SDD § 4 EX-6, EX-8):
  - the sentence covers the whole spot the Delete task control stood in;
  - when the confirmation opens, keyboard focus is on the sentence and never on the confirming
    control;
  - one Tab from the sentence reaches the confirming control, and a second Tab reaches Back out;
  - a double press on Delete task never deletes the task;
  - every part can be reached and pressed from the keyboard alone.

  It differs from that confirmation only in its words and in what it acts on.
- **CP-532:** Pressing Back out opens the task's page again with the Delete task control back in the
  same spot and keyboard focus on it. Nothing is saved, and no completion line is shown (CONTENT.md
  § Completed: backing out produces none).

### Confirming the deletion

- **CP-533:** Pressing the confirming `Delete task` removes the task and every comment on it, in one
  change of the saved data (FDR R-50; SRS FR-17). Nothing else changes: every other task and its
  comments, every project, the assignee list and the operator's name, and the counters that issue
  identities.
- **CP-534:** After a confirmed deletion, the operator lands on the deleted task's project's Tasks
  view (UXD UX-S4), with no filter or sort chosen. The page opens at its start (SDD § 4 EX-5, "a
  different page that an action lands on"). It shows the one completion line `You deleted '{title}'.`,
  where `{title}` is the deleted task's title as it was when the deletion ran (CONTENT.md
  § Completed; UXD UX-F9). Reloading that page, or returning to it through Back or Forward, shows the
  same line again and changes nothing (FDR R-106; PD-11).
- **CP-535:** A title holding `<`, `&` or `"` shows exactly as typed, both in CP-530's sentence and in
  CP-534's line. It changes nothing around it (FDR R-112).
- **CP-536:** When the save of a confirmed deletion fails for a reason that is not a refusal:
  - the task and its comments stay as they were, in the saved data and on every page;
  - the console shows a message naming the deletion of that task and the error;
  - the operator lands on the task's page, opened at the Delete task control, with a line saying the
    task could not be deleted and nothing was changed.

  This follows FDR R-107 and R-18 and SDD § 4 EX-4. The wording is CONTENT.md's.

### After the deletion

- **CP-537:** A deleted task appears nowhere the tracker lists or counts tasks. It is not in its
  project's Tasks view, not in All tasks, and not in any filter or sort result of either. It is not
  counted anywhere in its project's Summary: the total, the status, priority, overdue and
  no-due-date counts, and the per-assignee rows all leave it out (FDR R-81, R-96, R-97).
- **CP-538:** The deleted task's address `/tasks/{id}` shows the not-found page, headed
  `There's no task at this address`, with HTTP status 404 (UXD UX-S10; FDR R-105). This holds for
  that address with any query, including one that asks for a pending confirmation, whether the move
  to `cancelled` or the deletion.
- **CP-539:** A deleted task's identity is never issued again, including after the tracker is stopped
  and started again on the same saved data (SRS FR-15; FDR R-44). After the operator deletes the task
  with the highest identity, the next task added gets an identity higher than every identity issued
  before, the deleted one included.
- **CP-540:** Every submission sent for a deleted task is refused and changes nothing. The submission
  may come from a page another tab or an earlier load left open. It lands on the not-found page of
  CP-538 at that task's address, and the saved data is the same before and after (FDR R-103; SRS
  NFR-3, FR-39, AC-12).
  - The rule covers a domain, not a list: every submission whose target is one task.
  - Today that domain is the task edit, adding a label, removing a label, adding a comment, a status
    move (the first press of a move to `cancelled` and its confirming press included), and the two
    presses this change adds, Delete task and its confirming `Delete task`.
  - A task submission a later change adds falls under the same rule.
  - The refusal is the one the tracker already gives for a task identity no task holds. It adds no
    refusal wording.

### Checks this change carries

- **CP-541:** The integration-layer (layer 3) tests hold one test for each submission in CP-540's
  domain. Each test is sent for a task that was deleted through the confirming `Delete task`. Each
  asserts the not-found landing and saved data unchanged before and after. This covers SRS AC-12's
  deleted-target refusal for a task. NFDR QC-5 and QC-38 are verified by these tests, one per
  refusal.
- **CP-542:** A saved-data layer (layer 2) test, against real files, runs this sequence (NFDR QC-10):
  1. delete the task with the highest identity;
  2. start again on the same saved data;
  3. add a task;
  4. assert that the new task's identity is not the deleted one.

  The same saved data, read back after the deletion, holds neither the deleted task nor any of its
  comments, and holds every other task with its comments unchanged (SRS FR-17).
- **CP-543:** `python3 tests/timed_run.py` adds a task deletion to its listed actions (NFDR QC-48;
  SDD § 4 TS-5; SRS NFR-1, "deleting"). The fixture is SRS NFR-1's volume, 1,000 tasks with 20
  comments each, at ordinary text lengths. The run times the confirming `Delete task` submission and
  the page it lands on, apart and as a total. Each must be under 1 second. The run marks the
  submission `same-origin` (NFDR QC-32). The deletion counts only when both of these hold:
  - the saved data is the fixture without that task and its comments, and nothing else changed;
  - the landing page shows CP-534's completion line.

  A refused or failed deletion fails the run. Every action the run timed before this change is still
  timed and still passes. The run exits 0.
- **CP-544:** The tests that already walk every route or every action cover what this change adds:
  - the route test of NFDR QC-7 covers every address and submission this change adds, and it
    checks them for QC-8 (no cookie) and QC-33 and QC-34 (the page policy as a response header);
  - the no-outbound-connection test of NFDR QC-35 also drives a task deletion through both presses
    and its landing.
- **CP-545:** This change also meets NFDR QC-11:
  - the pointer test passes;
  - every test module this change adds names the SRS requirements or acceptance criteria it checks;
  - the Tasks feature's entry module `domain/tasks.py` keeps its opening docstring true for this
    change. It names the SRS requirements it now realizes (FR-17 among them, if the deletion rule
    lives there), every `application` and `web` module that takes part, and every test module that
    checks it.

---

## Examples

| Scenario | Expected behavior |
|---|---|
| Task 7 `Set up CI` in `done`; the operator opens its page | The page shows Delete task (CP-529). |
| On task 7's page the operator presses Delete task | Same page; in the control's place: `Delete 'Set up CI'? You can't undo this.`, then `Delete task`, then `Back out`. Focus is on the sentence. Nothing is saved (CP-530, CP-531). |
| The confirmation is open; the operator presses Tab, Tab | Focus moves to `Delete task`, then to `Back out` (CP-531). |
| The operator double-clicks Delete task | The confirmation opens. The second click lands on the sentence, and the task is not deleted (CP-531). |
| The confirmation is open; the operator presses Back out | Task 7's page, Delete task back in its spot with focus on it. No line, nothing saved (CP-532). |
| Task 7 in project `Alpha` (id 1) has 3 comments; the operator confirms | Saved data holds neither task 7 nor its 3 comments, and every other task and comment is unchanged. The operator lands on Alpha's Tasks view, at its start, unfiltered, with `You deleted 'Set up CI'.` (CP-533, CP-534). |
| The operator reloads that landing page | The same line shows again. Nothing changes (CP-534). |
| Task 7 was Alpha's only task; the operator confirms | Alpha's Tasks view shows the no-tasks state that invites a first task, with `You deleted 'Set up CI'.` (CP-534, CP-537). |
| Task titled `<b>Fix & ship</b>` is deleted | The sentence reads `Delete '<b>Fix & ship</b>'? You can't undo this.` and the line `You deleted '<b>Fix & ship</b>'.`, both shown as typed text (CP-535). |
| The save fails when the operator confirms | Task 7 and its comments are unchanged. The console names the deletion and the error. The operator lands on task 7's page at Delete task, with a line saying it could not be deleted and nothing was changed (CP-536). |
| Task 7 deleted; the operator opens All tasks, filters Alpha by status `done`, and opens Alpha's Summary | Task 7 is in neither list. The Summary's total and every count leave it out (CP-537). |
| Task 7 deleted; the operator opens `/tasks/7` or `/tasks/7?move_task=7&move_confirm=cancelled` | The not-found page, `There's no task at this address`, 404 (CP-538). |
| Tasks 1–5 exist; the operator deletes task 5, stops and starts the tracker, and adds a task | The new task is task 6, not task 5 (CP-539, CP-542). |
| Tab 1 shows task 7. Tab 2 deletes it. In tab 1 the operator saves an edit, adds a label, removes a label, adds a comment, presses a move, presses `cancelled` or confirms it, or presses Delete task or confirms it | Each lands on task 7's not-found page, and the saved data is unchanged (CP-540, CP-541). |
| The timed run at 1,000 tasks with 20 comments each | It deletes one task through the confirming submission and its landing, each under 1 second. It counts only on the exact saved delta and the completion line, and exits 0 (CP-543). |
| The route test and the no-outbound test run | Both cover the new delete addresses and the delete action (CP-544). |
| `pytest tests/` runs with this change's tests added | The pointer test passes. Each new test module names what it checks. `domain/tasks.py`'s docstring is true for this change (CP-545). |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| Every submission that targets a task identity no task holds is refused today through one path. It is answered by a redirect to `/tasks/{id}`, which shows the not-found page, and it saves nothing (the existing refusal path CP-540 reuses). | Ran a scratch probe (outside the tree, under `/tmp`) against the product at branch commit `da84a0857`. It used `web.Site` with `application.Tracker` in one process, a recording saver and `same-origin` marks, the conditions layer 3 runs under. The state held project 1, task 1, and a task counter at 3, so identity 2 was issued and is held by no task, the shape a deletion leaves. The probe sent each task submission for `/tasks/2`. | Each of the following answered `303` to `/tasks/2`, whose landing was `404` headed `There's no task at this address`, with 0 saves: edit, label add, label remove, comment add, move to `done`, move to `cancelled` first press, move to `cancelled` confirm. |
| A confirmation address for a task no task holds answers the not-found page (CP-538). | Same probe: `GET /tasks/2` and `GET /tasks/2?move_task=2&move_confirm=cancelled`. | Both `404`, headed `There's no task at this address`. |
| A task added after the counter has passed an unheld identity gets a new one (CP-539 rests on identities coming from a counter that only rises). | Same probe: `POST /projects/1/tasks` on the state above. | `303` to `/tasks/3?added`. The saved tasks were `[1, 3]`, so identity 2 was not reissued. |
| The task's page offers no delete control today, and three tests pin its full set of forms or the absence of the word "delete" on it. | Read `products/tracker17/tests/integration/test_task_pages.py:282-327` (`test_task_page_shows_the_four_fields_in_the_one_authorized_form`, form list at :314, `"delete"` absent at :325) and `:405-430` (`test_task_page_opens_edit_form_from_saved_values`, form list per status at :426). Read `products/tracker17/tests/integration/test_comment_pages.py:427-448` (`test_written_comments_offer_no_edit_delete_or_reply_control`, form list at :434, `"delete"` absent at :447). | As stated. Locked Answer Gap 12 names them. |
| The route test requires its sample set to equal the route set, and every submission sample to be accepted and saved once. | Read `products/tracker17/tests/integration/test_routes.py:303-334`. | `assert {route.pattern for route in ROUTES} == set(SAMPLE_ADDRESS)` at :306; `assert len(saver.saved) == before[3] + 1` at :334. |
| The no-outbound test drives a hand-written list of actions, not the route table. | Read `products/tracker17/tests/integration/test_routes.py:455-490`. | A literal sequence of `site.handle` and `get` calls. A new action is covered only when it is added there (CP-544). |
| The timed-run harness tests feed the whole run a fixed, ordered sequence of timer readings, one block per timed action. | Read `products/tracker17/tests/integration/test_timed_run.py:2084-2094` (`_run_readings`) and `:715-736`. | The order is fixed as `("comment", "assignee add", "assignee remove", "move", "filter", "sort")`, then the Summary. A new timed action changes that sequence (Locked Answer Gap 12). |
| The confirmation sentence, the confirming label and the completion verb are the content standard's. | Read `products/tracker17/docs/CONTENT.md:303-333`. | `"Delete 'Set up CI'? You can't undo this." The confirming control reads "Delete task".` The back-out control is always "Back out". The completed formula uses the verb "deleted". |

---

## Out of Scope

- Renaming a project, and deleting a project. The request: "Renaming a project, deleting a project
  … are not part of this change". They are items 2 and 3 of the same seed.
- S-7's slice-level artifact bar, that the opening docstrings of `domain/projects.py` and
  `domain/tasks.py` name every test the slice adds (SDD § 6 S-7, *Artifact*). The request: "the
  `domain/projects.py` / `domain/tasks.py` docstring bar … are not part of this change". This
  leaves out only that bar. The NFDR QC-11 check stays in for what this change itself adds (CP-545).
- Moving a task to another project (SRS FR-14; FDR R-49, OOS-9). The request rules it out too.
- Undoing a deletion, or getting a deleted task back. Nothing is undoable (UXD UX-I2).
- Deleting a task from a list row, or from All tasks (CP-529).
- Deleting or editing a single comment (FDR R-74). A comment goes only with its task.
- What a return through Back or Forward to a delete confirmation shows after the task is deleted
  (Locked Answer Gap 6).
- The HTTP caching of the delete confirmation page and of the deleted task's not-found answer. SDD
  § 4 RT-11 says whether the HTTP cache may keep that 404 is decided by the slice that makes a task
  deletable, `delete-and-rename`. This spec fixes only what the operator sees (CP-538). That is
  development-design's to settle. A deleted identity is never reissued (CP-539), so a not-found
  answer for its address never goes out of date.

---

## Locked Answers (the divergence record — self-review 2026-10-28)

- **Gap 1 — Delete is offered in every status (b):** CP-529 shows Delete task on a `done` or
  `cancelled` task too. *Reason:* FDR R-50 sets no status condition on deleting a task. UXD UX-S6
  lists Delete task among the task page's parts with no status condition. A final status bars only
  further moves (FDR R-54).
- **Gap 2 — The words (b):** CP-530 and CP-534 state the confirmation sentence, the two control
  labels and the completion line. They are not left implicit. *Reason:* CONTENT.md gives these exact
  strings for a task deletion (§ Needs confirming, the `Set up CI` example) and fixes the verb
  "deleted" (§ Completed). Stating them makes the rules testable from the page alone. The failure
  line of CP-536 is left to CONTENT.md's failure formula, because CONTENT.md gives no task-deletion
  example for it.
- **Gap 3 — Where the deletion lands (b):** CP-534 lands on the project's Tasks view with no filter
  or sort chosen, opened at its start. *Reason:* the request and UXD UX-F9 say only "lands on the
  task's project". The press is made on the task's page, which carries no list choices, so there are
  none to carry. SDD § 4 EX-5 opens a page an action lands on, when it is not the page the form was
  on, at its start.
- **Gap 4 — A failed save (b):** CP-536 lands on the task's page at the Delete task control and
  keeps the task. *Reason:* FDR R-107 and R-18 bind every action, this new one included: nothing
  changes, the console names the action and the error, and the browser says it failed. SDD § 4 EX-4
  opens the page answering a failed submission at the control used. The task still exists, so its
  page is that place.
- **Gap 5 — The deleted-target refusal covers every task submission (b):** CP-540 and CP-541 reach
  past the request's three examples, the comment add, the edit and the status move. They also cover
  label add and remove, both presses of a move to `cancelled`, and both presses of the deletion
  itself. *Reason:* FDR R-103 binds every action on a task that no longer exists, and SRS AC-12 asks
  for one test per refusal. Naming only three of the task's submissions would leave the rest of the
  domain undecided. The behaviour already holds for every one of them (Verified Claims, row 1), so
  each extra test is an assertion and not a new rule. A second Delete task sent from a stale tab is
  the case this change itself adds.
- **Gap 6 — No rule on history after a deletion (b):** no rule pins what Back or Forward to a delete
  confirmation shows once the task is gone. *Reason:* the history guarantee of SDD § 4 RT-11 and
  NFDR QC-63 is stated for the move to `cancelled` alone. S-7's "Both confirmations behave as the one
  in `status-moves` does" cites § 4 EX-6, the in-place behaviour CP-531 states. Whatever page
  history shows, any press from it is refused by CP-540 and changes nothing.
- **Gap 7 — Lists and the Summary (b):** CP-537 names the Summary and filter results as well as the
  two lists. *Reason:* the request says "in no list". A deleted task still counted in the Summary
  would contradict FDR R-96's "total number of tasks" for that project. Leaving it out is the only
  reading consistent with removal.
- **Gap 8 — The identity test is a restart test at layer 2 (e):** CP-542 sets the request's "a test
  that the identity is not reissued" as delete, restart on the same saved data, then add. *Reason:*
  NFDR QC-10 states that test: "layer 2, a test that deletes a task, restarts on the same saved data
  and creates a task, and asserts the deleted identity is not issued again".
- **Gap 9 — Route-wide tests cover the new action (e):** CP-544 is not in the request. *Reason:* NFDR
  QC-7 verifies through a route test that walks every route. QC-35 verifies through a test that
  "drives every action through `web`". Both bind the addresses and the action this change adds.
- **Gap 10 — QC-11 stays in although the request names "the docstring bar" (e):** CP-545 states NFDR
  QC-11 for what this change adds. *Reason:* QC-11 is a check the NFDR requires of every change, so
  it applies even where the request excludes it. The request's exclusion is read as S-7's slice
  artifact bar, which Out of Scope keeps out.
- **Gap 11 — The timed run's conditions (e):** CP-543 adds conditions to the request's "the timed run
  gains a task delete". The run marks the submission `same-origin`, fails on a refusal or a failure,
  and counts only on the exact saved delta. *Reason:* NFDR QC-48 requires the timed run to mark
  every submission `same-origin` (QC-32) and to fail when a timed action is refused or fails. The
  exact-delta and landing-line conditions match the bar every action timed before this change
  already meets.
- **Gap 12 — Existing tests that change (f):** these existing tests pin what this change alters, and
  they change. Each keeps asserting everything else it asserts today.
  - `tests/integration/test_task_pages.py::test_task_page_shows_the_four_fields_in_the_one_authorized_form`
    and `::test_task_page_opens_edit_form_from_saved_values`. Wherever they pin the task page's full
    set of forms, or that "delete" is absent from it, they admit CP-529's control. They keep
    asserting the edit form, its fields, the move, label and comment forms in their order, and the
    absence of "overdue".
  - `tests/integration/test_comment_pages.py::test_written_comments_offer_no_edit_delete_or_reply_control`.
    It admits the task-level Delete task in the page's forms and text. It keeps asserting that no
    written comment carries any control, and that no "reply" or "edit comment" appears.
  - `tests/integration/test_routes.py::test_every_route_leaves_state_and_headers_as_the_rules_say`.
    It gains samples for the addresses this change adds. It keeps asserting that a page request
    changes nothing, a submission redirects, no cookie is set, and the policy is on every response.
    Whether a first press is a submission at all is development-design's.
  - The `tests/integration/test_timed_run.py` tests that drive the whole run through `_run_readings`
    or a fixed reading sequence. They gain the deletion's readings. They keep asserting each earlier
    action's verdict and the run's exit status.

  *Reason:* the request asks for the control, the action and the timed deletion. NFDR QC-48 requires
  the timed deletion, and QC-7 the route coverage. None of these can be met with these tests
  unchanged.
