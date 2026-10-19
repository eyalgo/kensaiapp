# Change Spec — `separability_matrix` and `is_separable` read a nested right-hand `&` operand correctly

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Request:** "Fix the issue below in the product, the repository that the project card's
`Product path:` names (`astropy/astropy`). The repository stands at the commit before the issue was
fixed. Make the change the issue asks for, with tests of your own that show it, and leave the rest of
the product's behaviour as it is." The issue is `astropy__astropy-12907`, quoted in full in this
folder's `change_request.md` § *The issue*. Its constraints are that file's § *What must not be done*.

---

## Change Summary

`astropy.modeling.separable.separability_matrix` and `is_separable` get the right-hand operand of
`&` wrong when that operand is itself a compound model, or a model that supplies its own separability
matrix. They report every output of that operand as depending on every one of its inputs. So
`Pix2Sky_TAN() & (Linear1D(10) & Linear1D(5))` reports the two linear models as coupled, while the
same models written flat, `Pix2Sky_TAN() & Linear1D(10) & Linear1D(5)`, are reported as independent.
After this change a right-hand operand reads exactly as it does on the left-hand side, and the result
does not depend on how a chain of `&` is grouped.

**Terms used below.** For a model `L & R`, the outputs are L's outputs followed by R's, and the
inputs are L's inputs followed by R's (`docs/modeling/compound-models.rst`, *Model concatenation*).
`S(X)` is `separability_matrix(X)`, and `I(X)` is `is_separable(X)`. In `S(L & R)`, **R's block** is
the entries for R's outputs (rows) against R's inputs (columns), and **L's block** is the same for L.
The **cross blocks** are the entries that pair an output of one operand with an input of the other.
A **simple model** is a model that is not a `CompoundModel`. A model that **supplies its own
separability matrix** is one that implements the `_calculate_separability_matrix` hook, as
`docs/modeling/models.rst` § *Model Separability* documents it.

---

## Rules

### `&` — the cross blocks

- **CP-9:** In `S(L & R)` every entry of both cross blocks is `False`, whatever L and R are. That is
  what the docs say `&` does: it returns the two models' outputs "concatenated together, without mixing
  in any way" (`docs/modeling/compound-models.rst`, *Model concatenation*). This holds today and has to
  keep holding.

### `&` — a right-hand operand reads as it does on the left

- **CP-10:** Where R is a `CompoundModel` (built with any operator: `&`, `|`, `+`, `-`, `*`, `/`,
  `**`), or a model that supplies its own separability matrix, R's block in `S(L & R)` equals R's
  block in `S(R & L)`. L can be any model. In other words R's block does not depend on which side of
  `&` R stands on. L's block in `S(L & R)` keeps today's value. The rule exists because of a present
  defect: today R's block is all `True` for every such R, whatever R's own structure. The site is
  `astropy/modeling/separable.py` line 245, in `_cstack`, which sets a right-hand operand that is
  already a matrix to `1` instead of copying its values. The issue's case: `S(Pix2Sky_TAN() & cm)`,
  with `cm = Linear1D(10) & Linear1D(5)`, becomes
  `[[T, T, F, F], [T, T, F, F], [F, F, T, F], [F, F, F, T]]`. That is what the flat
  `Pix2Sky_TAN() & Linear1D(10) & Linear1D(5)` gives today.
- **CP-11:** For the same L and R as CP-10, the values `I(L & R)` gives for R's outputs equal the
  values `I(R & L)` gives for R's outputs. The values it gives for L's outputs keep today's values. For
  the issue's case, `I(Pix2Sky_TAN() & cm)` becomes `[False, False, True, True]`.

### Grouping does not change the answer

- **CP-12:** Take any model that contains an `&` sub-expression of the form `A & (B & C)`, at any
  depth, including inside a `|` pipeline or as an operand of another `&`. Regrouping it as
  `(A & B) & C` changes neither `S` nor `I` of the whole model. For example,
  `S(Mapping((0, 1, 0, 1)) | (Rotation2D(2) & (Shift(1) & Shift(2))))` equals
  `S(Mapping((0, 1, 0, 1)) | (Rotation2D(2) & Shift(1) & Shift(2)))`, and so does `I` of the two.

### Everything else keeps today's answer

