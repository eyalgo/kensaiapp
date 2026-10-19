---
version: "1.3.0"
---

# Comparison — what the skill chose to ask

**Not blind** — same footing as the version comparison, run at synthesis. Run when the skill
surfaces work to the owner **and** a prior version exists.

**A skill with no surfacing pattern has no surfaced set — but never infer that from the absence.**
A missing trail and an absent surfacing pattern look identical from here: both are no answered
set. The audit reads only the outputs, so the difference is a fact your brief must state — the
caller says whether this skill surfaces work. Brief says it surfaces and the trail is missing →
the skill dropped the owner's answers rather than never asking, `[blocking · skill-general]`.
Brief says no surfacing pattern → say so in one line and skip. Brief silent → report that the
pass cannot run soundly, and do not guess.

**Your question: did the fix change what the skill asks — and in which direction?**

**Why this is readable at all.** A kaizen round starts clean: same inputs, no inherited state, only
the skill version differs. So the questions are a **direct measurement of the skill** — if the
surfaced set moved, the skill moved. Nothing else could have moved it.

Compare this version's surfaced set against the prior version's, from the two snapshotted companion
files. Four buckets:

- **Appeared** — asked now, not before. Usually the good direction: a fix taught the skill to surface
  something it used to assert. Verify that read — check whether the prior artifact silently asserted
  it. If it did, this is a fix earning itself, and say so.
- **Vanished** — asked before, not now. **The dangerous direction, and why this pass exists.** Two
  causes look identical from the companion alone: the skill now answers it from the inputs (good), or
  it now silently defaults it (the worst defect in this class). You cannot tell them apart without
  looking. So for **every** vanished question: does this version's artifact assert it, and on what
  backing? Asserted with no owner answer and no source is the skill regressing from *surfacing* to
  *manufacturing* — `[blocking · skill-general · surfacing]`. This is the same event the
  unauthorized-delta check sees from the other side: **a value that changed without authorization is
  usually a question that stopped being asked.**
- **Persisted** — asked both rounds. Note it. A question the skill never learns to settle is a
  standing signal about its inputs or its reach.
- **Reshaped** — same question, asked differently. Better or worse: a choice that carried a drafted
  answer and a lean, now offered as a bare menu, is a regression the other three buckets miss.

**Churn is not a finding.** A better skill legitimately asks fewer or different questions. Never
score the size of the delta — adjudicate each **vanished** question individually against the
artifact. A pass reporting "the question set changed" has reported nothing.

Write this as a titled section beside the version comparison.
