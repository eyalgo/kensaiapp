---
version: "1.5.0"
---

# Python — toolchain

The interpreter, the version floor, the dependency position, and how a dependency is added. Where
a file of a given kind goes is `layout.md`; which checks run over it is `quality_gates.md`.

## Interpreter

CPython, and no alternative implementation is in scope. The `core/tools/` suite, every hook and
every launch run on the Python minor version that `.python-version` at the instance root names,
which uv selects. The hooks are the commands in `.claude/settings.json` and the two git hook shims
under `core/githooks/`. A launch is a launcher under `core/launchers/` or a `core/tools/launch-*.sh`,
together with the shell helpers it sources and the Python it starts. ADR-0001 under
`core/tools/docs/adr/` records the choice for the suite. A hook and a launch reach the pinned Python
through `core/tools/locked_python.sh`, and in a satellite or a pinned run they reach the host's or
the pin's instead. The one exception inside a launch is a pytest suite that `core/tools/suite_map.py`
names, which runs as the tools card's test command does, through `uv run --locked pytest`, on the
same Python. `core/tools/test_launches_run_on_the_locked_python.py` fails when a launcher, a shell
helper under `core/tools/` or a kensaiapp Python under `core/tools/` starts `python3` again.
Without uv on `PATH`, a launch stops before it starts anything and exits `1`, because `pin_enter` in
`core/tools/pin_run.sh` asks the runner for uv first. Nothing falls back to `python3`. A process
that a hook or a launch starts, a launched agent included, gets the `PATH` and `VIRTUAL_ENV` its
caller had and none of the variables uv sets, so a product suite an agent runs does not run on
kensaiapp's `.venv` (`core/tools/locked_python.sh`, held by `core/tools/test_locked_python.py`). A
command that a skill's `SKILL.md` or one of its prompts gives an agent runs through
`core/tools/locked_python.sh` too, written there as `"<CORE>/tools/locked_python.sh"`, so it runs on
the pinned Python whichever `python3` `PATH` finds first.
`core/tools/test_skills_run_on_the_locked_python.py` fails when one of those files holds a command
that starts `python3` again. No `tox.ini` or virtualenv is tracked (`git ls-files` matched neither,
2026-10-26).

**The supported floor is Python 3.13.** `pyproject.toml` at the instance root states it as
`requires-python = ">=3.13"`, and uv refuses to run the `core/tools/` suite or a hook when
`.python-version` names a Python below it (uv 0.11.14, 2026-10-26). For a hook, measured on a
scratch root pinned to 3.12, `uv run --no-sync` exited `2` with "incompatible with the project's
Python requirement". A launch reaches its Python through the same runner and the same
`uv run --no-sync`, so on that measurement uv refuses a launch below the floor the same way.

Two facts sit behind the number, and the second is the one that moves it. The syntax needs only
**3.10**: ten tracked files use a PEP 604 `X | None` annotation with no `from __future__ import
annotations` in front of it to defer its evaluation — `.claude/hooks/written_forward_guard.py:37`
reads `def _repo_root(file_path: str) -> str | None:` — and that union spelling parses before 3.10
(a return annotation is grammatically just an expression) but fails when it is evaluated: `str |
None` needs `type.__or__`, which PEP 604 added in 3.10, so calling the function under an older
interpreter raises `TypeError`, not a `SyntaxError`, at the point the annotation is read rather than
at import. What sets the floor is the standard library on a Mac: `core/tools/walk_stop.py` calls
`os.waitid`, which macOS Python has only from 3.13, so on 3.11 or 3.12 there stopping a walk raises
`AttributeError` (measured 2026-10-18 on 3.11, 3.12, 3.13 and 3.14). Linux has
had the call far longer, and the floor is one number for every host and for the products the
skeleton stamps all the same — the owner's call, 2026-10-18, raising it from 3.11.

## Build system

None. A `.py` file is executed as written — no compilation step, no wheel, no sdist, no generated
directory. `pyproject.toml` at the instance root carries no `[build-system]` table, so uv installs
nothing of the repository itself, only the test tools it declares, into a `.venv` at the instance
root that `.gitignore` ignores. `uv.lock` beside it is the one lockfile there. No `setup.py`,
`setup.cfg`, `requirements*.txt`, `poetry.lock` or `Pipfile` is tracked at the instance root
(`git ls-files`, 2026-10-26).

Because the repository's own code is not installed, a test cannot import its subject by package name. It gets there
through a directory-scoped `conftest.py` that puts that directory on `sys.path` —
`core/tools/conftest.py:9-12` and `.claude/conftest.py:8-11` are the two, each one
`sys.path.insert` call under a docstring saying the point is to work "regardless of pytest's import
mode or the working directory it is launched from".

## Dependencies

**Effectively zero.** Across 95 tracked `.py` files (`git ls-files '*.py' | wc -l`, 2026-08-21)
there is exactly one third-party import in shipped code — `import yaml` at
`skills/interactive/.claude/skills/skill-creator/scripts/quick_validate.py:9` — and it does not resolve on this
machine: `python3 -c "import yaml"` fails with `ModuleNotFoundError: No module named 'yaml'` and
`python3 -m pip show pyyaml` reports `Package(s) not found` (both 2026-08-21). Everything else
comes from the standard library.

**The test suite is the exception, and it is declared.** 42 tracked files carry `import pytest`
(`git grep -l '^import pytest' -- '*.py' | wc -l`, 2026-08-21). `pyproject.toml` at the instance
root names pytest and its plugin `pytest-xdist` as its only two dependencies, each pinned to an exact
version with `==`. The `core/` suites need `pytest-xdist` beside pytest: `core/pytest.ini` sets
`addopts = -n 32`, and without the plugin pytest stops with `unrecognized arguments: -n` before
running a test. `-n 0` runs serially and still needs the plugin installed. The `core/tools/` and `core/launchers/` suites run on the pinned pair through
`uv run --locked pytest core/tools/ core/launchers/`, the test command on the `tools` project card. A suite run with a bare `pytest` still gets whatever pytest the machine has.

### Adding one

Reaching outside the standard library is a product decision, not an implementation one. It is
recorded in that product's `docs/adr/`, which outranks this packet, and it lands in a single
change as three things:

- `pyproject.toml`, carrying a `requires-python` floor and the dependency under
  `[project.dependencies]`;
- the lockfile the chosen installer generates, committed;
- the dependency pinned to an exact version rather than a range, so a later install cannot change
  behaviour without a diff.

The instance root follows that shape. Its manager is uv, chosen for the Python version and the test
tools in ADR-0001 under `core/tools/docs/adr/`. A product that keeps a `pyproject.toml` of its own
names its manager in the record that adds its first dependency.
