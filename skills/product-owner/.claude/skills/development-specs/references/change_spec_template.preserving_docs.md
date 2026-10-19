---
version: "1.1.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->
<!-- Use this template for a Behaviour: preserving change on a product with no code (its project card reads Test command: none). The mechanism is <CORE>/doctrine/flow/change_classification.md § A product with no code. -->

# Change Spec — <title>

**Date:** YYYY-MM-DD
**Category:** <bug | refactor | nfdr>
**Behaviour:** preserving
**Request:** <verbatim user request>

---

## Change Summary

<1–2 sentences: what text is reworded, reordered, split or moved, and why. Every statement stays true.>

---

## Invariants (characterization contract)

Every statement this change touches, quoted as the documents state it now. Each has two places: where
it stands before the change, and where it will stand after. A statement that is not moving has the
same place twice. Take statements from the documents' own words, never from what the text might imply.
A statement the change would drop, weaken or add is not an invariant. It means the change is not
preserving, and the spec halts `behaviour-delta-detected`. A pointer left at a moved statement's old
place, saying only where it now stands, is not an addition. List it under the table as `Pointer:`.

| # | Statement (quoted) | Before: document § section | After: document § section |
|---|---|---|---|
| I-1 | "<the statement, verbatim>" | `<doc>` § <section> | `<doc>` § <section>, or `open — development-design places it` |

Pointer: `<doc>` § <old section> → names `<doc>` § <new section>   <!-- one line per pointer; omit when none -->

---

## Structural Goal

The arrangement this change makes, and why it is better. Say what the reader gains, not the exact
section layout; any after-place left open above is development-design's decision.

- <e.g. the setup steps move out of the README into their own document; the README keeps a pointer>

---

## Verified Claims

<!-- One row per claim about the documents that an Invariant or the Structural Goal rests on — that a statement is quoted exactly, and stands where the Before column says. Verified by opening the document, or by a command that finds the quoted words, with what it returned. `none — no Invariant rests on a claim about the documents` is the zero form; an absent section is not. -->

| Claim | Verified by | What came back |
|---|---|---|

---

## Out of Scope

- <what this change explicitly does NOT address — never a check `nfdr.md`, `SDD.md` or an ADR requires of it>

---

## Locked Answers (the divergence record — self-review YYYY-MM-DD)

<!-- Every decision where the spec departed from or went beyond the request, each with its REASON. An after-place left open for development-design is the EXPECTED handoff, not a divergence — do not log it. Log (e) for a check `nfdr.md`, `SDD.md` or an ADR requires of this change, stated as an invariant citing that record. -->

- **Gap N — <label>:** <resolution> — <reason>
