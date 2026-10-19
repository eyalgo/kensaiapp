# Flow Findings — development-implementation  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited: closing commit `a035434` (instance branch), product commits `83728a6`..`f355892` plus the
code-integrity commits `11017e3` and `67dbb94`, against `tl_instruction.md`, `change_design.md`,
`code-integrity-report.md` and `project.md` (`Languages: Python`). Lens 9 skipped: the product has no
`docs/SDD.md`, so no parts table; the integrity report's Placement says the same.

- **[non-blocking · change-local · evidence-that-could-have-failed]** The Language resolution block
  gives `testing_python.md:31` the verdict "followed with one difference". The quoted clause says the
  fake is "passed to the constructor"; the run handed `RecordingAdapter` in through `Session.mount`. The
  clause carries no such exception, so the verdict is a divergence. The block itself names the
  difference, and the integrity report lists it under accepted divergences, so the information is not
  lost. Where: closing commit `a035434`, `Language resolution:` § `testing_python.md:31`. Direction:
  record it as `diverged:` with the reason, as the block does for `testing_python.md:17`.
- **[non-blocking · change-local · evidence-that-could-have-failed]** The closing commit's block no
  longer matches the code at the product tip. It records `conventions.md:20` as "diverged" and says the
  new strings are single-quoted. Code-integrity then requoted them in `11017e3`, so the tip code
  follows the clause. The integrity report records the change (Calls made, 1), but the commit a reader
  sees first is stale. Where: closing commit `a035434`, `Language resolution:` § `conventions.md:20`.
  Direction: the commit cannot be amended, so the integrity report is the record that wins. A reader
  holding only the commit is misled.

Checked and clean:

- **Resolved language.** Python, matching `Languages: Python`; both touched files are `.py`.
- **Quotes, not paraphrases, and completeness.** The packet's `README.md` lists six concerns and the
  block has a per-concern line for each: Toolchain, Layout, Quality gates, Conventions, Errors and
  logging, and Testing. I opened each quoted line and the clauses match the packet's words. The
  bore-on-nothing lines (`layout.md:17`, `conventions.md:45`, `conventions.md:136`,
  `errors_logging.md:77`) hold: the change created no file, wrote no annotation and no handler. The
  run's own commands (the card's Test command and its interpreter) are quoted at `toolchain.md:12` and
  `quality_gates.md:14`, so no concern that governs them is hidden under a bore-on-nothing line.
- **Step 1b block.** Present, with both counts (1 added, 0 not delivered). I checked the 0 against each
  task's `#### Behaviours to verify` and the committed tests: all 14 named tests exist and assert
  everything listed (two spellings of the header, lower-case `get` and `head`, `Authorization` kept,
  the 302 redirect cases, the file-object `0` and `3`, and the five bodiless methods plus `PURGE`).
  The one added case (`data=[]` with auth) is in the count.
- **Several rules behind one entry point.** Task 1 lands the method, body, removal and repeat-delete
  rules in one function. The Developer Review Notes name the case that goes red for each rule reverted
  alone (skip-only, single delete, widened predicate, HEAD dropped, `not body`), established by mutation
  after the landing, and say so.
- **Step-specific.** One change, committed in the product worktree on the change branch. Only
  `requests/models.py` and `test_requests.py` were touched, nothing outside the instruction's scope. The
  new tests open no connection. The Task 2 "no red" lane is stated with its reason.
