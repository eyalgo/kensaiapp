# Change Spec — the Your name section shows a saved operator name holding a curly brace as typed

**Date:** 2026-10-29
**Category:** bug
**Behaviour:** changing
**Request:** Fix the People page's Your name section so a saved operator name holding a curly brace, such as `{x}`, `}` or `{0}`, shows as typed instead of making the page raise. Today `_your_name_section` (`products/tracker17/web/pages.py`) puts the already-escaped outcome line into an f-string paragraph and then calls `.format` on it, so the name's braces are read as format fields (`POST /operator-name` with `name={x}`, then `GET` of the address it redirects to, raises `KeyError: 'x'`). After this, the saved line and the failed line show the name exactly as typed, with its braces, HTML-escaped as before, on the address the save lands on. The three outcomes are one capability, so one merge: splitting by outcome would leave two still crashing. The proof goes in the same merge: one test for the saved outcome and one for the failed outcome, each of which fails on the code at the commit the change starts from and passes after; one test each for the blank and too-long refusals with `{x}` already saved, showing the refusal line and no error (guards, not required to fail beforehand); and `pytest products/tracker17/tests/` passing with its unit, integration, e2e and architecture folders all collected. What must not be weakened: the outcome lines' wording, CSS classes, ids and focus behaviour stay exactly as they are, only how the name reaches the page changes; no other page's text building is touched, including any other page that builds text with `.format` over a user-typed value, which is left to a later seed; and no document is edited to fit the code.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, and every concern it routes read; no line fixes the rendering of anything a rule below pins

---

## Change Summary

A saved or failed operator name holding `{` or `}` stops breaking the People page: the saved line and
the failed line show the name exactly as typed, braces included, HTML-escaped as any name is today.
Nothing else on the page, and no other page, changes.

Paths below are relative to the product root, which `system/projects/tracker17/project.md`
`Product path:` names. The change starts from commit `fd47d2155`.

---

## Rules

### A — The Your name section with a name holding a curly brace

- **CP-619:** After `POST /operator-name` saves a name, `GET` of the address the submission redirects
  to — `/people?operator_saved=<name>`, the address it lands on today, unchanged — answers status
  `200` with the People page. Its outcome line reads `You set your name to '<name>'.`, where `<name>`
  is the saved name exactly as typed: every `{` and `}` in it is shown, and none is added, dropped,
  doubled or halved.
- **CP-620:** After `POST /operator-name` whose save fails for a reason that is not a refusal,
  `GET` of the address it redirects to — `/people?operator_failed=save&operator_typed=<name>`,
  unchanged — answers `200` with the People page. Its outcome line reads `The tracker couldn't set
  your name to '<name>', and nothing was changed. What you typed is still in the form. Try again.`,
  with `<name>` the typed name exactly as typed, braces as CP-619 states. The field still holds the
  typed name.
- **CP-621:** The names CP-619 and CP-620 cover are every name the Your name form accepts — at least
  one non-whitespace character and at most 200 characters (FDR R-62, R-76) — wherever `{` or `}`
  sits in it, however many there are, and whether or not they pair. The request's `{x}`, `}` and
  `{0}` are members, not the set; so are `{}`, `a{b`, `{x!r}` and `{{x}}`.
- **CP-622:** The name in both lines is HTML-escaped as any name on the page is today, so a name
  holding `<`, `&` or `"` beside a brace — `{<b>&"}` — shows those characters as typed and changes
  nothing around it (FDR R-112; NFDR QC-36; SDD § 4 SEC-4).
- **CP-623:** With a name holding a brace already saved — `{x}` — a blank submission and a too-long
  submission each land on the People page, answered `200`, showing its refusal line:
  `Your name can't be blank. Type a name.` and
  `Your name can't be longer than 200 characters. Type a shorter one.`
