# Flow Findings — development-plan  (audited 2026-10-28)

Findings for this step's output only (`tl_instruction.md`), produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Cross-checked against `change_spec.md` (CP-546–CP-568, Examples E01–E28, Locked Answers) and `change_design.md` (§§ 1–5, T01–T16, Architect Review Notes). `docs/adr/`, `docs/nfdr.md`, `docs/fdr.md` present and cited by the plan; no finding raised for them.

- **[non-blocking · change-local · step-specific contract]** The verification gates pass on "no new failures in the full suite", but the baseline they measure against is a red one. Where: `tl_instruction.md §TL Review Notes` (Baseline and launch conditions) vs every task's `#### Verification gate`. The notes record the card's command ending `20 failed, 2222 passed, 31 errors` in one run and `51 passed` for `--lf` in a second, and say the failures come from socket binding and SIGINT handling. They never list which tests failed or say the full suite must be fully green once launch conditions hold. A developer who cannot meet those conditions cannot tell an inherited failure from a new one. Direction: state the pass condition for the full-suite gate as a property (green under the stated launch conditions, or the named inherited failures), not as a delta over an unrecorded baseline.

Lenses 1 (coverage), 2, 3 (Category `feature` / Behaviour `changing` copied verbatim from the spec and design), 4 (task cut, `ProjectNameRefusal` enum, added precedence and second-rename cases are each recorded in `## TL Review Notes` with a reason), 5 (CP-555 reuse is stated as held by review, not claimed through output equality), 8 (no downstream role named, no decision of another role made) and 7/9/10 (implementation-only and content-only lenses, not applicable to this step) found nothing further.
Coverage was walked row by row: every one of E01–E28 and CP-546–CP-568 maps to a Task behaviour or a Held-by-review line.
