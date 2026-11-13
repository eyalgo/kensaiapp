# Delegate report — the timed run's creates take the timer (2026-11-13)

## 1. Assignment

tracker17's seal halted on 4 load-flaky failures in `tests/integration/test_timed_run.py`. The job:
confirm the cause, then fix it by dependency injection. That meant giving `timed_creates` the
timer, scripting the create readings in every whole-run `Ticks`, adding a test that fails before the
fix and passes after, running the module, the card's `Test command:` and the module again under
load, and committing on branch `2026-11-13_timed-creates-takes-the-timer` without merging.
Writable: `products/tracker17/tests/`, `CHANGELOG.md`, this report. Read-only:
`products/tracker17/docs/`, every `journey/` and `trail/`, every version marker, other worktrees.
Model: Opus 5.5 (`claude-opus-5-5`), the tier the brief named.

## 2. What was searched, and what it settled

| Source | For | Settled |
|---|---|---|
| `core/roles/delegate_contract.md` | the contract | read in full |
| `grep -nE 'time\.\|perf_counter\|monotonic\|sleep\|timer' tests/timed_run.py` (at `<a commit not in the public history>`) | every clock read in the harness | the real `time.perf_counter()` was read only in `timed_creates`, at the old L359 and L361. Every `measure_*` reads its `timer` |
| `grep -rnE 'time\.\|perf_counter\|monotonic\|sleep\|datetime\.now' application domain persistence web errors.py` | real clock reads in the callees | none that time anything. The only hits are a docstring and `fromisoformat` |
| `tests/timed_run.py:L341`, `:L1390-L1392` | other wall-clock reads | `RealClock.now()` stamps the saved data, and `_local_today()` gives the Summary its date. Neither feeds a timed interval (see § 6) |
| `tests/integration/test_timed_run.py` grep for `harness.main(` | every whole-run `Ticks` | three were built by hand (old L412, L723, L988). The rest go through `_run_readings` (old L2099) |
| `core/doctrine/task_map.md:L94,L96` → `testing_doctrine.md:L70-L72`, `testing_python.md:L31-L32` | the test rules | the clock is passed in as a fake, and no test patches the module under test |
| `products/tracker17/docs/nfdr.md:L588-L594`, `:L720` | what governs the timed run | `python3 tests/timed_run.py` exits 0. Its default timer is unchanged, so it still does |
| `core/doctrine/governance/commit_format.md`, `commit_via_builder.md` | committing | read in full |
| `core/doctrine/setup/kensaiapp_structure.md:L2496-L2536` | changelog | "A commit that only adds or changes tests" earns no entry |
| `core/tools/suite_map.py:L89,L102`, `core/tools/commit_gate.py:L1-L12` | the commit gate | a commit under `products/**` runs `pytest products/`, and the gate refuses a commit that turns a test red that the parent does not also fail |
| `core/tools/commit_builder.py:L1863`, `:L1984-L1989` | the merge | the merge needs a changelog entry or `--user-invisible "<reason>"` |

## 3. Claims and their anchors

