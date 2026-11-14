# Tech Lead instruction — 2026-11-14_clock-fake-and-suite: one verified `Clock` fake, its contract suite, and QC-64's walk

**Category:** nfdr
**Behaviour:** preserving
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with every concern file it routes (`toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md`) and `testing_python.md`
**Product root:** `products/tracker17` — every path below is relative to it, unless a command says it runs from the change worktree's root.
**Scope:** test code only. Add `FakeClock` to `tests/fakes.py`, its contract suite and QC-64's layer-6 walk, and move every test's own `now` stand-in onto the fake. No file outside `tests/` changes.

---

## Project layout

```
products/tracker17/
  tests/
    fakes.py                                   ← modified (adds FakeClock beside FakeSaver)
    timed_run.py                               ← modified (RealClock goes; main.SystemClock is built)
    architecture/
      test_contract_fakes.py                   ← new (QC-64's layer-6 walk)
    integration/
      test_clock_contract.py                   ← new (fake-only checks, then the contract suite)
      test_timed_run.py                        ← modified (harness.RealClock() → SystemClock())
      test_routes.py                           ← modified (stand-in goes)
      test_task_routes.py                      ← modified (stand-in goes)
      test_people_routes.py, test_label_routes.py, test_comment_routes.py,
      test_task_pages.py, test_failure_report.py, test_summary_routes.py
                                               ← modified (stand-in or import only)
      test_assignee_tracker.py, test_comment_pages.py, test_comment_tracker.py,
      test_delete_project_tracker.py, test_filter_tracker.py, test_label_listener.py,
      test_label_tracker.py, test_listener.py, test_move_tracker.py,
      test_operator_name_tracker.py, test_rename_tracker.py, test_saved_data.py,
      test_sort_tracker.py, test_summary_tracker.py, test_task_tracker.py, test_tracker.py
                                               ← modified (stand-in goes)
    e2e/
      test_delete_project.py, test_filters.py, test_sorting.py, test_summary.py
                                               ← modified (stand-in goes)
```

No new directory and no `__init__.py` to create: `tests/architecture/` and `tests/integration/` exist. Every other file under `tests/`, and everything outside `tests/`, is untouched.

