# CONTENT open issues — tracker17

> Companion to `CONTENT.md`. The Content Manager authored the verbal language non-interactively;
> this file holds the calls it made and wants your sign-off on — each with the reason behind it,
> and what moves underneath it if you override — plus the few things it genuinely could not
> settle.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**,
> then re-run `product-content`. It folds your answers into `CONTENT.md` and drops the resolved
> items. When nothing is left open, `product-content` **deletes this file**: no file = the verbal
> language is done.
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

## 1. Open issues

None.

## 2. Choices to confirm

None.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 A refusal whose page already shows what the reader wanted: does it give an action?

- **Raised by:** PM — 2026-10-12
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`
- **What it blocks:** No seed. The wording of a refusal for removing something that is already gone
  has no single rule behind it.
- **Where it shows:** Two rules in `CONTENT.md` give different answers here. § Message patterns,
  *A refusal* (`CONTENT.md:L207-L209`), asks for the reason "then one action". § Voice
  (`CONTENT.md:L53`) says to give one next action "when one exists, and none when none does". The
  product ships a refusal for removing a label the task no longer carries. Its page already shows
  the task's current labels, so no action is left to give. The line is "The label '{label}' isn't on
  '{title}'. The labels shown are the ones the task carries." (`products/tracker17/web/pages.py:L718-L721`).
  It follows § Voice and departs from the refusal formula. Neither rule says which one governs.
- **If a document has to be written:** `CONTENT.md`, by the Content Manager through
  `product-content`.
- **Answer:** The Voice rule governs. A refusal gives one action when one exists. Where the reader's
  wanted state already holds and the page already shows it, the refusal states the reason and says
  what the page shows, and it gives no action. § Message patterns, *A refusal*, then reads "then one
  action where one exists", and the two-sentence limit stands. The label refusal at
  `products/tracker17/web/pages.py:L717-L722` already follows this and needs no change. A refusal
  whose input the reader can still fix, such as a blank title, always has an action. When the fold
  reads § Tone, the Failure row ("The reason comes first and the action second") and the Level 1
  definition need the same "where one exists". `UXD.md` UX-I3 still says a refusal "names what to do"
  and that an out-of-date refusal "offers a reload". That is raised as item 2.1 on
  `docs/UXD_open_issues.md` (commit `5a6570821`), and if the CDO overrides it, the formula goes back
  to unconditional. Reasoning: `products/tracker17/docs/trail/content/self_answer-9.md`.

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
