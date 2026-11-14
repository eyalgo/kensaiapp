# Architecture open issues — tracker17

> Companion to `adr/` and `nfdr.md`. The Principal Architect authored both records
> non-interactively; this file holds what the run could not settle from its inputs — the SRS, the SDD
> and the FDR.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `product-architecture`. It folds your answers into the records and drops the resolved items.
> When nothing is left open, `product-architecture` **deletes this file**: no file = the records are
> done.
>
> Your answers are never thrown away. Each time the Principal Architect folds them in, it first copies
> this file whole to `docs/trail/architecture/` — so what you decided, and why, stays readable and
> citable for good.
>
> **§ 3 is raised, not asked.** These records bind every later change, so the seats that live under
> them find gaps the authoring run could not. § 3 is where such a seat says so, against both records
> — an ADR's binding and an NFDR obligation reach the same file.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 QC-64 still reads as unmet, and the tree now meets it
- **Raised by:** PM — 2026-11-14
- **Which record:** `nfdr.md` QC-64, its *verified by* tail
- **Tracked by:** `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract`
- **What it blocks:** nothing runs on it; a reader takes the entry as unmet when it is met
- **Where it shows:** QC-64 ends "The entry starts unmet: at `373ecc8a8` neither the test-support
  module nor a contract suite exists, and 64 classes across 26 modules under `tests/`, `tests/e2e/`
  included, stand in for the clock or the saver". That is now false. `tests/fakes.py` holds both
  fakes, `FakeSaver` and `FakeClock`. `tests/integration/test_saver_contract.py` and
  `tests/integration/test_clock_contract.py` hold the two suites, each run both ways.
  `tests/architecture/test_contract_fakes.py` holds the layer-6 walk, its run over the product
  (`test_the_product_keeps_every_contract_with_one_fake_and_a_suite_run_both_ways`) and one failure
  test for each case the tail names. `grep -rEln --include='*.py' '^\s+def (now|save)\(' tests` prints
  only `tests/fakes.py`. The tail should say the entry is met, name those four files and the walk's
  run, and keep the dated start as "started unmet at `373ecc8a8`", in the form QC-39 uses.
- **If a document has to be written:** none.
- **Answer:**

**How it closes.** `product-architecture` folds it on its next run like any other item here.