No parts table covers test code (`docs/SDD.md` § 3 lists the five product parts), so placement follows `change_design.md` §2: the fake goes in `tests/fakes.py`, the suite beside `test_saver_contract.py`, the walk in `tests/architecture/`.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **Two task shapes in one preserving change.** Tasks 1, 2 and 12 add test code the spec requires (I-3 to I-5, I-12) and `change_design.md` §5 lists with layers; they use the standard test-first shape, not the invariant gate. The stand-in moves (Tasks 3 to 11) are relocations under green and use the preserving shape. Reason: `Behaviour: preserving` swaps the shape of a relocation task, and there is no relocation in the new fake, suite and walk.
- **Move tasks carry `Dependencies: Task 1`, not `None`.** The preserving rule writes `None` because a relocation uses nothing new. Each move here imports `FakeClock`, which Task 1 makes, and the design names that one edge (§3, "No build sequence"). `Dependencies:` names what a task uses.
- **Atomic-landing cuts the design left to the TL.** A stand-in another module imports cannot be removed while its importer stays, and neither half leaves the suite green alone, so each pair is one task: `test_routes.py` with `test_people_routes.py` (Task 4); `test_task_routes.py` with the five modules that import `MovableClock` from it, `ReadCountingClock`'s module included (Task 5); `timed_run.py` with `test_timed_run.py`, which reads `harness.RealClock` (Task 11). The two stand-ins in `test_saved_data.py` are one task because they are one file.
- **Granularity of the moves.** The 24 modules are cut by the stand-in family `change_design.md` §3's table already groups, one task per family, not one per module. Each task is one cohesive responsibility (the same mechanical swap) and independently green.
- **Task 2 is written already-green.** Task 1 builds the fake and `SystemClock` exists, so no case of the contract suite can be made to fail first. The case that proves the suite can fail is I-5's recorded mutation, carried as a held-by-review line in Task 2.
- **Task 13 is review-verified.** I-2, I-7, I-8, I-10 and I-11 are true of the finished change against its merge base. Written into the suite, a diff-against-base check would assert a fixed commit after the seal. Each is a command checked on the branch against `git merge-base main HEAD`.
- **Behaviours added to Task 1** (implied by the fake's surface in `change_design.md` §3, absent from its §5 list): reading `instant` does not count as a read; setting `instant` keeps the instants after it queued, as §3 states; a `then` instant is checked as well as `first` (§5 names it; kept as its own case so a missed refusal points at the argument).
- **Per-task gates are narrowed; Task 13 runs the whole Test command.** Measured 2026-11-14, the suite takes 6 min 39 s. Each move task runs the modules it touches, and every module that imports a touched one, through the card's own pytest form, plus Ruff over its files. The full Test command, both halves, runs in Task 13. A narrowed gate cannot hide a break: the importer cuts above keep every importer inside its task.
- **Hints carried from `change_design.md` §4:** `tests/fakes.py`, `test_clock_contract.py`, `test_contract_fakes.py` and `tests/timed_run.py`. Nothing dropped. The `test_clock_contract.py` hint sits in Task 1, which creates the file; Task 2 adds the suite to it.
- **Gate environment:** the product has no tracked CI configuration, so the evidence below records that finding. Its gates run on the owner's Mac by `languages/README.md` § Gate environment defaults, and `docs/nfdr.md` § 8 records no environment decision.

## Corrections owed while there

- Owed outside this change's reach: `docs/nfdr.md` QC-64, *verified by* — "The entry starts unmet: at `373ecc8a8` neither the test-support module nor a contract suite exists, and 64 classes across 26 modules under `tests/`, `tests/e2e/` included, stand in for the clock or the saver" reads as the entry's current state, and it is false once this change lands: both fakes and both suites exist, no stand-in is left, and the walk runs → the entry is met; it names `tests/fakes.py`, `tests/integration/test_saver_contract.py`, `tests/integration/test_clock_contract.py` and `tests/architecture/test_contract_fakes.py` with its run over the product, and keeps the dated start as "started unmet at `373ecc8a8`", in the form QC-39 uses.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git ls-files | grep -iE '(^|/)(\\.github/|\\.gitlab-ci\\.yml|\\.circleci/|azure-pipelines\\.yml|Jenkinsfile|\\.travis\\.yml|bitbucket-pipelines\\.yml|\\.buildkite/|\\.drone\\.yml|cloudbuild\\.ya?ml|\\.woodpecker)' | wc -l  ->  0, run in the change worktree on 2026-11-14"
  },
  "decisions": {"override": null, "amd64": null},
  "candidates": [],
  "guest": null
}
```

---

### Task 1: `FakeClock` and its own checks (`tests/fakes.py`, `tests/integration/test_clock_contract.py`)

**Dependencies:** None

**What to build:** `FakeClock` in `tests/fakes.py` beside `FakeSaver` (which stays untouched; the module docstring is extended to name both fakes), and the checks of the fake on its own as module-level test functions in the new `tests/integration/test_clock_contract.py`. The suite of Task 2 goes in the same file after them. Surface, from `change_design.md` §3:

- `FakeClock(first, *then, step=None, runs_out=False)`: `first` required, `step` (a `timedelta` or `None`) and `runs_out` (a bool) keyword-only. No base class, no `save`, no instant of its own.
- `now()` counts the read in `reads`, gives the instants handed in one per read in order, then by configuration: the last one again (default), the one before plus `step` (with `step`), or fails with `AssertionError` saying the clock was read more times than it was given instants (`runs_out`).
- `instant`, a property: reading it gives the instant the next read will give; setting it makes the next read give that instant, the instants after it stay queued.
- `restart(first, *then)`: hands out these instants from now on, `reads` back to 0.
- `reads`: every read since built or last restarted.
- The constructor (`first` and each of `then`), `restart` and the `instant` setter refuse an instant that is not an aware `datetime` with a UTC offset of zero, `ValueError` naming it. The constructor refuses `step` together with `runs_out`, `ValueError`.

#### Behaviours to verify (developer adds the fake-only checks to `tests/integration/test_clock_contract.py`)

- `test_a_fixed_clock_gives_its_one_instant_on_every_read` — layer 1 Unit — fakes: none (the subject is the fake) — three reads all give the one instant
- `test_a_sequence_gives_each_instant_in_order_then_the_last_again` — layer 1 Unit — fakes: none — instants come in the order handed, and every read after the last gives the last
- `test_a_clock_that_runs_out_gives_each_instant_once_then_fails` — layer 1 Unit — fakes: none — each instant once, then a read raises `AssertionError`
- `test_a_stepping_clock_gives_each_later_read_one_step_after_the_one_before` — layer 1 Unit — fakes: none — after the last handed instant, each read is one `step` after the previous
- `test_instant_reads_the_next_instant_and_does_not_count_as_a_read` — layer 1 Unit — fakes: none — `instant` equals what the next `now()` gives, and `reads` is unchanged by reading it
- `test_setting_instant_makes_the_next_read_give_it_and_keeps_the_rest_queued` — layer 1 Unit — fakes: none — after the set, the next read gives it; the instants that followed in the queue still come after
- `test_restart_hands_out_the_new_instants_and_resets_reads_to_zero` — layer 1 Unit — fakes: none — new instants in order, `reads == 0` straight after
- `test_reads_counts_every_read` — layer 1 Unit — fakes: none — `reads` equals the number of `now()` calls
- `test_a_naive_instant_is_refused_by_the_constructor_as_first_and_in_then` — layer 1 Unit — fakes: none — `ValueError` for each place
- `test_an_instant_at_plus_two_hours_is_refused_by_the_constructor_as_first_and_in_then` — layer 1 Unit — fakes: none — `ValueError` for each place
- `test_restart_and_the_instant_setter_refuse_a_naive_instant_and_one_off_utc` — layer 1 Unit — fakes: none — `ValueError` from each of the two
- `test_step_together_with_runs_out_is_refused` — layer 1 Unit — fakes: none — `ValueError`
- `test_the_fake_has_no_base_class_and_defines_no_save` — layer 1 Unit — fakes: none — `FakeClock.__bases__ == (object,)` and it has no `save`

#### Held by review (omit when every rule of this task reaches a test)

- `FakeSaver` and the `save` contract suite are unchanged — covered by no new test; `git diff "$(git merge-base main HEAD)" -- products/tracker17/tests/integration/test_saver_contract.py` lists nothing, and `FakeSaver`'s body in `tests/fakes.py` is untouched, checked in Task 13.

#### Implement

Infer from failing tests.

# Hint: `tests/fakes.py`: hold the instants still to come as one list whose head is `instant`. A read takes the head and drops it while more than one is left. With one left, it keeps it (default), replaces it with itself plus `step`, or empties the list (`runs_out`). An empty list fails the read. `instant` is the head, and setting it replaces the head. The UTC check is one private function that the constructor, `restart` and the setter all call.

# Hint: `tests/integration/test_clock_contract.py`: this task creates the file, and Task 2 adds the contract suite to it. The module docstring must name an SRS requirement and only paths that exist, because `tests/architecture/test_trace.py` reads it (TS-6 serves NFR-10 and NFR-11, as `test_saver_contract.py`'s docstring shows), and it names both what the fake-only checks and the contract suite check.

#### Verification gate

From the change worktree's root: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_clock_contract.py products/tracker17/tests/architecture/test_trace.py`, and `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests/fakes.py products/tracker17/tests/integration/test_clock_contract.py && uv run --locked --project products/tracker17 ruff check products/tracker17/tests/fakes.py products/tracker17/tests/integration/test_clock_contract.py`.

