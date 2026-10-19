---
version: "1.9.1"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# PRD — <product name>

**Status:** Draft | Settled | Locked
<!-- Draft = open issues, choices to confirm, or gates-to-confirm remain (open-issues file present).
     Settled = no owner action pending and no open product question — the done signal; recorded
       gates & external dependencies, if any, are tracked below (not "open") and do NOT hold
       Draft. Don't write a flat "Done / nothing is left open" while the body still records gates.
     Locked = ratified as the source of truth. -->
**Owner:** CPO
**Version:** <n> — <one-line note on what this revision changed **about the product** — not the authoring cycle; no "folded in the answer / retired the companion">

> The PRD is the product source of truth: the product-facing **what and why**, read cold
> by the CTO, the CDO, Principal PM, and Principal Architect. It is updated in place with
> versioning (bump the line above on each material change). Keep the **how** — architecture,
> system requirements, delivery sequencing — out; that belongs to the roles downstream.
> Omit a section only when it genuinely does not apply; do not pad one to fill it.
>
> **A decision the CPO introduced, or departed from the input on, wears its relation inline** —
> beside the decision itself, in whatever section it lives, so a cold reader can tell what came
> from the input and what the CPO put there without holding the two documents side by side. Which
> relations exist, which marker each takes, and when one is owed are the authoring prompt's
> (`<CORE>/../skills/cpo/.claude/skills/product-prd/prompts/rich.md` § *Every decision cites its relation to your input*); this
> template says only that the markers sit in the body, never in a section of their own. A
> **suggested removal** has nothing to mark here — the thing it concerns is not in the document —
> and lives only in the companion as a choice to confirm.

---

## Blurb

<!-- One short product description, distilled from `## Purpose` and `## Problem Statement` below —
     the product in a sentence or two, at the altitude a stranger could repeat back. A distillation,
     not a new claim: it says nothing those two sections don't. Fixed once here so the same short
     description is reused rather than re-invented wherever one is wanted. -->

<One or two sentences: what the product is, who it is for, and what it does for them.>

## Purpose

<One short paragraph: what the product is for, and why it should exist now.>

## Problem Statement

<The user / business problem, stated concretely: who feels it, how often, how badly, and
what they do today instead.>

## Why This

<What someone does instead of this, and what this does that it doesn't. Name the alternative
concretely — a competitor, a manual workaround, doing nothing. If the edge rests on something
unproven, say so here rather than letting the rest of the document assume it.>

## Target Users

- <Specific persona or segment — not "users" in general.>
- ...

## Goals

- <The outcome wanted — the change in the user's or business's world, not a feature.>
- ...

## Success Metrics

- <An observable **and** the bar that counts as working — a thing you can watch, plus the reading of
  it that means the goal is met. An observable with no bar can't separate success from noise, and it
  reads like a metric, which is how it survives review. If the bar isn't knowable yet, say so —
  "threshold TBD, tracked from launch" is a bar-shaped answer; silence is not.>
- ...

## Key Use Cases

1. <A concrete scenario: a named user does X and gets Y.>
2. ...

## Core Features

- <A capability the product must have to serve the use cases above.>
- ...

## UX Notes

<!-- The CDO designs the product's whole experience from this section. Cover the path end to end,
     the states the user lands in — including empty, degraded, and failure — and what must feel
     effortless. Product-level only: no visual design. -->

- <A state, a flow, or a thing that must feel effortless.>
- ...

## Scope (In)

- <What this version deliberately includes — the smallest set that proves the thesis.>
- ...

## Out of Scope

- <What this version deliberately excludes. As load-bearing as what's in — name it explicitly.>
- ...

## Assumptions

- <Something taken as true without proof here; if it were false, the product would need rethinking.>
- ...

## Dependencies / Integrations (Conceptual)

- <An external capability or system the product leans on — named at the product level, not the wiring.>
- ...

## Data & Privacy

<!-- Required whenever the product stores, receives, or derives anything about the people who use
     it — identity, auth tokens, preferences, behaviour, connection state. A vendor's or content
     provider's retention obligations do NOT discharge this section: what the product stores about
     its own users is a separate question from what it stores of a vendor's data, and conflating
     the two is how this axis goes missing. Omit only if the product touches no user data at all —
     and then Out of Scope says so. -->

- <What is stored about the product's own users, under what obligation (regulatory, contractual,
  promised), and its retention / deletion story.>
- ...

## Risks

- <What could make this product miss its goals — and, where known, how it shows up.>
- ...

## Open Questions

- [OPEN: <a product-defining question not yet answered — kept visible, never papered over>]
- ...

<!-- If an item is not an open product question but a gate or external dependency the owner has
     confirmed — an awaited vendor answer, a pending consent, an action not yet taken — one that
     does NOT block the PRD from being Settled — move it under the "Gates & External
     Dependencies" heading below, so "Open Questions" means only genuinely-open product
     questions. -->

## Gates & External Dependencies

<!-- Omit this section if there are none. A gate is an external action the owner has confirmed
     as worth recording but that isn't done — whether or not it has been started. Each item:
     what it gates (what it blocks / when it is "reached"), who owns the action, the contingency
     if the answer is unfavorable, and why it does not block Settled. A gate stays here, openly
     unperformed, until its action lands. -->

- <Gate — <what it blocks / when reached>; owner: <who performs the action>; contingency: <fallback>; non-blocking because <why>.>
- ...
