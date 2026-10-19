# Change Spec — evalf evaluates what an implemented function returns, including another implemented function

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Request:** "Fix the issue below in the product, the repository that the project card's
`Product path:` names (`sympy/sympy`). The repository stands at the commit before the issue was
fixed. Make the change the issue asks for, with tests of your own that show it, and leave the rest of
the product's behaviour as it is." The issue is `sympy__sympy-12096`, quoted in full in this folder's
`change_request.md` § *The issue*. Its constraints are that file's § *What must not be done*.
**Language resolution:** Python — step 1 (`project.md` `Languages:`) — `<CORE>/doctrine/engineering/languages/python/README.md` opened, and all six concerns it routes were read

---

## Change Summary

A function made with `sympy.utilities.lambdify.implemented_function` carries a Python implementation
that `evalf` calls. Today `evalf` turns the implementation's return value into a number only when that
value is already a numeric literal. When the return is a number written as an expression, the
application comes back unevaluated. That expression may hold another implemented application, as with
`f(g(2))` in the issue, or be something like `pi**2`, `sin(1)` or `2*I`. After this change `evalf`
evaluates such a return to the requested precision, through any depth of nesting. Returns that are
not numbers stay unevaluated, as they do today.

**Terms used below.** An **implemented function** is one returned by `implemented_function(name,
implementation)`. An **application** is that function applied to arguments, e.g. `f(g(2))`. The
application's **return** `r` is what its implementation returns when called on the application's
arguments. **evalf** means `expr.evalf(n)` and its other spellings, `expr.n(n)` and `N(expr, n)`;
`n` defaults to 15 significant digits. A **number** is what `evalf` gives for a numeric expression: a
finite real `Float`, a complex value `a + b*I` with `Float` parts (`sin(I).evalf()` prints
`1.1752011936438*I`), or `inf` / `-inf`. `zoo` and `nan` are not numbers here.

---

## Rules

### evalf of an implemented-function application — a return that is a number

- **CP-9:** When an application's return `r` is a SymPy expression or a Python `int`, `float` or
  `complex`, and `r` evaluated with evalf at the requested precision is a number, evalf of the
  application returns that number. This holds for:
  - a return that holds further implemented applications, at any depth (`f(g(2))`, `f(g(f(2)))`);
  - a return that is a numeric expression rather than a literal (`pi**2`, `sin(1)`);
  - a complex return (`2*I`), whether the implementation returns a SymPy expression or a Python
    `complex`.

  The result agrees with `r.evalf(n)` to within one unit in its `n`-th significant digit. For every
  row of the Examples table, the printed results are identical.

  This is a rule because of a present defect. `sympy/core/function.py` line 510 passes the return
  straight to `Float(r, prec)`. That raises `TypeError` for any non-literal number (`cannot create
  mpf from g(2)**2`, also for `pi**2` and `2*I`), and the application is then returned unevaluated.
- **CP-10:** The same holds wherever the application sits inside a larger expression, and when evalf
  is given `subs`. `(f(g(2)) + 1).evalf()` is `17.0000000000000`. `f(g(x)).evalf(subs={x: 2})` is
  `16.0000000000000`, as `f(x).evalf(subs={x: 2})` is `4.00000000000000` today.

### evalf of an implemented-function application — a return that is not a number

- **CP-11:** When `r`, evaluated with evalf, is not a number, evalf returns the application
  unevaluated, as it does today. That covers a return holding a free symbol (`f(x)`, `f(g(x))`), an
  application of a function with no implementation (`f(u(2))` with `u = Function('u')`), and
  `zoo` or `nan`. A return of any other Python type (a `str`, a `list`, `None`) is outside CP-9 and
  keeps today's outcome: a `str` `"pi**2"` leaves the application unevaluated, and a `str` `"2"`
  prints `2.00000000000000`, both as today. Inside a larger expression the application stays as written and the rest evaluates:
  `(f(g(x)) + 1).evalf()` is `f(g(x)) + 1.0`.
