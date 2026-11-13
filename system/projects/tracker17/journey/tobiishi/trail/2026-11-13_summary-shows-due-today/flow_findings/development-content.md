# Flow Findings — development-content  (audited 2026-11-13)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited: `change_text.md` against `change_spec.md` (CP-809 to CP-813), `change_design.md` (`Publishes text:` line), `tl_instruction.md`, `products/tracker17/docs/CONTENT.md` (§ Terminology, § Banned in anything a person sees, § Grammar and mechanics, § Localization, § Accessibility of text), `system/doctrine/writing_bar.md`, and the product's existing summary labels in `products/tracker17/web/pages.py`.

Lens 10 result: the design's `Publishes text:` line names one place, the new row's label in the Summary's "Due dates" group, and `change_text.md` has one block for it and no other. The one string, `Due on {date}`, contains no word from CONTENT's banned lexicon or rejected names, and none of the relative date words ("today", "yesterday", "tomorrow", "now", "ago", "recently"). It is whole, names no identifier or file, and claims no cause or guarantee beyond what CP-809 and CP-811 establish. `writing_bar.md` binds this instance's own documents and states no wording rule for a product's strings (§ 1.5), so nothing there applies. Lenses 1, 2, 3, 4 and 5 find nothing in this artifact.

- **[non-blocking · change-local · divergence record]** The text's whole-string form (`Due on {date}`) is recorded with its reason, but the plan still describes the label as "the words from `change_text.md` followed by `summary.today`". Where: `tl_instruction.md` task on `summary_page`, "What to build"; `change_text.md` § Wording decisions, first bullet. The design asked for "the words before its date", and the content step chose one string with a placeholder, citing CONTENT § Localization. That choice is sound and recorded. The plan was written earlier and still assumes fragment plus date, so the Developer, bound to place the text verbatim, will have to reconcile the two shapes. Direction: the Developer reads the text block as the one string and formats `{date}` into it. No re-run of the step is needed.

_No other findings._
