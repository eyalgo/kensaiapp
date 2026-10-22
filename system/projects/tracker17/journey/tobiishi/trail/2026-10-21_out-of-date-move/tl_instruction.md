# Tech Lead instruction — out-of-date-move: distinguish a refused press from a cancellation address

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — product paths below are relative to this directory.
**Scope:** Render the two move refusals, preserving the workflow, saving, confirmation and history contracts.
**Inputs read:** change_spec.md no Status line · change_design.md no Status line · project.md no Status line · FDR Settled (version 4) · NFDR Settled (version 15) · SDD Settled (version 11, § 3 read) · ADR index and ADR-0001–ADR-0010 Accepted · CONTENT Settled (version 12, refusal example and RN-26 read) · writing_bar Settled.
**Language resolution:** Python — step 1, project.md Languages; packet: `<CORE>/doctrine/engineering/languages/python/README.md`.

This document owns the implementation scaffold for `tracker17 · tobiishi · 2026-10-21_out-of-date-move`.
`change_spec.md`, `change_design.md` and the eventual `change_text.md` mean siblings of this file.
Commands labelled **worktree root** run from the instance's change worktree; commands labelled
**product root** run from `products/tracker17` within that worktree.

## Project layout

```text
products/tracker17/
  web/
    pages.py                            ← modified: page value and rendering (Task 1)
    routes.py                           ← modified: address context selection (Task 2)
  tests/
    integration/
      test_move_pages.py                ← modified: renderer and context assertions
      test_move_routes.py               ← modified: request/refusal assertions
    e2e/
      test_moves.py                     ← modified: wording and escaping assertions
```

Create no directory, module or `__init__.py`. The five-file delta follows `change_design.md:L31-L57`,
§ 2 Blast Radius. Placement remains in **web**, which owns requests and page building;
`docs/SDD.md:L198-L213`, § 3 The parts, forbids web owning workflow rules or saved data.
The full module set and allowed/forbidden import graph remain owned by
`docs/nfdr.md:L140-L170`, § 1.2 Forbidden imports. Add no part or import edge.

## TL Review Notes

Tech Lead decisions, 2026-10-21:

- **Task boundaries:** retain A then B from `change_design.md:L65-L137`, § 3 Sub-jobs.
  Task 1 includes every existing assertion affected by the renderer's changed default line,
  including address/history expectations while routes still construct the default context.
  Task 2 separates those expectations when routes begin selecting address context. This cut
  respects both atomic-landing edges without leaving either task dependent on unfinished work.
- **Test allocation:** allocate the mixed A+B rows T5, T7 and T9 in
  `change_design.md:L152-L188`, § 5 Test Additions, by the production seam exercised.
  Task 1 owns direct page-model cases and submission paths; Task 2 owns address requests and
  history paths. Existing mixed-context functions keep their non-word assertions throughout.
- **Review-only checks:** put T12's scope/unchanged-file checks in Task 3's review-verified lane.
  These properties compare this branch with its merge base and cease to apply after this change;
  permanent tests would incorrectly constrain later changes. The obsolete phrase also has its
  explicit grep gate, as `change_spec.md:L39-L42`, CP-362–CP-365, requires.
- **Coverage sharpened:** add page-model checks that context affects only a refusal for the
  rendered task, preserving failure/completion precedence and unrelated-row isolation.
  This makes A's context-only constraint observable rather than relying solely on request tests
  (`change_design.md:L77-L99`, § 3 Sub-job A).
- **No new workflow test module:** extend the three test modules the design names.
  `domain/workflow.py:L13-L23`, Checked by, already points to each of them, so QC-11 needs no
  workflow docstring edit. Update the edited test docstrings to name the requirements checked.
- **Gate environment:** `pytest products/tracker17/tests/` from the change worktree root
  returned **1250 passed in 92.68s**, exit 0, on Python 3.14.7 and pytest 9.0.3 with command
  approval for loopback servers and a terminal. The sandboxed run returned **20 failed,
  1200 passed, 30 errors**; the isolated listener check reported `PermissionError` at
  `socket.bind`. A permitted run through plain pipes timed out in the start tests.
  `python3 -c 'import signal; print(signal.getsignal(signal.SIGINT))'` returned `1`
  through pipes and `default_int_handler` in a terminal; `tests/integration/test_start.py:L516-L536`,
  `_run_real_start`, stops its child with SIGINT. Run server checks with loopback permission
  and normal terminal signal handling. These are environment requirements, not product-code
  or test-lane changes. This baseline did not use the locked pytest 9.1.1 from
  `pyproject.toml:L11-L17`, dependency-groups; the final gates still require the locked tools.

