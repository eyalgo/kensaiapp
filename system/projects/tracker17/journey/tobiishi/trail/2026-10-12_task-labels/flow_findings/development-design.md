# Flow Findings — development-design  (audited 2026-10-12)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 3, 5, 6, 8 (enacted / dropped), 9 and 10 raised nothing: header `Category: feature` / `Behaviour: changing` is copied verbatim from `change_spec.md`; order and uniqueness are by construction (tuples, `TaskLabelOutcome.changed`); atomic-landing edges are stated as properties; every spec Example and CP-182–CP-210 maps to a § 5 row (T1–T18). Lens 7 does not apply to a design.

- **[non-blocking · change-local · divergence-record]** The design adds save-failure behaviour the spec does not state, and records no reason for it. `label_failed=<add|remove>`, the failure focus-target row, "failed-action messages" and "console messages for failed label actions" in `Publishes text:`, and T6/T3 failure cases are all new. The spec's only mention of failure is CP-208's timed run. Where: `change_design.md §3 C` (redirect protocol, focus table), header `Publishes text:`, `§5 T3/T6`. The citation is NFDR QC-49/QC-56, but nothing in `## Architect Review Notes` says the spec was silent and this was added from the records. Direction: record it as a (b) decision with its reason. This also lets the content step know these strings are not spec-established (lens 10 downstream).
- **[non-blocking · change-local · divergence-record]** Remove focus target is narrowed to "Task heading" without a note. Spec CP-192 says only "the top of the sheet the thing was on, where the completion line sits". Where: `change_design.md §3 C` focus table, "Removed". The choice is plausible but is a decision with no entry in the review notes.
