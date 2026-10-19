---
version: "1.8.1"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

<!-- The single source of the UXD shape. The AUTHORING guidance lives in the fat prompt
     <CORE>/../skills/cdo/.claude/skills/product-uxd/prompts/rich.md — comments below say only what a section holds.

     § 9 "Design-System Direction" is the SEED for DESIGN.md (the system call + the constraints
     it must satisfy) and carries no token values; the same fact in two documents is the defect
     being avoided. Borrowed patterns are credited once, in the authoring prompt's
     § Attribution (<CORE>/../skills/cdo/.claude/skills/product-uxd/prompts/rich.md) — not restated here. -->

# UXD — <product name>

**Status:** Draft | Settled | Locked
<!-- Draft = open issues or choices to confirm remain (open-issues file present).
     Settled = nothing left for the owner to answer and no open experience question — the done
       signal, and the state a finished UXD carries; the open-issues file is gone.
     Locked = ratified as the source of truth. -->
**Owner:** CDO
**Version:** <n> — <one-line note on what this revision changed>
**Inputs read:** PRD <status>
<!-- `**Inputs read:**` IS A HEADER LINE OF THIS DOCUMENT, AND ITS FORM IS NOT THIS FILE'S TO
     STATE. `<CORE>/doctrine/governance/unsettled_inputs.md` owns the rule and the form, for every
     document in the chain rather than this one — write the line from there. **Every input this
     revision read, not only the unsettled ones**: a line that appears only when something was
     `Draft` is indistinguishable from a run that forgot it. -->

> The UXD is the experience source of truth: the experience-level **what**, derived from the
> settled PRD, authored concurrent with the SRS, and consumed cold by the SDD (so
> the architecture accommodates the experience) and by UI-touching change specs. It is updated
> in place with versioning (bump the line above on each material change); on a revision or a
> re-authoring it is **stable by default** — every delta traces to an owner answer or an
> upstream PRD change. Every entry traces back to a PRD feature, goal, use case, or `## UX
> Notes` item — no entry without a source. Keep technical feasibility and architecture out
> (SRS/SDD), and product intent out (PRD). Give every requirement-shaped entry a stable typed ID
> (`UX-Un`, `UX-Fn`, `UX-Sn`, `UX-In`, `UX-An`) so downstream documents can reference it. Omit a
> section only when it genuinely does not apply; do not pad one to fill it.

---

## 1. Design Read

<One line — "Reading this as: <product kind> for <audience>, with a <vibe> language, leaning
toward <design-system family or aesthetic>." — with its PRD basis.>

## 2. Design Dials

<Four 1–10 dials, each value with its reasoning from a PRD fact; an unbased value is a choice
to confirm, not a row here. A dial with no meaning for this product's surface is `n/a` with its
reason in the Reasoning column, never a number.>

| Dial | Value (1–10) | Reasoning (from the PRD) |
|---|---|---|
| VARIANCE (layout experimentation: symmetric ↔ asymmetric) | <n> | <why> |
| MOTION (animation depth: static ↔ cinematic) | <n> | <why> |
| DENSITY (information per viewport: airy ↔ packed) | <n> | <why> |
| TYPOGRAPHY (conventional ↔ characterful) | <n> | <why> |

## 3. Users & Contexts

<The PRD's Target Users elaborated to what design needs — device, situation, expertise,
assistive-tech expectations. Each as a `UX-Un`, traced.>

- **UX-U1** — <user/context>. *(→ PRD § Target Users)*

## 4. Information Architecture

<The product's structure as the user perceives it: top-level areas, navigation model, what
lives where and why.>

## 5. Key Flows

<One subsection per PRD key use case: steps, decision points, failure/recovery, and the data
the UI needs at each step — the seam the SDD's data model must accommodate.>

### 5.1 UX-F1 — <flow name> *(→ PRD § Key Use Cases: <case>)*

- Steps: <…>
- Data the UI needs at each step: <…>
- Failure/recovery: <…>

## 6. Screen Inventory & States

<Every screen lists all four states; an unhandled state is a defect of this document. On a
surface with no screens, the rows are its commands, endpoints, or entry points and the states each
can land in; a state that cannot arise there is `n/a` with one line of why, which is not a defect.>

