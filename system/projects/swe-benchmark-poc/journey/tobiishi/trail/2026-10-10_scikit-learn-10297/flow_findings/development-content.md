# Flow Findings — development-content  (audited 2026-10-10)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Checked: `change_text.md` against `change_spec.md` (CP-11, CP-12, CP-15, CP-16, Out of Scope),
`change_design.md` (`Publishes text:` line, § 5 docstring row), the product's `ridge.py` docstrings,
the instance's banned words (`system/experience/voice_restrictions.md`) and `writing_bar.md`. The
product has no `CONTENT.md`, so lens 10 ran against the writing bar and the banned-word list alone.
Banned-word hits: none. Both blocks name a place the `Publishes text:` line names, and each place has
a block. Each string is a whole entry and the longest line is 71 columns. The header Category and
Behaviour match the spec and design (`bug`, `changing`).

- **[non-blocking · change-local · coverage/claims]** The `cv_values_` entry states that, with
  `scoring=None`, the stored values are "the squared Leave-One-Out errors". Neither "squared" nor
  "Leave-One-Out" appears in the spec. CP-12 fixes only that the values are the errors `alpha_` is
  chosen by. Where: `change_text.md §Text, cv_values_ block`; `change_spec.md` CP-12. The grounding
  is the content step's own reading of the product's error function (`§Wording decisions`), not a
  spec claim run and verified, and the Developer places the sentence verbatim. Direction: the spec
  owner confirms or narrows the sentence before it is placed.
- **[non-blocking · change-local · divergence record]** The text goes beyond the spec's Out of Scope
  line ("the docstring's wording about them is not corrected beyond CP-16") by describing the values
  and dropping the `{loss,score}_func` clause. It is recorded with its reason under `§Wording
  decisions`, so it is not silent. Where: `change_text.md §Wording decisions`. Recorded only because
  the divergence is load-bearing and sits in this step's own notes, not in the spec's Locked Answers,
  so the spec's owner has no entry to see.
- **[non-blocking · skill-general · step-specific contract]** No standard covers text written into a
  third-party repository: the product has no `CONTENT.md`, and the writing bar and voice fence do not
  reach it. The step raised this itself under `§Findings for the Content Manager`. Where:
  `change_text.md §Findings for the Content Manager`. Raised here as a kaizen candidate. → kaizen
  `third-party-repo-text-standard`.
- **[non-blocking · change-local · divergence record]** The AI-use disclosure question is left open
  and unrouted ("Eyal confirms it"). It needs no action while the patch stays local. Where:
  `change_text.md §Wording decisions`. Noted so it is not lost if the patch is ever pushed.

No `blocking` finding.
