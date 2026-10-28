# Tech Lead instruction — delete-a-task: delete a task from its page

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every product path below is relative to it.
**Scope:** Scaffold CP-529–CP-545: confirmed task and comment deletion, retired identities, stale-submission refusals and the full-volume timed deletion.

This instruction owns the implementation tasks and their verification for
`tracker17 · tobiishi · 2026-10-28_delete-a-task`.
Its inputs are the sibling `change_spec.md` § Rules and `change_design.md` §§ 2–5.
The four tasks retain the design's A → B → C → D order.

## Project layout

```text
products/tracker17/
  domain/
    __init__.py                           ← modified: deletion re-export
    tasks.py                              ← modified: rule and Tasks trace
  application/
    tracker.py                            ← modified: deletion action
  web/
    pages.py                              ← modified: deletion values and rendering
    routes.py                             ← modified: requests, outcomes and response policy
  tests/
    unit/
      test_tasks.py                       ← modified: domain deletion
    integration/
      test_task_tracker.py                ← modified: application deletion
      test_saved_data.py                  ← modified: real-file cascade and restart
      test_delete_pages.py                ← new: deletion rendering
      test_delete_routes.py               ← new: deletion requests and stale targets
      test_task_pages.py                  ← modified: Gap 12's two form assertions
      test_comment_pages.py               ← modified: Gap 12's task-level deletion exclusion
      test_routes.py                      ← modified: route inventory and outbound audit
      test_timed_run.py                   ← modified: deletion timing and whole-run streams
    e2e/
      test_delete_task.py                 ← new: keyboard, double press and history
    timed_run.py                          ← modified: full-volume deletion measurement
```

Create only the three new test modules; their directories already exist
(`git -C products/tracker17 ls-files`, listing `tests/integration/` and `tests/e2e/`).
No new package or `__init__.py` is needed.
Placement follows `docs/SDD.md` § 3, “The parts”, and `docs/nfdr.md` § 1.2, QC-13–QC-19:
the rule belongs in domain, saving in application, and requests and presentation in web.
Persistence, the saving contract, main, errors, the stylesheet and dependency pins have no task
(`change_design.md` § 2, “Blast Radius”).

## TL Review Notes

The following are the Tech Lead's decisions of 2026-10-28.

- **Type tightened:** make the closed deletion mode an enum in `web/pages.py`, carried by
  `DeleteArea`, with ordinary, confirmation, backed-out and failed values. The design's § 3 C
  closes the vocabulary but names no type; an enum makes that constraint explicit without adding
  a module or changing an address.
- **Trace staged with its subjects:** Task 1 adds FR-17 and the rule's existing test paths to
  `domain/tasks.py`'s opening docstring. Task 3 adds the three new deletion test paths after those
  files exist. The pointer test checks that named paths exist
  (`tests/architecture/test_trace.py`, `missing_paths`); listing Task 3's files during Task 1
  would break the intermediate gate. No broader entry-docstring rewrite is included.
- **Coverage strengthened:** Task 2 explicitly checks that deletion reads no clock. Task 3 adds
  request-level confirmation after an intervening title edit, ignores submitted title/project
  metadata, and tests deletion precedence when a conflicting move marker names a missing task.
  These are consequences of § 3 B's no-clock contract and § 3 C's current-task, fixed-target and
  precedence contracts, rather than additional product behaviour.
- **Atomic task boundaries retained:** Task 3 includes page values, routing, browser tests and the
  three released full-page assertions together. Task 4 includes the timed deletion and every
  whole-run timer stream together. These are the two no-green-point edges in design § 3.
- **Existing read logic stays with its owners:** Task 3 proves lists and Summary after genuine
  deletion without adding removal logic to their renderers. Application reads already derive
  those values from current state (`application/tracker.py`, `project_task_list`,
  `all_task_list`, `project_summary`), as design § 2 requires.
