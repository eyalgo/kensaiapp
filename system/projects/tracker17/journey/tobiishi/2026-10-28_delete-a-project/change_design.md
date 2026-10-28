# Change Design — Delete a project and complete the deletion response contract

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — Delete project on a project's Tasks view, its confirmation and failure line, the completion line on Projects, and the console message for a failed project deletion

---

## 1. Change Summary

This document owns the module boundaries, interfaces and test coverage for
`tracker17 · tobiishi · 2026-10-28_delete-a-project`.
The behaviour remains defined by `change_spec.md` § Rules, CP-569–CP-593.
Add the project deletion rule to `domain`, save its single resulting state through `application`,
and expose the two presses and the shared confirmation through `web`.
Extend the timed harness with a separate project-deletion measurement.
The task deletion changes only its pending confirmation's response status, as specified by
`change_spec.md:148-175` (CP-583–CP-585).

All product paths below are relative to `products/tracker17/`.
The action artifact belongs beside the spec under the change-unit home in
`<CORE>/doctrine/setup/kensaiapp_structure.md:2189-2196` (§ 2, `journey/tobiishi/<key>/`).

---

## 2. Blast Radius

Placement follows `docs/SDD.md:199-230` (§ 3, The parts and The seams).
The module set and permitted dependencies are `docs/nfdr.md:161-192` (§ 1.2).

| Module | Status | What changes |
|---|---|---|
| `domain/` | Modified | The **domain** part owns project existence checks, the cascade, the count removed, and the immutable outcome. Add them to `projects.py` and re-export the public names from `__init__.py`. Update `projects.py` and `tasks.py` opening trace docstrings. No new feature module. |
| `application/` | Modified | The **application** part owns applying the deletion to the current state, saving once before publishing, returning the deletion outcome, and exposing it through `__init__.py`. Add the action to `tracker.py`. The existing project-list read supplies the unfiltered confirmation count. |
| `web/` | Modified | The **web** part owns the new routes, address encoding, resolved presentation state, page status/headers, failure reporting and UI. Change `routes.py`, `pages.py` and `style.css`. Reuse `confirm_strip`; add the full-size project trigger/strip context. |
| `persistence/` | Unchanged | The whole-state saving contract and saved shape remain unchanged. Prove the cascade by reading real files through the existing adapter. |
| `main.py` | Unchanged | Existing wiring supplies the same tracker, saver and listener. |
| `errors.py` | Unchanged | Reuse `ProjectNotFound`; no new refusal condition. |
| `tests/timed_run.py` | Modified | The test harness owns measurement and its independent expected saved delta, landing check and final verdict. This is test code, not a sixth product part. |

The new public names are additive. `persistence` imports `domain` but consumes no changed constructor
or state shape, so its production call sites need no change; `main` likewise keeps its existing
construction calls (`application/tracker.py:110-118`, § Tracker, and `domain/state.py:18-33`, § TrackerState).
The affected downstream production caller of the new action is `web`; its callers in
`web/listener.py` still consume the existing `Response` shape (`web/routes.py:97-104`, § Response).
No forbidden import is needed. Test changes are enumerated in § 5.

---

## 3. Sub-jobs

### Sub-job A — `domain/`: one cascade and one outcome

**Scope:** Implement the project deletion in `domain/projects.py`, with its public re-exports.
Complete the two feature-entry docstrings under CP-592.

**Exposes:**

- `ProjectDeletionOutcome`, an immutable value carrying `project: Project` as removed and
  `task_count: int` as the number actually removed.
- `delete_project(state: TrackerState, project_id: int) -> tuple[TrackerState, ProjectDeletionOutcome]`.
  A missing project raises the existing `ProjectNotFound` before any result is produced.
  A held project, including an empty one, yields one changed state and an outcome.
- The new state removes exactly the identified project and tasks whose `project_id` equals its
  identity. Task removal also removes the comments held inside those tasks, by the entity structure
  in `domain/tasks.py:72-85` (§ Task).
- Every surviving value keeps its value and sequence position. Neither identity counter changes.
  The returned project name and task count come from the state supplied to this call.

