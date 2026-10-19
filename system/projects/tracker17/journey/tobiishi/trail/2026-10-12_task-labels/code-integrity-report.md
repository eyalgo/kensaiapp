# Code integrity report — 2026-10-12_task-labels

Integrity: pass

**Reviewed at:** `85549516b` (`developer: 2026-10-12_task-labels — implementation complete`), on branch
`2026-10-12_task-labels`. Product root: `products/tracker17/`. Every path below is relative to that root.

## Deferrals

None. The newest closing marker (`85549516b`) has no `Deferred:` line.

## What was reviewed

Everything the implementation commits `c85cbf5c3`..`1d3439d1c` changed (`git diff --stat 00a14dba7..85549516b`,
25 files):

- production: `domain/labels.py` (new), `domain/tasks.py`, `domain/refusals.py`,
  `domain/__init__.py`, `application/tracker.py`, `application/__init__.py`, `web/pages.py` and
  `web/routes.py`
- the harness, `tests/timed_run.py`
- every test file the change added or modified

## The intent it was checked against

- `tl_instruction.md`: Tasks 1–5 and their *Behaviours to verify*.
- `change_spec.md`: CP-182–CP-210 and the Examples table.
- `change_design.md`: §§ 3–5, rows T1–T18, plus the Architect Review Notes.
- `change_text.md`: every string.
- The SDD's parts table, `docs/SDD.md` § 3.

`docs/fdr.md` was not needed beyond what the spec cites.

## Tests added or fixed

- **Fixed:** `tests/integration/test_timed_run.py::test_timed_label_landing_must_show_intended_result`.
  - CP-208 and T16 say a landing showing the wrong task or the wrong label must fail. In the old version, every wrong page also lacked the right title: it used `Seeded task <n>`, not the seeded title. Its remove case also said "to" instead of "from".
  - So a harness that never checked the task, or never checked the label, would still have passed the test.
  - Now each wrong page differs from the right line in exactly one value: another task's full title, or another label.
  - A new positive control first proves the harness accepts the exact right line.
- **Added:** `tests/integration/test_label_pages.py::test_every_label_outcome_line_shows_typed_text_as_text`, with four cases: added, removed, not-carried and failed-remove.
  - QC-36 requires that every typed insertion is shown as text. `change_text.md` § Text requires that a typed value is "placed exactly as it was typed".
  - The old page tests checked a hostile label and title only in the failed-add line and in the Remove name.
  - The new test sends markup, `&` and both kinds of quote through every other line that quotes a label or the title. It asserts the exact line, and that it is the focused element's description.
- **Added:** `tests/e2e/test_labels.py::test_keyboard_alone_tabs_types_adds_and_removes_a_label`, for CP-195 and its Examples row.
  - The existing keyboard tests reach each control with a scripted `focus()` and enter text with `fill()`.
  - The new test follows the spec's row exactly: Tab only to reach the field, typed keys, Enter, then Tab to Remove (with its accessible name checked) and Enter. It checks the saved data and where focus lands after each step.

Every other behaviour in Tasks 1–5 already had a test, and that test asserted the intent: I read each one against its rule. The run before any edit was green: `pytest products/tracker17/tests/` gave 809 passed.

## The finding

No bugs: all three added or fixed tests passed against the code as it stands.

No misplacement.

Language-packet fixes, which change no behaviour:

- 14 docstring lines this change wrote ran past 100 columns. That breaks `conventions.md:L17`, "Lines stay within 100 columns".
- `ruff format --check` cannot catch this, because it does not wrap docstrings.
- I reflowed them in `domain/labels.py`, `tests/timed_run.py`, `tests/unit/test_tasks.py`, `tests/integration/test_label_routes.py` and `tests/integration/test_timed_run.py`.
- The `domain/labels.py` lines break only at spaces, so every path the trace test reads is still whole. Lines that were long before this change were left as they were.

Final runs, all from the change worktree, with the pinned venv (pytest 9.1.1, ruff 0.16.10, mypy 2.4.0):

- `pytest products/tracker17/tests/`: 813 passed.
- `pytest products/tracker17/tests/e2e/`: 27 passed. The new e2e test passed in three repeat runs.
- From the product root, all exited 0: `ruff format --check .`, `ruff check .`, `mypy main.py errors.py domain application persistence web`, `python3 -m compileall -q main.py errors.py domain application persistence web tests` and `python3 tests/timed_run.py`.

