# Tech Lead instruction — project-list-sort: sort one project's task list

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every path below is relative to it unless an explicit working directory says otherwise.
**Scope:** Implement the sibling `change_spec.md` CP-426–CP-458 through the boundaries in sibling `change_design.md` §§ 2–5, including sort retention during moves and the timed sort.

This instruction owns the implementation tasks for `tracker17 · tobiishi · 2026-10-27_project-list-sort`.
The sibling `change_spec.md` owns the requirements; the sibling `change_design.md` owns the interfaces.
The output belongs beside those artifacts under `<CORE>/doctrine/setup/kensaiapp_structure.md` § 2, `journey/tobiishi/<key>/`.

**Language resolution:** Python — `system/projects/tracker17/project.md` **Languages** answers step 1 of `<CORE>/doctrine/engineering/languages/README.md` § The resolution chain. The Python packet and all seven routed concerns were read. `docs/nfdr.md` § 8 QC-59/60 and ADR-0002 govern the product's Python 3.11 floor.

## Project layout

```text
products/tracker17/
  domain/
    __init__.py                              ← modified
    sorting.py                               ← new
  application/
    __init__.py                              ← modified
    tracker.py                               ← modified
  web/
    pages.py                                 ← modified
    routes.py                                ← modified
  tests/
    timed_run.py                             ← modified
    unit/
      test_sorting.py                         ← new
    integration/
      test_sort_tracker.py                    ← new
      test_sort_pages.py                      ← new
      test_sort_routes.py                     ← new
      test_sort_move_routes.py                ← new
      test_routes.py                          ← modified
      test_timed_run.py                       ← modified
    architecture/
      test_shapes.py                          ← modified
      test_trace.py                           ← modified
    e2e/
      test_sorting.py                         ← new
```

Create the new files in the existing directories; no new directory or package initializer is needed
(the existing paths are listed by `git ls-files products/tracker17/`). Package initializers carry
re-exports only, per `docs/nfdr.md` § 1 and `change_design.md` § 3 A/B.

Placement and allowed imports follow `docs/SDD.md` § 3 **The parts** and `docs/nfdr.md` § 1.2:
`domain` owns selection, ordering, defaults, validation and counts; `application` projects the answer;
`web` owns decoding, addresses and presentation. `domain` may reach `errors` and the standard library;
`application` and `persistence` may reach `domain` and `errors`; `web` may reach `application` and
`errors`; `main` may reach all four parts and `errors`. Reverse edges, imports of `main` or `tests`
from a part, and third-party runtime imports remain forbidden by QC-13–QC-19.

## TL Review Notes

Decisions below are the Tech Lead's, 2026-10-28.

- **Task split:** split design § 3 C into Task 3's list read/presentation and Task 4's move carrying.
  They are independently testable responsibilities: a GET sort can be complete before move forms
  carry choices. Task 4 consumes Task 3's sorted list, field rendering and request decoding.
- **Contract reconciled:** retain the design's zero-match reading of CP-435: a valid filter with no
  matches shows the existing no-match sentence and Clear without a separate numeric count.
  `tests/integration/test_filter_pages.py` **test_no_matches_keeps_choices_and_clear_without_an_empty_project_message**
  asserts that state, and `web/pages.py` **_filtered_list** builds it. The sibling
  `deferred_decisions.md` **CP-435's separate count for a valid filter with zero matches** carries the
  reading set aside. Task 1 keeps count visibility in domain; Tasks 2/3 project and present it.
- **Buildable trace:** update the new entry's checking-test pointers as Tasks 2–4 create their files.
  `tests/architecture/test_trace.py` **test_every_path_named_in_the_entry_docstring_exists** rejects
  a pointer to a future file. Task 1 names its existing unit/architecture checks and all participating
  application/web modules; each later task adds its checking paths. This realizes the final CP-446
  trace without a forward reference that breaks an intermediate gate.
