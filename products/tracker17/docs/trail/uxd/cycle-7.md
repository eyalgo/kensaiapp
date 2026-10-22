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
> found missing while working from documents the UXD fed. It is answered here and folded by the
> same run, but it was never this run's question.
>
> **This file was opened by `companion-self-answer`, not by the CDO's run.** The run was answering
> `CONTENT_open_issues.md` item 3.2 (2026-10-21) and, reading `UXD.md` (version 8), found a state the
> product shows that the UXD does not describe. No producing run wrote this file, and the item below
> is the run's own raised item. Its reasoning is in `docs/trail/content/self_answer-12.md`. An earlier
> `UXD_open_issues.md` item 2.1 (opened 2026-10-20, a different question) was folded into UXD version
> 8 and is gone; this item is not that one.

---

## 1. Open issues — experience questions with no answer yet

None.

## 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override

### 2.1 The page an overtaken move lands on, opened again by a reload, Back or a bookmark: does it still say the task's status has changed?

- **Drafted into the UXD:** UX-F4 (§ 5.4) says a move pressed after the task was moved in another tab
  is refused, and "The reason says the task's status has changed and names the moves the page now
  shows, or that there are none when the status is final." UX-I3 says the same, and that the refusal
  lands on a page built after it. The UXD names no state for that landing page opened again with no
  press. The product shows one. The refusal rides in the address (`move_task` and `move_refused`),
  and the tracker reads it on every load (`products/tracker17/web/routes.py:L384-L396`). The line is
  "The status of '<title>' has changed to <status>." and then what that status allows
  (`products/tracker17/web/pages.py:L751-L756`). A reload, Back, a bookmark or a typed address of that
  page shows it again. The tracker sees only the address, so it can't tell the first landing from a
  later visit. It also doesn't compare the address with the task: `_move_view` returns the outcome
  without reading the task's status (`products/tracker17/web/routes.py:L353`), and the line is shown
  whenever the address names the task on the page (`products/tracker17/web/pages.py:L764-L770`). So an
  address typed for a task that was never moved shows "has changed to <status>" beside a status it
  has always had. The wording is pinned by tests (`products/tracker17/tests/integration/test_move_routes.py:L87-L99`).
- **Rationale:** The wording standard is `CONTENT.md`'s, and its rule is "State only what the tracker
  established" (§ Voice). On the press, the tracker established that the move isn't allowed from the
  task's current status. On a later visit it established only the address. "Has changed" is a claim
  about the past that the address can't back. `CONTENT.md` can't fix this alone: the two arrivals are
  one request, so one string serves both, and dropping "has changed" departs from UX-F4's sentence,
  which the owner confirmed (`docs/trail/uxd/cycle-6.md` § 2.2). Three ways to settle it:
  (a) the line states what the tracker established in every arrival, the task's status and what that
  status allows, such as "The status of 'Set up CI' is done. A task in done can't be moved." It tells
  the reader why the move didn't happen without naming a change; (b) keep "has changed" and accept
  that a visit with no press repeats it; (c) the page doesn't show the refusal on a later visit, which
  needs a mechanism the product lacks and is a design and architecture call. **The lean is (a).** It
  keeps what the reader needs, which is that the move didn't happen and what the page now allows, and
  it is the only form that is true on the press and on every later visit with no new mechanism.
- **If overridden:** Under (b), `CONTENT.md`'s rule for a refusal reached without a press can't cover
  this page, and its record says why. Under (c), UX-F4, UX-I3 and SDD § 6 `status-moves` change as
  well, and the SDD's history-admission rule (RT-11) is read again. Under (a), UX-F4 and UX-I3 lose
  "says the task's status has changed", SDD § 6 `status-moves` and its tests follow
  (`test_move_routes.py:L87-L99`, `test_move_pages.py:L445`), and a change that publishes text rewrites
  `_CHANGED` and `_OVERTAKEN_LINES`.
- **Confirm or override:** confirm, with two additions. (a) stands: the line states the task's status and what that status allows, and claims no change, for example "The status of 'Set up CI' is done. A task in done can't be moved." UX-F4 and UX-I3 lose "says the task's status has changed". Addition 1, the rule. UX-I3 says a refusal caused by the page being out of date "says so", which is the same claim about the past in other words, so it goes too, and so do RN-34's "says the page was out of date" and RN-17's "the refusal still says so". UX-I3 says once why: every refusal in this tracker is read from its page's address, so a reload, Back or a bookmark shows it again, and a refusal states what holds when its page is built, never an event before it. Addition 2, the assignee refusals. UX-F3 and UX-F9 say the reason "says the name has left the list". That is a past event as well, carried in the address the same way, and it becomes "says the name is not on the list". The cost is that the move line no longer says the press failed because the page was out of date. It still shows as a refusal beside the status, and the status it names is not the one the operator pressed from. Reasoning in `docs/trail/uxd/self_answer-7.md`.
