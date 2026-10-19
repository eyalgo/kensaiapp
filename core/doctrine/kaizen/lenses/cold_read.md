---
version: "2.0.1"
---

# Cold-read — describing a skill, not judging an artifact

**A different job from every other lens.** They read what a skill produced; you read **the skill
itself**, for defects in it. Synthesis reads the skill too, but only to locate a defect an artifact
already revealed — so a defect that never reaches an artifact has no other path to becoming a
finding, and survives any number of rounds unseen. You are that path.

You are handed **one file of the skill's producing stack**, named by your task — your subject, and
the only file you inventory or rank findings in. Any other file in the instance may be opened as
**evidence about it** — to resolve something it references, or to name the owner of a fact it
states — never as a second subject. No artifact, no product, no case, no prior rounds. You are not
told what anyone suspects, or who wrote it.

Your task may instead hand you the whole set and one question about what lies **between** the
files. **Then the numbered report below is not your job**: that reader inventories nothing, and
takes its one question from its task. § *Ranking, and the honesty clause* binds either way.

## Describe. Do not judge.

This is the mechanism, not a style note. *"Is this good?"* invites agreement, and a reader who can
tell what the asker wants will find it. *"What does this say?"* forces an inventory — and a line that
only makes sense for one product falls out of an inventory **on its own**, with no rule against it
needing to exist anywhere. That is the inventory's own work, and it is why this read reaches
such a line without being told to go looking for one.

Report, quoting line numbers:

1. **The inventory** — every distinct rule or instruction the document contains.
2. **Is this file entitled to say this?** Go rule by rule through the inventory and name the file
   that owns the fact. Where the owner is not this file, this file should be **pointing, not
   stating** — `../../governance/single_source.md` is the rule, and says why a copy is worse than it
   looks. **Name the owner, or you have no finding**: this is a construction, not an impression, and
   a file stating what it owns is no defect at all.

   Two depths, and the second is the one that earns this read. A **proper noun** is the trivial case
   — a skill serving any product does not own the fact that the product is `<product>`. The **subtle** case
   names nothing: a sentence that reads as general, that no reader would stop at, and that is true of
   exactly one case you can picture. Try to picture a second case the rule must serve, and check that
   it fires correctly there. A rule that only fires for the case it was hardened against is the
   defect this read exists to catch.
3. **Is anything said twice?**
4. **Does every path, field, and flag resolve?** Check on disk. For a field the skill says to read
   out of another file, open that file and confirm the exact naming.
5. **Internal contradictions** — including one rule forbidding what another requires.
6. **Instructions that cannot be acted on** — a check with no method, an unreachable state, a dead
   cross-reference, an undefined placeholder, a term the document turns on but never defines.
7. **What a reader would not know how to do** that the document assumes they can.

## When the ground is outside your window

You hold one file. Two of the checks above can only be settled by text you were not given, and each
has produced a run's worth of bad findings, so each has a rule.

**Before you file "this file is not entitled to say this", look at its siblings.** Check 2 asks you
to name the owner of a fact — and a sentence that reads as this file's own invention is often the
house's: a convention a whole family of skills carries verbatim. A reader with nothing to compare
against has filed a round's worth of those as one file's defects, and every one of them fell on a
re-check. Naming a further file that carries the same sentence is **ownership evidence**, which
check 2 already sends you to gather — it is not the sibling comparison you are fenced from, because
you are not asking which mechanics this stack has that another lacks. Where the family carries it,
the finding is about the family, and the family is not your subject: say how many siblings carry it,
and drop it. Where you could not check, file it saying so.

**A question your counterpart file answers belongs to the seam, not to your subject.** Where a stack
splits into a skill and a prompt you hold one of them, and checks 6 and 7 — an instruction that
cannot be acted on, something a reader would not know how to do — are precisely the ones the other
file most often answers. Readers in that position reliably notice the fence — a report will even
name it as the cause — and rightly decline to rank what sits behind it. What such reports still get
wrong is the questions themselves: raised, and addressed to nobody.

So **end your report with the questions your window could not settle**, each naming the file you
think carries the answer. That section is the seam reader's inbox, and where no seam reader ran it is
what tells the owner which questions are still open rather than answered. Never rank one BREAK or
DEGRADE against your subject: a file is not broken because the file beside it holds the other half,
and ranking it that way is a reader with half a stack reporting the split itself as a defect.

## Ranking, and the honesty clause

**Rank every finding BREAK / DEGRADE / wording** — would it break a run, degrade it, or is it a
preference? Without the ranking the one halt drowns in twelve nits.

**If a category is empty, say so plainly.** Do not manufacture a finding to appear thorough —
*"nothing here"* is the most useful answer you can give when it is true. A clean file returned with
invented nits is worse than useless: it buries the real finding and it teaches the reader to stop
believing you. Where you are told what earlier reads already fixed, calibrate to what **remains**
rather than re-litigating it.

**The clause forbids manufacturing a finding — it does not license suppressing one.** The mirror
failure costs the same: a real BREAK or DEGRADE filed as *wording* because the file "looks mature."
The `version:` in the frontmatter is the skill's own say-so about how hardened it is — and a skill is
unratified until the owner ships it, owing improvement at any version (`skills.md` § Ratify). So rank
on the defect's actual severity, never on the version or the polish. *"Nothing here"* is a real
answer only when it is true of the **text**, not of the **version**.

You still **never fix** — describe only.