- **Coverage sharpened:** add independent unset-value cases for each sort control and mixed empty/set
  controls in Tasks 1/3. CP-428 and CP-435 distinguish validated defaults from a nonempty raw choice,
  so a default value alone cannot decide count visibility.
- **Coverage sharpened:** Task 4 asserts retained sort tuples on refusal and failure redirects as
  well as success. Design T8 asks for every outcome address; equality of rendered selections alone
  would miss loss of blank or repeated values.
- **Change-only checks:** Task 6 holds the scope and old-assertion preservation checks by review
  against the branch's merge base. They describe this change and must not become permanent tests
  pinned to its base (`<CORE>/prompts/tech_lead_create_tl_instruction.md` Step 3).
- **Gate execution:** the card's command collects the intended suite; keep it in every gate.
  At `20271282cae2fcadd38328c97a080a9285610f31`, the sandboxed command
  `pytest products/tracker17/tests/` returned `20 failed, 1524 passed, 31 errors`.
  The listener probe failed at `socket.bind` with `PermissionError: [Errno 1] Operation not permitted`.
  With command approval its 20 tests passed. The approved nonterminal startup probe then timed out
  at `test_start.py` **_run_real_start**, after its SIGINT and 30-second wait.
  `python3 -c 'import signal; print(signal.getsignal(signal.SIGINT))'` reported `1` (SIG_IGN)
  without a terminal and the default interrupt handler with a terminal. Finally, the approved
  terminal command `pytest products/tracker17/tests/integration/test_label_listener.py products/tracker17/tests/integration/test_listener.py products/tracker17/tests/integration/test_people_routes.py products/tracker17/tests/integration/test_start.py -q`
  returned `151 passed in 10.49s`. Use a terminal and authorized loopback access for these gates;
  these execution restrictions do not define a red-at-baseline task or justify changing old tests.

## Corrections owed while there

- `tests/timed_run.py`, **main**, **_run_move** and **_run_filter** — their descriptions call the
  filter the final action/block. Describe the added sort as the final block, with the filter before
  it. Rides Task 5, which already opens this file (`change_design.md` § 3 D; CP-452).

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git ls-files inventoried the tracked repository and all 233 products/tracker17 paths. The repository-root files were .env.example, .gitignore, .providers.toml.example, .python-version, .telemetry.env, AGENTS.md, Brewfile, CLAUDE.md, Containerfile, README.md, kensaiapp.md, pyproject.toml and uv.lock. Product hidden configuration was only products/tracker17/.gitignore and products/tracker17/tests/e2e/.gitkeep. No CI configuration was found. Containerfile builds the interactive sandbox; .claude/workflows/eval-fix.js and run-skill-evals.js are agent workflows, not CI runner configurations."
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

### Task 1: Domain selection and ordering (`domain/sorting.py`, `domain/__init__.py`, `tests/architecture/test_trace.py`, `tests/architecture/test_shapes.py`)

**Dependencies:** None

**What to build:** Implement design § 3 A's immutable input, validated sort and combined selection
contracts. Export `SortInput`, `SortKey` (`due_date`, `priority`, `created_time`, `title`),
`SortDirection` (`ascending`, `descending`), `SortControl` (`field`, `direction`), `TaskSort`,
`SortedSelection`, `sort_project_tasks`, `ProjectListRefused`, `SortFieldRefusal`,
`InvalidSortField`, `InvalidSortDirection` and `RepeatedSortValue` through the domain facade.
The new refusal types live in `sorting.py` and derive from the existing `Refusal`.
Reuse `filter_project_tasks` without changing its signature or rules.

Keep raw field/direction tuples intact, validate both filter and sort independently, and report all
typed problems in filter-control order followed by field then direction. A repeated control gets
one repeated-value refusal instead of invalid-value refusals. Empty projects bypass validation;
zero matches in a nonempty project do not. `count_requested` is the domain result specified in
design § 3 A. Add the sorting entry docstring and the landed-feature/shape changes with the module,
preserving every other assertion as CP-456 requires.

