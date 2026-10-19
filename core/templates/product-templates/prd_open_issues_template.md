---
version: "1.7.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# PRD open issues — <product>

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

### 1.1 <the question, in one line>
- **Why it matters:** <what in the PRD depends on this>
- **Reasoning / what would settle it:** <your reasoning on the question, and the evidence or decision that would resolve it — no lean, because an open issue is one you have no basis to decide; if you have a lean it belongs in bucket 2>
- **Answer:** <the owner fills this in>

<!-- add 1.2, 1.3, … as needed -->

## 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override

<!-- Include here any input-inherited decision that rests on an unvalidated assumption or a
     workaround (a source's "for now / until X / not disclosed" choice, or a mechanism that
     doesn't fit the product's platform frame): draft your best-effort, but it is the owner's
     to confirm — never fold such a choice into the PRD as settled. Also here: any departure from
     the request — a value you changed, or something you suggest removing — surfaced as a "choice
     to confirm the change" (principle 12), never a silent edit. -->

### 2.1 <the decision, in one line>
- **Drafted into the PRD:** <the choice the CPO made and wrote into PRD.md>
- **Rationale:** <why this was the best-effort call>
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

<!-- add 2.2, 2.3, … as needed -->

## 3. Directives — an external action the owner confirms as a gate

<!-- A directive is an action outside the PRD that only a person can perform (open a file
     elsewhere, ask a third party, engage a reviewer) — one the CPO can't carry out and the
     owner may not be able to take now. It does NOT block the PRD. It is surfaced here as a
     *gate to confirm*: the CPO names the action, who performs it, and what it gates (what it
     blocks / when it is "reached"). Confirming a gate is a light sign-off that it's worth
     recording — NOT the performing of the action, which stays deferred. On confirmation, the
     next run records the gate in the PRD body (its "Gates & External Dependencies" heading) and
     drops it from here; the external action stays openly unperformed and recorded. Add entries
     here yourself when an override asks for something to be done; the CPO adds one when it reads
     a directive it can't carry out. -->

### 3.1 <the action, in one line>
- **Asked for:** <the directive, and where it was given — e.g. the override on 2.1>
- **Who performs it:** <the owner / the CPO / someone else>
- **What it gates:** <what it blocks / when it is "reached" — e.g. before v1 listing, before a Phase-2 commitment>
- **Confirm or override:** <"confirm" — record it as a gate in the PRD; or "override: <reframe / drop / who else>">
- **Performed?** <"not yet" — the action itself, deferred; or how it landed — a path, a link, a date>

<!-- add 3.2, 3.3, … as needed -->

## 4. Raised from downstream — an item from a seat that did not write the PRD

<Not the CPO's question. A seat working from what the PRD grounds — most often the Principal PM,
cutting a product's settled documents into seeds — found something only the PRD can settle: a
promise the product makes that no slice delivers, a behaviour the FDR locked that the PRD never
stated, a term the whole chain uses that the PRD never defined.>

### 4.1 <what the PRD is missing, in one line>
- **Raised by:** <the seat — e.g. Principal PM> — <YYYY-MM-DD>
- **Tracked by:** <the 根回し Nemawashi seed watching this item, by its triple — `<project> · nemawashi · <YYYY-MM-DD>_<slug>` — never by path, which a pick or a retire moves>
- **What it blocks:** <what the raising seat could not do — the seed it could not cut, the slice it
  could not trace, the decision it could not ground>
- **Where it shows:** <the document and line that reveals the gap, so the CPO can see it too>
- **If a document has to be written:** <name it, and the tool its writing seat uses — where none
  exists, say that: a missing tool is a finding the raising seat owes>
- **Answer:** <the owner fills this in>

**How it closes.** `product-prd` folds the answer on its next run exactly as it folds §§ 1–3, and
this file's own lifecycle is unchanged.

<!-- add 4.2, 4.3, … as needed -->
