# Tech Lead instruction — browser-suite-every-run: observe native focus after navigation

**Date:** 2026-10-12
**Surface:** Codex
**Category:** nfdr
**Behaviour:** preserving
**Product root:** products/tracker17 — every product path below is relative to it.
**Scope:** Diagnose the focus variation and repair observation in four existing browser-test modules, preserving the actions, targets and test inventory.

This document owns the task cut and verification gates for
`tracker17 · tobiishi · 2026-10-12_browser-suite-every-run`.
Read `change_spec.md` and `change_design.md` in that change unit before acting.
Classification is copied verbatim from `change_design.md:L4-L5`, header.
The plan's home is the change arc, per `core/doctrine/setup/kensaiapp_structure.md:L2102-L2106`,
§ 2 Per-project, `journey/tobiishi/`.

## Project layout

```text
products/tracker17/
  tests/e2e/
    test_first_project.py    ← modified: observation only
    test_people.py           ← modified: observation only
    test_labels.py           ← modified: observation only (Task 3)
    test_tasks.py            ← modified: observation only (Task 3)
```

Create no directory, module or `__init__.py`.
Keep the symbol-to-module mappings in `change_design.md`, § 3 Layout Plan.
The full production module set and allowed/forbidden imports remain
`docs/nfdr.md:L123-L153`, § 1.2 Forbidden imports.
Production ownership remains `docs/SDD.md:L195-L246`, § 3 The parts, and the seams between them.
Browser observation belongs to `tests/e2e/` under `docs/nfdr.md:L501-L512`, § 9 Test strategy.
Keep every other path byte-identical, including the harness, non-e2e tests,
production code, dependency files, README and decision records. The one other e2e module,
`test_start_command.py`, is unchanged.

## Commands and common verification

Use these working directories explicitly:

```sh
change_root=.worktrees/2026-10-12_browser-suite-every-run
product_root="$change_root/products/tracker17"
```

References beginning `core/` or `system/` resolve from `change_root`; product references resolve
from `product_root`. Local `change_spec.md` and `change_design.md` references name the inputs
inside the change unit identified above.

Set up and activate the product's `.venv` from `product_root`, using
`README.md:L87-L109`, Running the tests:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r tests/requirements.txt
python -m playwright install chromium
```

The environment must permit the suite's local loopback listeners and Chromium process.
Check command effects against the session policy before running them, including Git metadata writes
inside helpers. Request approval on the first invocation of a command that needs protected writes.

Run the card's command from `change_root` before and after each task:

```sh
pytest products/tracker17/tests/
```

Pass: all 813 existing in-process tests execute and pass, with no skip and no source change
(`change_spec.md:L18-L21`, Invariants I-1/I-4; `L46`, Verified Claims row 1).
Run these commands from `product_root` after each edit:

```sh
python3 -m compileall -q tests/e2e/test_first_project.py tests/e2e/test_people.py
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: each exits 0; use the locked versions without changing their pins
(`docs/nfdr.md:L298-L302`, QC-39; `L480-L489`, QC-62;
`core/doctrine/engineering/languages/python/quality_gates.md`, The two gates).

Compare source inventories from `change_root`, before editing and after both tasks:

```sh
git -C "$change_root" grep -nE '^def test_' 530d0c214 -- products/tracker17/tests/e2e/
git -C "$change_root" grep -nE '^def test_' -- products/tracker17/tests/e2e/
pytest --collect-only -q products/tracker17/tests/e2e/
git -C "$change_root" diff 530d0c214 -- products/tracker17
git -C "$change_root" diff --unified=0 530d0c214 -- products/tracker17 | awk '/^\+\+\+/{next} /^\+/{print}' | grep -inE 'rerun|flaky|retry|retries'
```

Pass: the same 27 function names in the same five modules are collected, with no new test function,
skip, expected failure or selection filter (I-4).
Ignore changed line numbers when comparing inventories.
The product diff must touch only the two layout paths.
Read that diff against the base source to verify unchanged callable signatures, opening docstrings,
assertions and keyboard actions (I-2/I-5/I-10/I-11).
The added-line search must print nothing and exit 1; another exit status is an error, not a pass (I-6).
No product code or public re-export changes are allowed.