Pass criteria: every test above passes and was red before `FakeClock` existed; `test_trace.py` passes; both Ruff commands exit 0; no new failures elsewhere.

---

### Task 2: The `now` contract suite (`tests/integration/test_clock_contract.py`)

**Dependencies:** Task 1 (the suite hands in `FakeClock` and shares the file Task 1 creates)

**What to build:** `ClockContract`, a plain base class holding the contract's cases against `Clock` alone, and its two subclasses, both filed with layer 2's tests. `ClockContract` is not `abc` and its name does not start with `Test`. It has one hook, `make(configuration)`, which raises `NotImplementedError` in the base. Every case is parametrized over six configurations, reads `now()` three times and asserts on each instant it reads.

- `TestSystemClockKeepsTheClockContract`: `make` gives `main.SystemClock()` and ignores the configuration, because the real clock has none. It reads the machine's clock and touches no file, so it takes no `tmp_path`.
- `TestFakeClockKeepsTheClockContract`: `make` gives a `FakeClock` in the named configuration.

| Configuration | The fake `make` gives |
|---|---|
| `fixed` | one instant |
| `sequence` | two instants, so the third read repeats the last |
| `runs_out` | three instants with `runs_out`, so the three reads stay within them |
| `step` | one instant with a one-minute `step` |
| `moved` | one instant, then `instant` set to another before the first read |
| `restarted` | one instant, read once, then `restart` with two others |

#### Behaviours to verify (developer adds the suite to `tests/integration/test_clock_contract.py`)

- `test_now_gives_a_datetime` — layer 2 Integration — fakes: none (the subject; the `SystemClock` run is the real clock, the other run is the fake) — each of three reads is a `datetime`, in both runs and every configuration
- `test_now_gives_an_aware_instant_at_utc` — layer 2 Integration — fakes: none — each of three reads is aware and its UTC offset is zero, in both runs and every configuration. This is I-4's minimum and I-5's target

#### Held by review (omit when every rule of this task reaches a test)

- The suite catches a fake that breaks the contract (I-5) — no test writes a naive-giving class, because that would put a second class with `now` under `tests/` (I-3, I-7). It is held by a recorded mutation: change `FakeClock.now` so it returns its instant with `replace(tzinfo=None)` and nothing else; run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_clock_contract.py`; the fake run fails `test_now_gives_an_aware_instant_at_utc` in every configuration and the `SystemClock` run passes; restore the fake. The command, both runs' counts and the restore are written into Developer Review Notes. Task 13 checks the note exists and `git diff` shows `FakeClock.now` as Task 1 left it.
- The `SystemClock` run touches no file — held by reading the diff: its subclass's `make` takes no `tmp_path`, and the case code names no path.
- The contract cases do not import the fake's own aware-and-UTC check — held by reading the diff, so I-5's mutation reaches the fake's run only.

#### Implement

Tests cannot go red.

Reason: the subjects already satisfy both cases. `main.SystemClock` landed in an earlier change unit and returns an aware UTC instant (`change_spec.md` § Verified Claims), and Task 1 built `FakeClock`, whose configurations all keep the contract, so no run of either case can be made to fail first. The mutation above is what shows the suite can fail.

# Hint: state the contract against the instant read: `isinstance(x, datetime)`, `x.utcoffset() is not None`, `x.utcoffset() == timedelta(0)`. Do not import the fake's own check, or I-5's mutation would reach both runs.

#### Verification gate

From the change worktree's root: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_clock_contract.py products/tracker17/tests/architecture/test_trace.py`, and Ruff over `products/tracker17/tests/integration/test_clock_contract.py` as in Task 1.

