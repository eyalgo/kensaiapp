---
version: "1.9.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# Change Spec — <title>

**Date:** YYYY-MM-DD
**Category:** <feature | bug | refactor | nfdr>
**Behaviour:** changing
**Request:** <verbatim user request>
**Language resolution:** <language | none resolved> — <the resolution-chain step that answered> — <packet README.md opened | floor>; one entry per language
<!-- Omit the Language resolution line on a product with no code (Test command: none). -->

---

## Change Summary

<1–2 sentences: what changes and why>

---

## Rules

<!-- PO altitude: pin observable behaviour only — the literal output (lines, order, exit codes), stated directly as shapes (e.g. `{id}: {name}`, `No projects.`). Never anchor a rule to another command's internals, persistence/bootstrap mechanism, counters, or on-disk format, and never specify output "by reference" to another command ("same style as X"). -->

<!-- Identifiers: each rule opens with a CP-<n> label continuing the project's own series, never restarting at CP-1 and never refilling a gap. The scheme and how to find the next number are `<CORE>/../skills/product-owner/.claude/skills/development-specs/SKILL.md` § Step 5, "The series belongs to the project, not to the change". -->

### <Group> — <title>
- **CP-<n>:** <rule>
- **CP-<n>:** <rule>

---

## Examples

| Scenario | Expected behavior |
|---|---|

---

## Verified Claims

<!-- One row per claim about existing code that a rule, an Invariant or a Locked Answer rests on. A claim about what a command *decides* is run-verified, never read-verified: name the command, the tree it ran against, the conditions it ran under — the ones the rule itself fixes, never a harness swapping out what the rule says must be real — and what it returned. Where the tree described does not exist yet, construct it and run against it. `none — no rule rests on a claim about existing code` is the zero form; an absent section is not.  Also one row per rule pinning output that renders a language-level fact (SKILL.md Step 6, *Language rendering*): the rule in *Claim*, and in *Verified by* the fixing packet line (file:line, quoted) or one of `packet does not fix it` (also for a resolved language with no packet), `language not resolved` (also for a language the chain did not resolve), or the packet line plus the overriding product record; in *What came back*, the rendering the rule now states. These rows are not claims about existing code. Where the rendered fact is read from code the product already has, the rule also gets its *Claims about existing code* row; the rendering row does not replace it. A spec with rendering rows and no code-claim row still writes the zero form, beside the rendering rows. -->

| Claim | Verified by | What came back |
|---|---|---|

---

## Out of Scope

- <what this change explicitly does NOT address> — never a check nfdr.md, SDD.md or an ADR requires of it
- <a record's behaviour the product does not have today, binding nothing this change adds or alters, that the request does not ask for — or one the request explicitly rules out, quoting its words: the record and item, then where the product does otherwise today (file:line) — also parked in deferred_decisions.md as a record gap (SKILL.md Step 5)>

---

## Locked Answers (the divergence record — self-review YYYY-MM-DD)

<!-- Every decision where the spec departed from or went beyond the request, each with its REASON. Required whenever any such decision was made; omit only if the spec restates the request with no added decision. Always log: (a) resolving a contradiction between the request and docs/fdr.md, (b) locking an observable behaviour the request left implicit (conservative-pick on an ambiguous direction — append vs replace, sort order), (c) overriding a recommendation the request stated, (d) restating a rule to the rendering a packet line fixes, where the request (its rule or its example) states the rendering otherwise (SKILL.md Step 2), (e) stating as a rule a check nfdr.md, SDD.md or an ADR requires of the change, where the request left it out or deferred it (SKILL.md Step 5), (f) naming an existing test as changing that the request did not name, with what it keeps asserting (SKILL.md Step 6). A silent resolution turns a reviewable decision into an unexamined assumption. -->

- **Gap N — <label>:** <resolution> — <reason>
