# Flow Findings — development-design  (audited 2026-09-08)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

_Context: the specs-stage blocking finding stands — the design adds no refund and no fence._

- **[non-blocking · change-local · coverage]** No test covers cancelling a pickup that is already
  cancelled. Where: `change_design.md §5`. Direction: add one row; the operation should refuse it.
