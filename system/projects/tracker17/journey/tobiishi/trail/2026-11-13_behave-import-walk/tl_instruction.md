# Tech Lead instruction — behave-import-walk: the Behave folder gets its walk for QC-19's second clause

**Category:** nfdr
**Behaviour:** changing
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with every concern file it routes (`toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md`, and `<CORE>/doctrine/engineering/testing_python.md`)
**Product root:** `products/tracker17` — every path below is relative to it.
**Scope:** one new walk class and fixture in `tests/conftest.py`, and one new layer-6 module that checks QC-19's second clause over `.behave/`. No product code, `.behave/` file or document changes.

---

## Project layout

```
products/tracker17/
  tests/
    conftest.py                        ← modified (BehaveWalk, behave_walk_of, docstring sentence)
    architecture/
      test_behave_imports.py           ← new
```

No parts table applies to test code (`docs/SDD.md` § 3 has no part that owns `tests/`) — placement follows `change_design.md` §2. Every other file under the product root stays as it is.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **Task split by what each task's tests need:** design §3 has two sub-jobs, A (`BehaveWalk`) and B (the check). Design §5 puts every test in `test_behave_imports.py`, and rows marked "A" assert `modules()` alone. Task 1 creates that module with the A rows (walk only), Task 2 adds the B rows to it. *Reason:* Task 1 then has failing tests of its own, and the suite is green after each task (no atomic-landing edge, design §3).
- **Behaviour added:** Task 1 asserts that `.behave/tests/w.py` with `from . import x` has `imported()` equal to `[".behave"]`, so the constant `part` is held at the walk, not only through the downstream check. *Reason:* the design's CP-801 row proves it only through `tests_imports`; a part derived from the path would pass the Examples and break the rule, and this assertion pins it where the walk makes it.
- **Behaviour added:** Task 1 asserts that every module path begins `.behave/` and every module's `part` is `.behave`. *Reason:* design §3 states both as the walk's contract, and §5 asserts neither directly.
- **Placement kept:** the walk goes in `tests/conftest.py` beside `SourceWalk`, as the design places it. *Reason:* SDD § 3 names no part for test code, so no placement is corrected.
- **Hint kept and carried:** all of design §4's hints for A and B are carried into the tasks as approach. *Reason:* the hints state non-obvious traps (three states before any glob, skip read relative to `.behave/`, constant `part`, Python 3.11 only, docstring tokens `test_trace.py` resolves). None needed rewriting.
- **Held by review, not by a test:** CP-796 (the module is collected by `pytest tests/`), CP-805 (the clone mutation run) and the `conftest.py` docstring sentence reach no suite test. *Reason:* design §5 says so for the first two; the docstring is text. Each is written in its task under `#### Held by review`.
- **Gate command:** the card's `Test command:` runs `pytest products/tracker17/tests/` then `pytest products/tracker17/tests/e2e/`. Run at the branch base through the card's own runner with `--offline`, the architecture directory passed on a green run (the spec's Verified Claims count 92). Each task's gate below uses the card's command. *Reason:* it collects what the spec measured, so no divergence is logged beyond this line.

## Corrections owed while there

- `products/tracker17/tests/conftest.py` module docstring, source-walk paragraph — says the source walk reads every product module and skips three root folders and `__pycache__`, and never names the second walk → one sentence naming `behave_walk_of`, the folder it reads, and what it skips. Rides Task 1 (that task already opens this file).
- Owed outside this change's reach: `docs/nfdr.md` § 1.2, preamble — "Every entry is verified by one layer-6 test that walks the imports of every module on disk" goes false for QC-19 once this lands, because two layer-6 tests then verify it → it should say each entry is verified by a layer-6 import walk, and that QC-19's second clause over `.behave/` has a walk of its own, which fails as the others do when it finds nothing.
- Owed outside this change's reach: `docs/nfdr.md` § 1.1, QC-1, *verified by* — "The source walk under it, which the import and reach walks of §§ 1.2, 1.3, 3 and 8 share" goes false once this lands, because the walk of `.behave/` for QC-19 does not share it → it should name that walk as the exception: it reads `.behave/` by its own rule, skipping only `.behave/.venv/` and `__pycache__`.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {"finding": "none",
         "inventory": "git ls-files | grep -E '(^|/)(\\.github|\\.gitlab-ci\\.yml|\\.circleci|azure-pipelines\\.yml|Jenkinsfile|\\.travis\\.yml|bitrise\\.yml|\\.buildkite|\\.drone\\.yml)' returned no line (exit 1) on the change worktree"},
  "decisions": {"override": null, "amd64": null},
  "candidates": [],
  "guest": null
}
```

### Task 1: The scenario folder's walk (`tests/conftest.py`, `tests/architecture/test_behave_imports.py`)

**Dependencies:** None

**What to build:** `BehaveWalk(root)` and the `behave_walk_of` fixture in `tests/conftest.py`, and the new `tests/architecture/test_behave_imports.py` holding the walk's own tests. `root` is a **product root**, never the `.behave` folder, and is kept as `.root`. `modules()` returns one existing `Module` per `.py` file under `root/.behave`, sorted by path, with `path` relative to the product root (so it begins `.behave/`), `part` the fixed string `.behave`, and `tree` the parsed file. It skips files under `root/.behave/.venv/` and files with a path piece named exactly `__pycache__` below `.behave/`, and reads every other folder, whatever its name. `behave_walk_of` is a fixture returning `(root: Path | None = None) -> BehaveWalk`, defaulting to the product root as `walk_of` does. `SourceWalk`, `walk_of`, `Module`, `dotted` and the skip constants do not change. Also add the one docstring sentence listed under Corrections owed.

#### Behaviours to verify (developer creates `tests/architecture/test_behave_imports.py`, layer 6, no fake handed in — files under `tmp_path`)

The module docstring names SRS NFR-9 and AC-5, with NFDR QC-19 as the clause, and spells no planted path (§ Hint).

- `test_a_root_without_a_behave_entry_reads_nothing` — layer 6 Architecture — fakes: none — `modules()` is `[]` and nothing is raised (CP-797)
- `test_an_empty_behave_folder_fails_naming_the_folder` — layer 6 — fakes: none — `modules()` raises `AssertionError` whose message contains `.behave` (CP-799)
- `test_only_skipped_files_fail_naming_the_folder` — layer 6 — fakes: none — `.py` files only under `.behave/.venv/` and `.behave/features/__pycache__/`; `modules()` raises, message contains `.behave` (CP-798, CP-799)
- `test_a_plain_file_named_behave_fails_naming_the_folder` — layer 6 — fakes: none — `.behave` written as a plain file; `modules()` raises, message contains `.behave` (CP-799)
- `test_the_virtual_environment_is_skipped_and_the_rest_read` — layer 6 — fakes: none — `.behave/.venv/lib/pkg.py` beside `.behave/features/a.py`; only `a.py`'s path is returned, and no path begins `.behave/.venv/` (CP-798)
- `test_named_and_dot_folders_inside_the_folder_are_read` — layer 6 — fakes: none — `.behave/tests/y.py`, `.behave/.hidden/z.py` and `.behave/.behave/d.py` are all returned (CP-798)
- `test_near_names_and_nested_names_are_read` — layer 6 — fakes: none — `.behave/.venvs/a.py`, `.behave/features/__pycache__2/b.py` and `.behave/features/.venv/c.py` are all returned, while `.behave/features/__pycache__/e.py` is not (CP-798)
- `test_every_module_path_begins_with_the_folder_and_its_part_is_the_folder` — layer 6 — fakes: none — over a planted tree, each returned path begins `.behave/` and each `part` is `.behave` (design §3 contract)
- `test_a_relative_import_in_a_nested_folder_is_not_read_as_the_tests_part` — layer 6 — fakes: none — `.behave/tests/w.py` holding `from . import x`: its `imported()` is `[".behave"]` (CP-801, held at the walk)
- `test_the_walk_returns_the_existing_module_type` — layer 6 — fakes: none — each result is an instance of the existing `Module`, and `imported()` works on it (the reuse the request asks for)

#### Held by review

- The `conftest.py` module docstring gains one sentence naming the second walk and what it skips — covered by no test; a reader checks that the paragraph names `behave_walk_of`, the folder it reads, and the two skips.
- Python 3.11 only (QC-60) — `ruff` and the interpreter the lock fixes catch a 3.12-only call at collection or at run; no test names it.

#### Implement

Infer from failing tests.

# Hint: three states, told apart before any glob — the entry is absent, or present and a folder, or present and not a folder. Glob only in the folder case. A plain-file `.behave` goes straight to the empty-walk assertion; do not rely on `rglob` below a file answering empty on Python 3.11. The skip reads the pieces of the path relative to `.behave/`, not relative to the product root, since relative to the root every first piece is `.behave`. Match the first piece against `.venv` and every piece against `__pycache__`, both by exact equality, so `.venvs` and `__pycache__2` are read and `features/.venv/` is read. `part` is the constant `.behave`, never a path piece: `Module.imported()` reports a relative import as the module's part, and a piece-derived part would make `.behave/tests/y.py`'s `from . import x` read as an import from `tests`. Keep to Python 3.11: `Path.exists(follow_symlinks=...)`, `Path.walk` and `relative_to(..., walk_up=...)` are 3.12. The module docstring names SRS NFR-9 and AC-5 with NFDR QC-19 as the clause and spells no planted path: `test_trace.py` resolves every path-shaped token in a test module's docstring against the product root and fails a test module that names no requirement. Name planted files only in function docstrings or code.

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/architecture/test_behave_imports.py` from the worktree root, then the card's `Test command:`.

