# Tech Lead instruction — comments-on-the-page: write, show and restore task comments

**Date:** 2026-10-12
**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17
**Scope:** Deliver CP-240–CP-272 and CP-274–CP-275 with domain-owned comment rules, a saved application action and the task-page comment area; carry the design's CP-273 exclusion.
**Inputs read:** change_spec.md no Status line · change_design.md no Status line · deferred_decisions.md no document Status line · project.md no Status line · SDD Settled version 10 (§ 3 and RT-4) · FDR Settled version 4 · NFDR Settled version 12 · ADR-0001–ADR-0009 Accepted · writing_bar Settled
**Language resolution:** Python, from `system/projects/tracker17/project.md:L12-L12` `Languages:`; packet `core/doctrine/engineering/languages/python/README.md:L13-L22` § The six concerns and where each is answered, including its five local destinations and `core/doctrine/engineering/testing_python.md`.

This document owns task placement, dependencies, test behaviours and verification gates for `tracker17 · tobiishi · 2026-10-12_comments-on-the-page`. Every product path below is relative to Product root; `change_spec.md`, `change_design.md` and `deferred_decisions.md` name inputs beside this document.

The output belongs beside the spec and design under `system/projects/tracker17/journey/tobiishi/2026-10-12_comments-on-the-page/`, per `core/doctrine/setup/kensaiapp_structure.md:L2089-L2093` § 2, “Holds the change arc”.

---

## Project layout

Placement follows `docs/SDD.md:L199-L232` § 3, “The parts, and the seams between them”, and `docs/nfdr.md:L129-L150` § 1.2, “Forbidden imports”; the file delta follows `change_design.md:L23-L36` § 2, “Blast Radius”.

```text
products/tracker17/
  domain/
    comments.py                              ← new
    tasks.py                                 ← modified
    refusals.py                              ← modified
    __init__.py                              ← modified, re-exports only
  application/
    tracker.py                               ← modified
    __init__.py                              ← modified, re-exports only
  web/
    pages.py                                 ← modified
    routes.py                                ← modified
    style.css                                ← modified
  tests/
    unit/
      test_comments.py                       ← new
      test_tasks.py                          ← modified
    architecture/
      test_shapes.py                         ← modified
      test_trace.py                          ← modified
    integration/
      test_comment_tracker.py                ← new
      test_comment_pages.py                  ← new
      test_comment_routes.py                 ← new
      test_saved_data.py                     ← modified
      test_start.py                          ← modified
      test_task_pages.py                     ← modified
      test_routes.py                         ← modified
    e2e/
      test_comments.py                       ← new
```

Create the five new test modules and `domain/comments.py` in the existing directories. Add no package or `__init__.py`. The full code-part set remains `domain`, `application`, `persistence`, `web`, `main.py` and `errors.py` (`docs/nfdr.md:L32-L37,L129-L150` §§ 1.1–1.2). Keep the existing inward import edges: application and persistence reach domain; web reaches application; main wires all four; errors reaches no product part (same § 1.2).

Keep `persistence/saved_data.py`, `main.py`, the clock/saver contracts and `tests/conftest.py` unchanged, as the design's adapter/start contracts require no production delta (`change_design.md:L31-L34,L70-L76`). Keep `tests/timed_run.py` and `tests/integration/test_timed_run.py` byte-identical to `3b5746f91d70763ea2115f896c1d694b7ab77e89`, the branch base returned by `git merge-base main HEAD` in this planning run.

Use the test environment pinned by `pyproject.toml` and `tests/requirements.txt`, with Chromium available (`docs/SDD.md:L290-L310` RT-4; `docs/nfdr.md:L305-L309,L479-L501` QC-39, QC-62). Each gate names both suites explicitly. A missing dependency, browser, socket permission or collected test is a failed gate, not permission to skip coverage (`core/doctrine/engineering/languages/python/quality_gates.md` § The two gates).

## Corrections owed while there

- Owed outside this change's reach: `docs/nfdr.md:L730-L738` RN-15 — “no product code has moved since” the recorded People focus run cannot describe the tree after this comment change → retain the dated People result and its SHA as evidence for that tree, and distinguish the new comment-focus coverage and its own measured verdict. The record's historical result remains its own; this plan supplies no new browser verdict.

