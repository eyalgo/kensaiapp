# Tech Lead instruction — project-list-filter: narrow a project's task list

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every product path below is relative to it.
**Scope:** Implement the filtering capability specified by `change_spec.md` § Rules, CP-393–CP-425, in `tracker17 · tobiishi · 2026-10-27_project-list-filter`.

This instruction owns the task cut, test behaviours and verification commands for this change.
`change_spec.md` owns behaviour; `change_design.md` owns the interfaces and placement.
The instruction's home follows `<CORE>/doctrine/setup/kensaiapp_structure.md` § 2,
“journey/tobiishi/<key>/”.

## Project layout

```text
products/tracker17/
  domain/
    __init__.py                         ← modified: public re-exports only
    filtering.py                        ← new: filter rules, input and selection values
    refusals.py                         ← modified: field discriminator and typed filter refusals
  application/
    __init__.py                         ← modified: public re-exports only
    tracker.py                          ← modified: read-only query and page read model
  web/
    routes.py                           ← modified: query transport and move returns
    pages.py                            ← modified: filter area, results and move context
    style.css                           ← modified: filter layout and focus
  tests/
    unit/test_filtering.py               ← new
    integration/
      test_filter_tracker.py            ← new
      test_filter_pages.py              ← new
      test_filter_routes.py             ← new
      test_filter_move_routes.py        ← new
      test_routes.py                    ← modified: additive route/policy coverage
      test_listener.py                  ← modified: additive outbound-audit coverage
      test_tracker.py                   ← modified: additive recording-saver coverage
      test_timed_run.py                 ← modified: harness tests and finite timer extensions
    e2e/test_filters.py                  ← new
    architecture/
      test_shapes.py                    ← modified: filtering presence only
      test_trace.py                     ← modified: landed feature and trace checks
    timed_run.py                        ← modified: appended filter measurement
```

Create no package or directory beyond this tree. Placement follows `docs/SDD.md` § 3,
“The parts”, and `change_design.md` § 2, “Blast Radius”. Keep the existing `persistence/`,
`main.py`, `errors.py` and public mutator signatures intact, per the design's transitive check.

The allowed inward edges are `web → application → domain → errors`; `persistence → domain`
and the existing composition-root imports remain as specified by `docs/nfdr.md` § 1.2,
QC-13–QC-19. Matching, validation, counts and offered filter options belong to domain.
The application projects those results. Web decodes requests, maps refusal types and renders pages.
Use that ownership for every task, per `docs/SDD.md:L202-L240`, “The parts” and “The seams”.

## TL Review Notes

Tech Lead decisions, 2026-10-27:

- **Task split:** Split design § 3 C into Task 3's filter page and Task 4's move-return context.
  They share web files but have separate observable responsibilities. Task 3 can leave existing
  move behaviour intact while its GET filtering tests pass; Task 4 uses that filter page.
  Keep design § 3 A's architecture-registration edge inside Task 1.
  Task 5 depends on Task 3, rather than Task 4, because its measurement uses the GET page and
  count but consumes no move-return output.
- **Type precision and placement:** Use the existing `TaskStatus` and `Priority` enums in the
  validated filter rather than open strings. Put `FilterField` beside the refusal types in
  `domain/refusals.py`, following its existing `TextField` discriminator (`domain/refusals.py:L13-L25`).
  Expose it through the public domain and application surfaces. This keeps a closed field set
  available to refusals without a runtime cycle back into `filtering.py`.
- **Coverage added:** Task 4 explicitly tests malformed carried filters on both ordinary and
  confirming move submissions before any save. Design § 3 requires that validation, but § 5 T8
  does not enumerate the malformed-submission cases. Add tests for unrelated return parameters
  and an outcome about another project's task so carrying choices cannot broaden the return target.
- **Coverage sharpened:** Task 4 tests an off-list cancellation address after another tab has
  made the task final. Preserve the saved-workflow refusal before deciding where the line goes;
  the existing `_move_view` checks visible membership before the workflow
  (`web/routes.py:L340-L372`). A visible-rows-only lookup must not suppress CP-409's refusal.
- **Review-only scope checks:** Task 6 holds CP-423's change-specific limits and unchanged-file
  checks against the branch's merge base. These checks belong to this change, so they are not
  permanent suite assertions. Task 6 uses the completed diff, rather than creating another feature.
