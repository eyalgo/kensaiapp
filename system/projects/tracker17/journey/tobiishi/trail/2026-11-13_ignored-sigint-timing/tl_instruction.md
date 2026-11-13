# Tech Lead instruction — ignored-sigint-timing: the ignored-SIGINT proof test holds in a full run

**Category:** bug
**Behaviour:** preserving
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with every concern file it routes (`toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md`, and `<CORE>/doctrine/engineering/testing_python.md`)
**Product root:** `products/tracker17` — every path below is relative to it, except the test command and the merge-base checks, which run from the change worktree root.
**Scope:** The proof test's launched pytest gets a base folder of its own, so it no longer makes or cleans a numbered session folder in the machine's shared temp root, and one new layer-2 test measures that dependence by its effect. No product module, public name or wait limit changes.

---

## Project layout

```
products/tracker17/
  tests/
    integration/
      test_sigint_launch.py              ← modified (test setup only)
      test_sigint_launch_temp_root.py    ← new (the measurement; no __init__.py — tests/integration/ has none)
```

No product module (`domain/`, `application/`, `persistence/`, `web/`, `main.py`, `errors.py`) changes, and no `__init__.py` is touched. `tests/integration/test_start.py`, `tests/conftest.py` and `tests/architecture/test_trace.py` stay unchanged.

