# Change Text — RidgeClassifierCV accepts `store_cv_values` and keeps `cv_values_`

**Date:** 2026-10-10
**Category:** bug
**Behaviour:** changing

This file holds the exact words this change puts in front of a reader of `RidgeClassifierCV`'s API
reference: the new `store_cv_values` entry under Parameters, and the `cv_values_` entry under
Attributes. Those are the two places `change_design.md`'s `Publishes text:` line names. The text is
settled for placement. It is not approved for publication. The patch stays in the local clone
(`system/projects/swe-benchmark-poc/project.md`, `Manages: none`).

**How to read each block.** Each block is one whole entry, exactly as `help(RidgeClassifierCV)` shows
it. The entry's name line is at the left margin, and its description is indented four spaces, as in
the entries around it. Every line break shown is a line break in the entry. No line ends in a
backslash. Each line fits the product's 79-column limit at the indent the entries around it use. The
`cv_values_` block is the whole of that entry and takes the place of the entry there now.

---

## Text

### `RidgeClassifierCV` API reference — Parameters, the `store_cv_values` entry

**Reading the reference, before or after constructing the classifier**

```text
store_cv_values : boolean, default=False
    Flag indicating if the cross-validation values corresponding to
    each alpha should be stored in the ``cv_values_`` attribute (see
    below). This flag is only compatible with ``cv=None`` (i.e. using
    Generalized Cross-Validation). With any other ``cv``, ``fit``
    raises a ``ValueError``.
```

When the person sees it: they are choosing constructor arguments, and they learn that the values are
kept only with `cv=None`, and that asking for them together with a `cv` fails at `fit`.

### `RidgeClassifierCV` API reference — Attributes, the `cv_values_` entry

**Reading the reference, before or after fitting**

```text
cv_values_ : array, shape = (n_samples, n_targets, n_alphas), optional
    Cross-validation values for each alpha, stored by ``fit`` only when
    ``store_cv_values=True`` and ``cv=None``. ``n_targets`` is 1 when
    ``y`` has one or two classes, the number of classes when it has
    more than two, and the number of columns of a multilabel indicator
    ``y``. With ``scoring=None``, the values are the squared
    Leave-One-Out errors, and ``alpha_`` is the alpha whose values have
    the lowest mean (the first such alpha in ``alphas`` on a tie).
```

When the person sees it: they want to read the stored values, and they learn when the attribute
exists, how to index it for any `y`, and what the values mean when no `scoring` is set.

---

## Wording decisions

- **The `store_cv_values` entry reuses `RidgeCV`'s wording for the same parameter.** `RidgeCV`'s
  docstring (`sklearn/linear_model/ridge.py`, its `store_cv_values` entry) already describes this
  flag. The flag means the same thing on both classes, because both pass it to the same base class
  (`change_design.md` § 1). One concept keeps one string, so the first three sentences are
  `RidgeCV`'s, including the product's term "Generalized Cross-Validation".
- **Added the sentence "With any other ``cv``, ``fit`` raises a ``ValueError``."** "Only compatible
  with `cv=None`" alone does not tell the reader what happens otherwise. The spec fixes that outcome
  (CP-15), and its Verified Claims show `fit` raising `ValueError` with the flag and `cv=2`, while
  construction raises nothing. The sentence says when the error comes (at `fit`) and names no message
  text, because CP-15 leaves the message's wording unfixed.
- **Code is marked with double backticks in both entries.** `RidgeCV`'s entry and the classifier's
  current `cv_values_` entry use single backticks. The classifier's Parameters section marks code
  with double backticks, as in ``` ``fit_intercept = False`` ``` and ``` ``normalize=False`` ```. The two
  entries follow the section they sit in.
- **The shape is given in one form, `(n_samples, n_targets, n_alphas)`.** CP-16 fixes this shape and
  bars any shape the classifier does not produce. So the two-dimensional `[n_samples, n_alphas]` is
  removed. `n_responses` becomes `n_targets`, the term the `coef_` and `intercept_` entries of the
  same docstring already use for the same axis. The parentheses are the form CP-16 states. The
  `intercept_` entry beside it, `shape = (n_targets,)`, shows that this docstring already uses them.
- **Added a sentence that says what `n_targets` is for a classifier.** A regressor's reader knows
  `n_targets` from the `y` they pass in. A classifier's reader does not, because `y` holds labels
  and the classifier decides the count. The sentence is CP-11's domain, which the spec's Verified
  Claims ran case by case. One or two classes give 1, more than two give the class count, and a
  multilabel indicator gives its column count. Without it, the reader cannot index axis 1, which
  is the point of keeping that axis for every `y` (spec, Locked Answers, Gap 1).
