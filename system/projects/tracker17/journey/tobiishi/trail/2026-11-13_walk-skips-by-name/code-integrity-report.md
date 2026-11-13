# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `2026-11-13_walk-skips-by-name` — the source walk skips by name.
**Verdict in one line:** clean pass. The code already did what its intent says. Two tests were added
for cases the spec states and no test covered. Both pass on the code as it stands.

## Deferrals

None. The newest closing marker (`developer: 2026-11-13_walk-skips-by-name — implementation
complete`, `<a commit not in the public history>`) carries no `Deferred:` line, and no `Failing:` line.

## What was reviewed

- `products/tracker17/tests/conftest.py`: `SourceWalk._all`, the two skip constants above it, the
  `SourceWalk` docstring and the module docstring's source-walk paragraph.
- `products/tracker17/tests/architecture/test_source_walk.py`: the new layer-6 module, with its five
  tests.
- Commits `601c3cf2c` (red), `a604290a5` (green), `de33064f0` (refactor) and the marker `<a commit not in the public history>`.

## The intent it was checked against

- `tl_instruction.md`, Task 1: its *What to build*, its five *Behaviours to verify*, *Held by review*
  and the hints.
- `change_spec.md`: CP-785 to CP-795 and the Examples table.
- `docs/fdr.md` was not needed for this change. The spec and the NFDR QC-1 clause it quotes settle
  every case.

## Tests added or fixed

Two added, both in `tests/architecture/test_source_walk.py`. No test was fixed: the five the developer
wrote each assert what their behaviour in the plan says, and each was red or green at the base exactly
as the plan predicts.

- `test_a_behave_folder_inside_a_part_is_walked_as_that_part`. CP-786 says a folder named `tests`,
  `.behave` or `.venv` below the root is walked as the part that holds it. The existing case plants
  `domain/.venv/` and `domain/tests/` but no `.behave` folder inside a part. So a walk that skipped
  `.behave` at any depth would still pass the suite. The new test plants `web/.behave/x.py` and
  asserts it is walked as part `web`.
- `test_a_root_file_named_like_a_skipped_folder_is_walked_as_its_own_part`. CP-785 matches a file's
  first path piece. CP-786 says a `.py` file at the root is walked as its own part, whatever its name
  begins with. Hint 1 of the plan states the consequence: a root file's first piece ends in `.py`, so
  it can never equal a skipped name. No test covered this, so a walk that compared the part name
  instead of the first piece would skip `tests.py` and still pass. The new test plants `tests.py`,
  `.behave.py` and `.venv.py` at the root and asserts the parts are `PARTS` plus `tests`, `.behave`
  and `.venv`. Its root has no `tests/` folder, because on a filesystem that ignores case the two
  names would clash (the plan's hint 4).

Both tests come from the spec's words, not from the code. Both pass on the code as committed.

## The finding

No issues. Nothing was misplaced. Every behaviour in the intent now has a test that would fail if
the code were wrong, and the whole suite passes.

- **CP-785 / CP-786.** `_all` skips exactly `tests`, `.behave` and `.venv` as the first piece, and
  `__pycache__` as any piece. It matches by set membership, with no prefix test, no case-folding and no
  leading-dot test. That is what the spec states.
- **CP-787.** The existing layer-6 modules over the product root pass, with `.venv/` and `.behave/`
  present: 92 passed in `tests/architecture/`.
- **CP-788 to CP-790.** The CP-788 test was red at the base on its first assertion (commit
  `601c3cf2c`), and the CP-790 test was green there, as the plan says.
- **CP-791.** The module docstring names NFR-9, AC-5 and QC-1 and spells no planted path.
  `test_trace.py` passes over it.
- **CP-792.** `uv run --locked ruff format --check --no-cache .` printed "350 files already
  formatted", and `uv run --locked ruff check --no-cache .` printed "All checks passed!". Both were
  run from `products/tracker17`, after the two tests were added.
- **CP-793 / CP-794.** The change adds no part. The tests use `pathlib`, set operations and
  `tmp_path` only, all of which Python 3.11 has.
- **CP-795.** Both suites passed through the gate tool: "3304 passed, 2 skipped, 6 warnings" and
  "122 passed" on their last lines.
- **The docstrings (held by review).** The `SourceWalk` docstring and the module docstring's
  source-walk paragraph now name what is skipped, by name, in place of "a hidden folder".

Owed outside this change, already recorded by the plan and the developer, and not this skill's to
make: `docs/nfdr.md` § 1.1, QC-1, *verified by*, still says "The entry starts unmet in its test". That
sentence goes false when this change lands. The NFDR belongs to the Principal Architect, and the spec
leaves it to its owner, under Out of Scope.

## Calls made

None.

## Placement

- **The skip set and the walk** (`_SKIPPED_ROOT_FOLDERS`, `_SKIPPED_AT_ANY_DEPTH`, `SourceWalk._all`
  in `tests/conftest.py`): **no owning part**. SDD § 3 lists the five product parts. `tests/` is placed
  by the language frame, inside the one unit, and is no part's `Owns`. Left where it is, beside the
  walk it serves, as `change_design.md` § 2 places it.
- **The proof** (`tests/architecture/test_source_walk.py`): test code, **no owning part**. Layer 6
  sits in `tests/architecture/`, as `testing_python.md` § Layer 6 says.
- No product part got new logic, so nothing was moved and no placement commit was made.

## Language resolution

- **Python**, answered by step 1 of the chain (`project.md` `Languages: Python`).
- Packet read: `languages/python/README.md` and every concern it routes: `toolchain.md`, `layout.md`,
  `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md`, and `testing_python.md`
  outside the folder. `arch_defaults.md` and `testing_doctrine.md` were read beside it.
- The packet's Python 3.13 floor (`toolchain.md`) yields to the product's own Python 3.11 floor
  (NFDR QC-60). The product's records outrank the packet (`languages/README.md` § Precedence).
- Against the bar:
  - `SourceWalk` is handed its root and builds no collaborator.
  - The tests hand `walk_of` a root they built under `tmp_path`, and patch nothing.
  - Layer 6 reads real files, and that is allowed: its subject is the tree (`testing_python.md`
    § Layer 6). Every file it reads is in the test's own temporary folder, or committed in the
    product root.
  - No test reads the home folder, the history or the network.
  - The new tests follow the module's own style: double quotes, `pathlib`, and underscore-prefixed
    module internals.
  - No departure from the packet was found.

## Test evidence

- **Full card run, through `gate_suite.py run --gate code-integrity`, owners-mac** (no CI: a
  `git ls-files` inventory for CI paths in the change worktree listed nothing; NFDR § 8 holds no
  environment entry). Exit status 0.
  - `products/tracker17/tests/`: "3304 passed, 2 skipped, 6 warnings in 2128.41s".
  - `products/tracker17/tests/e2e/`: "122 passed in 786.97s".
- **Targeted, before the full run:** `uv run --locked pytest -q -p no:cacheprovider tests/architecture/`
  from `products/tracker17`: "92 passed".