- **Verification command checked:** the project card's `pytest products/tracker17/tests/`, run
  from the instance change worktree, collected 2,090 tests and exited 1 with
  `20 failed, 2039 passed, 31 errors in 168.28s (0:02:48)`. It excludes browser tests by
  `tests/conftest.py`, `pytest_ignore_collect`, so Task 3 and Task 4 also name the explicit
  browser command. The isolated baseline command
  `pytest products/tracker17/tests/integration/test_listener.py -x -q` returned
  `1 error in 0.05s`: `socket.bind` raised
  `PermissionError: [Errno 1] Operation not permitted` before the test body. That is an observed
  execution restriction, not evidence of a product defect or a green baseline. These tasks use
  the ordinary test-first shape; no earlier deferred-red test is claimed.
- **Trace scanner left unchanged:** design T16 names `tests/architecture/test_trace.py` as the
  check. It already scans entry docstrings and test modules (`modules_under_test`,
  `missing_paths`, `unknown_requirements`), and deletion adds no feature word. Every task runs
  that check through the suite; no scanner change or new assertion is fabricated.
- **Local documentation corrections:** Task 4 updates the touched timing helper docstrings that
  call Summary the last block (`tests/timed_run.py`, `_run_move` and `_run_summary`;
  `tests/integration/test_timed_run.py`, `_run_readings`). Appending deletion otherwise makes
  those descriptions false. No record correction is owed outside the task: design § “Records
  this change makes false” carries its zero form, consistent with `docs/SDD.md` § 3 and
  `docs/nfdr.md` QC-10 and QC-63.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git -C products/tracker17 ls-files listed the product's tracked source, docs, pyproject.toml, tests, README.md and .gitignore; no build-service, runner or workflow configuration. The instance-level check git ls-files .github .gitlab-ci.yml Jenkinsfile .circleci azure-pipelines.yml bitbucket-pipelines.yml Makefile .buildkite returned no paths."
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

Language resolution: Python, step 1, the project card's `Languages:` field;
`<CORE>/doctrine/engineering/languages/python/README.md` opened.
The product's decision evidence is `docs/adr/` ADR-0001–ADR-0011,
`docs/nfdr.md` § 8 and `docs/SDD.md` § 3; none records a gate override or amd64 requirement.
No CI version supplies an image tag; the supported runtime floor in `pyproject.toml` is not a CI tag.

### Task 1: Remove a task through the domain (`domain/tasks.py`, `domain/__init__.py`)

**Dependencies:** None

**What to build:** The domain's additive `delete_task` interface from design § 3 A: take the current
`TrackerState` and task identity and return a new `TrackerState` with the exact removed `Task`.
Reuse `TaskNotFound` for an absent target. Removal includes the task's nested comments and preserves
every other state value, both counters and survivor order. Export the function through the existing
domain package. Update this task's requirement trace without pointing at tests created later.

#### Behaviours to verify (developer adds tests to `tests/unit/test_tasks.py`)

- `test_delete_task_accepts_every_saved_status` — cover todo, in-progress, done and cancelled,
  each with no comments and with several comments; only the selected task disappears
  (CP-529, CP-533; design T1).
- `test_delete_task_returns_the_current_removed_task` — return the full task actually held in
  the supplied state, including its title, project and comments (design § 3 A).
- `test_delete_task_keeps_the_input_and_survivors_unchanged` — the input remains intact and the
  result is a new state; survivor values/order, other projects, assignees and operator name are
  unchanged, including a state whose stored task order differs from identity order (CP-533).
- `test_delete_task_preserves_both_identity_counters` — deleting a highest, middle or last
  identity never lowers or recomputes either counter (CP-539; ADR-0008 § Decision).
- `test_delete_task_refuses_an_absent_identity` — an unheld identity raises `TaskNotFound`,
  including an empty task collection; the original state remains unchanged (design T1).

#### Implement

Infer from failing tests.

#### Verification gate

From the instance change worktree: `pytest products/tracker17/tests/`.
From the product root: `python3 -m compileall -q domain`.
Pass: the new domain tests and existing suite pass, including the import, immutability and pointer
checks; compile exits 0. The Tasks trace names only files present at this task.

