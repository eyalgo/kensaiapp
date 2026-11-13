# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-11-13
- **Sources re-read:** None. The answer rests on `core/doctrine/engineering/testing_python.md` and
  `nfdr.md`, both in this repository; no claim it leans on comes from a source outside it.

## Items worked

### 3.1 — QC-64 points at a section `testing_python.md` does not have

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** confirmed with addition
- **Why:** Both pointers should name § Rules, as the item says. The one addition is how to write it.
  1. **This is a correction, not a widening.** The item says a pointer names a section that does not
     exist. It asks the NFDR to require nothing new, so § *A widening item waits until it occurs*
     does not apply. The edit lands in `nfdr.md` and binds nobody outside it, so it is answered in
     the owner's seat. It is one question in two places, the *form* sentence and the trace tail, so
     it does not split. The item proposes its own fix, so it was weighed as a draft.
  2. **The facts are true, read on disk.** `testing_python.md` has four `## ` headings and no numbers:
     *Layers 1–5* (line 13), *Rules* (27), *Layer 6 — Architecture* (38) and *Layer 7 —
     Specification* (68). This holds in the pinned core and in this repository's `core/` alike. The
     fragment QC-64 quotes, "the fakes live in a test-support module such as `tests/fakes.py`", sits
     word for word in § Rules' bullet on the contract suite (line 32), which reads "In Python the
     fakes live in …". `nfdr.md` lines 343 and 360 read "`testing_python.md` § 2" as the item says.
     No other line in `nfdr.md` or in `adr/` cites a numbered section of `testing_python.md`.
  3. **Addition — the form.** The item writes the fix as "§ *Rules*", in italics. The NFDR writes a
     doctrine section by its plain heading: QC-64's own trace tail names "`testing_doctrine.md` § A
     fake is verified against its port's contract", and the other doctrine pointers follow the same
     pattern ("`arch_defaults.md` § The four layers", "`quality_defaults.md` § Dependencies"). Copied
     as the item writes it, the fix would make one pointer in the tail look different from the one
     beside it. So both read `§ Rules`.
  4. **What stays.** The quoted fragment is still true at its source, so it is not changed. QC-64's
     obligation, its *verified by* tail, its "starts unmet" sentence dated to `373ecc8a8`, § 10's
     QC-64 row and every record in `adr/` stay as they are: the change corrects where a citation
     points and decides nothing.
  5. **Failure cases.** *Stale:* a pointer by heading name stays true if `testing_python.md` gains or
     reorders a section, which a number does not. It goes false only if § Rules is renamed, and a
     search for the heading then finds the gap. *Empty*, *absent*, *concurrent* and *refused* reach
     nothing here: the item is a citation, and the work under way on the fakes does not touch it.
     The near miss was plain **confirmed**. Writing down the plain form tipped it, because the fold
     would otherwise copy the italic form from the item.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/nfdr.md** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
