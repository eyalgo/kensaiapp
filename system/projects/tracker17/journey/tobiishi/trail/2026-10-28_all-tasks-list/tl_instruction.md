# Tech Lead instruction — all-tasks-list: list, filter, sort and move tasks across projects

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every product path below is relative to it.
**Scope:** Build the All tasks capability specified by CP-459–CP-489 in `change_spec.md`, for `tracker17 · tobiishi · 2026-10-28_all-tasks-list`.
**Inputs read:** change_spec no Status line · change_design no Status line · project.md no Status line · FDR Settled (version 4) · NFDR Settled (version 16) · SDD Settled (version 12, § 3) · ADR-0001–ADR-0005 and ADR-0007–ADR-0011 Accepted · ADR-0006 Superseded by ADR-0011 · DESIGN Settled (Layout) · writing_bar Settled · affected product source and test layout (change worktree).

This instruction owns the task cut, behaviours and verification commands for the change.
The sibling `change_spec.md` owns acceptance; `change_design.md` owns the interfaces and placement.
Published text comes verbatim from the sibling `change_text.md`.

## Project layout

```text
products/tracker17/
  domain/
    __init__.py                         ← modified: public re-exports
    filtering.py                        ← modified: shared rules, global scope and trace
    sorting.py                          ← modified: shared ordering, global scope and trace
  application/
    tracker.py                          ← modified: global read and shared projection
  web/
    pages.py                            ← modified: navigation, list and presentation seams
    routes.py                           ← modified: global GET and move destination
    style.css                           ← modified: project/wrapping cell hooks
  tests/
    unit/
      test_filtering.py                 ← modified
      test_sorting.py                   ← modified
    integration/
      test_filter_tracker.py            ← modified
      test_sort_tracker.py              ← modified
      test_tracker.py                   ← modified
      test_pages.py                     ← modified
      test_people_pages.py              ← modified
      test_people_routes.py             ← modified
      test_task_pages.py                ← modified
      test_task_routes.py               ← modified
      test_filter_pages.py              ← modified
      test_sort_pages.py                ← modified
      test_filter_routes.py             ← modified
      test_sort_routes.py               ← modified
      test_routes.py                    ← modified
      test_move_pages.py                ← modified
      test_move_routes.py               ← modified
      test_filter_move_routes.py        ← modified
      test_sort_move_routes.py          ← modified
    e2e/
      test_first_project.py             ← modified
      test_filters.py                   ← modified
      test_sorting.py                   ← modified
      test_moves.py                     ← modified
```

No directory or package initializer needs creating. Extend the existing test files.
The parts table places rules in `domain`, page-data projection in `application`, and addresses,
request decoding and rendering in `web` (`docs/SDD.md:198–235`, § 3, “The parts”).
Use the full module set and import graph in `docs/nfdr.md:151–195`, § 1.2:
`domain` imports `errors` and the standard library; `application` imports `domain` and `errors`;
`persistence` imports `domain` and `errors`; `web` imports `application` and `errors`;
`main` may import all four parts and `errors`; `errors` imports no product part.
No part imports `main`, production imports no tests, and production imports no third-party package.

## TL Review Notes

The Tech Lead made these task-cut and precision decisions on 2026-10-28.

- **Split A by feature owner:** Tasks 1 and 2 separate filtering/options from combined sorting.
  Sorting consumes filtering; the design exposes additive entry points with no atomic-landing edge
  (`change_design.md:49–88`, § 3 A; § 3 “Build sequence”). Each task can therefore be checked against
  its own public entry points without an unfinished adjacent task.
- **Split C by responsibility:** Task 4 builds navigation, page presentation and ordinary GET reads.
  Task 5 connects the move POSTs and landing state, including browser history. Both use the same
  `web` files; the design's no-atomic-edge property permits this cut (`change_design.md`, § 3 C and
  “Build sequence”). Task 4 covers rendered move forms and injected presentation values; Task 5
  covers their live request flow. Task 4 tests require no Task 5 handler.
