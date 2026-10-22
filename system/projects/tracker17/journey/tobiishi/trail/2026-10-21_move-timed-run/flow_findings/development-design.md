# Flow Findings — development-design  (audited 2026-10-21)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses walked: coverage, altitude, classification propagation (Category `nfdr` / Behaviour `changing` copied verbatim from `change_spec.md`), divergence record, contract by construction, step contract, handed-down constraints. Lenses 7 (specs / implementation only), 9 (implementation only) and 10 (content only) do not apply to this step.

- **[non-blocking · change-local · coverage]** The harness's own "task 4 must be `todo` before a move counts" rule (CP-371) is stated but no test row isolates it. Where: `change_design.md §3 Sub-job A (Exposes)`, `§5 T1–T5`. T1 asserts `todo` on a success, and T2 starts from `in-progress`, where the product itself refuses with a non-matching redirect. Nothing covers a pre-state that is neither `todo` nor a refused move (e.g. `done`, if the product allows `done` → `in-progress`) with an exact 303 and a correct whole-state readback. The measurement would pass such a run, and the guard could be deleted with the suite green. Direction: add a case with a non-`todo` pre-state whose move the product accepts, and assert the POST and total rows fail.

Otherwise Clean: every CP-371–CP-392 rule and each Example maps to a T-row or a named acceptance check (Rule pass and Example pass); the CP-392 test list is carried through T11 unchanged; the atomic-landing edge is stated as a property with no downstream role named; no divergence from the spec is unrecorded.
