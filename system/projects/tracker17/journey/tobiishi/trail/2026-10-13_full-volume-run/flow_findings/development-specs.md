# Flow Findings — development-specs  (audited 2026-10-13)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 3 (classification copied verbatim: `nfdr` / `changing`, matches the request), 4 (Locked Answers carry reasons for each divergence), 5 and 7 (`## Verified Claims` present; each verdict-bearing claim is a run with command, tree `e5e1cbbae`, conditions and output; cited lines re-checked at that commit and match) held. Two findings:

- **[non-blocking · change-local · coverage]** The too-slow verdict for the three new actions has no test row. CP-284 and CP-287 make a row or total at or over 1.0 s fail the run, and an Examples row exercises it ("Only the assignee remove's total is over the limit"), but CP-288 lists only a refused-submission and a wrong-landing test per action, and CP-289 supplies new-action readings "each under the limit". Where: `change_spec.md §Rules` CP-284, CP-287, CP-288, CP-289. A slow-row rule for the new rows could be deleted with every listed test still green. Direction: map CP-284/CP-287 to a stated test row for the new actions.
- **[non-blocking · change-local · handed-down constraint]** The spec decides the shape of tests its successors own. CP-289 names three existing tests and fixes how each changes ("only by also supplying readings"); CP-288 fixes the test shape (collaborators handed in, no product-module patching). Where: `change_spec.md §Rules` CP-288, CP-289; `§Locked Answers` Gap 10. The properties (nothing loosened, QC-28's no-patch rule) are the spec's to state. Which tests change and how is the Developer's/TL's call. Direction: state the properties and leave the edit set to them.
