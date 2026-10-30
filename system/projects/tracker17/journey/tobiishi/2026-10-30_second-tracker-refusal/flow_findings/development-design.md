# Flow Findings — development-design  (audited 2026-10-30)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · coverage]** A location absent together with its parent directories is not addressed. CP-695 says a location is in use before the first save, and the existing save creates missing parents, but the design names only "an initially absent leaf" (T6, T13) and "directory creation" failures as CP-702's quiet path. Where: `change_design.md §3 Sub-job A, §5 T6/T13`. Whether a nested absent location is claimed, refused on a second start, or left to today's path is undecided, and no test row covers it. Direction: state the outcome for a missing-parent location and add it to the rows.

Lenses 1–8 otherwise held:
- Every CP-693–CP-709 rule and every Examples row maps to a T-row (rule pass at the end of §5).
- Category and Behaviour are copied verbatim from the spec.
- Mechanism decisions (directory descriptor, `mark_started`, quiet indeterminate path) are recorded with reasons in Architect Review Notes.
- The contracts (one claimer, alias equality, no stale-descriptor claim) are realized by construction.
- The build sequence is stated as dependency, and no plan decision is enacted.

Lenses 9 and 10 do not apply to this step.
