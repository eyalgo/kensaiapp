# Change Spec — RidgeClassifierCV accepts `store_cv_values` and keeps `cv_values_`

**Date:** 2026-10-10
**Category:** bug
**Behaviour:** changing
**Request:** "Fix the issue below in the product, the repository that the project card's
`Product path:` names (`scikit-learn/scikit-learn`). The repository stands at the commit before the
issue was fixed. Make the change the issue asks for, with tests of your own that show it, and leave
the rest of the product's behaviour as it is." The issue is `scikit-learn__scikit-learn-10297`, quoted
in full in this folder's `change_request.md` § *The issue*. Its constraints are that file's § *What
must not be done*.

---

## Change Summary

`sklearn.linear_model.RidgeClassifierCV` documents a `cv_values_` attribute that is set "if
`store_cv_values=True` and `cv=None`". But its constructor rejects `store_cv_values` with
`TypeError: __init__() got an unexpected keyword argument 'store_cv_values'`. After this change the
classifier accepts the parameter. With `store_cv_values=True` and `cv=None`, a fitted classifier keeps
the cross-validation values in `cv_values_`. With `store_cv_values=True` and a `cv`, `fit` refuses.
Nothing else about the classifier changes.

**Terms used below.** `n_samples` is the number of rows of `X` passed to `fit`. `n_alphas` is
`len(alphas)`. `n_targets` is the number of columns the classifier fits one per, as set out in CP-11.
"Today" means the product at `base_commit`, with no change applied.

---

## Rules

### Constructing the classifier

- **CP-9:** `RidgeClassifierCV` takes a keyword parameter `store_cv_values`, a boolean, default
  `False`. Constructing it with `store_cv_values=True` or `store_cv_values=False` raises nothing,
  whatever `cv` is. The existing parameters `alphas`, `fit_intercept`, `normalize`, `scoring`, `cv`
  and `class_weight` keep their names, defaults and positional order. `store_cv_values` comes after
  `class_weight`, so a call that passed arguments by position before the change means the same
  thing after it.
- **CP-10:** `get_params()` on a `RidgeClassifierCV` includes the key `store_cv_values`, with the value
  passed to the constructor, or `False` when none was passed. `set_params(store_cv_values=<bool>)`
  changes it, and `sklearn.base.clone` carries it over to the clone.

### Fitting with `store_cv_values=True` and `cv=None`

- **CP-11:** After `fit` returns, the classifier has an attribute `cv_values_`. It is a NumPy array of
  shape `(n_samples, n_targets, n_alphas)`, always three-dimensional. The domain is every `y` that
  `fit` accepts today, and `n_targets` is set for each part of it:
  - `y` with one class or two classes, of any label type (integers, strings): `n_targets = 1`;
  - one-dimensional `y`, or a single-column `y`, with more than two classes: `n_targets` is the
    number of classes;
  - `y` as a 2-D multilabel indicator matrix: `n_targets` is the number of its columns.

  A `y` that `fit` rejects today (e.g. continuous values) is still rejected, as today (see Locked
  Answers, Gap 2). Passing `class_weight`, `sample_weight` or `normalize=True` does not change the
  shape. With `scoring` set, the shape is the same.
- **CP-12:** With `scoring=None`, the values in `cv_values_` are the errors the classifier chooses
  `alpha_` by. For each `alphas` entry, take the mean of its `cv_values_[:, :, i]` slice. `alpha_` is
  the `alphas` entry whose mean is lowest; on a tie, it is the first such entry in `alphas`. With
  `scoring` set, this change does not fix the values (see Out of Scope).
- **CP-13:** Storing the values does not change the model. Take a classifier fitted with
  `store_cv_values=True` and one fitted with `store_cv_values=False`, with the same other parameters,
  on the same `X`, `y` and `sample_weight`. They have equal `alpha_`, `coef_`, `intercept_` and
  `classes_`, and `predict` and `decision_function` give equal output on any `X`.

### Fitting with `store_cv_values=False`

- **CP-14:** A classifier fitted with `store_cv_values=False`, set explicitly or left at the default,
  has no attribute `cv_values_`, whatever `cv` is. That is what happens today for every fitted
  `RidgeClassifierCV`.