- **CP-13:** Apart from CP-10 to CP-12, no output of `S` or `I` changes. In particular:
  - Where the right-hand operand of every `&` in a model is a simple model that does not supply its
    own separability matrix, `S` and `I` give today's answer. That covers every flat or left-grouped
    chain, such as `Pix2Sky_TAN() & Linear1D(10) & Linear1D(5)`.
  - A simple model's own `S` and `I` are unchanged. So is a model that supplies its own separability
    matrix, standing alone.
  - The special case for a model with one input and more than one output, where `S` reports every
    entry as `True` and `I` reports every output as `False`, stays as it is.
  - The other operators (`|`, `+`, `-`, `*`, `/`, `**`) give today's answer, except where one of
    their operands contains a nested `&` that CP-10 to CP-12 change.
  - The existing assertions on the public functions keep passing, unedited. These are the
    `compound_models` table in `test_separable`, the `test_custom_model_separable` test in the same
    file, and `test_custom_separability_matrix` in `astropy/modeling/tests/test_models.py`.

### Proof

- **CP-14:** The change carries tests of its own that the card's `Test command:` runs. They fail on
  the unchanged tree and pass with the change. Together they cover at least:
  - the issue's model `Pix2Sky_TAN() & (Linear1D(10) & Linear1D(5))`, checked with both
    `separability_matrix` and `is_separable`;
  - a `&` nested more than one level deep on the right, such as `Shift(1) & (Shift(2) & (Scale(1) & Scale(2)))`;
  - a nested right-hand `&` inside a `|` pipeline (CP-12);
  - a right-hand operand that supplies its own separability matrix (CP-10).
- **CP-15:** The card's `Test command:` exits 0, and its run has no failing test. The baseline is
  empty: `11 passed` at `base_commit`.

---

## Examples

`T`/`F` stand for `True`/`False`. Matrices are written row by row: outputs are rows and inputs are
columns. `cm = Linear1D(10) & Linear1D(5)`. `sh1 = Shift(1)`, `sh2 = Shift(2)`, `scl1 = Scale(1)`,
`scl2 = Scale(2)`, `rot = Rotation2D(2)`, and `TAN = Pix2Sky_TAN()`, all from `astropy.modeling.models`.
`custom` is a model with one input and one output, `_separable = False`, whose hook returns
`[[0]]`. That is the `ModelCustom` shape in `astropy/modeling/tests/test_models.py`. "Today" was run on
2026-10-11 (see Verified Claims).

