# Change Spec — a deleted project's Add task and Rename answer by redirect, and the deletion count comes only from the application

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing
**Request:** Make a submission for a deleted project answer the way a deleted task's submissions already do. When an Add task or a Rename is sent for a project that has been deleted (as from another tab after the deletion), the application redirects to that project's address, `/projects/<id>`, which shows the not-found page (404), and saves nothing; today both answer the not-found page directly (SDD § 4 RT-11). This covers both the case where the project is already gone when the form arrives and the case where it disappears between the check and the save. Also remove the one place `web` owns a count: `project_page` in `products/tracker17/web/pages.py` falls back to `len(rows)` when called without a listing, so Delete project's confirmation takes its task count only from the application's answer (SDD § 3). Tests: one per submission (Add task, Rename) asserting the redirect status and its location and that the saved projects and tasks are identical before and after, each failing on `main` today; and one showing Delete project's confirmation sentence carries the count the application answered, not the count of rows shown. `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/` must both exit 0. A deleted task's submissions, the not-found page itself and its lack of a cache header (RT-11) must stay as walked; no page's wording changes; `web` gains no counting of its own and `application` gains nothing beyond handing the count over. Deleting a task's confirmation size, moving tasks between projects (SRS FR-14) and changing a project's description (UXD § 10) are not part of this change.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, and every concern it routes read; no line fixes the rendering of anything a rule below pins

---

## Change Summary

Add task and Rename sent for a project the tracker no longer holds stop answering the not-found page
directly and instead redirect to that project's address, which shows the not-found page — the answer
SDD § 4 RT-11 gives every submission naming a deleted target, and the one a deleted task's
submissions already give. Delete project's confirmation takes its task count only from the
application's answer, because the one place `web` counts rows itself goes.

Paths below are relative to the product root, which `system/projects/tracker17/project.md`
`Product path:` names.

---

## Rules

### A — Add task and Rename for a project the tracker does not hold

- **CP-594:** An Add task submission, `POST /projects/<id>/tasks`, whose `<id>` the tracker reads as
  a project identity that no project holds when the action runs, is answered with HTTP status `303`
  and the header `Location: /projects/<n>`, where `<n>` is that identity written in decimal with no
  leading zeros and nothing follows it — no query. Nothing is saved: the saved data, its projects and
  its tasks are identical before and after, and no save is made. This holds whatever the form
  carries.
- **CP-595:** A Rename submission, `POST /projects/<id>/rename`, under the same condition is answered
  the same way as CP-594: `303`, `Location: /projects/<n>`, no query, nothing saved, whatever the
  form carries.
- **CP-596:** The condition in CP-594 and CP-595 covers both ways the project can be missing: it is
  already gone when the submission arrives, and the tracker reports it gone when the action itself
  runs. Both get the same answer. Neither ever answers the not-found page directly.
- **CP-597:** A missing project wins over every refusal of the form's values. A Rename whose name is
  blank, already in use or too long, and an Add task whose title is blank, whose priority is not one
  of the four, whose assignee is not on the list, whose due date is not a date, or whose text is too
  long, sent for a missing project, gets CP-594's or CP-595's answer. The `Location` carries no
  refusal, no failure and none of the typed text.
- **CP-598:** The `<id>`s CP-594 and CP-595 cover are every number in the route the tracker reads as
  an identity: a project deleted (as from another tab), and an identity no project was ever given,
  such as `99` or `0`, alike. `/projects/00/tasks` is answered with `Location: /projects/0`. The one
  `<id>` the route admits and the tracker does not read as an identity — a number too long to read,
  such as 5,000 nines — is outside this change (see `## Out of Scope`).
- **CP-599:** Following the redirect, `GET /projects/<n>` for a project no project holds answers the
  existing not-found page, the page headed `There's no project at this address`, with status `404`
  and no `Cache-Control` header (NFDR QC-63; SDD § 4 RT-11). The page and its wording do not change.

### B — Delete project's confirmation count

- **CP-600:** Delete project's confirmation sentence states the number of tasks the application
  answers for the project — every task the project holds, in every status — and never the number of
  rows the page shows, in every state the page can be in: unfiltered, filtered, sorted, with no
  match, or refused. The sentence keeps its three present forms: `Delete '<name>', which has no
  tasks? You can't undo this.`, `Delete '<name>' and its 1 task? You can't undo this.` and
  `Delete '<name>' and its <count> tasks? You can't undo this.`