| ID | Screen | Empty | Loading | Error | Success |
|---|---|---|---|---|---|
| UX-S1 | <screen> | <…> | <…> | <…> | <…> |

## 7. Interaction Patterns

<The patterns the product commits to — undo/confirmation model, feedback on long operations,
form-validation placement, keyboard model. Each a requirement with an ID, traced.>

- **UX-I1** — <pattern>. *(→ PRD § <ref>)*

## 8. Accessibility Requirements

<Requirements, not aspirations — each pinned to the standard it holds; they flow into the
SRS's NFRs and any later UI review.>

- **UX-A1** — <requirement, with the standard it pins (e.g. WCAG 2.1 AA)>.

## 9. Design-System Direction

<The brief→system call and nothing more: one system per product — the official package named,
or the aesthetic family labeled as built-from-primitives — plus any experience-level constraint
the design language must satisfy (the contrast floor, a mode requirement, a brand commitment).
This section is the SEED for `DESIGN.md`, not a summary of it.

**No token values here.** Colors, type scales, radii, and spacing values live only in
`<product>/docs/DESIGN.md`; naming one here creates a second copy that drifts. State the
constraint ("the accent must clear WCAG 2.1 AA on both surfaces") and let DESIGN.md carry the
value that satisfies it.>

- Direction: <system or aesthetic family, one line of reasoning>.
- Constraints the design language must satisfy: <…>
- Design language: `<product>/docs/DESIGN.md` (authored by `product-design` off this
  direction; may trail the SDD).

## 10. Out of Scope

<What this UXD deliberately does not design, so downstream doesn't infer silence as license.
Name the **terminus** this UXD is scoped against — the project's 上がり Agari — and what it
places outside done; where no terminus was available, say that instead of implying one.>

## 11. Traceability

<Every UX-… entry maps to a PRD feature/goal/use case or a `## UX Notes` item; an entry with no
source row is a defect.>

| UXD entry | PRD source |
|---|---|
| UX-F1 | <PRD § feature/goal, or § UX Notes item> |

---

## UXD Review Notes

<This section is the UXD's **creation trail** — every load-bearing element carries a written
*why*. A PRD-derived entry carries its why inline, as its `*(→ PRD …)*` tag; **everything the
PRD did not settle carries its why here**: an owner's answer folded from the open-issues file,
a best-effort choice the owner confirmed, or a cdo-derived value with the derivation that
grounds it. On a revision or a recreate, every change to already-settled content carries the
legitimate reason that authorized it — an owner answer or an upstream PRD change, never a
silent re-derivation. The owner's answered companions are retired whole to
`<product>/docs/trail/uxd/`, so their exact words stay citable; this section is where *this
document* says why it reads as it does. Omit it only when every element's why is already
carried inline by its PRD-trace tag and the UXD added no decision beyond a faithful read of the
PRD.
Each note names its **relation to the PRD**: *added* (the UXD states something the PRD does not)
or *changed* (it departs from what the PRD says). A **suggest-remove** — something the PRD
includes that you think should be cut — is a product-intent call and never appears here; it goes
to the open-issues companion as a choice to confirm.>

- **RN-1:** *(added | changed)* <what departed from / went beyond the PRD> — *because* <reason> *(re: UX-…; PRD source: <feature/goal, or UX Notes item>)*
- **RN-2:** ...

---

## Open Questions

<An experience question this UXD leaves standing — recorded so a reader does not mistake
silence for an answer, and never papered over.

**This section is not the companion, and never a copy of it.** Anything awaiting the owner lives in
`UXD_open_issues.md` alone, and that file's **absence is the done signal**. An item written in
both has two homes and only one of them says when it is finished — so this document could read
settled while the list below still stands open. If the owner has to answer it, it belongs there and
not here.

What belongs here is a question this UXD cannot close and is **not** asking the owner to close:
one that resolves downstream — in the design language, at implementation, or against a surface
not built yet — recorded so whoever meets it next is not the first to notice it.

Omit this section entirely when there is nothing in it. An empty heading reads as an unanswered
question.>

- [OPEN: <the question, and what would settle it>]
- ...
