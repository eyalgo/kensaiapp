# UXD open issues — tracker17

> Companion to `UXD.md`. The CDO authored the UXD non-interactively; this file holds
> what it could not settle from the inputs (the PRD, the project's finish line and its doctrine, the
> SRS when present, and any context the owner handed over) — and, when a design run has produced
> output for this product, the pointer to it. **Answer inline** — fill each **Answer** / **Confirm-or-override**
> slot — **commit this file**, then re-run `product-uxd`. It folds your answers into the UXD
> and drops the resolved items. When nothing is left open, `product-uxd` **deletes this file**:
> no file = the UXD is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git
> refuses to remove a file with uncommitted edits in it — so an uncommitted answer stops
> that run before it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the CDO folds them in, it first copies this
> file whole to `docs/trail/uxd/` — so what you decided, and why, stays readable and citable
> for good.
>
> **A third source of items, and it is not the CDO.** § 3 holds what a seat downstream of the UXD
> found missing while working from documents the UXD fed. It is answered here and folded by the same
> run, but it was never this run's question.

---

## 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override

### 2.1 UX-U2 quotes a PRD sentence that the PRD no longer holds

> **Raised by `companion-self-answer`, not by the CDO's run.** The run was answering item 3.1
> (2026-11-13), read `UXD.md` (version 11) whole, and found that UX-U2 quotes PRD § Assumptions in
> words that left the PRD at its version 8. No producing run wrote this item. Its reasoning is in
> `products/tracker17/docs/trail/uxd/self_answer-10.md` § 2.1.

- **Drafted into the UXD:** UX-U2 (§ 3) says "Today the reader and the operator are the same person, the owner (PRD § Assumptions, "Until then the owner is the only reader")." That sentence was in the PRD's not-public assumption (`products/tracker17/docs/trail/prd/cycle-3.md` § 2.2). PRD version 8 replaced that assumption with "tracker17 is public", and `grep -c 'Until then the owner is the only reader'` over `PRD.md` finds 0 (2026-11-13). PRD § Assumptions now reads "Until there are outside readers, the owner's own reading and setup stand in for theirs", and "No outside reader is known yet, so the owner's own reading still stands in for theirs".
- **Rationale:** UX-U2's claim still holds: no outside reader is known, so the owner is still the only reader and operator. Only the quote is false. The fix is to cite the sentence the PRD holds now in place of the one it dropped, with no change to UX-U2's meaning, to any flow, or to § 10's line on publishing, which rests on the finish line and not on this assumption. The UXD's Inputs line also reads PRD version 7, and the fold that takes item 3.1 reads version 9.
- **If overridden:** UX-U2 keeps quoting a sentence no reader can find in the PRD. Nothing else in the UXD moves either way.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

## 3. Raised from downstream — an item from a seat that did not write the UXD

### 3.1 UX-F6's summary shows no due-today count, and PRD version 9 and SRS version 8 require one
- **Raised by:** Principal PM — 2026-11-13
- **Tracked by:** `tracker17 · nemawashi · 2026-11-13_the-uxd-carries-the-due-today-count`
- **What it blocks:** the SDD, the FDR, the NFDR, `DESIGN.md` and `CONTENT.md` follow the UXD on what the summary shows, and a cut of the build seed waits on them. Cutting the count straight from the PRD or the SRS would double-cut it.
- **Where it shows:** `products/tracker17/docs/SRS.md` § 3.11 FR-38 now reads "beside the overdue count, the due-today count: the project's tasks whose due date is today and whose status is neither `done` nor `cancelled`" (SRS version 8, `trail/srs/cycle-6.md` § 3.1). `products/tracker17/docs/UXD.md` § 5.6 UX-F6 lists "the total, the count per status, the count per priority, the overdue count, the count with no due date, and each assignee's open-task count", and its link rule ("Every status count, priority count and the overdue count is a link") and "Data the UI needs" name no due-today count. UX-S5 ("the counts and rows UX-F6 lists") follows UX-F6. `grep -ci 'due today'` over the UXD finds none (run from `products/tracker17`, 2026-11-13). Open for the CDO to settle: where the count sits beside the overdue count, whether it is a link (the filter fields cannot express "open" with a due date of today, the reason UX-F6 gives for the no-due-date count) or a plain number, and its zero state.
- **If a document has to be written:** none. The UXD is revised by `product-uxd`. The SDD, FDR, NFDR, `DESIGN.md` and `CONTENT.md` carry no due-today count either (`grep -ci 'due.today'` finds none in each but the FDR, whose one match, `fdr.md` line 245, is the overdue rule), so each follows the UXD in its own run.
- **Answer:** UX-F6 and UX-S5 add the due-today count: the project's tasks whose due date is today and whose status is neither `done` nor `cancelled`. **Where:** directly after the overdue count, where the overdue count sits, so the two read together (PRD § Core Features, Project summary, "Beside the overdue count"). UX-F6's order becomes the total, the count per status, the count per priority, the overdue count, the due-today count, the count with no due date, and each assignee's open-task count. **A plain number, not a link**, the same as the no-due-date count. "Open" is two statuses and the status filter takes one value (PRD § Core Features, Filtering; RN-12), so no filter can express it. A link to a due range from today to today would also list the `done` and `cancelled` tasks due today, and land on a list that does not match the number, which is RN-13's reason. That address would also carry today's date, so a bookmark or a Back the next day would show a different day's tasks. UX-F6's link rule names it with the plain numbers, and UX-S5's links stay the status, priority and overdue counts. **Zero state:** the count always shows, "0" included, like every other count (SRS FR-38, "a zero count included"). An empty project shows it as 0 with the rest, beside UX-F6's invitation to add a first task. It is never hidden, because an absent count and a zero count would read the same. **Data the UI needs:** the count, worked out from today's local date, with one "today" for the overdue count and the due-today count in one summary. A task due today is counted as due today and never as overdue (PRD § Core Features, Due dates; SRS FR-38). **Only the summary carries it:** no "Due today" marker on list rows and no due-today filter, because the PRD asks for the count in the summary only (SRS RN-26). The count is labelled in words and never shown by colour alone, and its words are `CONTENT.md`'s. Reasoning: `products/tracker17/docs/trail/uxd/self_answer-10.md` § 3.1.
