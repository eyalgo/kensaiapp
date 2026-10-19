---
version: "1.5.1"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# UXD open issues — <product>

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

### 1.1 <the question, in one line>
- **Why it matters:** <what in the UXD depends on this — which flow / screen / pattern / accessibility bar>
- **Answer:** <the owner fills this in>

<!-- add 1.2, 1.3, … as needed -->

## 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override

<!-- Two item shapes, one action: the owner confirms or overrides either. 2.1 is a call the
     CDO made and wrote into UXD.md; 2.2 is a design-run output another actor pointed at, for
     the next run to fold. They sit together because the owner does the same thing with both,
     and 2.2 sits here rather than in § 1 for that reason — § 1 holds questions the owner
     answers, and a pointer asks nothing. The bucket title names only 2.1 and stays as
     written: both titles are pinned outside this file, so a title covering both would move a
     pin this template may not reach. Number the two shapes in one sequence. -->

### 2.1 <the decision, in one line>
- **Drafted into the UXD:** <the choice the CDO made and wrote into UXD.md>
- **Rationale:** <why this was the best-effort call, and the PRD source it derives from>
- **If overridden:** <the blast radius of not taking the draft — which flows, screens,
  patterns, and notes move, and how>
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

### 2.2 <the design-run output, in one line>
- **Pointer:** <where the design-run output is>
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

<!-- 2.2 is written here by the design run's sync, at the end of that run — created with the
     pointer, never executed by it. The run that reads it opens what the pointer names and folds
     what it carries, under the third permitted delta in <CORE>/../skills/cdo/.claude/skills/product-uxd/prompts/rich.md
     § On a re-run or a re-authoring. What a pointer names is transport's to fix; this file
     only gives it a home. -->

<!-- add 2.3, 2.4, … as needed -->

## 3. Raised from downstream — an item from a seat that did not write the UXD

<Not the CDO's question. A seat reading the UXD after it settled — most often the Principal PM,
cutting a product's settled documents into seeds — found an experience gap only the UXD can close: a
flow no slice realizes, a state the product can reach that the UXD never describes, a surface the
SDD designs and the UXD never named.>

### 3.1 <what the UXD leaves undescribed, in one line>
- **Raised by:** <the seat — e.g. Principal PM> — <YYYY-MM-DD>
- **Tracked by:** <the 根回し Nemawashi seed watching this item, by its triple — `<project> · nemawashi · <YYYY-MM-DD>_<slug>` — never by path, which a pick or a retire moves>
- **What it blocks:** <the seed that could not be cut, or the slice with nothing to build against>
- **Where it shows:** <the slice slug, flow or screen that has no UXD counterpart>
- **If a document has to be written:** <name it, and the tool its writing seat uses; where no tool
  exists, say so rather than leaving the walker to look>
- **Answer:** <the owner fills this in>

**How it closes.** `product-uxd` folds it on its next run, unchanged from how it folds §§ 1–2.

<!-- add 3.2, 3.3, … as needed -->
