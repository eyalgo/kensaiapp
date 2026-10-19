# Tech Lead instruction — add-and-list-tasks: save tasks and show a project's ordered list

**Date:** 2026-10-11
**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every product path below is relative to it.
**Scope:** Task creation, persistence, the project form/list and a read-only task page, with domain, request-path, browser and timed checks.

This document owns the task cut, task lanes and verification gates for
`tracker17 · tobiishi · 2026-10-11_add-and-list-tasks`.
The adjacent `change_spec.md` § Rules, CP-106–CP-143 (L26-L87), owns the required behaviour;
`change_design.md` §§ 2–4 (L18-L125) owns the structure and interface contracts.
The output's home is the active change folder, per
`core/doctrine/setup/kensaiapp_structure.md` § 2, `journey/tobiishi/<key>/`.

---

## Project layout

```text
<Product root>/
  domain/
    __init__.py                         ← modified; public re-exports only
    state.py                            ← modified
    refusals.py                         ← modified
    tasks.py                            ← new
    priorities.py                       ← new
    due_dates.py                        ← new
  application/
    __init__.py                         ← modified; public re-exports only
    tracker.py                          ← modified
  persistence/
    saved_data.py                       ← modified
  web/
    routes.py                           ← modified
    pages.py                            ← modified
    style.css                           ← modified only as rendering needs
  tests/
    unit/
      test_state.py                     ← modified
      test_tasks.py                     ← new
      test_priorities.py                ← new
      test_due_dates.py                 ← new
    integration/
      test_saved_data.py                ← modified
      test_start.py                     ← modified
      test_pages.py                     ← modified
      test_routes.py                    ← modified
      test_task_tracker.py              ← new
      test_task_pages.py                ← new
      test_task_routes.py               ← new
      test_timed_run.py                 ← new
    architecture/
      test_trace.py                     ← modified
    e2e/
      test_first_project.py             ← modified
      test_tasks.py                     ← new
    timed_run.py                        ← modified
```

Use the existing directories; no new package or `__init__.py` is needed.
Placement follows `docs/SDD.md` § 3, The parts (L198-L231), and the complete parts/import set
is `docs/nfdr.md` § 1.2, QC-13–QC-19 (L129-L153).
Keep task values/rules in domain, state publication and clock conversion in application,
file representation in persistence, and transport/rendering in web.
Keep the existing `main.py`, `errors.py`, `application/contracts.py` and listener contracts.
These boundaries follow `change_design.md` § 2 (L24-L29) and § 3 (L44-L103).

## TL Review Notes

Decisions by tech-lead, 2026-10-11:

- **Task cut:** distribute § 3 E's tests into the tasks whose contracts they prove, with the
  timed harness as Task 5. This keeps A with trace registration, B with saved-shape assertions,
  and D with page/browser/route-inventory assertions; the design declares no green point between
  those pairs (`change_design.md` § 3, Atomic-landing edges, L113).
- **Trace timing:** name only existing checking test files in entry docstrings at each task's
  gate; Tasks 2–5 extend those pointers as their test files arrive. A docstring naming a later
  task's absent test file fails the existing pointer check, so the final complete trace must grow
  with the tests (`tests/architecture/test_trace.py` § `missing_paths`, L45-L46, and
  `test_every_path_named_in_the_entry_docstring_exists`, L96-L101;
  `change_spec.md` § The code and its trace, CP-138, L76).
- **Type precision:** use enums for the closed task-outcome codes and the field selected by a
  refusal, in `web/pages.py`, and an immutable form/outcome value. The design names a web-only
  outcome/form value but leaves its type unspecified; typing it avoids free-form code comparisons
  while preserving the stateless outcome contract (`change_design.md` § 3 D, L85-L99).
