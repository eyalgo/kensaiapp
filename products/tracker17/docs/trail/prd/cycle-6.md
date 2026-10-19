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
> one owner-asked revision to the seat that can fold it. The settled PRD (version 5, `29352d2fc`)
> had no companion. The PRD itself was not edited.

---

## 1. Open issues — product-defining questions with no answer yet

### 1.1 Does tracker17 have a second purpose: KensaiApp's own testing ground?
- **Why it matters:** § Blurb and § Purpose give tracker17 one purpose, a worked example for a reader curious about KensaiApp. They say nothing of how tracker17 came to be, or of its use in building KensaiApp. The README's opening follows § Blurb, so it cannot say either until the PRD does.
- **Reasoning / what would settle it:** why the product exists is a product decision, and only the owner can make it. The owner has made it; the answer below is that decision, in the owner's own words.
- **Answer:** yes (Eyal, 2026-10-11). "It was built by kensaiapp completely. Even a lot of the definition of it. And kensaiapp was built using it and previous versions of it as testing ground. It started as a small CLI application as a PoC for what I mentioned above. Once kensaiapp was mature enough I upgraded it to a webapp and told kensaiapp to continue working on it. The idea is to dogfood kensaiapp and tracker17 and based on that find and fix issues in kensaiapp." State this in § Blurb and § Purpose beside the worked-example purpose, and let the README tell it too. Of the earlier versions, name only tracker16-X, the command-line predecessor the PRD already names.

## 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override

None.

## 3. Directives — an external action the owner confirms as a gate

None.

## 4. Raised from downstream — an item from a seat that did not write the PRD

None.
