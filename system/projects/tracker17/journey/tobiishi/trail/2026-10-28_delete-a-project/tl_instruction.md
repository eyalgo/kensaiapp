# Tech Lead instruction — delete-a-project: delete the project with its tasks and complete the deletion contract

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every product path below is relative to it.
**Scope:** Implement CP-569–CP-593 of `change_spec.md` § Rules through the interfaces in `change_design.md` § 3.

This instruction owns the task cut, dependency edges and verification gates for
`tracker17 · tobiishi · 2026-10-28_delete-a-project`.
Product behavior remains `change_spec.md` § Rules; architecture remains `change_design.md`
§§ 2–4, `docs/nfdr.md` § 1.2 and `docs/SDD.md` § 3.
The action file's home is `<CORE>/doctrine/setup/kensaiapp_structure.md` § 2,
“journey/tobiishi/<key>/”.

---

## Project layout

```text
products/tracker17/
  domain/
    __init__.py                                  ← modified: public re-exports
    projects.py                                  ← modified: cascade, outcome, trace
    tasks.py                                     ← modified: trace only
  application/
    __init__.py                                  ← modified: public re-export
    tracker.py                                   ← modified: save/publish action
  web/
    routes.py                                    ← modified: submissions, resolved state, response policy
    pages.py                                     ← modified: project interaction and Projects completion
    style.css                                    ← modified: full-size project strip context
  tests/
    unit/test_projects.py                        ← modified
    integration/
      test_delete_project_tracker.py             ← new
      test_delete_project_pages.py               ← new
      test_delete_project_routes.py              ← new
      test_delete_pages.py                       ← modified
      test_delete_routes.py                      ← modified
      test_saved_data.py                         ← modified
      test_pages.py                              ← modified
      test_filter_pages.py                       ← modified
      test_sort_pages.py                         ← modified
      test_routes.py                             ← modified
      test_timed_run.py                          ← modified
    e2e/
      test_delete_project.py                     ← new
      test_delete_task.py                        ← modified
    architecture/test_trace.py                   ← modified
    timed_run.py                                 ← modified
```

Create the four marked test files in their existing directories; create no package directory or
`__init__.py`. The five-part topology and import permissions remain `docs/nfdr.md:161-192`
§ 1.2, “Forbidden imports”: domain → errors/stdlib; application → domain/errors;
persistence → domain/errors; web → application/errors; main → all four/errors.
Each part's prohibited dependencies remain binding there.
Placement follows `docs/SDD.md:199-238` § 3, “The parts” and “The seams”:
domain owns cascade/count/refusal, application owns save/publish, web owns presentation/transport,
and the timed harness owns its measurement oracle. `persistence/`, `main.py` and `errors.py`
receive no production changes, per `change_design.md` § 2.

Language resolution: Python — step 1, `system/projects/tracker17/project.md` `Languages:`;
opened `<CORE>/doctrine/engineering/languages/python/README.md` and its seven concern destinations.
Product decisions take precedence under the packet registry's § Precedence; in particular,
`docs/adr/0002-standard-library-only-no-web-framework.md` § Decision fixes Python 3.11 support
and no runtime dependencies, and `docs/nfdr.md` QC-62 fixes Ruff and mypy.

## Corrections owed while there

- Owed outside this change's reach: `docs/nfdr.md:109-120` § 1.1 QC-63 — “The task deletion's 202 is unmet” becomes false. The verifier list needs the revised task response-policy row, `tests/e2e/test_delete_task.py::test_confirmation_is_loaded_afresh_after_confirming`, and Task 4's project response/history tests; QC-63's obligation stays intact.
- Owed outside this change's reach: `docs/SDD.md:468-477` § 4 RT-11, Tests — the live forward pointer needs both concrete deletion history tests from Tasks 3 and 4. The dated “does not exist at 4a9ff47d2” evidence remains history; the live handoff wording needs Accepted ADR-0012 and QC-63 rather than remaining record-writing work.
- Owed outside this change's reach: `docs/SDD.md:1559-1570` § 11 R-12 — “once it exists” needs the two concrete deletion history tests beside the move history tests.

