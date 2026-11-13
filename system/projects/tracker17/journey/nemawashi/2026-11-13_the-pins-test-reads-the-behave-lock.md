# 根回し Nemawashi seed — the pins test holds the Behave folder's lock

## What it is

Serves the Way `product-downstream`: the same product, the same reading (my reasoning, not a lookup). Moves the Agari toward **Works** and **Simple to set up** (a lock that cannot drift from its manifest).

NFDR QC-39 holds two sets of test dependencies to one bar: the suite's (`pyproject.toml`, `uv.lock`) and the Behave folder's (`.behave/pyproject.toml`, `.behave/uv.lock`). `tests/architecture/test_pins.py:L18` reads only the root manifest and `uv.lock`: `grep -n -i behave tests/architecture/*.py` → no match (run from `products/tracker17`, 2026-11-13, at `db8e9b81b`). The facts hold today: both manifests pin `playwright==1.65.1`, and `uv lock --check --project .behave` resolves clean. After this, the pins test reads the second manifest and lock the same way and fails when the folder holds no manifest or no lock, and reads nothing when the folder is absent. QC-40's lock clause rides on it.

## Source

Cut from `products/tracker17/docs/nfdr.md` QC-39 and QC-40 ("QC-39 starts unmet in its test"), RN-66, RN-69; `tests/architecture/test_pins.py:L18-L49`.

## Stations — dynamic checklist

- [ ] pins-over-behave — `test_pins.py` fails on a `.behave/` dependency not pinned with `==`, on a `.behave/` holding no manifest or no `uv.lock`, and on a declared dependency its lock does not fix at that version, and reads nothing when `.behave/` is absent; a mutation moving one pin fails it; the suite stays green

The route stays one station: one test file, one capability, one merge. Divergence: the bar now names the missing-manifest and absent-folder cases that the seed's `## What it is` states and the line omitted.

## Relation to existing work

Follows the root's half, `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv`, retired to `trail/`. Independent of `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` and `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder`.

## Out (later / elsewhere)

`uv lock --check --project .behave` is a `development-design` review bar by NFDR § 10, not a test; this seed does not move it into the suite.
