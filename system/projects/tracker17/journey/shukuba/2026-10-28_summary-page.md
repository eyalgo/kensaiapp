# 宿場 Shukuba — a project's summary page, counts as plain numbers

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-11_project-summary`. Slug: `summary-page`.*

## What it is

A project gains a Summary view beside its task list. The project's pages carry Tasks and Summary links, and each page's title names its view (`Alpha: Tasks - tracker17`, `Alpha: Summary - tracker17`, per `products/tracker17/docs/CONTENT.md` page titles). The summary shows the total, a count per status and per priority (four: `low`, `medium`, `high`, `critical`) with zeros shown, the overdue count, the count with no due date, and the open tasks per assignee (a row for every listed name, every unlisted name an open task still carries, and "(unassigned)"), all as plain numbers. An empty project shows zeros and invites a first task. The rules live in a new `domain/summary.py`. It is one capability and one merge; the counts becoming links into filtered lists is the next station, which is why this one stops at plain numbers.

## Reached when

1. `products/tracker17/domain/summary.py` exists.
2. `pytest products/tracker17/tests/` exits 0, and the suite holds a summary test that builds one project exercising each row (tasks across every status and priority, an overdue task, a task with no due date, a listed assignee, an unlisted name on an open task, and an unassigned task) and asserts every count it shows.
3. Opening `Alpha`'s Summary in the running app shows the total, each status and priority count (zeros included), the overdue count, the no-due-date count and the per-assignee rows, each as a plain number; opening an empty project shows zeros and the first-task invitation.
4. A project's task list and its summary each carry a Tasks and a Summary link to the other, and the page titles read `Alpha: Tasks - tracker17` and `Alpha: Summary - tracker17`.

## Guardrail

- The counts stay plain numbers; no count links anywhere. Linking is the next station's work.
- No second copy of the overdue, filter or sort rules: `domain/summary.py` reuses `domain/filtering.py` and the existing overdue marking.
- Existing pages, strings and timed actions in `tests/timed_run.py` keep working; the timed run is extended at the next station, not here.

- **Not here:** `tracker17 · nemawashi · 2026-10-11_project-summary` item 2, `linked-counts` (links from counts, AC-13 agreement, timed summary), and a summary across projects, which the PRD places out of scope.
