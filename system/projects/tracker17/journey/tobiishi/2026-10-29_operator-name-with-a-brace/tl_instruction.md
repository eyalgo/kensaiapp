# Tech Lead instruction — operator-name-with-a-brace: render the name as typed

**Category:** bug
**Behaviour:** changing
**Product root:** products/tracker17 — every product path below is relative to it; commands state their working directory.
**Scope:** Correct the Your name outcome paragraph, with regression and continuity coverage for saved, failed, blank and too-long outcomes (change_spec.md § Rules A–C).

This plan owns the tasks for `tracker17 · tobiishi · 2026-10-29_operator-name-with-a-brace`.
The required behaviour is `change_spec.md` § Rules; the rendering boundary is
`change_design.md` § 1, Change Summary. Product records are read-only inputs.

## Project layout

```text
products/tracker17/
  web/
    pages.py                                ← modified: _your_name_section only
  tests/
    integration/
      test_people_routes.py                 ← modified: redirect regressions and refusal guards
      test_people_pages.py                  ← modified: paragraph placement and escaping
```

Create no directory, module, package, dependency or public interface. Whole-page building belongs
to `web` (docs/SDD.md § 3, The parts, `web` row). The full module set and allowed/forbidden imports
remain those of docs/nfdr.md:166-197, § 1.2, Forbidden imports (QC-13–QC-19). No new import is
needed by the paragraph assembly in change_design.md § 1, Change Summary.

## TL Review Notes

Decisions by the Tech Lead, 2026-10-29:

- **Task cut:** The design has no separate § 3 sub-jobs table; § 2, Blast Radius explicitly says
  there is no sub-job split. Task 1 therefore carries its one web correction and T1–T5 coverage
  together. T3/T4 remain guards within that task: CP-626 does not require those assertions to
  fail before the correction. T1/T2 supply its regression failures, so the task uses the
  test-first marker rather than the already-green marker.
- **Change-only checks:** Task 2 makes the request's untouched-code and untouched-document
  boundaries review deliverables against the branch's own merge base. They are not permanent
  suite tests, because a later change may legitimately modify those files (change_spec.md
  § Out of Scope; change_design.md § 2, Blast Radius).
- **Suite coverage:** Keep the card's `pytest products/tracker17/tests/` and explicitly require
  the separate `pytest products/tracker17/tests/e2e/`. The collection hook excludes e2e unless
  that directory is named (tests/conftest.py:29-46, `_command_line_names_end_to_end` and
  `pytest_ignore_collect`); this is the two-command contract of CP-627 and design T7, not a
  collection change.
- **Language resolution:** Python, step 1, from the project card's `Languages:` line; opened
  `<CORE>/doctrine/engineering/languages/python/README.md` and its seven routed concerns.
  Product records govern the existing root layout, Python 3.11 floor and locked test tools
  (docs/SDD.md § 3, The units; docs/nfdr.md QC-39, QC-59 and QC-62). No type or topology
  change is required.
- **Baseline reproduction:** A read-only `python3 -` probe using the real `Site`, `named_site`, `set_name`,
  `location`, `RecordingSaver` and injected `RaisingSaver` returned 303 for both outcomes,
  followed by `KeyError: 'x'` on `{x}` and `ValueError` on `}` and `{0}`. `{{x}}` returned 200
  but its outcome showed `{x}`. Blank and 201-character submissions with `{x}` saved both
  returned 200 and made zero additional saves. This confirms T1/T2's regression shape and
  T3/T4's guard shape; the developer's tests still provide CP-625's before/after proof.
  `git diff fd47d2155 -- products/tracker17` printed nothing, so the probed product matches
  the spec's starting product.
- **Tool prerequisites:** The planning shell's `importlib.util.find_spec` and `shutil.which`
  probe returned unavailable for `playwright`, `ruff` and `mypy`. Do not substitute a skipped
  browser suite or omitted quality gate for CP-627/CP-628. Their prerequisites are the
  committed tests/requirements.txt and docs/SDD.md § 4 RT-4; no pin change is authorized.