#### Behaviours to verify

Developer adds `tests/unit/test_sorting.py` and extends the two named architecture tests (design T1–T3/T11; CP-428–CP-434, CP-441–CP-448, CP-456).

- `test_due_sort_keeps_undated_last_and_identity_ties` — both directions, equal dates, mixed dates,
  all-undated, and multiple undated tasks preserve ascending identity within ties.
- `test_priority_sort_uses_all_four_ranks_and_identity_ties` — low/medium/high/critical ascending,
  the reverse descending, with ascending-identity ties in each direction.
- `test_title_sort_casefolds_then_compares_code_points` — beta/Alpha/alpha in both directions,
  Straße/STRASSE ties, mixed Unicode characters, and Task 10 before Task 2 ascending.
- `test_created_sort_follows_identity_despite_recorded_time` — both directions with equal and
  reversed timestamps, identity gaps and deliberately shuffled storage order.
- `test_sort_defaults_each_unset_control_independently` — absent tuples, singleton-empty tuples,
  each control alone, explicit defaults and mixed empty/set inputs produce the required order.
- `test_count_request_uses_nonempty_raw_choices` — explicit due-date/ascending defaults count as a
  request; absent and blank-only choices do not. Filter-only, sort-only and combined choices use
  the design's nonempty-result visibility rule.
- `test_sort_keeps_filter_membership_and_full_project_options` — every existing filter kind and
  combinations preserve membership; counts and assignee/label options describe the whole project
  where the contract requires it, even when a labelled task is filtered out.
- `test_sort_refuses_unknown_tokens_by_concrete_type` — each field, unoffered tokens, spaces and
  case changes; assert `InvalidSortField`/`InvalidSortDirection`, the control and the raw value.
- `test_sort_refuses_repeated_values_before_invalid_values` — each control with equal, blank and
  mixed repeats; assert `RepeatedSortValue`, its control/count and no second refusal for that control.
- `test_list_collects_filter_and_sort_refusals_in_control_order` — reversed date range with invalid
  direction, both invalid sort controls, and repeated filter/sort controls retain every raw tuple
  and every applicable typed reason without exposing a selection.
- `test_zero_matches_still_validate_sort` — malformed sort is refused even when a valid filter
  selects no task; a valid zero-match result has no requested count under the recorded reading.
- `test_empty_project_ignores_all_choices` — valid or malformed filter/sort inputs keep the empty
  project result; no count or refusals.
- `test_sort_handles_empty_singleton_and_repeated_reads_without_mutation` — deterministic output
  and unchanged state/tasks; unit tests use no file or clock.
- Architecture — `sorting` is landed, `sorting.py` exists, its docstring names FR-36, participating
  modules and existing checking paths, and summary remains absent. Keep every TrackerState field
  assertion and run the existing import, reach, immutability, error and trace checks.

#### Implement

Infer from failing tests.

# Hint:
Establish ascending task identity explicitly as the tie baseline; apply a stable primary-field
ordering in the requested direction. Due-date ordering keeps dated and undated partitions separate
so descending reverses neither null placement nor ties. Created time orders identities in the
requested direction. Use Unicode case folding for the title key and an explicit priority rank.
The selection wrapper gathers filter and sort refusals independently before exposing any result.

#### Verification gate

From the change worktree root run `pytest products/tracker17/tests/`.
Pass: the new unit cases and architecture checks pass and the suite has no new failures.

### Task 2: Application list read (`application/tracker.py`, `application/__init__.py`, `domain/sorting.py`)

**Dependencies:** Task 1 — combined domain selection and refusal types.

**What to build:** Extend `Tracker.project_task_list(project_id, fields, *, sort_fields=SortInput())`
and `ProjectTaskList` per design § 3 B. Preserve existing members and the filter-only meaning of
`narrowed`; add raw `sort_fields`, validated `sorting` and domain-provided `count_requested`.
Use one injected clock reading for selection and row overdue flags. Project combined refusals with
empty rows, zero internal match count, no validated selection and no displayed count. Re-export
every value/refusal that web needs through `application`. Add this task's checking path to the
sorting entry docstring.