### `store_cv_values=True` together with a `cv`

- **CP-15:** With `store_cv_values=True` and `cv` not `None`, construction raises nothing (CP-9), and
  `fit` raises `ValueError`. Its message names both `cv` and `store_cv_values` and says that they
  cannot be used together. `RidgeCV` gives this verdict today, with the message
  `cv!=None and store_cv_values=True  are incompatible`. A message of that kind meets this rule, but
  the exact wording is not fixed here.

### Documentation

- **CP-16:** The classifier's docstring agrees with what CP-9 to CP-15 make true. Its Parameters
  section lists `store_cv_values` as a boolean, default `False`. It says that the parameter makes `fit`
  store the cross-validation values for each alpha in `cv_values_`, and that it works only with
  `cv=None`. Its `cv_values_` entry gives the shape CP-11 fixes, `(n_samples, n_targets, n_alphas)`.
  It gives no shape the classifier does not produce. This rule exists because of two present defects.
  Today the `cv_values_` entry (`sklearn/linear_model/ridge.py` lines 1306–1309) refers to
  `store_cv_values=True`, which the constructor at line 1335 rejects. The same entry also lists
  `[n_samples, n_alphas]`, a two-dimensional shape that, once the parameter is accepted, the
  classifier never produces (Verified Claims).

### Proof

- **CP-17:** The change carries tests of its own that the card's `Test command:` runs. They fail on the
  unchanged tree and pass with the change. Together they cover at least:
  - constructing `RidgeClassifierCV(store_cv_values=True)`, the issue's `TypeError`;
  - the shape of `cv_values_` for a two-class `y` and for a `y` with more than two classes or a
    multilabel `y` (CP-11);
  - `fit` raising `ValueError` when `store_cv_values=True` and `cv` is not `None` (CP-15).
- **CP-18:** The card's `Test command:` exits 0 with the change. Its baseline is empty: today it
  reports `28 passed, 1 xfailed`. With the change, no test that passes today fails, and the xfailed
  test is not touched.

---

## Examples

`x` is `[[-1, -1], [-1, 0], [-0.8, -1], [1, 1], [1, 0]]` and `alphas` is `[0.1, 1.0, 10.0]` unless a
row says otherwise. Every row's "Expected" column was produced by running the scratch probe described
under Verified Claims.

