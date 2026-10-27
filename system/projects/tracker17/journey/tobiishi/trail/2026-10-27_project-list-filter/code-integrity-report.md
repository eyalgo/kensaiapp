# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-27_project-list-filter` — a project's task list narrows by
filter. Reviewed 2026-10-27 by the Senior Engineer, workflow mode, on the branch at `<a commit not in the public history>`
(the developer's closing marker).

## Deferrals

None. The newest `developer: 2026-10-27_project-list-filter — implementation complete` marker
(`<a commit not in the public history>`) carries no `Deferred:` line and no `Failing:` line, so there was nothing to check.

## What was reviewed

The product code the change wrote under `products/tracker17` since the merge base `3cff55048`:
`domain/filtering.py` (new), `domain/refusals.py`, `domain/__init__.py`, `application/tracker.py`,
`application/__init__.py`, `web/routes.py`, `web/pages.py`, `web/style.css` and `tests/timed_run.py`,
and the tests it added or changed: `tests/unit/test_filtering.py`,
`tests/integration/test_filter_tracker.py`, `test_filter_routes.py`, `test_filter_pages.py`,
`test_filter_move_routes.py`, `test_routes.py`, `test_listener.py`, `test_tracker.py`,
`test_timed_run.py`, `tests/e2e/test_filters.py`, `tests/e2e/test_moves.py` and
`tests/architecture/test_shapes.py`, `test_trace.py`.

## The intent it was checked against

- `tl_instruction.md` — Tasks 1 to 6, each task's *Behaviours to verify*, *Held by review*, and the
  owner's ruling under Task 3, *Found after the second pause*.
- `change_spec.md` — rules CP-393 to CP-425 and the Examples table.
- `change_design.md` § 3 A to D, for the interfaces the instruction points at.
- `docs/fdr.md` — not needed beyond what the spec quotes.

## Placement

Walked against the parts table, `docs/SDD.md` § 3, and `docs/nfdr.md` § 1.2. Nothing was moved,
so there is no placement commit.

- Field parsing, cardinality, the reversed range, matching, the AND, the date range, the overdue
  verdict, the match count, label order, assignee choices and whether a filter narrows are all in
  `domain/filtering.py`. Owner: `domain`. Already there. The overdue verdict calls the one
  `domain.due_dates.is_overdue`, the same one the row marker uses.
- `FilterField` and the eight typed refusals are in `domain/refusals.py`. Owner: `domain`. Already
  there.
- One clock read per page, and turning the selection or refusal into `ProjectTaskList`, are in
  `application/tracker.py`. Owner: `application`. Already there. `ProjectTaskList.narrowed` only
  reads `TaskFilter.narrows`, and the refused case gets its options from `project_filter_options`.
  Neither is a rule of its own.
- Decoding the seven `filter_` keys, the repeated-pair address builder, which keys a move carries,
  checking the carried filter through `project_task_list` before a move, and deciding whether a
  task is on the list from the read model's chosen identities are in `web/routes.py`. Owner:
  `web`. Already there. No web module imports `domain`; they import `application`.
- Reasons mapped by type, controls, retained attempts, count sentences, the off-list line and the
  confirmation's layout are in `web/pages.py` and `web/style.css`. Owner: `web`. Already there.
  `_filter_select` adds a sent value that matches no choice to the options so the control can
  show it. That is display, not a filter rule.
- The timed filter measurement is in `tests/timed_run.py`, beside the move measurement. It is test
  harness code, outside the parts table.

## The tests added or fixed

- **Added** `test_a_refused_filter_keeps_every_choice_as_sent` in
  `tests/integration/test_filter_pages.py`, with its helper `shown_in_field`. It comes from CP-405,
  "the controls hold the choices as sent". The existing tests checked this only for refused fields
  (raw attempts, the removed assignee). Nothing checked that a field that was *not* refused keeps
  its value on a refused page. This test refuses Status and Due to, and checks that Priority,
  Assignee, Label, Due from and Overdue still hold what was sent, that the refused values show,
  and that focus is on Status. It would fail if the refused page dropped the valid choices. Green.
- **Strengthened** `test_a_filter_narrows_only_when_a_choice_is_set` in
  `tests/unit/test_filtering.py`. Assignee was the only one of the seven fields its loop did not
  check, so it now checks Assignee `dana` (CP-398, design § 3 A). Green.
- **Fixed:** none. Every existing test I read asserts what the intent says, not what the code
  happens to do. I checked the developer's two declared test corrections against the intent and
  both hold. In `test_filtered_move_responses_keep_history_contract`, a 202 is owed only for a
  confirmation that is shown, and the design shows one only on a visible row. In
  `test_double_click_never_confirms_at_the_original_trigger_coordinates`, the trigger is scrolled
  into view nearest-edge only, which the owner's ruling allows.

Every behaviour planned in Tasks 1 to 5 has a test. Four of the planned test names are carried
by other names (see *Calls made*, item 2).

## The finding

No issues. No code bug, no misplaced logic, no wrong test. The two test additions above both
passed against the code as it stands. The suite now has 1,575 cases, all green.

## Calls made

1. **An off-list confirmation the workflow still allows shows nothing.**
   - *The question:* the spec's Examples row for CP-409 says: "List filtered by `todo`; another tab
     moved task T to `in-progress`; this tab presses `cancelled` on T → the refusal line about T
     sits above the list". The workflow allows `in-progress → cancelled`
     (`domain/workflow.py:50`), so no refusal happens. The press opens a confirmation for a task
     the list does not show. Design § 3 C says "A pending confirmation is rendered only for a
     visible row", so the page lands at 200 with no line and no confirmation. The developer's test
     asserts exactly that (`test_stale_off_list_confirmation_address_shows_current_workflow_refusal`,
     second half).
   - *The readings:* (a) the example's setup is wrong for this workflow, and the rules (CP-407,
     CP-409) and the design are met as written; (b) the example means any stale press on an
     off-list task must leave a line, which would need a new line or a confirmation shown above
     the list.
   - *Taken:* (a). CP-409 covers "a refusal or failure line", and none happens here. CP-407 is met,
     because the press lands on the same filtered list. The design states the visible-row rule in
     so many words. Reading (b) would add a page state no rule or design names, which would be a
     redesign.
   - *Whose:* the Product Owner (the example in `change_spec.md`) and the Architect (design § 3 C).
   - *If they rule the other way:* a later change adds a line for an off-list confirmation, and
     that half of the developer's test is reversed.
