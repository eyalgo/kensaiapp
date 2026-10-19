# Flow Findings — development-specs  (audited 2026-10-12)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 1–8 walked against `change_spec.md` and `change_request.md`. Spot-checked at `5148e0366`: both SHAs exist and `5148e0366` is an ancestor of the change tip; `test_first_project.py:166`/`:177` and `test_people.py:157` are the focus assertions Claim 2 names; 27 `def test_` under `tests/e2e/`; `Category`/`Behaviour` (`nfdr` / `preserving`) match the request verbatim; every request clause (cause named in commit, no retry, no deletion/loosening, no new e2e tests, diagnosis and fix as one change, 20-run proof) maps to I-3..I-7. Lenses 9 and 10 do not apply to this step.

- **[non-blocking · change-local · evidence-that-could-have-failed]** I-1's collection claim ("collects everything under `tests/` except `tests/e2e/`") rests on reading `tests/conftest.py:L7-L9`, and Claim 9 confirms it by comparing counts (813 vs 27) rather than a run that could show an overlap. Where: `change_spec.md §Verified Claims`, row 9. A claim about what a command *collects* was derived from reading its configuration; a `pytest --collect-only` on the `tests/` path, run in the row-1 copy, would have been the run that could fail. Direction: record the collect-only result, or state the claim as read.
- **[non-blocking · change-local · evidence-that-could-have-failed]** The only run evidence that the suite varies is one failing run in eight (Claim 2); I-3's 20 consecutive passes is the proof that the variation is gone. Where: `change_spec.md §Verified Claims` row 2, `§Invariants` I-3. At the observed rate, 20 passes can still happen with the cause present, so I-3 alone is weak evidence. The 20 is the station's own number, so the spec was right to carry it; I-7 (cause named) is what keeps the proof from standing alone. No change needed unless the design leaves the cause unnamed.

No blocking findings. No altitude, classification-propagation, divergence-record or handed-down-constraint findings.
