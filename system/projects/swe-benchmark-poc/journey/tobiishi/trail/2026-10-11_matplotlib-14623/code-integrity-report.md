# Code integrity report — 2026-10-11_matplotlib-14623

Integrity: pass

**Change:** reversed limits invert an axis on a log scale (`matplotlib__matplotlib-14623`).
**Reviewer:** Senior Engineer, `development-code-integrity`, workflow mode, 2026-10-11.
**Product commits (code worktree, branch `2026-10-11_matplotlib-14623` of the product repo):**
`e1e227b83` (tests, green) and `ccf0eb4f3` (annotation, behaviour unchanged). No red commit was
made, because no test went red against the developer's code.

---

## Deferrals

None. The newest closing marker (`4037ea4`, `developer: 2026-10-11_matplotlib-14623 — implementation
complete`) has no `Deferred:` line and no `Failing:` line.

## What was reviewed

The product change from base `d65c9ca20` to the developer's last commit `819fe6883`, in
`<the issue's clone>/.worktrees/2026-10-11_matplotlib-14623`:

- `lib/matplotlib/axes/_base.py`: the new module-level helper `_keep_limit_order`, and its two call
  sites in `_AxesBase.set_xlim` and `_AxesBase.set_ylim`, between the major locator's
  `nonsingular` and `limit_range_for_scale`.
- `lib/matplotlib/tests/test_axes.py`: the 16 test functions the change added (23 cases).

The code does what the intent says. The resolved pair is captured after the non-positive `log`
replacement and the equal-limits warning. Only directions are compared, and the restore comes
before the scale clamp, so the view limits, the return value and the shared siblings all see the
same order. Equal limits carry no direction, so they are never swapped (CP-12).

## The intent it was checked against

- `tl_instruction.md`: Tasks 1 and 2, their *Behaviours to verify* and *Held by review* lists.
- `change_spec.md`: CP-9 to CP-17, the Examples table and the Out of Scope list.
- `change_design.md`: §2 (blast radius and transitive callers), §4 (the hint) and §5 (test rows
  1–13).
- `docs/fdr.md`: none. The product has no `docs/`, because `project.md` reads `Definition: none`.
  That is optional context, not a gap.

## The tests added or fixed

All are in `lib/matplotlib/tests/test_axes.py`, commit `e1e227b83`. Each is derived from the named
rule, never from the implementation.

| Test | What changed | Why (the intent) |
|---|---|---|
| `test_set_ylim_nonpositive_log_limit_warns_and_keeps_order` | Each warning is now compared with today's **full** text (helper `_nonpositive_limit_warning`), not a `match=` fragment. The `set_ylim(-1, 1)` case also asserts `not yaxis_inverted()`. | CP-11: "still ignored with today's warning, the text unchanged". The plan says every test asserts `yaxis_inverted()`. |
| `test_set_ylim_equal_limits_on_log_unchanged` | Compares the full `identical bottom == top == 10 …` text. | CP-12 quotes the warning in full. |
| `test_set_ybound_honours_inversion_on_log`, `test_set_xbound_honours_inversion_on_log` | The inverted case now asserts that the axis is still inverted. | CP-13: "an inverted axis stays inverted". Before, only the pair was asserted. |
| `test_set_ylim_descending_on_shared_log_axes` | Asserts that both Axes are inverted. | CP-14, and the plan's "asserts … `yaxis_inverted()`". |
| `test_set_ylim_other_cases_unchanged` | Every case asserts its inversion state. The `function` scale (`np.sqrt`/`np.square`) joins `symlog` and `linear`. | CP-15 names `function` among the scales that keep today's behaviour, and the suite did not test it. |
| `test_set_ylim_ascending_on_functionlog_and_logit_unchanged` (new) | An ascending pair on `functionlog` and `logit` returns and holds today's values, and the axis is not inverted. | CP-15: "An ascending pair on a covered scale ends with today's values". Before, it was tested on `log` only. |
| `test_set_xlim_nonpositive_log_limit_warns_and_keeps_order` (new) | On the x path: `set_xlim(1000, -1)` at `(1, 100)` warns about `right` and gives `(1000, 100)`, inverted. At `(1, 200)`, `set_xlim(50, 0)` gives `(50, 200)`, not inverted. `set_xlim(-1, 10)` warns about `left` and gives `(50, 10)`, inverted. | CP-11 holds for `left`/`right` too ("Everything below holds for the x-axis and the y-axis alike"). The second case passes a descending pair whose resolved pair is ascending, which is the only shape that shows *which* pair the setter captured. |

**Style.** The 47 single-quoted strings in the change's new tests are now double-quoted (see
*Language resolution*). No test outside the change's own block was touched.

**Test meaning, measured.** With base `d65c9ca20`'s `_base.py` swapped into the change's own
worktree, 6 of the 8 changed or added test functions fail. The 2 that pass are the equal-limits pin
and the new ascending pin, which by the spec pin unchanged behaviour. A mutation that moved
`set_xlim`'s capture above the non-positive replacement turned only
`test_set_xlim_nonpositive_log_limit_warns_and_keeps_order` red, and every other x-path test stayed
green. So before this review nothing guarded where the x setter captures the resolved pair. The
file was restored from `819fe6883` after each run, by explicit SHA.

**Left as written.** `test_set_ylim_other_cases_unchanged` chains the CP-15 `set_yscale('linear')`
case after the `draw` case on one Axes, so that case's own fail-before is not shown on its own. It
asserts the intended result, and it is not wrong, so it stays.

## The finding

**No bug.** Against its intent, the developer's code was correct. Every test added or tightened is
green on it, and no code fix was needed.