- **Capacity gate added:** Task 1 also runs `python3 tests/timed_run.py`, the command
  docs/nfdr.md § 10, Verification map assigns QC-48 at implementation. Design T7/T8 names
  the suites and quality tools but omits that inherited gate; adding its invocation preserves
  the product's existing capacity check without changing its measurement or adding an action.
- **Execution prerequisites:** The first `pytest products/tracker17/tests/` invocation collected
  2,629 tests and ended `20 failed, 2578 passed, 31 errors`; listener setup reported
  `PermissionError: [Errno 1] Operation not permitted` at `socket.bind`. A loopback-approved
  invocation was then allowed and ended `12 failed, 2617 passed in 636.86s`: all 12 failures
  were in `tests/integration/test_start.py`, timing out at `child.communicate(timeout=30)`
  after SIGINT. The diagnostic command
  `python3 -c 'import signal; print("SIGINT ignored:", signal.getsignal(signal.SIGINT) == signal.SIG_IGN)'`
  printed `SIGINT ignored: True` without a terminal and `False` with one. The startup helper
  sends SIGINT and waits up to 30 seconds (tests/integration/test_start.py:516-536,
  `_run_real_start`). A further suite invocation with a terminal was refused before execution
  by automatic approval review as a retry with changed execution settings; that invocation
  produced no test result. The observed ignored signal is consistent with the shutdown
  timeouts, but the terminal suite result is unverified. No green baseline suite is claimed,
  and no product source is changed to compensate for these run settings.

## Gate environment inputs

The tracked-file inventory was read from this change's product tree and repository; the JSON
records evidence for the gate tool, not an environment verdict. There is no CI version to quote
as an image tag. No environment override or amd64 decision was found in docs/adr/, docs/nfdr.md
or docs/SDD.md (their Decision sections, NFDR § 8, and SDD § 3–4 respectively).

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git -C products/tracker17 ls-files: 274 tracked product files, including 111 non-document paths; inspected the listing and found no CI configuration or build-service entry point. The repository-wide git ls-files inventory also found no hosted/self-hosted CI configuration or Makefile, justfile, Taskfile.yml, tox.ini or noxfile.py."
  },
  "decisions": {"override": null, "amd64": null},
  "candidates": [
    {
      "language": "python",
      "image": "docker.io/library/python",
      "image_source": {
        "root": "core",
        "file": "doctrine/engineering/languages/python/environment.md",
        "anchor": "Start a container from the official Python image, `docker.io/library/python`, tagged with CI's"
      }
    }
  ],
  "guest": null
}
```

### Task 1: Correct the Your name outcome paragraph and prove its four outcomes (`web/pages.py`, `tests/integration/test_people_routes.py`, `tests/integration/test_people_pages.py`)

**Dependencies:** None

**What to build:** In `_your_name_section`, insert the already-escaped outcome line as data
after selecting its paragraph class. Keep outcome selection, escaping, placement, field values,
redirects and focus as CP-619–CP-624 state. All four outcomes use this correction. Extend the two
existing test modules named in design § 5; retain their assertions and add the applicable CP
references to their opening docstrings (CP-629).

#### Behaviours to verify

In `tests/integration/test_people_routes.py`, add these four tests, using its existing helpers:

- `test_saved_operator_name_with_braces_is_shown_exactly` — one parameterized test (design T1;
  CP-619, CP-621, CP-622, CP-624, CP-625). POST a new name, assert 303 and the existing
  `/people` query `operator_saved=<name>`, then GET that actual Location. Assert 200, exactly
  one outcome paragraph with text `You set your name to '<name>'.`, exact field value, and the
  field as the sole focus with `aria-describedby="operator-name-outcome"`. Assert the tracker
  holds that name and the save is recorded. No Python exception text or traceback reaches the
  page.
- `test_failed_operator_name_with_braces_is_shown_exactly` — one parameterized test over the
  same names (design T2; CP-620–CP-622, CP-624, CP-625). Hand the tracker `RaisingSaver` with
  an error carrying a distinctive message; keep the real route, application and page builder.
  POST, assert 303 and `/people?operator_failed=save&operator_typed=<name>` by parsed query,
  then GET its actual Location. Assert 200 and exactly one line reading
  `The tracker couldn't set your name to '<name>', and nothing was changed. What you typed is still in the form. Try again.`
  The field retains the exact typed name; `#save-operator-name` is the sole focus and has the
  linked outcome description. The error type, distinctive error message and traceback are
  absent from the page. The saver is called once and the tracker's original name is unchanged;
  build the starting state before handing in the failing saver, so setup cannot consume the
  intended failure. Do not patch a name in a product module.
