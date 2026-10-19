# Tech Lead instruction — sympy-12096: evalf evaluates what an implemented function returns

**Product root:** <the issue's clone>/.worktrees/2026-10-11_sympy-12096 — every path below is relative to it.
**Scope:** `Function._eval_evalf` in `sympy/core/function.py` evaluates an implemented function's return when that return is a number written as an expression, at any nesting depth. Tests go in `sympy/core/tests/test_evalf.py`.
**Category / Behaviour:** bug / changing (copied from `change_design.md`).

**What this change may bring in.** No third-party origin, no device storage, no new dependency, no new module-level import, no new file. The one new import is function-local, inside `_eval_evalf` (see the hint). Nothing is published and nothing is pushed.

---

## Project layout

```
sympy/
  core/
    function.py                ← modified (Function._eval_evalf, non-mpmath branch only)
    tests/
      test_evalf.py            ← modified (three new test functions; existing ones untouched)
```

`sympy/core/evalf.py` and `sympy/utilities/lambdify.py` are read, not changed.

No parts table — placement follows change_design.md §2.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **Spec coverage checked, no gap:** every CP-9 to CP-15 rule maps to a test row in design §5 or to the full-suite gate. CP-15 is the gate, not a test.
- **No §3 in the design, one task here:** one file, one method, no internal seam and no ordering edge. Splitting the method's change from its tests would give a task with no test of its own, so the plan keeps one test-first task.
- **Behaviours added (implied by the rules, absent from §5):**
  - `test_..._not_a_number` also asserts a return of `inf` is a number while `zoo` and `nan` are not. CP-9 and CP-11 pin the boundary, and the hint's explicit `nan` rejection is otherwise unasserted.
  - `test_..._composition` also asserts that a failing inner application inside a sum leaves the rest to evaluate. CP-11 states `(f(g(x)) + 1).evalf()` for a symbolic case, and the same shape with a `ValueError` inner is the likeliest place for the exception handling to go wrong.
- **Hint carried, trimmed to the approach:** §4's hint is carried whole in substance. Its sentence on why `is_number` is wrong is kept, because a developer who reaches for `is_number` fails two CP-11 rows. No code is added to it.
- **Verification gate command:** the card's `Test command:` was run by the spec at base (`28 failed, 90 passed`, exit 0), so it runs the two files and is used as written. I did not re-run it.
- **Test-isolation hazard made a task rule:** design §5's cache hazard (an `_imp_` left on a name leaks to other tests) is carried into the behaviours list as a requirement on every test, because a leak shows up as a failure in a different test file.
- **Not planned, by design:** no depth guard for self-referential implementations (Architect Review Notes), so no test pins that.

## Corrections owed while there

- `sympy/core/function.py` `Function._eval_evalf` — the literal path passes the binary `prec` to `Float`, which reads it as decimal digits, so working precision is higher than needed. Found by the architect, not this change's to fix: CP-13 pins that path and the request says to leave the rest as it is. Owed outside this change's reach: `sympy/core/function.py` `_eval_evalf` literal path — `Float(self._imp_(*self.args), prec)` treats a binary precision as decimal digits → pass decimal digits, or convert with `prec_to_dps`, once a change is allowed to touch CP-13's path.

---

### Task 1: Evaluate an implemented function's numeric return (`sympy/core/function.py`, `sympy/core/tests/test_evalf.py`)

**Dependencies:** None

**What to build:** In the non-mpmath branch of `Function._eval_evalf`, keep today's literal conversion first and unchanged. When it fails on a return that is a SymPy object or a Python `int`/`float`/`complex`, evaluate that return at the binary precision the method received. Return the result only when it is a number (a finite real, a complex with real parts, or `±inf`; never `zoo` or `nan`). Otherwise return `None`, as today. The method's signature and its return contract do not change.

#### Behaviours to verify (developer adds three test functions to `sympy/core/tests/test_evalf.py`)

Compare printed results as strings wherever a digit count is pinned (`str(...)`), not with `==` on a `Float`. Use the Examples table in `change_spec.md` for each expected string.

**Rule for every test.** Each implemented function a test creates has its `_imp_` removed when the test ends, even if an assertion fails (`try`/`finally`), or uses names no other test in the run uses. No name may be an mpmath function or a key of `MPMATH_TRANSLATIONS` (`ff` is one). The spec's names (`f`, `g`, `h`, `c`, `pc`, `p`, `s`, `z`, `k`, `w`, `F`, `u`) are clear.

