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

### 3.1 The date rule bars telling the reader how to pick a date, and it is unclear whether a refusal may tell the reader to pick one
- **Raised by:** PM — 2026-10-11
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`
- **What it blocks:** a settled wording for the due-date refusal, and for any later refusal of a date
  field, such as the edit form's due date.
- **Where it shows:** `CONTENT.md:129-130` — "The date field's displayed form is the browser's own
  and is not a tracker string, so no string tells the reader how to type or pick a date." The
  product's due-date refusal reads "A due date has to be a calendar date. Pick one, or leave the due
  date empty." (`web/pages.py:276`). One reading bars only an instruction on how to enter a date.
  The other bars any string that tells the reader to pick one. The rule does not say which it
  means. If it means the second, the sentence becomes, for example, "Leave the due date empty, or
  give a calendar date."
- **If a document has to be written:** none. `CONTENT.md` changes through `product-content`.
- **Answer:** The second reading. No tracker string tells the reader to pick or to type a date, a refusal included, because the tracker states no way of entering a date for a control whose look is the browser's own. A refusal names the outcome instead of the means, for example "Give a calendar date, or leave the due date empty." The rule keeps the words the owner confirmed ("type or pick", `trail/content/cycle-1.md` § 1.1), and § Grammar and mechanics (Dates and times) says in its own words that no string names how a date is entered, whether by typing, picking or in a format. "Picked" in § Grammar and mechanics (Verbs for pressing) is for an option in a list and doesn't reach the date field. The string at `web/pages.py:276` ends "Pick one", so it doesn't meet the rule. That is a finding for a change that publishes text, not an edit to this document. Reasoning in `docs/trail/content/self_answer-8.md`.

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
