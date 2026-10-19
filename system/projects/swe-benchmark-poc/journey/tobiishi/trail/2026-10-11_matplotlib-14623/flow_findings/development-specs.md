# Flow Findings — development-specs  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 3 (classification copied verbatim: `bug` / `changing`, matching `change_request.md`), 4 (the six
gaps each carry a reason), 5, 6 and 8 found nothing. Lens 7's `## Verified Claims` section is present
and its Today cells and probe runs name command, tree and conditions.

- **[non-blocking · change-local · altitude]** The rules and the rationale carry mechanism anchors. CP-9 names `LogLocator.nonsingular` / `LogitLocator.nonsingular`, `ticker.py` lines 2382–2383 and 2627–2628, and `_base.py` lines 3267 and 3647. Gap 1 repeats the `ticker.py` lines, and Gap 4 cites test-file line numbers. Where: `change_spec.md §Rules (CP-9)`, `§Locked Answers (Gap 1, Gap 4)`. Altitude puts the mechanism outside the rules and the rationale. The same facts already sit in `## Verified Claims`, which is where they belong, and the spec itself says how the rules are met is development-design's decision. Direction: keep the observable defect in CP-9 and leave the locator and line anchors to Verified Claims.
- **[non-blocking · change-local · evidence-that-could-have-failed]** The claim that the card's `Test command:` runs only `lib/matplotlib/tests/test_axes.py` is established by reading `/home/kensai/issue-suite.sh`, not by running the command. Where: `change_spec.md §Verified Claims` (row "runs only test_axes.py"), `§Locked Answers (Gap 6)`. What a command decides is to be run, not derived from its script. CP-16 and Gap 6 rest on this claim, since they decide where the change's tests must live. The same section ran `/home/kensai/issue-test.sh` for the 112-failure count, so a run that shows a test placed outside `test_axes.py` is not collected is within reach. Direction: add a run for it, or word the claim as read.
- **[non-blocking · change-local · coverage]** Rule-implied cases on the other covered scales and the x-axis have no example row. CP-13 (set_ybound honouring inversion, autoscaling an inverted axis) is exampled on `log` only, except one `logit` autoscale row. `functionlog` has no CP-10, CP-11 or CP-13 row. CP-14 (shared axes) has no `sharex` row. CP-10 has only the `top`-only form, not `bottom`-only on an inverted axis. Where: `change_spec.md §Examples`. The Examples table is the floor, and the "x-axis stands for y-axis" note covers some of this. A `functionlog` and an `x`-side row would give the plan a test row each, as CP-16's four required tests do not name them. Direction: add rows or state the omission.

_Skill-general: none._
