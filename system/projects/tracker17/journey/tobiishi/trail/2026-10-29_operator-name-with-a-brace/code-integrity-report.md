# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-29_operator-name-with-a-brace` · reviewed 2026-10-29 by the
Senior Engineer (`development-code-integrity`, workflow mode).

## Deferrals

None — the closing marker (`<a commit not in the public history>`, `developer: 2026-10-29_operator-name-with-a-brace —
implementation complete`) carries no `Deferred:` line.

## What was reviewed

The branch's product diff against the merge base `fd47d2155` — three files under `products/tracker17/`:

- `web/pages.py` — `_your_name_section`: the paragraph class is chosen from the outcome before the
  paragraph is built, and the built paragraph is no longer passed through `.format`.
- `tests/integration/test_people_routes.py` — four new tests (T1–T4).
- `tests/integration/test_people_pages.py` — two tests extended (T5).

## The intent it was checked against

`tl_instruction.md` (Tasks 1 and 2, the shared T1/T2 name matrix), `change_spec.md` CP-619 to CP-630,
and `change_design.md` § 1, § 5 (T1–T9). `docs/fdr.md` was not opened; the spec quotes the requirements it binds.

## Placement

- Outcome-class choice and paragraph assembly in `_your_name_section` → owning part `web` ("building
  each whole HTML page", `docs/SDD.md` § 3, The parts) → **already there**. No move, no placement commit.

## Tests added or fixed

Every behaviour in the intent already had a test that asserts it; none was read off the code. Checked
for each:

- **CP-619, CP-621, CP-622, CP-624, CP-625 (saved)** — `test_saved_operator_name_with_braces_is_shown_exactly`
  over all ten names the plan lists (`{x}`, `}`, `{0}`, `{}`, `a{b`, `{x!r}`, `{{x}}`, `{<b>&"}`, `{`,
  and a 200-code-point mixed-brace name). Status `303` then `200` are asserted by the shared `location`
  and `page` helpers; exact line text, field value, field focus and description, stored name, one save,
  escaped source, and no Python error text.
- **CP-620 to CP-622, CP-624, CP-625 (failed)** — `test_failed_operator_name_with_braces_is_shown_exactly`,
  same ten names; failure through a `RaisingSaver` handed to `Tracker` (no patching), starting state
  built before the failing saver; exact line, field value, Save focus, one saver call, name unchanged,
  error type and message absent from the page.
- **CP-623, CP-626 (guards)** — the blank and too-long tests with `{x}` saved.
- **CP-622, CP-624 (markup continuity)** — the two extended page tests: exact `class`/`id` attribute
  set and placement for all four outcomes; `{&lt;b&gt;&amp;&quot;}` appears exactly twice (line and
  field) on the saved and failed pages.

**Proof the regressions catch the bug:** in a disposable clone at `<a commit not in the public history>` with `web/pages.py`
restored to `fd47d2155`, the two regression tests failed in all 20 cases (`KeyError`, `ValueError`,
`IndexError`, and wrong text for `{{x}}`), and the two guards passed — `20 failed, 2 passed`. This is
CP-625's before/after, re-run independently of the developer's red commit.

**One fix, to the language packet's bar** — not to an assertion. The two module docstrings the change
edited each gained a line over 100 columns (`test_people_routes.py` line 7, 116 columns;
`test_people_pages.py` line 6, 104 columns, with a dangling `QC-36 are` line after it).
`languages/python/conventions.md`: "**Lines stay within 100 columns.**" Ruff did not flag them because
the product's ruff config does not select the line-length rule. Reflowed both docstrings; their text
and every requirement they name are unchanged, and `tests/architecture/test_trace.py` passes. One
older over-long line in `test_people_pages.py` (now line 405) was not written by this change and is
left.

## The finding

**No issues** in the code: the correction does what CP-619 to CP-624 say on every name in the matrix,
every behaviour has a correct test, and nothing was misplaced. The only edit is the docstring reflow
above.

## Calls made

None.

## Language resolution

Python — `project.md` `Languages:`, chain step 1. Packet `<CORE>/doctrine/engineering/languages/python/`
read: `conventions.md` (the 100-column rule applied above; f-string at the point of use — the fix
follows it), `quality_gates.md`, `testing_python.md` (the handed-in fake seam — followed by the failed
test). The product's own records (NFDR QC-62) add ruff and mypy.

## Test evidence

- The verdict run: the card's `pytest products/tracker17/tests/` through `gate_suite.py --gate
  code-integrity` — exit 0, `2651 passed in 606.22s`.
- `pytest products/tracker17/tests/e2e/` (CP-627's second command, run by hand — it is not the card's
  command) — `121 passed in 80.48s`.
- From the product root: `ruff format --check .` (269 files already formatted), `ruff check .` (all
  checks passed), `mypy main.py errors.py domain application persistence web` (no issues in 27 source
  files) — each exit 0 (CP-628).
- Focused: the two changed test modules plus `tests/architecture/test_trace.py` — `168 passed`.
