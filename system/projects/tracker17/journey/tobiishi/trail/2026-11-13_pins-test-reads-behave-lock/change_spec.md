# Change Spec — the pins test reads the Behave folder's manifest and lock

**Date:** 2026-11-13
**Category:** nfdr
**Behaviour:** changing
**Request:** NFDR QC-39 holds two sets of test dependencies to one bar: the suite's (`pyproject.toml`, `uv.lock`) and the Behave folder's (`.behave/pyproject.toml`, `.behave/uv.lock`). `products/tracker17/tests/architecture/test_pins.py` reads only the root pair (`grep -n -i behave tests/architecture/test_pins.py` matches nothing today). Make it read the Behave folder's pair by the same three checks QC-39 names: every declared dependency pinned with `==`, a lock file present, and each declared dependency fixed by the lock at its declared version. Hold each case with a test in that file: a dependency not pinned with `==` fails; a `.behave/` with no `pyproject.toml` fails; a `.behave/` with no `uv.lock` fails; a declared dependency that `.behave/uv.lock` does not fix at that version fails; an absent `.behave/` reads nothing and passes (QC-1 lets the folder be absent). Each failing case is run against a temporary copy of the product whose `.behave/` is made to hold that case, and fails there. Prove it is a real guard: in a disposable copy, change `playwright==1.65.1` to `playwright==1.65.0` in `.behave/pyproject.toml` only; `uv run --locked --project . pytest tests/architecture/test_pins.py` then fails, and with the change reverted it passes. The change is the one test file; production code is not touched. Both suites pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and the same on `products/tracker17/tests/e2e/`, and the last line of each is read.
**Language resolution:** Python — step 1 (`project.md` `Languages:`) — `<CORE>/doctrine/engineering/languages/python/README.md` opened

---

## Change Summary

NFDR QC-39 holds the Behave folder's test dependencies to the same bar as the suite's, and its layer-6
test checks only the suite's. This change makes `tests/architecture/test_pins.py` check
`.behave/pyproject.toml` and `.behave/uv.lock` too, with a test for each case, and touches nothing else.

All paths below are relative to the product, which `project.md` `Product path:` names.

---

## Rules

### The Behave folder's set — QC-39's three checks

"Present" means a path named `.behave` exists at the product root. "Absent" means none does.

- **CP-773:** When `.behave` is present, `tests/architecture/test_pins.py` fails unless every
  requirement string in every dependency list `.behave/pyproject.toml` holds — `[project]
  dependencies`, every `[project.optional-dependencies]` list, every string in `[dependency-groups]`,
  and `[build-system] requires` — is pinned with `==` (NFDR QC-39). A requirement passes only when it
  is a name, optionally with extras in brackets, then `==`, then one version, with no further
  specifier. A floor (`>=`), a compatible release (`~=`), a bare name, a wildcard version (`==1.*`)
  and a pin combined with another specifier all fail.
- **CP-774:** When `.behave` is present and holds no `pyproject.toml` that reads as TOML, the test
  fails (NFDR QC-39). A `.behave` that is not a directory is in this case.
- **CP-775:** When `.behave` is present and holds no `uv.lock` that reads as TOML, the test fails
  (NFDR QC-39).
- **CP-776:** When `.behave` is present, the test fails unless `.behave/uv.lock` fixes each
  dependency CP-773 reads at its declared version: the lock holds a package record whose name equals
  the declared name and whose version equals the declared version (NFDR QC-39). Names compare as the
  packaging specification compares them: case is ignored, any run of `-`, `_` and `.` counts as one
  `-`, and extras are dropped. A `.behave/uv.lock` with no package record fails.
- **CP-777:** When `.behave/pyproject.toml` declares no dependency in any of the lists CP-773 names,
  the test fails.
