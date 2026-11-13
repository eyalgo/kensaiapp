# 宿場 Shukuba — a layer-6 walk of `.behave/` holds QC-19's second clause

*Item 2 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder`. Slug: `behave-import-walk`.*

## What it is

NFDR QC-19's second clause, no module outside `tests/` imports from `tests/`, binds `.behave/`, and its *verified by* asks a layer-6 walk of that folder that fails on an import from `tests` and, while the folder exists, on finding no module in it. The product's source walk skips `.behave/` by name, so no test reads it today, and the clause is true and unchecked. This station adds that walk in `products/tracker17/tests/architecture/`, taking `.behave/` as its own root and reusing `SourceWalk` and `Module.imported()`. It is one test file's worth of change; the root-folder walk is already by name (item 1, sealed).

## Reached when

1. A layer-6 test in `products/tracker17/tests/architecture/` walks `products/tracker17/.behave/` and passes on the real folder, which holds four modules in `features/` and its `steps/` today. Check: `ls products/tracker17/.behave/features/*.py | wc -l` → 4, and `uv run --locked --project products/tracker17 pytest products/tracker17/tests/architecture/` passes, run from the repository root in a disposable clone at the commit under test.
2. Against a root under `tmp_path` that holds `.behave/features/x.py` containing `from tests import conftest`, that walk fails; against the same root with the import removed it passes. Adding `import tests.conftest` or `from tests.x import y` to a real `.behave/features/*.py` in a disposable clone fails the test too, and the clone's `tests/architecture/` run is red on that test alone: the QC-19 test (`test_nothing_outside_tests_imports_third_party_or_tests`) and the QC-1 comparison keep passing.
3. Against a `tmp_path` root whose `.behave/` folder exists and holds no `.py` file, the walk fails with a message naming the folder; against a root with no `.behave/` folder at all it reads nothing and passes. The two failing cases are the ones that distinguish this walk from the root walk: pointed at the same planted root, the root `SourceWalk` at main's `HEAD` skips `.behave/` by name, reads no violation and no empty folder, so a test that took it as the walk would not fail them.
4. `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/` both pass, run from the repository root in a disposable clone at the commit under test.

## Guardrail

- The walk checks only the import-from-`tests` clause and the no-module-while-the-folder-exists clause; it does not ban third-party imports in `.behave/`, which QC-19's first clause exempts (`behave` is imported there).
- `SourceWalk` still skips `tests/`, `.behave/`, `.venv/` and `__pycache__` from the product root; the real root still walks to exactly the five parts.
- No product code, `.behave/` file or document changes; the NFDR already states this behaviour.
- A folder that is absent is not a failure: the walk must read nothing and pass.
- **Not here:** the by-name skip of the root walk is the sealed item 1, `tracker17 · shukuba · 2026-11-13_walk-skips-by-name`; `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` and `tracker17 · nemawashi · 2026-11-13_the-pins-test-reads-the-behave-lock` are other seeds.
