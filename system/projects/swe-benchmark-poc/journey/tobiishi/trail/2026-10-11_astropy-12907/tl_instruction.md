# Tech Lead instruction — astropy-12907: `separability_matrix` and `is_separable` read a nested right-hand `&` operand correctly

**Category:** bug
**Behaviour:** changing
**Product root:** <the issue's clone>/.worktrees/2026-10-11_astropy-12907 — every path below is relative to it.
**Scope:** fix the right-hand matrix branch of `_cstack` in `astropy/modeling/separable.py`, and add tests for it to `astropy/modeling/tests/test_separable.py`. Nothing else is edited: no existing test, no docs, no changelog fragment, no new import, no new dependency.

---

## Project layout

```
astropy/modeling/
  separable.py                 ← modified (`_cstack` only)
  tests/
    test_separable.py          ← modified (new tests only; existing tests unedited)
```

No parts table — placement follows change_design.md §2. `astropy/modeling/core.py` and `astropy/modeling/tests/test_models.py` are not touched.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **No §3 in the design:** `change_design.md` has no § 3 Sub-jobs table (it jumps from §2 to §4). The only sub-job §4 names is the `_cstack` right-hand branch, so the plan has one task. The tests in §5 exist to prove that one change, so they ride that task, test-first.
- **Behaviour added (T7b):** `_cstack` of a 2×2 identity array with a non-square 3×2 array, `[[1,0],[0,1],[1,1]]`. T7 uses two square identities and cannot tell "copy the right-hand values into the bottom-right block" from "write a transposed or wrongly anchored block". T7b pins the bottom-right anchoring of a non-square right operand. Literal: a 5×4 array, rows `[1,0,0,0]`, `[0,1,0,0]`, `[0,0,1,0]`, `[0,0,0,1]`, `[0,0,1,1]`.
- **Gate added:** the design says `test_custom_separability_matrix` in `test_models.py` is not run by the card's `Test command:` and "the run has to be named" (§5). The Verification gate therefore has a second command. The card's command was run once at the base and gives `11 passed`, exit 0, so it is a working gate for the new tests.
- **Behaviour locked, carried from the design:** Architect Review Note 1 resolves a contradiction between CP-13 bullet 1 and CP-10/CP-12 for simple right-hand operands with more than one input (`Identity(2)`, `Mapping`, and `separable = True` models such as `Pix2Sky_CAR`). The plan follows the design: T6 pins it. That note says this narrows a PO rule beyond the spec's stated class and is surfaced for the owner. The plan does not decide it either way. If the owner keeps CP-13 bullet 1 literally, the spec goes back, and T6 and the `_cstack` branch must not be developed.
- **Hint carried, not extended:** the §4 hint is carried unchanged. The `Model` branches of `_cstack` stay as they are (Review Note 3).
- **Taste fence (strings):** the developer writes no public string. This change publishes no text (`Publishes text: no`), and no docstring or comment in `separable.py` is edited.
- **What the task may bring in:** no third-party origin, no device storage. The one import the tests may need beyond the file's existing ones is `Model` from `astropy.modeling`, for the local `custom` model; the developer flags it in Developer Review Notes.

## Corrections owed while there

- Owed outside this change's reach: none. `change_design.md` § *Records this change makes false* is "None", and the walk of `separable.py` found nothing else wrong.

### Task 1: `_cstack` keeps a right-hand matrix operand's own values (`astropy/modeling/separable.py`, `astropy/modeling/tests/test_separable.py`)

**Dependencies:** None

**What to build:** in `_cstack`, the branch that handles a right-hand operand arriving as an ndarray places that operand's own matrix in its bottom-right block, as the left-hand branch already does for its block. The cross blocks stay zero. The new tests are added to `test_separable.py` and run under the card's command.

#### Behaviours to verify (developer adds tests to `astropy/modeling/tests/test_separable.py`; existing tests stay unedited)

Each test asserts the full `S` matrix and the full `I` array as literals. Where it compares two groupings, it asserts the literal and the equality both. `T`/`F` are `True`/`False`, matrices are rows of outputs by columns of inputs. Names `sh1`, `sh2`, `scl1`, `scl2`, `rot` already exist in the file; `cm = Linear1D(10) & Linear1D(5)`, `TAN = Pix2Sky_TAN()`, `custom` is a local model with one input, one output, `_separable = False` and a hook returning `[[0]]` (the `ModelCustom` shape from `test_models.py`, defined in this file, not imported from that one).

Regression tests (red on the unchanged tree, green with the change):

