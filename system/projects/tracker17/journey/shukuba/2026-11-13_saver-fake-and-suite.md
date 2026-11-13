# 宿場 Shukuba — one Saver fake and its contract suite

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract`. Slug: `saver-fake-and-suite`.*

## What it is

NFDR QC-64 and SDD § 4 TS-6 give the `Saver` contract (`application/contracts.py`, method `save`) one fake, written once in one test-support module under `tests/`, and one contract suite at layer 2 that runs twice: handed `persistence`'s `SavedData` (working in a folder the test makes) and handed the fake. This station creates that module, the fake and the suite, and moves every test's own `save` stand-in onto the fake, adding to the fake any behaviour a test needed, with that behaviour's case in the suite. It is the first of the seed's two fake stations; `Clock` is the next, and this one creates the shared module.

## Reached when

All hold at the station's merge commit, checked from `products/tracker17`:

1. A test-support module exists under `tests/` (QC-64's example name is `tests/fakes.py`) and defines one class with `save`, the `Saver` fake. `pytest tests/` collects a contract suite for `save` that has two runs, one handed `SavedData` over a `tmp_path` folder and one handed the fake.
2. The suite holds at least one case that fails the fake when the fake is made to break the contract, shown by a test or a recorded mutation: a fake whose `save` is changed to drop the state fails the suite while `SavedData` still passes.
3. `grep -rEn --include='*.py' '^\s+def save\(' tests` (extended regex, case-sensitive, over `tests/` including `tests/e2e/`) matches in exactly one file, the test-support module, and `grep -rEln --include='*.py' '^\s+def save\(' tests | wc -l` prints `1`. Before this station the same two commands matched 44 lines in 20 files (measured 2026-11-13 at `22365380e`), `Quiet` and `RecordingEverything` among them, so the pattern can appear.
4. `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` passes, run from the repository root as the project card's Test command does, and production code under `application/`, `domain/`, `persistence/`, `web/` and `main.py` is unchanged: `git diff --stat <base>..HEAD -- products/tracker17 ':!products/tracker17/tests'` lists no file outside `tests/`.

## Guardrail

- A fake that fails its suite fails the run: the fake is never loosened to pass a test; a test needing more adds it to the fake, with its case in the suite.
- Production code stays as it is; if the contract needs a change, it is raised, not made here.
- The fake does not inherit from `Saver` and `SavedData` is not subclassed or patched, per QC-3 (a class satisfies a contract by having the method).
- No `Clock` stand-in moves here; `now` stand-ins stay where they are until the Clock station.
- **Not here:** the `Clock` fake and its suite, and the layer-6 walk that keeps the whole shape, are items 2 and 3 of the same seed, `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract`.
