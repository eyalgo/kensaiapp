# 根回し Nemawashi seed — the pins test holds the Behave folder's lock

## What it is

Serves the Way `product-downstream`: the same product, the same reading (my reasoning, not a lookup). Moves the Agari toward **Works** and **Simple to set up** (a lock that cannot drift from its manifest).

NFDR QC-39 holds two sets of test dependencies to one bar: the suite's (`pyproject.toml`, `uv.lock`) and the Behave folder's (`.behave/pyproject.toml`, `.behave/uv.lock`). `tests/architecture/test_pins.py:L18` reads only the root manifest and `uv.lock`: `grep -n -i behave tests/architecture/*.py` → no match (run from `products/tracker17`, 2026-11-13, at `db8e9b81b`). The facts hold today: both manifests pin `playwright==1.65.1`, and `uv lock --check --project .behave` resolves clean. After this, the pins test reads the second manifest and lock the same way and fails when the folder holds no manifest or no lock, and reads nothing when the folder is absent. QC-40's lock clause rides on it.

## Source

Cut from `products/tracker17/docs/nfdr.md` QC-39 and QC-40 ("QC-39 starts unmet in its test"), RN-66, RN-69; `tests/architecture/test_pins.py:L18-L49`.

## Stations — dynamic checklist

- [x] pins-over-behave — `test_pins.py` fails on a `.behave/` dependency not pinned with `==`, on a `.behave/` holding no manifest or no `uv.lock`, and on a `.behave/` declared dependency that `.behave/uv.lock` does not fix at that version, and reads nothing when `.behave/` is absent, each case held by a test in the suite that fails at the commit before; a mutation moving one pin in `.behave/pyproject.toml` fails it; the suite stays green

The route stays one station: one test file, one capability, one merge. Divergence: the bar now names the missing-manifest and absent-folder cases that the seed's `## What it is` states and the line omitted.
Divergence, after the blind review (`docs/stations-blind-review/2026-11-13_the-pins-test-reads-the-behave-lock_review.md`): the lock clause and the mutation now name `.behave/`, since read over the root both already pass today; each case is held by a test in the suite. Readings settled: "QC-40's lock clause rides on it" is a note, not work, since QC-40 is a review gate with no test row (`docs/nfdr.md:L815`); "the same way" means QC-39's three checks (`docs/nfdr.md:L424-L425`).

## Relation to existing work

Follows the root's half, `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv`, retired to `trail/`. Independent of `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` and `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder`.

## Out (later / elsewhere)

`uv lock --check --project .behave` is a `development-design` review bar by NFDR § 10, not a test; this seed does not move it into the suite.
