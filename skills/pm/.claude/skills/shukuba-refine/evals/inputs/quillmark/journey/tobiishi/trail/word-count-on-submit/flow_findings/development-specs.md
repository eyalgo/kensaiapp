# Flow Findings — development-specs  (audited 2026-09-08)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · coverage]** WC2 says the count excludes "front matter as FR-2
  defines it", and FR-2 defines no front matter — the rule closes over itself. Where:
  `change_spec.md §Rules/WC2` against `docs/SRS.md` FR-2. The design will have to decide the set.
  Direction: record the set as a Locked Answer, or ask for it upstream.
