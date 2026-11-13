# Change request — 2026-11-13_walk-skips-by-name

---

**Request:** NFDR QC-1 says the source walk skips `tests/`, `.behave/` and `.venv/` by name and fails on any other root folder that holds a Python module. `SourceWalk._all` in `products/tracker17/tests/conftest.py` instead skips every path piece that begins with a dot, so code in any other dot-folder (say `.other/x.py`) passes unseen (`grep -nF 'startswith(".")' products/tracker17/tests/conftest.py` matches inside `_all` today). Change `_all` to skip `tests/`, `.behave/` and `.venv/` at the product root by name, and `__pycache__` anywhere, and to no longer test for a leading dot. Add a test in `products/tracker17/tests/architecture/` that builds a root under `tmp_path` holding the five parts, plus `tests/`, `.behave/features/x.py` and `.venv/x.py` (all skipped), plus `.other/x.py`, and asserts `top_level_parts(walk_of(root))` is not `PARTS` and contains `.other`. It must fail at `97603d4f3`, where the walk skips every dot piece, and pass once the walk is changed. A second case of the same root without `.other/` passes before and after and shows the three named folders stay skipped; removing `.other/x.py` makes the QC-1 comparison equal `PARTS` again. The change is one fixture and its tests; no product code, document or `.behave/` file changes. Both suites pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and the same on `products/tracker17/tests/e2e/`, each run from the repository root in a disposable clone at the commit under test, and the last line of each is read.

Sizing: one capability (the source walk skipping by name as QC-1 states), one merge; the acceptance boundary is the station's reached-when 1 to 4, per NFDR QC-1. The walk must keep skipping `tests/`, `.behave/`, `.venv/` and `__pycache__`, no module those skip may become visible, and the real product root must still walk to exactly `PARTS`. The layer-6 walk of `.behave/` (item 2 of the seed) and the other two seeds (`2026-11-13_one-fake-and-one-contract-suite-per-contract`, `2026-11-13_the-pins-test-reads-the-behave-lock`) are separate changes and not part of this one.

**Category:** nfdr
**Behaviour:** changing
**Classified because:** the station's reached-when has the source walk decide its verdict on a different basis (named folders, not a leading dot), so a code-holding dot-folder now fails QC-1 where it passed; a check whose verdict changes is a changed enforcement report, and it is driven by NFDR QC-1.

**Sealed:** 2026-11-13 — accepted; merged to `main` via `--no-ff`.
Environment: owners-mac — no CI
