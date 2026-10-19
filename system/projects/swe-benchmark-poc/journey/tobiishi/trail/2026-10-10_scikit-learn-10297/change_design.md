# Change Design — RidgeClassifierCV accepts `store_cv_values` and keeps `cv_values_`

**Date:** 2026-10-10
**Category:** bug
**Behaviour:** changing
**Publishes text:** yes — the `RidgeClassifierCV` API reference (what `help(RidgeClassifierCV)` and the generated reference page show): the new `store_cv_values` entry under Parameters, and the `cv_values_` entry under Attributes

---

## 1. Change Summary

`RidgeClassifierCV`'s constructor does not accept `store_cv_values`, but the class it inherits from
already does everything else the spec asks for. `_BaseRidgeCV.__init__` stores the flag, and
`_BaseRidgeCV.fit` stores `cv_values_` when `cv=None`. With a `cv` set, `fit` raises
`ValueError("cv!=None and store_cv_values=True  are incompatible")`. The classifier's `__init__`
never passes the flag on, so the base always sees its default. The change adds `store_cv_values`
to `RidgeClassifierCV.__init__` as its last parameter, default `False`, and passes it to the base
constructor. It also brings the classifier's docstring into line (CP-16). No new logic is
added, and the shared base classes, `_RidgeGCV` and `RidgeCV` stay as they are. One product module
changes, `sklearn/linear_model/ridge.py`. The tests go in `sklearn/linear_model/tests/test_ridge.py`,
which the card's `Test command:` runs.

The three-dimensional shape that CP-11 fixes comes from what the classifier already does. It always
hands the base a two-dimensional target (see Architect Review Notes, *CP-11's shape by
construction*).

**What crosses to the outside: nothing.** The change stores nothing on a visitor's device, collects
nothing and sends nothing to a third party. The patch stays in the local clone (`project.md`,
`Manages: none`), so there is no release step to keep. The text it publishes is the scikit-learn
docstring inside that clone.

---

## 2. Blast Radius

The product has no parts table. `docs/SDD.md`, `docs/nfdr.md`, `docs/fdr.md` and `docs/adr/` do not
exist under the product worktree (`project.md`, `Definition: none`), so the code decides placement.
The parameter belongs to the class that the issue says rejects it. The logic it switches on
(storing, and refusing alongside a `cv`) already lives in `_BaseRidgeCV` and `_RidgeGCV`, and the
change reuses it there.

| Module | Status | What changes |
|---|---|---|
| `sklearn/linear_model/ridge.py` — `RidgeClassifierCV` | Modified | `__init__` gains `store_cv_values=False` after `class_weight` and passes it to `_BaseRidgeCV.__init__`. The docstring gains a `store_cv_values` entry under Parameters, and its `cv_values_` entry gives the shape `(n_samples, n_targets, n_alphas)` alone (CP-16). `fit` and `classes_` do not change. |
| `sklearn/linear_model/ridge.py` — `_BaseRidgeCV`, `_RidgeGCV`, `RidgeCV`, `Ridge`, `RidgeClassifier` | Unchanged | Already store the flag, store `cv_values_` and refuse it alongside a `cv`. Nothing about them changes (spec, Out of Scope). |
| `sklearn/linear_model/__init__.py` | Unchanged | Re-exports `RidgeClassifierCV` by name. The class's surface grows by one keyword argument with a default, and no call that works today changes meaning (CP-9). |
| `sklearn/utils/estimator_checks.py`, `sklearn/tests/test_common.py` | Unchanged | They build every estimator with its defaults and check `get_params` and `clone`. The new parameter is a `bool` default, stored under its own name by the base constructor, which is what those checks require. They are outside the card's `Test command:`. |
| `sklearn/linear_model/tests/test_ridge.py` | Modified | New tests. See §5. |

**Public surface.** `RidgeClassifierCV`'s signature gains one trailing keyword. `get_params()` gains
one key (CP-10). Every existing parameter keeps its name, default and position. No module in
`sklearn/` other than `__init__.py` and the test file imports the class (`grep -rn RidgeClassifierCV
sklearn`), so no other module is affected through an import.

---

## 3. Sub-jobs

Omitted. One product module is affected. Its two edits, the constructor and the docstring, sit in
one class, change for one reason and have no ordering edge between them.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `ridge.py` — `RidgeClassifierCV.__init__` takes and passes `store_cv_values` | Forward the flag to the base constructor's existing `store_cv_values` argument, the same way `alphas`, `cv` and the others are forwarded. Add no storing, reshaping or validation code to the classifier, and change neither `_BaseRidgeCV` nor `_RidgeGCV`. CP-11's shape, CP-12's selection, CP-13's equality and CP-15's refusal all come from the base path as it stands (Architect Review Notes). |
| `ridge.py` — `RidgeClassifierCV` docstring | None. The words come from `change_text.md`. They go into the existing numpydoc Parameters and Attributes sections, in the form of the entries around them. |

---

## 5. Test Additions

Every row is in `sklearn/linear_model/tests/test_ridge.py`, as new module-level `test_` functions.
That file already imports `RidgeClassifierCV`, `RidgeCV` and `make_multilabel_classification`.