The rule does not call the per-task deletion action repeatedly.
The state and outcome are built together so CP-575's single change and CP-576's actual removed
count hold by construction, rather than by trusting form fields or an earlier confirmation.

Both opening docstrings name the seven slice-created modules listed by `change_spec.md:237-251`
(CP-592), plus the four new modules fixed in § 5: `test_delete_project_tracker.py`,
`test_delete_project_pages.py`, `test_delete_project_routes.py` and `test_delete_project.py`, with
their full test paths. Each retains its other valid trace pointers and names the participating
application/web modules and requirements. `projects.py` adds FR-13; no domain feature module is added.

**Depends on:** none.

### Sub-job B — `application/`: save before reporting deletion

**Scope:** Add `Tracker.delete_project(project_id: int) -> ProjectDeletionOutcome` and export the
outcome through `application/__init__.py` for the web boundary.

**Exposes:** One call invokes A against the tracker state held now, saves the returned whole state
once through the unchanged Saver, and only then publishes it and returns the outcome.
A typed refusal or a saver exception propagates while the old state remains current.
There is no count, cascade rule or state comparison in this layer.

For the confirmation, `Tracker.project_task_list(...).task_count` is the existing whole-project
count, including a refused/no-match selection (`application/tracker.py:76-99`, § ProjectTaskList,
and `application/tracker.py:334-375`, § _read_list). Web receives that value; it does not count visible rows.

**Depends on:** A, for the rule and outcome.

### Sub-job C — `web/`: project deletion and both deletion response policies

**Scope:** Add the project interaction and landing, keeping business decisions behind B.
Change the task deletion's pending status at the existing response seam.

**Exposes — addresses and form values:**

| Request | Answer |
|---|---|
| `POST /projects/{id}/delete` | Held target: 303 to its Tasks view with `project_delete_confirm` and carried filter/sort choices. No save. Missing target: 303 to the bare project address. |
| `POST /projects/{id}/delete/confirm` | Call B once. Success: 303 to Projects with `deleted_project` holding the removed name and `deleted_project_tasks` holding the removed count as a nonnegative decimal. Missing target: 303 to the bare project address. Save failure: 303 to its Tasks view with `project_delete_failed` and carried choices. |
| Back out, a GET form to `/projects/{id}` | `project_delete_back` and carried choices. No save or completion. |

Only the route chooses the project. Neither press accepts a project identity, name or count from
the form as authority. Only filter/sort pairs are carried, using the existing repeated-value
representation (`web/routes.py:227-247`, § _carried_filters and _carried_sorts).
Blank and repeated values remain intact. Unrelated outcome, rename, move and add-form keys are
not copied into these generated addresses. All POST redirects use `_address` through the existing
redirect path (`web/routes.py:156-166`, § _address).

**Exposes — resolved page state:**

- Resolve project deletion states as failure, confirmation, back-out, ordinary, by key presence.
  Reuse `DeleteMode`/`DeleteArea` as presentation values and the existing `confirm_strip`, not a
  second confirmation component (`web/pages.py:247-266`, § DeleteMode/DeleteArea, and `:761-787`,
  § confirm_strip).
- Resolve an active project deletion before consulting move markers or a `deleted_task` line.
  None of those markers renders or creates a missing-task answer while the project deletion wins.
  The project's existence check precedes every state resolution.
- A confirmation uses the current `Project.name` and the whole-project `task_count` handed in by B.
  Its confirm and back-out forms carry the same choices as its opening form.
- Place the Delete project section after the list/results and before Rename, in ordinary, empty,
  no-match and refused-list states. Rename stays last, preserving
  `tests/integration/test_rename_pages.py:83-108` (§ test_every_tasks_view_state_has_the_rename_area).
- Use the full-size secondary trigger and a full-size strip context derived from DESIGN's
  control-height token, without changing the existing task/move strip contexts
  (`docs/DESIGN.md:450-469`, § Components).
