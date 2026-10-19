# Change request — 2026-10-07_reverse-pointer-test

*Opened from station `2026-10-07_a-project-that-stays` (item 1 of `tracker17 · nemawashi · 2026-10-07_first-project`). Fourth change unit of that station; the station may take more.*

---

**Request:** Make the pointer test fail in the reverse direction too. Run from `products/tracker17/` under `pytest tests/`. `tests/architecture/test_trace.py` today checks that a feature word listed as landed has its `domain/<word>.py` (`test_each_landed_feature_word_has_its_domain_module`), and nothing checks the other way. After this change it also holds a test that fails when a feature word in SDD § 4 TS-3's table has its `domain/<word>.py` and is not listed in `LANDED_FEATURE_WORDS`, so a slice that adds a feature module without adding its word to the test breaks `pytest tests/` (SDD § 4 TS-4, fourth clause; NFDR QC-11). The check reads only TS-3's words, so a `domain/` module that is no feature's entry (`refusals.py`, `state.py`, `text.py`) is never flagged. Where the table's words come from in code is the design's to settle, with the table in the SDD still the one place they are stated. Like its forward neighbour it ships with a test showing it can fail: a word with its module that is not listed is reported, and a listed word, or a module that is no feature's entry, is not. `pytest tests/` exits 0 on the product as it stands, where `projects` is the only word with a module and it is listed.

**Must not be weakened or added:** the existing checks in `test_trace.py` keep behaving as they do; no product behaviour changes, so no page, route, message or saved-data change; no tasks, People or All tasks links, rename or delete; no unreadable-data page and no second-tracker refusal; the setup README is not touched.

**Left to later change units of this station:** the check that the station's whole reached-when holds. The README is the next station.

**Sizing:** the acceptance boundary is one responsibility, keeping the trace between TS-3's feature table and the code honest in the reverse direction (SDD § 4 TS-4, fourth clause; NFDR QC-11; station reached-when 8). The check and the test that it can fail stay together (`pm_right_size.md` § *Right-size to one honest merge*). It is separate from the address-taken message the previous unit delivered, and from the station's final check of reached-when 1 to 7, which is verification and not a capability.

**Category:** nfdr
**Behaviour:** changing
**Classified because:** QC-11 says the pointer test "fails on … a feature word in that table that has its module and is not listed as landed", and `docs/nfdr.md` records that `tests/architecture/test_trace.py` "holds the first three checks and not the fourth"; a check that gains a rule changes what an enforcement command reports, though no product behaviour moves.

**Sealed:** 2026-10-07 — accepted; merged to `main` via `--no-ff`.