- **Type precision:** represent the closed move destination with `MovePlace(str, Enum)` in
  `web/pages.py`, with values `task`, `list`, `all_tasks`. Keep the two existing constant names and
  their string values usable by current callers. The design fixes a closed discriminator but no
  representation (§ 3 C); the existing strings are `web/pages.py:262–263`, `MOVE_PLACE_LIST` and
  `MOVE_PLACE_TASK`. Unknown/missing request values retain the current task-page fallback
  (`web/routes.py:822–827`, `_move_task`), rather than introducing another refusal or a return URL.
- **Application exports:** no compulsory edit to `application/__init__.py` is needed for the new
  method. It already exports `Tracker`, `ProjectTaskList`, `TaskRow`, both raw inputs and the
  existing typed problems (`application/__init__.py:7–74`, imports, and its `__all__`). Preserve that
  surface and verify it in Task 3; method dispatch adds no new exported value. This narrows § 2's
  application export-file delta to the changes actually required.
- **Clock edge added:** Task 3 uses a clock that crosses local midnight between reads and a non-UTC
  zone. This makes § 3 B's one-local-date contract observable, beyond merely handing in a fixed
  date: selection and every overdue marker must agree even at that boundary.
- **Replay reading carried explicitly:** Task 5 keeps the design's visible-row/off-list distinction
  for CP-475. A final task excluded by the choices gets the refusal above results and no invented
  row; a listed final task gets it beside its status. This preserves matching and retained choices
  together. The design records the reason in “Architect Review Notes”, “Replay when a final task is
  filtered out”; the reading set aside remains in `deferred_decisions.md` under that CP-475 heading.
- **Change-only checks are review gates:** CP-486's unchanged timed harness and CP-487's limited
  assertion changes are checked against this branch's merge base in Task 5. No permanent test pins
  this change's base. Existing timed tests continue to run unchanged.
- **Language resolution:** Python, step 1 from the project card's `Languages:` line. The opened packet
  is `<CORE>/doctrine/engineering/languages/python/README.md`, with all seven concern destinations.
  The product's Python 3.11 runtime decision outranks the packet's instance toolchain
  (`docs/adr/0002-standard-library-only-no-web-framework.md`, § Decision; `docs/nfdr.md`, QC-59–QC-60).
- **Gate execution prerequisites:** the tests need loopback sockets and child processes that receive
  Ctrl-C. The card's exact command collected 1,846 tests in this planning run; sandboxed execution
  returned `20 failed, 1795 passed, 31 errors`, including `socket.bind` raising
  `PermissionError: [Errno 1] Operation not permitted`. The pipe runner's
  `python3 -c 'import signal; print("SIGINT handler:", signal.getsignal(signal.SIGINT))'`
  returned `SIGINT handler: 1` (`SIG_IGN`);
  the startup tests send SIGINT to a child and wait for exit
  (`tests/integration/test_start.py:517–536`, `_run_real_start`). A terminal probe returned
  `SIGINT ignored: False`. Automatic approval review denied a terminal-backed full-suite rerun
  as a prohibited retry; that denied command did not execute. These observations do not release
  any acceptance assertion or route a feature task into the red-at-baseline lane.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git -C <a path on Eyal's machine> ls-files returned the product-relative tracked tree: .gitignore, README.md, application/, docs/, domain/, errors.py, main.py, persistence/, pyproject.toml, tests/ and web/. No build-service, pipeline, runner or workflow configuration appears in that inventory; the product's pyproject.toml contains project metadata, exact dev dependency pins and Ruff/mypy/pytest configuration only."
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

### Task 1: Shared filtering and whole-tracker options (`domain/filtering.py`, `domain/__init__.py`)

**Dependencies:** None

**What to build:** Add `all_filter_options(state)` and
`filter_all_tasks(state, fields, today)` with the design's `FilterOptions`/`FilterSelection` and
typed-refusal contracts. Put shared scope-independent validation, label options and matching inside
the existing filtering module. Retain the project entry points' signatures and results.
Make the shared input/options/selection documentation describe either scope.
Update the feature docstring with FR-31, `application/tracker.py`, `application/__init__.py`, the
participating web files and the actual feature tests required by CP-481; all named files must exist.

#### Behaviours to verify

Extend `tests/unit/test_filtering.py` (design T4–T6, T10, T16; CP-466, CP-468–CP-469, CP-474, CP-480–CP-481).

