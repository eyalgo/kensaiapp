# Changelog report — 2026-11-13_pins-test-reads-behave-lock

## Change

- Change key: `2026-11-13_pins-test-reads-behave-lock`
- Project: tracker17
- The change's own product path: `products/tracker17`, in the instance repository.
- Considered changelog: `products/tracker17/CHANGELOG.md`, in the instance repository. It is the own product path's, and the one changed product file, `products/tracker17/tests/architecture/test_pins.py`, lies under that product path.
- The branch's other changed paths sit in the change folder under `system/projects/tracker17/journey/`, which lies under no product path and is no listed root file, so they are logged in no changelog.
- No project card was refused by the path tool. The card of tracker16-X names a product in another repository, which does not hold this branch, so its product path was not kept.

## Changelog

The change earns no entry, because it alters nothing a user of a fresh clone installs, runs, types or reads at any product path this run considered.

- `products/tracker17/CHANGELOG.md`, in the instance repository: no entry. The branch only changes the test file `tests/architecture/test_pins.py`, which adds checks that the Behave folder's manifest pins every dependency exactly and that its lock fixes each pin. A change that only adds or changes tests is seen by the instance's own developers alone.

## What-left

`products/tracker17/docs/what_left.md` already holds the line `Nothing is left to build.`, so the run removed nothing.

## Evidence

- `git diff --name-only --no-renames main...2026-11-13_pins-test-reads-behave-lock` lists `products/tracker17/tests/architecture/test_pins.py` as the only changed path under a product path; the other three are the change folder's `change_design.md`, `change_spec.md` and `tl_instruction.md`.
- The test commits that make up the built work: `f819265ae`, `c98c94de6`, `91caa3d2a`, `b791b02c7`, `071fc5120`, `d0e8a959c`, `<a commit not in the public history>`, `<a commit not in the public history>`.
- `products/tracker17/CHANGELOG.md` is on the branch's tree and holds exactly one `## [Unreleased]` line.
- `products/tracker17/docs/what_left.md` on the branch's tree holds its heading, its lead sentence and `Nothing is left to build.`, and no entry.