## TL Review Notes

Decisions below are the Tech Lead's, 2026-10-12.

- **Gate corrected:** The card's `pytest products/tracker17/tests/` omits browser tests: `tests/conftest.py:L33-L48` § collection rule includes e2e only when the invocation explicitly names that directory. `pytest products/tracker17/tests/` collected 937 items, none from e2e, in this run. Every task therefore gates both that command and `pytest products/tracker17/tests/e2e/`. This resolves the spec's CP-275 and design T21 claim about implicit collection while retaining the existing separate-suite contract (`change_spec.md:L106-L108` CP-275; `change_design.md:L151-L151`; `docs/nfdr.md:L553-L557` § 10).
- **Baseline execution context:** Sandboxed `pytest products/tracker17/tests/` returned `14 failed, 899 passed, 24 errors`, including socket-bind `PermissionError: [Errno 1] Operation not permitted`. The approved non-terminal invocation returned `6 failed, 931 passed in 221.19s`, with the six start cases failing on `TimeoutExpired`. The signal probe `python3 -c 'import signal; print("SIGINT handler:", signal.getsignal(signal.SIGINT))'` returned `SIGINT handler: 1` without a terminal and `SIGINT handler: <built-in function default_int_handler>` with one; `tests/integration/test_start.py:L517-L535` sends SIGINT and waits for the child to stop. Approved `pytest products/tracker17/tests/ -q` in a terminal returned `937 passed in 41.22s`, exit 0. Run localhost/browser checks with their required permissions and a terminal session. These execution conditions release no test assertion and establish no product red at baseline.
- **Browser prerequisite recorded:** `pytest products/tracker17/tests/e2e/ --collect-only -q` exited 4 with `ModuleNotFoundError: No module named 'playwright'` in this run's host Python. Browser acceptance is unmeasured by that invocation. The explicit browser gates require the pinned environment, and carry no skip or pass exemption (`docs/SDD.md:L290-L310` RT-4).
- **Task split:** Design sub-job D combines page rendering and submission. Task 4 owns the presentation vocabulary, task-page GET and stylesheet; Task 5 owns POST and browser action coverage. Task 4 can verify a page supplied valid restored comments and outcome addresses without calling the new action, so the split has a green point and no cross-part atomic edge (`change_design.md:L78-L108` § 3). Task 4 depends on Task 1's comment values/rules; it does not use Task 2's new action.
- **Already-green verification:** Task 3 takes `Tests cannot go red.` because Task 1 supplies the new restore refusals and Task 2 supplies the action used by AC-6. `SavedData.load` already catches domain `Refusal`, its decoder already restores through `restore_task`, and `main.start` already returns 1 on `UnreadableData` (`persistence/saved_data.py:L95-L108,L205-L231`; `main.py:L39-L49`). Task 3 asserts those real seams in full without inventing an adapter implementation or a red phase.
- **Trace continuity:** Extend `domain/comments.py`'s checked-test paths as each test file becomes present. Task 1 names its unit checks and existing architecture/restore checks; Tasks 2–5 add their own paths. This tightens the design's trace plan because `tests/architecture/test_trace.py:L94-L111` fails on an entry docstring naming a path that does not exist. No task points at a test file a later task has to create.
- **Route audit coverage tightened:** Task 5 updates `SUBMITTED_BODY` and the route audit's saved-name setup alongside the design's `SAMPLE_ADDRESS` addition. The existing audit requires each submission to be accepted and saved once (`tests/integration/test_routes.py:L265-L329`); a comment sample with no name would only exercise a refusal and fail that contract. Keep the operator-name sample a real change and preserve all old route assertions.
- **Hint partitioned:** Task 1 carries design A's scalar/task-composition hint. Task 4 carries D's stable-position, escaping and retained-textarea hint. Task 5 carries D's transport-normalization and stable-position hint. B and C retain no hint, as design § 4 states (`change_design.md:L118-L121`). Each hint names an approach and supplies no implementation.
- **Boundary coverage added:** Task 1 verifies that both existing `Comment` aliases resolve to the same frozen value and preserve the three-field shape, because moving its definition must keep the existing import contract (`change_design.md:L50-L50`; `domain/tasks.py:L66-L72`; `domain/__init__.py:L38-L54` § re-exports). Task 5 also sends an invalid UTF-8 comment body through the existing strict form reader and verifies 400 with no save, because the new field uses that same boundary (`web/routes.py:L128-L140`). Task 5 also checks forged author/instant/shown-name fields, because the action must derive its author from current state and its instant from the injected clock, while only text crosses the form seam (`change_design.md:L54-L54,L64-L64,L84-L84`).
- **Record correction surfaced:** Carry RN-15's code-unchanged sentence outside this change's reach. The new comment code changes the tree that sentence describes, while the recorded People browser result remains evidence for its named commit (`docs/nfdr.md:L730-L738` RN-15; `change_design.md:L27-L32` blast radius).
- **Timing contract reconciled:** Carry the design's exclusion of CP-273, its Example and Gap 18 because the requested boundary preserves both timed-run files. Verify their bytes and their existing checks, and make no claim that a comment add has been timed. The exact lines set aside and remaining QC-48/TS-5 obligation stay in `deferred_decisions.md` § CP-273's timed comment add (`change_design.md:L19-L19,L152-L152,L172-L172`; `change_spec.md:L96-L96,L155-L155,L218-L218`).

