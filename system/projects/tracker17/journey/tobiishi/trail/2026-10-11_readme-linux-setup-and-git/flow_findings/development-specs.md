# Flow Findings — development-specs  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Checked at the change's branch point (`47d40582a`), since the audited tip also carries later steps' README edits: the README had no `--with-deps` or `Debian 12`, no relative-time word, the closing paragraph at `:107` as quoted, and the block at `:91-99`. FDR R-119/R-120 and SDD `:285-296`, `:677-686` match what CP-69 to CP-76 cite.

- **[non-blocking · change-local · coverage]** CP-73 and CP-75 use "the full suite", a term the README never uses. Its commands are `pytest tests/` and `pytest tests/e2e/`, and `grep -i suite` on the branch-point README returns nothing. Where: `change_spec.md §Rules CP-73, §Locked Answers Gap 7`. Gap 7 keeps the SDD's term on purpose, so the wording is recorded. But no rule says the reader must be able to tell which commands the Git condition covers. Direction: a rule-level statement that the reader can tell what "full" covers, kept at requirement altitude.

Lenses 2, 3, 4, 5, 6, 7 and 8: Clean. Classification `bug` / `changing` is copied verbatim from the request. The one divergence from the request (CP-74) is recorded in Gap 1 with its reason. `## Verified Claims` is present, and each claim about what a command decides was run, with tree and conditions stated.
