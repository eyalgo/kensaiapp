# Change Spec — Reversed limits invert an axis on a log scale

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Request:** "Fix the issue below in the product, the repository that the project card's
`Product path:` names (`matplotlib/matplotlib`). The repository stands at the commit before the issue was
fixed. Make the change the issue asks for, with tests of your own that show it, and leave the rest of
the product's behaviour as it is." The issue is `matplotlib__matplotlib-14623`, "Inverting an axis
using its limits does not work for log scale", quoted in full in this folder's `change_request.md`
§ *The issue*. Its constraints are that file's § *What must not be done*.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with the five files it routes and `testing_python.md`

---

## Change Summary

`Axes.set_xlim` and `Axes.set_ylim` say in their docstrings that "Limits may be passed in reverse
order to flip the direction of the axis". On a `log` axis they do not. The descending pair comes back
ascending, and the axis is not inverted. After this change a descending pair keeps its order on a
`log` axis, as it already does on a `linear` one. The same holds on the two other built-in scales
that lose it today, `functionlog` and `logit`, and for the paths that already rely on that promise:
`set_xbound`/`set_ybound`, and autoscaling an inverted axis.

**Terms used below.**

- An axis's **limits** are the pair that `get_xlim()` returns for the x-axis, `(left, right)`, and
  that `get_ylim()` returns for the y-axis, `(bottom, top)`.
- A pair is **descending** when its first value is greater than its second.
- An axis is **inverted** when `xaxis_inverted()` (or `yaxis_inverted()`) returns `True`. Today that
  happens exactly when its limits are descending, and this change keeps it that way.
- The **covered scales** are the three built-in scales that lose the order today: `log`,
  `functionlog` and `logit`. A covered scale's **domain** is the values above 0 for `log` and
  `functionlog`, and the values strictly between 0 and 1 for `logit`.
- The **resolved pair** is what the call works with after its arguments are read. Each limit is
  the one passed, or the axis's current limit where none is passed. On a `log` axis, a non-positive
  limit is also replaced by the current limit (CP-11).

Everything below holds for the x-axis and the y-axis alike. A `set_ylim` example stands for its
`set_xlim` counterpart.

---

## Rules

### Setting limits in reverse order

- **CP-9:** On an axis with a covered scale, `set_xlim`/`set_ylim` given a descending pair inside the
  scale's domain leaves the axis with that pair, in that order. Afterwards `get_xlim()`/`get_ylim()`
  returns it, the axis is inverted, and the call's return value is the same pair in the same order.
  This holds for every argument form the methods accept:
  - two positional values, e.g. `set_ylim(100, 1)`;
  - one 2-tuple, e.g. `set_ylim((100, 1))`;
  - the keywords `left`/`right` and `bottom`/`top`;
  - the keywords `xmin`/`xmax` and `ymin`/`ymax`.

  It holds whether or not the Axes has data, and for any `log` base (e.g. `basey=2`). The cause is a
  present defect. On `log` and `functionlog` axes the descending pair is put in ascending order at
  `lib/matplotlib/ticker.py` lines 2382–2383 (`LogLocator.nonsingular`). On `logit` axes the same
  happens at lines 2627–2628 (`LogitLocator.nonsingular`). `set_xlim` (`lib/matplotlib/axes/_base.py`
  line 3267) and `set_ylim` (line 3647) pass the limits through those lines. So today the issue's
  `log` reproduction gets `(1.0, 100000.0)` back from `set_ylim(100000.0, 1.0)`, and
  `yaxis_inverted()` returns `False`.
- **CP-10:** When the call passes only one limit, the result keeps the order of the resolved pair, on
  a covered scale as on `linear` today. An axis at `(100, 1)` given `set_ylim(top=10)` ends at
  `(100, 10)`, still inverted. An axis at `(1, 100)` given `set_ylim(top=0.5)` ends at `(1, 0.5)`,
  inverted.
- **CP-11:** A non-positive limit passed to an axis whose scale is `log` is still ignored with
  today's warning, the text unchanged. For a bottom limit it is
  `Attempted to set non-positive bottom ylim on a log-scaled axis.\nInvalid limit will be ignored.`,
  and likewise for `top`, `left` and `right`. The current limit stands in for the ignored one, and
  the result keeps the order of the resolved pair. An axis at `(1, 100)` given `set_ylim(1000, -1)`
  warns about `top` and ends at `(1000, 100)`, inverted. An axis at `(0.79…, 125.89…)` given
  `set_ylim(50, 0)` ends at `(50, 125.89…)`, not inverted. That is today's result.
