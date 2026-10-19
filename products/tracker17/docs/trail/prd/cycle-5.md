# PRD open issues — tracker17

> Companion to `PRD.md`. The CPO authored the PRD non-interactively; this file holds
> what it could not settle from the inputs. **Answer inline** — fill each **Answer** /
> **Confirm-or-override** slot — **commit this file**, then re-run `product-prd`. It folds
> your answers into the PRD and drops the resolved items. When nothing is left unresolved,
> `product-prd` clears this file: no file = the PRD is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git
> refuses to remove a file with uncommitted edits in it — so an uncommitted answer stops
> that run before it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the CPO folds them in, it first copies
> this file whole to `docs/trail/prd/` — so what you decided, and why, stays readable
> and citable for good.
>
> **§§ 1–3 are the CPO's own questions. § 4 is not.** It holds what a seat downstream of the PRD —
> one that never wrote a line of it — found missing while working from the documents the PRD
> grounds. Same file, same fold, different asker.

> **No `product-prd` run wrote this file.** It was opened on 2026-10-11, at Eyal's word, to carry
> one owner-asked revision to the seat that can fold it. The settled PRD (version 4, `af14daba9`)
> had no companion. The PRD itself was not edited.

---

## 1. Open issues — product-defining questions with no answer yet

### 1.1 Does a task gain a fourth priority, `critical`?
- **Why it matters:** § Core Features, **Priorities**, says "A task is `low`, `medium` or `high`, and `medium` is the default." Filtering, sorting by priority and the count per priority in § Core Features all read that set.
- **Reasoning / what would settle it:** a new value in the priority set is a product decision, and only the owner can make it. The owner has made it; the answer below is that decision.
- **Answer:** yes. Add to **Priorities**, under § Core Features, a new priority: `critical` (Eyal, 2026-10-11).

## 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override

None.

## 3. Directives — an external action the owner confirms as a gate

None.

## 4. Raised from downstream — an item from a seat that did not write the PRD

None.
