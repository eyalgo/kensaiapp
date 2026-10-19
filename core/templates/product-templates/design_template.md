---
version: "1.7.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

<!-- The single source of the per-product DESIGN.md shape. Lands at <product>/docs/DESIGN.md —
     a sibling of PRD / SRS / SDD / UXD (owner decision Q3), read by explicit path.

     PROVENANCE — the format is EXTERNAL and we do not own it. It is Google's DESIGN.md format,
     linted and exported by the `@google/design.md` npm package (owner decision Q4: adopt the
     established toolchain rather than hand-roll one). The schema below was read from the
     vendor's own `spec --rules` output at package version 0.4.0 on 2026-07-30 — NOT from a
     third-party description of it.

     THE SCHEMA'S OWNER IS THE VENDOR. This template carries the shape as stamped plus this
     instance's own additions (the Status/Owner/Version header, the Review Notes trail, the UXD
     traceability table). It is not the authority on the format: `npx @google/design.md@0.4.0
     spec --rules` is. The format self-describes as `version: alpha`, so it will move — when it
     does, re-read the spec rather than trusting this file.

     CORRECTIONS to v1's design_md.md.template, which was drafted from ibelick/ui-skills'
     reading of the format rather than from the format itself:
     - EIGHT prose sections, not nine. ibelick's template inserted a `## Themes` section third;
       the canonical order has no Themes. Mode values now live in the Colors prose as a table
       (documentation, not a second token schema) — same content, inside the spec.
     - Frontmatter gains `name` (REQUIRED), `components`, and `omitted` — none of which v1's
       draft carried. `omitted` is the format's sanctioned way to declare a category
       intentionally absent; use it instead of leaving a silent hole.
     - Section aliases are permitted: Overview ("Brand & Style"), Layout ("Layout & Spacing"),
       Elevation & Depth ("Elevation"). Pick one spelling per product and keep it.

     VERIFIED EMPIRICALLY 2026-07-30, so the gates below are not inferred:
     - A NON-SPEC `##` section (this template's "DESIGN Review Notes") produces ZERO warnings —
       the format's own rule is "unknown section heading: preserve, do not error". Our additions
       are safe. A DUPLICATE section heading, by contrast, is a hard error that rejects the file.
     - `lint` EXITS 0 WITH WARNINGS PRESENT (probed: 2 warnings, exit 0). Only `broken-ref` is
       severity `error`. So "lint exited 0" is NOT a meaningful gate — the gate reads the JSON
       `summary` instead, which is the command's default output format. The bar over that
       summary is the prompt's § The machine gate, stated there and nowhere else.
     - An h1 title is allowed and is not parsed as a section. The Status/Owner/Version block
       below is prose, not an `##` heading, so it cannot affect section-order.

     WHAT THE LINTER ACTUALLY CHECKS (severity in brackets) — the prompt owns the discipline,
     this is the shape it is checked against: broken-ref [error] · missing-primary [warning] ·
     contrast-ratio [warning, component backgroundColor/textColor below AA 4.5:1] ·
     orphaned-tokens [warning, tokens never referenced by a component] · missing-typography
     [warning] · section-order [warning] · unknown-key [warning] · token-like-ignored [warning] ·
     token-summary / missing-sections / omitted-rules [info].

     Two consequences worth designing for: `contrast-ratio` only fires on COMPONENT colour
     pairs, so a product that defines no component pairs gets no contrast checking at all; and
     `orphaned-tokens` means a token nothing references is a warning — the format enforces the
     same "every value must change an implementation choice" bar this instance already holds. -->

---
version: alpha
name: <product name — REQUIRED>
description: <optional, one line — what surface this design language governs>
# omitted: declare any category that genuinely does not apply, rather than leaving it absent.
#   omitted:
#     - spacing
#     - section: rounded
#       reason: "<why — a documented reason beats a bare name>"
colors:
  # map<string, Color>. `primary` must exist (missing-primary is a warning).
  # Value = any valid CSS color; #RRGGBB is the recommended default.
  # Convention when there are several palettes: primary, secondary, tertiary, neutral.
  primary: <#RRGGBB>
typography:
  # map<string, Typography>. Named levels, canonical fields only:
  #   fontFamily · fontSize (px/em/rem) · fontWeight (number) ·
  #   lineHeight (Dimension or unitless multiplier) · letterSpacing · fontFeature · fontVariation
  # Most systems carry 9–15 levels; semantic names (headline-lg, body-md, label-sm) are the
  # recommended convention. A scalar entry (`sans: Inter`) is invalid.
  <level-name>:
    fontFamily: <family>
    fontSize: <16px>
    fontWeight: <400>
    lineHeight: <1.6>
rounded:
  # map<scale-level, Dimension>. Recommended levels: none, sm, md, lg, xl, full.
  <level>: <value>
spacing:
  # map<scale-level, Dimension | number>.
  <level>: <value>
components:
  # map<component, map<token, value>>. Values may be literals or {path.to.token} references;
  # composite references ({typography.body-md}) are permitted here only.
  # Properties: backgroundColor · textColor · typography · rounded · padding · size · height · width
  # Variants go under related keys: button-primary, button-primary-hover, button-primary-active.
  # DEFINE COLOUR PAIRS DELIBERATELY — contrast-ratio only checks components, and a token no
  # component references trips orphaned-tokens.
  <component-name>:
    backgroundColor: "{colors.primary}"
    textColor: <#RRGGBB or {colors.…}>
---

# DESIGN — <product name>

**Status:** Draft | Settled | Locked
<!-- Draft = the open-issues file is present — something awaits the owner: a sign-off on a
       load-bearing call (a declared omission among them), or a genuine open issue. The document
       itself is complete; every value is written.
     Settled = the open-issues file is gone. Nothing awaits the owner — the done signal, and
       the state a finished design language carries.
     Locked = ratified as the source of truth. -->
**Owner:** CDO
**Version:** <n> — <one-line note on what this revision changed>
**Inputs read:** UXD <status>
<!-- `**Inputs read:**` IS A HEADER LINE OF THIS DOCUMENT, AND ITS FORM IS NOT THIS FILE'S TO
     STATE. `<CORE>/doctrine/governance/unsettled_inputs.md` owns the rule and the form, for every
     document in the chain rather than this one — write the line from there. **Every input this
     revision read, not only the unsettled ones**: a line that appears only when something was
     `Draft` is indistinguishable from a run that forgot it. -->

> The design language is the visual source of truth: the tokens are normative, the prose says
> how to apply them. It is authored off the UXD's § Design-System Direction — that section names
> the system and the constraints; **this document holds every value**. A token value that also
> appears in the UXD is a defect of whichever document copied it. Unlike the UXD, this document
> may legitimately trail the SDD: structural UX must be settled before the architecture locks,
> visual language iterates. Updated in place with versioning (bump the line above whenever a value
> or the prose changes); on a revision it is **stable by
> default** — every changed value traces to an owner answer, a brand change, or an upstream UXD
> change, never a silent re-derivation. Evidence binds where it exists (the product's own
> source, its brand assets, the UXD's direction); where it is silent the value is the CDO's call,
> written here with a stated reason, and the load-bearing calls go to the companion file for
> sign-off. Declare a genuinely inapplicable category in `omitted:` rather than leaving it
> silently absent.

---

## Overview

<The product's brand personality, audience, and the emotional response the UI should evoke —
playful or professional, dense or spacious. This is the context an agent falls back on when no
token or rule covers the case. Name the design system or aesthetic family and the stack it is
realized in: one system per product, named honestly (an official package by name, or the
aesthetic labeled as built-from-primitives). No token restatement, no page summaries.>

## Colors

<Application rules — which role each palette plays and where it is used. Reference tokens by
{path}, e.g. "{colors.tertiary} is the sole driver for interaction, used only for primary
actions and critical highlights."

MODES GO HERE. The format has no Themes section; if the product has light/dark or brand modes
and the token schema cannot express them, carry the alternate values in a table in this
section — documentation, not a second token schema.>

## Typography

<Which level is used where, and the hierarchy rules that change an implementation choice.>

## Layout

<Grid, content width, spacing rhythm, responsive commitments. (Alias: "Layout & Spacing".)>

## Elevation & Depth

<Border and shadow policy: when a surface is elevated and how. (Alias: "Elevation".)>

## Shapes

<The corner-radius system, applied consistently, and border treatments.>

## Components

<Only components with a real contract used across two or more surfaces: the rule that governs
each, referencing tokens by {path}. Not an inventory.>

## Do's and Don'ts

<Do's: implementation-changing rules, sentence case.
Don'ts: ONLY prohibitions the owner or the product has actually made — an invented Don't is a
constraint nobody agreed to.>

---

## DESIGN Review Notes

<Non-spec section — the format preserves unknown headings (verified), and this is where this
instance's provenance discipline lands. Every value the evidence did not settle carries its
*why* here: an owner answer folded from the companion file, a confirmed best-effort choice, or a
cdo-derived value with the derivation that grounds it. On a revision, every change to a settled
value carries the reason that authorized it. The owner's answered companions are retired whole
to `<product>/docs/trail/design/`, so their exact words stay citable; this section is where
*this document* says why its values are what they are.>

- **RN-1:** <the value, and what grounded it> — *because* <reason> *(re: {colors.…}; source: <repo evidence / brand asset / owner answer / instance experience layer>)*

## Traceability

<Every constraint the UXD's § Design-System Direction stated must be satisfied here, or
explicitly answered as not satisfiable. This is the seam that keeps the two documents one
system rather than two opinions.>

| UXD constraint | How this document satisfies it |
|---|---|
| <UXD § 9 constraint> | <token / rule that meets it> |