- **CP-601:** `web` counts nothing to fill the sentence. The defect this removes is at
  `web/pages.py:2037`, `task_count = listing.task_count if listing is not None else len(rows)`,
  whose fallback counts the rows shown — against SDD § 3, where `web` must not own "what a count
  is", and NFDR QC-23's no-rule half. After the change,
  `git grep -n 'len(rows)' -- products/tracker17/web/pages.py`, run from the change worktree's
  root, prints no line inside `project_page`.

### C — Tests the change adds

- **CP-602:** One test per submission — Add task and Rename — deletes a project through its
  confirmation, then sends that submission for it, and asserts status `303`, `Location:
  /projects/<n>`, and that the saved projects and tasks are identical before and after. Each test
  fails on `main` at `443ee2179`, where both submissions answer `404` with no `Location`. These are
  the deleted-target refusals SRS AC-12 asks to be tested for a project another tab deleted.
- **CP-603:** One test shows Delete project's confirmation sentence carrying the count the
  application answered on a page that shows fewer rows than the project holds — a filter that
  leaves some of the project's tasks off the list — so a count of rows shown and the application's
  count differ, and the sentence states the application's.
- **CP-604:** `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/`, each
  run from the change worktree's root, both exit `0`.

### D — Checks the records above the change require of it

- **CP-605:** Both redirects of CP-594 and CP-595 are built by the one function in `web` that builds
  every address a submission is answered with, and the route test that checks every submission is
  answered by a redirect, `tests/integration/test_routes.py`,
  `test_every_route_leaves_state_and_headers_as_the_rules_say`, passes (NFDR QC-7; ADR-0011).
- **CP-606:** The code passes the three gates NFDR QC-62 names, each exiting `0` from the product
  root: `ruff format --check .`, `ruff check .`, and
  `mypy main.py errors.py domain application persistence web`, at the versions `pyproject.toml`
  pins (NFDR QC-62).
- **CP-607:** Every test module the change adds names the requirements or acceptance criteria it
  checks, and is named in the opening docstring of `domain/projects.py`, and the pointer test in
  `tests/architecture/test_trace.py` passes (NFDR QC-11; SDD § 6 S-7, *Artifact*).
- **CP-608:** Because the change touches `web`, it takes the three reviews at `development-design`
  the NFDR assigns a change to `web`: that `web` keeps nothing between requests (NFDR QC-8, its
  keeps-nothing half), that `web` owns no rule — which here includes no count (NFDR QC-23, its
  no-rule half) — and that the change adds no part no requirement pays for (NFDR QC-12).

---

## Examples

| Scenario | Expected behavior |
|---|---|
| Project 1 is deleted through its confirmation; Add task `title=Late` is then sent to `/projects/1/tasks` (CP-594, CP-602) | `303`, `Location: /projects/1`; saved data, projects and tasks unchanged; no save made |
| Project 1 is deleted; Rename `name=Renamed` is then sent to `/projects/1/rename` (CP-595, CP-602) | `303`, `Location: /projects/1`; nothing saved |
| The browser follows either redirect: `GET /projects/1` (CP-599) | `404`, the page headed `There's no project at this address`, no `Cache-Control` header |
| The tracker reports project 1 gone only when the Add task or Rename action runs, after the submission found it (CP-596) | Same answer as the row above it: `303`, `Location: /projects/1`, nothing saved — never the not-found page directly |
| Rename with `name=` (blank), with a name another project holds, or with 201 characters, to a deleted project (CP-597) | `303`, `Location: /projects/1` — no `rename_refused`, no `rename_typed`, no refusal shown |
| Add task with a blank title, `priority=bogus`, an unlisted assignee, `due_date=nope`, or a 201-character title, to a deleted project (CP-597) | `303`, `Location: /projects/1` — no `task_refused`, none of the typed fields in the address |
| Add task to `/projects/99/tasks` and Rename to `/projects/0/rename`, identities no project was ever given (CP-598) | `303`, `Location: /projects/99` and `Location: /projects/0`; nothing saved |
| Add task to `/projects/00/tasks` (CP-598) | `303`, `Location: /projects/0` |
| Project "Alpha" holds 4 tasks, one per status; its page is opened with Delete project's confirmation and `filter_status=done`, which shows 1 row (CP-600, CP-603) | `Delete 'Alpha' and its 4 tasks? You can't undo this.` |
| Same project, filter `filter_label=nothing`, no row shown (CP-600) | `Delete 'Alpha' and its 4 tasks? You can't undo this.` |
| A project with no tasks, confirmation open (CP-600) | `Delete 'Empty', which has no tasks? You can't undo this.` |
| `git grep -n 'len(rows)' -- products/tracker17/web/pages.py` after the change (CP-601) | No line inside `project_page` |
| The two suites after the change (CP-604) | Both exit `0` |
| The route test over every submission (CP-605) | Passes; each submission, Add task and Rename included, is answered by a redirect |
| The QC-62 gates (CP-606) | Each of the three commands exits `0` |
| A new test module checking the Projects feature (CP-607) | It names its requirements, `domain/projects.py`'s opening docstring names it, and the pointer test passes |

