# Tech Lead instruction — move-timed-run: measure a saved status move and its landing

**Category:** nfdr
**Behaviour:** changing
**Product root:** products/tracker17 — every code and product-record path below is relative to it.
**Scope:** Add the move measurement, loaded-fixture report and final whole-run block in the two
existing test files, per `change_design.md` § 1, “Change Summary”, L15–L25, in
`tracker17 · tobiishi · 2026-10-21_move-timed-run`.
**Language resolution:** Python — step 1, `system/projects/tracker17/project.md` `Languages:`,
L12–L12; opened `<CORE>/doctrine/engineering/languages/python/README.md` and all seven destinations.

This document owns the task cut, coverage additions and verification gates for the change. Read
`change_spec.md` and `change_design.md` in the change named above for the product and interface
contracts; those filenames below always mean that change's artifacts. The plan's home is the change
folder prescribed by `<CORE>/doctrine/setup/kensaiapp_structure.md` § 2, “Per-project”,
L2122–L2128.

## Project layout

```text
products/tracker17/
  tests/
    timed_run.py                       ← modified: measurement, report, final wiring
    integration/
      test_timed_run.py                 ← modified: move tests and authorized continuity updates
```

The source layout needs no new directory, package or `__init__.py`. Placement follows
`change_design.md` § 2, “Blast Radius”, L29–L48: the harness lives outside the runtime
responsibilities in `docs/SDD.md` § 3,
“The parts, and the seams between them”, L198–L243. The complete module set and allowed/forbidden
imports remain `docs/nfdr.md` § 1.2, “Forbidden imports”, L139–L170; this plan adds no runtime edge.

Use the pinned test environment required by `docs/adr/0002-standard-library-only-no-web-framework.md`
§ Decision, L17–L24, and `docs/nfdr.md` QC-39/QC-62, L322–L326 and L505–L518. The exact suite
command in every task runs from the **change worktree root**, with that environment active; the
compile, Ruff and mypy commands run from **Product root**. The separate browser suite retains
`docs/nfdr.md` § 9, “Test strategy”, L550–L555, as its prerequisite boundary.

## TL Review Notes

Decisions by Tech Lead, 2026-10-21:

- **Task split:** Split design sub-job A into Task 1's measurement and Task 2's fixture report.
  They expose separate callables and can be tested independently (`change_design.md` § 3,
  “Sub-job A”, L70–L103). Task 2 uses the task identity introduced by Task 1. Keep design
  sub-job B's wiring and finite-timer/output updates together in Task 3 because its atomic-landing
  edge names both files (`change_design.md` § 3, L128–L131).
- **Hints distributed:** Carry design § 4's dedicated-measurement, whole-state, redirect and verdict
  approach into Task 1; carry its `_volume_line` approach into Task 2. This follows the task split
  without dropping any of the original hint (`change_design.md` § 4, “Code Strategy”, L135–L140).
- **Coverage strengthened:** Add an identity/project variant and a false-success pre-state variant
  in Task 1. On this reading, the ordinary fixture alone cannot distinguish a loaded task identity
  from tuple position, or its project from a hard-coded first project (`tests/timed_run.py`
  “seeded_state”, L191–L201). A real refusal alone cannot prove the separate `todo` precondition
  when a collaborator supplies a plausible success; both added cases directly assert design § 3's
  explicit contracts (`change_design.md` L76–L87).
  Reorder the varied report fixture in Task 2 for the same identity check, and capture both
  callables' output to assert the design's no-print boundary directly (`change_design.md`
  § 3, L95–L103).
- **One-change checks:** Put the two-file scope, old-test continuity and Python 3.11 compatibility
  readings in Task 4's review lane. They check this delta rather than permanent product behavior;
  a suite test pinned to this change's base would constrain later changes. Every comparison below
  uses the branch's own merge base, per development-plan § “A check that holds only for this
  change is never a suite test”.
- **Input cross-reference resolved:** CP-383 points to CP-391 for existing-test changes, but CP-391
  states the Python floor; Task 3 uses CP-392's explicit list and permission, matching design
  T11 (`change_spec.md` “What does not change”, L97–L100; “The commands that pass at the end”,
  L132–L133; “Existing tests that change”, L137–L156; `change_design.md` T11, L167–L167).
