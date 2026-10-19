# skill-evals-creator — Ratification

**Ratified:** 2026-06-05
**Branch:** `skill/proposal-interview`
**Ratification commit:** `0befe23` (iter-18 results)

---

## Result

| Metric | Value |
|---|---|
| With skill | 89.6% |
| Without skill | 39.6% |
| Delta | **+0.50** |
| Gate | +0.20 |
| Status | **RATIFIED** |

Best delta in skill history across 18 iterations (previous record: iter-5 at +0.39).

---

## What the skill demonstrably adds

Three behaviors that baselines don't produce without the skill:

**1. Concrete phrasing examples on nuanced assertions** (`wins_assertion_is_concrete` — eval 1, +0.50 delta)

The skill teaches that assertions checking semantic content must anchor the equivalence boundary with at least one concrete example of an acceptable phrasing — e.g., "e.g., 'Hit 1,000 active users milestone' would pass; an empty bullet or N/A would fail." Without the skill, agents write the rule but omit the example, leaving graders guessing. With the skill, the example is present.

**2. Proactive nuanced→structural tier conversion** (`nuanced_converted_to_structural` — eval 6, +0.50 delta)

The skill teaches that existing nuanced assertions must be reviewed for structural convertibility. When an assertion checks a specific named condition (e.g., "+8% price target"), the tier should be converted to structural. Without the skill, agents leave existing nuanced assertions as-is. With the skill, the exit_judgment_sound assertion was converted to `price_target_condition_named` (structural).

**3. Nuanced justification naming the structural attempt** (`nuanced_justification_explains_structural_attempt` — eval 7, +1.00 delta)

The skill teaches that when an assertion must stay nuanced, its justification must explain what structural approach was tried and why it falls short — not just "requires judgment." Without the skill, agents produce no output file at all for this task, or write bare justifications. With the skill, the justification names the specific structural approach ("pattern presence checks for metric names") and provides a concrete failure example.

---

## Open gap

**Eval 5 (`catch-bug-vacuous-assertion`) — 0-delta across all 18 iterations.**

The target behavior: when a VALID-case assertion is vacuous (absence-only), replace it with a positive check that references domain indicators (RSI, SMA, 52w). Both arms consistently produce companions that check verdict-level phrases ("Meets minimum standards") rather than indicator terms. The assertion as written requires RSI/SMA/52w in the companion description — a harder bar than what either arm achieves.

This gap was not a blocker for ratification given the +0.50 overall delta. If eval 5 ever needs to discriminate, the discriminating surface is more likely "does the companion check that the output mentions the specific indicator from the input thesis" — a reformulation of the assertion, not a skill change.

---

## Eval set at ratification

4 evals, all Mode 2:

| Eval | Dummy skill | Key discriminating assertion |
|---|---|---|
| `mode-2-update-existing-evals` | `dummy-skill-with-evals` (standup formatter) | `wins_assertion_is_concrete` (nuanced) |
| `catch-bug-vacuous-assertion` | `dummy-trade-thesis-validator` | `vacuous_assertion_replaced_with_positive_check` (structural — 0-delta, open gap) |
| `nuanced-justification-explains-structural` | `dummy-copytrader-suitability-reviewer` | `nuanced_justification_explains_structural_attempt` (nuanced) |
| `proactive-structural-conversion` | `dummy-trade-exit-reviewer` | `nuanced_converted_to_structural` (structural) |
