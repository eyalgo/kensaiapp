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

> **No producing run wrote this file.** The PM opened it on 2026-10-28, in a route review, to carry
> item § 3.1: UX-S4 places a refusal reached by an address in the task's row, and a filtered list
> can leave the task with no row.

---

## 1. Open issues — experience questions with no answer yet

None.

## 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write the UXD

### 3.1 A refusal reached by an address has no place when the filter leaves the task off the list
- **Raised by:** PM — 2026-10-28
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_narrow-and-sort`
- **What it blocks:** nothing is blocked. A filtered Tasks view or All tasks can reach a state the
  UXD does not describe, and its place on the page has no UXD clause to be built against.
- **Where it shows:** UX-S4's failure column says "A refusal reached by an address and no control sits
  beside the task's status in its row (UX-F4)" (`docs/UXD.md:L337`), and UX-S7 takes it "As UX-S4"
  (`docs/UXD.md:L340`). UX-F4 says the cancellation confirmation, or its back-out, opened again once the
  task is `done` or `cancelled`, shows the refusal "beside the task's status"
  (`docs/UXD.md:L186-L191`), and that a task which no longer matches a status filter "leaves the list"
  (`docs/UXD.md:L192-L193`). With a status or Overdue filter applied, that reopened address names a
  final task the list does not show, so there is no row to put the refusal in. The product shows it
  above the results instead, as "The status of '{title}' is {status}, which doesn't allow a move to
  cancelled." followed by a sentence saying the task isn't listed (`web/pages.py:L896-L899`,
  `web/pages.py:L903-L914`; `web/routes.py:L577-L593` finds the task that is not shown), and a test pins
  both places (`tests/integration/test_filter_move_routes.py:L755`). The UXD should say where this
  refusal goes when the task is not listed, on a project's Tasks view and on All tasks.
- **If a document has to be written:** `UXD.md` itself, by `product-uxd`.
- **Answer:** When the list's filter leaves the task off the list, on a project's Tasks view (UX-S4)
  and on All tasks (UX-S7) alike, the refusal sits above the results, in the one line UX-I4's
  confirmation takes, and above the no-match state when the filter leaves no rows at all. The line
  names the task by its title and states its status, so it carries what the row would have shown. It
  says the task doesn't match this filter and so isn't in this list. As UX-I3 already rules for this
  case, it names no action and offers no reload, and it does not offer Clear either: the task is in a
  final status, so nothing is left to do with it. No row is invented for the task and no confirmation
  is shown. With no status on the page to sit beside, UX-A3's association is met by the line itself
  naming the task and its status, and the line is announced under UX-A5 without moving focus. The
  task's own page always shows the status, so there UX-F4's placement beside the status stands
  unchanged. The words are `CONTENT.md`'s. Reasoning: `docs/trail/uxd/self_answer-8.md`.

**How it closes.** `product-uxd` folds it on its next run, unchanged from how it folds §§ 1–2.
