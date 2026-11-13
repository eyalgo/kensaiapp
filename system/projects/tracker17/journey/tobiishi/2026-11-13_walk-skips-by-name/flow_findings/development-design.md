# Flow Findings — development-design  (audited 2026-11-13)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 1–6 and 8 walked against `change_design.md`, read beside `change_spec.md`. Lens 7 (specs and
implementation only), 9 (implementation only) and 10 (content only) do not apply to this step.

- **[non-blocking · change-local · coverage]** The near-name row asks for a root "with no `tests/`", but § 4 hint 1 says CP-788's one builder is shared by the three cases, and CP-788's root holds `tests/x.py`. Where: `change_design.md §5` (near-names row) against `§4` (hint 1, hint 4). Hint 4 plants `Tests/` where no `tests/` exists, while hint 1 builds one root for every case. The builder has to take that difference. This is not a missing case, and the Developer can follow either hint. Direction: state which root each row uses.

Checked and found clean:
- Coverage: CP-785 to CP-795 each map to a § 5 row, a gate command or a review note. The rule-implied edges (a root file `.x.py`, a nested dot-folder, a skipped name below the root, near names, `__pycache__` at the root and nested) have rows.
- Altitude: the design holds the mechanism, not the spec. The spec states no storage anchor.
- Classification: `nfdr` / `changing` match the spec header verbatim.
- Divergence record: the design diverges from the spec nowhere, and Architect Review Notes records its calls with reasons.
- Contract by construction: CP-790 asserts on the walked paths, not only on the part set, and the note says why.
- Handed-down constraints: stated as properties. Sub-jobs are omitted with a reason.
