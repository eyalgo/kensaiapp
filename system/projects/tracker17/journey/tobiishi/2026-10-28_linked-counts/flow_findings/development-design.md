# Flow Findings — development-design  (audited 2026-10-28)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · coverage]** CP-517's match line (`1 task matches this filter.` / `{N} tasks match this filter.`) is named by no test row. Where: `change_design.md §5 T02, T03`. CP-525 asks the AC-14 test to assert that the match line states the count; T02 says "numeral, and target's exact task identities and count", which can be read as a row count. T04 and T05 cover the zero and empty text only. Direction: have T02 name the match-line text for N ≥ 1.

Checked and found sound: header `Category`/`Behaviour` copied verbatim from the spec; CP-513–CP-528 each map to a T row in the coverage walk; the CP-525 fixture contradiction is recorded in `## Architect Review Notes (a)` and in `deferred_decisions.md`; "Records this change makes false" is consistent with `SDD.md` S-6 and `UXD.md` UX-F6, which already say the counts link; the B-then-A order is stated as a property (no atomic-landing edge) and names no downstream role; placement follows the SDD § 3 `web` row, with no logic added to `domain`, `application` or `persistence`; the `Publishes text:` line is present.