### Task 1: Domain comment construction, append and restore (`domain/comments.py`, `domain/tasks.py`, `domain/refusals.py`, `domain/__init__.py`)

**Dependencies:** None

**What to build:** Establish the scalar comment rules in the Comments entry and compose them with task lookup, immutable append and restore in `tasks.py`, following design A (`change_design.md:L44-L58` § 3).

- Move the frozen `Comment` value to `comments.py`; keep the same `text`, `author`, `created_at` fields and the identical class behind `domain.Comment` and `domain.tasks.Comment`.
- Expose `check_comment_text`, `create_comment`, `check_saved_comment`, `check_saved_comments` and `add_task_comment` with design A's argument/result contracts.
- Define `BlankComment` and `OperatorNameNotSet` under the existing `Refusal` base; extend `TextField` with `COMMENT`. Use the existing domain length constants and checker.
- Look up the task before checking comment values. Check too-long text, then blank text, then absent operator name. Preserve each accepted append even for identical text or equal/backwards times.
- Preserve `restore_task`'s signature. Validate historical authors with `check_operator_name`, with no comparison to the current name or assignee list. Preserve saved comment order.
- Apply only CP-274's released domain/architecture/saved-fixture changes: land `comments` in `test_shapes.py` and `LANDED_FEATURE_WORDS`; preserve workflow/filtering/sorting/summary exclusions; reverse only the empty-comment clause of `test_restore_task_checks_saved_label_rules`; replace the invalid comment values in `_state_holding_every_field` and `test_historical_assignee_and_structural_label_comment_values_load` while keeping their other assertions (`change_spec.md:L98-L103` CP-274).
- Correct the touched saved-data test docstrings that claim comments have no content rule or nothing adds a label/comment (`tests/integration/test_saved_data.py:L616-L618,L838-L840`), stating the creation/restore behaviours those tests check. Add the entry trace without naming absent future test files.

#### Behaviours to verify

Add `tests/unit/test_comments.py`; extend the existing tests named above. Coverage carries design T01–T04, T14's fixture corrections and T19 (`change_design.md:L131-L134,L144-L144,L149-L149`).