#### Behaviours to verify

Developer adds `tests/integration/test_sort_tracker.py` (design T4; CP-434/435/443/447/449).

- `test_sorted_read_projects_domain_order_and_choices` — exact identities, both directions,
  project isolation, raw choices, validated defaults and unchanged full-project options/counts.
- `test_sorted_read_keeps_filter_membership_and_filter_only_narrowed` — sort alone requests a
  count without claiming a filter; filter plus sort narrows by the existing rules.
- `test_sorted_read_projects_all_refusals_without_results` — combined concrete problems in domain
  order with raw input retained, empty rows and no validated filter/sort or visible count.
- `test_sorted_read_distinguishes_empty_project_and_zero_matches` — preserve Task 1's distinct
  validation/count outcomes through the application seam.
- `test_one_clock_read_serves_sorted_selection_and_row_marking` — a handed sequence clock crosses
  a local-date boundary on its next reading; one list still uses one date throughout.
- `test_sorted_reads_never_call_the_saver` — valid, invalid, repeated-address and clear-equivalent
  reads leave the handed recording saver untouched.
- `test_existing_two_argument_list_read_remains_compatible` — existing filter callers retain their
  old members and default due-date/identity order; the older `project_tasks` read stays compatible.

#### Held by review

- QC-21 and design § 3 B — application performs no sorting, ranking, validation or state comparison.
  Integration cases prove answers; reading the diff proves the rule lives in domain.

#### Implement

Infer from failing tests.

#### Verification gate

From the change worktree root run `pytest products/tracker17/tests/`.
Pass: the new read-model cases and existing filter/application tests pass, with no new failures.

### Task 3: Sorted list reads and controls (`web/routes.py`, `web/pages.py`, `tests/integration/test_routes.py`, `domain/sorting.py`)

**Dependencies:** Task 2 — extended read model and application exports.

**What to build:** Implement the GET/presentation portion of design § 3 C. Decode every raw
`sort_field`/`sort_direction` value with blanks retained and hand the tuples to the application.
Extend the existing form with the two native selects after the seven filter controls, keeping one
Apply and Clear. Render the supplied row order, count and validated defaults; retain refused values
as escaped options/attempts, map reasons by concrete type and focus only the first refused control.
Clear uses the bare project address. Unknown projects reach not-found before list validation.
Use the sibling `change_text.md` verbatim for published strings. Add this task's new checking paths
to the sorting entry docstring.

#### Behaviours to verify

Developer adds `tests/integration/test_sort_pages.py`, `tests/integration/test_sort_routes.py` and
`tests/e2e/test_sorting.py`; extends `tests/integration/test_routes.py` (design T5–T7/T9/T10; CP-426–CP-438, CP-441–CP-450).

- `test_nonempty_list_offers_nine_labelled_controls_in_one_form` — exact offered values/defaults,
  filter-seven then sort-two then the single Apply/Clear; empty projects still have no controls,
  including when supplied malformed choices.
- `test_every_sort_field_and_direction_reaches_the_real_site` — all eight combinations assert
  ordered task-link identities, retained controls and count, including due nulls and descending ties.
- `test_sort_controls_default_independently_and_count_only_nonempty_choices` — field-only,
  direction-only, explicit defaults, blank-only and mixed empty/set requests. An unsorted default
  address has no count; sort-only counts for one/several tasks use the text artifact's non-filter words.
- `test_sorted_filter_preserves_membership_options_and_count_wording` — status plus priority
  descending and other filter combinations keep membership and the existing filter words.
- `test_zero_matches_keeps_existing_empty_state_with_or_without_sort` — no table or separate count,
  no empty-project invitation; choices and Clear remain.
