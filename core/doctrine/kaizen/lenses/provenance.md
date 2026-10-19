---
version: "1.0.0"
---

# Lens — provenance

**Your question: is this document describing the thing it is about, or describing itself?**

A document is read by an agent that has loaded it in order to act. Every sentence addressed to the
person who *built* the document is spent on a reader who cannot use it — and worse, it is a claim
about a state, so it is true on the day it is written and silently false afterwards. Nothing brings
the writer back.

`<CORE>/doctrine/governance/written_forward.md` owns the rule. This lens is how a round finds it.

Walk the document for each of these:

- **Does it describe its own state?** `stub`, `shape only`, `provisional`, `placeholder`,
  `TBD until`, `first pass`. A file announcing its own maturity to a reader who was going to use it
  either way.
- **Does it say how it was made?** Which template stamped it, which step of which procedure produced
  it, which sibling it was modelled on, who authored it, when. That is the builder's record, and the
  builder has git.
- **Does it carry a build-state claim?** `not yet built`, `not yet wired`, `planned later`,
  `once X ships`. Check whether the thing is in fact unbuilt — the usual finding is that it shipped
  and the sentence stayed. Report the claim even when it is currently true: nothing keeps it honest.
- **Is a rationale told as a story?** `originally…`, `we used to…`, `this was changed because…`,
  `we considered X and decided against it`. The information is usually worth keeping; the form is
  not. Report it with the constraint it should have been: "Do not do X — X does Y."
- **Is a date, a SHA, or a version doing work in the prose?** Inside a live document these are
  almost always the residue of an edit. In a record — a seed, a station, an audit — they are the
  point. Know which one you are reading.
- **Does it hedge about a sibling's readiness?** *The X document does not exist yet*, *until Y is
  written*. That fact has an owner; a second copy of it here is a copy with a clock on it.

**The keep test, applied clause by clause: does this change what the reader does this session?**
An instruction survives even when it concerns something absent — *"do not reach for a capability
that isn't there"* is an instruction. The status note wrapped around it is not.

**What is not a finding here.** Present-tense argument for the document's own rules, however long.
Past-tense evidence describing **the system's** defects rather than this file's biography. And the
journey — a seed's findings, a station's attempts, a trail entry — where recording what happened is
the artifact's whole job.

**The sharp case is the true one.** A build-state claim that is accurate today reads as simply
correct, and every instinct says leave it. It is the finding: correctness now is exactly the
property that will not survive, and the document has no way to notice when it stops holding.
