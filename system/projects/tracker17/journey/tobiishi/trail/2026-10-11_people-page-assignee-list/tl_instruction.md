# Tech Lead instruction — people-page-assignee-list: keep the assignee list on People

This document owns the implementation task cut, test obligations and verification gates for
`tracker17 · tobiishi · 2026-10-11_people-page-assignee-list`.
Its behavioural input is that change's `change_spec.md` § Rules, CP-80 to CP-105; its structural
input is `change_design.md` §§ 2–5, Blast Radius through Test Additions.

**Date:** 2026-10-11
**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17
**Scope:** Add the ordered assignee list, compatible saved-data reading, People and its Add/Remove
actions, with browser proof of the added name's focus and accessible description.

Every code and test path below is relative to Product root. Every command labelled worktree root
runs from `.worktrees/2026-10-11_people-page-assignee-list`.

## Project layout

```text
products/tracker17/
  domain/
    __init__.py                           ← modified, re-exports
    assignees.py                          ← new, Assignees entry and rules
    state.py                              ← modified
    refusals.py                           ← modified
  application/
    __init__.py                           ← modified, re-exports
    tracker.py                            ← modified
  persistence/
    saved_data.py                         ← modified
  web/
    pages.py                              ← modified
    routes.py                             ← modified
    style.css                             ← modified
  tests/
    unit/
      test_assignees.py                    ← new
      test_state.py                        ← modified
    integration/
      test_assignee_tracker.py             ← new
      test_saved_data.py                   ← modified
      test_start.py                        ← modified
      test_people_pages.py                 ← new
      test_people_routes.py                ← new
      test_pages.py                        ← modified
      test_routes.py                       ← modified
    e2e/
      test_people.py                       ← new
      test_first_project.py                ← modified
    architecture/
      test_trace.py                        ← modified
      test_shapes.py                       ← modified
```

Create only the new files listed here; no new directory or package initializer is needed.
The five-part boundary and ownership are `docs/SDD.md:L186-L223` § 3, The parts and the seams
between them. The complete import constraints, including `main.py` and `errors.py`, are
`docs/nfdr.md:L123-L153` § 1.2, Forbidden imports; keep both unchanged as design § 2 specifies.
Retain the existing implementations of `domain/text.py`, `domain/projects.py`,
`application/contracts.py`, `web/listener.py`, `tests/conftest.py`, `tests/e2e/conftest.py`,
`tests/timed_run.py`, `pyproject.toml` and `tests/requirements.txt`.

Language resolution: Python, via the project's `project.md:L12-L12` Languages field; packet read:
`<CORE>/doctrine/engineering/languages/python/README.md` § The six concerns and where each is
answered. Product records take precedence under `<CORE>/doctrine/engineering/languages/README.md`
§ Precedence.

## TL Review Notes

The following are this Tech Lead's decisions of 2026-10-11.

- **Task split:** Split design sub-job D into Task 4's page rendering and Task 5's request path
  and browser proof. A page builder is independently testable without a new route; the request
  path consumes that builder. Keep the shared header and all retired navigation assertions in
  Task 4, preserving design § 3's atomic edge (`change_design.md:L196-L207`, Atomic-landing edges).
- **Dependency made explicit:** Task 3 uses Task 2's real actions for first-save/legacy-refusal
  proof, although its production adapter depends only on Task 1. Task 5 owns the combined real
  persistence/request restart proof. This avoids a test reaching a route that is not built yet
  (`change_design.md:L230-L248`, Test Additions, T5–T8 and the combined-proof paragraph).
- **Trace built with available tests:** Task 1's entry docstring names participating production
  modules and test modules that exist at its completion. Tasks 2, 4 and 5 extend that docstring
  when their tests exist; Task 5 verifies the complete final list. Design T4's complete list
  cannot be required in Task 1 because the pointer test fails on a named nonexistent file
  (`tests/architecture/test_trace.py:L96-L100`, test_every_path_named_in_the_entry_docstring_exists).
  The new entry and landed-feature declaration stay together in Task 1.
- **Types upgraded:** Use enums within `web/pages.py` for the new closed refusal codes
  (`blank-name`, `assignee-name-in-use`, `too-long`, `assignee-not-found`) and failed-action kinds
  (`add`, `remove`). Keep serialized query values exactly as design § 3 D's outcome table states
  (`change_design.md:L143-L163`, Outcome-address contract). Parse untrusted query strings at the
  routing boundary; exact assignee names and added/removed names remain strings. Leave the
  existing project-page interface intact. This gives the new page interface a closed vocabulary
  without adding a module or changing a route.
