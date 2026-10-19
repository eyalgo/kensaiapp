# Tech Lead instruction — task-labels: add, remove and restore task labels

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every code and test path below is relative to it.
**Scope:** Implement CP-182–CP-210 in `change_spec.md` § Rules, using the interfaces in `change_design.md` § 3, for `tracker17 · tobiishi · 2026-10-12_task-labels`.
**Inputs read:** change_spec no Status line · change_design no Status line · project card no Status line · ADR index no Status line · ADR-0001–0009 Accepted · FDR Settled (version 4) · NFDR Settled (version 11) · SDD Settled (version 9, § 3) · writing_bar Settled
**Language resolution:** Python — step 1, `system/projects/tracker17/project.md:L12-L12`, `Languages:`; `core/doctrine/engineering/languages/python/README.md` § The six concerns and where each is answered, its five local destinations, and `core/doctrine/engineering/testing_python.md` read.

This document owns the task cut, verification behaviours and execution gates. The behavioural contract remains `change_spec.md` § Rules; the structural contracts remain `change_design.md` §§ 2–4 and `docs/SDD.md:L195-L205`, § 3 The parts.

---

## Project layout

```text
products/tracker17/
  domain/
    labels.py                              ← new
    tasks.py                               ← modified
    refusals.py                            ← modified
    __init__.py                            ← modified, re-exports only
  application/
    tracker.py                             ← modified
    __init__.py                            ← modified, re-exports only
  web/
    pages.py                               ← modified
    routes.py                              ← modified
  tests/
    unit/
      test_labels.py                       ← new
      test_tasks.py                        ← modified
    architecture/
      test_shapes.py                       ← modified
      test_trace.py                        ← modified
    integration/
      test_label_tracker.py                ← new
      test_label_pages.py                  ← new
      test_label_routes.py                 ← new
      test_label_listener.py               ← new
      test_saved_data.py                   ← modified
      test_start.py                        ← modified
      test_routes.py                       ← modified
      test_timed_run.py                    ← modified
    e2e/
      test_labels.py                       ← new
    timed_run.py                           ← modified
```

Create the listed new files in the existing directories; create no package or directory beyond this tree. Placement follows `change_design.md:L21-L29`, § 2 Blast Radius, and `docs/SDD.md:L195-L205`, § 3 The parts. The five-part module set and allowed/forbidden imports are `docs/nfdr.md:L121-L154`, § 1.2 Forbidden imports; `main.py`, `errors.py` and production `persistence/` require no edit for this change (`change_design.md:L25-L28`, § 2).

Read `change_text.md` in this change before placing published wording; use its strings verbatim for visible text, accessible names, refusal/failure messages and label-action console messages (`change_spec.md:L25-L26`, CP-184–CP-185; `change_design.md:L6-L6`, Publishes text).

## TL Review Notes

Tech Lead decisions, 2026-10-12:

- **Atomic task cut:** Task 1 joins A with D's restoration/start checks and the label-only CP-209 fixture/assertion corrections. The design declares no green point between the constructor change and those fixtures, or between the feature module and its architecture checks (`change_design.md:L113-L116`, Atomic-landing edges). This cut keeps every replacement assertion beside the new rule that justifies it.
- **Trace-path scaffolding:** Task 1 creates requirement-docstring-only files for the new checking paths owned by Tasks 2–4. The label entry must name every checking test module, and the pointer check requires every named path to exist (`change_spec.md:L68-L68`, CP-200; `tests/architecture/test_trace.py:L96-L107`, `test_every_path_named_in_the_entry_docstring_exists`). These files contain no imports of later interfaces and no placeholder tests; their owning tasks add the actual behaviours. This resolves the atomic edge without moving later behaviours into Task 1.
- **Task split:** C is split into Task 3's plain-value page rendering and Task 4's submission/query handling with listener/browser proofs. `web/pages.py` already renders arguments without calling the site (`web/pages.py:L1-L8`, opening docstring), so its tests can fail independently before the routes exist. Task 4 uses Task 3's presentation contracts, matching `change_design.md:L78-L91`, sub-job C.
- **Hint adapted:** Task 3 carries C's focus approach and Task 4 carries its whole URL/focus hint (`change_design.md:L124-L124`, § 4 C). URL building is omitted from Task 3's hint because the page takes plain values rather than request/query metadata.
- **Boundary coverage placement:** D's action/restart proofs ride Task 2, whose new application actions perform the saves they exercise. The saver already serializes labels and restores through the domain constructor (`persistence/saved_data.py:L122-L140`, `_encode_task`; `persistence/saved_data.py:L176-L202`, `_decode_task`), so a separate later task would have an already-satisfied subject. No production persistence edit is needed; D's new rejection/start behaviours remain test-first in Task 1.
- **Type precision:** Use enums for the label refusal codes `empty`, `too-long`, `not-carried` and the failed-action codes `add`, `remove` in the plain presentation contract. The design names closed vocabularies without fixing their type (`change_design.md:L74-L78`, sub-job C). Existing page vocabularies are enums (`web/pages.py:L38-L97`, `AssigneeRefusal`, `TaskEditRefusal`, `FailedAction`); this strengthens precision without changing the address protocol or adding a module.
- **Contract reconciled:** The request header says both label refusals retain typed text, but CP-191 and Locked Answers Gap 1 discard an overlong submitted value (`change_spec.md:L6-L6`, Request; `change_spec.md:L35-L35`, CP-191; `change_spec.md:L182-L182`, Locked Answers). Tasks 3–4 follow that explicit resolution and `docs/adr/0006-last-action-travels-in-the-page-address.md` § Decision. Empty refusal retains its empty input; overlong refusal carries and renders none of the submitted text, including forged retained query text.
- **Forged outcome precedence:** Pin refusal before failure before completion, and added before removed when both completion keys are present. The design requires one label outcome and refusal/failure precedence but leaves the ties implicit (`change_design.md:L74-L91`, sub-job C). This follows the existing page outcome ordering (`web/pages.py:L744-L787` `_outcome_line`, “refusal, then failure, then success (added before removed)”). A recognized label outcome also suppresses competing edit-form autofocus/refusal/failure presentation on a mixed address; without this, `TaskEditForm` can create a second autofocus target (`web/pages.py:L569-L640`, `_edit_form`). Addresses with no recognized label outcome keep existing edit presentation.
- **Behaviour added:** Task 4 checks CR LF and lone CR normalization on crafted add/remove requests. The design requires the decoder's existing normalization but does not enumerate that check in § 5 (`change_design.md:L70-L70`, sub-job C; `web/routes.py:L156-L158`, `_line_feeds`). This guards exact comparison after the single permitted conversion, rather than testing trimmed values.
- **Native boundary proof:** The 200-code-point non-BMP case belongs to domain and crafted-request tests, while browser tests check the actual `maxlength` and permitted native entry. The distinction follows `docs/adr/0007-text-counted-once-in-domain-in-code-points.md` § Consequences and the design's Native maximum review note; no browser test forces a field past its native limit.
- **Gate evidence:** From the change worktree, `pytest products/tracker17/tests/` collected 696 tests and initially ended `5 failed, 675 passed, 16 errors`, with socket-bind `PermissionError: [Errno 1] Operation not permitted`. The same command, approved for loopback listener access, exited 0 with `696 passed in 19.74s`. The card command runs the intended non-browser suite; no command substitution or red-at-baseline task lane is warranted. Browser verification remains a separate invocation (`tests/conftest.py:L38-L56`, `pytest_ignore_collect`).
- **Final gate location:** Task 5 includes the spec's archive-copy pytest gates in addition to the worktree gate, because CP-210 explicitly requests both suites on a committed disposable copy (`change_spec.md:L104-L106`, CP-210). Initialize only that disposable directory as Git so QC-47's ignore check has its prerequisite (`docs/nfdr.md:L392-L400`, QC-47).

### Task 1: Domain label rules and atomic restoration boundary (`domain/labels.py`, `domain/tasks.py`, `domain/refusals.py`, `domain/__init__.py`, `tests/unit/test_labels.py`, `tests/unit/test_tasks.py`, `tests/architecture/test_shapes.py`, `tests/architecture/test_trace.py`, `tests/integration/test_saved_data.py`, `tests/integration/test_start.py`, new test-file scaffolds listed below)