- `test_sorted_address_reopens_and_clear_restores_every_task` — same address twice, reload and
  bookmark-like reopening show current data in the same order. Clear drops every choice/count and
  returns due ascending with identity ties. Applying adds no completion message.
- `test_each_sort_refusal_retains_raw_values_and_describes_first_focus` — invalid field, invalid
  direction and repeats of either (equal/blank/mixed); each gets its concrete reason, raw attempt,
  no results/count and unchanged saved bytes. Reversed date range plus invalid direction focuses
  Due from; both sort controls refused focuses Sort by. Exactly one focus owner.
- `test_missing_project_stays_not_found_with_sort_choices` — valid and invalid sorts both answer 404.
- `test_sorted_titles_and_refused_tokens_are_escaped` — `<b>&"x"` displays literally in title order;
  refused tokens containing markup cannot become markup in options, reasons or attempts.
- Browser — keys alone choose/apply sort with scripting disabled, then reload, Back/Forward and
  Clear. The first refused field has focus, its visible reason as accessible description and Clear
  in view. At the filter suite's 400% reflow dimensions the added controls do not clip or widen the page.
- Extend **test_filter_apply_reload_and_clear_are_pages_that_save_and_set_nothing** with sort
  values: each response is 200 without redirect, saved changes or Set-Cookie. Add sorted Apply
  to the existing audit-hook no-outbound and recording-saver action walks, retaining old actions.

#### Held by review

- QC-5/8/23/36 and design § 3 C — reason dispatch uses types, all typed values go through the
  existing escape function, and web adds no rule, clock/file access, script, cookie or retained
  server state. Read the diff beside the import/reach checks; individual requests cannot prove
  every path has these properties.

#### Implement

Infer from failing tests.

# Hint:
Carry raw value tuples symmetrically through address decoding, row forms and the shared address
builder. Reuse existing escaped fields and native select styling; page focus follows the combined
domain problem order. Row-form and address carrying belongs to Task 4.

#### Verification gate

From the change worktree root run `pytest products/tracker17/tests/` and
`pytest products/tracker17/tests/e2e/` as separate commands.
Pass: new GET/page/browser cases and all unchanged filter assertions pass, with no new failures.

### Task 4: Moves retain sort choices (`web/routes.py`, `web/pages.py`, `domain/sorting.py`)

**Dependencies:** Task 3 — sorted GET decoding, controls and results; Task 2 — combined validation before a move.

**What to build:** Complete design § 3 C's move contract through row hidden fields, confirmation,
Back out and the shared address builder. Carry only present sort keys with every value unchanged,
including blank and repeated values. Missing keys remain absent. Validate filter and sort together
before ordinary or confirming list moves can save or open confirmation. Keep existing workflow,
off-list outcome/focus and rendered-page status/cache rules. Add the move-checking path to the entry
docstring; finish its complete CP-446 path set.

#### Behaviours to verify

Developer adds `tests/integration/test_sort_move_routes.py` and extends the new sort page/browser
tests where needed (design T8/T9; CP-439/440/442/449; existing CP-408/409).

- `test_ordinary_move_preserves_sorted_list_choices` — sort alone and filter plus sort retain exact
  hidden fields and address tuples; landing order agrees with the resulting saved tasks.
- `test_cancel_open_back_out_and_confirm_keep_sort_choices` — opening saves nothing; Back out
  saves nothing; confirmation applies the allowed move. Every address/control keeps choices and
  the resulting list order, with the existing focus at the interaction/outcome.
- `test_move_refusal_and_saver_failure_keep_sort_choices` — workflow refusal, bad requested status
  and handed saver failure retain exact choices and state; no refused/failed action is reported done.
- `test_sorted_move_addresses_use_rendered_page_status` — pending confirmation alone is 202;
  other move pages are 200; each has no-store and no Clear-Site-Data. Stale/forged confirmations
  reflect current workflow state, never merely the address's request. A missing task remains the
  established 404 outside no-store, per `docs/adr/0010-pending-confirmation-answered-202-move-pages-not-stored.md` **Decision**.