- **CP-12:** Equal limits keep today's result on a covered scale. The call warns
  `Attempting to set identical bottom == top == <value> results in singular transformations; automatically expanding.`
  as it does today. The limits it ends with are today's, which are ascending. A `log` axis given
  `set_ylim(10, 10)` ends at `(1.0, 100.0)`.

### An inversion the axis already has is kept

- **CP-13:** On an axis with a covered scale, an inverted axis stays inverted through the two paths
  that keep it on `linear` today:
  - `set_xbound`/`set_ybound` honour the axis's inversion whatever order their arguments come in, as
    their docstrings say ("This method will honor axes inversion regardless of parameter order").
    An inverted `log` y-axis given `set_ybound(1, 100)` ends at `(100, 1)`. An axis that is not
    inverted stays that way: a `log` y-axis given `set_ybound(100, 1)` ends at `(1, 100)`.
  - When an axis is inverted with `invert_xaxis()`/`invert_yaxis()` while autoscaling is on, plotting
    data afterwards autoscales it to a descending pair, and the axis stays inverted. A `log` y-axis
    inverted before `plot([0, 1, 2], [1, 10, 100])` ends descending, with `yaxis_inverted()` `True`.
- **CP-14:** Axes that share the axis show the same limits in the same order. With
  `plt.subplots(2, sharey=True)`, a `log` y-axis on the first Axes given `set_ylim(100, 1)` leaves both
  Axes at `(100.0, 1.0)`.
- **CP-15:** Nothing else about limits changes. In particular:
  - An ascending pair on a covered scale ends with today's values.
  - The `linear`, `symlog` and `function` scales keep today's behaviour, which already meets CP-9 to
    CP-14.
  - Drawing the figure does not change the limits' order.
  - Changing the axis's scale with `set_xscale`/`set_yscale` keeps the order the limits already had.

### Proof

- **CP-16:** The change carries tests of its own that the card's `Test command:` runs. They fail on
  the unchanged tree and pass with the change. Together they cover at least:
  - the issue's reproduction, a `log` y-axis given `set_ylim(y.max(), y.min())`, ending descending
    and inverted;
  - a `log` x-axis given `set_xlim` with a descending pair;
  - a `logit` axis given a descending pair;
  - `set_ybound` (or `set_xbound`) on an inverted `log` axis.
- **CP-17:** The card's `Test command:` exits 0, and the only failures in its run are the 112 tests
  that fail at `base_commit`, listed in its baseline. This change fixes none of them, and no other
  test fails.

---

## Examples

"Today" is the result at `base_commit`, run on 2026-10-11 (see Verified Claims). Unless a row says
otherwise, the Axes holds data plotted from `[1, 100]`, or from `[0.2, 0.8]` on `logit`, and is
shown with its limits set as the row says.