Pass criteria: both cases pass in both runs and every configuration (`2 cases × 6 configurations × 2 runs` selected, all passing); the recorded mutation was run and is in Developer Review Notes; `test_trace.py` passes; Ruff exits 0; no new failures elsewhere.

---

### Task 3: Move the four e2e stand-ins onto `FakeClock` (`tests/e2e/test_delete_project.py`, `test_filters.py`, `test_sorting.py`, `test_summary.py`)

**Dependencies:** Task 1

**What to move:** each module's own fixed-instant stand-in goes, and the module hands `FakeClock` the instant the stand-in held, in the place where the stand-in was built. A type annotation naming the stand-in names `FakeClock`. Every test keeps its name and its assertions.

| Stand-in (site) | → Replaced by |
|---|---|
| `SeedClock` (`tests/e2e/test_delete_project.py:46`) | `FakeClock(<that instant>)` imported from `tests.fakes` |
| `FixedClock` (`tests/e2e/test_filters.py:30`) | `FakeClock(<that instant>)` |
| `FixedClock` (`tests/e2e/test_sorting.py:31`) | `FakeClock(<that instant>)` |
| `FixedClock` (`tests/e2e/test_summary.py:62`) | `FakeClock(<that instant>)` |

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The four modules' tests pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/test_delete_project.py products/tracker17/tests/e2e/test_filters.py products/tracker17/tests/e2e/test_sorting.py products/tracker17/tests/e2e/test_summary.py`, from the change worktree's root.
- Every test that existed in these modules still exists, is not skipped, and asserts the same facts.
- `grep -En '^\s+def now\(' products/tracker17/tests/e2e/test_delete_project.py products/tracker17/tests/e2e/test_filters.py products/tracker17/tests/e2e/test_sorting.py products/tracker17/tests/e2e/test_summary.py` prints nothing.
- Public surface identical: no file outside `tests/` is edited.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan; move tests to mirror only where they reference a relocated path (production + its mirrored tests move together). **No new tests — TDD under green** (baseline green, or red on exactly the `Red at baseline:` tests → restructure → green; no red phase).

#### Verification gate

Run the pytest command above, and `uv run --locked --project products/tracker17 ruff format --check <the four files> && uv run --locked --project products/tracker17 ruff check <the four files>` from the change worktree's root. Pass: the four modules pass unchanged in name and assertion; both Ruff commands exit 0.

---

### Task 4: Move `test_routes.py`'s stand-in and its importer (`tests/integration/test_routes.py`, `tests/integration/test_people_routes.py`)

**Dependencies:** Task 1

**What to move:** `FixedClock` in `test_routes.py` goes. The module hands the tracker a `FakeClock` of the instant `FixedClock` gave, where it built the stand-in, and keeps whatever the module's own helpers expose to the modules that import from it. `test_people_routes.py` (multi-line import at line 25) stops importing `FixedClock` from `test_routes` and imports `FakeClock` from `tests.fakes` instead. Where either module built `FixedClock()` with no argument, it passes the default instant explicitly.