| Claim | Anchor | Brief |
|---|---|---|
| `timed_creates` read the real clock and was not given `timer` | `git show <a commit not in the public history>:products/tracker17/tests/timed_run.py`, old L354-L361 and L1808 | confirmed |
| It was the only real-clock read that times anything | the greps in § 2 | confirmed |
| `timed_creates` now takes `timer` as a required keyword argument, and `main` passes its own | `tests/timed_run.py:L354-L360`, `:L1809` | done |
| The whole-run readings start with the 51 creates' two readings each | `tests/integration/test_timed_run.py:L773-L774`, `:L415`, `:L725`, `:L998`, `:L2107-L2123` | done |
| The count is pinned to `harness.specs()` | `test_timed_run_reads_two_create_readings_per_spec`, `:L2177` | added |
| A passing run prints the scripted create times | `:L2173-L2174`, `"ordinary create 1: 100.0 ms"` | added to an existing test, which only makes it stricter |
| Red before the fix | the new tests, run against `<a commit not in the public history>`'s harness: `3 failed, 1 passed, 355 deselected`. The create case failed with `'add a task at 1000 tasks: 1000.0 ms — at or over 1 s' != 'ordinary create 1: …'` and `[] == ['create at both maximums: …']`. The scripted reading landed on the add, because the old code never read it for the create | confirmed |
| Green after: the module | `uv run --locked pytest tests/integration/test_timed_run.py -q -p no:cacheprovider -W ignore` → `359 passed in 362.60s` (356 + 3 new). `-W ignore` only hides warnings, because pyproject sets no `filterwarnings` | — |
| The card's `Test command:`, run from the worktree root | `3307 passed, 2 skipped, 6 warnings in 674.01s` then `122 passed, 6 warnings in 59.14s`, exit 0 | — |
| The module again, under load | the brief's exact command, run while the full suite above was inside `test_timed_run.py` (its log shows 56–60% in that module at the time) → `359 passed, 6 warnings in 283.04s` | — |
| The commit gate | `commit_builder: test gate — ran products on the tree that will land; no new failure.` | — |
| Lint | `ruff check`, `ruff format --check` and `mypy tests/timed_run.py` all clean | — |

## 4. Decisions

| Fork | Chosen | Rejected, and why |
|---|---|---|
| The `timer` parameter: required or defaulted | required keyword-only, the shape of the newer `measure_*` functions (e.g. `:L828-L829`) | a `= time.perf_counter` default, like `measure_task_volume`'s. A caller that forgot to pass it would fall back to the real clock without a word, which is how this bug got in |
| Where the create count lives in the tests | `CREATES = 51`, with a test that pins it to `len(harness.specs())` | changing `_run_readings` to take `harness`, which would have touched about 15 call sites. Leaving the count unpinned was rejected too: two readings too many would shift silently into the task add and still read as quick |
| Red and green as separate commits | one green commit, with red shown in the working tree against the old harness (§ 3) | a red commit: the builder's commit gate refuses a commit that turns tests red, and this one turns several red (`commit_gate.py:L1-L12`) |
| Changelog line | none | a tests-only change earns none (`kensaiapp_structure.md` § The changelog). `python3 tests/timed_run.py` behaves the same for a user |

## 5. Problems hit

- The brief allowed separate red and green commits, but the commit gate makes a red commit
  impossible. That cost nothing here, but the brief should know.
- The seal reported `4 failed, 3328 passed` (3332). This run's card suite collects 3309 (3306 + 3
  new). The seal's tree evidently held about 23 more tests. Not investigated.
- An earlier run stopped on an API error before making any change, so the worktree was clean when
  this run started.

## 6. Surfaced, not settled

- **Whole runs on the real clock.** Four tests still call `harness.main(tmp_path)` with no timer
  (`test_timed_run.py:L94`, `:L225`, `:L506`, `:L807`), so they time every action on the real
  clock. At least `:L94` asserts `"over" not in report` (`:L109`). Under load they can still go
  red, the same way the four did. Recommendation: owner's call. If they are the NFR-1 measurement
  itself, they belong out of the gated suite. If they only check the harness's wiring, give them
  `_run_readings()`. Not changed, because it decides what those tests are for.
- **`_local_today()` reads the wall clock** (`:L1390-L1392`). Tests already set it with
  `monkeypatch.setattr(harness, "_local_today", …)` (`test_timed_run.py:L4438`), which
  `testing_python.md:L31` forbids. It is a date, not load: a midnight edge, not a flake under load.
  Recommendation: inject it as `today` in a later change.
- **The merge** needs a changelog entry or `--user-invisible "tests only: the timed run's creates
  read the injected timer"`. No changelog entry was added, per § 4.

## 7. Commits

| SHA | Covers |
|---|---|
| `ac619e5ff` | `tests/timed_run.py` + `tests/integration/test_timed_run.py`: the fix and the tests |
| this report's commit | this file |
