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

### 3.1 QC-11's *verified by* tail and RN-21 still say the pointer test lacks its fourth check, which it now holds
- **Raised by:** PM — 2026-10-07
- **Which record:** `nfdr.md` § 1.1 QC-11 (the *verified by* tail, `nfdr.md:109-111`) and § NFDR Review Notes RN-21 (`nfdr.md:765-767`)
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_first-project`
- **What it blocks:** nothing is blocked; the record misstates what verifies QC-11. The tail says "On 2026-10-07 `tests/architecture/test_trace.py` holds the first three checks and not the fourth, which the code owes", and RN-21 says "The reverse check is owed by the code … and tests only that each listed word has its module". Both are now false.
- **Where it shows:** `tests/architecture/test_trace.py:223` `test_each_feature_word_with_its_domain_module_is_listed_as_landed` is the fourth check, reading TS-3's words from `docs/SDD.md` (`FEATURE_WORDS = feature_words()`, `:84`), and `:229` `test_the_reverse_check_can_fail` shows it can fail. `pytest tests/` passes with both (220 passed). The tail should say the file holds all four checks and that the fourth reads TS-3's words from `docs/SDD.md`; RN-21's last sentence should say the reverse check is in that file.
- **If a document has to be written:** none — the fold is an edit to `nfdr.md`, by `product-architecture`.
- **Answer:** confirm the correction, with one addition. Both sentences are false at `HEAD`: `tests/architecture/test_trace.py:223-226` is the fourth check, it reads TS-3's words from `docs/SDD.md` when the suite runs (`:21`, `:65-84`), and `:229-236` shows it can fail. Fold: QC-11's tail drops "On 2026-10-07 … which the code owes" and says the file holds all four checks, the fourth reading TS-3's words from `docs/SDD.md`; RN-21's sentence from "The reverse check is owed by the code" to "where a reader will hit it" says instead that the reverse check is in that file. Addition: the tail also says the fourth check fails when it reads no word from the SDD (`:225`, `assert feature_words()`), the rule § 1.2 and § 9 give every layer-6 walk, and it names what the file holds without a date, because the dated clause is what went false. No ADR moves. Reasoning: `trail/architecture/self_answer-7.md`.

**How it closes.** `product-architecture` folds it on its next run like any other item here.
