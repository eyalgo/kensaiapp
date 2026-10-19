---
version: "1.1.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->
<!-- Use this template for a Behaviour: preserving change on a product with no code (its project card reads Test command: none). The mechanism is <CORE>/doctrine/flow/change_classification.md § A product with no code. -->

# Change Design — <title>

**Date:** YYYY-MM-DD
**Category:** <copied verbatim from change_spec.md>
**Behaviour:** preserving
**Publishes text:** no
<!-- A preserving change adds no words, so the line is always `no`. Moving existing text is placement, and placement is the Developer's. -->

---

## 1. Change Summary

<1–2 sentences: the arrangement this change makes. No statement is added, dropped or weakened.>

---

## 2. Blast Radius

| Document | Status | What changes |
|---|---|---|
| `<doc>` | `Modified (text moved or reworded)` \| `Modified (text moved out, pointer left)` \| `New (moved text only)` \| `Cites a moved statement's old place` | <which invariants leave, enter or are reworded here; or which citation goes false, and whether a pointer keeps it true or the citation is updated> |

<!-- Search the product root for every citation of a section a statement leaves. Each is a row: it goes false when the text moves unless a pointer keeps it true. A product record (`adr/`, `nfdr.md`, `fdr.md`, `SDD.md` § 3) that cites it is not a row: it goes under *Records this change makes false* below and stays owed, never edited. -->

---

## 3. Layout Plan

Every invariant from `change_spec.md`, with its final after-place. Where the spec left an after-place
open, this table settles it.

| Invariant | Before: document § section | After: document § section |
|---|---|---|
| I-1 | `<doc>` § <section> | `<doc>` § <section> |

Pointer: `<doc>` § <old section> → names `<doc>` § <new section>   <!-- each pointer says only where the text now stands -->

---

## 4. Code Strategy

None — no code.

---

## 5. Test Continuity

No suite — each invariant is checked by reading, or by a command that finds its quoted words.

---

## Records this change makes false

<!-- Always present. Every sentence in a product record — `adr/`, `nfdr.md`, `fdr.md`, `SDD.md` § 3 under the product's docs/, where they exist — that goes false when this change lands; a record that names where a statement lives is the usual one. This skill never edits a record; development-plan carries each line into its "Owed outside this change's reach" correction. The zero form names what was read. -->

- `<record>` — <what this change makes false> → <what it should say once this change has landed>.

(or: `None — read <records>; nothing in them goes false.`)

---

## Architect Review Notes

<!-- Every decision that departed from or went beyond change_spec.md, each with its reason — an after-place the spec left open and this design settled is the expected handoff, not a divergence. -->

- <decision> — <reason>
