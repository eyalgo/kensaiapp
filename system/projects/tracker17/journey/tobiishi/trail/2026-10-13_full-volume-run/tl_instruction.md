# Tech Lead instruction — full-volume-run: Time comments and People assignee changes

This document owns the task cut, test behaviours and verification commands for the timed-run extension specified by `tracker17 · tobiishi · 2026-10-13_full-volume-run`, `change_spec.md` § Rules. It is a scaffold for implementation, with the harness interfaces from `change_design.md` § 3.

**Date:** 2026-10-13
**Category:** nfdr
**Behaviour:** changing
**Product root:** products/tracker17
**Scope:** Extend only `tests/timed_run.py` and `tests/integration/test_timed_run.py` for comment add, People assignee add and People assignee remove, with CP-276–CP-292's existing-action and production-code fences.
**Language resolution:** Python — step 1, `system/projects/tracker17/project.md:L12-L12`, `Languages:`; opened `core/doctrine/engineering/languages/python/README.md` and all six routed concerns, including `core/doctrine/engineering/testing_python.md`.

Paths below are relative to Product root unless explicitly absolute. The change worktree is `.worktrees/2026-10-13_full-volume-run`. The path resolver returned `product_path: products/tracker17` and that worktree as `product_worktree` (`python3 core/tools/development_path.py resolve --format json --worktree .worktrees/2026-10-13_full-volume-run --project tracker17 --key 2026-10-13_full-volume-run`, exit 0).

---

## Project layout

```text
products/tracker17/
  tests/
    timed_run.py                       ← modified
    integration/
      test_timed_run.py                 ← modified
```

Create no directory, module or `__init__.py`. Placement follows `change_design.md:L35-L60` § 2, “Blast Radius”: the harness owns fixture preparation, measurement, result verification and reporting. The five runtime parts are defined by `docs/SDD.md:L195-L217` § 3, “The parts” and “The units”. Their allowed and forbidden imports remain `docs/nfdr.md:L123-L153` § 1.2, QC-13–QC-19. No production part imports this harness or its tests under QC-19.

The unchanged interface is `Timed(label, seconds, created)` and `main(directory, timer)` (`tests/timed_run.py:L99-L103`, `:L525-L556`, `Timed` and `main`). Preserve every existing function signature, action fixture, label, row, limit and assertion. New measurement collaborators are required keyword-only `site`, `saved_data` and `timer`, per `change_design.md:L81-L88` § 3, “Exposes”. The new site seam requires only `handle(method, target, headers, body)`.

## Verification commands

Run the card's `pytest products/tracker17/tests/` from the change worktree root (`system/projects/tracker17/project.md:L10-L10`, `Test command:`). Run targeted `pytest tests/integration/test_timed_run.py` and the Ruff commands from Product root. Every suite gate must collect tests and exit 0. Do not treat a socket permission refusal as a product regression or remove the socket checks.

Provision the execution environment from the unchanged `tests/requirements.txt`, whose install comment and locked versions are at `tests/requirements.txt:L1-L19`; QC-39 and QC-62 require the locked tools (`docs/nfdr.md` § 2, QC-39, and § 8, QC-62). The final clone gate below gives the exact provisioning command. The host's baseline pytest version is recorded in TL Review Notes and is not evidence of a run at the locked versions.

The suite process must have local loopback socket permission and normal terminal SIGINT handling. The start tests send SIGINT to their child (`tests/integration/test_start.py:L515-L535`, `_run_real_start`). A signal probe in this planning run, `python3 -c 'import signal; print(signal.getsignal(signal.SIGINT))'`, returned `1` with plain pipes and `<built-in function default_int_handler>` with a terminal. Request approval for a command needing protected effects before it executes, including clone checkout metadata, rather than changing a failed run's verdict.

## TL Review Notes

These are the Tech Lead's calls on 2026-10-13.

