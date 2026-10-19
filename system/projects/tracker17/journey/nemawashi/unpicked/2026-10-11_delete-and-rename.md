# 根回し Nemawashi seed — deleting, and renaming a project

## What it is

Serves the Way `fit-to-publish`, which `system/michi.md` Way 5 ranks above it; cut now because tracker17 is the product the owner runs the crew on (`products/tracker17/docs/PRD.md:L12-L14`), so it moves a product rather than machinery (my reasoning, not a lookup). After this, the operator can delete a task, rename a project, and delete a project together with its tasks. Completes the Projects and Tasks features toward the Agari's **Works** bar, and toward **Simple to read** by completing those features' traces: their entry points name the tests this slice adds.

Rests on SDD § 4 EX-6 and EX-13. Its bar is SDD § 6 S-7 *Reached when*: Delete task behind the in-place confirmation, landing on the task's project with a line naming it; Rename below a project's list, refusing a blank name or one in use; Delete project behind a confirmation naming the project and its task count, landing on Projects with a line naming it, and holding below a list long enough to scroll; a deleted project's tasks in no list; the address of anything deleted shows the not-found page; an action sent from another tab for something already deleted is refused and changes nothing; both suites pass, including FR-13 and FR-17 (tasks and comments gone), FR-15 (a deleted task's identity not issued again), FR-12 (rename leaves tasks unchanged) and AC-12's deleted-target refusals; an end-to-end test of Delete project's confirmation below a scrolled list (opens in view, focus on its sentence, a double press never confirms); `python3 tests/timed_run.py` exits 0 covering a deletion.

**Why it is here.** The SDD says it could sit anywhere after `tasks-in-a-project`; placing it after `status-moves` (reuses the confirmation) and `comment-on-a-task` (deletion checked with comments present) are preferences, not dependencies (SDD § 6 S-7, *Why here in the order*). So it can be picked before them if the owner wants.

## Source

Cut from `products/tracker17/docs/SDD.md` § 6 S-7, slug `delete-and-rename` ("After this, the operator can delete a task, rename a project, and delete a project together with its tasks"). Product checked on 2026-10-11: `grep -rn -i "rename\|delete" products/tracker17/web products/tracker17/application` matches no rename or delete action. The work is still owed.

## Stations — dynamic checklist

- [ ] delete-a-task — Delete task with the in-place confirmation, the landing line, the not-found address and the deleted-target refusal, and the timed run covering a task delete (NFDR QC-48)
- [ ] rename-a-project — Rename below a project's list with its blank and in-use refusals, and a test that tasks stay unchanged, and the timed run covering a rename (NFDR QC-48)
- [ ] delete-a-project — Delete project with its confirmation and scrolled-list end-to-end test, tasks and comments gone, and the timed run covering a deletion

2026-10-13, shukuba-refine after `tracker17` unit `2026-10-13_full-volume-run`: `delete-a-task` and `rename-a-project` each also add their action to the timed run. QC-48 has a change that adds a listed action add it to the run (`products/tracker17/docs/nfdr.md:L412-L414`), and that unit's spec left deleting a task and renaming a project to the station that builds each; only `delete-a-project` carried a timing.

## Relation to existing work

Rests on `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project` (SDD § 7, `depends_on`). Reuses the confirmation built in `tracker17 · nemawashi · 2026-10-07_status-moves` (`hands_off_to`) and checks deletion against `tracker17 · nemawashi · 2026-10-07_comment-on-a-task`'s comments; both are preferences. If it is picked before `status-moves`, the confirmation is built here and that seed reuses it: say so in the seed that goes second.

## Out (later / elsewhere)

Moving a task to another project, which SRS FR-14 excludes and no slice owns. Changing a project's description, which UXD § 10 excludes.