- The sentence covers the first button's spot and owns the sole autofocus on confirmation.
  Back-out/failure gives that autofocus to Delete project; the failure line describes that button.
  Simultaneous rename/add-form markers retain their own displayed data/lines under CP-574, but
  surrender autofocus to the active project deletion. With no active project deletion, existing
  focus precedence remains unchanged. No focus is put on the confirming button on arrival.
- Projects receives a plain deletion-completion value decoded from the two landing keys. The
  name is retained exactly and the count admits zero. An incomplete or malformed pair is ignored
  as an unrecognized outcome. No name/count is reconstructed from a deleted entity or from the
  new project list. A recognized completion gives the Projects heading autofocus and its line as
  the accessible description, at the start of the page, including the no-projects state.
- Every inserted name and completed sentence passes through `_escape`; confirmation uses the
  escaping already in `confirm_strip` (`web/pages.py:761-787`, § confirm_strip).
  Published wording follows `change_spec.md` CP-570, CP-576 and CP-578 and the change's text record.
  No additional refusal wording is introduced.

**Exposes — responses and failures:**

Compute pending status from the resolved state passed to page building: 202 iff a deletion
confirmation actually renders, otherwise 200 for a live deletion interaction/outcome.
Extend the existing pending-status seam for resolved deletion state, retaining its existing move
call contract. Use the same resolution for body and status. A failed state beats a confirmation
flag, so it remains 200. Task confirmation alone becomes 202; its other content and behaviour
remain unchanged (`change_spec.md:148-175`, CP-583–CP-585).

Each rendered project deletion confirmation, back-out and failure carries `no-store`; the recognized
Projects completion does too. Existing task deletion cache handling stays in place.
Missing project/task addresses return their existing 404 before any deletion/move policy is applied,
with no cache header, whatever the query. Other ordinary pages retain their existing policy.
Neither new submission adds `Clear-Site-Data`, cookies or a cache workaround.
Both new routes remain `SUBMISSION` entries behind the existing Host and Fetch-Site check
(`web/routes.py:296-318`, § Site.handle).

Use the existing `_guarded` failure site for the action and error on the console.
Its browser failure outcome carries choices but no raw exception, and B leaves the old state
current (`docs/nfdr.md:494-508`, § 7, QC-56/QC-57).
Adding a task and renaming a deleted project retain their direct 404 responses, per
`change_spec.md:129-144` (CP-582) and § Out of Scope; the pre-existing record gap stays in
`deferred_decisions.md`.

**Depends on:** B for the delete action and outcome; the existing project-list read for the count.

### Sub-job D — `tests/timed_run.py`: measure a real project deletion

**Scope:** Add one project-deletion block after the existing rename block, on its own saved-data
location and full-volume fixture, preserving every earlier block and its relative order.

**Exposes:** Three distinct labelled readings: confirming POST, Projects landing GET and the sum
of those intervals. Each is strictly below one second. Open the confirmation before timing.
The confirming POST is `same-origin`. Build the expected state independently from the loaded
fixture, removing only the target project and its tasks; never call the production deletion rule
to produce the oracle. Read back disk outside the intervals and check exact equality, including
other projects, comments, names and counters. The landing must be the Projects page, 200, showing
the removed name and actual task count in the completion line. A refused/failed opening,
confirmation, incorrect delta or incorrect landing makes the run fail. The sum passes only if
both readings pass. Fixture reporting states the actual volume and ordinary text lengths.

The unchanged measurements already separate action/landing timing from readback work
(`tests/timed_run.py:1452-1506`, § measure_task_delete); reuse the measurement structure without
using production deletion logic as the oracle.

**Depends on:** C for the new routes and landing contract.

