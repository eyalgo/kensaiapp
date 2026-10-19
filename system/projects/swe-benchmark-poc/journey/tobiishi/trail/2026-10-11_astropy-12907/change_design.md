# Change Design — `separability_matrix` and `is_separable` read a nested right-hand `&` operand correctly

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Publishes text:** no

---

## 1. Change Summary

The change touches one product module, `astropy/modeling/separable.py`, and one test file,
`astropy/modeling/tests/test_separable.py`. The defect sits in one branch of `_cstack`, the function
behind `&`. When the right-hand operand arrives as a matrix (line 245), its block is filled with `1`
instead of the operand's own values. The left-hand branch (line 240) already copies. `_separable`
hands `_cstack` a matrix for **every** operand, simple or compound, so this branch decides the
right-hand block of every `&` that the public functions evaluate. The fix makes the right-hand branch
mirror the left-hand one: the operand's own matrix is placed in its block, and the cross blocks stay
zero. `is_separable` reads the same `_separable` result, so CP-11 is fixed at the same site. The
public functions' special case for one input and several outputs (lines 57–59 and 97–99) lies
outside `_separable` and is not touched (CP-13).

Grouping invariance (CP-12) then holds **by construction**: both branches of `&` place an operand's
own matrix in its diagonal block, so the matrix of any `&` chain is the block-diagonal of its
operands' matrices, whatever the grouping. The design does not lean on test cases happening to agree.

That construction cannot meet CP-13's first bullet in full: some simple right-hand operands also
change. See `## Architect Review Notes`, item 1. Nothing is stored, collected, or sent anywhere. The
patch stays in the local clone (`project.md`, `Manages: none`).

---

## 2. Blast Radius

No `docs/SDD.md` § 3 parts table exists (the product carries no `docs/adr/`, `nfdr.md`, `fdr.md` or
`SDD.md`), so there is no placement to make. The module set is taken from the spec and the code. The
new logic is a corrected branch of existing logic, and it stays where that logic already lives.

| Module | Status | What changes |
|---|---|---|
| `astropy/modeling/separable.py` | Modified | `_cstack`: a right-hand operand given as a matrix keeps its own values in its block, as the left-hand branch already does. No signature, export or docstring contract changes. |
| `astropy/modeling/tests/test_separable.py` | Modified | New tests only (§5). Existing tests and the `compound_models` table are left unedited. |
| `astropy/modeling/core.py` (`_calculate_separability_matrix` hook, `CompoundModel`) | Unchanged | — read by `_separable` as today |
| `astropy/modeling/tests/test_models.py` | Unchanged | — `test_custom_separability_matrix` must keep passing (CP-13) |

**Transitive radius.** No public signature changes. Inside the repository, no module outside
`astropy/modeling/` calls `separability_matrix`, `is_separable` or `_separable`. The `is_separable`
in `astropy/visualization/wcsaxes/transforms.py` is an unrelated class attribute. So no other
in-repo module is affected. Outside the repository, callers such as GWCS see the corrected values.
The spec puts them out of scope, and they are named here only as radius.

**Values that change:** every `&` whose right-hand operand's own matrix is not all ones over its
block. That covers the spec's class (compound operands and hook operands, CP-10). It also covers the
simple operands in Review Note 1: a `Mapping`/`Identity` with more than one input, and a simple model
with `separable = True` and more than one input, such as the cylindrical projections
(`Pix2Sky_CAR`). Every other `&` keeps today's value, because there the copied matrix already equals
the all-ones block. That is every non-separable simple operand, and every operand with one input.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `separable.py` — `_cstack` right-hand matrix branch | Mirror the left-hand matrix branch: the operand's block, now anchored at the bottom-right, receives the operand's own matrix rather than a constant. The `Model` branches (reached only by direct calls such as `test_cstack`) are left as they are. |

---

## 5. Test Additions

All new tests go in `astropy/modeling/tests/test_separable.py`, the only file the card's
`Test command:` runs (spec, Locked Answer Gap 5). They are new functions or a new parametrized
table. The existing `compound_models` dict, `test_separable`, `test_custom_model_separable`,
`test_cstack` and the other private-helper tests stay unedited. The file needs a local test model
that supplies its own matrix: one input, one output, `_separable = False`, and a hook that returns
`[[0]]`, the `ModelCustom` shape. It is defined here rather than imported from another test module.
Below it is `custom`. The other names are the spec's Examples' names.

Each row is one of two kinds. A **regression** row fails on the unchanged tree and passes with the
change (CP-14). A **guard** row passes on both and stops the fix from going too far (CP-13). Each row
asserts the full `S` matrix and the full `I` array as literals. Where a row compares two groupings, it
asserts the literal and the equality both. An equality alone would also pass when both sides are wrong
in the same way.

