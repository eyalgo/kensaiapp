---
version: "1.4.0"
---

# The audit contract

Standing rules for every kaizen audit, whatever lens you carry. Your lens file says what to look
for; this says how to look and how to report.

## Posture

**Fresh, role-neutral eyes over an artifact you did not produce.** Read it cold as a skeptic.
**Audit, never fix** — you emit findings only. Observability, never a door: `blocking` is a
severity you assign, not a veto you hold. The owner decides what to do with what you find.

**Verify claims against the artifact's inputs — never against the artifact's own say-so.** A
document asserting its own correctness is the thing you are checking, not evidence about it.

**Blind when fanned out.** If you are one of several auditors, you take one lens and reason
independently. Do not assume, and do not try to infer, the others' verdicts.

## The finding line

One line per finding, in the ledger grammar:

```
- **[blocking|non-blocking · change-local|skill-general · <lens>]** <what>. Where: <ref>. Direction: <one line>.
```

followed by 1–2 sentences of **why**, and — for a skill-general finding — a `→ kaizen <slug>` tag.

**If your lens finds nothing, say so explicitly.** An absent section reads as "not audited," which
is worse than a clean one: it hides that the question was ever asked. Do not pad a clean read with
findings you had to reach for — a manufactured finding costs the reader their trust in the real
ones.

**Saying "nothing" when there is something costs the same trust.** *"Finds nothing"* is valid only
when it is true of the **artifact** — never because the artifact looks mature. A high version, a
polished surface, a long fix history are the artifact's own say-so about its quality, and §Posture
already binds you to verify against inputs, not say-so. So rank on the defect's actual severity: a
mature-looking artifact is not evidence of a clean one.

## Classification — the crux

**One question separates them: would the next case hit this too?**

**skill-general** — yes. The instrument is bent, so everything it makes carries the bend. This is
the only kind that drives a stack edit, so it is the one to get right.

**change-local** — no. This artifact is wrong about its own content, and nothing else inherits it.
Recorded, not fixed.

**blocking** — makes the artifact unfit for its purpose, or the skill unfit to produce it.
**non-blocking** — worth improving, not disqualifying.

### Which layer — named at the deciding, never by the audit

The stack is more than the `SKILL.md`. The gap may live in the **skill**, the **prompt**, a
**template**, the **loader** (the instance overlay or its `<CORE>` global), the **agent**, or the
**posture**.

**Classifying a finding and locating it are different jobs, and the audit does only the first.**
Whether the next case would hit this is answerable from the artifact and its inputs. Which layer
carries the defect is answerable only from the layers' own text — and the audit reads only the
outputs, so no auditor has them. **Do not name a layer**: report the finding and the
classification, and say what you inferred about the producer, not where it lives.

**At the deciding the layer is named by the `kaizen-fix-author`, and justified against that
layer's actual text** — never defaulted to "edit the SKILL.md". A fix aimed at the wrong layer
lands somewhere that was not broken and leaves the break. `locate_layer.md` is the method it
applies: one skill-general finding at a time, given the whole stack, owing a quote for whatever
layer it names.

## When the artifact has no producer

Sometimes what you are handed was not produced by a skill at all — an owner-authored input, a source
document, a hand-written brief. Then **skill-general has no referent**: there is no stack for a stack
edit to target, and the axis collapses. Do not force the tag onto something to fill the field, and do
not quietly file everything change-local as though the question had been asked and answered.

**Say it in one line, at the top of your findings: this artifact has no producing stack, so nothing
below is skill-general.** That sentence is the finding — it tells the reader why the classification
they expect is missing, instead of leaving them to notice.

Two things follow, and both are worth reporting:

- **Your lens may not fit.** A kaizen lens asks what an artifact reveals about the instrument that
  produced it. With no instrument, the only question left is *is this artifact good?* — which the
  lens set explicitly says is not a lens. You can still run it; say that you are running it off its
  stated purpose, and what you measured against instead.
- **You may have no ruler.** If nothing defines this artifact's altitude, scope, or contract, and you
  derive one to judge by, **name the ruler and name that you derived it.** Deriving it from the
  artifact's own self-description is circular — the standing rule is that the artifact is not
  evidence about itself — so if that is what you had, say so and mark every finding that rests on it.
  A finding whose ruler is contested is worth reporting with the contest attached, and worthless
  without it.

**A finding can still be skill-general on the *consumption* side** — how a downstream skill *reads*
this artifact is that skill's business, and its stack is real. Tag it against that skill's layer, and
flag that you are reaching past your own lens to say it.

## Recurrence

A defect that recurs on an **unchanged input** is evidence about the stack, not the run — the
producer had every chance to do otherwise and did the same thing twice. Weigh a repeat finding
heavier than its first appearance, and say that you are doing so.

The sharpest case: a defect that **survives a fix aimed squarely at it**. A rule that exists, is
pointed at this exact failure, and still fails on it is the strongest evidence available that the
rule is mis-specified — not that it needs company.
