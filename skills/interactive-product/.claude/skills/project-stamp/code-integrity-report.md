# code-integrity-report — stamp_project.py

*Written by the `development-code-integrity` skill, interactive mode, 2026-07-06.*

> **The paths below were rewritten on 2026-08-27**, when `project-scaffold` became
> `project-stamp` and `scaffold_project.py` became `stamp_project.py` (`38fae701`). The review
> ran under the old names; only the paths moved, and nothing it found changed.

## What was reviewed

`.claude/skills/project-stamp/scripts/stamp_project.py` — the deterministic
scaffolder that stamps a new managed project's `system/projects/<name>/` tree. It
was untested before this review.

## Intent it was checked against

The script's **documented contract**, never its implementation:

- `.claude/skills/project-stamp/SKILL.md` — "What it creates (and what it must
  not)", "Run it", and "External products: the directory grant is set automatically".
- `core/doctrine/setup/kensaiapp_structure.md §2` — the canonical per-project tree.

## Tests added

New suite at `.claude/skills/project-stamp/tests/` (subprocess against the
documented CLI, fully isolated in a temp instance root; `--core` points at the real
`core/` for read-only template reads). 12 tests:

**`test_creates_tree.py`** — the produced tree and bindings
- creates the exact §2 tree (all 10 files) for an internal project
- `project.md` binds the default `products/<name>` path and stamps the execution fields
- creates **no** product docs or code (only the management folder)
- success output reports the resolved `<CORE>` and the files created

**`test_guards.py`** — the input guards
- missing `--placement` is rejected
- external without a path → exit 2
- external with a relative path → exit 2
- internal with an absolute path → exit 2
- existing project folder → exit 3, and nothing inside it is touched (never overwrite)

**`test_external_grant.py`** — the external-only directory grant
- external placement merges the product path into
  `permissions.additionalDirectories` of `.claude/settings.local.json`
- the merge preserves a pre-existing `allow` list and other keys (never clobbers)
- an internal placement adds no grant

## Finding

**No issues.** Every behaviour in the contract already had correct code — all 12
tests passed on the first run, with no change to `stamp_project.py`. The script
matches its documented §2 contract across tree creation, `project.md` bindings,
the placement guards (exit 2), the never-overwrite guard (exit 3), and the external
directory-grant merge. The gap this review closed was **coverage**: the behaviour
was correct but unproven; it now has a regression suite derived from intent.

*Note on isolation:* the suite mirrors the script into a temp instance and runs with
`cwd` there, so both its CWD-relative writes (`system/projects/…`) and its
`.claude/settings.local.json` grant write land in the temp tree — verified to never
touch the real repo.