**Build sequence:** A → B → C → D. This follows the production import direction, with the test
harness outside it. This is the order of the functional contracts, not a requirement that all
of A's documentation land before B. A's trace completion has a file-existence dependency on the
four new test modules belonging to B/C. A docstring naming one of those paths cannot pass the
pointer check while that path is absent (`tests/architecture/test_trace.py:57-58,108-112`,
§ missing_paths and test_every_path_named_in_the_entry_docstring_exists).
New APIs are additive, so no cross-module atomic-landing edge is required for those APIs.
Within C, body/status resolution is one coherent response change; no green point exists between
rendering a pending deletion confirmation and assigning that same resolved confirmation its 202,
because CP-583 requires them together.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — `domain/` | Derive the cascade and count from the same supplied state; one replacement preserves all unaffected fields and both counters. Keep runtime imports acyclic: `tasks.py` already imports `projects.py`, so the project rule must not add the reverse runtime dependency (`domain/tasks.py:42-45`, § imports). |
| B — `application/` | None |
| C — `web/` | Reuse `confirm_strip` and its sentence-covering grid. Add only a project full-size context; its padding/coverage must account for the two full-size controls, including bottom-of-page scroll clamping. Resolve deletion precedence once for body, autofocus and status. |
| D — `tests/timed_run.py` | Use an independent fixture and exact-state oracle; exclude fixture/readback work from measured intervals, and retain the existing injected timer seam. |

There is no write outside the instance/product worktree in this design.

---

## 5. Test Additions

Rows T1–T22 define the delta; layers are `docs/nfdr.md:542-579` (§ 9).
The four new test modules are fixed by T2, T4, T8 and T16 below.