What this review did find and close:

- **Test gaps:** six tests asserted less than the intent says (warning text, inversion state), and
  two rule-implied behaviours had no test (CP-15 for `function` and for ascending pairs on the other
  covered scales, and CP-11 on the x path). Before this review, a regression in the capture point of
  `set_xlim` would have stayed green.
- **Packet conventions:** `_keep_limit_order` is now annotated (`ccf0eb4f3`), and the new tests use
  double quotes. Both were raised by the developer for this seat.
- **Misplacements:** none moved (see *Placement*).

The card's `Test command:` (`/home/kensai/issue-test.sh`), run from the product worktree after
each commit: exit 0, `112 failed, 427 passed, 140 skipped`, `issue-test: only baseline failures
remain (112 known at base_commit)`. That is 2 more passed than the developer's 425, from the two new
test functions (CP-17). The compile gate (`python -m compileall -q lib/matplotlib/axes/_base.py`) exits 0.

**Held by review**, checked by reading `git diff d65c9ca20..ccf0eb4f3`: additions only, in
`_base.py` (three hunks: the helper and the two call sites) and `test_axes.py`. Nothing changes in
zoom/pan (`_set_view_from_bbox`, `drag_pan`), the `imshow`/`matshow` extents, polar `set_ylim`,
`ticker.py`, `scale.py` or `axis.py`.

**Domain (instance overlay).** The change stores nothing on a device, embeds nothing, collects
nothing and loads no third-party origin (`change_design.md` §1, *What crosses outward: nothing*). It
publishes no text and is not pushed (`project.md`, `Manages: none`), so no rule of
`system/doctrine/kensaiapp_doctrine.md` bears on it. No test reaches LinkedIn.

## Calls made

1. **How to annotate the return under the product's Python floor.**
   - *The question:* the Python packet wants builtin generics (`tuple[float, float]`) with
     `from __future__ import annotations` as the first statement. matplotlib at base declares
     `python_requires='>=3.6'` (`setup.py:291`), and that import needs 3.7.
   - *Readings weighed:* the future import, which would break the module on 3.6; the `typing.Tuple`
     spelling, which the packet forbids; or a string annotation.
   - *Taken:* `-> "tuple[float, float]"` as a string, with `float` parameters. `languages/README.md`
     § Precedence ranks the product's own records above the packet, and this keeps the packet's
     spelling without evaluating it.
   - *Whose:* the owner, as keeper of `core/doctrine/engineering/languages/python/conventions.md`.
   - *If reversed:* drop the annotations, or add the future import and accept the loss of 3.6.
2. **`__version__` on `lib/matplotlib/axes/_base.py`: not added.**
   - *The question:* `conventions.md` § Naming says every non-test module carries the marker.
   - *Taken:* not added. The rule is `versioning.md`'s script marker for house-authored modules.
     This change authored no module; it edited an existing upstream one whose versioning is
     matplotlib's own release process. Adding it would put scope into an upstream patch that the
     intent does not ask for. The developer recorded the same divergence.
   - *Whose:* the owner, for the packet.
   - *If reversed:* one line after the imports in `_base.py`.
3. **Two product commits on a clean pass, not one.**
   - *The question:* the skill's table gives a clean pass one commit (tests + report).
   - *Taken:* the tests (`e1e227b83`) and the behaviour-neutral annotation (`ccf0eb4f3`) are
     separate, so the tests-only commit stays legible and no code change rides inside it. The report
     is its own commit in the pipeline worktree, as the table says for a product in its own repo.
   - *Whose:* the owner, for `development-code-integrity`.
   - *If reversed:* squash the two product commits. Nothing else changes.

## Placement

**No parts table.** The product has no `docs/` (`project.md`, `Definition: none`), so there is no
`docs/SDD.md` § 3 to place against, and Step 0 was skipped. For the record, the one piece of new
logic, `_keep_limit_order`, sits in `lib/matplotlib/axes/_base.py` beside its only two callers.
That is the module `change_design.md` §2 names and argues (Architect Review Notes (e)). No
placement commit was made.

## Language resolution

- **Language:** Python. **Step:** 1, `project.md` `Languages: Python`.
- **Packet:** `core/doctrine/engineering/languages/python/README.md`, with the three concerns this
  review is held to: Conventions (`python/conventions.md`), Quality gates (`python/quality_gates.md`)
  and Testing (`core/doctrine/engineering/testing_python.md`). Precedence comes from
  `core/doctrine/engineering/languages/README.md` § Precedence. Toolchain, Layout and Errors and
  logging were not re-read; the developer's marker records reading them.
- **Where the packet won over the file, and the code changed:**
  - `conventions.md` § Surface style, double-quoted strings. The change's new tests now use double
    quotes, while the rest of `test_axes.py` keeps its single-quote habit. The file's style is now
    split, and that is recorded here.
  - `conventions.md` § Typing, an annotated production function. `_keep_limit_order` is annotated,
    while the rest of `_base.py` carries no annotations.
- **Where the product's record won over the packet:** the Python floor and the future import (Call
  1). Test location stays the product's own: `lib/matplotlib/tests/test_axes.py`, the file the card
  runs (`change_spec.md` Gap 6), not `tests/test_<domain>.py`.
- **Not applied:** `__version__` (Call 2). Errors and logging: no raise, catch or log was written.
  Test seams: no monkeypatching. The tests drive real Axes objects, as `testing_python.md` § Rules
  asks.
- **Quality gates:** Compile exits 0, and the Suite is the card's command (exit 0, the 112 baseline
  failures only, per CP-17).