- **CP-624:** Everything else about the section stays as it is today. The three lines' wording. The
  saved line is `<p class="outcome" id="operator-name-outcome">`, above the form. A refusal line is
  `<p class="reason" id="operator-name-outcome">`, inside the field's block, above the field. The
  failed line is `<p class="reason" id="operator-name-outcome">`, below the field, above Save. The
  saved and refusal outcomes put `autofocus` and `aria-describedby="operator-name-outcome"` on the
  field `#operator-name`; the failed outcome puts them on Save, `#save-operator-name`. The no-name
  line, and the addresses every `POST /operator-name` redirects to, are unchanged.

### B — Tests the change adds

- **CP-625:** One test for the saved outcome and one for the failed outcome. Each sends
  `POST /operator-name` with each of `{x}`, `}` and `{0}`, follows the redirect, and asserts status
  `200`, the outcome line of CP-619 or CP-620 with the name as typed, and that the page holds no
  error text produced by Python — no exception message, no traceback (FDR R-108; NFDR QC-57). Each
  fails on the code at `fd47d2155`, where the `GET` raises, and passes after the change. The
  failed-outcome test makes the save fail through a saver handed to the tracker, never by patching a
  name inside a product module (SDD § 4 TS-2; NFDR QC-28).
- **CP-626:** One test per refusal, blank and too-long, with `{x}` saved, asserting `200`, the
  refusal line of CP-623 and no Python error text. These are guards: a refusal line carries no
  name, so they pass on `fd47d2155` and are not required to fail there.
