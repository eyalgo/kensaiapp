# Tech Lead instruction — pins-test-reads-behave-lock: the pins test reads the Behave folder's manifest and lock

**Category:** nfdr
**Behaviour:** changing
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with its concern files (`toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md`) and `testing_python.md`
**Product root:** `products/tracker17` — every path below is relative to it.
**Scope:** `tests/architecture/test_pins.py` gains a check of `.behave/pyproject.toml` and `.behave/uv.lock` by NFDR QC-39's three checks, one test per case run on a temporary copy of the product, and its exact-pin pattern refuses a wildcard version. No other file in the product changes (CP-783).

---

## Project layout

```
products/tracker17/
  tests/
    architecture/
      test_pins.py        ← modified (the only file this change touches)
```

No new directory and no new `__init__.py`. The fixture that makes the temporary copy lives in `test_pins.py`, not in `conftest.py` (CP-783). `domain/`, `application/`, `persistence/`, `web/`, `main.py`, `errors.py`, both `pyproject.toml` files and both `uv.lock` files stay as they are.

No part owns the new logic: `docs/SDD.md` § 3's five parts own tracker behaviour, and this is test code. Placement follows `change_design.md` §2 and NFDR QC-39's *verified by*.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):
- **Task split:** §3's one sub-job (the file) bundled three responsibilities: the shared exact-pin pattern, the check's manifest side, and its lock side. Cut into Task 1 (the pattern), Task 2 (the check over the manifest, the copy fixture, the product test, the absent case) and Task 3 (the check over the lock). Each is independently red and green, and each adds a failing test before it adds code. The file is still the only one touched. Task 4 holds what the design lists as "Checked outside the suite".
- **Behaviour added:** `test_a_missing_manifest_gives_no_lock_mismatch_finding` in Task 3. The design says "when the manifest is missing, no later check runs over it" in §4 and has no §5 row for it. Without it a missing manifest could raise from the lock check, or report a mismatch for a dependency nobody could read.
- **Behaviour added:** `test_the_exact_pattern_refuses_a_wildcard_version` in Task 1. The design's Architect Review Notes (b) widens `EXACT` and §5 holds only the `==1.*` row inside the check's parametrized cases. A pattern change gets its own test so the red sits at the pattern and not only at the check. The four existing tests keep every assertion they make (CP-781).
- **Layer and fakes written:** §5 states layer 6 and "none" for every row, carried onto each behaviour below. The temporary copy is real files under `tmp_path`, as `change_design.md` §5 says.
- **Gate command:** the card's `Test command:` was run once on the pins test, in the form the card gives, and it collected and passed 4 tests at the base. It runs what the spec's claims ran, so no gate is rewritten.
- **Packet:** no conflict with any concern file. The check is handed the folder it reads and builds no collaborator. Reading a file counts as missing only on `OSError`, `UnicodeDecodeError` or `tomllib.TOMLDecodeError` (`errors_logging.md` § Catching). No packet departure, so `deferred_decisions.md` is not written.
- **Checked outside the suite becomes Task 4:** the design leaves CP-780 and CP-782 to CP-784 outside the suite. They are true only while this change is built (a diff against the base, a mutation in a clone of this commit), so they are a review-verified task, each against the branch's own merge base and never a pinned SHA.

## Corrections owed while there

