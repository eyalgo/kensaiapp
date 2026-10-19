# skill-evals-creator — Design Decisions

## 2026-06-04 — Mode 1 dropped from eval set

**Decision:** eval coverage for Mode 1 (TDD — create evals from intent, no SKILL.md) is dropped from the current iteration. Focus is entirely on Mode 2 (from existing SKILL.md).

**Why:** the use cases that discriminate well are all Mode 2: the skill reads the source-of-truth SKILL.md and identifies/fixes problems in existing evals. Mode 1 evals that don't rely on transcript assertions have not proven discriminating; if needed, Mode 1 can be added later as a separate effort.

---

## 2026-06-04 — Simplify evals: output quality over process compliance

**Decision:** evals for this skill should grade the *output evals.json* only — not the transcript, not step labels, not process structure.

**What we were doing:** assertions checked whether the transcript contained step labels ("Step 1", "Step 2"...), whether gap analysis appeared before case design, whether SKILL.md was read first. All process-compliance checks.

**Why it doesn't work:** a capable baseline improvises the same process. Iter-13 confirmed it — `uses_skill_step_labels` passed on both arms; `assertions_reference_dummy_skill_patterns` passed on both arms. The baseline reads SKILL.md and structures its work in numbered steps naturally. Process compliance is not discriminating.

**What discriminates:** the *quality of the produced evals.json*. Does it have concrete assertions with examples? Are nuanced assertions justified? Are cardinality guards present? These are skills the baseline doesn't apply consistently without the skill's explicit guidance.

**New rule:** no transcript-based assertions. All assertions grade the output file directly.
