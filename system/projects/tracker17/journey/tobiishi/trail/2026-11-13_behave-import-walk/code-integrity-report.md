# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `2026-11-13_behave-import-walk` — the Behave folder gets its walk for QC-19's second
clause.
**Verdict in one line:** pass, with two bugs found and fixed. The walk took a dangling link named
`.behave` for an absent folder and passed, and it crashed on a subfolder whose name ends in `.py`.
Three tests were added. Two went red on the code as the developer left it, and both are green now.

## Deferrals

None. The newest closing marker (`developer: 2026-11-13_behave-import-walk — implementation
complete`, `<a commit not in the public history>`) carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

- `products/tracker17/tests/conftest.py`: `BehaveWalk`, its two constants, the `behave_walk_of`
  fixture and the module docstring's new paragraph. `SourceWalk`, `walk_of`, `Module` and `dotted`
  were read and are unchanged.
- `products/tracker17/tests/architecture/test_behave_imports.py`: the new layer-6 module, with its
  helpers `imports_from_tests` and `check_behave_folder` and its tests.
- Commits `b13ddc0a0` and `5ab59d992` (task 1, red and green), `1112d5822` and `a217613e7` (task 2,
  red and green) and the marker `<a commit not in the public history>`.

## The intent it was checked against

- `tl_instruction.md`: Tasks 1 and 2, with their *What to build*, *Behaviours to verify*, *Held by
  review* and hints.
