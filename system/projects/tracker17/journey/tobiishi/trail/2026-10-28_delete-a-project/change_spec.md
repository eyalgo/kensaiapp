# Change Spec — Delete a project with its tasks, and finish the slice's deletion contract

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing
**Request:** Let the operator delete a project, with its tasks, from its Tasks view, and finish the slice's deletion contract. A project's Tasks view offers Delete project; it opens a confirmation whose sentence names the project and its number of tasks, built on the confirmation `status-moves` and the task deletion already use (no second confirmation scheme), and holding below a list long enough to scroll: it opens in view with keyboard focus on its sentence, and a double press on its first button never confirms (SDD § 4 EX-6). Confirming deletes the project with its tasks and their comments and lands on Projects with a line naming the deleted project; the project, its tasks and their comments are in no list and cannot be read at any address (SRS FR-13, FR-17; SDD § 6 S-7). The project's own address then shows the not-found page, and an action for it sent afterwards, as from another tab, is refused and changes nothing (AC-12). The same change widens the two deletions' pending confirmations as SDD v13 and ADR-0012 state: a page showing a pending confirmation of a project deletion and one of a task deletion each answer 202 (a task deletion's answers 200 today, and `products/tracker17/tests/integration/test_delete_routes.py` asserts 200, so that test changes), the other pages of either deletion answer 200 and a deleted address 404, and every page that shows a deletion's confirmation or outcome carries `Cache-Control: no-store`, the not-found page for a deleted address carrying none (RT-11); Back to a deletion's confirmation after confirming is a fresh load (S-7 *Command*), shown by an end-to-end test. The opening docstrings of `products/tracker17/domain/projects.py` and `products/tracker17/domain/tasks.py` each name the tests the whole slice added (S-7 *Artifact*). The timed run gains a project deletion (NFDR QC-48). Tests: one that a deleted project's tasks and comments are gone, and one per deleted-target refusal asserting unchanged saved data. The task deletion's behaviour otherwise must not change, no page script or other cache workaround may stand in for the 202 (ADR-0012), no new feature module is added for the docstrings, and moving a task between projects (SRS FR-14) and changing a project's description (UXD § 10) are not part of this change; existing pages and timed actions must keep working.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, and every concern it routes read

---

## Change Summary

The operator can delete a project from its Tasks view, behind the in-place confirmation that the
move to `cancelled` and the task deletion already use. Confirming removes the project, its tasks and
their comments in one change, and lands on Projects with a line naming the project and how many
tasks went with it. Afterwards the project's addresses show the not-found page, and every action
sent for the project or one of its tasks is refused and changes nothing. The same change gives both
deletions the response policy SDD § 4 RT-11, ADR-0012 and NFDR QC-63 state. A page showing a
pending confirmation answers 202. Back after confirming loads the page afresh. It also finishes
S-7's docstring bar. The behaviour contract already states the action (`products/tracker17/docs/fdr.md`
R-37, R-38, R-103, R-105), and the product does not have it yet. The product's location is
`project.md` `Product path:`. Every product file named below is relative to it.

---

## Rules

### The control and its confirmation

- **CP-569:** A project's Tasks view offers a **Delete project** control below the list (UXD UX-F10,
  UX-S4). It shows in every state of that view: a project with tasks, a project with no tasks yet,
  and a filter that matches nothing. No other page offers a project deletion. That includes the
  Projects list, the project's Summary, a task's page and All tasks.
- **CP-570:** Pressing Delete project deletes nothing and saves nothing. It opens the project's Tasks
  view again with the in-place confirmation in that control's place. The confirmation has three
  parts, in this order:
  1. the sentence, which is one of:
     - `Delete '{name}' and its {count} tasks? You can't undo this.` when `{count}` is 2 or more;
     - `Delete '{name}' and its 1 task? You can't undo this.` when it is 1;
     - `Delete '{name}', which has no tasks? You can't undo this.` when it is 0;
  2. a confirming control labelled `Delete project`;
  3. a back-out control labelled `Back out`.

  `{name}` is the project's name as saved when that page is built. `{count}` is the number of tasks
  the project holds when that page is built. It counts every task in every status, whether or not
  the list's filter shows it. It never counts comments (CONTENT.md § Needs confirming, § Grammar
  and mechanics *Numbers*).
- **CP-571:** The Delete project confirmation behaves exactly as the move-to-`cancelled` and Delete
  task confirmations do today (UXD UX-I2; SDD § 4 EX-6, EX-8). It differs only in its words and in
  what it acts on. Each of these holds on a short page, and on a list long enough to scroll that is
  scrolled part-way when Delete project is pressed:
  - the confirmation opens in view;
  - the sentence covers the whole spot the Delete project control stood in;
  - keyboard focus is on the sentence when the confirmation opens, and never on the confirming
    control;
  - one Tab from the sentence reaches `Delete project`, and a second Tab reaches `Back out`;
  - a double press on Delete project never deletes the project;
  - every part can be reached and pressed from the keyboard alone.