- **Hints divided by responsibility:** Carry design § 4 D's focus/ordinal-ID approach in Task 4
  and its redirect-query/shared-failure-boundary approach in Task 5. Neither task loses the
  approach relevant to its responsibility (`change_design.md:L209-L216`, Code Strategy).
- **Gate contract reconciled:** CP-104 requests all four layers from one broad invocation, but
  the current collection rule excludes e2e unless explicitly named
  (`tests/conftest.py:L33-L48`, _command_line_names_end_to_end and pytest_ignore_collect).
  `docs/nfdr.md:L491-L535` § 9, Test strategy, and
  `<CORE>/doctrine/engineering/testing_doctrine.md` § Layers 1–5, "Layer 5 runs separately",
  require separate e2e execution. Every task therefore gates both the exact card command and a
  separate e2e command. Together they must collect all four requested layers; a green card
  command alone is insufficient. Do not change the collection hook to silently include e2e.
- **Observed baseline limitation:** From the change worktree root, the card's exact command
  `pytest products/tracker17/tests/` collected 224 items and exited 1 with
  `5 failed, 203 passed, 16 errors in 4.40s`. The displayed listener/start failures report
  `PermissionError: [Errno 1] Operation not permitted` at socket bind. This is no proof of
  deferred product tests red on main, and grants no red-at-baseline exemption. The prerequisite
  check `python3 -c 'import importlib.util; print(importlib.util.find_spec("playwright"))'`
  returned `None`; the check of `products/tracker17/.venv` returned `False`. No browser success
  is claimed. Verification requires the pinned test environment and permitted loopback binds;
  missing prerequisites or permission failures are failed gates, never skipped tests.
- **Coverage added:** Task 5 extends the held-saver serialization test to assignee submissions
  and mixed project/assignee requests. Design T13 preserves the request lock but only names the
  existing route coverage; the new cases make QC-53's one-action-at-a-time obligation observable
  on the added dispatch paths (`docs/nfdr.md:L423-L427`, QC-53).
- **Evidence boundary retained:** The browser description assertion must check the browser's
  computed accessible description, beyond checking the HTML's `aria-describedby` value.
  CP-87 and CP-103 require that result (`change_spec.md:L39-L39`, CP-87;
  `change_spec.md:L70-L70`, CP-103). That browser evidence proves neither assistive-technology
  speech nor confirmation behaviour; the records owed below retain both gaps.

## Corrections owed while there

- Owed outside this change's reach: `products/tracker17/docs/adr/0003-no-script-in-any-page.md:L45-L50`
  § Consequences, Dependence — after a passing CP-103 proof, its wholly unverified non-control
  focus/description statement needs narrower evidence: the added-name span's focus, viewport
  position and computed accessible description are checked in Chromium; confirmation and
  assistive-technology speech remain unchecked, and the no-script decision remains in force.
- Owed outside this change's reach: `products/tracker17/docs/SDD.md:L1154-L1164` § 11 R-2 — after
  that proof, distinguish the added-name span now checked from confirmation and
  assistive-technology speech still unchecked; preserve the experience conditions and the
  untested cases.
- Owed outside this change's reach: `products/tracker17/docs/SDD.md:L1769-L1774` § Open Questions —
  after that proof, narrow the non-control focus/description question to its untested cases;
  a passing added-name browser assertion does not close the whole question.
- Owed outside this change's reach: `tracker17 · tobiishi · 2026-10-11_people-page-assignee-list`,
  `change_spec.md:L71-L71` CP-104, and `tracker17 · shukuba · 2026-10-11_people-and-assignees`,
  § Reached when, item 6 — the single broad invocation does not collect e2e under the preserved
  collection rule; the verification statement should name the card command and separate e2e
  command, both required to exit 0. This is the gate reconciliation recorded above.

### Task 1: Immutable ordered assignee rules (`domain/assignees.py`, `domain/state.py`, `domain/refusals.py`, `domain/__init__.py`, `tests/unit/test_assignees.py`, `tests/unit/test_state.py`, `tests/architecture/test_trace.py`, `tests/architecture/test_shapes.py`)