No parts table entry covers test code — placement follows `change_design.md §2`.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **Task merge (the design's two files are one task):** §3 lists the measurement and the proof-test setup as two units with no build sequence. Planned apart, the first task would add a test that is red at its base and nothing in that task turns it green, so the suite stays red until the second task lands. The measurement and the setup change are one responsibility (remove the proof test's dependence on the shared temp root), so Task 1 carries both files, test-first: the red is the measurement, the green is the setup change.
- **Behaviour added:** the proof test's own assertions are listed in Task 1 as the existing behaviour that must keep passing (`launch.returncode == 0`, one `ONE_CASE_PASSED` line, same `SELECTED_CASE`), so the green phase cannot weaken I-3. They are existing tests; no new test is written for them.
- **Layer and fakes carried:** §5 gives layer 2 and "none: real pytest processes" for the measurement. Carried onto the behaviour line as written.
- **One-change checks moved out of the suite (Task 2):** `change_design.md §5` lists I-2 (no product file changes), I-5 (no wait limit raised, no skip, retry or xfail added) and the I-3 "assertions unchanged" reading as coverage by invariant. Each is true only while this change is built, and written as a suite test would assert a fixed commit after the seal. They are Task 2, a review-verified deliverable, each with a command checked against the branch's merge base.
- **Hint carried, tightened:** the §4 hint for the measurement is carried as the approach. Its step (6), the docstring constraints, stays as a plain constraint because `tests/architecture/test_trace.py` resolves every path-shaped token in a docstring.
- **Gate:** the card's `Test command:` was checked: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/ --collect-only -q` collects 3337 tests and `…/tests/e2e/` collects 122, so both commands of it run what the spec measured. Each gate below uses the card's command as written.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git ls-files, filtered for CI configuration paths (.github/, .gitlab-ci, .circleci/, azure-pipelines, Jenkinsfile, .travis, bitbucket-pipelines, .buildkite/, .drone), returned 0 files; read in the change worktree on 2026-11-13"
  },
  "decisions": {"override": null, "amd64": null},
  "candidates": [],
  "guest": null
}
```

### Task 1: The launched pytest has a base folder of its own (`tests/integration/test_sigint_launch.py`, `tests/integration/test_sigint_launch_temp_root.py`)

**Dependencies:** None

**What to build:** Remove the proof test's dependence on the shared temp root: `test_real_start_stops_when_pytest_launch_ignores_sigint` takes `tmp_path` and adds a `--basetemp` option, pointing at a folder that does not yet exist under it, to the pytest it launches. A new module `test_sigint_launch_temp_root.py` holds the measurement that fails on the base and passes after. The cause, in words, for the measurement's docstring: a pytest started with no base folder takes its base from the temp root every pytest session on the machine shares, and on exit deletes each earlier session folder three or more numbers below the newest that holds no live lock (a lock older than three days counts as dead), and how long that takes depends on what other sessions left behind, all of it inside the proof test's `OUTER_DEADLINE_SECONDS`. The selected case's own 30-second wait is not involved. `SELECTED_CASE`, `IGNORE_INTERRUPT_THEN_RUN`, `OUTER_DEADLINE_SECONDS`, `ONE_CASE_PASSED` and every assertion of the proof test keep their values and text; the module docstring of `test_sigint_launch.py` gains the reason.

#### Behaviours to verify (developer adds the test to `tests/integration/test_sigint_launch_temp_root.py`)

- `test_launched_pytest_leaves_the_shared_temp_root_alone` — layer 2 Integration — fakes: none (a real nested pytest and a real tracker; the private temp root and both base folders sit under `tmp_path`) — the nested run of the proof test, started against a private temp root that holds a leftover session pytest would delete, exits 0 and reports exactly one case passed, and the private root's listing equals the listing taken before the run. Red at the base on the listing assertion, on every run.
- Existing, must keep passing: `tests/integration/test_sigint_launch.py::test_real_start_stops_when_pytest_launch_ignores_sigint` — layer 2 Integration — fakes: none, as at the base — still asserts `launch.returncode == 0` and one `ONE_CASE_PASSED` line, and still selects the case that asserts `(status, errors) == (0, b"")`.
- Existing, must keep passing: `tests/integration/test_start_stop.py::test_arming_preserves_an_inherited_ignored_sigint` — an ignored SIGINT stays ignored once armed; the fix never makes it caught.

#### Held by review (omit when every rule of this task reaches a test)

- The measurement's docstring names the cause — no test reads a docstring's meaning, so Task 2 holds it by reading. The architecture test `test_trace.py` checks only its path-shaped tokens and its requirement pointers.

#### Implement

Infer from failing tests.

```
# Hint:
# Proof test: add --basetemp to the launched argument list, after -p no:cacheprovider and before
# SELECTED_CASE, pointing at a not-yet-existing folder under the test's own tmp_path. Given a base
# folder, pytest uses it (deleting it first if it exists) and never makes a numbered session
# folder or cleans the shared root. The shell trap and exec "$@" stay as they are.
#
# Measurement: (1) make a private temp root under tmp_path; inside it the user folder pytest would
# make, "pytest-of-" plus getpass.getuser(); in that, a leftover pytest-1 holding a file and no
# .lock, and a newer pytest-5, so any new session is numbered three or more above the leftover;
# list the private root. (2) Launch sys.executable -m pytest -q -p no:cacheprovider from
# PRODUCT_ROOT on the proof test's node id alone — never the whole module, which would run itself —
# with its own --basetemp under tmp_path, and an environment copied from os.environ plus
# PYTEST_DEBUG_TEMPROOT set to the private root (pytest's temp-root variable, inherited by the
# proof test's launched pytest). Hand the environment to Popen, never to monkeypatch. (3) Start it
# in a new session and wait on a module constant longer than OUTER_DEADLINE_SECONDS, for the reason
# that one is longer than the selected case's 30 seconds; on expiry kill the process group and fail
# with both outputs, as the proof test does. (4) Assert exit 0, exactly one case passed (reuse
# ONE_CASE_PASSED), and the private root's listing equals the first. (5) Import only names
# test_sigint_launch.py already has at the base (PRODUCT_ROOT, OUTER_DEADLINE_SECONDS,
# ONE_CASE_PASSED), so the red is on the assertion and not an ImportError. (6) Docstring: name the
# cause in words, with SRS NFR-11 and SDD § 4 TS-2; name no path that does not exist under the
# product root, and no planted file name ending .py, .md, .toml, .txt or .css. (7) Python 3.11
# standard library only, plus pytest's --basetemp and PYTEST_DEBUG_TEMPROOT.
```

#### Verification gate

Run, from the change worktree root, both commands of the card's `Test command:`:

`uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`

Run from `products/tracker17`: `uv run --locked ruff format --check .`, `uv run --locked ruff check .`, `uv run --locked mypy main.py errors.py domain application persistence web`.

Pass criteria: the measurement fails on the base and passes after the setup change; the proof test passes alone and in the full run; both test commands exit 0 in full; the three code gates pass; no existing test loses an assertion.

### Task 2: One-change checks against the branch's merge base (`products/tracker17`)

**Dependencies:** Task 1 (the diff it makes)

**What to build:** The checks that hold only while this change is built — no product file moved, no wait limit raised, nothing hidden, no assertion retired — held by reading the diff against the branch's merge base. Nothing is written.

#### Deliverables verified by review (no test asserts these — the gate is the diff)

- Only the two test modules change — `git diff "$(git merge-base main HEAD)" --name-only -- products/tracker17` lists exactly `products/tracker17/tests/integration/test_sigint_launch.py` and `products/tracker17/tests/integration/test_sigint_launch_temp_root.py` (spec I-2).
- No wait limit is raised — `git diff "$(git merge-base main HEAD)" -- products/tracker17/tests/integration/test_start.py` prints nothing, and `git diff "$(git merge-base main HEAD)" -- products/tracker17/tests/integration/test_sigint_launch.py | grep -nE '^[-+].*(OUTER_DEADLINE_SECONDS *=|timeout=)'` prints nothing (spec I-5).
- Nothing is skipped, retried or marked expected-to-fail — `git diff "$(git merge-base main HEAD)" -- products/tracker17 | grep -nE '^\+.*(mark\.(skip|skipif|xfail)|xfail|retry|flaky|reruns)'` prints nothing, comments and names included (spec I-5).
- The proof keeps proving what it proves — `git diff "$(git merge-base main HEAD)" -- products/tracker17/tests/integration/test_sigint_launch.py | grep -nE '^-.*(assert|SELECTED_CASE|IGNORE_INTERRUPT_THEN_RUN|ONE_CASE_PASSED|returncode)'` prints nothing: no assertion or selection line is removed or changed (spec I-3).
- The measurement patches nothing and defines no stand-in — `grep -nE 'monkeypatch|mock|patch\(|^class ' products/tracker17/tests/integration/test_sigint_launch_temp_root.py` prints nothing (spec I-6, I-8).
- The measurement's opening docstring names SRS NFR-11 and SDD § 4 TS-2, and names the cause in words — reading (spec I-4, I-7); `test_trace.py` passes in Task 1's gate.

#### Implement

Verified by review — no test.

#### Verification gate

Use the card's `Test command:` from the change worktree root: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`.

Pass criteria: every criterion above is met on reading the diff, each command printing what it says; the full suite has no new failures.
