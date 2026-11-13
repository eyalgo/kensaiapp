# Tech Lead instruction — walk-skips-by-name: the source walk skips by name

**Category:** nfdr
**Behaviour:** changing
**Language resolution:** Python — step 1, `project.md` `Languages:` — `languages/python/README.md` opened, with every concern file it routes (`toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md`, and `testing_python.md`)
**Product root:** `products/tracker17` — every path below is relative to it.
**Scope:** `SourceWalk._all` in `tests/conftest.py` skips `tests/`, `.behave/` and `.venv/` at the root and `__pycache__` anywhere, by exact name, with no leading-dot test; a new layer-6 module proves it.

---

## Project layout

```
products/tracker17/
  tests/
    conftest.py                          ← modified (SourceWalk._all, SourceWalk docstring, module docstring)
    architecture/
      test_source_walk.py                ← new
      test_shapes.py                     unchanged (PARTS, top_level_parts imported from it)
      test_imports.py                    unchanged
      test_reach.py                      unchanged
      test_trace.py                      unchanged (reads the new module's docstring)
```

No parts table applies: SDD § 3 covers the five product parts, and `tests/` is no part's `Owns` (design, Architect Review Notes). Placement follows `change_design.md §2`. No directory or `__init__.py` is created.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **One task, not two units:** `change_design.md §3` names no sub-jobs, and the walk's new behaviour can only be stated through the tests in `test_source_walk.py`. A walk-only task would have no behaviours of its own and no red; a tests-only task would leave the suite red at its end. Both files are one task, test-first.
- **Hints merged:** `§4` carries one hint per file. Both go into the one task's `# Hint:` block, unchanged in substance, and numbered as the design numbers them.
- **Mixed red at baseline, stated:** four of the five behaviours fail at `97603d4f3` (the base walk skips every dot piece); the CP-790 behaviour passes there and after, as the spec requires. The task is test-first because it has a red; the green-at-base behaviour is marked so the developer does not read its green as a missed red.
- **Docstrings are held by review:** the design requires the `SourceWalk` docstring and the module docstring's source-walk paragraph to say what is skipped, by name. No test asserts docstring text, so they are listed under `#### Held by review`, not invented as behaviours.
- **Gate command checked:** the card's `Test command:` ran in the change worktree and collected tests (3296 passed, 1 failed, 2 skipped; and 122 passed in `tests/e2e/`). The one failure, `tests/integration/test_sigint_launch.py::test_real_start_stops_when_pytest_launch_ignores_sigint`, passed when run alone, so it is a full-run timing failure and not red at baseline from an earlier change unit. No red-at-baseline shape is used. Ruff's two checks are added to the gate (CP-792), because the card's command does not run them.

## Corrections owed while there

