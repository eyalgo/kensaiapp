# Tech Lead instruction — start tests under ignored SIGINT

**Category:** bug
**Behaviour:** preserving
**Product root:** products/tracker17 — code paths below are relative to this folder; command blocks name their working directory.
**Scope:** Repair pytest's launch conditions and full-suite selection, with the isolated characterization proof specified by `tracker17 · tobiishi · 2026-10-29_start-tests-under-ignored-sigint`, `change_design.md` § 3.

This instruction owns the implementation tasks and their gates. Read the same change's `change_spec.md` § Invariants for the characterization contract and `change_design.md` § 3 Layout Plan for the binding placement decisions.

## Project layout

```text
products/tracker17/
  tests/
    conftest.py                 ← modified: session signal fixture and collection hook
    integration/
      test_start.py             ← modified: one characterization proof
```

Create no directory, module or `__init__.py`. The five production parts and `errors.py` retain the graph in `docs/nfdr.md:L166-L199`, § 1.2 Forbidden imports: `domain` may import `errors` and the standard library; `application` and `persistence` may import `domain` and `errors`; `web` may import `application` and `errors`; `main` may import all four and `errors`; `errors` imports no product part. Preserve every forbidden edge in that section, including production imports of tests or third-party packages. The owning parts are `docs/SDD.md:L202-L238`, § 3 The parts, and the seams between them; pytest lifecycle and selection stay in test support.

## TL Review Notes

Decisions below are the Tech Lead's, 2026-10-29.

- **Preserving repair and characterization:** keep the input classification. Use structural tasks with `#### Invariant gate`, not a new-product-behaviour lane. The preserving marker's “No new tests” excludes tests of new product behaviour here; the one required characterization proof remains included because `<CORE>/doctrine/flow/change_classification.md` § Constraints explicitly states “Adding characterization tests is always in scope for a `preserving` change.” The same doctrine's preserving mechanism has no red phase. The proof's failure on the branch's starting tree is a separate historical acceptance check, not a reason to change that mechanism.
- **Task cut:** use one task per affected test-support unit in `change_design.md` § 3. Repair the shared harness before adding its permanent proof so the proof enters a working harness. Neither task consumes a new interface or file from the other; ordering is not an import dependency. Both therefore retain `Dependencies: None` as the preserving shape requires.
- **Historical proof command:** replay the proof against a fresh clone at the branch's merge base with only the proof-bearing module copied over. This supplies the spec's starting-tree demonstration without putting a fixed revision assertion into the permanent suite or modifying the shared checkout.
- **Gate invocation:** the card's `pytest products/tracker17/tests/` differs from the spec's measured `python -m pytest products/tracker17/tests/ -q`. Use the spec's two exact commands in both gates, with the product's locked environment active. The card probe in this run exited 1 with `20 failed, 2600 passed, 31 errors in 269.00s`, having collected 2651 items and no end-to-end modules. That is not a valid acceptance baseline: a separate `python3` loopback-bind probe raised `PermissionError: [Errno 1] Operation not permitted`; the available interpreter reported `pytest=9.1.1`, `pluggy=1.7.0`, and no `playwright` distribution. The lock instead fixes `pluggy==1.6.0` and `playwright==1.63.0` (`tests/requirements.txt:L12-L13`, exact pins). A bare `python` also exited 127 through pyenv, saying the worktree's `3.14` version was not installed. None of these observations establishes an additional product defect or a SIGINT timeout.
- **Collection edges:** add equivalent absolute and trailing-slash directory arguments to the isolated collection checks. Add outer integration-directory and single-node exclusions, and the no-argument default from the product directory. These sharpen `change_design.md` § 3 Collection boundary without widening it: only an explicit whole-test-directory argument from outside the product gains browser collection. Check actual collected node IDs rather than parsing a green exit or assuming a total.
- **Failure restoration:** carry `change_design.md` § 5 T6's unsuccessful-session restoration as a review-held invariant. The required successful nested run proves restoration on normal return. Review the fixture's finalization path for a failing session rather than adding a second permanent test or altering an existing assertion.
- **Corrections:** update the opening description in `tests/conftest.py:L1-L14`, the module docstring, alongside its new session duty. Also carry the command-equivalence sentence in `docs/nfdr.md` § 10 as owed outside this change: the outer command's new browser coverage makes that equivalence false even though the product-local split remains intact. This is the addition to the design's zero-form records sweep.
- **Language resolution:** Python, step 1 from the project card's `Languages: Python`; opened `<CORE>/doctrine/engineering/languages/python/README.md` and its seven routed concerns. Product decisions retain their Python 3.11 floor and QC-62 commands (`docs/nfdr.md:L516-L548`, QC-59, QC-60 and QC-62).