### Task 2: Save deletion before publishing it (`application/tracker.py`)

**Dependencies:** Task 1 — its public domain deletion interface.

**What to build:** `Tracker.delete_task(task_id)` from design § 3 B. Delegate the rule to domain,
save the complete candidate state through the existing saver seam and publish only after the save
succeeds. Return the removed `Task` after success. Carry real-file cascade/restart coverage in
`tests/integration/test_saved_data.py` without changing persistence or its saved format.

#### Behaviours to verify (developer adds tests to `tests/integration/test_task_tracker.py` and `tests/integration/test_saved_data.py`)

- `test_delete_task_saves_once_before_publishing` — a recording saver receives the exact
  candidate once while public reads still expose the old task, comments, lists and Summary;
  after success those reads expose deletion and the return is the removed task (CP-533; T2).
- `test_delete_task_returns_metadata_from_the_current_task` — edit a title through Tracker
  before deletion; deletion returns the edited title and current owning project (CP-534; T2).
- `test_missing_delete_calls_no_saver` — `TaskNotFound` propagates with no save or publication
  and unchanged reads (T2).
- `test_failed_delete_preserves_every_application_read` — a saver failure propagates after
  one attempted save; the task, its comments, both lists, Summary and all other read values
  remain as before (CP-536; T2).
- `test_deletion_needs_no_clock_read` — successful, refused and failed deletions do not ask the
  injected clock for an instant; exclude any deliberate list/Summary read from that count
  (design § 3 B, no clock read).
- `test_highest_deleted_identity_stays_retired_after_restart` — save a populated real-file
  fixture, delete its highest task, and independently reload the full state. Only that task
  and its comments are absent. Construct a fresh Tracker from that saved state and add a task;
  the new identity exceeds every identity issued before deletion (CP-539, CP-542; T3).
- `test_last_task_deletion_reloads_as_empty_without_resetting_identity` — remove the only task
  with comments, reload the empty collection, then add a task after a restart; retain the
  project, operator, assignees and counters, and never reuse the deleted identity (T3).

#### Implement

Infer from failing tests.

#### Verification gate

From the instance change worktree: `pytest products/tracker17/tests/`.
From the product root: `python3 -m compileall -q application`.
Pass: application and real-file tests pass with every existing test, compile exits 0, and the
import graph remains intact. State readback compares the complete expected state, including
survivor comments and counters, rather than only a reduced task count.

### Task 3: Confirm deletion and show its outcome (`web/pages.py`, `web/routes.py`, `domain/tasks.py`)

**Dependencies:** Task 2 — the saved deletion action and returned removed task.

**What to build:** The request and page contracts of design § 3 C, with an enum-backed `DeleteArea`
and neutral defaults on existing page entry points. Add two `SUBMISSION` routes:
`POST /tasks/{id}/delete` opens `/tasks/{id}?delete_confirm` without saving;
`POST /tasks/{id}/delete/confirm` performs the saved action once and lands at
`/projects/{project_id}?deleted_task={encoded current title}` without a filter, sort or fragment.
Back out is a GET to the task address with `delete_back`; unexpected failure redirects to that
address with `delete_failed`. Use the existing confirmation strip, address builder, escape function,
guarded failure site and typed missing-task path. Add the three new test modules in the layout,
extend the route audit, and revise only the old clauses released by spec Locked Answer Gap 12.
Complete the Tasks entry docstring's trace to the new collaborating test files.

#### Behaviours to verify (developer adds tests to `tests/integration/test_delete_pages.py`, `tests/integration/test_delete_routes.py` and `tests/e2e/test_delete_task.py`, and updates the existing route/page tests named below)

- `test_delete_control_is_task_level_in_every_status` — each status shows the separate control
  after task content, outside all other forms and written comments; neither project nor All
  tasks rows offer deletion (CP-529; T4).
