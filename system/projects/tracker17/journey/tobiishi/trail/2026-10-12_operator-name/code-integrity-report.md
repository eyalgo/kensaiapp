# Code integrity report — tracker17 · tobiishi · 2026-10-12_operator-name

Integrity: pass

**Date:** 2026-10-12
**Reviewed at:** `9036cc6ed` (the closing marker `developer: 2026-10-12_operator-name — implementation complete`)
**Mode:** workflow · product inside the instance, so `code_worktree` = `pipeline_worktree` = the change worktree (`core/tools/development_path.py resolve`, `"kind": "relative"`)

## Deferrals

None. The closing marker carries no `Deferred:` line and reads `Suite: green`.

## What was reviewed

The code commits `351496249`..`ed45e02c8` under `products/tracker17/`: `domain/operator_name.py`
(new), `domain/state.py`, `domain/__init__.py`, `application/tracker.py`,
`application/__init__.py`, `persistence/saved_data.py`, `web/pages.py`, `web/routes.py`,
`tests/timed_run.py`, and the eleven test files the instruction's layout names.

## The intent it was checked against

`tl_instruction.md` (Tasks 1–5, their Behaviours to verify, Held by review and TL Review Notes),
`change_spec.md` (CP-211–CP-239), `change_design.md` §§ 3–5 and `change_text.md` for every published
string. `docs/fdr.md` was not needed for any call.

## Placement

Walked against `products/tracker17/docs/SDD.md` § 3 (the parts table). Nothing moved, so there is no
`— placement` commit.

| Logic | Owning part | Where it is |
|---|---|---|
| Blank and too-long rule, exact comparison, `OperatorNameOutcome`, `set_operator_name` | `domain` | `domain/operator_name.py`: already there |
| The state field, and the rule applied on restore | `domain` | `domain/state.py`: already there |
| Reading the name; save before publishing, only on a changed outcome | `application` | `application/tracker.py`: already there, with no blank, length or comparison rule of its own |
| Six-key format, the three old exact shapes, the text-or-null type check | `persistence` | `persistence/saved_data.py`: already there; the rule itself goes to `restore_state` |
| Form decoding, line-feed normalization, refusal type → address code, guarded failure, outcome reconstruction | `web` | `web/routes.py`: already there |
| Section markup, outcome precedence, focus and description, typed-text fallback | `web` | `web/pages.py`: already there, with no rule (it maps an outcome to markup) |
| Name measurement and its verdict | the harness (no product part) | `tests/timed_run.py`: already there |

## Tests added or fixed

None were added, and none were corrected against the intent. Every `#### Behaviours to verify` name
in `tl_instruction.md` exists exactly once in the suite: all 63 were grepped, and none were missing
or duplicated.

**Discrimination, established here.** The developer left this item open for the task 4 precedence
rules. Each rule below was broken once in a disposable copy (`git archive HEAD`), and the named
test files were run against the broken copy. 35 mutations were killed and one survived, and the
survivor is equivalent:

- **Page and address** (`test_people_pages.py`, `test_people_routes.py`, `test_routes.py`):
  - refusal → failure → completion order: failure first, and completion before failure;
  - the operator outcome suppresses the assignee outcome;
  - typed text kept for too-long, dropped for failure, or kept on a plain page;
  - empty typed read as absent, and absent read as empty;
  - each redirect's typed or completion payload dropped or added, and a no-change redirect carrying completion;
  - the no-name line always shown;
  - failure focus on the field, and completion described on Save;
  - each of the three `_escape` calls removed, and the failure line naming the saved name;
  - an unknown `operator_failed` code accepted;
  - no line-feed normalization;
  - the console line without the name;
  - the section placed after Assignees;
  - `maxlength` off by one;
  - the note, the no-name, the blank and the too-long strings altered;
  - a forged empty `operator_saved` shown as a completion.

  All were killed.
- **Domain**: blank checked before length, comparison after stripping or case-folding, restore skipping the rule, and no-change returning a new state. All were killed.
- **Application**: saving on every outcome. Killed.
- **Persistence**: a non-text name accepted, null omitted on write, a partial old shape with a name accepted, the old five-key form refused, and the name not passed to restore. All were killed.
- **Survived, equivalent**: dropping `name = ""` from the operator-outcome suppression in `people_page`. With refusal and failure already cleared, `kept` is `""` either way (`web/pages.py`, `kept = name if reason is not None or outcome is _Outcome.FAILED_ADD else ""`), so no behaviour exists to test.

**Test files touched, with no assertion changed.** These edits ride with the convention fixes below:

- `tests/integration/test_timed_run.py` — the six `measure_operator_name` calls now name their arguments (`site=`, `saved_data=`, `timer=`), because the harness signature became keyword-only.
- The docstrings of the test files listed under *Language resolution* were re-wrapped.
- `test_people_routes.py` — one address string literal was split in two. Its bytes are unchanged.

## The finding

**No bug.** Every behaviour of the intent has a test that fails when the behaviour is broken, and the
suite is green. Three divergences from the Python packet were fixed in the code, with no change in
behaviour:

