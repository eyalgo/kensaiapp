# Change Design — Reversed limits invert an axis on a log scale

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Publishes text:** no

---

## 1. Change Summary

`set_xlim` and `set_ylim` on `_AxesBase` (`lib/matplotlib/axes/_base.py`) take the order of their
result from the **resolved pair**, as the spec defines it, and not from whatever order the major
locator's `nonsingular` returns. The resolved pair is what the call has once it has read its
arguments, filled in any limit not passed, and replaced a non-positive `log` limit (CP-11). Today
`LogLocator.nonsingular` (which also serves `functionlog`) and `LogitLocator.nonsingular` sort their
input ascending. `set_*lim` passes the resolved pair through that call, so the descending order is
lost there. After this change each setter remembers whether the resolved pair was descending. If the
locator gives the pair back in the other order, the setter swaps it back before the scale clamp
(`limit_range_for_scale`), the view-limit write, the return and the shared-axes propagation. The
result keeps the resolved pair's order by construction, whatever the locator does (CP-9, CP-10,
CP-11). A pair that is not descending, equal limits included (CP-12), comes out exactly as today.

The locators are **not** changed. Their sorting `nonsingular` is a contract that other callers rely
on (Architect Review Notes, *Where the order is restored*). `set_xbound`/`set_ybound`, autoscaling an
inverted axis, and shared axes reach the limits only through `set_xlim`/`set_ylim`, so CP-13 and CP-14
follow from the same two edits.

One module changes, `lib/matplotlib/axes/_base.py`, together with the tests in
`lib/matplotlib/tests/test_axes.py`. **What crosses outward:** nothing. The change stores nothing on a
device, collects nothing and sends nothing to a third party. It is a local patch to a clone that is
not pushed (`project.md`, `Manages: none`), so no surface publishes it and it has no release step to
keep.

---

## 2. Blast Radius

The product has no `docs/` (`project.md`, `Definition: none`), so it has no parts table
(`SDD.md` § 3) and no module set (`nfdr.md § 1.2`). The modules below are the ones this change and
the spec name, read from the source under the product worktree.

| Module | Status | What changes |
|---|---|---|
| `lib/matplotlib/axes/_base.py` | Modified | `_AxesBase.set_xlim` and `_AxesBase.set_ylim`: after the major locator's `nonsingular` call, the result is put back into the resolved pair's order when the pair was descending. Signatures, argument handling, warnings and return shape are unchanged. |
| `lib/matplotlib/ticker.py` | Unchanged | `LogLocator.nonsingular` and `LogitLocator.nonsingular` still sort ascending. This is deliberate: see Architect Review Notes. |
| `lib/matplotlib/scale.py` | Unchanged | `LogScale.limit_range_for_scale` treats each end separately and keeps the order. `LogitScale.limit_range_for_scale` changes nothing for values in the domain. |
| `lib/matplotlib/axis.py` | Unchanged | `Axis.set_inverted`, which `invert_*axis` uses, writes the view interval directly and is not on this path. |
| `lib/mpl_toolkits/mplot3d/axes3d.py` | Unchanged | `set_xlim3d`, `set_ylim3d` and `set_zlim3d` call the locator themselves and do not go through `_AxesBase.set_*lim`. 3D stays as it is, as the spec's Out of Scope says. |
| `lib/matplotlib/tests/test_axes.py` | Modified | New tests (§5). |

**Transitive radius: callers whose behaviour changes.** No public interface changes, but what
`set_xlim`/`set_ylim` produce from a descending pair on a covered scale does. Every caller below that
passes a descending pair on a `log`, `functionlog` or `logit` axis now gets that order kept instead of
sorted. Each is the same docstring promise reached by another caller, and the code of none of them
changes:

- `set_xbound`/`set_ybound` (`_base.py` ~3105–3118, ~3502–3515) give descending limits to an inverted
  axis. This is CP-13.
- `autoscale_view` sets limits through `set_bound`, which is `set_xbound`/`set_ybound`. This is
  CP-13's autoscale path.