### Diagnostic evidence and final whole-folder proof

I don't know the runtime cause. Check an unmodified whole-folder failure with the destination
document, completed navigation/load and active-element transitions recorded around its failing
assertion, without establishing focus or repeating the action.
The required evidence boundary is `change_design.md:L27-L37`, Change Summary.
Keep temporary diagnostic instrumentation in a disposable copy, outside committed product code.
Preserve the baseline run's actual output, exit status, test names and trace in the existing
implementation record and causal commit account (I-7; design § 5 C10).
Evidence must show whether the snapshot precedes native focus settling or native focus never reaches
the target. A passing run after inserting a wait does not establish either cause.
If the measured cause requires a harness edit outside the four modules, stop and surface the placement
conflict. If native focus fails the product contract and the remedy changes product behaviour, stop
for reclassification under `change_spec.md:L58-L64`, Out of Scope.

For each task, run its existing negative diagnostic in a separate disposable copy: remove the relevant
autofocus attribute from a form-control answer and from a focusable non-control answer, without
changing the committed product or adding a test function (design § 5 C5).
The original positive focus checks must fail within their bounded observation when the target is
absent or focus remains on the body or another element.
Confirm that the failure is the focus check, rather than a setup or unrelated failure.
Restore neither attribute nor focus during the measured action; discard the diagnostic copy.

After both tasks, the whole-folder proof uses the final committed tree (I-3).
From `change_root`, create a disposable archive:

```sh
proof_sha=$(git -C "$change_root" rev-parse HEAD)
proof_root=$(mktemp -d /private/tmp/tracker17-browser-proof.XXXXXX)
git -C "$change_root" archive "$proof_sha" products/tracker17 | tar -x -C "$proof_root"
git -C "$proof_root" init
```

From `proof_root/products/tracker17`, run the four README setup commands above.
Keep that archive's `.venv` active, then use `proof_root` as the working directory.
Record `proof_sha`, macOS/Python/locked-package versions, browser version, collected node inventory,
full outputs and actual exit statuses alongside the implementation record.
Run `python --version`, `python -m pip freeze`, and
`python -c 'from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); print(b.version); b.close(); p.stop()'`
to capture the environment; each must exit 0.
Record the inventory with `pytest --collect-only -q products/tracker17/tests/e2e/`.
Run the exact whole-folder command twenty times, with verbose reporting solely to expose executed names:

```sh
for run in {1..20}; do
  if PYTEST_ADDOPTS=-v pytest products/tracker17/tests/e2e/ > "$proof_root/run-$run.log" 2>&1; then
    run_status=0
  else
    run_status=$?
  fi
  printf 'run %s exit %s\n' "$run" "$run_status" >> "$proof_root/exit-statuses.log"
  if [ "$run_status" -ne 0 ]; then
    cat "$proof_root/run-$run.log"
    break
  fi
done
cat "$proof_root/exit-statuses.log"
awk '$1 != "run" || $2 != NR || $3 != "exit" || $4 != "0" { failed=1 } END { exit (NR != 20 || failed) }' "$proof_root/exit-statuses.log"
```

Pass: twenty consecutive exit codes of 0 for the same committed SHA, each log showing all 27 names
executed and passed, without skip, xfail or deselection.
A failed or incomplete sequence does not meet I-3; retain its log and actual status.
The final log check must exit 0; it rejects a missing run, a changed run number or a nonzero status.
The additional verbosity changes reporting only; no repeated test attempt is added.
Preserve logs outside the product diff and cite their location and SHA in the implementation record.
The causal account must identify the failed tests, measured variation and why the repair removes it
in the fix's landing body and closing body, without prescribing how tasks are committed (I-7;
`tracker17 · shukuba · 2026-10-12_browser-suite-every-run`, Reached when 1).