- **CP-12:** When an implementation that evalf calls raises, the outcome follows the exception's
  type. This holds for the outer application's implementation and for any inner one reached while
  evaluating `r`:
  - `TypeError`, `ValueError` or `AttributeError`: the application it belongs to is not a number.
    It is left unevaluated, as today, and CP-11 then applies to anything holding it. With
    `s = implemented_function('s', lambda x: math.sqrt(x))`, `s(-1).evalf()` is `s(-1)` and
    `f(s(-1)).evalf()` is `f(s(-1))`.
  - Any other exception propagates out of evalf with its own type, as it does today when evalf
    reaches that implementation inside any other expression. With
    `z = implemented_function('z', lambda x: int(x) // 0)`, `z(2).evalf()` and `(z(2) + 1).evalf()`
    raise `ZeroDivisionError` today. After this change, `f(z(2)).evalf()` raises `ZeroDivisionError`
    too (see Locked Answers, Gap 4).

### Nothing else changes

- **CP-13:** Every application whose evalf returns a number today returns the same printed result,
  at the same precision. Examples are `f(2).evalf(50)`, a Python-`float` return such as
  `p = implemented_function('p', lambda x: math.pi)` with `p(2).evalf(50)`, `oo` returns, and
  `s(g(2)).evalf()`. Creating or printing an application does not evaluate it: `str(f(g(2)))` is
  `f(g(2))`. An implemented function whose name is also an mpmath function keeps today's behaviour,
  whatever it is (Out of Scope).

### Proof

- **CP-14:** The change carries tests of its own that the card's `Test command:` runs. They fail on
  the unchanged tree and pass with the change. Together they cover at least:
  - the issue's three lines: `f(2).evalf()` and `g(2).evalf()` print `4.00000000000000`, and
    `f(g(2)).evalf()` prints `16.0000000000000`;
  - a return that is a numeric expression with no composition, such as `f(pi)` or `h(1)` with
    `h = implemented_function('h', lambda x: sin(x))`;
  - a return that is not a number staying unevaluated (CP-11), such as `f(g(x)).evalf() == f(g(x))`.
- **CP-15:** The card's `Test command:` exits 0. Its run fails only the 28 tests that
  `change_request.md` § *What must not be done* lists. `test_implemented_function_evalf` in
  `sympy/core/tests/test_evalf.py` still passes, with its four assertions unchanged.

---

## Examples

Definitions used in the rows: `x = Symbol('x')`, `u = Function('u')`, and implemented functions
`f = x**2`, `g = 2*x`, `h = sin(x)`, `c = x*I`, `pc = 1j` (Python `complex`), `p = math.pi` (Python
`float`), `s = math.sqrt(x)`, `z = int(x) // 0`, `k = x/3`, and `F` returning the value its row
names (`zoo`, `nan`, `oo`, a `str`, …).
"Today" is the printed result at `base_commit`. "Expected" is the printed result after the change.
Both were run on 2026-10-11 (Verified Claims).