- `test_blank_operator_name_after_brace_name_shows_refusal` — save `{x}`, snapshot the save
  count, POST an empty name and GET its actual redirect (design T3; CP-623, CP-624, CP-626).
  Assert the blank-refusal query, 200, exactly one line
  `Your name can't be blank. Type a name.`, an empty field, field focus/description, no Python
  error text, `{x}` still stored and no additional save.
- `test_overlong_operator_name_after_brace_name_shows_refusal` — save `{x}`, snapshot the save
  count, submit 201 characters and GET the actual redirect (design T4; CP-623, CP-624, CP-626).
  Assert the too-long query, 200, exactly one line
  `Your name can't be longer than 200 characters. Type a shorter one.`, `{x}` as the field
  fallback, field focus/description, no Python error text, no overlong payload in the address
  or page, and unchanged stored name and save count.

The shared T1/T2 matrix is `{x}`, `}`, `{0}`, `{}`, `a{b`, `{x!r}`, `{{x}}`, `{<b>&"}`, the
one-character `{`, and an accepted name of exactly 200 code points containing repeated and mixed
braces (design § 5, T1/T2). Use fresh state per case. Preserve literal braces in the expected
parsed text, including both pairs in `{{x}}`; the absence of an exception alone does not prove
CP-621. The raw source for `{<b>&"}` contains `{&lt;b&gt;&amp;&quot;}` on both outcome paths (CP-622).

In `tests/integration/test_people_pages.py`, extend rather than replace these tests (design T5):

- `test_operator_outcome_focus_has_one_linked_accessible_description` — retain its four rows
  and plain-name cases. Check the paragraph's exact tag/class/id and placement: saved uses
  `<p class="outcome" id="operator-name-outcome">` above the form; blank and too-long use
  `<p class="reason" id="operator-name-outcome">` inside the field block above the input;
  failed uses that same reason paragraph after the field block and before Save. Preserve the
  existing single-focus and linked-description assertions (CP-624).
- `test_operator_name_and_outcome_values_render_as_text` — retain the hostile-text cases and
  extend saved and failed outcomes with `{<b>&"}`. Check the escaped raw source, the original
  name in parsed outcome text and field value, no injected tags, unique ids and unchanged
  surrounding structure (CP-622, CP-624).

Keep the existing no-name, unchanged-name, query-precedence and assignee assertions intact
(design § 5, Rule-implied edges). Both modified modules remain named by the `Checked by` opening
docstring in `domain/operator_name.py:12-16`; this plan adds no module needing a new pointer.

#### Held by review

- CP-630's one-function escaping, no retained state, no new rule, web-only correction and no
  unpaid part — inspect the production diff against docs/nfdr.md QC-8, QC-12, QC-23, QC-27 and
  QC-36 and docs/SDD.md § 3 and § 4 SEC-4. These absolute properties are held by reading the
  changed assembly; the rendering tests exercise the specified outcomes.
- CP-624's unchanged wording and no-name text, and the ban on changing other pages' text
  building — Task 2's diff review holds the change boundary. Do not edit product documents.

#### Implement