**Dependencies:** None

**What to build:** Implement design § 3 A's immutable ordered assignee state and rule surface in
the owning `domain` part. Preserve the existing state constructor arguments and two-argument
restoration; add the default empty tuple and optional third restoration argument. Expose
`check_assignee_names`, `add_assignee`, `remove_assignee` and `list_assignees`, plus
`AssigneeNameInUse` and `AssigneeNotFound` deriving from `Refusal`. Reuse `BlankName`, `TextTooLong`,
`TextField.NAME` and the existing single name maximum. Update the landed trace declaration with
the entry module, and update state docstrings in the files this task opens.

#### Behaviours to verify

Add `tests/unit/test_assignees.py`; extend `tests/unit/test_state.py`,
`tests/architecture/test_trace.py` and `tests/architecture/test_shapes.py`.

- `test_assignees_start_empty_and_append_in_order` — empty state lists nothing; Dana, Ari and Bo
  appear earliest first, independent of alphabetical order. CP-82, CP-86.
- `test_assignee_names_match_exactly` — Dana, dana, Dana with a trailing space, repeated spaces,
  and markup remain distinct exact values; remove matches only the exact name. CP-88, CP-95.
- `test_remove_preserves_survivor_order_and_readd_appends` — remove the first, middle and last
  names; survivors retain order and a re-added name goes last. CP-82, CP-96.
- `test_assignee_actions_preserve_the_input_and_projects` — input state remains immutable; the
  returned state preserves projects and the identity counter, including on refusal. CP-105.
- `test_blank_assignee_is_refused` — empty and Unicode-whitespace-only names raise `BlankName`.
  CP-89.
- `test_exact_duplicate_assignee_is_refused` — only the exact listed value raises
  `AssigneeNameInUse`. CP-90.
- `test_assignee_length_is_in_unicode_code_points` — 200 code points pass, 201 raise
  `TextTooLong` for the name field; include non-BMP characters and 201 spaces, where length wins
  over blank. CP-91.
- `test_assignee_actions_use_the_state_given_now` — adding against a newly populated state
  refuses a duplicate; absent removal raises `AssigneeNotFound`; removal after re-add succeeds.
  CP-92, CP-96.
- `test_old_state_callers_default_to_no_assignees` — empty state, the existing constructor form
  and two-argument restore remain valid. CP-100.
- `test_restore_retains_order_and_refuses_invalid_assignees_whole` — restoration preserves
  exact values/order and rejects every domain-value break: blank, duplicate, overlong. Preserve
  all existing project-name, length, identity and counter checks. CP-101.
- `test_creating_a_project_preserves_assignees` — use the real existing project rule against an
  enriched state; the assignee list is unchanged. CP-100, CP-105.
- `test_assignees_entry_names_requirements_and_existing_participants` — entry docstring names
  FR-20, FR-22, FR-39, FR-40, DR-4, NFR-9, participating application/web modules and current
  checking tests; all named paths exist and both trace directions remain asserted. CP-102.
- `test_only_the_assignee_feature_is_added_to_domain` — the entry exists, no tasks/priorities/
  due_dates/labels feature module exists, and state gains no task or operator-name field. CP-105.

Each new test module names SRS requirements as well as its CP rules, as design § 5 requires.

#### Held by review

- Domain owns all assignee value rules; no I/O, clock, HTML or published wording enters it.
  The import/reach walks cover structural violations; inspect rule placement and wording in
  the diff against `docs/SDD.md` § 3 domain and `docs/nfdr.md` QC-20.

#### Implement

Infer from failing tests.

# Hint:
Preserve the projects module's separation between runtime state construction and type-only state
references; a mutual runtime import between `state.py` and `assignees.py` would create a cycle.

#### Verification gate

Worktree root: `pytest products/tracker17/tests/` and, separately,
`pytest products/tracker17/tests/e2e/`.
Product root: `python3 -m compileall -q domain application persistence web main.py errors.py`.
Pass: all commands exit 0, both suites collect tests, this task's tests pass, and no existing test
fails. The new entry's named paths all exist; no future test path is required yet.

### Task 2: Saved-before-current assignee actions (`application/tracker.py`, `application/__init__.py`, `domain/assignees.py`, `tests/integration/test_assignee_tracker.py`)

**Dependencies:** Task 1 — assignee state, rules, list query and refusal types.