- **Language resolution:** Python, step 1, from `system/projects/tracker17/project.md` `Languages:`.
  Opened `<CORE>/doctrine/engineering/languages/python/README.md` and all seven routed concerns.
  The product's Python 3.11 floor and pinned tools outrank packet defaults, per `docs/nfdr.md`
  § 8 QC-59–QC-62 and `docs/adr/0002-standard-library-only-no-web-framework.md` § Decision.
- **Gate invocation:** The card's `pytest products/tracker17/tests/` collected 1,370 tests but its
  sandboxed run ended `20 failed, 1320 passed, 30 errors`, with socket binds refused. With socket
  approval, `test_listener.py -x -q --tb=short` gave `19 passed`, but a startup probe still timed
  out after `child.send_signal(signal.SIGINT)` (`tests/integration/test_start.py:L514-L536`).
  The command environment's signal probe printed `SIGINT handler: 1` and `SIG_IGN: 1`.
  The full-suite command used in the gates below restores the normal handler before entering
  pytest; with socket approval it gave `1370 passed in 131.37s` on the unchanged product at
  `71c98a64fed3f1bb26de56bf8b3917958a8c5ff6`. The test selection is the card's; the wrapper changes
  only the execution environment. The browser command uses the same signal handling because its
  harness also stops child trackers with SIGINT (`tests/e2e/conftest.py:L50-L61`). This baseline
  was on Python 3.15.0, so it does not discharge CP-425's Python 3.11 gate.

## Gate environment inputs

Collected from the product worktree by `<CORE>/prompts/gate_suite.md` Steps 1, 3 and 4.
The inventory command lists tracked product files; no product CI configuration or runner file
appears in that listing. The repository-level configuration inventory returned only
`.python-version` for the named CI/configuration paths. No decision in `docs/nfdr.md` § 8 or
Accepted ADR-0001–ADR-0010 names a gate environment or an amd64 requirement.

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git ls-files products/tracker17 returned the product's source, documentation, tests, .gitignore and pyproject.toml; no CI configuration, runner or included pipeline file. git ls-files .github .gitlab-ci.yml .buildkite Jenkinsfile azure-pipelines.yml .circleci Makefile justfile tox.ini .python-version returned exactly .python-version."
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

### Task 1: Domain filter rules (`domain/filtering.py`, `domain/refusals.py`, `domain/__init__.py`, `tests/architecture/test_shapes.py`, `tests/architecture/test_trace.py`)

**Dependencies:** None

**What to build:** Implement design § 3 A's pure filter input, validation, option query and selection.
Expose immutable `FilterInput` with a tuple of raw strings for each field, immutable `TaskFilter`,
immutable option/selection results and the seven-member `FilterField`. Use optional `TaskStatus`
and `Priority`, optional exact names/labels and calendar dates, and a boolean overdue choice.
Define and raise all eight specific refusal types and `FilterRefused` in the designed domain
surface. Each refusal carries its field; the aggregate carries original input and ordered refusals.
Keep all field cardinality, parsing, matching, count and option-order rules here.

Add `filtering` to `LANDED_FEATURE_WORDS`. Replace only the filtering-absence assertion in
`test_only_the_task_features_are_added_to_domain` with presence. The feature module and those
architecture expectations have no green point between them, per design § 3's atomic-landing edge.
The entry docstring names FR-32–FR-35, the existing participating application/web modules and
checking test files that exist. Each later task updates the entry trace when it adds a participant.

#### Behaviours to verify (developer adds tests to `tests/unit/test_filtering.py` and extends `tests/architecture/test_trace.py`)

- `test_each_filter_selects_only_matching_project_tasks` — parameterize all six filters and both
  date controls; exclude another project's matching task. Use supplied state and date, with no I/O.
  Covers CP-396, CP-412, CP-414 and design T1.
- `test_filter_fields_combine_as_and` — one fully matching task and one task missing each selected
  predicate prove conjunction across all fields, per design T1.
- `test_absent_and_singleton_empty_fields_do_not_narrow` — absent tuples and singleton empty
  values leave the ordered list unchanged; overdue absent/empty is off and `on` is on (design § 3 A).
- `test_exact_labels_and_names_keep_case_and_spaces` — exact comparison preserves surrounding
  spaces and distinguishes `Bug` from `bug`; a single unknown label is valid with zero matches
  (CP-396, CP-403–CP-404, CP-411).
