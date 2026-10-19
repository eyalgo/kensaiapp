# Flow Findings — development-specs  (audited 2026-10-10)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · evidence]** CP-12's tie rule ("on a tie, the first such entry in `alphas`") has no run behind it. Verified Claims shows `alpha_ == argmin` only on cases the probe produced, none constructed to tie. Likewise CP-11 states "With `scoring` set, the shape is the same" for every `y`, but the only run was `scoring='neg_mean_squared_error'` on one case (`(40, 1, 5)`). Where: `change_spec.md §Rules CP-11, CP-12; §Verified Claims`. Each claim is about what the command decides, so it should be run, not inferred from the argmin. Direction: add a tie case and a scored multiclass or multilabel case to the probe, or narrow the rules to what was run.
- **[non-blocking · change-local · altitude]** CP-16 puts product source anchors into a rule: `sklearn/linear_model/ridge.py` lines 1306–1309 and line 1335. Those lines were checked and are right today, but they are positions in a file the change edits, so they go stale. The behaviour the rule states (docstring lists the parameter and the three-dimensional shape) needs none. Where: `change_spec.md §Rules CP-16`. Direction: keep the line numbers in Verified Claims, where the read is recorded, and leave the rule to say what the docstring must state.

Lenses with no finding:
- Coverage: every rule maps to an Examples row, including the one-class `y`, the string labels, the single-column `y` and the positional call. The rule-implied edges are present.
- Classification propagation: `bug` / `changing` were copied from the request, and Gap 8 records why they were kept. The request invited reclassification for a capability request, and the issue's second half reads that way. The pair is in vocabulary and the divergence has a reason.
- Divergence record: Gaps 1–8 carry reasons. The decision that `cv_values_` is always three-dimensional (Gap 1) is recorded. It departs from what `_RidgeGCV` does for one target today (line 1079, two-dimensional), and the entry says so.
- Altitude of the rationale: the Locked Answers mention no storage anchor or mechanism beyond the product's public surface.
- Handed-down constraint (lens 8): Gap 7 and CP-17 state the property "tests the card's `Test command:` runs" and leave placement to development-design. No downstream role is named or enacted.
- Evidence (lens 7): `## Verified Claims` is present, and the claims about what each command decides carry the command, the tree and the interpreter. The post-change probe is a scratch subclass, which the spec says plainly it is.
- Cross-checks: `docs/fdr.md` is absent (`Definition: none`), which is not a finding. The request and the public surface were used.
