# Flow Findings — development-design  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Read against: `change_spec.md`; no `docs/` (adr / nfdr / fdr) exists for the product, so that cross-check column is skipped. The design's claims about `visit_literal` (early returns before the highlighted branch; `rstrip()[:-14]` leaves exactly one trailing line end; no in-tree override) were checked against the product source at base and hold. Classification (`bug` / `changing`) is copied verbatim from the spec.

- **[non-blocking · change-local · coverage]** The rule-implied edge that justifies the trailer strategy, highlighted code ending in its own trailing whitespace (`x = 1 `), has no test row. Where: `change_design.md §4 Code Strategy` (names the edge and the probe) versus `§5 Test Additions` (no row asserts it). The design picks "insert `%` before the single last line end, never strip a second time" because a second strip would eat that whitespace and break CP-11's byte-identity. Nothing in the proposed tests would fail if the implementation did strip a second time, because every probed input ends in a non-space. Direction: a row asserting the exact form for code with trailing spaces, so the stated contract is held by a case that could fail.

Lenses 2, 3, 4, 5, 6 and 8: clean. Lenses 7, 9 and 10 do not apply to `development-design`.