| Row / sub-job | Test file | What to add / modify |
|---|---|---|
| T1 / A, layer 1 | `tests/unit/test_projects.py` | Cascade for zero, one and many tasks, all four statuses, comments, two projects, exact survivors and their order, assignees/operator/counters unchanged; input immutable; missing project raises `ProjectNotFound`; outcome name/count reflect the call's state. CP-575, CP-576, CP-581, CP-582. |
| T2 / B, layer 3 | **New** `tests/integration/test_delete_project_tracker.py` | Action returns A's outcome only after one save; capture candidate state and verify publication follows saving. Refusal performs no save. A failing saver leaves every read at the old state. Add a task and rename between confirmation read and confirm; removed name/count come from confirm time. Recording saver receives saves only, covering QC-54. CP-575, CP-576, CP-578, CP-591. |
| T3 / A+B+C, layer 2 | `tests/integration/test_saved_data.py` | Real saved file: delete through the confirming route with multiple statuses/comments and a second project/task/comment; read disk and compare the exact expected state. Restart with that data, create project and task, and prove both counters retire the highest deleted identities. Repeat with the only project and with an empty project. CP-575, CP-579, CP-581, CP-586. |
| T4 / C, layer 4 | **New** `tests/integration/test_delete_project_pages.py` | Trigger after list and before Rename in ordinary/empty/no-match/refused-filter/refused-sort views. No project trigger on Projects, Summary, task page or All tasks, and none on list rows. First press: ordered sentence/confirm/back-out using the shared strip; zero/one/many sentences and current name; total count despite status/label filters. CP-569–CP-571. |
| T5 / C, layer 4 | `tests/integration/test_delete_project_pages.py` | Whole filter/sort pairs, repeated and blank values, survive first press, confirm form, back-out and failure; unrelated address keys are dropped by generated forms/redirects. CP-572. |
| T6 / C, layer 4 | `tests/integration/test_delete_project_pages.py` | Back-out has no completion and focuses the restored trigger. Failure focuses the trigger described by its reason. Pair/triple combinations of failure/confirmation/back-out render exactly the winning mode; every move marker and deleted-task line is suppressed, including a missing move task. CP-573, CP-574. |
| T7 / C, layer 4 | `tests/integration/test_delete_project_pages.py` | Combined rename/add-form state retains its own display with exactly one deletion-owned focus. Projects completion opens on heading with accessible description and no focused line; zero/one/many counts, only-project empty state, and ordinary/malformed landing markers. Hostile name `<b>R&D "x"</b>` shows as text in sentence and completion with no injected element/attribute. CP-574, CP-576, CP-577. |
| T8 / C, layer 3 | **New** `tests/integration/test_delete_project_routes.py` | First POST redirects to confirmation and saves nothing; confirm saves once, redirects to Projects using action outcome, and drops carried choices from this different-page landing. Form-forged id/name/count cannot choose target or completion. Reloading landing changes nothing. Confirm after intervening task add/project rename reports fresh count/name. CP-570, CP-575, CP-576. |
| T9 / C, layer 3 | `tests/integration/test_delete_project_routes.py` | Saver failure leaves saved bytes and every current project/task/comment page unchanged; console names project/action/error once; browser has the failure wording and no exception/traceback; filter/sort retained. CP-578. |
| T10 / C, layer 3 | `tests/integration/test_delete_project_routes.py` | After cascade, Projects/All tasks and filtered/sorted counts/results contain no deleted project/task; surviving project's Summary and comments unaffected. Every deleted project Tasks/Summary URL and child task URL, bare and with deletion/move/rename/comment queries, answers correct 404, no cache header and no deleted comment. Include never-held identities. CP-579, CP-580, CP-583. |
| T11 / C, layer 3 | `tests/integration/test_delete_project_routes.py` | One independently reported case per deleted-project submission: add task, rename, first Delete project, confirm. Delete the project through confirm before each case; assert saved bytes unchanged and exact CP-582 response (direct 404 for first two; 303 then 404 for new two). Include repeated confirming press. CP-582, CP-587. |
| T12 / C, layer 3 | `tests/integration/test_delete_project_routes.py` | One independently reported case per deleted-child submission: edit; add label; remove label; add comment; ordinary move; opening cancellation; confirming cancellation; opening Delete task; confirming Delete task. Each begins with real project deletion, then proves 303 to child address, 404 and unchanged saved bytes. Task-not-found wins even over invalid submitted values. CP-582, CP-587. |
| T13 / C, layer 3 | `tests/integration/test_delete_project_routes.py` | Response matrix: shown project confirmation 202/no-store, back-out/failure/Projects completion 200/no-store, failure+confirmation 200/no-store, ordinary pages unchanged, missing targets 404/no cache even with confirmation query. No Clear-Site-Data on either POST or any state/landing. Both routes refuse cross-site, same-site, none, absent mark and foreign Host with 403 and unchanged bytes. CP-583, CP-588. |
| T14 / C, layer 3 | `tests/integration/test_delete_routes.py` | Change only the confirmation row of `test_live_delete_views_have_their_response_policy` to 202. Add/retain failure+confirmation precedence at 200. Keep every back-out/failure/landing, missing/never-held, save and no-Clear-Site-Data assertion. CP-583, CP-585, CP-588. |
| T15 / C, layer 3/4 | `tests/integration/test_delete_pages.py` | Also change `test_delete_first_press_opens_confirmation_without_saving`'s confirmation expectation from 200 to 202 (`:124-145`). Keep all markup/focus/no-save assertions. Narrow `test_no_list_row_offers_deletion` to task-row deletion and absence of project deletion on All tasks, admitting the new project section. CP-583, CP-585. |
| T16 / C, layer 5 | **New** `tests/e2e/test_delete_project.py` | Keyboard-only first press, sentence focused/in view, Tab to confirm then Back out, back-out restores focus, keyboard confirm. Cover short/empty page and 60-task list scrolled part-way; real double-click at original trigger coordinates never deletes, including near page bottom and a long name. Full-size trigger/sentence/confirm and full-size back-out meet DESIGN; no scripts. CP-571, CP-573, CP-589. |
| T17 / C, layer 5 | `tests/e2e/test_delete_project.py` | Confirm project deletion, verify heading/line/absence, actual reload and Back/Forward preserve landing line without another save. Using `history_page`, Back to confirmation after confirming issues a fresh request and gives 404; Forward and Back again do likewise. Assert actual pinned browser version. Hostile project name remains typed text. CP-576, CP-577, CP-584, CP-589. |
| T18 / C, layer 5 | `tests/e2e/test_delete_task.py` | Add `test_confirmation_is_loaded_afresh_after_confirming` beside `test_completion_survives_actual_reload_back_and_forward`; drive `history_page`, assert pinned browser, actual requests and 404 on Back to confirmation, then Forward/Back. Keep the existing task golden paths. CP-584, CP-585, CP-589. |
| T19 / C, layer 3/4 | `tests/integration/test_pages.py`, `test_filter_pages.py`, `test_sort_pages.py` | Update the page-shape assertions assigned here from the spec's Locked Answer Gap 12: project/created samples admit Delete project; empty view form sets gain its POST. Keep header links, fields, rename, no table on empty state and no filter/sort there. Existing rename-last and move-focus tests remain unchanged. CP-569, CP-593. |
| T20 / C, layer 3 | `tests/integration/test_routes.py` | Add both routes to exhaustive samples and the first press's zero-save count; keep no-cookie/CSP/redirect/read-immutability assertions. Extend `test_no_socket_connection_is_made` with both presses and landing while retaining earlier actions. T2 covers QC-54. CP-591. |
| T21 / D | `tests/integration/test_timed_run.py` | Test new full-volume project measurement, same-origin mark, exact cascade oracle, POST/landing/total intervals strictly below 1 second, and failed/refused opening/confirm, wrong delta/name/count/landing and slow intervals failing the final exit. Fixture/readback stay outside intervals. Extend `_run_readings`, fixed clock sequences, label-order expectations and failing-action parametrization with the new final block, retaining every earlier verdict. CP-590. |
| T22 / A–D, layer 6 and product gates | `tests/architecture/test_trace.py` and the existing architecture suite | Add a trace-completeness assertion that each feature docstring names the seven slice-created plus four newly created test modules specified by CP-592 and this design. Keep existing pointer/SRS/participant/test-header checks. Existing module/import checks prove no new feature part. Run the CP-593 Ruff, mypy and both suite commands from the product root, and CP-590's timed run. No architecture rule is weakened. CP-592, CP-593. |

