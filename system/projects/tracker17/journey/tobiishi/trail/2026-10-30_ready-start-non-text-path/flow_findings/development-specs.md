# Flow Findings — development-specs  (audited 2026-10-30)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · altitude]** A rule carries a code anchor and a runtime mechanism. Where: `change_spec.md §Rules` CP-750 (`products/tracker17/main.py:139`, "Python's UTF-8 mode", "C locale"). The rule should state the observable (the same four characters on any console); the source line belongs in Verified Claims, where it is already recorded. Direction: drop the anchor from the rule.
- **[non-blocking · change-local · altitude]** The proof rules prescribe the test's shape: child process, `os.fsdecode`, the strict-UTF-8 console setting. Where: `change_spec.md §Rules` CP-752, CP-754. The request asks for a real start and a failing-on-main test, but not for these mechanisms. Direction: state what the test must hold and leave how to design.
- **[non-blocking · change-local · evidence]** The valid-file case (CP-753) has no run behind it. Where: `change_spec.md §Verified Claims`, row on CP-753. The section says so honestly, and the skip rule covers it. Still, CP-747's "standard error stays empty" and "nothing more written" after Ctrl-C are also only partly shown: the rows give status 0 and the line, not stderr. Direction: add a stderr result to the plain-path start row.

Lenses 3 (header Category/Behaviour copied verbatim from the request), 4 (six gaps recorded with reasons), 5, 6 and 8 hold: no finding. Lens 1: rule-implied edges (several bytes, byte at any position, non-UTF-8 console, valid non-ASCII, real backslash) are all mapped to rules and examples. The deferred failed-action message is recorded in `deferred_decisions.md`. `docs/fdr.md` is present and the spec cites it without contradiction.