## Corrections owed while there

- Owed outside this change's reach: `docs/CONTENT.md:L208-L221`, Message patterns → Error →
  A refusal, fifth example — “Reload the page to see it” describes a reload action the new
  submission line must not offer → replace that example with the settled no-reload submission
  variants consistent with CP-359/CP-362. This carries `change_design.md` § Records this change
  makes false; no task edits a product record.

### Task 1: Refusal context and page rendering (`web/pages.py`, `tests/integration/test_move_pages.py`, `tests/integration/test_move_routes.py`, `tests/e2e/test_moves.py`)

**Dependencies:** None

**What to build:** Extend the existing immutable move page value and render its refusal using
the context and the same ordered allowed-moves tuple supplied to its controls, per
`change_design.md` § 3 Sub-job A.

- Add `MoveRefusalContext` with `SUBMISSION` and `CANCELLATION_ADDRESS`; append the typed
  `MoveOutcome.refusal_context` field with default `SUBMISSION`. Preserve the four existing
  fields, their order and defaults, positional/keyword constructions and immutability.
- Keep `MoveRefusal`'s two codes and both public page-builder signatures/defaults unchanged.
  Extend the private line-building seam and all its call sites together. Context only selects
  a refusal about the task being rendered.
- Within each row/status area, share the supplied query's ordered tuple between the line and
  controls. An empty result selects the no-moves wording. Name no move outside the tuple and
  change neither its order nor its membership.
- Place published strings from sibling `change_text.md` verbatim. Keep the submission prefix
  contract `The status`; CP-359 governs what the submission line communicates and CP-361 fixes
  the address sentence. Preserve every other outcome's words and markup/focus contract.
- Include the existing quoting assertions affected by the changed default renderer. Routes
  still use default submission context in this task; explicit address context is exercised
  directly through the public page builders.

#### Behaviours to verify (extend `tests/integration/test_move_pages.py`, `tests/integration/test_move_routes.py` and `tests/e2e/test_moves.py`)

- `test_move_outcome_retains_existing_construction_and_defaults` — existing four-field
  positional/keyword constructions retain their meaning and use submission context; the
  extended value remains immutable. Design A, T6.
- `test_refusal_context_selects_only_the_rendered_tasks_refusal` — both builders render the
  explicit address context's CP-361 line; context beside no refusal changes neither a failure
  nor completion, creates no outcome, and takes no focus for an absent/foreign task. Preserve
  refusal-before-failure-before-completion precedence. Design A, T6/T7; CP-363.
- `test_refusal_line_and_controls_share_the_supplied_move_order` — inject an allowed-moves
  callable through each public builder, with an ordered tuple different from the workflow's
  normal order. Both named moves and buttons follow that result exactly. An empty result
  names no move. Exercise both refusal codes without patching product names. T6; CP-359/CP-364.
- Extend `test_a_stale_press_is_refused_against_the_saved_status_and_saves_nothing` and
  `test_a_stale_todo_press_after_done_is_refused_and_the_task_stays_done` to cover four saved
  statuses × list/task place. First load the earlier page, change status through the real
  Tracker, then press a move that was offered and is now refused. For a todo landing, start
  in-progress, move back to todo, then press done. Assert current title/status, correct
  redirect/destination, and exact text from `change_text.md`; match the named moves to that
  task's buttons in order, with no moves for terminal statuses. T1; CP-355/CP-358/CP-359.
- Extend `test_a_non_status_or_missing_status_is_refused_and_answered_like_a_stale_press` —
  retain finished, missing, empty and Done cases at both places; preserve the two URL refusal
  codes and assert the same submission wording, destination and current moves. T4; CP-357.
- Keep `test_a_press_on_a_cancelled_task_is_refused_with_the_cancelled_reason` and every
  CP-370 quoting function; replace their default-renderer wording while keeping all other
  assertions. Keep the `The status` prefix assertion in
  `test_move_query_collisions_select_one_interaction_and_focus_owner`. T7/T9; CP-370.
- `test_overtaken_press_uses_the_current_title_as_text` — use `a < b & "c"`, including a title
  changed through the other tab's real action after loading the first page. The saved title
  occurs once in the reason as parsed text, with no injected element or double escaping.
  Cover both places. T5; CP-359/CP-366.
- For every refused request above, snapshot actual saved-file bytes and save count after the
  intervening valid action, before the refused request; compare again after the POST and its
  landing GET. Assert no confirmation, exactly one focused non-control status, the exact line
  as that status's accessible description, no focus on the line, and no reload/link/control
  inside it. T1/T4/T5/T7; CP-358/CP-362/CP-366.