| Stand-in (site) | → Replaced by |
|---|---|
| `FixedClock` (`tests/integration/test_routes.py:36`, `now(self)` unannotated) | `FakeClock(<that instant>)` |
| `FixedClock` imported by `tests/integration/test_people_routes.py:25` | `FakeClock` from `tests.fakes` |

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- Both modules, and every module that names `test_routes` (`grep -rl "test_routes" products/tracker17/tests --include='*.py'` from the change worktree's root, `tests/architecture/test_trace.py` included), pass: `uv run --locked --project products/tracker17 pytest <test_routes.py> <test_people_routes.py> <the grep's modules>`.
- Every test that existed in these modules still exists, is not skipped, and asserts the same facts.
- `grep -En '^\s+def now\(' products/tracker17/tests/integration/test_routes.py products/tracker17/tests/integration/test_people_routes.py` prints nothing, and neither module imports a clock from another test module.
- Public surface identical: no file outside `tests/` is edited.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan; move tests to mirror only where they reference a relocated path (production + its mirrored tests move together). **No new tests — TDD under green** (baseline green, or red on exactly the `Red at baseline:` tests → restructure → green; no red phase).

#### Verification gate

Run the pytest command above and Ruff over the two edited files as in Task 3. Pass: every module in the run passes unchanged in name and assertion; Ruff exits 0.

---

### Task 5: Move `test_task_routes.py`'s stand-in and the five modules that use it (`tests/integration/test_task_routes.py`, `test_comment_routes.py`, `test_label_routes.py`, `test_task_pages.py`, `test_failure_report.py`, `test_summary_routes.py`)

**Dependencies:** Task 1

**What to move:** `MovableClock` in `test_task_routes.py` goes, and `World`'s clock becomes a `FakeClock`. Tests that set the clock between reads set `instant` on the fake, as before. The five modules that import `MovableClock` from `test_task_routes` (`test_comment_routes.py:24`, `test_failure_report.py:27`, `test_summary_routes.py:21`, `test_label_routes.py:19`, `test_task_pages.py:20`, the last two as multi-line imports) import `FakeClock` from `tests.fakes` instead. `ReadCountingClock(MovableClock)` (`test_comment_routes.py:48`) becomes no class at all: it is a `FakeClock(WRITTEN)`, tests read `reads` off it, and a type check that named the subclass is `isinstance(world.clock, FakeClock)`. The module defines no subclass of the fake (I-8). Where a stand-in was built with no argument, the site passes the instant its default was (`NOON`; `WRITTEN` for `ReadCountingClock`).

| Stand-in (site) | → Replaced by |
|---|---|
| `MovableClock` (`tests/integration/test_task_routes.py:58`) | `FakeClock(NOON)` or `FakeClock(<the instant handed>)`; `instant` |
| `ReadCountingClock(MovableClock)` (`tests/integration/test_comment_routes.py:48`) | `FakeClock(WRITTEN)`; `reads`; `isinstance(world.clock, FakeClock)` |
| `MovableClock` imported by `test_comment_routes.py`, `test_failure_report.py`, `test_summary_routes.py`, `test_label_routes.py`, `test_task_pages.py` | `FakeClock` from `tests.fakes` |

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The six modules, and every module that names `test_task_routes` (`grep -rl "test_task_routes" products/tracker17/tests --include='*.py'` from the change worktree's root; it holds the filter, move, sort, delete, rename and page modules that import `World` and `make_world`, which set `world.clock.instant`), pass: `uv run --locked --project products/tracker17 pytest <the six modules> <the grep's modules>`.
- Every test that existed in these modules still exists, is not skipped, and asserts the same facts.
- `grep -En '^\s+def now\(' <the six modules>` prints nothing; no module under `tests/` imports a clock from another test module; no class outside `tests/fakes.py` has `FakeClock` as a base.
- Public surface identical: no file outside `tests/` is edited.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan; move tests to mirror only where they reference a relocated path (production + its mirrored tests move together). **No new tests — TDD under green** (baseline green, or red on exactly the `Red at baseline:` tests → restructure → green; no red phase).

#### Verification gate

Run the pytest command above and Ruff over the six edited files as in Task 3. Pass: every module in the run passes unchanged in name and assertion; Ruff exits 0.

---

### Task 6: Move the fixed-instant tracker and listener stand-ins (`tests/integration/test_delete_project_tracker.py`, `test_label_listener.py`, `test_label_tracker.py`, `test_listener.py`, `test_tracker.py`, `test_move_tracker.py`)

**Dependencies:** Task 1

**What to move:** each module's own fixed-instant stand-in goes, and the module hands `FakeClock` the instant the stand-in held (the module's own constant where it has one). `test_move_tracker.py`'s `FixedClock` was built with an instant handed in, `CREATED` by default: the site passes `FakeClock(<the instant>)`.

| Stand-in (site) | → Replaced by |
|---|---|
| `FixedClock` (`tests/integration/test_delete_project_tracker.py:31`) | `FakeClock(<that instant>)` |
| `FixedClock` (`tests/integration/test_label_listener.py:27`) | `FakeClock(<that instant>)` |
| `FixedClock` (`tests/integration/test_label_tracker.py:36`) | `FakeClock(<that instant>)` |
| `FixedClock` (`tests/integration/test_listener.py:40`) | `FakeClock(<that instant>)` |
| `FixedClock` (`tests/integration/test_tracker.py:34`) | `FakeClock(<that instant>)` |
| `FixedClock` with an instant handed in (`tests/integration/test_move_tracker.py:38`) | `FakeClock(<the instant>)`, `CREATED` where none was handed |

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The six modules pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_delete_project_tracker.py products/tracker17/tests/integration/test_label_listener.py products/tracker17/tests/integration/test_label_tracker.py products/tracker17/tests/integration/test_listener.py products/tracker17/tests/integration/test_tracker.py products/tracker17/tests/integration/test_move_tracker.py`, from the change worktree's root.
- Every test that existed in these modules still exists, is not skipped, and asserts the same facts.
- `grep -En '^\s+def now\(' <the six modules>` prints nothing.
- Public surface identical: no file outside `tests/` is edited.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan; move tests to mirror only where they reference a relocated path (production + its mirrored tests move together). **No new tests — TDD under green** (baseline green, or red on exactly the `Red at baseline:` tests → restructure → green; no red phase).

#### Verification gate

Run the pytest command above and Ruff over the six edited files as in Task 3. Pass: the six modules pass unchanged in name and assertion; Ruff exits 0.

---

### Task 7: Move the read-counting stand-ins (`tests/integration/test_assignee_tracker.py`, `test_comment_pages.py`, `test_operator_name_tracker.py`, `test_rename_tracker.py`)

**Dependencies:** Task 1

**What to move:** each `CountingClock` (one fixed instant that counts its reads) goes. The module hands `FakeClock(<that instant>)` and every assertion that read the stand-in's count reads `reads` off the fake.

| Stand-in (site) | → Replaced by |
|---|---|
| `CountingClock` (`tests/integration/test_assignee_tracker.py:31`) | `FakeClock(<that instant>)`; `reads` |
| `CountingClock` (`tests/integration/test_comment_pages.py:75`) | `FakeClock(<that instant>)`; `reads` |
| `CountingClock` (`tests/integration/test_operator_name_tracker.py:35`) | `FakeClock(<that instant>)`; `reads` |
| `CountingClock` (`tests/integration/test_rename_tracker.py:44`) | `FakeClock(<that instant>)`; `reads` |

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The four modules pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_assignee_tracker.py products/tracker17/tests/integration/test_comment_pages.py products/tracker17/tests/integration/test_operator_name_tracker.py products/tracker17/tests/integration/test_rename_tracker.py`, from the change worktree's root.
- Every test that existed in these modules still exists, is not skipped, and asserts the same facts, including every read-count assertion.
- `grep -En '^\s+def now\(' <the four modules>` prints nothing.
- Public surface identical: no file outside `tests/` is edited.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan; move tests to mirror only where they reference a relocated path (production + its mirrored tests move together). **No new tests — TDD under green** (baseline green, or red on exactly the `Red at baseline:` tests → restructure → green; no red phase).