- **Task split:** Split design § 3's harness sub-job A and consumer sub-job B into one task per action, with that action's tests beside its implementation, followed by whole-run integration. Each action has its own location and no state dependency on the other two (`change_design.md:L163-L169`, “Build sequence”). This cut makes each measurement independently testable and avoids a later tests-only task whose subject is already green. Task 4 consumes the shared `ASSIGNEE_NAME` introduced by Task 3; its dependency records that symbol, not shared saved state.
- **Compatibility by review:** Task 1 carries design T12's timer-input extension before whole-run integration. It uses the review-verified lane because preserving old assertions while adding unused readings is a diff property, not a new behaviour that can honestly fail first. `Ticks` consumes readings only when called (`tests/integration/test_timed_run.py:L46-L54`, `Ticks`). Task 1 orders compatibility work first but is not an interface dependency of Tasks 2–4.
- **Timing coverage added:** Tasks 2–4 explicitly check that setup and saved-data reads are outside the timed POST/GET spans. Design § 3's measurement contract states that fence, but § 5 T9 enumerates duration arithmetic without the collaborator-event ordering check. The added check prevents a duration that accidentally includes validation from satisfying the arithmetic assertions.
- **Escaping coverage added:** Task 2 uses a valid selected-task title and saved operator name containing markup characters in a fixture variant. CP-283 and design § 3 require escaped comparison values (`change_spec.md:L53-L58`, CP-283), but design T8's wrong-title cases alone do not prove that escaping holds.
- **Change-only evidence:** Task 6 checks production/documents untouched, only the two allowed code files changed, and old tests retained against the branch's current merge base. This replaces design V3's fixed “change input commit” comparison because these obligations end with this change; they are review evidence, never collected suite tests.
- **Tool environment:** The initial card command used host pytest 9.0.3 and collected 1,047 items (`pytest products/tracker17/tests/`, session header). The lock names pytest 9.1.1 (`tests/requirements.txt:L13-L13`, pinned dependency). Retain the exact card command; Task 6 runs it in the locked clone environment so the final acceptance evidence has the requested versions.
- **Baseline execution boundary:** The sandboxed card run exited 1 with 997 passed, 20 failed and 30 errors, including `socket.bind` raising `PermissionError: [Errno 1] Operation not permitted` (`pytest products/tracker17/tests/`, actual summary and listener traceback). An approved run with plain pipes was stopped after the SIGINT probe above identified an ignored signal; its exit was 143, not a pass. The approved terminal run of the same command exited 0 with `1047 passed in 47.89s`, at input commit `5a5e928678c4b1ea85733a7a2fa1dd36f1614b37`. These execution-boundary results do not supply any `Red at baseline:` task: the terminal baseline is green.
- **Final review task:** Move design V1–V3 into Task 6's review-verified deliverables so fresh-clone timing, quality gates and scope evidence have explicit pass criteria without manufacturing a red suite test for a one-change obligation.

### Task 1: Extend the three existing whole-run timer scripts (`tests/integration/test_timed_run.py`)

**Dependencies:** None

**What to build:** Append four under-limit timer readings per new action, twelve readings total, to only the three existing whole-run failure tests named in CP-289 (`change_spec.md:L89-L89`, CP-289).

#### Deliverables verified by review

- `test_timed_run_fails_when_only_the_edit_fails`, `test_timed_run_fails_when_only_a_label_action_fails` and `test_full_timed_run_fails_when_only_name_measurement_fails` retain their names, cases, slow-action choices and every assertion; only their supplied timer streams gain the twelve readings.
- No other existing test is removed, skipped, loosened or edited as part of this compatibility task.

#### Implement

Verified by review — no test.

#### Verification gate

From Product root, run `pytest tests/integration/test_timed_run.py`. From the change worktree root, run `pytest products/tracker17/tests/`. Review `git -C .worktrees/2026-10-13_full-volume-run diff "$(git -C .worktrees/2026-10-13_full-volume-run merge-base main HEAD)" -- products/tracker17/tests/integration/test_timed_run.py`.

Pass: both commands exit 0, all existing tests pass, and both review criteria hold. The extra unused readings must already be compatible before `main` consumes them.

### Task 2: Measure comment add and report its fixture (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** None

**What to build:** `open_comment_volume(saved_data)`, `measure_comment_add` and `comment_fixture_report(state)`, with `COMMENT_TASK_ID` 250, ordinary `COMMENT_TEXT` distinct from seeded comments, and `COMMENT_OPERATOR_NAME` `Jordan Rivera`, per design § 3 “Exposes” (`change_design.md:L89-L107`). Keep whole-run wiring for Task 5. The opener saves its own full-volume fixture with the operator name and returns the real site and loaded pre-state. The measurement returns three existing `Timed` values, ordered submission, landing, total.

#### Behaviours to verify

Add tests in `tests/integration/test_timed_run.py`:

