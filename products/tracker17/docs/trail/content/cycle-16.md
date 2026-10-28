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

> **No producing run wrote this file.** The PM opened it on 2026-10-28, after reading the product's
> task deletion sentence against § Needs confirming, to carry § 3.1. `product-content` has no record
> of writing it.

---

## 1. Open issues

None.

## 2. Choices to confirm

None.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 § Needs confirming does not say whether a task's comments are "what goes with it"
- **Raised by:** PM — 2026-10-28
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_delete-and-rename`
- **What it blocks:** nothing is blocked. A writer of a deletion's question has two readings of the
  formula.
- **Where it shows:** the formula's first sentence names "the thing and the count of what goes with
  it" (`docs/CONTENT.md:L326-L327`). A task's comments go with it (`docs/SRS.md:L156`, FR-17), yet the
  task example names no count, and the project example counts tasks only
  (`docs/CONTENT.md:L331-L333`). The product follows the task example: "Delete '{title}'? You can't
  undo this." (`web/pages.py:L782`). The section should say whether comments count, for a task and for
  a project's tasks, so the formula and its examples agree.
- **If a document has to be written:** `CONTENT.md` itself, by `product-content`.
- **Answer:** Comments do not count, for a task or for a project's tasks. The count in the formula is of what the thing holds that the reader manages one by one: a project's tasks, each with its own page, status and controls. A task's comments are part of the task, a flat list on its page that is never edited or deleted on its own (PRD § Core Features, Comments). So a task's question names the task only, as the example already does, and a project's question counts its tasks and not the comments on them. The section should say this in the formula's first sentence, and say that what goes with the thing but is not counted (a task's comments, labels, assignee and due date; the comments on a deleted project's tasks) is covered only by the second sentence's claim that the step can't be undone. The completion line after a project deletion follows the same rule. Not covered: a reader who does not know comments go with a task is not told by the sentence; the comments are on the same page beside the Delete task control, and if operators turn out to be surprised, the first change is the UXD's (UX-F9 lists no comment count among the data the page needs), not a new rule here. Reasoning in `docs/trail/content/self_answer-17.md`.

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