- `test_date_ranges_include_both_boundaries` — lower only, upper only, both and equal ends include
  boundary dates. Every nonempty range excludes undated tasks (CP-396, CP-402, design T1).
- `test_overdue_uses_the_supplied_day_and_open_status` — yesterday/open matches; today/open,
  undated, yesterday/done and yesterday/cancelled do not (CP-415).
- `test_each_invalid_filter_has_its_own_typed_refusal` — separately assert `InvalidFilterStatus`,
  `InvalidFilterPriority`, `FilterAssigneeNotListed`, `InvalidFilterDueFrom`, `InvalidFilterDueTo`,
  `ReversedFilterRange`, `InvalidFilterOverdue` and `RepeatedFilterValue`, with their field inside
  the aggregate. A removed name still on a task is refused. Cover invalid shape and impossible date
  for each end (CP-402–CP-406, design T2).
- `test_repeated_values_are_refused_for_every_field` — all seven fields, equal duplicates and blank
  duplicates included, are refused before parsing; a singleton empty remains unset (design T2).
- `test_multiple_filter_problems_follow_control_order` — collect all bad fields; bad Status plus a
  reversed range reports both, with the range on Due from. An invalid or repeated date end produces
  no spurious reversed-range refusal (CP-405, design T2).
- `test_filter_results_preserve_explicit_due_then_identity_order` — shuffled storage, tied due
  dates and undated ties retain the order of `list_project_tasks`, with ascending identities for
  ties (CP-397, design T3; `domain/tasks.py:L372-L380`).
- `test_filter_options_cover_the_whole_project` — `ui`, `Bug`, `bug` and duplicate labels yield
  `Bug`, `bug`, `ui`; another project's labels are absent. Filtering out a labelled task does not
  remove its option. Assignees remain earliest-added first (CP-394, design T3).
- `test_empty_project_ignores_filter_validation` — return the empty-project selection even for
  malformed/repeated choices, with full-project count zero (CP-393, design § 3 A).
- `test_filtering_changes_no_input_value` — valid, refused and empty-project queries leave the
  supplied state and raw input unchanged; the filter values/results are immutable (CP-413, T2).
- `test_filtering_entry_has_requirements_and_participants` — filtering's trace names actual
  requirements and existing application, web and checking-test paths; the pointer and shape
  suites retain their other assertions (CP-412, CP-423, design T10).

#### Implement

Infer from failing tests.

# Hint:
Preserve multi-values until cardinality validation; aggregate typed field refusals to show
simultaneous errors. Filter the existing explicitly ordered list; reuse the one overdue predicate.
Keep the field discriminator beside the refusals, as the existing text-field discriminator does.

#### Verification gate

From the change worktree root: `pytest products/tracker17/tests/unit/test_filtering.py products/tracker17/tests/architecture/`
and `python3 -c 'import signal, pytest; signal.signal(signal.SIGINT, signal.default_int_handler); raise SystemExit(pytest.main(["products/tracker17/tests/", "-q", "--tb=short"]))'`.
From the product root:
`python3 -m compileall -q domain`, `ruff format --check .`, `ruff check .`,
`mypy main.py errors.py domain application persistence web`.
Pass: the new rules and architecture checks pass, each command exits 0 and the suite has no new
failure. Architecture assertions for sorting, summary and `TrackerState` remain intact (CP-423).

### Task 2: Read-only application query (`application/tracker.py`, `application/__init__.py`, `domain/filtering.py`)

**Dependencies:** Task 1's input, selection, options and refusal contracts.

**What to build:** Add `Tracker.project_task_list(project_id, fields)` and immutable `ProjectTaskList`
as design § 3 B specifies. Carry the full-project count, ordered `TaskRow` values, domain match
count, validated choices, original input, typed problems and offered choices. Refusal has no
result rows or count. The application uses domain's option query for the refused projection.
Re-export every contract web needs through `application/__init__.py`. Keep
`Tracker.project_tasks(project_id)` and all mutator signatures compatible. Update the feature
trace for the new checking module (CP-412).

#### Behaviours to verify (developer adds tests to `tests/integration/test_filter_tracker.py`)

- `test_project_task_list_projects_domain_selection` — selected rows, order, options and counts
  agree with the domain result for a valid filter, unfiltered query and empty project (design T4).
