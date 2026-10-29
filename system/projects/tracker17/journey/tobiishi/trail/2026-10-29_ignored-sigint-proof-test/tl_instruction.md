# Tech Lead instruction — ignored-sigint-proof-test: guard the test launch condition

**Category:** bug
**Behaviour:** preserving
**Product root:** products/tracker17 — code paths below are relative to it unless stated otherwise.
**Scope:** Add the one characterization test named below and reflow the shared test file's opening
paragraph, per `tracker17 · tobiishi · 2026-10-29_ignored-sigint-proof-test`, `change_spec.md`
§ Structural Goal and `change_design.md` § 3 Layout Plan.

This instruction owns the task cut and the commands that verify each deliverable. The spec owns
the invariants; the design owns the two-file layout and the child-process boundary.
The instruction's home is the change folder, per `<CORE>/doctrine/setup/kensaiapp_structure.md`
§ 2, “Per-project — `system/projects/<name>/`”, `journey/tobiishi/<key>/`.

---

## Project layout

```text
products/tracker17/
  tests/
    conftest.py                         ← modified: opening paragraph's line breaks only
    integration/
      test_sigint_launch.py             ← new: one characterization test
```

No directory or `__init__.py` needs creation: both parent directories exist in the tracked product
inventory (`git -C products/tracker17 ls-files`, 274 paths). Production placement stays at
`docs/SDD.md` § 3, “The parts, and the seams between them”; imports stay within `docs/nfdr.md`
§ 1.2, “Forbidden imports”. Neither task introduces production logic or a production import edge.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "Read git -C products/tracker17 ls-files: 274 tracked paths; top-level names .gitignore, README.md, application, docs, domain, errors.py, main.py, persistence, pyproject.toml, tests, web. No workflow, runner or build-service configuration occurs in that inventory. Filtering the inventory for .yml, .yaml, .sh, Makefile, Jenkinsfile, Dockerfile, tox.ini and noxfile.py returned []. Repository-level git ls-files for .github/*, .gitlab*, *Jenkins*, *jenkins*, *azure*, *circleci*, *buildkite*, *travis*, *drone*, *ci*.yml and *ci*.yaml returned no paths."
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

## TL Review Notes

Decisions made by the Tech Lead on 2026-10-29:

- **Task shape:** Task 1 uses the sanctioned already-green marker because the requested test pins
  the existing `_interruptible_test_session`, rather than a new product behaviour
  (`tests/conftest.py:L62-L82`, `_interruptible_test_session`). The selected real-start case passed
  before any edit, both normally (`pytest` with the exact node below: `1 passed in 5.58s`) and
  with ignored SIGINT (`sh -c 'trap "" INT; exec pytest …'`: `1 passed in 5.89s`). A historical
  counterexample is required evidence, not a red phase against this branch. This applies the shared
  planning prompt's “already-green shape” to the design's characterization-only addition; a
  relocation block would incorrectly forbid the test the spec requires.
- **Task shape:** Task 2 is verified by review. Its only deliverable is line wrapping, so it adds no
  test. The diff and docstring-word comparison are the falsifiable checks in design § 5 C6.
- **Gate command:** The card's command is `pytest products/tracker17/tests/`, from the instance
  worktree root (`system/projects/tracker17/project.md`, `Test command:`). It collected 2,651
  tests in this planning run. The spec's claims use `python -m pytest … -q`, so every task gate
  below names that invocation as well. The two browser-suite invocations remain separate.
- **Execution conditions:** A sandboxed loopback bind failed with
  `PermissionError: [Errno 1] Operation not permitted` during diagnosis. The sandboxed card run
  exited 1 with `20 failed, 2600 passed, 31 errors in 293.82s`; it is not evidence of a green
  product baseline. The two
  successful selected-case checks above ran with command approval. Socket access is a prerequisite
  for these real-start checks, not grounds to alter a product test.
- **Interpreter preparation:** Bare `python -m pytest` exited 127 here because pyenv selected an
  unavailable `3.14`. `python3` reported `/opt/homebrew/opt/python@3.15/bin/python3.15`; the card's
  `pytest` used Python 3.15.0. The clone recipes use the product's documented virtual-environment
  setup (`README.md`, “Running the tests”), so `python` and `pytest` refer to the same interpreter
  and the pinned test tools. No interpreter floor or project card changes are part of this plan.
- **One-change checks:** Historical checkout, unchanged-file review and docstring comparison stay
  in the task gates. The committed test performs none of them, per design § 5 C2/C5/C6 and
  `<CORE>/doctrine/engineering/testing_doctrine.md` § “A test reads nothing of the machine it runs on”.

### Task 1: Characterize the fixture through the real start (`tests/integration/test_sigint_launch.py`)

**Dependencies:** None