- `test_nested_right_and_issue_model` (T1) — `S(TAN & cm)` = `[[T,T,F,F],[T,T,F,F],[F,F,T,F],[F,F,F,T]]` and `I(TAN & cm)` = `[F,F,T,T]`. The cross blocks are all `F` (CP-9).
- `test_nested_right_deep_and_compound_left` (T2) — `S(sh1 & (sh2 & (scl1 & scl2)))` is the 4×4 identity, `I` all `T`. `S((sh1 & sh2) & (scl1 & scl2))` is the 4×4 identity, `I` all `T`.
- `test_nested_right_rotation` (T3) — `S(rot & (sh1 & sh2))` = `[[T,T,F,F],[T,T,F,F],[F,F,T,F],[F,F,F,T]]`, `I` = `[F,F,T,T]`.
- `test_right_hand_custom_matrix` (T4) — `S(sh1 & custom)` = `[[T,F],[F,F]]`, `I` = `[T,F]`. In the same test, as guards: `S(custom & sh1)` = `[[F,F],[F,T]]` and `S(custom)` = `[[F]]`.
- `test_nested_and_inside_pipeline` (T5) — `Mapping((0,1,0,1)) | (rot & (sh1 & sh2))`: `S` = `[[T,T],[T,T],[T,F],[F,T]]`, `I` = `[F,F,T,T]`, each equal to the flat `Mapping((0,1,0,1)) | (rot & sh1 & sh2)`. `(sh1 & sh2 & sh1) | (scl1 & (scl2 & scl1))`: `S` is the 3×3 identity, `I` all `T`, each equal to the flat `(sh1 & sh2 & sh1) | (scl1 & scl2 & scl1)`.
- `test_simple_multi_input_right_operand_reads_as_on_the_left` (T6) — `S(sh1 & Identity(2))` is the 3×3 identity, `I` all `T`, equal to its mirror `S(Identity(2) & sh1)`. `sh1 & (Identity(2) & sh2)` and `(sh1 & Identity(2)) & sh2` both give the 4×4 identity for `S` and all `T` for `I`.
- `test_cstack_keeps_right_array_values` (T7) — `_cstack` of two 2×2 identity arrays is the 4×4 identity.
- `test_cstack_non_square_right_array` (T7b) — `_cstack` of a 2×2 identity array with `[[1,0],[0,1],[1,1]]` is the 5×4 array with rows `[1,0,0,0]`, `[0,1,0,0]`, `[0,0,1,0]`, `[0,0,0,1]`, `[0,0,1,1]`.

Guard tests (green on both trees; they stop the fix from going too far, CP-13):

- `test_right_operand_guards` (T8) — `S(cm & TAN)` = `[[T,F,F,F],[F,T,F,F],[F,F,T,T],[F,F,T,T]]`. `S(sh1 & (rot | rot))` = `[[T,F,F],[F,T,T],[F,T,T]]`. `S(sh1 & (sh2 | scl1))` = `[[T,F],[F,T]]`. Flat `S(TAN & Linear1D(10) & Linear1D(5))` = `[[T,T,F,F],[T,T,F,F],[F,F,T,F],[F,F,F,T]]`. `S(sh1 & rot)` = `[[T,F,F],[F,T,T],[F,T,T]]`. `sh1 & Mapping((0,0))`: `S` = `[[T,F],[F,T],[F,T]]`, `I` = `[T,T,T]`. `Mapping((0,0))` alone: `S` = `[[T],[T]]`, `I` = `[F,F]`.

Existing tests that must pass unedited (CP-13): the `compound_models` table and `test_custom_model_separable` in `test_separable.py`, `test_cstack` and the other private-helper tests in that file, and `astropy/modeling/tests/test_models.py::test_custom_separability_matrix`.

#### Implement

Infer from failing tests.

# Hint: Mirror the left-hand matrix branch: the operand's block, now anchored at the bottom-right, receives the operand's own matrix rather than a constant. The `Model` branches (reached only by direct calls such as `test_cstack`) are left as they are.

#### Verification gate

Run, from the product root:

1. `/home/kensai/issue-test.sh`
2. `/home/kensai/issue-venv/bin/python -m pytest astropy/modeling/tests/test_models.py::test_custom_separability_matrix`

Pass criteria: command 1 exits 0 with no failing test, and its run includes the new tests (the count rises from the base's `11 passed`). Command 2 reports `1 passed`. `git diff --stat` against the branch base names only `astropy/modeling/separable.py` and `astropy/modeling/tests/test_separable.py`, and the diff of the second has added lines only. On the unchanged tree the new regression tests T1–T7b fail and the guards T8 pass; this red is what the red commit shows.