- `test_refused_list_preserves_typed_problems_and_raw_choices` — every typed refusal reaches the
  read model in order, with full-project options and no result/count (CP-405–CP-406).
- `test_overdue_filter_and_row_marking_agree` — injected clock covers yesterday/open,
  today/open, yesterday/done and yesterday/cancelled, through both selection and markers (CP-415).
- `test_one_local_date_snapshot_serves_the_whole_page` — a clock whose second read crosses local
  midnight records exactly one call for a query; all results use its first local date. A later
  query recomputes on the next date (CP-396, CP-399; design T4).
- `test_filter_queries_never_reach_the_saver` — valid, refused, clear and repeated reads leave
  the recording saver empty and current state unchanged (CP-413, design T4).
- `test_existing_project_tasks_remains_compatible` — the old signature returns its existing
  ordered rows and overdue flags (design § 2 transitive check and T4).

#### Held by review

- `docs/nfdr.md` QC-21 and `docs/SDD.md` § 3 application row — read the diff for domain-owned
  comparisons, validation, counting or option sorting placed in application; behaviour tests alone
  cannot prove ownership. Application only orchestrates and projects the domain results.

#### Implement

Infer from failing tests.

# Hint:
One clock snapshot serves selection and row markers; a refused selection is projected with its
typed problems and domain-supplied options.

#### Verification gate

From the change worktree root: `pytest products/tracker17/tests/integration/test_filter_tracker.py`
and `python3 -c 'import signal, pytest; signal.signal(signal.SIGINT, signal.default_int_handler); raise SystemExit(pytest.main(["products/tracker17/tests/", "-q", "--tb=short"]))'`.
From the product root:
`python3 -m compileall -q application domain`, `ruff format --check .`, `ruff check .`,
`mypy main.py errors.py domain application persistence web`.
Pass: each command exits 0; query tests and existing consumers pass, with no saver call on a read.

### Task 3: GET filtering and the project page (`web/routes.py`, `web/pages.py`, `web/style.css`, `domain/filtering.py`)

**Dependencies:** Task 2's read model and application re-exports.

**What to build:** Implement design § 3 C's address and page contracts, including refusal mapping,
retained raw attempts, controls, counts and result states. Extend the existing address builder to
support repeated query pairs while preserving its existing callers. Use the seven exact keys
`filter_status`, `filter_priority`, `filter_assignee`, `filter_label`, `filter_due_from`,
`filter_due_to`, `filter_overdue`. Apply is a separate GET form to the bare project path, without
a fragment; Clear links to that path with no query. Preserve all decoded raw values. The native
controls emit a single value each; the overdue checkbox's checked value is `on`.

Implement layout from `docs/DESIGN.md` § Layout, “The filter controls”, and its focus/reflow rules.
Place the change's published words verbatim from `change_text.md`; wording is governed by CP-395.
Update `tests/integration/test_routes.py`, `test_listener.py` and `test_tracker.py` additively
for route/policy, outbound-audit and recording-saver coverage, per CP-417 and design T11.
Extend the feature trace for each new participant/checking module when it exists.

#### Behaviours to verify (developer adds tests to `tests/integration/test_filter_routes.py`, `tests/integration/test_filter_pages.py`, `tests/e2e/test_filters.py` and extends the three existing integration modules above)

- `test_nonempty_project_offers_labelled_filter_controls` — Status/Priority offer their four
  values, names and labels follow domain order, all fields have visible labels, and the controls
  sit above the task list (CP-393–CP-395, design T5).
- `test_empty_project_retains_first_task_page_without_filters` — valid and malformed query choices
  both retain the first-task invitation and exactly one add form, with no filter controls (T5).
- `test_each_get_filter_and_and_combination_show_matches` — every field, all-field AND and lower,
  upper, both and equal date ends produce exactly matching task links in the required order,
  with the count and selected values retained (CP-396–CP-398, T6).
- `test_reload_bookmark_and_back_recompute_without_saving` — reusing the address retains choices;
  a later load reflects current state and clock. Clear returns all tasks, unset controls and a bare
  address. Neither Apply nor Clear shows a success message (CP-395, CP-399–CP-400).
- `test_unset_controls_show_no_filter_count` — absent/singleton-empty values show no active count
  or applied message; unknown query parameters add no filter (design § 3 C).