- Owed outside this change's reach: `docs/nfdr.md` QC-39, *verified by* — the sentence "**The entry starts unmet in its test:** at `<a commit not in the public history>`, `test_pins.py` reads only the root `pyproject.toml` and `uv.lock`" goes false once this change lands → it should say that the Behave half is met, that `test_pins.py` reads both pairs, and that it was verified by CP-782's mutation in a fresh clone at the landing commit (non-zero mutated, 0 reverted). RN-69's "QC-39 starts unmet in its test" is a dated note and stays as written.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git ls-files, filtered for a hosted service's folder or file (.github, .gitlab-ci, .circleci, Jenkinsfile, azure-pipelines, .travis, bitbucket-pipelines, .buildkite, .drone, cloudbuild, appveyor, .woodpecker), a Makefile and a Dockerfile, run in the change worktree: no line returned"
  },
  "decisions": {"override": null, "amd64": null},
  "candidates": [],
  "guest": null
}
```

---

### Task 1: The exact-pin pattern refuses a wildcard version (`tests/architecture/test_pins.py`)

**Dependencies:** None

**What to build:** `EXACT`'s version part stops accepting `*`, so `httpx==1.*` is no longer an exact pin. Both sets of dependencies read this one pattern, so both meet one bar. Everything `EXACT` refused before it still refuses, and the root manifest holds no `*`.

#### Behaviours to verify (developer adds tests to `tests/architecture/test_pins.py`)

- `test_the_exact_pattern_refuses_a_wildcard_version` — layer 6 Architecture — fakes: none — `EXACT.fullmatch` returns nothing for `httpx==1.*` and for `httpx[http2]==1.*`, and still matches `httpx==0.28.1`.

The four existing tests keep every assertion they make. `test_the_exact_pattern_refuses_a_range_and_accepts_a_pin` still passes: its accepted pins hold no `*`, and `pytest==9.*,<10` stays refused.

#### Implement

Infer from failing tests.

# Hint: the version part of the pattern is a negated character class. Add `*` to the characters it refuses, and leave the name part and the extras part as they are.

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`.

Pass criteria: the new test passes; the four existing tests in the file pass; no new failures elsewhere, and each half's last line reports passed tests and no failure.

---

### Task 2: The Behave folder's manifest is checked, on a copy of the product (`tests/architecture/test_pins.py`)

**Dependencies:** Task 1 (the check refuses `==1.*` through the tightened `EXACT`)

**What to build:** A check over a given product folder's `.behave/pyproject.toml` that returns one finding per failure, each naming its case. It reuses `declared_dependencies`, `normalized` and `EXACT`, and reads only under the folder it is handed. Findings for this task:

- the manifest is missing, or is not readable TOML;
- the manifest declares no dependency in any of the four lists `declared_dependencies` reads;
- a requirement is not an exact pin.

When `.behave` is absent the check returns nothing. A file counts as missing when it is not a regular file, or when reading or parsing it raises one of the narrow errors named in the TL Review Notes. When the manifest is missing, no later check runs over it. Also in this task: a fixture in this file that copies the product root into `tmp_path` (leaving out `.venv`, `.pytest_cache` and `__pycache__`) so that each case edits only the copy's `.behave/`, and the product test that runs the check on `PRODUCT_ROOT` itself. The module docstring keeps naming SRS NFR-9 and adds the new rule ids, and every path a docstring names is written from the product root.

#### Behaviours to verify (developer adds tests to `tests/architecture/test_pins.py`)

- `test_the_behave_folder_of_the_product_holds_every_pin` — layer 6 Architecture — fakes: none (reads the committed tree beside it) — the check run on `PRODUCT_ROOT` returns no finding. Example 1.
- `test_a_requirement_not_pinned_exactly_is_found` — layer 6 — fakes: none (the copy) — parametrized, the copy's manifest declares one requirement not pinned exactly, and the finding names that entry. Cases: `httpx>=0.28` in `[project] dependencies`; a bare `behave` in `[dependency-groups]`; `~=` in `[project.optional-dependencies]`; `==1.*` in `[project.optional-dependencies]`; a pin combined with a second specifier in `[build-system] requires`. All four lists appear at least once.
- `test_a_missing_or_unreadable_manifest_is_found` — layer 6 — fakes: none (the copy) — parametrized, the manifest finding appears when `.behave/` holds `uv.lock` and no `pyproject.toml`, when `.behave` is a plain file, and when `pyproject.toml` is not readable TOML.
- `test_a_manifest_declaring_nothing_is_found` — layer 6 — fakes: none (the copy) — a manifest of `dependencies = []` and nothing else gives the nothing-declared finding.
- `test_an_absent_behave_folder_finds_nothing` — layer 6 — fakes: none (the copy) — the copy with `.behave` removed gives no finding. The root checks still run: they are the four existing tests, whose inputs hold nothing of `.behave`.

Each failing case asserts that its own finding is among the returned ones, so a case cannot pass because some other check failed.

#### Implement

Infer from failing tests.