- `test_comment_text_requires_a_non_whitespace_character` — empty, space, tab, LF, U+00A0, U+3000 and mixtures raise `BlankComment`; U+200B is accepted exactly.
- `test_comment_keeps_text_author_and_supplied_instant` — valid text, surrounding spaces, line breaks and markup characters are unchanged; the supplied author and instant are kept without I/O.
- `test_comment_accepts_the_code_point_maximum_without_truncation` — exactly `LONG_TEXT_MAX` accepts with line breaks and a non-BMP character; one more raises `TextTooLong` identifying `TextField.COMMENT` and the same maximum.
- `test_comment_refusal_precedence_is_length_blank_then_unset_name` — 4,001 spaces with no name raise too-long, empty with no name raises blank, and otherwise-valid text with no name raises `OperatorNameNotSet`.
- `test_comment_append_preserves_written_order_and_duplicate_text` — append after every existing comment with equal or backwards instants; repeated text creates another comment.
- `test_comments_can_be_added_in_every_task_status` — todo, in-progress, done and cancelled each accept.
- `test_unknown_task_precedes_every_comment_refusal` — missing task raises `TaskNotFound` for valid/blank/over-long text with saved/unset names; old state and counters are unchanged.
- `test_comment_add_changes_only_the_named_tasks_comments` — successful and refused operations preserve their inputs; compare complete other task/project/name/assignee/counter values and the named task's other fields.
- `test_restore_checks_comment_text_and_historical_author` — blank and over-long text/author refuse; exact 4,000/200-code-point maxima, historical names and comments without a current name restore in order.
- `test_comment_public_aliases_keep_one_frozen_three_field_value` — both old aliases identify the same immutable Comment; the field set stays text/author/created_at.
- `test_comments_entry_has_existing_trace_paths_and_landed_word` — its opening docstring names SRS FR-28–FR-30, FR-39, FR-40 and DR-3/DR-6, participating application/web modules and currently present checks; existing trace/import/reach/frozen-shape tests pass.

#### Held by review

- CP-266 / QC-20 — scalar rules and the value are in `domain/comments.py`; state composition is in `domain/tasks.py`; domain publishes no wording and imports no outer part. Existing architecture walks cover import/reach; read the diff for ownership and wording (`change_spec.md:L67-L67`; `docs/nfdr.md:L160-L168`).
- CP-274 — each changed existing assertion is one the spec releases; all label, historical-assignee, state-field and excluded-feature assertions remain. Check the diff against the exact CP-274 list (`change_spec.md:L98-L105`).

#### Implement

Infer from failing tests.

# Hint:
Keep scalar Comment construction/restoration in the feature entry and task/state composition in `tasks.py`, so restoration and adding share validation without a circular dependency. Append to the immutable tuple; preserve its order across save and load.

#### Verification gate

From `.worktrees/2026-10-12_comments-on-the-page`, run `pytest products/tracker17/tests/` and separately `pytest products/tracker17/tests/e2e/`.
From Product root, run `python3 -m compileall -q domain application persistence web main.py errors.py`, `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web`.
Pass: each command exits 0; domain/trace/fixture tests pass and both existing suites have no new failures; CP-274 changes only its released clauses.

### Task 2: Apply and save a comment under the current name (`application/tracker.py`, `application/__init__.py`, `domain/comments.py` trace only)

**Dependencies:** Task 1 — domain add rule, Comment and refusal exports.

**What to build:** Add `Tracker.add_task_comment(task_id, text)` using the injected clock and whole-state saver, returning the updated Task after saving and publishing; hand the new refusal types through application's re-exports (`change_design.md:L60-L68` § 3 B). Extend only the comment entry's checked-test paths for the test module this task adds.

#### Behaviours to verify

Add `tests/integration/test_comment_tracker.py`, carrying design T05 and the recording-saver half of T11 (`change_design.md:L135-L135,L141-L141`). Keep the Tracker and domain real; hand in clocks and recording/failing savers.

- `test_comment_action_saves_once_before_publishing` — one injected instant supplies the comment; saver observes one whole new state while Tracker still exposes the old task, and the returned/current task changes only after save succeeds.
- `test_comment_action_uses_the_name_at_action_time` — a read under Sam followed by a saved rename to Lee adds as Lee; a read with no name followed by setting Sam adds as Sam.
- `test_rename_keeps_historical_comment_authors` — previous authors remain unchanged and the next comment carries the newly saved name.
- `test_comment_action_refusals_save_nothing_and_keep_current_state` — each typed domain refusal, including unknown task, propagates with no save or state publication.
- `test_failed_comment_save_keeps_the_previous_task_current` — injected saver failure propagates and leaves all current values unchanged.
- `test_comment_action_reaches_only_the_injected_saver_and_clock` — successful add records one save and one instant read; no load is available or called through that seam (CP-271/QC-54).
- `test_comment_refusals_are_available_through_application` — BlankComment, OperatorNameNotSet and the updated TextField are the domain types handed to web, with no application-owned refusal or comparison.