**What to build:** Add `Tracker.assignees`, `Tracker.add_assignee` and `Tracker.remove_assignee`
with design § 3 B's signatures/results, using domain rules and the unchanged saver/clock contracts.
Publish the new refusal types through `application`, and add this task's test path to the
Assignees entry docstring.

#### Behaviours to verify

Add `tests/integration/test_assignee_tracker.py`, exercising the real Tracker with handed
recording, inspecting and failing savers; no product-name patching.

- `test_assignee_query_does_not_save_or_read_the_clock` — query retains exact order and writes
  nothing, for empty and nonempty starting state. CP-81, CP-86.
- `test_assignee_action_reports_the_exact_name_after_save` — add/remove return the exact value
  only after the saver has accepted the complete candidate. CP-86, CP-93.
- `test_assignee_candidate_is_saved_before_becoming_current` — during the saver call the real
  Tracker still exposes the old list; afterwards it exposes the accepted candidate. CP-97.
- `test_failed_assignee_save_leaves_the_old_state_current` — failing add/remove propagate the
  failure, keep old names/projects/counter and produce no success result. CP-97.
- `test_refused_assignee_action_never_calls_the_saver` — blank, duplicate, overlong and absent
  remove propagate their types, with state unchanged. CP-89 to CP-91, CP-96.
- `test_assignee_actions_check_current_state_after_other_actions` — duplicate after another add,
  remove after another remove, and remove after re-add obey the current-state rules. CP-92, CP-96.
- `test_projects_and_assignees_preserve_each_other` — project creation retains the list and
  list actions retain every project and the counter, in empty/nonempty starting states. CP-105.
- `test_assignee_refusals_are_available_through_application` — web's required types are exported
  from application; the existing import walk continues to forbid a direct web/domain edge.

#### Held by review

- Application adds no validation, duplicate search, HTML or file-format knowledge; check the
  action bodies against `docs/SDD.md` § 3 application and `docs/nfdr.md` QC-21.

#### Implement

Infer from failing tests.

#### Verification gate

Worktree root: `pytest products/tracker17/tests/` and, separately,
`pytest products/tracker17/tests/e2e/`.
Product root: `python3 -m compileall -q domain application persistence web main.py errors.py`.
Pass: all commands exit 0, both suites collect tests, this task's tests pass, and no new failure
occurs elsewhere. No concrete persistence adapter is needed for this task's action tests.

### Task 3: Compatible whole-state saving (`persistence/saved_data.py`, `tests/integration/test_saved_data.py`, `tests/integration/test_start.py`)

**Dependencies:** Task 1 — enriched state/restoration; Task 2 — actions used by the legacy
first-save and refusal tests, not by production persistence.

**What to build:** Extend the adapter under design § 3 C's unchanged load/save interfaces, with
ordered assignees in the exact three-key current JSON shape and the explicit two-key legacy read
case. Keep atomic replacement, project shape, counter and location unchanged. Update the
adapter's opening format description with its implementation; the existing description says
"counter and the projects, and nothing else" (`persistence/saved_data.py:L1-L6`, opening docstring).
The new shape and the existing exact-key assertion form one task.

#### Behaviours to verify

Extend `tests/integration/test_saved_data.py` and `tests/integration/test_start.py`.

- `test_saved_assignees_round_trip_exactly_in_order` — real-file round trip preserves spaces,
  Unicode, markup, remove/re-add order and the empty tuple/list case. CP-99.
- `test_current_saved_data_has_exactly_its_three_keys` — replace the legacy-only expected set
  with exactly next_project_id/projects/assignees, asserting an empty array when appropriate;
  preserve project record keys and counter assertions. Design T6, CP-105.
- `test_legacy_data_loads_without_writing` — two-key saved data loads every project with an
  empty assignee list and identical bytes/directory listing. CP-100.
- `test_first_successful_action_saves_the_complete_shape` — first accepted assignee add or
  project create after legacy load writes the full state, retaining projects/counter. CP-100.
- `test_refused_remove_on_legacy_empty_list_writes_nothing` — absent-name refusal preserves
  legacy bytes and list; a refusal never upgrades the saved document. CP-96, CP-100.
- `test_invalid_present_assignee_list_is_unreadable_and_untouched` — parameterize blank/empty,
  duplicate, overlong, number member, mixed members, null, scalar and mapping; expect
  `UnreadableData` and no partial state, identical bytes and unchanged directory listing. CP-101.
