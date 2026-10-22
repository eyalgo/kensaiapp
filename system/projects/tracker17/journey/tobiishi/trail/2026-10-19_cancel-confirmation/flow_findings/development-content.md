# Flow Findings — development-content  (audited 2026-10-20)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Checked: every string against `CONTENT.md` (banned lexicon, rejected terms, punctuation, contractions, sentence counts, Needs confirming / Completed / Error patterns); the design's `Publishes text:` places against the blocks (all present, none extra); the reused strings against `web/pages.py` and `web/routes.py` (identical); lens 10's whole-string and no-identifier checks (clean). The writing bar adds no ban this text hits.

- **[non-blocking · change-local · divergence-record / claim beyond spec]** The refusal "…doesn't allow the move you pressed…" is also shown on a reload or a return to the confirmation's page after the move was saved, where no press happens in that request. The text keeps it and says so only under its own "Findings for the Content Manager". Where: `change_text.md §Text (Refused blocks), §Findings for the Content Manager`. `change_spec.md` CP-331 establishes the page and the refusal, not that the person pressed anything. The reader can be told they pressed a move beside a status showing it took effect. The finding lives only in this file; `deferred_decisions.md` has no entry for it, so it may not reach `shukuba-refine`. Direction: record it as a deferred decision, or give that state its own string once CONTENT.md states a rule for it.