- **Gate environment:** Keep the card's command; use a terminal with loopback binding permitted.
  The first sandbox invocation of `pytest products/tracker17/tests/` returned
  `20 failed, 1266 passed, 30 errors`, including `socket.bind` raising
  `PermissionError: [Errno 1] Operation not permitted`. A minimal bind reproduced that error.
  The approved non-terminal run then hit start-test shutdown timeouts; the isolated command
  `pytest products/tracker17/tests/integration/test_start.py -x -q --tb=short` returned
  `1 failed, 39 passed`, at `child.communicate(timeout=30)`. The signal probe
  `python3 -c 'import signal; print(signal.getsignal(signal.SIGINT))'` returned `1` without a
  terminal and `<built-in function default_int_handler>` with one. These are execution conditions,
  not deferred product tests; no red-at-baseline task is inferred from them.
  The terminal invocation of the unchanged card command then exited 0:
  `1316 passed in 92.14s`, on Python 3.14.7 with pytest 9.0.3. That establishes the planning
  baseline, not the pinned-environment or Python 3.11 acceptance evidence; the implementation
  gates retain those product requirements.

### Task 1: Measure one move and verify its outcome (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** None

**What to build:** Add `MOVE_TASK_ID = 4` and
`measure_task_move(*, site, saved_data, timer)`, with required handed collaborators and a
`list[Timed]` result ordered POST, landing, total, per `change_design.md` § 3, “Sub-job A”,
L66–L94. Keep the existing `Timed` representation and `verdict` interface.

Implement the design's explicit contracts: resolve the moved task from the loaded pre-state before
timing; submit the one same-origin list-row move with exactly `status=in-progress` and `place=list`;
require the exact 303 address and the independent whole-state saved delta; request a valid landing
even when the readback is wrong; require its 200 and escaped completion sentence; measure only the
POST and GET, and sum those intervals. Use CP-373–CP-375's text from `change_text.md` in this change,
without rewriting it (`change_design.md` § 3, L70–L103).

#### Behaviours to verify (developer adds tests to `tests/integration/test_timed_run.py`)

- `test_timed_move_saves_only_status_and_lands_at_full_volume` — use the real `SavedData`, `Site`
  and tracker over a loaded 1,000-task fixture with 20 comments each. Record exactly one POST to
  `/tasks/4/move` with the exact two fields, form content type and same-origin mark, followed by
  one GET of `/projects/{loaded project id}?moved=in-progress&move_task=4`. Require the pre-state
  status `todo`, the whole saved state equal to only that status changed, three successful results
  with exact labels, no output from the measurement itself, and verdict 0 for fast handed readings
  (T1; CP-371/CP-372/CP-377/CP-378).
- `test_timed_move_uses_loaded_task_identity_and_project` — retain task 4 but reorder the loaded
  task tuple and place task 4 in a project other than the first one. Require the POST still targets
  identity 4 and the redirect/GET names that task's actual project; no other field changes
  (TL addition, design § 3 L76–L87).
- `test_timed_move_refusal_never_requests_landing` — use the real product over task 4 already
  `in-progress`. Require one refused POST, unchanged saved data, exactly two timer reads, no GET,
  three failed flags, a zero-duration failed landing, total equal to POST and verdict 1
  (T2; CP-379/CP-381/CP-384).
- `test_timed_move_requires_todo_even_with_plausible_success` — give the measurement a loaded
  non-`todo` task and a collaborator returning the exact 303 and plausible readback. Require POST
  and total failure despite the apparent success; the valid redirect still gets its landing
  (TL addition, design § 3 L81–L87).
- `test_timed_move_invalid_response_never_requests_landing` — parameterize 403, 500, non-303 with
  the exact Location, no Location, wrong project/task, wrong destination, missing/extra/reordered
  query fields and refusal/confirmation addresses. Include a wrapper that drops the same-origin
  mark before forwarding to the real site and observes 403 with unchanged saved data. Require
  exactly two readings, no GET, failed POST/landing/total, zero landing, POST-only total and
  verdict 1 (T3; CP-371/CP-377/CP-379).
- `test_timed_move_requires_exact_saved_delta_but_still_lands` — after a correct redirect,
  parameterize missing readback, unchanged state, wrong moved status, a second task changed, the
  moved task's other fields/comments changed, and project, either counter, assignee-list or
  operator-name changes. Use populated assignee/operator values. Require POST and total failure,
  the exact GET still made, four readings and verdict 1; assert the landing flag separately
  against its own response (T4; CP-377(b)).