- In `test_stale_first_press_refuses_at_the_visible_current_status`, use submission wording
  and retain focus, viewport, no-strip and saved-bytes assertions. Add browser escaping
  coverage for the submission context in both places using the existing harness. Update the
  history tests' old sentences to the changed default line without removing any history,
  cache-availability or fresh-load assertion; Task 2 changes their context expectation. T9.

#### Held by review

- The one ordered workflow table remains in domain, and both page outputs consume its query
  through application. The injected-tuple test observes sharing; read the renderer diff for
  a copied status-to-moves table or enumeration that those examples might miss. CP-364/QC-16.
- Both refusal titles pass once through `_escape`; a parsed-text test observes escaping,
  while reading the line-building path holds QC-36's one-function constraint.

#### Implement

Infer from failing tests.

```text
# Hint:
Carry context on the existing immutable page value rather than encoding another URL outcome.
Share the ordered tuple supplied by the existing query between the line and the controls;
the tuple is the seam, not a second status-to-moves table.
```

#### Verification gate

From the **worktree root**, run:

```sh
pytest products/tracker17/tests/integration/test_move_pages.py products/tracker17/tests/integration/test_move_routes.py
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/
```

From the **product root**, run:

```sh
python3 -m compileall -q web
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: every command exits 0; new assertions and all retained assertions pass. The browser
suite is a separate invocation; it is not counted as run by the ordinary suite.

### Task 2: Request-derived address refusal (`web/routes.py`, `tests/integration/test_move_routes.py`, `tests/integration/test_move_pages.py`, `tests/e2e/test_moves.py`)

**Dependencies:** Task 1 — uses `MoveRefusalContext`, the appended page-model field and both renderings.

**What to build:** Select `CANCELLATION_ADDRESS` only at the existing `_move_view` branch that
finds the task on this page and finds cancelled absent from the current allowed moves, per
`change_design.md` § 3 Sub-job B. Keep `_move_view`'s result shape, `_move_outcome`'s vocabulary
and precedence, submission exception mappings and redirects, and the resolved response machinery.
No new route, query parameter, outcome code or state between requests is part of this task.

#### Behaviours to verify (extend `tests/integration/test_move_routes.py`, `tests/integration/test_move_pages.py` and `tests/e2e/test_moves.py`)

- `test_cancellation_addresses_at_final_statuses_refuse_as_facts` — cover done/cancelled ×
  confirmation/back-out GET × list/task page. Assert CP-361's exact sentence from
  `change_text.md`, current title/status, no confirmation or move controls for this task,
  status focus/described-by, no focus on the line, 200 with Cache-Control: no-store and no
  reload/link/control within the reason. Compare saved bytes and save count around each GET,
  including repeated loads. Extend `test_confirmation_address_at_a_final_status_shows_the_saved_status`
  without weakening its current assertions. T3/T8; CP-356/CP-360–CP-362/CP-365/CP-366.
- Extend `test_stale_opening_and_confirmation_use_the_saved_workflow_answer` — actually load
  the earlier eligible page/confirmation, then change the task through Tracker to done or
  cancelled. Both an ordinary cancelled POST and the confirming POST retain submission
  wording; the back-out GET uses address wording. Keep the existing eligible transition case.
  For every refusal compare saved bytes/count before the request and through any landing
  GET; assert unchanged destinations, focus, no confirmation and response contract. T2; CP-355.
- Extend `test_confirmation_and_back_out_reads_never_save` — preserve repeated reads and
  restored-trigger assertions; after the intervening saved move take a fresh snapshot and
  compare again after each revisit, now with address wording. T3; CP-360/CP-370.
- `test_address_refusal_shows_the_current_escaped_title` — use `a < b & "c"` and a renamed
  title after an earlier page was loaded, at both places. Assert exactly-once saved title as
  text in the accessible description, no injection/double escaping and byte/count equality.
  T5; CP-361/CP-366.
- `test_reopening_a_refused_submission_keeps_submission_wording` — a recognized refused
  outcome keeps submission context even when an interaction query is also present; unknown
  outcome words select no new code. A refused POST's landing address reopened without a
  press keeps the submission line and saves nothing. T7/T8; spec Out of Scope, first entry.
- Retain `test_first_press_opens_confirmation_without_a_save`,
  `test_missing_confirmation_targets_answer_not_found_without_saving`,
  `test_other_moves_keep_their_first_press_outcomes` and failed-save tests. Cover todo and
  in-progress for both eligible interaction GETs. Missing targets, targets on another page,
  unknown values, outcome collisions and plain pages keep their existing responses. T8.
- Retain `test_a_landing_page_has_exactly_one_autofocus_on_a_non_control_status_element_that_names_the_line`
  and `test_back_out_restores_only_the_selected_trigger`; separate address/submission text
  expectations and keep every focus, placement, trigger-name, per-row and form assertion. T7.
- In `test_real_history_traversal_revalidates_the_confirmation` and
  `test_history_matrix_revalidates_current_saved_status`, use address-specific expectations
  for history returns. Keep every key, geometry, viewport, Back/Forward, fresh-load,
  cache-availability, pinned-browser and saved-bytes assertion. Add browser escaping coverage
  for address refusals through the existing harness; keep Task 1's submission coverage. T9.
- Keep the route enumeration test
  `tests/integration/test_routes.py::test_every_route_leaves_state_and_headers_as_the_rules_say`
  and all four QC-63 tests unchanged: `test_pending_confirmation_response_matches_the_rendered_page`,
  `test_non_confirmation_move_views_keep_their_response_contract`,
  `test_move_interaction_and_outcome_pages_are_not_stored`, and
  `test_move_responses_do_not_clear_site_data`. Pending rendered confirmation remains 202;
  refusal remains 200/no-store; missing-task confirmation remains 404 without no-store. T10.

#### Held by review

- Context is selected from the resolved request and workflow answer, never from message text;
  no last-action store, direct domain import or new refusal type is introduced. Request tests
  observe the two presentations; reading `_move_view` and its imports holds QC-5/QC-8/QC-16.

#### Implement

Infer from failing tests.

#### Verification gate

From the **worktree root**, run:

```sh
pytest products/tracker17/tests/integration/
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/
```

From the **product root**, run:

```sh
python3 -m compileall -q web
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: each command exits 0; both refusal contexts satisfy their complete request matrices,
all four QC-63 layer-3 tests and both history tests pass, and no existing assertion outside
CP-370's wording replacements is lost. Use the product's locked tool environment for the gates.

