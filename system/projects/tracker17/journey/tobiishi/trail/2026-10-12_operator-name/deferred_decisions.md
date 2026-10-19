# Deferred Decisions — operator-name

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## Pages served while saved data is unreadable — record gap, handed on by development-specs (2026-10-12)
**Record:** `products/tracker17/docs/fdr.md` R-25, R-26 (SRS FR-8; SDD § 3 SM-6, § 4 EX-12)
**Product today:** the start refuses and returns before any listener exists, so no page is served for any unreadable data (`products/tracker17/main.py:39-48`).
**Why not this change:** the requirement binds the unreadable-data mode, which this change leaves as it is. A broken operator name only widens when the existing start refusal happens (change_spec CP-228). The request asks for an unreadable start, not for that mode. SDD § 6 S-8 `protect-saved-data` cuts it.
**Owner:** none — for shukuba-refine
**Status:** open

## Comments on a task — record gap, handed on by development-specs (2026-10-12)
**Record:** `products/tracker17/docs/fdr.md` R-71 to R-75 (SRS FR-28 to FR-30; UXD UX-F7, UX-S6)
**Product today:** a task's page has no comment form or list (`products/tracker17/web/pages.py:818`, `task_page`, builds no comment area); comments are carried in saved data as a structural value with no rule (`products/tracker17/domain/tasks.py:66-72`).
**Why not this change:** the request rules it out: "Nothing about comments is built here". It names `tracker17 · nemawashi · 2026-10-07_comment-on-a-task`, item 2 `comments-on-the-page`, as the place.
**Owner:** none — for shukuba-refine
**Status:** open

## Timing the assignee add and remove — record gap, handed on by development-specs (2026-10-12)
**Record:** `products/tracker17/docs/nfdr.md` QC-48 ("a change that adds a listed action adds it to the run"); SRS NFR-1 ("every operator action")
**Product today:** `products/tracker17/tests/timed_run.py:1-17` times project creation, a task add, a task edit and the label add and remove, and no People action.
**Why not this change:** this change adds the name save to the run (change_spec CP-237) and adds no assignee action. The `2026-10-11_people-page-assignee-list` change left the two assignee actions out of the run.
**Owner:** none — for shukuba-refine
**Status:** open


## CP-239 verification copy — reading set aside by development-design (2026-10-12)
**Spec lines:** CP-239's archive/init method and its final Example (`change_spec.md:L100-L102`, Tests, and `L141-L141`, Examples).
**Conflict:** `core/roles/CROSS_ROLE.md:L12-L24`, “Every seat — a run leaves the product's main checkout as it found it”, requires a disposable clone checked out at the tested commit for checks outside the change worktree. It explicitly rejects an archive because checks may read history. The spec and request prescribe an initialized archive instead.
**Reading taken:** preserve every named command and its zero-exit gate; use a disposable clone at the explicit tested SHA for checks outside the change worktree. The clone is a Git repository and retains the saved-data ignore check, which `products/tracker17/tests/integration/test_start.py` `test_data_is_ignored_by_version_control` exercises. The archive/init reading is set aside only as a verification procedure, with no change to operator behavior or acceptance.
**Owner:** none — for shukuba-refine
**Status:** open
