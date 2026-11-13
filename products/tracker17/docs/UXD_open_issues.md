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

## 3. Raised from downstream — an item from a seat that did not write the UXD

### 3.1 UX-F6's summary shows no due-today count, and PRD version 9 and SRS version 8 require one
- **Raised by:** Principal PM — 2026-11-13
- **Tracked by:** `tracker17 · nemawashi · 2026-11-13_the-uxd-carries-the-due-today-count`
- **What it blocks:** the SDD, the FDR, the NFDR, `DESIGN.md` and `CONTENT.md` follow the UXD on what the summary shows, and a cut of the build seed waits on them. Cutting the count straight from the PRD or the SRS would double-cut it.
- **Where it shows:** `products/tracker17/docs/SRS.md` § 3.11 FR-38 now reads "beside the overdue count, the due-today count: the project's tasks whose due date is today and whose status is neither `done` nor `cancelled`" (SRS version 8, `trail/srs/cycle-6.md` § 3.1). `products/tracker17/docs/UXD.md` § 5.6 UX-F6 lists "the total, the count per status, the count per priority, the overdue count, the count with no due date, and each assignee's open-task count", and its link rule ("Every status count, priority count and the overdue count is a link") and "Data the UI needs" name no due-today count. UX-S5 ("the counts and rows UX-F6 lists") follows UX-F6. `grep -ci 'due today'` over the UXD finds none (run from `products/tracker17`, 2026-11-13). Open for the CDO to settle: where the count sits beside the overdue count, whether it is a link (the filter fields cannot express "open" with a due date of today, the reason UX-F6 gives for the no-due-date count) or a plain number, and its zero state.
- **If a document has to be written:** none. The UXD is revised by `product-uxd`. The SDD, FDR, NFDR, `DESIGN.md` and `CONTENT.md` carry no due-today count either (`grep -ci 'due.today'` finds none in each but the FDR, whose one match, `fdr.md` line 245, is the overdue rule), so each follows the UXD in its own run.
- **Answer:**