- `test_unknown_or_missing_required_saved_keys_still_refuse` — missing projects/counter,
  unknown top-level keys and existing malformed project shapes still fail whole. CP-100, CP-101.
- `test_invalid_assignees_stop_start_with_the_existing_plain_message` — drive real `main.start`
  for each invalid list case; nonzero status, location named, no ready line, no Python diagnostic
  on the page/console in place of the existing plain unreadable message, bytes unchanged. CP-101.
- Existing interrupted-save and failed-save tests remain green with the enriched state; no
  assertion of whole/absent replacement or untouched unreadable data is removed.

#### Held by review

- Persistence checks JSON shape/types only and delegates data rules to domain restoration;
  no migration, rewrite on load or alternative save path exists. Review against
  `docs/SDD.md` § 3 persistence and ADR-0004 § Decision.

#### Implement

Infer from failing tests.

# Hint:
Distinguish a missing optional legacy field from an explicitly malformed field; reuse domain
construction for value rules and the existing atomic replacement for saves.

#### Verification gate

Worktree root: `pytest products/tracker17/tests/` and, separately,
`pytest products/tracker17/tests/e2e/`.
Product root: `python3 -m compileall -q domain application persistence web main.py errors.py`.
Pass: all commands exit 0, both suites collect tests, this task's real-file/startup tests pass
and all previous persistence/startup assertions still pass. No People route is used by this task.

### Task 4: People rendering and the shared header (`web/pages.py`, `web/style.css`, `domain/assignees.py`, `tests/integration/test_people_pages.py`, `tests/integration/test_pages.py`, `tests/e2e/test_first_project.py`)

**Dependencies:** Task 2 — the application surface and exports used by web.

**What to build:** Add design § 3 D's pure `people_page` interface and outcome presentation,
with the closed types recorded above; add People after Projects in the shared header. Build
semantic list/form markup, exact-name text, ordinal IDs, accessible names, outcome targets and
stylesheet treatment from the change's `change_text.md` and `docs/DESIGN.md`. Replace only the
obsolete full-page navigation assertions named by design T16; keep the not-found main body
Projects-only. Add the new page-test path to the entry docstring. Correct the singular-link
stylesheet comment while editing its header treatment (`web/style.css:L40-L40`, Header comment).

#### Behaviours to verify

Add `tests/integration/test_people_pages.py`; extend `tests/integration/test_pages.py` and the
existing not-found browser test in `tests/e2e/test_first_project.py`.

- `test_every_html_page_has_the_projects_people_header` — exactly one header with Projects
  then People, using the design addresses; include plain/outcome People and existing pages.
  Not-found retains 404, main-body wording, single Projects body link and no forms. CP-80.
- `test_people_has_its_title_list_and_add_form` — correct title, one name field with the
  application-provided maximum and one Add; initially empty shows the authored empty text.
  No operator-name/comment or unavailable controls/links. CP-81, CP-84, CP-85, CP-91.
- `test_people_shows_each_exact_name_and_one_remove` — supplied order and all whitespace/markup
  preserved, one Remove per row, exact hidden submitted name, distinct accessible names for
  case/space/repeated-space variants, visible Remove included unbroken in each name. CP-82, CP-83.
- `test_added_name_is_the_only_non_tab_focus_target` — matching name span has autofocus,
  tabindex -1 and completion description; its Remove is the next control in reading order.
  Neither outcome paragraph nor another element receives autofocus. CP-87.
- `test_removed_or_absent_subject_uses_the_assignees_heading` — removed/stale outcomes and
  added/failed-remove history whose subject is absent retain their authored line, focus the
  heading and describe it; empty-after-remove retains the Add form. CP-94, CP-96; design T18.
- `test_refused_add_describes_and_focuses_the_retained_input` — blank/duplicate reasons keep
  the exact text beside the field, with focus and description on that input. CP-89, CP-90.
- `test_too_long_refusal_renders_none_of_the_payload` — input focused with its reason; no
  supplied name, added/removed value or failure payload appears. CP-91; design T11/T18.
- `test_failed_action_focuses_its_control` — failed add keeps input and focuses Add; failed
  remove retains the row and focuses its Remove; each failure describes that control and the
  message never takes focus. CP-97.
