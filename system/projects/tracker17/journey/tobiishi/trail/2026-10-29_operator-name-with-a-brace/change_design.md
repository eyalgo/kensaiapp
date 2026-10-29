# Change Design — show braces in the operator name as typed

**Date:** 2026-10-29
**Category:** bug
**Behaviour:** changing
**Publishes text:** yes — the saved, failed and refusal messages in Your name on the People page

This document owns the rendering boundary and the regression coverage for
`tracker17 · tobiishi · 2026-10-29_operator-name-with-a-brace`.
`change_spec.md` § Rules owns the required behaviour. Product paths below are relative to
`products/tracker17/` in this change's worktree.

---

## 1. Change Summary

Change only the paragraph assembly in `web/pages.py`, `_your_name_section`, so an outcome line
containing the name is inserted as data and never becomes a format string. The current assembly
puts the line inside a paragraph containing a class placeholder, then formats that paragraph
(`web/pages.py:2816-2829`, `_your_name_section`). Keep escaping in `_operator_line` and the field's
existing `_escape` call (`web/pages.py:2793-2814`, `_operator_line` and `_your_name_section`).
Select the paragraph's class from the outcome before assembling the paragraph with its line.
There must be no subsequent format-string interpretation of that completed paragraph.

The single delta covers saved, failed, blank and too-long outcomes together, as `change_spec.md`
§ Rules A requires. Wording, outcome selection, form values, placement and focus remain subject to
CP-624; request handling, redirects and every other page's rendering are outside the delta.

---

## 2. Blast Radius

Place the corrected paragraph assembly in the **web** part: whole-page building belongs there
(`docs/SDD.md:202-212`, § 3, `web` row). The part already lives at the product root's `web/`;
this needs no new part, interface, dependency or import permission (`docs/SDD.md:214-242`, § 3,
The units and The direction of dependence).

| Module | Status | What changes |
|---|---|---|
| `web/` | Modified | The web part's `_your_name_section` in `pages.py` assembles its outcome paragraph without interpreting the escaped line as a format template. Keep the existing placement and focus rules for all four outcomes. |
| `domain/` | Unchanged | No rule or representation changes; existing trace pointers suffice when the named test modules are extended (`domain/operator_name.py:1-17`, opening docstring, Checked by). |
| `application/` | Unchanged | No action, saving contract or result changes. |
| `persistence/` | Unchanged | No saved-data change. |
| `main.py` | Unchanged | No wiring change. |
| `errors.py` | Unchanged | No error type change. |

The module set and permitted dependence are `docs/nfdr.md:166-197`, § 1.2, QC-13–QC-19.
`main.py` may import `web`, but no public signature or export changes, so its call sites need no
change. Within `web`, the existing route continues to hand `people_page` the same outcome values
(`web/routes.py:792-817`, `_people_page` and `_operator_area`).

Extend `tests/integration/test_people_routes.py` and `tests/integration/test_people_pages.py`.
No sub-job split is needed: only `web` changes, and the paragraph assembly has no independent
internal seam requiring an ordering edge. All outcomes belong to the same rendering correction.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `web/` — Your name outcome paragraph | Resolve the class using the existing outcome, then insert the already-escaped outcome line as a value in one assembly step. Do not pre-double braces or escape the completed HTML; either would change the text or markup. Keep `_escape` as the sole value-to-HTML boundary. |

---

## 5. Test Additions

The test names below describe coverage; assertions come from the referenced CP rules.

