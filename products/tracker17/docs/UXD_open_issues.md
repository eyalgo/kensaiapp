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

---

## 1. Open issues — experience questions with no answer yet

### 1.1 Where a pressed move's refusal or failure goes when the filter leaves the task off the list
- **Why it matters:** UX-F4 says an overtaken move "offers no reload: the list or the task's page it
  lands on is built after the refusal and already shows the task's current status and the moves that
  status allows", and UX-I3 puts every refusal "beside the control that was used". Both fail on a
  filtered list. Under a status or Overdue filter, a move made in another tab can take the task out of
  the filter, and a press from the stale page then lands on a list with no row for it: the control is
  gone, and the list shows neither the status nor the moves. A failure that is not a refusal (UX-I5)
  has the same gap. The answer to the address-reached case (RN-36) placed that refusal above the
  results and covers only it. The product already handles both pressed cases there, ending with
  "press Clear to see it" when the task still has moves, and the address case without it
  (`products/tracker17/web/pages.py`, `_OFF_LIST_REFUSALS` and `_OFF_LIST_FAILURE`; pinned by
  `tests/integration/test_filter_move_routes.py`, `test_off_list_refusal_and_failure_remain_visible`).
  My reading, for you to take or replace: the same place as RN-36, above the results in UX-I4's line,
  naming the task and its status, and the moves that status allows. Where a move is still possible, or
  the move failed, the line names Clear as what is left to do, since the task can be acted on only once
  it is shown. Where the status is final, it names no action, as RN-36. This moves UX-F4's
  failure/recovery, UX-I3's placement sentence, UX-S4's and UX-S7's error column, and UX-A3's
  association for these cases. The words are `CONTENT.md`'s.
- **Answer:** <the owner fills this in>

## 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write the UXD

None.