**Examples pass.** Number the spec's Examples rows in source order, 1–30
(`change_spec.md:260-290`, § Examples). Coverage is:

| Examples | Rows |
|---|---|
| 1–3: location and page states | T4, T19 |
| 4–6: first press, singular/zero, filtered count | T4, T5, T8, T13 |
| 7–8: Tab order and far-list double click | T16 |
| 9–10: back-out and competing move state | T5, T6, T13, T16 |
| 11–14: cascade, changed count, last project, reload | T1–T3, T7–T8, T17 |
| 15–16: hostile name and failed save | T7, T9, T17 |
| 17–20: absent lists/addresses and retired identities | T3, T10 |
| 21–22: project and child stale submissions | T11, T12 |
| 23–25: task confirmation, failure precedence, origin refusal | T13–T15 |
| 26: both deletion history paths | T17, T18 |
| 27: timed run | T21 |
| 28: exhaustive route/no-outbound/read-once checks | T2, T20 |
| 29–30: slice pointers and product gates | T22 |

**Rules pass.** CP-569–CP-574 are covered by T4–T7/T16/T19; CP-575–CP-578 by
T1–T3/T7–T9/T17; CP-579–CP-582 by T1/T3/T10–T12; CP-583–CP-585 by
T13–T18; CP-586–CP-593 by T2/T3/T11–T22.
These include the rule-implied edges: empty deletion, all statuses, zero-task completion,
current-time name/count, failed saves, each stale-target action, both retired counters after restart,
mixed query precedence, malformed/blank/repeated choices, missing/never-held targets, and exact
one-second rejection. No example or rule-implied failure path is left to an unnamed test.

**Assertions retired.** T14 and T15 replace the obsolete task-confirmation 200 assertion with
202 while preserving their remaining clauses. T15/T19 replace whole-project-page “no deletion”
and exact-two-form assertions with the specified project section while continuing to prove no
task-row deletion and no project deletion on other pages. T20 replaces the old exhaustive route
set with the enlarged set. T21 enlarges reading/label sequences while continuing to prove every
earlier action, order and failure verdict. No other assertion is retired.

---

## Records this change makes false

- `docs/nfdr.md:109-120` (§ 1.1 QC-63) — the live claim “The task deletion's 202 is unmet” becomes
  false. Replace that build-state claim with the actual verifiers: the revised task response-policy
  row, `tests/e2e/test_delete_task.py::test_confirmation_is_loaded_afresh_after_confirming`, and
  the new project response/history tests in T13/T17. Keep QC-63's obligation intact.
