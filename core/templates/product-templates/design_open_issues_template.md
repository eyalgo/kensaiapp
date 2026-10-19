---
version: "1.5.1"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

<!-- Matched to uxd_open_issues_template.md (and through it to srs_open_issues_template.md):
     same buckets, same answer-inline-then-re-run loop, same absence-is-done signal.

     One difference from the UXD companion, and it is the reason this file exists rather than
     reusing that one: the design language is the CDO's own call wherever the evidence is silent,
     so § 2 holds decisions awaiting sign-off rather than questions — a drafted value, a
     declared omission and a design-run pointer alike, because the owner does the same thing
     with all of them. On a greenfield
     product § 2 is nearly the whole file; on an existing one the evidence settles more and it
     shrinks. What qualifies for which section is the prompt's, not stated here. -->

# DESIGN open issues — <product>

> Companion to `DESIGN.md`. The CDO authored the design language non-interactively; this file
> holds the calls it made and wants your sign-off on — each with the reason behind it, and what
> moves underneath it if you override — plus the few things it genuinely could not settle, and,
> when a design run has produced output for this product, the pointer to it.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `product-design`. It folds your answers into `DESIGN.md` and drops the resolved
> items. When nothing is left open, `product-design` **deletes this file**: no file = the
> design language is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git
> refuses to remove a file with uncommitted edits in it — so an uncommitted answer stops
> that run before it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the CDO folds them in, it first copies this
> file whole to `docs/trail/design/` — so what you decided, and why, stays readable and citable
> for good.
>
> **§ 3 is not the CDO asking.** The design language is read by everything built after it, and a
> seat downstream can find a rule missing that the authoring run had no occasion to write. That item
> lands in § 3 and is folded by the same run.

---

## 1. Open issues

### 1.1 <the question, in one line>
- **Why it matters:** <what in DESIGN.md depends on this — which token, component contract, or application rule>
- **What was searched:** <where the evidence was looked for and what was found instead>
- **Answer:** <the owner fills this in>

<!-- add 1.2, 1.3, … as needed -->

## 2. Choices to confirm

<!-- Three item shapes, one action: the owner confirms or overrides any of them. 2.1 is a value
     the CDO wrote; 2.2 is a category it declared absent in `omitted:`; 2.3 is a design-run output
     another actor pointed at, for the next run to fold. They sit together because the owner does
     the same thing with all three, and 2.3 sits here rather than in § 1 for that reason — § 1
     holds questions the owner answers, and a pointer asks nothing. The bucket title names only
     2.1 and stays as written: the titles are pinned outside this file, so a title covering every
     shape would move a pin this template may not reach. Use whichever fits; number them in one
     sequence. -->

### 2.1 <the decision, in one line>
- **Drafted into DESIGN.md:** <the token or rule the CDO wrote, with its {path}>
- **Grounds:** <the evidence it derives from — a file and line, a brand asset, a UXD constraint — or "none: taste call, drafted to keep the system coherent">
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

### 2.2 <category declared absent — colors / typography / rounded / spacing / components>
- **Reason written into `omitted:`** <why it does not apply to this product>
- **Confirm or override:** <"confirm", or "override: define it, because <…>">

### 2.3 <the design-run output, in one line>
- **Pointer:** <where the design-run output is>
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

<!-- 2.3 is written here by the design run's sync, at the end of that run — created with the
     pointer, never executed by it. The run that reads it opens what the pointer names and folds
     what it carries, under the fourth permitted delta in <CORE>/../skills/cdo/.claude/skills/product-design/prompts/rich.md
     § The stability rule. What a pointer names is transport's to fix; this file only gives it a
     home. -->

<!-- add 2.4, 2.5, … as needed -->

## 3. Raised from downstream — an item from a seat that did not write the design language

<Not the CDO's question. A seat working against `DESIGN.md` — most often the Principal PM, cutting a
product's settled documents into seeds — found a standard the language does not state: a surface no
rule covers, a token the SDD assumes and the language never declared, a category declared absent
that the product turns out to need.>

### 3.1 <what the design language does not rule on, in one line>
- **Raised by:** <the seat — e.g. Principal PM> — <YYYY-MM-DD>
- **Tracked by:** <the 根回し Nemawashi seed watching this item, by its triple — `<project> · nemawashi · <YYYY-MM-DD>_<slug>` — never by path, which a pick or a retire moves>
- **What it blocks:** <what cannot be cut, designed or built while the rule is missing>
- **Where it shows:** <the slice, surface or component with nothing in `DESIGN.md` to build against>
- **If a document has to be written:** <name it, and the tool its writing seat uses — and where none
  exists, that absence is the finding>
- **Answer:** <the owner fills this in>

**How it closes.** `product-design` folds it on its next run like any other item here.

<!-- add 3.2, 3.3, … as needed -->