| # | Kind | Test file | What to add |
|---|---|---|---|
| T1 | regression | `test_separable.py` | The issue's model `TAN & cm`: `S` = `[[T,T,F,F],[T,T,F,F],[F,F,T,F],[F,F,F,T]]` and `I` = `[F,F,T,T]`. This also proves CP-9's cross blocks are all `F`. |
| T2 | regression | `test_separable.py` | Deep and compound-left nesting. `S(sh1 & (sh2 & (scl1 & scl2)))` = 4×4 identity, `I` all `T`. `S((sh1 & sh2) & (scl1 & scl2))` = 4×4 identity, `I` all `T` (CP-10, "L can be any model"). |
| T3 | regression | `test_separable.py` | `S(rot & (sh1 & sh2))` = `[[T,T,F,F],[T,T,F,F],[F,F,T,F],[F,F,F,T]]`, `I` = `[F,F,T,T]`. |
| T4 | regression | `test_separable.py` | Hook operand on the right: `S(sh1 & custom)` = `[[T,F],[F,F]]`, `I` = `[T,F]`. In the same test, as guards: its mirror `S(custom & sh1)` = `[[F,F],[F,T]]` and `S(custom)` = `[[F]]`. |
| T5 | regression | `test_separable.py` | Nested `&` inside `\|` (CP-12). `Mapping((0,1,0,1)) \| (rot & (sh1 & sh2))`: `S` = `[[T,T],[T,T],[T,F],[F,T]]`, `I` = `[F,F,T,T]`, each equal to the flat `Mapping((0,1,0,1)) \| (rot & sh1 & sh2)`. `(sh1 & sh2 & sh1) \| (scl1 & (scl2 & scl1))`: `S` = 3×3 identity, `I` all `T`, each equal to the flat `(sh1 & sh2 & sh1) \| (scl1 & scl2 & scl1)`. |
| T6 | regression | `test_separable.py` | The resolution in Review Note 1, pinned. `S(sh1 & Identity(2))` = 3×3 identity, `I` all `T`, equal to its mirror `S(Identity(2) & sh1)`. `sh1 & (Identity(2) & sh2)` and `(sh1 & Identity(2)) & sh2` both give `S` = 4×4 identity and `I` all `T` (CP-12 with a simple multi-input middle operand). |
| T7 | regression | `test_separable.py` | Private helper at the defect site: `_cstack` of two 2×2 identity arrays = 4×4 identity, so the right-hand array's values are kept and the cross blocks are zero. The spec leaves private-helper tests to this stage (Out of Scope). |
| T8 | guard | `test_separable.py` | CP-10/CP-13 rows that must not move. `S(cm & TAN)` = `[[T,F,F,F],[F,T,F,F],[F,F,T,T],[F,F,T,T]]`. `S(sh1 & (rot \| rot))` = `[[T,F,F],[F,T,T],[F,T,T]]`. `S(sh1 & (sh2 \| scl1))` = `[[T,F],[F,T]]`. Flat `S(TAN & Linear1D(10) & Linear1D(5))` = `[[T,T,F,F],[T,T,F,F],[F,F,T,F],[F,F,F,T]]`. `S(sh1 & rot)` = `[[T,F,F],[F,T,T],[F,T,T]]`. `sh1 & Mapping((0,0))`: `S` = `[[T,F],[F,T],[F,T]]`, `I` = `[T,T,T]`. `Mapping((0,0))` alone: `S` = `[[T],[T]]`, `I` = `[F,F]`. |

**Spec Examples → rows.** CP-9 → T1. CP-10 `TAN & cm` → T1. `cm & TAN` → T8. Deep nesting → T2.
`rot & (sh1 & sh2)` → T3. `sh1 & custom` → T4. `sh1 & (rot | rot)` and `sh1 & (sh2 | scl1)` → T8.
CP-11 rows → T1, T2, T4. CP-12 rows → T5. CP-13 flat TAN chain, `sh1 & rot`, `sh1 & Mapping((0,0))`
and `Mapping((0,0))` alone → T8. `S(custom)` alone → T4. CP-13's existing tests, unedited → the
unchanged `compound_models`/`test_custom_model_separable` in this file, plus a separate run of
`astropy/modeling/tests/test_models.py::test_custom_separability_matrix`. The card's command does not
run that test, so the run has to be named. CP-14 → T1–T7 fail on the unchanged tree and pass with
the change. T8 passes on both. CP-15 → the card's `Test command:` exits 0 with the change.

