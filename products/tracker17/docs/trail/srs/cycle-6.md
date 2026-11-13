# SRS open issues — tracker17

> Companion to `SRS.md`. The CTO authored the SRS non-interactively; this file holds
> what it could not settle from the inputs (the PRD and any context/constraints).
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this
> file**, then re-run `product-srs`. It folds your answers into the SRS and drops the
> resolved items. When nothing is left open, `product-srs` **deletes this file**: no file =
> the SRS is done.
>
> Your answers are never thrown away. Each time the CTO folds them in, it first copies this
> file whole to `docs/trail/srs/` — so what you decided, and why, stays readable and citable
> for good.
>
> **§§ 1–2 are the CTO's own questions; § 3 is somebody else's.** A seat reading the SRS long after
> it settled can find a gap the authoring run had no way to see, and § 3 is where it says so.

---

## 3. Raised from downstream — an item from a seat that did not write the SRS

### 3.1 FR-38's summary list has no due-today count, and PRD version 9 requires one
- **Raised by:** Principal PM — 2026-11-13
- **Tracked by:** `tracker17 · nemawashi · 2026-11-13_the-srs-carries-the-due-today-count`
- **What it blocks:** a cut of the due-today count into seeds. The SDD, the FDR and the NFDR cannot state it until the SRS does, and cutting it straight from the PRD would double-cut it.
- **Where it shows:** `products/tracker17/docs/PRD.md` § Core Features, **Project summary**: "Beside the overdue count, it shows the count of tasks due today: tasks whose due date is today's date and that are neither `done` nor `cancelled`." (PRD version 9, `trail/prd/cycle-7.md` § 1.1). `products/tracker17/docs/SRS.md` § 3.11 FR-38 lists the total, the status and priority counts, the overdue count, the no-due-date count and the per-assignee rows, and no due-today count. The SRS header reads PRD version 6. AC-14 (§ Acceptance) checks the summary against FR-38, so it does not check the count either. `grep -rniE 'due.today' products/tracker17 --include='*.py' --include='*.html'` finds no summary code for it, and `products/tracker17/docs/what_left.md` lists it as not built.
- **If a document has to be written:** none. The SRS is revised by `product-srs`. The UXD, SDD, FDR and NFDR carry no due-today count either (`grep -ci 'due today'` finds none in the UXD, SDD or NFDR, and one line in the FDR (`fdr.md` line 245, "A task due today is not overdue"), which is the overdue rule), so each follows the SRS in its own run.
- **Answer:** yes, the SRS takes PRD version 9's due-today count. FR-38 gets one more line, beside the overdue count: the count of the project's tasks whose due date is today and whose status is neither `done` nor `cancelled`, with "today" as FR-25 defines it, and a zero count included. FR-25's overdue rule does not change. A task due today is counted as due today and not as overdue, and one summary uses one "today" for both counts, so no task is counted in both or in neither. The count is worked out from the tasks, so DR-1 to DR-6 do not change and saved data written before it still loads. No due-today filter or list marking is added, because the PRD asks for the count in the summary only. AC-13 adds the due-today side of its boundary: an open task due today is in the due-today count and not overdue, and a task due today in `done` or `cancelled` is in neither. AC-14 checks the count through FR-38. The Version line moves to 8, and the Inputs line names PRD version 9. Why: `products/tracker17/docs/trail/srs/self_answer-6.md` § 3.1.
