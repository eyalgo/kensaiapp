# 宿場 Shukuba — the lock is `uv.lock`, and the pin test reads it

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv`. Slug: `lock-and-pins-test`.*

## What it is

Replace the product's pip lock file with uv's. Generate `uv.lock` beside `pyproject.toml` from the exact pins already in `[dependency-groups] dev`, delete `tests/requirements.txt`, and rewrite `tests/architecture/test_pins.py`'s lock-file test so it checks `uv.lock` instead. The comments in `pyproject.toml` that name `tests/requirements.txt` are reworded to name `uv.lock`. One station because the file, its test and the comment that names it must move together: the test reads the old file, so none can land alone. The README's setup lines and the project card's commands are the next two stations.

## Reached when

All hold at the product root (`products/tracker17`), checked in a fresh clone of the branch's commit:

1. `uv.lock` exists beside `pyproject.toml`, and `uv lock --check` exits 0.
2. `tests/requirements.txt` does not exist, and `grep -n "requirements.txt" pyproject.toml tests/architecture/test_pins.py` prints nothing (fixed-string, case-sensitive, over those two files; today it prints `pyproject.toml:8` and `tests/architecture/test_pins.py:40`).
3. `tests/architecture/test_pins.py` fails when `uv.lock` is absent, and fails when a test dependency in `[dependency-groups]` is not pinned with `==`. Shown by running that file in a scratch copy, once with `uv.lock` removed and once with `pytest==9.1.1` changed to `pytest>=9`, each exiting non-zero. The file reads no `tests/requirements.txt`.
4. `uv sync --locked` exits 0, then `uv run pytest tests/unit tests/architecture` exits 0, both from the product root.

## Guardrail

- Dependency versions stay as they are: `uv.lock` resolves the existing exact pins, and no pin in `pyproject.toml` is changed, added or removed.
- `test_every_declared_dependency_is_pinned_exactly`, `test_requires_python_is_3_11` and `test_the_exact_pattern_refuses_a_range_and_accepts_a_pin` keep passing and are not weakened; no test is deleted, skipped, retried or marked expected-to-fail.
- No tracker code, no record under `docs/`, and no project card line changes. A README sentence this change makes false may be corrected on the branch (`found_while_walking.md` clause 1); the README's uv rewrite is the next station's.
- **Not here:** the README's suite section and "How it's built" line are `tracker17 · shukuba · 2026-10-29_readme-on-uv`'s; the project card's Setup and Test commands are `tracker17 · shukuba · 2026-10-29_project-card-commands`'s; QC-40's review moment and QC-60's Python 3.11 run are held by the owner and the Principal Architect, not this seed.