- **CP-572:** The confirmation, the back-out page and the failure page of CP-578 show the project's
  list with the filter and sort choices the Tasks view carried when Delete project was pressed. They
  carry nothing else from that page's address (SDD § 4 EX-3, EX-6, "the same page").
- **CP-573:** Pressing Back out opens the Tasks view again with the Delete project control back in
  the same spot and keyboard focus on it. Nothing is saved, and no completion line is shown
  (CONTENT.md § Completed: backing out produces none).
- **CP-574:** A Tasks view address may ask for more than one deletion or move state. Then one state
  shows, in this order of precedence: a failed project deletion, then its confirmation, then its
  back-out. While any of the three shows, the page shows no move confirmation, no move outcome
  and no task-deletion completion line. The rename area and the add-task form show as their own
  address keys say. This is the precedence a task's page already gives the Delete task states over
  every move marker.

### Confirming the deletion

- **CP-575:** Pressing the confirming `Delete project` removes, in one change of the saved data,
  the project, every task it holds, and every comment on those tasks (SRS FR-13; FDR R-37).
  Nothing else changes (FDR R-38):
  - every other project, with its tasks and their comments;
  - the assignee list;
  - the operator's name;
  - the two counters that issue identities.
- **CP-576:** After a confirmed deletion, the operator lands on Projects (UXD UX-F10). The page
  opens at its start (SDD § 4 EX-5, "a different page that an action lands on"). It shows one
  completion line:
  - `You deleted '{name}' and its {count} tasks.` when `{count}` is 2 or more;
  - `You deleted '{name}' and its 1 task.` when it is 1;
  - a form saying the project had no tasks when it is 0. Its words are `CONTENT.md`'s and the
    content stage's, for example `You deleted '{name}', which had no tasks.`

  `{name}` is the project's name as it was when the deletion ran. `{count}` is the number of tasks
  the deletion removed, read when it ran. It may differ from the confirmation's count, which is the
  page's as loaded (CONTENT.md § Completed). The deleted project is not in the list. When it was the
  only project, Projects shows its no-projects state together with the line. Reloading the landing,
  or returning to it through Back or Forward, shows the same line again and changes nothing (FDR
  R-106).
- **CP-577:** A project name holding `<`, `&` or `"` shows exactly as typed, both in CP-570's
  sentence and in CP-576's line. It changes nothing around it (FDR R-112).
- **CP-578:** When the save of a confirmed deletion fails for a reason that is not a refusal:
  - the project, its tasks and their comments stay as they were, in the saved data and on every
    page;
  - the console shows a message naming the deletion of that project and the error;
  - the operator lands on the project's Tasks view, opened at the Delete project control, with a
    line saying the project could not be deleted and nothing was changed.

  This follows FDR R-107 and R-18 and SDD § 4 EX-4. The wording is `CONTENT.md`'s failure formula
  ("The tracker couldn't…").

### After the deletion

- **CP-579:** A deleted project and every task it held appear nowhere the tracker lists or counts
  projects or tasks. That covers Projects, All tasks and every filter or sort result of it, and the
  counts on any page (SRS FR-13, FR-17).
- **CP-580:** The deleted project's addresses `/projects/{id}` and `/projects/{id}/summary`, with
  any query, show the not-found page headed `There's no project at this address`, HTTP status 404.
  Each address `/tasks/{task id}` of a task it held, with any query, shows the not-found page headed
  `There's no task at this address`, 404. Neither carries a `Cache-Control` header. No comment on
  any of those tasks shows at any address (UXD UX-S10; FDR R-105; SDD § 4 EX-13, RT-11).
- **CP-581:** A deleted project's identity is never issued again. The same holds for each identity
  of the tasks it held. Both hold after the tracker is stopped and started on the same saved data
  (SDD § 3, What the system holds; ADR-0008; SRS FR-15; FDR R-44). After the operator deletes the
  project with the highest identity, the next project created gets an identity higher than every
  project identity issued before, the deleted one included.
