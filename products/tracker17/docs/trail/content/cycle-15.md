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
- **Answer:** Yes, the section states it. In a list row, every control that acts on the row's task takes the suffix the title link already carries, so its accessible name ends ", number {position} on the task list", with the position the page shows for that row. The move button then reads "Move 'Set up CI' to in-progress, number 2 on the task list", which still contains its visible label "in-progress" as one unbroken string. The suffix is added on every list row, not only when two titles match. A rule conditional on a title match would change a control's name when another task is added, and it would have to define what counts as the same title. The title link keeps its existing name, and the section says so, because two links to different tasks with one title would otherwise share a name against its own rule that "Two links to different places never share their text". On a task's own page the title alone stands, because one task is shown and nothing there repeats. The cancel confirmation's sentence stays as written. It is visible text and not an accessible name, only one confirmation is shown at a time, and it takes the place of the pressed button in its own row and takes focus. The product's move button names the task by title alone, so it does not yet meet this rule, and that is a finding for a change that publishes text, not an edit to `CONTENT.md`. Reasoning in `docs/trail/content/self_answer-16.md`.

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
