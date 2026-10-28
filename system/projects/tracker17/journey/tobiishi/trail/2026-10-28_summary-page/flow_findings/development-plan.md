# Flow Findings — development-plan  (audited 2026-10-28)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited `tl_instruction.md` against `change_spec.md` (CP-490–CP-512, Examples, Locked Answers) and `change_design.md` (§ 3 sub-jobs and atomic edges, § 5 T01–T17). Lenses 1–6 and 8 walked; lenses 7, 9 and 10 do not apply to this step.

- **[non-blocking · change-local · coverage]** Task 1 modifies `tests/architecture/test_shapes.py` (the positive landed-feature assertion and the retained exact saved-state field check, design T13) but names no behaviour for it. Its `#### Behaviours to verify` header and bullets cover only `test_summary.py` and `test_trace.py`; the shape change appears in "What to build" and nowhere a developer's red phase is told to prove. Where: `tl_instruction.md §Task 1`. The task's only pass criterion for it is the bare "all existing tests pass". Direction: name the shape-test change as a verified behaviour, so the released assertion cannot be swapped for a weaker one unnoticed.
- **[non-blocking · change-local · coverage]** CP-512's "status, priority and the overdue count are words and numerals" has no named assertion. The accessibility behaviours cover reflow, keyboard focus and target size, and the page-rows test covers numerals, but nothing asserts labels are words rather than colour or icon. Where: `tl_instruction.md §Task 3`. Direction: fold into the rows test.

Checked and clean:
- Classification: `feature` / `changing` copied verbatim from the spec and design.
- The four atomic-landing edges of the design each sit inside one task: module + shape/trace in Task 1, links/titles + compatibility assertions in Task 3, route + sample in Task 3, timed block + labels in Task 4.
- Every T01–T17 row maps to a named behaviour, and every Example maps to a design row that maps on.
- Divergences carry reasons in `## TL Review Notes`: the separate e2e gate, trace-follows-creation, the casefold-tie edge and the gate-runtime conditions.
- No downstream role is named and no decision a successor owns is made. The Hint lines repeat the design's Code Strategy.
