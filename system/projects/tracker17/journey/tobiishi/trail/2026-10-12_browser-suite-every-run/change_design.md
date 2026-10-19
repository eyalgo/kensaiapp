# Change Design — observe browser focus after the page transition

**Date:** 2026-10-12
**Category:** nfdr
**Behaviour:** preserving
**Publishes text:** no
**Language resolution:** Python — project card `Languages:`; `core/doctrine/engineering/languages/python/README.md`, § The six concerns and where each is answered.

This document owns the placement and observation boundary for the test repair in
`tracker17 · tobiishi · 2026-10-12_browser-suite-every-run`. The characterization contract remains
`change_spec.md`, § Invariants, inside that change unit. The document's home is the change arc under
`core/doctrine/setup/kensaiapp_structure.md`, § 2 Per-project, `journey/tobiishi/<key>/`.

## 1. Change Summary

Repair focus observation in the existing end-to-end tests, keeping each action and its expected
focus target. The structural target is a bounded observation of the intended element in the answer
document before the existing focused-element snapshot is asserted. Do not move code, add a test
function, change a callable's signature, or alter the page to make the assertion pass.

The two focus readers are immediate evaluations of `document.activeElement`
(`products/tracker17/tests/e2e/test_first_project.py:L38-L39`, `focused_id`;
`products/tracker17/tests/e2e/test_people.py:L46-L51`, `focused_id` and `focused_tag`). Page-load
completion is the documented contract of `wait_for_load_state`, rather than a focus predicate
(https://playwright.dev/python/docs/api/class-page#page-wait-for-load-state).

I don't know the runtime cause. Check an unmodified whole-suite failure with the destination
document, navigation/load completion and active-element transitions recorded around the failing
assertion, without setting focus or repeating the action. The evidence must distinguish reading
before native focus has settled from native focus never reaching the intended element. The repair
and its landing commit must explain the observed cause, per the spec's I-7; passing after adding a
wait alone is not that explanation.

The selected repair boundary is the tests' observation of the page. If the evidence requires a
different harness boundary while preserving the same action and focus target, revise this design's
placement before expanding the edit. If the page fails its focus contract and repairing it changes
product behaviour, the spec's § Out of Scope sends the change back for reclassification.

## 2. Blast Radius

No transitive blast radius — public surfaces unchanged. No production importer consumes a changed
contract: NFDR § 1.2 QC-13 to QC-19 forbids every production part from importing `tests/`
(`products/tracker17/docs/nfdr.md:L129-L153`, § 1.2 Forbidden imports).

All paths below are relative to `products/tracker17/`.

| Module | Status | What changes |
|---|---|---|
| `tests/e2e/test_first_project.py` | Modified (observation only) | Observe native focus on the answer page before the existing `name`, `description` and `H1` assertions. File location and callable surfaces stay identical. |
| `tests/e2e/test_people.py` | Modified (observation only) | Observe native focus on the answer page before post-navigation focus assertions, including the shared added-name check. File location and callable surfaces stay identical. |
| `tests/e2e/conftest.py` | Unchanged | Keep process startup, browser/context lifetime, the page fixture and timeouts. |
| `tests/e2e/test_labels.py` | Modified (observation only) | Replace each string-predicate focus wait with `to_be_focused` on the same target. File location and callable surfaces stay identical. |
| `tests/e2e/test_tasks.py` | Modified (observation only) | Replace each string-predicate focus wait with `to_be_focused` on the same target. File location and callable surfaces stay identical. |
| `tests/e2e/test_start_command.py` | Unchanged | Keep its test and observations; include it in the whole-folder proof. |
| `tests/conftest.py`, all non-e2e tests, `tests/timed_run.py` | Unchanged | Keep the in-process characterization suite and its collection boundary. |
| `domain/` | Unchanged | Rule core, per SDD § 3. |
| `application/` | Unchanged | Operator actions and contracts, per SDD § 3. |
| `persistence/` | Unchanged | Saved data, per SDD § 3. |
| `web/` | Unchanged | Page building, attributes, focus target selection and policy, per SDD § 3. |
| `main.py` | Unchanged | Composition and start surface, per SDD § 3. |
| `errors.py` | Unchanged | Base error, per SDD § 3, The units. |
| `pyproject.toml`, `tests/requirements.txt`, `README.md` | Unchanged | Dependency pins, lock, configuration and setup instructions. |

Test observation belongs in `tests/e2e/`, which NFDR § 9 assigns the browser-driven boundary
(`products/tracker17/docs/nfdr.md:L505-L512`, layer 5). The five SDD parts own production concerns,
not this observer (`products/tracker17/docs/SDD.md:L199-L216`, § 3). No product logic is added.

## 3. Layout Plan

Keep every implementation symbol in its current module. No new named module or public re-export is
needed. This is a test-tooling repair rather than a relocation; the shape departure is recorded in
Architect Review Notes. The four edited modules expose no new contract to each other, so there is no
build-sequence edge between them.

### `tests/e2e/test_first_project.py`

The inventory below is the existing module's top-level definitions
(`products/tracker17/tests/e2e/test_first_project.py:L22-L222`, `HOSTILE` through
`test_not_found_requests_write_nothing`). Every listed name keeps its signature or value.

| Symbol | Kind | Target module |
|---|---|---|
| `HOSTILE` | Constant | `tests/e2e/test_first_project.py` |
| `create`, `listed_names`, `focused_id`, `_hand_built` | Helpers | `tests/e2e/test_first_project.py` |
| `test_the_first_output_is_the_ready_message_address_before_location` | Existing test | `tests/e2e/test_first_project.py` |
| `test_the_first_project_lands_on_its_page_with_spaces_line_break_and_created_line` | Existing test | `tests/e2e/test_first_project.py` |
| `test_a_created_project_is_listed_after_a_stop_and_a_start` | Existing test | `tests/e2e/test_first_project.py` |
| `test_names_list_in_case_blind_order` | Existing test | `tests/e2e/test_first_project.py` |
| `test_a_refused_name_puts_focus_in_the_name_field_with_the_reason_as_its_description` | Existing test | `tests/e2e/test_first_project.py` |
| `test_a_description_of_4000_characters_with_line_breaks_is_saved_whole` | Existing test | `tests/e2e/test_first_project.py` |
| `test_a_hand_built_201_character_name_gets_the_reason_and_none_of_the_text` | Existing test | `tests/e2e/test_first_project.py` |
| `test_a_hand_built_over_long_description_is_refused` | Existing test | `tests/e2e/test_first_project.py` |
| `test_markup_in_a_name_shows_as_text` | Existing test | `tests/e2e/test_first_project.py` |
| `test_an_address_with_no_project_shows_the_not_found_page` | Existing test | `tests/e2e/test_first_project.py` |
| `test_not_found_requests_write_nothing` | Existing test | `tests/e2e/test_first_project.py` |

### `tests/e2e/test_people.py`

The inventory below is the existing module's top-level definitions
(`products/tracker17/tests/e2e/test_people.py:L21-L229`, `HOSTILE` through
`test_a_tracker_started_on_data_from_before_the_list_keeps_its_projects`). Every listed name keeps
its signature or value.

| Symbol | Kind | Target module |
|---|---|---|
| `HOSTILE`, `QUOTED`, `NARROW_WIDTH`, `NARROW_HEIGHT` | Constants | `tests/e2e/test_people.py` |
| `press_and_load`, `type_and_add`, `add_name`, `focused_id`, `focused_tag`, `listed`, `assert_added_name_is_focused` | Helpers | `tests/e2e/test_people.py` |
| `test_added_markup_name_has_browser_focus_and_accessible_description` | Existing test | `tests/e2e/test_people.py` |
| `test_people_keyboard_refusals_and_removal_keep_focus_at_the_action` | Existing test | `tests/e2e/test_people.py` |
| `test_a_stale_remove_focuses_the_heading_with_the_reason_and_a_reload_link` | Existing test | `tests/e2e/test_people.py` |
| `test_long_people_names_and_controls_reflow` | Existing test | `tests/e2e/test_people.py` |
| `test_the_list_is_there_after_a_stop_and_a_start` | Existing test | `tests/e2e/test_people.py` |
| `test_a_tracker_started_on_data_from_before_the_list_keeps_its_projects` | Existing test | `tests/e2e/test_people.py` |

### `tests/e2e/test_labels.py` and `tests/e2e/test_tasks.py`

Every top-level definition keeps its name, signature and module
(`products/tracker17/tests/e2e/test_labels.py:L20-L173`, `MARKUP` through
`test_markup_label_is_literal_on_task_and_project_list`;
`products/tracker17/tests/e2e/test_tasks.py:L21-L174`, `MARKUP` through
`test_browser_edit_controls_and_keyboard_focus`). Only the bodies of `open_task` and the tests that
wait on focus change, one line per wait site.

No affected implementation resides in `__init__.py`. Leave the four production re-export modules
byte-identical; their existing `__all__` declarations are the reference, rather than a copied list
here (`products/tracker17/application/__init__.py:L40-L74`, `__all__`;
`products/tracker17/domain/__init__.py:L56-L113`, `__all__`;
`products/tracker17/persistence/__init__.py:L3-L5`, `__all__`;
`products/tracker17/web/__init__.py:L6-L9`, `__all__`).

## 4. Code Strategy

| Module | Hint |
|---|---|
| `tests/e2e/test_first_project.py` | Use Playwright's bounded `to_be_focused` observation on the intended answer-page element before retaining the original snapshot assertion. Bind observation to the completed destination navigation; no focus-setting action is part of this observation. |
| `tests/e2e/test_people.py` | Use the same Playwright observation boundary after navigation, including once in `assert_added_name_is_focused` before its snapshot. Keep `focused_id` and `focused_tag` as immediate readers so the Tab-stop inventory continues to record each key's result. |
| `tests/e2e/test_labels.py`, `tests/e2e/test_tasks.py` | Replace every `wait_for_function("document.activeElement.<tagName\|id> === '<target>'")` with `expect(<page>.locator(<target>)).to_be_focused()` on the same element: `main h1` for `H1`, `#<id>` for an id. Keep the same page object (`page` or `other`) and position. |

`to_be_focused` checks that the selected DOM node has focus and has a finite default assertion
timeout of 5,000 milliseconds
(https://playwright.dev/python/docs/api/class-locatorassertions#locator-assertions-to-be-focused).
Keep that default bound rather than introducing a timing constant, timeout increase or unconditional
delay. The assertion observes a single action's result; it does not submit again, reload, restart a
test, catch and suppress a failure, or turn a failed suite into another attempt.

Do not call `focus()`, click, type or press a key to establish the focus being measured. Preserve
the existing setup actions and keyboard sequence. Positive autofocus assertions precede any
subsequent action that could move focus. Retain assertions on descriptions, viewport position,
outline, saved data and message elements; a focus barrier is not their replacement.

## 5. Test Continuity

No test additions — the existing suite is the characterization contract. Only focus observation
in the four modified § 2 modules changes. The focused-element snapshot assertions remain, so no assertion is
retired without replacement. The spec's § Verified Claims is baseline evidence from its producing
run, not a suite result produced by this design.

The spec has no Examples table or CP Rules; the table maps every invariant and its failure paths
instead (`change_spec.md:L17-L38`, § Invariants and § Structural Goal, in this change unit).

| Row | Existing coverage / check | Continuity and edge paths | Spec |
|---|---|---|---|
| C1 | `test_first_project.py`: first project, refused duplicate name, hand-built 201-character name, hand-built over-long description | Keep the `H1`, `name`, `name`, `description` targets respectively. Keep the refusal reason and discarded-text checks. Retain snapshots after the focus boundary. | I-5; I-8 |
| C2 | `test_people.py`: added markup name and `assert_added_name_is_focused` | Keep both added-name positions, description, outcome-line non-focus, viewport and following Remove Tab stop. | I-5; I-8 |
| C3 | `test_people.py`: keyboard refusals and removal | Keep blank-name and duplicate-name refusal focus on `assignee-name`, successful add on `assignee-1`, `INPUT`, all eight Tab-stop snapshots, `tabIndex == -1`, empty-list heading focus and both outline checks. | I-5; I-8 |
| C4 | `test_people.py`: stale remove and narrow-width controls | Keep two-tab stale removal, unchanged saved bytes, empty-list heading focus, reload link and long-name focus on `assignee-4` together with its outline and overflow bounds. | I-5 |
| C5 | Failure of each positive focus observation | A target absent, body focused, or another element remaining focused must exhaust the bounded observation and fail. Use a disposable diagnostic copy to remove the relevant autofocus attribute, without adding test functions to the committed suite, and demonstrate that the existing control and non-control cases still fail. | I-4; I-5; I-8 |
| C6 | `pytest products/tracker17/tests/`, from the worktree root | Exit 0 with no changes to collected modules, including page-attribute and architecture/trace checks. The browser layer is separately collected by `tests/conftest.py:L33-L48`, `pytest_ignore_collect`. | I-1; I-10; I-11 |
| C7 | Source and callable comparison against the pre-fix tree | Keep production exports and `main.start`, fixture/helper signatures, test names, module docstrings and existing assertions. No patch of a product module's internals. | I-2; I-4; I-10; I-11 |
| C8 | Whole-folder run on a committed archive, with README setup | From the archived instance root, run the exact I-3 command twenty times. Record the commit SHA, environment/browser version, all 27 executed test names, each run's output and its actual exit status. Each of the twenty must exit 0; a nonzero status cannot be dropped from the record. | I-3; I-4 |
| C9 | Added-line review from station-open SHA `530d0c214` | Apply I-6's search to added product lines, including comments; no matching plugin, option or added text. Do not treat a match confined to an unchanged line as a new addition. | I-6 |
| C10 | Landing commit's causal account | Name failing tests, measured variation, and the evidence that the repair removes it. Preserve diagnostic evidence in the change's existing implementation record and commit body, rather than product comments. | I-7 |
| C11 | Product-root Ruff and mypy commands | Run the three commands in I-9, each exiting 0. | I-9 |
| C12 | Dependency/configuration diff | No dependency or configuration edit is designed, so I-12's conditional is inactive. Any justified pin change requires a fresh QC-39/QC-40 check and a placement revision. | I-12 |

The success, refusal, over-limit, empty-list and stale-tab paths are covered by C1 to C4. A
permanently wrong or missing focus target is C5, rather than an accepted timeout. The twenty-run
requirement measures the final committed tree; diagnosis runs and incomplete sequences do not
contribute to C8. The label and task modules' focus waits are repaired too (§ 2), and they count
toward C8's whole folder only through the twenty-run proof.

## Records this change makes false

None — read `products/tracker17/docs/adr/README.md` and Accepted ADR-0001 through ADR-0009,
`products/tracker17/docs/nfdr.md` §§ 1, 2, 8, 9 and RN-15/RN-33,
`products/tracker17/docs/fdr.md` and `products/tracker17/docs/SDD.md` § 3 and TS-1 to TS-4.
The observation-only repair changes none of their contracts. Keep these records outside the edit.

## Architect Review Notes

- **Template adaptation — architect, 2026-10-12 (kind d):** use an in-place observation layout rather
  than label these edits relocation-only. The spec's § Structural Goal requests a suite-tooling
  repair, and `core/doctrine/flow/change_classification.md`, § Behaviour-preserving — definition,
  binds the product contract and public interface, not test-source immobility. No classification is
  re-derived, no invariant is released, and no spec reading is set aside.
- **Realization by construction — architect, 2026-10-12 (kind b):** bind each post-navigation focus
  observation to the expected target before keeping its snapshot assertion. The intended condition
  is focus, whereas the load-state contract only names document load completion
  (https://playwright.dev/python/docs/api/class-page#page-wait-for-load-state). Keep each deadline
  finite and each action single, so a missing native focus remains a failure.
- **Placement — architect, 2026-10-12 (kind e):** no SDD § 3 production part owns test observation;
  place it at NFDR § 9's layer-5 boundary. Use the existing library's observer at the affected
  assertions rather than introduce a new observer module or change `focused_id`'s signature. The
  added-name path already has its shared assertion home in `assert_added_name_is_focused`
  (`products/tracker17/tests/e2e/test_people.py:L58-L67`, that helper).
- **Placement revised after code-integrity stopped — owner-directed, 2026-10-12 (kind e):** the
  first design kept `test_labels.py` and `test_tasks.py` unchanged. Code-integrity's twenty-run proof
  on `7ba95e221` then failed once in `test_labels.py`, with `Page.wait_for_function: EvalError ...
  'unsafe-eval' is not an allowed source of script: script-src 'none'` (`code-integrity-report.md`
  at `486d5dbae`). Cause: Playwright 1.63.0's `waitForFunctionExpression` calls
  `globalThis.eval(expression)` in the page's main world on every poll (the bundled
  `playwright/driver/package/lib/coreBundle.js`, `waitForFunctionExpression`). The page policy is
  `script-src 'none'` (`products/tracker17/web/routes.py:L47`, `PAGE_POLICY`). A probe on a page
  serving that policy in the locked environment: a string predicate true on its first check passed,
  and one false on its first check, so it had to poll, raised that `EvalError`. `to_be_focused`
  passed on the focused element and failed with a plain timeout on an unfocused one. So the label
  and task waits fail whenever focus has not settled by the first check, which is the same timing
  variation this change removes. That brings them into the blast radius under the spec's § Structural
  Goal: "The fix reaches every end-to-end test that varies, whichever module it sits in."
- **QC-12 review — pass:** the placement adds no part or module; this meets the review question in
  `products/tracker17/docs/nfdr.md:L115-L120`, QC-12.
- **QC-41 review — pass:** the design introduces no saved field, credential or outside service;
  the boundary remains observation through the existing local browser harness
  (`products/tracker17/docs/nfdr.md:L328-L332`, QC-41;
  `products/tracker17/tests/e2e/conftest.py:L78-L98`, `TrackerFactory.start`).
- **QC-60 review — pass for the selected approach:** `to_be_focused` exists from Playwright 1.20,
  before the locked 1.63.0, and this design adds no Python syntax or dependency
  (https://playwright.dev/python/docs/api/class-locatorassertions#locator-assertions-to-be-focused;
  `products/tracker17/pyproject.toml:L12-L18`, dev dependencies). This is the feature review of
  `products/tracker17/docs/nfdr.md:L471-L475`, QC-60, not a claim to have run Python 3.11.
- **QC-40 review — pass under RN-33 on 2026-10-12:** query GitHub's public advisory API for every
  package in `products/tracker17/tests/requirements.txt:L4-L18`, using
  `https://api.github.com/advisories?ecosystem=pip&affects=<package>&severity=critical&per_page=100`.
  The actual responses were empty for fourteen package names; Pygments returned
  `GHSA-fff8-4w9p-7v76`, affected range `>= 1.2.2, < 2.1`, first patched version `2.1`, outside the
  locked `Pygments==2.21.0` (https://github.com/advisories/GHSA-fff8-4w9p-7v76).
  The installed headless binary's `--version` returned `Google Chrome for Testing 153.0.8010.12`,
  exit 0, at `~/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell`.
  That matches both Chromium entries in the pinned vendor manifest
  (https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/packages/playwright-core/browsers.json).
  The vendor's 2026-09-15 release lists critical fixes in `153.0.8010.47/.48`
  (https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0541751186.html).
  The vendor's 2026-10-01 release lists a further critical fix in `154.0.8037.97/.98`
  (https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop.html).
  These comparisons do not establish that the installed build is free of advisories. The owner's
  dated exception explicitly covers this build through 2026-11-07
  (`products/tracker17/docs/nfdr.md:L976-L988`, RN-33), so it does not block this review. The exception
  covers no changed build and gives no indefinite waiver.
- **Conditional stage gates:** QC-5, QC-8, QC-20 to QC-27, QC-36 and QC-46 have no triggering
  production change in § 2; their refusal, layer, replaceability, page-building and saved-field
  boundaries stay intact (`products/tracker17/docs/nfdr.md:L56-L84`, QC-5/QC-8;
  `:L160-L216`, QC-20 to QC-27; `:L278-L284`, QC-36; `:L385-L391`, QC-46). The ADR sweep found no
  additional delegated design gate (`rg -n development-design products/tracker17/docs/adr/`:
  no output, exit 1).
