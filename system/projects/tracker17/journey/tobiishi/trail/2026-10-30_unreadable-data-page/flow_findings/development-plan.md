# Flow Findings — development-plan  (audited 2026-10-30)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · coverage / contract-realized]** Task 5 drops its dependency on Task 4 (README). Where: `tl_instruction.md §Task 5 Dependencies` ("Task 3" only) against `§TL Review Notes — Ordering` and `change_design.md §3 Build sequence` ("the set-aside/readme checks require B + C"; T16 = B + C). The TL note says the README is placed first "so the operator-facing passages are ready when real-start/set-aside tests run", but that order is carried only by task numbering. Task 4 lists "Dependencies: None", and a sequencer that reads the Dependencies field is free to run Task 5 first. Task 5 holds T16 (set-aside then restart) and a pass criterion that "the README's two edited passages match the approved text", and both need Task 4's output. Direction: state Task 4 as a dependency of Task 5, or move the README-dependent proof out of Task 5.
- **[non-blocking · change-local · divergence record]** Cosmetic: the plan splits design sub-job A into three tasks and the split is recorded (`§TL Review Notes — Task split`). It does not record that design T10 (`tests/integration/test_start_stop.py`, tagged A + B) lands in Task 5 only. The reason is implicit in the B dependency and nothing is lost. No action needed beyond a note.

Lenses with no finding:
- Coverage: T1–T20 and every Example map to a Task 1–5 behaviour or review item. The ten "Records this change makes false" map one-to-one to the ten "Corrections owed" lines, and the existing deferred decisions cover the CONTENT.md and EX-12 items.
- Altitude: no mechanism leaks beyond the design's own hints.
- Classification: `feature` / `changing` copied verbatim.
- Handed-down constraints: the atomic-landing edge is kept as one task (Task 5), stated as a property and not enacted.