- `docs/SDD.md:468-477` (§ 4 RT-11, Tests) — the deletion history test “does not exist at
  `4a9ff47d2`” remains true as dated evidence, but its live forward pointer must name the task
  history test above and `tests/e2e/test_delete_project.py`'s project history test. The line handing
  the deletion record/obligation to the Principal Architect should point to Accepted ADR-0012 and
  QC-63, rather than describe that handoff as remaining work.
- `docs/SDD.md:1559-1570` (§ 11 R-12) — “the deletion history test ... once it exists” becomes a
  stale live trigger; name both concrete deletion history tests alongside the move history tests.

Read `docs/fdr.md` (§ Rules and Product decisions), `docs/SDD.md` § 3 and
`docs/adr/README.md` with ADR-0001–ADR-0012 (Accepted records binding; ADR-0006/ADR-0010
superseded). No behaviour, part, import edge, schema, or Accepted ADR decision becomes false.
The existing project-submission redirect gap is unchanged, not caused by this change, and remains
in `deferred_decisions.md`.

---

## Architect Review Notes

Decisions and stage-delegated reviews below are the Architect's, 2026-10-28.

1. **Placement and actual counts (b).** A owns one cascade and its removed count. B passes the
   outcome through after saving. Confirmation uses the domain-backed whole-project count, not
   visible rows. This realizes CP-570/CP-575/CP-576 explicitly and keeps rules/counts out of web,
   as `docs/SDD.md:205-213` (§ 3) requires.
2. **Placement before Rename (b).** Put deletion between the list and Rename. The spec leaves the
   relative position open (`change_spec.md:343-345`, § Out of Scope), and the existing Rename-last
   test cited in C is an unreleased contract. Placing deletion after Rename would break it.
3. **One focus, retained form displays (b).** Active deletion owns focus while rename/add-form
   displays follow their own keys. CP-574 explicitly retains those displays; CP-571/CP-573/CP-578
   fix deletion focus. No active deletion means the previous precedence remains intact. T6/T7
   prove both sides rather than relying on body-building order.
4. **Address contract (b).** Use project-specific keys, keep only filter/sort on same-page
   redirects, and carry the actual removed name/count on Projects. The count parser admits zero;
   an incomplete/malformed completion pair produces no outcome. These are conservative transport
   choices for CP-572/CP-576 under ADR-0011, not additional actions or refusal copy.
5. **Response by construction (b).** Resolve the winning deletion mode before page/status
   selection. Missing entities return first. This prevents raw confirmation flags from assigning
   202 to failure or missing pages, the explicit CP-583 and ADR-0012 contract.
6. **Test assertion beyond the named route test.** T15 also changes the task first-press page
   test's 200 (`tests/integration/test_delete_pages.py:124-145`,
   `test_delete_first_press_opens_confirmation_without_saving`). CP-583 releases that status
   everywhere; the markup and no-save clauses stay proved. No spec reading is set aside.
7. **Existing task strip size — record gap.** The task strip passes `TRIGGER_SIZE`, the
   `row-control` context (`web/pages.py:743-743,833-841`), whose confirming control is 28px
   (`web/style.css:316-325`), while DESIGN § Components assigns deletion a full-size control.
   This change supplies the proper full-size context only for the new project deletion.
   The request and CP-585 expressly preserve task-deletion behaviour apart from status; that
   existing visual discrepancy is handed on in `deferred_decisions.md`, not silently repaired.
8. **Trace completion depends on new test paths (b).** A's final docstrings refer to tests owned
   by B/C. Their path-existence dependency is separate from the forward production API order.
   T22 adds a completeness assertion because the existing pointer check proves only that named
   paths exist, not that every CP-592 module is named
   (`tests/architecture/test_trace.py:57-58,108-112`, § missing_paths and the entry-docstring test).

### Reviews delegated by the records