**Rule-implied edges.** "L can be any model" (CP-10): compound L → T2 second case. Hook L → T4
mirror. Simple L → T1, T3. "L's block keeps today's value" (CP-10, CP-11) → T1–T4 assert the full
matrix and array, L's entries included. An R built with an arithmetic operator: its own matrix is
all ones, so its block cannot move. This is covered by the same reasoning as T8's `sh1 & (rot | rot)`
row and has no row of its own. "At any depth, including as an operand of another `&`" (CP-12) → T2
first case, T6. The one-input/many-output special case (CP-13) → T8 `Mapping((0,0))` alone.

**Assertions retired:** none. No existing test is edited or removed, so no clause stops being proved.

---

## Records this change makes false

None. The product carries no `docs/adr/`, `docs/nfdr.md`, `docs/fdr.md` or `docs/SDD.md`. What was
read: `change_spec.md`, `change_request.md`, `project.md`, and `astropy/modeling/separable.py`
(its module and function docstrings stay true). No record exists for anything to go false in. The
spec sentences this design narrows are listed under Review Notes 1, not here.

---

## Architect Review Notes

1. **(a) Contradiction resolved: CP-13's first bullet against CP-10 + CP-12, for a simple right-hand
   operand whose own matrix does not fill its block.** CP-13 bullet 1 keeps today's answer wherever
   every `&` has a simple right-hand operand without the hook. CP-12 requires `A & (B & C)` to equal
   `(A & B) & C`. CP-10 fixes the left side of that: B is on the left inside the compound `(B & C)`,
   so it reads as it does on the left. These cannot all hold when B is a `Mapping`/`Identity` with
   more than one input, or a simple model with `separable = True` and more than one input (the
   cylindrical and pseudo-cylindrical projections, such as `Pix2Sky_CAR`). This was run on
   2026-10-11 against the product change worktree, with an in-memory probe:
   `S(sh1 & (Identity(2) & sh2))` must be the 4×4 identity under CP-10. Today
   `S((sh1 & Identity(2)) & sh2)` = `[[T,F,F,F],[F,T,T,F],[F,T,T,F],[F,F,F,T]]`, which CP-13 bullet 1
   would freeze. No construction meets all three rules.
   **Resolved for CP-10/CP-12:** such an operand also reads, on the right, as it does on the left.
   For example `S(sh1 & Identity(2))` becomes the 3×3 identity, matching today's
   `S(Identity(2) & sh1)`. That is pinned by T6. The reasons:
   (i) The spec's own feasibility probe (Verified Claims, "CP-9 to CP-13 can all be met together")
   copied **every** right-hand matrix operand. That is exactly this construction, so the evidence the
   spec rests on is this resolution. Its pools held no simple operand with more than one input on the
   right, which is why the clash went unseen. Out of Scope admits that placement was "not examined".
   (ii) The spec's tie-breakers point the same way. Gap 1 reads "leave the rest as it is" as the
   rest of the *correct* behaviour. Gap 3 takes the left-hand reading as the reference. The docs say
   `&` concatenates outputs "without mixing in any way". Today's coupled right-hand
   `Identity(2)` mixes two outputs that are independent on the left.
   (iii) The other choice would keep the issue's complaint alive for these operands: flat and nested
   would disagree, which is the issue itself. It would also need code whose only job is to keep a
   wrong answer.
   No existing test asserts the old value; the spec's own probe ran `test_separable.py` and
   `test_custom_separability_matrix` green under this construction. **This narrows a PO rule and
   changes product behaviour beyond the spec's stated class. It is surfaced for the owner. If the
   owner prefers CP-13 bullet 1 kept literally, the spec has to go back, because CP-12 would then need
   narrowing, and that call is not this stage's.**
2. **(b) CP-12 realized by construction, not by coincidence.** Grouping invariance follows from both
   branches of `&` placing an operand's own matrix in its block (§1). The tests pin literal values and
   the flat/nested equality together (§5 preamble), so a fix that makes both groupings wrong in the
   same way still fails.
3. **(b) Private `Model` branches of `_cstack` left as they are.** `_separable` never passes a
   `Model` to `_cstack`. Those branches run only from direct calls (`test_cstack`). Leaving them
   unchanged keeps `test_cstack` unedited and its clauses proved. Unifying them is not this change.
4. **(b) No changelog fragment.** The request asks for none, and the spec neither asks for nor
   forbids one. The design adds none, so the patch touches only the module and its test file.
5. **Sweep for gates this stage owns:** none. With no `nfdr.md` and no `adr/`, no record names a
   `development-design` review.