- **Coverage added:** Task 1 tests Unicode whitespace and code-point title boundaries; Task 4
  tests CR LF/lone CR normalization, strict UTF-8 rejection, and preservation of handed-in row
  order. These sharpen the shared-text and layer boundaries without adding a product rule
  (`docs/adr/0007-text-counted-once-in-domain-in-code-points.md` § Decision;
  `docs/nfdr.md` QC-9, L85-L93; `change_design.md` § 3 D, L85-L101).
- **Timed harness coverage:** add `tests/integration/test_timed_run.py` to prove that the harness
  reports and actually exercises the task-volume case, and rejects a refused/failed add, a bad
  landing, and either duration at or above one second. A script exiting 0 alone can time the
  wrong path; the design requires actual saved state and landing content, and a strict bound
  (`change_design.md` § 5 T10, L144; `change_spec.md` CP-143, L87).
- **Ordering without a false dependency:** Task 3 follows Task 2 so the saved representation is
  addressed first, but depends only on Task 1. Its tests use an injected Saver and Clock; it
  consumes no persistence contract (`change_design.md` § 3 C, L73-L77).
- **Baseline and gate scope:** running the card's exact command from the change worktree,
  `pytest products/tracker17/tests/`, collected 356 tests. The sandboxed run returned
  `5 failed, 335 passed, 16 errors`, with socket binding reporting
  `PermissionError: [Errno 1] Operation not permitted`. The approved run returned
  `356 passed in 11.81s`, exit 0. No task takes the red-at-baseline lane. Keep the card command;
  run the separate browser suite as well, because the collection rule excludes it
  (`tests/conftest.py` § `pytest_ignore_collect`, L42-L48).
- **Verification prerequisites:** the baseline used Python 3.14.7 and pytest 9.0.3, as the
  actual pytest header reported. The command
  `python3 -c 'import importlib.util; print({name: importlib.util.find_spec(name) is not None for name in ("pytest", "playwright", "ruff", "mypy")})'`
  returned `{'pytest': True, 'playwright': False, 'ruff': False, 'mypy': False}`.
  This is a baseline measurement, not a browser/quality verdict. The implementation gates require
  the product's pinned test environment and browser; keep the pins and configuration
  (`pyproject.toml` § dependency-groups, L11-L17; `docs/nfdr.md` QC-39 and QC-62).

## Corrections owed while there

- Owed outside this change's reach: `tracker17 · shukuba · 2026-10-11_add-and-list-tasks`
  § Guardrail, “the 1,000-task timed run (item 5, `timed-run`)” — the exclusion contradicts this
  change's owner-authorized CP-143 → the station includes the add/landing timed case at 1,000
  tasks; the remaining timed-run work keeps its own scope (`change_spec.md` § Locked Answers,
  Gap 14, L185, and CP-143, L87). No code task opens the station record.

### Task 1: Pure task state and rules (`domain/tasks.py`, `domain/priorities.py`, `domain/due_dates.py`, `domain/state.py`, `domain/refusals.py`, `domain/__init__.py`, `tests/architecture/test_trace.py`)

**Dependencies:** None

**What to build:** The immutable task state and all pure rules for creating, restoring, finding,
ordering and assessing tasks, together with the feature trace registration.
Use the contracts in `change_design.md` § 3 A (L44-L53): Task's ten fields; immutable Comment
values and ordered label/comment tuples; `TaskStatus` and `Priority` string-valued enums;
`PRIORITY_CHOICES`; task counter/defaults on `TrackerState`; `add_task`, `restore_task`,
`find_task`, `list_project_tasks`; calendar-date validation and `is_overdue`.
Extend `restore_state` with keyword-only tasks/counter while preserving the first three arguments.
Keep `TextField.TITLE` and typed task refusals in `refusals.py`, derived from the existing base.
Domain owns every value/invariant decision and reads no clock or file.
Update the state/refusal docstrings for both identity kinds.
Entry docstrings name their SRS requirements, participating existing application/web paths and
the tests present at this gate; register `tasks`, `priorities`, `due_dates` as landed.

#### Behaviours to verify

