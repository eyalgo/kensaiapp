# Tech Lead instruction — operator-name: Your name on People

**Date:** 2026-10-12
**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every code, test and `docs/` path below is relative to it.
**Scope:** Set, replace, restore and show the one operator name on People, with the refusal, failure, browser and full-volume checks of `change_spec.md` § Rules CP-211–CP-239:L23-L102.
**Language resolution:** Python — `system/projects/tracker17/project.md:L12-L12`, `Languages:`, resolves step 1 of `core/doctrine/engineering/languages/README.md` § The resolution chain; the Python router and all six concerns were read.

This document owns the task cut, engineering review decisions and verification gates for
`tracker17 · tobiishi · 2026-10-12_operator-name`. `change_spec.md` and `change_design.md` mean the
input files in that change unit. The output belongs beside them under
`core/doctrine/setup/kensaiapp_structure.md` § 2, `journey/tobiishi/<key>/`:L2104-L2108.

## Project layout

```text
tracker17/
  domain/
    __init__.py                         ← modified: public re-exports
    state.py                            ← modified: optional scalar and restore rule
    operator_name.py                     ← new: scalar rule and set outcome
  application/
    __init__.py                         ← modified: outcome re-export
    tracker.py                          ← modified: reader and set action
  persistence/
    saved_data.py                       ← modified: encode, decode, restore
  web/
    pages.py                            ← modified: Your name section and outcome value
    routes.py                           ← modified: guarded POST and outcome address
  tests/
    architecture/
      test_shapes.py                    ← modified: exact state-field assertion
    unit/
      test_operator_name.py             ← new: name checks and set outcome
      test_state.py                     ← modified: restore and constructor compatibility
    integration/
      test_operator_name_tracker.py     ← new: application action
      test_saved_data.py                ← modified: format and durable round trips
      test_start.py                     ← modified: invalid and legacy name starts
      test_people_pages.py              ← modified: section and assignee regression checks
      test_people_routes.py             ← modified: Site, real listener and restart checks
      test_routes.py                    ← modified: route, origin, audit and saver coverage
      test_timed_run.py                 ← modified: name measurement and verdict checks
    e2e/
      test_people.py                    ← modified: keyboard and hostile name flows
    timed_run.py                        ← modified: name POST and landing measurement
```

