# Code integrity report — 2026-10-11_people-page-assignee-list

Integrity: pass

**Date:** 2026-10-11 · **Reviewer:** Senior Engineer (`development-code-integrity`, workflow mode)
**Reviewed at:** `1edaef66c` (the newest `implementation complete` marker), product `products/tracker17`
(in-repo: `code_worktree` = `pipeline_worktree` = this change's worktree).

## Deferrals

None. The marker `1edaef66c` carries no `Deferred:` and no `Failing:` line (`git log -1 1edaef66c
--format=%B | grep -E '^(Deferred|Failing):'` exits 1). It reads `Suite: green`.

## What was reviewed

The diff `main...1edaef66c` under `products/tracker17/`: `domain/assignees.py` (new),
`domain/state.py`, `domain/refusals.py`, `domain/__init__.py`, `application/tracker.py`,
`application/__init__.py`, `persistence/saved_data.py`, `web/pages.py`, `web/routes.py` and
`web/style.css`, plus the 13 test files the change added or changed.

## The intent it was checked against

`tl_instruction.md` (Tasks 1–5, each task's Behaviours to verify and Held by review),
`change_spec.md` § Rules CP-80 to CP-105, § Examples and § Locked Answers, and `change_design.md`
§ 3 (the interfaces and the outcome-address contract) and § 5 (T1–T18). The strings were checked
against `change_text.md`. `docs/fdr.md` was not needed beyond what the spec cites.

## Placement (Step 0)

The parts table is `products/tracker17/docs/SDD.md:L190-L196`. Every piece of new logic is already
in the part that owns it, so nothing moved and there is no placement commit.

| Logic | Owning part | Where it is |
|---|---|---|
| Name rules (length, then blank, then exact duplicate), add, remove, list; restoring the list | `domain` | `domain/assignees.py`, `domain/state.py` — already there |
| The two refusal types | `domain` | `domain/refusals.py` — already there |
| Apply the rule, save, then make it current; the list query | `application` | `application/tracker.py` — already there; no rule of its own |
| Three-key and legacy two-key shape, list-of-text type check, value rules handed to `restore_state` | `persistence` | `persistence/saved_data.py` — already there |
| Routes, form decoding, closed outcome codes, refusal-to-redirect by type, the shared failure boundary, the page and its focus targets | `web` | `web/routes.py`, `web/pages.py` — already there; no list rule decided here |

## Tests added or fixed

All were written from the intent. None is fixed, because no existing test asserted wrong behaviour.

- `tests/integration/test_people_pages.py::test_an_absent_subject_keeps_its_own_authored_line_on_the_heading`
  — design T18 and `change_text.md` § Wording decisions, "A later page whose added or failed-remove
  name has left the list shows the same line". The earlier test only asserted that the heading's
  description was non-empty. This one asserts the exact authored line.
- `…::test_a_removal_or_stale_line_sits_at_the_top_of_the_list_area` — CP-94 says "the page opens
  at the top of the area that held the list, where the completion line sits". CP-96 adds "with the
  reason in place of the completion line". No test fixed the line's place. This one asserts it sits
  under the Assignees heading and before the list or the empty text and the form, with the list
  populated, emptied and stale.
- `…::test_a_stale_remove_outranks_a_failure_and_a_success` — design § 3 D: "refusal before failure
  before success". Only the blank refusal had been tested against a failure. The stale refusal takes
  its own code path in `_outcome_line`.
- `…::test_no_people_state_offers_a_name_field_comment_or_absent_area` — CP-85 applies to the whole
  page. It had been checked only on the empty plain page, and is now checked in all nine states.
- `tests/integration/test_routes.py::test_every_route_leaves_state_and_headers_as_the_rules_say`
  is strengthened, with nothing removed. Each submission must now be accepted: there is no
  `refused=` or `failed=` in Location, and exactly one save. Design T13 asks for "meaningful setup
  for remove". The old assertion would also have passed if the remove had been refused.

Each one was checked by mutation, one at a time, with the tree restored after each:
- Changing only the absent-subject line fails the first test. The test it strengthens did not
  catch that change.
- Moving the outcome line below the list fails the second.
- Ranking a failure above the stale refusal fails the third.
- Taking the listed subject out of the route sample fails the strengthened assertion, on
  `/assignees/remove` → `refused=assignee-not-found`.

## The finding

No issues. Every behaviour in CP-80 to CP-105 already had a test that passes, and the additions
above are the gaps between those tests and the intent. No code was wrong and nothing was misplaced.
Each was run in the pinned venv built from `tests/requirements.txt`. `pip freeze` matched the
lock exactly.
- `pytest products/tracker17/tests/`: 344 passed before, 356 after.
- `pytest products/tracker17/tests/e2e/`: 18 passed.
- `python3 products/tracker17/tests/timed_run.py`, `compileall`, `ruff format --check`,
  `ruff check` and `mypy main.py errors.py domain application persistence web`: each exits 0.
- The browser assertions for CP-87 checked the computed accessible description in Chromium. They do
  not prove assistive-technology speech. `tl_instruction.md` § *Corrections owed while there* lists
  the records to correct for that gap. They are unchanged here.

## Calls made

- **Is the packet's `__version__` rule broken by the new module?** The question comes from
  `languages/python/conventions.md:L135-L141`: "Every non-test module carries `__version__`". The
  developer diverged from it, citing product practice. Under this skill, a packet's rule outranks the
  file's habit (`languages/README.md` § Precedence). There were two readings: (a) add the marker,
  or (b) accept the divergence. **Taken: (b).** That same rule says "a package carries the marker
  once, in its `__init__.py`", and `domain/assignees.py` is a member of a package. The rule also
  calls itself "`versioning.md`'s marker for a script". `versioning.md` § Out of scope says "A
  product's artifacts version by the product's rules, not the instance's", and tracker17's records
  state no such rule. Whose call: the Principal Architect's, through `docs/nfdr.md`. If ruled the
  other way, each package `__init__.py` across the product takes a marker. That is a product-wide
  change, not this one.

## Language resolution

Python, declared in `project.md` (`Languages: Python`), step one of
`<CORE>/doctrine/engineering/languages/README.md`. The packet read was `languages/python/README.md`
§ The six concerns, with its concern files `toolchain.md`, `layout.md`, `quality_gates.md`,
`conventions.md`, `errors_logging.md` and `testing_python.md`. Product records outrank the packet
(§ Precedence). The new tests use hand-written savers and no monkeypatch
(`testing_python.md:L31`), and e2e runs as its own invocation (`testing_python.md:L29`). Its one
divergence is the call above.
