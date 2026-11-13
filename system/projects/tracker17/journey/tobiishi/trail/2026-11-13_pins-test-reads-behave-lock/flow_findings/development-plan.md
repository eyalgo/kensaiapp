# Flow Findings — development-plan  (audited 2026-11-13)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 1 (coverage), 3 (classification: `nfdr` / `changing` copied verbatim), 5, 6, 8 (hints state the
property and the seam, no downstream role is named or decided for) read clean. Every §5 row, all five
CP-773 refusal forms across all four lists, the three CP-774 cases, both CP-775 cases and both CP-776
cases map to a task test. Lenses 7, 9 and 10 do not apply to this step.

- **[non-blocking · change-local · divergence-record]** The TL Review Notes say each of Tasks 1 to 3 "adds a failing test before it adds code", but two Task 3 tests cannot go red at that point. `test_a_name_spelt_differently_is_still_fixed_by_the_lock` asserts "no finding", and `test_a_missing_manifest_gives_no_lock_mismatch_finding` asserts the manifest finding (built in Task 2) plus no lock-mismatch finding. Both pass once Task 2's check exists, before any lock code. Where: `tl_instruction.md §TL Review Notes (Task split)`, `§Task 3 Behaviours to verify`. Either the note's claim is wrong for these two, or they are guards, not red-first tests. Direction: say so in the note, so the developer does not read a green start as a defect, and treat the mismatch cases as the Task 3 red.
- **[non-blocking · change-local · divergence-record]** "Corrections owed while there" hands the `docs/nfdr.md` QC-39 *verified by* correction to "outside this change's reach" and names no owner or step. CP-783 confines the diff to one file, so the exclusion is right, but the correction is left unowned. Where: `tl_instruction.md §Corrections owed while there`. Direction: name who or what carries it after the seal.