The sweep of `docs/nfdr.md` for `development-design` covered QC-5, QC-8, QC-12, QC-20–QC-27,
QC-36, QC-40, QC-41, QC-46 and QC-60; the ADR sweep found no separate stage-named review.

| Gate | Verdict and reason |
|---|---|
| QC-5, QC-20, QC-21, QC-23 | Pass for this design: domain raises the existing typed missing-project refusal and owns cascade/count; application only saves/publishes; web maps types and builds pages. No message inspection, rules in web, or operator wording in domain. |
| QC-8, QC-27 | Pass: presentation state is rebuilt from current tracker reads and the address. No web outcome store, cookie, session or request object crosses inward. |
| QC-12 | Pass: existing parts and the shared strip cover the feature; no requirement-free part or feature module is added. |
| QC-22, QC-24–QC-26 | Not triggered: persistence, composition and the Saver contract do not change. |
| QC-36 | Pass: every new name/line uses `_escape`, including the shared strip's existing escape boundary. T7/T17 verify hostile names and surrounding structure. |
| QC-41, QC-46 | Pass: no credential or new saved field; removed name/count travel only in the completion address. |
| QC-60 | Pass for the proposed constructs: tuples, immutable dataclasses, Protocol-based saving and existing form/address helpers require no new runtime/library feature beyond the product's current Python 3.11 declaration (`pyproject.toml:1-4`). This is design review, not a claim of a 3.11 suite run. |
| QC-40 | Pass within the checked sources: the exact-version OSV query returned no vulnerability entries for any of the 15 locked packages, as recorded below. No pin/lock-format change is proposed. The existing dated browser exception applies on this review date. |

**QC-40 evidence and limits.** Pins were read from `pyproject.toml` § dependency-groups and all
15 entries of `tests/requirements.txt`. The browser under test is explicitly pinned by
`tests/e2e/test_moves.py:515,604` (`PINNED_BROWSER`, `153.0.8010.12`), not inferred from a browser
installed during this run. Google's [2026-10-06 desktop security release](https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop_086471744.html)
publishes critical fixes in a later browser line. The owner-recorded exception in
`docs/nfdr.md:1043-1056` (§ NFDR Review Notes, RN-33) covers that exact pinned build through
2026-11-07, including this 2026-10-28 review.

On 2026-10-28, an approved read-only `python3` probe sent the exact 15 package/version pairs from
`tests/requirements.txt` to `https://api.osv.dev/v1/querybatch`; its actual output was:

```text
ast_serialize 0.12.1 {}
greenlet 3.5.6 {}
iniconfig 2.3.1 {}
librt 0.16.0 {}
mypy 2.4.0 {}
mypy_extensions 1.1.0 {}
packaging 26.3 {}
pathspec 1.1.1 {}
playwright 1.63.0 {}
pluggy 1.6.0 {}
pyee 13.0.1 {}
Pygments 2.21.0 {}
pytest 9.1.1 {}
ruff 0.16.10 {}
typing_extensions 4.16.0 {}
```

The maintainer advisory pages for
[Playwright](https://github.com/microsoft/playwright-python/security/advisories),
[pytest](https://github.com/pytest-dev/pytest/security/advisories),
[mypy](https://github.com/python/mypy/security/advisories) and
[Ruff](https://github.com/astral-sh/ruff/security/advisories) were opened, and advisory searches
covered the locked transitive package names. These checks establish no guarantee about advisories
absent from those sources. The searched Ruff-related
finding was checked at its [maintainer advisory](https://github.com/astral-sh/ty/security/advisories/GHSA-vxvm-j4xq-q7m4),
not treated as proof that every locked dependency is safe. The bounded review found no additional
established QC-40 blocker; the browser exception
is not extended by this design.

### Cold-read result

All nine changing-mode checks were walked against this document: complete part placement and
transitive review (§ 2), sufficient additive contracts and dependency order (§ 3), two-pass
coverage and retired assertions (§ 5), count/status/focus realized by construction, all choices
and delegated reviews recorded here, record corrections named, settled text verdict, and no
third-repository write. No conflicting spec line was set aside.
