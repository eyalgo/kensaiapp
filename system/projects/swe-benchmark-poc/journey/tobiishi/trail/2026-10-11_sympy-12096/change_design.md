# Change Design — evalf evaluates what an implemented function returns, including another implemented function

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Publishes text:** no

---

## 1. Change Summary

`evalf` of an implemented-function application turns the implementation's return `r` into a number
only through `Float(r, prec)`. That call accepts numeric literals and nothing else. Any return that
is a number written as an expression (`g(2)**2`, `pi**2`, `sin(1)`, `2*I`) raises inside it, and the
application comes back unevaluated. The defect and its whole fix sit in one method,
`Function._eval_evalf` in `sympy/core/function.py`, in the branch taken when the function's name is
not an mpmath function. The literal path stays exactly as it is. Only where it fails, a return that
is a SymPy object or a Python `int`/`float`/`complex` is evaluated at the requested binary precision
by the product's own numeric evaluator. It is accepted only when the result is a number in the
spec's sense (a finite real, a complex with real parts, or `±inf`, but never `zoo` or `nan`).
Nesting needs no code of its own. Evaluating `r` reaches each inner application's
`_eval_evalf`, so any depth is covered. The `subs` case needs none either, because the evalf
dispatcher substitutes before it calls `_eval_evalf`. The mpmath-named branch and the method's
signature and return contract (an `Expr`, or `None` for "not a number") do not change. The tests go
in `sympy/core/tests/test_evalf.py`.

What crosses to the outside: nothing. The change stores nothing on a device, collects nothing, sends
nothing to a third party and publishes nothing. The patch lands in a local clone that is never pushed
(`project.md`, `Manages: none`). It reaches no presence surface, so it has no blast radius across
projects and no release step to keep.

---

## 2. Blast Radius

No `docs/SDD.md` § 3 parts table, `docs/nfdr.md`, `docs/adr/` or `docs/fdr.md` exists for this
product (`project.md`, `Definition: none`). So there is no part to place the new logic by. The
module set below is read from the product's source tree, and the import graph from the code.

| Module | Status | What changes |
|---|---|---|
| `sympy/core/` — `function.py` | Modified | `Function._eval_evalf`, non-mpmath branch: after the unchanged `Float(r, prec)` literal attempt fails, evaluate a return that is a SymPy object or a Python `int`/`float`/`complex` at binary precision `prec`, and return the result only when it is a number (CP-9, CP-10). Otherwise return `None`, as today (CP-11). An implementation's `TypeError`/`ValueError`/`AttributeError` still means "not a number". Every other exception propagates (CP-12). |
| `sympy/core/` — `evalf.py` | Unchanged | Consumed, not changed. Its dispatcher already reaches `Function._eval_evalf` through the fallback for functions missing from `evalf_table`, and it applies `subs` before doing so. Its module-level evaluator is what the new branch calls to tell whether `r` is a number. |
| `sympy/core/tests/` — `test_evalf.py` | Modified | New tests (§5). `test_implemented_function_evalf` stays as it is. |
| `sympy/utilities/lambdify.py` (`implemented_function`) | Unchanged | It attaches `_imp_`, as before. Its docstring ("numerical implementation to be called by `evalf()`") stays true. |
| `sympy/printing/codeprinter.py`, `sympy/printing/lambdarepr.py` | Unchanged | They read `_imp_` directly and never go through `_eval_evalf`. |

No transitive blast radius. The signature of `Function._eval_evalf(prec)` does not change, and
neither does its return contract (an `Expr`, or `None` for "not a number"). Its callers are the
evalf dispatcher's fallback and `EvalfMixin.evalf`'s fallback, and both read that contract unchanged.
No import surface changes.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `sympy/core/function.py` — `Function._eval_evalf`, non-mpmath branch | **Keep the existing literal path first and untouched.** Fall through to the new evaluation only when it raises one of its three exception types. Then every return that converts today converts the same way, by construction (CP-13), the `str` `"2"` row included. Call the implementation once, separately from the conversion. An implementation that raises one of the three types still means "not a number" and must not reach the new path. **Gate on type before sympifying:** a SymPy object, or a Python `int`/`float`/`complex`. A `str`, a `list` or `None` never enters, which is CP-11's boundary. **Test "is a number" with the module-level evaluator in `sympy/core/evalf.py`, never with `is_number`.** At base, `is_number` is `True` for `u(2)**2` and for `zoo`. The module-level evaluator raises `NotImplementedError` for both, and for anything with a free symbol, but it returns a value for `nan`, so `nan` has to be rejected explicitly. Evaluate at the binary `prec` the method receives, never as decimal digits. Build the returned value from the evaluator's parts with the same normalisation `EvalfMixin.evalf` applies to its own result. Then it agrees with `r.evalf(n)` because it is built the same way, not by coincidence (CP-9). Around the new evaluation, catch only `NotImplementedError` and the three types, and return `None` on any of them. Anything else propagates. That is how `f(z(2))`'s `ZeroDivisionError` comes out (CP-12, Gap 4). Import from `evalf.py` inside the method, as the branch already does for `MPMATH_TRANSLATIONS`. That avoids adding a module-level import between `function.py` and `evalf.py`. |

