# 宿場 Shukuba — the source walk skips by name

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder`. Slug: `walk-skips-by-name`.*

## What it is

`SourceWalk._all` in `products/tracker17/tests/conftest.py` skips every path piece that begins with a dot, so code in any dot-folder passes unseen. NFDR QC-1 says the walk skips `tests/`, `.behave/` and `.venv/` by name and fails on any other root folder that holds a Python module. This station changes the walk to skip those three by name (and `__pycache__`), and adds the test that a module in another dot-folder at the product root is seen. One change to one fixture, one test; the `.behave/` walk is the next item.

## Reached when

1. In `products/tracker17/tests/conftest.py`, `SourceWalk._all` no longer tests `piece.startswith(".")`; it skips `tests/`, `.behave/` and `.venv/` at the root by name, and `__pycache__` anywhere. Check: `grep -nF 'startswith(".")' products/tracker17/tests/conftest.py` → no match (fixed-string, case-sensitive; it matches today at the line inside `_all`).
2. A test in `products/tracker17/tests/architecture/` builds a root under `tmp_path` holding the five parts, plus `tests/`, `.behave/features/x.py` and `.venv/x.py` (all skipped), plus `.other/x.py`, and asserts `top_level_parts(walk_of(root))` is not `PARTS` and contains `.other`. It fails at `97603d4f3`, where the walk skips every dot piece, and passes now. A second case of the same root without `.other/` passes at both commits and shows the three named folders stay skipped.
3. Removing `.other/x.py` from that root makes the QC-1 comparison equal `PARTS` again.
4. `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/` both pass, run from the repository root in a disposable clone at the commit under test.

## Guardrail

- The walk keeps skipping `tests/`, `.behave/`, `.venv/` and `__pycache__`; no module those skip becomes visible, and the real product root still walks to exactly `PARTS`.
- No product code, document or `.behave/` file changes; the NFDR already states this behaviour.
- **Not here:** the layer-6 walk of `.behave/` is item 2 of this seed, `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder`; `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` and `tracker17 · nemawashi · 2026-11-13_the-pins-test-reads-the-behave-lock` are other seeds.