Add tests in `tests/unit/test_tasks.py`, `test_priorities.py`, `test_due_dates.py`, and extend
`tests/unit/test_state.py`; retain the existing architecture assertions.

- `test_add_task_saves_all_values_and_leaves_original_state_unchanged` — exact title/assignee,
  project, priority, calendar date and aware UTC creation instant; todo, empty labels/comments.
- `test_title_only_add_uses_defaults` — absent/empty optional strings yield medium, unassigned
  and undated; all four nonempty priorities are accepted and choices retain their specified order.
- `test_task_title_is_exact_and_need_not_be_unique` — surrounding spaces and duplicate titles
  survive; duplicate titles still get different global identities across projects.
- `test_title_bounds_count_code_points` — 200 accepted, 201 refused with TITLE/maximum;
  include non-BMP characters, empty text and Unicode-whitespace-only text.
- `test_refusal_precedence_consumes_no_identity` — project existence, title length, title
  blankness, priority, current assignee, due date in design order; 201 spaces gets too-long.
  Every refusal leaves all original state/counters unchanged.
- `test_new_assignment_requires_current_exact_listed_name` — off-list/case-changed name refused
  with its submitted name; none accepted; exact names with surrounding spaces retained.
- `test_calendar_date_requires_exact_valid_iso_date` — valid leap day accepted; bad leap day,
  impossible day, compact/week date, timestamp, padding and malformed strings refused;
  form empty means none, saved empty is invalid.
- `test_task_restoration_accepts_all_statuses_and_historical_assignee` — all four statuses,
  all four priorities, optional values, off-list exact valid assignee, labels/comments preserved.
- `test_task_restoration_refuses_each_invalid_value` — each CP-137 title, assignee,
  priority, status and date break individually refused; saved priority receives no default.
- `test_state_restoration_checks_task_identity_and_project_invariants` — positive task IDs and
  counter, duplicate IDs, missing projects and IDs equal to/above the counter; refuse the whole
  state and preserve legacy positional restoration. Boolean wire types belong to Task 2.
- `test_list_project_tasks_orders_explicitly_by_date_then_identity` — shuffled storage, equal
  instants and reversed timestamps; dated first, ascending date, ascending ID for ties and
  undated rows; no other project's tasks; empty/all-undated lists.
- `test_overdue_matrix` — each of four statuses against yesterday/today/tomorrow/no date;
  only open statuses before the supplied today are overdue, with no clock read.
- `test_other_domain_changes_keep_tasks_and_counter` — project creation and People add/remove
  preserve every task/counter, including the assignee stored on a task after removal.
- `test_task_values_are_immutable` — Task, Comment, state and their containers cannot be mutated.
- Existing trace checks — landed words, real checking-file pointers and valid requirement IDs;
  no `domain/labels.py` or new top-level part.

#### Implement

Infer from failing tests.

# Hint:
Explicit due-date/identity sort key; shared value checks for creation and restoration, with
current assignee membership required only for a new add. Keep the state/type cycle out of runtime imports.

#### Verification gate

From `.worktrees/2026-10-11_add-and-list-tasks`:
`pytest products/tracker17/tests/`.
From Product root: `ruff format --check .`, `ruff check .`,
`mypy main.py errors.py domain application persistence web` and
`python3 -m compileall -q domain application persistence web main.py errors.py`.
Pass: all commands exit 0; new pure-rule tests and the full existing suite pass;
trace pointers resolve without naming a checking test file that has not been created.

### Task 2: Whole-state task codec and legacy reads (`persistence/saved_data.py`, `domain/tasks.py`, `domain/priorities.py`, `domain/due_dates.py`, `tests/integration/test_saved_data.py`, `tests/integration/test_start.py`)

**Dependencies:** Task 1