## TL Review Notes

Decisions by Tech Lead, 2026-10-12:

- **Preserving shape adaptation:** retain the architect's in-place test-observation layout and make
  one task per edited module. No symbol moves or test additions are ordered because design § 3
  explicitly fixes every symbol at its existing home. Use the preserving invariant gate and literal
  `No new tests — TDD under green` marker, rather than inventing a new implementation lane.
- **Baseline precision:** carry only the three failure locations the spec actually reports, verbatim,
  on `Red at baseline:` lines. Map those locations to the unchanged functions by source reading
  (`tests/e2e/test_first_project.py:L158-L177`, the two hand-built tests;
  `tests/e2e/test_people.py:L142-L157`, the stale-remove test).
  Their baseline red is intermittent according to `change_spec.md:L47`, Verified Claims row 2.
  No red from another case is licensed. Task 1's interim whole-folder run can expose the named
  People failure before Task 2; that observation cannot count as a completed whole-folder proof.
- **Gate coverage:** keep the card command and add the separate browser command to each gate, because
  `tests/conftest.py:L33-L48`, `pytest_ignore_collect`, excludes e2e from the card invocation.
  Put the twenty-run archive procedure at change level because it measures both tasks together.
  No task consumes another task's code, so both dependencies are `None`.
- **Environment verification:** the sandboxed card command ended with `5 failed, 788 passed, 20 errors`,
  exit 1. A diagnostic command,
  `pytest products/tracker17/tests/integration/test_label_listener.py -q --tb=short`, showed
  `PermissionError: [Errno 1] Operation not permitted` at `socket.bind`, exit 1.
  With approved loopback access, the card command returned `813 passed in 31.23s`, exit 0.
  It ran with Python 3.14.7 and host pytest 9.0.3, as its actual session header states; it is not
  evidence of the locked pytest 9.1.1 environment in `pyproject.toml:L12-L18`, dev dependencies.
  The implementation gates therefore use the README's locked `.venv`; no card edit is ordered.
- **Review precision:** explicitly require source inventory comparison, negative focus diagnostics
  and raw status logs. These make design § 5 C5/C7/C8 falsifiable without adding committed tests.
  Add reporting-only verbosity to the twenty-run command so every executed name appears in its log;
  pytest documents this output option at https://docs.pytest.org/en/stable/how-to/output.html.
- **Observation ordering:** the narrow-width People assertion reads the outline before its focus
  snapshot (`tests/e2e/test_people.py:L185-L187`, `test_long_people_names_and_controls_reflow`).
  Put the bounded observation before that outline read as well, so the outline still measures the
  focused state. Also cover the final added-name outline after removal in the keyboard test
  (`tests/e2e/test_people.py:L135-L139`). This clarifies design § 5 C3/C4 without changing a target.
- **Language resolution:** Python is declared by `system/projects/tracker17/project.md:L12`, Languages.
  Step 1 of `core/doctrine/engineering/languages/README.md`, The resolution chain, answers.
  Opened `core/doctrine/engineering/languages/python/README.md` and its six routed concerns,
  including `core/doctrine/engineering/testing_python.md`; the product's records retain precedence.

- **Task 3 added after code-integrity stopped — owner-directed, 2026-10-12:** the design's § 2 now
  lists `test_labels.py` and `test_tasks.py` as modified, and its Architect Review Notes give the
  cause: a string predicate passed to `wait_for_function` is evaluated with `eval` on every poll,
  which the page's `script-src 'none'` refuses. One task covers both modules, because they share one
  edit and one cause.

### Task 1: Project answer-page focus observation (`tests/e2e/test_first_project.py`)

**Dependencies:** None

**What to build:** Repair native-focus observation in place at the existing project answer-page
assertions, per design § 3; preserve every helper, test, signature, action and expected target.

#### Invariant gate

