# 根回し Nemawashi seed — comments under the operator's name

## What it is

Serves the Way `fit-to-publish`: the Comments feature is one of the entry points a reader traces from the product definition to its code (`products/tracker17/README.md:L3-L5`). After this, the operator can set their own name and comment on a task, and each comment shows under the name it was written with and the time it was written. Moves the Agari toward **Works** for Key Use Case 5 and toward **Simple to read** for the Comments feature (`domain/comments.py`).

Rests on SDD §§ 3 (Comment and Operator name entities) and 4. Its bar is SDD § 6 S-3 *Reached when*: Your name on People; comments oldest first with author and local time; the new comment in view with focus after Add; refusals that keep the typed text; no edit or delete control; both suites pass, including SRS AC-6 with every field and AC-20's full test; `tests/timed_run.py` exits 0 with 1,000 tasks of 20 comments each.

**Why it is here.** It could be built at any point after tasks; the SDD places it third because it brings the saved data to SRS NFR-1's full volume, the measurement most able to overturn how the saved data is written (§ 6 S-3, *Why here in the order*; § 9 TO-3). That is a risk reason, not a dependency.

## Source

Cut from `products/tracker17/docs/SDD.md` § 6 S-3, slug `comment-on-a-task` ("After this, the operator can set their own name and comment on a task"). Product re-checked on 2026-10-12, after `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project` was walked: `domain/comments.py` does not exist (`ls products/tracker17/domain` lists `__init__.py assignees.py due_dates.py labels.py priorities.py projects.py refusals.py state.py tasks.py text.py`). The work is still owed.

## Stations — dynamic checklist

- [x] operator-name — Your name on People sets or changes the saved name, refuses a blank one with the typed text kept, and says beside the field that written comments keep their name; the integration and end-to-end tests for People pass
- [x] comments-on-the-page — a task's page lists comments oldest first with author and local time and adds one under the saved name, with the no-name notice and both refusals keeping the typed text, no edit or delete control, earlier comments keeping the earlier name after a rename, the in-view-with-focus and `maxlength` tests, AC-20's comment test, saved data breaking a comment rule reported unreadable at start (SD-5), and `domain/comments.py` present; `pytest products/tracker17/tests/` exits 0
- [x] full-volume-run — `python3 tests/timed_run.py` exits 0 with its comment add and that add's landing page each under the limit at 1,000 tasks of 20 comments each, and the People assignee add and remove each timed under the same limit (NFDR QC-48), checked by `tests/integration/test_timed_run.py`

2026-10-11, shukuba-refine after `tracker17` unit `add-and-list-tasks`: `comments-on-the-page` gains SD-5's start check for a saved comment. That unit's spec handed the check to this seed, and SD-5 has each slice that adds a data rule test it (`products/tracker17/docs/SDD.md:L392-L395`).

2026-10-12, shukuba-refine after `tracker17` unit `edit-task-fields`: § Out names `delete-and-rename` by its seed, `tracker17 · nemawashi · 2026-10-11_delete-and-rename`, which is now cut.

2026-10-12, stations-from-seed: three stations kept, in the same order (`operator-name` is a hard dependency of the comment form; `full-volume-run` needs the comment action). Reached-whens written out. The rule that earlier comments keep the earlier name moved from `operator-name` to `comments-on-the-page`, because it cannot be shown before a comment exists. `full-volume-run` narrowed to timing the comment add: the 1,000 × 20 fixture is already seeded (`products/tracker17/tests/timed_run.py:L11`, `L60`, `L175`).

2026-10-12, shukuba-refine after `tracker17` unit `operator-name`: `full-volume-run` also times the People assignee add and remove. QC-48 has a change that adds a listed action add it to the run, the assignee change did not, and the unit handed the gap on with no owner (`timed_run.py` `main` times tasks, edits, labels and the name only).

## Relation to existing work

Rests on `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`. It also tests, rather than rests on, `tracker17 · nemawashi · 2026-10-07_first-project`: its timed run exercises the whole-state save that slice introduces (SDD § 7, `validates`). A failure there is a finding about that seed's design (ADR-0004), not about this one.

## Out (later / elsewhere)

Deleting a task together with its comments (`tracker17 · nemawashi · 2026-10-11_delete-and-rename`). Threaded replies, which the PRD places out of scope.