**What to build:** The additive five-key saved representation and all-or-nothing restoration,
per `change_design.md` § 3 B (L61-L65), retaining atomic save and the People encoding.
Every task uses exactly its ten fields; comments use text/author/created_at; enums are strings,
optionals null, due dates calendar ISO, instants UTC ISO, labels/comments arrays.
Recognize exactly the two complete legacy forms and the complete new form.
Persistence checks wire shape/types and decodes instants; domain checks content/invariants.
Update the codec docstring and the applicable domain entry docstrings' checking-file pointers.
Replace the old exact-three-key expectations while retaining every project/People clause,
as `change_design.md` § 5, Assertions retired and clauses re-proved (L153) requires.

#### Behaviours to verify

- `test_tasks_and_counter_round_trip_every_field` — two projects, all statuses/priorities,
  none/present assignee/date, exact whitespace, UTC instants and ordered labels/comments;
  newly added tasks have no labels/comments; People keeps exact saved order and representation.
- `test_restart_keeps_task_identities_fields_and_list_order` — restore, read and add again;
  no reused address, same due/identity order and next counter.
- `test_both_legacy_forms_load_without_rewriting` — project-only and project/People files keep
  exact bytes, restore empty tasks/counter 1, and acquire all five keys only on successful save.
- `test_first_project_or_people_save_writes_full_shape` — retain existing value/counter/order
  assertions, and require empty tasks/counter as appropriate after each legacy path.
- `test_partial_extra_or_malformed_task_shape_is_unreadable` — missing/extra top-level/task/comment
  keys, wrong arrays/objects/primitives, boolean/non-integer IDs/counters, undecodable or non-aware
  timestamps; name the location and keep exact bytes, with no partial state.
- `test_each_task_rule_break_is_unreadable_at_start` — one fixture for each CP-137 break and
  positive-ID/counter invariant; include equal/greater-than-counter identities, duplicate IDs,
  unknown project/status/priority, Unicode-blank and overlong title/assignee and bad dates.
- `test_historical_assignee_and_structural_label_comment_values_load` — off-list assignee
  remains readable; no deferred label/comment content rules are introduced.
- `test_task_save_failure_preserves_original_file` — failed and interrupted atomic save with
  nonempty tasks/counter leaves a complete before/after file, never a mixture; a failed save keeps
  the prior bytes. Retain existing unreadable-data/no-action and single-tracker-lock tests.

#### Implement

Infer from failing tests.

# Hint:
Recognize complete key sets, then shape-decode and delegate data validity; preserve the existing
atomic full-file save.

#### Verification gate

From `.worktrees/2026-10-11_add-and-list-tasks`:
`pytest products/tracker17/tests/`.
From Product root: `ruff format --check .`, `ruff check .`,
`mypy main.py errors.py domain application persistence web` and
`python3 -m compileall -q domain application persistence web main.py errors.py`.
Pass: each exits 0; round-trip/legacy/start/failure tests and every existing test pass;
trace checking-file pointers added here exist.

### Task 3: Save-before-publication and local-date projection (`application/tracker.py`, `application/__init__.py`, `domain/tasks.py`, `domain/priorities.py`, `domain/due_dates.py`, `tests/integration/test_task_tracker.py`)

**Dependencies:** Task 1

**What to build:** `Tracker.add_task`, `Tracker.task` and `Tracker.project_tasks`, returning the
saved Task, optional Task and immutable `TaskRow(task, overdue)` tuple respectively, per
`change_design.md` § 3 C (L73-L77).
Application orchestrates the domain calls and existing Saver/Clock; it performs no rule or codec.
Re-export the task values, choices, bound and typed refusals that web needs.
Extend domain checking-file pointers for this task's test file.

#### Behaviours to verify

- `test_add_task_saves_once_before_publishing` — recording Saver sees the candidate full state
  while the Tracker still exposes its original state; return the saved Task after successful save.
- `test_refused_task_add_never_calls_saver` — each applicable refusal leaves all public reads
  unchanged, and no identity is consumed.
- `test_failed_save_keeps_tasks_and_counter` — injected failure propagates, old reads remain,
  and a subsequent success receives the unconsumed identity.
- `test_add_uses_current_people_list` — remove a name between page-like read and add;
  assignment refuses; earlier tasks retain that name.
