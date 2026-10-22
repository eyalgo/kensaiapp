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
> **This file was opened by `companion-self-answer`, not by the CDO's run.** The item left below,
> 2.2, is that run's own raised item. It was raised on 2026-10-20 while the run answered item 2.1
> of this file, which `product-uxd` has since folded (`docs/trail/uxd/cycle-5.md`). Its reasoning is
> in `docs/trail/uxd/self_answer-5.md` § Raised on this document.

---

## 1. Open issues — experience questions with no answer yet

None.

## 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override

### 2.2 UX-F4 says a refused status move offers a reload, and the page that refusal lands on is already up to date
> Raised by a `companion-self-answer` run on 2026-10-20, not written by a `product-uxd` run. The run was answering item 2.1 of this file and read `UXD.md` and the product's move route to do it. No item asked about this. It found that UX-F4's reload, and UX-I3's naming of the overtaken status move as a reload case, rest on the refusal being shown on the page the operator pressed from, which the interface does not do. The run left `UXD.md` unchanged and raised the change here. Its reasoning is in `docs/trail/uxd/self_answer-5.md` § Raised on this document.
- **Drafted into the UXD:** UX-F4 (§ 5.4): "The reason says the task's status has changed and offers
  a reload." UX-I3: "Where the wanted state does not hold, the out-of-date refusal still names what to
  do and offers a reload. A status move another tab overtook (UX-F4) is that case". RN-32 gives the
  reason: "A reload offers something only on a page that is still out of date". The previous answer
  (`docs/trail/uxd/self_answer-4.md` § 2.1, check 4) kept the overtaken move as a reload case because
  "A refusal shown on the page the operator acted from would still owe a reload".
- **Rationale:** The interface never shows a refused move on the page the operator pressed from. A
  refused move redirects to the list or the task page it was pressed on
  (`products/tracker17/web/routes.py:L724-L737`), and that page is built from the saved data when it
  loads. It shows the task's current status and the moves that status allows, so by RN-32's own reason
  a reload shows nothing new. The product's line offers none. For a task in `todo` or `in-progress` it
  ends "The moves shown are the ones you can press.", which names what is left to do. For a final status
  it ends "A task in done can't be moved." (`products/tracker17/web/pages.py:L739-L744`). The draft's
  lean: UX-F4 drops "offers a reload". Its reason says the task's status has changed and names the moves
  the page now shows, or none for a final status. UX-I3 stops naming the overtaken status move as a
  reload case. This run did not check the assignee refusals UX-I3 names in the same sentence (UX-F3,
  UX-F9), and the `product-uxd` run should check where they land before keeping or moving them.
- **Checked by the `product-uxd` run, 2026-10-20, as the rationale asks:** the two assignee
  refusals UX-I3 names beside the overtaken move land the same way. A refused add returns to the
  project's Tasks view, and a refused edit to the task's page, each built when it loads, with what was
  typed carried in the address (`products/tracker17/web/routes.py`, `_add_task` and `_edit_task`).
  Their lines say the page is out of date and link to the page's plain address to reload it
  (`products/tracker17/web/pages.py`, the two `ASSIGNEE_NOT_LISTED` reasons), and that link drops what
  was typed. Something is left to do there, picking another assignee, so UX-I3's "names what to do"
  holds for them. Whether their reload holds, by RN-32's reason, is part of this item.
- **If overridden:** UX-F4 keeps its reload, and the product's move refusal is a finding for a change
  that publishes text, which adds a reload that shows the same page. RN-32's reason for a reload then
  needs a second ground that this run could not find.
- **Confirm or override:** confirm, with two additions. UX-F4 drops "offers a reload": its reason
  says the task's status has changed and names the moves the page now shows, or none for a final
  status. UX-I3 stops naming the overtaken status move as a reload case. Addition 1, the assignee
  refusals go the same way. A refused add lands on the project's Tasks view, whose assignee control is
  built from the current list and drops the refused name (`products/tracker17/web/pages.py`,
  `_add_task_form`). A refused edit lands on the task's page, which offers the current listed names and
  shows the refused name only as the failed choice (`_edit_form`). Both pages are built after the
  refusal, so by RN-32's reason a reload shows nothing new, and the reload link drops what was typed.
  What is left to do is pick another assignee or none, so UX-F3's and UX-F9's refusals say the name has
  left the list and name that, with no reload, and UX-I3 stops naming them as reload cases. Addition 2,
  UX-I3's reload sentence: with these three cases gone, "A refusal caused by the page being out of
  date … says so and offers a reload" has no case left on this interface. It becomes: the refusal says
  the page was out of date and names what is left to do on the page it lands on, and offers a reload
  only where the page that shows it is itself still out of date. RN-17's reason for the out-of-date
  refusal stands. The product's two assignee lines (`_task_reason`, `_edit_reason`) still offer a
  reload, which is a finding for a change that publishes text and not this document's to fix.
  Reasoning in `products/tracker17/docs/trail/uxd/self_answer-6.md`.
