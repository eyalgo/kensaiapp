# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `2026-11-13_saver-fake-and-suite` (tracker17) · **Mode:** workflow · **Reviewed at:** `<a commit not in the public history>`, the
newest `implementation complete` marker, with the changelog report `0c2d51cf6` on top.

## The finding

The code does what its intent says, and no code changed. Two of the fake's layer-1 checks were wrong
tests and are rewritten, and one check the plan held by review is added. All three are green on the
fake as the developer wrote it.

1. **Two layer-1 checks waited on the real clock.**
   `test_the_held_call_keeps_its_state_and_waits_for_release` and
   `test_calls_other_than_the_held_one_are_not_held` started a real thread and waited on it, with
   `thread.join(timeout=0.3)` and `entered.wait(timeout=10)`. The plan files them at layer 1, and
   `testing_doctrine.md` § *A unit test hands its unit fakes and touches nothing real* says a unit test
   "neither reads the real clock nor waits on it". Both now hand the fake a recorded release in place
   of its `release` event. The recorded release keeps the bound of each wait, whether `entered` was
   set and what `saved` held at that moment, and answers as an event that was or was not set. Neither
   check starts a thread or waits.
2. **One of those checks could not see the fault it names.** The old
   `test_calls_other_than_the_held_one_are_not_held` made its third save after `release` was already
   set. A fake that held every call from the held one on therefore passed it. With `==` changed to
   `<=` in the fake's hold test, the original suite printed `33 passed`. The rewritten check records
   every wait, and the same mutation fails it.
3. **Added: `test_a_held_call_not_released_in_time_fails`.** `change_design.md` § 3 says the held
   call "fails with `AssertionError` if `release` was not set in that time". The plan held that line by
   review only because a real test would cost the full 10 seconds. A recorded release that answers
   "not set" proves it with no wait. The first rewritten check now also asserts the bound, `10`.
4. **The moved tests keep their assertions (I-1).** An AST comparison of every changed module against
   the merge base `61a5b1ecc` found no test missing or added outside the suite file and no change to
   any decorator. It found 105 tests whose assertion text changed. 96 changed only the record they
   read from: `saves` → `len(saved)`, `*_during_save` → `seen`, `other_access` /
   `other_attributes_asked_for` → `asked_for`, `states` → `saved`. Three kept their number of
   assertions in a new form. Two are `RecordingEverything` swaps (finding 5). The third is
   `test_delete_task_saves_once_before_publishing`, whose two reads per save are now one pair in
   `seen`, as § 3 maps `_ReadingSaver`. Six lost one assertion, and each
   loss is one of the moves `change_design.md` § 5 *What the change stops proving* names:
   - The `assert release.wait(timeout=10)` inside the five `HeldSaver`s. These are in
     `test_comment_requests_serialize_through_the_save`,
     `test_label_routes_keep_request_and_response_policy`, `test_a_saver_held_open_makes_a_second_submission_wait`,
     `test_assignee_and_project_requests_serialize_through_the_save` and `test_task_edits_wait_for_held_save`.
     The fake's held call now carries that assertion, and items 1 and 3 prove it.
   - The `all(len(arguments) == 1 …)` check in `test_operator_name_route_hands_recording_saver_only_saves`.
     The `TrackerState` check moved onto `saved`.