- `test_delete_first_press_opens_confirmation_without_saving` — 303 to the pending address,
  followed by the strip replacing the trigger in its spot. Its sentence, confirm and Back out
  appear in that order, with the current saved title, one sentence autofocus and unchanged
  saved bytes; the deletion action is not called (CP-530–CP-531; T4).
- `test_back_out_restores_the_trigger_without_an_outcome` — Back out restores and focuses the
  trigger, with no completion or failure line and unchanged saved bytes (CP-532; T4).
- `test_confirmed_delete_lands_on_its_unfiltered_project` — one save removes precisely the
  task/comments, preserves both counters and all other state, and redirects to the owning
  project's Tasks view with one completion line. Heading focus has that line as its accessible
  description, no fragment is present, and the page opens at its start (CP-533–CP-534; T6).
- `test_confirmation_uses_the_title_current_at_each_request` — edit between first press and
  confirmation GET, then again before confirm POST; the sentence uses the GET's current title
  and completion uses the task returned by the POST. Submitted title/project/status values
  cannot choose the target or the success metadata (CP-530, CP-534; design § 3 C).
- `test_last_task_delete_keeps_the_first_task_invitation` — the empty owning project keeps its
  existing no-tasks invitation alongside the completion (CP-534, CP-537; T6).
- `test_delete_completion_reads_never_repeat_the_action` — repeated GETs of the successful
  landing retain the same line with no additional saves and identical saved bytes (T6).
- `test_deletion_disappears_from_every_list_and_summary_count` — after genuine confirmed
  deletion, assert the project's list, All tasks, their filtered/sorted results and every
  Summary group. Cover every status/priority, overdue/undated targets, listed/unlisted/none
  assignees, retained tasks in both projects and zero counts after the last deletion.
  Each read preserves saved bytes; survivor order and ordinary row controls stay correct
  (CP-537; T7).
- `test_deletion_titles_are_text_in_every_outcome` — titles containing `<`, `&`, double/single
  quotes and non-ASCII characters survive query encoding and show exactly as text in sentence,
  completion and failure. No typed markup becomes an element (CP-535; T8).
- `test_failed_confirm_keeps_saved_bytes_and_current_pages` — fail a real-file saver before
  replacement. Assert unchanged file bytes, full state, task/comments on reads and lists;
  console output names task deletion and the error. The redirect carries the failure marker
  alone, and the task page has one failure line describing the focused restored trigger,
  no completion and no Python error/traceback in the address or page (CP-536; T9).
- `test_deleted_target_refuses_edit_without_saving` — a genuine confirmed deletion precedes
  a stale edit; expect 303 to the task address then 404 with the existing task-not-found
  heading, no additional save and identical saved bytes (CP-540–CP-541; T10).
- `test_deleted_target_refuses_label_add_without_saving` — the same independent layer-3
  deleted-target assertion for label add (CP-540–CP-541; T10).
- `test_deleted_target_refuses_label_remove_without_saving` — the same independent assertion
  for label removal (CP-540–CP-541; T10).
- `test_deleted_target_refuses_comment_add_without_saving` — the same independent assertion
  for comment add (CP-540–CP-541; T10).
- `test_deleted_target_refuses_each_ordinary_move_without_saving` — separate cases for every
  permitted ordinary target from the task's former status (CP-540–CP-541; T10).
- `test_deleted_target_refuses_cancellation_first_press_without_saving` — the same independent
  assertion for cancellation's opening POST (CP-540–CP-541; T10).
- `test_deleted_target_refuses_cancellation_confirm_without_saving` — the same independent
  assertion for cancellation's confirming POST (CP-540–CP-541; T10).
- `test_deleted_target_refuses_delete_first_press_without_saving` — the same independent
  assertion for stale/repeated deletion opening (CP-540–CP-541; T10).
- `test_deleted_target_refuses_delete_confirm_without_saving` — the same independent assertion
  for stale/repeated deletion confirmation (CP-540–CP-541; T10). In each refusal case use a
  complete request whose payload would otherwise be valid, snapshot saved bytes after the
  real deletion and compare after both refusal and not-found GET; no fake empty-target setup.