#### Held by review

- QC-21 — application performs orchestration only; it introduces no comment rule, state comparison, HTML or concrete persistence dependency (`docs/nfdr.md:L169-L189`; `change_design.md:L62-L66`).

#### Implement

Infer from failing tests.

#### Verification gate

From `.worktrees/2026-10-12_comments-on-the-page`, run `pytest products/tracker17/tests/` and separately `pytest products/tracker17/tests/e2e/`.
From Product root, run `python3 -m compileall -q domain application persistence web main.py errors.py`, `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web`.
Pass: each command exits 0; injected-clock/save-order/current-name tests pass; old People/operator-name tests and both suites have no new failures.

### Task 3: Verify unreadability, compatibility and restart (`tests/integration/test_saved_data.py`, `tests/integration/test_start.py`, `domain/comments.py` trace only)

**Dependencies:** Task 1 — restore refusals and corrected fixtures; Task 2 — add action for the AC-6 sequence.

**What to build:** Assert the existing real adapter/start seams against the new domain rules and prove the complete action-and-restart sequence, preserving saved key sets and four supported forms (`change_design.md:L70-L76` § 3 C). Add these checks to the comment entry's trace; change no adapter/start production logic.

#### Behaviours to verify

Extend the two named integration modules, carrying design T13–T15 (`change_design.md:L143-L145`).

- `test_saved_comment_blank_text_is_unreadable` — empty text raises `UnreadableData(location)` on real load; real start exits non-zero, prints the existing unreadable/location line, serves no listener and changes no bytes.
- `test_saved_comment_whitespace_text_is_unreadable` — whitespace-only text, including LF/U+00A0/U+3000 mixtures, has that same whole-file/start result.
- `test_saved_comment_overlong_text_is_unreadable` — 4,001 code points has that result.
- `test_saved_comment_blank_author_is_unreadable` — empty author has that result.
- `test_saved_comment_whitespace_author_is_unreadable` — whitespace-only author has that result.
- `test_saved_comment_overlong_author_is_unreadable` — 201 code points has that result.
- `test_bad_comment_prevents_partial_loading` — valid projects/tasks/comments before the broken comment produce no returned partial state; bytes and directory listing remain unchanged. Retain all existing bad-shape/type/instant assertions.
- `test_saved_comment_boundaries_and_historical_authors_load` — exact text/author maxima including non-BMP characters, author unequal to current operator, and comments with no current name load and start successfully without writes.
- `test_every_supported_saved_form_keeps_all_existing_values` — projects-only, projects+assignees, task-bearing pre-name and current data load/start with each available project/task/label/assignee/name value unchanged; older absent fields take the existing defaults; loading writes nothing.
- `test_every_field_and_comment_survives_action_and_restart` — create project, assignee, a task with all editable fields, label, operator name and comments through Tracker actions; rebuild a Tracker from real saved data and verify all values and append order.
- `test_comment_restart_has_only_the_existing_saved_keys` — state, projects, tasks, counters and each three-field comment have exactly the existing key sets; no request/outcome/comment-identity key is saved.

#### Implement

Tests cannot go red.

Reason: Task 1 supplies all content checks through `restore_task`, and Task 2 supplies the action used by the restart sequence. The existing adapter catches those refusals around the complete load and already preserves the shape; existing start handles UnreadableData before listening (`persistence/saved_data.py:L95-L108,L133-L151,L205-L231`; `main.py:L39-L49`). This task adds verification of those seams, not another implementation.

#### Verification gate

From `.worktrees/2026-10-12_comments-on-the-page`, run `pytest products/tracker17/tests/` and separately `pytest products/tracker17/tests/e2e/`.
From Product root, run `python3 -m compileall -q domain application persistence web main.py errors.py`, `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web`.
Pass: each command exits 0; all new whole-file/start/restart assertions pass on real files, old malformed-data coverage remains, and both suites have no new failures.

