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

---

## 1. Open issues — product-defining questions with no answer yet

None.

## 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override

### 2.1 Key Use Case 2's trace — following one feature from the PRD to its code and tests — has no success bar

> **Raised by a `companion-self-answer` run on 2026-10-05, not written by a `product-prd` run.** No item
> asked for it. The run read `PRD.md` whole while answering last round's items 2.1 and 2.2, and found that § Success
> Metrics says its bars cover all five Key Use Cases, while no bar checks the trace that Key Use Case 2
> describes. The gap comes from an earlier self-answer. Last round's item 2.4 was answered with "use case
> 2, reading the code and tests, is checked by **Simple to read**" (`trail/prd/cycle-2.md` § 2.4). That
> answer read Key Use Case 2 as reading only, and item 2.10 in the same round kept the trace in it. The
> run's reasoning is in `docs/trail/prd/self_answer-2.md` § Raised on this document.

- **Drafted into the PRD:** Nothing yet. The bar is one you confirmed (`trail/prd/cycle-2.md` § 2.4), so it changes only on your answer. § Open Questions records the gap meanwhile. Today § Success Metrics says "Each bar names the Key Use Cases it checks, and together they cover all five". Its **Simple to read** bar (Key Use Case 2) checks only that "the owner reads the code cold and judges it simple". Key Use Case 2 is "A reader reads the code and its tests, and follows one feature from the product definition to where it is built and where it is tested".
- **Rationale:** The trace is the one thing § Why This says tracker17 adds over tracker16-X, which "can't show that trace". Yet no bar checks it, so the "cover all five" claim is only half true for Key Use Case 2. The SRS and the documents below it take their acceptance from these bars. With no bar, nothing downstream has to make the trace followable. The proposed change adds one sentence to **Simple to read**: the owner picks one Core Feature, follows it from this PRD through the definition documents to the code that builds it and the tests that check it, and reaches both without searching the whole codebase. It stays a pass/fail call by the owner, like the rest of the bar. The alternative is a fourth bar of its own. The run leans to one sentence in the existing bar, because the bar already names Key Use Case 2. The CPO agrees with that lean. This item was 2.3 last round (`trail/prd/cycle-3.md` § 2.3), left unanswered.
- **Confirm or override:** confirm, with two additions. (1) The owner picks the feature when they run the check, and they may pick any Core Feature the operator uses. A single feature set up in advance to trace cleanly does not meet the bar. (2) "Without searching the whole codebase" means the owner reaches the code and its tests by following what the definition documents and the code point to, not by searching for them. Keep it as one sentence in **Simple to read**, so § Success Metrics still has three bars. Reasoning in `docs/trail/prd/self_answer-3.md`.

## 3. Directives — an external action the owner confirms as a gate

None.

## 4. Raised from downstream — an item from a seat that did not write the PRD

None.
