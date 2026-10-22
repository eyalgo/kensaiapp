# DESIGN open issues — tracker17

> Companion to `DESIGN.md`. The CDO authored the design language non-interactively; this file
> holds the calls it made and wants your sign-off on — each with the reason behind it, and what
> moves underneath it if you override — plus the few things it genuinely could not settle, and,
> when a design run has produced output for this product, the pointer to it.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `product-design`. It folds your answers into `DESIGN.md` and drops the resolved
> items. When nothing is left open, `product-design` **deletes this file**: no file = the
> design language is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git
> refuses to remove a file with uncommitted edits in it — so an uncommitted answer stops
> that run before it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the CDO folds them in, it first copies
> this file whole to `docs/trail/design/` — so what you decided, and why, stays readable and
> citable for good.
>
> **§ 3 is not the CDO asking.** The design language is read by everything built after it, and a
> seat downstream can find a rule missing that the authoring run had no occasion to write. That item
> lands in § 3 and is folded by the same run.

> **No `product-design` run wrote this file.** The PM opened it on 2026-10-20, from a route review
> (`shukuba-refine`), to carry item 3.1. It exists because `DESIGN.md` is settled and nothing else
> would bring the question to the CDO.

---

## 1. Open issues

None from this file's opening.

## 2. Choices to confirm

None from this file's opening.

## 3. Raised from downstream — an item from a seat that did not write the design language

### 3.1 The confirm-strip's height on the task page
- **Raised by:** PM — 2026-10-20
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_status-moves`
- **What it blocks:** a single height rule for the strip. § Components, {components.confirm-strip},
  says the sentence and the confirming button take the first button's height, and then that this
  height "is {spacing.row-control} in a task row and {spacing.control} elsewhere" (`DESIGN.md:458-461`).
  The first button for a status move is {components.button-move}, which the same section makes
  {spacing.row-control} tall "on a task row or on the task page" (`DESIGN.md:452-453`). On the task
  page the two sentences give the strip two heights.
- **Where it shows:** the move to `cancelled` on the task page. `web/style.css:228-231` makes
  `button.move-button` 28px ({spacing.row-control}) on both places, and the strip follows the
  button it replaces. A future confirmation whose first button is a full-size
  {components.button-secondary} (Delete project, Delete task) is the case "elsewhere" fits.
- **If a document has to be written:** `DESIGN.md` § Components, {components.confirm-strip} — the
  strip takes the height of the button it replaces, with a status move on a row or the task page and
  a full-size first press as its examples; `product-design`.
- **Answer:** confirmed with an addition — take the proposed rule. In § Components,
  {components.confirm-strip}, replace "That height is {spacing.row-control} in a task row and
  {spacing.control} elsewhere" with a rule keyed to the button the strip replaces: the sentence and
  the confirming button take that button's height token, so {spacing.row-control} where the first
  button is a {components.button-move} (a status move, on a task row or on the task page) and
  {spacing.control} where it is a full-size {components.button-secondary} (Delete project's and
  Delete task's first press). This is what RN-25 already says ("The height is the first button's
  height token") and what the Traceability row's "at the first button's height" says, so only the
  one § Components sentence moves. The addition: the rule binds the sentence and the confirming
  button only, and the back-out control stays a full-size {components.button-secondary}, as the
  same bullet already names it. No token value changes, and the stylesheet needs no change, since
  `web/style.css` already sizes the task page's strip from the 28px move button. Reasoning:
  `products/tracker17/docs/trail/design/self_answer-2.md`.

**How it closes.** `product-design` folds it on its next run like any other item here.