| Rule | Scenario | Today | Expected behavior |
|---|---|---|---|
| CP-9 | `RidgeClassifierCV(store_cv_values=True)` | `TypeError: __init__() got an unexpected keyword argument 'store_cv_values'` | constructs, raises nothing |
| CP-9 | `RidgeClassifierCV(store_cv_values=True, cv=2)` | `TypeError` | constructs, raises nothing |
| CP-9 | `RidgeClassifierCV([0.1, 1.0], True, False, None, None, 'balanced')` (positional) | `class_weight == 'balanced'` | `class_weight == 'balanced'`, `store_cv_values == False` |
| CP-10 | `RidgeClassifierCV().get_params()` | keys `alphas, class_weight, cv, fit_intercept, normalize, scoring` | the same keys plus `store_cv_values: False` |
| CP-10 | `clone(RidgeClassifierCV(store_cv_values=True)).get_params()['store_cv_values']` | `TypeError` | `True` |
| CP-10 | `RidgeClassifierCV().set_params(store_cv_values=True).store_cv_values` | — | `True` |
| CP-11 | fit with `store_cv_values=True` on `x`, `y = [1, 1, 1, -1, -1]` | `TypeError` | `cv_values_.shape == (5, 1, 3)` |
| CP-11 | the same, `y = ['a', 'b', 'a', 'b', 'b']` | `TypeError` | `(5, 1, 3)` |
| CP-11 | 40×6 random `X`, `y` all one class (`np.ones(40)`), 5 alphas | `TypeError` (without the flag, `fit` accepts it) | `(40, 1, 5)` |
| CP-11 | the same, `y = [0, 1, 2, 0, 1]` (three classes) | `TypeError` | `(5, 3, 3)` |
| CP-11 | the same, `y` = 3-column ±1 indicator matrix, 5 rows | `TypeError` | `(5, 3, 3)` |
| CP-11 | 40×6 random `X`, single-column `y` with 3 classes, 5 alphas | `TypeError` | `(40, 3, 5)` |
| CP-11 | the same with `class_weight='balanced'`, with `normalize=True`, or with `sample_weight` | `TypeError` | shape unchanged by each |
| CP-11 | the issue's call with its `X`, and `y` made two-class (`y > 0`), `alphas=np.arange(0.1, 1000, 0.1)`, `normalize=True` | `TypeError` | `cv_values_.shape == (100, 1, 9999)` |
| CP-11 | the issue's call exactly as written (continuous `y`) | `TypeError` at construction | constructs. `fit` raises `ValueError: Unknown label type: ...`, as `fit` without the flag does today (Locked Answers, Gap 2) |
| CP-12 | two-class, four-class and multilabel `y`, `scoring=None` | — | `alpha_ == alphas[argmin over i of mean(cv_values_[:, :, i])]` |
| CP-13 | the CP-11 rows fitted with and without `store_cv_values=True` | — | equal `alpha_`, `coef_`, `intercept_`, `classes_`, and equal `predict` and `decision_function` output |
| CP-14 | `RidgeClassifierCV(alphas=alphas).fit(x, y)` | no `cv_values_` | no `cv_values_` |
| CP-14 | `RidgeClassifierCV(alphas=alphas, cv=2).fit(...)` (10 rows) | no `cv_values_`, `alpha_` set | the same |
| CP-15 | `RidgeClassifierCV(alphas=alphas, store_cv_values=True, cv=2).fit(...)` | `TypeError` at construction | `fit` raises `ValueError` naming `cv` and `store_cv_values` |
| CP-16 | `help(RidgeClassifierCV)`, Parameters and Attributes sections | `cv_values_` refers to a parameter the constructor rejects, and lists `[n_samples, n_alphas]` | `store_cv_values` listed. `cv_values_` shape `(n_samples, n_targets, n_alphas)` |
| CP-17 | the change's own tests, run on the unchanged tree | — | they fail |
| CP-17 | the change's own tests, run with the change | — | they pass |
| CP-18 | the card's `Test command:` run with the change | `28 passed, 1 xfailed`, exit 0 | exit 0, no test that passes today fails |

---

## Verified Claims

All run claims were run on 2026-10-10 in a disposable copy of the product. The copy was taken with
`git archive` from the product's change worktree for this key, at `base_commit`, with no change
applied, and built with `python setup.py build_ext --inplace`. The runs used the card's interpreter,
`/home/kensai/issue-venv/bin/python` (Python 3.8.20). Nothing outside the repository was consulted: no
upstream history, no pull request, no benchmark copy.

The "post-change" rows used a scratch subclass of `RidgeClassifierCV`, defined only in the probe
script. Its constructor added `store_cv_values=False` after `class_weight` and passed it on to the
classifier's existing base. Nothing else differed from the real class. It shows that CP-9 to CP-15
can be met together and that the values in the Examples are what such a tree produces. It is not a
design.

