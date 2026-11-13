# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-11-13
- **Sources re-read:** None. The answer rests on the product's own test fixture and test module,
  which are in this repository; no claim it leans on comes from a source outside it.

## Items worked

### 3.1 — QC-1 says it starts unmet in its test; the source walk now skips by name

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** confirmed with addition
- **Why:** The change the item asks for is right: QC-1 should say the entry is met, and date the
  half that was unmet. One thing is added.
  1. **This is a correction, not a widening.** The item says a sentence in the entry is now false
     and asks for nothing new to be required, so § *A widening item waits until it occurs* does not
     apply. The edit lands in `nfdr.md`, this companion's document, and commits nobody outside it,
     so it is answered in the owner's seat. The item carries its own proposed wording, so it was
     weighed as a draft.
  2. **The fact is false, measured.** `nfdr.md` lines 44–46 say that `SourceWalk._all` "skips every
     path piece that begins with a dot". On disk, `tests/conftest.py` line 129 holds
     `_SKIPPED_ROOT_FOLDERS = frozenset({"tests", ".behave", ".venv"})`, line 130 skips
     `__pycache__`, `_all` tests the first path piece against the set, and
     `grep -nF 'startswith(".")' tests/conftest.py` prints nothing. This run repeated the item's
     mutation in a disposable clone at `9e5d92a3d`: `tests/architecture/test_source_walk.py` gave 7
     passed; with `tests/conftest.py` put back to `97603d4f3`, 6 failed and 1 passed. The item's 6
     failed, 1 passed matches; its 92 passed was over all of `tests/architecture/`, which this run
     did not re-run.
  3. **The dating holds.** The item dates the unmet half to `97603d4f3`, the way QC-39 dates its own
     to `<a commit not in the public history>`. `97603d4f3` is the last commit before the walk changed, and its
     `tests/conftest.py` line 142 still holds the `piece.startswith(".")` test. The entry's current
     `373ecc8a8` is also true, but it is when the entry was written, not when the gap ended.
     The mutation reverts to `97603d4f3`, so the date and the proof name the same commit.
  4. **Addition — say where each skip counts.** The item's wording, "skips the three root folders
     and `__pycache__` by name", leaves the depth implicit, and the entry's current words say
     neither. The fixture skips the three folders only as the first path piece under the root, and
     `__pycache__` at any depth. `test_a_dot_or_named_folder_inside_a_part_is_walked_as_that_part`
     asserts that `domain/.venv/x.py`, `domain/tests/x.py` and `web/.hidden/y.py` are walked as
     their parts. QC-2, QC-3, QC-4, QC-19 and the § 3 and § 8 walks rest on this walk, and a reader
     who takes "skips `tests/`" to mean any folder named `tests` would read their scope wrongly. So
     the met sentence names both depths.
  5. **What stays.** RN-66's "That test change has not landed" and RN-76's "QC-1's and QC-64's
     'starts unmet' lines are still true on disk" are dated notes, true when written, and stay as
     written. QC-64's "starts unmet" is a different entry and this item does not reach it. QC-19's
     second clause over `.behave/` is still unmet, as the item says, and is not this item. The rest
     of QC-1's *verified by* — the layer-6 test listing the root's parts — still agrees with the
     test, so it stays. § 10's QC-1 row (`pytest tests/` · layer 6) stays. Nothing in `adr/` moves.
  6. **Failure cases.** *Absent:* a root with no `.behave/` is walked the same way, which QC-1's
     "may also hold" already allows. *Stale:* the met sentence names the commit and date of its
     measurement, so a later reader can tell how old it is. *Empty:* the walk's own assertion fails
     on finding no module, which § 1.2 and § 9 already state. *Concurrent* and *refused* reach
     nothing: the entry records a check, and no second actor or refusal changes what it says. The
     near miss was plain **confirmed**. The depth addition tipped it, because the item's wording and
     the entry's both leave it to the reader.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/nfdr.md** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
