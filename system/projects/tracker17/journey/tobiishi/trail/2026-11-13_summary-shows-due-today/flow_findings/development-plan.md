# Flow Findings — development-plan  (audited 2026-11-13)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited: `tl_instruction.md` against `change_design.md` and `change_spec.md`; the `docs/` cross-checks (adr, nfdr, fdr) are carried by the design's own review notes and raised nothing here. Classification (`feature` / `changing`) copied verbatim. Both design sub-jobs map to Tasks 1 and 2, the atomic-landing edge is held whole inside Task 2, and the divergences (the early construction-site landing, the task cut, the trace test with its docstring) are recorded with reasons. The design's test rows are all carried.

- **[non-blocking · change-local · coverage]** CP-817's "every new or changed test module names the requirements or acceptance criteria it checks" is carried for fewer modules than the plan changes. Task 1 says "the two test modules' own docstrings name AC-13", and Task 2 says "The two modules' own docstrings", yet Task 2's header lists three test modules and the plan also edits `tests/integration/test_pages.py`, `tests/integration/test_timed_run.py` and `tests/integration/test_summary_pages.py` (in Task 1 as well). Where: `tl_instruction.md` Task 1 closing paragraph, Task 2 closing paragraph. The count does not match the files each task touches, so which modules owe a docstring line is left for the developer to infer. Direction: name the modules, or say "every test module this task changes".
- **[non-blocking · change-local · coverage]** Task 1's "Behaviours to verify" header says the developer adds tests to `tests/unit/test_summary.py` and `tests/integration/test_summary_tracker.py`, but its last bullet (`test_summary_trace_names_ac13`) is a change to `SUMMARY_REQUIREMENTS` in `tests/architecture/test_trace.py`, a third module. Where: `tl_instruction.md` Task 1 §Behaviours to verify. The header's file list is short by the file the bullet lives in. Direction: list the trace test's module in the header.

Lenses 3, 4, 5, 6 and 8: clean. Lens 2 (altitude), 7, 9 and 10 do not apply to this step.