- Full existing in-process suite green: `pytest products/tracker17/tests/`, from `change_root` (I-1).
- Red at baseline: `test_first_project.py:166` (`assert '' == 'name'`).
- Red at baseline: `test_first_project.py:177` (`assert '' == 'description'`).
- Those are the spec's verbatim baseline cases (`change_spec.md:L47`, Verified Claims row 2),
  mapped to `test_a_hand_built_201_character_name_gets_the_reason_and_none_of_the_text` and
  `test_a_hand_built_over_long_description_is_refused` by the unchanged source.
  They may pass on an unmodified baseline; after the repair they must pass on every proof run.
- `test_the_first_project_lands_on_its_page_with_spaces_line_break_and_created_line`:
  retain the `H1` snapshot, created line, form inventory, description and whitespace checks.
- `test_a_refused_name_puts_focus_in_the_name_field_with_the_reason_as_its_description`:
  retain focus on `name`, its reason/description and both entered values.
- The two hand-built tests retain focus on `name` and `description` respectively, the saved-byte
  check in `_hand_built`, discarded-text assertions and refusal reasons (I-5; design § 5 C1).
- Keep `focused_id` an immediate reader and every existing assertion intact.
- Negative diagnostics in disposable copies must still fail for wrong, absent or body focus,
  including form-control and `H1` targets (design § 5 C5).
- Keep production exports and `main.start` byte-identical (I-2).
  Keep docstrings, collaborator seams and all non-e2e tests unchanged (I-10/I-11).
- An unexpected new red is a reclassification event: stop and surface it; do not loosen a check.

#### Implement

Restructure per the § 3 Layout Plan in place; no symbol or test moves.
No new tests — TDD under green (baseline green, or red on exactly the named baseline cases →
observation repair → green; no red phase).

