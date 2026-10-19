# Code integrity report — 2026-10-11_astropy-12907

Integrity: pass

**Mode:** workflow. **Date:** 2026-10-11. **Reviewer:** Senior Engineer (`development-code-integrity`).
**Outcome:** clean pass. One test was added and no code changed. One owner decision is carried
forward from the design (see *Calls made*).

## Deferrals

None. The closing marker (`771b016`, `developer: 2026-10-11_astropy-12907 — implementation complete`,
the only marker on the branch) carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

The product branch `2026-10-11_astropy-12907` in the product change worktree
(`<the issue's clone>/.worktrees/2026-10-11_astropy-12907`),
against `base_commit` `d16bfe05`. That covers the developer's commits `40b7207c` (red), `fcb870a2`
(green) and `0eda79a1` (refactor):

- `astropy/modeling/separable.py`: one line in `_cstack`. The right-hand matrix branch now copies
  `right` into its bottom-right block instead of writing `1`.
- `astropy/modeling/tests/test_separable.py`: 123 added lines and no edited line. They are a local
  hook model, four module-level names, three helpers and nine tests (T1–T8 and T7b).

## The intent it was checked against

- `tl_instruction.md`: Task 1 and its *Behaviours to verify* (T1–T8, T7b) and *Verification gate*.
- `change_spec.md`: CP-9 to CP-15, the Examples table and Locked Answers Gaps 1–5.
- `change_design.md`: §5 (test rows, spec-to-row map and rule-implied edges) and Architect Review
  Notes 1–3.
- `change_request.md`: the issue text and *What must not be done*.
- `docs/fdr.md`: absent. The product has no FDR, which is the normal case, so this is not a finding.

## Tests added or fixed

**Added (1):** `test_right_hand_pipeline_operand_reads_as_on_the_left`, in product commit `801f33a8`.

- **Why:** CP-10 covers a right-hand operand "built with any operator: `&`, `|`, …". The suite had
  no test that fails when a `|`-built right operand is misread. The only `|`-built right operands in
  it (T8: `sh1 & (rot | rot)`, `sh1 & (sh2 | scl1)`) have all-ones blocks. Those blocks are the same
  under the defect, so those assertions pass on the buggy branch too. The design's rule-implied
  edges list covered the arithmetic-operator case by reasoning (its block is always all ones). They
  did not cover a `|` case whose block is *not* all ones.
- **What it asserts, from the rules:** take `R = (sh1 & sh2) | (scl1 & scl2)`. The test asserts that
  `S(sh1 & R)` is the 3×3 identity and `I(sh1 & R)` is all `True`. The values come from three rules:
  R's block equals its left-hand reading in `S(R & sh1)` (CP-10, CP-11), L's block keeps today's
  value, and the cross blocks are `F` (CP-9). The test checks the mirror's literal and the block
  equality as well. These values were not read off the implementation.
- **Discriminates:** I ran it in memory against the pre-fix right-hand branch, with a scratch probe
  outside the tree, and it fails there. The old code gives `S = [[T,F,F],[F,T,T],[F,T,T]]`. The test
  passes on the fixed branch.

**Fixed:** none. Each of the developer's nine tests matches its row in the instruction and the
design. I checked every literal against the spec's Examples table. `map3` is `Mapping((0, 0))`, as
the T8 row requires. The two assertions the developer added beyond the instruction,
`I(custom & sh1) = [F,T]` (T4) and `I(cm & TAN) = [T,T,F,F]` (T8), are the left-hand readings CP-11
and CP-13 hold fixed, and they are correct.

**Gate, after this commit:** `/home/kensai/issue-test.sh` exits 0 with `21 passed` (the base's 11,
the developer's 9 and this run's 1). `astropy/modeling/tests/test_models.py::test_custom_separability_matrix`
reports `1 passed`. `python3 -m compileall -q` over both files exits 0. `git diff --stat d16bfe05`
still names only `separable.py` (1 line) and `test_separable.py` (added lines only), so CP-13's
"existing assertions unedited" holds.

