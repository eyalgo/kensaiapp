---
version: alpha
name: Trimly
description: The design language for trimly's workspace surface — the link list, analytics, and admin screens.
colors:
  primary: "#2563EB"
  primary-hover: "#1D4ED8"
  ink: "#111827"
  paper: "#FFFFFF"
  positive: "#15803D"
  negative: "#B91C1C"
  border: "#E5E7EB"
  muted: "#6B7280"
typography:
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.4
rounded:
  md: 6px
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    typography: "{typography.body-md}"
    rounded: "{rounded.md}"
  table-row:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.body-md}"
---

# DESIGN — Trimly

**Status:** Draft
**Owner:** CDO
**Version:** 1 — first authoring from the product source; the heading scale and the accent are with the owner.

> The design language is the visual source of truth: the tokens are normative, the prose says
> how to apply them. It is authored off the UXD's § Design-System Direction — that section names
> the system and the constraints; this document holds every value.

---

## Overview

Trimly is a utility dashboard for small marketing teams: dense, still, and legible. Built from
primitives with a thin in-house layer — no component package. The emotional register is
"dependable tool", not "marketing surface": recognisable screens, quiet colour, tables first.

## Colors

{colors.primary} is the sole interaction colour — primary actions and links, nothing else.
{colors.ink} on {colors.paper} is the reading pair; {colors.muted} carries secondary metadata
only, never body text. {colors.positive} and {colors.negative} are reserved for click-trend
badges and error text. No dark mode in v1 — the product is used in work contexts on desktop.

## Typography

Inter throughout. {typography.body-md} is the working size for tables and forms;
{typography.body-sm} is metadata only. All figures — click counts, money — render in tabular
numerals (UXD UX-A2). The heading scale above body is unresolved this round — see the
open-issues companion.

## Layout

Density-first (UXD DENSITY 8): the spacing scale tops out at {spacing.xl} for section gaps;
tables use {spacing.sm} vertical rhythm. Content width is full-bleed inside the left-rail shell.

## Elevation & Depth

Flat by default. One elevation step for overlays (dialogs, menus): a border in {colors.border}
plus a single soft shadow. Nothing else floats.

## Shapes

One radius, {rounded.md}, applied to every interactive element and card. No pill shapes, no
mixed radii — the source uses a single radius everywhere and that is kept as the system.

## Components

button-primary and table-row are the two contracts used across all five screens. button-primary
pairs {colors.primary} with white text (AA-checked); table-row pairs {colors.ink} on
{colors.paper}. Hover on button-primary moves to {colors.primary-hover}.

## Do's and Don'ts

Do render all numeric columns in tabular numerals. Do keep {colors.primary} for actions only.
Don't introduce decorative motion — MOTION is dialled to 2 by owner answer (UXD § 2).

---

## DESIGN Review Notes

- **RN-1:** the palette, radius, and body type are read from the product source — *because* they
  are the live values shipped today *(re: {colors.primary}, {rounded.md}, {typography.body-md};
  source: src/styles/tokens.css)*
- **RN-2:** the spacing scale names the five steps observed in the codebase (4/8/12/16/24) —
  *because* they are what the product already uses; no invented levels *(re: {spacing.xs}–{spacing.xl};
  source: src/styles/tokens.css, closing comment)*

## Traceability

| UXD constraint | How this document satisfies it |
|---|---|
| AA 4.5:1 on analytics/table surfaces (UX-A1) | button-primary and table-row pairs both clear 4.5:1 |
| Tabular numerals for figures (UX-A2) | Typography rule: all figures in tabular numerals |
| Density-first (DENSITY 8) | Spacing scale from observed values; body at 14px |
| Stillness (MOTION 2) | Do's and Don'ts: no decorative motion |
