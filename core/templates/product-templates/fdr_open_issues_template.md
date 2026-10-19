---
version: "1.3.2"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

<!-- The single source of the FDR companion's shape. Lands beside the FDR as
     `<Product path>/docs/fdr_open_issues.md`; the `product-fdr` skill resolves the location.

     MODEL-FACING, like the document template it pairs with: the skill reads this file and authors a
     fresh companion, so everything here may explain itself and none of it survives into the result.

     WHAT THIS FILE OWNS: the three buckets, their order, and the shape of an item in each. **Which bucket
     an item belongs in** is `<CORE>/../skills/principal-pm/.claude/skills/product-fdr/prompts/rich.md` § Sorting what the lens turns up
     — the one test that draws the line, which also fixes that an item is led with the run's reasoning
     and, for a choice, with the drafted answer. **The loop** — when this file is written, when it is
     copied to the trail, and when it is deleted — is the `product-fdr` skill's. Neither is restated
     here.

     THE TWO SLOT LABELS ARE EXACT AND MEASURED SIX OF SIX: `**Answer:**` and
     `**Confirm or override:**` (`<CORE>/templates/authoring-templates/document_template_template.md`
     § THE COMPANION). A consumed companion is detected by a FILLED slot, so renaming a label makes a
     filled answer read as unfilled and the owner's words are dropped.

     TWO BUCKETS FROM THE RUN, AND § 3. An FDR run produces questions the owner answers and drafts the
     owner confirms, and nothing else. § 3 holds a different kind of item: one a seat raises against
     the FDR after it settled. -->

# FDR open issues — <product name>

> Companion to `fdr.md`. The Principal PM authored the FDR non-interactively; this file holds what the
> run could not settle from its inputs — the PRD, the SRS and the SDD.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `product-fdr`. It folds your answers into the FDR and drops the resolved items. When nothing is
> left open, `product-fdr` **deletes this file**: no file = the FDR is done.
>
> Your answers are never thrown away. Each time the Principal PM folds them in, it first copies this
> file whole to `docs/trail/fdr/` — so what you decided, and why, stays readable and citable for good.
>
> **§ 3 is the odd one, and worth reading twice.** The Principal PM writes the FDR *and* is the seat
> most likely to raise an item against it later, cutting the same product's documents into seeds. The
> two are different acts at different times, and § 3 keeps the later one visible instead of letting
> it be quietly folded back into § 1 as though the authoring run had asked it.

---

## 1. Open issues — behavioural questions with no answer yet

### 1.1 <the question, in one line>
- **Why it matters:** <what in the FDR depends on this — which rule, product decision, exclusion or example>
- **Answer:** <the owner fills this in>

<!-- add 1.2, 1.3, … as needed -->

## 2. Choices to confirm — the Principal PM drafted a best-effort answer; confirm or override

### 2.1 <the decision, in one line>
- **Drafted into the FDR:** <the call the Principal PM made, and the entry it was written into>
- **Rationale:** <why this was the best-effort call, and the PRD / SRS / SDD source it derives from>
- **If overridden:** <the blast radius of not taking the draft — which rules, product decisions,
  exclusions and examples move, and how>
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

### 2.2 <a section of the FDR declared absent — Product decisions / Out of scope / Examples / Review Notes>
<!-- The document template permits omitting a section that genuinely does not apply. An omission reaches
     the owner here as a choice to confirm rather than as a silent hole. -->
- **Reason it does not apply:** <why this product's FDR carries nothing under that heading>
- **Confirm or override:** <"confirm", or "override: fill it, because <…>">

<!-- add 2.3, 2.4, … as needed; number every item in § 2 in one sequence whichever shape it takes -->

## 3. Raised from downstream — an item raised against the FDR after it settled

<Not a question from the authoring round. A seat reading `fdr.md` long after it settled — commonly
the Principal PM in its *other* posture, cutting this product's documents into seeds — found a
behaviour the FDR locked that nothing delivers, a rule stated so that no bar can check it, or an
Out-of-scope line the design contradicts.>

### 3.1 <what the FDR locks that does not hold, in one line>
- **Raised by:** <the seat — e.g. Principal PM, cutting seeds> — <YYYY-MM-DD>
- **Tracked by:** <the 根回し Nemawashi seed watching this item, by its triple — `<project> · nemawashi · <YYYY-MM-DD>_<slug>` — never by path, which a pick or a retire moves>
- **What it blocks:** <the seed that could not be cut, or the behaviour nothing realizes>
- **Where it shows:** <the FDR rule or product decision, and the document or slice that contradicts
  it>
- **If a document has to be written:** <name it, and the tool its writing seat uses; where none
  exists, say so — the missing tool is the finding>
- **Answer:** <the owner fills this in>

**How it closes.** `product-fdr` folds it on its next run like any other item.

<!-- add 3.2, 3.3, … as needed -->