| Rule | Scenario | Today | Expected behavior |
|---|---|---|---|
| CP-9 | `f(g(2)).evalf()` (the issue) | `f(g(2))` | `16.0000000000000` |
| CP-9 | `g(f(2)).evalf()` | `g(f(2))` | `8.00000000000000` |
| CP-9 | `f(g(f(2))).evalf()` | `f(g(f(2)))` | `64.0000000000000` |
| CP-9 | `f(g(2)).evalf(50)` | `f(g(2))` | `16.000000000000000000000000000000000000000000000000` |
| CP-9 | `N(f(g(2)))` | `f(g(2))` | `16.0000000000000` |
| CP-9 | `f(g(2)).n(30)` | `f(g(2))` | `16.0000000000000000000000000000` |
| CP-9 | `f(pi).evalf()` | `f(pi)` | `9.86960440108936`, as `(pi**2).evalf()` |
| CP-9 | `h(1).evalf()` | `h(1)` | `0.841470984807897` |
| CP-9 | `h(1).evalf(30)` | `h(1)` | `0.841470984807896506652502321630`, as `sin(1).evalf(30)` |
| CP-9 | `f(h(1)).evalf(30)` | `f(h(1))` | `0.708073418273571193498784114750`, as `(sin(1)**2).evalf(30)` |
| CP-9 | `c(2).evalf()` | `c(2)` | `2.0*I` |
| CP-9 | `f(c(2)).evalf()` | `f(c(2))` | `-4.00000000000000` |
| CP-9 | `pc(2).evalf()` | `pc(2)` | `1.0*I` |
| CP-10 | `(f(g(2)) + 1).evalf()` | `f(g(2)) + 1.0` | `17.0000000000000` |
| CP-10 | `f(g(x)).evalf(subs={x: 2})` | `f(g(x))` | `16.0000000000000` |
| CP-11 | `f(x).evalf()` | `f(x)` | `f(x)` |
| CP-11 | `f(g(x)).evalf()` | `f(g(x))` | `f(g(x))` |
| CP-11 | `(f(g(x)) + 1).evalf()` | `f(g(x)) + 1.0` | `f(g(x)) + 1.0` |
| CP-11 | `f(u(2)).evalf()` | `f(u(2))` | `f(u(2))` |
| CP-11 | `w(2).evalf()`, `w = implemented_function('w', lambda x: x + Symbol('y'))` | `w(2)` | `w(2)` |
| CP-11 | `F(2).evalf()`, `F` returning `zoo` / `nan` | `F(2)` | `F(2)` |
| CP-11 | `F(2).evalf()`, `F` returning the `str` `"pi**2"` / a `list` / `None` | `F(2)` | `F(2)` |
| CP-11 | `F(2).evalf()`, `F` returning the `str` `"2"` | `2.00000000000000` | `2.00000000000000` |
| CP-12 | `s(-1).evalf()` (`ValueError`) | `s(-1)` | `s(-1)` |
| CP-12 | `f(s(-1)).evalf()` | `f(s(-1))` | `f(s(-1))` |
| CP-12 | `z(2).evalf()` | raises `ZeroDivisionError` | raises `ZeroDivisionError` |
| CP-12 | `f(z(2)).evalf()` | `f(z(2))` | raises `ZeroDivisionError` — see Locked Answers, Gap 4 |
| CP-13 | `f(2).evalf()`, `g(2).evalf()` | `4.00000000000000` | `4.00000000000000` |
| CP-13 | `f(2).evalf(50)` | `4.0000000000000000000000000000000000000000000000000` | unchanged |
| CP-13 | `p(2).evalf(50)` | `3.1415926535897931159979634685441851615905761718750` | unchanged |
| CP-13 | `k(2).evalf(30)` | `0.666666666666666666666666666667` | unchanged |
| CP-13 | `f(Rational(1, 3)).evalf(30)` | `0.111111111111111111111111111111` | unchanged |
| CP-13 | `s(g(2)).evalf()` | `2.00000000000000` | unchanged |
| CP-13 | `F(2).evalf()`, `F` returning `oo` / `-oo` | `inf` / `-inf` | unchanged |
| CP-13 | `str(f(g(2)))`, no evalf | `f(g(2))` | `f(g(2))` |
| CP-14 | the change's own tests, run on the unchanged tree | — | they fail |
| CP-14 | the change's own tests, run with the change | — | they pass |
| CP-15 | the card's `Test command:` run with the change | exit 0, 28 baseline failures | exit 0; the only failures are the 28 baseline tests; `test_implemented_function_evalf` passes |

---

## Verified Claims

Every run below was made on 2026-10-11 with the card's interpreter (`/home/kensai/issue-venv`,
Python 3.9.25). "Base" means the product's change worktree for this key, which is opened from the
repository named by the card's `Product path:`, at `base_commit`, with no change applied. Each probe
printed `sympy.__file__` to confirm which tree it imported. "Candidate" means a disposable copy of that
tree (`git archive HEAD` into a scratch folder outside every checkout), changed in one place to
evaluate a return that is a SymPy expression or a Python `int`/`float`/`complex`, and imported via
`PYTHONPATH`. A first candidate that also converted `str` returns printed `9.86960440108936` for the
`"pi**2"` row. That is why CP-11 states the type boundary, and every *Expected* claim below was re-run
on the second candidate. The candidate shows that the rules can all hold at
once. It is not a design. Nothing outside the repository was consulted: no upstream history, no pull
request, no benchmark copy.

