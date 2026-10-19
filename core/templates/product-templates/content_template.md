---
version: "1.1.2"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

<!-- The single source of the per-product CONTENT.md shape. Lands at <product>/docs/CONTENT.md —
     a sibling of PRD / SRS / UXD / DESIGN / SDD, read by explicit path.

     PROVENANCE — the format is OURS, and that is a deliberate difference from its peer.
     DESIGN.md follows an external vendor format with a linter, so a vague entry there is caught
     by a machine. No design system publishes a schema or a lint for a *content* standard —
     the published material is prose guidance — so there is nothing external to adopt and
     nothing mechanical to check this file. The consequence is carried in
     <CORE>/../skills/content-manager/.claude/skills/product-content/prompts/rich.md § The checkability bar, which is the only
     thing standing where the linter stands for DESIGN.md. Do not soften it.

     WHAT THIS TEMPLATE OWNS: the section shape and the header block. What each section must
     ANSWER, and the bar an entry is written to, are the prompt's — restating them here would be
     a second copy that drifts. The comments below say what a section is for, never how to
     decide it.

     THE ONE RULE THAT DECIDES WHETHER A LINE BELONGS IN THIS FILE AT ALL: it must still be true
     after the next feature ships. This is the standing verbal language, not the copy. A specific
     screen's wording is per-change work and belongs in that change's own artifacts. Examples in
     this document illustrate a rule; they never specify a screen.

     SECTION ALIASES are not permitted here the way they are in DESIGN.md — the headings below
     are the shape. A section that does not apply is declared in `omitted:`, with its reason,
     rather than deleted silently. -->

---
name: <product name>
omitted:
  # Declare any section that genuinely does not apply, with its reason. A declared omission is
  # a product decision — the prompt routes it to the owner as a choice to confirm.
  # <section-name>: <why it does not apply to this product>
---

# CONTENT — <product name>

**Status:** Draft | Settled | Locked
<!-- Draft = the open-issues file is present — something awaits the owner: a sign-off on a
       load-bearing call (a declared omission among them), or a genuine open issue. The document
       itself is complete; every rule is written.
     Settled = the open-issues file is gone. Nothing awaits the owner — the done signal, and the
       state a finished verbal language carries.
     Locked = ratified as the source of truth. -->
**Owner:** Content Manager
**Version:** <n> — <one-line note on what this revision changed>
**Inputs read:** PRD <status> · UXD <status> · SRS <status> · DESIGN <status>
<!-- `**Inputs read:**` IS A HEADER LINE OF THIS DOCUMENT, AND ITS FORM IS NOT THIS FILE'S TO
     STATE. `<CORE>/doctrine/governance/unsettled_inputs.md` owns the rule and the form, for every
     document in the chain rather than this one — write the line from there. **Every input this
     revision read, not only the unsettled ones**: a line that appears only when something was
     `Draft` is indistinguishable from a run that forgot it. -->

> The verbal language is the source of truth for everything this product says to a person. It is
> the peer of `DESIGN.md`, not a part of it: a rule about how something **looks** belongs there,
> a rule about what it **says** belongs here. It is authored off the UXD — the states the words
> live in are named there — and it holds **no per-change copy**: a line that would need editing
> when a feature ships belongs to that change, not to this file. Updated in place with
> versioning (bump the line above whenever a rule or the prose changes); on a revision it is
> **stable by default** — every shipped string was written under the voice as it stood, so a
> silent re-voicing invalidates the corpus without telling anyone. Every delta traces to an
> owner answer, a change in the evidence, or an upstream UXD/PRD change.

---

## Voice

<!-- Two parts, in this order.

     First: one paragraph — who is speaking, to whom, and what the product is trying to do for
     them. This is the fallback a writer reaches for when no rule below covers their case, so it
     has to be able to settle a sentence on its own.

     Then the behaviours. Each row is a thing the voice DOES with words, checkable against one
     string, paired with the adjacent trait it is not, and shown on real strings from this
     product. The prompt owns why an adjective is not admissible here and what makes a valid
     "not" — read it there before filling this table. -->

<one paragraph: the relationship and the intent>

**Conversational or casual:** <this product is conversational; and either "not casual" or
"casual, because <reason tied to the audience or the positioning>">

| We do | We are not | On a real string |
|---|---|---|
| <the behaviour, checkable against one string> | <the adjacent trait a writer could land on by accident> | <a real string of this product's, and the same string written wrong> |

## Tone

<!-- The same voice at different magnitudes. Two maps, both required:
       - across one high-stakes FLOW, end to end;
       - across the LIFECYCLE — first run, habitual use, failure, leaving.
     Name the points where the tone changes and what makes it change there; a map with no named
     change points is a list of adjectives with a table around it. -->

**Across <the flow>:**

| Moment | Tone, and how far | Why it changes here |
|---|---|---|

**Across the lifecycle:**

| Stage | Tone, and how far | Why it changes here |
|---|---|---|

## Grammar and mechanics

<!-- Person and tense · sentence case or title case and where each applies · the punctuation used
     and the punctuation banned · contractions · numbers · dates and times · currency · units ·
     abbreviations and acronyms on first use. Each line stated so a reader holding one string can
     decide. -->

## Terminology

<!-- One approved term per concept. The rejected alternates stay visible with their reason —
     that column is what stops a rejected term coming back. The concept is the PRD's; the word is
     this document's. -->

| Concept | The term | Rejected, and why | Notes |
|---|---|---|---|

**Banned in anything a person sees:**

| Never | Say instead | Why |
|---|---|---|

## Message patterns

<!-- The five standing states. Each needs a structural formula — the parts, in order — and at
     least two real examples, so a writer can produce a sixth message without asking. A pattern
     with no formula is a pair of examples that will be copied wrongly. -->

### Error
**Formula:** <the parts, in order>
**Examples:** <two, from this product>

### Empty
**Formula:**
**Examples:**

### Loading
**Formula:**
**Examples:**

### Partial
<!-- Something worked and something did not — the pattern products most often lack, and the one
     that most often gets written as a full error. -->
**Formula:**
**Examples:**

### Recovered
<!-- The state came back on its own. What the product says about what just happened, and what it
     does not apologise for. -->
**Formula:**
**Examples:**

## Accessibility of text

<!-- The bar the text holds for people who cannot see it or cannot read quickly: alternative text
     conventions · the accessible name of a control · link text that means something read out of
     context · tying an error to the field it is about · the reading level this product commits
     to. Bound by the UXD's accessibility requirements — a requirement this section cannot meet
     is surfaced, never quietly dropped. -->

## Localization

<!-- What has to be true for these words to survive translation: which strings may never be
     assembled from fragments · how placeholders are named and what may be interpolated · the
     expansion headroom the layout owes · forms of address and grammatical gender · what is never
     translated at all (product names, legal strings, identifiers). Applies even to a product
     shipping in one language today — the rules that cost nothing now are the ones that are
     unaffordable later. -->

## Traceability

<!-- Every UXD state that carries text gets a row: which pattern or rule covers it, or an
     explicit answer that it is not covered and why. A state with no row is a state whose words
     nobody specified. -->

| UXD state or requirement | Covered by | Notes |
|---|---|---|

## CONTENT Review Notes

<!-- The why, beside the what — this document stands alone for a cold reader, and a rule with no
     reason is the first one someone deletes. One line per rule the evidence did not settle, in
     one of three currencies: the owner answer it came from, the observation that grounds it, or
     the stated reason behind the call. A rule whose why is already carried inline needs no note.

     This is also where an improvement is logged: a rule you changed because the corpus or an
     upstream document was wrong is recorded here with its reason, never applied silently. -->
