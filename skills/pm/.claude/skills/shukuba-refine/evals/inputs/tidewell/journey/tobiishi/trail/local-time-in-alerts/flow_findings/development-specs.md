# Flow Findings — development-specs  (audited 2026-09-08)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · coverage]** The Examples table has no row for a day on which the
  daylight-saving change falls between two tides. Where: `change_spec.md §Examples`. Rule LT2 covers
  it, so the design can derive it. Direction: add one row for the change day.