- `test_timed_move_landing_requires_200_and_completion` — after a real successful POST, substitute
  a non-200 with the correct sentence, a 200 without it, title-only content, another task's sentence
  and another destination status. Require POST success, landing/total failure and verdict 1
  (T5; CP-378/CP-381/CP-385).
- `test_timed_move_completion_escapes_loaded_title` — use a moved title containing `<`, `&`,
  double/single quotes and a non-ASCII character. Accept the page's exact escaped completion
  sentence; refuse its raw or incorrectly escaped counterpart (T5; CP-378).
- `test_timed_move_excludes_setup_readback_and_gap_from_intervals` — record the initial load
  before tick 1, only POST between ticks 1–2, readback between ticks 2–3 and only GET between
  ticks 3–4. Assert the whole sequence and exact count of readings. A large gap between the
  intervals changes neither individual duration nor their summed total (T6; CP-376).
- `test_timed_move_requires_each_interval_and_total_below_limit` — parameterize fast parts and
  total; total exactly 1 s and above with fast parts; POST exactly 1 s and 1.5 s; GET exactly
  1 s and above. Assert raw durations, unchanged success flags for a correctly completed action,
  precise problem labels and verdict. Include a raw duration just below 1 s that prints
  `1000.0 ms` but passes that row (T7; CP-375/CP-380).
- `test_timed_move_rows_print_exact_times_and_ordered_problems` — pass the helper's results to
  `verdict` and assert all three complete lines, one-decimal milliseconds and no suffix on success.
  A refused POST of exactly 1 s prints `refused or failed, at or over 1 s` in that order, the
  failed zero landing, and the matching failed/slow total; cover 1.5 s formatting too
  (T8; CP-375/CP-379/CP-380).

These cases refine design T1–T8 (`change_design.md` § 5, “Test Additions”, L157–L164). Hand recording
sites, saved-data wrappers and timers through the existing seams; keep the measurement real
(`tests/integration/test_timed_run.py` “Intercept”, L200–L213, and “EventLog”, L1276–L1316).

#### Held by review

- Construct the expected state without calling the workflow move rule; no test of returned values
  alone proves that independence. Read the helper's expectation and imports in the diff
  (`change_design.md` § 3, L81–L84).
- Preserve `TimedAction`, `_measure_action`, its three consumers and every earlier action's
  behavior; the unchanged-source comparison is in Task 4 (`change_design.md` § 4, L139–L140).

#### Implement

Infer from failing tests.

# Hint:
A dedicated two-field measurement keeps the existing one-field `TimedAction` and its consumers
unchanged. Use independent whole-state equality for success, exact response/address gating for the
GET, and the existing `verdict` seam (design § 4's measurement approach).

#### Verification gate

From the change worktree root, in the active test environment and a terminal allowing loopback:

```sh
pytest products/tracker17/tests/integration/test_timed_run.py
pytest products/tracker17/tests/
```

From Product root:

```sh
python3 -m compileall -q tests/timed_run.py tests/integration/test_timed_run.py
```

Pass: every new measurement case passes, all existing tests pass, and compile exits 0. The whole
run still has its old output until Task 3 wires in the new callables.

### Task 2: Report the loaded move fixture (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** Task 1 — its shared moved-task identity.

**What to build:** Add `move_fixture_report(state)` returning a string without printing. Read task
and uniform-comment counts from the loaded state, and title/first-comment lengths from task 4,
counted in code points, per `change_design.md` § 3, “Sub-job A”, L95–L103. Use the complete
CP-373 fixture-line shape from this change's `change_text.md`.

#### Behaviours to verify (developer adds tests to `tests/integration/test_timed_run.py`)

- `test_move_fixture_report_uses_loaded_full_volume` — save and reload the normal fixture and
  assert the entire report: 1,000 tasks, 20 comments each, 20,000 in all and task 4's actual text
  lengths. Capturing output around the report call finds no printed line (T9; CP-374/CP-386).
- `test_move_fixture_report_uses_varied_loaded_counts_and_code_points` — save and reload a
  300-task/3-comment state with task 4 titled `Plan 😀😀` and its first comment `Note 😀`.
  Keep the first task's text different and reorder tasks. Require the exact line with 900 comments,
  title length 7 and comment length 6; every number comes from the loaded fixture, not constants
  or tuple position (T9; CP-374/CP-386).

T9 supplies these report checks (`change_design.md` § 5, “Test Additions”, L165–L165). Unequal
per-task comment counts remain outside this change's specified fixture policy (`change_spec.md`
“Out of Scope”, L216–L217); do not add a new policy for them.

