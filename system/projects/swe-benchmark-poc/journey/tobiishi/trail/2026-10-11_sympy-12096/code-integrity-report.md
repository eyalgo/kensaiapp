# Code integrity report — 2026-10-11_sympy-12096

Integrity: pass

**Date:** 2026-10-11 · **Mode:** workflow · **Reviewer:** Senior Engineer (`development-code-integrity`)

The code already does what its intent says. No bug was found and nothing was misplaced. Three
behaviours the intent states had no test that would go red if the code were wrong. They are now
pinned, in one test commit in the product repository.

---

## Deferrals

**None.** The closing marker is `e930a90` (`developer: 2026-10-11_sympy-12096 — implementation
complete`), the only marker on the branch, and it carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

The product is `sympy__sympy-12096`, in its own repository. Its change worktree is
`<the issue's clone>/.worktrees/2026-10-11_sympy-12096`.
The diff reviewed is `d7c304511..4b06b310c`: the developer's `— red` commit `6dfdd9319` and its
`— green` commit `4b06b310c`.

- `sympy/core/function.py`: `Function._eval_evalf` (non-mpmath branch) and the new private method
  `Function._evalf_implementation_result`.
- `sympy/core/tests/test_evalf.py`: the helper `_implemented` and three new tests,
  `test_implemented_function_evalf_composition`, `_numeric_return` and `_not_a_number`.

## The intent it was checked against

- `tl_instruction.md`: Task 1, its *Behaviours to verify*, the rule every test must follow, the hint,
  *Held by review* and the verification gate.
- `change_spec.md`: CP-9 to CP-15, the Examples table and Locked Answers Gaps 1–6.
- `docs/fdr.md`: absent. The card reads `Definition: none`, so this is the normal case and not a gap.

## Tests added or fixed

No existing test was wrong. Every *Behaviours to verify* row and every Examples row was already
asserted, as the plan's strings require, and `test_implemented_function_evalf` is unchanged (CP-15).
The added assertions are in product commit `7e1937e01`
(`senior-engineer: 2026-10-11_sympy-12096 integrity tests — clean pass`):

1. **An infinite return reached through the new evaluator.** `g(F(2))` with `F` returning `oo` or `-oo`
   prints `inf` or `-inf` (in `_numeric_return`).
   *Why:* the TL added the behaviour "a return of `inf` is a number while `zoo` and `nan` are not"
   (CP-9's definition of a number, CP-11's boundary). The developer's `F → oo` rows print `inf` at
   base too, so they go through the old `Float(result, prec)` literal path and never reach the
   evaluator. Code that rejected `finf` beside `fnan` would have stayed green. **Proven:** a scratch
   copy with that mutation fails `_numeric_return`. At base, `g(F(2))` is unevaluated.
2. **All three caught types, outer and inner.** `ty` (raises `TypeError`) and `at` (raises
   `AttributeError`) join `s` (raises `ValueError`). Each of `failing(-1).evalf()` and
   `f(failing(-1)).evalf()` stays unevaluated, and `(f(ty(2)) + 1).evalf()` is `f(ty(2)) + 1.0`
   (in `_not_a_number`).
   *Why:* CP-12's first bullet names all three types, "for the outer application's implementation
   and for any inner one". Only `ValueError` was tested. **Proven:** a scratch copy that narrows the
   catch around `self._imp_(*self.args)` to `ValueError` fails `_not_a_number`.
3. **Propagation inside a larger expression and at depth.** `(z(2) + 1).evalf()`,
   `(f(z(2)) + 1).evalf()` and `f(g(z(2))).evalf()` raise `ZeroDivisionError` (in `_not_a_number`).
   *Why:* CP-12's second bullet says any other exception propagates from an inner implementation
   "reached while evaluating `r`", and CP-10 says the rule holds inside a larger expression. Only the
   bare `z(2)` and the one-level `f(z(2))` were tested. These rows hold on the tree, and they keep a
   later catch-all in the evaluator path from passing.

Test isolation follows the plan's rule. `ty` and `at` live inside the `_implemented` context manager,
so their `_imp_` is removed on exit. Neither name is an mpmath function or a `MPMATH_TRANSLATIONS`
key (checked with `hasattr(mpmath, …)` and a lookup in the dict), and neither is used elsewhere in the
two test files the card runs.