5. **The swaps are faithful.** `SwitchedSaver` and `CountingSaver` counted a save only once the inner
   `SavedData` had kept it. So `len(saved)`, which grows only after `passes_to` returns, is the same
   count. A swapped `RecordingEverything`'s `calls == []` reads `len(saved) == saves and asked_for ==
   []`, with no `error` set. The two `holding`-switch sites set `hold_save` to `calls + 1` where the
   switch was thrown.
6. **No misplacement.** See *Placement*.

## Deferrals

None. The marker `<a commit not in the public history>` carries no `Deferred:` line.

## What was reviewed

- `products/tracker17/tests/fakes.py`, which is new: `FakeSaver`.
- `products/tracker17/tests/integration/test_saver_contract.py`, which is new: the fake-only checks,
  `SaverContract` and its two `Test…` subclasses.
- The 33 modified modules under `products/tracker17/tests/integration/`. These are the plan's 20,
  plus 13 that read `SwitchedSaver`, `world.saver.saves` or `RecordingSaver` and that the developer's
  notes name.
- Nothing outside `tests/` changed. `git diff --stat 61a5b1ecc..HEAD -- . ':!tests'`, run from the
  product root, printed nothing (I-2).

## The intent it was checked against

`tl_instruction.md` (Tasks 1–24, the Behaviours to verify, and Task 24's gates), `change_spec.md`
(I-1 to I-11, Locked Answers) and `change_design.md` (§ 3 the fake's surface and the stand-in map, § 5
the test continuity). `docs/fdr.md` was read for context and holds no line on test code.

## Tests added or fixed

All are in `products/tracker17/tests/integration/test_saver_contract.py`, and all are layer 1:

| Test | What changed | Why |
|---|---|---|
| `test_the_held_call_keeps_its_state_and_waits_for_release` | Fixed. It now uses a recorded release in place of a thread and a timed join, and asserts one wait with bound 10, `entered` set and the state kept | Finding 1 |
| `test_calls_other_than_the_held_one_are_not_held` | Fixed. Three saves on one thread, and exactly one wait, at call 2 | Findings 1 and 2 |
| `test_a_held_call_not_released_in_time_fails` | Added | Finding 3 |
| `RecordedRelease` (helper) | Added | It stands in for an event, not a saver. It defines no `save` and bases on nothing in `tests/fakes.py`, so I-7 and I-8 still hold |

## Placement

`docs/SDD.md` § 3 names five parts: `domain`, `application`, `persistence`, `web` and `main`. None of
them owns test code. Two pieces of new logic were walked:

- **`FakeSaver`**: no owning part (test code). Nothing was moved.
- **`SaverContract` and its two subclasses, and the fake-only checks**: no owning part (test code).
  Nothing was moved.

There is no placement commit.

## Calls made

1. **How a layer-1 check proves "does not return until `release` is set".** The two readings were
   (a) watching a real thread stay blocked for a while, and (b) proving that the held call waits on
   `release`, with the bound, and returns only on its answer. I took (b), because (a) waits on the
   real clock, which a layer-1 test may not. The layer-2 contract case still runs a real held save on
   a thread. This belongs to the **Tech Lead** (`tl_instruction.md` Task 1) and the **Architect**
   (`change_design.md` § 5, "The fake-only checks touch no real resource"). If they rule for (a), the
   two checks move to layer 2 and keep their thread.
2. **The 10-second bound is tested, not held by review.** The plan held it by review only for cost,
   and a clock-free test costs nothing. This belongs to the **Tech Lead**. If they rule the other way,
   `test_a_held_call_not_released_in_time_fails` goes, and so does the bound's value in the first
   check.
3. **`only_save` stays silent on the fake's own attribute names** (`saved`, `calls`, `seen`,
   `error`, `release` and the rest). A `RecordingEverything` refused every name but `save`, so this is
   narrower. I left it as is. Production reaches the saver only through `save`: `grep -rnE 'saver\.'`
   over `application/`, `web/` and `main.py` finds nothing else. Making the fake refuse its own names
   would change the surface `change_design.md` § 3 fixes. This belongs to the **Architect**. If they
   rule the other way, the fake needs a different refusal mechanism, and its own check goes in the
   suite.
4. **The fake's two `threading.Event`s are records, not collaborators it builds.**
   `change_design.md` § 3 lists `entered` and `release` among the fake's records. Both can be set
   after construction, which is how items 1 and 3 hand one in. I did not treat them as a breach of
   `arch_defaults.md` § *Dependency Graph Rules*. This belongs to the **Architect**.

## Language resolution

- Python, declared in `project.md` `Languages:`, which is step 1 of the chain.
- The packet is `<CORE>/doctrine/engineering/languages/python/README.md`. I read all seven concern
  files it routes: `toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`,
  `errors_logging.md`, `environment.md` and `testing_python.md`.
- I read `arch_defaults.md` (with `arch_defaults_python.md`) and `testing_doctrine.md` beside them.
- **Held:**
  - `testing_python.md` § Rules: the fake is in `tests/fakes.py`, and the suite is a plain base with
    two `Test…` subclasses filed at layer 2.
  - `conventions.md` § Constructs: `FakeSaver` has no base, and `passes_to` defaults to `None`, never
    a real saver.
  - `quality_gates.md`: Ruff exits 0 over the whole product.
- **Repaired:** `testing_doctrine.md` § *A unit test hands its unit fakes and touches nothing real*
  (finding 1).

## Test evidence

- The full card command, run through the gate tool with `--gate code-integrity`, exited 0. The
  first half printed `3370 passed, 2 skipped`. That is the developer's 3369 plus the added check, and
  `test_timed_run_exercises_and_reports_task_volume` passed. The browser half printed `122 passed`.
- The contract file alone printed `34 passed`.
- Mutations of `tests/fakes.py`. Each was restored from HEAD, and `git diff --quiet HEAD --` exited 0
  after each:
  - Hold every call from the held one on: `1 failed, 33 passed`
    (`test_calls_other_than_the_held_one_are_not_held`). Against the original checks it printed
    `33 passed`.
  - Bound 10 → 5: `2 failed, 32 passed`.
  - I-5, drop the state (the `saved.append` line removed): `16 failed, 18 passed`. The fake's
    contract run failed 8 of its 9 cases, every case but `test_nothing_is_kept_before_the_first_save`.
    The `SavedData` run passed all 9. This agrees with the developer's recorded run.
- Whole-change gates, from the product root:
  - I-7: `tests/fakes.py` alone, `1`.
  - I-8: no class bases on `FakeSaver`.
  - I-10: `25` lines in `24` files.
  - I-9: `10` matching lines over the product at both the merge base and HEAD.
  - I-11: `ruff format --check .` printed "370 files already formatted", and `ruff check .` printed
    "All checks passed!".