| Rule | Scenario | Today | Expected behavior |
|---|---|---|---|
| CP-9 | `S(TAN & cm)`: the cross blocks (rows 0–1 × cols 2–3, rows 2–3 × cols 0–1) | all `F` | all `F` |
| CP-10 | `S(TAN & cm)` (the issue's nested model) | `[[T,T,F,F],[T,T,F,F],[F,F,T,T],[F,F,T,T]]` | `[[T,T,F,F],[T,T,F,F],[F,F,T,F],[F,F,F,T]]` |
| CP-10 | `S(cm & TAN)`, the same compound on the left | `[[T,F,F,F],[F,T,F,F],[F,F,T,T],[F,F,T,T]]` | unchanged |
| CP-10 | `S(sh1 & (sh2 & (scl1 & scl2)))` | `[[T,F,F,F],[F,T,T,T],[F,T,T,T],[F,T,T,T]]` | the 4×4 identity: `T` on the diagonal, `F` elsewhere |
| CP-10 | `S(rot & (sh1 & sh2))` | `[[T,T,F,F],[T,T,F,F],[F,F,T,T],[F,F,T,T]]` | `[[T,T,F,F],[T,T,F,F],[F,F,T,F],[F,F,F,T]]` |
| CP-10 | `S(sh1 & custom)` (R supplies its own matrix) | `[[T,F],[F,T]]` | `[[T,F],[F,F]]`, the mirror of today's `S(custom & sh1)` = `[[F,F],[F,T]]` |
| CP-10 | `S(sh1 & (rot \| rot))` (R's own block is all `T`) | `[[T,F,F],[F,T,T],[F,T,T]]` | unchanged |
| CP-10 | `S(sh1 & (sh2 \| scl1))` (R has one output and one input) | `[[T,F],[F,T]]` | unchanged |
| CP-11 | `I(TAN & cm)` | `[F,F,F,F]` | `[F,F,T,T]` |
| CP-11 | `I(sh1 & (sh2 & (scl1 & scl2)))` | `[T,F,F,F]` | `[T,T,T,T]` |
| CP-11 | `I(sh1 & custom)` | `[T,T]` | `[T,F]` |
| CP-12 | `S`/`I` of `Mapping((0,1,0,1)) \| (rot & (sh1 & sh2))` | `[[T,T],[T,T],[T,T],[T,T]]` / `[F,F,F,F]` | `[[T,T],[T,T],[T,F],[F,T]]` / `[F,F,T,T]`, equal to the flat `Mapping((0,1,0,1)) \| (rot & sh1 & sh2)` today |
| CP-12 | `S`/`I` of `(sh1 & sh2 & sh1) \| (scl1 & (scl2 & scl1))` | `[[T,F,F],[F,T,T],[F,T,T]]` / `[T,F,F]` | the 3×3 identity / `[T,T,T]`, equal to the flat `(sh1 & sh2 & sh1) \| (scl1 & scl2 & scl1)` today |
| CP-13 | `S(TAN & Linear1D(10) & Linear1D(5))` (flat) | `[[T,T,F,F],[T,T,F,F],[F,F,T,F],[F,F,F,T]]` | unchanged |
| CP-13 | `S(sh1 & rot)` (simple R) | `[[T,F,F],[F,T,T],[F,T,T]]` | unchanged |
| CP-13 | `S`/`I` of `sh1 & Mapping((0,0))` (simple R) | `[[T,F],[F,T],[F,T]]` / `[T,T,T]` | unchanged |
| CP-13 | `S`/`I` of `Mapping((0,0))` alone (one input, two outputs) | `[[T],[T]]` / `[F,F]` | unchanged |
| CP-13 | `S(custom)` alone | `[[F]]` | unchanged |
| CP-13 | the six `compound_models` rows and `test_custom_model_separable` in `test_separable`, and `test_custom_separability_matrix` in `test_models.py` | pass | pass, unedited |
| CP-14 | the change's own tests, run on the unchanged tree | — | they fail |
| CP-14 | the change's own tests, run with the change | — | they pass |
| CP-15 | the card's `Test command:` run with the change | exit 0, `11 passed` | exit 0, no failing test |

---

## Verified Claims

All runs were made on 2026-10-11 against the product's change worktree for this key. That worktree is
opened from the repository the card's `Product path:` names, at `HEAD` `d16bfe05a744909de4b27f5875fe0d4ed41ce607`,
with no change applied. They used the card's interpreter (`/home/kensai/issue-venv/bin/python`, Python
3.9.25, NumPy 1.25.2), whose editable install of astropy resolves to that worktree. The probe scripts
lived in a scratch folder outside both repositories. The product worktree's `git status --short` was
empty after every run. Nothing outside the repository was consulted: no upstream history after this
commit, no pull request, no issue thread and no benchmark copy.

| Claim | Verified by | What came back |
|---|---|---|
| Every "Today" cell in the Examples table | ran `separability_matrix` and `is_separable` on each row's model | each value as written in the table |
| Today a nested right-hand operand reads wrong across the board, and a left-hand one reads right | ran a pool of 18 left operands (6 simple, 12 compound or hook) against 12 compound or hook right operands, and checked CP-9, CP-10 and CP-11 on each pair | 126 of 216 pairs violate CP-10 or CP-11. None violates CP-9 |
| Today regrouping changes the answer | ran CP-12 on every `A & (B & C)` drawn from a pool of 5 (`sh1`, `rot`, `TAN`, `sh1 & sh2`, `custom`), alone and behind an identity `Mapping` pipeline | 250 of 250 regroupings differ |
| The cause is at `astropy/modeling/separable.py` line 245 | read `_cstack` (lines 219–247): a left-hand matrix operand is copied (line 240). A right-hand one has its region set to `1` (line 245) | confirmed |
| CP-9 to CP-13 can all be met together, without editing an existing test | scratch probe, not a design. In memory only, it replaced `_cstack` so that a right-hand matrix operand keeps its own values. Then it re-ran the pair and regrouping checks above, every Expected cell, and pytest on `test_separable.py` plus `test_models.py::test_custom_separability_matrix` (`-p` plugin, nothing written to the tree) | 0 of 216 pairs and 0 of 250 regroupings violate the rules. Every Expected cell matched. `12 passed` |
| The card's `Test command:` passes at base with no failure | ran `/home/kensai/issue-test.sh` from the product worktree root. It runs `pytest` on `astropy/modeling/tests/test_separable.py` only | `11 passed`, exit 0. `/home/kensai/issue-baseline.txt` is empty |
| `test_custom_separability_matrix` passes at base | ran it with pytest | `1 passed` |
| The hook is a documented extension point | read `docs/modeling/models.rst` lines 744–747 and `docs/changes/modeling/12900.feature.rst` | both describe `_calculate_separability_matrix` as the way a `Model` subclass supplies its own separability matrix |
| No doc page or docstring shows the output for a nested right-hand `&` | `grep -rn "separability_matrix\|is_separable"` over `docs/` and `astropy/` (tests and `separable.py` excluded), and read the docstring examples in `separable.py` lines 43–55 and 83–95, which are all left-grouped | none found |

---

## Out of Scope

- **Simple right-hand operands.** A right-hand operand that is a simple model without the hook keeps
  today's answer (CP-13). That holds even for a simple model that declares `separable = True` with more
  than one input, whose placement on the right this spec did not examine.
- **The special case for one input and more than one output** (CP-13). This spec does not decide
  whether that convention should also hold for such a model nested inside a compound.
- **The other operators' own rules.** `|` and the arithmetic operators are not changed, apart from
  what a nested `&` inside them contributes.
- **The private helpers' unit tests** (`test_coord_matrix`, `test_cdot`, `test_cstack`,
  `test_arith_oper`). The spec pins the public functions only. Whether those tests change is
  development-design's decision, within CP-15.
