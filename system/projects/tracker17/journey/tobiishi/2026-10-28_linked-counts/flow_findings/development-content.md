# Flow Findings — development-content  (audited 2026-10-28)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Clean — no flow-issues found.

Checked against `change_spec.md` (CP-513, CP-515, CP-521, CP-522), `change_design.md` (`Publishes text:` line), `products/tracker17/docs/CONTENT.md` and `system/doctrine/writing_bar.md`:

- **Places (lens 10).** The design's `Publishes text:` names one place, the accessible names of the nine linked counts. `change_text.md` has one block for it, covering all nine counts in a one-count form and an any-other-count form (eighteen strings). No block names a place the line does not.
- **Banned words (lens 10).** No string uses a word from `CONTENT.md`'s banned lexicon or rejected terminology, in any inflection. Status and priority words stay lowercase and hyphenated as § Terminology defines them. The writing bar has no word ban that reaches these strings.
- **Whole strings (lens 10).** Each string is written out whole, and `{count}` holds one number. No identifier or file name appears in a string. None ends with punctuation.
- **Claims (lens 10).** No string claims a cause, state or guarantee the spec does not establish. "Open tasks" is rejected on the grounds that the count includes `done` and `cancelled` tasks.
- **Coverage and distinctness.** The two names `CONTENT.md` fixes ("12 tasks in todo", "3 overdue tasks") are reproduced as the pattern. Zero shares the plural form, per the Numbers and Plurals rules, and the wording decisions record why. CP-522 distinctness holds across the nine and against the header and view links.
- **Divergence record (lens 4).** The priority wording and the zero form are not in `CONTENT.md`. They are recorded under `## Wording decisions` with reasons, and the "Findings for the Content Manager" section is "None" with the reasoning given.
- **Classification (lens 3).** `Category: feature` and `Behaviour: changing` match the spec header verbatim.
