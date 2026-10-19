---
version: "1.1.4"
---

# Python — layout

The source tree, where a new file of each kind goes, and how files and modules are named. How the
things *inside* a file are named is `conventions.md`. **Where a test file goes splits by tree** — a
managed product's test location is `testing_python.md`'s to own, per test layer. This instance's
own Python is not a product, and its test location is this file's own, stated below in § Two
trees, and which rule governs which.

## Two trees, and which rule governs which

A **managed product** gets its package shape from `arch_defaults.md` § Package Structure — which is
language-agnostic, so it is the body and not the Python overlay — and its test tree from
`testing_python.md`. This file adds nothing to either.

**This instance's own Python is not a product** — it is a set of standalone executables and the
small modules they import, and it is laid out accordingly:

```
core/tools/<module>.py             a tool, flat, one responsibility
core/tools/<package>/              a tool that grew internal files: __init__.py + its modules
core/launchers/<launcher-name>/    the launcher's shell script and its test, together
.claude/hooks/<hook>.py            one Claude Code hook per file
```

**A test sits beside its subject, not under a `tests/` directory.** All 17 tests of `core/tools`
are `core/tools/test_<module>.py` (`git ls-files 'core/tools/test_*.py' | wc -l`, 2026-08-21) and
`core/tools` has no `tests/` subdirectory at all. Only two directories named `tests/` hold Python
anywhere in the tree — `.claude/tests/` and `skills/interactive-product/.claude/skills/project-stamp/tests/`.

## Where a new file goes

| Kind | Path |
|---|---|
| A tool with one responsibility | `core/tools/<module>.py` |
| A tool needing more than one module | `core/tools/<package>/`, with `__init__.py` |
| A Claude Code hook | `.claude/hooks/<hook>.py` |
| A test for any of the above | `test_<subject-basename>.py`, in the same directory |
| The `sys.path` shim a directory's tests need | `conftest.py`, in that directory |

## Naming

- **snake_case for a module filename**, all lowercase: `commit_builder.py`, `written_forward.py`,
  `verify_commit_msg.py`. One tracked `.py` file departs from it and cannot be imported because of
  it: `.claude/hooks/development-bash-approve.py`, whose test therefore drives it as a subprocess
  through `sys.executable` rather than importing it
  (`.claude/hooks/test_development_bash_approve.py:26` and `:32`). That is the cost of the hyphen,
  and it is the reason the rule is worth keeping.
- **A test file is `test_` plus its subject's basename.** All 52 test files in the tree open with
  `test_`; none uses the `<name>_test.py` form pytest also accepts
  (`https://docs.pytest.org/en/stable/explanation/goodpractices.html`, read 2026-08-21).
- **A directory holding a launcher may be kebab-case; the Python file inside it may not.** 13 of
  the 14 entries under `core/launchers/` are kebab-case directory names (`ratify` is the one-word
  exception), and each holds `test_<the same name in snake_case>.py` —
  `core/launchers/launch-eval-fix/test_launch_eval_fix.py`. The directory is never imported; the
  file is.

## `__init__.py`

`<CORE>/doctrine/engineering/languages/developer_standards.md` § Clean code fixes the rule — package
initialization and public re-exports only, never implementation — and this file adds only what the
two package `__init__.py` files here carry beyond that: a docstring naming the package's single
responsibility, and `__version__` (`core/tools/auditrun/__init__.py` and
`core/tools/coldread/__init__.py`). The other three tracked `__init__.py` files are empty, which is
the right content for a package that exports nothing.

## Shebang and the executable bit

Two decisions, and they are not the same one.

- **A file meant to be run carries `#!/usr/bin/env python3` as line 1.** 30 tracked files do, and
  all 30 use that exact line — no variation. A file meant only to be imported carries none and
  opens with its module docstring instead (`core/tools/reporters.py:1`,
  `core/tools/coldread/manifest.py:1`). **No test file carries a shebang**, because pytest imports
  it rather than executing it.
- **The executable bit is required where something execs the path directly, and carried by more
  files than need it.** 15 of the 30 carry mode `100755` (`git ls-files -s '*.py'`, 2026-08-21).
  Two of those must: `core/githooks/commit-msg:20` ends `exec "$core/tools/verify_commit_msg.py"
  "$1"` and `core/githooks/pre-commit:27` ends `exec "$core/tools/written_forward.py" --staged
  --repo "$repo"`. The three executable files under `.claude/hooks/` do not — every hook command in
  `.claude/settings.json` invokes its script as `python3 "<path>"`, which ignores the bit. **Set it
  when you add an `exec` of the path, and not because the file has a shebang**; every file with the
  bit does have one, and the reverse does not hold.