- **Documentation and changelog.** The request asks for none. No doc page shows the corrected output
  (Verified Claims). This spec neither asks for nor forbids a `docs/changes/` fragment. Other surfaces
  were not looked at: downstream users of these functions, such as GWCS, and astropy's own
  coordinate or WCS code.
- **Anything outside the local clone.** The patch is not pushed (`project.md`, `Manages: none`).
  Per the request, no record, grade or benchmark file is produced.

---

## Locked Answers (the divergence record — self-review 2026-10-11)

- **Gap 1 — `is_separable` is fixed too (CP-11).** The issue names only `separability_matrix`.
  `is_separable` gives the same wrong answer for the issue's model: today `[F,F,F,F]`, where the flat
  form gives `[F,F,T,T]`. Fixing one and leaving the other would leave two public functions of the same
  module disagreeing about one model. The request's "leave the rest as it is" is read as the rest of
  the product's *correct* behaviour.
- **Gap 2 — models that supply their own matrix are in the class (CP-10).** The issue names nested
  compound models. A right-hand operand that uses the documented hook is misread the same way: today
  `S(sh1 & custom)` reports `custom`'s output as depending on its input, though `custom` says it does
  not. Its mirror `S(custom & sh1)` already reads it right. The rule is keyed to the class "a right-hand
  operand whose answer is not just its `separable` flag". A list of the issue's cases would have left
  this member undecided.
- **Gap 3 — the reference is the same operand on the left, not `S(R)` on its own (CP-10, CP-11).** A
  simpler rule would say "R's block equals `S(R)`". The two differ for a model with one input and more
  than one output: alone, `S` reports it all `True` and `I` all `False`, a convention the left-hand side
  does not apply inside a compound. Taking the left-hand reading as the reference changes only what the
  issue reports, and it fits the docs' "without mixing in any way". The other rule would also move that
  convention, which nothing asked for.
- **Gap 4 — grouping invariance at any depth (CP-12).** The issue shows a nested `&` at the top level.
  The same model sitting inside a `|` pipeline, or nested deeper, is wrong today for the same reason
  (Examples, CP-12 rows). A fix that held only at the top level would leave the issue's model wrong as
  soon as it is used in a pipeline. That is the ordinary way such a model is used.
- **Gap 5 — the change's tests run under the card's `Test command:`, and existing public assertions
  stay unedited (CP-13, CP-14, CP-15).** The request asks for "tests of your own" and does not say
  where they run. The card's command runs only `astropy/modeling/tests/test_separable.py`, so a test
  outside that file shows nothing at the change's gate. The public-function assertions stay unedited,
  because otherwise a red test could be "fixed" by rewriting what it expects. Where the tests go within
  that file is development-design's decision.
