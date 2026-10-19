# Flow Findings — development-specs  (audited 2026-10-10)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 3 (classification copied verbatim: bug / changing), 4 (Gaps 1–6 each carry a reason; no silent resolution found), 5, 6 and 8 (test placement and data handling are left to development-design, as properties) found nothing. Lens 7: `## Verified Claims` is present, and every verdict claim names a run, its tree, its interpreter and what came back. Fixture counts (59 invalid, 73 valid) and the `TEST_DATA` baseline values were re-checked against the product and match. `docs/fdr.md` is absent (Definition: none), which is not a finding.

- **[non-blocking · change-local · altitude]** CP-5 anchors a rule to a mechanism and a source line: "out of the `urlsplit` call at `django/core/validators.py` line 136". Where: `change_spec.md §Rules CP-5`. The rule is output-observable on its own (a rejection is `ValidationError`, code `invalid`, never `ValueError`), and the `ValueError` is already in the Examples row and Verified Claims. The call and line anchor belongs in Verified Claims only. Direction: strip it from the rule text.
- **[non-blocking · change-local · coverage]** CP-4 states that "#" is rejected in the username and password through CP-1, but the Examples carry a "?" row inside the password (`http://user:pa?ss@example.com`) and no matching "#" row. Where: `change_spec.md §Examples`, CP-4/CP-1. A rule-implied case (`http://user:pa#ss@example.com`, rejected on host `user`) has no row, so downstream coverage can drop it. Direction: add the row.