#### Verification gate

Run the pytest command above and Ruff over the four edited files as in Task 3. Pass: the four modules pass unchanged in name and assertion; Ruff exits 0.

---

### Task 8: Move the sequence stand-ins (`tests/integration/test_filter_tracker.py`, `test_task_tracker.py`, `test_sort_tracker.py`, `test_summary_tracker.py`)

**Dependencies:** Task 1

**What to move:** each `SequenceClock` (each instant given once, then the last again; counts reads) goes. The module hands `FakeClock(*instants)`. Where a site built it with none, it passes the module's default (`CREATED`, or `NOON` in `test_summary_tracker.py`) explicitly. `test_sort_tracker.py` and `test_summary_tracker.py` also used `restart`; they call the fake's `restart`. Counts read off `reads`.

| Stand-in (site) | → Replaced by |
|---|---|
| `SequenceClock` (`tests/integration/test_filter_tracker.py:41`) | `FakeClock(*instants)`; `reads` |
| `SequenceClock` (`tests/integration/test_task_tracker.py:48`) | `FakeClock(*instants)`, default `CREATED` passed explicitly; `reads` |
| `SequenceClock` with `restart` (`tests/integration/test_sort_tracker.py:42`) | `FakeClock(*instants)`, default `CREATED`; `restart`; `reads` |
| `SequenceClock` with `restart` (`tests/integration/test_summary_tracker.py:30`) | `FakeClock(*instants)`, default `NOON`; `restart`; `reads` |

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The four modules pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_filter_tracker.py products/tracker17/tests/integration/test_task_tracker.py products/tracker17/tests/integration/test_sort_tracker.py products/tracker17/tests/integration/test_summary_tracker.py`, from the change worktree's root.
- Every test that existed in these modules still exists, is not skipped, and asserts the same facts, including every read-count and restart assertion.
- `grep -En '^\s+def now\(' <the four modules>` prints nothing.
- Public surface identical: no file outside `tests/` is edited.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan; move tests to mirror only where they reference a relocated path (production + its mirrored tests move together). **No new tests — TDD under green** (baseline green, or red on exactly the `Red at baseline:` tests → restructure → green; no red phase).

#### Verification gate

Run the pytest command above and Ruff over the four edited files as in Task 3. Pass: the four modules pass unchanged in name and assertion; Ruff exits 0.

---

### Task 9: Move the one-per-read stand-in with a guard (`tests/integration/test_comment_tracker.py`)

**Dependencies:** Task 1

**What to move:** `ListClock` (each instant handed once, no repeat; counts reads) goes. The module hands `FakeClock(*instants, runs_out=True)` and reads `reads` off it. `runs_out` keeps `ListClock`'s guard: a read past the handed instants fails, and `ListClock`'s `IndexError` becomes `AssertionError`. No test of this module asserts `IndexError` (`grep -n IndexError tests/integration/test_comment_tracker.py` prints nothing at the base), so no assertion moves.

| Stand-in (site) | → Replaced by |
|---|---|
| `ListClock` (`tests/integration/test_comment_tracker.py:44`) | `FakeClock(*instants, runs_out=True)`; `reads` |

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module passes: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_comment_tracker.py`, from the change worktree's root.
- Every test that existed in this module still exists, is not skipped, and asserts the same facts. The fake is not loosened: the site uses `runs_out=True`, not the default.
- `grep -En '^\s+def now\(' products/tracker17/tests/integration/test_comment_tracker.py` prints nothing.
- Public surface identical: no file outside `tests/` is edited.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan; move tests to mirror only where they reference a relocated path (production + its mirrored tests move together). **No new tests — TDD under green** (baseline green, or red on exactly the `Red at baseline:` tests → restructure → green; no red phase).

