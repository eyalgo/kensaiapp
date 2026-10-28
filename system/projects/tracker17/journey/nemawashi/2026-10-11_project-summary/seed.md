# 根回し Nemawashi seed — the project summary

## What it is

Serves the Way `fit-to-publish`, which `system/michi.md` Way 5 ranks above it; cut now because tracker17 is the product the owner runs the crew on (`products/tracker17/docs/PRD.md:L12-L14`), so it moves a product rather than machinery (my reasoning, not a lookup). After this, the operator can open a project's summary to see where it stands and step from a count into the list of tasks it counts. Completes Key Use Case 4 toward the Agari's **Works** bar, and adds the Project summary entry point (`domain/summary.py`, SDD § 4 TS-3) toward **Simple to read**.

Rests on SDD § 3. Its bar is SDD § 6 S-6 *Reached when*: a project gains Tasks and Summary links; the summary shows the total, a count per status and per priority with zeros shown, the overdue count, the count with no due date, and each assignee's open tasks (a row for every listed name, every unlisted name still on an open task, and "(unassigned)"); each status, priority and overdue count links to the project's list filtered to that value; an empty project shows zeros and invites a first task; both suites pass, including SRS AC-14's summary test on a project built to exercise each row, and the overdue count agreeing with the marking and the filter on AC-13's three cases; `python3 tests/timed_run.py` exits 0 covering opening a summary. The priority counts are four (`low`, `medium`, `high`, `critical`; FDR R-51).

**Why it is here.** Its linked counts open lists only `narrow-and-sort` can show (SDD § 6 S-6, *Why here in the order*).

## Source

Cut from `products/tracker17/docs/SDD.md` § 6 S-6, slug `project-summary` ("After this, the operator can open a project's summary to see where the project stands"). Product checked on 2026-10-11: `ls products/tracker17/domain/summary.py` reports it missing. The work is still owed.

## Stations — dynamic checklist

- [x] summary-page — a project gains Tasks and Summary links, its page title takes its view (`Alpha: Tasks - tracker17`, CONTENT.md page titles), and the summary shows total, status and priority counts with zeros, overdue, no-due-date and per-assignee rows as plain numbers, an empty project showing zeros and inviting a first task; `domain/summary.py` exists and `pytest products/tracker17/tests/` exits 0 with a summary test on a project built to exercise each row
- [x] linked-counts — each status, priority and overdue count links to the project's list filtered to that value (the other counts stay plain), with AC-14's summary test covering the links; the AC-13 agreement test and the timed summary, landed with `summary-page`, still pass with `pytest products/tracker17/tests/` and `python3 products/tracker17/tests/timed_run.py` exiting 0

2026-10-28, shukuba-refine after `tracker17` unit `2026-10-28_summary-page`: `linked-counts` no longer carries the AC-13 agreement test or the timed summary as new work. That unit's spec folded both in (Locked Answers e-1, e-2), and they landed: `tests/integration/test_summary_routes.py:L76` and `tests/timed_run.py:L140-L145`. The station keeps them as checks that must still pass.

2026-10-28, stations-from-seed: the cutter's two-station route kept. `summary-page` and `linked-counts` each deliver one working state in one merge, and the filtered lists the links open already exist (`narrow-and-sort` and `all-tasks-list` both sealed). Only the reached-whens are sharpened, and the S-6 bar's tests and timed run sit on `linked-counts`, the last station, which carries the seed's own bar.

2026-10-11, shukuba-refine after `tracker17` unit `add-and-list-tasks`: `summary-page` gains the project page's title with its view. That unit's spec handed the title to the Tasks and Summary links. CONTENT.md's page-title rule names the view where a page has views (`products/tracker17/docs/CONTENT.md:L378-L381`), and today the title is the bare project name (`products/tracker17/web/pages.py:L1506`; it was `L630` when the note was written).

## Relation to existing work

Rests on `tracker17 · nemawashi · 2026-10-11_narrow-and-sort`, walked and retired to `trail/` (SDD § 7, `depends_on`: the counts link into its lists, which now exist), and through it on `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project` and `tracker17 · nemawashi · 2026-10-07_status-moves`.

## Out (later / elsewhere)

A summary across projects, which the PRD places out of scope and no slice owns.
