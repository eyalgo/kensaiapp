# Flow Findings — development-design  (audited 2026-10-10)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited: `change_design.md` against `change_spec.md`. No `docs/adr/`, `nfdr.md` or `fdr.md` exists (Definition: none), so that cross-check was skipped, as the skill allows.

Lenses 1 (coverage), 3 (classification: `bug` / `changing` copied verbatim), 4 (divergence: the test location, the empty-sequence edge, the Function 1/2 split and `Publishes text: no` each carry a reason), 5 (padding with `S.Zero` is by construction, and the read-once rule is stated with its reason) and 6 held. I also re-ran two of the design's claims on the unchanged tree: `Point(2,0).distance(())` returns `0`, and `tuple(Line(...))` raises `TypeError`. Both match.

- **[non-blocking · change-local · step-specific contract]** The Blast Radius row for `line.py`, `line3d.py`, `polygon.py`, `ellipse.py` and `plane.py` says they "call … on points of one dimension", so "none of their results moves". That is not true for every caller. `Ray.distance(o)` (`line.py` 1445) and `Segment.distance(o)` (`line.py` 1770–1774, `line3d.py` 1433–1437) pass a caller-supplied `o`, which may have a different length from the segment's points. Their result for a different-length `o` moves under the fix. Where: `change_design.md §2 Blast Radius`. This is the intended effect of CP-9 and not a regression, but the row asserts an unchanged result without having checked the pass-through callers. Direction: state that the pass-through callers take the fix for a different-length argument.
- **[non-blocking · change-local · handed-down constraint]** §5 fixes the test shape: "two new test functions" and the split between them. The design owns which cases are tested and why Function 1 must fail on base. Function boundaries are the Developer's to choose. The property to hand down is that the CP-13 fix cases fail at base and the pin cases pass at base. Where: `change_design.md §5 Test Additions`. Direction: state the property and drop the function count.

No blocking findings. No `skill-general` findings.