- Propagation to shared siblings in `set_*lim` itself, and `sharex`/`sharey` setup (`_base.py`
  ~988–1008). This is CP-14.
- Interactive zoom and pan (`_set_view_from_bbox` ~4102–4132, `drag_pan` ~4241) on an inverted
  covered axis now keep it inverted, where today they flip it back.
- `AxesImage` extent (`image.py` ~905, e.g. `imshow(origin='upper')`) and `matshow`
  (`_axes.py` ~7883) on a covered y-axis now show it inverted, as on `linear`.
- `PolarAxes.set_ylim` calls `super().set_ylim`, so a `log` radial axis given a descending pair now
  keeps it. Polar axes are out of the spec's scope. This consequence is recorded here and not tested.

**Other surfaces:** none. This project is not a presence surface, and no other project says anything
this change affects.

---

## 3. Sub-jobs

Omitted. One module is affected. `set_xlim` and `set_ylim` are two places in the same file with the
same edit, and there is no ordering edge between them: either can land first and the suite stays
green. So this is a single delta.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `_base.py` — `set_xlim` and `set_ylim` keep the resolved pair's order | Before the `get_major_locator().nonsingular(...)` call, take the direction of the resolved pair, strictly descending or not, after the CP-11 replacement and the equal-limits warning. After the call, compare the result's direction with it and swap the two values only when they differ. Keep this between `nonsingular` and `limit_range_for_scale`, so the clamp, `viewLim`, the return value and the siblings all see the restored order. Do not touch `ticker.py`. A test of "make it descending" or of the locator's class would break `linear`/`symlog`/`function` and future locators. Compare directions instead. |

---

## 5. Test Additions

Every test goes in `lib/matplotlib/tests/test_axes.py`, the only file the card's `Test command:` runs
(CP-16, Gap 6). Each test closes its figure. Unless a row says otherwise, the Axes holds data plotted
from `[1, 100]`, or `[0.2, 0.8]` on `logit`, as the spec's Examples assume. Each test asserts
`get_*lim()`, the setter's return value where the row names it, and `*axis_inverted()`.