- `test_all_filter_options_use_the_whole_scope` — total tasks from at least two projects, current
  assignees in list order, exact distinct labels in code-point order; case variants and labels
  belonging only to excluded tasks remain offered.
- `test_empty_all_scope_ignores_every_choice` — no projects and only empty projects, with absent,
  valid, invalid and repeated fields, return the default empty selection and no refusal.
- `test_each_filter_matches_across_projects` — status, priority, exact assignee, exact label,
  from-date, to-date and Overdue each work across at least two projects.
- `test_all_filter_fields_combine_as_and` — matching requires every supplied criterion, including
  an unknown single label yielding no matches rather than a refusal.
- `test_global_due_ranges_are_inclusive_and_exclude_undated` — either endpoint, both endpoints and
  equal endpoints include their dated boundaries; an undated task matches none of those ranges.
- `test_global_overdue_matches_the_row_rule` — yesterday/today/tomorrow, undated, `done` and
  `cancelled` cases agree with the overdue rule for the supplied date.
- `test_global_filter_reports_each_refusal_without_losing_raw_input` — reversed range, unlisted
  assignee, unknown status/priority/overdue, invalid from/to dates and repeats of every filter field
  produce the same typed problems as the project path, in control order. Include identical, empty
  and spaced repeated values; retain the raw input exactly.
- `test_project_filter_contract_survives_shared_scope_extraction` — existing project-only options,
  matching, ordering, empty shortcut and typed refusals remain unchanged; filtering changes no state.

#### Held by review

- CP-480 — both entry points reach one validator, matcher and label-options computation in
  `domain/filtering.py`; no behavioural test alone proves that there is no duplicate implementation.

#### Implement

Infer from failing tests.

# Hint:
Select the scope once, then run the same validation/matching machinery. Establish options from the
whole selected scope before matching. This is the filtering half of design § 4 A's shared-scope hint.

#### Verification gate

From the change worktree root, run `pytest products/tracker17/tests/unit/test_filtering.py`, then
`pytest products/tracker17/tests/`. Pass: the new whole-scope behaviours and existing project tests
pass, the trace checks pass, and the full suite has no new failures.

### Task 2: One combined sort over all matching tasks (`domain/sorting.py`, `domain/__init__.py`)

**Dependencies:** Task 1

**What to build:** Add `sort_all_tasks(state, fields, sort_fields, today)` returning
`SortedSelection` or the existing `ProjectListRefused`. Both list scopes share combined validation,
count visibility and ordering. Keep existing public types and project signatures, with scope-neutral
input/selection documentation. Extend the sorting feature docstring's participants/checks for CP-481.

#### Behaviours to verify

Extend `tests/unit/test_sorting.py` (design T4, T7, T10, T16; CP-465–CP-466, CP-469–CP-471, CP-474).

- `test_default_all_order_interleaves_projects` — the spec's Alpha/Beta fixture returns identities
  2, 1, 4, 3, even when supplied tasks/projects are out of identity order.
- `test_all_sort_fields_work_in_both_directions` — due date, priority, created time and title;
  priorities have all four ranks, title ignores case, undated tasks stay last in both directions.
- `test_cross_project_ties_keep_creation_order` — ties on each field retain ascending identity in
  both directions; equal and nonmonotonic recorded timestamps do not replace creation identity.
  Created-time descending reverses identity order, including identical timestamp cases.
- `test_sort_preserves_exact_global_matches` — filter and sort compose across projects; ordering
  never adds or loses a selected task and counts refer to the whole scope and its matches.
- `test_global_count_is_requested_only_when_owed` — default/blank inputs owe no count; a filter,
  sort-only, combined choice or explicit nonempty default sort requests a count only with results.
- `test_empty_all_sort_scope_precedes_both_validations` — no projects and empty projects ignore
  valid, invalid and repeated filter/sort choices and return the default empty selection.
- `test_all_list_refusals_include_filter_then_sort_problems` — each invalid sort field/direction
  and repeated sort control, plus simultaneous filter problems, yields typed problems in the nine
  controls' order with both raw inputs intact. Sort is checked even after a no-match filter.
- `test_project_sort_contract_survives_shared_ordering` — the existing project behaviours stay
  unchanged after sharing machinery.