- **CP-627:** Run from the change worktree's root, `pytest products/tracker17/tests/` exits `0`
  having collected the `unit`, `integration` and `architecture` folders, and
  `pytest products/tracker17/tests/e2e/` exits `0` having collected the `e2e` folder, where the
  browser-driving library `tests/requirements.txt` pins is installed (NFDR § 9, § 10; SDD § 4 TS-1; SDD § 6, "'Both suites pass' means `pytest tests/` exits 0 and
  `pytest tests/e2e/` exits 0").

### C — Checks the records above the change require of it

- **CP-628:** The code passes the three gates NFDR QC-62 names, each exiting `0` from the product
  root: `ruff format --check .`, `ruff check .`, and
  `mypy main.py errors.py domain application persistence web`, at the versions `pyproject.toml`
  pins (NFDR QC-62).
- **CP-629:** Every test module the change adds names the requirements or acceptance criteria it
  checks, and is named in the opening docstring of `domain/operator_name.py`, and the pointer test
  in `tests/architecture/test_trace.py` passes (NFDR QC-11; SDD § 4 TS-3, TS-4).
- **CP-630:** Because the change touches page building in `web`, it takes the reviews at
  `development-design` the NFDR assigns such a change: that the name still reaches the page only
  through the one function that escapes every value (NFDR QC-36, its one-function half; SDD § 4
  SEC-4); that `web` keeps nothing between requests (QC-8, its keeps-nothing half); that `web` owns
  no rule (QC-23, its no-rule half); that the change stays inside `web` (QC-27); and that it adds no
  part no requirement pays for (QC-12).

---

## Examples

| Scenario | Expected behavior |
|---|---|
| `POST /operator-name` with `name={x}`, then `GET /people?operator_saved=%7Bx%7D` (CP-619, CP-625) | `200`; line `You set your name to '{x}'.`, focus on the field |
| Same with `name=}` and `name={0}` (CP-619, CP-621, CP-625) | `200`; `You set your name to '}'.` and `You set your name to '{0}'.` |
| Same with `{}`, `a{b`, `{x!r}` (CP-621) | `200`; each name shown as typed |
| Same with `{{x}}` (CP-621) | `200`; `You set your name to '{{x}}'.` — not `'{x}'`, which shows today |
| A save of `{x}` that fails, then `GET /people?operator_failed=save&operator_typed=%7Bx%7D` (CP-620, CP-625) | `200`; line `The tracker couldn't set your name to '{x}', and nothing was changed. What you typed is still in the form. Try again.`; the field holds `{x}`; focus on Save |
| Same failed save with `}` and `{0}` (CP-620, CP-625) | `200`; each name shown as typed in the failed line |
| Saved name `{<b>&"}` (CP-622) | `200`; the page source holds `{&lt;b&gt;&amp;&quot;}` in the line; the operator reads `{<b>&"}` |
| `{x}` saved; a blank submission (CP-623, CP-626) | `200`; `Your name can't be blank. Type a name.`; no Python error text |
| `{x}` saved; a 201-character submission (CP-623, CP-626) | `200`; `Your name can't be longer than 200 characters. Type a shorter one.`; no Python error text |
| `Sam` saved, or failed, or refused (CP-624) | Every line, class, id and focus exactly as on `fd47d2155` |
| The saved and failed tests at `fd47d2155` (CP-625) | Each fails |
| The two suites after the change (CP-627) | Both exit `0`; the first collects unit, integration and architecture, the second e2e |
| The QC-62 gates (CP-628) | Each of the three commands exits `0` |
| A new test module for the Your name section (CP-629) | It names its requirements, `domain/operator_name.py`'s opening docstring names it, and the pointer test passes |

CP-630 has no row: it is a review at `development-design`, which no scenario's output shows.

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| Today the `GET` after a saved or a failed name holding a brace raises; the redirect addresses are as CP-619 and CP-620 state | Ran a probe at `fd47d2155` on the real `Site` built by `tests/integration/test_routes.py`'s `make_site` — a recording saver for the saved outcome, a saver raising `OSError` for the failed one — sending `POST /operator-name` and then `GET` of its `Location`, for `{x}`, `}`, `{0}`, `{}`, `a{b`, `{x!r}`, `{<b>&"}` and `Sam` | Every brace name, on both outcomes: `POST` `303` to `/people?operator_saved=…` or `/people?operator_failed=save&operator_typed=…`, then the `GET` raised — `KeyError: 'x'` for `{x}` and `{x!r}`, `ValueError` for `}`, `{0}` and `a{b`, `IndexError` for `{}`, `KeyError` for `{<b>&"}`. `Sam`: `200`, the lines as CP-619 and CP-620 state them |
| `{{x}}` raises nothing today but shows `{x}` | Same probe with `{{x}}` | `200`; saved line `You set your name to '{x}'.`, failed line likewise |
| With `{x}` saved, the two refusals already answer `200` with their lines | Same probe: `{x}` saved, then a blank and a 201-character submission | `200`; `Your name can't be blank. Type a name.` and `Your name can't be longer than 200 characters. Type a shorter one.`; no `Traceback` in either page |
| The cause sits in `_your_name_section` | Read `web/pages.py:2806-2852` | `:2818` builds the line, `:2819` puts it in `f'<p class="{{}}" id="{_OPERATOR_OUTCOME_ID}">{line}</p>\n'`, and `:2823`, `:2827`, `:2829` call `.format` on the result |
| CP-624's placement, classes, ids and focus are today's | Read `web/pages.py:2816-2851` and `:386-388` | Saved line class `outcome` before the form; refusal line class `reason` before the field's `<input>`; failed line class `reason` after the field's block, before Save; the description and `autofocus` go to the button for a failure, else to the field; ids `operator-name`, `save-operator-name`, `operator-name-outcome` |
| A name enters a page through one escaping function | Read `web/pages.py:452-454` | `_escape` returns `html.escape(value, quote=True)`, docstring "The one place a value enters a page (SEC-4)" |
| No other `.format` call in `web` puts typed text into a template | `grep -n '\.format(' web/pages.py web/routes.py` and read each site | 23 calls, all in `pages.py`; every one but `:2823`, `:2827`, `:2829` fills a template the code holds (module constants such as `DELETED_LINE` `:846`, `_OVERTAKEN_LINES` `:1030`, `_UNLISTED_ASSIGNEE` at `:1367`) and passes typed text only as an argument |
| `pytest products/tracker17/tests/` does not collect `tests/e2e/` | Ran `pytest products/tracker17/tests/ --collect-only -q` from the change worktree's root at `fd47d2155`; read `tests/conftest.py:7-9` and `:40-46` | 64 architecture, 1,959 integration, 606 unit, no e2e. The conftest's `pytest_ignore_collect` skips `tests/e2e/` unless the command line names it, and its docstring cites "docs/nfdr.md § 10" for the two suites |
| The e2e suite needs the pinned browser-driving library | Ran `pytest products/tracker17/tests/e2e/ --collect-only -q`; read `tests/requirements.txt:12` | On this machine: `ModuleNotFoundError: No module named 'playwright'`; the pin is `playwright==1.63.0` |
| The suite passes today, and no existing test asserts today's brace behaviour | Ran `pytest products/tracker17/tests/` at `fd47d2155`; grepped `tests/integration/test_people_*.py` and `tests/e2e/test_people.py` for a brace inside a name | `2629 passed`; the only braces are the tests' own `'{name}'` templates, filled with `.format(name=…)`. No existing test is named as changing |
| `domain/operator_name.py`'s opening docstring lists the Your name section's test modules | Read `domain/operator_name.py:1-17` | Lines 12-16 list them, `tests/integration/test_people_routes.py` and `tests/integration/test_people_pages.py` among them |
| No rule pins output rendering a language-level fact | Walked every rule against SKILL.md Step 2's definition | The lines, statuses, classes and ids are all product-chosen; no rendering row is owed |

The QC-62 gates were not run: neither `ruff` nor `mypy` is installed on the machine this spec was
written on. CP-628 states what must pass, and claims nothing about the tree today.

---

## Out of Scope

- Every other page's text building, including any page that builds text with `.format` over a
  user-typed value — in the request's words, "no other page's text building is touched … which is
  left to a later seed". The read under Verified Claims found no other `.format` call in `web` that
  puts typed text into its template, so no record gap is handed on.
- The wording of every line, and the section's classes, ids, focus and layout (CP-624).
- `POST /operator-name` itself: what it accepts and refuses, what it saves, the address it redirects
  to, and the console message a failed save writes.
- The Your name field's value on the plain People page and after a refusal, which already shows a
  brace name as typed.
- Every product document. None is edited to fit the code.
- NFDR QC-36's end-to-end test entering `<`, `&` and `"`: it binds every text field a change adds,
  and this change adds none. Its one-function half binds this change and is CP-630.

---

## Locked Answers (the divergence record — self-review 2026-10-29)

- **Gap 1 — which names the fix covers (b):** every name the form accepts, wherever its braces sit
  (CP-621). The request names three examples and says "shows as typed". A rule keyed to those three
  would leave `{}`, `a{b` and `{x!r}` — each of which also raises today — and `{{x}}`, which raises
  nothing but shows the wrong name, inside the same defect and outside the rule.
- **Gap 2 — the suite command (a request that contradicts the product's own records):** CP-627
  states two commands where the request names one. `pytest products/tracker17/tests/` cannot collect
  the `e2e` folder: the product keeps the browser suite separate on purpose, and NFDR § 9 and § 10,
  SDD § 6 ("'Both suites pass' means `pytest tests/` exits 0 and `pytest tests/e2e/` exits 0")
  and the Python testing packet ("Layer 5 lives in `tests/e2e/`. Separate invocation") all
  say so. Making the one command collect it would change the product's test setup against those
  records, which the request rules out ("no document is edited to fit the code") and which is not
  this fix. The request's intent — every folder collected and passing — is what CP-627 keeps. The
  station's reached-when 5 carries the same wording, so it cannot be met as written either.
- **Gap 3 — what "exactly as they are" pins (b):** CP-624 writes out today's classes, ids, placement
  and focus, so a reviewer can check "unchanged" against a stated shape rather than against memory.
- **Gap 4 — checks the records require (e):** CP-622 (FDR R-112, NFDR QC-36, SDD SEC-4), CP-625's
  no-error-text and saver-handed-in clauses (FDR R-108, QC-57; SDD TS-2, QC-28), CP-628 (QC-62),
  CP-629 (QC-11; SDD TS-3, TS-4) and CP-630 (the `development-design` reviews of QC-36, QC-8, QC-23,
  QC-27 and QC-12) are stated, though the request names none of them. Each binds a change that
  touches page building in `web` or adds tests, and this one does both.