| # | Sub-job | Test file | What to add / modify |
|---|---|---|---|
| 1 | `_base.py` | `tests/test_axes.py` | **The issue's reproduction (CP-9, CP-16).** `y = np.linspace(1000e2, 1, 100)`, `x = np.exp(-np.linspace(0, 1, y.size))`, parametrized over `linear` and `log`. `set_ylim(y.max(), y.min())` leaves `get_ylim() == (y.max(), y.min())` and `yaxis_inverted()` True on both. |
| 2 | `_base.py` | `tests/test_axes.py` | **Every argument form on a `log` y-axis (CP-9).** Parametrized over `set_ylim(100, 1)`, `set_ylim((100, 1))`, `set_ylim(bottom=100, top=1)` and `set_ylim(ymin=100, ymax=1)`. Each returns `(100, 1)`, holds `(100.0, 1.0)` and is inverted. |
| 3 | `_base.py` | `tests/test_axes.py` | **The `set_xlim` path on a `log` x-axis (CP-9, CP-16).** Parametrized over `set_xlim(100, 1)`, `set_xlim(left=100, right=1)` and `set_xlim(xmin=100, xmax=1)`. Each returns `(100, 1)`, holds `(100.0, 1.0)` and `xaxis_inverted()` is True. The edit is made twice, once in each setter, so the x path is tested on its own. |
| 4 | `_base.py` | `tests/test_axes.py` | **No data, and another base (CP-9).** A `log` y-axis with no data, `set_ylim(100, 1)`, gives `(100.0, 1.0)`. `set_yscale('log', basey=2)`, `set_ylim(64, 2)`, gives `(64.0, 2.0)`. Both are inverted. |
| 5 | `_base.py` | `tests/test_axes.py` | **The other covered scales (CP-9, CP-16).** `functionlog` (`functions=` any monotonic pair, e.g. identity), `set_ylim(100, 1)`, gives `(100.0, 1.0)`. `logit` with data, `set_ylim(0.9, 0.1)`, gives `(0.9, 0.1)`. Both are inverted. |
| 6 | `_base.py` | `tests/test_axes.py` | **One limit passed (CP-10), all three Examples.** Axis at `(100, 1)`, `set_ylim(top=10)`, gives `(100.0, 10.0)`, inverted. Axis at `(1, 100)`, `set_ylim(top=0.5)`, gives `(1.0, 0.5)`, inverted. Axis at `(100, 1)`, `set_ylim(1, 100)`, gives `(1.0, 100.0)`, not inverted. |
| 7 | `_base.py` | `tests/test_axes.py` | **A non-positive limit on `log` (CP-11), all three Examples.** Use `pytest.warns(UserWarning, match=...)` on the existing text. Axis at `(1, 100)`, `set_ylim(1000, -1)`, warns about `top` and gives `(1000.0, 100.0)`, inverted. Axis autoscaled from `[1, 10, 100]` to about `(0.79, 125.89)`, `set_ylim(50, 0)`, warns about `top` and gives `(50.0, ≈125.89)`, not inverted. `set_ylim(-1, 1)` warns about `bottom` and gives `(≈0.79, 1.0)`, as today. Compare values with `pytest.approx`. |
| 8 | `_base.py` | `tests/test_axes.py` | **Equal limits (CP-12).** A `log` axis at `(1, 100)`, `set_ylim(10, 10)`, gives the "identical bottom == top" warning and `(1.0, 100.0)`, not inverted. This pins today's result. |
| 9 | `_base.py` | `tests/test_axes.py` | **`set_*bound` honours inversion (CP-13, CP-16).** A `log` y-axis after `invert_yaxis()`, then `set_ybound(1, 100)`, gives `(100.0, 1.0)`. A `log` y-axis that is not inverted, `set_ybound(100, 1)`, gives `(1.0, 100.0)`. The same pair through `set_xbound` on a `log` x-axis, for the x path. |
| 10 | `_base.py` | `tests/test_axes.py` | **Autoscaling an inverted axis (CP-13).** An empty `log` y-axis, `invert_yaxis()`, then `plot([0, 1, 2], [1, 10, 100])`, ends descending (≈`(125.89, 0.79)`) and inverted. An empty `logit` y-axis, `invert_yaxis()`, then `plot([0, 1, 2], [0.2, 0.3, 0.8])`, ends descending (≈`(0.821, 0.178)`) and inverted. |
| 11 | `_base.py` | `tests/test_axes.py` | **Shared axes (CP-14).** `plt.subplots(2, sharey=True)`, first Axes `log`, `set_ylim(100, 1)`. Both Axes give `(100.0, 1.0)`. |
| 12 | `_base.py` | `tests/test_axes.py` | **Nothing else changes (CP-15), every Example.** `log`, `set_ylim(1, 100)`, gives `(1.0, 100.0)`, not inverted. `symlog` and `linear`, `set_ylim(100, 1)`, give `(100.0, 1.0)`. `log`, `set_ylim(100, 1)` then `fig.canvas.draw()`, stays `(100.0, 1.0)` and inverted. `linear`, `set_ylim(100, 1)` then `set_yscale('log')`, stays `(100.0, 1.0)`. `log`, `set_ylim(100, 1)` then `set_yscale('linear')`, gives `(100.0, 1.0)`. |
| 13 | `_base.py` | `tests/test_axes.py` | **`logit` with no data (edge; Architect Review Notes (a)).** An empty `logit` y-axis, `set_ylim(0.9, 0.1)`, ends descending and inverted. Assert the order and the inversion only. The values are today's initial range (`1e-7`, `1 - 1e-7`), which the spec leaves as they are. |

**CP-16, fail before and pass after:** rows 1 (`log` case), 2, 3, 4, 5, 6 (first two cases), 7 (first
case), 9 (first case), 10, 11, 12 (the `draw` and `set_yscale('linear')` cases) and 13 fail on the
unchanged tree. The remaining cases guard behaviour that is unchanged and pass both before and after.
Rows 1, 3, 5 and 9 between them cover CP-16's four named minimums. **CP-17:** the card's
`Test command:` is run with the change. It must exit 0, with exactly the 112 baseline failures. That
is a gate check, not a test row.