### Task 4: Task-page comment values, GET rendering and focus (`web/pages.py`, `web/routes.py` GET only, `web/style.css`, `domain/comments.py` trace only)

**Dependencies:** Task 1 — valid immutable Comment values and restoration for page fixtures.

**What to build:** Render comments and the form through optional `comment_area` and `operator_name` page values; decode comment outcomes and provide the current name on GET, leaving submission handling to its own task (`change_design.md:L90-L99` § 3 D). Define `CommentRefusal` as an enum with `too-long`, `blank`, `no-name`; define immutable `CommentArea` with text, optional typed refusal, failed boolean and optional added position. Keep existing `task_page` arguments/defaults. Use approved `change_text.md` strings verbatim for all new published words (CP-248; `change_design.md:L6-L6`).

#### Behaviours to verify

Add `tests/integration/test_comment_pages.py`; amend only CP-274's task-page clauses in `tests/integration/test_task_pages.py`. Carry design T06/T07, the rendering/outcome part of T09/T12 and T20 (`change_design.md:L136-L142,L150-L150`). Use real Site/Tracker/SavedData, valid restored comments, and handed-in clocks; no new POST is needed for these checks.

- `test_task_comments_are_between_labels_and_the_add_form` — heading then flat comments then form, below the existing fields/labels; every item contains its author, local written time and text.
- `test_comment_page_preserves_append_order_when_times_disagree` — duplicate/equal/backwards instants retain tuple order; GET reads neither saver nor injected clock.
- `test_comment_time_is_machine_local_in_the_required_format` — under controlled process UTC+2, `2026-10-12T12:32:00Z` renders `2026-10-12 14:32`, with no seconds/relative words/zone. Restore timezone environment after the test; patch no product clock.
- `test_comment_page_preserves_spaces_line_breaks_and_markup_as_text` — exact author/text include initial/interior/trailing LF, surrounding spaces, `<`, `&` and quotes; values use the same escaping path and display line breaks.
- `test_comment_form_has_one_label_and_one_shared_maximum` — four-line textarea, visible label, text-only submission value, Add below newest; field maximum and approved maximum sentence both use application's LONG_TEXT_MAX; no required/disabled control intercepts the specified refusals.
- `test_empty_comments_show_the_approved_empty_line_and_form` — empty state remains visible with form.
- `test_comment_name_notice_matches_the_current_saved_name` — unset name yields the approved notice with exactly its People link above the form; saved name yields no notice, including a later GET after rename.
- `test_comment_refusal_focuses_and_describes_the_textarea` — blank/no-name outcomes retain the exact normalized text, including an initial LF; too-long ignores any supplied retained text; one field focus target and one associated reason.
- `test_comment_failure_focuses_and_describes_add` — failure retains text and focuses Add with one associated failure line; the line itself has no focus.
- `test_comment_added_outcome_focuses_the_addressed_position` — valid position focuses exactly that comment with tabindex -1 and its single completion description; another appended comment leaves the original position's target intact.
- `test_comment_query_accepts_only_recognized_outcomes` — unknown codes, malformed/nonexistent positions and orphan retained text yield ordinary comment presentation; recognized refusal precedes failure, which precedes valid added position; recognized comment outcomes precede label/edit/task outcomes. Unknown comment metadata preserves existing outcome handling.
- `test_written_comments_offer_no_edit_delete_or_reply_control` — a page with several comments has no control acting on an existing comment; label removal controls retain their existing scope.
- `test_comment_outcomes_keep_one_focus_target_and_the_existing_page_contract` — all mixed outcomes have exactly one target, no message focus, no fragment/script/table, and preserve old task edit/label/facts behaviour.

#### Held by review

- CP-248 — check every published comment string and accessible description against `change_text.md`, including empty/no-name/max/refusal/failure/completion variants; do not change wording elsewhere (`change_spec.md:L31-L31` CP-248).
- Comment metadata, separators and focus styling follow `docs/DESIGN.md` § Comments / The comment textarea as named by design D; inspect the stylesheet delta and preserve existing selectors (`change_design.md:L95-L97`).
- CP-274 — only the exact form-order, comment-absence and conditional People-link clauses change in the old task-page tests; every edit/label/facts/no-script/no-table assertion and every People test remains (`change_spec.md:L104-L105`).