| Claim | Verified by | What came back |
|---|---|---|
| Today the constructor rejects `store_cv_values` | ran `RidgeClassifierCV(store_cv_values=True)` | `TypeError: __init__() got an unexpected keyword argument 'store_cv_values'` |
| Today's signature and `get_params` keys | `inspect.signature(RidgeClassifierCV.__init__)`; `get_params()` | `(alphas=(0.1, 1.0, 10.0), fit_intercept=True, normalize=False, scoring=None, cv=None, class_weight=None)`; keys `alphas, class_weight, cv, fit_intercept, normalize, scoring` |
| Today no fitted classifier has `cv_values_` | fit with defaults on 10×3 random data, `y = [0, 1] * 5`; `hasattr(..., 'cv_values_')` | `False` |
| The docstring refers to a parameter the constructor rejects | read `sklearn/linear_model/ridge.py` lines 1306–1309 (`cv_values_` entry) and 1335–1340 (`__init__`) | confirmed. The constructor has no `store_cv_values`, and the Parameters section does not list it |
| Post-change shapes (CP-11) | probe subclass, `store_cv_values=True`, the CP-11 rows | two-class int and string `y`: `(5, 1, 3)`. Three classes: `(5, 3, 3)`. 3-column indicator: `(5, 3, 3)`. 40×6 `X` with five alphas: binary `(40, 1, 5)`, four classes `(40, 4, 5)`, 2-column multilabel `(40, 2, 5)`, single-column three classes `(40, 3, 5)`. Unchanged by `class_weight='balanced'`, `normalize=True` and `sample_weight`. With `scoring='neg_mean_squared_error'`: `(40, 1, 5)`. No case was two-dimensional |
| `alpha_` is the argmin of the mean `cv_values_` slice (CP-12) | probe subclass, `scoring=None`, every 40×6 case above | `True` in every case |
| Storing the values leaves the model unchanged (CP-13) | probe subclass fitted with and without `store_cv_values=True`, every 40×6 case and with `sample_weight`; `decision_function` also compared on a separate 7×6 `X` | equal `alpha_`, `coef_`, `intercept_`, `classes_`, `predict` and `decision_function` in every case |
| `store_cv_values=True` with a `cv` fails at `fit`, not construction (CP-15) | probe subclass with `cv=2` on `x` stacked twice; `RidgeCV(cv=2, store_cv_values=True)` today | construction raises nothing. `fit` raises `ValueError: cv!=None and store_cv_values=True  are incompatible`, in both |
| `store_cv_values=False` with a `cv` still fits (CP-14) | probe subclass with `cv=2`, flag left at default | fitted, `alpha_ == 0.1`, no `cv_values_` |
| Positional calls keep their meaning (CP-9) | probe subclass `([0.1, 1.0], True, False, None, None, 'balanced')` | `class_weight == 'balanced'` |
| `clone` and `set_params` carry the parameter (CP-10) | probe subclass | `clone(...).get_params()['store_cv_values'] == True`. `set_params(store_cv_values=True)` sets it |
| The issue's continuous `y` is rejected by `fit` with or without the flag (Gap 2) | ran the issue's code with `RidgeClassifierCV(normalize=True)` today, and with the probe subclass and `store_cv_values=True` | both raise `ValueError: Unknown label type: (array([...]),)` |
| A one-class `y` is accepted today, and gives `n_targets = 1` (CP-11) | `RidgeClassifierCV(alphas=al).fit(X, np.ones(40))` today; the probe subclass with `store_cv_values=True` | today: fitted, `coef_.shape == (1, 6)`. Probe: `cv_values_.shape == (40, 1, 5)` |
| The issue's call with a two-class `y` stores the values | probe subclass, the issue's `X` and parameters, `y = (y > 0)` | `cv_values_.shape == (100, 1, 9999)` |
| `scoring='accuracy'` fails today, independent of this change | ran `RidgeClassifierCV(alphas=alphas, scoring='accuracy').fit(x, y)` today, flag absent | `ValueError: continuous is not supported` |
| The card's `Test command:` passes at base, with an empty baseline | read `/home/kensai/issue-test.sh`, `issue-suite.sh` (runs `sklearn/linear_model/tests/test_ridge.py`) and `issue-baseline.txt` (empty). Ran `issue-test.sh` from the copy's root | `28 passed, 1 xfailed`. The suite exited 0 |
| No other file in the product mentions `store_cv_values` | `grep -rn store_cv_values doc sklearn`, excluding `ridge.py` and `test_ridge.py` | no match |

---

## Out of Scope

- **What `cv_values_` holds when `scoring` is set.** CP-11's shape holds. The values themselves are not
  fixed by this change, and the docstring's wording about them is not corrected beyond CP-16.
- **`scoring` values that fail on the classifier today**, e.g. `scoring='accuracy'`, which raises
  `ValueError: continuous is not supported` with or without the flag (Verified Claims).
- **Continuous targets.** `RidgeClassifierCV` does not start accepting them (Locked Answers, Gap 2).
- **`RidgeCV`, `Ridge`, `RidgeClassifier` and `_RidgeGCV`'s behaviour.** Nothing observable about them
  changes. In particular `RidgeCV.cv_values_` stays two-dimensional for one-dimensional `y`.
