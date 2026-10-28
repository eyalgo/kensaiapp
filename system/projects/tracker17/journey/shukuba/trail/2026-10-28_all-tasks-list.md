# 宿場 Shukuba — an All tasks list across every project, with the filter and sort controls

*Item 3 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-11_narrow-and-sort`. Slug: `all-tasks-list`.*

## What it is

The header gains All tasks, and the not-found page links to it beside Projects (UXD UX-S10). All tasks (UX-S7) lists every task across every project with a project column linking to each task's project, the moves on each row that a project's rows carry, and no add-task form (a task is created in a project). The filter and sort controls the two earlier stations built for a project's list sit above it and work across all projects: Apply, Clear, the count, the choices in the address, the reversed-range refusal and the no-match line (FR-31 to FR-37). The assignee filter offers the names on the list and the label filter the labels carried across all projects. With no tasks anywhere the page says so and links to Projects. This is SDD § 6 S-5's closing bar and the last station of the seed; it reuses `domain/filtering.py` and `domain/sorting.py` and adds no new rule.

## Reached when

1. Every page's header has an All tasks link, and the not-found page links to both Projects and All tasks: `grep -rn -i 'all tasks' products/tracker17/web` (case-insensitive, fixed by `-i`) matches nothing before this station, so a match in `web/pages.py` and a page test showing the link in the header and on the not-found page are new.
2. In a browser or through `web`, All tasks shows every task of every project, each row with a project column linking to its project, and the status moves a project's rows offer; moving a task there changes its status as in its project and shows All tasks again. The page has no add-task form.
3. With no tasks anywhere, All tasks says there are no tasks yet and links to Projects.
4. On All tasks, Apply with a filter, a sort, or both shows only the matches in the sort order FR-36 defines, with the match count and the choices still shown; the choices appear in the address, so a reload shows the same list; Clear returns every task in due-date ascending order; a from-date after the to-date is refused with FR-34's reason; a filter matching nothing says so and shows Clear; the assignee filter offers the names on the list and the label filter the labels carried by tasks in any project.
5. `pytest products/tracker17/tests/` exits 0, with tests for lines 1 to 4, including AC-14's filter and sort tests run across projects and a task moved out of a filtered status leaving All tasks with the completion line naming it (UX-F4).
6. `python3 products/tracker17/tests/timed_run.py` exits 0 and its output still shows the `filter total at 1000 tasks` and `sort total at 1000 tasks` lines under `LIMIT_SECONDS`.

## Guardrail

- All tasks only: no project summary and no links into a filtered list, no summary across projects (SRS: All tasks has no summary view), no add-task form.
- The filter's and sort's rules stay as `domain/filtering.py` and `domain/sorting.py` hold them; the station reuses them and does not fork a second copy for All tasks.
- One value per filter field and one sort field, as the PRD puts more out of scope; the choice is carried in the address and not remembered between sittings (UX-I7).
- The limit and every existing timed action stay as they are.

- **Not here:** the project summary and its links into a filtered list, `tracker17 · nemawashi · 2026-10-11_project-summary`.
