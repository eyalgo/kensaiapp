# Flow Findings — development-design  (audited 2026-10-29)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 7, 9 and 10 do not apply to `development-design`. Lens 1: CP-668–CP-684 each map to a check V1–V14, and the rule-implied paths (Linux, misplaced environment, new terminal, non-Git copy, forbidden substrings) are named. Lens 3: Category `nfdr` and Behaviour `changing` match the spec. Lens 4: the no-count choice for CP-678 and the extra QC-40 review are recorded in Architect Review Notes with reasons. Lens 8: the design states properties and prescribes no downstream role's decision. Spot-checked citations (nfdr RN-33, QC-12, QC-40; the SDD parts table; the README-heading tests) match the files.

- **[non-blocking · change-local · coverage]** The § 5 lead-in says "V1–V13 cover every Example", but the CP-684 Example is covered only by V14. The section numbering also jumps from § 2 to § 4. Where: `change_design.md §5 Test Additions` and section headings. A reader following the lead-in literally would count one Example uncovered. The coverage itself is complete. Direction: a wording slip, no downstream effect.

Otherwise clean — no further flow-issues found.
