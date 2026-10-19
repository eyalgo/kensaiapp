---
version: "1.2.0"
---

# Ratifying a skill — what happens when the owner says ship it

`skills.md` § Ratify owns what ratification **is**. This file owns what it **costs** — what must be
true before a verdict can mean anything, where the verdict lives, the places a ratification is
recorded, and what later ends the claim.

It is a file rather than a paragraph because a ratification is the only thing in kaizen spread across
three kinds of repo: the instance the skill lives in, the product repos holding the output being
judged, and the audit instance holding the vault. Each has been the site of a miss — a step that
lands in a repo you are not sitting in is the step a session forgets.

## Before — what a verdict rests on

**1. A round has settled, and ratification is how the skill leaves the loop.** The owner's "ship it"
is taken **instead of** step 7's return to 2 in `skills.md` — it ends the looping rather than sitting
inside it. So it follows a settled run (step 3, and whatever audit followed at 4) and is judged on
that round's outputs, which is why it comes before step 6 deletes them.

A version under ratification is also a version that stopped moving. `skills.md` § Why every round
starts clean owns why a mid-round bump destroys the control; it binds harder here, because a stack
that moves while it is judged leaves the verdict naming something that no longer exists.

**2. The evidence is this version's own output, on at least two independent cases.**
`<CORE>/prompts/ratify_skill.md` § What a verdict may rest on owns that rule and the reasoning
behind it. What this file adds is the **checkable form**: each producing commit in the case repos
carries `Skill-Version: <skill>@<version> <sha>` (`../governance/commit_format.md` § `Skill-Version:`
trailer). That trailer is what makes "this version produced it" a fact you can grep for rather than
a claim you assemble from dates. A case whose commits carry a different version is a different
version's output, however recent it looks.

**3. What is ratified is the stack, not the file.** A skill is its `SKILL.md` plus the files it
draws on — its authoring prompt above all — and `stack.json` is the manifest of which. A verdict
that names one version has judged a pair (or a set) and must state each file at its own version,
or nobody can later tell what was signed.

## The verdict

**4. Run it through a launcher, never a composed prompt.** A session asked to ratify composes the
prompt, and that is the one place a lean leaks into a run that exists to be independent. The
launcher builds a fixed prompt around `<CORE>/prompts/ratify_skill.md` on the independent model
(`model_assignment.md`), and a caller passes identifiers, never prose. This instance carries no
ratify launcher, so do not ratify by composing the prompt by hand: build the launcher first. A
case resolves one of two ways — a `product-*` skill's case names a **project**, whose
`Product path:` locates the document; an instance-level skill's case names an **instance**, whose
root locates it, as `kensaiapp-writing-bar`'s does at `system/doctrine/writing_bar.md`.

**5. The verdict has one home:**

```
system/projects/<managing-project>/docs/<skill>_ratification_verdict.md
```

in the instance that manages the skill's project — the path a launcher resolves from
`--project`, committed by the ratifying run itself. This is doctrine rather than convention
because the path has wandered: one verdict has lived under the skill's own `references/`, under the
audit instance's `references/`, and here. Three copies of one fact, and the stale ones do not
announce themselves. A copy that is *frozen* with the evidence (step 6) is a snapshot and is fine;
a second **live** home is not.

## After — the three places a ratification is recorded

Nothing below is optional, and all of it happens outside the session that produced the verdict.

**6. Freeze the evidence in the audit vault**, in the version folder for the version just ratified —
**the verdict goes in with it.** `../engineering/skill_evidence.md` owns where that folder lives, how
it is keyed, and everything it holds, the verdict copy included. The freeze is what makes the
signature survive its own success: the verdict cites the case's live outputs, and the next version
overwrites them.

**7. Update the skill's `README.md`** — its *Version and ratification* section carries the **status**:
ratified at these versions, a link to the verdict, and whether what is on disk is still the signed
pair. Not the reasoning, the cases, or the ratifying model — those are the verdict's, and a second
live copy of them is what step 5 forbids. The standing claim is the README's own fact, because it is
about files that keep changing after the verdict is frozen.

**8. Close the round** — the station retires and the seed item it was opened from ticks
(`shukuba-retire` owns that move). A ratification is the end of a round, not a thing beside it.

## The claim is about versions, and a bump ends it

**9. A verdict is a statement about the versions it judged, and stays one.** It does not carry
forward. Any bump to any file in the stack ends the standing claim, and the README stops claiming it
**in the same session as the bump** — the stack then reads *ratified at v<x>, plus changes nobody has
signed*, which is an honest and perfectly workable state to sit in.

**A bump is a bump.** The rule does not weigh whether the edit was substantive, and must not:
deciding case by case which changes "really" invalidate a verdict is how a signature stops meaning
anything, and the weighing always runs in the direction of keeping the badge. An edit that only
changed what the role *knows* still ends the claim; say so plainly in the README rather than
carrying it as an excuse.

What ends is the **claim**, not the verdict. The verdict remains true about the versions it judged
and stays where it is. Re-earning the claim is a fresh round at the current stack, producing the
output a new verdict would judge — an ordinary round, not a repair.

## What a ratified skill becomes

**10. A referent.** `lenses/compare_sibling.md` reads a skill against a ratified sibling to find the
mechanics only this one carries — the one read in the loop whose referent is not the skill's own
text. So each ratification makes the next skill's hardening cheaper, and this is the one check whose
cost falls as the instance grows.

That lens also makes a ratified skill **read-only in that role**: editing it to close a gap found
while auditing a *different* skill un-ratifies it silently, spending two ratifications for one read.
`compare_sibling.md` owns that constraint.

## Relationship to other docs

- `skills.md` § Ratify — what ratification is, and why an auditor-clean gate is the shape to avoid.
  That file owns the meaning; this one owns the act.
- `<CORE>/prompts/ratify_skill.md` — the lens the ratifying run reads: what "ratifiable" means, the
  verdict values, what evidence may be rested on, and the verdict file's own shape.
- `../engineering/skill_evidence.md` — how a version's evidence folder is keyed and what it holds.
  Step 6 is that convention applied at the moment a version is signed.
- `lenses/compare_sibling.md` — what a ratified skill is used for afterwards, and why it must not be
  edited in that role.
- `../governance/commit_format.md` — the `Skill-Version:` trailer that makes step 2 checkable.
