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
> item § 3.1. `product-architecture` has no record of writing it. It exists because QC-39's
> *verified by* still says the entry starts unmet in its test, and the pins test now reads the Behave
> folder's manifest and lock.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 QC-39 says its Behave half starts unmet in its test; the pins test now reads both pairs
- **Raised by:** PM — 2026-11-13
- **Which record:** `nfdr.md` QC-39, *verified by*
- **Tracked by:** `tracker17 · nemawashi · 2026-11-13_the-pins-test-reads-the-behave-lock`
- **What it blocks:** nothing is blocked. QC-39 states as current a gap the product no longer has, so
  a reader of the entry would look for work that is done.
- **Where it shows:** `nfdr.md:L435-L438` — "**The entry starts unmet in its test:** at `<a commit not in the public history>`,
  `test_pins.py` reads only the root `pyproject.toml` and `uv.lock`." In the product,
  `tests/architecture/test_pins.py:L83-L101` (`behave_findings`) reads `.behave/pyproject.toml` and
  `.behave/uv.lock` by QC-39's three checks, and
  `test_the_behave_folder_of_the_product_holds_every_pin` (`:L160`) runs it over the product. Measured
  2026-11-13 in a disposable clone at `789255723`: `test_pins.py` gave 25 passed; with
  `playwright==1.65.1` moved to `playwright==1.65.0` in `.behave/pyproject.toml` only it gave 4 failed;
  reverted, 25 passed. The full suite gave 3297 passed, 2 skipped, and `tests/e2e/` 122 passed. The
  change asked: say the Behave half is met, that `test_pins.py` reads both pairs, and cite that
  mutation (non-zero with the pin moved, 0 reverted). RN-69's "QC-39 starts unmet in its test" is a
  dated note and stays as written.
- **If a document has to be written:** none. The record changes through `product-architecture`.
- **Answer:** <the owner fills this in>

**How it closes.** `product-architecture` folds it on its next run like any other item here.
