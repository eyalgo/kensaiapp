# Tech Lead instruction — scikit-learn-10297: RidgeClassifierCV accepts `store_cv_values` and keeps `cv_values_`

**Category:** bug
**Behaviour:** changing
**Product root:** <the issue's clone>/.worktrees/2026-10-10_scikit-learn-10297 — every path below is relative to it.
**Scope:** `RidgeClassifierCV.__init__` gains `store_cv_values=False` (last parameter) and forwards it to `_BaseRidgeCV`; the class docstring is brought into line (CP-16); new tests go in `sklearn/linear_model/tests/test_ridge.py`. No storing, reshaping or validation logic is added anywhere.

---

## Project layout

```
sklearn/
  linear_model/
    ridge.py                 ← modified (RidgeClassifierCV only)
    tests/
      test_ridge.py          ← modified (new module-level test_ functions)
```

No parts table — placement follows change_design.md §2. No directories or `__init__.py` files are created.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **Task split:** the design omits §3 (one module). Its two edits are different in kind: the constructor is code with a hint, the docstring is published text whose words the developer does not write (`Publishes text: yes`). They have no atomic-landing edge, so they are Task 1 (constructor) and Task 2 (docstring). Reason: separate responsibilities, each independently red-then-green, and the docstring task can carry the "no string the instruction did not supply" rule on its own.
- **Words are not supplied here:** Task 2 supplies tokens only (CP-16's fixed ones). Every sentence comes from `change_text.md`, verbatim. A string the developer adds beyond it is an unapproved addition. Reason: public text about the product is not the developer's to write.
- **Third-party origins and device storage:** every task may introduce none. The change touches a Python class and its tests; nothing is fetched, stored or sent.
- **Fence tests marked as passing today:** the design's CP-14 row passes on the unchanged tree. It sits in Task 1 with an explicit note so the developer does not treat a green result as a missed red. The remaining behaviours in Task 1 do fail today, so the task stays test-first.
- **Test helper added:** `clone` is not imported in `test_ridge.py` (checked). The CP-10 behaviour needs `sklearn.base.clone`; the developer adds that import. Reason: implied by the design's §5 and absent from the file.
- **Hint carried verbatim in substance:** the §4 hint for the constructor is carried as a `# Hint:` block. §4's docstring row reads `None`, so Task 2 carries no hint.
- **Gate command:** `/home/kensai/issue-test.sh` was read against the spec's Verified Claims (it runs `sklearn/linear_model/tests/test_ridge.py`, empty baseline, `28 passed, 1 xfailed` at base). It runs what the spec measured, so it is used unchanged.

## Corrections owed while there

- `sklearn/linear_model/ridge.py:1306-1311` — the `cv_values_` Attributes entry refers to a parameter the constructor rejects, offers `[n_samples, n_alphas]`, and its continuation lines are mis-indented → replaced by the CP-16 text. Rides Task 2 (that task already opens this file).

---

### Task 1: RidgeClassifierCV constructor takes and forwards `store_cv_values` (`sklearn/linear_model/ridge.py`, `sklearn/linear_model/tests/test_ridge.py`)

**Dependencies:** None

**What to build:** `RidgeClassifierCV.__init__` accepts `store_cv_values` (bool, default `False`) as its last parameter, after `class_weight`, and passes it on to the base constructor. Nothing else about the class changes. May introduce no third-party origin and no device storage.

#### Behaviours to verify (developer adds tests to `sklearn/linear_model/tests/test_ridge.py`, as new module-level `test_` functions beside `test_ridgecv_store_cv_values`)

Construction (CP-9)
- `test_ridgeclassifiercv_accepts_store_cv_values` — `RidgeClassifierCV(store_cv_values=True)` and `RidgeClassifierCV(store_cv_values=True, cv=2)` both construct without raising.
- `test_ridgeclassifiercv_positional_args_keep_meaning` — `RidgeClassifierCV([0.1, 1.0], True, False, None, None, 'balanced')` has `class_weight == 'balanced'` and `store_cv_values is False`.

Parameters (CP-10)
- `test_ridgeclassifiercv_get_params_has_store_cv_values` — `get_params()` has exactly the keys `alphas, class_weight, cv, fit_intercept, normalize, scoring, store_cv_values`, with `store_cv_values` `False` by default.
- `test_ridgeclassifiercv_clone_keeps_store_cv_values` — `clone(RidgeClassifierCV(store_cv_values=True)).get_params()['store_cv_values']` is `True`. (Add `from sklearn.base import clone`.)
- `test_ridgeclassifiercv_set_params_store_cv_values` — `RidgeClassifierCV().set_params(store_cv_values=True).store_cv_values` is `True`.

Shape (CP-11), `x` = `[[-1, -1], [-1, 0], [-0.8, -1], [1, 1], [1, 0]]`, `alphas = [0.1, 1.0, 10.0]`, `store_cv_values=True`; every assertion also checks `cv_values_.ndim == 3`
- `test_cv_values_shape_two_class_int` — `y = [1, 1, 1, -1, -1]` gives `(5, 1, 3)`.
- `test_cv_values_shape_two_class_string` — `y = ['a', 'b', 'a', 'b', 'b']` gives `(5, 1, 3)`.
- `test_cv_values_shape_three_class` — `y = [0, 1, 2, 0, 1]` gives `(5, 3, 3)`.
- `test_cv_values_shape_indicator_matrix` — a 5-row, 3-column ±1 indicator `y` gives `(5, 3, 3)`.

Shape (CP-11), 40×6 random `X` from a seeded `RandomState`, 5 alphas
- `test_cv_values_shape_one_class` — `y = np.ones(40)` gives `(40, 1, 5)`.
- `test_cv_values_shape_single_column_y` — a single-column 2-D `y` with 3 classes gives `(40, 3, 5)`.
- `test_cv_values_shape_four_class` — a 4-class 1-D `y` gives `(40, 4, 5)`.
- `test_cv_values_shape_multilabel` — a 2-column `y` from `make_multilabel_classification` gives `(40, 2, 5)`.
- `test_cv_values_shape_unchanged_by_options` — for a two-class `y`, the shape is `(40, 1, 5)` with `class_weight='balanced'`, with `normalize=True`, with a `sample_weight`, and with `scoring='neg_mean_squared_error'`.

The issue's own call (CP-11): 100×30 `X` from a seeded `RandomState`, `alphas=np.arange(0.1, 1000, 0.1)`, `normalize=True`, `store_cv_values=True`
- `test_issue_call_two_class_y_stores_values` — with `y > 0` from the issue's `y`, `cv_values_.shape == (100, 1, 9999)`.
- `test_issue_call_continuous_y_still_rejected_at_fit` — with the issue's continuous `y` exactly as written, construction succeeds and `fit` raises `ValueError` whose message holds `Unknown label type`. (Regression fence for spec Gap 2.)

Selection and equality (CP-12, CP-13), 40×6 `X`, `scoring=None`
- `test_alpha_is_argmin_of_mean_cv_values` — for a two-class, a four-class and a multilabel `y`, `alpha_ == alphas[argmin_i mean(cv_values_[:, :, i])]`.
- `test_storing_cv_values_does_not_change_model` — a classifier fitted with `store_cv_values=True` and one with the default have equal `alpha_`, `coef_`, `intercept_` and `classes_`, and equal `predict` and `decision_function` output on the training `X` and on a separate 7×6 `X`. Repeat once with a `sample_weight`.

No values when not asked for (CP-14) — **these pass on the unchanged tree; they are fences against storing unasked, not the red proof**
- `test_no_cv_values_by_default` — `RidgeClassifierCV(alphas=alphas).fit(x, y)` has no `cv_values_` attribute.
- `test_no_cv_values_with_cv_set` — `RidgeClassifierCV(alphas=alphas, cv=2).fit(...)` on `x` stacked twice (10 rows) has `alpha_` set and no `cv_values_`.

Refusal with a `cv` (CP-15)
- `test_store_cv_values_with_cv_refused_at_fit` — `RidgeClassifierCV(alphas=alphas, store_cv_values=True, cv=2).fit(...)` on the same 10 rows raises `ValueError`; its message holds both `cv` and `store_cv_values`. Assert on those two substrings, not the whole message.

#### Held by review

- No storing, reshaping or validation code is added to `RidgeClassifierCV`, and `_BaseRidgeCV`, `_RidgeGCV`, `RidgeCV` stay unchanged — no test can see that the work was not duplicated; it is held by reading the diff.
- CP-11's "always 3-D" comes from the classifier always handing the base a 2-D target; the one-class and two-class rows pin it.

#### Implement

Infer from failing tests.

# Hint: forward the flag to the base constructor's existing `store_cv_values` argument, the same way `alphas`, `cv` and the others are forwarded. Add no storing, reshaping or validation code to the classifier, and change neither `_BaseRidgeCV` nor `_RidgeGCV`. CP-11's shape, CP-12's selection, CP-13's equality and CP-15's refusal all come from the base path as it stands.

#### Verification gate

Run `/home/kensai/issue-test.sh` (from the product root).

Pass criteria: exit 0; the new tests pass; no test that passed before fails; `test_ridgecv_store_cv_values` and the xfailed test are untouched. Every new test except the two CP-14 fences fails on the unchanged tree.

---

### Task 2: RidgeClassifierCV docstring agrees with the new parameter (`sklearn/linear_model/ridge.py`, `sklearn/linear_model/tests/test_ridge.py`)

**Dependencies:** None

**What to build:** the `RidgeClassifierCV` docstring gains a `store_cv_values` entry under Parameters and a corrected `cv_values_` entry under Attributes, in the numpydoc form of the entries around them. Every sentence is copied verbatim from `change_text.md`. A string not in `change_text.md` is an unapproved addition; if a string cannot be placed as written, record it in Developer Review Notes and do not reword it. May introduce no third-party origin and no device storage.

#### Behaviours to verify (developer adds the test to `sklearn/linear_model/tests/test_ridge.py`)

- `test_ridgeclassifiercv_docstring_documents_store_cv_values` — in `RidgeClassifierCV.__doc__`: the Parameters section holds an entry that begins with `store_cv_values`; the `cv_values_` entry's shape names `n_targets`; and it does not offer the two-dimensional alternative `[n_samples, n_alphas]`. Check those three tokens and no wording around them. Fails on the unchanged tree.

#### Implement

Infer from failing tests.

#### Verification gate

Run `/home/kensai/issue-test.sh` (from the product root).

Pass criteria: exit 0; the docstring test passes; no new failures elsewhere; every docstring sentence in the diff appears in `change_text.md`.
