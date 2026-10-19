# Flow Findings — development-specs  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 3 (classification copied verbatim: `bug` / `changing`), 4 (Gap 1–6 each carry a reason; the str-return boundary is recorded in Verified Claims), 5, 6, 7 (`## Verified Claims` present, every verdict run with command, tree and result; the 28-failure baseline and the candidate run both ran the card's `Test command:`) and 8 (Gap 6 states the test-placement constraint and leaves it to design) found nothing.

- **[non-blocking · change-local · altitude]** The rule text carries a mechanism and a code anchor. Where: `change_spec.md §Rules, CP-9` ("`sympy/core/function.py` line 510 passes the return straight to `Float(r, prec)`"); echoed in `§Locked Answers, Gap 4` ("the defect stops evalf from ever calling `z`"). The cause belongs in Verified Claims, where it already sits. In a rule it leaks the storage/mechanism anchor to design. Direction: keep CP-9 to the observable behaviour.
- **[non-blocking · change-local · coverage]** Rule-implied cases CP-9 and CP-13 name have no Examples row. Where: `change_spec.md §Examples`. CP-9 names a Python `int` return, but only `float` (`p`) and `complex` (`pc`) rows exist. A nested return that is `oo` (e.g. `f(F(2))` with `F` returning `oo`) is a "number" by the Terms definition, but its expected result is unstated. The Examples table is the floor, so a downstream test could drop these without any row to trace them. Direction: add the rows or narrow the rule.