**Rule-implied edges:** CP-10's "the resolved pair decides" when the pair flips direction is covered
by row 6, case 2. CP-11's "the replacement can make the pair ascending" is covered by row 7, case 2.
The out-of-domain `functionlog`/`logit` inputs are out of the spec's scope, so no row pins them.

**Retired assertions:** none. No existing assertion goes false. `test_inverted_limits` (lines
921–939) stays as it is and keeps proving the `linear` autoscale-inversion path.

---

## Records this change makes false

None. The product has no `docs/`: `adr/`, `nfdr.md`, `fdr.md` and `SDD.md` are absent, because the card
reads `Definition: none`. The `set_xlim`, `set_ylim` and `set_ybound` docstrings already state the
behaviour this change delivers (spec, Verified Claims), so nothing in them goes false either.

---

## Architect Review Notes

- **(e) Where the order is restored: in `_AxesBase.set_xlim`/`set_ylim`, not in the locators.** The
  product has no parts table, so the placement is argued here. The spec's scratch probe changed the
  locators' `nonsingular`, and the spec says plainly that this was not a design. Changing the
  locators would change a contract that other callers rely on. `LogitLocator.tick_values`
  (`ticker.py` ~2587) relies on `nonsingular` sorting the view interval before it takes logs and
  floor/ceil decades. On an inverted `logit` axis it would get a descending pair and produce wrong or
  missing ticks. The polar branch of `LogLocator.view_limits` (~2366) treats the second value as the
  upper one. The mplot3d setters (out of scope) call the same method. The setter is the only place
  that knows the resolved pair, which is the user's intent. The locator sees only two numbers. So
  the order is restored there, and every locator's contract stays as it is.
- **(b) The order is kept by construction: compare directions, then swap.** CP-9 to CP-11 state that
  the result keeps the resolved pair's order. The design does not rely on today's locators happening
  to sort ascending (which "reverse when descending" would assume). It compares the direction of the
  input with the direction of the output. On `linear`, `symlog` and `function`, where the base
  `Locator.nonsingular` already keeps the order, the step does nothing. A future locator that keeps
  the order is not double-swapped.
- **(b) The restore comes before `limit_range_for_scale`.** The spec does not say where on the path
  the order comes back. Putting it before the scale clamp means the clamp, `viewLim`, the return value
  and the sibling propagation all see one order. For values in the domain both clamps are position
  independent or do nothing. Out-of-domain `functionlog`/`logit` inputs are out of the spec's scope,
  and their results stay as unspecified as today.
- **(a) CP-9's "with or without data" against Out of Scope's "the values are today's", on `logit`.**
  With no data, `LogitLocator.nonsingular` returns its initial range `(1e-7, 1 - 1e-7)` and drops the
  passed values. This was checked at base on 2026-10-11 from a scratch folder:
  `set_ylim(0.9, 0.1)` gives `(1e-07, 0.9999999)`. The spec's no-data Example is `log` only. Making
  CP-9 hold literally there would change values, which Out of Scope keeps as they are. Resolved:
  values stay today's, and the order follows the resolved pair, so the axis ends
  `(0.9999999, 1e-07)` and inverted. Row 13 pins the order and not the values. For `log` and
  `functionlog` with no data the passed pair comes back intact (row 4), so this gap is `logit`'s
  alone.
- **(b) The transitive callers are the same contract, not new behaviour.** Zoom and pan, `imshow`
  extents, `matshow` and polar `set_ylim` on a covered scale change for descending pairs (§2). CP-15's
  "nothing else about limits changes" is read as covering the values and the scales. These callers
  only reach `set_*lim`'s documented promise. They are named here so that the review after
  implementation reads them as intended, not as leakage. None of them is tested by this change, and
  none is in the card's run.
