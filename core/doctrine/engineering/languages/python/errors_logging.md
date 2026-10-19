---
version: "1.1.3"
---

# Python — errors and logging

What the code does at a failure and at an event. How code is named and shaped the rest of the time
is `conventions.md`.

## The cut: a module raises, an entry point exits

- **A module that can be imported raises a named exception and says nothing about exit status.**
  Three exist in the tree, each defined at the top of the module that raises it:
  `AuditRoundError(Exception)` (`core/tools/auditrun/rounds.py:36`), `ManifestError(Exception)`
  (`core/tools/coldread/manifest.py:28`) and `UnknownActorError(ValueError)`
  (`core/tools/commit_builder.py:197`). **Two of the three docstrings name who converts it** — the
  first says "the launcher converts it to `die()` before any run launches", the second "The entry
  converts it to a die() before any link launches." **The third names the refusal's rationale
  instead** — why the builder raises rather than emitting a malformed trailer — and not its
  converter; `commit_builder.py:881` and `:915` are where `main()` actually catches it, in the
  `print(…, file=sys.stderr)` / `return 1` shape § Exiting below documents, so the contract still
  holds — it just is not the docstring that states it.
- **An entry point converts a failure into a message on stderr and a non-zero exit status.** Never
  a traceback: an unhandled exception reaching the top prints an internal call stack to a person
  who cannot act on it.

The base class is the narrowest one that is still true, for the house's own tools — not a product,
per `layout.md` § Two trees. Two of the three subclass `Exception` directly; `UnknownActorError`
subclasses `ValueError` because an unmapped actor *is* a bad argument value, and a caller that
already handles `ValueError` should not have to learn a new name. A managed product does not get
that choice: `arch_defaults.md` § *Exception shape* states the single-named-base rule and
`arch_defaults_python.md` § *Exception hierarchy* spells it in Python, forbidding exactly what two of
these three do — a typed exception inheriting directly
from bare `Exception`.

## Exiting

Two shapes are in use and they reach the same place. `SystemExit` carrying a string prints that
string to stderr and exits `1` — checked on 2026-08-21: `python3 -c 'raise SystemExit("error:
boom")'` wrote `error: boom` to stderr and nothing to stdout, exit status `1`.

- **`raise SystemExit(f"error: …")`, from wherever the failure is found.** 27 sites, all in
  `core/tools/link_satellite.py` (7) and `core/tools/spawn_satellite.py` (20) — one-shot tools
  where a check deep in a helper has no caller to report upward to.
- **`print(…, file=sys.stderr)` then `return 1` from `main()`.** `core/tools/commit_builder.py:881`
  and `:915` are the model — `print(f"commit_builder: {exc}", file=sys.stderr)` — and
  `core/tools/written_forward.py` ends its `main()` the same way.

**Which shape follows from where the failure is detected**, and that reading of the corpus is this
authoring run's, 2026-08-21: inside `main()`'s own body, return the status, because the exit path
stays in one place and a test can assert the integer (`core/tools/test_commit_builder.py:553`
calls `commit_builder.main([...])` and reads its return); deeper than that, raise `SystemExit`, and
the test catches it with `pytest.raises(SystemExit)` instead.

**A `main()` that returns a status is spelled `def main(argv: list[str] | None = None) -> int` and
wired as `sys.exit(main())`.** Twelve files carry that exact signature — the `argv` parameter is
what lets a test drive the entry point without touching `sys.argv` — and 19 of the 31 `__main__`
blocks in the tree are `sys.exit(main())`.

## Message shape

- **The prefix is lowercase `error: `.** 34 sites: the 27 `SystemExit` messages above, plus seven
  `print` calls in `skills/interactive-product/.claude/skills/project-stamp/scripts/stamp_project.py`. The capitalised
  `Error:` / `ERROR:` form is used by eight `print` calls in six files, every one of them under
  `.claude/scripts/` or `.claude/skills/` and none under `core/`.
- **A module that could be one of several in a run prefixes with its own name instead**, because
  no logger stamps it: `commit_builder: unknown actor …` (`core/tools/commit_builder.py:881`).
- **The message says what is wrong and what to fix.** `core/tools/commit_builder.py:209-211` is the
  shape — "unknown actor {actor!r} has no AGENT_ROLE mapping — refusing to build a commit with no
  derivable Role:" names the bad input, the refusal, and the mapping to add.

## Catching

- **Catch the narrowest type that can actually arrive.** `OSError` for a read that may not resolve
  (`core/tools/coldread/manifest.py:56`), `ValueError` and `TypeError` for input that will not parse
  (`:63`), `KeyError` for a lookup with a known miss.
- **No bare `except:` exists anywhere** — `git grep -nE '^\s*except:'` returned nothing across all
  95 tracked files on 2026-08-21.
- **`except Exception` is allowed only where the function's contract is best-effort, and the
  function says so.** 23 uses across the tree; ten are in `core/tools/reporters.py`, in five
  composer functions, and **all five name the choice in their own docstring** — the composer's job
  is to report what a run produced, and a reporter that raises would break the caller it exists to
  inform.
- **Re-raising discards or preserves the original, explicitly.** `raise … from None` where the
  original adds nothing a reader needs — two sites, each a `KeyError` turned into
  `UnknownActorError` with the `KeyError` suppressed because the missing key is already in the new
  message: `core/tools/commit_builder.py:212` (an actor lookup) and `:236` (a merge-authorizer
  lookup). `raise … from <caught>` where it does — `.claude/scripts/utils.py:55` re-raises a
  `json.JSONDecodeError` as a `RuntimeError` and keeps it. Those three sites are all of them in the
  tree; the two forms are the language's, and the rule to pick between them deliberately rather
  than by default is this authoring run's, 2026-08-21.

## Emitting

**Plain lines on two channels, and no logger.** `import logging` appears in no tracked file
(2026-08-21). There is no structured output and no level API. Symbol markers do appear — `✅`, `⚠️`,
`✓`, `✗`, `❌` — but they are not a ladder: five production files use them, no two use the same set,
and nothing reads them.

The one division that holds is the channel. **stdout carries what the command was asked to
produce; stderr carries why it could not.** Across the 40 production files, 185 `print(` calls, 84
of them with `file=sys.stderr`. `core/tools/written_forward.py` shows both in one `main()`: the
`--report` path prints its report to stdout and returns `0`, while the `--staged` path prints the
offending lines to stderr and returns `1`.

A product that needs levels, timestamps or structured records is adding a requirement this house
does not have, and it records the choice in its own `docs/nfdr.md`.