- `test_no_matches_keeps_choices_and_clear_without_an_empty_project_message` — retain an unmatched
  label option, show the filter-specific empty state, and show no table or first-task invitation
  (CP-401, T5).
- `test_each_refusal_shows_its_field_reason_and_preserves_data` — parameterize every Task 1 refusal
  through web, including repetition in each of the seven fields. Assert unchanged state and real
  saved bytes, no results/count/no-match line, and Clear present (CP-402–CP-406, T7).
- `test_simultaneous_refusals_focus_only_the_first_field` — bad Status plus reversed range shows
  both reasons, one autofocus on Status, and descriptions on every refused field (CP-405, T7).
- `test_malformed_and_repeated_attempts_remain_visible` — preserve every raw date, invalid overdue
  token and repeated value in its labelled area, escaped. The correction control keeps its normal
  single-value form and a corrected Apply is accepted. Include blank duplicates (design § 3 C, T7).
- `test_removed_assignee_is_refused_even_when_a_task_still_carries_it` — choices use the current
  list, and an old address shows the assignee reason (CP-403, T6).
- `test_missing_project_wins_over_invalid_filter_choices` — return the established 404 page (CP-410).
- `test_names_and_labels_round_trip_as_text` — `<`, `&`, quotes and surrounding spaces survive
  option values, display and percent-encoded addresses, without becoming markup (CP-411, T9).
- `test_filter_get_preserves_route_security_and_state_contracts` — route enumeration reaches
  Apply/reload/Clear; policy headers remain present, no cookie is set, the recording saver receives
  no call, and the outbound audit drives Apply without a connection (CP-417, T11).
- `test_filter_apply_and_clear_work_with_keyboard_and_no_script` — drive the real tracker through
  its existing layer-5 harness with scripting disabled. Use only browser keys to change choices,
  Apply and Clear; verify the result links, count and URL (CP-411, T9).
- `test_filter_refusal_focus_and_filter_row_reflow` — in the real browser, the first bad control
  actually receives focus and enters view, its reason describes it, and a valid Apply opens at
  page start. At 400% zoom the filter row stacks and only the table scrolls horizontally (T9).

#### Found after the second pause (owner, 2026-10-27)

The second pause's open failure is a product defect, not a test-setup gap. Its planned fix is ruled
out.

- `tests/e2e/test_moves.py` `test_double_click_never_confirms_at_the_original_trigger_coordinates`
  `[short-row-interior]` and `[short-row-far-edge]` fail. The filter row puts a short list's
  cancelled button below the 720px fold (box y 787).
- Scrolling it into view does not pass: tried as nearest-edge and as `scroll_to_middle`, both fail
  at "the original coordinate must land on the sentence". At the page's bottom (scrollY 145, height
  865) the confirmation reopens at scrollY 208, height 928, and `.button-confirm` (y 634–662) sits
  under the trigger's old box (y 642–670). A stray click there confirms the cancel (CP-325, CP-337).
- Requirement: the confirmation opens with `#confirm-sentence` under the trigger's coordinates
  wherever the trigger sat, including at the bottom of the page. Fix it in the product. Do not
  weaken the test or bring the trigger in from the page's bottom in its setup.
- Add a case with the trigger at the page's bottom, so the guarantee does not rest on the filter
  row's height. Log the fix in Developer Review Notes.

#### Held by review

- `docs/nfdr.md` QC-5/QC-16/QC-23/QC-36 — map refusals by type through application, escape dynamic
  HTML through the existing `_escape` only, and leave rule/count/clock work out of web.
  The architectural placement and single escape site are checked by reading the changed call sites.

#### Implement

Infer from failing tests.

# Hint:
GET form plus the existing address builder, extended for repeated pairs. Keep the raw request
values intact through the application query; render the refused, empty-project and no-match states
from the read model's distinct results.

#### Verification gate

From the change worktree root:
`pytest products/tracker17/tests/integration/test_filter_routes.py products/tracker17/tests/integration/test_filter_pages.py products/tracker17/tests/integration/test_routes.py products/tracker17/tests/integration/test_listener.py products/tracker17/tests/integration/test_tracker.py`,
`python3 -c 'import signal, pytest; signal.signal(signal.SIGINT, signal.default_int_handler); raise SystemExit(pytest.main(["products/tracker17/tests/", "-q", "--tb=short"]))'`
and `python3 -c 'import signal, pytest; signal.signal(signal.SIGINT, signal.default_int_handler); raise SystemExit(pytest.main(["products/tracker17/tests/e2e/"]))'`.
From the product root: `python3 -m compileall -q web domain`, `ruff format --check .`,
`ruff check .`, `mypy main.py errors.py domain application persistence web`.
Pass: every command exits 0; browser focus/keyboard/reflow checks pass; existing move and add-task
behaviours retain their assertions. The browser suite is separate from the card's suite,
per `tests/conftest.py` “The collection rule” and `docs/nfdr.md` § 9.

