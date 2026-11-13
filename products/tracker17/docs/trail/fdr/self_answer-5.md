# Self-answer report — fdr.md

## Header

- **Companion:** `products/tracker17/docs/fdr_open_issues.md`
- **Document:** `products/tracker17/docs/fdr.md`, version 7
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-11-13
- **Sources re-read:** None. Every answer below rests on documents in this repository: the PRD, SRS, UXD and SDD beside the FDR, and the project's finish line.

## Items worked

### 2.1 — The inputs moved after FDR version 6 read them, and the FDR now follows them

- **Bucket:** 2. Choices to confirm — the Principal PM drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The drafted entries are right, and each was checked against its source.
  - **R-129 and R-130** match PRD version 9 § Core Features, Project summary ("the count of tasks due today: tasks whose due date is today's date and that are neither `done` nor `cancelled`", "a task due today is counted as due today and not as overdue") and SRS version 8 FR-38.
  - **R-131** is SRS FR-38's "one summary uses one 'today' for both counts, so no task is counted in both or in neither", and SRS RN-26 gives the reason it is there: a summary produced across midnight.
  - **OOS-17** is SRS RN-26's "FR-26 adds no due-today marking and FR-32 no due-today filter". UXD version 12 UX-F6 says the same, and SDD version 23 S-6's fence too.
  - **The changed R-128** matches SDD § 4 RT-8 as it reads now: "While the saved data cannot be read, such a form's address answers as every address does (EX-13): its values are not read, no refusal arises". R-128 as version 6 wrote it was false on unreadable data.
  - **The version line.** The *Inputs read* line's versions (PRD 9, SRS 8, SDD 23, UXD 12) match each document's own header.
  - **RN-11.** It names every SDD change between version 18 and version 23 that moves no rule: § 3's four layers, TS-6 and TO-10 at 20, the Behave folder at 21, and the S-6 re-cut at 23. Version 22's Playwright pin moves the pin and leaves the list of Linux systems as it stood, so R-120, which leaves the pin to the SDD, stands without a line.

  **The failure paths hold.** An empty project shows 0 (R-129, and its Examples row). A task with no due date is in neither count. A page loaded before midnight keeps its counts, under R-101 and R-69. The date changing during one summary is R-131. An unreadable store shows R-25's page at the summary's address. And PD-15's replaceable clock is how AC-13's due-today side sets the date in a test.

  **The addition is about the finish line, not the FDR.** The rationale says correctly that `system/projects/tracker17/finish_line.md` quotes PRD § Assumptions in words PRD version 8 removed, and that the fix is the CPO's. But it sends the fix nowhere. The finish line has no companion, so the correction would reach no seat. The same removed wording is also in a second place the rationale missed: bar 3 says the owner runs it alone "because the PRD makes them the only reader until they publish". A search of PRD.md for "stays that way until" and "only reader" found 0 lines. Both are now item § 2.1 of `system/projects/tracker17/finish_line_open_issues.md`, which this run opened (see § Companions opened). OOS-1 stands. Its conclusion, that done does not require publishing or an outside reader, still rests on the owner's "by myself" and on PRD § Assumptions' "Until there are outside readers, the owner's own reading and setup stand in for theirs". Only the reason the finish line gives for it is false. What would have tipped this to plain **confirmed**: the finish line already carrying a companion with this correction on it.

  **A note on the companion's form, not an item.** The producing run left this item's slot empty rather than at the template's placeholder (`<"confirm", or "override: <what to do instead>">`). The run read the empty slot as unanswered. That is how it reads, but a fold that tells "unanswered" from "answered" by the placeholder could misread an empty one. It is `product-fdr`'s to keep the placeholder, and this run changed nothing else in the file.

## Left for the owner

None this run.

## Skipped

- **§ 1. Open issues** — "None." No item to answer.
- **§ 3. Raised from downstream** — "None." No item to answer.

## Companions opened

- **system/projects/tracker17/finish_line_open_issues.md** — **opened** — companion to `finish_line.md`, landed in commit `e2de3434e`

## Launchers owed

- **products/tracker17/docs/fdr.md** — `<CORE>/launchers/skill/launcher.sh product-fdr tracker17`
- **system/projects/tracker17/finish_line.md** — `<CORE>/launchers/companion-self-answer/launcher.sh tracker17 finish_line`