| Rule | Scenario | Today | Expected behavior |
|---|---|---|---|
| CP-9 | The issue's reproduction, `log` y-axis: `set_ylim(100000.0, 1.0)` | returns and holds `(1.0, 100000.0)`, not inverted | returns and holds `(100000.0, 1.0)`, inverted |
| CP-9 | The issue's reproduction, `linear` y-axis | `(100000.0, 1.0)`, inverted | unchanged |
| CP-9 | `log` x-axis: `set_xlim(100, 1)` | returns `(1, 100)`, holds `(1.0, 100.0)`, not inverted | returns `(100, 1)`, holds `(100.0, 1.0)`, inverted |
| CP-9 | `log` y-axis: `set_ylim((100, 1))` | `(1.0, 100.0)` | `(100.0, 1.0)` |
| CP-9 | `log` y-axis: `set_ylim(bottom=100, top=1)` | `(1.0, 100.0)` | `(100.0, 1.0)` |
| CP-9 | `log` y-axis: `set_ylim(ymin=100, ymax=1)` | `(1.0, 100.0)` | `(100.0, 1.0)` |
| CP-9 | `log` x-axis: `set_xlim(left=100, right=1)` | `(1.0, 100.0)` | `(100.0, 1.0)` |
| CP-9 | `log` y-axis with no data: `set_ylim(100, 1)` | `(1.0, 100.0)` | `(100.0, 1.0)` |
| CP-9 | `log` y-axis, `basey=2`: `set_ylim(64, 2)` | `(2.0, 64.0)` | `(64.0, 2.0)` |
| CP-9 | `functionlog` y-axis: `set_ylim(100, 1)` | `(1.0, 100.0)` | `(100.0, 1.0)` |
| CP-9 | `logit` y-axis: `set_ylim(0.9, 0.1)` | `(0.1, 0.9)` | `(0.9, 0.1)` |
| CP-10 | `log` y-axis at `(100, 1)`: `set_ylim(top=10)` | `(1.0, 10.0)` (the axis was never inverted) | `(100.0, 10.0)` |
| CP-10 | `log` y-axis at `(1, 100)`: `set_ylim(top=0.5)` | `(0.5, 1.0)` | `(1.0, 0.5)`, inverted |
| CP-10 | `log` y-axis at `(100, 1)`: `set_ylim(1, 100)` | `(1.0, 100.0)` | `(1.0, 100.0)`, not inverted |
| CP-11 | `log` y-axis at `(1, 100)`: `set_ylim(1000, -1)` | warns (top), `(100.0, 1000.0)` | warns (top, same text), `(1000.0, 100.0)` |
| CP-11 | `log` y-axis at `(0.79…, 125.89…)`: `set_ylim(50, 0)` | warns (top), `(50.0, 125.89…)` | unchanged |
| CP-11 | `log` y-axis: `set_ylim(-1, 1)` | warns (bottom), `(0.79…, 1.0)` | unchanged |
| CP-12 | `log` y-axis at `(1, 100)`: `set_ylim(10, 10)` | warns, `(1.0, 100.0)` | unchanged |
| CP-13 | `log` y-axis, `invert_yaxis()`, then `set_ybound(1, 100)` | `(1.0, 100.0)` | `(100.0, 1.0)` |
| CP-13 | `log` y-axis, not inverted: `set_ybound(100, 1)` | `(1.0, 100.0)` | unchanged |
| CP-13 | Empty `log` y-axis, `invert_yaxis()`, then `plot([0, 1, 2], [1, 10, 100])` | `(0.79…, 125.89…)`, not inverted | `(125.89…, 0.79…)`, inverted |
| CP-13 | Empty `logit` y-axis, `invert_yaxis()`, then `plot([0, 1, 2], [0.2, 0.3, 0.8])` | `(0.178…, 0.821…)`, not inverted | `(0.821…, 0.178…)`, inverted |
| CP-14 | `plt.subplots(2, sharey=True)`, first Axes `log`: `set_ylim(100, 1)` | both `(1.0, 100.0)` | both `(100.0, 1.0)` |
| CP-15 | `log` y-axis: `set_ylim(1, 100)` | `(1.0, 100.0)`, not inverted | unchanged |
| CP-15 | `symlog` y-axis: `set_ylim(100, 1)` | `(100.0, 1.0)` | unchanged |
| CP-15 | `linear` y-axis: `set_ylim(100, 1)` | `(100.0, 1.0)` | unchanged |
| CP-15 | `log` y-axis: `set_ylim(100, 1)`, then `fig.canvas.draw()` | `(1.0, 100.0)`, not inverted | `(100.0, 1.0)`, inverted |
| CP-15 | `linear` y-axis: `set_ylim(100, 1)`, then `set_yscale('log')` | `(100.0, 1.0)` | unchanged |
| CP-15 | `log` y-axis: `set_ylim(100, 1)`, then `set_yscale('linear')` | `(1.0, 100.0)` | `(100.0, 1.0)` |
| CP-16 | the change's own tests, run on the unchanged tree | — | they fail |
| CP-16 | the change's own tests, run with the change | — | they pass |
| CP-17 | the card's `Test command:` run with the change | exit 0, 112 baseline failures | exit 0, the same 112 failures and no other |

---

## Verified Claims

Every run below was made on 2026-10-11 in the product's change worktree for this key. That worktree
is opened from the repository the card's `Product path:` names, at `base_commit` (`d65c9ca20`), with
no change applied. The runs used the card's interpreter (`/home/kensai/issue-venv/bin/python`,
Python 3.8.20, numpy 1.24.4), which imports `matplotlib` from that worktree, with the `agg` backend.
Nothing outside the repository was consulted: no upstream history, no pull request, no benchmark
copy. The scratch probe named below lived in `/tmp`, outside the product tree, and the worktree was
clean after every run (`git status --short` printed nothing).

