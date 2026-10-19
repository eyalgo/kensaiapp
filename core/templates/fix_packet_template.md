---
version: "1.0.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# Fix packet — <skill> <from-version> → <to-version>

**State:** awaiting-owner | approved
**Verdict:** fix | rebuild
**Audit:** <path to the audit.md these entries answer>
**Projected net lines:** <current> → <projected> (<+/-n>)

> The baton from `kaizen-fix-author` (who decided and wrote it) to `kaizen-fixer` (who applies it).
> The rules for every field are `<CORE>/doctrine/kaizen/fix_packet.md`.
>
> **The fixer has this file and nothing else** — it has not read the audit. Every anchor must resolve
> and every replacement must be final prose, or the deciding lands back on the wrong tier.
>
> **`State: approved` is the owner's move, and the fixer refuses anything else.** Entries can rest on
> a call the owner has not yet made; until they mark it, this is a draft that happens to be executable.

---

## Verdict

<One paragraph. On `fix`: why patching is the right move here, against the escape-hatch conditions in
`skills.md` § *A fix subtracts or trades* — which you checked, and what you counted. On `rebuild`: the
case, in full — which conditions hold, with the evidence, and what the rebuild would cost. **A
`rebuild` packet stops here and carries no entries.**>

---

## Entries

### E1 — <what this fixes, in one line>

- **File:** <path — the layer the audit's locate named, not a default>
- **Anchor:**
  ```
  <the exact current text being replaced, quoted, long enough to be unique in the file>
  ```
- **Replacement:**
  ```
  <the final prose, verbatim, as it will read in the file>
  ```
- **Subtracts or trades:** <the rule this removes or supersedes — or "nothing; this can only add",
  which is a finding to report, never a blank>
- **Conditional on:** <the adjudication this waits for, if any — otherwise omit this field>

<!-- add E2, E3, … as needed. If two entries touch the same passage, or one's anchor only exists
     after another lands, they are applied in the order listed — say so here. -->

---

## Out of scope

<What the fixer is NOT being asked to do, and why. Absent this, an unlisted finding reads as an
oversight and invites improvisation.>

- **Declined:** <finding — why it is not a defect>
- **About the artifact, not the instrument:** <finding — recorded, not fixed>
- **Deferred to the owner:** <the adjudication, and what it blocks>

---

## Owner adjudications

<Only what is genuinely the owner's — a design call the audit surfaced rather than settled. Options,
what each costs, and your recommendation. Draft the replacement text for the recommended option under
Entries, marked `Conditional on`, so it is ready if they take it. Omit this section if there are none.>

### A1 — <the decision, in one line>
- **What turns on it:** <which entries, and what changes depending on the answer>
- **Options:** <each, with its cost>
- **Recommendation:** <your lean, and why>

<!-- The owner answers in `owner_answers.md` beside this file, stamped from
     `<CORE>/templates/owner_answers_template.md` — never in here. This packet is your record; a
     field for them to fill would make it a document two hands wrote. -->