**What to build:** Exactly one test,
`test_real_start_stops_when_pytest_launch_ignores_sigint`, in the module fixed by design § 3.
Its opening docstring names SRS NFR-11 and explains the launch condition it checks, per
`docs/nfdr.md:L146-L157`, QC-11, and `docs/SDD.md` § 4 TS-2/TS-3.

#### Behaviours to verify

- `test_real_start_stops_when_pytest_launch_ignores_sigint` — from a product root derived from
  the test file, start `/bin/sh` with INT ignored, then exec the current interpreter into pytest.
  Pass executable and pytest arguments positionally, per design § 3. Select exactly
  `tests/integration/test_start.py::test_start_reads_each_legacy_form_with_every_existing_value[projects-only]`.
  Require child exit 0 and a positive result that exactly one case passed. Capture both output
  channels for a failed assertion. The outer test's deadline exceeds the selected case's
  30-second stop deadline, and children are reaped on failure. The tracker is the real `main.start`
  in the selected case's child process, stopped by the real SIGINT that case sends
  (`tests/integration/test_start.py:L516-L563`, `_run_real_start` and its selected caller).

#### Held by review

- The test neither imports the fixture by name nor resets a handler in the subject. It uses no
  `preexec_fn`, product-name patch or substitute tracker, per design §§ 3–4.
- The selected node excludes the proof module, preventing recursion, per design § 3 item 3.
- Exactly one test is added. Existing test bodies, assertions, skip/xfail status, fixture code and
  collection rules stay unchanged, per spec § Invariants and § Out of Scope.
- No Git history, historical SHA, checkout operation, private checkout or machine-owned data is
  read by the lasting test. The historical proof below is external validation, per design § 5 C2.

#### Implement

Tests cannot go red.

Reason: The session fixture already normalizes the ignored launch before the selected case runs
(`tests/conftest.py:L62-L82`, `_interruptible_test_session`); the two approved pre-edit case runs
recorded in TL Review Notes passed. Production behaviour and the fixture are outside this task.

# Hint:
Use an ignored-INT shell launch of one explicit pytest node, under the current interpreter, with a
bounded captured result. The extra pytest process is essential: the outer fixture has already
normalized SIGINT, so directly starting another tracker from the outer test would not recreate the
defect. No fixture-name import, handler replacement in the subject, or `preexec_fn` is needed.

#### Verification gate

From the instance change worktree root, with the product's test environment active:

```sh
python -m pytest products/tracker17/tests/ -q
python -m pytest 'products/tracker17/tests/integration/test_sigint_launch.py::test_real_start_stops_when_pytest_launch_ignores_sigint' -q
sh -c 'trap "" INT; exec python -m pytest "products/tracker17/tests/integration/test_sigint_launch.py::test_real_start_stops_when_pytest_launch_ignores_sigint" -q'
```

Pass: the suite has no new failures; each focused run reports exactly one passing test and exits 0.
Collection of the first suite includes the new node exactly once. Check with
`python -m pytest products/tracker17/tests/ --collect-only -q`; compare the listing with the
pre-edit collection, with one addition and no removals. This is a change-local review, not another
test to commit. An existing test going red is a preserving-change halt, not a test to weaken.

The historical counterexample is also mandatory. From the instance change worktree root, create a
fresh disposable clone and add only the new module:

```sh
PROOF_WORKTREE=$(git rev-parse --show-toplevel)
PROOF_SCRATCH=$(mktemp -d)
git clone --quiet "$PROOF_WORKTREE" "$PROOF_SCRATCH/historical"
git -C "$PROOF_SCRATCH/historical" checkout --quiet 970f6a4ca04b93093d36873737a1087286a9a844
cp "$PROOF_WORKTREE/products/tracker17/tests/integration/test_sigint_launch.py" "$PROOF_SCRATCH/historical/products/tracker17/tests/integration/test_sigint_launch.py"
python3 -m venv "$PROOF_SCRATCH/historical/products/tracker17/.venv"
"$PROOF_SCRATCH/historical/products/tracker17/.venv/bin/python" -m pip install -r "$PROOF_SCRATCH/historical/products/tracker17/tests/requirements.txt"
(
  cd "$PROOF_SCRATCH/historical"
  products/tracker17/.venv/bin/python -m pytest 'products/tracker17/tests/integration/test_sigint_launch.py::test_real_start_stops_when_pytest_launch_ignores_sigint' -q
)
git -C "$PROOF_SCRATCH/historical" diff --exit-code -- products/tracker17
git -C "$PROOF_SCRATCH/historical" ls-files --others --exclude-standard -- products/tracker17
```

