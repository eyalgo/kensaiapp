# Changelog report — 2026-11-13_summary-shows-due-today

## Change

The change key is `2026-11-13_summary-shows-due-today`, made under the project tracker17. The change's own product path is `products/tracker17`, in the instance repository.

The run considered one changelog. `products/tracker17/CHANGELOG.md`, in the instance repository, is the own product path's changelog, and the branch's changed product files all lie under `products/tracker17`. The branch also changes files under `system/projects/tracker17/journey/`, which sit under no product path and are no listed root file. The path tool refused no project card.

## Changelog

`products/tracker17/CHANGELOG.md`, in the instance repository: one entry written under `### Added`, citing `c8dd2026d` and `1bbe99203`. The entry says that a project's Summary shows the count of its open tasks due on the summary's date, in a `Due on {date}` row right after Overdue.

## What-left

The run removed the want "The project summary shows how many of the project's open tasks are due today, beside the overdue count." from `products/tracker17/docs/what_left.md`. Its whole want is built at `1bbe99203`, the commit that adds the `Due on {date}` row beside Overdue on the Summary page. That commit's first parent `32bfdb0ee` shows no such row. It was the file's last entry, so the file now holds the line `Nothing is left to build.`

## Evidence

- `c8dd2026d` (task 1 green) adds the `today` and `due_today` fields to `ProjectSummary` in `products/tracker17/domain/summary.py`, and counts the open tasks due on the summary's date.
- `1bbe99203` (task 2 green) adds the `Due on {date}` row, as a plain number between Overdue and No due date, to the Summary page in `products/tracker17/web/pages.py`. `git show 32bfdb0ee:products/tracker17/web/pages.py` holds no `Due on`, and `git show 1bbe99203:products/tracker17/web/pages.py` holds it.
- Both commits are reachable from branch `2026-11-13_summary-shows-due-today` (`git merge-base --is-ancestor`).
