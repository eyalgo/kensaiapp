# Change request — 2026-11-13_pins-test-reads-behave-lock

---

**Request:** NFDR QC-39 holds two sets of test dependencies to one bar: the suite's (`pyproject.toml`, `uv.lock`) and the Behave folder's (`.behave/pyproject.toml`, `.behave/uv.lock`). `products/tracker17/tests/architecture/test_pins.py` reads only the root pair (`grep -n -i behave tests/architecture/test_pins.py` matches nothing today). Make it read the Behave folder's pair by the same three checks QC-39 names: every declared dependency pinned with `==`, a lock file present, and each declared dependency fixed by the lock at its declared version. Hold each case with a test in that file: a dependency not pinned with `==` fails; a `.behave/` with no `pyproject.toml` fails; a `.behave/` with no `uv.lock` fails; a declared dependency that `.behave/uv.lock` does not fix at that version fails; an absent `.behave/` reads nothing and passes (QC-1 lets the folder be absent). Each failing case is run against a temporary copy of the product whose `.behave/` is made to hold that case, and fails there. Prove it is a real guard: in a disposable copy, change `playwright==1.65.1` to `playwright==1.65.0` in `.behave/pyproject.toml` only; `uv run --locked --project . pytest tests/architecture/test_pins.py` then fails, and with the change reverted it passes. The change is the one test file; production code is not touched. Both suites pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and the same on `products/tracker17/tests/e2e/`, and the last line of each is read.

Sizing: one capability (the pins test holding the Behave folder's manifest and lock to QC-39), one merge; the acceptance boundary is the station's reached-when 1 to 4, per NFDR QC-39. The root checks keep reading the root manifest and `uv.lock` as they do and their tests stay green and unweakened. `.behave/pyproject.toml` and `.behave/uv.lock` must stay byte-identical; the mutation runs in a copy only. `uv lock --check --project .behave` must stay a `development-design` review bar (NFDR § 10) and is not moved into the suite. The contract-suite and source-walk seeds are other changes and are not part of this one.

**Category:** nfdr
**Behaviour:** changing
**Classified because:** the station's reached-when has the pins check gain rules over `.behave/` (a check that gains a rule changes what an enforcement command reports), and it is driven by NFDR QC-39.

**Sealed:** 2026-11-13 — accepted; merged to `main` via `--no-ff`.
Environment: owners-mac — no CI