- **Replaced the sentence about what the values contain.** The current entry ends: "After `fit()`
  has been called, this attribute will contain the mean squared errors (by default) or the values of
  the `{loss,score}_func` function (if provided in the constructor)." The new text says only what
  the change's sources ground:
  - The constructor has no `loss_func` or `score_func` parameter. A search of
    `sklearn/linear_model/ridge.py` finds neither name. The clause tells the reader to pass an
    argument the class does not take.
  - With `scoring=None`, each stored value is one sample's squared Leave-One-Out error for one target
    and one alpha. The product's error function returns `(c / G_diag) ** 2` per sample. The mean over
    a slice is what `alpha_` is chosen by (CP-12, verified by the spec's probe for every case). So
    "mean squared errors" describes the choice, not the stored values. Where `sample_weight` or
    `class_weight` is given, the errors are those of the weighted problem the classifier fits. They
    are still squared errors, so the sentence stays true without a clause about weights.
  - With `scoring` set, the entry says nothing about the values. The spec does not fix them (CP-12,
    and its Out of Scope). A sentence describing them would promise what the change does not.
  - The tie clause is CP-12's rule, that the first such entry in `alphas` wins.
  - "Leave-One-Out" is capitalised as in the classifier's own `cv` entry ("the efficient
    Leave-One-Out cross-validation").

  **This goes past one line of the spec, and is recorded as such.** The spec's Out of Scope says
  "the docstring's wording about them is not corrected beyond CP-16". The new entry still makes no
  claim about the values when `scoring` is set. What it does beyond CP-16 is drop a clause that names
  a constructor argument the class lacks. The Developer places this text verbatim, so writing that
  clause here would have published a claim the product cannot keep. No behaviour, calculation or
  test moves with it. The design's docstring test checks only the three tokens CP-16 fixes
  (`change_design.md` § 5), and the text holds all three. If the owner of the change's meaning wants
  the old clause back, that is a change to this file in a later change, not a rewording at placement.
- **The `ValueError` message is not written here.** The change makes the base class's message
  `cv!=None and store_cv_values=True  are incompatible` reachable from the classifier. That is a new
  state for a reader of this class. But `Publishes text:` names no place for it. The message also lives
  in the base class that `RidgeCV` shares, and the spec keeps `RidgeCV`'s behaviour as it is (Out of
  Scope). The `store_cv_values` entry now tells the reader about this outcome before they meet it. The
  message's doubled space before "are" is left for a later change on the base class.
- **The strings make no claim about KensaiApp or Eyal.** So `system/doctrine/claims_doctrine.md`
  has nothing to check here. The instance's banned words
  (`system/experience/voice_restrictions.md`, entry `no-ai-tell-vocabulary-or-openers`) and its marks
  (entry `plain-text-marks`) bind prose published in Eyal's name, which a scikit-learn docstring is
  not. Both strings were searched for every listed word and mark anyway, and none occurs. No em-dash
  is used.
- **No AI-use disclosure is added or dropped.** `system/doctrine/kensaiapp_doctrine.md` § 6 leaves
  that call to each project, for a text it publishes. This change publishes nothing: the patch stays
  in the local clone (`project.md`, `Manages: none`; spec, Out of Scope). Whether a disclosure would
  be owed if a patch from this project were ever pushed is not answered by any record. It is open,
  and Eyal confirms it.
- **The strings are in fenced blocks, not the template's quote marks.** The indentation and line
  breaks are part of what `help()` shows. A quote mark at each line's start would be one more thing
  the Developer has to strip.

---

## Findings for the Content Manager

- **Both entries** — **No standard covers the text this project writes into another project's
  repository.** The product is a third-party repository with no `CONTENT.md`.
  `system/doctrine/writing_bar.md` § 1.1 binds the documents this instance authors, for its own three
  readers. `system/experience/voice_restrictions.md` binds this instance's surfaces and prose
  published in Eyal's name. A scikit-learn docstring is neither. Each later issue in this project
  will meet the same gap, in whatever repository it lands in. The missing rule would say what a
  change's words in such a repository are held to. It would also say whether the instance's banned
  words reach them. In the meantime, both entries were written to the conventions of the entries
  around them: numpydoc layout, the product's existing terms, and `RidgeCV`'s wording for the same
  parameter. They were also checked against the instance's banned words, which found none.
