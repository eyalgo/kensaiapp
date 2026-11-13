# Changelog report — 2026-11-13_walk-skips-by-name

## Change

- Change key `2026-11-13_walk-skips-by-name`, project tracker17, own product path `products/tracker17` in the instance repository.
- Considered changelog: `products/tracker17/CHANGELOG.md`, in the instance repository, because it is the own product path's, and because the branch changes `products/tracker17/tests/conftest.py` and `products/tracker17/tests/architecture/test_source_walk.py` under it.
- The branch's other changed paths sit in the change folder under `system/projects/`, which lies under no product path and is no listed root file, so they are logged in no changelog.
- No project card was refused by the path tool.

## Changelog

The change earns no entry, because it alters nothing a user of a fresh clone installs, runs, types or reads at any product path this run considered.

- `products/tracker17/CHANGELOG.md`, in the instance repository: no entry. The branch changes only the test fixture's source walk and adds a test module; the tracker's code, documents, commands and dependencies are unchanged, and a change that only adds or changes tests earns none.

## What-left

`products/tracker17/docs/what_left.md` already holds the line `Nothing is left to build.`, so no want was removed and the file was left as it was.

## Evidence

- `601c3cf2c` (red), `a604290a5` (green), `de33064f0` (refactor), `<a commit not in the public history>` (implementation complete): the branch's product commits, touching only `products/tracker17/tests/conftest.py` and `products/tracker17/tests/architecture/test_source_walk.py`.
- The branch tip read at the start was `<a commit not in the public history>`.