| Row / change | Test file or check | What to add / modify |
|---|---|---|
| T1 — saved outcome | `tests/integration/test_people_routes.py` | Add one parameterized regression test sending `POST /operator-name`, then `GET` of its actual Location. Assert the existing redirect query, `200`, exactly one saved line with the exact name, field value and field focus/description, and no Python error text (CP-619, CP-621, CP-624, CP-625). Include `{x}`, `}`, `{0}`, `{}`, `a{b`, `{x!r}`, `{{x}}`, `{<b>&"}`, a one-character `{`, and an accepted 200-code-point name with repeated/mixed braces. Check the tracker holds the submitted name. |
| T2 — failed outcome | `tests/integration/test_people_routes.py` | Add one parameterized regression test over the same names as T1. Hand the tracker a saver that raises an error with a distinctive message, using the existing `RaisingSaver` seam. Submit then GET the actual Location; assert its existing failure query, `200`, the exact failed line, retained field value, Save focus/description, and absence of the error type, distinctive message and traceback. Assert the tracker name stays unchanged (CP-620–CP-622, CP-624, CP-625). |
| T3 — blank guard | `tests/integration/test_people_routes.py` | Add one test with `{x}` already saved, submitting a blank name and following its redirect. Assert `200`, CP-623's exact blank reason, the empty field, field focus/description and no Python error text; the stored name and save count remain unchanged (CP-623, CP-624, CP-626). |
| T4 — too-long guard | `tests/integration/test_people_routes.py` | Add one test with `{x}` already saved, submitting 201 characters and following its redirect. Assert `200`, CP-623's exact too-long reason, `{x}` as the field fallback, field focus/description and no Python error text. Assert the overlong value is absent and no save occurs (CP-623, CP-624, CP-626). |
| T5 — markup and escaping continuity | `tests/integration/test_people_pages.py` | Extend `test_operator_outcome_focus_has_one_linked_accessible_description` to assert CP-624's exact paragraph class/id and placement for saved, failed and both refusal outcomes, retaining its `Sam` cases. Extend `test_operator_name_and_outcome_values_render_as_text` with `{<b>&"}` for saved and failed lines: raw source contains `{&lt;b&gt;&amp;&quot;}`, parsed line and field show the original name, and tags, ids and surrounding structure remain intact (CP-622, CP-624). |
| T6 — before/after evidence | The T1 and T2 regression tests | Each of the two tests must fail against product code at `fd47d2155` and pass against the changed product. The `{x}`, `}` and `{0}` cases must reach the redirect GET; an earlier setup failure does not prove the regression. T3 and T4 are guards and need no baseline failure (CP-625, CP-626). |
| T7 — complete suites | From the change worktree root: `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/` | Both exit `0`, with unit, integration and architecture collected by the first, and e2e collected by the second, using the product's locked dependencies and installed browser (CP-627). The tests retain their existing collection policy. |
| T8 — quality gates | From the product root: `ruff format --check .`, `ruff check .`, `mypy main.py errors.py domain application persistence web` | Each exits `0` with the product's pinned tools (CP-628). |
| T9 — trace continuity | `tests/architecture/test_trace.py`, included in T7 | Both extended modules retain their requirement/acceptance-criterion docstrings. They are already named in `domain/operator_name.py`'s opening docstring, so extending them requires no new pointer or domain edit (CP-629; `domain/operator_name.py:12-16`, Checked by). |

**Examples coverage:** Examples 1–4 map to T1; 5–6 to T2; 7 to T1/T2/T5; 8 to T3; 9 to T4;
10 to T5 plus the retained `Sam` route cases; 11 to T6; 12 to T7; 13 to T8; 14 to T9.
CP-630 is reviewed below, rather than represented by an output scenario.

**Rule-implied edges:** CP-621's unpaired, repeated, positional-looking and conversion-looking braces,
one-character lower boundary, and accepted upper boundary are covered by T1/T2. Their mixed markup
and brace case covers CP-622 on both lines, with source and structure checked by T5. CP-623's
refusal-after-saved-name edges are T3/T4. For CP-624, retain the existing plain/unset-name, query
precedence and unchanged-name route cases and the existing no-name/assignee page assertions
(`tests/integration/test_people_routes.py:502-518,668-734`, same-name and query tests;
`tests/integration/test_people_pages.py:512-552,637-683`, section and precedence tests).

No assertion is retired. Existing tests continue to prove their present clauses, with T5 adding
the paragraph class and placement checks to the focus and description checks.

---

## Records this change makes false

None — reviewed `docs/adr/README.md` and ADR-0001–ADR-0012, `docs/nfdr.md` §§ 1–2 and §§ 7–10,
`docs/fdr.md` R-62, R-76, R-108 and R-112, and `docs/SDD.md` § 3 and § 4 SEC-4/TS-1–TS-4.
The delta restores their typed-text contract and changes no architectural decision. ADR-0006 and
ADR-0010 remain superseded as their Status lines state. No product document is edited.

