# CONTENT open issues — tracker17

> Companion to `CONTENT.md`. The Content Manager authored the verbal language non-interactively;
> this file holds the calls it made and wants your sign-off on, plus the few things it genuinely could
> not settle.
> **Answer inline** — fill each **Answer** slot — **commit this file**, then re-run `product-content`.
> It folds your answers into `CONTENT.md` and drops the resolved items. When nothing is left open,
> `product-content` **deletes this file**: no file = the verbal language is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git refuses
> to remove a file with uncommitted edits in it — so an uncommitted answer stops that run before
> it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the Content Manager folds them in, it first copies
> this file whole to `docs/trail/content/` — so what you decided, and why, stays readable and
> citable for good.
>
> **§ 3 comes from outside this run.** The verbal language is read by everyone who writes a string,
> and a seat downstream can find a pattern it has no rule for. It is recorded there, answered here,
> and folded by the same run.

---

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 The verbal language has no word for the due-today count UXD version 12 puts on the summary
- **Raised by:** Principal PM — 2026-11-13
- **Tracked by:** `tracker17 · nemawashi · 2026-11-13_the-content-carries-the-due-today-count`
- **What it blocks:** the seed that builds the count in the product, which would have to write a label and an accessible name with no standard behind them. The build seed also waits on the SDD.
- **Where it shows:** `products/tracker17/docs/UXD.md` § 5.6 UX-F6 says the due-today count "is labelled in words and never shown by colour alone" and sits "directly after the overdue count" as a plain number; UX-S5 shows 0 when nothing is due. `CONTENT.md` fixes "Overdue" as the term for the overdue state (line 165) and the accessible name of a summary count, "3 overdue tasks" (line 404), and carries no term for tasks due today: `grep -ciE 'due.today'` over `CONTENT.md` finds none (run from `products/tracker17`, 2026-11-13). Open for the Content Manager to settle: the summary label, the term for the state against the words it rejects, and whether the plain number, which is not a link, takes an accessible name.
- **If a document has to be written:** none. `CONTENT.md` is revised by `product-content`.
- **Answer:** The label is "Due on {date}", where {date} is the one date the summary's counts were worked out for, written `YYYY-MM-DD`, such as "Due on 2026-11-13". The tracker's own words never say "today" for it. The fold adds one row to § Terminology: the concept is a task due on that date and neither `done` nor `cancelled`; the term is "Due on {date}", which joins "Due from" and "Due to"; the rejected words are "Due today" and "Today" (§ Grammar and mechanics bars "today", because a page doesn't update itself and a summary read after midnight would still say it), "Due now", "Due soon" and "Upcoming" (each claims a time window the count doesn't measure), and "Due" alone (the row for the due date rejects it, and it blurs the count against "Overdue"). The definition documents keep "due today" as their own phrase. The date is the one the overdue count is worked out against, so the label also tells the reader which day "Overdue" was measured on. The plain number takes no accessible name of its own, because a name belongs to a control or a link and this number is neither. Its row label is its words, so § Accessibility of text gains one sentence: the label of a plain count names what it counts without help from the row beside it. The Traceability row for UX-S5 names the new label. A project with no tasks shows the label and "0". Not covered: the label shows a date no earlier summary showed, which the CDO reviews against the experience, and the "Overdue" label stays without a date. Reasoning: `products/tracker17/docs/trail/content/self_answer-22.md`.

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
