---
version: "1.0.1"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

<!-- The single source of ONE ADR record's shape. Lands at `<Product path>/docs/adr/NNNN-slug.md`,
     one file per architecturally significant decision. Its index is
     `adr_index_template.md` beside this file.

     MODEL-FACING: the `product-architecture` skill reads this file and authors a fresh record, so
     everything here may explain itself and none of it survives into the result. No script stamps it,
     which is why it carries a `version:` at all
     (`<CORE>/doctrine/governance/versioning.md` § Templates — the stamper's code is the proof).

     WHAT THIS FILE OWNS: the parts of one record, their order, and the shape of each. Nothing else.
     What earns a record at all (the three-gate significance test), how a decision is found in the SDD,
     what a faithful recording is, and what a run does with a decision it judges wrong are
     `<CORE>/../skills/principal-architect/.claude/skills/product-architecture/prompts/rich.md`'s — the authoring body this shape is
     stamped under, declared on both sides (`<CORE>/doctrine/setup/authoring_layers.md` § The carriers).
     The posture gate, the file loop and the commit are the `product-architecture` skill's.

     ONE DECISION, ONE FILE, AND THE FILE IS NEVER REWRITTEN. A reversal is a NEW record whose Status
     names the one it supersedes, and the superseded record's own Status line is the only line in it
     that ever changes. That is the whole reason the log is many files rather than one: with one record
     per file the "never a rewrite" rule is checkable from a diff — a commit touching an accepted
     record's body is visibly wrong — where in a single shared document it survives only as prose
     discipline in a file every run rewrites.

     NUMBERING: four digits, scan `docs/adr/` for the highest existing number and increment. The slug is
     a short kebab-case phrase from the title. Numbers are never reused and never renumbered.

     ALTERNATIVES RULED OUT IS MANDATORY, not optional. The minimal practitioner forms make it optional
     because they optimise for a solo author's write-cost; these records are written by one seat and
     read by five cold sessions, and the alternatives are the half a cold reader cannot reconstruct.
     The SDD's own weighing has already been done, so recording it here is transcription rather than
     fresh work — the write-cost argument does not reach this house.

     THE STATUS VOCABULARY HAS NO `Rejected`. A proposal the owner declined is a companion item their
     answer resolved, and the trail already keeps it; a standing file for a decision never made would
     give the log two kinds of entry and its reader a sorting job. Adding `Rejected` later is cheap if
     the owner wants declined options durable in the log itself.

     AND NO `Deprecated` — dropped by the owner, 2026-08-30, for the same reason one step further on.
     Three statuses each have a lifecycle a run can act on: `Proposed` may still be revised, `Accepted`
     is never rewritten, `Superseded by` is how a reversal lands and names its replacement. `Deprecated`
     had none: nothing said what deprecates a record, whether a deprecated one may be edited, or how it
     differs from superseded. It also could not be reached — the producing run only ever moves a record
     Proposed -> Accepted or Accepted -> Superseded — so it was a status no writer could write and no
     rule governed. It came in by faithfully copying Nygard's four-word vocabulary; the industry sense,
     *still true but discouraged*, is a state this chain has no use for, because a record that stops
     being in force here stops by being superseded, and `Superseded by` already carries the pointer to
     what replaced it.

     PROVENANCE — the skeleton is the industry's and the two house fields are ours. Status / Context /
     Decision / Consequences are Nygard's; Alternatives ruled out is MADR's *Considered Options* under
     a plainer name. `## Traces to` and `## Binds` are this template's own: the first applies the
     house provenance discipline to a record so that faithful recording is checkable, the second keeps
     the ADR/NFDR pair navigable in both directions by pointer rather than by copied content
     (`<CORE>/doctrine/governance/single_source.md`). The reasoning for each was written once as a
     research record in the instance that authored this shape, and is deliberately **not cited by path
     here**: every instance stamps from this file, so a path into one instance's own projects resolves
     in none of the others. A second copy of that reasoning here is the one that would go stale. -->

# ADR-NNNN: <the decision, as a short active phrase>

**Status:** Proposed | Accepted | Superseded by ADR-NNNN
**Date:** <YYYY-MM-DD>

## Context

<The forces that made this a decision rather than a default — the SRS requirement, the SDD condition,
or the reality of the product that forced a choice. Enough that a cold reader understands why anyone
had to decide anything here. Not a description of the system.>

## Decision

<What is now true, in full sentences and active voice. Pithy, assertive, on-topic. This is not a design
guide: it says what was decided, not how to build against it.>

## Alternatives ruled out

<One block per option that was genuinely in play: what it was, and the specific reason it lost. "We
just picked it" is not a rationale, and an empty section means the decision had no alternatives — which
almost always means it was not a decision and does not earn a record.>

- **<option>** — <why it lost>

## Consequences

<What becomes easier and what becomes harder — both signs, honestly. What this binds for every later
change, and what undoing it would now cost.>

## Traces to

<The SDD section, SRS requirement, owner answer, or trail cycle that surfaced or authorized this
decision — a path or locator a cold reader can open, not a description. A record whose decision is
visible in the design but argued nowhere is **reconstructed**, and says so here.>

## Binds

<The NFDR entries derived from this record, by their `QC-n` anchor — or `none`. A pointer, never a
restatement of the entry's content.>
