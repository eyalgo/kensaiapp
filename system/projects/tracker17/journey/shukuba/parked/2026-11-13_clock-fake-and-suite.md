# 宿場 Shukuba — one Clock fake and its contract suite

*Item 2 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract`. Slug: `clock-fake-and-suite`.*

## What it is

NFDR QC-64 and SDD § 4 TS-6 give the `Clock` contract (`application/contracts.py`, method `now`) one fake, written once in the test-support module `tests/fakes.py` that the `Saver` station created, and one contract suite at layer 2 that runs twice: handed `main.SystemClock` (which reads the machine's clock and touches no file) and handed the fake. This station adds the `Clock` fake and the suite, and moves every test's own `now` stand-in onto the fake, adding to the fake any behaviour a test needed, with that behaviour's case in the suite. It is the second of the seed's two fake stations; the layer-6 walk is the third.

## Reached when

All hold at the station's merge commit, checked from `products/tracker17`:

1. `tests/fakes.py` defines one class with `now`, the `Clock` fake, beside the `Saver` fake. `pytest tests/` collects a contract suite for `now` that has two runs, one handed `main.SystemClock` and one handed the fake.
2. The suite holds at least one case that fails the fake when the fake is made to break the contract, shown by a test or a recorded mutation: a fake whose `now` returns a naive datetime (the contract is an aware UTC instant, as `SystemClock` returns) fails the suite while `SystemClock` still passes.
3. `grep -rEn --include='*.py' '^\s+def now\(' tests` (extended regex, case-sensitive, over `tests/` including `tests/e2e/`) matches in exactly one file, `tests/fakes.py`, and `grep -rEln --include='*.py' '^\s+def now\(' tests | wc -l` prints `1`. Before this station the same two commands matched 25 lines in 24 files (measured 2026-11-13 at `34ab71296`), so the pattern can appear.
4. `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/` both pass, run from the repository root as the project card's Test command does, and production code under `application/`, `domain/`, `persistence/`, `web/` and `main.py` is unchanged: `git diff --stat <base>..HEAD -- products/tracker17 ':!products/tracker17/tests'` lists no file outside `tests/`.

## Guardrail

- A fake that fails its suite fails the run: the fake is never loosened to pass a test; a test needing more adds it to the fake, with its case in the suite.
- Production code stays as it is; if the contract needs a change, it is raised, not made here.
- The fake does not inherit from `Clock` and `SystemClock` is not subclassed or patched, per QC-3 (a class satisfies a contract by having the method).
- The `Saver` fake and its suite stay as the previous station left them, except where a test needs a `Clock` case in a shared module.
- **Not here:** the layer-6 walk that keeps the whole shape is item 3 of the same seed, `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract`; the `Saver` fake is item 1, already reached.
