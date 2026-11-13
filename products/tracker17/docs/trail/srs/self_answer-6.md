# Self-answer report — SRS.md

## Header

- **Companion:** products/tracker17/docs/SRS_open_issues.md
- **Document:** products/tracker17/docs/SRS.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-11-13
- **Sources re-read:** None. No answer rests on a source outside this repository. The answer rests on
  `PRD.md:159-165` (version 9), the owner's answer in `docs/trail/prd/cycle-7.md` § 1.1, and
  `SRS.md` § 2, § 3.8 FR-25, § 3.11 FR-38 and § 8 AC-13 and AC-14. All were read on disk in this run.

## Items worked

### 3.1 — FR-38's summary list has no due-today count, and PRD version 9 requires one

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the SRS
- **Verdict:** answered
- **Why:** The SRS takes the count. FR-38 gets a due-today line beside the overdue count, AC-13 adds
  the due-today side of its boundary, and the header names PRD version 9. The item carried no draft,
  so it was answered from scratch.
  - **Whose it is.** The edit lands in `SRS.md`, so the item belongs to this document. The owner
    made the product decision upstream: "Summary: due-today count" (`trail/prd/cycle-7.md` § 1.1),
    folded into PRD version 9 (`PRD.md:163-165`). The answer commits no person, money or risk. All
    that is left to decide is how the SRS states a requirement the PRD has already set.
  - **Why "not until it occurs" does not apply.** The item asks the SRS to state a count it does not
    state now, so at first sight it widens the document. It cites no site in the product and no
    failing test, so it cites no occurrence in the narrow sense. But it is a correction of a statement
    that is now false, and that is not widening. The SRS § 2 says it covers "Every PRD Core Feature",
    and FR-38 traces to "PRD § Core Features, Project summary". Since PRD version 9, both claims leave
    out part of that feature. The prompt also names this ground: "Something upstream moved and it has
    not seen it". Check 3 decides it as well: answering "not until it occurs" would contradict a
    settled PRD clause the owner set that day. I came close to that verdict. A widening that came
    from a downstream seat's own idea, with no PRD clause behind it, would have got it.
  - **What the line says.** The due-today count is the PRD's own definition: due date is today's
    date, and status is neither `done` nor `cancelled` (`PRD.md:163-164`). "Today" is FR-25's: the
    machine's local calendar date at the moment the summary is produced. FR-25 already says a task due
    today is not overdue, and the PRD says "The overdue rule is unchanged". So FR-25 stays as written,
    and the new line points at it. The zero count is included, as with FR-38's other counts (RN-15).
  - **What does not change.** The PRD asks for the count in the summary only. So no due-today filter
    is added to FR-32, and no due-today marking to FR-26. The count is worked out from tasks the
    tracker already holds, so DR-1 to DR-6 and NFR-6 stay as written.
  - **Acceptance.** AC-14 checks "the summary's counts and rows match FR-38", so it covers the new
    count once FR-38 holds it. AC-13 is where the boundary is tested, and the due-today count is
    defined by that same boundary. So AC-13 adds the due-today side: an open task due today is in the
    due-today count and not overdue, an open task due yesterday is overdue and not due today, and a
    task due today in `done` or `cancelled` is in neither.
  - **Failure paths.** *Empty:* a project with no tasks, or with no dated tasks, shows zero. A task
    with no due date is never due today, and it stays in the no-due-date count. *Stale:* a summary
    stays as it was when the page loaded (NFR-3). Across midnight, a reload works the count out again
    for the new date. Saved data written before the count existed loads unchanged, because nothing new
    is stored. *Concurrent:* a summary produced across midnight could read two dates. Then one task
    could count as both overdue and due today, or as neither. So the answer states that one summary
    uses one "today" for both counts. *Absent and refused:* the count reads only the machine's clock,
    as FR-25 already does, and nothing about it is refused. NFR-1's one-second bar already covers
    opening a summary.
  - **Stale header fact, folded in by this answer.** `SRS.md:6` reads "PRD Settled (v6)", although
    the Version line at `SRS.md:5` says version 7 carried PRD version 8. The answer has the Inputs
    line name PRD version 9, so the fold fixes this without a separate item.
  - **Downstream, not raised now.** The UXD, SDD, FDR and NFDR do not have the count yet. The seed
    that tracks this item puts their re-runs after the SRS fold, under its § Out
    (`system/projects/tracker17/journey/nemawashi/unpicked/2026-11-13_the-srs-carries-the-due-today-count.md`).
    So this run opened no companion on them.
  - **Supporting text.** The item's citations are correct on disk: `PRD.md:163-165`, `SRS.md`
    § 3.11 FR-38, AC-14, `what_left.md`, and `fdr.md` line 245 as the only due-today line in the FDR.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SRS.md** — `<CORE>/launchers/skill/launcher.sh product-srs tracker17`
