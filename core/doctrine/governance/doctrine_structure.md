---
version: "1.5.1"
---

# Doctrine structure

This file defines how a project's doctrine is structured, classified, and revised. The meta layer — not trading rules, not AI rules. Those live in project-specific doctrine files. This file carries only the structural principles.

## Doctrine sources

- **`AGENTS.md`** — runtime contract. Contract-shape stubs of the doctrine, loaded on every session.
- **Project doctrine directory** (e.g. `system/doctrine/`) — binding full specifications. Loaded on demand when a stub references a body.
- **Project ADR directory** (e.g. `system/adrs/`) — point-in-time architectural decisions. Binding from ratification.
- **Project paper trail directory** (e.g. `system/paper_trail/`) — historical findings, rejected approaches, decision context. Non-binding.

## Consistency model (no override hierarchy)

The general rule is `single_source.md` — a fact has one owner, every other file points at it, and a restatement that disagrees is a bug in the copy rather than a precedence call. What is specific to doctrine, and what this section owns, is **which side is which: the body is the owner, and the `AGENTS.md` stub is the copy.**

So a stub **summarizes** its body; it never **overrides** it. If the two disagree, the stub is wrong — fix the stub. There is no scenario where `AGENTS.md` "wins": the stub is a contract surface, the body is the contract.

A stub is the one copy this system keeps on purpose, because the runtime needs the contract every session and a body is loaded on demand. It is a copy all the same, and it drifts like one — which is why the check exists at all. The exception is earned by a stub being unable to be a pointer; nothing that *can* point gets it.

## ADR promotion lifecycle

ADRs in the project's ADR directory are binding from ratification. When an ADR's decision generalizes into a standing rule (referenced beyond its originating context, or cited by other ADRs / cross-role contracts), the rule is **promoted** into the project's doctrine directory. The original ADR remains as the historical decision record; the project's doctrine directory carries the rule going forward.

**Promotion is tech lead proposal, Product ratification** — same shape as Tier 2 doctrine reshape per §Doctrine tiers below. The tech lead proposes the promotion in conversation or in a retro; Product ratifies; one commit lands the new project doctrine content + a "Promoted from ADR <path>" note.

## Doctrine tiers

Doctrine items are tier-classified to enable customer-driven reshape without compromising safety.

**Tier 1 — Safety. Never flexes.** User-owned. Roles do not raise reshape candidates. PM does not touch.

**Tier 2 — Architecture. Flexes via formal review when customer evidence demands.** PM raises reshape candidates with evidence; user + Tech Lead decide together. Changes generate an ADR in the project's ADR directory.

**Tier 3 — Product. Customer feedback reshapes freely between iterations.** PM owns the recommendation; user owns the call.

The project's doctrine_structure overlay carries the concrete per-tier classification table with project-specific items.

## How tiers move

- A change to Tier 1 requires user explicit decision; no role can propose. (Even raising a Tier 1 reshape requires a doctrine-change event per §Doctrine change protocol.)
- A change to Tier 2 requires PM-raised evidence + Tech Lead review + user ratification. The change generates an ADR in the project's ADR directory.
- A change to Tier 3 happens routinely between iterations as customer evidence accumulates.

**When a doctrine item's tier is unclear, PM raises it for user classification. When in doubt, prefer the higher tier (more locked).**

## Versioning

Owned by `versioning.md` — which artifacts carry a semver `version:` (doctrine files do, in their
frontmatter), the marker's form per kind, and the bump semantics.

## A rule-stating file is its own first reader

**A file that states a rule is checked against that rule, in its own prose, before it is called done.**
Not the task it was written for — the artifact. Auditing the task (rows repointed, file registered, no
stale references) passes straight through a file that breaks its own rule in the sentence stating it.

This is a structural principle rather than a style note, because a rule-stating file is the one
document whose credibility rests entirely on its own compliance. A reader who finds the rule broken in
the file that states it has been told what the rule is worth, and no later enforcement recovers that.

The check is cheap and it is specific: read the finished file as its first reader, against the rule it
just stated, before the commit.

## Doctrine change protocol

Doctrine changes invalidate in-flight iterations — surface as a doctrine-change event, not a silent edit. When doctrine moves, the tech lead re-scopes affected open issues. Claude may propose `[PROPOSED]` changes but never ratifies them unilaterally.