# Hint:
Use Playwright's bounded `to_be_focused` observation on the intended answer-page element before
retaining the original snapshot assertion. Bind observation to the completed destination navigation;
no focus-setting action is part of this observation (design § 4).
Keep the default 5,000-millisecond assertion bound; it checks a focused DOM node
(https://playwright.dev/python/docs/api/class-locatorassertions#locator-assertions-to-be-focused).
Add no timing constant, timeout increase, unconditional delay or repeated action.

#### Verification gate

From `change_root`, with the product `.venv` active:

```sh
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/test_first_project.py
pytest products/tracker17/tests/e2e/
```

Run the common compile/Ruff/mypy and diff checks as well.
Pass: 813 in-process tests and all 11 project browser tests pass; no new failure elsewhere.
Only the spec-named `test_people.py:157` baseline focus failure may remain before Task 2.
That interim result does not meet the final whole-folder gate.
The project negative diagnostics fail at the intended focus checks, and the causal evidence explains
the repair without treating a wait's success as proof of cause.

### Task 2: People answer-page focus observation (`tests/e2e/test_people.py`)

**Dependencies:** None

**What to build:** Repair native-focus observation in place at the existing People answer-page
assertions and shared added-name check, per design § 3; retain the keyboard sequence and snapshots.

#### Invariant gate

- Full existing in-process suite green: `pytest products/tracker17/tests/`, from `change_root` (I-1).
- Red at baseline: `test_people.py:157` (`assert '' == 'assignees-heading'`).
- That is the spec's verbatim baseline case (`change_spec.md:L47`, Verified Claims row 2), mapped
  to `test_a_stale_remove_focuses_the_heading_with_the_reason_and_a_reload_link` by the unchanged
  source. It may pass on an unmodified baseline; it must pass on every final proof run.
- `test_added_markup_name_has_browser_focus_and_accessible_description`: retain both added-name
  positions, text, accessible description, viewport and outcome-line non-focus checks, the next
  Remove Tab stop, saved data and history navigation assertions (I-5/I-8; design § 5 C2).
- `test_people_keyboard_refusals_and_removal_keep_focus_at_the_action`: retain blank and duplicate
  refusal focus on `assignee-name`, successful-add focus on `assignee-1`, `INPUT`, all eight
  immediate Tab snapshots, `tabIndex == -1`, empty-list heading focus and both outline checks
  (I-5/I-8; design § 5 C3).
- `test_a_stale_remove_focuses_the_heading_with_the_reason_and_a_reload_link`: retain both tabs,
  saved bytes, `assignees-heading` focus, accessible reason and reload-link checks (design § 5 C4).
- `test_long_people_names_and_controls_reflow`: retain `assignee-4` focus, its outline and all
  overflow and control bounds, including the outline read's observation order (design § 5 C4).
- Keep `focused_id` and `focused_tag` immediate. A wait in either would change what every Tab
  snapshot observes; preserve the separate post-navigation boundary (design § 4).
- The existing intentional setup focus and blur actions stay in their existing positions.
  No added action may establish the focus being asserted.
- Negative diagnostics must still fail on a refused-name control and a focusable non-control
  answer in disposable copies, without adding a test function (design § 5 C5).
- Public surfaces, fixture/helper signatures, docstrings, dependencies and other modules are
  unchanged (I-2/I-4/I-10/I-11/I-12).
- An unexpected new red is a reclassification event: stop and surface it; do not loosen a check.

#### Implement

Restructure per the § 3 Layout Plan in place; no symbol or test moves.
No new tests — TDD under green (baseline green, or red on exactly the named baseline case →
observation repair → green; no red phase).

# Hint:
Use the same Playwright observation boundary after navigation, including once in
`assert_added_name_is_focused` before its snapshot. Keep `focused_id` and `focused_tag` as immediate
readers so the Tab-stop inventory continues to record each key's result (design § 4).
Observe the intended target before any following outline, viewport or keyboard observation.
Keep the default finite bound and the single existing action.

#### Verification gate

From `change_root`, with the product `.venv` active:

```sh
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/test_people.py
pytest products/tracker17/tests/e2e/
```

Run the common compile/Ruff/mypy and diff checks as well.
Pass: 813 in-process tests, all six People tests and all 27 whole-folder tests pass with no skipped
case or new failure. The People negative diagnostics fail at their intended focus checks.
After both tasks, complete the change-level twenty-run committed-archive proof and preserve its
actual logs and causal account. No individual module run substitutes for that proof.

### Task 3: Label and task focus waits (`tests/e2e/test_labels.py`, `tests/e2e/test_tasks.py`)

**Dependencies:** None

**What to build:** Replace each of the 13 string-predicate focus waits with `to_be_focused` on the
same element, per design § 4: ten in `test_labels.py` (L34, L60, L70, L86, L94, L102, L108, L134,
L142, L159) and three in `test_tasks.py` (L67, L153, L163), as they stand at `7ba95e221`.

#### Invariant gate

- Full existing in-process suite green: `pytest products/tracker17/tests/`, from `change_root` (I-1).
- Red at baseline: `test_labels.py::test_keyboard_label_add_focuses_label_with_accessible_description`
  (`Page.wait_for_function: EvalError`), whole-folder run 15 of `code-integrity-report.md` at
  `486d5dbae`. It is intermittent; after the repair it must pass on every proof run.
- Every target stays the same: `H1` reads as `main h1`, the page's only heading, and an id reads as
  `#<id>`. The `other` page in the stale-remove test keeps its own observation.
- No wait, focus or key action is added. The default 5,000-millisecond bound is kept.
- No `wait_for_function` remains under `tests/e2e/`.
- Test names, docstrings, helpers and their signatures are unchanged (I-4, I-10, I-11).
- An unexpected new red is a reclassification event: stop and surface it; do not loosen a check.

#### Implement

No new tests — TDD under green (baseline green, or red on exactly the named baseline case →
observation repair → green; no red phase).

#### Verification gate

From `change_root`, with the product `.venv` active:

```sh
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/
grep -rn wait_for_function products/tracker17/tests/e2e/
```

Run the common compile/Ruff/mypy and diff checks as well.
Pass: 813 in-process tests and all 27 whole-folder tests pass, and the grep prints nothing.
Then the change-level twenty-run committed-archive proof, as after Task 2.