#### Held by review

- CP-480 — the project and All tasks entry points reach the same sort validator and `_ordered`;
  no concatenation of independently sorted project results or duplicated priority/overdue rule.

#### Implement

Infer from failing tests.

# Hint:
Select the scope once, then run the same validation/matching/ordering machinery. Reuse the explicit
identity baseline and undated partition in `sorting.py::_ordered`; never merge per-project ordered
results. Preserve independent filter and sort validation before returning a combined refusal.

#### Verification gate

From the change worktree root, run `pytest products/tracker17/tests/unit/test_sorting.py`, then
`pytest products/tracker17/tests/`. Pass: every new ordering/refusal/count test passes, all prior
project sort tests pass, and the full suite has no new failures.

### Task 3: Global page-data read (`application/tracker.py`)

**Dependencies:** Tasks 1 and 2

**What to build:** Add `Tracker.all_task_list(fields, *, sort_fields=NO_SORT) -> ProjectTaskList`.
Share projection of selections/refusals with `project_task_list`. Make `ProjectTaskList` and `TaskRow`
documentation scope-neutral without renaming them or changing their fields. Keep project display
values separate: the renderer obtains projects through `Tracker.projects()`, not copied task data.

#### Behaviours to verify

Extend `tests/integration/test_filter_tracker.py`, `test_sort_tracker.py` and `test_tracker.py`
(design T3–T10, T16–T17; CP-462, CP-465–CP-474, CP-480–CP-483, CP-485).

- `test_all_task_list_projects_global_selection` — whole-scope count, ordered rows and match count,
  validated choices, raw choices, assignees, labels and count visibility all match the global rule
  result; at least two projects contribute rows.
- `test_all_task_list_refusal_is_page_data` — no raised refusal, no rows/count/validated choices,
  every typed problem in order, both raw inputs and whole-scope options retained.
- `test_all_task_list_empty_and_no_match_are_distinct` — zero tasks returns defaults; nonzero total
  with zero matches retains valid choices and options without requesting a visible count.
- `test_all_task_list_uses_one_local_date_for_selection_and_marking` — exactly one clock read per
  call supplies every row and the filter, including a non-UTC date boundary and a clock that would
  cross midnight if read twice. Subsequent calls recompute against the newly supplied instant.
- `test_all_task_list_recomputes_current_state_without_saving` — empty, ordinary, filtered, sorted,
  refused and repeated reads call no saver; a later accepted task change appears on the next read.
  Distinguish setup saves from calls made by the read.
- `test_project_read_and_application_exports_remain_compatible` — prior project results and the
  existing public imports still work, with no HTML, query-key or destination value crossing inward.

#### Implement

Infer from failing tests.

#### Verification gate

From the change worktree root, run
`pytest products/tracker17/tests/integration/test_filter_tracker.py products/tracker17/tests/integration/test_sort_tracker.py products/tracker17/tests/integration/test_tracker.py`,
then `pytest products/tracker17/tests/`. Pass: the global read uses one clock read and zero saves,
all projection/refusal tests pass, and the full suite has no new failures.

### Task 4: All tasks page, read route and navigation (`web/pages.py`, `web/routes.py`, `web/style.css`)

**Dependencies:** Task 3

**What to build:** Register exactly `GET /tasks` as a `PAGE`, dispatch the global read and build
`pages.all_tasks_page` from its read model, projects and existing move presentation values.
Generalize the shared controls, rows and table with existing-project defaults, including the closed
move destination and cancellation back-out address. Add the shared header and both not-found links.
Place the eight-column table and wrapping hooks according to `docs/DESIGN.md` § Layout.

#### Behaviours to verify

Extend `tests/integration/test_pages.py`, `test_people_pages.py`, `test_people_routes.py`,
`test_task_pages.py`, `test_task_routes.py`, `test_filter_pages.py`, `test_sort_pages.py`,
`test_filter_routes.py`, `test_sort_routes.py` and `test_routes.py`; extend
`tests/e2e/test_first_project.py`, `test_filters.py` and `test_sorting.py`
(design T1–T10, T15–T19; CP-459–CP-474, CP-479–CP-485, CP-487).

