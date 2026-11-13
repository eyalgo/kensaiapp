# Flow Findings — development-specs  (audited 2026-11-13)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Checked cold against `change_request.md` and the base commit `8c3f7e74d`. Every file and line the spec cites matches the base. Category and Behaviour are copied verbatim from the request. Every request clause maps to an invariant or the Structural Goal. The `## Verified Claims` section is present, and its gate and test verdicts were run. The one failure not reproduced is declared as such.

- **[non-blocking · change-local · contract-realized]** I-5's "prints nothing" command greps added lines for `retry` and `flaky` anywhere in the line. Where: `change_spec.md §Invariants I-5`. The request asks for the cause to be named in a docstring or commit body. A docstring that names a cause as a retry or a flaky wait would trip the check, though no test is retried or skipped. The check may be met only if the cause is worded around it. Direction: anchor the pattern on the markers and decorators that do the hiding.
- **[non-blocking · change-local · altitude]** I-3 and I-5 pin wait limits by line number (`test_start.py:L708`, `test_sigint_launch.py:L38`) without saying the lines are the base's. Where: `change_spec.md §Invariants I-5`. The change may edit those files, so the lines may move. The values (`30`, `120`) are the rule and the lines are only locators. Direction: say "at the base" or drop the line anchors.

_Lenses 3, 4, 5 (otherwise), 6, 8 and 9 to 10 raised nothing; 9 and 10 do not apply to this step._