- `test_move_leaving_status_filter_keeps_off_list_outcome` — the moved task can disappear from
  matching rows while the existing off-list line and focus survive above the sorted remaining list.
- `test_refused_sort_blocks_ordinary_and_confirming_moves` — every invalid/repeated sort condition
  prevents saving and confirmation; landing shows combined field refusals, exact raw values and
  only the first refused field focused.
- `test_move_carrying_preserves_blank_repeats_and_absence` — retained malformed tuples survive the
  redirect unchanged; requests with no sort keys gain none. Existing filter-move tests stay unchanged.

#### Implement

Infer from failing tests.

# Hint:
Carry raw value tuples symmetrically through address decoding, row forms and the shared address
builder. Reuse existing escaped fields and native select styling; page focus follows the combined
domain problem order.

#### Verification gate

From the change worktree root run `pytest products/tracker17/tests/` and
`pytest products/tracker17/tests/e2e/` separately.
Pass: every new move path and all existing filter/move/browser cases pass, with no new failures.

### Task 5: Timed sort and its verdict (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** Task 3 — the sorted GET address, count and row contracts.

**What to build:** Implement design § 3 D's keyword-injected
`measure_task_sort(site, saved_data, timer)` and `sort_fixture_report(state)`, and activate the final
sort block in `main(directory, timer)`. Load the independent 1,000-task/20-comment fixture from its
own `sort-volume` location. Apply priority descending without a filter and mark both GETs
same-origin. The second request opens the sorted address. Compare the full ordered task identities
and count against an oracle derived independently from the loaded fixture, never production sort.
Keep fixture inspection and saved-byte comparisons outside measured intervals. Feed all three rows
into the existing verdict and main's final result. Printed text comes verbatim from `change_text.md`
and the CP-452 contract; the unchanged filter block precedes exactly the four sort lines.

Adapt only CP-456's named timer streams/whole-run expectations as the measurement activates.
Update the descriptions identified under Corrections owed while there.

#### Behaviours to verify

Developer extends `tests/integration/test_timed_run.py` (design T12–T14; CP-451–CP-456).

- `test_timed_sort_uses_its_own_loaded_volume_and_two_same_origin_reads` — independent saved
  directory and loaded fixture, no filter choice, exact priority-descending Apply/reload requests,
  fixture data and product data byte-for-byte unchanged.
- `test_sort_fixture_report_reads_actual_counts_and_first_sorted_text_lengths` — standard fixture
  plus a different loaded fixture with changed task/comment counts, storage order, first sorted
  identity and Unicode code-point lengths; report the loaded truth instead of constants.
- `test_timed_sort_reports_apply_landing_and_sum` — handed timer readings prove each interval and
  their total, using existing Timed/verdict formatting and unchanged LIMIT_SECONDS.
- `test_sort_threshold_failures_reach_main` — slow Apply, slow landing and total exactly 1.0 while
  each part is below it fail their proper rows and main; values below the bar pass.
- `test_failed_sort_apply_suppresses_landing` — refusal or failure returns only the Apply request,
  failed zero-time landing and Apply-only failed total; verdict and main are nonzero.
- `test_timed_sort_rejects_wrong_landing` — refusal, failure status, swapped tasks, missing,
  duplicate or extra identities, wrong count and changed saved bytes each fail landing/total and
  main. The correctly ordered page passes; set equality alone does not suffice.
- `test_timed_sort_detects_saved_byte_changes_during_either_read` — any mutation makes the run
  fail; byte reads do not inflate either measured interval.
- `test_full_run_appends_only_sort_fixture_and_three_rows` — all previous lines unchanged and in
  order, followed by CP-452's four lines, total last. Keep the two existing whole-output test names.