CP-608 has no row: it is a review at `development-design`, which no scenario's output shows.

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| Today Add task and Rename for a project no project holds answer the not-found page directly, `404`, no `Location`, nothing saved | Ran, in the change worktree at `443ee2179`, a probe on the real `Site` built by `tests/integration/test_task_routes.py`'s `make_world`: `POST /projects/00/tasks`, `/projects/99/tasks`, `/projects/<5000 nines>/tasks`; and ran `test_rename_routes.py::test_a_missing_rename_project_answers_404_without_saving`, `test_task_routes.py::test_a_missing_project_post_gets_project_not_found_and_saves_nothing`, `test_delete_project_routes.py::test_deleted_project_submission_changes_nothing` | Each Add task: `404`, `Location` none. The three tests pass (24 passed in the run that held them), each asserting the direct `404` and nothing saved |
| Both paths answer the not-found page directly today: the check before the action and the action's own report | Read `web/routes.py:869-870` and `:898-899` (`if project is None: return self._not_found_page()`), `:877-878` and `:910-911` (`except ProjectNotFound: return self._not_found_page()`) | As claimed |
| A deleted task's submissions redirect to `/tasks/<n>`, with leading zeros dropped, and an unreadable number answers `404` directly | Same probe: `POST /tasks/00`, `/tasks/99`, `/tasks/<5000 nines>` as edits; ran `test_delete_project_routes.py::test_deleted_child_submission_changes_nothing`, `test_task_routes.py::test_task_edit_missing_identity_uses_task_not_found` | `303 /tasks/0`, `303 /tasks/99`, `404`; both tests pass |
| Delete project's own presses on a project no project holds already redirect to `/projects/<n>` | Same probe: `POST /projects/00/delete` | `303`, `Location: /projects/0` |
| `GET /projects/<n>` for a project no project holds answers `404` with no `Cache-Control` | Same probe: `GET /projects/99` | `404`, no `Cache-Control` header |
| The `len(rows)` fallback sits in `project_page` | `git -C <worktree> grep -n 'len(rows)' -- products/tracker17/web/pages.py`; read `web/pages.py:1941-2047` | One line, `2037: task_count = listing.task_count if listing is not None else len(rows)`, inside `project_page` (starts at `:1941`) |
| The application already answers the project's task count | Read `application/tracker.py:91` (`task_count: int` on the listing it returns) and `:362`, `:378` | As claimed; `web/routes.py`'s `_project_page` hands that listing to `project_page` |
| The confirmation's count already follows the whole project through the real `Site` | Ran `test_delete_project_pages.py::test_project_confirmation_counts_all_current_tasks` | Passes for 4, 1 and 0 tasks under `filter_status=done` and `filter_label=nothing` |
| No existing page-level test builds a project page with a deletion area and no listing, so removing the fallback contradicts no assertion | `grep -rn -A12 'project_page(' products/tracker17/tests --include='*.py' \| grep -c 'delete_area'` | `0` |
| `domain/projects.py`'s opening docstring lists the Projects feature's test modules | Read `domain/projects.py:1-26` | Lines 14-25 list them |
| No rule pins output rendering a language-level fact | Walked every rule against SKILL.md Step 2's definition | The statuses, addresses, page and sentences are all product-chosen; no rendering row is owed |