- `test_implemented_function_evalf_composition` (CP-9 nesting, CP-10, CP-14 issue lines, CP-13 print):
  - `f(2).evalf()` and `g(2).evalf()` print `4.00000000000000`; `f(g(2)).evalf()` prints `16.0000000000000`.
  - `g(f(2))` prints `8.00000000000000`; `f(g(f(2)))` prints `64.0000000000000`.
  - `f(g(2)).evalf(50)`, `N(f(g(2)))` and `f(g(2)).n(30)` print as the Examples table records.
  - `(f(g(2)) + 1).evalf()` prints `17.0000000000000`; `f(g(x)).evalf(subs={x: 2})` prints `16.0000000000000`.
  - `str(f(g(2)))` is `f(g(2))`: creating or printing does not evaluate.
  - A failing inner application inside a sum leaves the sum partly evaluated: with `s` returning `math.sqrt(x)`, `(f(s(-1)) + 1).evalf()` is `f(s(-1)) + 1.0`.
- `test_implemented_function_evalf_numeric_return` (CP-9 non-literal and complex, CP-13, CP-14 second bullet):
  - `f(pi).evalf()` prints `9.86960440108936`; `h(1).evalf()` prints `0.841470984807897`.
  - `str(h(1).evalf(30)) == str(sin(1).evalf(30))` and `str(f(h(1)).evalf(30)) == str((sin(1)**2).evalf(30))`, each also equal to the table's string.
  - `c(2).evalf()` prints `2.0*I`; `f(c(2)).evalf()` prints `-4.00000000000000`; `pc(2).evalf()` (Python `1j`) prints `1.0*I`.
  - Unchanged outputs: `f(2).evalf(50)`, `p(2).evalf(50)` (Python `float` `math.pi`), `k(2).evalf(30)`, `f(Rational(1, 3)).evalf(30)`, `s(g(2)).evalf()` is `2.00000000000000`, and `F` returning `oo` / `-oo` prints `inf` / `-inf`.
- `test_implemented_function_evalf_not_a_number` (CP-11, CP-12, CP-14 third bullet):
  - Each of `f(x)`, `f(g(x))`, `f(u(2))` (`u = Function('u')`) and `w(2)` (`w` returning `x + Symbol('y')`) evalfs to itself.
  - `str((f(g(x)) + 1).evalf())` is `f(g(x)) + 1.0`.
  - `F` returning `zoo`, `nan`, the `str` `"pi**2"`, a `list` or `None` gives `F(2)`; `F` returning the `str` `"2"` prints `2.00000000000000`.
  - `s(-1).evalf()` is `s(-1)` and `f(s(-1)).evalf()` is `f(s(-1))` (`ValueError`).
  - `z(2).evalf()` raises `ZeroDivisionError`, and so does `f(z(2)).evalf()`. The second is this test's red at base.

Every one of the three functions holds at least one assertion that fails on the unchanged tree, so each is red before the change. Regression assertions sit inside them rather than in a test of their own. `test_implemented_function_evalf` stays as written, four assertions unchanged (CP-15).

#### Held by review (omit when every rule of this task reaches a test)

- A self-referential implementation (`F` returning `F(x)`, or two that return each other) recurses until `RecursionError` and propagates. No test pins it and no guard is added. The architect left it out on purpose, so the rule is held by reading the diff: the diff must contain no depth guard.
- The new path catches only `NotImplementedError` and the three types. A test reaches this only through `z`; a broader `except` that also let `z` through would still be caught by that row, but one that swallowed `RecursionError` would not. The rule is held by reading the diff.

#### Implement

Infer from failing tests.

# Hint:
Keep the existing `Float(r, prec)` attempt as the first thing that runs, byte for byte, so every return that converts today converts the same way (CP-13), the `str` `"2"` row included. Call the implementation once, separately from the conversion; an implementation that raises one of its three caught types still means "not a number" and must not reach the new path. Fall into the new evaluation only when the literal attempt fails. Gate on type before sympifying: a SymPy object, or a Python `int`/`float`/`complex`. A `str`, a `list` or `None` never enters (CP-11's boundary). Decide "is a number" with the module-level evaluator in `sympy/core/evalf.py`, never with `is_number`: at base `is_number` is `True` for `u(2)**2` and for `zoo`, while the evaluator raises `NotImplementedError` for both and for anything with a free symbol, but returns a value for `nan`, which has to be rejected explicitly. Evaluate at the binary `prec` the method receives, not as decimal digits. Build the returned value from the evaluator's parts with the same normalisation `EvalfMixin.evalf` applies to its own result, so it agrees with `r.evalf(n)` by construction. Around the new evaluation catch only `NotImplementedError` and the three types, returning `None` on any of them; everything else propagates, which is how `f(z(2))` raises `ZeroDivisionError`. Import from `evalf.py` inside the method, as the branch already does for `MPMATH_TRANSLATIONS`, so no module-level import between `function.py` and `evalf.py` is added.

#### Verification gate

Run `/home/kensai/issue-test.sh` from the product root.

Pass criteria: exit 0; the run's failures are exactly the 28 baseline tests that `change_request.md` § *What must not be done* lists, and its last line reads `issue-test: only baseline failures remain (28 known at base_commit)`; the three new tests pass; `test_implemented_function_evalf` passes with its assertions unchanged; no `_imp_` leaks between tests (the new tests pass in any order and the rest of the two-file run is unchanged).
