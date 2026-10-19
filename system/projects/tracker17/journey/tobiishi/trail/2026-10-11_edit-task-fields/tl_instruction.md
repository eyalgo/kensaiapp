# Tech Lead instruction — edit-task-fields: edit four fields without overwriting untouched values

**Date:** 2026-10-12
**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17
**Scope:** Implement the title, priority, assignee and due-date edit, its task-page form and project text, refusal/retry outcomes, and timed measurement under CP-144–CP-181.

This document owns the implementation tasks and their verification gates for `tracker17 · tobiishi · 2026-10-11_edit-task-fields`.
Its behavioural input is that change's `change_spec.md` § Rules (L27-L83), and its structural input is `change_design.md` §§ 2–5 (L21-L151).
Code and test paths below are relative to Product root; citations beginning `products/` or `system/` are relative to the instance worktree.
The output belongs in the change arc under `<CORE>/doctrine/setup/kensaiapp_structure.md` § 2, “Holds the change arc” (L2097-L2101).

---

## Project layout

```text
products/tracker17/
  domain/
    tasks.py                                  ← modified: edit values/rule/context and feature trace
    refusals.py                               ← modified: TaskNotFound and assignment refusal docstring
    __init__.py                               ← modified: public re-exports only
  application/
    tracker.py                                ← modified: edit action and context query
    __init__.py                               ← modified: public re-exports only
  web/
    pages.py                                  ← modified: edit carrier, task page and typed outward codes
    routes.py                                 ← modified: task POST, GET context and outcome transport
    style.css                                 ← modified only if existing form/reason styles need extension
  tests/
    unit/test_tasks.py                        ← modified: domain edit and context
    integration/test_task_tracker.py          ← modified: edit orchestration and page query
    integration/test_task_pages.py            ← modified: form rendering and literal text
    integration/test_task_routes.py           ← modified: request path, retries, restart and refusals
    integration/test_routes.py                ← modified: every-route/action samples and serialization
    integration/test_saved_data.py            ← modified: existing-format read and edit read-back
    integration/test_timed_run.py             ← modified: measurement truth and boundaries
    e2e/test_tasks.py                         ← modified: browser edit, focus and escaping
    timed_run.py                             ← modified: edit and edit-landing measurements
```

Create no directory or package initializer.
Keep implementation in named modules and exports in the two listed `__init__.py` files.
The complete production part set is `domain/`, `application/`, `persistence/`, `web/`, `main.py`, plus `errors.py`; retain the unchanged files rather than adding a part (`products/tracker17/docs/nfdr.md:L31-L36`, QC-1; `change_design.md:L25-L31`, Blast Radius).

Placement follows the parts table: rules and choice computations in domain; save/publication flow and queries in application; request transport, HTML, focus and stylesheet in web (`products/tracker17/docs/SDD.md:L194-L204`, “The parts”).
The allowed/forbidden imports are binding as recorded in `products/tracker17/docs/nfdr.md:L122-L154`, § 1.2: domain → errors/standard library; application → domain/errors; persistence → domain/errors; web → application/errors; main → all four/errors; errors → no product part.
No runtime third-party import or production import of tests is permitted (`products/tracker17/docs/nfdr.md:L122-L154`, § 1.2).

## TL Review Notes

Decisions below are the Tech Lead's, 2026-10-12.