- `tests/conftest.py` — the `SourceWalk` docstring ("not a test, a hidden folder or generated") and the module docstring's source-walk paragraph (which says only "outside ``tests/``") name a hidden-folder rule that is gone → say what is skipped, by name. Rides Task 1 (that task already opens this file).
- Owed outside this change's reach: `docs/nfdr.md` § 1.1, QC-1, *verified by* — the sentence "The entry starts unmet in its test: at `373ecc8a8`, `SourceWalk._all` in `tests/conftest.py` skips every path piece that begins with a dot, so a dot-folder holding code passes unseen" goes false once the walk skips by name → the entry is met: the walk skips the three root folders and `__pycache__` by name, and `tests/architecture/test_source_walk.py` fails on a code-holding dot-folder at the root; the unmet half is dated to the last commit before this change lands, as QC-39's tail dates its own.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git ls-files filtered for .github, .circleci, .gitlab-ci, azure-pipelines, Jenkinsfile, .travis, buildkite, bitbucket-pipelines, .drone, appveyor, .woodpecker and cloudbuild paths listed nothing"
  },
  "decisions": {"override": null, "amd64": null},
  "candidates": [],
  "guest": null
}
```

### Task 1: The source walk skips by name (`tests/conftest.py`, `tests/architecture/test_source_walk.py`)

**Dependencies:** None

**What to build:** `SourceWalk._all` leaves out exactly the `.py` files whose first path piece under the root is `tests`, `.behave` or `.venv`, and those with a path piece named `__pycache__` at any depth, each by exact name; it no longer tests for a leading dot. `tests/architecture/test_source_walk.py` is a new layer-6 module that builds roots under `tmp_path` and proves it. The walk's surface (`walk_of`, `SourceWalk.modules`, `Module`) keeps its signatures, and its verdict over the product root stays exactly `PARTS` (CP-785, CP-786, CP-787).

The roots the tests build hold the six parts: `domain/`, `application/`, `persistence/` and `web/` each with one module, plus `main.py` and `errors.py`. A shared builder plants CP-788's root (the six parts; `tests/x.py`, `.behave/features/x.py`, `.venv/x.py`, `__pycache__/x.py`, `domain/__pycache__/x.py`; `.other/x.py`) so the cases cannot drift apart.

#### Behaviours to verify (developer adds tests to `tests/architecture/test_source_walk.py`)

- `test_a_code_holding_dot_folder_fails_the_parts_comparison` — layer 6 Architecture — fakes: none, real files under `tmp_path`, root handed to `walk_of` — on CP-788's root, `top_level_parts(walk_of(root))` is not `PARTS` and contains `.other`; after `.other/x.py` is removed it equals `PARTS` (CP-788, CP-789). Fails at `97603d4f3` on its first assertion.
- `test_the_named_folders_and_pycache_stay_skipped` — layer 6 Architecture — fakes: none — CP-788's root built without `.other/` reports exactly `PARTS`, and no walked module's path has a first piece in `tests`, `.behave` or `.venv`, or any piece named `__pycache__` (CP-790, CP-785). **Passes at `97603d4f3` and after the change.**
- `test_a_dot_named_file_at_the_root_is_walked_as_its_own_part` — layer 6 Architecture — fakes: none — the six parts plus `.x.py` at the root report `PARTS` plus `.x` (CP-786). Fails at `97603d4f3`.
- `test_a_dot_or_named_folder_inside_a_part_is_walked_as_that_part` — layer 6 Architecture — fakes: none — the six parts plus `web/.hidden/y.py`, `domain/.venv/x.py` and `domain/tests/x.py`: all three paths are among the walked modules, with parts `web`, `domain` and `domain`, and `top_level_parts` equals `PARTS` (CP-786). Fails at `97603d4f3`.
- `test_near_names_of_the_skipped_folders_are_walked` — layer 6 Architecture — fakes: none — the six parts plus `.venvs/x.py`, `.behave2/x.py` and `Tests/x.py`, in a root with no `tests/` folder: the parts reported are `PARTS` plus `.venvs`, `.behave2` and `Tests`, so QC-1's comparison is not equal (CP-786). Fails at `97603d4f3`.

#### Held by review (rules of this task that reach no test)

- The `SourceWalk` docstring and the module docstring's source-walk paragraph in `tests/conftest.py` say what is skipped, by name, in place of "a hidden folder" — no test asserts docstring text; held by reading the diff.
- CP-787 (the product root still walks to exactly `PARTS`, with `.venv/` and `.behave/` present) — held by the existing `test_shapes.py::test_the_top_level_parts_are_the_five_the_sdd_names` and the other layer-6 modules over the product root, which this task does not alter; no new test.
- CP-791 — the new module's opening docstring names the SRS requirements it checks (NFR-9, AC-5, with NFDR QC-1 as the clause) and spells no planted path; held by the existing `tests/architecture/test_trace.py`, which reads it.
- CP-793 and CP-794 — the design's own reviews, passed at `development-design`; the code review re-reads that the new module adds no part and uses nothing newer than Python 3.11.

#### Implement

Infer from failing tests.

```
# Hint:
# (1) tests/conftest.py — SourceWalk._all skips by name. The skip set is data: a module-level
#     constant holding the three root names, and the one name matched at any depth. The test is
#     set membership on the relative path's pieces, the first piece for the root names and every
#     piece for __pycache__, with no prefix, case-folding or pattern match, so that .venvs,
#     .behave2 and Tests miss. A file at the root has a first piece ending .py, so it can never
#     equal a root name, and no separate guard for root files is needed.
# (2) tests/architecture/test_source_walk.py — plant files the way test_shapes.py's
#     test_each_walk_finds_a_violation_planted_where_it_looks does: write each relative path under
#     tmp_path, making parents first. Use one small builder for CP-788's root that the cases share.
#     Take PARTS and top_level_parts from test_shapes by import, as tests/integration/ modules
#     import from their siblings, rather than copying the set.
# (3) The module docstring must spell no planted path. test_trace.py's path pattern resolves every
#     path-shaped token in a test module's docstring against the product root, and a planted name
#     such as the CP-788 dot-folder file does not exist there. Describe planted files in words, or
#     name them only in function docstrings and code.
# (4) Plant Tests/ in a root with no tests/ folder. On a filesystem that ignores case, the macOS
#     default, the two names are one folder, and the near-name case would silently become the
#     skipped one.
# (5) Keep to Python 3.11 (QC-60): Path.walk and relative_to(..., walk_up=...) are 3.12, and
#     nothing here needs them.
```

#### Verification gate

Run from the change worktree's root, the card's command: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`. Then, from `products/tracker17`: `uv run --locked ruff format --check --no-cache .` and `uv run --locked ruff check --no-cache .` (CP-792).

Pass criteria: the five new tests pass; both suites report passed tests and no failed or errored one on the last line of each (CP-795); both Ruff commands exit 0. The CP-788 test fails when run against `SourceWalk._all` as it stands at `97603d4f3`.
