# Tech Lead instruction — matplotlib-14623: reversed limits invert an axis on a log scale

**Product root:** <the issue's clone>/.worktrees/2026-10-11_matplotlib-14623 — every path below is relative to it.
**Scope:** `Axes.set_xlim` / `set_ylim` keep the order of the resolved pair on the `log`, `functionlog` and `logit` scales (CP-9 to CP-15), with tests the card's `Test command:` runs (CP-16, CP-17). Category: bug. Behaviour: changing.

**Third-party origins and device storage this change may introduce:** none. No dependency is added, nothing is stored on a device, nothing is requested over a network. No string a visitor can read is published (`Publishes text: no`).

---

## Project layout

```
lib/matplotlib/
  axes/_base.py              ← modified (set_xlim, set_ylim)
  tests/test_axes.py         ← modified (new tests only; no existing assertion changes)
```

`ticker.py`, `scale.py`, `axis.py` and `mplot3d` are **not** touched. No parts table (the product has no `docs/`) — placement follows `change_design.md §2`.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **Task split:** the design's single delta is two edits in two setters. Planned as Task 1 (`set_ylim`) and Task 2 (`set_xlim`), because no edge joins them, each is independently testable and goes red on its own, and the x path is otherwise exercised only by one design row. The design's §5 rows are distributed by the setter they exercise.
- **Behaviour added (Task 2):** `set_xbound` on an inverted `log` x-axis already sits in design row 9; it is kept in Task 2 so the x path has the same inversion coverage as y. Added `set_xlim` with `(100, 1)` as a tuple on a `log` x-axis to Task 2 (CP-9 lists the one-tuple form for both setters; the design tested the tuple form only on y).
- **Behaviour added (Task 2):** `logit` x-axis descending pair, since the `logit` edit shares the setter but the design tested it on y only.
- **Gate command:** `project.md` `Test command:` is `/home/kensai/issue-test.sh`, which runs only `lib/matplotlib/tests/test_axes.py` and passes while only the 112 baseline failures remain (spec, Verified Claims). Used as is for every gate. The developer's focused red/green runs use `-k` on the new tests.
- **Hint carried:** the §4 hint is carried into both tasks unchanged in substance; it is an approach, not code.
- **Held by review:** the transitive callers in §2 (zoom/pan, `imshow`/`matshow` extents, polar `set_ylim`) have no test, per the design's own note; recorded in each task as held by review.

### Task 1: `_AxesBase.set_ylim` order restore (`lib/matplotlib/axes/_base.py`, `lib/matplotlib/tests/test_axes.py`)

**Dependencies:** None

**What to build:** `set_ylim` keeps the order of the resolved pair (arguments read, missing limit filled from the current one, non-positive `log` limit replaced, equal-limits handling as today) whatever order the major locator's `nonsingular` returns. Argument handling, warnings, signature and return shape do not change. Shared-axes propagation, `set_ybound` and autoscaling of an inverted axis get CP-13/CP-14 from this edit alone.

#### Behaviours to verify (developer adds tests to `lib/matplotlib/tests/test_axes.py`; each closes its figure and asserts `get_ylim()`, the return value where named, and `yaxis_inverted()`)

- `test_set_ylim_descending_on_log_and_linear` — the issue's reproduction: `y = np.linspace(1000e2, 1, 100)`, `x = np.exp(-np.linspace(0, 1, y.size))`, parametrized over `linear` and `log`; `set_ylim(y.max(), y.min())` leaves `(y.max(), y.min())`, inverted.
- `test_set_ylim_descending_argument_forms_on_log` — parametrized over `(100, 1)`, `((100, 1))`, `bottom=100, top=1`, `ymin=100, ymax=1`; each returns `(100, 1)`, holds `(100.0, 1.0)`, inverted.
- `test_set_ylim_descending_log_no_data_and_base_2` — no data: `set_ylim(100, 1)` gives `(100.0, 1.0)`; `set_yscale('log', basey=2)` then `set_ylim(64, 2)` gives `(64.0, 2.0)`; both inverted.
- `test_set_ylim_descending_on_functionlog_and_logit` — `functionlog` (identity-style monotonic pair) `set_ylim(100, 1)` gives `(100.0, 1.0)`; `logit` with data `[0.2, 0.8]`, `set_ylim(0.9, 0.1)` gives `(0.9, 0.1)`; both inverted.
- `test_set_ylim_one_limit_keeps_resolved_order` — at `(100, 1)`, `set_ylim(top=10)` gives `(100.0, 10.0)`, inverted; at `(1, 100)`, `set_ylim(top=0.5)` gives `(1.0, 0.5)`, inverted; at `(100, 1)`, `set_ylim(1, 100)` gives `(1.0, 100.0)`, not inverted.
- `test_set_ylim_nonpositive_log_limit_warns_and_keeps_order` — `pytest.warns(UserWarning, match=...)` with today's text. At `(1, 100)`, `set_ylim(1000, -1)` warns about `top`, gives `(1000.0, 100.0)`, inverted. Axis autoscaled from `[1, 10, 100]` (≈`(0.79, 125.89)`), `set_ylim(50, 0)` warns about `top`, gives `(50.0, ≈125.89)`, not inverted. `set_ylim(-1, 1)` warns about `bottom`, gives `(≈0.79, 1.0)`. Compare with `pytest.approx`.
- `test_set_ylim_equal_limits_on_log_unchanged` — at `(1, 100)`, `set_ylim(10, 10)` gives the "identical bottom == top" warning and `(1.0, 100.0)`, not inverted.
- `test_set_ybound_honours_inversion_on_log` — after `invert_yaxis()`, `set_ybound(1, 100)` gives `(100.0, 1.0)`; not inverted, `set_ybound(100, 1)` gives `(1.0, 100.0)`.
- `test_autoscale_inverted_axis_on_log_and_logit` — empty `log` y-axis, `invert_yaxis()`, `plot([0, 1, 2], [1, 10, 100])` ends ≈`(125.89, 0.79)`, inverted; empty `logit` y-axis, `invert_yaxis()`, `plot([0, 1, 2], [0.2, 0.3, 0.8])` ends ≈`(0.821, 0.178)`, inverted.
- `test_set_ylim_descending_on_shared_log_axes` — `plt.subplots(2, sharey=True)`, first Axes `log`, `set_ylim(100, 1)`: both Axes `(100.0, 1.0)`.
- `test_set_ylim_other_cases_unchanged` — `log` `set_ylim(1, 100)` gives `(1.0, 100.0)` not inverted; `symlog` and `linear` `set_ylim(100, 1)` give `(100.0, 1.0)`; `log` `set_ylim(100, 1)` then `fig.canvas.draw()` stays `(100.0, 1.0)` inverted; `linear` `set_ylim(100, 1)` then `set_yscale('log')` stays `(100.0, 1.0)`; `log` `set_ylim(100, 1)` then `set_yscale('linear')` gives `(100.0, 1.0)`.
- `test_set_ylim_descending_on_logit_with_no_data` — empty `logit` y-axis, `set_ylim(0.9, 0.1)` ends descending and inverted. Assert the order and the inversion only; the values are today's initial range, which the spec leaves as they are.

