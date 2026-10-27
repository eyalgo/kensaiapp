# 根回し Nemawashi seed — narrowing and sorting a task list

## What it is

Serves the Way `fit-to-publish`, which `system/michi.md` Way 5 ranks above it; cut now because tracker17 is the product the owner runs the crew on (`products/tracker17/docs/PRD.md:L12-L14`), so it moves a product rather than machinery (my reasoning, not a lookup). After this, the operator can narrow a task list by status, priority, assignee, label, due-date range or overdue, sort it by one field, and do both within one project or across all projects. Moves the Agari toward **Works** for the first half of Key Use Case 4 and toward **Simple to read** for Filtering and Sorting, whose entry points (`domain/filtering.py`, `domain/sorting.py`, SDD § 4 TS-3) this slice adds.

Rests on SDD § 4 EX-3. Its bar is SDD § 6 S-5 *Reached when*: All tasks in the header with a project column and the moves on each row; filter and sort controls above both lists; Apply shows matches, sorted, with their count; the choices are in the address, so reload, back and bookmark agree; Clear; a reversed date range refused; a filter matching nothing says so; a task moved out of a filtered status leaves the list and the completion line names it; both suites pass, including SRS AC-14's filter and sort tests, AC-12's reversed range and the overdue filter agreeing with the marking on AC-13's three cases; `python3 tests/timed_run.py` exits 0 covering a filter and a sort. Priority sorts `low`, `medium`, `high`, `critical` (FDR R-90).

**Why it is here.** The PRD names these rules as the likeliest to drift (SDD § 6 S-5, *Why here in the order*), so they come as early as their inputs allow, right after `status-moves`.

## Source

Cut from `products/tracker17/docs/SDD.md` § 6 S-5, slug `narrow-and-sort` ("After this, the operator can narrow a task list by status, priority, assignee, label, due-date range or overdue"), and `products/tracker17/docs/fdr.md` R-90 for the four-value priority order. Product checked on 2026-10-11: `ls products/tracker17/domain/filtering.py products/tracker17/domain/sorting.py` reports both missing; `grep -rn -i "all tasks" products/tracker17/web products/tracker17/application` matches nothing. The work is still owed.

## Stations — dynamic checklist

- [ ] project-list-controls — filter and sort controls above a project's list, Apply, Clear, the match count, choices in the address, the no-match line, the reversed-range refusal
- [ ] all-tasks-list — All tasks across projects with a project column and the moves on each row, its empty state, and the not-found page's link to it
- [ ] filter-sort-tests — AC-14, AC-12's reversed range and AC-13's overdue agreement, a moved-out task leaving a filtered list with its completion line, and the timed run covering a filter and a sort

## Relation to existing work

Rests on `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project` and `tracker17 · nemawashi · 2026-10-07_status-moves` (SDD § 7, both `depends_on`: until moves exist every task is `todo`). `tracker17 · nemawashi · 2026-10-11_project-summary` rests on it. The new `critical` priority (FDR R-51) is carried by `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`, not here; this seed only sorts by it.

## Out (later / elsewhere)

The project summary and its links into a filtered list (`tracker17 · nemawashi · 2026-10-11_project-summary`). More than one value per filter field and sorting by more than one field, which the PRD places out of scope and no slice owns.
