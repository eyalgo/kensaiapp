# Changelog report — 2026-11-13_behave-import-walk

## Change

Change key `2026-11-13_behave-import-walk`, project tracker17, own product path `products/tracker17` in the instance repository.

- `products/tracker17/CHANGELOG.md`, in the instance repository: considered because it is the own product path's, and because the changed paths `products/tracker17/tests/architecture/test_behave_imports.py` and `products/tracker17/tests/conftest.py` lie under it.

The branch's other changed paths, under `system/projects/tracker17/journey/`, lie under no product path and are no listed root file, so no changelog logs them. The path tool refused no project card. The card for tracker16-X resolves to a separate repository that holds no branch for this change, so that product path was not kept.

## Changelog

The change earns no entry, because it alters nothing a user of a fresh clone installs, runs, types or reads at any product path this run considered.

- `products/tracker17/CHANGELOG.md`, in the instance repository: no entry. The branch's diff there adds a test module and a test fixture and changes nothing else, and a change that only adds tests is one only the instance's own developers see.

## What-left

`products/tracker17/docs/what_left.md` already holds the line `Nothing is left to build.`, so the run removed nothing.

## Evidence

- The product diff is test-only: `products/tracker17/tests/architecture/test_behave_imports.py` (new, 294 lines) and `products/tracker17/tests/conftest.py` (49 lines added), from `git diff --stat main...2026-11-13_behave-import-walk -- products/tracker17`.
- The commits that carry it: `b13ddc0a0`, `5ab59d992`, `1112d5822`, `a217613e7`, and `<a commit not in the public history>`, the implementation's closing commit.
- The change's request and spec say no product code, `.behave/` file or document changes.