Create only files marked new; use the existing package directories and initializers
(`domain/__init__.py:L1-L8`, “The rule core”; `application/__init__.py:L1-L8`, “The operator's actions”).
Placement follows the parts table
in `docs/SDD.md` § 3:L198-L216 and `change_design.md` § 2:L21-L29.
The module set and allowed/forbidden edges remain those of `docs/nfdr.md` § 1.2:L122-L153:
domain imports no other part; application and persistence may import domain/errors; web may import
application/errors and receives domain names through application; main wires all parts; errors
imports no product part. Package initializers contain public re-exports only.

## TL Review Notes

The following decisions are the Tech Lead's call, 2026-10-12.

- **Task cut and assertion ownership:** retain A–E as five cohesive tasks in their designed order
  (`change_design.md` § 3:L35-L96). Attach T10's exact state-field change to Task 1, its seven
  `FULL_KEYS` sites to Task 2, and its section-scoped People assertions to Task 4. Each travels with
  the subject that falsifies it, rather than a separate late cleanup task, because CP-238's assertions
  concern those subjects (`change_spec.md` § Rules:L93-L99). Task 4 includes pages and routes as
  the designed one People request responsibility; its real-file tests consume Task 2's format.
- **Gate measured:** from the instance change worktree, `pytest products/tracker17/tests/` collected
  813 items. In the sandbox it exited 1 with `5 failed, 788 passed, 20 errors in 25.11s`, including
  `PermissionError: [Errno 1] Operation not permitted` at `socket.bind`. The identical command with
  command approval exited 0 with `813 passed in 31.05s`. Keep the card's working invocation in every
  task gate. This measured permission restriction is not a red-at-baseline product task. No task
  receives `Tests are red at baseline.`
- **Lane selection:** all five tasks use the test-first marker. Their new subjects are absent from
  the baseline interfaces (`domain/state.py:L26-L30`, state fields;
  `application/tracker.py:L48-L139`, actions; `persistence/saved_data.py:L26-L29,L102-L111`, format;
  `web/routes.py:L86-L99`, routes; `tests/timed_run.py:L462-L490`, `main`). Existing shared checks
  do not make the requested operator-name behaviours already green.
- **Malformed form edge added:** Task 4 adds malformed UTF-8 cases at `/operator-name` and proves
  no action/save occurs. This preserves the existing `_form` contract instead of letting a new route
  silently bypass it (`web/routes.py:L120-L132`, `_form`; `change_design.md` § 3 D:L74-L74).
- **Outcome immutability asserted:** Task 1 adds a direct outcome-immutability behaviour beyond
  design T1's enumerated cases, because the interface requires a frozen outcome
  (`change_design.md` § 3 A:L44-L44). It keeps that contract asserted as well as covered by the
  existing domain dataclass walk.
- **Current-state comparison made explicit:** Task 4 adds a two-page/stale-name submission case.
  The decision follows CP-218's “already saved at that moment” (`change_spec.md` § Rules:L33-L33):
  submitting the current exact value saves nothing even from an older page, while submitting the
  older different value replaces the current value. No shown-name field or task-edit comparison
  enters this action. This proves the design's comparison rather than merely first-set/replacement.
- **Direct page reconstruction edge added:** Task 4 tests combined metadata directly at the page
  builder as well as through Site. The reason is that `people_page` is itself a consumed interface
  (`change_design.md` § 3 D:L75-L83); redirect-only checks cannot prove its focus arbitration or
  suppression of typed text under a too-long outcome.
- **Missing retained text locked:** a recognized blank/failure query without `operator_typed`
  falls back to the current saved name, or empty when unset. This Tech Lead reading makes absence
  different from an explicitly empty typed value, following the optional area's `typed=None` default
  and presence contract (`change_design.md` § 3 D:L77-L81); genuine submitted empty text still keeps
  its empty value.
- **Timed harness fixture precision:** Task 5's existing deterministic full-run fixtures may supply
  additional timer values for the added name measurement, preserving every existing verdict and
  assertion. `Ticks.__call__` consumes a finite iterator (`tests/integration/test_timed_run.py:L46-L55`,
  `Ticks`), and `main` shares the timer among its measurements (`tests/timed_run.py:L462-L490`,
  `main`). On this reading, design § 5 T12's “Retain existing measurements and their checks”
  (`change_design.md:L125-L125`) permits added fixture inputs; CP-238's prohibition on changing tests
  to fit (`change_spec.md:L93-L99`) still prohibits weakening their checked behaviour. No timer
  exhaustion fallback, removed assertion or altered expected old verdict is permitted.
- **Verification copy contract:** retain the design's disposable-clone reading of CP-239
  (`change_design.md` § Architect Review Notes:L148-L148). Checks outside the change worktree use
  a clone at the exact tested SHA, per `core/roles/CROSS_ROLE.md` § Every seat:L12-L24, because the
  archive/init prescription in `change_spec.md` § Rules:L100-L102 loses history. Inside this change
  worktree the card command runs directly. Do not run checks in the primary product checkout.
- **Additional foundation correction:** carry the archive reference in `docs/nfdr.md` QC-47 and
  RN-28 as owed below. QC-47:L392-L400 and RN-28:L904-L912 still attribute an archive to the
  cross-role contract, whereas `core/roles/CROSS_ROLE.md` § Every seat:L12-L24 requires a clone.
  Inputs remain read-only; this correction has no code task to ride.
- **Station verification reference:** carry the same archive-reference correction for
  `tracker17 · shukuba · 2026-10-12_operator-name` § Reached when, item 5:L15-L15, which still names
  an archive. The plan's clone contract follows `core/roles/CROSS_ROLE.md` § Every seat:L12-L24;
  the station is outside this artifact-producing task's write scope.

## Corrections owed while there

- Owed outside this change's reach: `docs/SDD.md` § 3, application row:L202-L202 — its unqualified
  submitted-versus-page-shown comparison would wrongly describe operator-name setting → qualify
  that comparison as the task-edit rule; scalar name setting compares against the saved name at
  action time, with application reading the domain outcome and comparing no states. The correction
  is carried from `change_design.md` § Records this change makes false:L134-L136.
- Owed outside this change's reach: `docs/nfdr.md` § 1.3, QC-21:L167-L180 — its unqualified
  submitted-versus-shown comparison would wrongly cover this scalar → retain the task-edit rule,
  qualify other actions by their own domain comparison, and retain application's no-comparison rule,
  as identified in `change_design.md` § Records this change makes false:L134-L136.
- Owed outside this change's reach: `docs/nfdr.md` § 4, QC-47:L392-L400 and NFDR Review Notes,
  RN-28:L904-L912 — they wrongly say the cross-role contract sends checks to an archive → name the
  disposable clone at the tested SHA required by `core/roles/CROSS_ROLE.md` § Every seat:L12-L24;
  keep the Git prerequisite and fail-rather-than-skip check.
- Owed outside this change's reach: `tracker17 · shukuba · 2026-10-12_operator-name` § Reached when,
  item 5:L15-L15 — its archive verification reference disagrees with the clone requirement → name
  the disposable clone at the exact tested SHA under `core/roles/CROSS_ROLE.md` § Every seat:L12-L24.

### Task 1: Domain name rule, immutable state and restore (`domain/operator_name.py`, `domain/state.py`, `domain/__init__.py`, `tests/architecture/test_shapes.py`)

**Dependencies:** None

**What to build:** the optional name scalar, shared-rule validation, frozen `OperatorNameOutcome`
and pure set/restore operations in domain, to `change_design.md` § 3 A:L35-L46.
Append `TrackerState.operator_name: str | None` with default `None`; retain all existing positional
meanings and add the optional keyword to `restore_state`. Expose `check_operator_name`,
`set_operator_name` and `OperatorNameOutcome` through domain's public surface. The outcome carries
`name: str` and `changed: bool`. Validate before exact comparison; an unchanged submission returns
the original state. A changed result differs only in the name. Reuse `BlankName`,
`TextTooLong`, `TextField.NAME` and `SHORT_TEXT_MAX`; define no new maximum or refusal.

#### Behaviours to verify

In `tests/unit/test_operator_name.py`, realize design T1 (`change_design.md` § 5:L114-L114):

- `test_operator_name_refuses_each_blank_value` — separately check empty, spaces, tab, U+00A0 and
  U+3000 through both the checker and set operation; expect `BlankName` and unchanged input state.
- `test_operator_name_keeps_surrounding_spaces_and_case` — a valid string is returned and saved
  verbatim; U+200B alone is accepted by the shared whitespace definition.
- `test_operator_name_accepts_200_code_points_including_non_bmp` — the boundary is accepted,
  with spaces counted and a character outside the Basic Multilingual Plane counting once.
- `test_operator_name_refuses_201_code_points_before_blankness` — both a nonblank over-limit value
  and 201 spaces raise `TextTooLong` with the existing name-field/maximum seam, not `BlankName`.
- `test_first_name_and_replacement_change_only_the_name` — first set and replacement report changed;
  projects, tasks with labels/comments, assignees and both counters remain identical, and the input
  state is unchanged.
- `test_same_name_returns_unchanged_outcome_and_original_state` — exact equality reports no change;
  `Sam` to `Sam ` and case-only differences report a change.
- `test_blank_name_cannot_clear_a_saved_name` — each blank form is refused from both unset and set
  states without clearing the saved name.
- `test_operator_name_outcome_is_immutable` — the outcome cannot be mutated after construction.

In `tests/unit/test_state.py`, realize design T2 (`change_design.md` § 5:L115-L115):

- `test_empty_and_legacy_state_construction_have_no_name` — empty state, omitted restore keyword,
  explicit `None` and existing positional constructor/restore calls keep their established meanings.
- `test_restore_operator_name_keeps_exact_valid_values` — ordinary, space-surrounded and boundary
  names restore without modifying unrelated values.
- `test_restore_operator_name_refuses_whole_invalid_state` — each blank form and each over-limit
  form raises the same domain refusal as setting, and no partial state is returned.

Extend only the exact state-field assertion in
`tests/architecture/test_shapes.py::test_only_the_task_features_are_added_to_domain` to admit
`operator_name`; retain the prohibited `comments.py` and other feature checks, per
`change_spec.md` § Rules CP-238:L96-L96. The existing frozen/import/reach/trace walks must include
the added domain module without exemptions. Its opening docstring and added test module name
their SRS requirements and participating modules/tests under CP-230 (`change_spec.md:L66-L66`).

#### Implement

Infer from failing tests.

# Hint:
The state restore constructor and operator-name rule have a potential runtime cycle. Keep rule
access usable by restoration without importing the state constructor back during module
initialization; the operation's state typing must not create that cycle.

#### Verification gate

From `.worktrees/2026-10-12_operator-name`, run
`pytest products/tracker17/tests/unit/test_operator_name.py products/tracker17/tests/unit/test_state.py products/tracker17/tests/architecture/`
and `pytest products/tracker17/tests/`.
Pass: both exit 0, the new/restore behaviours pass, the exact state shape admits only the new scalar,
and no existing test has a new failure. The new tests require no file, clock or network.

### Task 2: Durable name encoding, legacy loading and start refusal (`persistence/saved_data.py`, `tests/integration/test_saved_data.py`, `tests/integration/test_start.py`)

**Dependencies:** Task 1 — state field and restore keyword/rule.

**What to build:** the six-key full writer and exact old/new readers in persistence, to
`change_design.md` § 3 B:L50-L58. Always write the prior five keys plus `operator_name`, as string
or JSON null. Accept exactly the three old key sets and the new full set; do not accept a partial
old shape with a name added. Decode text/null as format facts and delegate name rules to restore.
Leave `main.py`, atomic writing and the one-tracker lock unchanged.

#### Behaviours to verify

In `tests/integration/test_saved_data.py`, realize design T4 and its T10 exact-key updates
(`change_design.md` § 5:L117-L117,L123-L123):

- `test_saved_operator_name_has_only_the_six_allowed_keys` — each full save writes exactly the
  previous five keys and `operator_name`; unset writes null, and a valid name writes verbatim.
- `test_operator_name_round_trip_preserves_the_complete_rich_state` — real save/load retains
  projects, task fields, labels, existing comment values/order, assignees and both counters exactly.
- `test_each_legacy_shape_loads_without_a_name_or_a_write` — separately load projects-only,
  projects/assignees, and prior full task forms; every value the form can hold survives, name is
  absent, and bytes are unchanged. An actual subsequent change writes the six-key full form.
- `test_new_saved_name_loads_null_boundary_and_surrounded_spaces` — null, 200 code points including
  a non-BMP character, and a space-surrounded name load without rewriting.
- `test_invalid_operator_name_type_refuses_the_whole_file_untouched` — boolean, number, list and
  object each raise `UnreadableData`; no partial load or byte change.
- `test_invalid_operator_name_value_refuses_the_whole_file_untouched` — empty, whitespace-only,
  over-limit and over-limit whitespace each reach the domain restore rule and become unreadable.
- `test_name_format_keeps_exact_required_and_unknown_key_checks` — unknown keys, missing required
  keys and unsupported mixed shapes stay unreadable; no old shape is widened accidentally.

`FULL_KEYS` admits only `operator_name` at all seven current-write assertion sites
(`tests/integration/test_saved_data.py:L319-L338,L395-L395,L666-L682,L1028-L1028,L1091-L1091`,
`FULL_KEYS`). Retain each unrelated-value assertion and keep old-format fixtures proving old reads.

In `tests/integration/test_start.py`, realize design T5 (`change_design.md` § 5:L118-L118):

- `test_start_refuses_saved_empty_operator_name` — an empty saved string returns nonzero,
  reports unreadable data/location, produces no ready/listener success, and preserves file bytes.
- `test_start_refuses_saved_whitespace_operator_name` — the same guarantees for whitespace only.
- `test_start_refuses_saved_overlong_operator_name` — the same guarantees for 201 code points.
- `test_start_refuses_saved_numeric_operator_name` — the same guarantees for a number.
- `test_start_reads_each_legacy_form_with_every_existing_value` — real starts on all three old
  forms show no name, retain their projects/tasks/labels/comments/assignees and counters, and do not
  rewrite on load.
- `test_start_reads_valid_unset_boundary_and_surrounded_name` — null and valid boundary/exact text
  survive start; use the real start path, not a replaced `SavedData.load` or listener.

#### Implement

Infer from failing tests.

# Hint:
Keep exact accepted key sets: retain the old five-key set separately before widening the writer's
full set. Missing old data and new null are two format representations of the same domain None.

#### Verification gate

From `.worktrees/2026-10-12_operator-name`, run
`pytest products/tracker17/tests/integration/test_saved_data.py products/tracker17/tests/integration/test_start.py`
and `pytest products/tracker17/tests/`.
Pass: both exit 0; new round-trip/start behaviours pass; existing atomic-save, interruption, lock,
unknown-key and legacy-data checks still pass; no new failure elsewhere.

### Task 3: Application reader and save-before-publication action (`application/tracker.py`, `application/__init__.py`)

**Dependencies:** Task 1 — domain set operation and outcome. Task 2 is not a dependency of the
injected Saver contract (`change_design.md` § 3 C:L64-L66).

**What to build:** `Tracker.operator_name() -> str | None` and
`Tracker.set_operator_name(name: str) -> OperatorNameOutcome`, with the outcome re-exported for web,
to `change_design.md` § 3 C:L60-L66. Invoke domain once against the current state; save the complete
new state only on a changed outcome, publish only after save success, and propagate refusals/failures.
Leave Saver/Clock contracts unchanged; no application equality/length/blank rule or request data.

#### Behaviours to verify

In `tests/integration/test_operator_name_tracker.py`, realize design T3
(`change_design.md` § 5:L116-L116):

- `test_operator_name_reader_reports_unset_and_restored_name` — the reader returns the current
  scalar exactly without save or clock use.
- `test_name_change_saves_once_before_the_reader_publishes` — a handed recording saver receives
  the whole candidate state once; during its save, the reader still reports the old name; afterwards
  the new name and outcome are visible.
- `test_replacing_name_preserves_every_unrelated_value` — only the scalar differs, including when
  surrounding spaces or case make the exact name different.
- `test_same_name_never_reaches_even_a_failing_saver` — no save/publication or refusal on equality.
- `test_each_domain_name_refusal_propagates_without_a_save` — blank and over-limit refusals are
  the domain types; saved name and complete current state stay unchanged from both unset and set.
- `test_failed_name_save_does_not_publish` — a handed failing saver propagates its error and the
  reader/unrelated state stay as before; there is no success outcome.
- `test_name_action_never_reads_clock_and_saver_receives_only_saves` — fake records prove the
  clock is unused and there is no load/request detail on the saver boundary.

#### Held by review

- Application contains orchestration only, with no blank/length/state-comparison rule. Behaviour
  assertions cannot prove the owning part of a duplicated rule; read the action diff against
  `docs/SDD.md` § 3:L202-L202 and `docs/nfdr.md` QC-21:L167-L180, with the carried scalar qualification.

#### Implement

Infer from failing tests.

#### Verification gate

From `.worktrees/2026-10-12_operator-name`, run
`pytest products/tracker17/tests/integration/test_operator_name_tracker.py`
and `pytest products/tracker17/tests/`.
Pass: both exit 0, all reader/save/no-change/failure behaviours pass, the review-held placement holds,
and no new failure elsewhere.

### Task 4: People section, guarded name submission and browser flow (`web/pages.py`, `web/routes.py`)

**Dependencies:** Task 3 — application reader, action and public outcome/refusal/bound seam;
Task 2 — real saved name and fresh-start acceptance.

**What to build:** the one People name request/response responsibility, to
`change_design.md` § 3 D:L68-L86. Add submission route `POST /operator-name` with URL-encoded
`name`; missing field means empty, decoded through `_form` and normalized through `_line_feeds`.
Use the existing request lock/origin check, `_address` and guarded failure site. GET changes nothing.

Add `OperatorNameRefusal` enum values `BLANK_NAME="blank-name"` and `TOO_LONG="too-long"`, and frozen
`OperatorNameArea(typed: str | None = None, refusal: OperatorNameRefusal | None = None,
failed: bool = False, saved: str | None = None)` as the page's plain request value, to
`change_design.md` § 3 D:L75-L79. Extend `people_page` only with the designed keyword-only
`operator_name` and `operator_area` defaults; all old parameters keep their meanings.

The query contract is `operator_refused`, `operator_failed=save`, `operator_typed`, and
`operator_saved`. Changed success carries the saved name; unchanged success redirects to plain
`/people`. Blank/failure retains normalized typed text, including empty; too-long carries no text.
Reconstruct only recognized codes; typed text applies only to recognized blank/failure, and a
too-long outcome discards even forged typed text. Operator outcome wins over assignee metadata;
within operator outcomes use refusal, failure, completion precedence, to
`change_design.md` § 3 D:L78-L83.

Compose Your name above Assignees. Use the designed IDs `your-name`, `your-name-heading`,
`operator-name`, `save-operator-name` and `operator-name-outcome`, the visible label, Save, static
keep-their-name note, and absent-name line. Field maximum comes through application's shared
export. Success/refusal focus the field; failure focuses Save, each described by its one outcome
line, with no focused paragraph, fragment or script. Escape variable text through `_escape`, to
`change_design.md` § 3 D:L80-L84. Place the change's published strings from `change_text.md`
verbatim; do not author wording.

#### Behaviours to verify

In `tests/integration/test_people_pages.py`, realize T6/T10
(`change_design.md` § 5:L119-L119,L123-L123):

- `test_people_shows_your_name_above_unchanged_assignees` — title/header/navigation remain the
  same; section, label, field, Save, static note and absent-name line are in their defined places.
- `test_people_name_field_uses_saved_name_and_shared_maximum` — saved exact text fills the field,
  unset shows empty and the no-name line, saved name removes that line; no limit sentence.
- `test_operator_outcome_focus_has_one_linked_accessible_description` — success/blank/too-long
  focus the field, failure focuses Save; one autofocus and one action outcome; line takes no focus.
- `test_operator_name_and_outcome_values_render_as_text` — parse field and completion text with
  `<`, `&` and quotes; no injected tags, duplicate IDs or surrounding-structure changes.
- `test_people_operator_precedence_holds_for_direct_page_values` — refusal beats failure/completion,
  failure beats completion, recognized operator outcome suppresses assignee outcome/focus; plain
  operator area leaves every assignee outcome path intact.
- `test_operator_too_long_page_discards_forged_typed_text` — both saved/unset field fallback;
  no forged typed payload in the page, including combined operator metadata.

Re-prove the authorized existing single-section/field/label/button/no-paragraph assertions inside
Assignees, including `name_input`, `heading`, the single-section traversal and the route test's
retained `" Cy "` field. Drop only `your name` and `comment` from the two absence lists; keep all
other prohibited terms and every assignee behaviour/content/focus/no-script assertion, per
`change_spec.md` § Rules CP-238:L93-L99. Any renamed existing test keeps its assertions.

In `tests/integration/test_people_routes.py`, realize T7/T8
(`change_design.md` § 5:L120-L121):

- `test_operator_name_post_sets_and_replaces_exact_text` — POST then redirect GET shows changed
  name and quoted completion; case/spaces survive; only normalization changes line breaks.
- `test_same_saved_name_redirects_without_save_or_outcome` — exact current value redirects to
  plain People and writes nothing; a trailing-space difference still changes the name.
- `test_stale_people_name_submission_compares_with_current_name` — after another submission
  changes the name, equality with the current value is unchanged, and an older different value
  replaces it. No hidden shown-name field is required.
- `test_empty_name_refusal_retains_empty_field_and_saved_state` — separate empty cases from both
  unset and saved-name starts; blank reason/field focus/description, empty query value and bytes kept.
- `test_whitespace_name_refusal_retains_text_and_saved_state` — separate whitespace cases from
  unset and saved-name starts, with exact retained whitespace and unchanged state/file.
- `test_missing_name_field_is_empty_refusal` — missing POST field follows the empty-name rule.
- `test_overlong_name_refusal_omits_payload_and_keeps_fallback` — from saved/unset starts, 201
  characters and 201 spaces give too-long before blank; neither Location nor page carries submitted
  text; field holds saved value/empty and the reason describes its focus.
- `test_name_submission_normalizes_only_line_breaks` — CRLF and lone CR become LF; preserve all
  other text; accept U+200B and exactly 200 code points including non-BMP.
- `test_failed_name_save_keeps_typed_text_and_reports_action` — handed saver fails from both
  unset/set starts; current state/file stay unchanged, normalized typed text stays, Save has focus
  and description; stderr names action then error, and the page has no Python error text.
- `test_operator_query_presence_unknown_codes_and_precedence` — empty typed differs from missing;
  empty retains an empty field, missing falls back to the saved value/empty; unknown refusal/failure
  codes ignore typed payload; forged too-long ignores text; refusal/failure/
  completion and operator/assignee combinations yield exactly the designed outcome/focus.
- `test_operator_name_form_rejects_malformed_utf8_without_saving` — raw/percent invalid UTF-8,
  incomplete sequence and encoded surrogate answer the existing 400 with no action or state change.
- `test_name_landing_gets_never_repeat_save` — repeated landing GETs, reload and history-equivalent
  GETs leave saver count/state/file unchanged.
- `test_real_listener_people_shows_and_sets_operator_name` — use an actual bound listener/server
  and HTTP requests for GET, set, replacement, and separate empty/whitespace refusals from both
  saved/unset starts. Do not substitute `Site.handle` for this acceptance path.
- `test_operator_name_survives_real_save_and_restart` — real SavedData and a fresh tracker/Site,
  with real listener requests, retain exact name and all rich unrelated data after restart; keep
  `test_people_survives_real_save_and_restart`'s existing assignee coverage.

In `tests/integration/test_routes.py`, realize T9 (`change_design.md` § 5:L122-L122):

- Extend `SAMPLE_ADDRESS`, `SUBMITTED_BODY` and the enumerated route test with an accepted changed
  `/operator-name` submission; extend the before/after snapshot with the name scalar while retaining
  its existing members; assert one save, 303, no cookie, page policy and unchanged GETs.
- `test_operator_name_submission_origin_checks_run_before_action` — wrong/missing Host and each
  non-same-origin mark, including cross-site/same-site/none/missing, give the existing refusal and
  change no state/file; same-origin succeeds.
- Extend the outbound audit-window action sequence with a changed name save and landing GET;
  no `socket.connect` event occurs inside the subject window.
- `test_operator_name_route_hands_recording_saver_only_saves` — assert actual handed saver calls,
  and no additional load or format knowledge crosses application.

In `tests/e2e/test_people.py`, realize T11 (`change_design.md` § 5:L124-L124):

- `test_operator_name_keyboard_set_replace_reload_and_blank_refusal` — a main-started tracker
  in Chromium is operated with keyboard navigation/typing/Enter, without pointer use or scripted
  product interaction; set, replace, reload/back/forward, then blank refusal. Assert actual browser
  field value, focused element and computed accessible description, plus unchanged durable data on
  refusal. Observe that history navigation sends no further submission.
- `test_operator_markup_name_has_exact_browser_text_and_description` — save `<`, `&` and quotes;
  exact input and completion text, normal surrounding structure, browser focus and computed
  accessible description. Use browser inspection only as an assertion, not injected interaction.

#### Held by review

- Every published string is placed verbatim from `change_text.md`, with no authored substitute,
  per `change_spec.md` § Rules CP-213:L25-L25 and the cross-role implementation contract.
  Text assertions prove rendered values; read the diff for the complete string inventory.
- Domain owns name validation; web only decodes, normalizes, maps refusal types and renders, per
  `docs/SDD.md` § 3:L200-L204. Read the diff for placement and the single `_escape`/guarded failure
  seams; do not add length/blank checks or another console/failure catch site in web.

#### Implement

Infer from failing tests.

# Hint:
Namespace the new outcome address values so assignee outcomes cannot consume them; retain
empty-versus-absent typed text, and omit/drop over-long text at both redirect construction and
page reconstruction.

#### Verification gate

From `.worktrees/2026-10-12_operator-name`, run
`pytest products/tracker17/tests/integration/test_people_pages.py products/tracker17/tests/integration/test_people_routes.py products/tracker17/tests/integration/test_routes.py`,
`pytest products/tracker17/tests/`, and `pytest products/tracker17/tests/e2e/`.
Pass: all exit 0; in-process and actual-server checks both pass; the Chromium name flows and the
existing browser regression suite pass; CP-238's surviving assertions and review-held rules hold.
The e2e gate runs in the product's pinned test environment with its installed browser, not the
baseline machine pytest environment (`pyproject.toml:L12-L17`, dev pins;
`tests/e2e/conftest.py:L22-L23,L126-L136`, Playwright browser fixtures).

### Task 5: Name action measured at full volume (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** Task 2 — real persisted scalar and read-back; Task 4 — name POST and landing page.

**What to build:** a changed name-save POST and its landing GET measurement, plus harness checks,
to `change_design.md` § 3 E:L88-L96. Use an ordinary-length name and a real saved fixture of
1,000 tasks with 20 comments each in its own temporary location. Report each duration separately;
each must be strictly below one second. Read-back proves the name and all unrelated fixture values;
the successful People landing shows the intended saved result. Keep existing measurements and
their verdicts. Do not time a refusal, failure, no-change redirect or wrong landing as a success.

#### Behaviours to verify

In `tests/integration/test_timed_run.py`, realize design T12
(`change_design.md` § 5:L125-L125):

- `test_timed_run_reports_name_save_and_landing_at_exact_volume` — the full run emits two name
  rows and states volume/name length; durable result has exactly the name change and 1,000 × 20
  existing task/comment values, with an independent name fixture.
- `test_timed_name_request_is_same_origin_and_uses_real_readback` — record the accepted POST then
  exact landing GET; verify the actual persisted scalar and unchanged complete fixture.
- `test_timed_name_false_save_or_unrelated_delta_is_failure` — a plausible 303 with no write,
  unchanged name, wrong name, or unrelated mutation fails the measurement/verdict.
- `test_timed_name_refusal_failure_or_wrong_redirect_is_failure` — blank/too-long/failure metadata,
  server error, plain no-change People redirect, missing or wrong address all yield a failed verdict.
- `test_timed_name_landing_requires_intended_saved_result` — correct response/page passes first;
  wrong status, missing name field/completion or wrong name fails even after a real save.
- `test_timed_name_requires_each_duration_strictly_below_one_second` — deterministic timer cases
  at exactly one second and above fail separately for POST and landing; below passes.
- `test_full_timed_run_fails_when_only_name_measurement_fails` — the complete entry returns
  nonzero when either name row fails while all old rows pass; retain old-row failure checks.
- `test_timed_name_fixture_does_not_touch_product_data_or_other_fixtures` — independent real-file
  fixture, no writes to product `data/`, and existing task/label fixtures and assertions stay intact.

Finite timer fixtures may gain only the extra ticks the new measurement consumes, with their old
assertions/verdicts retained, as decided in TL Review Notes. No silent iterator-exhaustion fallback.

#### Implement

Infer from failing tests.

# Hint:
Reuse the existing volume fixture and verdict, proving the stored result and landing content
rather than treating any 303 as success.

#### Verification gate

From `.worktrees/2026-10-12_operator-name`, run
`pytest products/tracker17/tests/integration/test_timed_run.py`,
`pytest products/tracker17/tests/`, and `pytest products/tracker17/tests/e2e/`.
From the Product root run each of:

```sh
python3 tests/timed_run.py
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
python3 -m compileall -q main.py errors.py domain application persistence web tests
```

Pass: every command exits 0; the actual timed run reports accepted durable name POST and landing,
each below one second, with all existing measurements passing; both suites and all format/lint/type/
compile gates pass. Run pinned Ruff/mypy/pytest/browser versions from the product test environment
(`pyproject.toml:L12-L17`, dev pins; `docs/nfdr.md` QC-62:L480-L495).
Existing architecture and trace walks cover the new module without exemptions; `comments.py` and
the landed `comments` feature word stay excluded, per `change_spec.md` CP-229–CP-230:L62-L66.
No gate runs in the primary product checkout; an out-of-worktree gate uses the disposable clone
at the explicit tested SHA prescribed in TL Review Notes.