- `test_project_and_people_actions_retain_tasks` — existing actions keep tasks and counter
  while each still saves its complete resulting state.
- `test_task_lookup_and_project_rows_return_complete_values` — missing ID yields none, projects
  remain isolated, rows preserve domain order and contain correct overdue flags; no read saves.
- `test_project_page_uses_one_injected_local_date` — one Clock instant per projection, machine-local
  calendar date across a UTC/local-midnight boundary; a later projection obtains a renewed date.
  Supply the clock through the constructor, patch no product name.
- `test_add_records_the_injected_creation_instant` — the new task records the one supplied aware
  UTC instant without consulting a real clock.

#### Implement

Infer from failing tests.

# Hint:
Convert one injected aware instant to machine-local today per project page, and pass it to the
domain predicate.

#### Verification gate

From `.worktrees/2026-10-11_add-and-list-tasks`:
`pytest products/tracker17/tests/`.
From Product root: `ruff format --check .`, `ruff check .`,
`mypy main.py errors.py domain application persistence web` and
`python3 -m compileall -q domain application persistence web main.py errors.py`.
Pass: each exits 0; new injected-Saver/Clock tests and all existing tests pass;
Saver/Clock and Site constructor signatures remain unchanged.

### Task 4: Task requests, pages and browser contract (`web/routes.py`, `web/pages.py`, `web/style.css`, `domain/tasks.py`, `domain/priorities.py`, `domain/due_dates.py`, `tests/integration/test_task_routes.py`, `tests/integration/test_task_pages.py`, `tests/integration/test_pages.py`, `tests/integration/test_routes.py`, `tests/e2e/test_first_project.py`, `tests/e2e/test_tasks.py`)

**Dependencies:** Tasks 2 and 3

**What to build:** The complete web feature and its request/page/browser regression coverage,
per `change_design.md` § 3 D (L83-L103).
Add `POST /projects/<digit-id>/tasks` and `GET /tasks/<digit-id>` to the existing route inventory.
Success redirects 303 to `/tasks/<id>?added`; refusals/failures redirect to the project with
task-scoped stateless outcomes. Keep the existing single address builder, request guard, request
lock, UTF-8 codec, newline normalization, escaping seam and guarded failure/logging site.
Use typed web-only outcome/form values in pages; web imports task contracts through application.
Render the persistent four-field form, empty invitation or supplied six-column task rows,
read-only task page and distinct task not-found page. Rendering decides no ordering/overdue rule.
Place the adjacent `change_text.md` strings verbatim, including console text; invent no wording.
Update domain checking-file pointers and superseded page/not-found docstrings.
Replace only the no-form/no-invitation clauses and old inventory examples that the design
identifies, retaining exact heading/description/title, focus, security and inventory coverage
(`change_design.md` § 5, L151-L156).

#### Behaviours to verify

Use real Site, Tracker and SavedData for whole-path tests, with an injected Clock and a failing
Saver where relevant; no socket for these integration cases. Use the existing browser harness
for `tests/e2e/test_tasks.py`.

- `test_form_is_present_for_empty_and_populated_projects` — four labelled fields and Add;
  shared title maxlength, low/medium/high/critical in order with medium chosen, exact People
  order after none with none chosen, only none plus People link when empty, empty native date,
  no script. Preserve the project document title and created-heading focus.
- `test_add_all_fields_and_title_only_land_on_saved_task` — 303 and correct saved fields/defaults;
  unique task addresses, duplicate/exact-space titles, quoted completion line describing the
  autofocused title heading; line never focused; plain GET has no completion line.
- `test_task_read_reload_and_history_never_save` — both landing/plain GETs and repeated reads
  leave bytes, tasks and counters identical.
- `test_blank_title_retains_all_four_fields_and_focuses_title` — empty, spaces and Unicode
  whitespace; adjacent accessible reason, old bytes/state, no new task.