Infer from failing tests.

# Hint:
Resolve the class using the existing outcome, then insert the already-escaped outcome line as a
value in one assembly step. Do not pre-double braces or escape the completed HTML; either would
change the text or markup. Keep `_escape` as the sole value-to-HTML boundary.

#### Verification gate

Run from the change worktree root, with the product's locked test environment on PATH:

```sh
pytest products/tracker17/tests/integration/test_people_routes.py products/tracker17/tests/integration/test_people_pages.py
pytest products/tracker17/tests/architecture/test_trace.py
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/
```

Pass: every command exits 0; the full non-browser command collects unit, integration and
architecture, and the separate browser command collects e2e (CP-627). T1 and T2 both fail on
the starting product at `fd47d2155` and pass on the corrected product; specifically `{x}`, `}`
and `{0}` must reach their redirect GET before the baseline fails (CP-625, design T6). T3/T4
are guards and need no baseline failure. Existing assertions remain and the trace test passes.
Record the before/after test results as change evidence, not as a suite assertion about a SHA.

The product's test environment is prepared from the product root with the existing lock, per
tests/requirements.txt:1-3, Install, and docs/SDD.md § 4 RT-4:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tests/requirements.txt
.venv/bin/python -m playwright install chromium
```

Use that virtual environment for the commands above and below. Run these from the product root:

```sh
python3 -m compileall -q main.py errors.py domain application persistence web tests
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
python3 tests/timed_run.py
```

Pass: every command exits 0, with Ruff and mypy at the versions pyproject.toml pins (CP-628;
docs/nfdr.md QC-62). Run the two suites with tests/requirements.txt's locked tools and installed
Chromium (docs/SDD.md § 4 RT-4). Missing tools or a missing browser do not satisfy the gate.
The timed run exits 0 at the volume and action bar in docs/nfdr.md QC-48 and retains its existing
measurement; this change adds no listed action.

### Task 2: Verify the change stays inside its rendering boundary (`web/pages.py`, `tests/integration/test_people_routes.py`, `tests/integration/test_people_pages.py`)

**Dependencies:** Task 1 — reviews the correction and coverage it produces.

**What to build:** A review verdict for the change-only scope constraints; no extra product file
or permanent test. Record each verdict in Developer Review Notes.

#### Deliverables verified by review

- The product diff names only the three paths in Project layout. Every product document,
  other page, route, state/rule module, dependency pin and collection hook stays unchanged
  (change_spec.md § Out of Scope; change_design.md § 2, Blast Radius).
- Within `web/pages.py`, the production diff changes only `_your_name_section`'s paragraph
  assembly/class placement. `_operator_line` still escapes the name, `_escape` is unchanged,
  no completed paragraph is interpreted as a format string, and outcome selection, wording,
  form placement, ids and focus follow CP-624. Other `.format` sites stay unchanged.
- Both test modules retain their existing assertions and trace references and add the T1–T5
  coverage. The saved and failed regressions have the CP-625 before/after record; guards do
  not acquire a requirement to fail on the starting code.

#### Implement

Verified by review — no test.

#### Verification gate

Run these commands from the product root; each compares with this branch's own merge base,
including uncommitted changes:

```sh
git diff --name-only "$(git merge-base main HEAD)" -- . ':!web/pages.py' ':!tests/integration/test_people_routes.py' ':!tests/integration/test_people_pages.py'
git diff --function-context "$(git merge-base main HEAD)" -- web/pages.py
git diff "$(git merge-base main HEAD)" -- tests/integration/test_people_routes.py tests/integration/test_people_pages.py
```

Pass: the first prints nothing; the second and third satisfy every review criterion above.
These checks belong to this change and are not added to the permanent suite.

From the change worktree root, run:

```sh
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/
```

From the product root, run:

```sh
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: both full suites and all three quality checks exit 0 with no new failures; Task 2 adds no
tests of its own. All review deliverables have recorded verdicts.