- `test_timed_comment_fixture_saves_full_volume_and_operator` — 1,000 tasks with 20 comments each, a saved ordinary operator name, and save/load through the supplied real `SavedData` before the request (CP-277; design T2).
- `test_timed_comment_submission_saves_exact_delta_and_lands` — exactly one same-origin POST to `/tasks/250/comments`, body containing only `text`, then GET to exactly `/tasks/250?comment_added=21`; host is `127.0.0.1:8017`. Readback preserves the entire pre-state except one final comment on task 250, with submitted text and the pre-state's operator name. Compare all fields except only the newly added comment's timestamp (CP-278–CP-279; T3–T4).
- `test_timed_comment_refusal_or_wrong_redirect_never_requests_landing` — real no-name refusal and scripted failure redirect, 500, another non-303 status, non-303 with otherwise correct Location, missing Location, wrong task/count, plain redirect and unrelated address all produce three failed rows and verdict 1. There is no GET; retain measured POST duration, zero landing duration and total equal to POST (CP-282, CP-288; T6).
- `test_timed_comment_plausible_redirect_requires_exact_saved_change` — correct redirect with no write, missing saved state, wrong text/author/target/order/count, altered old comment or unrelated state change fails submission and total even with a plausible landing. Readback comparison must be independent of the product action being checked (CP-279, CP-282; T7).
- `test_timed_comment_landing_requires_completion_and_new_text` — after a real successful POST, 404/500, missing/wrong completion line, wrong title, correct line without new text, and new text without line fail landing and total while submission passes. A correct replacement page passes. A title with `<`, `&`, quotes and an astral character verifies escaped completion text; a different valid saved operator name containing markup characters verifies that readback checks the loaded name rather than a fixture-name constant (CP-279, CP-283, CP-288; T8).
- `test_timed_comment_intervals_exclude_setup_and_readback` — handed-in recording collaborators place only the single POST and single GET between their respective timer readings; initial and fresh saved-data loads occur outside the intervals (design § 3, “Measurement contract”, points 1–5).
- `test_timed_comment_each_interval_and_total_are_strictly_below_limit` — deterministic POST/GET durations 0.4/0.5 pass; 0.5/0.5 fails only total; a sum above 1 fails total; POST exactly 1 fails POST/total; GET exactly 1 fails GET/total. Verify ordered labels, duration sum excluding an arbitrary timer gap, verdict 1 on each failure, one-decimal millisecond formatting and the exact problem words in CP-285 (CP-284–CP-287; T9).
- `test_comment_fixture_report_uses_loaded_values_and_code_points` — CP-286's literal report shape uses selected-task title/original comment, loaded operator name, actual task count, actual comments-per-task and summed total, and actual submitted comment length. Valid uniform fixture variants retaining task 250 but changing volume/text lengths, including an astral character, change the report accordingly (T11).

#### Implement

Infer from failing tests.

```text
# Hint:
Compare immutable whole-state values, allowing only the intended delta; mask only the new comment's timestamp. Keep pre/post saved-data reads outside timer spans. Query-encode expected names and HTML-escape expected landing values. Derive fixture counts from the loaded pre-state.

For request and landing tests, use a recording wrapper around a real site. For false-success tests, use a scripted responder that writes an independently constructed wrong saved state. Supply these collaborators; patch no module name.
```

#### Verification gate

From Product root, run `pytest tests/integration/test_timed_run.py`, `ruff format --check .` and `ruff check .` in the locked environment. From the change worktree root, run `pytest products/tracker17/tests/`.

Pass: all commands exit 0, this action's tests pass, and no existing test gains a failure. `main` still has its existing output until Task 5.

### Task 3: Measure People assignee add and report its fixture (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** None

**What to build:** `open_assignee_add_volume(saved_data)`, `measure_assignee_add` and `assignee_add_fixture_report(state)`, with ordinary `ASSIGNEE_NAME` `Avery Chen`, per design § 3 “Exposes” (`change_design.md:L89-L107`). Its own saved/loaded full-volume fixture lacks that name. Keep whole-run wiring for Task 5. Return submission, landing, total as existing `Timed` values.

#### Behaviours to verify

Add tests in `tests/integration/test_timed_run.py`:

