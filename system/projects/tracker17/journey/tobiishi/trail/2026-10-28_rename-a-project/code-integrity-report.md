# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-28_rename-a-project` — rename a project from its Tasks view.
**Reviewed:** 2026-10-28, by the Senior Engineer (`development-code-integrity`, workflow mode).

## Deferrals

None. The closing marker, `<a commit not in the public history>` (`developer: 2026-10-28_rename-a-project — implementation
complete`), carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

The product diff from the merge base `2f9cedf87` to `<a commit not in the public history>`, under `products/tracker17/`:

- production — `domain/projects.py`, `domain/__init__.py`, `application/tracker.py`,
  `application/__init__.py`, `web/pages.py`, `web/routes.py`;
- test support — `tests/timed_run.py`;
- tests — `tests/unit/test_projects.py`; `tests/integration/test_rename_tracker.py`,
  `test_rename_pages.py`, `test_rename_routes.py`, `test_pages.py`, `test_filter_pages.py`,
  `test_sort_pages.py`, `test_routes.py`, `test_timed_run.py`; `tests/e2e/test_rename_project.py`,
  `test_first_project.py`.

## The intent it was checked against

`tl_instruction.md` (Tasks 1–5 and their *Behaviours to verify* and *Held by review*),
`change_spec.md` CP-546–CP-568 and its Examples, `change_design.md` § 3 A–D and § 5 T01–T16, and
`change_text.md` for every published string. `docs/fdr.md` exists and was not needed beyond the
spec's own citations.

## Language resolution

Python — `project.md` `Languages:`, chain step 1. Packet opened:
`core/doctrine/engineering/languages/python/README.md`, with Conventions (`conventions.md`), Quality
gates (`quality_gates.md`) and Testing (`testing_python.md`) read as the review bar. Product records
outrank the packet on the Python floor (3.11 in the product's `pyproject.toml`). One divergence from
the packet is kept, under **Calls made** (1).

## Placement

Parts table: `docs/SDD.md` § 3. Every piece of logic the change added is in its owning part; nothing
was moved and no `… — placement` commit was made.

- The rename rule, `ProjectRenameOutcome` and the shared availability check — `domain`
  (`domain/projects.py`). Already there. No wording, HTML or I/O (QC-20).
- The rename action, saving only on a reported change — `application` (`application/tracker.py`).
  Already there. It branches on `outcome.changed` alone (QC-21).
- The request, the shared typed-refusal translation `_project_refusal`, the outcome decoding
  `_rename_area` — `web` (`web/routes.py`); the Rename area, `ProjectNameRefusal`, the one-focus read
  `_takes_focus` — `web` (`web/pages.py`). Already there. No name rule in `web`.
- The rename measurement, its expected-state oracle and its fixture report — test support
  (`tests/timed_run.py`), the home of every timed action. No production logic.

## The tests added or fixed

- **Added** `test_a_rename_counts_its_length_on_the_name_as_saved`
  (`tests/integration/test_rename_routes.py`). CP-552 counts the 200 code points "on the value as
  saved", after RT-10's line-break normalization, and no test sent a name that is over 200 as sent
  but exactly 200 as saved. It sends `a\r\n` × 100 (300 code points) and asserts it is accepted and
  saved as `a\n` × 100 (200), then sends one code point more after normalization and asserts the
  too-long refusal with saved bytes, saves and state unchanged. It is the rename's counterpart of
  the comment request's own normalized-length test (`test_comment_routes.py:289`). Checked against
  a mutant: with `_line_feeds` removed from `Site._rename_project` it goes red, beside the existing
  normalization test.
- **Fixed:** none. Every other behaviour the intent names already had a test written from the
  intent. The edits to the older tests (`test_pages.py`, `test_filter_pages.py`, `test_sort_pages.py`,
  `test_routes.py`, `test_first_project.py`, `test_timed_run.py`) were read against spec Gap 10 and
  design T13–T15: each admits the Rename form or the rename block and keeps every other assertion.

## The finding

No issues. The code does what its intent says: the new test was green on its first run against the
code as the developer left it, and so was the whole suite. Nothing was misplaced.

Held-by-review items, read off the diff:

- CP-555 / QC-5 — creation and rename share `check_project_values` and `_check_name_available` in
  `domain`, one `_project_refusal` in `web/routes.py`, and one `_name_reason` in `web/pages.py`.
  Creation's redirects are unchanged, its description-too-long case included.
- QC-23 / QC-36 — every value the Rename area interpolates goes through `_escape`, and every
  redirect through `_redirect` / `_address`. The area keeps nothing between requests.
- CP-548 — "Project name", "Save", the completion line, the failed-save line, the console line,
  the three timed labels and the fixture line match `change_text.md` character for character.
- CP-566 — `_expected_after_rename` replaces one name in the loaded fixture and calls no domain
  rule. The rename runs on its own `rename-volume` fixture.

Observed and left as is: `_takes_focus` recognises every way `web/pages.py` writes `autofocus`
today. All of them are a bare attribute followed by a space or `>`. A future page that writes
`autofocus=""` would not be seen by it.

## Calls made

1. **The exit-status test that patches the harness.**
   - *Question:* `test_a_failed_rename_or_older_action_makes_the_run_exit_nonzero`
     (`tests/integration/test_timed_run.py`) uses `monkeypatch.setattr` on
     `harness.measure_project_rename`. The packet's testing rule says the seam is a hand-written
     fake passed in, never `monkeypatch.setattr` on the module under test
     (`testing_python.md` § Rules).
   - *Readings:* bring the test to the packet by giving `main` a measurement seam, or keep it.
   - *Taken:* keep it. `main(directory, timer)` seeds a fresh fixture for every block and takes
     nothing else. No real refusal can reach it without a new parameter, and that changes the
     harness's interface, which the plan did not cut. Three older tests in the file replace a
     measurement the same way (the filter, the sort and the Summary), and a fourth patches the
     harness's clock. The developer recorded this divergence. The test itself is written from
     T15's intent, and the site it drives is a hand-written fake (`Intercept`).
   - *Owner:* the Tech Lead (the plan).
   - *If reversed:* `main` gains a measurement seam, and this test and the four older ones move to it.
2. **The header test left unedited.**
   - *Question:* spec Gap 10 expected
     `test_pages.py::test_every_page_has_a_header_with_the_projects_and_people_links` to admit
     "rename" on the project pages. The diff leaves it unchanged.
   - *Taken:* leave it. The test reads visible text only. The Rename area shows no word "rename":
     its label is "Project name" and its button "Save" (`change_text.md`). So the test passes
     unchanged and keeps its stronger assertion, and nothing the spec asks for is lost.
   - *Owner:* the Product Owner (the spec).
   - *If reversed:* the test admits "rename" on the project and created samples, and is weaker for it.

## Test evidence

- Full-card run through `gate_suite.py run --gate code-integrity`:
  `pytest products/tracker17/tests/` on Python 3.11.15, **2384 passed in 340.15s**, exit 0. That
  is the developer's 2383 plus the one added here.
- Local runs before it: `tests/integration/test_rename_routes.py`, 29 passed; the mutant run of
  the normalization and length tests, 2 failed as expected, with `web/routes.py` restored after.
- `ruff format --check` and `ruff check` on the edited test file: clean.
