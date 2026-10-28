# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-28_delete-a-project` · **Date:** 2026-10-28 · **Mode:** workflow

## Deferrals

None. The closing marker (`<a commit not in the public history>`, the newest `— implementation complete` commit on the branch)
carries no `Deferred:` and no `Failing:` line.

## What was reviewed

The product diff `main...2026-10-28_delete-a-project` under `products/tracker17/`: production code in
`domain/projects.py`, `domain/tasks.py`, `domain/__init__.py`, `application/tracker.py`,
`application/__init__.py`, `web/routes.py`, `web/pages.py`, `web/style.css`, and every test file and
`tests/timed_run.py` the six tasks changed (26 files).

## The intent it was checked against

`tl_instruction.md` (Tasks 1–6, their *Behaviours to verify* and *Held by review* items),
`change_spec.md` (CP-569–CP-593 and its Examples), `change_design.md` § 3 and § 5 (T1–T22), and
`change_text.md` for every published string. `docs/fdr.md` was not needed for any call.

## Tests added or fixed

- **Added** one case to
  `tests/integration/test_delete_project_pages.py::test_malformed_or_incomplete_completions_are_ignored`:
  a Projects address whose `deleted_project_tasks` holds 5,000 digits. The decoder guards that
  conversion (Python refuses to turn more than 4,300 digits into an int, with a `ValueError`), but no
  test reached the guard. With the guard removed, Projects would raise on that address instead of
  answering. The case asserts the ordinary Projects page, 200, with no `Cache-Control` header (see
  *Calls made*).
- **Fixed:** none. Each named behaviour of Tasks 1–6 has its test, and each one asserts the intent.
  The route tests check the saved bytes before and after each refusal, each stale submission is its
  own case, forged form fields are tried, and the timed run's expected state is built without the
  product's deletion rule.

## The finding

No issues. The code already did what its intent says, every behaviour now has a correct test, and the
suite is green. Nothing was moved.

The plan leaves two checks to review, and both hold:

- **CP-585:** the task deletion changes only its confirmation's status. `_delete_area` takes its keys
  as a parameter now, with the task's keys and order as the default. The task page passes its
  resolved area to `_pending_status`. The new CSS rules are scoped to `.strip-control`, and task
  strips render as `strip-row-control`. `pages.py` has no other task-deletion change.
- **CP-592:** `git diff --name-only --diff-filter=A "$(git merge-base main HEAD)" -- domain` prints
  nothing. Both opening docstrings name the seven slice modules and the four new ones, and their
  participants (`application/tracker.py`, `web/pages.py`, `web/routes.py`, `web/style.css`) match the
  diff.

Beyond the card's command, all of these were run from the product root and exited 0:

- `pytest tests/e2e/`: 117 passed on Playwright 1.63.0, in a venv built from `tests/requirements.txt`
  in `/tmp`, outside the tree.
- `ruff format --check .` and `ruff check .`, both at ruff 0.16.10.
- `mypy main.py errors.py domain application persistence web`: 27 files, no issues.
- `python3 -m compileall -q` over the product's code and tests.
- `python3 tests/timed_run.py`: the project-deletion POST took 6.8 ms and its landing 0.1 ms.

## Test evidence

- The card's command, `pytest products/tracker17/tests/`, ran once, through `gate_suite.py run --gate code-integrity`.
  It exited 0 with 2556 passed: the developer's 2555 plus the one case above. The verdict rests on this run.

## Calls made

- **Question:** what should Projects show when `deleted_project_tasks` is a well-formed decimal too
  long to read as an int? **Readings:** (a) show it as the count, since it is a canonical nonnegative
  decimal; (b) treat it as no completion. **Taken:** (b). CP-576's `{count}` is "the number of tasks
  the deletion removed", and no deletion removes that many. `change_design.md` § 3 C and Architect
  Review Note 4 ignore a pair that is malformed. Reading (a) cannot be built without raising
  Python's digit limit. **Owner:** the Architect (`change_design.md` § 3 C). **If reversed:** the
  decoder must render the digits as given, and this case's expected page changes from the ordinary
  one to the completion.

## Placement

The SDD § 3 parts table was read. Each piece of logic below is already in the part that owns it, and
nothing was moved:

- **domain:** the cascade, the removed count, the missing-project refusal and
  `ProjectDeletionOutcome` are in `domain/projects.py`.
- **application:** `Tracker.delete_project` applies the rule, then saves, then publishes. It holds no
  rule of its own.
- **web:**
  - In `routes.py`: the two routes, the deletion-mode resolution, the decoder for the completion
    pair, the response status and cache policy, and the guarded failure report.
  - In `pages.py`: the wording, the strip, the focus handling and `ProjectDeletion`.
  - In `style.css`: the full-size strip.
  - The confirmation's count is the application's `listing.task_count`. `project_page` falls back
    to `len(rows)` only when it is called without a listing. The live route always passes one, so
    `web` decides no count.
- **Test harness:** the oracle and the timing are in `tests/timed_run.py`, as the design places them.

## Language resolution

- **Language:** Python, from `project.md` `Languages:`, step 1 of the chain.
- **Read:** `languages/python/README.md`, then:
  - `conventions.md`: Surface style; Comments and docstrings.
  - `quality_gates.md`: the two gates; What is not installed.
  - `testing_python.md`: Layers 1–5 and their rules; Layer 6.
- **The added line:** within 100 columns, ruff-clean, an f-string, and its comment says why rather
  than what.
- **Compile and Suite gates:** both run, both exit 0.
- **Ruff and mypy:** the product's own decision (`docs/nfdr.md` QC-62), run at the pinned versions.