#### Implement

Infer from failing tests.

# Hint:
Use the append position in the outcome address for a stable autofocus target, not matching text or timestamp. Reuse the one escaping path; retained textarea rendering must preserve a leading LF as well as interior line breaks.

#### Verification gate

From `.worktrees/2026-10-12_comments-on-the-page`, run `pytest products/tracker17/tests/` and separately `pytest products/tracker17/tests/e2e/`.
From Product root, run `python3 -m compileall -q domain application persistence web main.py errors.py`, `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web`.
Pass: each command exits 0; real GET and page/outcome assertions pass; old outcomes and People behaviour remain; all review criteria hold and both suites have no new failures.

### Task 5: Comment POST, real saved outcomes and keyboard browser flow (`web/routes.py`, `tests/integration/test_routes.py`, `domain/comments.py` final trace)

**Dependencies:** Task 2 — Tracker add action and refusal exports; Task 4 — CommentArea, typed presentation codes and complete GET rendering.

**What to build:** Add `POST /tasks/[0-9]+/comments` inside the existing policy/lock/strict-form/guarded-redirect path, map typed domain refusals and saved outcomes to Task 4's address contract, and prove the keyboard action in Chromium (`change_design.md:L80-L88,L99-L99` § 3 D). Keep web free of text/name/status rules. Complete the feature docstring with every test module that now exists.

#### Behaviours to verify

Add `tests/integration/test_comment_routes.py` and `tests/e2e/test_comments.py`; extend `tests/integration/test_routes.py`. Carry design T08–T12, T16–T18 and T21/T22's gates (`change_design.md:L138-L148,L151-L152`). Exercise real Site/Tracker/SavedData with injected instants; browser tests enter through main with the existing harness.

- `test_comment_post_saves_then_redirects_to_the_added_comment` — successful text-only POST returns 303 to `/tasks/<id>?comment_added=<one-based-position>`; follow GET and reload real saved data to find the appended text/author/instant and every unrelated field/counter unchanged.
- `test_comment_post_reads_the_name_at_submission_time` — stale Sam page after rename writes Lee; stale no-name page after setting a name succeeds; later rename leaves old authors intact. Forged author/time/shown-name fields do not supply the saved author or instant.
- `test_comment_post_accepts_all_task_statuses_and_repeated_text` — each status accepts; identical text adds another comment and gets its own position.
- `test_comment_post_refuses_each_rule_without_saving` — separate no-name, empty, whitespace and over-long cases prove typed reason, 303/landing, unchanged state/file bytes, retained text for blank/no-name and no retained value for too-long.
- `test_comment_post_uses_length_blank_name_precedence` — 4,001 spaces/no-name gives only too-long; empty/no-name gives only blank; missing text is blank. A missing task wins before every text/name combination.
- `test_comment_post_normalizes_line_breaks_before_domain_counting` — CR LF and lone CR become LF; a native-maximum value whose transmitted length exceeds the normalized length saves whole; code-point maximum including a non-BMP character also saves whole.
- `test_comment_unknown_identity_has_the_existing_not_found_outcome` — numeric missing task redirects to ordinary task GET/404; identity too large to parse follows the direct task-not-found page; no save.
- `test_comment_failed_save_keeps_data_and_retains_the_field` — a handed-in failing saver leaves old comments/current state/file bytes unchanged; landing focuses Add and associates the approved failure line; console emits approved action then underlying error; page contains no Python error/traceback.
- `test_comment_post_applies_request_policy_before_the_action` — wrong Host, cross-site, same-site, none, missing and unknown submission marks refuse without clock/action/save; retain existing policy/no-cookie assertions for success/refusal/failure responses.
- `test_comment_invalid_utf8_request_changes_nothing` — invalid raw and percent-encoded UTF-8 gives the existing empty-body 400; no replacement text, action or save.
- `test_comment_landing_get_and_history_never_repeat_the_add` — repeated landing GET leaves state/saver/file bytes unchanged; earlier valid outcome position still targets the same comment after another append.
- `test_route_audit_accepts_and_saves_the_comment_sample` — add sample pattern/address and submitted text; seed a valid name for this sample; preserve the audit's accepted-once-save, no-refusal/failure, GET-no-change, policy and no-cookie assertions across every route.
- `test_outbound_audit_hook_drives_a_successful_comment_add` — extend the existing all-action sequence with a saved-name comment add, and retain the socket.connect failure condition (CP-271/QC-35).
- `test_recording_saver_comment_route_never_loads` — one successful comment submission reaches only save, not any read of saved data (CP-271/QC-54).
- `test_keyboard_comment_add_brings_the_new_comment_into_view_and_focus` — through main/Chromium, earlier comments exceed the viewport; Tab/type/Tab/Enter submits with browser keys alone; new last comment is in viewport and focused, with the single approved completion as its accessible description. The message is not focused; check visible focus styling. Reload/back/forward never append again.
- `test_browser_maximum_comment_with_line_breaks_is_saved_whole` — native-max BMP text plus line breaks fills the field; submitted/saved normalized value is complete, neither shortened nor refused. Keep the separate non-BMP/code-point boundary in unit/request tests, as design T17 states.
- `test_browser_comment_text_and_author_render_literally` — markup characters, spaces and line breaks display literally; compare saved text and real browser text/author.
- `test_keyboard_comment_refusals_keep_text_focus_and_description` — no-name and blank submissions use keyboard only; textarea remains focused, exact text/line breaks survive and the approved reason describes it.
- `test_comments_entry_names_every_participating_module_and_check` — final feature trace contains the production participants and every comment unit/integration/start/architecture/browser check, and all paths exist.