Fail before, pass after: the `log` case of the reproduction, argument forms, no-data/base-2, functionlog/logit, the first two one-limit cases, the first non-positive case, the first `set_ybound` case, autoscale, shared axes, the `draw` and `set_yscale('linear')` cases, and the logit no-data case. The rest pin unchanged behaviour and pass on both sides.

#### Held by review

- Zoom and pan (`_set_view_from_bbox`, `drag_pan`), `imshow`/`matshow` extents and polar `set_ylim` change for a descending pair on a covered scale (design §2). No test is written or run for them; they are held by reading the diff, and the diff must change nothing in those callers.
- The rule that `ticker.py` and `scale.py` stay untouched is held by reading the diff.

#### Implement

Infer from failing tests.

# Hint: Before the `get_major_locator().nonsingular(...)` call, record the direction of the resolved pair — strictly descending or not — after the non-positive `log` replacement and the equal-limits warning. After the call, compare the result's direction with it and swap the two values only when they differ. Do this between `nonsingular` and `limit_range_for_scale`, so the scale clamp, the view-limit write, the return value and the shared-axes propagation all see the restored order. Compare directions; never test the locator's class or "force descending", which would break `linear`, `symlog`, `function` and any future locator.

#### Verification gate

`/home/kensai/issue-test.sh` (run from the product root).

Pass criteria: exit 0; the new Task 1 tests pass; the only failures are the 112 baseline ones (`issue-test: only baseline failures remain (112 known at base_commit)`); `git diff` shows changes only in `lib/matplotlib/axes/_base.py` and `lib/matplotlib/tests/test_axes.py`, and no change to `ticker.py`.

### Task 2: `_AxesBase.set_xlim` order restore (`lib/matplotlib/axes/_base.py`, `lib/matplotlib/tests/test_axes.py`)

**Dependencies:** None

**What to build:** the same edit in `set_xlim`, which has its own copy of the call (`_base.py` ~3267). It is a separate place with its own failure, so the x path is tested on its own. `set_xbound` on an inverted axis reaches it through `set_xlim`.

#### Behaviours to verify (developer adds tests to `lib/matplotlib/tests/test_axes.py`; assert `get_xlim()`, the return value, and `xaxis_inverted()`)

- `test_set_xlim_descending_argument_forms_on_log` — parametrized over `set_xlim(100, 1)`, `set_xlim((100, 1))`, `set_xlim(left=100, right=1)` and `set_xlim(xmin=100, xmax=1)` on a `log` x-axis; each returns `(100, 1)`, holds `(100.0, 1.0)`, inverted.
- `test_set_xlim_descending_on_functionlog_and_logit` — `functionlog` x-axis `set_xlim(100, 1)` gives `(100.0, 1.0)`; `logit` x-axis with data `[0.2, 0.8]`, `set_xlim(0.9, 0.1)` gives `(0.9, 0.1)`; both inverted.
- `test_set_xbound_honours_inversion_on_log` — `log` x-axis after `invert_xaxis()`, `set_xbound(1, 100)` gives `(100.0, 1.0)`; not inverted, `set_xbound(100, 1)` gives `(1.0, 100.0)`.
- `test_set_xlim_ascending_on_log_unchanged` — `set_xlim(1, 100)` gives `(1.0, 100.0)`, not inverted.

#### Held by review

- The same transitive callers as Task 1, for the x-axis. Nothing in them changes.

#### Implement

Infer from failing tests.

# Hint: Same approach as Task 1, applied to `set_xlim`: take the direction of the resolved pair before the locator call, restore it after the call if the locator changed it, and do so before `limit_range_for_scale`. Compare directions, not locator types.

#### Verification gate

`/home/kensai/issue-test.sh` (run from the product root).

Pass criteria: exit 0; the Task 1 and Task 2 tests pass; the only failures are the 112 baseline ones; the diff touches only `lib/matplotlib/axes/_base.py` and `lib/matplotlib/tests/test_axes.py`.