---

## Architect Review Notes

Decisions and review verdicts below are the architect's, 2026-10-29.

- **Realized by construction (b):** Resolve the paragraph class before inserting the outcome line,
  and never interpret the assembled line as a format template. This makes every brace ordinary
  data, including double braces, instead of special-casing the examples in CP-621. The present
  second interpretation is the seam being removed (`web/pages.py:2818-2829`, `_your_name_section`).
- **Text verdict:** `yes` identifies the People page's Your name messages whose values this delta
  renders. Their wording stays locked by CP-624; this verdict authorizes no rewording.
- **QC-36 / SEC-4 — pass:** Keep `_operator_line`'s calls to `_escape` for both names and the field's
  `_escape(shown)` call. `_escape` uses `html.escape` with quote escaping (`web/pages.py:452-454`,
  `_escape`; `:2793-2814`, line and field building). Insert that escaped line without another
  escaping pass. T1/T2/T5 guard exact text and markup. No new text field is added, so QC-36's
  additional-field browser test condition does not apply (`docs/nfdr.md:329-336`, QC-36).
- **QC-8 — pass:** The changed assembly uses request-local values only. It introduces no retained
  state, cookie or cache (`web/pages.py:2806-2853`, `_your_name_section`;
  `docs/nfdr.md:85-90`, QC-8).
- **QC-23 — pass:** Only paragraph building changes; validation, refusal choice and saved state
  remain outside it. No rule, data access or clock is introduced (`docs/SDD.md:208-212`, § 3;
  `web/pages.py:2768-2829`, outcome helpers and paragraph building).
- **QC-27 / QC-12 — pass:** This design modifies one existing web function, adds no part and needs
  no wiring or inner-layer change (`docs/nfdr.md:159-164,262-268`, QC-12 and QC-27). Existing named
  test modules carry the proof, keeping their existing trace pointers.
- **Other delegated reviews:** The sweep of `docs/nfdr.md` and `docs/adr/` for `development-design`
  found further applicable QC-40, QC-41 and QC-60 reviews (`docs/nfdr.md:354-383,522-527`, their
  verified-by tails). QC-41 passes: the delta introduces no secret. QC-60 passes for the design:
  it requires only string assembly already available on Python 3.11, with no new library feature.
  QC-5's by-type review is not triggered: the existing outcome/refusal selection is unchanged.
  Reviews conditional on changing saving, persistence or a saved field are not triggered.
- **QC-40 — pass under the existing browser exception:** On 2026-10-29, a read-only POST to
  `https://api.osv.dev/v1/querybatch`, querying each exact PyPI name/version in
  `tests/requirements.txt:4-18`, returned `{}` for all 15 results, with no vulnerability entries.
  The maintainers' advisory pages also showed no published advisories for
  [pytest](https://github.com/pytest-dev/pytest/security/advisories),
  [mypy](https://github.com/python/mypy/security/advisories),
  [Ruff](https://github.com/astral-sh/ruff/security/advisories) and
  [Playwright](https://github.com/microsoft/playwright/security/advisories).
  The pinned Playwright manifest specifies Chromium `153.0.8010.12`
  ([vendor manifest](https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/packages/playwright-core/browsers.json)).
  Google's October 27 desktop release publishes critical browser fixes
  ([vendor release](https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop_0562499947.html)).
  This is not a browser-clean verdict: `docs/nfdr.md:1049-1061`, RN-33, permits that precise build
  through 2026-11-07, which includes this review date. No pin or lock format changes here.
  The current shell reported `playwright import available: False` from
  `importlib.util.find_spec('playwright')`; the comparison therefore uses the pinned build,
  not a claim about an installed browser. T7 still requires the locked environment and browser.
- **Spec reading:** No spec line is set aside. CP-627's two suite invocations are retained;
  `tests/conftest.py:7-9,40-46`, collection policy, explicitly separates the browser suite.
  No collection change or product-document change is part of this design.
