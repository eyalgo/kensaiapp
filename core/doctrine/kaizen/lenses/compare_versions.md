---
version: "1.2.0"
---

# Comparison — what the artifact says

**Not blind, and never handed to a lens auditor** — you need both versions, so you cannot fresh-read
either. Run at synthesis, after the blind fan-out. If there is no prior evidence version, say so in
one line and skip: there is nothing to compare.

**Your question: did the version bump earn itself?**

You are given this version's artifact, the prior version's artifact and its `audit.md`, **this
version's answered companion** — the owner's in-loop answers — and the round-shape flags (a re-run
vs a delete-and-recreate, any mid-round version change). Report three lists:

- **Closed** — prior findings this version fixed. Say how you verified it, not that the text moved.
- **Persisted / escalated** — prior findings still here, or now generalized to a broader root.
- **Newly emerged** — findings absent last round. Flag especially a **regression a fix introduced**:
  a narrow fix that opened a new failure shape. That is the most valuable thing you can find, and
  the round that produced it will not be looking for it.

## The unauthorized-delta check

Beyond the three lists, one more question: **did anything change that nobody authorized?**

A round is **stable by default** — but the baseline is *the settled content the producer actually
read this run*, not the prior artifact you hold for comparison. On a **re-run**, the producer read
the prior artifact at intake, so it *is* the baseline: the new version reproduces it exactly except
where something authorized a change. On a **delete-and-recreate** (per the round-shape flag), the
producer authored fresh from the base inputs and never read the prior artifact — so the baseline is
its own answered companion plus any upstream document it read, and the prior artifact is not. A
value present in the prior artifact but in *none* of the producer's actual inputs was outside its
reach, and its absence is not a delta it could have authorized. (Absent a round-shape flag, assume a
re-run and hold the stricter baseline.) So walk **every** substantive delta against the baseline the
producer actually read, and place it in one bucket.

Two moves per delta:

**Does it carry a why?** A producer that changes settled content and records no reason has made a
silent change. Where the artifact carries its own provenance — an inline trace, a review-notes
section, whatever the skill's convention is — a delta with no entry is silent by definition.

**Is the why legitimate?** A recorded why is not automatically a valid one: the producer wrote both
the change and its note. A legitimate why is **owner-driven or source-driven** — an owner answer, a
confirmed choice, a trace to an upstream document, or, for a genuinely new element, a derivation
the producer's role is entitled to make. A why of the shape *"re-derived / re-measured / reads
better now"* on content that was **already settled** is the producer authorizing itself. That should
have been surfaced as a choice to confirm, not edited.

**Verify the why against the inputs, never the artifact's own say-so.** A claimed owner answer is
checked against the answered companion; a claimed upstream trace against the upstream document.

**Report the residue**: `delta(baseline → this)` minus `legitimately-authorized`, where `baseline`
is the content the producer actually read (above). **Any non-empty residue is `[blocking ·
skill-general · stability]`.**

**A value the producer couldn't carry is not lost here — it is a question that stopped being asked.**
When a delete-and-recreate drops something an earlier round had settled — an owner-confirmed fact that
lives only in the prior artifact, not in any of this run's inputs — that is not a stability delta and
does not belong in the residue: the producer had no input basis to carry it, and firing a blocker it
could not have prevented is the freshness error this check most often makes. Hand it to
`compare_surfaced_set` instead: did the producer stop *surfacing* the question whose answer it can no
longer see? That is the real defect, and that lens owns it.

**Judge on authorization, not correctness.** A silently-changed value is blocking **even when the new
value is more right than the old one** — the fault is the silence, not the number. This is the rule
most often got wrong, because the wrong question ("is the new value correct?") has an answer and it
feels like diligence.

**If the answered companion is missing, say so and treat every claimed owner-answer why as
unverified.** An unverifiable authorization record is not authorization. It is snapshotted with the
artifact because the trail holding it lives in the case, and step 6 deletes the case.

Write this as a titled section of the audit output, with the residue check as a named subsection.