| Claim | Verified by | What came back |
|---|---|---|
| Every *Today* cell of the Examples table | ran each scenario at base | as written in the table. `f(g(2)).evalf()` printed `f(g(2))`, and `f(2).evalf()` and `g(2).evalf()` printed `4.00000000000000`, matching the issue |
| The defect site: `sympy/core/function.py` line 510 is `return Float(self._imp_(*self.args), prec)`, inside an `except (AttributeError, KeyError)` branch, and its own `TypeError`/`ValueError`/`AttributeError` makes `_eval_evalf` return nothing | read `sympy/core/function.py` lines 500–513; ran `Float(g(2)**2, 53)`, `Float(pi**2, 53)`, `Float(2*I, 53)` at base | line confirmed. All three raised `TypeError: cannot create mpf from …` |
| evalf of the return written directly already gives the number at base, so the gap is only in the application's own evaluation | ran `(g(2)**2).evalf()` at base | `16.0000000000000` |
| Every *Expected* cell of the Examples table can hold together, and the precision rows print identically to `r.evalf(n)` | ran every scenario on the candidate | as written in the table, including `h(1).evalf(30)` = `sin(1).evalf(30)` and `f(h(1)).evalf(30)` = `(sin(1)**2).evalf(30)` digit for digit |
| Base propagates an implementation's non-caught exception wherever evalf reaches it (CP-12, Gap 4) | ran `(z(2)+1).evalf()`, `(z(2)**2).evalf()`, `sin(z(2)).evalf()` at base | each raised `ZeroDivisionError: integer division or modulo by zero` |
| Exactly-cancelling numeric returns are evalf's general behaviour, not this change's (Out of Scope) | ran at base: `(1/(g(1)-2)).evalf()`, `(1/(sin(1)**2+cos(1)**2-1)).evalf()`; on the candidate: `q(g(1)).evalf()` with `q = 1/(x-2)` | base `7.26838724295607e+134` and `-3.63419362147803e+134`; candidate `1.52429128433398e+141`. `q(2).evalf()` is `q(2)` on both |
| The product already asserts that a symbolic return stays unevaluated (CP-11) | read `sympy/core/tests/test_evalf.py` lines 320–328, `test_implemented_function_evalf` | asserts `f(2).evalf() == 3` and `f(x).evalf() == f(x)` for `f = x + 1` |
| The card's `Test command:` runs `sympy/core/tests/test_evalf.py` and `sympy/utilities/tests/test_lambdify.py` only | read `/home/kensai/issue-test.sh`, which runs `/home/kensai/issue-suite.sh` | `python -m pytest -rfE -p no:cacheprovider sympy/core/tests/test_evalf.py sympy/utilities/tests/test_lambdify.py` |
| The card's `Test command:` passes at base with exactly the 28 baseline failures | ran `/home/kensai/issue-test.sh` from the base worktree root | `28 failed, 90 passed`, `issue-test: only baseline failures remain (28 known at base_commit)`, exit 0. `git status --short` empty afterwards |
| The candidate breaks no test the command runs | ran `/home/kensai/issue-test.sh` from the scratch copy, `PYTHONPATH` on it | `28 failed, 90 passed`, `only baseline failures remain`, exit 0 |
| The product's docs do not state how evalf treats an implemented function's return | `git grep -n implemented_function -- doc/`; read the `implemented_function` docstring, `sympy/utilities/lambdify.py` lines 655–700 | one mention, in `doc/src/modules/numeric-computation.rst` line 85, about `binary_function`. The docstring says only "numerical implementation to be called by `evalf()` or `lambdify`", which stays true |
| The product holds no `CP-<n>` label, so the series continues from the trail's CP-8 | `git grep -nE '\bCP-[0-9]+\b'` in the product worktree; grep of `journey/tobiishi/trail/` | none in the product; highest in the trail `CP-8` |
| Language rendering | no rule pins output that renders a language-level fact. Every printed value is SymPy's own `Float`/expression printing, which the product chooses. CP-12 pins that an exception propagates, not how it is shown | — |

---

## Out of Scope

- **The 28 baseline failures.** They stay failing, as `change_request.md` § *What must not be done*
  requires. No other test that fails today is touched.
