# Flow Findings — development-design  (audited 2026-10-10)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Checked against `change_spec.md` (CP-9..CP-18, Gaps 1–8) and the product's `ridge.py`. The design's reuse claims hold: `_BaseRidgeCV.__init__` stores the flag, `_BaseRidgeCV.fit` stores `cv_values_` or raises the `cv!=None` ValueError, and `RidgeClassifierCV.fit` always hands the base a `LabelBinarizer` 2-D target. Classification copied verbatim (bug / changing). Gap 7 (test location) is delegated by the spec and answered in Architect Review Notes with a reason. No ADR/NFDR/FDR/SDD exists (Definition: none), so those cross-checks and lens 9 are skipped.

- **[non-blocking · change-local · coverage]** The coverage map says `set_params` to `True` followed by a `cv` refusal is covered by the refusal row. It is not. The refusal row constructs with `store_cv_values=True, cv=2`, and nothing sets the flag through `set_params` before `fit`. Where: `change_design.md §5 Coverage map, Rule-implied edges`. The claim of coverage is stronger than the row. Either add the `set_params` path to the refusal row or drop the claim.
- **[non-blocking · change-local · step-specific contract]** The Code Strategy docstring row says "The words come from `change_text.md`", and the Architect Review Notes name "the Content Editor". The design is the earlier step and points at a successor's artifact. This states ownership and does not decide anything the role owns, so it is not an enactment. But it makes the design's completeness depend on a file that did not exist when it was written. Where: `change_design.md §4`. Direction: say only that the words are a later step's, fixed by CP-16's tokens.

Lenses 2, 3, 5, 8 and 10: Clean. Lens 4: Clean. The one design-level decision, test placement, is recorded with its reason.
