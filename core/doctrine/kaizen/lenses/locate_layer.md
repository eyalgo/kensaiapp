---
version: "1.3.0"
---

# Locate — which layer carries the defect

**A different job from a lens, and not the audit's.** Lenses ask what an artifact reveals about
the instrument. This is the method the `kaizen-fix-author` applies at the deciding — handed
something already revealed, one skill-general finding, and asked where in the instrument it lives
before a fix can be directed there. Nothing is being judged here; something is being found.

**Not blind.** This runs after the audit has returned, where the fresh read is already spent. You
have the whole stack, the skill included. Work one finding at a time, on its own merits — where
the last finding landed must not steer where this one lives.

## Your question: which layer's text, had it said something different, would have prevented this?

That is a counterfactual, and it is the whole method. It cannot be answered by feel — it sends you
into a layer's actual text to check whether that text, changed, would have stopped this. Answer it by
reading, and quote what you read.

The layers are `contract.md` § Classification's list. Do not keep your own.

## Read the layer as it stood

A finding comes from a run, and that run had a stack. **Read every layer at the version that produced
the artifact, never at today's.** Evidence is keyed by producing version and git holds the rest —
`git show <commit>:<path>` is the whole technique.

Skipping this does not give you a cautious wrong answer, it gives you a confident one. A layer that
gained the offending text *after* the run reads as the obvious culprit, complete with a real quote,
and nothing about the quote will tell you it is anachronistic. **A quote from the wrong version
satisfies every check this file makes.**

**Never default to the skill.** The skill is the layer you already have in mind, so it is the one you
will reach for tired, and a tag that lands there by gravity rather than by reading is worth nothing —
`contract.md` says a fix aimed at the wrong layer lands somewhere that was not broken and leaves the
break. If your answer is the skill, it is because you read the skill's text and can quote the line
that would have prevented this, same as any other layer.

**For a producing stack that splits orchestration (a skill) from authoring doctrine (a prompt), say
which side the finding falls on before quoting a layer.** The boundary test: would the fix change how
the author *thinks about a claim*, or how the run *moves files*? Thinks-about-a-claim → the authoring
prompt. Moves-files (a posture gate, a bucket's lifecycle, paths, cycle numbering, staging, the DONE
signal, reporting) → the skill. This keeps the location honest when both files "say something about" a
finding — the skill's own text may point at a principle the prompt owns, but the pointer is not the
owner: a restatement that disagrees with its owner is a bug in the copy, not a defect in the layer
that only points to it.

Walk it:

- **Which layers say anything about this at all?** Read them. More than one may speak; then ask which
  one, changed alone, is sufficient — and if the answer is "none alone", say that, because a defect
  needing two layers changed is a different and worse finding than one needing one.
- **Is the text there wrong, or merely not followed?** A layer that says the right thing and was
  ignored is not the layer with the defect. Look for what made it ignorable — an instruction with no
  method, a rule stated where nobody reads, a contradiction elsewhere that outranked it. The gap is
  wherever the ignoring became possible.
- **Is this shared or local?** A defect in a layer other layers inherit from travels further than one
  in the skill. Say so when you find one — it changes what the fix is worth.

## When no layer's text would have prevented it

This is the case that matters most and reads as a dead end. If you have walked the stack and nothing
in it, changed, would have stopped this, the stack is **silent** here — and silence is why the defect
exists. That is not "no layer": it is a finding about an absence.

**Name where it should have been said, and say that nothing says it.** Both halves. "Nothing covers
this" leaves the reader to guess; "this belongs in the prompt" without saying the prompt is currently
silent reads as though the prompt got it wrong.

Do not resolve a silence by picking the nearest layer that is merely *related*. A layer that talks
about the neighbourhood is not a layer that would have prevented this, and tagging it sends the fix
somewhere that was not broken — the same failure as defaulting to the skill, wearing better clothes.

## Reporting

The location lands in the packet entry the finding drives: its `File:` is the layer, named from
the contract's list, and the quote you justified it against travels with the entry. A layer named
without a quote is a guess, and it will be executed as though it were not.

Locating is not yet fixing: settle where the defect lives before deciding what the replacement
says, or the file you happened to have open decides both.