## Corrections owed while there

- Owed outside this change's reach: `products/tracker17/docs/nfdr.md:L597-L601`, § 10 Verification map — “typed from the product root ... that command is `pytest tests/`” equates the card's outer full-suite command with the local command → distinguish the outer explicit full-suite invocation, which includes browser tests, from product-local `pytest tests/`, which continues to exclude them; retain the local `pytest tests/e2e/` command. This change reads that record and does not edit it.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "From the product's instance worktree, git ls-files | rg '(^|/)(\\.github/|\\.gitlab-ci|azure-pipelines|Jenkinsfile|\\.circleci/|\\.buildkite/|\\.woodpecker|\\.travis|buildspec|bitbucket-pipelines|Taskfile|Makefile|Containerfile|Dockerfile|justfile|\\.python-version)' returned only .python-version and Containerfile. Read Containerfile in full: it builds the coding-agent image and executes the supplied command, with no product CI runner or included pipeline configuration. The tracked product files contain no CI configuration."
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

No candidate tag is inferred from the instance's Python pin or the product's supported floor. No recorded environment override or amd64 requirement was found by reading the product's ADR decisions, `docs/nfdr.md` § 8 and `docs/SDD.md` § 3; the environment is resolved from the sourced inputs by the gate tool, per `<CORE>/prompts/gate_suite.md` § Step 3 — read the evidence.

### Task 1: Repair shared pytest launch conditions (`tests/conftest.py`)

**Dependencies:** None

**What to build:** Keep the existing test-support unit and its symbols in place. Add `_interruptible_test_session`, the private autouse session fixture; extend `pytest_ignore_collect` for the outer whole-directory case. Retain `_command_line_names_end_to_end`'s signature and explicit end-to-end selection. Preserve the import shim and source-walk code (`tests/conftest.py:L27-L48`, collection constants and hooks; `SourceWalk` and `walk_of`).

#### Invariant gate

