# Flow Findings — development-design  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · contract realized]** Test row 6 (per-group `annotate`) would also pass if `DISTINCT` were dropped, since each author is one row per group. Where: `change_design.md §5` row 6. The "cannot pass if DISTINCT is dropped" property is carried by rows 4, 5 and 7, which meets CP-15's second bullet, so record-and-proceed. Direction: none needed.

Lenses walked: coverage (every Example and rule-implied edge maps to rows 1–9; CP-16 correctly a gate), classification (`bug` / `changing` copied verbatim from the spec), divergence (the CP-15 red-versus-fence reading, the PostgreSQL reach and the test placement are all recorded in Architect Review Notes with reasons), contract by construction (CP-9/CP-10 realized by the one `distinct` value, checked against `Aggregate.as_sql`; the claim that no template in the tree already spaces after `%(distinct)s` holds), handed-down constraints (stated as properties; no downstream role named, no task granularity decided). The Records-this-change-makes-false and SDD-optional cases are handled correctly: no `docs/` decision files exist and none are flagged missing.
