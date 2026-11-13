# SDD open issues — tracker17

> Companion to `SDD.md`. The CTO wrote the SDD; this file holds what that run could not settle from
> its inputs (the PRD, the SRS, the UXD, and any context or constraints), and the calls that are the
> CPO's or the CDO's to make.
>
> **Answer inline** — fill each **Answer** slot — **commit this file**, then re-run `product-sdd`. It
> folds your answers into the SDD and drops the resolved items. When nothing is left open,
> `product-sdd` **deletes this file**: no file = the SDD is done.
>
> Your answers are never thrown away. Each time `product-sdd` folds them in, it first copies this
> file whole to `docs/trail/sdd/` — so what you decided, and why, stays readable and citable for good.
>
> **§ 5 names a raiser from outside the SDD's lanes entirely**: a seat that never held a lane in it,
> reading it after it settled and finding something only the SDD can fix.

---

## 5. Raised from downstream — an item from a seat that did not write the SDD

### 5.1 The project-summary slice delivers no due-today count, and PRD version 9, SRS version 8 and UXD version 12 require one
- **Raised by:** Principal PM — 2026-11-13
- **Tracked by:** `tracker17 · nemawashi · 2026-11-13_the-sdd-carries-the-due-today-count`
- **What it blocks:** the seed that builds the count in the product. Cutting it from the PRD, the SRS or the UXD would double-cut it, and `products/tracker17/docs/what_left.md` names the count as not built. The FDR and the NFDR follow the SDD.
- **Where it shows:** § 6 S-6 `project-summary`, *Reached when* → *Behaviour*, lists "the total, a count for each status and each priority with zeros shown, the overdue count, the count with no due date, and the open tasks for each assignee" and names no due-today count; its *Traces to* stops at SRS FR-25, FR-38 and UXD UX-F6, UX-S4, UX-S5 without the count. SRS § 3.11 FR-38 now reads "beside the overdue count, the due-today count", and UXD § 5.6 UX-F6 and § 4 UX-S5 place it "directly after the overdue count as a plain number" that shows 0 (UXD version 12, `trail/uxd/cycle-10.md` § 3.1). `grep -ciE 'due.today'` over `SDD.md` finds none (run from `products/tracker17`, 2026-11-13). `S-6` is already built and retired, so open for the CTO to settle: whether the count is a new slice after `project-summary` or a re-cut of S-6 (§ 10 holds the earlier re-cuts, RC-1 to RC-6), what § 7 edge it takes, and what the layer-5 pass of § 4 must hold for a count of today's tasks that excludes `done` and `cancelled`.
- **If a document has to be written:** none. The SDD is revised by `product-sdd`.
- **Answer:**

**How it closes.** `product-sdd` folds it on its next run like every other item in this file, and the trail copy and the delete-when-empty behaviour are unchanged.
