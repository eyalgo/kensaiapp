# Flow Findings — development-plan  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited: `tl_instruction.md` against `change_design.md`, `change_spec.md`, `docs/adr/` 0001–0009, `docs/nfdr.md`, `docs/fdr.md`. Lenses 1–6 and 8 walked; 7, 9 and 10 do not apply to this step.

- **[non-blocking · change-local · coverage]** Two existing assertions that Task 1 turns red are in neither the plan's layout nor its retire list, and Task 1 says to retain them. Where: `tl_instruction.md` § Task 1 (layout; "retain the existing architecture assertions"; "the full existing suite pass"). `tests/architecture/test_shapes.py` `test_only_the_assignee_feature_is_added_to_domain` asserted `tasks.py`, `priorities.py` and `due_dates.py` absent and `TrackerState` fields equal to three names. `tests/integration/test_tracker.py` asserted `TextField` values equal to `{"name", "description"}`. Neither file appears in the layout tree or any task header; both were rewritten in commit `65af2285e` (Task 1 green). The design's "Assertions retired" list (`change_design.md` § 5) names four assertions and omits both, so the gap is inherited from the design, and the plan did not re-derive it from the baseline suite it ran. Direction: a plan that gates on the full existing suite lists each existing assertion the new contracts contradict, with the owning task.
- **[non-blocking · change-local · divergence record]** The plan's gate for Tasks 1–3 does not run the browser suite, and the reason is not stated for the tasks that change the saved shape (Task 2). Where: `tl_instruction.md` § Task 2 gate. The TL notes record that playwright is absent at baseline and that the browser suite is a separate run, so the omission may be deliberate. It is not stated whether any browser test reads the saved file's keys (`tests/e2e/test_people.py` names `next_project_id`). Direction: one line recording that no browser test depends on the saved shape before Task 4.

Checked and clean:
- **Classification propagation:** header `feature` / `changing` copied verbatim from the design and spec.
- **Coverage:** CP-106–CP-143 and the design's T1–T11 each map to a task's `#### Behaviours to verify`, including CP-107, CP-118 (crafted GET), CP-121, CP-125, CP-136/137 and CP-142/143.
- **Divergence record:** the TL's additions are logged with reasons in `## TL Review Notes`: the cut, trace timing, type precision, added coverage, timed harness, the Task 3 dependency, baseline and gate scope, and the station-record correction owed.
- **Atomic-landing edges:** A+trace is in Task 1, B+saved-shape in Task 2, D+page/route/browser assertions in Task 4.
- **Handed-down constraint:** the design states the atomic-landing edges as properties, and the plan, not the design, chose the task cut.