---

## 5. Test Additions

All rows go in `sympy/core/tests/test_evalf.py`, which the card's `Test command:` runs (CP-14, Gap 6),
beside `test_implemented_function_evalf`. Three new test functions are proposed. **Each one holds at
least one assertion that fails on the unchanged tree**, so each is red before the change and green
after it. Regression assertions (CP-11, CP-13) go inside them rather than in a test of their own,
which would be green at base (Architect Review Notes, *Every new test is red at base*). Printed
results are compared as strings wherever the spec pins digits. `str(Float)` is what the Examples table
records, and comparing `Float` values with `==` would not pin the digit count.

**Cache hazard (applies to every row).** `UndefinedFunction` compares equal by name, and applications
are cached. An `_imp_` left on `f`, `g` or any other name can leak into other tests that build
`Function('<same name>')`. That is the reason for the `del f._imp_` in the existing test. Every
implemented function a new test creates must have its `_imp_` removed when the test ends, even when
an assertion fails. Otherwise each test must use names that no other test in the run uses. **No name may be an mpmath
function or a key of `MPMATH_TRANSLATIONS`.** Such a function takes the mpmath branch and never
reaches the changed code. Probed at base: `implemented_function('ff', …)` goes to `mpmath.ff`. The
spec's names (`f`, `g`, `h`, `c`, `pc`, `p`, `s`, `z`, `k`, `w`, `F`, `u`) are all clear, and a
replacement name must be checked the same way.

| Sub-job | Test file | What to add / modify |
|---|---|---|
| `function.py` | `sympy/core/tests/test_evalf.py` | **New `test_implemented_function_evalf_composition`** (CP-9 nesting, CP-10, CP-14 issue lines). `str(f(2).evalf())` and `str(g(2).evalf())` are `4.00000000000000`, and `str(f(g(2)).evalf())` is `16.0000000000000`. `g(f(2))` is `8.00000000000000` and `f(g(f(2)))` is `64.0000000000000`. Precision and spelling: `f(g(2)).evalf(50)`, `N(f(g(2)))` and `f(g(2)).n(30)` print exactly as the Examples table records. Inside a larger expression and with `subs`: `(f(g(2)) + 1).evalf()` is `17.0000000000000`, and `f(g(x)).evalf(subs={x: 2})` is `16.0000000000000`. Creating or printing does not evaluate: `str(f(g(2)))` is `f(g(2))` (CP-13). |
| `function.py` | `sympy/core/tests/test_evalf.py` | **New `test_implemented_function_evalf_numeric_return`** (CP-9 non-literal and complex returns, CP-13, CP-14 second bullet). Numeric-expression returns: `f(pi).evalf()` is `9.86960440108936`, `h(1).evalf()` is `0.841470984807897`, `str(h(1).evalf(30)) == str(sin(1).evalf(30))`, and `str(f(h(1)).evalf(30)) == str((sin(1)**2).evalf(30))`, with both strings also matching the table. Complex returns: `c(2).evalf()` is `2.0*I`, `f(c(2)).evalf()` is `-4.00000000000000`, and `pc(2).evalf()` (Python `1j`) is `1.0*I`. Returns that convert today print the same (CP-13 rows): `f(2).evalf(50)` (51 digits as today), `p(2).evalf(50)` (Python `float` `math.pi`), `k(2).evalf(30)`, `f(Rational(1, 3)).evalf(30)`, `s(g(2)).evalf()` is `2.00000000000000`, and `F` returning `oo` / `-oo` prints `inf` / `-inf`. |
| `function.py` | `sympy/core/tests/test_evalf.py` | **New `test_implemented_function_evalf_not_a_number`** (CP-11, CP-12, CP-14 third bullet). These stay unevaluated: `f(x)`, `f(g(x))`, `f(u(2))` with `u = Function('u')`, and `w(2)` with `w` returning `x + Symbol('y')`. Each evalf equals the application itself. Inside a sum, `str((f(g(x)) + 1).evalf())` is `f(g(x)) + 1.0`. `F` returning `zoo`, `nan`, the `str` `"pi**2"`, a `list` or `None` gives `F(2)`. `F` returning the `str` `"2"` prints `2.00000000000000`. Exceptions: with `s` returning `math.sqrt(x)`, `s(-1).evalf()` is `s(-1)` and `f(s(-1)).evalf()` is `f(s(-1))`. With `z` returning `int(x) // 0`, `z(2).evalf()` raises `ZeroDivisionError`, and so does `f(z(2)).evalf()`. The last assertion is this test's red at base (Gap 4). |
| — | `sympy/core/tests/test_evalf.py` | **Unchanged: `test_implemented_function_evalf`.** Its four assertions stay as written (CP-15). |

