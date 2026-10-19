# Code integrity report — 2026-10-10_scikit-learn-10297

Integrity: pass

**Mode:** workflow · **Reviewer:** Senior Engineer · **Date:** 2026-10-10
**Outcome:** clean pass. The code does what its intent says. Some tests did not prove it, and they
were added or corrected. No code was changed.

## Deferrals

None. The newest closing marker on the instance branch (`f43f8c3`, `developer:
2026-10-10_scikit-learn-10297 — implementation complete`) has no `Deferred:` line and no `Failing:`
line.

## What was reviewed

The product worktree `…/scikit-learn__scikit-learn-10297/.worktrees/2026-10-10_scikit-learn-10297`,
the diff from `b90661d` (base) to `fdf2be2` (the developer's last commit), made by four commits:

- `sklearn/linear_model/ridge.py`: `RidgeClassifierCV.__init__` takes `store_cv_values=False` as
  its last parameter and forwards it to `_BaseRidgeCV`. The class docstring has a new
  `store_cv_values` entry and a rewritten `cv_values_` entry.
- `sklearn/linear_model/tests/test_ridge.py`: 22 new tests and four helpers.

## The intent it was checked against

- `tl_instruction.md`: Tasks 1 and 2, with their *Behaviours to verify* and *Held by review*.
- `change_spec.md`: CP-9 to CP-18, the Examples table and Locked Answers Gaps 1 to 8.
- `docs/fdr.md`: absent. The project card reads `Definition: none`, so there is no FDR or SDD, and
  that is the normal case.

## Placement

**No parts table.** The product has no `docs/SDD.md` (`docs/` does not exist in the product
worktree), so there was nothing to place the code against. Step 0 did not run, and no
`… — placement` commit was made. The *Held by review* item was checked by reading the diff
instead. No storing, reshaping or validation code was added to `RidgeClassifierCV`, and
`_BaseRidgeCV`, `_RidgeGCV` and `RidgeCV` are unchanged.

## Tests added or fixed

All are in `sklearn/linear_model/tests/test_ridge.py`, in product commit `85bf914`.

**Added.** Each one covers a rule that no existing test reached.

| Test | Rule | Why it was missing |
|---|---|---|
| `test_ridgeclassifiercv_signature_keeps_existing_parameters` | CP-9: the existing parameters keep their *names, defaults and positional order* | The positional test checks `class_weight` and `store_cv_values` only. The `get_params` test checks the key names and one default. If another parameter's default changed, both stayed green. Under mutation M5 (below), this test is the one that failed. |
| `test_store_cv_values_set_after_construction_reaches_fit` | CP-10: `set_params` *changes* the parameter, and `clone` *carries it over* | The developer's tests read the attribute back but never fit. A flag that changed the attribute but did not govern `fit` passed them. The test checks both directions: `set_params(True)` stores values and `set_params(False)` stops storing them. |
| `test_storing_cv_values_does_not_change_multi_target_model` | CP-13 over the CP-11 rows (the spec's CP-13 example row) | The equality test covered a two-class `y` only. This adds the four-class and the multilabel `y`, so the multi-target path is covered too. |
| `test_no_cv_values_when_store_cv_values_false` | CP-14: *set explicitly or left at the default*, *whatever `cv` is*. Also CP-9: constructing with `False` raises nothing | Only the default was tested. This passes `store_cv_values=False` explicitly, with `cv=None` and with `cv=2`. |

**Corrected.** Each test was green, but it could not fail in the case it existed to catch.

| Test | Rule | What was wrong |
|---|---|---|
| `test_store_cv_values_with_cv_refused_at_fit` | CP-15: the message names both `cv` and `store_cv_values` | The `"cv" in message` check is true for any message that contains `"store_cv_values"`, so it did not test anything. It is now `re.search(r"\bcv\b", …)`, which matches `cv` only as a separate word. Under mutation M1 the old assertion stayed green and the new one went red. |
| `test_ridgeclassifiercv_docstring_documents_store_cv_values` | CP-16 | It checked only that `n_targets` appeared somewhere in the entry, so a wrong shape would pass. It now also checks for the shape `n_samples, n_targets, n_alphas` in the entry header, for `bool` and `False` in the parameter's header, and for `cv=None` in its entry. It refuses any 2-D `n_samples, n_alphas` shape, not just the one `[…]` spelling. See *Calls made* 1. |

The two CP-13 tests now share a `_assert_same_model` helper.

**Evidence that the tests can fail.** These were run in a disposable copy of the worktree, with the
copy's `ridge.py` mutated each time:

| Mutation | Result |
|---|---|
| M1: the refusal message names only `store_cv_values` | the corrected CP-15 test fails |
| M2: the docstring shape is `(n_samples, n_targets)` | the docstring test fails |
| M3: the docstring header reads `default=True` | the docstring test fails |
| M4: the classifier keeps the flag it was constructed with and ignores `set_params` at `fit` | the new reaches-fit test fails. The developer's `set_params` and `clone` tests pass. |
| M5: the `class_weight` default changes | the signature test fails. The positional and `get_params` tests pass. |
| Base tree (`b90661d`'s `ridge.py`) | all six added or corrected tests fail, as CP-17 requires |

**Suite after the review:** `/home/kensai/issue-test.sh` exits 0 with 54 passed, 1 xfailed. Before
the review it was 50 passed, 1 xfailed. The xfailed test is untouched.

**Checked and kept as written:**

- The argmin test (CP-12) can fail. The alphas it selects are 10, 100 and 100, all inside the grid
  rather than at its ends.
- The ±1 indicator `y` is a real multilabel input: `type_of_target` returns `multilabel-indicator`.
- `test_ridgeclassifiercv_positional_args_keep_meaning` passes on the base tree, as the developer
  noted. It guards against a parameter being inserted before `class_weight`. CP-17's list of what
  must fail at base does not include it.

## The finding

**No code bugs.** The constructor change and the docstring do what CP-9 to CP-16 say. Six tests
were weak and are now strong: four added and two corrected (above). No code was moved.

Recorded for the record only, with nothing to act on: the developer's task 1 red commit body says
16 tests failed. The closing marker corrects that to 18, and that matches the instruction.

## Calls made

1. **How far the docstring test may check CP-16.**
   - *The question:* `tl_instruction.md` Task 2 says to check three tokens "and no wording around
     them". CP-16 also requires the entry to give the shape `(n_samples, n_targets, n_alphas)`, to
     list the parameter as a boolean that defaults to `False`, and to say it works only with
     `cv=None`. With only the three tokens checked, a docstring that gave a wrong shape or the
     wrong default passed.
   - *The readings weighed:* (a) keep the test to the plan's three tokens; (b) also check the
     identifiers and values CP-16 fixes.
   - *Taken:* (b), checking only identifiers and values and no wording. The plan's reason for its
     limit is that the sentences belong to `change_text.md`, and (b) keeps to that: it checks no
     sentence. It closes gaps that M2 and M3 show are real, and it meets both documents as written.
   - *Whose call to confirm:* the Tech Lead (`tl_instruction.md` Task 2).
   - *If reversed:* drop the five added assertions. The docstring itself does not change.

2. **The CP-15 test checks the two names and nothing more.** CP-15 says the message "says that they
   cannot be used together", but "the exact wording is not fixed". The plan also says to "assert on
   those two substrings". So no assertion was added about the incompatibility wording.
   - *Whose call to confirm:* the Product Owner (CP-15).
   - *If reversed:* add an assertion on the wording the PO fixes.

## Language resolution

- **Language:** Python. It was answered at step 1 of the chain: `project.md` has `Languages:
  Python`.
- **Packet read:** `<CORE>/doctrine/engineering/languages/python/README.md`, the router. From it:
  `conventions.md` (100 columns, double-quoted strings), `quality_gates.md` (compile, and the rule
  that a red or non-running suite is a failed gate), and `testing_python.md` (no `monkeypatch` on
  the unit under test). The floor is `developer_standards.md`.
- **How the review met it:**
  - No added line is longer than 80 columns.
  - New strings are double-quoted. That differs from the file's single-quote habit, and the packet
    wins.
  - `python -m compileall -q` on the test file exits 0.
  - The tests fit real estimators and patch nothing.
  - Test location: the packet's `tests/test_<domain>.py` is set aside in favour of the product's own
    tree and the card's test command, the same divergence the developer recorded.
