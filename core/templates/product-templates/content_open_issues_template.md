---
version: "1.3.1"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

<!-- Matched to design_open_issues_template.md (and through it to uxd_open_issues_template.md):
     same buckets, same answer-inline-then-re-run loop, same absence-is-done signal.

     One difference from the design companion, and it is the reason this file exists rather than
     reusing that one: a verbal language has no linter, so nothing mechanical can raise an item
     into § 1 on this document's behalf. Every item here was put there by the run's own judgment,
     which makes § 2 the load-bearing half — the calls the rest of the document hangs from, put up
     for override while overriding them is still cheap. Once strings are shipped under a voice,
     changing it invalidates them.

     What qualifies for which section is the prompt's, not stated here. -->

# CONTENT open issues — <product>

> Companion to `CONTENT.md`. The Content Manager authored the verbal language non-interactively;
> this file holds the calls it made and wants your sign-off on — each with the reason behind it,
> and what moves underneath it if you override — plus the few things it genuinely could not
> settle.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**,
> then re-run `product-content`. It folds your answers into `CONTENT.md` and drops the resolved
> items. When nothing is left open, `product-content` **deletes this file**: no file = the verbal
> language is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git refuses
> to remove a file with uncommitted edits in it — so an uncommitted answer stops that run before
> it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the Content Manager folds them in, it first copies
> this file whole to `docs/trail/content/` — so what you decided, and why, stays readable and
> citable for good.
>
> **§ 3 comes from outside this run.** The verbal language is read by everyone who writes a string,
> and a seat downstream can find a pattern it has no rule for. It is recorded there, answered here,
> and folded by the same run.

---

## 1. Open issues

### 1.1 <the question, in one line>
- **Why it matters:** <what in CONTENT.md depends on this — which rule, term, or message pattern>
- **What was searched:** <where the evidence was looked for and what was found instead>
- **Answer:** <the owner fills this in>

<!-- add 1.2, 1.3, … as needed -->

## 2. Choices to confirm

<!-- Three item shapes, one action: the owner confirms or overrides any of them. 2.1 is a rule the
     Content Manager wrote; 2.2 is a section it declared absent in `omitted:`; 2.3 is a term that
     renames something the product already ships — which sits here rather than in § 1 because it
     is a decision already made, not a question, and because its cost lands outside this document
     (existing strings, help content, anything a person has already learned). Use whichever fits;
     number them in one sequence. -->

### 2.1 <the decision, in one line>
- **Written into CONTENT.md:** <the rule, behaviour or pattern, and which section it sits in>
- **Grounds:** <the evidence it derives from — a string in the corpus, a PRD term, a UXD requirement — or "none: a call, made to keep the language coherent">
- **What moves if you override:** <what else in the document is derived from this one>
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

### 2.2 <section declared absent — tone / terminology / message patterns / accessibility / localization>
- **Reason written into `omitted:`** <why it does not apply to this product>
- **Confirm or override:** <"confirm", or "override: write it, because <…>">

### 2.3 <the renaming, in one line>
- **Today the product says:** <the term in the corpus, and where it appears>
- **This document says:** <the approved term, and why the old one was rejected>
- **What it costs:** <what has to change if this is confirmed — strings, help content, anything already learned>
- **Confirm or override:** <"confirm", or "override: keep <the existing term>">

<!-- add 2.4, 2.5, … as needed -->

## 3. Raised from downstream — an item from a seat that did not write the verbal language

<Not the Content Manager's question. A seat working against `CONTENT.md` — most often the Principal
PM, cutting a product's settled documents into seeds — found words the product owes and the language
has no rule for: a message pattern for a state nothing covers, a term the design uses that
terminology never fixed, a section declared absent that the product turns out to need.>

### 3.1 <what the verbal language has no rule for, in one line>
- **Raised by:** <the seat — e.g. Principal PM> — <YYYY-MM-DD>
- **Tracked by:** <the 根回し Nemawashi seed watching this item, by its triple — `<project> · nemawashi · <YYYY-MM-DD>_<slug>` — never by path, which a pick or a retire moves>
- **What it blocks:** <the seed that cannot be cut, or the surface with no wording standard behind
  it>
- **Where it shows:** <the state, screen or term with nothing in `CONTENT.md` to write against>
- **If a document has to be written:** <name it, and the tool its writing seat uses; no tool is a
  finding, not a blank>
- **Answer:** <the owner fills this in>

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.

<!-- add 3.2, 3.3, … as needed -->
