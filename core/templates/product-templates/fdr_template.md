---
version: "1.1.1"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

<!-- The single source of the FDR shape. Lands at `<Product path>/docs/fdr.md`.

     MODEL-FACING: the `product-fdr` skill reads this file and authors a fresh document, so everything
     here may explain itself and none of it survives into the result. No script stamps it —
     `git grep -n "fdr_template" -- '*.py'` returns nothing — which is why it carries a `version:` at
     all. `<CORE>/doctrine/governance/versioning.md` § Templates — the stamper's code is the proof makes
     the stamper's code the test, and requires it re-read before any marker is added; it was.

     WHAT THIS FILE OWNS: the sections of the document, their order, and the shape of an entry in each.
     Nothing else. What each section must answer, what makes a rule verifiable, how an unsettled item is
     routed, and what may change on a re-run are `<CORE>/../skills/principal-pm/.claude/skills/product-fdr/prompts/rich.md`'s — the
     authoring body this shape is stamped under, declared on both sides
     (`<CORE>/doctrine/setup/authoring_layers.md` § The carriers). The posture, the file loop and the
     commit are the `product-fdr` skill's. This file points at both; it defines neither.

     WHAT IS REQUIRED HERE, AND WHO SAYS SO — every element below resolves one of two ways:
       - The `Status:` / `Owner:` / `Version:` header lines and the orientation blockquote are the
         measured six-of-six shape in
         `<CORE>/templates/authoring-templates/document_template_template.md` § THE HEADER BLOCK, which
         also fixes the three `Status:` values and that the `Version:` note is written against the
         subject rather than the authoring cycle.
       - `## FDR Review Notes` is required because
         `<CORE>/../skills/principal-pm/.claude/skills/product-fdr/prompts/rich.md` § The why is the gate — creation provenance routes
         a why with no inline home to "the section the template fixes for exactly this". This file is
         what fixes it.
       - The typed IDs and the inline trace tag are THIS TEMPLATE'S OWN. Nothing upstream fixes their
         letters. They exist because the prompt requires every rule to name which of three upstream
         documents it realizes, and because an acceptance criterion, a change spec and a later revision
         each need to cite one entry rather than a paragraph.

     PROVENANCE — the shape is OURS. No vendor publishes an FDR schema, so there is no external format
     to track and no linter to run a filled-in one against.
     `<CORE>/doctrine/setup/setting_up_a_project.md` § The foundation step names the prior art a run may
     draw on — the FRD of the BRD → FRD chain and its standards-body form, each with the edition to read
     — and the prompt is where that prior art is applied, section by section. Both are named there and
     in `<CORE>/../skills/principal-pm/.claude/skills/product-fdr/prompts/rich.md`; a third copy here would be the one that goes stale. What stands where a vendor's
     linter would have stood is the prompt's finish walk and its rule that every rule yields at least one
     test case: nothing mechanical reads this document.

     THE SECTIONS ARE NOT NUMBERED, and that is a choice (§ THE OPEN CHOICES, item 4 of the shape above).
     The prompt's completeness lens points at four of them BY NAME — Rules, Product decisions, Out of
     scope, Examples — so numbering would give every one of those arrows a second identifier to keep in
     step. Entries carry the citable identity instead, which is what a downstream document actually
     references.

     THERE IS NO `## Open Questions` SECTION, and its absence is a decision rather than an oversight.
     Three of the six measured templates carry one for a question that resolves downstream rather than by
     an owner's answer. An FDR cannot: it is the behavioural contract every later change is checked
     against, and the prompt's § Every rule is singular, unambiguous and verifiable states that an
     unresolved gap never survives in the body of a settled FDR. Anything unsettled lives in
     `fdr_open_issues_template.md`'s buckets until the owner answers it.

     THERE IS NO `## Traceability` SECTION EITHER, for a different reason, and it is stated because an
     unstated absence reads as an oversight. Three of the six carry one as a table mapping each entry to
     its single upstream source. Every entry here already carries that inline, as its trace tag, and an
     FDR traces to three sources rather than one — so a table would hold the same fact in a second home
     that drifts from the first, and would be a section no arrow of the prompt's lens points at.

     THE FIVE SECTIONS BELOW SURVIVE FROM THE SHAPE THIS TEMPLATE CARRIED BEFORE IT MOVED HERE —
     Description, Rules, Product decisions, Out of scope, Examples — and the prompt's arrows point at
     those names. Renaming one is a two-file edit, in one commit. -->

# FDR — <product name>

**Status:** Draft | Settled | Locked
<!-- Draft = the companion is on disk, so something awaits the owner.
     Settled = the companion is gone. Nothing awaits the owner — the done signal.
     Locked = ratified as the source of truth. The owner's act, never the run's. -->
