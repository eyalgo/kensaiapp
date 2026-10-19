# UXD open issues — tracker17

> Companion to `UXD.md`. The CDO authored the UXD non-interactively; this file holds
> what it could not settle from the inputs (the PRD, the project's Agari and its doctrine, the
> SRS when present, and any context the owner handed over) — and, when a design run has produced
> output for this product, the pointer to it. **Answer inline** — fill each **Answer** / **Confirm-or-override**
> slot — **commit this file**, then re-run `product-uxd`. It folds your answers into the UXD
> and drops the resolved items. When nothing is left open, `product-uxd` **deletes this file**:
> no file = the UXD is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git
> refuses to remove a file with uncommitted edits in it — so an uncommitted answer stops
> that run before it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the CDO folds them in, it first copies this
> file whole to `docs/trail/uxd/` — so what you decided, and why, stays readable and citable
> for good.
>
> **A third source of items, and it is not the CDO.** § 3 holds what a seat downstream of the UXD
> found missing while working from documents the UXD fed. It is answered here and folded by the same
> run, but it was never this run's question.
>
> **This file was opened by `companion-self-answer`, not by the CDO's run.** The run was answering
> `CONTENT_open_issues.md` item 3.1 (2026-10-12) and, reading `UXD.md`, found a sentence in UX-I3
> that disagrees with a refusal the product ships. No producing run wrote this file, and the item
> below is the run's own raised item. Its reasoning is in
> `docs/trail/content/self_answer-9.md`.

---

## 1. Open issues — experience questions with no answer yet

None.

## 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override

### 2.1 A refusal whose page already shows what the reader wanted: does UX-I3 still require it to name an action or offer a reload?

- **Drafted into the UXD:** UX-I3 (`UXD.md:L349-L353`) says the reason "is in plain words and names
  what to do", and that "A refusal caused by the page being out of date, because another tab changed
  or moved the task, says so and offers a reload." Nothing in it covers a refusal where the reader has
  nothing to do. The product ships one: removing a label the task no longer carries. The page
  that follows already lists the task's current labels, so a reload would show the reader nothing new.
  The line is "The label '{label}' isn't on '{title}'. The labels shown are the ones the task
  carries." (`products/tracker17/web/pages.py:L717-L722`). It names no action and offers no reload. The
  refusal arises from another tab having removed the label, which is the out-of-date case UX-I3 names.
- **Rationale:** `CONTENT.md` has two rules that disagree here. § Message patterns, *A refusal* asks
  for the reason "then one action". § Voice says to give one next action "when one exists, and none
  when none does". The answer given to `CONTENT_open_issues.md` item 3.1 (self-answered 2026-10-12) resolves it for
  `CONTENT.md`: the Voice rule governs, and a refusal gives no action where the page already shows
  what the reader wanted. The Content Manager may not relax a UXD requirement. `UXD.md` is the
  upstream source of "names what to do", so the UXD is where the exception has to be stated for the
  two documents to agree. The PRD does not require an action: § UX Notes, *Refusals say why* asks only
  that the refusal tells the reason "in plain words" (`PRD.md:L179-L180`).
- **If overridden:** If every refusal must still name an action or offer a reload, the label refusal
  has no action that is true. A reload shows what the page already shows. Then the product's string
  has to change, through a change that publishes text, and `CONTENT.md` has to take the formula's
  "then one action" back as unconditional. If the UXD takes the exception, the `CONTENT.md` fold of item 3.1
  stands and nothing in it moves.
- **Confirm or override:** confirm, with two additions. UX-I3 takes the exception: a refusal names what to do where something is left to do. Where the state the operator wanted already holds and the page the refusal lands on already shows it, the refusal says what is true now and names no action and offers no reload. The draft's reasons hold. A stronger one is in the UXD itself: UX-A3 already asks a refusal to describe how to correct it "where a correction exists" (`UXD.md:L386-L389`), so UX-I3's unconditional "names what to do" disagrees with its own document as well as with `CONTENT.md` v10. (1) The exception is bounded by where the refusal is shown, not only by what was refused. It holds because the refusal lands on a page loaded after the refusal, built from the saved data: removing a label the task no longer carries returns the task's own page (`web/routes.py:L506-L522`). A reload offers something only on a page that is still out of date. Where the wanted state does not hold, as with a status move another tab overtook or an assignee who left the list before an add or an edit, the refusal still names what to do, and UX-F3, UX-F4 and UX-F9 stand. (2) The product ships a second refusal of the same kind, and it does not follow the exception. Removing an assignee who is already off the list returns People, freshly built (`web/routes.py:L568-L580`), and its line still ends "Open People again to reload the list." (`web/pages.py:L925-L930`). That reload shows nothing new. Neither document needs a change for it. The string has to change, through a change that publishes text, to meet UX-I3 as amended and `CONTENT.md` v10's refusal pattern. Reasoning in `docs/trail/uxd/self_answer-4.md`.

## 3. Raised from downstream — an item from a seat that did not write the UXD

None.
