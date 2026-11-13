# Deferred Decisions — walk-skips-by-name

What this change held back, for `shukuba-refine` to place after the unit lands.

---

## The layer-6 walk of `.behave/` — record gap, handed on by development-specs (2026-11-13)
**Record:** nfdr.md QC-19, its *verified by* for the second clause: "for the second clause over `.behave/`, a walk of that folder that fails on an import from `tests` and, while the folder exists, on finding no module in it"
**Product today:** no test walks `.behave/` — `tests/architecture/test_imports.py` and `tests/architecture/test_reach.py` hold no `behave` at `654de549c`; the source walk leaves `.behave/` out (`tests/conftest.py:141-143`), as it still will after this change
**Why not this change:** the request rules it out: "The layer-6 walk of `.behave/` (item 2 of the seed) … [is a] separate change and not part of this one"; this change alters the source walk's skip set and adds no module under `.behave/`
**Owner:** none — for shukuba-refine
**Status:** open