- The twelve real-start cases still call the real child-process start and retain all assertions, saved-data checks and timeout bounds (`tests/integration/test_start.py:L516-L588,L680-L758`, `_run_real_start` and its four callers).
- Red at baseline: `test_start_reads_each_legacy_form_with_every_existing_value` — its three cases under ignored SIGINT only, as named in `change_spec.md` § Verified Claims.
- Red at baseline: `test_start_reads_valid_unset_boundary_and_surrounded_name` — its three cases under ignored SIGINT only, from the same spec section.
- Red at baseline: `test_saved_comment_boundaries_and_historical_authors_load` — its two cases under ignored SIGINT only, from the same spec section.
- Red at baseline: `test_every_supported_saved_form_keeps_all_existing_values` — its four cases under ignored SIGINT only, from the same spec section.
- The shared fixture saves and restores the exact incoming handler, including `SIG_IGN` and a callable handler. Its active lifetime encloses setup and teardown of test-launched subprocess fixtures; signal setup runs in the main thread. This is the binding boundary in `change_design.md` § 3 Signal boundary, supported by [Python's signal rules](https://docs.python.org/3.11/library/signal.html) and [pytest's autouse ordering](https://docs.pytest.org/en/stable/reference/fixtures.html#autouse-fixtures-are-executed-first-within-their-scope).
- An outer explicit whole-directory argument admits nonempty `unit`, `integration`, `e2e` and `architecture` node sets. Equivalent resolved paths have the same selection; an integration directory or integration node alone admits no browser node. Product-local `tests/` and no arguments retain the browser exclusion; explicitly selecting `tests/e2e/` retains browser inclusion. Inspect collection with the commands below, and retain the collected node IDs.
- Foreground suite green, and all four named baseline-red families green under ignored SIGINT, with no additional failures; an unexpected existing-test failure is a STOP for investigation, never permission to weaken an assertion.

#### Held by review

- On unsuccessful sessions the fixture restores the saved handler during teardown, with no permanent module-import handler change. Review the finalization path; no second permanent proof is added for this branch (`change_design.md` § 5 T6).
- Update the module docstring's duties and selection description to match this unit's signal lifetime and outer-versus-local distinction. This correction rides Task 1 because it already edits `tests/conftest.py`.
- Production behaviour, public imports and entry signatures remain identical. Review the branch diff using the merge-base command below; no product code is edited (`change_spec.md` § Invariants).

#### Implement

Restructure test support per `change_design.md` § 3 Layout Plan, retaining the mapped files and existing assertions. **No new tests — TDD under green** (foreground baseline green, or ignored-SIGINT baseline red on exactly the four named families → harness repair → green; no red phase).

```text
# Hint:
Use a session autouse fixture with `signal.default_int_handler`, retaining the previous handler for teardown. Do the setup in pytest's main thread. The collection seam is `config.invocation_params.dir` together with explicit arguments resolved to `TESTS_DIRECTORY`; preserve the product-local exclusion (`change_design.md` § 4 Code Strategy).
```

#### Verification gate

Use the locked test environment prepared by `README.md:L91-L105`, § Running the tests, including its installed Chromium. Activate that environment for every command; from the change worktree root the activation is `source products/tracker17/.venv/bin/activate`. The gate requires permission to bind loopback sockets; the restricted planning-run probe recorded above is not its baseline.

From the change worktree root:

```sh
python -m pytest products/tracker17/tests/ --collect-only -q
python -m pytest "$(pwd)/products/tracker17/tests/" --collect-only -q
python -m pytest products/tracker17/tests/integration/ --collect-only -q
python -m pytest 'products/tracker17/tests/integration/test_start.py::test_every_supported_saved_form_keeps_all_existing_values[current]' --collect-only -q
python -m pytest products/tracker17/tests/e2e/ --collect-only -q
python -m pytest products/tracker17/tests/ -q
sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/ -q'
git diff "$(git merge-base main HEAD)" -- products/tracker17/main.py products/tracker17/errors.py products/tracker17/domain/ products/tracker17/application/ products/tracker17/persistence/ products/tracker17/web/ products/tracker17/docs/ products/tracker17/README.md
```

From the product root, with the same environment active:

```sh
python -m pytest tests/ --collect-only -q
python -m pytest --collect-only -q
python -m pytest tests/e2e/ --collect-only -q
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: every collection selection matches the invariant above; both executed full-suite commands exit 0 with all four folders represented, no skip or expected failure, and no start timeout. The production/document diff is empty. All three QC-62 commands exit 0. Review the test-support diff against `git diff "$(git merge-base main HEAD)" -- products/tracker17/tests/conftest.py`; the import shim, source walk and explicit end-to-end selector contract are preserved.

### Task 2: Add the isolated launch characterization (`tests/integration/test_start.py`)

**Dependencies:** None

**What to build:** Add exactly `test_real_start_stops_when_pytest_inherits_ignored_sigint` in the existing requirement-naming module. It owns the isolated driver and collection evidence in `change_design.md` § 3 Regression boundary and § 5 T2–T3. Leave `_run_real_start`, `RUN_START`, every existing test body and every parametrization intact.

#### Invariant gate

- The new proof starts its driver with `sys.executable`, deliberately sets and checks `SIG_IGN` before pytest begins, and selects only `test_every_supported_saved_form_keeps_all_existing_values[current]`. Assert that exactly that one case executes successfully, with no skip or expected failure, and that `SIG_IGN` is restored after pytest returns. The nested selection never includes the new proof, so it cannot recurse (`change_design.md` § 3 Regression boundary).
- Signal execution and restoration checks precede collection checks, so an ignored-SIGINT baseline failure comes from the existing stop wait, not the collection assertion (`change_design.md` § 5 T2–T3).
- Within the same proof, use separate collection-only processes to assert Task 1's outer-whole-directory, local-default, local-whole-directory, explicit-e2e and integration-only boundaries. Compare actual collected IDs and require nonempty expected folder sets; the single-node control collects exactly its selected node. Collection-only processes do not execute the collected proof. The absolute-path and trailing-slash controls guard path normalization (`TL Review Notes`, Collection edges).
- The selected case retains its real startup, SIGINT stop, zero status, empty stderr, saved values, byte-preservation and unchanged listing assertions (`tests/integration/test_start.py:L730-L758`, `test_every_supported_saved_form_keeps_all_existing_values`). The driver does not patch a product name or alter the real-start program.
- Give the added proof a docstring naming FR-1 and the saved-data requirements the existing module names; retain the module's requirement trace. The architecture pointer tests and full suite must pass (`docs/nfdr.md:L144-L157`, QC-11; `tests/integration/test_start.py:L1-L10`, opening docstring).
- The foreground existing suite remains green when this characterization is added. The ignored-SIGINT run is green too, including the new proof and all twelve existing real-start cases. Unexpected existing-test failures are STOP conditions rather than assertion edits.

#### Held by review

- Demonstrate the new proof's failure against the branch's starting product tree in a disposable Git clone, copying only the proof-bearing `tests/integration/test_start.py` into that tree and leaving the original shared harness intact. Derive the starting tree from the branch's merge base rather than pinning a SHA in a permanent test. The observed failure must identify the selected case's existing `communicate(timeout=30)` stop timeout; missing dependencies, denied sockets, collection failures and an enclosing-driver timeout do not count (`change_spec.md` § Structural Goal, The proof). This is change-level evidence, not a permanent test against history and not a red implementation phase.
- Subprocess waits are bounded, expose captured output on failure, and reap their processes. An enclosing bound must permit the existing 30-second stop failure to report itself; do not change the existing helper's wait or cleanup (`change_design.md` § 3 Regression boundary).
- Review the merge-base diff of `tests/integration/test_start.py`: only the new characterization and its supporting test code are added. Existing helpers, assertions, parameter values and IDs remain unchanged. Do not create a permanent test asserting an immutable historical file or total.

#### Implement

Restructure test coverage per `change_design.md` § 3 Layout Plan, adding only its characterization of the preserved contract. **No new tests — TDD under green** (no tests of new product behaviour; existing suite green → add the permitted characterization → green; no red phase).

```text
# Hint:
Use an isolated Python driver that sets `SIG_IGN` before `pytest.main` and selects one existing parametrized real-start node. Assert the incoming and restored dispositions in that driver. Invoke subprocesses with argument lists and the same interpreter; keep the existing timeout and kill/reap behavior (`change_design.md` § 4 Code Strategy).
```

#### Verification gate

Use the same locked environment, installed browser and working-directory conventions as Task 1.

From the change worktree root:

```sh
python -m pytest products/tracker17/tests/integration/test_start.py -q
sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/integration/test_start.py -q'
python -m pytest products/tracker17/tests/architecture/test_trace.py -q
python -m pytest products/tracker17/tests/ -q
sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/ -q'
git diff "$(git merge-base main HEAD)" -- products/tracker17/tests/integration/test_start.py
git diff "$(git merge-base main HEAD)" -- products/tracker17/main.py products/tracker17/errors.py products/tracker17/domain/ products/tracker17/application/ products/tracker17/persistence/ products/tracker17/web/ products/tracker17/docs/ products/tracker17/README.md
git diff --name-only "$(git merge-base main HEAD)" -- products/tracker17/ ':!products/tracker17/tests/conftest.py' ':!products/tracker17/tests/integration/test_start.py'
```

From the product root:

```sh
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: every test command exits 0 without skips, expected failures or start timeouts; collection evidence confirms all four folders in both full runs. The trace and QC-62 checks pass. Review confirms no existing assertion, case, helper signature or timeout changed. The final two diff commands print nothing. Keep the disposable-clone proof's starting revision, invocation, output and timeout verdict in Developer Review Notes as the historical evidence required above.

For the historical proof, from the change worktree root with its locked environment still active, run the following commands separately. The clone uses the same test dependencies through the active environment; it does not install into or test the primary checkout.

```sh
PROOF_START=$(git merge-base main HEAD)
PROOF_COPY=$(mktemp -d)
git clone --quiet --no-hardlinks . "$PROOF_COPY"
git -C "$PROOF_COPY" checkout --quiet "$PROOF_START"
cp products/tracker17/tests/integration/test_start.py "$PROOF_COPY/products/tracker17/tests/integration/test_start.py"
(cd "$PROOF_COPY" && python -m pytest products/tracker17/tests/integration/test_start.py::test_real_start_stops_when_pytest_inherits_ignored_sigint -q)
```

Expected: exit 1, with the selected saved-form case's 30-second SIGINT stop timeout visible in the proof's failure output. Read and retain that output before removing the disposable clone from the unchanged outer working directory:

```sh
rm -rf "$PROOF_COPY"
```
