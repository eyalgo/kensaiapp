---
version: "2.8.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# Change Design — <title>

**Date:** YYYY-MM-DD
**Category:** <feature | bug | refactor | nfdr>
**Behaviour:** changing
**Publishes text:** <yes — the places the words live | no>
<!-- Decided by the CP-438 test: does this change put text in front of a person to read? `yes` names each place, as the person knows it. Otherwise write `no`. The chain reads the first word, which must be exactly `yes` or `no`. -->
**Language resolution:** <language | none resolved> — <the resolution-chain step that answered> — <packet README.md opened | floor>; one entry per language

---

## 1. Change Summary

<one-paragraph description of what changes, which modules are affected, and why>

---

## 2. Blast Radius

<!-- Each new piece of logic is named in the *What changes* cell of the module holding its owning part (docs/SDD.md § 3). With no § 3 parts table, say so in one line above the table. -->

| Module | Status | What changes |
|---|---|---|
| ... | ... | ... |

---

## 3. Sub-jobs

(omit this section if only 1 module is affected)

### Sub-job A — `<module>`
**Scope:** <what this sub-job changes>
**Exposes:** <interface contract — types, signatures, schema entries that downstream sub-jobs consume>
**Depends on:** none

### Sub-job B — `<module>`
**Scope:** <what this sub-job changes>
**Exposes:** <interface contract>
**Depends on:** Sub-job A (needs `<specific type / signature>`)

**Build sequence:**
```
Parallel start: Sub-job A [, Sub-job N if independent]
After A: Sub-job B, Sub-job C  [parallel]
After B + C: Sub-job D
```

---

## 4. Code Strategy

<!-- A hint only where the approach is non-obvious: a non-obvious algorithm, a library-specific pattern, format parsing, a protocol constraint. Everywhere else the row reads `None`. A hint names the approach — algorithm shape, data layout, atomicity pattern, key library call — never production code, type annotations, working definitions, or complete logic. Every sub-job has a row; `None` is a stated answer, a missing row is not. There is no `Complexity` column: retired 2026-09-09, the owner's call. A write into a repository that is neither the instance worktree nor the product worktree puts its commands in this column, and they are not a hint: each one plain call, the status check and the undo included, naming the allow rule each matches or carrying a `No allow rule:` line (SKILL.md Step 4). -->

| Sub-job / change | Hint |
|---|---|
| ... | ... |

---

## 5. Test Additions

<!-- Layer: the layer's number and name from `<CORE>/doctrine/engineering/testing_doctrine.md`. Fakes handed in: each collaborator the test fakes and the seam it arrives through, or `none` (`testing_doctrine.md` § *A unit test hands its unit fakes and touches nothing real*). -->

| Sub-job | Test file | Layer | Fakes handed in | What to add / modify |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

---

## Testing the change from outside the code

<!-- Always present. State how this change's new or changed behaviour is made testable from outside the code, through the way in the product's NFDR records. The way in is read from the `Behave way in` line of § 9 in the product's `docs/nfdr.md`. This section picks no way in and offers no choice of one: it uses the way in that line records. Write the zero form where the record holds no way in: no `docs/nfdr.md`, a `**Behave:**` line that does not read `behave`, a way-in line still holding its three forms written together, or a `**Behave:**` line that reads `behave` with no `Behave way in` line at all. -->

- <the behaviour this change adds or changes> — reached through <the way in the NFDR records>: <what a scenario does through that way in to see the behaviour>.

(or: `None — no way in is recorded (<what was read and what it held>), and this design picks none.`)

---

## Records this change makes false

<!-- Always present. Every sentence in a product record — `adr/`, `nfdr.md`, `fdr.md`, `SDD.md` § 3 under the product's docs/ — that goes false when this change lands. This skill never edits a record; development-plan carries each line into its "Owed outside this change's reach" correction. The zero form names what was read. -->

- `<record>` — <what this change makes false> → <what it should say once this change has landed>.

(or: `None — read <records>; nothing in them goes false.`)

---

## Architect Review Notes

<!-- The divergence record. Required whenever the design departed from or went beyond `change_spec.md`; omit the section only when it added no decision beyond the spec. Always log, each with its reason: (a) resolving a contradiction between two stated contracts — never one with the `Behaviour` label, (b) locking an observable behaviour the spec left implicit — in particular HOW a stated contract is realized by construction (e.g. an ordering realized via an explicit sort key, cf. cold-read #5), (c) overriding an upstream recommendation, (d) departing from this skill's own stated shape — the sub-module cut is the case that recurs. A silent resolution turns a reviewable decision into an unexamined assumption. -->

- **<label>:** <decision> — <reason>