Pass criteria: this task's tests pass; the seven source-walk tests, `test_nothing_outside_tests_imports_third_party_or_tests`, `test_each_walk_fails_when_its_directory_holds_no_module` and `test_the_top_level_parts_are_the_five_the_sdd_names` still pass; no new failures elsewhere (CP-807).

### Task 2: The import-from-`tests` check and its proof (`tests/architecture/test_behave_imports.py`)

**Dependencies:** Task 1 (uses `behave_walk_of`, `BehaveWalk.root` and `BehaveWalk.modules()`). It also uses `walk_of`, `PARTS`, `top_level_parts` and `violations`, which already exist.

**What to build:** in the module Task 1 created, `tests_imports(walk) -> list[str]` returning one `"<module.path>: <name>"` entry for every name `Module.imported()` yields whose first dotted piece is exactly `tests`, across every module the walk returns (empty when the walk returns none), and one helper for the real-product check, handed a `BehaveWalk`, which asserts that `walk.root / ".behave"` is a folder with a message naming `.behave`, and that `tests_imports(walk) == []`. Then every test below. No file but this one changes.

#### Behaviours to verify (developer adds tests to `tests/architecture/test_behave_imports.py`, layer 6, no fake handed in)

- `test_a_root_without_a_behave_entry_passes` — layer 6 — fakes: none — `tests_imports` is `[]` and nothing is raised (CP-797)
- `test_an_import_from_tests_fails_listing_the_module` — layer 6 — fakes: none — `.behave/features/x.py` with `from tests import conftest`: the result holds an entry for that path naming `tests` or `tests.conftest`; the file is then rewritten without that line, kept on disk, and the result is `[]` (CP-800, CP-802)
- `test_an_import_inside_a_function_is_found` — layer 6 — fakes: none — `import tests` inside a function body is listed (CP-800)
- `test_the_remaining_forms_are_each_found` — layer 6 — fakes: none — `import tests.x as y`, `from tests.x import y` and `import tests` under an `if`, each in its own module; each module is listed (CP-800)
- `test_a_multi_name_import_lists_the_tests_name_only` — layer 6 — fakes: none — `import os, tests.x` is listed with `tests.x`, and no entry names `os` (CP-800)
- `test_every_site_in_one_run_is_listed` — layer 6 — fakes: none — `import tests.x` in `a.py` and `from tests.y import z` in `b.py`, both in `.behave/features/`; one call lists both modules (CP-802)
- `test_an_import_under_a_skipped_folder_is_not_listed` — layer 6 — fakes: none — `.behave/.venv/lib/pkg.py` holding `import tests`, beside a clean `.behave/features/a.py`: the result is `[]` (CP-798)
- `test_named_and_dot_folders_are_checked` — layer 6 — fakes: none — `.behave/tests/y.py` holding `from tests import conftest` and `.behave/.hidden/z.py` holding `import tests`: both paths are listed (CP-798, CP-800)
- `test_near_names_and_nested_names_are_checked` — layer 6 — fakes: none — `.behave/.venvs/a.py`, `.behave/features/__pycache__2/b.py`, `.behave/features/.venv/c.py` and `.behave/.behave/d.py`, each holding `import tests`: all four paths are listed (CP-798)
- `test_near_names_and_relative_imports_are_not_imports_from_tests` — layer 6 — fakes: none — `import testsuite`, `from tests_util import x`, `from .tests import y` in `a.py`, and `from . import x` in `.behave/tests/w.py`: the result is `[]` (CP-801)
- `test_third_party_standard_library_and_sibling_imports_pass` — layer 6 — fakes: none — `from behave import given`, `import httpx`, `import subprocess`, `from server_way_in import request_page`: the result is `[]` (CP-803)
- `test_the_real_behave_folder_passes_and_is_present` — layer 6 — fakes: none — the product's own `.behave/`, read only. The helper over `behave_walk_of()` passes; `modules()` read at least one module; no count is asserted (CP-804)
- `test_the_real_product_check_fails_when_the_root_holds_no_behave_folder` — layer 6 — fakes: none — the same helper over `behave_walk_of(tmp_path)`, a root with no `.behave`, raises `AssertionError` (CP-804)
- `test_the_root_walk_misses_a_planted_import_from_tests` — layer 6 — fakes: none — a root holding the six root files plus `.behave/features/x.py` with `from tests import conftest`: `violations(walk_of(root), part) == []` for every part in `PARTS`, `top_level_parts(walk_of(root)) == PARTS`, and the new check lists `.behave/features/x.py` (CP-806)
- `test_the_root_walk_misses_an_empty_behave_folder` — layer 6 — fakes: none — the same six root files plus an empty `.behave/`: the same two root-walk assertions hold, and the new walk raises naming `.behave` (CP-806)