## Calls made

1. **Existing tests changed beyond CP-209's four.**
   - **The question:** CP-209 names four tests and says "No other existing test is changed to fit". The developer also changed five more:
     - `tests/integration/test_task_pages.py`, two sites: one form only, and "label" in the absent words
     - the `edit_form` helper in `tests/integration/test_task_routes.py`
     - `test_the_names_web_needs_are_reexported` in `tests/integration/test_tracker.py`: the set of `TextField` values
     - the rename of `test_no_labels_module_or_excluded_feature_entry_exists`
   - **Readings weighed:** these are forbidden fits; or they are the same case as Gap 16, assertions of the state the request itself reverses.
   - **Taken: the second.** Each changed assertion was made false by a rule:
     - CP-182 puts a second form and the word "Labels" on the task page.
     - CP-201 and the design's `TextField.LABEL` add a fourth field.
     - CP-200 lands `labels.py`.
   - **Why it is not a weakening:** each edit replaces the assertion with the new state, stated just as strictly. The task page must now show exactly the edit form, then the Add form. Every other clause stays.
   - **Owner:** the Product Owner (`change_spec.md` CP-209).
   - **If reversed:** CP-209 would need to name these sites, or the old assertions would have to come back. They cannot pass while CP-182 and CP-201 hold.
2. **No `__version__` marker added.**
   - **The question:** `conventions.md:L148-L152` says "Every non-test module carries `__version__`", and "a package carries the marker once, in its `__init__.py`".
   - **Taken:** `domain/labels.py` is a member of the `domain` package, so it owes no marker of its own. The package's marker would go in `domain/__init__.py`.
   - **Why not add it:** no product module or package has one, and none did before this change. The developer's pause commits record this. Adding one would start a version scheme for the product that no record of it states.
   - **Owner:** the product's NFDR (CTO). The packet itself is core's.
   - **If reversed:** every product package gets a marker in one change of its own, not in this one.
3. **The keyboard-alone e2e test waits on each Enter with `page.expect_navigation()`.**
   - **The question:** how the test should wait. The existing helpers wait with `wait_for_load_state()` after `press("Enter")`. That returned before the navigation began, so the next check ran on the old page.
   - **This is test mechanics, not behaviour.** The product was never at fault.
   - **Owner:** none beyond this report.

## Placement

The parts table is `docs/SDD.md` § 3. Every piece of new logic was already in its owning part, so no `… — placement` commit was made:

| Logic | Owning part | Where it is |
|---|---|---|
| `check_label`, `check_saved_labels`, `add_label`, `remove_label`: validation, exact membership, order | `domain`: every rule that accepts or refuses a change | `domain/labels.py`, already there |
| `add_task_label`, `remove_task_label`, `TaskLabelOutcome`, and the saved-label check in `restore_task` | `domain` | `domain/tasks.py`, already there |
| `EmptyLabel`, `LabelNotCarried`, `RepeatedSavedLabel`, `TextField.LABEL` | `domain`: one typed refusal per condition | `domain/refusals.py`, already there |
| Save, then publish, only when `outcome.changed` | `application` | `application/tracker.py`, already there |
| Routes, mapping each refusal by type, redirect query and its parsing, console failure line | `web`: addresses, reading form fields, one action per request | `web/routes.py`, already there |
| Label area, focus target, outcome precedence, wording | `web`: building each page | `web/pages.py`, already there |
| Label timing and the saved-delta check | No product part. This is the SDD TS-5 harness (design, Architect Review Note (e)) | `tests/timed_run.py`, already there |

`web/pages.py` decides whether an added label is still on the task (`area.added in task.labels`). That only chooses whether there is an element to focus, so it is a page decision, not a label rule.

## Language resolution

- **Language:** Python, from step 1 of the chain: `project.md` `Languages: Python`.
- **Packet:** `core/doctrine/engineering/languages/python/README.md`, which routes to `toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, and to `core/doctrine/engineering/testing_python.md` for Testing. I read Conventions, Quality gates and Testing as the bar.
- **What it found:**
  - `conventions.md:L17`: the line-length fix above.
  - `conventions.md:L148`: call 2.
  - `quality_gates.md` § The two gates: compile and suite both exit 0.
  - `testing_python.md` § Rules, the seam rule: the added tests patch nothing. Each runs on the real site or the page builder, with collaborators passed in.