**Dependencies:** None

**What to build:** The ordered label collection rules, immutable task outcomes/actions, and strengthened restoration contract in `change_design.md:L35-L52`, sub-job A; prove unreadability through the existing real saver and start boundaries in § 5 T9/T10/T17.

Update the task entry/restoration docstrings to include label validation while retaining the unrestricted-comment contract (`domain/tasks.py:L1-L21`, entry docstring; `L270-L277`, `restore_task`).

Expose `check_label`, `check_saved_labels`, `add_label`, `remove_label`, frozen `TaskLabelOutcome(task, changed)`, `add_task_label` and `remove_task_label`, with the design's signatures and return shapes. Define `EmptyLabel`, `LabelNotCarried`, `RepeatedSavedLabel` and `TextField.LABEL` in `domain/refusals.py`, using existing `TextTooLong` and `SHORT_TEXT_MAX`; place collection decisions in `labels.py` and task lookup/replacement in `tasks.py` (`change_design.md:L41-L52`, A interfaces).

Update only the label assertions and their requirement docstrings at the CP-209 sites, including the dependent round-trip labels assertion (`change_spec.md:L98-L102`, CP-209; `change_design.md` Architect Review Notes, “CP-209's fixture and its dependent assertion”). Preserve every non-label assertion, historical off-list assignee load and unrestricted comment-content load. Create `tests/integration/test_label_tracker.py`, `test_label_pages.py`, `test_label_routes.py`, `test_label_listener.py` and `tests/e2e/test_labels.py` as requirement-docstring-only trace scaffolds; no future interface imports or future behavioural assertions belong in these scaffolds.

#### Behaviours to verify

In `tests/unit/test_labels.py` (design § 5 T1; CP-182, CP-187–CP-193, CP-202):

- `test_empty_label_is_refused` — raise `EmptyLabel` only for the exact empty value.
- `test_overlong_label_is_refused_by_code_point_count` — raise `TextTooLong` identifying LABEL and the domain maximum for 201 code points, including non-BMP input.
- `test_label_at_maximum_is_accepted_verbatim` — accept exactly 200 code points, including a non-BMP character and surrounding spaces.
- `test_spaces_only_label_is_accepted` — retain all spaces without stripping.
- `test_new_label_appends_after_existing_labels` — preserve prior order and report changed.
- `test_repeated_label_add_returns_unchanged_collection` — retain one exact instance and report no change; case-distinct and space-distinct values append.
- `test_remove_keeps_survivors_in_order` — remove first, middle, last and the sole label without reordering.
- `test_remove_of_absent_label_is_refused` — raise `LabelNotCarried` for absent, case-mismatched, empty and overlong absent values; removal applies membership, not add-validation.
- `test_saved_labels_are_ordered_and_unique_per_task` — reject exact repetition with `RepeatedSavedLabel`; accept empty collections and distinct exact values.

In `tests/unit/test_tasks.py` (design § 5 T2; CP-194, CP-197, CP-199, CP-201):

- `test_label_actions_change_only_target_labels` — preserve other tasks, every non-label task field, People values and both counters; the new outcome reflects the resulting task and domain change report.
- `test_duplicate_task_label_reports_no_change` — retain the original state and labels after an exact repeated add.
- `test_missing_task_precedes_label_validation` — both actions raise `TaskNotFound` for a missing task, including invalid add and absent remove values.
- `test_label_success_and_refusal_leave_input_immutable` — success and each typed refusal leave the input values untouched.
- `test_restore_task_checks_saved_label_rules` — reject empty/overlong/repeated labels and accept empty, spaces-only, case-distinct and boundary collections through the unchanged constructor signature.

In `tests/integration/test_saved_data.py` and `tests/integration/test_start.py` (design § 5 T9/T10/T17; CP-197–CP-198, CP-205, CP-209):

- `test_saved_label_break_refuses_whole_file_unchanged` — one case each for empty, 201-code-point and repeated labels, with a valid task before the invalid task; `UnreadableData` exposes no partial state and preserves bytes and directory listing.
- `test_valid_saved_labels_load_verbatim` — accept no labels, spaces-only, exactly 200 code points including non-BMP, case-distinct values, and the same label on different tasks.
- `test_invalid_saved_labels_stop_start_with_existing_message` — one case per break calls real `main.start`, returns nonzero, prints exactly the existing location-bearing unreadable line, produces no ready line or listener, and preserves bytes/listing.
- Keep the existing historical-assignee/comment assertions and all-fields round-trip assertions with valid unique labels replacing only invalid label fixtures.

In `tests/architecture/test_shapes.py` and `tests/architecture/test_trace.py` (design § 5 T12; CP-200–CP-201, CP-209):

- Extend landed-feature containment and entry checks to `labels`; preserve existing state-field, excluded-feature and previous-entry assertions.
- Verify the new entry names FR-23/FR-40, `application/tracker.py`, `application/__init__.py`, `web/pages.py`, `web/routes.py` and every label-checking module in the layout; each path exists and every new test module names its requirements.
- Retain existing whole-tree import, reach and frozen-value checks.

#### Held by review

- Collection rules live in `domain/labels.py`; task lookup/replacement lives in `domain/tasks.py`; neither defines published wording or reaches I/O. Import/reach tests cover capability limits, while the ownership and no-wording clauses require reading the diff (`docs/SDD.md:L195-L205`, § 3 The parts; `docs/nfdr.md:L160-L166`, QC-20).

#### Implement

Infer from failing tests.

# Hint:
Keep collection rules independent of Task so restoration shares validation without an import cycle. Use ordered tuples and exact membership; a set used for saved-repetition detection is auxiliary and never the returned order (`change_design.md:L122-L122`, § 4 A).

#### Verification gate

From `.worktrees/2026-10-12_task-labels`, run `pytest products/tracker17/tests/`. Pass: every domain, restoration, start and architecture behaviour above passes; all previously passing tests remain green; trace scaffolds import without using later interfaces.

### Task 2: Application label actions and restart proofs (`application/tracker.py`, `application/__init__.py`, `tests/integration/test_label_tracker.py`, `tests/integration/test_saved_data.py`)

**Dependencies:** Task 1 — domain actions, outcome and refusal types.

**What to build:** `Tracker.add_task_label` and `Tracker.remove_task_label`, returning the domain outcome, saving before publishing only when it reports a change, and re-exporting the plain values/refusal types web needs (`change_design.md:L56-L64`, sub-job B). Add D's real-file action/restart proofs here (§ 5 T11) without modifying production persistence.

#### Behaviours to verify

In `tests/integration/test_label_tracker.py` (design § 5 T3; CP-187–CP-194, CP-199, CP-204; QC-49):

- `test_label_action_saves_once_before_publication` — each changed add/remove reaches the injected saver exactly once while application reads still show the preceding state, then publishes the saved result.
- `test_repeated_add_hands_saver_nothing` — exact duplicate returns unchanged and sends no save; case-distinct and space-distinct values change normally.
- `test_label_refusal_hands_saver_nothing` — each domain refusal, including missing task for either action, leaves current state unchanged and sends nothing.
- `test_failed_label_save_leaves_previous_state_current` — a failing saver for add and remove propagates failure, retains all fields/current labels and yields no success outcome.
- `test_label_actions_preserve_unrelated_reads_and_fields` — read-back/list rows, other tasks, edit context, People and counters remain consistent.

In `tests/integration/test_saved_data.py` (design § 5 T11; CP-198–CP-199):

- `test_labels_survive_add_reload_remove_reload` — real Tracker actions save through real `SavedData`; newly constructed application instances load the exact add/remove result in order.
- `test_label_actions_preserve_saved_shape_and_other_values` — compare exact state/task/comment key sets, People values, counters and every non-label task field across both saves/reloads.

#### Held by review

- Application consumes the domain report without comparing states or deciding label membership; web-facing refusal exports originate in domain. The save-order tests witness publication, but rule ownership needs reading the diff (`docs/nfdr.md:L167-L182`, QC-21; `docs/nfdr.md:L56-L67`, QC-5).

#### Implement

Infer from failing tests.

#### Verification gate

From `.worktrees/2026-10-12_task-labels`, run `pytest products/tracker17/tests/`. Pass: Task 2's fake-saver and real-file restart proofs pass and the full suite stays green.

### Task 3: Plain label presentation and task-page area (`web/pages.py`, `tests/integration/test_label_pages.py`)

**Dependencies:** Task 2 — application re-exports; Task 1 — existing trace scaffold.

**What to build:** An optional immutable label presentation value separate from `TaskEditForm`, with enum refusal/failure vocabularies, and the label area following the existing edit form (`change_design.md:L74-L91`, sub-job C). Render all published strings from `change_text.md`; preserve existing callers and the Labels cell renderer.

#### Behaviours to verify

In `tests/integration/test_label_pages.py` (design § 5 T4; CP-182–CP-186, CP-187–CP-193, CP-199, CP-203):

- `test_task_page_shows_ordered_labels_with_separate_forms` — exact labels in saved order, each with its Remove form and hidden exact value, plus a visibly labelled Add field; no nested forms or changed edit fields.
- `test_label_less_task_shows_sentence_and_add` — the published no-labels sentence and usable Add form appear together.
- `test_remove_accessible_name_names_label_and_task` — include visible “Remove” unbroken, the exact label and task name, following the text artifact.
- `test_label_maxlength_comes_through_application` — equal to the supplied domain maximum, with no adjacent maximum-length note.
- `test_label_page_escapes_text_and_attributes` — text, whitespace, hidden values and accessible names preserve `<`, `&`, quotes and surrounding spaces as literal data through `_escape`; position-based IDs never embed labels.
- `test_added_label_is_the_only_focus_target` — exact added label text element has native autofocus, `tabindex="-1"` and its completion description, with no competing task/edit outcome.
- `test_removed_label_describes_focused_task_heading` — heading at the sheet's top takes focus and the removal completion is its description.
- `test_label_refusal_focus_and_retention_match_condition` — empty/too-long add focuses the field with the adjacent reason; too-long retains no input; stale remove focuses the section with its reason.
- `test_label_save_failure_focus_names_failed_action` — Add form or Remove section takes focus with its failure description, retained permitted input, no completion and no Python error text.
- `test_plain_label_area_leaves_existing_edit_outcome_intact` — no label autofocus/completion on the ordinary page; existing add-task/edit-task presentation remains valid without a recognized label outcome.
- `test_mixed_label_outcomes_produce_one_focus_and_description` — refusal, failure, added, removed precedence and suppression of competing edit/task outcomes follow the TL decision; completion/reason text never itself takes focus.

#### Held by review

- Every new typed insertion uses `_escape`; presentation owns no validation, trimming or membership decisions. The single escaping seam and rule ownership require reading the diff (`docs/nfdr.md:L278-L284`, QC-36; `docs/nfdr.md:L190-L194`, QC-23).

#### Implement

Infer from failing tests.

# Hint:
Use fragment-free native autofocus on one focusable target with the outcome line as its accessible description, following ADR-0003/0006 and SDD RT-9 (`change_design.md:L124-L124`, § 4 C). Render the supplied plain presentation value; keep address construction in `web/routes.py`.

#### Verification gate

From `.worktrees/2026-10-12_task-labels`, run `pytest products/tracker17/tests/`. Pass: the plain page tests pass, the existing edit/list renderer assertions remain green, and page tests use plain values without calling label routes.

### Task 4: Label request handling, real listener and browser proofs (`web/routes.py`, `tests/integration/test_label_routes.py`, `tests/integration/test_label_listener.py`, `tests/integration/test_routes.py`, `tests/e2e/test_labels.py`)

**Dependencies:** Task 2 — Tracker actions; Task 3 — presentation value and page rendering.

**What to build:** Register POST `/tasks/<id>/labels` and `/tasks/<id>/labels/remove`, each with form field `label`, under the existing request lock/check. Map domain refusals by type, publish the design's label-specific query protocol through `_address`, and parse it into Task 3's presentation without changing state on GET (`change_design.md:L70-L91`, sub-job C).

#### Behaviours to verify

In `tests/integration/test_label_routes.py` (design § 5 T5–T7; CP-187–CP-199, CP-203):

- `test_label_add_redirects_then_reads_saved_result` — real Site/Tracker/domain with injected clock/saver accepts exact input, spaces-only, surrounding spaces, case-distinct labels and a crafted 200-code-point non-BMP value; appends after existing labels and redirects 303 without a fragment.
- `test_duplicate_add_redirects_plain_without_save_or_message` — exact repeat saves nothing, renders neither completion nor refusal, and changes no bytes with a real saver.
- `test_label_remove_redirects_with_survivors_in_order` — remove-middle keeps order and remove-last shows the published empty area, followed by the removal completion.
- `test_each_label_refusal_preserves_saved_bytes_and_shows_reason` — one case each for empty add, overlong add, absent remove and missing task for each action; follow redirects, assert the right field/section or task-not-found page and unchanged real-file bytes.
- `test_overlong_label_is_absent_from_redirect_and_landing` — retain none of the sent text; forged `label` beside recognized `too-long` is also discarded.
- `test_normalized_label_requests_use_exact_membership` — crafted CR LF/lone CR values become LF before both actions; perform no other conversion, and remove the normalized saved value exactly.
- `test_label_save_failure_reports_failure_without_publication` — injected failing saver for each action leaves current/file state intact, shows published failure wording and permitted input, writes action/error at the existing console site and shows no Python error text or success line.
- `test_label_outcome_query_is_stateless_and_presence_based` — preserve blank-vs-absent query values; unknown refusal/failure codes alone consume no retained text; reload and back-equivalent GETs never save; mixed recognized flags obey Task 3 precedence.
- `test_stale_label_action_checks_current_state` — a second removal from a stale page refuses without saving, and an exact add already completed elsewhere is a no-op.
- `test_label_routes_keep_request_and_response_policy` — each new route rejects wrong Host and prohibited/missing fetch marks before action execution; malformed UTF-8 retains the existing 400; accepted submissions are `same-origin`, answer 303 with policy and no cookie, and serialize through the save.
- `test_labels_cell_keeps_existing_rendering_after_actions` — real-file success/reload/list read-back shows ordered comma-joined exact labels or `none`, without changing the cell's renderer.

In `tests/integration/test_label_listener.py` (design § 5 T8; CP-203):

- `test_real_listener_serves_label_area_and_actions` — run the existing real loopback listener with real application/domain and handed-in saver/clock; exercise populated/empty pages, add, repeat, remove, both add refusals and stale remove, following redirects and reading the project list; mark every submission `same-origin`.

In `tests/integration/test_routes.py` (design § 5 T13; CP-206):

- Extend the route enumeration's accepted setup with both label routes without weakening its state/policy/no-cookie assertions.
- Extend `test_no_socket_connection_is_made` to drive add and remove under the existing audit hook.
- `test_label_actions_hand_recording_saver_only_saves` — run both actions and subsequent reads and assert the saver received only saves, never loads.

In `tests/e2e/test_labels.py` (design § 5 T14/T15; CP-185–CP-188, CP-192–CP-195, CP-207):

- `test_keyboard_label_add_focuses_label_with_accessible_description` — Chromium against real `main`; operate by keyboard, assert exact added text has browser focus, is in view, is outside ordinary Tab stops, and has the completion as its computed accessible description.
- `test_keyboard_label_remove_and_refusals_focus_the_action` — keyboard-only remove focuses the heading with its description; empty add focuses its field, and stale remove focuses its label section, each with the computed reason.
- `test_markup_label_is_literal_on_task_and_project_list` — native entry of `<`, `&` and quotes, with surrounding spaces, reads back literally in both locations and accessible naming; check the field's domain-supplied native maximum without forcing over-limit entry.

#### Held by review

- Keep one console failure boundary, map refusals by type rather than message, and keep request/outcome state out of module caches or cookies. Tests witness failures and responses; inspect the diff for the ownership/no-hidden-state clauses (`docs/nfdr.md:L57-L85`, QC-5/QC-8; `docs/nfdr.md:L190-L194`, QC-23; `docs/nfdr.md:L450-L457`, QC-56/QC-57).

#### Implement

Infer from failing tests.

# Hint:
Carry label outcomes through the shared URL builder; use fragment-free native autofocus on one focusable target with the outcome as its accessible description, following ADR-0003/0006 and SDD RT-9 (`change_design.md:L124-L124`, § 4 C).

#### Verification gate

From `.worktrees/2026-10-12_task-labels`, run `pytest products/tracker17/tests/` and separately `pytest products/tracker17/tests/e2e/`. Pass: both exit 0 with tests collected; real listener, request/refusal/failure and computed browser focus/description proofs pass; the existing browser regressions remain green.

### Task 5: Label timing and committed-copy gates (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** Task 4 — label routes and landing protocol; Task 2 — real saved action results.

**What to build:** Add and remove measurements and harness self-tests at 1,000 tasks with 20 comments each, with actual ordinary label lengths stated in the report (`change_design.md:L103-L109`, E; § 5 T16). Keep fixture setup and saved-delta inspection outside measured intervals; report submission, landing and their total for each label action. A total at or above one second fails, even if both separate intervals are below one second.

#### Behaviours to verify

In `tests/integration/test_timed_run.py` (design § 5 T16; CP-208):

- `test_timed_run_reports_label_add_and_remove_at_volume` — real saver/request path performs both actions at the stated task/comment volume and reports label lengths, each submission, each landing and each total beside existing measurements.
- `test_timed_label_requests_are_same_origin` — recording request collaborators witness the required mark and exact action/landing addresses.
- `test_timed_label_actions_require_exact_saved_delta` — success is the intended ordered label change only, with every non-label field, other task and counter preserved; a 303 with no save or wrong saved delta fails.
- `test_timed_label_refusal_or_failure_is_not_success` — each action rejects refused/failed responses and never passes by timing them.
- `test_timed_label_landing_must_show_intended_result` — missing/wrong redirect or landing status, wrong task or wrong shown label result fails.
- `test_timed_label_total_is_strictly_below_one_second` — injected deterministic timer proves below-bound success, equality/over-bound failure and two separately short intervals whose sum reaches/exceeds the bound, for add and remove.
- `test_timed_label_fixtures_leave_product_data_untouched` — use the harness's own temporary locations and preserve the product's `data/` state.

#### Implement

Infer from failing tests.

# Hint:
Measure actual actions and their landing reads against the real saver, and validate the saved delta outside the timing interval; a redirect alone does not prove success (`change_design.md:L126-L126`, § 4 E).

#### Verification gate

From `.worktrees/2026-10-12_task-labels`, run `pytest products/tracker17/tests/`. From Product root, run:

```sh
python3 tests/timed_run.py
python3 -m compileall -q main.py errors.py domain application persistence web tests
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: each command exits 0; new harness self-tests pass; the timing report includes both label actions with the intended saved delta and submission-plus-landing result strictly below one second; existing measurements remain successful (`change_spec.md:L96-L106`, CP-208–CP-210; `core/doctrine/engineering/languages/python/quality_gates.md` § The two gates).

After the code is present in HEAD, run CP-210's committed-copy checks from the change worktree, with the product's pinned test environment on PATH:

```sh
set -eu
set -o pipefail
LABEL_CHECK_COPY=$(mktemp -d /private/tmp/tracker17-labels-check.XXXXXX)
git -C .worktrees/2026-10-12_task-labels archive HEAD products/tracker17 | tar -x -C "$LABEL_CHECK_COPY"
git -C "$LABEL_CHECK_COPY" init -q
(
  cd "$LABEL_CHECK_COPY" || exit 1
  pytest products/tracker17/tests/ || exit
  pytest products/tracker17/tests/e2e/ || exit
  cd products/tracker17 || exit 1
  python3 tests/timed_run.py || exit
  ruff format --check . || exit
  ruff check . || exit
  mypy main.py errors.py domain application persistence web
)
```

Pass: both pytest invocations collect tests and exit 0; the timed run and all three quality checks exit 0; the archive copy alone receives Git initialization. The copy supplies the repository required by QC-47, while both suites are explicitly owed by CP-210 (`change_spec.md:L104-L106`, CP-210; `docs/nfdr.md` § 4, QC-47). This gate claims no VoiceOver speech verification: computed descriptions are the browser observable specified by CP-207, and speech remains the separate condition in `docs/nfdr.md` NFDR Review Notes RN-15.