- **Storing values when `cv` is set.** That stays refused (CP-15). Making grid-search cross-validation
  produce `cv_values_` is a different capability.
- **Documentation outside the classifier's docstring.** `grep` found no other mention of
  `store_cv_values` under `doc/` or `sklearn/`. Release notes (`doc/whats_new`) were not looked at for
  an entry the change might add, and the request asks for none.
- **Anything outside the local clone.** The patch is not pushed (`project.md`, `Manages: none`), and
  nothing is published. As the request says, no record, grade or benchmark file is produced.

---

## Locked Answers (the divergence record — self-review 2026-10-10)

- **Gap 1 — the shape is always three-dimensional (CP-11).** The docstring offers `[n_samples, n_alphas]`
  "or" `[n_samples, n_responses, n_alphas]`. The issue does not say which applies when. The spec picks
  the three-dimensional form for every `y`, including one or two classes, where `n_targets = 1`. The
  reason is that a shape keyed only to `n_targets` gives a caller one indexing rule for every `y`:
  axis 0 is the sample, axis 1 the target, axis 2 the alpha. With a two-dimensional form for two
  classes, code reading the values would have to branch on how many classes `y` held. It is also
  the shape the probe tree produced in every case, so no second shape is introduced to meet the
  docstring's first alternative. The choice is reversible, because it moves an attribute's shape and
  not stored data. CP-16 brings the docstring into line with it.
- **Gap 2 — the issue's literal example still fails, at `fit`, for a different reason.** The issue's
  code passes continuous `y = np.random.normal(size=n)` to a classifier. Today, `fit` without the flag
  rejects that `y` with `ValueError: Unknown label type`. The issue's error is the constructor's
  `TypeError`, and the expected result it states is keeping the cross-validation values. The spec
  removes the `TypeError` and stores the values for every `y` the classifier accepts (CP-11). It does
  not make a classifier accept regression targets. That would change what the classifier is for, and
  it goes against the request's "leave the rest of the product's behaviour as it is". The Examples
  show both the literal call and the same call with a two-class `y`.
- **Gap 3 — `store_cv_values` goes after `class_weight` (CP-9).** The request does not say where the
  parameter goes. Putting it last keeps every positional call that works today meaning the same thing.
  That is the additive choice.
- **Gap 4 — `store_cv_values=True` with a `cv` is refused at `fit` (CP-15).** The issue does not say
  what happens then. The docstring the issue quotes says the values are kept only "if
  `store_cv_values=True` and `cv=None`". `RidgeCV`, which documents the same pair, refuses it at `fit`
  today. Refusing it, rather than silently storing nothing, means a caller who asked for values gets
  either the values or an error. Refusing at `fit`, not at construction, keeps CP-10's `set_params`
  and `clone` usable for any combination.
- **Gap 5 — storing values must not change the model (CP-13), and must not appear when not asked for
  (CP-14).** The request says to leave the rest of the behaviour as it is. These two rules are that
  sentence made checkable for this change.
- **Gap 6 — the docstring is part of the fix (CP-16).** The request asks for "the change the issue asks
  for". The issue's second half asks that the documentation's claim become true. Once the parameter
  exists, the docstring has to list it, and it must not give a shape the classifier never produces.
- **Gap 7 — the change's tests are ones the card's `Test command:` runs (CP-17, CP-18).** The request
  asks for "tests of your own" and does not say where they run. The card's command runs only
  `sklearn/linear_model/tests/test_ridge.py`. A test it does not run shows nothing at the change's
  gate. Where the tests go is development-design's decision. This rule states only the property.
- **Gap 8 — the classification stays `bug`, `changing`.** The request's note says the specs step
  reclassifies a request that asks for a capability the product lacks. The pair is valid
  (`<CORE>/doctrine/flow/change_classification.md`). This skill halts on an invalid pair but has no
  move to re-label a valid one. The issue is also a defect in an existing contract: the docstring
  promises an attribute that no constructor call can reach. So the labels the PM set are kept.