- `test_too_long_title_exposes_no_submitted_fields` — 201 characters and 201 spaces give
  too-long, fresh defaults/title focus, no sent text in Location or rendered page; a crafted GET
  beside the too-long outcome also discards every submitted field.
- `test_stale_assignee_rebuilds_choices_and_retains_other_fields` — real removal after form read;
  reason names removed name, reload link, assignee focus/description, selected none, no off-list
  option, exact title/priority/date retained, data unchanged.
- `test_invalid_priority_and_date_focus_the_rejected_control` — reason and accessible relationship,
  other valid fields preserved, rejected priority reset to medium/date to empty, no save;
  include the design's mixed-invalid precedence.
- `test_failed_add_retains_form_and_reports_one_failure` — all fields retained, Add-form focus
  with tabindex/autofocus and described plain failure text; no Python text in page, action before
  error at the existing console site, original file/state/counter unchanged.
- `test_missing_project_and_numeric_task_addresses_save_nothing` — missing project POST gets
  project not-found; missing task IDs, zero and unrepresentable digit sequences get task 404;
  task not-found body offers Projects only; unrelated unknown paths keep their old page.
- `test_every_task_submission_passes_existing_origin_guard_first` — cross-site, same-site,
  none and absent mark refuse before action/save; same-origin accepts; bad Host refuses.
- `test_task_form_uses_existing_strict_utf8_and_newline_codec` — invalid raw/percent-encoded UTF-8
  gives empty 400 with no save; valid CR LF/lone CR normalize once to LF before rules apply.
- `test_project_list_shows_every_own_task_in_six_columns` — title link, status, priority,
  exact/historical assignee or unassigned, all carried labels, ISO date/undated text from content;
  no other project, no row limit/pagination, invitation only when empty, including failed-only adds.
- `test_project_order_and_overdue_survive_restart` — dated/undated and equal-date ties in identity
  order, unchanged after restore; injected yesterday/today boundary marks only overdue rows.
- `test_renderer_preserves_supplied_row_order_and_overdue_flags` — deliberately supplied rows
  differing from date/ID order still display in that order, with exactly the supplied flags.
- `test_task_page_is_read_only_and_shows_only_four_fields` — correct document title and exact
  title/priority/assignee/date, unassigned/undated content; no status/label/comment field or form,
  move/edit/delete/filter/sort/summary/label/comment controls.
- `test_every_rendered_value_is_literal_text` — titles, assignee/label values, retained form
  attributes, completion, reasons and document titles with markup characters are escaped once.
- Existing route-wide probes — extend sample/body maps with successful task fixtures; enumerate
  every route, preserve CSP/headers/no cookies/no external egress and compare tasks/counter as
  well as projects/People/saver calls. Do not weaken inventory equality or skip a route.
- `test_browser_task_title_limit_and_native_date` — ordinary typing stops at the 201st
  character; valid 200-character title saves; browser date control chooses the saved date.
- `test_browser_added_task_has_heading_focus_and_description` — keyboard-capable complete add
  produces actual heading focus and completion accessible description; the message is unfocused.
- `test_browser_task_markup_title_is_literal_on_task_and_project` — enter `<b>A&B</b> "Q"`,
  follow task to project list and task link again; exact visible text/link/document title,
  no injected bold node. Retain first-project creation/read-back/focus checks while asserting
  the new invitation and exact form.

#### Held by review

- Words come verbatim from `change_text.md` — compare every added page/control/message and console
  string with the content artifact; behavioural assertions do not establish authorship.
- One escaping seam, one failure/logging site, no pending form/session/outcome store and no
  business rule in web — read the diff against `docs/nfdr.md` QC-8/QC-23/QC-36/QC-56.

#### Implement

Infer from failing tests.

# Hint:
Use stateless POST/303/GET outcomes; the too-long outcome carries no submitted text. Rebuild
People choices on each GET.

#### Verification gate

