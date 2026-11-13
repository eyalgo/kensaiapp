# Self-answer report — UXD.md

## Header

- **Companion:** `products/tracker17/docs/UXD_open_issues.md`
- **Document:** `products/tracker17/docs/UXD.md` (version 11)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-11-13
- **Sources re-read:** None. No answer rests on a source outside this repository. The answer rests on `PRD.md` (version 9) and `SRS.md` (version 8), both read at their own text.

## Items worked

### 3.1 — UX-F6's summary shows no due-today count, and PRD version 9 and SRS version 8 require one

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the UXD
- **Verdict:** answered
- **Why:** The UXD adds the count to UX-F6 and UX-S5, directly after the overdue count, as a plain number that always shows, 0 included.
  - **Seat (check 1).** The CDO's, in the owner's seat. The edit lands in `UXD.md`, the answer binds nothing but the UXD's own consistency with its inputs, and the product call itself is already made. PRD § Core Features, Project summary has the summary show "the count of tasks due today: tasks whose due date is today's date and that are neither `done` nor `cancelled`", confirmed by the owner (`trail/prd/cycle-7.md` § 1.1). SRS FR-38 carries it.
  - **Not "not until it occurs".** The item widens the UXD, and it cites the form where it is present: SRS FR-38's due-today line, and the PRD's Project summary paragraph. It also cites the measured absence in the UXD. This is an upstream change the UXD has not seen, not a case that might occur, so the UXD takes the change.
  - **The question (check 2).** No draft, so the question was read. It hides three questions, all with one seat, and all three are answered: where the count sits, whether it links, and its zero state. A fourth was added, what data the count needs, because UX-F6's "Data the UI needs" line names only the overdue count's date rule.
  - **Where.** Directly after the overdue count, because the PRD says "Beside the overdue count" and the SRS says the same. Order: total, statuses, priorities, overdue, due today, no due date, assignees. How that group is laid out is `DESIGN.md`'s. Its summary already has a "Due dates" table (`DESIGN.md` line 387), which this order fits.
  - **Plain number, not a link.** "Open" is two statuses (`todo`, `in-progress`), and every filter field takes one value (PRD § Core Features, Filtering). The UXD already says no filter can express "open" (RN-12) and keeps such counts as plain numbers (RN-13). A due range from today to today is the nearest filter, and it also lists `done` and `cancelled` tasks due today, so it lands on a list that doesn't match the number. That is RN-13's reason exactly. The overdue count can link because the overdue filter applies the same rule as the count (SRS FR-35).
  - **Settled record (check 3).** No contradiction. UX-S5's "status, priority and overdue counts as links" stays true unchanged. UX-I9 and § 10 add nothing, since the count is computed when the page is built and is not a notification. The PRD and SRS put the count in the summary only (SRS RN-26: no due-today marking, no due-today filter), so UX-F5 and UX-S4 don't change, and the answer says the count goes nowhere else. Without that, a downstream run could add a row marker the PRD never asked for. UX-A4 names status, priority and overdue. The count is a labelled number, so "in words, not colour alone" is enough, and its words are `CONTENT.md`'s.
  - **Failure paths (check 4).**
    - *Empty:* an empty project shows 0 with every other count, as UX-F6's failure line and UX-S5's Empty column already state. The count is never hidden, because an absent count reads the same as a zero one.
    - *Stale:* a link holding today's date would show another day's tasks when bookmarked or reopened through Back. That is a second reason against linking. A summary left open past midnight shows the counts as of when it loaded, which UX-I9 already covers and UX-S5's "as of today's local date" already states.
    - *Concurrent:* one summary uses one "today" for both counts (SRS FR-38), so a summary built across midnight never counts a task as both overdue and due today, or as neither. The answer has the UXD's data line say so.
    - *Absent / refused:* the count reads no outside source and refuses nothing.
  - **Close call.** I nearly chose a link with a disclaimer, because one-action narrowing is what the summary is for (RN-13). It did not win: a link whose list doesn't match its number is what RN-13 rules out, and nothing in the PRD asks for the link.

## Left for the owner

None this run.

## Skipped

None this run.

## Raised on this document

### 2.1 — UX-U2 quotes a PRD sentence that the PRD no longer holds

- **What the document is owed:** UX-U2 should cite PRD § Assumptions in the words it holds now ("Until there are outside readers, the owner's own reading and setup stand in for theirs"), in place of "Until then the owner is the only reader". UX-U2's meaning stays as it is.
- **Why it is worth a cycle:** *A fact in it is now false*, a claim about another document (`<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` § The items are not the whole of what a document is owed). `grep -c 'Until then the owner is the only reader'` over `products/tracker17/docs/PRD.md` returns 0 and over `UXD.md` returns 1 (2026-11-13). The sentence came from the PRD's not-public assumption (`products/tracker17/docs/trail/prd/cycle-3.md` § 2.2), and PRD version 8 replaced that assumption with "tracker17 is public". It is also the case *something upstream moved and it has not seen it*: the UXD's Inputs line reads PRD version 7. The cost is small, because the UXD is already owed a round for item 3.1.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/skill/launcher.sh product-uxd tracker17`
