# Flow Findings — development-plan  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited: `tl_instruction.md` against `change_design.md` and `change_spec.md`. The product has no `docs/` (`Definition: none`), so the adr / nfdr / fdr cross-check is skipped, as the skill allows.

- **[non-blocking · change-local · coverage]** Task 2 (`set_xlim`) drops the rule-implied x-path edges that the plan itself says need their own test. Where: `tl_instruction.md` §Task 2 *Behaviours to verify*. The plan splits the setters because "the x path is otherwise exercised only by one design row" and "it is a separate place with its own failure". Task 2 then covers only argument forms, `functionlog`/`logit`, `set_xbound` and an ascending case. The spec says everything holds "for the x-axis and the y-axis alike". Task 1 gives each of these a test on y, and none has one on x:
  - CP-10, one limit passed (`left=`/`right=`);
  - CP-11, a non-positive `left`/`right` limit with its warning text;
  - CP-12, equal limits;
  - CP-13, autoscaling after `invert_xaxis()`;
  - CP-14, `sharex`;
  - CP-9, no data and `basex=2`.

  The CP-11 case matters most. `set_xlim` has its own copy of the non-positive replacement, and the hint's capture point ("after the CP-11 replacement") sits right after it. A wrong capture point in `set_xlim` would pass every Task 2 test. Direction: add x counterparts, or record why the shared design covers them.
- **[non-blocking · change-local · coverage]** Task 2 has no "fail before, pass after" statement, though CP-16 requires one. Where: `tl_instruction.md` §Task 2. Task 1 lists which of its tests go red on the unchanged tree, and Task 2 lists none. Its gate says only "the Task 1 and Task 2 tests pass". The developer is left to work out which x tests must fail first. Direction: state it per task, as Task 1 does.
- **[non-blocking · change-local · divergence-record]** The design's single-delta ruling is overridden by a two-task split, and the plan's reason is thin. Where: `tl_instruction.md` §TL Review Notes, *Task split*, against `change_design.md` §3 *Sub-jobs*. The split is recorded with a reason, so lens 4 is met. But both tasks have no dependency, edit the same two files, and add the same helper idea. Neither task states which one introduces a shared helper and which reuses it, although the later commit shows a shared `_keep_limit_order`. The hint tells each task to do the edit separately. Direction: state the shared piece's owner, or say the duplication is intended.
- **[non-blocking · change-local · coverage]** The design's task-independence claim ("either can land first and the suite stays green") is carried into `Dependencies: None` on both tasks, but Task 1's `test_set_ybound_honours_inversion_on_log` and the autoscale test run through shared-axes and `set_bound` paths whose x counterparts live in Task 2. Where: `tl_instruction.md` §Task 1 *Behaviours to verify*. This is low-risk, since the y tests do not need Task 2. It is recorded because the "which task owns the shared path" point above is not settled.

Checked and clean:
- **Classification (lens 3):** `Category: bug` and `Behaviour: changing` match the design and the spec.
- **Enacted constraints (lens 8):** the hint states an approach in terms of direction comparison. It prescribes no downstream role's decision, and the spec's Gap 6 (tests the card runs) is carried as a property.
- **Step contract (lens 6):** the third-party / device-storage line is present. `Publishes text: no` is carried. The layout matches the design's §2.
- **Design §5 rows 1–13:** all are carried into Task 1 or Task 2, with the TL additions recorded in the review notes.
