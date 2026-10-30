# Flow Findings — development-design  (audited 2026-10-30)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 1, 2, 3, 5, 6 and 8 (dropped) found nothing: every one of the 13 spec Examples maps to a V-row in order, and every rule CP-736–CP-746 is covered by the rule pass. `Category: feature` and `Behaviour: changing` are copied verbatim from the spec. No altitude leak and no mechanism anchor appears. No code part is added, so the parts table is untouched. Lenses 7, 9 and 10 do not apply to this step.

- **[non-blocking · change-local · handed-down constraint]** The Architect Review Notes decide how the published text must be built: "Realize CP-742 through wording that identifies both running cases in the keep-running and stop instruction's scope. Do not rely on sentence proximity". V8 repeats it as "apply explicitly". Where: `change_design.md §Architect Review Notes (Explicit running-case scope (b))`, `§5 V8`. CP-742 requires only that the two sentences *read as* applying to the running lines. The design adds a wording-level construction that the content step owns. It is recorded with its reason, so lens 4 is satisfied. Direction: state the property (the reader cannot read the keep-running and Ctrl-C sentences as covering the refused start) and leave how to `change_text.md`.
- **[non-blocking · change-local · divergence record]** The design's section numbers run 1, 2, 4, 5 with no § 3, and no note says it is deliberately omitted. Where: `change_design.md` headings. Direction: if § 3 is conditional in the design template, a one-line "not applicable" would show it was considered. This is low-confidence and cosmetic.
