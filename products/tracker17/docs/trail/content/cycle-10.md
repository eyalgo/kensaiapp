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

> **No `product-content` run wrote this file.** The PM opened it on 2026-10-13, from a route review
> (`shukuba-refine`), to carry item 3.1. It exists because `CONTENT.md` is Settled and nothing else
> would bring the question to the Content Manager.

---

## 1. Open issues

None from this file's opening.

## 2. Choices to confirm

None from this file's opening.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 Whether § Scope governs what the timed run prints
- **Raised by:** PM — 2026-10-13
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_status-moves`
- **What it blocks:** the wording standard for every row the timed run adds. Each new action adds
  a fixture line and timing rows, and each time the content step has to decide alone whether
  `CONTENT.md` binds them.
- **Where it shows:** `tests/timed_run.py` prints rows whose failing form ends ` — refused or failed`
  (`products/tracker17/tests/timed_run.py:153`, `:158`) and fixture lines joined by `; `
  (`:691`, `:783`). § Scope covers "the text the tracker prints in the terminal it was started
  from" and excludes code comments and test names (`CONTENT.md` § Scope). The timed run is a
  developer check read in a terminal, and it is neither of those. If Scope reaches it, the em dash
  and the semicolon break § Grammar and mechanics, "Banned punctuation", and "failed" breaks
  § Terminology, "Banned in anything a person sees". If Scope does not reach it, say so in § Scope.
- **If a document has to be written:** none. `CONTENT.md` § Scope, through `product-content`.
- **Answer:** No. § Scope does not reach what the timed run prints, and § Scope should say so. It should state that the language governs no output of a script a developer runs to check or measure the tracker, such as the timed run, because the tracker doesn't print those words. Where such a script prints a string the tracker wrote, the string is governed where the tracker writes it. The rows' wording is then not this document's, and no rule here bans their em dash, semicolon or "failed". Reasoning: `products/tracker17/docs/trail/content/self_answer-10.md`.

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