### Task 3: Verify the bounded product delta (`web/pages.py`, `web/routes.py`, `tests/integration/test_move_pages.py`, `tests/integration/test_move_routes.py`, `tests/e2e/test_moves.py`)

**Dependencies:** Tasks 1 and 2 — reviews their finished product diff and complete text replacements.

**What to build:** A review verdict for the change-only scope and continuity checks in design T12,
against the branch's own merge base. Add no permanent suite test for these properties.

#### Deliverables verified by review

- Obsolete wording is absent from web: from the **worktree root**,
  `grep -rn "the move you pressed" products/tracker17/web` prints nothing and exits 1.
- Workflow, saved-data code, wiring, format/pins, stylesheet, timed run and product records
  remain unchanged: from the **worktree root**,
  `git -C products/tracker17 diff "$(git -C products/tracker17 merge-base main HEAD)" -- domain application persistence main.py errors.py pyproject.toml tests/requirements.txt tests/timed_run.py web/style.css docs`
  prints nothing. This comparison includes uncommitted edits.
- No other product file is changed: from the **worktree root**,
  `git -C products/tracker17 diff --name-only "$(git -C products/tracker17 merge-base main HEAD)" -- . ':(exclude)web/pages.py' ':(exclude)web/routes.py' ':(exclude)tests/integration/test_move_pages.py' ':(exclude)tests/integration/test_move_routes.py' ':(exclude)tests/e2e/test_moves.py'`
  prints nothing. In particular, no harness, route-inventory test, architecture test or new
  test module is changed.
- Read the five-file diff with
  `git -C products/tracker17 diff "$(git -C products/tracker17 merge-base main HEAD)" -- web/pages.py web/routes.py tests/integration/test_move_pages.py tests/integration/test_move_routes.py tests/e2e/test_moves.py`
  from the **worktree root**. Verdict criteria: no second workflow table, no page script, no
  alternate escaping path, no changed confirmation/completion/failure/unrelated-refusal words,
  no response/history mechanism change, and no non-word assertion removed or weakened.
  Every quoting function CP-370 names remains, with the context-appropriate replacement.
- The edited test modules name their checked requirements in their docstrings and
  `tests/architecture/test_trace.py` passes; no new pointer in workflow is needed because
  the named test-module set stays the same. T11; CP-368.

#### Implement

Verified by review — no test.

#### Verification gate

Run every review check above from its stated directory and record a verdict per criterion.
From the **worktree root**, run:

```sh
pytest products/tracker17/tests/architecture/test_trace.py
pytest products/tracker17/tests/integration/
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/
```

From the **product root**, run:

```sh
python3 -m compileall -q web
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: every review criterion holds, each test/static command exits 0 and the full suites have
no failures. The no-match grep exits 1 by design; the empty git diffs exit 0.