No rule pins output that renders a language-level fact. Every value and message the rules pin is
one matplotlib chooses, so no *Language rendering* row is owed.

| Claim | Verified by | What came back |
|---|---|---|
| The issue reproduces at base: a descending pair comes back ascending on `log` and is kept on `linear` | ran the issue's code, printing the return value of `set_ylim`, `get_ylim()` and `yaxis_inverted()` | `linear`: `(100000.0, 1.0)`, `(100000.0, 1.0)`, `True`. `log`: `(1.0, 100000.0)`, `(1.0, 100000.0)`, `False` |
| Every *Today* cell in the Examples | ran each row's scenario (`/tmp/probe14623/rows.py`, `ood.py`, `corner.py`, without the probe) and printed `get_*lim()`, `*axis_inverted()` and any warning text | each row as written under *Today*, warning texts included |
| `functionlog` and `logit` lose the order too, and `symlog`, `linear` and `function` keep it | same runs, plus `function` with `functions=(np.sqrt, np.square)` | `functionlog` `(1.0, 100.0)`, `logit` `(0.1, 0.9)`. `symlog` `(100.0, 1.0)`, `linear` `(100.0, 1.0)`, `function` `(100.0, 1.0)` |
| The built-in scales at base are six | `matplotlib.scale.get_scale_names()` | `['function', 'functionlog', 'linear', 'log', 'logit', 'symlog']` |
| The present defect sits where CP-9 says | read `lib/matplotlib/ticker.py` lines 2378–2399 and 2622–2650, and `lib/matplotlib/axes/_base.py` lines 3250–3267 and 3622–3664 | `if vmin > vmax: vmin, vmax = vmax, vmin` at ticker 2382–2383 (`LogLocator.nonsingular`) and 2627–2628 (`LogitLocator.nonsingular`). `set_xlim` calls the locator's `nonsingular` at _base 3267, and `set_ylim` at 3647. The base `Locator.nonsingular` (ticker 1523–1525) passes `increasing=False` and keeps the order |
| The docstrings promise what CP-9 and CP-13 state | read `set_xlim` (_base 3220–3226), `set_ylim` (3599–3605) and `set_ybound` (3477–3482) | "Limits may be passed in reverse order to flip the direction of the x-axis" (and "y-axis"). "This method will honor axes inversion regardless of parameter order." |
| `invert_yaxis` and `set_ybound` reach the limits through `set_ylim` | read `invert_yaxis` (_base 3435–3445, which calls `Axis.set_inverted`, axis.py 999–1011) and `set_ybound` (3496–3510) | `set_ybound` on an inverted axis calls `set_ylim(upper, lower, auto=None)`. `set_inverted` sets the view interval directly, and that is why `invert_yaxis` alone inverts a `log` axis today |
| CP-9 to CP-15 can all be met at once, and no test the card runs changes its result | scratch probe outside the tree (`/tmp/probe14623/orderprobe.py`), loaded only for these runs. It wraps the two locators' `nonsingular` so that a descending pair comes back descending. It shows the rules are consistent. It is not a design | every *Expected behavior* cell for CP-9 to CP-15 matched. `pytest -p orderprobe lib/matplotlib/tests/test_axes.py`: `112 failed, 402 passed, 140 skipped`, and the failure set equals `/home/kensai/issue-baseline.txt`. `test_ticker.py` (313 passed), `test_scale.py` (12 passed, 2 skipped) and `test_transforms.py` (1 failed, 36 passed) gave the same counts with and without the probe |
| The card's `Test command:` passes at base, with exactly the 112 baseline failures | ran `/home/kensai/issue-test.sh` from the product worktree root | `112 failed, 402 passed, 140 skipped`, `issue-test: only baseline failures remain (112 known at base_commit)`, exit 0 |
| The card's `Test command:` runs only `lib/matplotlib/tests/test_axes.py` | read `/home/kensai/issue-suite.sh`, which `/home/kensai/issue-test.sh` calls | `python -m pytest -rfE -p no:cacheprovider lib/matplotlib/tests/test_axes.py` |
| Out-of-domain limits on `logit` give results whose order does not follow the order passed (Out of Scope) | `corner.py`, without the probe | `logit` holding `[0.2, 0.8]`, `set_ylim(0.05, -1)` → `(0.2, 0.05)`. `set_ylim(2, 0.95)` → `(0.95, 0.8)` |