### Task 4: Moves return to the filtered list (`web/routes.py`, `web/pages.py`, `domain/filtering.py`)

**Dependencies:** Task 3's filter page, repeated-query address support and result states.

**What to build:** Implement design § 3 C's move-return contract. Carry only the seven filter keys
through row forms, open confirmation, Back out, confirming submission and success/refusal/failure
redirects. Validate carried filters through the application before a list move can save.
Resolve current task/project membership independently of visible membership; use selected identities
from the query to place outcomes rather than retesting a filter rule in web. Keep existing outcome
precedence and saved-workflow checks. Only a visible pending confirmation produces 202; other move
landings produce 200, with the existing absent-target 404 exception. Every move interaction/outcome
landing carries `Cache-Control: no-store` and no move response carries `Clear-Site-Data` (CP-407).

A visible row keeps its existing message/focus. An off-list outcome about this project gets one
line above the results, including a no-match state. Its described list section takes focus, not
the line. Preserve task-page moves and the add-task behaviour excluded by the spec.
Update the feature trace when the move test module exists (CP-412).

#### Behaviours to verify (developer adds tests to `tests/integration/test_filter_move_routes.py` and extends `tests/integration/test_filter_pages.py` and `tests/e2e/test_filters.py`)

- `test_each_list_move_path_keeps_filter_choices` — ordinary move, open cancelled confirmation,
  Back out, confirm, workflow refusal and saver failure retain values in forms, redirects, URLs
  and controls; the landing answers its actual rendered interaction (CP-407, design T8).
- `test_status_filtered_move_leaves_with_one_named_completion` — moving todo to in-progress removes
  the row, names title/new status and explains its departure. The last matching row yields the
  no-match state below that line (CP-408).
- `test_overdue_move_to_either_final_status_leaves_the_list` — both done and confirmed cancelled
  remove the overdue row with the completion above results (CP-408, T8).
- `test_priority_filtered_move_keeps_the_row_and_its_existing_focus` — a task still matching
  Priority high remains in place with its existing row outcome (CP-407).
- `test_off_list_refusal_and_failure_remain_visible` — stale other-tab moves and a failing saver
  can produce an outcome for a task absent from the visible selection. Show the reason above the
  results with list-section focus, and leave the current/saved state unchanged on failure (CP-409).
- `test_stale_off_list_confirmation_address_shows_current_workflow_refusal` — after another tab
  makes the task final, reopening its confirmation address shows the saved-status refusal above
  results rather than a hidden/stale confirmation; answer 200 with no-store (CP-409; TL review).
- `test_invalid_carried_filters_prevent_ordinary_and_confirmed_moves` — repeat a field or send a
  reversed range/unlisted assignee before either move endpoint. No save or move occurs; the
  redirect/landing keeps the whole raw attempt and shows the field refusals (CP-405; design § 3 C).
- `test_move_returns_allow_only_filter_keys` — unrelated query keys and an arbitrary return URL
  cannot change the destination or become hidden filter state; an outcome naming a different
  project's task produces no line on this project (design § 3 C; TL review).
- `test_filtered_move_responses_keep_history_contract` — 202 only when confirmation is actually
  rendered, otherwise 200; no-store on move landings, no Clear-Site-Data on submissions or pages.
  Keep absent-target 404, outcome precedence and unfiltered/task-page results (CP-407, T8).
- `test_special_filter_values_survive_move_and_confirmation` — names/labels with `<`, `&`, quotes
  and spaces survive encoded URLs and escaped hidden values exactly; repetition is not collapsed
  on a refused return (CP-411, T9).
- `test_off_list_completion_focus_enters_the_list_section` — through the real browser with no
  script, moving out of the list focuses its described section and brings the line into view.
  Verify that the message itself receives no focus, including the last-match case (CP-408, T9).

#### Implement

Infer from failing tests.