# Hint: the seam is the folder. The check takes the product folder as a parameter and returns its findings as a list. The product test hands it `PRODUCT_ROOT`, and each case test hands it the copy. The copy is made once per test with `shutil.copytree` and `ignore_patterns`. Each case then rewrites the manifest's text, removes or overwrites a file, turns `.behave` into a plain file, or removes it.

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`.

Pass criteria: this task's tests pass; the four existing tests pass; no new failures elsewhere; each half's last line reports passed tests and no failure.

---

### Task 3: The Behave folder's lock is checked against its manifest (`tests/architecture/test_pins.py`)

**Dependencies:** Task 2 (extends the check Task 2 builds, and uses its fixture)

**What to build:** The same check also reads `.behave/uv.lock`, adding findings for: the lock is missing or not readable TOML; the lock holds no package record; a declared dependency the lock does not fix at its declared version. Names compare as `normalized` compares them (case and separator runs folded, extras dropped), the way the root lock test already compares them. The mismatch check runs only over a manifest that read, and over a lock that read.

#### Behaviours to verify (developer adds tests to `tests/architecture/test_pins.py`)

- `test_a_missing_or_unreadable_lock_is_found` — layer 6 Architecture — fakes: none (the copy) — parametrized, the lock finding appears when `.behave/` holds `pyproject.toml` and no `uv.lock`, and when `uv.lock` is not readable TOML.
- `test_a_pin_the_lock_does_not_fix_is_found` — layer 6 — fakes: none (the copy) — the copied manifest says `playwright==1.65.0` against the lock's `1.65.1`, and the finding names it. The copy is made the way CP-782 makes it, by replacing the `playwright` pin in the copied manifest.
- `test_a_lock_with_no_package_record_is_found` — layer 6 — fakes: none (the copy) — a copied lock with no package record gives its own finding.
- `test_a_name_spelt_differently_is_still_fixed_by_the_lock` — layer 6 — fakes: none (the copy) — parametrized, `Behave==1.3.3` in place of `behave==1.3.3` gives no finding, and neither does `httpx[http2]==0.28.1`, because extras are dropped.
- `test_a_missing_manifest_gives_no_lock_mismatch_finding` — layer 6 — fakes: none (the copy) — with `pyproject.toml` removed and the lock present, the manifest finding appears and no finding about a lock mismatch does.

The product test from Task 2 now also covers CP-775 and CP-776 on the product's own tree, and it is the test CP-782's mutation fails.

#### Implement

Infer from failing tests.

# Hint: read the lock with `tomllib` and build the set of (normalized name, version) pairs from its package records, as the root lock test does, then compare each declared pin's pair with that set.

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`.

Pass criteria: this task's tests pass; Task 1 and Task 2's tests and the four existing tests pass; no new failures elsewhere; each half's last line reports passed tests and no failure.

---

### Task 4: What the suite cannot measure (the change as a whole)

**Dependencies:** Task 3 (measures the finished file)

**What to build:** Nothing is written. The deliverables below are the spec's own measurements, and a test cannot make them: a test reads no commit history, and each is true only while this change is built.

#### Deliverables verified by review (no test asserts these — the gate is the diff)

- CP-783 — the change touches `products/tracker17/tests/architecture/test_pins.py` alone — `git diff --name-only "$(git merge-base main HEAD)" -- products/tracker17` run in the change worktree lists that path and no other.
- CP-780 — the product's own Behave files are untouched by the suite — after both halves of the card's `Test command:` have run, `git status --porcelain -- products/tracker17/.behave` in the change worktree prints nothing.
- CP-782 — the guard is real — in a fresh clone of this repository at the change's tip, made with `mktemp -d` and removed from outside in a command of its own, `playwright==1.65.1` changed to `playwright==1.65.0` in `.behave/pyproject.toml` only, `uv run --locked --project . pytest tests/architecture/test_pins.py` run from the clone's product folder exits non-zero and the product test's row is the one that fails. With the change reverted, the same command exits 0.
- CP-784 — both halves of the card's `Test command:` — each last line reports passed tests and no failure or error.
- QC-62 — `ruff format --check` and `ruff check` over `tests/architecture/test_pins.py`, run under the product's own tooling, report nothing to fix.

#### Implement

Verified by review — no test.

#### Verification gate

Run the card's `Test command:` in full, then each check above.

Pass criteria: every criterion above is met on reading the diff and the output; the full suite has no new failures.
