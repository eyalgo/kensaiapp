---
version: "1.6.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# Change Spec — <title>

**Date:** YYYY-MM-DD
**Category:** <bug | refactor | nfdr>
**Behaviour:** preserving
**Request:** <verbatim user request>
**Language resolution:** <language | none resolved> — <the resolution-chain step that answered> — <packet README.md opened | floor>; one entry per language

---

## Change Summary

<1–2 sentences: what is restructured and why. Behaviour is unchanged.>

---

## Invariants (characterization contract)

The behaviours that MUST remain true after this change — the existing contract, pinned. Not new rules.

Characterize from the request/diagnosis, `docs/fdr.md`, the public export surface, and any check `nfdr.md`, `SDD.md` or an ADR requires of this change only — **never sourced from implementation bodies.** If an invariant describes how something is done internally (atomic-write strategy, internal counter names, on-disk file format), it is mechanism the change is free to alter — drop it; the suite already covers it. **This binds where an invariant comes *from*, never what you may read to check one.** An invariant sourced as above is then verified against the tree like any other claim about existing code — bodies included — which is § *Verified Claims* below and Step 6's *Claims about existing code (both modes)* pass. Sourcing an invariant from a body invents a contract out of an implementation detail; reading that same body to confirm a contract sourced properly is what stops the claim being a guess — except a claim about what a command decides, which § *Verified Claims* requires be run, never read.

- **The existing test suite passes unchanged** — the suite *is* the characterization contract. Do not re-transcribe the scenarios it guards.
- **Public interface:** <importable symbols / signatures that stay identical>
- <a further behaviour to protect — only if the request names one explicitly, or a check `nfdr.md`, `SDD.md` or an ADR requires of this change, citing that record and item>

---

## Structural Goal

The non-behavioural target of this change — the fix direction, not the layout.

- <e.g. implementation moves out of `__init__.py` into named modules; `__init__.py` re-exports the public interface only>
- Name the target, not the layout — module/file names are development-design's decision; do not propose them here, even illustratively.

---

## Verified Claims

<!-- One row per claim about existing code that an Invariant, the Structural Goal or a Locked Answer rests on — in preserving mode the characterization contract is made of such claims, so this section is rarely short. A claim about what a command *decides* is run-verified, never read-verified: name the command, the tree it ran against, the conditions it ran under — the ones the rule itself fixes, never a harness swapping out what the rule says must be real — and what it returned. Where the tree described does not exist yet, construct it and run against it. `none — no Invariant rests on a claim about existing code` is the zero form; an absent section is not. -->

| Claim | Verified by | What came back |
|---|---|---|

---

## Out of Scope

- <what this change explicitly does NOT address — never a check `nfdr.md`, `SDD.md` or an ADR requires of it>

---

## Locked Answers (the divergence record — self-review YYYY-MM-DD)

<!-- Every decision where the spec departed from or went beyond the request, each with its REASON. A preserving spec deferring layout to development-design is the EXPECTED handoff, not a divergence — do not log it. Log only a genuine departure: a resolved request↔fdr contradiction, a recommendation overridden, or (e) a check a record above the change requires, stated as an Invariant citing that record. Usually omitted for a clean characterization contract. -->

- **Gap N — <label>:** <resolution> — <reason>