- **Task split:** Split design sub-job A into Task 1's mutation contract and Task 2's read-only context query because their responsibilities and failing tests are independent (`change_design.md:L40-L65`, “A — domain”). Task 2 uses Task 1's `TaskFields`; Task 3 uses both. Carry A's complete edit hint into Task 1 only: its change-set/validation approach does not describe the context query (`change_design.md:L119-L123`, Code Strategy).
- **Atomic task:** Combine C and D in Task 4 because the design explicitly gives their required renderer signature an atomic-landing edge (`change_design.md:L109-L115`, “Atomic-landing edges”). Keep both architectural hints and both files' responsibilities.
- **Type precision:** Name the closed edit refusal vocabulary `TaskEditRefusal`, an enum local to `web/pages.py`, in Task 4; the design specifies a closed code without a precise type/name (`change_design.md:L77-L77`, C's Exposes). Distinct edit codes keep the add contract separate. Preserve `TaskFields` as optional raw strings: it must represent absent, empty and invalid submitted values before domain validation (`change_design.md:L46-L52`, Contract table).
- **Measurement precision:** Task 5 gives the edit measurement a separately seeded 1,000-task location. The existing add measurement appends a task (`products/tracker17/tests/timed_run.py:L195-L225`, `measure_task_volume`), and its tests require 1,001 tasks afterwards (`products/tracker17/tests/integration/test_timed_run.py:L79-L101`, `test_timed_run_exercises_and_reports_task_volume`). A separate fixture meets CP-179's exact edit volume without changing the add fixture's preservation proofs. Extend E's hint with that fixture separation.
- **Coverage made explicit:** Add Task 4 tests for newline normalization on both field sets, ignored unknown edit-outcome query codes, and absent-pair carry-over. These are directly implied by CP-151/CP-166 and D's presence-preserving transport, but the design's table does not name each request-level assertion (`change_spec.md:L37-L37,L55-L55`, Rules; `change_design.md:L93-L95`, D's extraction/outcomes).
- **Corrections in touched code:** Task 3 qualifies the unconditional action-saving module docstring, and Task 4 replaces the read-only task-page docstring, because their existing descriptions would become false under CP-157 and CP-144 (`products/tracker17/application/tracker.py:L1-L5`, opening docstring; `products/tracker17/web/pages.py:L470-L473`, `task_page`; `change_spec.md:L27-L27,L43-L43`, Rules). Each correction rides the task already opening its file.
- **Gate evidence:** The card's exact command, `pytest products/tracker17/tests/`, collected 574 tests from the worktree root. The sandboxed invocation exited 1 with `5 failed, 553 passed, 16 errors` and loopback binds raising `PermissionError: [Errno 1] Operation not permitted`; the same command with command approval exited 0, `574 passed in 15.35s`. Keep the card command in every task gate (`system/projects/tracker17/project.md:L10-L10`, Test command). This baseline used Python 3.14.7 / pytest 9.0.3 as printed by pytest; it is not a verdict on the pinned environment or the separate browser suite. No task uses the red-at-baseline lane.

## Corrections owed while there

- Owed outside this change's reach: `products/tracker17/docs/SDD.md:L201-L201`, § 3 application row — “Each action ... saves the new state” becomes unconditional wording that the no-change edit does not satisfy → qualify saving/publication as applying when the domain outcome marks a changed field; a no-change edit returns the current task without saving or publishing (`change_spec.md:L43-L44`, CP-157/CP-158; `change_design.md:L160-L160`, Records this change makes false).
- Owed outside this change's reach: `products/tracker17/docs/nfdr.md:L167-L174`, QC-21 — the unconditional apply/save/publish sequence becomes false for no-change edits → state the same domain-outcome qualification without giving application a comparison or membership rule (`change_spec.md:L43-L44`, CP-157/CP-158; `change_design.md:L160-L160`, Records this change makes false).
- Owed outside this change's reach: `products/tracker17/docs/adr/0001-rule-core-behind-server-rendered-pages.md:L26-L28`, Decision/application bullet — “Each ... saves the result” needs the no-change qualification → keep the Accepted record append-only and record beside QC-21 that save-before-publication applies to operations reporting a change (`change_design.md:L161-L161`, Records this change makes false; `products/tracker17/docs/adr/README.md:L3-L6`, append-only log).

### Task 1: Domain edit rule (`domain/tasks.py`, `domain/refusals.py`, `domain/__init__.py`)

**Dependencies:** None

**What to build:** The immutable `TaskFields`, `TaskEditOutcome`, `edit_task(state, task_id, submitted, shown)` contract and `TaskNotFound` refusal from design A (`change_design.md:L40-L65`, A).
`TaskFields` carries title/priority/assignee/due_date as string or None; None is absence, empty string is a present value.
`TaskEditOutcome` carries the resulting Task and whether any supplied submitted/shown pair differed.
Find the current task before the no-change path; validate only pairs whose two values are present and different.
Use the existing priority enum and date/title validators; an edit's empty priority has no creation default.
Return the resulting state and outcome without I/O, clock access or published wording.
Update the task feature's opening trace for FR-16 and all participating application/web/test modules under CP-173 (`change_spec.md:L68-L68`, CP-173).
Widen `AssigneeNotListed`'s creation-only docstring to cover a changed assignment, as design A requires (`change_design.md:L59-L59`, Refusals).

#### Behaviours to verify

Add to `tests/unit/test_tasks.py`; map assertions to design T1–T4 (`change_design.md:L133-L136`, Test Additions).

- `test_task_edit_saves_all_four_fields_exactly` — all changed values apply; preserve surrounding title spaces and exact assignee names.
- `test_task_edit_changes_each_field_independently` — each single-field edit leaves the other three current values intact; verify all four priority words and valid/leap dates.
- `test_task_edit_clears_optional_fields` — present-empty assignee and due date clear them; present-empty priority raises `InvalidPriority`.
- `test_task_edit_uses_only_complete_changed_pairs` — missing submitted or shown value means unchanged; distinguish None from empty; equal normalized values mean unchanged.
- `test_task_edit_replaces_stale_changed_field` — compare with shown values, not current state; stale title and low → high → medium priority edits replace current values.
- `test_task_edit_preserves_concurrent_untouched_fields` — a field equal to its shown value keeps a newer current value while another field changes.
- `test_task_edit_changed_to_current_still_reports_change` — a supplied/shown difference reports changed even when the resulting state equals the current state.
- `test_task_edit_with_no_changes_returns_current_values` — return original state/current task, unchanged outcome; unchanged invalid pairs are not validated.
- `test_task_edit_keeps_or_replaces_unlisted_assignee` — untouched unlisted name survives; listed/none replaces it; restoring the removed name as a changed assignment raises `AssigneeNotListed` carrying that exact name.
- `test_task_edit_rejects_each_invalid_changed_value` — blank/empty/Unicode-whitespace title → `BlankTitle`; 201 characters and 201 spaces → `TextTooLong`; unknown/empty/case-varied priority → `InvalidPriority`; unlisted assignee → `AssigneeNotListed`; malformed/impossible date → `InvalidDueDate`; 200 title code points are accepted.
- `test_task_edit_uses_complete_refusal_precedence` — parametrize competing invalid fields to prove title length, title blankness, priority, assignee, due date in that order; no accepted subset leaks from a refused edit.
- `test_task_edit_missing_task_wins_over_no_change` — `TaskNotFound` for missing identity, including an empty or otherwise invalid request.
- `test_task_edit_preserves_every_protected_value` — edit in todo/in-progress/done/cancelled; preserve identity/project/status/labels/comments/created instant, tuple position, counters, all other tasks/projects/People/operator name and the original immutable state.
- `test_task_edit_values_are_immutable` — edit carriers and outcome reject mutation.

#### Implement

Infer from failing tests.

```text
# Hint:
Build the change set from submitted/shown pairs, validate it completely in the explicit refusal order, then replace only those fields on the current immutable task. A changed-to-current value still has a changed outcome.
```

#### Verification gate

From the instance worktree root `.worktrees/2026-10-11_edit-task-fields`, run:

```sh
pytest products/tracker17/tests/unit/test_tasks.py
pytest products/tracker17/tests/architecture/
pytest products/tracker17/tests/
python3 -m compileall -q products/tracker17/domain
```

Pass: new edit behaviours and trace/import/immutability checks pass; the full suite collects tests and exits 0; compile exits 0; no earlier assertion is weakened.

### Task 2: Domain task-edit context (`domain/tasks.py`, `domain/__init__.py`)

**Dependencies:** Task 1 — uses `TaskFields` to expose the saved field strings.

**What to build:** The frozen `TaskEditContext` and `task_edit_context(state, task_id)` query in design A, exposing the current Task, its Project, saved field strings, ordered choices and `assignee_unlisted` (`change_design.md:L46-L53`, Contract table).
Keep the assignee-list and carried-name computation in domain.

#### Behaviours to verify

Add to `tests/unit/test_tasks.py`; cover design T2/T6's context contribution (`change_design.md:L134-L134,L138-L138`, Test Additions).

- `test_task_edit_context_shows_saved_fields` — title exactly as saved, priority word, ISO date or empty, assignee or empty, and the exact project entity/name.
- `test_task_edit_context_orders_listed_choices` — none first, listed names in saved order, no duplicate for a carried listed name; preserve case, spaces and markup characters.
- `test_task_edit_context_appends_carried_unlisted_name` — none/listed names then carried name once, flag true; listed or unassigned tasks have flag false.
- `test_task_edit_context_handles_empty_people` — none only for unassigned task; none then carried name for an unlisted assignee.
- `test_task_edit_context_exists_in_every_status` — the same context contract in all four statuses without imposing workflow rules.
- `test_task_edit_context_missing_task_returns_none` — unknown identity yields None.
- `test_task_edit_context_is_pure_and_immutable` — query changes no state and context rejects mutation.

#### Implement

Infer from failing tests.

#### Verification gate

From the instance worktree root, run:

```sh
pytest products/tracker17/tests/unit/test_tasks.py
pytest products/tracker17/tests/architecture/
pytest products/tracker17/tests/
python3 -m compileall -q products/tracker17/domain
```

Pass: the context tests and Task 1 tests pass; architecture/trace checks and full suite exit 0 with tests collected; compile exits 0.

### Task 3: Application edit and context query (`application/tracker.py`, `application/__init__.py`)

**Dependencies:** Tasks 1 and 2 — uses the domain edit, outcome, fields, context and refusal contracts.

**What to build:** `Tracker.edit_task(task_id, submitted, shown)` and `Tracker.task_edit_context(task_id)` with design B's save-before-publication and no-change paths (`change_design.md:L67-L75`, B).
Return domain outcomes and expose the new contracts plus all six refusal types through application for web.
Keep membership/comparison/validation in domain; use the existing saver seam and no edit clock read.
Correct `application/tracker.py`'s unconditional action-saving opening docstring in this task: changed outcomes save before publication; no-change edits return without saving (`products/tracker17/application/tracker.py:L1-L5`, opening docstring; `change_spec.md:L43-L43`, CP-157).

#### Behaviours to verify

Add to `tests/integration/test_task_tracker.py`, using real Tracker/domain and injected recording/failing savers and clock; cover T4/T5 and T14's application contribution (`change_design.md:L136-L137,L146-L146`, Test Additions).

- `test_tracker_edit_saves_once_before_publishing` — one changed whole-state candidate reaches the saver while public queries still show the old state; only successful return makes the new task current.
- `test_tracker_edit_changed_to_current_still_saves` — a changed outcome triggers one save even when current state equality would suggest no change.
- `test_tracker_unchanged_edit_never_saves` — no-change outcome returns current task, no saver call or publication.
- `test_tracker_refused_edit_never_saves` — every typed refusal propagates through the application contract; no candidate is saved and current reads stay unchanged.
- `test_tracker_failed_edit_keeps_current_state` — a failing saver propagates its error and leaves current task and whole state unchanged.
- `test_tracker_edit_never_reads_clock_or_saved_data` — injected clock records no read during edit/context lookup; recorder receives only saves.
- `test_tracker_edit_preserves_other_fields_in_every_status` — protect every state value, and retain current values for untouched fields after a concurrent edit.
- `test_tracker_task_edit_context_delegates_saved_values` — listed/unlisted/unassigned/missing-task contexts match domain and perform no save.
- `test_tracker_edited_due_date_updates_list_order_and_overdue` — existing list query recomputes due-date then identity order, undated-last and equal-date ties, and overdue status from the edited task; no edit-time clock update.

#### Held by review

- The action/context query must own no changed-field, membership or refusal rule; read the diff for delegation because architecture import tests do not prove placement (`products/tracker17/docs/nfdr.md:L167-L174`, QC-21; `products/tracker17/docs/SDD.md:L201-L201`, application row).

#### Implement

Infer from failing tests.

#### Verification gate

From the instance worktree root, run:

```sh
pytest products/tracker17/tests/integration/test_task_tracker.py
pytest products/tracker17/tests/architecture/
pytest products/tracker17/tests/
python3 -m compileall -q products/tracker17/application
```

Pass: every orchestration behaviour passes; read the diff against the review property; no new failure in the full suite; every command exits 0.

### Task 4: Served task-edit form and outcomes (`web/pages.py`, `web/routes.py`, `web/style.css`)

**Dependencies:** Task 3 — uses application edit/context/field/outcome/refusal exports and existing maximum/priority exports.

**What to build:** Design C/D's required `task_page(context, *, form=None, added=False, saved=False)`, frozen `TaskEditForm`, enum `TaskEditRefusal`, task POST route and context-backed GET (`change_design.md:L77-L103`, C/D).
The enum represents blank-title, too-long, invalid-priority, assignee-not-listed and invalid-due-date edit outcomes; keep add codes/carrier separate.
The form carries retained visible `TaskFields` and original shown `TaskFields`, refusal-or-none and failure flag.
Use the exact visible names title/priority/assignee/due_date and hidden names shown_title/shown_priority/shown_assignee/shown_due_date; post to `/tasks/<id>`.
Transport edit_refused/edit_failed/saved outcomes as the design specifies; preserve presence and normalize each present value before application.
Reuse the request gate/lock, identity parser, address builder, escaping function and failure boundary.
Take every published page/console string verbatim from this change's `change_text.md` when present, under CP-144–CP-169 and the design's text verdict (`change_design.md:L6-L6`, Publishes text; `change_spec.md:L17-L19`, wording boundary).
Rewrite the read-only `task_page` docstring as part of this task because its current description no longer describes CP-144 (`products/tracker17/web/pages.py:L470-L473`, `task_page`; `change_spec.md:L27-L27`, CP-144).
Extend existing styles only as needed by the edit form/reason/failure rendering.

#### Behaviours to verify

Add/extend `tests/integration/test_task_pages.py`, `tests/integration/test_task_routes.py`, `tests/integration/test_routes.py`, `tests/integration/test_saved_data.py`, and `tests/e2e/test_tasks.py`; cover design T6–T16 and T18's web contribution (`change_design.md:L138-L148,L150-L150`, Test Additions).

- `test_task_page_opens_edit_form_from_saved_values` — one labelled Save form in every status; exact saved title/hidden baseline, four priority words/selection, listed/none selection, empty/native date and domain-supplied maxlength; plain project name, no project link/control; unchanged bytes on repeated GET.
- `test_task_page_shows_carried_unlisted_assignee` — chosen carried name plus none/listed choices and the supplied notice beside the control; no notice for listed/none; include empty People and markup/case/spaced names.
- `test_task_edit_saves_all_fields_and_each_one_field` — real Site/Tracker/SavedData accepts ` Ship it `, critical, Ari, 2026-11-01, every single-field change and optional clear; verify disk bytes/state and fresh redirected values.
- `test_task_edit_preserves_absent_and_empty_pairs` — absent submitted/shown keys and a body with no fields mean no change for those fields; present-empty clears only eligible optional fields.
- `test_task_edit_normalizes_both_field_sets` — CR LF/lone CR normalize in submitted and shown strings before comparison; no other trim or case normalization.
- `test_task_edit_no_change_has_no_save_or_completion` — plain task redirect and no saver call; a changed-to-current pair instead saves once and shows completion.
- `test_task_edit_stale_form_replaces_changed_values` — load hidden values from a real form; second tab saves another title, first tab's changed title overwrites it; repeat low → high → medium; title-only edit preserves another tab's priority.
- `test_task_edit_keeps_then_replaces_unlisted_assignee` — remove Dana, edit title and keep Dana; replace with Ari/none and remove Dana/notice from choices; subsequent changed Dana is refused.
- `test_task_edit_rejects_assignee_removed_after_load` — loaded Ari disappears from People before submission; exact stale reason/reload link, assignee focus, other three entered values and saved bytes unchanged.
- `test_task_edit_blank_title_refusal_keeps_all_entered_values` — blank plus valid changes saves none; supplied reason beside title, field focus and accessible description; retain both field sets.
- `test_task_edit_too_long_discards_all_submission_text` — 201 characters and 201 spaces each use too-long reason; neither visible nor shown submitted sentinel text enters redirect/page; controls and baseline reset to current saved values; title focus.
- `test_task_edit_invalid_priority_refusal_changes_nothing` — exact reason and priority focus/description; no saved-byte change.
- `test_task_edit_invalid_due_date_refusal_changes_nothing` — exact reason and date focus/description; no saved-byte change.
- `test_task_edit_multiple_refusals_show_only_first_reason` — complete CP-165 precedence, one reason and one focused control; no partial save.
- `test_task_edit_missing_identity_uses_task_not_found` — nonexistent/zero/oversized-digit addresses and the typed missing-task outcome save nothing and show the existing task not-found reason.
- `test_task_edit_retry_keeps_original_baseline` — fix blank title after retained priority change and save both; an untouched field another tab changed stays current. Repeat after assignee/priority/date refusal and saver failure, retaining missing pairs; too-long retry instead uses reset saved baseline.
- `test_task_edit_failed_save_retains_form_without_python_error` — failing saver leaves disk/current state unchanged; supplied failure message describes focused form, both field sets retained; console action then error; no Python message/traceback in page/address; healthy retry succeeds.
- `test_task_edit_origin_gate_prevents_all_actions` — cross-site/same-site/none/absent/other non-same-origin mark and wrong Host each forbid before edit/saver, with unchanged bytes.
- `test_every_route_and_action_includes_accepted_edit` — add an accepted changed-pair body for `/tasks/1` to existing route samples; prove 303, one save, policy header and no cookie; add edit to no-outbound audit and recording-saver sequences.
- `test_task_edits_wait_for_held_save` — two edit submissions serialize through an injected held saver; the second cannot save until the first is released, and sees its current result.
- `test_task_edit_restart_preserves_format_and_protected_fields` — pre-change data loads without migration; edit title/due date and restart with real SavedData; same file/task keys, counters, comments/labels/status/project/created instant; correct list ordering and overdue flags including undated/equal-date ties.
- `test_task_edit_completion_describes_heading_after_save` — one supplied saved-change line quotes current saved title; heading focus and description, line unfocused; reload/back/forward never saves; normal/no-change GET has no completion; existing added completion remains intact.
- `test_task_edit_renders_every_operator_value_as_text` — visible/hidden title, project and listed/carried/rejected assignee names, retained outcomes and completion text escape markup through the existing escape function.
- `test_task_edit_ignores_unrecognized_outcome_query` — unknown edit refusal/failure codes or field query without recognized retaining outcome do not reconstruct a retained form or change state.
- `test_browser_edit_title_is_literal_on_task_and_project` — edit to `<b>A&B</b> "Q"`; exact heading, input and list/link text; no injected element; preserve existing add escaping assertions.
- `test_browser_edit_controls_and_keyboard_focus` — title entry stops at maximum; native date sets/clears; keyboard Save reaches heading/accessible description; blank refusal focuses/describes title.

Replace only the superseded form/control prohibition, forbidden edit word and blanket main-area link prohibition in `test_task_page_is_read_only_and_shows_only_four_fields` with the authorized form/project/refusal-link assertions; retain exact title/page-title, saved values, navigation, no status/labels/comments/overdue/script/table and all remaining assertions (`change_design.md:L156-L156`, Assertions superseded; `change_spec.md:L184-L184`, Gap 10).
Update direct renderer fixtures to context without reducing their assertions.
Every refusal has a distinct test asserting its supplied reason and unchanged bytes; use real parts and injected collaborators, never patch a product name (CP-175/CP-176, `change_spec.md:L72-L78`).

#### Held by review

- Domain owns comparison/membership/choice rules; web only transports values and renders domain data. Refusals branch by type, and all operator values use the one escape function; read the diff for these properties because import/behaviour tests alone cannot prove them (`products/tracker17/docs/nfdr.md:L56-L67,L182-L186,L268-L275`, QC-5/QC-23/QC-36).
- No new cookie/session/cache, production module, runtime dependency, status/delete/label/comment/filter/sort/summary control or `domain/labels.py`; verify the diff against CP-174 and the recorded part set (`change_spec.md:L69-L69`; `products/tracker17/docs/nfdr.md:L31-L36`, QC-1).

#### Implement

Infer from failing tests.

```text
# Hint:
Two separate field sets: visible retained values and hidden original values. The too-long outcome resets both from the current context. Use the single escape function at every text/attribute insertion.

Preserve absent versus present-empty through extraction and URL encoding. Keep both sets on retained outcomes, neither on too-long outcomes; reuse the existing redirect builder and failure boundary.
```

#### Verification gate

From the instance worktree root, run:

```sh
pytest products/tracker17/tests/integration/test_task_pages.py products/tracker17/tests/integration/test_task_routes.py products/tracker17/tests/integration/test_routes.py products/tracker17/tests/integration/test_saved_data.py
pytest products/tracker17/tests/architecture/
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/
python3 -m compileall -q products/tracker17/web products/tracker17/tests
```

Pass: all listed edit/retention/escaping/browser/format proofs pass; all existing add proofs remain green; review properties hold; every command exits 0 and each pytest command collects tests.
The browser suite uses the locked test environment and installed Chromium required by `products/tracker17/docs/adr/0002-standard-library-only-no-web-framework.md:L20-L24`, Decision; unavailable prerequisites are not a passing gate.

### Task 5: Truthful field-edit timing (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** Task 4 — uses the served edit form and POST/landing contract.

**What to build:** Separate edit and edit-landing measurements at 1,000 tasks/20 comments each, while retaining every existing project/add/add-landing measurement and proof (`change_design.md:L105-L107`, E; `change_spec.md:L81-L81`, CP-179).
Load the edit form before timing, use its shown fields and a changed title, and submit the same-origin request through Site.
Judge the edit by successful redirect plus exact saved field delta and preserved fixture, then judge the landing by response and edited title.
Declare fixture/edited title text lengths; duration at least 1 second, refusal/failure, wrong/missing delta or wrong landing gives failed verdict.
Use a separate seeded edit location so neither add nor edit alters the other's 1,000-task start.

#### Behaviours to verify

Add to `tests/integration/test_timed_run.py`; cover T17/T18 (`change_design.md:L149-L150`, Test Additions).

- `test_timed_run_reports_edit_and_landing_at_exact_volume` — report both labels, 1,000 tasks/20 comments each and actual edited title length; retain all project/add report assertions.
- `test_timed_edit_uses_loaded_form_baseline_and_same_origin` — record the request sequence; form GET precedes measured POST, posted shown values come from it, one changed title, landing measured separately.
- `test_timed_edit_preserves_every_other_fixture_value` — real SavedData contains exact title delta with unchanged other fields/entities/comments/counters/tuple positions; fixture remains 1,000 tasks; never touch product data.
- `test_timed_edit_fails_on_refusal_failure_or_false_success` — scripted refusal/failure response and successful-looking redirect with no save, incorrect delta or unrelated mutation all fail the verdict.
- `test_timed_edit_landing_fails_on_missing_or_wrong_page` — missing/bad address, non-200 landing or wrong title fails; no invalid-address request counts as successful landing.
- `test_timed_edit_requires_each_duration_below_one_second` — injected timer proves each measurement separately passes below 1 second and fails at/above 1 second; retain add boundary tests unchanged.
- `test_timed_edit_and_add_have_independent_volume_fixtures` — the edit starts and ends with 1,000 tasks; the existing add still starts with 1,000 and preserves its earlier-task snapshot while producing 1,001.

#### Implement

Infer from failing tests.

```text
# Hint:
Measure edit and landing separately; prove the saved field delta and preserved fixture before reporting success. Seed the edit in its own saved-data location so the retained add measurement cannot change its starting volume.
```

#### Verification gate

From the instance worktree root, run:

```sh
pytest products/tracker17/tests/integration/test_timed_run.py
pytest products/tracker17/tests/
python3 products/tracker17/tests/timed_run.py
python3 -m compileall -q products/tracker17/tests
```

For CP-180's final verification, make a disposable copy of the change branch's current committed product; initialize only that copy as a Git repository. Exact preparation and checks:

```sh
VERIFY_ROOT="$(mktemp -d /private/tmp/tracker17-edit-fields.XXXXXX)"
git -C .worktrees/2026-10-11_edit-task-fields archive HEAD products/tracker17 | tar -x -C "$VERIFY_ROOT"
git -C "$VERIFY_ROOT" init --quiet
(cd "$VERIFY_ROOT" && pytest products/tracker17/tests/)
(cd "$VERIFY_ROOT" && pytest products/tracker17/tests/e2e/)
(cd "$VERIFY_ROOT" && python3 products/tracker17/tests/timed_run.py)
(cd "$VERIFY_ROOT/products/tracker17" && ruff format --check .)
(cd "$VERIFY_ROOT/products/tracker17" && ruff check .)
(cd "$VERIFY_ROOT/products/tracker17" && mypy main.py errors.py domain application persistence web)
(cd "$VERIFY_ROOT/products/tracker17" && python3 -m compileall -q domain application web tests)
```

Use the locked test environment on PATH for the archived checks; do not substitute host-tool versions as a pinned-tool verdict (`products/tracker17/docs/nfdr.md:L469-L485`, QC-62; `products/tracker17/pyproject.toml:L11-L17`, dev pins).
Pass: all commands exit 0; both suites collect/run tests; edit and landing each report below 1 second on the owner's machine at the declared exact volume; all existing timing proofs remain intact; Ruff/mypy/compile pass; the archive contains the finished source rather than uncommitted edits.
