# Changelog report — 2026-11-12_failed-action-path-non-text-byte

## Change

- Change key: `2026-11-12_failed-action-path-non-text-byte`. Project: tracker17. Own product path: `products/tracker17`, in the instance repository.
- Considered changelog: `products/tracker17/CHANGELOG.md`, in the instance repository, because it is the own product path's, and because a changed path, `products/tracker17/tests/integration/test_failure_report.py`, lies under its product path.
- The branch's other changed paths sit under `system/projects/tracker17/journey/`, which lies under no product path and is no listed root file, so they are logged in no changelog.
- The path tool refused no project card.

## Changelog

The change earns no entry, because it alters nothing a user of a fresh clone installs, runs, types or reads at any product path this run considered.

- `products/tracker17/CHANGELOG.md`, in the instance repository: no entry. The branch's only change under `products/tracker17` adds an integration test, `tests/integration/test_failure_report.py`, which pins the console report of a failed action at a non-text-byte path. No production code changed, and a change that only adds tests earns no entry.

## What-left

`products/tracker17/docs/what_left.md` already holds the line `Nothing is left to build.`, so the run removed nothing.

## Evidence

- `edd1b6380` adds `products/tracker17/tests/integration/test_failure_report.py`, the branch's only change under `products/tracker17`.
- `<a commit not in the public history>` is the developer's implementation-complete commit and carries no change under `products/tracker17`.
- `d33dd0009`, `11cb3ae5d` and `368824486` add the change's spec, design and plan under `system/projects/tracker17/journey/`.
