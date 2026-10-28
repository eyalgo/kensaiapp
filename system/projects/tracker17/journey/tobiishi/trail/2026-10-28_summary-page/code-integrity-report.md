# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** tracker17 · `2026-10-28_summary-page` — a project's Summary view, counts as plain numbers.
**Mode:** workflow. In-repo product (`products/tracker17`): one worktree takes both the test and this report.

## Deferrals

None. The closing marker (`<a commit not in the public history>`, the newest `implementation complete`) carries no `Deferred:` line. It
records tasks 1 to 4 as landed at `4d0016f53`, `82d903b87`, `42380c1fb` and `b6cf4838d`.

## What was reviewed

The branch's code commits against `main`, under `products/tracker17/`:

- `domain/summary.py` (new), `domain/__init__.py`, `application/tracker.py`, `application/__init__.py`
- `web/routes.py`, `web/pages.py`, `web/style.css`
- the tests: `tests/unit/test_summary.py`, `tests/integration/test_summary_{tracker,routes,pages}.py`,
  `tests/e2e/test_summary.py`, `tests/timed_run.py`, `tests/integration/test_timed_run.py`, and the
  released edits to `test_pages.py`, `test_task_pages.py`, `test_routes.py`, `test_shapes.py` and `test_trace.py`

## The intent it was checked against

- `tl_instruction.md`: tasks 1 to 4, their *Behaviours to verify* and *Held by review* items.
- `change_spec.md`: CP-490 to CP-512, the Examples table and Locked Answers e-1, e-2, b-1 to b-5 and f-1 to f-5.
- `change_design.md` § 3 A to D: interfaces, ordering, reuse and atomic-landing edges.
- `change_text.md`: every published string. Each string on the page and in the timed run matches it word for word.
- `docs/fdr.md` was not needed. The spec cites its rules.

## Tests added or fixed

- **Added** `tests/unit/test_summary.py::test_summary_counts_no_overdue_or_undated_task_of_another_project`
  (CP-496 to CP-498, CP-507). Before this test, no case put an **overdue** task in a second project. So a
  Summary that took its overdue count over the whole tracker, not the requested project, would still have
  passed. CP-507 asks that "the second project's tasks are counted nowhere". The new case gives Beta two open
  tasks due yesterday, an undated `done` task and a task under a listed name. It asserts that Alpha's
  total, overdue, no-due-date, status, priority and assignee rows count none of them, and that Beta's own
  Summary counts them (3 · 2 overdue · 1 undated). It passed against the code as written.
- **Fixed:** none. Every existing Summary test asserts what the intent says. None was read off the code.

## The finding

**No issues.** The code already does what its intent says, so this is a clean pass with no red state.
Checked behaviour by behaviour:

- **Rows, order and zeros (CP-496, CP-499, CP-500).** `summarize_project` lists every status and priority
  in its enum order, so a zero still gets a row. Listed names keep `list_assignees` order. Unlisted names
  come only from this project's open tasks, sorted by `(casefold, exact)`, and the `None` bucket is last.
  The spec's five-task example is asserted row for row.
- **One copy of each rule (CP-505).** The total, status, priority and overdue counts all go through
  `filter_project_tasks`, with `OVERDUE_ON` imported from `domain/filtering.py`. Open membership is
  `TaskStatus.is_open`. An unlisted name is never sent through the assignee filter.
- **Fences (CP-506).** The domain module reads no clock, does no I/O, holds no wording and uses only frozen
  dataclasses. `Tracker.project_summary` reads the clock once (`astimezone().date()`, as the list reads
  do), then delegates.
- **Route and page (CP-490 to CP-495, CP-501 to CP-503, CP-510).** The route answers through `Site.handle`'s
  checks, maps a missing or oversized identity to the existing 404, and ignores the query. Every typed
  value goes through `_escape`. The page's only links are the header, the view pair and the empty
  project's invitation.
- **The view pair (CP-491).** `project_page` places the pair straight after the heading, so every outcome
  of the Tasks view shows it. The test covers 16 outcomes.