- `test_timed_assignee_add_fixture_starts_without_submitted_name` — real save/load, 1,000 tasks and 20 comments each; intended name absent (CP-277; T2).
- `test_timed_assignee_add_saves_only_requested_name_and_lands` — one POST to `/assignees` with only `name`, the host and same-origin headers, followed by exactly `/people?added=Avery+Chen`. Whole-state readback adds exactly that name at the end, preserving unrelated names, order, tasks and all other fields (CP-278, CP-280; T3, T5).
- `test_timed_assignee_add_refusal_or_wrong_redirect_never_requests_landing` — real duplicate-name refusal and scripted failure redirect, 500, another non-303 status, non-303 with correct Location, missing Location, wrong name, plain and unrelated redirects produce three failed rows, retained POST duration, zero landing duration, total equal to POST and verdict 1; no GET (CP-282, CP-288; T6).
- `test_timed_assignee_add_plausible_redirect_requires_exact_saved_change` — correct address with no write, missing state, unchanged/wrong name, an additional name, name reorder/removal or unrelated state change fails submission and total even with a plausible correct-address landing (CP-280, CP-282; T7).
- `test_timed_assignee_add_landing_requires_its_completion` — after a real save, wrong status, absent completion, another action's line and wrong name fail landing and total while submission passes; the correct `You added 'Avery Chen' to the assignees.` line is a passing control (CP-283, CP-288; T8).
- `test_timed_assignee_add_intervals_exclude_setup_and_readback` — collaborator event ordering proves only POST/GET are timed, with pre/post saved-data loads outside spans (design § 3, “Measurement contract”).
- `test_timed_assignee_add_each_interval_and_total_are_strictly_below_limit` — the same deterministic boundary matrix as Task 2, with this action's three CP-285 labels, exact failure sets, sum excluding the timer gap and unchanged 1.0 limit (CP-284–CP-287; T9).
- `test_assignee_add_fixture_report_uses_loaded_values_and_code_points` — CP-286's exact shape uses actual loaded volume, comments and text lengths, plus submitted name length. Different valid uniform volumes and texts with an astral character detect copied counts and byte/UTF-16 length substitution (T11).

#### Implement

Infer from failing tests.

```text
# Hint:
Compare immutable whole-state values, allowing only the intended delta; mask only the new comment's timestamp where that delta applies. Keep pre/post saved-data reads outside timer spans. Query-encode expected names and HTML-escape expected landing values. Derive fixture counts from the loaded pre-state.

Use a recording wrapper around a real site for request and landing cases, and a scripted responder that writes an independently constructed wrong saved state for false-success cases. Supply both as collaborators; patch no module name.
```

#### Verification gate

From Product root, run `pytest tests/integration/test_timed_run.py`, `ruff format --check .` and `ruff check .` in the locked environment. From the change worktree root, run `pytest products/tracker17/tests/`.

Pass: all commands exit 0, this action's tests pass, and no existing test gains a failure.

### Task 4: Measure People assignee remove and report its fixture (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** Task 3 supplies the shared `ASSIGNEE_NAME` ordinary input.

**What to build:** `open_assignee_remove_volume(saved_data)`, `measure_assignee_remove` and `assignee_remove_fixture_report(state)`, using design § 3's ordinary `ASSIGNEE_NAME` `Avery Chen` (`change_design.md:L89-L107`, “Exposes”). Its own saved/loaded full-volume fixture carries that name. Keep whole-run wiring for Task 5. Return submission, landing, total as existing `Timed` values.

#### Behaviours to verify

Add tests in `tests/integration/test_timed_run.py`:

- `test_timed_assignee_remove_fixture_starts_with_submitted_name` — real save/load, 1,000 tasks and 20 comments each; intended name present (CP-277; T2).
- `test_timed_assignee_remove_changes_only_list_and_lands` — one same-origin POST to `/assignees/remove`, body containing only `name`, followed by exactly `/people?removed=Avery+Chen`. Readback equals the pre-state with only that name removed. A variant with other names and a task already assigned to Avery proves name order and every task assignee stay intact (CP-278, CP-281; T3, T5; `docs/fdr.md` § Rules, R-61).
- `test_timed_assignee_remove_refusal_or_wrong_redirect_never_requests_landing` — real unlisted-name refusal and scripted failure redirect, 500, another non-303 status, non-303 with correct Location, missing Location, wrong name, plain/unrelated addresses produce three failed rows, retained POST duration, zero landing duration, total equal to POST and verdict 1; no GET (CP-282, CP-288; T6).
- `test_timed_assignee_remove_plausible_redirect_requires_exact_saved_change` — no write, missing state, requested name still present, wrong or extra name removed, unrelated name reordered, task assignee cleared or other unrelated state change fails submission and total despite the correct address and plausible landing (CP-281–CP-282; T7).
- `test_timed_assignee_remove_landing_requires_its_completion` — after real removal, wrong status, absent completion, another action's line or wrong name fails landing and total while submission passes. The passing control includes the full line `You removed 'Avery Chen' from the assignees, and tasks that already carry the name keep it.` (CP-283, CP-288; T8).
- `test_timed_assignee_remove_intervals_exclude_setup_and_readback` — collaborator event ordering proves only POST/GET are timed, with pre/post saved-data loads outside spans (design § 3, “Measurement contract”).
- `test_timed_assignee_remove_each_interval_and_total_are_strictly_below_limit` — Task 2's deterministic boundary matrix with the removal's labels, exact failure sets, sum excluding timer gap and unchanged 1.0 limit (CP-284–CP-287; T9).
- `test_assignee_remove_fixture_report_uses_loaded_values_and_code_points` — CP-286's exact shape uses actual pre-removal volume and text lengths, including submitted name length. Valid alternate uniform fixtures with astral characters expose constant or byte/UTF-16 counts (T11).