2. **Four planned test names are carried by other names.**
   - *The question:* four names in the plan's *Behaviours to verify* do not exist as written:
     `test_each_get_filter_and_and_combination_show_matches`,
     `test_each_refusal_shows_its_field_reason_and_preserves_data`,
     `test_removed_assignee_is_refused_even_when_a_task_still_carries_it` and
     `test_timed_run_keeps_prefix_and_appends_only_filter_block`.
   - *Taken:* I accepted them, because each behaviour is tested in full under another name.
     - The first is split into `test_each_get_filter_shows_exactly_its_matches_in_list_order` and
       `test_all_fields_combine_as_and`.
     - The second is split into `test_each_refusal_shows_its_reason_at_its_field` (reason,
       described-by, one autofocus, no result, Clear) and `test_a_refused_filter_changes_nothing_on_disk`
       (state, saver and saved bytes, including blank repeats in all seven fields).
     - The third is `test_a_removed_assignee_is_refused_even_when_a_task_still_carries_it`.
     - The fourth is the CP-419 four-line extension of the two existing whole-run tests that
       CP-423 names, `test_timed_run_appends_exactly_three_ordered_action_blocks` and
       `test_timed_run_appends_exact_move_block_and_nothing_after`.

     Asking for the planned names would only rename tests.
   - *Whose:* the Tech Lead (`tl_instruction.md`).
   - *If they rule the other way:* the tests are renamed. No assertion changes.
3. **Where a refused Status value shows.**
   - *The question:* CP-405 says the controls hold the choices "as sent", but it does not say
     whether a value no option offers (Status `blocked`) shows as a selected option or in the
     field's retained-attempt area.
   - *Taken:* the new test accepts either, as long as it shows in that field. The design leaves the
     form open, and pinning the form the code happens to use would be reading the test off the
     implementation.
   - *Whose:* the Architect (design § 3 C).
   - *If they rule the other way:* the test is narrowed to the form they name.

## The language resolution

- **Language:** Python, step 1 of the chain, from the `Languages:` line in
  `system/projects/tracker17/project.md`.
- **Packet:** `<CORE>/doctrine/engineering/languages/python/README.md`, with its seven concerns.
  Toolchain, Layout, Quality gates, Conventions, Errors and logging and Gate environment are
  `toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md` and
  `environment.md`. Testing is `<CORE>/doctrine/engineering/testing_python.md`.
- **The product's own floor:** the product pins Python 3.11, in `docs/nfdr.md` § 8 QC-59 to QC-62
  and ADR-0002. That outranks the packet's 3.13 floor, as the developer's marker also records.
- **The two test edits against the packet:**
  - Lines stay within 100 columns, and both files pass the product's pinned `ruff format --check .`
    and `ruff check .`.
  - Strings are double-quoted and use f-strings.
  - Annotations use builtin generics and PEP 604 unions.
  - No name in a product module is patched. The test runs through the real Site, Tracker and saved
    data, with the injected clock (`testing_python.md`, the seam rule).

## Test evidence

- **The verdict rests on this run:** the card's `pytest products/tracker17/tests/`, run through
  `<CORE>/tools/gate_suite.py run --gate code-integrity` on the plan's environment evidence. Before
  running it I re-checked that evidence: the same tracked-file inventory, and still no CI. There was
  no owner's ask, because `KENSAIAPP_GATE_OWNERS_MAC` was unset. The run exited 0 with
  `1575 passed in 120.42s` on Python 3.15.0. The tool printed the one `Environment:` line above.
- **Supplementary check on the product's 3.11 floor (CP-425):** I ran the two edited files on
  Python 3.11.9 (`/private/tmp/t17-venv311`) with
  `pytest products/tracker17/tests/unit/test_filtering.py products/tracker17/tests/integration/test_filter_pages.py`.
  The result was `113 passed`. This run is not the verdict's.
- **The browser suite and the timed run** were not run again. This review changed no layer-5 test
  and no product code. The developer's closing marker records both as exit 0 on 3.11.9.
