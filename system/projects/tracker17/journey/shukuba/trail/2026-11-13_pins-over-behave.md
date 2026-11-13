# 宿場 Shukuba — the pins test reads the Behave folder's manifest and lock

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-11-13_the-pins-test-reads-the-behave-lock`. Slug: `pins-over-behave`.*

## What it is

`tests/architecture/test_pins.py` reads only the root `pyproject.toml` and `uv.lock`. This station makes it read `.behave/pyproject.toml` and `.behave/uv.lock` by the same three checks NFDR QC-39 names: every declared dependency pinned with `==`, a lock file present, and each declared dependency fixed by the lock at its declared version. The folder is a second set of test dependencies held to the same bar (`docs/nfdr.md:L418-L425`). A `.behave/` holding no manifest or no lock fails, and an absent `.behave/` reads nothing, which QC-1's "may also hold" allows. One test file, one capability, one merge.

## Reached when

Each is checked from `products/tracker17`:

1. `tests/architecture/test_pins.py` holds a test for each case over `.behave/`: a dependency not pinned with `==` fails; a `.behave/` with no `pyproject.toml` fails; a `.behave/` with no `uv.lock` fails; a declared dependency that `.behave/uv.lock` does not fix at that version fails; an absent `.behave/` reads nothing and passes. `grep -n -i behave tests/architecture/test_pins.py` matches (it matches nothing at the commit before this station).
2. Each of those tests fails when run against the test file at the commit before (`git stash` of the production change is not needed: the test file is the change, so the five cases are run against a temporary copy of the product whose `.behave/` is made to hold that case, and each case fails there; the absent-folder case passes there).
3. Mutation: change `playwright==1.65.1` to `playwright==1.65.0` in `.behave/pyproject.toml` only, in a disposable copy; `uv run --locked --project . pytest tests/architecture/test_pins.py` then fails, and with the change reverted it passes.
4. `uv run --locked --project . pytest tests/ -q` and `uv run --locked --project . pytest tests/e2e/ -q` both pass, and the last line of each is read.

## Guardrail

- The suite's own two checks keep reading the root manifest and `uv.lock` as they do; their tests stay green and unweakened.
- `uv lock --check --project .behave` stays a `development-design` review bar by NFDR § 10, and is not moved into the suite.
- `.behave/pyproject.toml` and `.behave/uv.lock` are left byte-identical; the mutation runs in a copy only.
- **Not here:** `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract`, and `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder`.
