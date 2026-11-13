# 根回し Nemawashi seed — the source walk sees the Behave folder

## What it is

Serves the Way `product-downstream`: the same product, the same reading (my reasoning, not a lookup). Moves the Agari toward **Works** (the layer-6 gates mean what they say) and **Simple to read** (the checked layout is the layout).

NFDR QC-1 says the root holds five parts and may also hold `.behave/`; the source walk skips `tests/`, `.behave/` and `.venv/` by name and fails on any other root folder that holds a Python module. `SourceWalk._all` in `tests/conftest.py:L138-L146` skips every path piece that begins with a dot, so code in any dot-folder passes unseen. QC-19's second clause binds `.behave/` too (no import from `tests`), and its tail names a walk of that folder, which does not exist: `grep -rn "\.behave" tests --include='*.py'` → no match (run from `products/tracker17`, 2026-11-13, at `db8e9b81b`). The folder holds modules today (`.behave/features/*.py`) and imports nothing from `tests` (`grep -rnE "^\s*(from|import) tests" .behave --include='*.py'` → 0), so the clause is true and unchecked. After this, the walk skips by name, a code-holding dot-folder other than `.behave/` fails QC-1, and a walk of `.behave/` fails on an import from `tests` and on finding no module while the folder exists.

## Source

Cut from `products/tracker17/docs/nfdr.md` QC-1 and QC-19 ("The entry starts unmet in its test"; "a walk of that folder that fails on an import from `tests`"), RN-66; `tests/conftest.py:L138-L146`; `tests/architecture/test_shapes.py:L135-L137`.

## Stations — dynamic checklist

- [ ] walk-skips-by-name — `SourceWalk` skips `tests/`, `.behave/` and `.venv/` by name, not by a leading dot; a test with a module in another dot-folder at the product root fails QC-1 (red at `97603d4f3`, where the walk skips every dot piece) and passes once the module is removed; both suites stay green
- [ ] behave-import-walk — a layer-6 walk of `.behave/` fails on an import from `tests` and on finding no module in it while the folder exists, reads nothing when the folder is absent; a mutation adding such an import to `.behave/features/*.py` fails it, and the QC-19 and QC-1 tests keep passing

## Relation to existing work

Independent of `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` and `tracker17 · nemawashi · 2026-11-13_the-pins-test-reads-the-behave-lock`.

Route re-cut (PM, 2026-11-13): the two stations stand as cut and stay two, one per NFDR entry; the bars are sharpened and the order is risk, not dependency: the second walk takes `.behave/` as its own root and needs nothing from the first, so either may go first. The first goes first because it changes the walk every import and reach test shares.

## Out (later / elsewhere)

Scenarios for tracker17 itself: NFDR § 9 states layer 7 has no producer, which this seed does not change.