#### Held by review

- QC-5/QC-23/QC-36 — web maps refusal types received through application, uses existing `_line_feeds`/`_escape`/`_address`/`_guarded`, compares no text length and introduces no clock, persistent outcome state or console catch site (`docs/nfdr.md:L56-L67,L197-L201,L285-L291`; `change_design.md:L84-L97`).
- CP-248 — every new published string, including the failed-comment console action, is `change_text.md` verbatim; no wording change outside the named comment surfaces (`change_spec.md:L31-L31`; `change_design.md:L6-L6`).
- CP-274 — existing route audit assertions and People/task-page tests keep their released-only boundary (`change_spec.md:L98-L105`).

#### Implement

Infer from failing tests.

# Hint:
Reuse the existing newline-normalization and guarded address-building paths. Use the returned task's append position for the success target, which stays stable for duplicate text, equal/backwards times and later appends.

#### Verification gate

From `.worktrees/2026-10-12_comments-on-the-page`, run `pytest products/tracker17/tests/` and separately `pytest products/tracker17/tests/e2e/`.
From Product root, run `python3 -m compileall -q domain application persistence web main.py errors.py`, `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web`.
From Product root, run `python3 tests/timed_run.py`; pass its unchanged existing measurements without claiming comment-add timing.
Run `git -C .worktrees/2026-10-12_comments-on-the-page diff --exit-code 3b5746f91d70763ea2115f896c1d694b7ab77e89 -- products/tracker17/tests/timed_run.py products/tracker17/tests/integration/test_timed_run.py`; pass: exit 0 and no diff.
For CP-275's commit-under-test check outside this worktree, use these commands with the pinned test environment. The clone must be checked out at the code commit being verified (`change_spec.md:L106-L108`; `core/roles/CROSS_ROLE.md:L14-L24` § Every seat).

```bash
VERIFIED_COMMIT="$(git -C .worktrees/2026-10-12_comments-on-the-page rev-parse HEAD)"
CHECK_COPY="$(mktemp -d /private/tmp/tracker17-comments-cp275.XXXXXX)"
git clone --quiet . "$CHECK_COPY"
git -C "$CHECK_COPY" checkout --quiet "$VERIFIED_COMMIT"
pytest "$CHECK_COPY/products/tracker17/tests/"
pytest "$CHECK_COPY/products/tracker17/tests/e2e/"
```

Pass: every gate exits 0, both suites collect and pass including every new browser case, the existing timed checks pass, both timing files are byte-identical, all review criteria hold, and no old test is deleted, skipped or loosened outside CP-274's named clauses.