- `test_missing_task_wins_over_every_query` — deleted-task GETs without a query, with either
  confirmation, delete back-out/failure, mixed markers or unknown keys all return the existing
  404 with no `no-store` (CP-538; T11).
- `test_live_delete_views_have_their_response_policy` — confirmation, back-out, failure and
  successful project landing are 200 with `Cache-Control: no-store`. Neither POST bypasses
  existing Host/origin checks; test refused marks and unchanged bytes. No deletion response
  carries `Clear-Site-Data`; existing move-only 202/history tests retain their assertions (T11).
- `test_delete_outcome_resolves_one_focus_before_other_regions` — failure beats confirmation,
  which beats back-out. Any active deletion state suppresses move/comment/label/edit outcomes
  and autofocus, even a conflicting move reference to a missing task. With no deletion state,
  prior precedence holds. Project completion beats other outcomes/interactions (T12).
- `test_delete_confirmation_is_keyboard_operable` — browser-only proof: open by keyboard,
  sentence visibly focused, first Tab to confirm and second to Back out; keyboard Back out
  restores the trigger, and keyboard confirm focuses the project heading (CP-531–CP-534; T5).
- `test_double_press_never_confirms_deletion` — actual pointer double-click at the original
  trigger coordinates opens confirmation without deletion on short and scrolled pages; check
  sentence focus/visibility, untouched bytes and trigger-sized strip placement (T5).
- `test_completion_survives_actual_reload_back_and_forward` — confirm, reload, navigate away,
  then use actual browser Back/Forward; retain the same completion line with unchanged bytes.
  Use the existing history-enabled browser fixture for traversal. This asserts the completed
  address, not pending-delete restoration after deletion (CP-534; T5; spec Gap 6).
- Existing `test_task_page_shows_the_four_fields_in_the_one_authorized_form`,
  `test_task_page_opens_edit_form_from_saved_values` and
  `test_written_comments_offer_no_edit_delete_or_reply_control` — admit the separate delete
  form and remove only the whole-page delete-word prohibition. Retain edit fields, old form
  order, no overdue text, comment items without controls, and absence of reply/edit-comment
  text (`test_task_pages.py`, `test_comment_pages.py`; T13).
- Existing `test_every_route_leaves_state_and_headers_as_the_rules_say` — samples exactly
  cover the enlarged `ROUTES` set; opening deletion saves zero, confirm saves once, every old
  sample still saves once. All POST samples redirect; GETs save nothing. Check the first
  press's landing separately as 200 and preserve policy/no-cookie assertions. The no-outbound
  audit drives both delete presses and landing within its audit window (CP-544; T14).
- Existing pointer test — new modules name their actual SRS requirements, including FR-15,
  FR-17, FR-39, NFR-3 and AC-12 where applicable; the Tasks opening docstring includes FR-17,
  its collaborating application/web files and all three new deletion test modules
  (CP-545; T16).

#### Held by review

- Reuse the existing `confirm_strip` rather than recreate confirmation markup; retain its
  public contract and existing styling (`change_design.md` § 3 C).
- Requests and wording stay in web, the deletion rule in domain and save orchestration in
  application; use the existing typed refusal and single `_guarded` catch site. Tests prove
  the outcomes; reading the diff proves those mechanisms have one owner (QC-5, QC-20–QC-23).
- Published strings come verbatim from sibling `change_text.md` when present, as required by
  the cross-role implementation contract. This task supplies no alternative copy.

#### Implement

Infer from failing tests.

# Hint:
Reuse the action-neutral `confirm_strip` with plain text and two `StripForm` values; route outcomes
through `_address` and `_guarded`. Resolve one presentation outcome before building page regions
so only its focus target survives.

#### Verification gate

From the instance change worktree:

- `pytest products/tracker17/tests/`
- `pytest products/tracker17/tests/e2e/`

From the product root:

- `python3 -m compileall -q domain application web tests`
- `ruff format --check .`
- `ruff check .`
- `mypy main.py errors.py domain application persistence web`

Pass: all commands exit 0, all nine deleted-target refusal families assert unchanged saved bytes,
the browser exercises actual input/history and every held-by-review criterion holds. The route
inventory, outbound audit, existing move history and pointer checks pass. Keep all existing
assertions except the exact clauses released by spec Gap 12 and design T13–T14.

### Task 4: Measure deletion at full volume (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** Task 3 — the confirming route and project landing contract.

**What to build:** Append one deletion block after Summary in the timed run, with a fresh real-file
fixture of 1,000 tasks and 20 comments per task. Report its ordinary text lengths. Open the
confirmation outside timing; measure confirming POST, project landing GET and their total, each
strictly below one second. Include its verdict in the whole-run result. Extend the harness tests,
all whole-run reading streams and the descriptions of block order together (design § 3 D and T15).

#### Behaviours to verify (developer adds tests to `tests/integration/test_timed_run.py`)

- `test_full_volume_deletion_measures_post_landing_and_total` — report the fixture's volume
  and actual text lengths, then three measurements for the confirming action, in order;
  each under-limit result passes, and the whole run exits 0 (CP-543; T15).
- `test_delete_fixture_and_oracle_work_are_outside_the_intervals` — fixture setup, opening
  confirmation, constructing the independent expected full state and saved readback are
  outside the two timed requests; total is their sum, without the gap (design § 3 D).
- `test_timed_delete_is_same_origin_and_a_real_change` — mark the confirming POST
  `same-origin`, assert its correct project redirect and completion, and reload exactly the
  fixture minus the target and its comments with every other value/counter unchanged (T15).
- `test_delete_time_limits_are_strict` — check POST, landing and total separately: just below
  one second passes; equality and greater fail, including two individually passing intervals
  whose sum reaches the limit (CP-543; T15).
- `test_timed_delete_rejects_wrong_saved_results` — independent mutation probes reject no
  deletion, retained comments, another task removed, another task field/comment altered,
  project/assignee/operator data changed, or either counter changed. The oracle never calls
  the production deletion rule to derive its expected result (T15).
- `test_timed_delete_rejects_refusal_failure_or_wrong_landing` — refuse or fail the action,
  return a wrong redirect/project/title, wrong landing status or omit completion; each fails
  the deletion and whole run. Unexpected failure is not a passing duration (T15).
- `test_whole_run_keeps_earlier_blocks_and_appends_deletion` — extend `_run_readings` and
  every fixed whole-run stream; Summary immediately precedes deletion, every earlier action
  keeps its order, labels, thresholds and success/failure verdict, and the run's return value
  includes deletion. Retire only the “Summary is last” assertion (spec Gap 12; T15).
- Existing pointer test — touched/new test descriptions name the SRS requirements they prove,
  and touched timing helper docstrings describe deletion after Summary (CP-545; T16).

#### Held by review

- Ordinary text lengths and the independent expected complete state are visible in the
  fixture/oracle code; no production rule is used as its own success oracle (design § 3 D).

#### Implement

Infer from failing tests.

# Hint:
Use an isolated fixture and an independent expected full state. Place fixture setup and state
readback outside the two request intervals; extend both whole-run timer sources and rejection
probes.

#### Verification gate

From the instance change worktree:

- `pytest products/tracker17/tests/`
- `pytest products/tracker17/tests/e2e/`
- `python3 products/tracker17/tests/timed_run.py`

From the product root:

- `python3 -m compileall -q main.py errors.py domain application persistence web tests`
- `ruff format --check .`
- `ruff check .`
- `mypy main.py errors.py domain application persistence web`

Pass: every command exits 0; the actual timed run on the owner's machine reports deletion after
Summary with POST, landing and total each strictly under one second. Every earlier timed action
also passes. Synthetic timer tests prove boundaries and failures, and do not substitute for the
real measurement (CP-543; `docs/nfdr.md` QC-48).