- **Released test edits (f-1 to f-5).** Each edit stays inside its Locked Answer. f-5's "no later feature
  module" clause is now held by `test_trace.py`'s reverse check and `test_no_excluded_feature_entry_exists`.

## Calls made

- **Three timed-run tests patch the harness with `monkeypatch.setattr`.** The cases are
  `tests/integration/test_timed_run.py::test_timed_summary_accepts_a_run_that_crosses_midnight` (it patches
  `harness._local_today` twice) and `::test_timed_run_includes_summary_failure_in_exit_status` (it patches
  `harness.measure_project_summary`).
  - *Question:* the Python packet's testing rule (`testing_python.md:31`, "The seam is a hand-written fake
    passed to the constructor — not `monkeypatch.setattr` on the module under test") binds over the
    file's own style. Should these tests be rewritten?
  - *Readings weighed:* (a) rewrite them by adding a `today` seam to `measure_project_summary` and a measure
    seam to `main`; (b) leave them, and record the divergence.
  - *Taken:* (b). Reading (a) changes two interfaces. `change_design.md` § 3 D fixes the first
    (`measure_project_summary(*, site, saved_data, timer) -> list[Timed]`). The second, `main(directory,
    timer)`, predates this change, and its two sibling tests (`:3270`, `:3653`) patch it the same way. That
    is a change of interface, which this skill does not make. The record-level rule, NFDR QC-28 ("never by
    patching a product module"), still holds, because `tests/timed_run.py` is test code and not a product
    module. The behaviour these tests assert is correct, and the developer's marker records the same
    divergence.
  - *Whose:* the Tech Lead's (the harness interface in the plan and design).
  - *If reversed:* `measure_project_summary` gains a keyword-only `today` callable that defaults to
    `_local_today`, and `main` gains a seam for its measures. Then the three cases, and the two older ones,
    hand fakes in instead of patching.

## Placement

The parts table is `docs/SDD.md` § 3. All of the change's logic is already in its owning part, so nothing
moved and there is no placement commit:

- The Summary counts, their order and the zero rows: `domain/summary.py` → **domain** ("the filter, sort
  and summary computations"). Already there.
- The clock read and the delegation: `Tracker.project_summary` → **application**. It counts, classifies and
  sorts nothing. Already there.
- The address, the not-found mapping, the HTML, the `(unassigned)` label, the choice of invitation by
  `total == 0`, and the CSS: `web/routes.py`, `web/pages.py`, `web/style.css` → **web**. It shows what
  `application` returns and computes no count. Already there.
- The timed measurement and its own expected values: `tests/timed_run.py` → test code. No production part
  owns it.

## Language resolution

Python, from step 1 of the chain: `project.md` `Languages: Python`. Packet read:
`<CORE>/doctrine/engineering/languages/python/README.md`, which routes to `conventions.md`, `layout.md`,
`quality_gates.md`, `toolchain.md`, `errors_logging.md`, `environment.md`, and to
`<CORE>/doctrine/engineering/testing_python.md` for testing. The review held the code to the packet
(frozen dataclasses, injected collaborators, PEP 604 unions, 100 columns). One divergence is recorded
under *Calls made* (`testing_python.md:31`). The developer's other recorded divergences give way to the
product's narrower records and are not re-decided here: no `__version__` in `domain/`, the
`requires-python` floor, and the test layout under `tests/unit` and `tests/integration`.

## Test evidence

- Full card run (`pytest products/tracker17/tests/`) through `gate_suite.py run --gate code-integrity`, with
  the added test: exit 0, **2046 passed in 165.24s**. The verdict rests on this run. No earlier full-card
  run was made in this review.
- Also run, because the card's command leaves out the browser tests: `pytest tests/e2e/test_summary.py`
  from the product root (`uv run`, with SIGINT reset as in the plan's notes) — **4 passed**.
- On the added test: `ruff format --check` and `ruff check` both clean.
