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

> **No `product-content` run wrote this file.** The PM opened it on 2026-10-20, from a route review
> (`shukuba-refine`), to carry item 3.1. It exists because `CONTENT.md` is Settled and nothing else
> would bring the question to the Content Manager.

---

## 1. Open issues

None from this file's opening.

## 2. Choices to confirm

None from this file's opening.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 A refusal shown when the reader pressed nothing
- **Raised by:** PM — 2026-10-20
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_status-moves`
- **What it blocks:** the wording standard for a refusal the reader meets by reloading a page or
  going Back to it, with no press in that step. § Message patterns, Error, *A refusal* states its
  reason "as a fact about what the reader typed or pressed", and has no case for a refusal the
  reader reached without pressing anything.
- **Where it shows:** a page whose address still asks to show the confirmation for a move to
  `cancelled`, opened again (a reload, or Back after the move was saved) once the task's status no
  longer allows that move. The page shows the refusal `web/pages.py:760` writes, "The status of
  '<title>' is <status>, which doesn't allow the move you pressed.", chosen at `web/routes.py:351-352`
  while the request is a page load and not a press. The same page shows the task's new status, so
  the reader is told they pressed a move beside a status showing it took effect.
- **If a document has to be written:** `CONTENT.md` § Message patterns, Error — whether the refusal
  formula covers a refusal reached without a press, and with what reason; `product-content`.
- **Answer:** Yes. The one refusal formula covers it, with one added rule. A refusal the reader reached without typing or pressing anything in that step (a reload, Back, or a saved or typed address) states its reason as a fact about the task and what its status allows, and never as a fact about a press. It does not say "the move you pressed": the tracker can't establish a press from an address, and after a saved move the line would deny a move the page shows took effect. It names the move the address asks for, such as "The status of 'Set up CI' is done, which doesn't allow a move to cancelled." It gives no action and offers no reload, because the page is built from the saved data when it loads and a reload shows nothing new. Its second sentence says what the page shows, as the formula already says for a refusal with no action, such as "A task in done can't be moved." The same formula serves a task already in `cancelled` and one in `done`, the only two statuses that can reach it. The rule governs this refusal only while the interface shows one. Whether it does is the UXD's call, and it is raised on `docs/UXD_open_issues.md` item 2.1. A refusal shown after a redirect from a real press and then reloaded has the same property, and no site is cited for it, so it waits until it occurs. Reasoning in `docs/trail/content/self_answer-11.md`.

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