#### Implement

Infer from failing tests.

```text
# Hint:
Compare immutable whole-state values, allowing only the intended delta; mask only the new comment's timestamp where that delta applies. Keep pre/post saved-data reads outside timer spans. Query-encode expected names and HTML-escape expected landing values. Derive fixture counts from the loaded pre-state.

Use a recording wrapper around a real site for request and landing cases, and a scripted responder that writes an independently constructed wrong saved state for false-success cases. Supply both as collaborators; patch no module name.
```

#### Verification gate

From Product root, run `pytest tests/integration/test_timed_run.py`, `ruff format --check .` and `ruff check .` in the locked environment. From the change worktree root, run `pytest products/tracker17/tests/`.

Pass: all commands exit 0, this action's tests pass, and no existing test gains a failure.

### Task 5: Append the three action blocks and aggregate every verdict (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** Tasks 2, 3 and 4 supply the openers, measurements and reports consumed here. Task 1 supplies the extended timer streams used by the existing whole-run tests.

**What to build:** Wire the three measurements into existing `main(directory, timer)` using locations `comment-volume`, `assignee-add-volume` and `assignee-remove-volume` beneath its supplied directory. Append the blocks in CP-285's explicit order after the unchanged old output prefix. Aggregate every new row's verdict with every old one. Update the two edited modules' trace docstrings for their added coverage (design § 3 A/B, “Scope”; `change_design.md:L76-L79`, `:L149-L151`).

#### Behaviours to verify

Add tests in `tests/integration/test_timed_run.py`:

- `test_timed_run_appends_exactly_three_ordered_action_blocks` — all old creates, fixtures and action labels retain their original order and bar; then comment fixture and its three rows, assignee-add fixture and its three rows, assignee-remove fixture and its three rows. No extra action or extra old-action total appears (CP-276, CP-285; T1).
- `test_new_timed_fixtures_are_independent_and_preserve_name_save_precondition` — each real location is distinct under the supplied temporary directory, with its loaded pre-state at 1,000 × 20 and its action-specific conditions. Acting on one leaves the other fixtures unchanged. The old name-save fixture starts without an operator name (CP-277; T2).
- `test_new_timed_actions_leave_product_data_unchanged` — observe the actual Product root `data/` before and after; preserve absence, or, if present, every entry and byte. Do not create or mutate `data/` to arrange a test. Fixture state changes must occur only in the supplied temporary directory (CP-277; T2).
- `test_timed_run_reports_actual_fixture_lengths_for_all_three_actions` — one whole-run test checks each CP-286 literal fixture-line shape against that action's loaded pre-state and actual submitted values, including every task's 20 comments, the 20,000 total, selected-task text where applicable and code-point lengths. The passing report contains no `over` or `refused` (CP-285–CP-286, CP-288; T11).
- `test_timed_run_fails_when_only_a_new_action_total_reaches_limit` — parameterize all three actions; deterministic readings put only its total at 1.0 while the parts and every other row pass. Only that total has the problem suffix and `main` returns 1, including CP-287's assignee-removal example (T10).
- `test_timed_run_propagates_new_submission_and_landing_timing_failures` — for each new action, a slow POST or slow GET produces exactly that row and its total as slow; every unrelated action passes and `main` returns 1 (CP-287; T10).
- Keep Task 1's three failure tests passing with their original slow-row assertions and all other existing tests intact (CP-289; T12).

#### Implement

Infer from failing tests.