- `test_every_dynamic_name_is_text_in_every_people_context` — markup, ampersand and quote
  characters remain literal in names, values, outcome lines and accessible names; no injection
  or name-derived ID, no script, outside address or meta page policy. CP-82, QC-36.
- `test_plain_people_has_no_action_focus_or_outcome` — no action autofocus/line on plain render;
  unknown outcome codes are parsed by Task 5, not guessed by this builder. Design § 3 D.

#### Held by review

- Every visible/accessible string is placed verbatim from this change's `change_text.md`;
  domain/application add no wording. Inspect all message/control templates and placeholders.
- Visual values, sheet layout, row wrapping and focus treatment follow `docs/DESIGN.md`;
  focus reaches name spans and the Assignees heading as well as existing controls. Browser
  observables are checked by Task 5; source/value fidelity is held by reading this diff.
- Page rendering stores no outcome/state and sends every dynamic value through the existing
  `_escape` boundary; inspect all interpolation contexts against `docs/nfdr.md` QC-8/QC-36.

#### Implement

Infer from failing tests.

# Hint:
Native `autofocus` on a `tabindex="-1"` name span/heading gives the required non-Tab target;
use ordinal IDs rather than embedding names.

#### Verification gate

Worktree root: `pytest products/tracker17/tests/` and, separately,
`pytest products/tracker17/tests/e2e/`.
Product root: `python3 -m compileall -q domain application persistence web main.py errors.py`.
Pass: all commands exit 0, both suites collect tests, direct rendering tests pass, existing
browser tests pass with the new full-header contract and unchanged not-found main body.

### Task 5: People requests, shared failures and real-browser proof (`web/routes.py`, `domain/assignees.py`, `tests/integration/test_people_routes.py`, `tests/integration/test_routes.py`, `tests/e2e/test_people.py`, `tests/architecture/test_trace.py`)

**Dependencies:** Task 2 — list/actions/refusal exports; Task 3 — real save/restart proof through
main; Task 4 — People builder, closed presentation types and stylesheet.

**What to build:** Add GET /people, POST /assignees and POST /assignees/remove under design
§ 3 D's exact route/query contract. Route form decoding and typed results into the application
surface and People builder, preserving the request check and lock. Use one unexpected-action
catch and one console-report site shared with project create. Complete the entry's checking-test
list when all tests exist, and prove the feature in Chromium through the existing main-start
harness. Web imports no concrete persistence class; real persistence belongs only to test wiring.

#### Behaviours to verify

Add `tests/integration/test_people_routes.py` and `tests/e2e/test_people.py`; extend
`tests/integration/test_routes.py` and `tests/architecture/test_trace.py`.

- `test_people_get_and_header_navigation_write_nothing` — GET serves empty/populated People;
  follow the link from every header, including not-found, without state or save changes. CP-80/81.
- `test_assignee_submissions_redirect_to_people_and_do_not_repeat` — successful add/remove
  answer 303 to /people through the address seam, no fragment; following/reloading/history
  outcome GETs leave names/projects/counter and saver count unchanged. CP-86, CP-93.
- `test_assignee_requests_preserve_exact_matching_and_order` — exact case/spaces, append,
  survivor order, remove/re-add and empty-after-last-remove. CP-82, CP-88, CP-95.
- `test_stale_assignee_requests_check_current_state` — another add causes duplicate refusal;
  another remove causes stale refusal with current list/reload link; remove then re-add makes
  old Remove valid again. Refusals save nothing. CP-92, CP-96.
- `test_add_refusals_keep_the_field_and_focus_description` — absent name behaves as blank;
  empty/Unicode whitespace and exact duplicate keep typed value/reason under the right code.
  CP-89, CP-90.
- `test_length_refusal_wins_and_omits_all_submitted_text` — 200 code points accepted, 201
  refused, including 201 spaces; no sent text in Location or resulting HTML, even when a
  hand-built outcome URL adds name/added/removed/failed payload. CP-91.
- `test_assignee_forms_reject_bad_utf8_and_normalize_newlines_only` — raw and percent-encoded
  invalid UTF-8 return 400 without action/save; CRLF and lone CR become LF, preserving other
  characters/spaces. Both submission paths are covered. Design T11, CP-88.