- **Returns that lose significance by exact cancellation**, such as `q(g(1))` with
  `q = implemented_function('q', lambda x: 1/(x - 2))`. Evaluated directly, such a return already gives
  a meaningless large value at base, for example `(1/(sin(1)**2+cos(1)**2-1)).evalf()`. This change
  promises nothing for them beyond CP-9's "is a number". How evalf handles cancellation is product-wide
  and not this issue.
- **Implemented functions whose name is also an mpmath function** (e.g. `implemented_function('sin',
  …)`). Their evalf is not part of this change, and CP-13 keeps it as it is.
- **`lambdify`, `autowrap.binary_function` and `implemented_function` itself.** Their behaviour does not
  change. `lambdify(x, f(g(x)))(2)` already returns `16`.
- **evalf options other than precision and `subs`** (`chop`, `strict`, `maxn`, `verbose`). They keep
  whatever they do today.
- **Functions defined by subclassing `Function`.** This change is about implemented functions only.
- **Documentation and release notes.** The request asks for none, and the docs do not state the fact
  that changes (Verified Claims). I did not look at other surfaces such as the tutorial, the
  StackOverflow answer the issue cites, or the release notes.
- **Anything outside the local clone.** The patch is not pushed (`project.md`, `Manages: none`), and
  nothing is published. As the request says, no record, grade or benchmark file is produced.

---

## Locked Answers (the divergence record — self-review 2026-10-11)

- **Gap 1: the rule covers every number-valued return, not only composition (CP-9).** The issue's
  example is `f(g(2))`, but its diagnosis is that `evalf` is not applied to "the return of `_imp_`".
  `f(pi)`, `h(1)` (returns `sin(1)`) and `c(2)` (returns `2*I`) are unevaluated today for that same
  reason (Verified Claims, the defect site). A fix scoped only to nesting would leave the cause the
  issue names in place. The rule is reversible, since it changes printed values and no stored data.
- **Gap 2: complex returns are numbers (CP-9).** The issue shows only real values. A complex return is
  turned into a number because evalf already does that for complex-valued applications elsewhere
  (`sin(I).evalf()` is `1.1752011936438*I`). A nested complex value can also make a real result, as
  in `f(c(2))` = `-4.00000000000000`, which a real-only rule would leave unevaluated for no
  observable reason. `zoo` and `nan` stay non-numbers because their applications are unevaluated
  today (`F(2)`), and nothing in the issue asks to change that.
- **Gap 3: a return that is not a number stays unevaluated (CP-11).** The issue says nothing about
  symbolic returns. The request says to leave the rest of the behaviour as it is. The product's own
  test (`test_implemented_function_evalf`) asserts `f(x).evalf() == f(x)`. So `f(x)` and `f(g(x))`
  keep today's output, and evalf does not substitute an implementation's symbolic result for the
  application. Returns of other Python types are outside the rule for the same reason. `F(2)` with a
  `str` return `"pi**2"` is unevaluated today, and turning text into an expression is not what the
  issue asks for.
- **Gap 4: an inner implementation's uncaught exception now propagates (CP-12).** `f(z(2)).evalf()`
  returns `f(z(2))` today only because the defect stops evalf from ever calling `z`. Wherever else
  evalf reaches `z`, for example `(z(2)+1)`, `z(2)**2` or `sin(z(2))`, it raises `ZeroDivisionError`
  today. The rule makes the composition behave like those, rather than adding a new place where an
  exception is silently swallowed. This is a stated change from today for one shape. It is
  reversible.
- **Gap 5: precision is pinned within one unit in the last digit, and exactly for the Examples rows
  (CP-9).** The issue does not mention precision. The rule requires the requested precision to be
  honoured, since a composition evaluated at fixed double precision would print `16` correctly but
  fail at `evalf(50)` for an irrational return. It also does not pin a last-digit rounding that no
  reader could verify ahead of the design. Every Examples row prints identically on the candidate.
- **Gap 6: the change's tests are ones the card's `Test command:` runs, and existing assertions hold
  (CP-14, CP-15).** The request asks for "tests of your own" without saying where they run. The
  command runs only two test files (Verified Claims), and a test it does not run proves nothing at
  this change's gate. Which of the two files holds the tests is development-design's decision.
  `test_implemented_function_evalf` is named because it states CP-11's behaviour today and must stay
  as it is.