Pass for this negative check: the pytest run exits 1 because the selected legacy case reports its
tracker-stop `subprocess.TimeoutExpired`, or otherwise shows that the tracker remained running after
SIGINT. An outer timeout, import/setup/collection failure or skipped case does not qualify.
Inspect the captured inner report and preserve the actual command, status and relevant failure
output in the review record. The final diff is empty; the untracked listing names only the copied
proof module. No historical conftest or product code was edited. Run cleanup from outside the clone,
as its own command: `rm -rf "$PROOF_SCRATCH"`.

The final committed tree must also meet all four suite launches in Task 2's resulting-commit gate.
That gate is change-wide evidence, not a dependency of Task 2 on Task 1's code.

### Task 2: Reflow the opening paragraph (`tests/conftest.py`)

**Dependencies:** None

**What to build:** Change only the opening paragraph's first line break, retaining every word in
order, as fixed by design § 3 “The shared docstring”. The pre-edit first line measured 101 columns
(`python3` reading `tests/conftest.py` and printing its first-line length: `101`).

#### Deliverables verified by review

- First line at most 100 columns: measure its length. The opening docstring's whitespace-split
  word list equals the merge-base version's word list, per spec § Structural Goal, “The reflow”.
- Only the first two docstring lines change in `tests/conftest.py`. All text after the opening
  paragraph, including imports, fixture bodies and collection code, is byte-identical to the
  merge-base version, per design § 3 “The shared docstring”.
- Outside the two paths in Project layout the product diff is empty. Review from the instance
  worktree root with the commands below, checking the branch's merge base rather than a fixed
  historic revision:

  ```sh
  git diff "$(git merge-base main HEAD)" -- products/tracker17 ':!products/tracker17/tests/conftest.py' ':!products/tracker17/tests/integration/test_sigint_launch.py'
  git diff "$(git merge-base main HEAD)" -- products/tracker17/tests/conftest.py
  git diff --no-index /dev/null products/tracker17/tests/integration/test_sigint_launch.py
  ```

  Pass: the first diff is empty; the second changes the allowed line breaks only; the third shows
  exactly one test definition and its local scaffolding. The last command normally exits 1 because
  it displays a new file; inspect the diff rather than treating that status as a failed suite.
  These checks also hold the no-document-edit and public-interface invariants in spec § Invariants.

#### Implement

Verified by review — no test.

#### Verification gate

From the instance worktree root with the test environment active, run
`python -m pytest products/tracker17/tests/ -q`.
Pass: every review criterion above holds and the suite has no new failures.

The resulting commit is also checked in a fresh clone, as spec § Request and design § 5 C3/C8
require. From the instance change worktree root:

```sh
VERIFY_WORKTREE=$(git rev-parse --show-toplevel)
VERIFY_REVISION=$(git rev-parse HEAD)
VERIFY_SCRATCH=$(mktemp -d)
git clone --quiet "$VERIFY_WORKTREE" "$VERIFY_SCRATCH/current"
git -C "$VERIFY_SCRATCH/current" checkout --quiet "$VERIFY_REVISION"
python3 -m venv "$VERIFY_SCRATCH/current/products/tracker17/.venv"
"$VERIFY_SCRATCH/current/products/tracker17/.venv/bin/python" -m pip install -r "$VERIFY_SCRATCH/current/products/tracker17/tests/requirements.txt"
"$VERIFY_SCRATCH/current/products/tracker17/.venv/bin/python" -m playwright install chromium
(
  cd "$VERIFY_SCRATCH/current"
  . products/tracker17/.venv/bin/activate
  python -m pytest products/tracker17/tests/ -q
  sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/ -q'
  python -m pytest products/tracker17/tests/e2e/ -q
  sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/e2e/ -q'
)
(
  cd "$VERIFY_SCRATCH/current/products/tracker17"
  . .venv/bin/activate
  python -m compileall -q main.py errors.py domain application persistence web tests
  ruff format --check .
  ruff check .
  mypy main.py errors.py domain application persistence web
)
```

Record each command's own exit status and output; a later passing command does not erase an
earlier failure. Pass: all four suites and each quality command exit 0, with no new skip or xfail.
The proof passes in both first-suite launches; the foreground run keeps the real-start operator-stop
assertions, saved-byte checks and directory-listing checks unchanged (design § 5 C1/C3/C4/C7).
The browser suites remain separate and exercise their existing cases unchanged. The compile check
is the Python packet's additional gate (`quality_gates.md`, “The two gates”); Ruff and mypy are
QC-62's commands (`docs/nfdr.md:L532-L545`).

On Linux the product's documented browser preparation is
`python -m playwright install --with-deps chromium` in place of the browser-install command
above (`README.md`, “Running the tests”). Run no product checks in the main checkout.
Remove the disposable clone from outside it, as a separate command: `rm -rf "$VERIFY_SCRATCH"`.

The closing card-suite gate follows `<CORE>/prompts/gate_suite.md`, using this plan's Gate environment
inputs. The clone checks above supply the additional change-specific evidence and do not replace
the card-suite gate's own environment record.
