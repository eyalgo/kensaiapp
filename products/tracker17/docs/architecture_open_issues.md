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

### 3.1 QC-64 points at a section `testing_python.md` does not have
- **Raised by:** PM — 2026-11-13
- **Which record:** `nfdr.md` QC-64, its *form* sentence and its *traces to* tail
- **Tracked by:** `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract`
- **What it blocks:** nothing runs on it; a reader following the pointer finds no § 2
- **Where it shows:** `nfdr.md` QC-64 says the fake is written "in the form
  `<CORE>/doctrine/engineering/testing_python.md` § 2 states" and traces to "`testing_python.md` § 2".
  That file numbers no section: its headings are *Layers 1–5*, *Rules*, *Layer 6 — Architecture* and
  *Layer 7 — Specification*, and the sentence QC-64 quotes ("the fakes live in a test-support module
  such as `tests/fakes.py`") stands in § *Rules*. Both pointers should name § *Rules*.
- **If a document has to be written:** none
- **Answer:** Confirmed, with one addition. `testing_python.md` numbers no section, and the sentence QC-64 quotes stands word for word in its § Rules, so both pointers name § Rules: the *form* sentence reads "in the form `<CORE>/doctrine/engineering/testing_python.md` § Rules states" and the trace tail reads "`testing_python.md` § Rules". The addition is the form: write it plain, `§ Rules`, as QC-64's own `testing_doctrine.md` § A fake is verified against its port's contract and every other doctrine pointer in this document is written, not italic. The quote stays as it is, and no obligation, check, § 10 row or record moves. Reasoning: `docs/trail/architecture/self_answer-34.md`.

**How it closes.** `product-architecture` folds it on its next run like any other item here.
