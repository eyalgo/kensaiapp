# Change request — 2026-10-11_matplotlib-14623

**Request:** Fix the issue below in the product, the repository that the project card's
`Product path:` names (`matplotlib/matplotlib`). The repository stands at the commit before the issue was
fixed. Make the change the issue asks for, with tests of your own that show it, and leave the rest of
the product's behaviour as it is.

It is done when it is sealed. Nothing else is
asked of it: no record, no grade and no benchmark file. Bookkeeping is done outside
KensaiApp.

## The issue

*Not reproduced in this example.* The run was given the issue's title and body verbatim, as the benchmark SWE-bench Verified publishes them. That text is its author's, and the benchmark declares no licence for it, so this example links the issue and summarises it instead.

**The issue:** https://github.com/matplotlib/matplotlib/issues/14615

**In short:** Since Matplotlib 3.1.0, setting a log-scale axis's limits in reverse order no longer inverts the axis, as it still does for a linear scale.

## What must not be done

- **Do not look for the fix.** Work from this request and the repository you are given. Do not read
  the repository's history after this commit, its pull requests, its issue tracker, its later
  releases, or any copy of the SWE-bench benchmark
  (`system/projects/swe-benchmark-poc/doctrine/ai_responsibility.md` § 1.1). A patch made with any of
  them in view is not graded.
- **Do not delete anything outside the change** (same file, § 1.2).
- **Do not fix the product's other failing tests.** 112 tests fail before any change, in the environment the card's `Test command:` runs (========== 112 failed, 402 passed, 140 skipped, 13 warnings in 35.62s ==========, at `base_commit`):

  - `lib/matplotlib/tests/test_axes.py::TestScatter::test_scatter_marker[png]`
  - `lib/matplotlib/tests/test_axes.py::test_acorr[png]`
  - `lib/matplotlib/tests/test_axes.py::test_as_mpl_axes_api`
  - `lib/matplotlib/tests/test_axes.py::test_auto_numticks[png]`
  - `lib/matplotlib/tests/test_axes.py::test_auto_numticks_log[png]`
  - `lib/matplotlib/tests/test_axes.py::test_axhspan_epoch[png]`
  - `lib/matplotlib/tests/test_axes.py::test_axvspan_epoch[png]`
  - `lib/matplotlib/tests/test_axes.py::test_bar_tick_label_multiple[png]`
  - `lib/matplotlib/tests/test_axes.py::test_bar_tick_label_multiple_old_alignment[png]`
  - `lib/matplotlib/tests/test_axes.py::test_bar_tick_label_single[png]`
  - `lib/matplotlib/tests/test_axes.py::test_barh_tick_label[png]`
  - `lib/matplotlib/tests/test_axes.py::test_basic_annotate[png]`
  - `lib/matplotlib/tests/test_axes.py::test_boxplot[png]`
  - `lib/matplotlib/tests/test_axes.py::test_boxplot_autorange_whiskers[png]`
  - `lib/matplotlib/tests/test_axes.py::test_bxp_baseline[png]`
  - `lib/matplotlib/tests/test_axes.py::test_bxp_precentilewhis[png]`
  - `lib/matplotlib/tests/test_axes.py::test_bxp_rangewhis[png]`
  - `lib/matplotlib/tests/test_axes.py::test_bxp_with_xlabels[png]`
  - `lib/matplotlib/tests/test_axes.py::test_bxp_with_ylabels[png]`
  - `lib/matplotlib/tests/test_axes.py::test_canonical[png]`
  - `lib/matplotlib/tests/test_axes.py::test_const_xy[png]`
  - `lib/matplotlib/tests/test_axes.py::test_contour_colorbar[png]`
  - `lib/matplotlib/tests/test_axes.py::test_date_timezone_x[png]`
  - `lib/matplotlib/tests/test_axes.py::test_date_timezone_x_and_y[png]`
  - `lib/matplotlib/tests/test_axes.py::test_date_timezone_y[png]`
  - `lib/matplotlib/tests/test_axes.py::test_eb_line_zorder[png]`
  - `lib/matplotlib/tests/test_axes.py::test_errorbar[png]`
  - `lib/matplotlib/tests/test_axes.py::test_errorbar_limits[png]`
  - `lib/matplotlib/tests/test_axes.py::test_fill_units[png]`
  - `lib/matplotlib/tests/test_axes.py::test_formatter_ticker[png]`
  - `lib/matplotlib/tests/test_axes.py::test_get_tightbbox_polar`
  - `lib/matplotlib/tests/test_axes.py::test_hexbin_log[png]`
  - `lib/matplotlib/tests/test_axes.py::test_hist2d[png]`
  - `lib/matplotlib/tests/test_axes.py::test_hist2d_density_normed`
  - `lib/matplotlib/tests/test_axes.py::test_hist2d_transpose[png]`
  - `lib/matplotlib/tests/test_axes.py::test_hist_auto_bins`
  - `lib/matplotlib/tests/test_axes.py::test_hist_density[png]`
  - `lib/matplotlib/tests/test_axes.py::test_hist_emptydata`
  - `lib/matplotlib/tests/test_axes.py::test_hist_offset[png]`
  - `lib/matplotlib/tests/test_axes.py::test_hist_stacked_bar[png]`
  …and 72 more, listed in the test command's baseline.

  Leave them failing. The card's `Test command:` knows them: it passes while they are the only failures, and fails on any other.

**Category:** bug
**Behaviour:** changing
**Classified because:** the issue reports behaviour the product gets wrong. Correcting it changes what
the product does, so Behaviour is `changing`, and the cause is a defect in existing behaviour, so
Category is `bug` (`<CORE>/doctrine/flow/change_classification.md`, the two axes). Where the issue
asks for a capability the product lacks rather than a defect, the specs step reclassifies it.

**Sealed:** 2026-10-11 — accepted; merged to `main` via `--no-ff`.