```text
# Hint:
Keep pre/post saved-data reads outside timer spans. Derive fixture counts from the loaded pre-state. Compare immutable whole-state values allowing only the intended delta; mask only the new comment's timestamp. Query-encode expected names and HTML-escape expected landing values.

Use handed-in timers and recording site collaborators for the regression checks; patch no module name. Derive expected output and saved deltas independently of the harness's predicates and templates.
```

#### Verification gate

From Product root, run `pytest tests/integration/test_timed_run.py`, `ruff format --check .` and `ruff check .` in the locked environment. From the change worktree root, run `pytest products/tracker17/tests/`.

Pass: all commands exit 0; new whole-run behaviours and every existing harness test pass. The real-clock acceptance and branch-scope review remain Task 6's deliverables.

### Task 6: Verify the finished harness at its code commit (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** Task 5 supplies the complete whole-run extension.

**What to build:** Collect falsifiable review evidence for design V1–V3 and CP-289–CP-292. Add no suite test for a fixed commit or for files unchanged only during this change.

#### Deliverables verified by review

- Production paths and product records unchanged — the protected-path diff below prints nothing.
- Only the two scoped product files changed — the excluded-path diff below prints nothing. Do not edit a dependency, threshold or product document to improve a measurement.
- Every old harness test remains present and unskipped, with no assertion weakened — compare the merge-base test file with the working file using the commands below; apart from the three timer extensions, old test bodies stay unchanged. New tests and shared test scaffolding may be added.
- Fresh-clone real-clock command exits 0 — all old report lines retain their labels/order and the three CP-285 blocks show successful POST, GET and total, each strictly below 1.0 seconds. Each CP-286 fixture line describes the fixture actually used.
- Fresh-clone card suite and locked Ruff checks exit 0 — no skipped/removed/weakened old harness assertion, and no formatter/linter finding.

#### Implement

Verified by review — no test.

#### Verification gate

First run `pytest products/tracker17/tests/` from the change worktree root. Then run the following read-only scope checks there, including uncommitted changes:

```sh
git -C .worktrees/2026-10-13_full-volume-run diff "$(git -C .worktrees/2026-10-13_full-volume-run merge-base main HEAD)" -- products/tracker17/domain products/tracker17/application products/tracker17/persistence products/tracker17/web products/tracker17/main.py products/tracker17/errors.py products/tracker17/docs
git -C .worktrees/2026-10-13_full-volume-run diff --name-only "$(git -C .worktrees/2026-10-13_full-volume-run merge-base main HEAD)" -- products/tracker17 ':!products/tracker17/tests/timed_run.py' ':!products/tracker17/tests/integration/test_timed_run.py'
git -C .worktrees/2026-10-13_full-volume-run show "$(git -C .worktrees/2026-10-13_full-volume-run merge-base main HEAD):products/tracker17/tests/integration/test_timed_run.py"
git -C .worktrees/2026-10-13_full-volume-run diff "$(git -C .worktrees/2026-10-13_full-volume-run merge-base main HEAD)" -- products/tracker17/tests/integration/test_timed_run.py
```

Pass: the first two commands produce no output; reading the baseline and diff meets the old-test criterion. These checks end with the change.

After the complete code is present at the commit under test, use a fresh clone. The commands below run in a terminal with loopback socket permission. Request approval before commands writing protected metadata; this includes checkout in the new clone. Every failed command is a failed gate, not a reason to continue through this block.

```sh
set -e
review_copy=$(mktemp -d /private/tmp/tracker17-full-volume-review.XXXXXX)
tested_sha=$(git -C .worktrees/2026-10-13_full-volume-run rev-parse HEAD)
git clone --quiet --no-hardlinks .worktrees/2026-10-13_full-volume-run "$review_copy/repo"
git -C "$review_copy/repo" checkout --quiet "$tested_sha"
python3 -m venv "$review_copy/venv"
"$review_copy/venv/bin/python" -m pip install -r "$review_copy/repo/products/tracker17/tests/requirements.txt"
. "$review_copy/venv/bin/activate"
(
  cd "$review_copy/repo/products/tracker17"
  python3 tests/timed_run.py
  ruff format --check .
  ruff check .
)
(
  cd "$review_copy/repo"
  pytest products/tracker17/tests/
)
```

Pass: the real-clock run, both locked Ruff gates and the exact card suite command all exit 0, and each review deliverable holds. Record the checked SHA, tool versions, command results and one verdict per deliverable in Developer Review Notes. A measured duration at or over 1.0 is a failing result; CP-292 forbids changing runtime code to make it pass (`change_spec.md:L95-L95`, CP-292).