- `test_failed_assignee_actions_keep_state_and_report_plain_failure` — handed failing saver
  leaves current list and real pre-existing saved bytes unchanged; failed add retains input
  and focuses Add; failed remove retains its row and focuses Remove. Console names action
  before diagnostic; page exposes no Python error. Retain existing failed-create proof. CP-97.
- `test_assignee_submission_origin_and_host_checks_run_first` — cross-site, same-site, none,
  missing and any other non-same-origin mark refused; same-origin accepted; wrong/missing
  Host refused. Assert no action/save and unchanged projects/list on every refusal. CP-98.
- `test_all_declared_routes_have_meaningful_state_and_policy_proof` — extend exact route/sample
  equality and set up a listed subject for remove; every GET is read-only and every submission
  redirects. All responses retain policy/no cookie, and no-outbound audit drives both new
  actions. Preserve all earlier route assertions. Design T13, QC-7/QC-8/QC-31 to QC-35.
- `test_assignee_and_project_requests_serialize_through_the_save` — handed held saver proves
  another assignee submission and a mixed project/assignee request wait for the first save;
  both accepted results survive, rather than one overwriting the other. QC-53.
- `test_people_outcome_queries_obey_precedence_without_mutation` — recognized refusal before
  failure before success, added before removed; unknown codes plain; later missing subject
  uses heading with retained line; too-long suppresses all payloads. Every synthetic GET
  leaves saver count/state unchanged. Design T18.
- `test_people_survives_real_save_and_restart` — application/Site wired with real SavedData
  retain ordered exact names after add/remove and fresh load; legacy startup retains every
  project with an empty list and unchanged bytes. Include whole-process legacy browser start.
  CP-99, CP-100; design T8.
- `test_added_markup_name_has_browser_focus_and_accessible_description` — existing Chromium
  harness starts main; add exactly `<b>A&B</b>`, observe literal text/no injected b element,
  active element is the added name, element in viewport, quoted completion is the browser's
  computed accessible description. Tab next reaches that name's Remove. Repeat with a quote
  in the name, and verify reload/back/forward leave saved bytes unchanged. CP-87, CP-103, QC-36.
- `test_people_keyboard_refusals_and_removal_keep_focus_at_the_action` — keyboard-only blank
  and duplicate input focus/description; remove without confirmation, remove-last and stale
  removal heading focus/description. The message is never focused and the name is not a
  sequential Tab stop. No page script; focused non-control has visible focus. Design T15.
- `test_long_people_names_and_controls_reflow` — at the narrow desktop viewport required by
  DESIGN, long exact names and row controls wrap without page overflow or losing controls;
  inspect non-control focus treatment in the actual browser. Design T15.
- `test_assignees_entry_names_all_participating_modules_and_checks` — final entry lists FR-20,
  FR-22, FR-39, FR-40, DR-4, NFR-9 and all participating production/checking test modules;
  retain both trace directions and every projects trace check. CP-102.

#### Held by review

- The unexpected-action failure catch/report sites are shared, refusals handled separately by
  type, and create's outcome/diagnostic semantics retained. Inspect all three action paths
  against `docs/nfdr.md` QC-5/QC-45/QC-56/QC-57; behaviour tests alone do not prove site count.
- Route parsing stores no outcome/session and the application owns all list rules; compare the
  final dependency placement with `docs/SDD.md` § 3 and the import graph. No task feature,
  operator name, migration, library/pin change or README/what-left edit enters this diff.
- Browser focus/description evidence is scoped to the browser assertions above. No script
  fallback or closure of the foundation question is within this change, per `change_spec.md`
  § Out of Scope, "The SDD's Open Question and § 11 R-2's fallback".

#### Implement

Infer from failing tests.

# Hint:
Outcome information travels only in the redirect query. Keep unexpected action failures at one
shared boundary.

#### Verification gate

Worktree root, as separate commands:

```sh
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/
python3 products/tracker17/tests/timed_run.py
```

Product root, in the pinned test environment, as separate commands:

```sh
python3 -m compileall -q domain application persistence web main.py errors.py
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: every command exits 0; the first suite collects unit/integration/architecture and the
second collects e2e, including test_people.py; all previous tests pass with only the explicitly
re-proved exact-key/header expectations changed. The timed run retains its current scope and
passes. QC-62's existing catch-site exception remains narrowly justified at that site; no gate,
test layer or browser assertion is waived to achieve green. Read the final diff against all
Held by review rules and the conditional evidence boundary in Corrections owed while there.