| Sub-job | Test file | What to add / modify |
|---|---|---|
| `RidgeClassifierCV` | `tests/test_ridge.py` | **Construction (CP-9).** `RidgeClassifierCV(store_cv_values=True)` and `RidgeClassifierCV(store_cv_values=True, cv=2)` both construct without raising. The positional call `RidgeClassifierCV([0.1, 1.0], True, False, None, None, 'balanced')` gives `class_weight == 'balanced'` and `store_cv_values is False`. This fails on the unchanged tree, with the issue's `TypeError`. |
| `RidgeClassifierCV` | `tests/test_ridge.py` | **Parameters (CP-10).** `RidgeClassifierCV().get_params()` has exactly the keys `alphas, class_weight, cv, fit_intercept, normalize, scoring, store_cv_values`, with `store_cv_values` `False`. `clone(RidgeClassifierCV(store_cv_values=True)).get_params()['store_cv_values']` is `True`. `RidgeClassifierCV().set_params(store_cv_values=True).store_cv_values` is `True`. |
| `RidgeClassifierCV` | `tests/test_ridge.py` | **Shape (CP-11), `x` = the spec's 5×2 matrix, `alphas = [0.1, 1.0, 10.0]`.** With `store_cv_values=True`: `y = [1, 1, 1, -1, -1]` gives `cv_values_.shape == (5, 1, 3)`. `y = ['a', 'b', 'a', 'b', 'b']` gives `(5, 1, 3)`. `y = [0, 1, 2, 0, 1]` gives `(5, 3, 3)`. A 5-row, 3-column ±1 indicator `y` gives `(5, 3, 3)`. Every assertion checks `cv_values_.ndim == 3` as well as the shape. |
| `RidgeClassifierCV` | `tests/test_ridge.py` | **Shape (CP-11), 40×6 random `X`, 5 alphas.** One-class `y` (`np.ones(40)`) gives `(40, 1, 5)`. A single-column 2-D `y` with 3 classes gives `(40, 3, 5)`. A 4-class 1-D `y` gives `(40, 4, 5)`. A 2-column multilabel `y` from `make_multilabel_classification` gives `(40, 2, 5)`. For a two-class `y`, the shape is the same with `class_weight='balanced'`, with `normalize=True`, with a `sample_weight` and with `scoring='neg_mean_squared_error'` (CP-11's last sentence). |
| `RidgeClassifierCV` | `tests/test_ridge.py` | **The issue's own call (CP-11).** A 100×30 `X` from a seeded `RandomState`, `alphas=np.arange(0.1, 1000, 0.1)`, `normalize=True` and `store_cv_values=True`. (a) With `y > 0` from the issue's `y`, `cv_values_.shape == (100, 1, 9999)`. (b) With the issue's continuous `y` exactly as written, construction succeeds and `fit` raises `ValueError` whose message holds `Unknown label type`. This is the regression fence for Gap 2. |
| `RidgeClassifierCV` | `tests/test_ridge.py` | **Selection and equality (CP-12, CP-13).** For a two-class, a four-class and a multilabel `y` on the 40×6 `X`, with `scoring=None`: `alpha_ == alphas[argmin_i mean(cv_values_[:, :, i])]`. A classifier fitted with `store_cv_values=True` and one fitted with the default have equal `alpha_`, `coef_`, `intercept_` and `classes_`, and equal `predict` and `decision_function` output, on the training `X` and on a separate 7×6 `X`. Run the equality once more with a `sample_weight`. |
| `RidgeClassifierCV` | `tests/test_ridge.py` | **No values when not asked for (CP-14).** `RidgeClassifierCV(alphas=alphas).fit(x, y)` has no `cv_values_` attribute. `RidgeClassifierCV(alphas=alphas, cv=2).fit(...)` on `x` stacked twice (10 rows) has `alpha_` set and no `cv_values_`. Both pass today. They are fences against the change storing values unasked, not CP-17's proof. |
| `RidgeClassifierCV` | `tests/test_ridge.py` | **Refusal with a `cv` (CP-15).** `RidgeClassifierCV(alphas=alphas, store_cv_values=True, cv=2).fit(...)` on the same 10 rows raises `ValueError`. Its message holds both `cv` and `store_cv_values`. Assert on those two substrings, not on the whole message, because CP-15 does not fix the wording. Fails on the unchanged tree with `TypeError` at construction. |
| `RidgeClassifierCV` | `tests/test_ridge.py` | **Docstring (CP-16).** In `RidgeClassifierCV.__doc__`, the Parameters section holds an entry that begins with `store_cv_values`. The `cv_values_` entry's shape names `n_targets`, and it does not offer the two-dimensional alternative `[n_samples, n_alphas]`. The test checks those three tokens, which the spec fixes, and no wording around them. Fails on the unchanged tree. |

**Coverage map: every spec Example, and the rule-implied edges.**

- **CP-9:** all three Examples are in the construction row.
- **CP-10:** all three Examples are in the parameters row.
- **CP-11:**
  - The 5×2 Examples (two-class int, string, three-class, indicator) are in the first shape row.
  - The one-class, single-column three-class and `class_weight` / `normalize` / `sample_weight`
    Examples are in the 40×6 row.
  - The two issue-call Examples are in the issue row.
  - The spec's rule names the four-class, multilabel and `scoring` cases as well. They are also
    in the 40×6 row, so every part of CP-11's domain has a case.
- **CP-12, CP-13:** the selection and equality row.
- **CP-14:** both Examples are in the no-values row.
- **CP-15:** the refusal row.
- **CP-16:** the docstring row.
- **CP-17:** the construction, parameters, shape, issue, selection, refusal and docstring rows all
  construct with `store_cv_values` or read the new docstring. Each one fails on the unchanged tree.
  The CP-14 row passes on both trees and is a fence.
- **CP-18:** the card's `Test command:` checks it. No row is needed.
- **Rule-implied edges:**
  - `set_params` to `True` followed by a `cv` refusal is covered by the refusal row, because
    `fit` reads the attribute however it was set.
  - The empty-`cv_values_` case does not arise, because `alphas` and `X` are never empty in a fit
    the classifier accepts.
  - A tie in CP-12 is not given a case of its own. `numpy.argmin` returns the first index of the
    minimum, which is what the rule asks for, and the selection row checks the argmin itself.

**What the change stops proving.** Nothing. No existing assertion is modified or removed.
`test_ridgecv_store_cv_values` keeps proving that `RidgeCV.cv_values_` stays two-dimensional for
one-dimensional `y`, which the spec's Out of Scope keeps.

---

## Records this change makes false

None. The product has no decision records to read: `docs/adr/`, `docs/fdr.md`, `docs/nfdr.md` and
`docs/SDD.md` are absent under the product worktree (`project.md`, `Definition: none`). scikit-learn's
own documentation lives under `doc/`, which is not a record of this kind, and the spec's Verified
Claims found no mention of `store_cv_values` there. Nothing goes false.

---

## Architect Review Notes

- **Where the tests go (Gap 7, delegated here):** every new test goes into
  `sklearn/linear_model/tests/test_ridge.py`, as module-level `test_` functions beside
  `test_ridgecv_store_cv_values`. *Reason:* that file is the only one the card's `Test command:`
  runs. A test placed anywhere else would show nothing at the change's gate.
- **Reuse, not new logic:** the classifier passes the flag on and does nothing else with it. Storing,
  reshaping and refusing stay in `_BaseRidgeCV.fit` and `_RidgeGCV.fit`. *Reason:* that code already
  meets CP-11 to CP-15 for this classifier, as the spec's probe subclass showed. A second copy in
  the classifier could drift from `RidgeCV`'s. Changing the base would reach `RidgeCV`, whose
  behaviour the spec's Out of Scope keeps as it is.
- **CP-11's shape by construction:** `cv_values_` is three-dimensional for every `y` because the
  classifier always passes the base a two-dimensional target, never because of what a given `y`
  happens to look like. The target is `LabelBinarizer.fit_transform`'s output. That method's
  documented contract is `[n_samples, n_classes]`, `[n_samples, 1]` for binary problems, and dense
  under the default `sparse_output=False`. A multilabel indicator comes through it as a 2-D matrix.
  `_RidgeGCV.fit` reshapes a 2-D target's values to `(n_samples, n_y, n_alphas)`. The classifier
  adds no reshape of its own. *Reason:* the contract is the binarizer's documented one, not a
  coincidence of today's code. The one-class and two-class rows in §5 pin it. If either the
  binarizer or the base's 2-D branch changes, a test fails instead of a 2-D array coming back
  silently.
- **CP-12 and CP-13 by construction:** `_RidgeGCV.fit` computes the per-alpha values and picks
  `alpha_` whether or not the flag is set. With `scoring=None` the pick is the argmin of the
  per-alpha column means, and `numpy.argmin` takes the first index on a tie. The flag only gates the
  reshape and the assignment of `cv_values_`, after the model is chosen. The reshape is row-major
  and keeps alphas on the last axis, so the mean of `cv_values_[:, :, i]` is the column mean the
  pick used. *Reason:* this is why the design adds no code for either rule, and why §5 asserts
  them and does not build them.
- **CP-15 by reuse:** the refusal is `_BaseRidgeCV.fit`'s existing `ValueError`, whose message
  already names both `cv` and `store_cv_values`. The classifier does not catch it or re-raise it.
  *Reason:* the spec takes `RidgeCV`'s verdict as the model for CP-15, and keeping one raise site
  keeps the two classes' messages the same.
- **`Publishes text: yes`, and the form the words go into:** the docstring is what a user reads
  through `help()` and the API reference, so the change puts text in front of a person. The places
  are the two numpydoc entries named in the header. The design fixes only the tokens CP-16 fixes:
  the parameter name `store_cv_values`, `bool` with default `False`, the `cv=None` condition, and
  the shape `(n_samples, n_targets, n_alphas)`. The §5 docstring row tests those tokens and nothing
  else, so the wording stays the Content Editor's. The product has no `CONTENT.md`, and its existing
  docstrings, `RidgeCV`'s `store_cv_values` entry among them, are the standard around these words.
