# Flow Findings — development-design  (audited 2026-10-29)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Read `change_design.md` cold against `change_spec.md`, `docs/SDD.md` § 3/§ 4 and the product tests at the branch tip. Header `Category: bug` / `Behaviour: preserving` copied verbatim; every Invariant and Structural Goal item maps to C1–C8; the one departure from the template (characterization-only rows) is recorded in Architect Review Notes with its reason; the cited lines (`test_start.py:L516-L563`, SDD TS-1/TS-2 serving NFR-11) match the files.

- **[non-blocking · change-local · contract-realized]** The reaping of the inner child is stated by pointing at a helper that does not cover it. Where: `change_design.md §3 The proof module, item 4`. The design says "child processes must be reaped on failure; the existing tracker helper already kills and waits for a tracker that remains running" — `_run_real_start` reaps the *tracker*, not the extra pytest process the proof test itself starts under an ignored-INT shell. If the outer wait expires, nothing in the design says who ends that pytest process and its tracker, and an ignored-INT launch cannot be ended by SIGINT. Direction: state the property (no process outlives a failed proof) and leave how to the successor.

_No other findings. Lens 9 and 10 do not apply to this step; the ADR/NFDR cross-checks were run against the records the design cites._
