---
version: "1.6.1"
---

# Kaizen lenses

The lenses a kaizen round audits with. Each is one file, versioned on its own, loaded by the
auditor agent — which is plumbing and carries none of this.

**A lens judges the skill, through its output.** That is the distinction from a review: a
reviewer asks *is this artifact good?*, a lens asks *what does this artifact reveal about the
instrument that produced it?* Same document, different question — and a lens worded the first way
has stopped being a lens. Watch for it when adding one.

**Four files here are not lenses, and say so in their own first line.** `cold_read` reads the skill's
text and no artifact; `containment` reads a stack file's text for facts that are not true of every
reader it has; `locate_layer` reads the stack to place a finding the lenses already made —
it is the method the `kaizen-fix-author` applies at the deciding, not a job the audit runs;
`compare_sibling` reads this skill against a ratified one that does the same kind of work.
All are bound by the contract, which is why they live here — but none judges a skill through
its output, so the rule above is not theirs to fail.

**One lens per auditor, and it loads only its own.** A lens that reads its siblings' definitions
learns which failures are somebody else's job, and stops looking there. That is why these are
separate files rather than a list.

## The set

| File | Blind? | When |
|---|---|---|
| `contract.md` | — | Every audit. The reporting grammar, the classification, the standing rules. |
| `cold_read.md` | yes | Step 2 — reads the **skill's own text**, no artifact. |
| `containment.md` | yes | Step 2, beside the cold read — reads a **stack file's own text**, no artifact. |
| `surfacing.md` | yes | Step 4 fan-out. |
| `coverage.md` | yes | Step 4 fan-out. |
| `altitude.md` | yes | Step 4 fan-out. |
| `traceability.md` | yes | Step 4 fan-out. |
| `content.md` | yes | Step 4 fan-out. |
| `provenance.md` | yes | Step 4 fan-out. |
| `compare_versions.md` | **no** | Step 4 synthesis, when a prior version exists. What the artifact **says**. |
| `compare_surfaced_set.md` | **no** | Step 4 synthesis, when a prior version exists and the skill surfaces. What the skill **chose to ask**. |
| `locate_layer.md` | **no** | Step 4 deciding — applied by the `kaizen-fix-author`, one skill-general finding at a time. Which **layer** carries it. |
| `compare_sibling.md` | **no** | The **escape hatch** (and stack setup), when a ratified sibling exists. Which **mechanics** only this skill has. |

The blind lenses each get the artifact and its inputs, and nothing about each other — and never the
skill. `compare_versions` and `compare_surfaced_set` need both versions by definition, so they cannot
be blind — run them at synthesis, never hand one to a lens auditor, or the fresh read is gone. The
same bar covers `compare_sibling`, which needs two skills: it runs at the hatch, never inside a round.
Two jobs here read a whole stack, the skill included, and neither is the audit's — `locate_layer` is
the fix-author's read at the deciding, and `compare_sibling` reads this stack against a sibling's;
`contract.md` § Classification owns why the layer is named there and nowhere in the audit.

## Growing the set

The set grows as rounds reveal failure shapes; that is expected, and `development-audit`'s own lens
set grew the same way. But a lens set is a rule set, and rule sets rot the way `skills.md` describes:
a new lens must name a **shape of failure**, not an instance of one. If it only fires on the case
that prompted it, it is a finding, not a lens.

Bump a lens's own version when you sharpen it — then the audit that used it can say which version
found what, and whether sharpening it earned itself.

## What does not live here

- **Flow-audit's lenses.** The change pipeline's audit step (`development-audit`) audits the
  pipeline's output, not a skill; its lenses are owned by the `development-audit` skill and are a
  different set answering a different question.
- **Why and when.** `../skills.md` — the loop these serve.
- **How the loop's evidence is stored.** `../../engineering/skill_evidence.md`.
