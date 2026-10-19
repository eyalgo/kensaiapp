# Self-answer report — SRS.md

## Header

- **Companion:** products/tracker17/docs/SRS_open_issues.md
- **Document:** products/tracker17/docs/SRS.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-11
- **Sources re-read:** None. No answer rests on a source outside this repository. The answer rests on
  `PRD.md:9-29` (v6), the owner's own words at `docs/trail/prd/cycle-6.md:32`, and
  `README.md:3`, all read on disk this run.

## Items worked

### 3.1 — PRD § Purpose now wants the first thing a reader reads to name both purposes; the SRS states neither the second purpose nor that want

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the SRS
- **Verdict:** answered
- **Why:** The SRS takes PRD v6. It adds the second purpose to § 1, adds FR-41 for the README's
  opening, adds AC-21 to check it, and narrows RN-18's drop-line. The item carried no draft, so it was
  answered from scratch.
  - **Whose it is.** The edit lands in `SRS.md`, so the item belongs to this document. The decision
    was already made upstream. The owner confirmed the second purpose and its first-read want in
    PRD v6 (`PRD.md:23-29`, from `trail/prd/cycle-6.md` § 1.1). Nothing here binds a person, money or
    a risk. What is left is how the SRS states a want the PRD has already settled.
  - **Widening, but it occurs.** The item asks the SRS to state a requirement it does not state now,
    so it widens the document. It also cites an occurrence: `README.md:3` names only the first
    purpose, and `grep -n -i 'testing ground' products/tracker17/README.md` printed nothing and exited
    1 on this run. So the "not until it occurs" rule does not apply. It is also an upstream move the
    SRS has not seen. Its Inputs line reads "PRD Settled (v5)" (`SRS.md:6`), and RN-18's claim that
    § Purpose "require[s] no behaviour" (`SRS.md:620-621`) is no longer true of § Purpose's last
    sentence.
  - **What "the first thing they read" is.** The PRD does not name the file. Two sources settle it.
    PRD § UX Notes, Arrival says "A reader arrives at the written setup instructions"
    (`PRD.md:168`). In the product those instructions are `README.md` § Setup instructions, below
    its opening paragraph. The owner's answer also says "let the README tell it too"
    (`trail/prd/cycle-6.md:32`). So FR-41 is about the README's opening paragraph, under its title.
    The answer also takes the owner's limit: of the earlier versions, name only tracker16-X.
  - **Only one sentence of the purpose is behaviour.** The rest of the testing-ground purpose is how
    tracker17 came to be and why it is built. It is intent, and § 1 carries it as intent. Nothing in
    it asks the tracker to do anything. It must not be read as a reason to record or report anything
    to kensaiapp. NFR-5 (`SRS.md:331-334`) and NFR-6 stand as written, and RN-18's new line says so.
  - **Checked against the settled record.** § 2's terminus keeps publishing outside done
    (`SRS.md:62-64`). FR-41 is about the README in the operator's copy, not about a public page, so
    the two do not conflict. C-4 (source code to read and run) and FR-4 are unchanged. The words of
    the opening are not the SRS's. `CONTENT.md:160` sets the term for "the written document a reader
    starts from", so the SRS states only that both purposes are named.
  - **Failure paths.** *Stale:* if the PRD's purposes change later, AC-21 is an inspection the owner
    can run again, and the PRD's "again on every later release" stays upkeep under § 2. *Absent:* a
    reader may meet tracker17 first somewhere outside the copy, such as a repository description or a
    kensaiapp document that mentions it. FR-41 does not cover that, and this is stated rather than
    fixed: the SRS can only require what the product ships, and publishing is outside done. *Empty,
    concurrent, refused:* none applies to a document's opening paragraph.
  - **What would have changed the verdict.** If the owner had named a different first-read document
    than the README, FR-41 would name that document instead. Their words name the README, so it does.
  - **Downstream, not raised now.** `SDD.md:106` still describes tracker17 only as a worked example.
    The SDD will owe a slice for FR-41 once the SRS holds it. This run did not open an SDD companion,
    because that item would ask the SDD to cut a slice from a requirement the SRS does not state yet.
    If the owner changes this answer on the fold, that SDD item would be left pointing at nothing.
    The SDD's turn comes after `product-srs` folds FR-41. I nearly opened it anyway, because a settled
    SDD has no other channel. What tipped the call was that, once the fold lands, FR-41 is a
    requirement the SDD can be measured against. An item raised then can cite it, and this one could
    only cite a proposal.
  - **Supporting text.** The item's citations hold on disk: `PRD.md:23-29`, `SRS.md:30-38` and
    `SRS.md:620-621` say what the item says they say.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SRS.md** — `<CORE>/launchers/skill/launcher.sh product-srs tracker17`
