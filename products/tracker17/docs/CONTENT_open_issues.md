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

> **No producing run wrote this file.** The PM opened it on 2026-10-28, in a route review, to carry
> item § 3.1: the accessible-name rule names a task by its title, and two tasks may share one.

---

## 1. Open issues

None.

## 2. Choices to confirm

None.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 Two move buttons for two tasks with the same title get the same accessible name
- **Raised by:** PM — 2026-10-28
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_narrow-and-sort`
- **What it blocks:** nothing is blocked. A writer of a control's accessible name has no rule for
  telling two tasks apart when they share a title.
- **Where it shows:** § Accessibility of text says that where a visible label repeats, the accessible
  name "adds the thing the control acts on", and its examples name a task by its title alone ("Move
  'Set up CI' to in-progress") (`docs/CONTENT.md:L336-L342`). Titles need not be unique (`docs/fdr.md`
  R-40, `docs/fdr.md:L148`; `docs/SRS.md:L140`). The product's move button is named
  "Move '{title}' to {status}" (`web/pages.py:L769`), and the cancel confirmation "Move '{title}' to
  cancelled? A cancelled task can't be moved again." (`web/pages.py:L676`), so two tasks titled 'Set up
  CI' on one list, which a project's list allows and All tasks makes likelier across projects, give
  two buttons that act on different tasks one name. The title link already tells such rows apart with
  ", number {position} on the task list" (`web/pages.py:L979`). The section should say what tells two
  same-titled tasks apart in a control's accessible name, or that the position suffix the title link
  uses does.
- **If a document has to be written:** `CONTENT.md` itself, by `product-content`.
- **Answer:** <the owner fills this in>

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
