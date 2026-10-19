---
version: "1.1.1"
---

# Python — toolchain

The interpreter, the version floor, the dependency position, and how a dependency is added. Where
a file of a given kind goes is `layout.md`; which checks run over it is `quality_gates.md`.

## Interpreter

CPython, reached as `python3`. `python3 --version` returned `Python 3.14.4` on this machine on
2026-08-21. No alternative implementation is in scope and no interpreter other than the one on
`PATH` is selected anywhere: no `.python-version`, `tox.ini` or virtualenv is tracked
(`git ls-files` matched none of them, 2026-08-21).

**The supported floor is Python 3.13**, and nothing enforces it — with no packaging metadata there
is no `requires-python` field to hold it, so it is a rule a reader applies.

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
directory. Nothing here is installed: `git ls-files 'pyproject.toml' 'setup.py' 'setup.cfg'
'requirements*.txt'` returned nothing on 2026-08-21, and no lockfile of any manager
(`poetry.lock`, `uv.lock`, `Pipfile`) is tracked either.

Because nothing is installed, a test cannot import its subject by package name. It gets there
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

**The test suite is the exception, and it is undeclared.** 42 tracked files carry `import pytest`
(`git grep -l '^import pytest' -- '*.py' | wc -l`, 2026-08-21) and no file in the repository names
pytest as a requirement, because there is no file that could. It is satisfied by whatever is on
the machine: `python3 -m pytest --version` returned `pytest 9.0.3` on 2026-08-21. The `core/`
suites need `pytest-xdist` beside it: `core/pytest.ini` sets `addopts = -n 32`, and without the
plugin pytest stops with `unrecognized arguments: -n` before running a test. `-n 0` runs serially
and still needs the plugin installed.

### Adding one

Reaching outside the standard library is a product decision, not an implementation one. It is
recorded in that product's `docs/adr/`, which outranks this packet, and it lands in a single
change as three things:

- `pyproject.toml`, carrying a `requires-python` floor and the dependency under
  `[project.dependencies]`;
- the lockfile the chosen installer generates, committed;
- the dependency pinned to an exact version rather than a range, so a later install cannot change
  behaviour without a diff.

No dependency has ever been added in this repository, so that procedure is this authoring run's
reasoning about the shape a first one should take, 2026-08-21, rather than an observed practice.
The manager is unfixed for the same reason — the first product to need one names it in the same
ADR.