The QC-62 gates were not run: neither `ruff` nor `mypy` is installed on the machine this spec was
written on. CP-606 states what must pass, and claims nothing about the tree today.

---

## Out of Scope

- An Add task or Rename whose `<id>` is a number too long for the tracker to read as an identity,
  such as 5,000 nines. NFDR QC-7 and ADR-0011 say every submission is answered by sending the browser
  to a page address. Today these two answer the not-found page directly (`web/routes.py:869-870` and
  `:898-899`, reached when `_identity` at `:402-407` reads no identity), as a task's submissions do
  for the same kind of number (`web/routes.py:931-933`). Such a number never names a deleted project,
  and the request asks only about deleted projects. This spec states no rule on it either way.
  Handed on in `deferred_decisions.md`.
- A deleted task's submissions, the not-found page, its wording, and the fact that it carries no
  cache header — all stay as walked (SDD § 4 RT-11).
- The wording of every page and line. The redirect lands on the existing not-found page.
- Add task and Rename for a project that exists: their success, refusals, failure page and the
  check every request passes first are unchanged.
- Delete project's own two presses for a missing project, which already redirect.
- Any new capability in `application`. It already answers the project's task count.
- Delete task's confirmation size (seed `delete-and-rename`, item 5).
- Moving a task to another project (SRS FR-14), and changing a project's description (UXD § 10).

---

## Locked Answers (the divergence record — self-review 2026-10-28)

- **Gap 1 — the redirect's status (b):** `303`. The request says "redirects" and leaves the status
  open. `303` is what a deleted task's submissions, Delete project's presses and every other
  submission answer with (Verified Claims), and the request asks for "the way a deleted task's
  submissions already do".
- **Gap 2 — the `Location`'s shape (b):** `/projects/<n>`, the number in decimal with no leading
  zeros, and nothing after it. The request writes `/projects/<id>`. A deleted task's edit sent to
  `/tasks/00` lands on `/tasks/0`, and a bare address carries none of what was typed to a page that
  cannot show it.
- **Gap 3 — an identity no project was ever given (b):** it gets the same redirect as a deleted one.
  The request speaks of a deleted project. The not-found page the operator sees is the same either
  way, a deleted task's submissions treat an identity no task was given the same way (`/tasks/99`
  answers `303 /tasks/99`), and Delete project's presses already do.
- **Gap 4 — the missing project against refusals of the typed values (b):** the missing project wins.
  It wins today, through the direct `404` — the existing Rename test asserts it "even for an invalid
  name". A refusal of a name or title is meaningless for a project that does not exist.
- **Gap 5 — checks the records require (e):** CP-605 (NFDR QC-7, ADR-0011), CP-606 (QC-62), CP-607
  (QC-11, SDD § 6 S-7) and CP-608 (the `development-design` reviews of QC-8, QC-12 and QC-23) are
  stated, though the request names only the two suites. Each binds a change that touches `web`, or
  that adds a test module, and this one does.
- **Gap 6 — existing tests named as changing (f):** each asserts the direct `404` that CP-594 and
  CP-595 replace, so neither rule can be met while it stands as written. The request asks for the
  redirect.
  - `tests/integration/test_rename_routes.py`, `test_a_missing_rename_project_answers_404_without_saving`:
    its `absent` (`99`) and `zero` (`0`) cases move to the redirect of CP-595. It keeps asserting that
    nothing is saved and no refusal wording is shown for blank, valid and too-long names. Its `huge`
    case is outside this change and keeps its assertion as it stands.
  - `tests/integration/test_task_routes.py`, `test_a_missing_project_post_gets_project_not_found_and_saves_nothing`:
    the same split for Add task, CP-594. It keeps asserting that nothing is saved.
  - `tests/integration/test_delete_project_routes.py`, `test_deleted_project_submission_changes_nothing`:
    its `add-task` and `rename` cases move from the direct `404` to `Location: /projects/1`, after
    which `GET /projects/1` shows the not-found page with no `Cache-Control` — the branch its other
    three cases already take. It keeps asserting that nothing is saved in every case.

  CP-558, which answered a Rename for such an identity with the not-found page directly, is
  superseded in that one respect by CP-595 and CP-598. CP-582 and CP-587 stand as written: the
  submission is still refused and changes nothing, and the not-found answer is now reached through
  the redirect.
