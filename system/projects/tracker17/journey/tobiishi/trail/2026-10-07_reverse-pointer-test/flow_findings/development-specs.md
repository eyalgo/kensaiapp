# Flow Findings — development-specs  (audited 2026-10-07)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Clean — no flow-issues found.

Checked, all lenses 1-8 (9 and 10 do not apply to this step):
- Coverage: CP-47..CP-50 (unlisted word with module, several words, non-entry modules, word with no module) map to Examples rows; CP-51 carries the can-fail proof; CP-53 keeps the seven existing tests.
- Altitude: the rules name the landed list and the test file only as NFDR QC-11's tail places them; how the test gets the words is left to design (CP-48).
- Classification: `nfdr` / `changing` is in vocabulary.
- Divergence: Gaps 1-5 in Locked Answers each carry a reason (CP-49 no-module-not-flagged, CP-51 tree left unchanged).
- Verified Claims is present. Each command-verdict claim names the command, the tree (`57b86b647`) and the result: 209 passed, and 7 passed on the scratch copy with an unlisted `domain/tasks.py`. The line citations were re-checked at that commit: `test_trace.py:L19`, `L87-L89`, seven `def test_`, and SDD L441-L453 (eleven words). `nfdr.md` QC-11 matches the spec's account.
- Nothing is handed down as an enacted constraint, and no input property is dropped.