- `test_header_links_are_projects_all_tasks_people_on_every_page_kind` — ordinary pages,
  confirmations, refusals, failures and both 404 forms have the three links in order. Unreadable
  saved data still has no header. Follow the All tasks link to a direct 200 read with no save.
- `test_both_not_found_forms_offer_both_destinations` — one heading, one following paragraph
  containing Projects then All tasks, no form, 404; three header links and five total links.
  Only `/tasks` leaves the existing unknown-path cases; `/tasks/` and malformed paths remain 404.
- `test_all_tasks_has_one_row_per_task_and_project_after_title` — exact title/h1, eight headers in
  order, spec fixture order 2,1,4,3, task links/attributes/markers and offered moves. Project names
  link to `/projects/<id>` with no choices; no add, rename, delete or summary control appears.
- `test_global_empty_page_precedes_controls_and_refusals` — no projects or only empty projects,
  with absent, valid, invalid and repeated choices, show only the empty invitation under the
  heading, with Projects; no table/controls/count/filter reason or blank result placeholder.
- `test_all_tasks_controls_and_options_cover_the_whole_scope` — nine labelled controls in their
  stated order, one Apply/Clear, list-order assignees, exact code-point labels from all tasks
  before matching, including case variants, duplicate labels and labels only on excluded tasks.
- `test_global_apply_sort_and_clear_are_stateless_reads` — GET Apply targets `/tasks`; a fresh
  address and Clear contain no choices; repeated/bookmarked/Back-equivalent GETs retain choices
  and order while recomputing changed state/date. All return 200 without redirect, cookie, saver
  call or state mutation, and include the page policy. Apply/Clear carry no old move outcome.
- `test_global_controls_realize_cross_project_filter_and_sort_cases` — exercise each field, AND,
  range endpoints and undated cases, AC-13 overdue agreement, all sort fields/directions, priority
  rank, title case, undated last and cross-project identity ties through the real Site.
- `test_global_count_and_no_match_states_use_the_read_model` — filter, sort-only and combined
  counts; explicit default counts versus no-choice no count; sort-only wording makes no filter
  claim. No matches keeps choices/Clear and its filter reason, without table/count/global-empty
  wording. Applying a choice adds no completion message.
- `test_every_global_choice_refusal_keeps_raw_values_and_first_field_focus` — one case per
  CP-474 refusal kind, each filter/sort repeat and simultaneous problems, including sort refused
  after a no-match filter. Reasons are ordered, raw blanks/repeats/spaces remain shown, first
  refused field owns focus/description, no results/count/save appears, and Clear is available.
- `test_global_row_forms_and_injected_move_views_keep_the_destination` — direct page tests with
  existing outcome/interaction values assert `place=all_tasks`, all nine raw carried choices,
  confirmation and back-out forms targeting their authorized destinations, visible-row status
  focus, confirmation sentence focus and restored-button focus. Existing project/task forms
  retain their destinations. These tests call the renderer; they require no global move handler.
- `test_global_typed_values_are_text_in_every_rendered_context` — project names, titles, labels
  and assignees containing `<`, `&` and quotes remain text in cells, options, carried fields,
  titles and accessible descriptions; no script or truncation. Table has the established scroll
  wrapper and wrapping cells, with Project after Title.
- `test_global_get_is_in_the_route_enumeration` — add `/tasks` to `SAMPLE_ADDRESS`, retain route-set
  equality and every prior route sample; include open, Apply, reload, Clear and refusal among
  state/header/no-cookie checks.
- `test_keyboard_reaches_and_filters_all_tasks_without_script` — browser keys from a project's
  header to All tasks, apply filter and sort, verify focus/retained choices, and Clear. Extend
  the browser not-found test to press Projects by name. Use the pinned browser and scripting off.

#### Held by review

- CP-480 — `web` only decodes and presents; shared controls/rows/move rendering are parameterized,
  not copied. No matcher, sort key, count computation or overdue rule enters `web`.
- CP-479 — inspect `web/style.css` against `docs/DESIGN.md:340–385`, § Layout: wrapping header and
  controls, minimum-width title/labels/assignee/project cells, and horizontal scrolling confined
  to the table. Browser checks should also inspect long values and 400% zoom.
