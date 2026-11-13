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
> item § 3.1. `product-architecture` has no record of writing it. It exists because QC-1's
> *verified by* still says the entry starts unmet in its test, and the source walk now skips by name.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 QC-1 says it starts unmet in its test; the source walk now skips by name
- **Raised by:** PM — 2026-11-13
- **Which record:** `nfdr.md` QC-1, *verified by*
- **Tracked by:** `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder`
- **What it blocks:** nothing is blocked. QC-1 states as current a gap the product no longer has, so
  a reader of the entry would look for work that is done.
- **Where it shows:** `nfdr.md:L44-L46` — "The entry starts unmet in its test: at `373ecc8a8`,
  `SourceWalk._all` in `tests/conftest.py` skips every path piece that begins with a dot, so a
  dot-folder holding code passes unseen". In the product, `tests/conftest.py:L129` holds
  `_SKIPPED_ROOT_FOLDERS = frozenset({"tests", ".behave", ".venv"})`, and
  `grep -nF 'startswith(".")' tests/conftest.py` prints nothing.
  `tests/architecture/test_source_walk.py:L48-L55`
  (`test_a_code_holding_dot_folder_fails_the_parts_comparison`) plants `.other/x.py` at a root and
  asserts the parts are not the five. Measured 2026-11-13 in a disposable clone at `6a0f1fe6c`:
  `tests/architecture/` gave 92 passed; with `tests/conftest.py` put back to `97603d4f3`,
  `test_source_walk.py` gave 6 failed, 1 passed. The entry is met: say the walk skips the three root
  folders and `__pycache__` by name, that `test_source_walk.py` fails on a code-holding dot-folder at
  the root, and date the unmet half to `97603d4f3`, as QC-39's tail dates its own. RN-66's "That test
  change has not landed" (`nfdr.md:L1858`) is a dated note and stays as written. QC-19's second clause
  over `.behave/` is still unmet and is not this item.
- **If a document has to be written:** none. The record changes through `product-architecture`.
- **Answer:** confirm, with one addition. QC-1's *verified by* says the entry is met: the source walk
  skips `tests/`, `.behave/` and `.venv/` by name at the product root only, and `__pycache__` by name
  at any depth, and `tests/architecture/test_source_walk.py` fails on a code-holding folder at the
  root whatever its name begins with. The unmet half is dated as QC-39's is: it started unmet at
  `97603d4f3`, where `SourceWalk._all` skipped every path piece beginning with a dot, and was verified
  2026-11-13 in a disposable clone at `9e5d92a3d`: `test_source_walk.py` gave 7 passed, and with
  `tests/conftest.py` put back to `97603d4f3`, 6 failed, 1 passed. The addition is the depth: the
  three folders count at the root only, which `test_a_dot_or_named_folder_inside_a_part_is_walked_as_that_part`
  asserts, and the entry's current words do not say. RN-66 and RN-76 are dated notes and stay as
  written; QC-19's `.behave/` clause and QC-64 are not this item. Reasoning:
  `trail/architecture/self_answer-32.md`.

**How it closes.** `product-architecture` folds it on its next run like any other item here.
