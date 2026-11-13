# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-11-13
- **Sources re-read:** None. The answer rests on the product's own test fixture, its test module
  and a run of them, all in this repository; no claim it leans on comes from a source outside it.

## Items worked

### 3.1 — QC-19's second clause over `.behave/` is met by its own walk; three NFDR lines predate it

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** confirmed with addition
- **Why:** The three changes the item asks for are right, and one case is added: what happens when
  `.behave/` is absent.
  1. **This is a correction, not a widening.** The item says two lines of `nfdr.md` state as true
     what no longer is, and one states as wanted a walk that exists. It asks for nothing new to be
     required, so § *A widening item waits until it occurs* does not apply. The edit lands in
     `nfdr.md`, this companion's document, and commits nobody outside it, so it is answered in the
     owner's seat. It is one question with three places to land, not two questions, so it does not
     split. The item carries its own wording, so it was weighed as a draft.
  2. **The facts are true, measured on disk.** `tests/conftest.py` line 139 holds `class SourceWalk`
     and line 171 `class BehaveWalk`. `BehaveWalk` skips a first piece below the folder named `.venv`
     and any piece named `__pycache__`, by exact name, and reads every other folder.
     `tests/architecture/test_behave_imports.py` holds
     `test_the_real_behave_folder_passes_and_is_present`. `nfdr.md` lines 201–203, 42 and 242–246
     read as the item quotes them. This run repeated the mutation in a disposable clone at
     `1d7ac1a03`. Nothing outside `docs/` changed between `69265afe1` and `1d7ac1a03`.
     `tests/architecture/` gave 120 passed. With `import tests.conftest` appended to
     `.behave/features/command_way_in.py`, it gave 1 failed and 119 passed, and the one failure was
     that test. Those are the item's numbers.
  3. **Each line's fix holds.** The § 1.2 preamble's "one layer-6 test" is false for QC-19, which now
     has two walks. QC-1's "which the import and reach walks of §§ 1.2, 1.3, 3 and 8 share" is false
     for the walk of `.behave/`, which is a § 1.2 walk that does not use `SourceWalk`. QC-19's tail
     names as wanted a walk that exists. Naming the test and the mutation follows how QC-1 and QC-39
     already state that they are met.
  4. **Addition — the absent case.** The item's preamble wording says the new walk "fails as the
     others do when it finds nothing". That holds for a `.behave/` that is empty. It does not
     describe an absent one. `BehaveWalk.modules()` returns nothing when the folder is not there.
     But the product's test, `check_behave_folder`, asserts the folder is present. With `.behave/`
     moved out of the clone, `test_behave_imports.py` gave 1 failed and 27 passed, the one failure
     `test_the_real_behave_folder_passes_and_is_present`. So QC-19's "while the folder exists"
     describes the walk and understates the product's test. QC-1 says the root "may also hold"
     `.behave/`, and QC-39's pins checks read nothing when it is absent. A reader of the NFDR would
     take removing the folder as a change no test notices, and this test does notice it. So the met
     sentence says the product's test also fails when the root holds no `.behave/`, and that a change
     removing the folder changes that test with it. That does not contradict QC-1: the entry allows
     the folder to be missing, and the test is stricter than the entry, on purpose (its own docstring
     cites CP-804, "cannot pass by reading nothing").
  5. **What stays.** QC-19's first-clause tail, the import walk that skips `tests/` and `.behave/` by
     name, is still true. § 10's QC-19 row (`pytest tests/` · layer 6) still names the command that
     runs both walks, so it stays. § 9's "Every layer-6 walk fails when the directory it walks holds
     no module" is not made false: an empty `.behave/` fails the walk, and an absent one fails the
     product's test. QC-39's pins checks already read nothing when the folder is absent, and their
     own tail says so. RN-66's "It holds today", RN-76 and RN-78 are dated notes and stay as written.
     Nothing in `adr/` moves: this corrects statements about a check and decides nothing.
  6. **Failure cases.** *Empty:* the walk fails on a `.behave/` with no module, which
     `test_an_empty_behave_folder_fails_naming_the_folder` asserts. *Absent:* the addition above.
     *Stale:* the met sentence names the commit and date of its measurement. *Concurrent* and
     *refused* reach nothing: the entry records a check, and no second actor or refusal changes what
     it says. The near miss was plain **confirmed**. The absent case tipped it, because the item's
     wording and the current QC-19 tail both leave it out.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/nfdr.md** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
