# Flow Findings — development-plan  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited: `tl_instruction.md` against `change_design.md`, `change_spec.md`. No `docs/` exists (`Definition: none`), so the ADR/NFDR/FDR cross-check was skipped, with no finding raised for it.

- **[non-blocking · change-local · divergence-record / contract-realized]** Two of Task 1's seven behaviours cannot go red on the unchanged tree, yet the instruction says "All of these fail on the unchanged tree (CP-13). Run them red first." `test_clear_empties_records_tuples_messages_text` asserts only `records`, `record_tuples`, `messages` and `text` straight after a clear. The spec's Examples (CP-12 rows) and Verified Claims show those values are identical at base. `test_clear_leaves_not_started_phase_empty` asserts `get_records("teardown") == []` during call, which the spec shows as `[]` today (CP-11 row). Where: `tl_instruction.md` Task 1 § Behaviours to verify, last paragraph. Design row 2 was one test that did go red through its `get_records == records` checks. The TL's split into separate tests removed that red from these two, and the split is not in `## TL Review Notes`. Direction: record the split with its reason, and say which Task 1 tests are guards that pass at base. The developer will otherwise see an unexplained green at the red phase. (code-integrity's commit already reports this same mismatch.)
- **[non-blocking · change-local · coverage]** `caplog.messages` and `caplog.record_tuples` are asserted only in the several-clears test and the two-clear sequence, not at the clear in an empty phase. Where: `tl_instruction.md` Task 1 behaviours 2 and 4. Detail: this follows the design and is low-risk, so it is recorded only. No action needed.

Lenses 2, 3, 6, 8, 9, 10: clean. Category and Behaviour were copied verbatim (`bug` / `changing`). The design hint was carried. The Gap 3 constraint is stated as "held by review", and no test is prescribed for it. Lens 7 (implementation-only) and lens 9 do not apply here.
