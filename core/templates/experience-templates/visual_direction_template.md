---
version: "1.4.2"
---
<!-- The version above is template-file metadata; it is not copied into the stamped document. -->

<!-- The single source of the shape of an instance's `system/experience/visual_direction.md`.

     MODEL-FACING (`<CORE>/templates/README.md` § the two-consumer table): the `experience-visual`
     skill reads this file and authors a fresh document, so everything here may explain itself and
     none of it survives into the stamped result.

     THE FORMAT IS EXTERNAL AND WE DO NOT OWN IT. This document is written in Google's DESIGN.md
     format — the same format a product's own design language uses, one layer up. The schema's
     authority is the vendor: `npx @google/design.md@0.4.0 spec --rules`. What the linter checks,
     and why a zero exit code is not the gate, was verified empirically and is recorded at
     `<CORE>/templates/product-templates/design_template.md:32-53`; read it there rather than
     re-deriving it. The format self-describes as `version: alpha`, so it moves.

     WHY THIS DOCUMENT EXISTS AT ALL, next to the fence: a fence says what no product may do. This
     document says what products inherit and how to decide when nothing covers the case. Token
     values may live only in a file in this format (`<CORE>/roles/loaders/cdo_global.md` § What you
     own), so an instance with no such file cannot hold a shared value at all.

     WHAT THIS FILE OWNS: the sections and their order. How a value is derived, when it is left
     absent, and how it is marked are `<CORE>/../skills/cdo/.claude/skills/experience-visual/prompts/rich.md`'s — the
     authoring body this shape is stamped under, declared on both sides
     (`<CORE>/doctrine/setup/authoring_layers.md` § The carriers).

     TWO SHAPE DECISIONS THIS TEMPLATE CARRIES, both from the owner's settled calls:
     - § Do's and Don'ts is dropped; the reason lives in § Direction Review Notes, not `omitted:` —
       `omitted:` accepts only missing-token-section entries, and Do's and Don'ts carries no tokens.
       The fence sits in the same folder; a second copy of it here buys nothing.
     - § 0 is a non-spec `##` section. The format preserves an unknown heading rather than erroring
       (verified — `design_template.md:32-35`), and a non-spec section costs zero warnings there.
       Placed FIRST it does not perturb the `section-order` warning either — measured 2026-08-12 on
       a document stamped from this template, with a transposed-section control confirming the rule
       fires when the order is genuinely wrong. So § 0 stays first at no cost, which is what the
       placement was for: a hand-editor meets the governing rules before anything else. -->

---
version: alpha
name: <instance name>
description: <one line — the visual direction every product under this instance inherits>
omitted:
  # The format's sanctioned way to declare a category intentionally absent. Use it rather than
  # leaving a silent hole — and note that "absent" here is a real declaration, not a gap: a
  # category this instance sets no shared value for is one every product decides for itself.
  - section: <token category with no instance-wide value>
    reason: "<either: this instance sets no shared value here, so each product decides — or: waiting on the first design run to fill it>"
# Every category that DOES carry a shared value is written below in the format's own schema, exactly
# as `<CORE>/templates/product-templates/design_template.md` lays it out. That template is the
# schema reference; this one does not repeat it.
---

# Visual direction — <instance name>

**Status:** Draft | Settled | Locked
<!-- Draft = the companion `visual_direction_open_issues.md` is on disk, so something awaits the
       owner. Settled = the companion is gone. Locked = ratified; the owner's act, never the run's.
     A document with no values in it can be Settled. Absent values are a declaration, not an
     unfinished state. -->
**Owner:** CDO
**Version:** <n> — <one line on what this revision changed **about the direction** — which value,
marker or declared absence moved. Not the authoring cycle: no "folded in the owner's answers".>

## 0. What governs this file

The rules this document is authored under are `<CORE>/doctrine/setup/setting_up_an_instance.md`
§ The three rules. Read them there. Nothing in this file repeats them, and a copy that disagrees is
a bug in the copy (`<CORE>/doctrine/governance/single_source.md`).

<!-- Carry the two sentences above into the stamped document as they stand — they are the § 0, not
     guidance about it. Point; never restate. -->

## Overview

<The direction: what products under this instance should feel like, who they are for, and what an
agent should fall back on when no value and no limit covers the case. This is the one section of
this document that carries direction rather than values, and it is what
`<CORE>/../skills/cdo/.claude/skills/experience-visual/prompts/rich.md` holds to the highest bar — a product's design run
reads it exactly when nothing else answers.

No product is described here. No token value is restated here.>

## Colors

<Application rules for any shared colour this instance carries: which role it plays, and where.
Reference tokens by {path}.

EACH SHARED VALUE CARRIES ITS MARKER in this prose — whether a product is bound to it or may
replace it. What the markers are and what an unmarked value means are the prompt's
§ Markers. Modes go here too, as a table: the format has no Themes section.

Where this instance carries no shared colour, this section says so in one line and the category is
declared in `omitted:` above.>

## Typography

<Same shape: the shared levels if there are any, each with its marker; otherwise one line and an
`omitted:` entry.>

## Layout

<Shared grid, content width, spacing rhythm — if the instance holds any. (Alias: "Layout & Spacing".)>

## Elevation & Depth

<Shared border and shadow policy, if any. (Alias: "Elevation".)>

## Shapes

<Shared corner-radius and border treatment, if any.>

## Components

<Only a component contract this instance genuinely holds across products. Most instances hold none;
say so and declare it in `omitted:`.>

---

## Direction Review Notes

<Non-spec section — the format preserves unknown headings (verified). Every value carries its *why*
here: an owner answer folded from the companion, or the citation that grounds it. Every marker
carries why it is that marker: binding a product to a value is a decision with a cost, and the
reason is what a later reader needs to judge whether it still holds. On a revision, every change to
a settled value carries the reason that authorized it. The owner's answered companions are retired
whole to `system/experience/trail/visual/`.

§ Do's and Don'ts is dropped from this document's scope. Record that here, once, as its own line:
the fence is `system/experience/visual_restrictions.md`, in this same folder, and a second copy of
it here buys nothing. `omitted:` cannot carry this — it accepts only missing-token-section entries,
and Do's and Don'ts carries no tokens — so this is where the drop and its reason live.>

- **RN-1:** <the value or marker, and what grounded it> — *because* <reason> *(re: {colors.…}; source: <owner answer / citation>)*
