# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-28
- **Sources re-read:** None — no answer this run rests on a source outside this repository. RT-11's
  RFC and Chromium claims were not leaned on: the item asks which tests exist, and that is read on
  disk. Read at `958a36c7c`: `SDD.md` whole, and § 4 RT-11 (`:L440-L483`), § 6 S-7, § 11 R-12
  (`:L1558-L1570`), § 12, RN-56, RN-58, the header's *Inputs read*; the companion whole;
  `architecture_open_issues.md` whole; `adr/README.md`; `adr/0012-*.md` § Context and § Decision;
  `nfdr.md` header and QC-63; `web/routes.py` `_task_page` and `_pending_status` (`:L474-L490`,
  202 when a confirmation is pending); `tests/e2e/test_delete_task.py:L154-L218`;
  `tests/e2e/test_delete_project.py:L254-L327`; `tests/integration/test_delete_project_routes.py:L268-L308`;
  `tests/integration/test_delete_routes.py:L451-L478`; `git log` on the test files, which places the
  history tests in `delete-a-project`'s unit, merged at `ac09e56af`. Run in a fresh clone at
  `958a36c7c`: `pytest products/tracker17/tests/integration/test_delete_routes.py
  products/tracker17/tests/integration/test_delete_project_routes.py` — 85 passed. The end-to-end
  pair was not run: the clone's interpreter has no `playwright`, so both are read on disk; the
  whole-suite pass of 2556 is the PM's record in `architecture_open_issues.md` § 3.1, not this
  run's. The seed `2026-10-11_delete-and-rename` and the open station `2026-10-28_delete-a-project`
  were read as input and are cited nowhere in the answer.

## Items worked

### 5.1 — RT-11's test list and R-12's trigger still wait on deletion history tests that now exist

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** answered
- **Why:** Answered: RT-11's *Tests* and R-12's trigger name the four tests on disk, and the two
  "does not exist" / "once it exists" clauses go. Check 1: the edit lands in § 4 RT-11 and § 11
  R-12, both the CTO's own sections, and it binds nothing but the document's trace to the suite —
  mine, in the owner's seat. It is a correction, not a widening: the document states a test is
  missing that is present, so § *A widening item waits until it occurs* does not apply, and the
  item cites its occurrences anyway. Check 2: the item carries no draft and one question — name
  what exists — with three places it lands (RT-11's list, R-12's trigger, the project-deletion
  response test RT-11 omits); breadth, not a second question. Its supporting text is right on every
  line I checked: the four tests sit at the lines it names, and
  `test_live_delete_views_have_their_response_policy` asserts 202 on `?delete_confirm` at L455.
  Check 3: the tests test what RT-11 and R-12 say. R-12's trigger is "a return to a confirmation's
  address restored from history instead of loaded"; both history tests assert the confirmation's
  address is in the requests made on Back and that `pageshow` reported `persisted` false
  (`window.__shows == [False]`). The response-policy test asserts exactly RT-11's rule — 202 for a
  shown confirmation, 200 for back-out, failure and landing, `no-store` on each, 404 with no cache
  header for the deleted address — and `_pending_status` answers 202 when a deletion state is
  pending, so the product no longer diverges on the clause RN-56 records. RN-56 is a dated record
  pinned to `4a9ff47d2` and stays, as the SDD's own precedent for RN-49 says; the answer tells the
  fold so, because the fold would otherwise read it as a line to fix. Nothing settled moves and no
  earlier answer this run exists to contradict. Check 4: *stale* is the real path — named tests go
  stale when renamed, which the document already accepts by naming tests throughout, and the
  answer pins the merge they landed in (`ac09e56af`) so a later reader can date the claim; *absent*
  — the end-to-end pair could not be run here, and the answer says they were read, not run, rather
  than claiming a pass; empty, concurrent and refused do not reach a list of test names. I was not
  close to another verdict.

## Left for the owner

None this run.

## Skipped

None this run.

## Raised on this document

### 2.1 — § 4 RT-11, § 12 and the header still read the records at ADR-0011 and NFDR version 16

- **What the document is owed:** RT-11 names ADR-0012 as the record of its boundary, with ADR-0010
  superseded, and drops "theirs to write"; § 12 counts twelve records; the header reads ADR-0012
  and NFDR version 17.
- **Why it is worth a cycle:** *A fact in it is now false* — three of them, measured on disk at
  `958a36c7c`: `SDD.md:L474-L478` sends the reader to `adr/0010-…` and says the deletion record
  "is theirs to write"; `:L1581-L1582` says "ADR-0001 to ADR-0011"; `:L6` says "ADR-0001 to
  ADR-0011 … NFDR Settled (version 16". `adr/README.md` lists ADR-0012 Accepted 2026-10-28 and
  ADR-0010 "Superseded by ADR-0012"; `nfdr.md` is at version 17; both landed at `d459f69d9`. The
  doubt, stated in the item: the fold's own input catch-up has caught ADR-0011 and NFDR versions
  before (RN-52, cycle-9), so it may reach these lines unprompted; raising costs nothing extra
  because it rides the round § 5.1 already owes, and leaving it would trust a catch-up nobody is
  watching. One item, not three, because the three lines are one consequence of one landing.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