**Coverage map.** Every Examples row maps to a cell above. The CP-14 rows (fail on the unchanged
tree, pass with the change) are met by the per-test red assertion named in the preamble. The CP-15
row (the card's `Test command:` exits 0 with only the 28 baseline failures) is the suite run itself,
not a test row. Edges implied by the rules: an empty or failing inner application (CP-11 `f(u(2))`,
CP-12 `f(s(-1))`) is covered by row 3. The `str` type boundary on both sides (`"pi**2"` and `"2"`) is
covered by row 3. Precision at more than one `n` for both a literal and an irrational return is
covered by rows 1 and 2. `subs` is covered by row 1.

**What this change stops proving:** nothing. No existing assertion is modified or removed.

---

## Records this change makes false

None. I checked for `docs/adr/`, `docs/nfdr.md`, `docs/fdr.md` and `docs/SDD.md` under the
product's change worktree, and none of them exists (`Definition: none`), so no record can go false.
The only nearby statement is the `implemented_function` docstring
(`sympy/utilities/lambdify.py`): "numerical implementation to be called by `evalf()`". The spec's
Verified Claims checked it, and it stays true.

---

## Architect Review Notes

- **Delegated-gate sweep (pre-flight):** there are no `nfdr.md` or `adr/` entries to sweep, so no
  record names a review at `development-design`. Nothing is inherited.
- **(b) "Is a number" is decided by the numeric evaluator, not by `is_number`:** the design names
  `sympy/core/evalf.py`'s module-level evaluator, plus an explicit rejection of `nan`, as the test of
  CP-9's "is a number". The reason is a probe at base. `u(2)**2` and `zoo` both report
  `is_number == True` and come back unchanged from `_evalf`, while the module-level evaluator raises
  `NotImplementedError` for both and returns a NaN part for `nan`. A check built on `is_number` would
  accept `f(u(2))` and a `zoo` return, contradicting CP-11.
- **(b) CP-13 holds because the literal path is kept, not because the new path happens to agree:** the
  existing `Float(r, prec)` attempt stays first and byte-identical, and the new evaluation runs only
  when it fails. So every return that converts today converts identically, because it takes the same
  code. A single evaluate-everything path would also have to treat the `str` `"2"` row as a
  special case, and CP-13 would then hold only as far as the two paths happened to agree.
- **(b) Agreement with `r.evalf(n)` comes from building the value the same way:** the new path
  evaluates at the binary precision `_eval_evalf` receives, and builds its value with
  `EvalfMixin.evalf`'s own normalisation. So CP-9's "agrees with `r.evalf(n)`" holds because the two
  values are built the same way, not by a rounding coincidence.
- **(b) Exceptions caught by the new path:** only `NotImplementedError` (the evaluator's "not a
  number") and CP-12's three types. Catching more would swallow `f(z(2))`'s `ZeroDivisionError`,
  which Gap 4 locks as propagating.
- **(b) Self-referential implementations are not guarded:** the spec says nothing about an
  implementation whose return contains its own application (`F` returning `F(x)`), or about two that
  return each other. Today such an application is left unevaluated. After the change, evaluating `r`
  recurses until Python's limit, and the `RecursionError` propagates under CP-12's second clause, as
  it would for any implementation that does not terminate. A depth guard would be new logic that no
  rule asks for, so the design adds none and pins none with a test.
- **(a) Every new test is red at base:** CP-14 says the change's tests "fail on the unchanged tree",
  yet it also requires them to cover CP-11's "stays unevaluated", which passes today. To satisfy both,
  each new test function holds at least one assertion that fails at base, and the regression
  assertions sit inside those functions (§5 preamble).
- **(d) No §3:** one module, one file, one method, with no internal seam and no ordering edge, so
  there is a single delta and the section is omitted.
- **Test file (Gap 6, delegated here):** `sympy/core/tests/test_evalf.py`. The defect is in evalf, the
  existing assertion of this behaviour lives there, and `test_lambdify.py` covers `lambdify`, which is
  out of scope.
- **Found while walking, not fixed:** the existing literal path passes the binary `prec` to `Float`
  as its second argument, which `Float` reads as decimal digits. Probed at base:
  `f(2)._eval_evalf(170)` carries 568 bits. Nothing printed shows it. The 51 digits of
  `f(2).evalf(50)` are how evalf prints any exact integer (`Integer(4).evalf(50)` prints the same),
  and the outer evalf rounds the extra precision away. So the quirk only makes the working
  precision higher than it needs to be. It is outside this issue. Changing it would touch a path
  CP-13 pins, and the request says to leave the rest of the product's behaviour as it is, which is
  the owner's decision in advance not to take it up here. The design keeps that path verbatim and
  does not repeat the quirk in the new path, which evaluates at binary `prec`.
