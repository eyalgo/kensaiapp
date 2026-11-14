# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-11-14
- **Sources re-read:** None. The answer rests on `nfdr.md` and the product's own test tree, both in
  this repository; no claim it leans on comes from a source outside it.

## Items worked

### 3.1 — QC-64 still reads as unmet, and the tree now meets it

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** confirmed with addition
- **Why:** The tail should say QC-64 is met, as the item says. Two things are added: the
  measurement, and what the fold leaves out.
  1. **This is a correction, not a widening.** The item says a sentence in QC-64 is now false. It
     asks the NFDR to require nothing new, so § *A widening item waits until it occurs* does not
     apply. The edit lands in `nfdr.md` and binds nobody outside it, so it is answered in the owner's
     seat. It is one question, so it does not split. The item proposes its own fix, so it was weighed
     as a draft.
  2. **The facts are true, read on disk at `1ed46ab17`.** `tests/fakes.py`,
     `tests/integration/test_saver_contract.py`, `tests/integration/test_clock_contract.py` and
     `tests/architecture/test_contract_fakes.py` all exist. Each suite has a real-side and a fake-side
     subclass: `TestSavedDataKeepsTheSaverContract` and `TestFakeSaverKeepsTheSaverContract`;
     `TestSystemClockKeepsTheClockContract` and `TestFakeClockKeepsTheClockContract`. The walk module
     holds the run over the product and a failure test for each case QC-64's tail names: a contracts
     file with no method, a stand-in class outside the support module, a class based on the fake, a
     missing support module, a contract with no fake, and a suite run against one side only. The
     item's grep prints only `tests/fakes.py`.
  3. **Measured in a disposable clone at `1ed46ab17`, 2026-11-14.** The walk module and the two
     suites gave 87 passed. With a class `LocalSaver` that defines `save`, put in a new module under
     `tests/unit/`, the walk's run over the product failed: 1 failed, 14 passed. With it removed, 15
     passed. The whole `pytest tests/` gave 3436 passed, 2 skipped. So the walk catches what it
     claims to.
  4. **Addition 1 — carry the measurement.** The item asks for QC-39's form. QC-39's tail does more
     than say "met": it names the date, the commit, and a mutation that fails the check. Without the
     measurement, QC-64's "met" would be a claim with nothing behind it. So the answer gives the fold
     the measured sentence.
  5. **Addition 2 — what the fold leaves out and leaves alone.** The item's *Tracked by* line names a
     journey seed. The NFDR cites nothing under `journey/`, so that line is not copied in. RN-65's
     "QC-64 starts unmet" and RN-82's mention of the dated reading are dated notes. They stay as
     written, as RN-57 left QC-39's. § 10's QC-64 row reads "suite", which is still true, so it does
     not move. No record in `adr/` changes.
  6. **Failure cases.** *Stale:* the "met" sentence is dated to `1ed46ab17`. A later stand-in class
     fails the walk in `pytest tests/`, so the sentence cannot go false without the suite going red.
     *Empty:* a third contract added to `application/contracts.py` with no fake fails the walk,
     because the walk reads the method names from the `Protocol` classes and not from a fixed list.
     *Absent*, *concurrent* and *refused* do not apply: the item is a statement about the tree.
     The near miss was plain **confirmed**. The missing measurement tipped it.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/nfdr.md** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
