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

> **No producing run wrote this file.** The PM opened it on 2026-10-11, in a route review, to carry
> item § 3.1. `product-content` has no record of writing it. It exists because the PRD now names a
> priority that the terminology lists as a word not to use.

---

## 1. Open issues

None.

## 2. Choices to confirm

None.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 The terminology bans `critical` for priority, and the PRD now names it as a priority
- **Raised by:** PM — 2026-10-11
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`
- **What it blocks:** writing the priority strings: a string naming the PRD's fourth priority
  breaks the terminology row as it stands.
- **Where it shows:** `CONTENT.md:150` — the row for how important a task is gives `low`, `medium`,
  `high` and lists "urgent, critical, normal, P1." as words not to use. `PRD.md:128` (PRD v5) — "A
  task is `low`, `medium`, `high` or `critical`".
- **If a document has to be written:** none. `CONTENT.md` changes through `product-content`.
- **Answer:** The terminology row takes `critical` as the fourth priority: the term becomes "priority, with `low`, `medium`, `high`, `critical`", and the rejected list keeps "urgent, normal, P1" and drops `critical`. The priority values are the PRD's (`PRD.md:128`), so the verbal language can't ban one of them, and `critical` is written lowercase as defined, like the other three. Reasoning in `products/tracker17/docs/trail/content/self_answer-7.md`.

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