#### Verification gate

Run the pytest command above and Ruff over the edited file as in Task 3. Pass: the module passes unchanged in name and assertion; Ruff exits 0.

---

### Task 10: Move both stand-ins in `test_saved_data.py` (`tests/integration/test_saved_data.py`)

**Dependencies:** Task 1

**What to move:** `_FixedClock` and `_SteppingClock` go. A site that read the fixed one hands `FakeClock(<that instant>)`. A site that read the stepping one hands `FakeClock(NOW, step=timedelta(minutes=1))`: `NOW`, then a minute after the one before.

| Stand-in (site) | → Replaced by |
|---|---|
| `_FixedClock` (`tests/integration/test_saved_data.py:63`) | `FakeClock(<that instant>)` |
| `_SteppingClock` (`tests/integration/test_saved_data.py:1279`) | `FakeClock(NOW, step=timedelta(minutes=1))` |

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module passes: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_saved_data.py`, from the change worktree's root.
- Every test that existed in this module still exists, is not skipped, and asserts the same facts.
- `grep -En '^\s+def now\(' products/tracker17/tests/integration/test_saved_data.py` prints nothing.
- Public surface identical: no file outside `tests/` is edited.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan; move tests to mirror only where they reference a relocated path (production + its mirrored tests move together). **No new tests — TDD under green** (baseline green, or red on exactly the `Red at baseline:` tests → restructure → green; no red phase).

#### Verification gate

Run the pytest command above and Ruff over the edited file as in Task 3. Pass: the module passes unchanged in name and assertion; Ruff exits 0.

---

### Task 11: Hand the timed run the real clock (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** None (it uses `main.SystemClock`, which exists, and not the fake)

**What to move:** `RealClock` in `tests/timed_run.py` is a copy of `SystemClock`, not a stand-in: the timed run counts the Summary against the machine's own day, and handed a fixed instant it fails (`change_spec.md` § Verified Claims). So it is not moved onto the fake. The class goes, and the two sites that built it (`tests/timed_run.py:437` and `:1815`) build `main.SystemClock()`. `tests/integration/test_timed_run.py:1064` reads `harness.RealClock()` and builds `SystemClock()` instead. After this task `tests/timed_run.py` defines no class with `now` and is handed the real clock.

| Stand-in (site) | → Replaced by |
|---|---|
| `RealClock` (`tests/timed_run.py:341`) | `main.SystemClock()` |
| `harness.RealClock()` (`tests/integration/test_timed_run.py:1064`) | `SystemClock()` |

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- `tests/integration/test_timed_run.py` passes: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_timed_run.py`, from the change worktree's root.
- The timed run exits 0, as it does at the base: `uv run --locked python tests/timed_run.py`, from the product root (`products/tracker17`).
- Every test that existed in `test_timed_run.py` still exists, is not skipped, and asserts the same facts.
- `grep -En '^\s+def now\(' products/tracker17/tests/timed_run.py products/tracker17/tests/integration/test_timed_run.py` prints nothing.
- Public surface identical: no file outside `tests/` is edited.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan; move tests to mirror only where they reference a relocated path (production + its mirrored tests move together). **No new tests — TDD under green** (baseline green, or red on exactly the `Red at baseline:` tests → restructure → green; no red phase).

# Hint: `PRODUCT_ROOT` is already on `sys.path` (`tests/timed_run.py:77`), so `from main import SystemClock` resolves. `main` starts nothing on import (its entry is under `if __name__ == "__main__":`, `main.py:202`).

#### Verification gate

Run both commands above and Ruff over the two edited files as in Task 3. Pass: the test module passes unchanged in name and assertion, the timed run exits 0, Ruff exits 0.

---

### Task 12: QC-64's layer-6 walk (`tests/architecture/test_contract_fakes.py`)

**Dependencies:** Tasks 1 and 2 (the run over the product needs the fake and the suite), Tasks 3 to 11 (it passes only once every stand-in is gone)

**What to build:** one function, given the product root and the product's source walk (the `walk_of` fixture's `SourceWalk`), that returns a list of findings; the run over the product asserts the list is empty. It reads:

- **The contract methods:** the method names, without a leading underscore, defined in each class in `application/contracts.py` whose base is `Protocol` (`save` and `now` today, read, never listed). A missing file, or one with no such method, is a finding.
- **The test modules:** every `.py` under `tests/`, `tests/e2e/` included, read as a syntax tree; `__pycache__` skipped. No module is a finding.
- **The test-support module:** `tests/fakes.py` and the classes it defines. A missing module is a finding.

It finds, each with its module and line: a class outside `tests/fakes.py` that defines a contract method; a class outside it whose base names a class `tests/fakes.py` defines, as a bare name or an attribute; a contract method no class in `tests/fakes.py` defines; a contract method with no suite run both ways. A suite run both ways is a class under `tests/` that defines at least one `test_` method and has at least two subclasses under `tests/`, one whose body names the method's fake and one whose body names a real implementation (a class in the source walk that defines the method and whose base is not `Protocol`; `SavedData` and `SystemClock` today). The module's docstring names the requirements it checks.