- CP-487 — edit only the assertions its exact list releases, preserving existing test names and
  all other assertions. In particular keep rename/delete prohibitions and the People main-content
  All tasks prohibition. The new header link is permitted outside that main content.

#### Implement

Infer from failing tests.

# Hint:
A closed destination discriminator feeds the row forms and cancellation back-out forms. Shared
presentation helpers keep project defaults; the optional project cell and page destination are
parameters, not a copied table or control renderer. This carries the presentation half of design § 4 C.

#### Verification gate

From the change worktree root, run `pytest products/tracker17/tests/` and separately
`pytest products/tracker17/tests/e2e/test_first_project.py products/tracker17/tests/e2e/test_filters.py products/tracker17/tests/e2e/test_sorting.py`.
Pass: all page/read-route/navigation behaviours pass, existing project/task behaviour passes, the
named browser flows pass, and there are no new suite failures.

### Task 5: All tasks move flow and regression boundary (`web/routes.py`, `web/pages.py`)

**Dependencies:** Tasks 3 and 4

**What to build:** Carry `place=all_tasks` through both existing move POSTs and the global landing
read. Validate carried choices through `all_task_list` before opening confirmation or saving.
Resolve current move state, selected-row visibility, off-list outcomes, response status and cache
headers while preserving project-list/task-page landings. Keep failure reporting at the existing site.

#### Behaviours to verify

Extend `tests/integration/test_move_routes.py`, `test_filter_move_routes.py`,
`test_sort_move_routes.py`, `test_move_pages.py`, `test_routes.py` and `test_tracker.py`;
extend `tests/e2e/test_moves.py`, `test_filters.py` and `test_sorting.py`
(design T11–T14, T16–T20; CP-475–CP-489).

- `test_all_offered_moves_return_to_global_choices` — every offered move with no choices, filter
  only, sort only and both redirects to `/tasks`, retains exact carried values and lands with
  current status, one outcome line and the proper focus. Completed-address reload saves nothing.
- `test_global_cancellation_open_back_out_and_confirm_keep_choices` — initial press opens a
  visible-row confirmation without saving; GET back-out restores the cancelled-button focus and
  saves nothing; confirming POST saves once. All destinations remain global with choices intact.
- `test_global_move_page_status_describes_the_rendered_confirmation` — 202 only with a confirmation
  actually rendered, otherwise 200 for the move view; `no-store` on each. No move response has
  `Clear-Site-Data`. Outcome precedence suppresses pending state; hidden/choice-refused rows
  cannot produce a confirmation or a spurious 202.
- `test_global_stale_refused_and_failed_move_keep_state_and_context` — stale disallowed moves and
  typed invalid-status moves show the current allowed moves without saving; a handed-in failing
  saver keeps state, choices and global landing, reports at the existing console site and leaks
  no Python error text. Refused/failed-address reload saves nothing.
- `test_moved_task_leaves_global_status_or_overdue_selection` — moving out of a status, or to
  `done`/`cancelled` under Overdue, removes the row, retains choices, and names the task/new status
  in one completion above results. Check both other matches left and the final match leaving.
  The results section owns focus and the line is its accessible description, including no matches.
- `test_final_task_replay_uses_visible_row_or_off_list_refusal` — reopen both confirmation and
  back-out addresses after final status: a selected task has its refusal beside status; an
  excluded task has the off-list refusal above unchanged selected results, no fabricated row or
  confirmation. Include the final-match/no-match case.
- `test_bad_global_choices_prevent_both_move_posts` — invalid and repeated values for every filter
  and sort control, including simultaneous problems, stop both ordinary and confirming POSTs
  before any save/status change/confirmation. Landing retains raw choices and ordered field reasons.
- `test_global_missing_move_targets_keep_existing_not_found_handling` — deleted POST target
  redirects to its task-not-found path; missing confirmation/back-out target answers 404 without
  `no-store`. Malformed identity/unknown outcome handling keeps existing closed parsing semantics.
- `test_project_and_task_move_destinations_remain_unchanged` — ordinary, cancellation, back-out,
  stale/refused/failed landings for both existing destinations retain their contracts. Missing and
  unknown `place` still fall back to the task page; arbitrary address text never becomes a target.
