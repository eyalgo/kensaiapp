# Flow Findings — development-design  (audited 2026-10-07)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Clean — no flow-issues found.

Lenses walked against `change_design.md` read beside `change_spec.md`:

- **Coverage.** CP-39 to CP-46 each map to a test row or a named existing row. The rule-implied edges are covered: another bind failure (CP-42), saved data present or absent (CP-41), unreadable data with a held address (CP-43), and a holder that keeps answering (CP-39).
- **Altitude and classification.** `Category: feature` and `Behaviour: changing` are copied verbatim from the spec. The design places logic by SDD § 3's `Owns` cells and quotes them.
- **Divergence.** Exit status 1, the typed error, the e2e placement and the no-skip choice are each recorded in `## Architect Review Notes` with a reason. The spec-level choices are not re-decided.
- **Contract by construction.** "Address in use" is decided by `errno.EADDRINUSE` at the bind. The unreadable-data-first order is the order `start` already has, with a stated reason. Neither rests on a coincidence.
- **Handed-down constraints.** The design states properties and does not name a downstream role. It owns the build sequence and test additions, so those are not enacted.
- **Records made false.** The one stale sentence, the docstring at `web/listener.py:5`, is named, and Sub-job W rewrites it. No other product file I grepped still says a bind error propagates.

Observation, not a finding: the QC-40 row records "Pass today, failing tomorrow" with the 2026-10-08 deadline and the owner's way out. It is recorded with its reason, and the same row stood in the previous design.