#### Behaviours to verify (developer adds tests to `tests/architecture/test_contract_fakes.py`)

- `test_the_product_keeps_every_contract_with_one_fake_and_a_suite_run_both_ways` — layer 6 Architecture — fakes: none — the walk's findings over the product root are `[]`
- `test_a_pinger_tree_that_keeps_the_rule_has_no_finding` — layer 6 Architecture — fakes: none (a tree built in `tmp_path`, contract `Pinger` with one method `ping`) — the baseline the failure cases below each depart from by one change
- `test_a_contracts_file_with_no_method_is_a_finding` — layer 6 Architecture — fakes: none — one finding, as the walk reads no method name
- `test_a_class_outside_the_support_module_that_defines_a_contract_method_is_a_finding` — layer 6 Architecture — fakes: none — one finding naming the module and line
- `test_a_class_outside_the_support_module_whose_base_is_the_fake_is_a_finding` — layer 6 Architecture — fakes: none — one finding, for a bare-name base and for an attribute base
- `test_a_missing_support_module_is_a_finding` — layer 6 Architecture — fakes: none — one finding
- `test_a_contract_with_no_fake_in_the_support_module_is_a_finding` — layer 6 Architecture — fakes: none — one finding naming the method
- `test_a_contract_with_a_suite_run_only_against_the_fake_is_a_finding` — layer 6 Architecture — fakes: none — one finding: the real side is missing
- `test_a_tests_directory_with_no_module_is_a_finding` — layer 6 Architecture — fakes: none — one finding, as every layer-6 walk fails on a directory that holds no module (NFDR § 9)

#### Implement

Infer from failing tests.

# Hint: no fixture line may start with whitespace then `def now(` or `def save(`. I-7 and I-10 grep every line under `tests/`, string literals included. That is why the fixture contract is `Pinger.ping`, which also shows the walk reads its method names off the contracts file. Name a class in a subclass body by any `ast.Name` id or `ast.Attribute` attr in that class's subtree. The docstring follows the same trace rule as the contract suite's: it names an SRS requirement and only paths that exist, because `tests/architecture/test_trace.py` reads it.

#### Verification gate

From the change worktree's root: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/architecture/`, and Ruff over `products/tracker17/tests/architecture/test_contract_fakes.py` as in Task 1.

Pass criteria: every test above passes and was red before the walk existed; the run over the product finds `[]`; `test_trace.py` and `test_reach.py` still pass; Ruff exits 0; no new failures elsewhere.

---

### Task 13: The shape of the finished change (no file edited)

**Dependencies:** Tasks 1 to 12 (it checks the whole)

**What to build:** nothing. This task holds the checks that are true of the finished change against its base and so never become suite tests.

#### Deliverables verified by review (no test asserts these — the gate is the diff)

- I-7, from the product root: `grep -rEn --include='*.py' '^\s+def now\(' tests` matches in `tests/fakes.py` alone, and `grep -rEln --include='*.py' '^\s+def now\(' tests | wc -l` prints `1`.
- I-10, from the product root: `grep -rEln --include='*.py' '^\s+def save\(' tests` lists `tests/fakes.py` alone; `git diff "$(git merge-base main HEAD)" -- tests/integration/test_saver_contract.py` prints nothing, and `FakeSaver`'s body in `tests/fakes.py` is as the base left it.
- I-2, from the change worktree's root: `git diff --stat "$(git merge-base main HEAD)" -- products/tracker17 ':!products/tracker17/tests'` lists nothing.
- I-8, a syntax-tree read of every import under `tests/` (multi-line imports included) finds no clock imported from a test module other than `tests.fakes`, and no class outside `tests/fakes.py` has a base that module defines. A written finding per case, with the reader's command in Developer Review Notes.
- I-9, `grep -rn "SystemClock" tests` from the product root shows `SystemClock` built or handed in, never subclassed, patched or given to `monkeypatch`.
- I-3, `tests/fakes.py` defines exactly one class with a `now` method, with no base class, and `FakeSaver` defines no `now`.
- I-5, the recorded mutation of Task 2 is in Developer Review Notes with its command, both runs' counts and the restore, and `git diff` shows `FakeClock.now` as Task 1 left it.
- I-11, from the product root: `uv run --locked python tests/timed_run.py` exits 0, and `tests/timed_run.py` defines no class with `now` and builds `main.SystemClock`.
- I-13, from the product root: `uv run --locked ruff format --check .` and `uv run --locked ruff check .` both exit 0.
- I-1, both halves of the card's `Test command:` pass, with no test skipped beyond the base's two skips and no test removed: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and then `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`, from the change worktree's root.

#### Implement

Verified by review — no test.

#### Verification gate

Run every command above. Pass criteria: every criterion above is met on reading the diff and the command output; both halves of the Test command pass, the full suite has no new failures, and the passing count is at least the base's 3383 passed (2 skipped) plus the new tests of Tasks 1, 2 and 12, and the e2e half at least 122.
