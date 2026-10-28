# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-28_delete-a-task`, reviewed 2026-10-28 by the Senior
Engineer in workflow mode. No bug was found in the code. Three tests did not prove what the plan
asks of them, and one test broke the Python packet's testing rule. All four were corrected, and the
suite is green.

## Deferrals

None. The closing marker, `<a commit not in the public history>` (`developer: 2026-10-28_delete-a-task — implementation
complete`), carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

The branch's code commits against `main`, under `products/tracker17/`:

- `domain/tasks.py`, `domain/__init__.py`: `delete_task` and its export.
- `application/tracker.py`: `Tracker.delete_task`.
- `web/pages.py`, `web/routes.py`, `web/style.css`: the Delete task area, the two POST routes, the
  address states, the project page's completion line and the response policy.
- `tests/timed_run.py`: the timed deletion block.
- The tests the change added or changed: `tests/unit/test_tasks.py`,
  `tests/integration/test_task_tracker.py`, `test_saved_data.py`, `test_delete_pages.py`,
  `test_delete_routes.py`, `test_task_pages.py`, `test_comment_pages.py`, `test_routes.py`,
  `test_timed_run.py`, and `tests/e2e/test_delete_task.py`.

## The intent it was checked against

- `tl_instruction.md`: Tasks 1 to 4, each task's *Behaviours to verify*, and the Task 3 and Task 4
  *Held by review* lists.
- `change_spec.md`: rules CP-529 to CP-545, the Examples, and Locked Answers Gaps 1 to 12.
- `change_design.md` §§ 2 to 5, and `change_text.md` for every string.
- `products/tracker17/docs/fdr.md` exists. The spec already cites the rules it needs (R-44, R-50,
  R-103, R-105 to R-107, R-112), and nothing more from it was needed.

Every behaviour the instruction lists has a test with the name it gives. The plan asks for 24 tests
across Tasks 1 to 4, and all 24 are present. Each was read against its rule.

## Tests added or fixed

1. **Fixed: the stale-tab refusal tests sent two payloads that a live task also refuses.**
   (`tests/integration/test_delete_routes.py`, the fixture `stale_world`, CP-540 and CP-541, T10)
   The plan says each refusal case uses "a complete request whose payload would otherwise be valid".
   A probe sent each payload for the held task, before any deletion:
   - label remove `ui` answered `label_refused=not-carried`, because the task carried no `ui` label;
   - comment add answered `comment_refused=no-name`, because no operator name was saved.

   Those two tests passed whether the refusal came from the deleted target or from the payload. The
   fixture now saves an operator name and gives task 1 the label `ui` before the deletion, through
   a new `held_world`. The label-add case now sends `bug`, because `ui` is already carried and
   adding it would change nothing.
2. **Added: `test_each_refused_payload_is_accepted_for_a_held_task`** (same file, 11 cases). This
   makes the plan's "otherwise valid" clause a check rather than an assumption. Each payload the
   refusal tests send is sent for the held task in the same world. The test asserts that it is
   accepted, with no `refused=` or `failed=` in the address, and that it saves exactly as that
   action does. That is one save, or none for the two first presses, which open a confirmation.
   Moves from `done` and `cancelled` are left out: the workflow allows no move from either status.
3. **Fixed: the deletion-precedence test had one case that tested nothing.**
   (`tests/integration/test_delete_pages.py`, `NOISE`, T12) The entry `label_refused=blank` is not
   an address the tracker produces. The real refusal code is `empty`, and the redirect is
   `label_refused=empty&label=`. Sent alone, the old entry showed no outcome, so it proved nothing
   about suppression. The entry is now the real address. The list of outcome lines that must be
   absent under an active deletion state, `OTHER_OUTCOME_IDS`, now names all eleven move, edit,
   label and comment lines. Before, it named five. This matches design T12: an active deletion
   "suppresses move/comment/label/edit outcomes".
4. **Added: `test_the_noise_shows_its_own_outcome_without_a_deletion_state`** (same file, 12
   cases). This is the control for item 3. Each noise address, sent without a deletion marker,
   shows an outcome, a strip or a focus of its own. Its absence beside the marker is therefore
   caused by the deletion state. The two `move_task=999` entries are left out: they stand for a move
   reference to a missing task, not an outcome.