- `test_global_apply_and_move_open_no_outbound_connection` — extend the existing audit-hook action
  sequence with All tasks Apply and a successful global move. Keep the existing connection check
  and action samples; recording saver sees no reads, no save for global GETs, and only the move's save.
- `test_keyboard_global_filter_sort_move_and_history_revalidate_saved_status` — with scripting off,
  use keys from a project's header through All tasks controls to a row move, then cancellation,
  back-out and confirmation. Verify focus/description and retained choices, including a filtered-out
  result. Extend the pinned-browser history tests to global confirmation and final-status replay;
  use both reload/Back-equivalent requests and real browser Back/Forward traversal.
- `test_global_move_markup_is_escaped_and_trace_paths_resolve` — typed values in move lines,
  confirmation, hidden choices and accessible descriptions remain text; current architecture
  tests pass with FR-31, participating application/web files and actual feature test modules in
  both domain feature docstrings.

#### Held by review

- CP-480 — off-list membership uses selected row identities and a current task lookup. Workflow
  answers still come through `Tracker.allowed_moves`/`move_task`; no filter or move rule is copied.
- CP-486 — `tests/timed_run.py` and `tests/integration/test_timed_run.py` are unchanged against the
  branch's merge base. The standalone run keeps every row in its prior order, both filter/sort
  totals included, and `LIMIT_SECONDS` remains 1.0; no new timed row or relaxed assertion.
- CP-487 — inspect edits to pre-existing assertions against the spec's precise release list.
  No unrelated assertion is removed, weakened, skipped or renamed.
- CP-482 — no saved-schema, dependency or runtime-wiring delta: `persistence/`, `main.py`,
  `errors.py`, `pyproject.toml` and `tests/requirements.txt` remain unchanged.
- CP-481 — trace docstrings name every actual All tasks participant/check. Each extended test
  module retains its trace and names the SRS requirements/acceptance criteria it now checks.

#### Implement

Infer from failing tests.

# Hint:
A closed destination discriminator feeds both move redirects and cancellation back-out forms.
Apply the rendered-row visibility gate before choosing the confirmation response status. Reuse
`_move_view`, outcome precedence and the selected identity set rather than re-evaluating a filter.
Use the existing `_address` entry for every submission redirect (design § 4 C; § 3 C).

#### Verification gate

From the change worktree root:

- `pytest products/tracker17/tests/` — every layer-1–4/architecture case passes with no new failures.
- `pytest products/tracker17/tests/e2e/` — the full separate browser suite passes, including global
  keyboard flow and confirmation history, with the pinned browser.
- `python3 products/tracker17/tests/timed_run.py` — exit 0; every existing row remains in order and
  under 1.0 s, including `filter total at 1000 tasks` and `sort total at 1000 tasks`.
- `python3.11 -m pytest products/tracker17/tests/` and
  `python3.11 -m pytest products/tracker17/tests/e2e/` — exit 0 with the product's pinned test
  dependencies/browser available to that interpreter; CP-489 needs actual 3.11 execution.
- `git diff "$(git merge-base main HEAD)" -- products/tracker17/tests/timed_run.py products/tracker17/tests/integration/test_timed_run.py products/tracker17/persistence products/tracker17/main.py products/tracker17/errors.py products/tracker17/pyproject.toml products/tracker17/tests/requirements.txt products/tracker17/docs` — no output. This is a change-only review, never a permanent suite assertion.
- `git diff "$(git merge-base main HEAD)" -- products/tracker17/tests` — inspect existing assertion
  edits against CP-487 and retain all tests outside its released assertions.
- `rg -n -i 'all tasks' products/tracker17/web/pages.py` — matches for the published page/navigation.

From the product root, run `ruff format --check .`, `ruff check .`,
`mypy main.py errors.py domain application persistence web`, and
`python3 -m compileall -q main.py errors.py domain application persistence web tests`.
Each exits 0 at the product's pinned tool versions.

A run of product checks outside this change worktree uses a fresh clone checked out at the commit
under test, per `change_spec.md` CP-488 and `<CORE>/roles/CROSS_ROLE.md` § Every seat.
