# Self-answer report — `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-07
- **Sources re-read:** None. The one answer rests only on sources in this repository: the product's code and a suite run.

## Items worked

### 3.1 — QC-11's *verified by* tail and RN-21 still say the pointer test lacks its fourth check, which it now holds

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** confirmed with addition
- **Why:** The PM is right. Both sentences in `nfdr.md` are false at `HEAD`. QC-11's tail (`nfdr.md:109-111`)
  says "`tests/architecture/test_trace.py` holds the first three checks and not the fourth, which the code
  owes". RN-21 (`nfdr.md:765-767`) says "The reverse check is owed by the code … and tests only that each
  listed word has its module". The file now holds the fourth check:
  `test_each_feature_word_with_its_domain_module_is_listed_as_landed` (`test_trace.py:223-226`). It reads the
  words from `docs/SDD.md` when the suite runs (`:21`, `feature_words` at `:65-84`), and
  `test_the_reverse_check_can_fail` (`:229-236`) shows it fails on an unlisted word. Senior-engineer commit
  `30d4a85b0` landed it, and that commit is an ancestor of `HEAD` (`git merge-base --is-ancestor`). On a copy of
  `HEAD` made with `git archive`, `pytest tests/` gave 219 passed and 1 failed. The failure was
  `test_data_is_ignored_by_version_control`, which runs `git check-ignore` and needs a git checkout that the copy
  does not have, so it does not touch this item. The checks matching "reverse" or "feature_word_with" passed,
  5 of 5.
  This is a correction, not a widening, so § *A widening item waits until it occurs* does not apply. The edit
  lands in `nfdr.md`, the document this companion belongs to, and only that document's consistency depends on
  it, so the seat is this run's.
  **Addition 1:** the tail should also say that the fourth check fails when it reads no word from the SDD.
  `test_trace.py:225` asserts `feature_words()` before comparing, so a renamed table header cannot pass by
  finding nothing. This is the same no-empty-pass rule that § 1.2 and § 9 give every layer-6 walk, and a reader
  of QC-11 should not have to open the test to learn it holds here too. A missing `docs/SDD.md` fails loudly
  too: `:21` reads the file when the module is imported, so collection errors.
  **Addition 2:** the corrected tail should say what the file holds without a date. The clause that went false
  was the dated one, "On 2026-10-07 …", written on the same day the reverse check landed. A sentence about the
  code's state at a date goes stale silently. A sentence naming the check by its test name stays checkable with
  one grep.
  **Not moved:** no ADR changes, because the obligation and the decision are unchanged and only the description
  of the verifier was wrong.
  **Considered and not raised:** SDD RN-34 (`SDD.md:1597-1599`) says "On the day of the fold the test has the
  first direction … and not the reverse". That is a dated, past-tense Review Note and still true as history.
  SDD TS-4 and R-6 already describe the test as it now stands. So the SDD is owed nothing, and this run raised
  no item on it.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