# Hint:
Carry allowlisted choices through every list move path; render off-list outcomes at the list
section. Keep the full-project task lookup separate from selected membership so the saved-workflow
check still runs before the rendered confirmation and response status are chosen.

#### Verification gate

From the change worktree root:
`pytest products/tracker17/tests/integration/test_filter_move_routes.py products/tracker17/tests/integration/test_filter_pages.py products/tracker17/tests/integration/test_move_routes.py products/tracker17/tests/integration/test_move_pages.py products/tracker17/tests/integration/test_routes.py`,
`python3 -c 'import signal, pytest; signal.signal(signal.SIGINT, signal.default_int_handler); raise SystemExit(pytest.main(["products/tracker17/tests/", "-q", "--tb=short"]))'`
and `python3 -c 'import signal, pytest; signal.signal(signal.SIGINT, signal.default_int_handler); raise SystemExit(pytest.main(["products/tracker17/tests/e2e/"]))'`.
From the product root: `python3 -m compileall -q web domain`, `ruff format --check .`,
`ruff check .`, `mypy main.py errors.py domain application persistence web`.
Pass: every command exits 0, the real browser confirms focus and current-state history behaviour,
and all unfiltered/task-page move assertions still pass.

### Task 5: Timed filter measurement (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** Task 3's real GET filtering address, task-link identities and displayed count.

**What to build:** Add the filter fixture opener, measurement, report and appended runner block
with the callable seams of the move harness, per design § 3 D. Give it its own temporary saved-data
location and a loaded 1,000-task fixture with 20 comments per task. Filter Status in-progress.
Time GET Apply and the reload GET with the injected timer, using same-origin headers.
Check the saved bytes around both requests. Determine expected matching identities independently
from the loaded fixture. Validate the landing's exact identities, number of rows and match count.

Append exactly CP-419's fixture line and three measurement lines after the existing move total,
in that order, with no later output. Derive fixture counts and first-displayed-task text lengths
from the loaded fixture. Keep `LIMIT_SECONDS` at 1.0, with the existing verdict formatting and
strict bound for Apply, reload and their sum. A refused/failed Apply skips reload with zero elapsed
time and propagates failure to the total and run. Update the runner docstrings that describe the
move as last (`tests/timed_run.py:L1-L27`, `L885-L888`, `L953-L956`) to include the appended filter.

Extend only the finite timer readings and whole-output expectations CP-423 identifies in
`change_spec.md` § Verified Claims. Preserve their other assertions. Add the filter harness tests
to the existing integration module, whose opening trace also gains the filter requirements.

#### Behaviours to verify (developer extends `tests/integration/test_timed_run.py`)

- `test_timed_filter_uses_independent_loaded_fixture` — its location differs from every earlier
  action's fixture; source data and all earlier fixture preconditions survive. Both requests are
  same-origin GETs, and the production data directory is untouched (CP-418, design T12).
- `test_timed_filter_reports_loaded_counts_and_first_displayed_lengths` — an independent fixture
  with different text, ordering and matching count proves every field is read back. The title and
  first comment lengths belong to the first matching row in list order, not storage order (CP-419).
- `test_timed_filter_rejects_refused_or_failed_apply` — field-refusal/result-less 200, action-failure
  response and non-success response all fail. No reload is requested; its row is
  `0.0 ms — refused or failed`, and the total uses Apply time with failure (CP-421).
- `test_timed_filter_times_apply_and_reload_destinations` — real GET Apply reloads the same
  filtered address. A successful redirect supplied by the request seam reloads its Location,
  as CP-420 requires. The four timer reads exclude setup and readback work (design § 3 D).
- `test_timed_filter_rejects_inexact_landing` — non-200, one extra nonmatch, one missing match,
  a duplicate match row, a wrong matching identity or a wrong displayed count fail the landing
  and total (CP-421–CP-422, design T12).
- `test_timed_filter_detects_saved_byte_changes` — even equivalent decoded data with altered
  bytes fails the measurement and makes the run nonzero (CP-421).
- `test_timed_filter_requires_every_duration_below_the_limit` — slow Apply, slow reload,
  each part exactly 1.0, and a sum exactly 1.0 with both parts below it fail their respective
  rows and run. A total below 1.0 passes (CP-420–CP-422).
- `test_timed_filter_failures_reach_main_verdict` — each new rejection class makes the complete
  harness return nonzero even when every earlier action passes (CP-422).
