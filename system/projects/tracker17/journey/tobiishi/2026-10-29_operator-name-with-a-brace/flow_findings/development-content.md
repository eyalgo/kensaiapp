# Flow Findings — development-content  (audited 2026-10-29)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · words the product can keep]** A saved name that is itself `{value}` reads exactly like the slot `products/tracker17/docs/CONTENT.md` § Voice, "Limits the product holds" bans, and the standard does not say whether a typed value is exempt. Where: `change_text.md §Findings for the Content Manager`. The step recorded the gap and kept the name exactly as typed, per `CONTENT.md` § Voice and § Grammar and mechanics, "Quotes"; that is a correct reading and not a defect in the step. The open question belongs to the Content Manager, so no string here is blocked on it.

Checks that found nothing (lens 10 and the others that bear on this step):

- **Places:** the design's `Publishes text:` line names the saved, failed and refusal messages in Your name on the People page, and `change_text.md` has four blocks (saved, failed, blank refusal, too-long refusal) and no block for any other place. The no-name line is left out, as the line requires.
- **Banned lexicon:** none of `CONTENT.md`'s "Banned in anything a person sees" words appears in any of the four strings, in any inflection. `failed` and `refused` appear only in the document's own headings, which a person never sees. `system/doctrine/writing_bar.md` binds this instance's own prose and states no word ban for a product string.
- **Whole strings:** each string is a full sentence with one variable part, `{name}`, and the quotes around it belong to the string (`CONTENT.md` § Localization). None names an identifier or a file.
- **Claims:** "nothing was changed" and "What you typed is still in the form" are the failure formula's own parts (`CONTENT.md` § Message patterns, Error, "A failure that is not a refusal") and are what `change_spec.md` CP-620 states. No cause is named.
- **Existing strings:** all four match the product's current text in `products/tracker17/web/pages.py` `_operator_line`. The 200 is `SHORT_TEXT_MAX == 200`, asserted in `tests/unit/test_projects.py`.
- **Altitude and divergence:** the description of `{name}` states the requirement (CP-619, CP-621) and names no mechanism. The unchanged wording is recorded under `## Wording decisions` with its reason (CP-624 and the design's Architect Review Notes).