- `change_spec.md`: CP-796 to CP-807, the Examples table and the Locked Answers.
- `change_design.md` § 3 (the walk's contract) and § 5, as the plan carries them.
- `docs/fdr.md` was not needed. The spec and the NFDR QC-19 clause it quotes settle every case.

## Tests added or fixed

Three added, all in `tests/architecture/test_behave_imports.py`. No test was fixed: the 25 the
developer wrote each assert what their behaviour in the plan says.

- `test_a_dangling_link_named_behave_fails_naming_the_folder`. CP-797 lets the check pass only when
  the root holds **no entry** named `.behave`. CP-799 fails it when `.behave` exists and nothing is
  read. The design's hint A(1) names three states: absent, a folder, and present but not a folder. A
  link whose target is gone is an entry that is not a folder. **Red:** the walk asked
  `folder.exists()`, which follows the link, and returned `[]` as if nothing were there.
- `test_a_folder_whose_name_ends_in_py_is_read_as_a_folder`. CP-798 says every other subfolder is
  read, whatever its name. **Red:** `rglob("*.py")` also yields a folder named `pkg.py`, and the walk
  tried to read it as a file and stopped with `IsADirectoryError`.
- `test_modules_come_back_sorted_by_path_from_any_depth`. The plan's *What to build* says the
  modules come back sorted by path, and CP-798 says any depth. No test held either the order or a file
  sitting directly in `.behave/`. Green on the code, and red in a scratch copy with the sort removed,
  so the test can fail.

Each test comes from the spec's or the plan's words, not from the code.

## The finding

Two bugs, both in `BehaveWalk` and both fixed in the green commit:

1. **A dangling link named `.behave` passed as absent.** `modules()` now returns `[]` only when the
   path neither exists nor is a link. A dangling link falls through to the empty-walk assertion and
   fails naming `.behave`, as a plain file does.
2. **A subfolder named like a module stopped the walk.** `_all` now passes over a path that is a
   folder. The files inside it are still yielded by `rglob` and read. Only folders are passed over,
   so a broken file link named `x.py` still fails loudly when it is read, and is not skipped in
   silence.

The module docstring's new paragraph said the walk "reads nothing when the folder is absent". With
fix 1 that is not the whole truth, so it now says the walk reads nothing when the root holds no entry
by that name, and fails on a dangling link.

Everything else holds:

- **CP-797 to CP-799.** Absent entry, empty folder, only-skipped files, plain file and now dangling
  link each have a test. The skip reads pieces below `.behave/` by exact equality: `.venv` as the
  first piece only, `__pycache__` as any piece.
- **CP-800 to CP-803.** `imports_from_tests` matches the first dotted piece exactly. Relative imports
  report the constant part `.behave`, whose first piece is empty, so they can never match.
- **CP-804.** The real-product test passes and asserts the folder is present. The pointed-elsewhere
  case raises.
- **CP-805,** re-run on the final code: in a scratch copy of the product with `import tests.conftest`
  and `from tests.x import y` appended to `.behave/features/command_way_in.py`, the architecture
  tests gave 1 failed and 119 passed. The one failure is
  `test_the_real_behave_folder_passes_and_is_present`. The QC-19 and QC-1 tests passed.
- **CP-806 and CP-807.** The two planted-root tests pass. `SourceWalk` and every test the spec lists
  are unchanged and green.
- **QC-60.** The code uses `Path.exists`, `Path.is_symlink`, `Path.is_dir`, `rglob` and
  `relative_to` without 3.12-only arguments. It was not run on 3.11 here (the lock resolves 3.14).
- **QC-62.** `ruff format --check` and `ruff check` pass over the product's tests folder. Compile
  passes on both changed files.

## Calls made

1. **Is a dangling link named `.behave` an absent entry or an entry that reads nothing?**
   - *Readings:* absent, so the check passes (what the code did); or an entry that is not a folder,
     so it fails like a plain file.
   - *Taken:* it fails. CP-797 is worded as "no entry named `.behave`", and a link is an entry. The
     design's three states put "present and not a folder" on the failing side, and NFDR § 9 fails a
     walk that can pass by reading nothing.
   - *Whose:* the Product Owner's (`change_spec.md` CP-797 and CP-799).
   - *If reversed:* drop the `is_symlink()` half of the first check in `BehaveWalk.modules` and the
     new test. A dangling link would then pass as an absent folder.
2. **What does the walk do with a subfolder whose name ends in `.py`?**
   - *Readings:* read it as a folder; or treat the crash as acceptable, since the error is loud.
   - *Taken:* read it as a folder, which is what CP-798's "every other subfolder is read, whatever its
     name" says. Only folders are passed over, so a dangling file link still fails loudly. That is the
     smaller change, and it keeps the fail-loud behaviour.
   - *Whose:* the Product Owner's (CP-798).
   - *If reversed:* remove the `is_dir()` guard in `BehaveWalk._all` and the new test.
3. **`SourceWalk` has the same defect with a folder named like a module. Is it fixed here?**
   - *Taken:* no. CP-807 holds the product-root walk unchanged, and that is the spec's locked rule.
     Changing it is outside this change.
   - *Whose:* the PM's, at `shukuba-refine`. One `is_dir()` guard in `SourceWalk._all` would fix it.
     It needs a change of its own.
   - *If reversed:* a later change adds the guard and a test to `test_source_walk.py`.

## Placement

`docs/SDD.md` § 3 was read. Every piece of new logic is test code, and the parts table gives no part
an `Owns` over `tests/`.

- `BehaveWalk` and `behave_walk_of` in `tests/conftest.py`: **no owning part**. They sit beside
  `SourceWalk`, where the design puts them.
- `imports_from_tests` and `check_behave_folder` in `tests/architecture/test_behave_imports.py`:
  **no owning part**. They sit where `testing_python.md` § Layer 6 puts a layer-6 module.

Nothing was moved, so there is no placement commit.

## Language resolution

- Python, from step 1 of the chain: `project.md` `Languages: Python`.
- Packet read: `languages/python/README.md`, with every concern file it routes: `toolchain.md`,
  `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md`, and
  `testing_python.md`. `arch_defaults.md` and `testing_doctrine.md` were read beside it.
- Where it bore on the code:
  - `conventions.md` § Constructs: `BehaveWalk` is given its root and builds nothing. It is built
    only in the fixture, as `SourceWalk` is in `walk_of`.
  - `conventions.md` § Typing: the helpers in the test module are unannotated on `walk`, as
    `violations` in `test_imports.py` is. They are test code, and the packet asks annotation of
    production functions only.
  - `testing_doctrine.md`: these are layer-6 tests whose subject is files on disk. They write only
    under `tmp_path` and read the product's own `.behave/`. No unit test touches a real resource,
    and no code builds its own collaborator.
  - `testing_python.md` § Layer 6: the real-product test enumerates from disk and asserts no count.

## Test evidence

Every full run of the card's test command went through the gate tool, on the owner's Mac (the
product has no CI).

- An earlier run of the test command exited 1 and printed `Environment: owners-mac — no CI`. That was
  the red run after the three tests were added: 2 failed (the dangling-link and the `pkg.py` tests),
  3330 passed, 2 skipped. The end-to-end suite did not run, because the card chains the two with `&&`.
- An earlier run of the test command exited 0 and printed `Environment: owners-mac — no CI`. That was
  the first green run, with a guard that skipped every path that was not a file: 3332 passed and 2
  skipped, then the end-to-end suite with 122 passed. The guard was then narrowed to folders only
  (Calls made, item 2).
- The run this verdict rests on exited 0 and printed the `Environment:` line under the verdict: 3332
  passed, 2 skipped, then the end-to-end suite with 122 passed.

Commits: `5f2f364df` (red, the three tests), then the green commit that carries this report.