**Run:** the card's `Test command:` (`/home/kensai/issue-test.sh`), run from the product change
worktree, exited 0: `28 failed, 93 passed`, last line
`issue-test: only baseline failures remain (28 known at base_commit)`. Every failure is in the
baseline. `pytest -k implemented_function` gave 4 passed. In a scratch copy with the base
`function.py` and the new tests, the three new tests fail and `test_implemented_function_evalf`
passes (CP-14).

## The finding

**No issues in the code.** The implementation meets every rule:

- CP-9 and CP-10 hold, for nesting at any depth, numeric expressions, complex returns (SymPy and
  Python), precision at n = 15, 30 and 50, inside an `Add`, and with `subs`.
- CP-11 holds for free symbols, undefined functions, `zoo`, `nan` and the `str`/`list`/`None` type
  gate, with the `"2"` row unchanged.
- CP-12 holds for all three caught types, and other exceptions propagate.
- CP-13 holds: the literal path runs first, the returned value is built with `EvalfMixin.evalf`'s own
  normalisation, and the implementation is called once.

The *Held by review* rules were read in the diff and hold. There is no depth guard. The new path
catches only `NotImplementedError`, `AttributeError`, `TypeError` and `ValueError`, so a
`RecursionError` is not swallowed. The new imports are local to the method, and there is no new
module-level import between `function.py` and `evalf.py`.

The gaps were in the tests: three intent rules had no test that a wrong implementation would fail.
They are closed above. Nothing was moved (see *Placement*).

The correction the plan records as owed outside this change is left as instructed: the literal path
passes the binary `prec` to `Float` as decimal digits. It is not this change's to fix.

## Calls made

1. **Where the "inf is a number" row lives.**
   - *Question:* the plan puts this behaviour in `test_..._not_a_number`, but the developer put the
     `F → oo` rows in `_numeric_return`.
   - *Readings:* move the rows to match the plan's wording, or extend them where they already are.
   - *Taken:* extend them in `_numeric_return`. An infinite return *is* a number under CP-9, so it
     belongs in the test of numeric returns. Moving them would have changed a test file for no
     behavioural gain, and the plan's real requirement, that the boundary be asserted, is met
     either way.
   - *Owner:* the **Tech Lead** (`tl_instruction.md`). If they rule the other way, three assertions
     move between two test functions, with no change to code or coverage.
2. **The developer's divergence from the Python packet on annotations and the future import is
   accepted.**
   - *Question:* `python/conventions.md` asks for `from __future__ import annotations` and annotated
     production functions, and the packet binds over the file's style.
   - *Readings:* annotate per the packet, or leave the code unannotated.
   - *Taken:* leave it unannotated. This is not a question of style. The product declares Python
     2.6–3.5 (`setup.py` 360–367), where annotations do not parse, so following the packet would
     break the product's own supported interpreters. The contract is stated in the method's
     docstring.
   - *Owner:* the owner of the Python packet (`core/doctrine/engineering/languages/python/`). If
     they rule the other way, the method gains annotations and the product drops Python 2 support,
     which is far outside this change.

## Placement

**No parts table.** `docs/SDD.md` does not exist under the product path, and `tl_instruction.md`
says "No parts table — placement follows change_design.md §2", so Step 0 was skipped. For the record,
the only new logic, `_evalf_implementation_result`, sits in `Function` in `sympy/core/function.py`,
the unit the design names. No `— placement` commit was made.

## Language resolution

- **Language:** Python, from chain step 1 (`project.md` `Languages: Python`).
- **Packet read:** `<CORE>/doctrine/engineering/languages/python/README.md`, with `conventions.md`
  (surface style, typing, naming, comments and docstrings) and `quality_gates.md` (the compile and
  suite gates), plus `testing_python.md` for Testing, which the router sends outside the folder.
  The developer's marker accounts for `toolchain.md`, `layout.md` and `errors_logging.md`, and
  nothing this review added bears on them.
- **Applied:**
  - The added assertions use double-quoted strings, as the packet requires, though the surrounding
    file uses single quotes.
  - No added line exceeds 100 columns (checked with awk).
  - The suite gate passed, as run above.
  - The `#` comments in the new method record why (a rejected alternative), which matches the
    packet's comment form.
  - The one divergence, on annotations, is Call 2.

## Domain note

This instance's domain rules are about its public sites (`system/doctrine/kensaiapp_doctrine.md`),
and this product is a sympy patch with no site surface, so none of them applies here. No test
reaches LinkedIn, and no fixture states anything about KensaiApp or Eyal.
