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
> `CONTENT_open_issues.md` item 3.1 (2026-10-20) and, reading `UXD.md`, found a state the product
> shows that the UXD never names. No producing run wrote this file, and the item below is the run's
> own raised item. Its reasoning is in `docs/trail/content/self_answer-11.md`.

---

## 1. Open issues — experience questions with no answer yet

None.

## 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override

### 2.1 A refusal shown on a page the operator reached without pressing: does the interface show one, and what does UX-F4 and UX-I3 say about it?

- **Drafted into the UXD:** UX-F4 (§ 5.4) says a move the workflow doesn't allow is refused, that
  "On this interface that refusal arises only when the task was moved in another tab after the page
  loaded", and that "The reason says the task's status has changed and offers a reload." UX-I3 says
  a refusal comes "beside the control that was used" and that "A status move another tab overtook
  (UX-F4)" is a refusal that names what to do and offers a reload. UX-A3 says a refusal is
  "associated with the control it concerns". The UXD names no state for the case below.
  The product shows a refusal in it. The address of the confirmation for a move to `cancelled`
  (`move_task`, `move_confirm`) is opened again, by a reload or by Back after the move was saved, once
  the task's status no longer allows that move. Only `done` and `cancelled` are final, so those are the
  only two statuses it can meet. The route answers with the refusal instead of the confirmation
  (`products/tracker17/web/routes.py:L351-L352`). The page shows "The status of '<title>' is <status>,
  which doesn't allow the move you pressed." (`products/tracker17/web/pages.py:L760`). No other tab is
  involved, no control was used, and the page was just built from the saved data, so a reload shows
  nothing new. The same page shows the task's status and no move buttons. After a Back that follows a
  saved move, the status it shows is the one that move set, so the line sits beside a status that shows
  the move took effect.
- **Rationale:** The wording of that line is `CONTENT.md`'s, and the self-answer to its item 3.1
  (`docs/trail/content/self_answer-11.md`) gives it a rule: a refusal the operator reached without
  pressing states its reason as a fact about the task and what its status allows, never as a fact
  about a press, and names no action and offers no reload. Whether the interface shows a refusal in
  this case at all is the UXD's call, and the UXD is silent on it. UX-F4's "arises only when the task
  was moved in another tab" is not what the interface does, and UX-I3 and UX-A3 place a refusal beside
  a control that, here, was never used. The draft's lean is to keep what ships, with no action and no
  reload, because UX-I3 as amended (version 6) already says a refusal on a page loaded after its cause
  offers a reload only if that page is still out of date, and this page is not. The other reading is
  that no message is needed: the page already shows the status and no move buttons, and backing out
  of a confirmation is a reading action that produces no message (`CONTENT.md` § Voice, "A reading
  action ... produces no message"). That reading removes the refusal, which is the interface's change,
  so the run did not take it.
- **If overridden:** If the CDO decides the interface shows the plain task page and no refusal, the
  route changes through a change that publishes no text, UX-F4's "only" sentence is corrected, and the
  clause the `CONTENT.md` fold adds for this refusal comes out again on `product-content`'s next run.
  If the CDO keeps the refusal, UX-F4 and UX-I3 take the case in the words the owner sets: a state the
  operator reaches by an address, not by a control, with no action and no reload. Either way UX-F4's
  "arises only when the task was moved in another tab after the page loaded" no longer stands as written.
- **Confirm or override:** confirm, with three additions. The interface keeps the refusal, with no
  action and no reload, and UX-F4's "arises only when the task was moved in another tab" sentence is
  corrected to name this second way in. Addition 1, the reason: UX-I3's exception does not cover this
  case as written, because it needs the wanted state to hold, and for a task in `done` the move to
  `cancelled` never holds. The case is covered because the page is not out of date and nothing is left
  to do, so UX-I3 names it as its own case: a refusal reached by an address and no control states what
  is true now, for a task in `done` and a task in `cancelled` alike. Addition 2, the ways in: the
  confirmation's address and its back-out address (`move_back`) both reach it
  (`products/tracker17/web/routes.py:L357-L362`), on a list row as well as on the task's page
  (`routes.py:L439`). Addition 3, the place: no control was used, so the line sits beside the task's
  status in that row or on that page, and UX-I3's "beside the control that was used" and UX-A3's
  "the control it concerns" read as the task's status for this case. The refusal is kept because the
  address asks for a confirmation the page then does not show, and PRD § UX Notes, Refusals say why
  does not let a requested step vanish with no reason. Reasoning in
  `docs/trail/uxd/self_answer-5.md`.

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
- **If overridden:** UX-F4 keeps its reload, and the product's move refusal is a finding for a change
  that publishes text, which adds a reload that shows the same page. RN-32's reason for a reload then
  needs a second ground that this run could not find.
- **Confirm or override:** <the owner fills this in>
