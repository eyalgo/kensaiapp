# 根回し Nemawashi seed — each contract has one fake and one contract suite

## What it is

Serves the Way `product-downstream`: tracker17 is the product the owner runs the crew on (`products/tracker17/docs/PRD.md:L12-L14`), so this moves a product rather than machinery (my reasoning, not a lookup). Moves the Agari toward **Simple to read** (a reader tracing a feature to its tests meets one fake, not 64) and keeps **Works** true (the suite's integration layer).

`application/contracts.py` states two contracts, `Saver` (`save`) and `Clock` (`now`). NFDR QC-64 says each has one fake, written once in one test-support module under `tests/`, and one contract suite run against the real implementation and the fake. Neither exists: `ls products/tracker17/tests/fakes.py` → no such file, and `grep -rEn "^\s*class \w*(Clock|Saver)\w*" tests --include='*.py' | wc -l` → 64 classes, `grep -rEln` the same → 26 modules, including `tests/e2e/` (run from `products/tracker17`, 2026-11-13, at `db8e9b81b`). After this, one module holds both fakes, each fake passes the suite the real class passes, no other test module defines a stand-in, and a layer-6 walk keeps it so.

## Source

Cut from `products/tracker17/docs/nfdr.md` QC-64 ("The entry starts unmet: at `373ecc8a8` neither the test-support module nor a contract suite exists"); `products/tracker17/docs/SDD.md` § 4 TS-6; `products/tracker17/application/contracts.py`. Named as owed by `tracker17 · nemawashi · 2026-10-30_a-path-with-a-non-text-byte-is-printed`'s refine report (`system/projects/tracker17/docs/nemawashi-refine/2026-10-30_a-path-with-a-non-text-byte-is-printed_report.md`, next move 1). Count re-measured now; the NFDR's 64 and 26 still hold.

## Stations — dynamic checklist

- [x] saver-fake-and-suite — one `Saver` fake in a new test-support module under `tests/`; a layer-2 contract suite for `save` that passes handed `persistence`'s `SavedData` and handed the fake; no test module outside it defines a class with `save`, the five by other names (`Quiet`, `RecordingEverything`) included — `pytest tests/` passes
- [ ] clock-fake-and-suite — one `Clock` fake in that module; a layer-2 contract suite for `now` that passes handed `main.SystemClock` and handed the fake; no test module outside it defines a class with `now` — `pytest tests/` and `pytest tests/e2e/` pass
- [ ] the-qc-64-walk — the layer-6 walk reads `save` and `now` off the `Protocol` classes and passes on the tree; a test per case shows it fails on a stand-in outside the module, on a subclass of the module's fakes, on a missing module, on a contract with no fake, on a contract with no suite run both ways, and on reading no method; `pytest tests/` passes, so one module holds both fakes and nothing else stands in

Route re-cut at pick, three stations kept. Bars now test methods, not names, because `Quiet` and `RecordingEverything` define `save` under names the 64-class count misses (69 classes, 26 modules by method, measured 2026-11-13). The two fake stations are independent of each other and may be walked in either order; only the walk must come last. The last bar carries the seed's whole end state, which the cutter's bar left to the sum of the first two.

## Relation to existing work

The walk goes last: it fails while any stand-in remains. Independent of the two other seeds cut the same day, `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder` and `tracker17 · nemawashi · 2026-11-13_the-pins-test-reads-the-behave-lock`.

## Out (later / elsewhere)

Production code stays as it is. A third contract is bound the day it lands; none is added here.