From `.worktrees/2026-10-11_add-and-list-tasks`:
`pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/`.
From Product root: `ruff format --check .`, `ruff check .`,
`mypy main.py errors.py domain application persistence web` and
`python3 -m compileall -q domain application persistence web main.py errors.py`.
Pass: every command exits 0, both suites pass including prior browser cases, every route remains
  under the security probes, and every held-by-review criterion is satisfied.
Missing browser/test prerequisites are not a pass or permission to skip the browser suite.

### Task 5: Task-volume timed measurement (`tests/timed_run.py`, `tests/integration/test_timed_run.py`, `domain/tasks.py`)

**Dependencies:** Tasks 1, 2 and 4

**What to build:** The actual add-task and landing-page measurement at 1,000 tasks with 20
comments each, retaining existing ordinary and maximum-length project-create checks, per
`change_design.md` § 5 T10 (L144) and `change_spec.md` CP-143 (L87).
Seed real immutable domain values/restoration and SavedData in a private temporary location;
exercise real same-origin Site requests. Report volume and the actual ordinary text lengths.
Time add POST and its landing GET separately; verify the added identity/full saved state and
landing content. The measurement must not add a comment or label action to the product.
Extend the task entry docstring's checking-file pointer for the harness regression tests.

#### Behaviours to verify

Add `tests/integration/test_timed_run.py`; tests may supply request/timing collaborators through
the harness's own seams, and must not patch a name inside a product module.

- `test_timed_run_exercises_and_reports_task_volume` — real temporary-file run seeds exactly
  1,000 tasks with 20 comments each, reports volume/actual lengths and independent add/landing
  durations, verifies the new saved identity and landing title, and retains project timings.
- `test_timed_task_add_rejects_refusal_or_failure` — a refused/failed POST or a redirect without
  the actual saved new task makes the harness exit nonzero, regardless of its elapsed time.
- `test_timed_task_landing_rejects_missing_or_wrong_page` — missing/bad landing response or wrong
  task content makes the harness exit nonzero, even when the POST succeeded.
- `test_timed_task_requires_each_duration_strictly_below_limit` — below-limit add and GET pass;
  either at exactly one second or above fails independently, with a reported failed measurement.
- `test_timed_fixture_preserves_whole_state_without_touching_product_data` — original fixture
  task/comment values survive the add and real save; the harness uses its own location, never data/.

#### Implement

Infer from failing tests.

# Hint:
Seed volume through immutable domain values/restoration in a disposable location; time the real
same-origin request and its landing GET separately.

#### Verification gate

From `.worktrees/2026-10-11_add-and-list-tasks`:
`pytest products/tracker17/tests/`, `pytest products/tracker17/tests/e2e/` and
`python3 products/tracker17/tests/timed_run.py`.
From Product root: `ruff format --check .`, `ruff check .`,
`mypy main.py errors.py domain application persistence web` and
`python3 -m compileall -q domain application persistence web main.py errors.py`.
Pass: every command exits 0; the harness reports the required volume/lengths and both successful
task measurements strictly below one second; no previous test/measurement is weakened.

For CP-141's additional disposable-copy check, use these exact preparation commands:

```sh
CHECK_ROOT=$(mktemp -d /private/tmp/tracker17-add-and-list-tasks.XXXXXX)
git -C .worktrees/2026-10-11_add-and-list-tasks archive HEAD | tar -x -C "$CHECK_ROOT"
git -C "$CHECK_ROOT" init -q
```

From `$CHECK_ROOT`, run `pytest products/tracker17/tests/`,
`pytest products/tracker17/tests/e2e/` and `python3 products/tracker17/tests/timed_run.py`.
From `$CHECK_ROOT/products/tracker17`, run `ruff format --check .`, `ruff check .` and
`mypy main.py errors.py domain application persistence web` in the pinned test environment.
Pass: every command exits 0 with tests collected, both suites green and both task timings below
one second. Git initialization makes the ignore check meaningful, per `docs/nfdr.md` QC-47
(L384-L392); it does not supply missing browser or Python dependencies.
