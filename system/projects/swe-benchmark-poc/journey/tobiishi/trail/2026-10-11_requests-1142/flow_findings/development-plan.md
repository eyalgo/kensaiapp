# Flow Findings — development-plan  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited: `tl_instruction.md` against `change_design.md` and `change_spec.md`. No `docs/adr/`, `docs/nfdr.md`, `docs/fdr.md` or `docs/SDD.md` exist for this product, so those cross-checks (and lens 9) are skipped. Classification (`bug` / `changing`) is copied verbatim. Coverage holds: design §5 rows 1–12 each map to a named test, and CP-9 to CP-15 are all reached.

- **[non-blocking · change-local · divergence-record]** Task 2 adds a fifth test, `test_bodiless_post_with_auth_keeps_content_length_zero`, which no design §5 row has (rows 9–12 give four). It is explained inside the task, but TL Review Notes lists only the Task 1 additions under "Behaviour added". Where: `tl_instruction.md §TL Review Notes` and `§Task 2`. A decision that diverged from the input should have its entry in the divergence section; add the entry there.
- **[non-blocking · change-local · divergence-record]** The "Behaviour added" bullet for Task 1 presents `Authorization` still set on a tuple-auth `GET`, and the lower-case `'get'` / `'head'` method, as edge cases the design only pins "in passing". Design §5 rows 1 and 6 state both outright, so those are carried inputs, not additions. Where: `tl_instruction.md §TL Review Notes`, third bullet. The divergence record overstates what diverged; the remaining true addition is the caller-supplied-`Content-Length` redirect test (the next bullet).
- **[non-blocking · change-local · evidence-that-could-fail]** Both verification gates require the new tests to "appear among the passes". The gate command, `/home/kensai/issue-test.sh`, reports only a summary (`N failed, M passed`, then "only baseline failures remain"), and the plan itself says the tool "does not by itself prove the new tests ran". The plan names no way to see the tests (a count of 5 + 14 passed, a verbose or `-k` run, or similar). A gate that cannot show the claim could not fail on a missing test. Where: `tl_instruction.md §TL Review Notes` (gate bullet), `§Task 1` and `§Task 2` *Verification gate*. Direction: state the observation the developer is to make.

_Lenses 2, 3, 5, 6 and 8: Clean. Lenses 7 (implementation-only), 9 and 10 do not apply to this step._