**Owner:** Principal PM
**Version:** <n> — <one-line note on what this revision changed **about the product's behaviour or its
product decisions** — not the authoring cycle; no "folded in the answer / retired the companion">
**Inputs read:** PRD <status> · SRS <status> · SDD <status>
<!-- `**Inputs read:**` IS A HEADER LINE OF THIS DOCUMENT, AND ITS FORM IS NOT THIS FILE'S TO
     STATE. `<CORE>/doctrine/governance/unsettled_inputs.md` owns the rule and the form, for every
     document in the chain rather than this one — write the line from there. **Every input this
     revision read, not only the unsettled ones**: a line that appears only when something was
     `Draft` is indistinguishable from a run that forgot it. -->

> The FDR is the product's **behavioural contract**: what the product does, and the product decisions
> every change after it is built against. It is written once per product from the PRD, the SRS and the
> SDD, and read cold by the Principal Architect (ADR / NFDR), the PM, the Product Owner specifying a
> change, and the QA seat deriving acceptance. It is updated in place with versioning (bump the line
> above on each material change); every delta in a revision traces to an owner answer or directive, or
> to a change in one of the three upstream documents.
> **Keep the *how* out.** Module names, layer names, file paths, class and method names, protocols and
> data-structure design belong to the SDD and to the Principal Architect's ADR;
> `<CORE>/../skills/principal-pm/.claude/skills/product-fdr/prompts/rich.md` § The altitude test owns the test that draws the line.
> **Every entry carries a stable typed ID** — `R-n` a rule, `PD-n` a product decision, `OOS-n` an
> out-of-scope entry, `RN-n` a review note — so an acceptance criterion, a change spec, or a later
> revision cites one entry rather than a paragraph. An ID is never reused and never renumbered.
> **Every rule and product decision carries an inline trace tag** naming which upstream document it
> realizes and where: `*(traces to: SRS § 3.1 FR-2)*`, `*(traces to: PRD § Core Features)*`,
> `*(traces to: SDD § 4)*`.
> Omit a section only when it genuinely does not apply; do not pad one to fill it.

---

## Description

<!-- What the product is and what this document covers, in one short paragraph. The product intent it
     serves comes from the PRD; the behaviour is everything below. -->

<One short paragraph: what the product does, and the product intent from the PRD that the behaviour
below serves.>

---

## Rules

<!-- The behaviours the product must exhibit, each as one testable `R-n`. Group them under headings
     that fit the product — a capability area, a command, a lifecycle stage, an interface. Add, rename
     or drop groups freely; the grouping is the product's, not this template's. -->

### <Group — a capability area, a command, a lifecycle stage>

- **R-1:** <A single behaviour the product must exhibit, stated so that one test can prove it.> *(traces to: SRS § 3.1 FR-2)*
- **R-2:** ...

### <Group>

- **R-3:** ...

---

## Product decisions

<!-- The choices that are the product's rather than the architecture's, each as one `PD-n`. What makes
     a choice a product decision, and what a later change owes one, are the prompt's
     § The derivation — the FDR-completeness lens and § What you own — and what you don't. -->

- **PD-1:** <The decision, stated as a decision rather than a preference, with what it binds.> *(traces to: PRD § Scope)*
- **PD-2:** ...

---

## Out of scope

<!-- What is deliberately excluded, each as one `OOS-n`, with the boundary that excludes it — the
     project's 上がり Agari, a PRD scope call, or the SDD's § 12. -->

- **OOS-1:** <What is excluded — and the boundary that excludes it.> *(traces to: SDD § 12)*
- **OOS-2:** ...

---

## Examples

<!-- The concrete case for a rule a reader could otherwise read two ways, and the rule it pins down.
     Which rules earn one is the prompt's. -->

| Input / Scenario | Expected behaviour | Rule |
|---|---|---|
| `<input or scenario>` | `<what the product does>` | R-n |

---

## FDR Review Notes

<!-- This section is the FDR's **creation trail**: the run's own divergences from its three upstream
     documents, and every load-bearing *why* that has no inline home. A rule whose why is "it realizes
     an upstream item" carries that why inline as its trace tag and needs no note here. Everything else
     does — an owner's answer folded from the companion, a best-effort choice the owner confirmed, a
     value derived with a basis, or a place where this document departed from a source.

     Each note names its **relation to the source**: *added* (the FDR states something none of the three
     upstream documents does) or *changed* (it departs from what one of them says). A **suggest-remove**
     never appears here — it is a scope call and goes to the companion as a choice to confirm.

     Which whys are legitimate, and that the why is the gate on making a change rather than a caption
     added to one, are `<CORE>/../skills/principal-pm/.claude/skills/product-fdr/prompts/rich.md` § The why is the gate — creation
     provenance and § Every rule cites its relation to the three sources. This section is where those
     discharge; it does not restate them.

     Omit this section only when every element's why is already carried inline by its trace tag and the
     run added no decision beyond a faithful read of the three upstream documents. -->

- **RN-1:** *(added | changed)* <what this FDR added beyond, or changed from, its sources> — *because* <reason> *(re: R-n / PD-n; source: SRS § 3.1 FR-2)*
- **RN-2:** ...