---

## Out of Scope

- **The 112 baseline failures.** They stay failing, as `change_request.md` § *What must not be done*
  requires.
- **Limits outside a `functionlog` or `logit` axis's domain.** These scales replace such a value
  silently, with no warning. This spec does not fix which values or which order the result has when
  a passed limit lies outside the domain. Today's results already do not follow the order passed:
  `logit` holding `[0.2, 0.8]`, given `set_ylim(0.05, -1)`, returns `(0.2, 0.05)`. On a `log` axis the
  case is decided by CP-11.
- **Which values limits on a covered scale take, beyond their order.** The values a call ends with
  are today's: how non-positive or equal limits are handled, and the margins autoscaling adds.
- **`invert_xaxis`/`invert_yaxis` with no data on a `log` axis.** Today they leave limits such as
  `(1e15, 1e-315)`. That is not changed.
- **Scales registered outside matplotlib**, and 3D (`mplot3d`) and polar axes.
- **Non-finite limits**, which `set_xlim`/`set_ylim` reject today. That is not changed.
- **What a locator's `nonsingular` returns when called directly.** It is not pinned here. How the
  rules are met is development-design's decision.
- **Documentation and release notes.** The request asks for none. The `set_xlim`, `set_ylim` and
  `set_ybound` docstrings already state the behaviour this change delivers, as checked above.
  `doc/` (the API-change notes and the "what's new" pages) was not looked at.
- **Anything outside the local clone.** The patch is not pushed (`project.md`, `Manages: none`), and
  nothing is published. As the request says, no record, grade or benchmark file is produced.

---

## Locked Answers (the divergence record — self-review 2026-10-11)

- **Gap 1 — `functionlog` and `logit` are covered too (CP-9).** The issue names only `log`.
  The spec covers the two other built-in scales that lose the order, for three reasons.
  - The docstring promise CP-9 restores makes no exception for any scale.
  - The failure is the same: the same swap stands at `ticker.py` 2382–2383 for `log` and `functionlog`,
    and at 2627–2628 for `logit`. A rule keyed to "log scales" also has to decide `functionlog`, which
    the user picks as a log scale.
  - It was found on this change's own walk, so it is fixed here
    (`<CORE>/doctrine/governance/found_while_walking.md`, clause 1).

  The change is reversible, because it moves an order and not data. The scratch probe shows no test
  changes its result.
- **Gap 2 — the result keeps the order of the resolved pair (CP-10, CP-11).** The issue passes both
  limits. When the call passes one limit, or a `log` axis ignores a non-positive one, the spec takes
  `linear`'s present behaviour: the order of the pair the call ends up with decides. That is the
  only reading under which the same call inverts a `linear` axis and a `log` axis alike.
- **Gap 3 — equal limits keep today's result (CP-12).** Two equal values carry no direction. The
  conservative pick is no change, and `linear` does the same: it expands equal limits to an
  ascending pair.
- **Gap 4 — `set_*bound` and autoscaling after `invert_*axis` are covered (CP-13).** The issue's own
  call, `set_ylim` with `auto=False` by default, does not autoscale afterwards. But `set_ybound`'s
  docstring promises to honour inversion, and on a `log` axis it fails for the same reason as the
  issue: it hands `set_ylim` a descending pair. Autoscaling an inverted axis is how `invert_yaxis`
  before plotting keeps working on `linear` (`test_inverted_limits` in
  `lib/matplotlib/tests/test_axes.py` lines 921–939). A user who inverts a `log` axis that way sees
  the issue's symptom. Leaving these out would leave the issue's symptom reachable by a documented
  route.
- **Gap 5 — out-of-domain limits on `functionlog` and `logit` are left open (Out of Scope).** The
  results there today do not follow the passed order in either direction. Fixing them means choosing
  what a silently replaced value should be, and neither the issue nor the docstrings say. This
  deferral is reversible and decides nothing, so it is stated in Out of Scope rather than parked.
- **Gap 6 — the change's tests are ones the card's `Test command:` runs (CP-16, CP-17).** The request
  asks for "tests of your own" and does not say where they run. The card's command runs only
  `lib/matplotlib/tests/test_axes.py`, and a test it does not run shows nothing at the change's gate.
  That is stated as a property of the result. Where the tests go is development-design's decision.
