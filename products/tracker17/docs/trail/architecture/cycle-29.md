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
> **No producing run wrote this file.** The PM opened it on 2026-11-13, in a route review, to carry
> item § 3.1. `product-architecture` has no record of writing it. It exists because QC-19's second
> clause over `.behave/` now has its own walk and test, and three lines of the NFDR still describe
> the time before it.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 QC-19's second clause over `.behave/` is met by its own walk; three NFDR lines predate it
- **Raised by:** PM — 2026-11-13
- **Which record:** `nfdr.md` § 1.2 preamble; § 1.1 QC-1, *verified by*; § 1.2 QC-19, *verified by*
- **Tracked by:** `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder`
- **What it blocks:** nothing is blocked. Two lines state as true what no longer is, and one states
  as owed a walk that exists, so a reader of either looks for the wrong test.
- **Where it shows:**
  - `nfdr.md:L201-L203`, § 1.2 preamble — "Every entry is verified by one layer-6 test that walks
    the imports of every module on disk". QC-19 is now verified by two: the root import walk and
    `tests/architecture/test_behave_imports.py`. Say each entry is verified by a layer-6 import walk,
    and that QC-19's second clause over `.behave/` has a walk of its own, which fails as the others
    do when it finds nothing.
  - `nfdr.md:L42`, QC-1 *verified by* — "The source walk under it, which the import and reach walks
    of §§ 1.2, 1.3, 3 and 8 share". The walk of `.behave/` does not share it: `tests/conftest.py:L171`
    holds `class BehaveWalk`, separate from `SourceWalk` (`:L139`), and it reads `.behave/` by its own
    rule, skipping only `.behave/.venv/` and `__pycache__`. Name that walk as the exception.
  - `nfdr.md:L242-L246`, QC-19 *verified by* — names "a walk of that folder that fails on an import
    from `tests` and, while the folder exists, on finding no module in it" as a thing wanted. It is
    met: say so, name `test_behave_imports.py` and
    `test_the_real_behave_folder_passes_and_is_present`, and cite the mutation that fails it, as
    QC-1's and QC-39's tails do. Measured 2026-11-13 in a disposable clone at `69265afe1`:
    `tests/architecture/` gave 120 passed; with `import tests.conftest` appended to
    `.behave/features/command_way_in.py`, 1 failed, 119 passed, the one failure that test.
- **If a document has to be written:** none. The record changes through `product-architecture`.
- **Answer:** confirm, with one addition. The three lines change as the item asks. § 1.2's preamble
  says each entry is verified by a layer-6 import walk, and that QC-19's second clause over
  `.behave/` has a walk of its own, `BehaveWalk` in `tests/conftest.py`, which fails as the others do
  when the folder holds no module. QC-1's *verified by* names `BehaveWalk` as the one walk that does
  not share the source walk: it reads `.behave/` by its own rule, skipping only `.behave/.venv/` and
  `__pycache__`. QC-19's *verified by* says the second clause is met, names
  `tests/architecture/test_behave_imports.py` and `test_the_real_behave_folder_passes_and_is_present`,
  and cites the mutation: re-measured 2026-11-13 in a disposable clone at `1d7ac1a03`, whose code is
  `69265afe1`'s, `tests/architecture/` gave 120 passed, and with `import tests.conftest` appended to
  `.behave/features/command_way_in.py`, 1 failed, 119 passed, the one failure that test. The
  addition is the absent case. `BehaveWalk` reads nothing when `.behave/` is absent, but
  `test_the_real_behave_folder_passes_and_is_present` fails then: with `.behave/` moved away, 1
  failed, 27 passed. So QC-19's "while the folder exists" describes the walk, not the product's test.
  The met sentence says the product's test also fails when the root holds no `.behave/`, so a change
  that removes the folder, which QC-1's "may also hold" allows, changes that test with it. This is
  unlike QC-39's pins checks, which read nothing then. Reasoning:
  `trail/architecture/self_answer-33.md`.

**How it closes.** `product-architecture` folds it on its next run like any other item here.
