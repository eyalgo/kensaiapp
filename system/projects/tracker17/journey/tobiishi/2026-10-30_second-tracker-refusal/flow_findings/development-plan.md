# Flow Findings — development-plan  (audited 2026-10-30)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited: `tl_instruction.md` against `change_design.md` and `change_spec.md`. Lens 3: Category `feature` / Behaviour `changing` copied verbatim. Lenses 7, 9, 10 do not apply to this step. Lens 8: the plan states the design's properties and names no downstream role.

- **[non-blocking · change-local · coverage]** CP-699 says the start after a kill or Ctrl-C has "no message about the earlier tracker", but no Task 2 case asserts it. `test_tracker_starts_after_the_owner_is_killed` and `test_tracker_restarts_after_ctrl_c` assert ready, HTTP and saved bytes only. Where: `tl_instruction.md` Task 2 §Behaviours to verify. A rule-implied negative (stderr empty on the restart) is left to the Developer; direction: add the stream assertion to those two cases.
- **[non-blocking · change-local · step-specific contract]** Task 3 limits the README edit to "only the requested restart passage", and its review criterion fails any other change. The sibling `change_text.md` publishes a third README string in "Setting saved data aside" ("If the new directory is empty, there was no saved data to set aside."), a consequence of CP-703. Where: `tl_instruction.md` Task 3 §Deliverables verified by review; `change_text.md` §The setup instructions. Task 3 also says to place the text "verbatim" from `change_text.md`, so the two instructions conflict on the one sentence and a reviewer cannot give both a pass. Direction: the plan should scope the README task to the places `change_text.md` names, not to one passage. The spec and design did not name the CP-703 effect on the set-aside section, so this entered at the content step; the plan's "only" wording was the part that could not absorb it.
Divergence record (lens 4), no finding: the Tech Lead dropped design T17's README test assertion, added the lifetime-during-close observation, and sharpened rollback coverage. Each carries its reason in `## TL Review Notes`.

_Lenses 1, 2, 4, 5 and 6 otherwise clean: every design row T1–T19 maps to a Task 1/2/3 case or gate, and every spec rule CP-693–CP-709 is reachable through them._