These are the three entries in `change_design.md` § Records this change makes false, checked
against the named records. The plan does not assign edits to product decision documents.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git -C products/tracker17 ls-files, run from the change worktree root, returned 266 product-relative tracked paths: product source, docs, tests, .gitignore, README.md and pyproject.toml. The complete listing contains no CI configuration or runner/build-service configuration."
  },
  "decisions": {"override": null, "amd64": null},
  "candidates": [
    {
      "language": "python",
      "image": "docker.io/library/python",
      "image_source": {
        "root": "core",
        "file": "doctrine/engineering/languages/python/environment.md",
        "anchor": "Start a container from the official Python image, `docker.io/library/python`, tagged with CI's"
      }
    }
  ],
  "guest": null
}
```

Product-root quality and browser commands use the product's pinned test environment, per
`docs/nfdr.md` § 10, “Every row's command”, and ADR-0002 § Decision.

## TL Review Notes

The following task decisions are the Tech Lead's, 2026-10-28.

1. **Split C by independently testable responsibility.** Task 3 aligns the existing task deletion's status and history proof; Task 4 builds the project interaction. Task 3 uses no new domain/application API. Within Task 4, body, focus, status and cache policy stay together: `change_design.md:200-208` § 3 states that the rendered project confirmation and its 202 have no green point between them.
2. **Separate A's trace completion.** Task 1 builds the additive domain API; Task 6 updates both docstrings and asserts completeness after the new test modules exist. `tests/architecture/test_trace.py:108-112`, “test_every_path_named_in_the_entry_docstring_exists”, fails for a named absent path. Task 6 depends on Tasks 2 and 4 for those files, rather than falsely making application depend on the completed documentation.
3. **Tighten the existing task-status assertion in its own task.** Task 3 changes the two 200 assertions named by design T14/T15 and their stale descriptive docstrings together. `tests/integration/test_delete_routes.py:450-457`, “test_live_delete_views_have_their_response_policy”, explicitly describes all live states as 200; leaving that sentence would contradict the released confirmation status.
4. **Add boundary probes to C.** Task 4 adds GET-on-action checks and an overlong numeric route target, alongside the required missing/never-held targets. The existing task deletion checks both in `tests/integration/test_delete_routes.py:479-495`, “test_first_press_for_a_held_task_never_saves_and_a_get_never_deletes” and “test_a_task_identity_too_long_to_read_is_the_missing_task”. On this reading, the new routes need the same read-only and missing-target boundaries; the project POSTs still redirect to their canonical bare project address.
5. **Keep timing assertions independent.** Task 5 tests each interval and their sum, including exactly one second and two individually fast intervals whose sum is too slow. This makes CP-590's three strict bounds explicit rather than inferring the total from individual successes; `change_design.md` § 3 D requires all three.
6. **Carry hints at their owning responsibility.** A's cascade/acyclic-import hint belongs to Task 1. C's precedence hint is narrowed to Task 3's existing task response and carried in full for Task 4's project response. D's independent-oracle/injected-timer hint belongs to Task 5. B's `None` stays without a hint, per `change_design.md` § 4.
7. **Keep the stated boundaries.** The existing add-task/rename direct-404 gap and task strip-size discrepancy remain the cases in `deferred_decisions.md`, per `change_design.md` § Architect Review Notes 7 and § 3 C. CP-585 permits only the task confirmation status change. No task here repairs those separate behaviors or rewrites published copy; project wording comes from the change's text record under `change_design.md` § Publishes text.
8. **Gate execution evidence.** Ran the card's exact `pytest products/tracker17/tests/` from the change worktree root in an approved terminal session: `2384 passed in 318.80s`, exit 0, on Python 3.15.0. The command collects the intended non-browser suite, so no gate-command substitution is made. Earlier pipe runs encountered denied loopback binding or inherited ignored SIGINT: a runtime probe returned `parent SIGINT handler: 1` and `child SIGINT handler: 1`, while the terminal probe returned `default_int_handler`; the isolated start test timed out after sending SIGINT at `tests/integration/test_start.py:517-535`, “_run_real_start”. Direct gate sessions need loopback permission and normal SIGINT handling. The passing baseline is the terminal run, not those earlier runs; no product code was changed for it. This run establishes no browser-suite or Python 3.11 verdict.

Coverage assignment for `change_design.md` § 5:

| Design rows | Task |
|---|---|
| T1 | 1 |
| T2 | 2 |
| T3–T13 | 4 |
| T14 | 3 |
| T15 | 3 for the confirmation status; 4 for list-row assertions |
| T16–T17 | 4 |
| T18 | 3 |
| T19–T20 | 4 |
| T21 | 5 |
| T22 | 6 |

### Task 1: Project cascade and immutable outcome (`domain/projects.py`, `domain/__init__.py`)

**Dependencies:** None

**What to build:** Sub-job A's domain API: immutable `ProjectDeletionOutcome` carrying the removed
`Project` and actual `task_count`, and `delete_project(state, project_id)` returning the changed
`TrackerState` with that outcome. Missing targets raise `ProjectNotFound`. Keep the two counters
and every surviving value and sequence position unchanged. Re-export the public names.
This is `change_design.md` § 3 A and CP-575/CP-576/CP-581/CP-582.

#### Behaviours to verify (developer adds tests to `tests/unit/test_projects.py`)

- `test_delete_project_removes_only_its_tasks_and_comments` — all four statuses and several comments, with another project interleaved among survivors; exact survivors and their order remain.
- `test_delete_empty_project_preserves_every_other_value` — zero tasks still removes the project, reports zero, and preserves assignees, operator name, counters and unrelated data.
- `test_delete_project_reports_the_removed_project_and_actual_task_count` — zero, one and many tasks; count all statuses, never comments, and return the name supplied in this call's state.
- `test_delete_project_leaves_the_input_unchanged` — the original state, projects, tasks and comments remain the original values; the resulting state and outcome are immutable values.
- `test_delete_missing_project_is_refused` — an absent identity raises `ProjectNotFound` and produces no changed state, including a repeated deletion.
- `test_delete_project_never_rewinds_identity_counters` — removing the highest identities leaves both counters unchanged; a subsequent project/task creation issues higher identities.

#### Implement

Infer from failing tests.

# Hint:
Derive the cascade and count from the same supplied state; one replacement preserves all
unaffected fields and both counters. Keep runtime imports acyclic: `tasks.py` already imports
`projects.py`, so the project rule must not add the reverse runtime dependency.

#### Verification gate

From the change worktree root: `pytest products/tracker17/tests/`.
Pass: Task 1's new tests pass, including the typed refusal and exact state comparisons;
no new failures in the existing suite.

### Task 2: Save before publishing project deletion (`application/tracker.py`, `application/__init__.py`)

**Dependencies:** Task 1 — deletion rule and outcome.

**What to build:** Sub-job B's `Tracker.delete_project(project_id)` action and public outcome
re-export. Apply the rule to current state, save its one candidate once, then publish and return
its outcome. Propagate refusal/save failure with the old state current. Obtain confirmation counts
from the existing `project_task_list(...).task_count`, as specified in `change_design.md` § 3 B.

#### Behaviours to verify (developer creates `tests/integration/test_delete_project_tracker.py`)

- `test_delete_project_saves_once_before_publishing` — a recording saver sees the exact candidate while tracker reads still show the old project/tasks/comments; after saving, the action returns the outcome and every read shows the new state.
- `test_delete_project_refusal_never_calls_the_saver` — missing or already removed target raises `ProjectNotFound`; saved-call record and current state remain unchanged.
- `test_delete_project_failed_save_keeps_every_read_unchanged` — a failing injected saver propagates its exception; projects, task lookups, lists, comments, summary, assignees and operator name retain the old values, with no success result returned.
- `test_delete_project_uses_state_at_confirm_time` — read the initial count, then add a task and rename before deleting; outcome reports the current name and actual removed count.
- `test_delete_project_receives_saves_only` — recording saver exposes attempted accesses and receives only saves for the action, satisfying CP-591/QC-54 without reading persistence through application.

#### Implement

Infer from failing tests.

#### Verification gate

From the change worktree root: `pytest products/tracker17/tests/`.
Pass: Task 2's tests pass with the real domain and injected saver; no new failures elsewhere.

### Task 3: Existing task deletion's 202 and fresh history load (`web/routes.py`, `tests/integration/test_delete_routes.py`, `tests/integration/test_delete_pages.py`, `tests/e2e/test_delete_task.py`)

**Dependencies:** None

**What to build:** Align the task deletion's pending response with CP-583/CP-585/CP-588/CP-589,
using its already resolved `DeleteArea` in the existing pending-status seam. Preserve the seam's
move callers and every other task deletion behavior. Add the actual Back-to-confirmation proof
beside the existing task completion history test, per design T14/T15/T18.

#### Behaviours to verify

- `test_live_delete_views_have_their_response_policy` in `tests/integration/test_delete_routes.py` — change only the confirmation's expected status to 202; back-out/failure/landing stay 200 with no-store. Keep its no-save/origin/no-Clear-Site-Data assertions and update its descriptive docstring.
- `test_delete_first_press_opens_confirmation_without_saving` in `tests/integration/test_delete_pages.py` — change the shown confirmation's expectation to 202; retain all markup, order, focus and unchanged saved-data assertions.
- `test_task_delete_failure_wins_over_confirmation_for_response_status` in `tests/integration/test_delete_routes.py` — combined failure/confirmation renders the failure and answers 200/no-store; a bare confirmation renders and answers 202/no-store.
- Retain missing/never-held task query coverage at 404 with no Cache-Control, and all existing move response assertions, per design T14.
- `test_confirmation_is_loaded_afresh_after_confirming` in `tests/e2e/test_delete_task.py` — use `history_page`, confirm and land, then actual Back to the confirmation address issues a new request, answers 404, and shows the task not-found page. Forward then Back again does the same. Assert the actual pinned Chromium version and unchanged post-delete saved bytes, not only DOM text or address.

#### Held by review

- CP-585 — the product diff changes only the task confirmation status; task deletion's words, dimensions, routes and focus remain unchanged. The existing task suite provides the behavioral regression checks; inspect the diff for unrelated changes.

#### Implement

Infer from failing tests.

# Hint:
Use the same resolved deletion precedence for page construction and pending status. A raw query
key must not make a failure or missing page 202. Keep the existing move call contract intact.

#### Verification gate

From the change worktree root:

```sh
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/test_delete_task.py
```

Pass: both commands exit 0; both named status assertions and the history proof pass;
no existing task/move assertion is lost.

### Task 4: Project deletion interaction and response (`web/routes.py`, `web/pages.py`, `web/style.css`)

**Dependencies:** Task 2 — the action and public outcome; Task 3 — the resolved-deletion pending-status seam.

**What to build:** Sub-job C's complete project interaction. Render the section after results and
before Rename in every project's Tasks view state, using `DeleteMode`/`DeleteArea` and
`confirm_strip`. Add POST `/projects/{id}/delete` and `/projects/{id}/delete/confirm` as
`SUBMISSION` routes behind the existing request check. Transport only filter/sort choices on
same-page redirects/forms, retaining blank and repeated values. The first press saves nothing;
the confirming press uses Task 2's outcome for a 303 to Projects with `deleted_project` and
`deleted_project_tasks`. Missing targets redirect to their bare project address. Save failure
uses the existing guarded console-reporting site and the project failure address.

Resolve project modes by failure → confirmation → back-out → ordinary, before consulting move or
deleted-task markers. Existing-project lookup precedes that resolution. Use the whole-project
count, not visible rows. Keep rename/add-form displays but give active deletion the sole focus.
Decode only a complete valid completion pair, including zero tasks; ignore malformed/incomplete
pairs. The recognized Projects completion owns heading focus and its accessible description,
including the empty Projects state. These contracts are `change_design.md` § 3 C and CP-569–CP-588.
Place exact published strings from the change's text record.

Use resolved state for both page and response: shown confirmation 202/no-store;
back-out/failure/recognized completion 200/no-store; deleted/missing address 404/no Cache-Control;
ordinary pages keep their policy. No Clear-Site-Data, cookie, session, page script or alternate
cache mechanism. Task deletion remains within Task 3's narrow change.

#### Behaviours to verify

In new `tests/integration/test_delete_project_pages.py` (design T4–T7):

- `test_delete_project_is_offered_only_below_its_tasks_view_results` — ordinary, empty, no-match, refused-filter and refused-sort states; section before Rename, outside all other forms, and no project deletion on Projects/Summary/task/All tasks or list rows.
- `test_project_confirmation_counts_all_current_tasks` — zero/one/many wording, current saved name, all four statuses and comments; a status or label filter never reduces the count. Sentence, confirm and Back out are ordered and use the shared strip.
- `test_project_deletion_preserves_only_filter_and_sort_choices` — complete pairs, repeated and blank values survive opening, confirming form, back-out and failure; unrelated address keys are absent from generated forms/redirects.
- `test_project_deletion_mode_precedence_controls_body_and_focus` — pair/triple combinations select failure before confirmation before back-out. Suppress all move markers and deleted-task lines, including a move naming a missing task. With no deletion state, existing precedence remains unchanged.
- `test_project_deletion_keeps_rename_and_add_displays_with_one_focus` — active deletion retains their requested form values/lines but suppresses their autofocus. Confirmation focuses the sentence; back-out/failure focuses the restored trigger, with the failure reason as its description; no back-out completion line.
- `test_projects_completion_covers_zero_one_many_and_empty_projects` — exact removed name/count, heading focused/described at page start; malformed/incomplete outcomes ignored, zero accepted. No reconstruction from a missing entity.
- `test_project_deletion_names_remain_text` — `<b>R&D "x"</b>` and surrounding whitespace survive as typed text in the confirmation and completion without injected elements or attributes.

In new `tests/integration/test_delete_project_routes.py` (design T8–T13):

- `test_first_project_delete_press_redirects_without_saving` — 303 with choices and confirmation marker; saved bytes and save count unchanged. Form-forged target/name/count cannot select the target or completion.
- `test_confirm_project_delete_saves_once_and_reports_current_outcome` — exact cascade, 303 to Projects, fresh name/count after intervening rename/task addition, and no carried filter/sort on the different-page landing. Reload changes no saved bytes or save count.
- `test_failed_project_delete_keeps_saved_and_visible_state` — failing saver, exact pre-state bytes and unchanged project/task/comment pages; console reports action/project/error once; failure page retains choices and focuses its trigger, without exception text or traceback.
- `test_deleted_project_and_children_disappear_from_every_read` — Projects, All tasks, filter/sort results and counts exclude the removed entities; the other project's Summary/tasks/comments retain their values. Bare/query Tasks/Summary/child URLs give the appropriate 404, no Cache-Control and no removed comments; include never-held targets.
- `test_deleted_project_submission_changes_nothing` — independently reported cases for add task, rename, first Delete project and confirm. Each setup actually deletes through confirmation; compare saved bytes before/after each stale action. Add/rename keep direct 404; the two new presses give 303 to the bare project address then project 404. Include repeated confirmation.
- `test_deleted_child_submission_changes_nothing` — independently reported cases for edit, add label, remove label, add comment, ordinary move, opening cancellation, confirming cancellation, opening Delete task and confirming Delete task. Each setup deletes the parent through confirmation first; every action gives 303 to the child address then task 404, saved bytes unchanged. Missing target wins over invalid submitted values.
- `test_project_delete_response_policy_matches_rendered_state` — confirmation 202/no-store; back-out/failure/Projects completion 200/no-store; failure+confirmation 200/no-store; ordinary pages unchanged; missing/never-held/deleted targets with confirmation queries 404/no cache. No Clear-Site-Data on either press or any live state/landing.
- `test_project_delete_submissions_require_same_origin_and_own_host` — each new route refuses cross-site, same-site, none, absent mark and foreign Host with 403 and unchanged saved bytes.
- `test_get_on_project_delete_action_addresses_never_deletes` — GET on either action URL is not a submission, saves nothing and follows the existing unknown-page answer.
- `test_overlong_numeric_project_target_is_missing` — both new POSTs redirect to the canonical bare project address and its GET shows project 404; no save, crash or confirmation.

In `tests/integration/test_saved_data.py` (design T3):

- `test_confirm_project_delete_persists_the_exact_cascade_and_retires_identities` — use real saved files with two projects, different statuses, multiple comments and interleaved survivors. Confirm through the route, reopen from disk, and compare the exact expected whole state, including untouched counters/assignees/operator. Restart, create project and task, and prove both exceed the highest deleted identities.
- `test_confirm_last_or_empty_project_delete_persists` — repeat real confirmation/readback for the only project and for an empty project, including the correct empty landing.

In existing page/route tests (design T15/T19/T20 and spec § Locked Answers, Gap 12):

- Narrow `tests/integration/test_delete_pages.py::test_no_list_row_offers_deletion` to no task-row deletion, admitting the project section but keeping All tasks free of deletion.
- Update `tests/integration/test_pages.py` header samples `project`/`created` and the empty project's exact form set; keep links, fields, description, rename, and absence of textarea/table.
- Update empty-project form sets in `tests/integration/test_filter_pages.py` and `test_sort_pages.py`; retain invitations, no table and no filter/sort controls. Keep rename-last and move-focus assertions intact.
- Extend `tests/integration/test_routes.py::test_every_route_leaves_state_and_headers_as_the_rules_say` with both route samples and opening zero-save count; retain read immutability, redirect, no-cookie and CSP assertions for the enlarged complete route set.
- Extend `tests/integration/test_routes.py::test_no_socket_connection_is_made` through both presses and Projects landing; retain every preceding action. QC-54's recording-saver case belongs to Task 2.

In new `tests/e2e/test_delete_project.py` (design T16/T17):

- `test_project_confirmation_is_keyboard_operable` — keyboard-only opening/confirm/back-out on short and empty pages; sentence focused/in view, Tab to Delete project then Back out, back-out restores trigger focus, successful confirm lands on heading described by completion.
- `test_double_press_never_confirms_project_deletion` — 60-task scrolling list, part-way scroll and near-bottom cases, short/long names; actual double click at the original trigger coordinates only opens confirmation. Sentence covers that spot after load, a further click there cannot confirm, and saved bytes remain unchanged.
- `test_project_strip_uses_full_size_controls` — full-size trigger, sentence and confirming control share the DESIGN control height; Back out stays full-size. No resize of the existing task/move contexts.
- `test_project_completion_survives_actual_reload_back_and_forward` — completion/heading/absence, actual reload and traversal retain the line and post-delete bytes without another save; hostile names show exactly as text.
- `test_project_confirmation_is_loaded_afresh_after_confirming` — use `history_page` and assert actual pinned Chromium version. After confirm/landing, Back to the original confirmation address makes a fresh request and shows project 404, with no confirmation. Forward/Back again gives the same result and saved bytes remain unchanged.

#### Held by review

- The shared component is reused, and new strings are placed verbatim from the change's text record. Check `web/pages.py` at the call site, per design § 3 C; browser geometry alone cannot prove there is one component.
- Domain/application own cascade/count/save decisions; web only decodes presentation values and calls the action. Check the added logic against `docs/SDD.md` § 3 and the allowed import graph.
- Product pages contain no script or cache workaround; test-side history observation is confined to the browser harness, per ADR-0003/ADR-0012 § Decision.

#### Implement

Infer from failing tests.

# Hint:
Reuse `confirm_strip` and its sentence-covering grid. Add only a project full-size context;
its padding/coverage must account for the two full-size controls, including bottom-of-page scroll
clamping. Resolve deletion precedence once for body, autofocus and status.

#### Verification gate

From the change worktree root:

```sh
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/test_delete_project.py products/tracker17/tests/e2e/test_delete_task.py
```

Pass: both exit 0; every stale-action case has its own reported result and unchanged-byte
assertion; real-file cascade, exact current outcome, response matrix, keyboard/double-click and
fresh-load history proofs pass. Existing rename/move/task assertions retain their other clauses.

### Task 5: Full-volume project deletion measurement (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** Task 4 — both project routes and Projects landing.

**What to build:** Sub-job D's own project-deletion fixture/location and final measurement block,
after the rename, with separate labels for confirming POST, landing GET and sum. Use 1,000 tasks
with 20 comments each at ordinary text lengths, including tasks in the removed project and
survivors elsewhere. Open confirmation before timing; mark POST same-origin. Independently
derive the exact saved delta and completion expectation from the fixture. Keep every older action
and relative order, adjusting old “last rename” assertions and fixture descriptions where needed,
as design T21 and CP-590 specify.

#### Behaviours to verify (developer adds to `tests/integration/test_timed_run.py`)

- `test_project_delete_measurement_uses_full_volume_and_reports_actual_lengths` — fixture is the required volume, deleted project holds tasks, separate saved location, output states actual text lengths.
- `test_project_delete_measurement_reports_post_landing_and_sum` — injected timer yields separately labelled readings; excludes fixture setup, opening and readback work from intervals.
- `test_project_delete_measurement_checks_exact_saved_state` — correct project/tasks/comments removed, every surviving value/order and both counters preserved; wrong cascade, survivor, counter or metadata makes the action fail.
- `test_project_delete_measurement_checks_actual_completion` — 200 Projects landing shows actual removed name/count; wrong destination, name, count or missing completion fails the landing and total.
- `test_project_delete_measurement_requires_a_successful_same_origin_action` — inspect the request mark through a passed-in Site wrapper; refused/failed opening or confirming press produces failed rows and nonzero whole-run verdict.
- `test_project_delete_each_interval_and_total_must_be_under_one_second` — individually slow POST/GET, exactly 1 second and individually fast intervals whose sum reaches/exceeds 1 second fail; a fully fast correct action passes.
- `test_whole_run_appends_project_deletion_and_keeps_every_older_action` — extend `_run_readings`, fixed sequences, ordered labels, previous rename-last assertions and failing-action parameters. Preserve all earlier verdicts, ordering and saved-delta checks; any old or new failed action still makes final exit nonzero.

#### Implement

Infer from failing tests.

# Hint:
Use an independent fixture and exact-state oracle; exclude fixture/readback work from measured
intervals, and retain the existing injected timer seam. Never call the production deletion rule
to produce the oracle.

#### Verification gate

From the change worktree root: `pytest products/tracker17/tests/`.
From the product root: `python3 tests/timed_run.py`.
Pass: both exit 0; each old action still passes, and the new POST, landing and sum each report
strictly below one second with successful exact-delta/completion checks.

### Task 6: Complete both slice traces (`domain/projects.py`, `domain/tasks.py`, `tests/architecture/test_trace.py`)

**Dependencies:** Task 2 — new tracker test module; Task 4 — new page, route and browser test modules.

**What to build:** Complete both opening docstrings under CP-592 and design T22. Each names the
seven slice-created modules and all four project-deletion modules shown in the layout, with full
test paths. Retain every valid existing pointer and requirement, add FR-13 to the Projects entry,
and describe participating application/web modules truthfully. Add the trace-completeness
assertion alongside the existing path/requirement/participant/test-header checks.

#### Behaviours to verify (developer adds to `tests/architecture/test_trace.py`)

- `test_both_deletion_slice_entries_name_every_slice_created_test_module` — read both real opening docstrings and assert the complete required test-path set from CP-592, including all four project-deletion files. An omitted slice test fails even when every remaining pointer exists.
- Retain `test_every_path_named_in_the_entry_docstring_exists`, test-module path/requirement checks, participating-module checks and landed-feature coverage. Every new test file names its SRS requirement or acceptance criterion.

#### Held by review

- CP-592's no-new-feature-module clause: from the change worktree root, `git diff --name-only --diff-filter=A "$(git merge-base main HEAD)" -- products/tracker17/domain` returns no path. This is a branch review against its merge base, never a suite test pinned to a historical SHA.
- Docstring prose names actual participants and checked behaviors. The completeness assertion checks names; read the two updated docstrings against the changed implementation for truthfulness.

#### Implement

Infer from failing tests.

#### Verification gate

From the change worktree root: `pytest products/tracker17/tests/`.
From the product root, run each command separately:

```sh
python3 -m compileall -q main.py errors.py domain application persistence web tests
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
pytest tests/
pytest tests/e2e/
python3 tests/timed_run.py
```

Pass: every command exits 0; both traces are complete, every retained/new assertion passes,
both browser deletion history proofs pass in the pinned build, and every timed action meets
its bound. These are CP-590/CP-592/CP-593 and `docs/nfdr.md` QC-11/QC-48/QC-62.