- `test_timed_run_keeps_prefix_and_appends_only_filter_block` — all old lines retain their order
  and format through the move total; exactly four filter lines follow. Extend both existing
  output assertions, the 15 finite-timer cases and six `whole_run` users listed in the spec;
  each preserves every other assertion (CP-423, design T13).

#### Implement

Infer from failing tests.

# Hint:
Independent loaded fixture readback and exact task identities guard the measurement; four timer
reads cover Apply and reload.

#### Verification gate

From the change worktree root: `pytest products/tracker17/tests/integration/test_timed_run.py`
and `python3 -c 'import signal, pytest; signal.signal(signal.SIGINT, signal.default_int_handler); raise SystemExit(pytest.main(["products/tracker17/tests/", "-q", "--tb=short"]))'`.
From the product root: `python3 tests/timed_run.py`, `python3 -m compileall -q tests`,
`ruff format --check .`, `ruff check .`, `mypy main.py errors.py domain application persistence web`.
Pass: every command exits 0; timed output has the unchanged prefix and exactly the specified suffix;
all three filter times are strictly below 1.0 second, with no refused or failed measured action.

### Task 6: Verify the change boundary and complete gates (`domain/`, `application/`, `web/`, `tests/`)

**Dependencies:** Tasks 1–5's completed implementation, tests and changed-file set.

**What to build:** Record review verdicts for the change-specific scope and compatibility limits
of CP-412, CP-413 and CP-423–CP-425. This task adds no feature and no permanent test against a base
commit. Use the branch's own merge base and its live working tree for the review.

#### Deliverables verified by review

- From the change worktree root, `git diff --name-status "$(git merge-base main HEAD)" -- products/tracker17`
  lists only the product paths in Project layout. Read every existing-test diff: only the shape
  reversal, trace registration, additive filter coverage and CP-423's exact timer/output extensions
  are permitted. No earlier assertion is weakened, deleted or skipped, and no old timed action or
  limit changes. New failure-injection tests check the real subject through handed-in seams.
- From the change worktree root,
  `git diff "$(git merge-base main HEAD)" -- products/tracker17/persistence products/tracker17/main.py products/tracker17/errors.py products/tracker17/web/listener.py products/tracker17/pyproject.toml products/tracker17/tests/requirements.txt products/tracker17/tests/conftest.py products/tracker17/docs`
  prints nothing. No saved field, dependency pin, listener, composition-root or input-record change
  is part of this delta (design § 2 and § 5 T14).
- Read the changed domain/application/web files against `docs/SDD.md` § 3 and `docs/nfdr.md` § 1.2.
  Every filter rule and count is in domain, web imports no domain module, re-export files contain
  no implementation, and filtering introduces no clock read or saver call outside the designed
  read-only query. The compile/architecture/type checks supplement this placement review.
- Read `domain/filtering.py`'s entry docstring against all actual participants and checking files.
  Every newly added test module has its SRS requirement or acceptance-criterion trace (CP-412).
- Run the product checks below with Python 3.11 and the product's pinned test tools.
  Record the interpreter's `python3 --version` output and each gate's outcome.
  CP-425 is satisfied only by a real 3.11 execution; a newer interpreter's green result or Ruff's
  target setting cannot stand in for it. The test command remains the project's card command.

#### Implement

Verified by review — no test.

#### Verification gate

From the change worktree root:
`python3 -c 'import signal, pytest; signal.signal(signal.SIGINT, signal.default_int_handler); raise SystemExit(pytest.main(["products/tracker17/tests/", "-q", "--tb=short"]))'`
and `python3 -c 'import signal, pytest; signal.signal(signal.SIGINT, signal.default_int_handler); raise SystemExit(pytest.main(["products/tracker17/tests/e2e/"]))'`.
From the product root: `python3 --version`, `python3 tests/timed_run.py`,
`python3 -m compileall -q main.py errors.py domain application persistence web tests`,
`ruff format --check .`, `ruff check .`, `mypy main.py errors.py domain application persistence web`.
Run the two diff commands above from the change worktree root.
Pass: the Python version is 3.11, every gate exits 0, unchanged paths produce an empty diff,
and each review criterion has a recorded verdict. The terminal suite's environment and execution
follow `<CORE>/prompts/gate_suite.md`; this evidence section selects no environment itself.
