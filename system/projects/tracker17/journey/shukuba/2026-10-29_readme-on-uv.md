# 宿場 Shukuba — the README sets up the suite with uv

*Item 2 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv`. Slug: `readme-on-uv`.*

## What it is

Rewrite the product README's suite instructions to the uv path the records already state (SDD § 4 RT-4, ADR-0013). The "Running the tests" section stops making a `venv` and installing from `tests/requirements.txt`, a file that no longer exists; it says uv must be installed first, then gives `uv sync --locked`, `uv run playwright install chromium`, `uv run pytest tests/` and `uv run pytest tests/e2e/`, with the Linux `--with-deps` variant and the `.venv` and activation paragraphs reworded to match. The "How it's built" test line says uv makes the suite's environment. One station because the two README places state the same fact and must not disagree. The tracker's own setup lines stay as they are.

## Reached when

All hold at the product root (`products/tracker17`), checked on `main` after the change lands:

1. `grep -nF -e 'python3 -m venv' -e 'pip install' -e 'requirements.txt' -e 'activate' -e 'python -m playwright' -e '`venv`' README.md` prints nothing and exits 1 (fixed-string, case-sensitive, one file; before the work it prints lines 93, 97, 98, 99, 100, 109 and 135).
2. `README.md` holds, inside "Running the tests", each of `uv sync --locked`, `uv run playwright install chromium`, `uv run pytest tests/` and `uv run pytest tests/e2e/`, found by `grep -nF -e` for each string, each printing at least one line; and that section says uv has to be installed first and where to get it.
3. The "How it's built" test line names uv as what makes the suite's environment: `sed -n "/^## How it's built/,/^## The documents/p" README.md | grep -nw uv` prints at least one line.
4. The tracker's own setup names uv nowhere: `sed -n '/^## Setup instructions/,/^### Running the tests/p' README.md | grep -nw uv` prints nothing and exits 1.

## Guardrail

- The tracker's start path stays `python3 main.py` with nothing installed; the tracker's own setup text is not changed except for a sentence this edit makes false.
- No command in the README is invented: each is the one SDD § 4 RT-4 gives, and a command the README gives is one that works from `products/tracker17` on `main`.
- No tracker code, test, record under `docs/`, or project card line changes.
- **Not here:** the project card's Setup and Test commands are `tracker17 · shukuba · 2026-10-29_project-card-commands`'s (route item 3 of the seed); QC-40's review moment and QC-60's Python 3.11 run are held outside this seed (`tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv`, § Out).
