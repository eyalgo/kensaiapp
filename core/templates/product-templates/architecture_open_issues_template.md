---
version: "1.2.2"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

<!-- The single source of the architecture companion's shape. Lands beside the records as
     `<Product path>/docs/architecture_open_issues.md`; the `product-architecture` skill resolves the
     location.

     MODEL-FACING, like the templates it pairs with: the skill reads this file and authors a fresh
     companion, so everything here may explain itself and none of it survives into the result.

     ONE COMPANION FOR BOTH RECORDS, because one run writes both (the owner's ruling 1 of 2026-08-30 —
     the NFDR derives from the ADRs the same run just wrote). An item says which artifact it lands in;
     it does not get its own file. Two companions would ask the owner to answer the same question twice
     whenever a decision and the obligation it binds are unsettled together, which is the common case.

     WHAT THIS FILE OWNS: the three buckets, their order, and the shape of an item in each. **Which bucket
     an item belongs in** is `<CORE>/../skills/principal-architect/.claude/skills/product-architecture/prompts/rich.md`'s, along with
     the rule that an item is led with the run's reasoning and, for a choice, with the drafted answer.
     **The loop** — when this file is written, when it is copied to the trail, and when it is deleted —
     is the `product-architecture` skill's. Neither is restated here.

     THE TWO SLOT LABELS ARE EXACT AND MEASURED SIX OF SIX: `**Answer:**` and
     `**Confirm or override:**` (`<CORE>/templates/authoring-templates/document_template_template.md`
     § THE COMPANION). A consumed companion is detected by a FILLED slot, so renaming a label makes a
     filled answer read as unfilled and the owner's words are dropped.

     TWO BUCKETS FROM THE RUN, AND § 3. An architecture run produces questions the owner answers and
     drafts the owner confirms, and nothing else; § 3 holds an item a seat that did not write
     these records raises later. In particular a decision the run judges WRONG is not a bucket of
     its own: it is a § 1 question routed to the seat that owns the lane, because the run records
     faithfully and never writes a divergent record.

     AN UNSETTLED INPUT IS NOT A COMPANION ITEM. The owner's ruling 6 of 2026-08-30: a run derived from
     an input at Draft says so in the entry's trace and continues. It never halts for it, and it does
     not ask the owner to settle the upstream document first. Only what this run cannot decide reaches
     this file. -->

# Architecture open issues — <product name>

> Companion to `adr/` and `nfdr.md`. The Principal Architect authored both records
> non-interactively; this file holds what the run could not settle from its inputs — the SRS, the SDD
> and the FDR.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `product-architecture`. It folds your answers into the records and drops the resolved items.
> When nothing is left open, `product-architecture` **deletes this file**: no file = the records are
> done.
>
> Your answers are never thrown away. Each time the Principal Architect folds them in, it first copies
> this file whole to `docs/trail/architecture/` — so what you decided, and why, stays readable and
> citable for good.
>
> **§ 3 is raised, not asked.** These records bind every later change, so the seats that live under
> them find gaps the authoring run could not. § 3 is where such a seat says so, against both records
> — an ADR's binding and an NFDR obligation reach the same file.

---

## 1. Open issues — questions with no answer yet

### 1.1 <the question, in one line>
- **Lands in:** <`adr/NNNN-slug.md` | `nfdr.md` QC-n | both>
- **Why it matters:** <what in the records depends on this — which decision, obligation, or trace>
- **Answer:** <the owner fills this in>

<!-- add 1.2, 1.3, … as needed -->

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

### 2.1 <the decision, in one line>
- **Lands in:** <`adr/NNNN-slug.md` | `nfdr.md` QC-n | both>
- **Drafted into the records:** <the call the Principal Architect made, and the record or entry it was
  written into>
- **Rationale:** <why this was the best-effort call, and the SRS / SDD / FDR source it derives from>
- **If overridden:** <the blast radius of not taking the draft — which records supersede, which
  obligations move, and how>
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

### 2.2 <an NFDR section declared not applicable>
<!-- A conditional section that does not bind this product is declared not applicable with its reason,
     and that declaration reaches the owner here as a choice rather than as a silent hole. -->
- **Lands in:** `nfdr.md` § <n>
- **Reason it does not apply:** <why this product carries no obligation under that heading, with the
  SRS and FDR citations that support it>
- **Confirm or override:** <"confirm", or "override: fill it, because <…>">

<!-- add 2.3, 2.4, … as needed; number every item in § 2 in one sequence whichever shape it takes -->

## 3. Raised from downstream — an item from a seat that did not write these records

<Not the Principal Architect's question. A seat living under these records — most often the
Principal PM, cutting a product's settled documents into seeds — found something only they can fix:
an NFDR obligation with nothing in § 10's verification map, a verification named with nothing that
runs it, an ADR decision recorded and never realized, a binding nothing enforces, or an operations
document the NFDR names and no one has written.

Both records reach this one file, so say which — an `ADR-n` or an NFDR section.>

### 3.1 <what the records leave unenforced or unwritten, in one line>
- **Raised by:** <the seat — e.g. Principal PM> — <YYYY-MM-DD>
- **Which record:** <`adr/NNNN-<slug>.md`, or the NFDR section by number>
- **Tracked by:** <the 根回し Nemawashi seed watching this item, by its triple — `<project> · nemawashi · <YYYY-MM-DD>_<slug>` — never by path, which a pick or a retire moves>
- **What it blocks:** <the seed that could not be cut, or the obligation nothing verifies>
- **Where it shows:** <the binding, the obligation, or the verification-map row that is empty>
- **If a document has to be written:** <name it, where the records name it, and the tool its writing
  seat uses — where none exists, that absence is the finding>
- **Answer:** <the owner fills this in>

**How it closes.** `product-architecture` folds it on its next run like any other item here.

<!-- add 3.2, 3.3, … as needed -->