1. `OperatorNameRefusal(Enum)` → `OperatorNameRefusal(str, Enum)` (`web/pages.py`). Its value is written into an address (`web/routes.py`, `operator_refused=...value`) and read back (`_closed(pages.OperatorNameRefusal, ...)`). For that case the packet's house form is `(str, Enum)` (`conventions.md:82-86`). The developer's marker left this for this review.
2. `measure_operator_name(site, saved_data, timer=time.perf_counter)` → `measure_operator_name(*, site, saved_data, timer)` (`tests/timed_run.py`). The defaulted real clock is a collaborator default, which the packet forbids, and three collaborators go keyword-only (`conventions.md:116-128`). `main` passes its own `timer` by name.
3. 23 lines the change added ran past 100 columns (`conventions.md:17`). They were re-wrapped, and 0 now do.
   - Two one-line docstring summaries were shortened to fit: `application/tracker.py` `set_operator_name` and `domain/operator_name.py` `OperatorNameOutcome`. No contract changed.
   - The People note string in `web/pages.py` was split across two literals, and its rendered text is unchanged. `test_people_pages.py` reads the exact sentence, and the M24 mutation of it was killed.

No misplacement was found and none was moved.

**Gates at the commit, run in the change worktree with the product's `.venv`:**

- `pytest products/tracker17/tests/`: 937 passed.
- `pytest products/tracker17/tests/e2e/`: 29 passed.
- `python3 tests/timed_run.py`: exit 0, with `set your name at 1000 tasks: 28.4 ms` and `name landing page at 1000 tasks: 0.1 ms`. Every existing row passed.
- `ruff format --check .` (171 files) and `ruff check .`: clean.
- `mypy main.py errors.py domain application persistence web`: no issues found in 22 source files.
- `compileall`: exit 0.

The intermittent `test_start.py::test_a_start_on_another_port_names_that_port` failure the developer
saw once did not recur in either of the two full runs here.

## Calls made

1. **Non-behavioural code fixes ride in the clean-pass commit.** The commit table has no row for a packet fix on a clean pass. The readings weighed were: leave the divergences as notes, open an extra commit, or carry them in the one commit. I took the one commit, because the skill says the packet wins and the code changes, and the table allows one commit on a clean pass. Whose to confirm: the owner of `development-code-integrity`. If ruled the other way, the three fixes split into their own commit, and nothing else changes.
2. **`(str, Enum)` only for the new vocabulary.** `AssigneeRefusal`, `TaskRefusal`, `TaskEditRefusal`, `FailedAction` and `LabelRefusal` (`web/pages.py`) are older address vocabularies with the same shape and stay bare `Enum`. They are not this change's code. The divergence from the file is recorded here. Whose to confirm: the Tech Lead. If ruled the other way, the siblings change in a change of their own.
3. **Keyword-only and no default only for the new measurement.** `measure_task_volume`, `measure_task_edit`, `measure_label_add` and `measure_label_remove` keep `timer=time.perf_counter`, and `main` keeps its defaults as the entry point. Same owner and same consequence as call 2.
4. **`__version__` is not applied to `domain/operator_name.py`.** It is a member of the `domain` package, and "a package carries the marker once, in its `__init__.py`" (`conventions.md:150-153`). No product package carries one today (`grep -rl __version__` over the product's `.py` files returned nothing), so adding the first is a product-wide decision, not this change's. This corrects the marker's "divergence for domain/operator_name.py". Whose to confirm: the Tech Lead. If ruled the other way, each of the five packages gains one line.
5. **`from __future__ import annotations` after the module docstring is not a divergence.** The marker records it as one (`conventions.md:46`). But Python allows only the module docstring, comments, blank lines and other future statements before a future statement (https://docs.python.org/3/reference/simple_stmts.html#future), so this is the earliest legal position. Whose to confirm: the packet's owner, in case its wording should say "first import". Nothing changes in this change either way.

## Language resolution

- **Language:** Python, declared at `system/projects/tracker17/project.md:L12` (`Languages: Python`). Step 1 of `core/doctrine/engineering/languages/README.md` § The resolution chain answered.
- **Packet:** `core/doctrine/engineering/languages/python/README.md` (1.2.1) was opened, along with these concern files:
  - `conventions.md` (1.3.0): lines ≤ 100, `(str, Enum)` for written values, collaborators handed in keyword-only with no default, the package `__version__` clause, `from __future__`;
  - `quality_gates.md` (1.0.2): ruff with `line-length` 100 and mypy for a product, both run;
  - `layout.md` § Two trees: it adds nothing to a managed product's test tree, so its test-name rule does not bind here;
  - `core/doctrine/engineering/testing_python.md` (2.2.0): hand-written fakes, never `monkeypatch.setattr`. The added test lines hold no `monkeypatch`, `mock.` or `patch(` (grep, 0 hits).
- **Not reopened:** `toolchain.md` and `errors_logging.md`. Nothing in the diff adds a dependency or a new catch site: the one catch is `Site._guarded`, which already existed.
- **Docstrings re-wrapped** to the ≤ 100 line: `tests/e2e/test_people.py`, `test_operator_name_tracker.py`, `test_people_pages.py`, `test_people_routes.py`, `test_saved_data.py`, `test_start.py`, `test_timed_run.py`, `tests/timed_run.py`, `test_operator_name.py` and `test_state.py`.
