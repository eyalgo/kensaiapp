# Change request — 2026-10-11_sympy-12096

**Request:** Fix the issue below in the product, the repository that the project card's
`Product path:` names (`sympy/sympy`). The repository stands at the commit before the issue was
fixed. Make the change the issue asks for, with tests of your own that show it, and leave the rest of
the product's behaviour as it is.

It is done when it is sealed. Nothing else is
asked of it: no record, no grade and no benchmark file. Bookkeeping is done outside
KensaiApp.

## The issue

*Not reproduced in this example.* The run was given the issue's title and body verbatim, as the benchmark SWE-bench Verified publishes them. That text is its author's, and the benchmark declares no licence for it, so this example links the issue and summarises it instead.

**The issue:** https://github.com/sympy/sympy/issues/12092

**In short:** SymPy's `evalf` evaluates a function made with `implemented_function`, but not a composition of two of them: `f(g(2)).evalf()` stays unevaluated, because `Function._eval_evalf` does not call `evalf` again on what `_imp_` returns.

## What must not be done

- **Do not look for the fix.** Work from this request and the repository you are given. Do not read
  the repository's history after this commit, its pull requests, its issue tracker, its later
  releases, or any copy of the SWE-bench benchmark
  (`system/projects/swe-benchmark-poc/doctrine/ai_responsibility.md` § 1.1). A patch made with any of
  them in view is not graded.
- **Do not delete anything outside the change** (same file, § 1.2).
- **Do not fix the product's other failing tests.** 28 tests fail before any change, in the environment the card's `Test command:` runs (================= 28 failed, 90 passed, 7492 warnings in 3.59s =================, at `base_commit`):

  - `sympy/core/tests/test_evalf.py::test_evalf_complex_bug`
  - `sympy/core/tests/test_evalf.py::test_evalf_complex_powers_bug`
  - `sympy/utilities/tests/test_lambdify.py::test_Indexed`
  - `sympy/utilities/tests/test_lambdify.py::test_issue_9334`
  - `sympy/utilities/tests/test_lambdify.py::test_issue_9871`
  - `sympy/utilities/tests/test_lambdify.py::test_numexpr_printer`
  - `sympy/utilities/tests/test_lambdify.py::test_numexpr_userfunctions`
  - `sympy/utilities/tests/test_lambdify.py::test_numpy_dotproduct`
  - `sympy/utilities/tests/test_lambdify.py::test_numpy_inverse`
  - `sympy/utilities/tests/test_lambdify.py::test_numpy_logical_ops`
  - `sympy/utilities/tests/test_lambdify.py::test_numpy_matmul`
  - `sympy/utilities/tests/test_lambdify.py::test_numpy_matrix`
  - `sympy/utilities/tests/test_lambdify.py::test_numpy_numexpr`
  - `sympy/utilities/tests/test_lambdify.py::test_numpy_old_matrix`
  - `sympy/utilities/tests/test_lambdify.py::test_numpy_piecewise`
  - `sympy/utilities/tests/test_lambdify.py::test_numpy_transl`
  - `sympy/utilities/tests/test_lambdify.py::test_numpy_translation_abs`
  - `sympy/utilities/tests/test_lambdify.py::test_numpy_transpose`
  - `sympy/utilities/tests/test_lambdify.py::test_python_div_zero_issue_11306`
  - `sympy/utilities/tests/test_lambdify.py::test_tensorflow_basic_math`
  - `sympy/utilities/tests/test_lambdify.py::test_tensorflow_logical_operations`
  - `sympy/utilities/tests/test_lambdify.py::test_tensorflow_multi_max`
  - `sympy/utilities/tests/test_lambdify.py::test_tensorflow_multi_min`
  - `sympy/utilities/tests/test_lambdify.py::test_tensorflow_piecewise`
  - `sympy/utilities/tests/test_lambdify.py::test_tensorflow_placeholders`
  - `sympy/utilities/tests/test_lambdify.py::test_tensorflow_relational`
  - `sympy/utilities/tests/test_lambdify.py::test_tensorflow_transl`
  - `sympy/utilities/tests/test_lambdify.py::test_tensorflow_variables`

  Leave them failing. The card's `Test command:` knows them: it passes while they are the only failures, and fails on any other.

**Category:** bug
**Behaviour:** changing
**Classified because:** the issue reports behaviour the product gets wrong. Correcting it changes what
the product does, so Behaviour is `changing`, and the cause is a defect in existing behaviour, so
Category is `bug` (`<CORE>/doctrine/flow/change_classification.md`, the two axes). Where the issue
asks for a capability the product lacks rather than a defect, the specs step reclassifies it.

**Sealed:** 2026-10-11 — accepted; merged to `main` via `--no-ff`.