Assert which modules and names appear, never how many entries the list holds (`from tests import y` lists both `tests` and `tests.y`).

#### Held by review

- CP-805 is a verification run, not a suite test. In a disposable clone at the commit under test (made with `mktemp -d`, the checks run in a subshell, removed afterwards from outside, per `<CORE>/roles/CROSS_ROLE.md` § *Every seat — a run leaves the product's main checkout as it found it*), append `import tests.conftest` to `.behave/features/command_way_in.py` and run `pytest products/tracker17/tests/architecture/`. Only the real-product test fails, and the QC-19 and QC-1 tests pass. The observable is that clone's test report.
- CP-796 — the module sits under `tests/architecture/` with a `test_` name, so the card's `Test command:` collects it. The observable is the card's run listing the module.
- QC-62 (Ruff format and lint) binds the new module and the edited `conftest.py` — a gate command, not a test.

#### Implement

Infer from failing tests.

# Hint: match on `name.split(".")[0] == "tests"`, never on a prefix, so `testsuite`, `tests_util` and `mytests` miss. `Module.imported()` yields both `tests` and `tests.conftest` for `from tests import conftest`, and `tests.x` once for `import os, tests.x`. Plant files as `test_source_walk.py`'s `_plant` does: each relative path under `tmp_path`, parents first. For the CP-806 roots plant the same six root files, under this module's own constant (that one is module-private there). Import `PARTS` and `top_level_parts` from `test_shapes` and `violations` from `test_imports`, as `test_source_walk.py` already imports from `test_shapes`.

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/architecture/test_behave_imports.py` from the worktree root, then the card's `Test command:`.

Pass criteria: this task's tests pass; the whole of `tests/architecture/` passes, with `test_behave_imports.py` collected by `pytest products/tracker17/tests/`; the e2e suite has no new failures; the CP-805 clone run shows only the real-product test failing.
