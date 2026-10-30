# Flow Findings — development-content  (audited 2026-10-30)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · lens 10 (whole string, claims)]** The killed-tracker passage says "Type the same commands", but the passage directly before it is now the refusal line's code block, so "the same commands" has no antecedent in the sentence or the one before it. Where: `change_text.md` § The setup instructions, "A start after a tracker was killed". The commands sit in the section's opening paragraph; name them or point at the opening, for example by repeating that the start is `python3 main.py` from `products/tracker17`.
- **[non-blocking · change-local · lens 10 (whole string)]** The added empty-directory sentence repeats the conclusion of the sentence it follows ("there was no saved data to set aside" twice, back to back), and the existing sentence it follows still says "instead", which reads as the only alternative. Where: `change_text.md` § The setup instructions, "An empty saved-data directory set aside". The two sentences state one conclusion for two observations; the writing bar's no-restatement rule (`system/doctrine/writing_bar.md` § 1.2 rule 8) is the check, and a reword that names the second observation in the new sentence would stop the repeat.

## Checked, no finding

- Lexicon: no banned or rejected word in any inflection. "left" and "no" were scanned and are not the position or control-label senses (`CONTENT.md` § Terminology); "killed" is not rejected, and the step surfaced it as a terminology gap under "Findings for the Content Manager". No banned punctuation.
- The terminal line equals the `CONTENT.md` § Message patterns, Terminal messages example and `change_spec.md` CP-693 word for word.
- Places: the design's `Publishes text:` line names the terminal refusal and the README's setup instructions; the four blocks sit in those two places and no other. The third README block ("Setting saved data aside") goes beyond Sub-job C's named section, is recorded under Wording decisions with its reason (CP-703), and sits inside "the README's setup instructions".
- Claims: each is backed by the spec (CP-694, CP-699, CP-702, CP-703); the smaller claims are explained under Wording decisions. No identifier or file name in any string except the existing `mv` sentence's neighbours.
- CP-708's "another tracker" is present in the README passage.