5. **Replaced: `test_whole_run_exit_status_includes_the_deletion`.** (`tests/integration/
   test_timed_run.py`, CP-543, T15) It used `monkeypatch.setattr(harness, "measure_task_delete",
   …)`. `testing_python.md:31` forbids that: "The seam is a hand-written fake passed to the
   constructor — not `monkeypatch.setattr` on the module under test". The developer recorded the
   divergence and gave the sibling tests' habit as the reason. The packet outranks the file's habit.
   The replacement, `test_a_failed_deletion_fails_the_verdict_the_whole_run_returns`, keeps the same
   two cases, refused and wrong landing. It drives them through the fake site handed to
   `measure_task_delete` and asserts that `verdict` returns 1 and prints the deletion's rows as
   ` — refused or failed`. That `main` returns the deletion's verdict is already proven through the
   timer seam, by `test_delete_time_limits_are_strict` (`_run_readings(delete=…)`, status 1 on the
   deletion's rows alone). The sibling Summary and Apply tests still patch the module. They are not
   this change's code, so they are left as they are.

## The finding

**No bug in the code. Four test defects were corrected and two controls were added.** Every
production behaviour of CP-529 to CP-545 was already correct:

- the rule removes only the target, keeps both counters and refuses a missing identity;
- the action saves once before it publishes the deletion and reads no clock;
- the first press saves nothing;
- the confirming press lands on the owning project with the title held when the deletion ran;
- a failed save leaves the bytes as they were and prints the two terminal lines;
- every stale submission is refused as missing, with the bytes unchanged;
- the deleted address is 404 with no `no-store` under every query;
- the four live deletion views are 200 with `no-store`;
- the timed run accepts only the exact saved state and the completion line.

**Nothing was misplaced** (§ Placement).

Checked by reading as well as by tests:

- `confirm_strip` is reused and keeps its public contract (`web/pages.py`, `_delete_strip`).
- The one `_guarded` site catches the failure, and the terminal line comes from `change_text.md`.
- Every displayed title passes through `_escape`, or through the strip's own escaping.
- `_address` (`urlencode`) builds the success address, and `parse_qs` reads it back. The
  `a%2Fb+c` case shows that a title round-trips.
- The confirming target comes from the route alone. `test_confirmation_uses_the_title_current_at_each_request`
  shows that a forged title, project or identity in the body changes nothing.

## Calls made

1. **What "otherwise valid" requires of a refusal fixture** (T10). There were two readings. One:
   any well-formed request will do, because the bare `/tasks/1` redirect already tells a missing
   target apart from a payload refusal. Two: the payload must be one the held task would accept.
   I took the second. The plan's words are "a complete request whose payload would otherwise be
   valid", and only that reading makes each test show that the deletion, and nothing else, caused
   the refusal. This call belongs to the Tech Lead (`tl_instruction.md` Task 3). If the Tech Lead
   rules the other way, `held_world`'s label and operator name and the control test can go, and
   the refusal tests still pass.
2. **Replacing a monkeypatched test with one that uses a seam** (T15). The packet binds over the
   file's habit (`development-code-integrity`, *Language packets*), and the behaviour was already
   provable without the patch. I took the smaller fix: an assertion on `verdict` through the fake
   site. I did not add a seam to `main`, which would have changed the harness's interface. This call
   belongs to the Tech Lead, who owns the plan's test shape. If the Tech Lead prefers a whole-run
   test, the way to get one without a patch is a parameter on `main` that injects the deletion
   measurement. That is a harness interface change for a later plan.

## Placement

The parts table is `products/tracker17/docs/SDD.md` § 3, *The parts*.

- `delete_task` (`domain/tasks.py`): the rule. Its owning part is **domain**, and it was already
  there. It has no I/O, no wording and no import of another part.
- `Tracker.delete_task` (`application/tracker.py`): applies the domain rule, then saves and
  publishes. Its owning part is **application**, and it was already there. It holds no rule of its
  own.
- `DeleteMode`, `DeleteArea`, `_delete_section`, `_delete_strip` and the deletion strings
  (`web/pages.py`), plus `_delete_task`, `_delete_area`, the routes and `_stored_as_asked`
  (`web/routes.py`): addresses, form reading, one action call per request and page building.
  Their owning part is **web**, and they were already there. The existence check in `_delete_task`
  reads `Tracker.task`, the same lookup every other task route makes. It is not a rule.
- `measure_task_delete`, `_expected_after_deletion`, `_delete_landing_shows`,
  `delete_fixture_report` and `_run_delete` (`tests/timed_run.py`): the timed harness, which SDD
  § 4 TS-5 assigns to `tests/timed_run.py`. They are in no product part. The oracle drops one task
  itself and calls no production rule.

No move was needed, so there is no placement commit.

## Language resolution

- **Language:** Python. Step 1 of the chain answered it, from `project.md` `Languages: Python`.
- **Packet:** `<CORE>/doctrine/engineering/languages/python/README.md` was opened. Its concern
  files were read for this review:
  - `quality_gates.md:14` (compile) and `:66` (Ruff): `compileall -q` on `main.py errors.py domain
    application persistence web tests` exited 0. `ruff format --check .` reported 250 files already
    formatted. `ruff check tests/` passed.
  - `quality_gates.md:76` (mypy): `mypy main.py errors.py domain application persistence web`
    reported no issues in 27 source files.
  - `conventions.md:17` (100 columns) and `:92` (a module is given its collaborators): the changed
    tests meet both. Ruff is clean, and the new tests take the world and fakes they use as
    arguments.
  - `testing_python.md:31` (the seam is a hand-written fake): it governed item 5 above, where the
    packet won over the file's habit and the test changed.
- The floor, `developer_standards.md`, has nothing more to say about four test-only edits.

## Test evidence

- An earlier run of the test command exited 0 and printed `Environment: owners-mac — no CI`.
  `2273 passed in 205.27s`. That run came before item 5.
- The last run, which the verdict rests on, was `gate_suite.py run --gate code-integrity`. It exited
  0 with `2273 passed in 198.52s (0:03:18)` and an empty error file. Its count matches the earlier
  run because item 5 replaced two cases with two.
- The browser tests are outside the card's command (`tests/conftest.py` `pytest_ignore_collect`).
  `uv run --with playwright==1.63.0 python -m pytest -q tests/e2e/test_delete_task.py`, run from the
  product root, gave `7 passed in 7.42s`.
- The suite before these edits, the developer's closing run, was `2250 passed` (marker `<a commit not in the public history>`).
  The difference is 23 new cases: 11 + 12 from items 2 and 4, and items 1, 3 and 5 changed no count.