## The finding

**No bug.** The fixed `_cstack` already does what CP-9 to CP-12 say, and everything passes. The one
finding is a **coverage gap**: CP-10 had no test for a `|`-built right operand. It is now closed by
the test above. Nothing was moved (see *Placement*).

The design's claim that CP-12 holds by construction was checked independently with the same
in-memory probe, and it holds. Both groupings of `sh1 & Identity(2) & sh2` give the 4×4 identity on
the fixed branch.

## Calls made

None of my own. One owner decision is **carried, not made here**:

- **Architect Review Note 1 (design), carried by the TL and the developer: a simple right-hand
  operand with more than one input now reads as it does on the left.** The probe confirmed the
  contradiction the note describes. On the fixed branch `S((sh1 & Identity(2)) & sh2)` moves from
  `[[T,F,F,F],[F,T,T,F],[F,T,T,F],[F,F,F,T]]` to the 4×4 identity, and `S(sh1 & Pix2Sky_CAR())`
  moves from `[[T,F,F],[F,T,T],[F,T,T]]` to the 3×3 identity. CP-13 bullet 1 freezes both values,
  but CP-12 together with CP-10 requires the move, so no code meets all three rules. The design
  resolved it and T6 pins it.
  - **Whose call:** the owner's (Eyal). The note narrows the Product Owner's CP-13 bullet 1.
  - **What this pass does with it:** it does not decide the question again. The design is the
    stage that may resolve a contradiction in the spec. The code and T6 follow the design as
    written, and nothing in the intent asks this step to override it.
  - **If the owner rules for CP-13 bullet 1 kept literally:** the spec goes back to the Product
    Owner, because CP-12 would need narrowing. T6, and the `_cstack` branch as now written, would
    have to be redone. This report's added test would not be affected, because it uses no simple
    multi-input right operand.

## Placement

**No parts table.** The product has no `docs/SDD.md` (and no `docs/adr/`, `nfdr.md` or `fdr.md`),
so there is nothing to place against and Step 0 did not run a move. For the record, the one piece
of new logic is the corrected right-hand branch, and it sits in `_cstack` in
`astropy/modeling/separable.py`, where the `&` logic already lives (design §2). No `— placement`
commit was made.

## Language resolution

- **Language:** Python. Answered at step 1 of the chain, from `project.md` `Languages: Python`.
- **Packet read:** `core/doctrine/engineering/languages/python/README.md`, with `conventions.md`,
  `quality_gates.md` and `testing_python.md` (Testing, outside the packet folder) read for the bar.
  The project has no decision files (ADR, NFDR or FDR), so the packet sits directly over the floor
  (`languages/README.md` § Precedence).
- **Quality gates:** Compile (`python3 -m compileall -q`) exits 0. The suite gate is the card's
  command, run with the card's interpreter (`/home/kensai/issue-venv`, Python 3.9.25). It exits 0
  with 21 passed.
- **Conventions checked on the change's added lines:** all lines are within 100 columns. The one
  docstring is triple-double-quoted, and this run's test writes no string literal. Test functions
  carry no annotations, and the helpers are underscored.
- **Divergence recorded, not changed:** `from __future__ import annotations` (`conventions.md`
  § Typing) is not added to `test_separable.py`. `tl_instruction.md` § *Scope* forbids any new
  import beyond `Model`. Following it here would also be inert, because the file carries no
  annotations. I accept the developer's recorded divergences on `custom`/`cm` naming (the spec's own
  names) and on test location (the product's existing `tests/` tree, which the instruction names).

## Process notes

- I ran every check in the change's own product worktree or in a scratch folder outside both
  repositories. The scratch folder was removed afterwards. The product's main checkout was not
  touched (`CROSS_ROLE.md` § *Every seat*).
- Nothing outside the change request and the clone was read. I consulted no upstream history after
  `base_commit`, no pull request, no benchmark copy and no harness output
  (`system/projects/swe-benchmark-poc/doctrine/ai_responsibility.md` § 1.1).
