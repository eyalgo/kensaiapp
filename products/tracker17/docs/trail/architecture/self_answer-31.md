# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-11-13
- **Sources re-read:** None. The answer rests on the product's own test file and manifests, which
  are in this repository; no claim it leans on comes from a source outside it.

## Items worked

### 3.1 — QC-39 says its Behave half starts unmet in its test; the pins test now reads both pairs

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** confirmed with addition
- **Why:** The change the item asks for is right, and QC-39 should say both halves are met. Two
  more edits come with it.
  1. **This is a correction, not a widening.** The item says a statement in the entry is now false
     and asks for nothing new to be stated, so § *A widening item waits until it occurs* does not
     apply. The edit lands in `nfdr.md`, which is this companion's document, and it commits nobody
     outside it. So it is answered in the owner's seat.
  2. **The fact is false, measured.** `nfdr.md` lines 435–438 say that `test_pins.py` "reads only the
     root `pyproject.toml` and `uv.lock`". On disk, `tests/architecture/test_pins.py` line 83
     defines `behave_findings`, which reads `.behave/pyproject.toml` and `.behave/uv.lock` by
     QC-39's three checks: pinned with `==`, lock present, each pin fixed by the lock. Line 160's
     `test_the_behave_folder_of_the_product_holds_every_pin` runs it over the product. This run
     repeated the item's mutation in a disposable clone at `7caae544a`: 25 passed;
     `playwright==1.65.1` moved to `1.65.0` in `.behave/pyproject.toml` alone gave 4 failed and 21
     passed; reverted, 25 passed. These are the item's counts, at a later commit.
  3. **Addition 1 — a second sentence is a forecast that has come true.** Right after "starts
     unmet", QC-39 says `declared_dependencies` "already reads `[project] dependencies` … so the
     same two checks run over the second manifest". That described how the change would work before
     it landed. It goes with the "starts unmet" sentence, and the met half says, in the present
     tense, what the test reads. The item asked only for the first sentence, which is the narrowing
     check 2 names.
  4. **Addition 2 — keep the history in the entry.** The root's half is written as "started unmet
     at `9219be1e1` … Verified when the lock landed". The Behave half should read the same way:
     started unmet at `<a commit not in the public history>`, verified 2026-11-13 by the mutation above. That way the entry
     still records that it was ever unmet, without stating the gap as current.
  5. **What stays.** RN-54's and RN-69's "QC-39 starts unmet" are dated notes, and the item rightly
     leaves them as written. QC-1's "starts unmet" is still true: `tests/conftest.py` line 142 still
     skips every path piece that begins with a dot. QC-64's is still true too: `tests/` holds no
     test-support module of fakes. So neither of those changes, and nothing in `adr/` changes. The
     rest of QC-39's *verified by* still agrees with the test. It says an absent `.behave/` reads
     nothing (lines 86–87), a folder with no manifest or no lock fails, and the pins test does not see a
     lock file that still carries a package its manifest dropped. § 10's QC-39 rows stay as they
     are.
  6. **Failure cases.** *Stale:* the new text names the commit it was measured at, so a later
     reader can tell how old the measurement is. *Absent:* already covered by the entry, as above.
     *Concurrent* and *refused* reach nothing here: the entry is a record of a check, and no second
     actor or refusal changes what it says. The near miss was plain **confirmed**. Addition 1 tipped
     it, because once the "starts unmet" sentence goes, the forecast sentence left behind would
     describe a change that has already happened.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/nfdr.md** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
