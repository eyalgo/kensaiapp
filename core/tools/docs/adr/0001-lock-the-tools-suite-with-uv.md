# ADR-0001: Lock the tools suite's Python and test tools with uv

**Status:** Accepted
**Date:** 2026-10-26

## Context

The `core/tools/` suite ran on whichever `python3` and `pytest` the shell found first. Nothing in
the repository named either, because no file at the instance root declared a dependency. On
2026-10-21, as recorded with the owner's rulings of 2026-10-22, Homebrew made Python 3.15 the
`python3` a shell found first on the owner's Mac while pytest and pytest-xdist were installed only
for Python 3.14, and a walk halted twice on a red suite with no test failing. The suite's verdict
had come to depend on what the machine last installed, not on the code under test.

`core/doctrine/engineering/languages/python/toolchain.md` § *Adding one* makes reaching outside the
standard library a product decision, recorded in that product's `docs/adr/`. This record is that
decision for the test tools and the Python they run on.

## Decision

The owner's call, 2026-10-22: "**uv** locks the Python side: the Python version and the test tools
(pytest, pytest-xdist), pinned exactly, with a committed lock file. The project's test command runs
through it." The owner settled the version on 2026-10-26: the pinned Python is `3.14`, "the minor
version and not a patch release".

The instance root is a uv project, and three tracked files there fix what the `core/tools/` suite
runs on. `.python-version` reads `3.14`, so uv runs the suite on a CPython 3.14 release.
`pyproject.toml` states `requires-python = ">=3.13"` and declares exactly two dependencies under
`[project.dependencies]`, pytest and pytest-xdist, each pinned to an exact version with `==`. It has
no `[build-system]` table, so uv installs those two tools and nothing of the repository itself.
`uv.lock` is the lock uv generates from `pyproject.toml`, and it is committed.

This product's test command, as its project card gives it, is
`uv run --locked pytest core/tools/ core/launchers/`, run from the instance root.
`core/launchers/` joined it on 2026-10-26, by the owner's call of that date, so the suite gate also
runs the launchers' own tests. `--locked` makes uv stop when `uv.lock` no longer matches
`pyproject.toml`, rather than rewrite the lock, so running the suite never edits a tracked file.

## Alternatives ruled out

- **Keep running on the machine's `python3` and `pytest`.** It lost because the suite's verdict then
  depends on what the machine last installed, which is how the walk of 2026-10-21 halted with no
  test failing.
- **A virtual environment made with Python's `venv`, from a `requirements.txt` of exact pins.** It
  pins the test tools and not the Python. On this record's reading, it lost because
  `python3 -m venv` builds on whichever interpreter runs it, so the Python stays the one the shell
  finds first.
- **A `.python-version` file read by pyenv, with no manager.** It lost on a measurement. On
  2026-10-26, in a directory whose `.python-version` read `3.14`, the `python3` shim of pyenv 2.6.7,
  which held no 3.14, ran Python 3.15.0 and exited 0. The file named a Python without making
  anything run on it, and it pins no test tool.

## Consequences

Easier: the suite's verdict no longer depends on which `python3` or `pytest` the shell finds first.
Measured 2026-10-26 on a disposable clone with the three files added and a `python3` that only exits
1 first on `PATH`: `uv run --locked pytest core/tools/ -q -p no:cacheprovider` reported 8354 passed
and 16 skipped, exit 0, on CPython 3.14.7, with pytest 9.0.3 and pytest-xdist 3.8.0. Moving a test
tool is now a diff: an edit to `pyproject.toml` and a regenerated `uv.lock`, both reviewed.

Harder: uv is a prerequisite for running the suite, on every machine and in every environment the
suite gate uses. Each checkout makes its own `.venv` on its first run, a change worktree included.
Where the machine has no Python 3.14, uv downloads one unless downloads are turned off
(`uv run --help`: "Disable automatic downloads of Python"), so a first run there needs the network.

What stays as it was: the `python3` commands skills give an agent still run the `python3` that
`PATH` finds first, and a suite run with a bare `pytest` still runs on the machine's pytest. This
record does not move them. The hooks and the launchers moved on 2026-10-26, by the owner's call of
that date: "the hooks and launchers run through uv too, on the same pinned Python, so nothing
kensaiapp runs depends on the machine's `python3`." Every hook, and every Python a launch starts
other than a pytest suite, now runs through `core/tools/locked_python.sh` on the Python
`.python-version` names, with `--no-sync`, so it installs nothing of the test tools this record
locks. A pytest suite that `core/tools/suite_map.py` names runs as this product's test command
does, through `uv run --locked pytest`. Without uv, a launch stops before it starts anything. What a
launch hands the processes it starts, its agent included, also stays as it was: the runner gives
them the `PATH` and `VIRTUAL_ENV` the launcher was given, so an agent and the product suites it runs
do not run on this record's `.venv`.

Every later change binds to it: a test tool added at the instance root goes into `pyproject.toml`
with an exact pin, and `uv.lock` is regenerated in the same change. Undoing the decision is one change: delete the three files and set the test command back to
`pytest core/tools/ core/launchers/`. No test
imports anything of uv.

## Traces to

- The owner's call of 2026-10-22 and the version settled on 2026-10-26, both quoted under
  *Decision*.
- `core/doctrine/engineering/languages/python/toolchain.md` § *Adding one* — what a first dependency
  lands as, and where the choice of its manager is recorded.

## Binds

none