#### Implement

Infer from failing tests.

# Hint:
Reuse `_volume_line` for the loaded volume portion, and obtain the text lengths from the moved task
identified by `MOVE_TASK_ID` (design § 4's reporting approach).

#### Verification gate

From the change worktree root, in the active test environment and a terminal allowing loopback:

```sh
pytest products/tracker17/tests/integration/test_timed_run.py
pytest products/tracker17/tests/
```

From Product root:

```sh
python3 -m compileall -q tests/timed_run.py tests/integration/test_timed_run.py
```

Pass: both complete report cases and the full existing suite pass; compile exits 0.

### Task 3: Append the move block and preserve existing callers (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** Task 1 — move measurement; Task 2 — loaded-fixture report.

**What to build:** Append the four move lines after `_run_new_actions` using an independent
`move-volume` location under the supplied temporary root, the unchanged `open_task_volume`, the
handed timer and the existing aggregate verdict. Preserve `main(directory=None, timer=...)`.
The whole-run wiring and finite-timer/exact-output changes form one atomic task, per
`change_design.md` § 3, “Sub-job B” and “Atomic-landing edge”, L109–L131.

Append four fast readings after the old readings in exactly the CP-392 callers and shared
`_run_readings` source. Do not extend the existing three-action parameter families with a fourth
case: their old cases remain intact; add move-specific cases alongside them. Extend the exact
output expectation by the final four labels without altering its previous prefix assertions
(`change_spec.md` “Existing tests that change”, L137–L156).

#### Behaviours to verify (developer adds tests to `tests/integration/test_timed_run.py`)

- `test_timed_run_appends_exact_move_block_and_nothing_after` — a real full run with deterministic
  fast readings exits 0. Assert every old output label and its position, then exactly the fixture,
  POST, landing and total move lines, with exact report contents and formatted fast times. The
  final line is the move total; there is no footer (T10; CP-373/CP-375/CP-381).
- `test_timed_move_fixture_is_independent_and_product_data_unchanged` — inspect the run's
  `move-volume` state, all 1,000 tasks with 20 comments, exactly task 4's status changed. Check its
  saved location is inside the supplied root and distinct from every earlier fixture. Compare
  product `data/` before/after as absent or identical file bytes (T10; CP-372).
- `test_timed_run_fails_when_only_move_total_reaches_limit` — give every prior action fast readings,
  then move POST and GET below 1 s with total exactly 1 s and above in separate cases. Only the
  move total has the timing problem, and `main` returns 1 (T12; CP-380/CP-381).
- `test_timed_run_propagates_move_submission_and_landing_timing_failures` — parameterize the move
  POST and GET at/exceeding 1 s while earlier actions pass. Require exactly that move row and
  its total to be slow, and `main` returns 1 (T12; CP-380/CP-381).

Retain and run these existing tests under their exact names with their old cases/assertions:

- `test_timed_run_fails_when_only_the_edit_fails`
- `test_timed_run_fails_when_only_a_label_action_fails`
- `test_full_timed_run_fails_when_only_name_measurement_fails`
- `test_timed_run_fails_when_only_a_new_action_total_reaches_limit` — all three cases
- `test_timed_run_propagates_new_submission_and_landing_timing_failures` — all three cases
- `test_timed_run_appends_exactly_three_ordered_action_blocks` — its exact expectation gains only
  the final four labels; keep its old-prefix, success and no-problem assertions
- `test_new_timed_fixtures_are_independent_and_preserve_name_save_precondition`
- `test_new_timed_actions_leave_product_data_unchanged`
- `test_timed_run_reports_actual_fixture_lengths_for_all_three_actions`

The new and existing cases carry T10–T12 (`change_design.md` § 5, “Test Additions”, L166–L173).
Task 1's real refusal and missing-result cases prove failure flags reach the same `verdict` used
here; do not patch `main` or its internal names to simulate them.

#### Held by review

- Update the two files' opening descriptions and `main`'s description to include the newly measured
  move; preserve their existing requirement/path trace anchors (`tests/timed_run.py` module
  docstring, L1–L23 and “main”, L796–L799; `tests/integration/test_timed_run.py` module docstring,
  L1–L12). This is a correction in the files Task 3 already opens, not a new product record.
- Task 4 checks the old assertions, cases and older action implementations against the branch's
  merge base; runtime green alone cannot establish that none were weakened.

#### Implement

Infer from failing tests.

#### Verification gate

From the change worktree root, in the active test environment and a terminal allowing loopback:

```sh
pytest products/tracker17/tests/integration/test_timed_run.py
pytest products/tracker17/tests/
```

From Product root:

```sh
python3 -m compileall -q tests/timed_run.py tests/integration/test_timed_run.py
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: all new and old cases pass, exact output appends only the four specified lines, all four
product-root commands exit 0, and a slow injected move changes the exit verdict without changing
any earlier action's result or the 1.0-second limit.

### Task 4: Verify change scope, continuity and real-command acceptance (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** Tasks 1, 2 and 3 — their complete two-file delta.

**What to build:** Verify the completed delta against the review criteria below, per
`change_design.md` § 5, “Acceptance checks”, L187–L199. These are checks of this change, with
no permanent suite test asserting its merge base.

#### Deliverables verified by review (no test asserts these — the gate is the diff)

- Two-file product scope — the excluded-path diff below is empty. No runtime file, dependency,
  manifest, pin or product record changes (CP-382; design § 2).
- Existing tests and old actions — inspect both files against the merge base. Every old test
  name, case and assertion remains; CP-392 permits only appended readings and the final output
  extension. Every older measurement, fixture opener, row, done-check and limit stays unchanged
  (CP-383/CP-392; design T11).
- Independent success check — the new helper creates its expected state from the loaded fixture
  without calling the workflow rule, and uses the exact redirected address and escaped result
  sentence rather than incidental state order or title presence (design § 3).
- Python 3.11 compatibility — read new syntax and library uses against the product's existing
  floor. Add no feature requiring a later Python, no library dependency and no pin change; this
  reading is not a claim that a Python 3.11 suite ran (CP-391; `docs/nfdr.md` QC-60, L496–L500).
- Real timing — in a fresh clone at the commit under test, the real command exits 0, prints
  all old rows and the four final move lines, and every move duration is strictly below 1 s.
  A duration at/above the limit is a finding in output/exit status; keep the limit and product
  implementation intact (CP-382/CP-387).

#### Implement

Verified by review — no test.

#### Verification gate

From Product root, compare with this branch's own merge base; these commands include uncommitted
edits as well as the branch delta:

```sh
git -C . diff "$(git -C . merge-base main HEAD)" --name-only -- . ':(exclude)tests/timed_run.py' ':(exclude)tests/integration/test_timed_run.py'
git -C . diff "$(git -C . merge-base main HEAD)" -- tests/timed_run.py tests/integration/test_timed_run.py
git -C . show "$(git -C . merge-base main HEAD):products/tracker17/tests/integration/test_timed_run.py"
```

Pass: the first command prints nothing. Read the second and third outputs against every review
criterion, including the two files' updated descriptions, without adding a fixed-base test.

From the change worktree root, with its pinned test environment active and terminal/loopback
conditions satisfied:

```sh
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/
```

Pass: full suite exits 0 with every old test still present; browser suite exits 0 where NFDR § 9
supports layer 5. Record an unavailable browser prerequisite as such, never as a passing suite.

For CP-387, from the change worktree root create a disposable clone and select the commit under
test; each Git operation remains a separate call:

```sh
move_check=$(mktemp -d)
git -C . clone --quiet . "$move_check"
git -C "$move_check" checkout --quiet "$(git -C . rev-parse HEAD)"
(cd "$move_check/products/tracker17" && python3 tests/timed_run.py)
(cd "$move_check" && pytest products/tracker17/tests/)
```

Pass: both checks exit 0 and the timed output meets the real-timing criterion. Read the output,
then remove the clone from outside it in its own command:

```sh
rm -rf "$move_check"
```

The clone/run/remove form follows `<CORE>/roles/CROSS_ROLE.md` § “Every seat — a run leaves the
product's main checkout as it found it”, L8–L29. In a runner whose command calls do not share shell
variables, retain the exact generated temporary path between calls.

From Product root in the pinned environment, finish with:

```sh
python3 -m compileall -q tests/timed_run.py tests/integration/test_timed_run.py
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: all four exit 0, the full suite has no new failures, and each review criterion has a recorded
verdict. The real timing and browser checks are acceptance evidence, not tests added by Task 4.
