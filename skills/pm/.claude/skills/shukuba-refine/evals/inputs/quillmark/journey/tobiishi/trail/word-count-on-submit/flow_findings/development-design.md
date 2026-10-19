# Flow Findings — development-design  (audited 2026-09-08)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · divergence]** The design decides the front-matter set (title page,
  dedication, an epigraph before the first chapter, table of contents) with no upstream source. Where:
  `change_design.md §3`. Reasonable, and nothing breaks, but on this reading a preface or a foreword
  counts as body text, and nothing upstream says whether the press wants that. Direction: state where
  the set comes from.