- **CP-778:** When `.behave` is absent, the Behave checks read nothing and pass (NFDR QC-1, "may also
  hold"; NFDR QC-39). The suite's checks still run as CP-781 states.

### Each case is held by a test

- **CP-779:** `tests/architecture/test_pins.py` holds one test for each of CP-773, CP-774, CP-775,
  CP-776 and CP-777, and one for CP-778. Each failing case runs against a temporary copy of the
  product whose `.behave/` is made to hold that case, and asserts that the check fails there. The
  absent case runs against a temporary copy with no `.behave`, and asserts that the check passes.
- **CP-780:** The product's own `.behave/pyproject.toml` and `.behave/uv.lock` are byte-identical
  before and after the suite runs. No test writes into the product's own tree.

### The suite's set stays as it is

- **CP-781:** The four existing tests in `tests/architecture/test_pins.py` —
  `test_every_declared_dependency_is_pinned_exactly`,
  `test_uv_lock_fixes_every_declared_dependency_at_its_declared_version`,
  `test_requires_python_is_3_11` and `test_the_exact_pattern_refuses_a_range_and_accepts_a_pin` — keep
  reading the root `pyproject.toml` and `uv.lock`, keep every assertion they make, and pass.

### The guard is real, and the change is the one file

- **CP-782:** In a disposable copy of the product (a fresh clone at the change's commit), with
  `playwright==1.65.1` changed to `playwright==1.65.0` in `.behave/pyproject.toml` and nothing else
  changed, `uv run --locked --project . pytest tests/architecture/test_pins.py`, run from the copy's
  product folder, exits non-zero. With the change reverted, it exits 0. Today it exits 0 both ways:
  at `c5cb3cc28` the mutated copy gives `4 passed`, because `test_pins.py` reads only the root pair
  (`grep -n -i behave tests/architecture/test_pins.py` matches nothing).
- **CP-783:** Inside the product, the change's diff touches `tests/architecture/test_pins.py` only,
  which is where NFDR QC-39's *verified by* places the check. No file under `domain/`,
  `application/`, `persistence/` or `web/`, nor `main.py`, `errors.py`, either `pyproject.toml` or
  either `uv.lock`, changes.
- **CP-784:** Both halves of the card's `Test command:` pass:
  `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and
  `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`, each run from
  the change worktree's root, each with a last line that reports passed tests and no failure or error.

---

## Examples

| Scenario | Expected behavior |
|---|---|
| The product as it is: `.behave/` declares `behave==1.3.3`, `httpx==0.28.1`, `playwright==1.65.1`, and its lock fixes all three (CP-773, CP-775, CP-776, CP-781) | `test_pins.py` passes |
| Temporary copy: `.behave/pyproject.toml` declares `httpx>=0.28` (CP-773) | the check fails |
| Temporary copy: `.behave/pyproject.toml` has a `[dependency-groups]` entry `behave` with no version (CP-773) | the check fails |
| Temporary copy: `.behave/` holds `uv.lock` and no `pyproject.toml` (CP-774) | the check fails |
| Temporary copy: `.behave` is a plain file (CP-774) | the check fails |
| Temporary copy: `.behave/` holds `pyproject.toml` and no `uv.lock` (CP-775) | the check fails |
| Temporary copy: `.behave/pyproject.toml` declares `playwright==1.65.0` while `.behave/uv.lock` fixes `1.65.1` (CP-776) | the check fails |
| Temporary copy: `.behave/pyproject.toml` declares `Behave==1.3.3` and the lock fixes `behave` at `1.3.3` (CP-776) | the check passes for that dependency |
| Temporary copy: `.behave/pyproject.toml` declares `dependencies = []` and nothing else (CP-777) | the check fails |
| Temporary copy with no `.behave` (CP-778) | the Behave checks pass, the root checks run as before |
| The suite runs, then the product's `.behave/pyproject.toml` and `.behave/uv.lock` are compared with the commit (CP-779, CP-780) | both byte-identical |
| Disposable clone, `playwright==1.65.0` in `.behave/pyproject.toml` only (CP-782) | `uv run --locked --project . pytest tests/architecture/test_pins.py` exits non-zero; reverted, exits 0 |
| `git diff` of the change, inside the product (CP-783) | lists `tests/architecture/test_pins.py` alone |
| Both halves of `Test command:` (CP-784) | each last line reports passed and no failure |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| `test_pins.py` reads only the root pair today (CP-782) | `git grep -n -i behave -- tests/architecture/test_pins.py` in the product | at `c5cb3cc28`: no match, exit 1 |
| The four existing tests pass at the base (CP-781, a rule left unchanged) | `uv run --locked --project products/tracker17 pytest -q` with the four ids `tests/architecture/test_pins.py::test_every_declared_dependency_is_pinned_exactly`, `::test_uv_lock_fixes_every_declared_dependency_at_its_declared_version`, `::test_requires_python_is_3_11`, `::test_the_exact_pattern_refuses_a_range_and_accepts_a_pin`, in the change worktree before any edit | at `c5cb3cc28`: `4 passed`; worktree clean after |
| The mutation passes today (CP-782's present defect) | fresh clone at `c5cb3cc28`, `playwright==1.65.0` in `.behave/pyproject.toml` only, `uv run --locked --project . pytest tests/architecture/test_pins.py -q` from the clone's product folder, real `uv run --locked` | `4 passed`, exit 0 |
| The real `.behave/` meets CP-773 and CP-776, so the change starts green on the product's tree | same clone, unmutated: the two existing check functions run with their product root pointed at `.behave/`, under `uv run --locked --project .` | both pass; declared set `['behave==1.3.3', 'httpx==0.28.1', 'playwright==1.65.1']`; `.behave/uv.lock` holds 17 package records, with `behave` 1.3.3, `httpx` 0.28.1, `playwright` 1.65.1 |
| The CP-782 mutation is one the CP-776 bar catches (the post-change tree, built and checked) | same clone, mutated: the existing lock check run with its product root pointed at `.behave/` | fails (AssertionError) |
| The suite's set is checked over four dependency lists, with names compared case- and separator-blind and extras dropped (Locked Answers, Gap 3) | read `declared_dependencies`, `normalized` and `test_uv_lock_fixes_every_declared_dependency_at_its_declared_version` in `tests/architecture/test_pins.py` | at `c5cb3cc28`: `[project] dependencies`, `[project.optional-dependencies]`, string entries of `[dependency-groups]`, `[build-system] requires`; `[-_.]+` folds to `-`, lowercased; extras cut at `[` |
| An absent `.behave` leaves the file passing today (CP-778) | same clone with `.behave` moved out, `uv run --locked --project . pytest tests/architecture/test_pins.py -q` | `4 passed` |

---

## Out of Scope

- `uv lock --check --project .behave` stays where NFDR QC-39 and § 10 put it: the `development-design`
  review of a change to `.behave/pyproject.toml` or `.behave/uv.lock`. It is not moved into the suite.
  This change edits neither file, so that review does not apply to it. The pins test still does not
  see a lock that keeps a package its manifest dropped.
- `.behave/pyproject.toml`'s `requires-python`. NFDR QC-59 binds the root `pyproject.toml` alone.
- Production code, both manifests and both lock files (CP-783).
- The contract-suite work and the source-walk work, which the request names as other changes.
- Running the Behave scenarios. Layer 7 has no stage (NFDR § 9).

---

## Locked Answers (the divergence record — self-review 2026-11-13)

- **Gap 1 — what "present" means:** a path named `.behave` at the product root. A `.behave` that is not
  a directory holding both files fails (CP-774). — (b) The request names a present folder and an
  absent one. A stray file in that place is neither, and failing on it is the stricter, reversible
  choice.
- **Gap 2 — a manifest that declares nothing:** fails (CP-777). — (b) QC-39 names three dependencies
  for the folder. A manifest with none has lost all three, and "every declared dependency is pinned"
  would pass it with nothing checked. Failing keeps the guard from going quiet. It is reversible.
- **Gap 3 — which lists count as declared:** all four dependency lists, names compared as packaging
  compares them, extras dropped (CP-773, CP-776). — (b) The request says "the same three checks", and
  the suite's set is held over these four lists with these comparisons today. The bar is stated
  outright here instead of by reference.
- **Gap 4 — a manifest or lock that is not readable TOML:** counts as missing, and fails (CP-774,
  CP-775). — (b) QC-39 has each manifest read with `tomllib`. A file that cannot be read checks
  nothing.
- **Gap 5 — the absent case gets a test too (CP-779):** — (b) the request lists the absent case among
  the cases each held by a test.
- **No records defect raised.** ADR-0013 says the tests' dependencies are locked "in one committed
  file, `uv.lock`", and QC-39 names two lock files. These do not contradict each other. ADR-0013's
  subject is the suite's environment. The Behave folder sits outside that environment (NFDR QC-1;
  SDD § 4 RT-4: "the folder is not the suite"). QC-39 traces to ADR-0013 "narrowed to the suite's set
  by RN-69". Both statements hold.