- CP-456 compatibility — extend all 21 fixed timer-stream cases and all seven `whole_run` users
  named in sibling `change_spec.md` **Verified Claims**. Preserve every old action, threshold,
  failure probe, test name and assertion beyond the explicitly released readings/output suffix.

#### Held by review

- CP-454 — the expected order is independent of the product's sorting implementation. Read the
  oracle's imports and comparison beside the wrong-order failure probes.

#### Implement

Infer from failing tests.

# Hint:
The oracle compares the full ordered identity sequence, rather than set membership. Keep fixture
reads and byte comparisons outside both timed intervals. The filter measurement's two-GET shape
is the seam, while CP-454's exact ordering check is specific to sorting.

#### Verification gate

From the change worktree root run `pytest products/tracker17/tests/`.
From the product root run `python3 tests/timed_run.py`.
Pass: new timing/failure cases and all existing timed-action cases pass; the timed run exits 0,
prints exactly the required suffix and every measured row remains below 1.0 second.

### Task 6: Scope and complete-change checks (`domain/`, `application/`, `web/`, `tests/`)

**Dependencies:** Tasks 1–5 — completed sorting capability and timed measurement.

**What to build:** Verify the change's scope and preservation obligations against the branch's merge
base. These are checks of this change, not permanent tests tied to a historical commit.

#### Deliverables verified by review

- From the change worktree root, `git diff "$(git merge-base main HEAD)" -- products/tracker17/docs products/tracker17/persistence products/tracker17/main.py products/tracker17/errors.py products/tracker17/web/style.css products/tracker17/pyproject.toml products/tracker17/tests/requirements.txt`
  prints nothing: the plan changes none of those paths (design § 2; CP-447/458).
- From the change worktree root, `git diff --name-only "$(git merge-base main HEAD)" -- products/tracker17`
  lists only the Project layout paths. Read the full diff to confirm no All tasks route/link,
  summary, saved field, dependency, filter-rule or add-task-flow change (spec **Out of Scope**).
- From the change worktree root, `git diff "$(git merge-base main HEAD)" -- products/tracker17/tests/integration/test_filter_pages.py products/tracker17/tests/integration/test_filter_routes.py products/tracker17/tests/integration/test_filter_move_routes.py products/tracker17/tests/integration/test_filter_tracker.py products/tracker17/tests/unit/test_filtering.py products/tracker17/tests/e2e/test_filters.py`
  prints nothing. Existing filter assertions are retained (CP-456).
- Read `git diff "$(git merge-base main HEAD)" -- products/tracker17/tests/architecture/test_shapes.py products/tracker17/tests/architecture/test_trace.py products/tracker17/tests/integration/test_routes.py products/tracker17/tests/integration/test_timed_run.py`
  from the change worktree root: only the CP-446/450/456-authorized extensions alter existing tests;
  every unrelated assertion, action, failure probe and test name remains, with no new skip.
- Read changed code and tests against Python 3.11 and QC-60; a host-interpreter run alone does
  not prove compatibility with that floor (`docs/nfdr.md` § 8 **QC-60**).

#### Implement

Verified by review — no test.

#### Verification gate

Run the card's `pytest products/tracker17/tests/` from the change worktree root. For the complete
CP-457 check, run that same command from a fresh disposable Git clone checked out at the commit
under test, per `<CORE>/roles/CROSS_ROLE.md` **Every seat** and spec CP-457. Keep the clone's history;
an archive does not satisfy the saved-data ignore check. Remove the disposable clone from outside
it after reading its results.

Also run `pytest products/tracker17/tests/e2e/` from the checked-out repository root.
From its `products/tracker17/` run each command separately:

```sh
python3 -m compileall -q domain application web tests
python3 tests/timed_run.py
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Use the product-pinned tools from `pyproject.toml`/`tests/requirements.txt`, with temporary test data.
Pass: every review criterion holds, both suites and every command exit 0, and no existing test is
loosened, removed or skipped to pass the change. Record per-line review verdicts; do not claim a
check passed when the required environment or permission prevented it from running.
