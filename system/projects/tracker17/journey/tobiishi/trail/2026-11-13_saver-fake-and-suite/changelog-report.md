# Changelog report — 2026-11-13_saver-fake-and-suite

## Change

- Change key `2026-11-13_saver-fake-and-suite`, project `tracker17`, own product path `products/tracker17` in the instance repository.
- Considered changelog: `products/tracker17/CHANGELOG.md`, in the instance repository — it is the own product path's, and every changed path under `products/` lies under that product path. The other changed paths, the change's record under `system/projects/tracker17/journey/`, lie under no product path and are no listed root file.
- The path tool refused no project card. One card, `tracker16-X`, resolves to another repository, which does not hold the change's branch, so it gives no product path here.

## Changelog

The change earns no entry, because it alters nothing a user of a fresh clone installs, runs, types or reads at any product path this run considered.

- `products/tracker17/CHANGELOG.md`, instance repository — no entry: the branch changes only test code under `products/tracker17/tests/` (a `Saver` fake, its contract suite and 33 test modules moved onto it); production code, the launch command and every user-facing file are unchanged.

## What-left

No entry in `products/tracker17/docs/what_left.md` is wholly built by the change, so the run removed none. Its one entry, "The project summary shows how many of the project's open tasks are due today, beside the overdue count.", is untouched: the branch changes no product code.

## Evidence

- Branch commits read: `cf9d1fe7c` through `<a commit not in the public history>` (spec, design, instruction, tasks 1–24 and the implementation-complete commit), all on `2026-11-13_saver-fake-and-suite`.
- The diff from `main` over `products/tracker17` touches only `tests/fakes.py` and modules under `tests/integration/`; `<a commit not in the public history>`'s body records the diff over the product, tests excluded, as empty.