- **CP-582:** Every submission sent after the deletion whose target is the deleted project, or a
  task it held, is refused and changes nothing. The saved data is the same before and after (FDR
  R-103; SRS NFR-3, FR-39, AC-12). Such a submission may come from a page another tab or an earlier
  load left open.
  - The rule covers a domain, not a list: every submission whose target is one project, and every
    submission whose target is one task. A submission of either kind that a later change adds falls
    under the same rule.
  - **The project's submissions today** are adding a task, the rename, and this change's two
    presses: Delete project and its confirming `Delete project`. Each shows the not-found page
    headed `There's no project at this address`, 404. Each of this change's two presses is answered
    by sending the browser to `/projects/{id}`, which shows that page (SDD § 4 RT-11, "a submission
    naming a deleted target is answered by a redirect to that address and saves nothing"). Adding
    a task and the rename keep the answer they give today (Out of Scope).
  - **The task's submissions today** are:
    - the task edit;
    - adding a label and removing one;
    - adding a comment;
    - a status move, including the first press of a move to `cancelled` and its confirming press;
    - Delete task and its confirming `Delete task`.

    Each keeps the answer the tracker already gives for a task no task holds. It is sent to
    `/tasks/{task id}`, which shows `There's no task at this address`, 404.
  - No refusal wording is added.

### The two deletions' response policy

- **CP-583:** Both deletions answer with the status and headers below. Each line is fixed by SDD § 4
  RT-11, ADR-0012 and NFDR QC-63, which state it:
  - a project's Tasks view that shows a pending Delete project confirmation answers **202**, with
    `Cache-Control: no-store`;
  - a task's page that shows a pending Delete task confirmation answers **202**, with
    `Cache-Control: no-store`. It answers 200 today;
  - these pages answer **200**, each with `Cache-Control: no-store`: each deletion's back-out page,
    each deletion's failure page, the project's Tasks view landing that names a deleted task, and
    the Projects landing that names a deleted project;
  - the status is read off the page as built. An address that asks for a deletion's confirmation
    the page does not show answers 200. One case is an address where a failure wins under CP-574,
    or under the task page's precedence;
  - the address of a deleted project or task, with any query, and an address naming an identity no
    project or task ever held, answers the not-found page, **404**, with no `Cache-Control` header,
    never 202 (CP-580);
  - no response of either deletion carries `Clear-Site-Data`, neither its submissions nor its
    confirmation, back-out, failure or landing pages;
  - no page script, cookie, session or other cache workaround is added. The 202 alone keeps a
    confirmation out of the browser's history cache (ADR-0012; ADR-0003; ADR-0011).

  Every page that shows no deletion state keeps the status and headers it has today.
- **CP-584:** After the operator confirms either deletion and lands, Back to the confirmation's
  address loads that address afresh from the saved data. It shows the not-found page of CP-580, and
  never the confirmation that offers the deletion again. Forward and Back again give the same
  result (SDD § 4 RT-11; § 6 S-7 *Command*; UXD UX-S10).
- **CP-585:** Apart from CP-583's status on its pending confirmation, the task deletion behaves
  exactly as it does today. That covers its control, its words, its confirmation, back-out, failure
  and landing, and its refusals (the request; `tracker17 · tobiishi · 2026-10-28_delete-a-task`,
  its spec's CP-529 to CP-540).

### Checks this change carries

- **CP-586:** A saved-data test (layer 2), against real files, sets up two projects. The first holds
  several tasks, in different statuses, some with comments. The second sits beside it with its own
  task and comment. The test deletes the first project through its confirming `Delete project`.
  It then reads the saved data back from disk and asserts:
  - neither the project, nor any of its tasks, nor any comment on them is there;
  - the other project with its task and comment, the assignee list, the operator's name and both
    counters are unchanged (SRS FR-13, FR-17);
  - after a start on the same saved data, a project created gets an identity that is not the
    deleted one (CP-581; NFDR QC-10).
- **CP-587:** Application-layer tests (layer 3) hold one test for each submission in CP-582's
  domain. Each test is sent after the project was deleted through its confirming `Delete project`.
  Each asserts the not-found answer CP-582 gives and saved data unchanged before and after. The
  task submissions are sent for a task the project held. This covers SRS AC-12's deleted-target
  refusal for a project and for a task another tab deleted (NFDR QC-5, QC-38).
- **CP-588:** Layer-3 tests cover the response policy (NFDR QC-63):
  - `tests/integration/test_delete_routes.py::test_live_delete_views_have_their_response_policy`
    has its `?delete_confirm` row assert 202, and keeps every other assertion it makes today;
  - a test of the project deletion asserts that the confirmation answers 202 with `no-store`, and
    that the back-out, the failure page and the Projects landing answer 200 with `no-store`;
  - the same test asserts no `Clear-Site-Data` on either press or on any of those pages;
  - each of the two presses is refused with 403 and saves nothing when it is marked `cross-site` or
    `same-site`, carries no mark, or names another host (NFDR QC-31, QC-32);
  - the deleted project's address, with no query and with a query asking for its confirmation,
    answers 404 with no `Cache-Control` header.
- **CP-589:** End-to-end tests (layer 5), in the pinned Chromium, show three things:
  - Delete project's confirmation below a list long enough to scroll, scrolled part-way. It opens
    in view with keyboard focus on its sentence, and a double press on Delete project does not
    delete the project (SDD § 4 EX-6; § 6 S-7 *Command*).
  - For the task deletion: confirm, land, then go Back to the confirmation's address. The page is
    loaded afresh and shows the not-found page, never the confirmation. The test sits beside
    `tests/e2e/test_delete_task.py::test_completion_survives_actual_reload_back_and_forward`, where
    NFDR QC-63 names it.
  - The same history test for the project deletion (CP-584; NFDR QC-63, "the project deletion's
    pages … verified by the layer-3 and layer-5 tests SDD § 6 `delete-and-rename`'s *Command* half
    adds").
- **CP-590:** `python3 tests/timed_run.py` adds a project deletion to its listed actions (NFDR
  QC-48; SDD § 4 TS-5; SRS NFR-1, "deleting").
  - The fixture is SRS NFR-1's volume, 1,000 tasks with 20 comments each, at ordinary text
    lengths. The project deleted holds tasks.
  - The run times the confirming `Delete project` submission and the Projects page it lands on,
    apart and as a total. Each must be under 1 second.
  - The run marks the submission `same-origin` (NFDR QC-32).
  - The deletion counts only when both of these hold:
    - the saved data is the fixture without that project, its tasks and their comments, and nothing
      else changed;
    - the landing shows CP-576's completion line.
  - A refused or failed deletion fails the run.
  - Every action the run timed before this change is still timed and still passes, and the run
    exits 0.
- **CP-591:** The tests that already walk every route or every action cover what this change adds:
  - the route test of NFDR QC-7 covers every address and submission this change adds. It checks
    each for QC-8 (no cookie), and for QC-33 and QC-34 (the page policy as a response header);
  - the no-outbound-connection test of NFDR QC-35 also drives a project deletion through both
    presses and its landing;
  - NFDR QC-54's read-once check covers the project deletion. A test runs one against an
    `application` built with a recording saver and asserts that the saver received only saves.
- **CP-592:** The docstrings and the trace (SDD § 6 S-7 *Artifact*; NFDR QC-11):
  - the opening docstring of `domain/projects.py` and that of `domain/tasks.py` each name every
    test module the slice `delete-and-rename` created. Today that is
    `tests/integration/test_delete_pages.py`, `tests/integration/test_delete_routes.py`,
    `tests/e2e/test_delete_task.py`, `tests/integration/test_rename_pages.py`,
    `tests/integration/test_rename_routes.py`, `tests/integration/test_rename_tracker.py` and
    `tests/e2e/test_rename_project.py`, together with every test module this change creates;
  - each docstring stays true for this change. It names the SRS requirements its module realizes
    (FR-13 in `domain/projects.py` if the project deletion rule lives there), every `application`
    and `web` module that takes part, and every test module that checks it;
  - this change adds no new feature module under `domain/` (SDD § 6 S-7 *Artifact*, "No new feature
    module");
  - the pointer test passes, and every test module this change adds names the SRS requirements or
    acceptance criteria it checks.
- **CP-593:** `ruff format --check .`, `ruff check .` and
  `mypy main.py errors.py domain application persistence web` pass, each typed from the product
  root (NFDR QC-62). `pytest tests/` and `pytest tests/e2e/` exit 0 (SDD § 6 S-7 *Command*, "Both
  suites pass").

---

## Examples

| Scenario | Expected behavior |
|---|---|
| Project `Alpha` (id 1) holds 12 tasks; the operator opens its Tasks view | Delete project shows below the list (CP-569). |
| Project `Empty` holds no tasks; its Tasks view, or Alpha's under a filter matching nothing | Delete project shows in both (CP-569). |
| The operator opens Projects, Alpha's Summary, a task's page, or All tasks | None offers a project deletion (CP-569). |
| On Alpha's Tasks view the operator presses Delete project | Same view, and in the control's place: `Delete 'Alpha' and its 12 tasks? You can't undo this.`, then `Delete project`, then `Back out`. Focus is on the sentence. Nothing is saved. The page answers 202 with `no-store` (CP-570, CP-571, CP-583). |
| Alpha holds 1 task; or `Empty` holds none; Delete project pressed | `Delete 'Alpha' and its 1 task? You can't undo this.`; `Delete 'Empty', which has no tasks? You can't undo this.` (CP-570). |
| Alpha is filtered to `status=done`, showing 3 of its 12 tasks; Delete project pressed | The sentence still says 12 tasks. The confirmation shows the list still filtered to `done` (CP-570, CP-572). |
| The confirmation is open; the operator presses Tab, Tab | Focus moves to `Delete project`, then to `Back out` (CP-571). |
| Alpha's list has 60 tasks, scrolled part-way; the operator double-clicks Delete project | The confirmation opens in view. The second click lands on the sentence, and Alpha is not deleted (CP-571, CP-589). |
| The confirmation is open; the operator presses Back out | Alpha's Tasks view with Delete project back in its spot and focus on it, the same filter and sort. No line, nothing saved. 200 with `no-store` (CP-572, CP-573, CP-583). |
| Alpha's address carries both a Delete project confirmation and a move-to-`cancelled` confirmation | Only the Delete project confirmation shows (CP-574). |
| Alpha holds 12 tasks with 40 comments; Beta holds 2; the assignee list is `Dana`; the operator confirms | Saved data holds Beta with its tasks and comments, `Dana`, the operator's name and both counters unchanged. Alpha, its 12 tasks and the 40 comments are gone. The operator lands on Projects, at its start, with `You deleted 'Alpha' and its 12 tasks.` The page answers 200 with `no-store` (CP-575, CP-576, CP-583). |
| Tab 2 adds a task to Alpha after tab 1's confirmation showed 12; tab 1 confirms | 13 tasks are deleted, and the line says `You deleted 'Alpha' and its 13 tasks.` (CP-576). |
| Alpha was the only project; the operator confirms | Projects shows its no-projects state with the completion line (CP-576). |
| The operator reloads the Projects landing | The same line shows again. Nothing changes (CP-576). |
| Project named `<b>R&D "x"</b>` is deleted | The sentence and the line show `<b>R&D "x"</b>` as typed text (CP-577). |
| The save fails when the operator confirms | Alpha with its tasks and comments is unchanged. The console names the deletion and the error. Alpha's Tasks view opens at Delete project with a line saying it couldn't be deleted and nothing was changed, the same filter and sort, 200 with `no-store` (CP-572, CP-578, CP-583). |
| Alpha deleted; the operator opens All tasks, filters it, sorts it, and opens Projects | Neither Alpha nor any of its tasks shows or is counted (CP-579). |
| Alpha deleted; the operator opens `/projects/1`, `/projects/1/summary` or `/projects/1?move_task=3&move_confirm=cancelled` | `There's no project at this address`, 404, no `Cache-Control` (CP-580, CP-583). |
| Alpha held task 3; the operator opens `/tasks/3` or `/tasks/3?delete_confirm` | `There's no task at this address`, 404, no `Cache-Control` (CP-580, CP-583). |
| Projects 1–3 exist; the operator deletes project 3, stops and starts the tracker, and creates a project | The new project is project 4, not 3 (CP-581, CP-586). |
| Tab 1 shows Alpha's Tasks view; tab 2 deletes Alpha. In tab 1 the operator adds a task, renames, presses Delete project, or confirms it | Each shows `There's no project at this address`, 404. The two Delete project presses get there by being sent to `/projects/1`. Saved data unchanged (CP-582, CP-587). |
| Tab 1 shows task 3 of Alpha; tab 2 deletes Alpha. In tab 1 the operator edits, adds or removes a label, adds a comment, presses a move, presses `cancelled` or confirms it, or presses Delete task or confirms it | Each is sent to `/tasks/3`, which shows `There's no task at this address`, 404. Saved data unchanged (CP-582, CP-587). |
| A task's page shows a pending Delete task confirmation | It answers 202 with `no-store`. Everything else about the task deletion is as today (CP-583, CP-585, CP-588). |
| A task's address carries `?delete_confirm&delete_failed` | The failure shows, 200 with `no-store` (CP-583). |
| A Delete project press marked `cross-site`, or with no mark | Refused, 403. Nothing changes (CP-588). |
| After confirming a task deletion, then a project deletion, the operator presses Back each time | Each confirmation's address loads afresh and shows the not-found page, never the confirmation (CP-584, CP-589). |
| The timed run at 1,000 tasks with 20 comments each | It deletes a project that holds tasks. The submission and the Projects landing are each under 1 second, and they count only on the exact saved delta and the completion line. Every earlier action still passes, and the run exits 0 (CP-590). |
| The route test, the no-outbound test and the read-once test run | Each covers the project deletion's addresses or the project deletion (CP-591). |
| `pytest tests/` runs with this change's tests added | The pointer test passes. Each docstring names the seven slice test modules and this change's new ones, and no new `domain/` feature module exists (CP-592). |
| The QC-62 gates and both suites run | All exit 0 (CP-593). |

---

## Verified Claims

No rule here pins output that renders a language-level fact. Every rendering a rule states is a name
the operator typed, a count, a word the product chooses or an HTTP status a record fixes, so no
language-rendering row is owed. Each claim below is about existing code.

| Claim | Verified by | What came back |
|---|---|---|
| A task deletion's pending confirmation answers 200 today, and its back-out and failure pages answer 200; all three carry `no-store` (CP-583's one changed status). | Ran a scratch probe under `/tmp`, outside the tree, against the branch at `e9c600016`. It used `web.Site` with `application.Tracker` in one process, a counting saver over a real `SavedData` and `same-origin` marks, the conditions layer 3 runs under. The state held project 1 with task 1. The project counter was at 3 and the task counter at 3, so project 2 and task 2 were issued and are held by nothing, the shape a deletion leaves. | `GET /tasks/1?delete_confirm`, `?delete_back`, `?delete_failed` and `?delete_confirm&delete_failed`: each `200`, `Cache-Control: no-store`. |
| A task's page lets a Delete task state win over every move marker, a failure before a confirmation before a back-out (the precedence CP-574 copies). | Read `products/tracker17/web/routes.py:403-411` and `:433-443`. | `# An active deletion state wins over every move marker, even one naming no task.` at :410; `_delete_area` tests `DELETE_FAILED_KEY` at :436, then `DELETE_CONFIRM_KEY` at :438, then `DELETE_BACK_KEY` at :440. |
| The task-deletion landing answers 200 with `no-store`, and a Tasks view or Projects page with no deletion state carries no `Cache-Control` (CP-583's 200 rows and its last sentence). | Same probe: `GET /projects/1?deleted_task=Set%20up%20CI`, `GET /projects/1`, `GET /`. | `200`, `no-store`; `200`, none; `200`, none. |
| An unheld project's addresses answer the project not-found page, 404, with no cache header, whatever the query (CP-580). | Same probe: `GET /projects/2`, `/projects/2?deleted_task=x&move_task=1&move_confirm=cancelled`, `/projects/2/summary`. | Each `404`, `Cache-Control` absent, heading `There's no project at this address`. |
| An unheld task's addresses answer the task not-found page, 404, with no cache header (CP-580). | Same probe: `GET /tasks/2`, `/tasks/2?delete_confirm`. | Each `404`, `Cache-Control` absent, heading `There's no task at this address`. |
| Adding a task and the rename, sent for an unheld project, answer the not-found page directly, not by a redirect, and save nothing (CP-582; the Out of Scope record gap). | Same probe: `POST /projects/2/rename` (`name=Beta`), `POST /projects/2/tasks` (`title=T`). Read `web/routes.py:805-807` and `:834-836`. | Each `404`, no `Location`, heading `There's no project at this address`. Saves unchanged. The code is `if project is None: return self._not_found_page()` at both sites. |
| A task submission for an unheld task is sent to the task's address and saves nothing (CP-582's task half). | Same probe: `POST /tasks/2/delete`. | `303`, `Location: /tasks/2`, no save. |
| No project deletion route exists today. | Same probe: `POST /projects/2/delete`, `POST /projects/2/delete/confirm`. Read `web/routes.py:124-146`, `ROUTES`. | Both `404` with an empty body. The route table holds no project deletion route. |
| Project identities come from a counter that only rises (CP-581). | Same probe: `POST /projects` (`name=Gamma`) with project 2 unheld and the counter at 3. | `303` to `/projects/3?created`. Projects held: `[(1, 'Alpha'), (3, 'Gamma')]`. Identity 2 was not reissued. |
| The task deletion's response-policy test asserts 200 for the confirmation. | Read `tests/integration/test_delete_routes.py:451-457`. | `for query in ("?delete_confirm", "?delete_back", "?delete_failed"):` … `assert shown.status == 200 and header(shown, "Cache-Control") == "no-store"`. |
| Five page tests pin the Tasks view in a way Delete project breaks. | Read `tests/integration/test_pages.py:175-194` and `:226-238`, `tests/integration/test_filter_pages.py:126-136`, `tests/integration/test_sort_pages.py:90-104`, `tests/integration/test_delete_pages.py:115-122`. | `:193-194` asserts "delete" absent from every sample page, the `project` and `created` samples among them (`:144`, `:148`). `:237-238` pins exactly two forms, `/projects/7/rename` and `/projects/7/tasks`. Filter `:133-136` and sort `:101-104` pin the empty project's forms as exactly those two. `test_no_list_row_offers_deletion` asserts `"Delete" not in shown` for `/projects/1`. |
| The route test requires its samples to equal the route set and fixes what each submission sample saves. | Read `tests/integration/test_routes.py:268-314`. | `SAMPLE_ADDRESS` at :268; `SAVES_FOR = {"/tasks/1/delete": 0}` at :307; `assert {route.pattern for route in ROUTES} == set(SAMPLE_ADDRESS)` at :314. |
| The no-outbound test drives a hand-written list of actions. | Read `tests/integration/test_routes.py:483-543`. | A literal sequence of `site.handle` and `get` calls. It ends with the task deletion and the rename and has no project deletion (CP-591). |
| The timed-run harness tests feed a fixed, ordered sequence of readings. | Read `tests/integration/test_timed_run.py:2094-2112` and `:5176-5190`. | `_run_readings` ends `*summary, *delete, *rename`. A parametrized test fails each of `["rename", "delete"]` in turn. A new timed action changes both (Locked Answer Gap 12). |
| The two docstrings each name only part of the slice's test modules today (CP-592). | Read `domain/projects.py:1-17` and `domain/tasks.py:1-26`. Ran `git diff --name-only --diff-filter=A <first parent> <merge> -- products/tracker17/tests` for the slice's two merges, `e25e527b9` (delete a task) and `1eecb6c0e` (rename). | The slice created seven modules: `test_delete_task.py`, `test_delete_pages.py` and `test_delete_routes.py` with the task deletion, and `test_rename_project.py`, `test_rename_pages.py`, `test_rename_routes.py` and `test_rename_tracker.py` with the rename. `projects.py` names the four rename modules and none of the deletion's three. `tasks.py` names the deletion's three and none of the rename's four. |
| The existing deletion history neighbour exists where QC-63 places the new test. | Read `tests/e2e/test_delete_task.py:151`. | `def test_completion_survives_actual_reload_back_and_forward(`. No test there goes Back to the confirmation after confirming. |
| The confirmation sentence, the confirming label, the completion line and its count rule are the content standard's. | Read `products/tracker17/docs/CONTENT.md:124-125`, `:305-311` and `:324-338`. | "Counts are numerals ("1 task", "12 tasks"…). A count of zero is "no" inside a sentence". "A line that reports a project deletion gives the count of tasks the action deleted, read when it ran." `"Delete 'Alpha' and its 12 tasks? You can't undo this." The confirming control reads "Delete project".` `"Delete 'Alpha', which has no tasks? You can't undo this."` `"You deleted 'Alpha' and its 12 tasks."` |

---

## Out of Scope

- Moving a task between projects (SRS FR-14; FDR R-49, OOS-9). The request rules it out.
- Changing a project's description (UXD § 10; FDR R-36, OOS-15). The request rules it out.
- Undoing a project deletion, or getting a deleted project or its tasks back. Nothing is undoable
  (UXD UX-I2).
- Deleting a project from any page but its Tasks view (CP-569).
- Any change to the task deletion beyond its confirmation's status. The request: "The task
  deletion's behaviour otherwise must not change" (CP-585).
- The answer that adding a task and the rename give for a deleted project. SDD § 4 RT-11 says "a
  submission naming a deleted target is answered by a redirect to that address and saves nothing".
  Today both answer the not-found page directly, 404, with no redirect (`web/routes.py:805-807`,
  `:834-836`; Verified Claims). This change leaves both submissions as they are. It only adds the
  data, a deleted project, that now reaches that existing refusal. The request asks only that the
  action "is refused and changes nothing", which both already do. Parked in `deferred_decisions.md`
  as a record gap.
- Bringing the records up to the built product: SDD § 4 RT-11's test list, § 11 R-12's trigger, and
  NFDR QC-63's "unmet" line and verifier list naming the tests CP-588 and CP-589 add. Those are the
  CTO's and the Principal Architect's documents.
- The exact words of CP-576's zero-task completion line and of CP-578's failure line, beyond what
  those rules fix. They are `CONTENT.md`'s and the content stage's.
- Where Delete project sits relative to the Rename area below the list, and how it looks. These are
  development-design's under `products/tracker17/docs/DESIGN.md`, which already sizes Delete
  project's first press as a full-size secondary button and its confirm strip.

---

## Locked Answers (the divergence record — self-review 2026-10-28)

- **Gap 1 — Offered in every state, on the Tasks view only (b):** CP-569 shows Delete project with
  no tasks and under a no-match filter too, and on no other page. *Reason:* UXD UX-S4 lists "the
  rename and delete controls" among the Tasks view's parts with no state condition, and CONTENT.md
  gives the no-tasks sentence. FDR R-37 sets no condition on deleting a project. UXD UX-F10 places
  the control on the Tasks view alone.
- **Gap 2 — The words (b):** CP-570, CP-573 and CP-576 state the sentence, both labels and the
  completion line. *Reason:* CONTENT.md gives the sentence for 12 tasks and for none, the `Delete
  project` label, `Back out`, and `You deleted 'Alpha' and its 12 tasks.` Its *Numbers* rule
  ("1 task", numerals) and its *Plurals are written out* rule give the one-task forms. CONTENT.md
  gives no zero-task completion line, so CP-576 leaves those words to the content stage and only
  requires that one exists.
- **Gap 3 — What the counts count (b):** the confirmation counts every task the project holds when
  the page is built, whatever the filter. The line counts what the deletion removed. *Reason:*
  CONTENT.md § Needs confirming counts "a project's tasks" and not their comments. § Completed
  says the line's count is "read when it ran" and "may be out of date" on the confirmation. UXD
  UX-F10 counts "the number of tasks that go with it", and a filter does not change which tasks go.
- **Gap 4 — The list's choices are carried (b):** CP-572 keeps the filter and sort through the
  confirmation, back-out and failure. *Reason:* SDD § 4 EX-6 says "The first press opens the same
  page", and EX-3 puts a list's choices in its address. A list that lost its filter would re-lay the
  page under the operator's second click, which is the double-press case EX-6 guards on "a list
  scrolled part-way". This differs from the rename, whose landing carries no choices
  (`tracker17 · tobiishi · 2026-10-28_rename-a-project`, its spec's Gap 3), because a rename has no
  confirmation to hold in place. It is reversible.
- **Gap 5 — One state per page (b):** CP-574 orders the Delete project states and lets them win over
  move markers. *Reason:* a page shows at most one in-place confirmation (UXD UX-I2), and an address
  can carry several keys. The order copies the one a task's page already applies to Delete task.
  The request is silent.
- **Gap 6 — A failed save (b):** CP-578 lands on the Tasks view at Delete project. *Reason:* FDR
  R-107 and R-18 bind every action, and SDD § 4 EX-4 opens a failed submission's page at the
  control used. The project still exists, so its Tasks view is that place. The task deletion lands
  the same way on the task's page.
- **Gap 7 — Identities stay retired (b):** CP-581 is not in the request. *Reason:* SDD § 3 says a
  project's identity "is never reused" and a task's "is never reused after a deletion" (SRS FR-15;
  FDR R-44). ADR-0012 rests the cacheable 404 on "an identity is never issued twice". The
  behaviour holds today (Verified Claims), so the rule asserts it for the new action and adds
  nothing to build.
- **Gap 8 — The deleted-target domain, and how the new presses answer (b):** CP-582 reaches past
  the request's "an action for it". It covers the submissions of the tasks the project held, and it
  sends the two new presses by redirect. *Reason:* SRS AC-12 tests "a project or task another tab
  deleted", and FDR R-103 binds every action on either. A deleted project's tasks are deleted tasks.
  SDD § 4 RT-11 states the redirect for a submission naming a deleted target, and the two presses
  are new, so they are built to it. The existing two project submissions keep their answer (Out of
  Scope).
- **Gap 9 — A history test for each deletion (e):** CP-589 asks for two Back-after-confirming tests
  where the request says "an end-to-end test". *Reason:* NFDR QC-63 names the task deletion's
  history test beside `test_completion_survives_actual_reload_back_and_forward` as the verifier of
  its unmet 202. It binds the project deletion's pages to "the layer-3 and layer-5 tests" S-7's
  *Command* half adds. ADR-0012 gives the project deletion's case, Back restoring a confirmation
  that offers the deletion again, as the reason the boundary covers it.
- **Gap 10 — Checks the records require (e):** CP-588's project policy test and its 403 rows,
  CP-590's conditions, CP-591, CP-592's second to fourth points and CP-593 are not in the request.
  *Reason:*
  - NFDR QC-63 is verified "clause by clause", and the project deletion's clauses are "verified by
    the layer-3 and layer-5 tests" this slice adds.
  - NFDR QC-31 and QC-32 refuse a submission not marked `same-origin` or naming another host. The
    task deletion's policy test asserts the same for its two presses.
  - NFDR QC-48 has the timed run mark every submission `same-origin` and fail on a refused or failed
    action. The exact-delta and landing-line conditions are the bar every timed action already
    meets.
  - NFDR QC-7, QC-35 and QC-54 are verified by tests that walk every route or every action.
  - NFDR QC-11 binds every change's docstrings and the pointer test.
  - NFDR QC-62's three gates and S-7's "Both suites pass" bind every change.
- **Gap 11 — How the docstring bar is read (b):** CP-592 has each docstring name every test module
  the slice created. *Reason:* the request says each docstring names "the tests the whole slice
  added". NFDR QC-11 has a docstring name "the test modules that check it", and the pointer test
  checks named paths, so a module is the unit a docstring names. "Created" bounds the set to modules
  the slice made rather than every module it touched. The modules it touched are already named
  under QC-11 where they check the feature.
- **Gap 12 — Existing tests that change (f):** these existing tests pin what this change alters, and
  they change. Each keeps asserting everything else it asserts today. The request names one of
  them, `test_live_delete_views_have_their_response_policy` (CP-588).
  - `tests/integration/test_pages.py::test_every_page_has_a_header_with_the_projects_and_people_links`.
    It admits "delete" on the `project` and `created` samples. It keeps asserting the header's three
    links, every link's address, "rename" absent, and "delete" absent from every other sample.
  - `tests/integration/test_pages.py::test_a_project_page_shows_name_description_the_invitation_and_only_the_add_form`.
    It admits Delete project among the forms. It keeps asserting the heading, the description, the
    invitation, the add form and its fields, the rename form, and no textarea and no table.
  - `tests/integration/test_filter_pages.py::test_empty_project_retains_first_task_page_without_filters`
    and `tests/integration/test_sort_pages.py::test_an_empty_project_has_no_controls_even_with_malformed_sort_choices`.
    They admit Delete project among the empty project's `post` forms. They keep asserting no table,
    the no-tasks invitation, and no filter or sort control.
  - `tests/integration/test_delete_pages.py::test_no_list_row_offers_deletion`. It admits the Delete
    project control on `/projects/1`. It keeps asserting that no row of the project's list and no
    row of All tasks carries a delete form, and that All tasks shows no "Delete".
  - `tests/integration/test_routes.py::test_every_route_leaves_state_and_headers_as_the_rules_say`.
    It gains samples for the addresses this change adds, and a saves entry for any press that saves
    nothing. It keeps asserting that a page request changes nothing, that a submission redirects,
    that no cookie is set, and that the policy is on every response.
  - `tests/integration/test_routes.py::test_no_socket_connection_is_made`. It gains the project
    deletion and its landing, and keeps every action it drives today.
  - The `tests/integration/test_timed_run.py` tests that drive the whole run through `_run_readings`
    or a fixed reading sequence, those that list the run's labels in order, and the parametrized
    failing-action test. They gain the project deletion's readings, label and failure case, and keep
    asserting each earlier action's verdict and the run's exit status.
  - Any other test that pins the Tasks view's full set of forms, buttons or words admits the Delete
    project area and keeps asserting the rest. Development-design names any it finds.

  *Reason:* the request asks for the control, the action and the timed deletion. NFDR QC-7, QC-35,
  QC-48 and QC-63 require the route coverage, the timing and the 202. None of these can be met with
  these tests unchanged.
