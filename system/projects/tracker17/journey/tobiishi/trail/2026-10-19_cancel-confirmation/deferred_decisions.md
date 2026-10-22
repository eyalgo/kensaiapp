# Deferred Decisions — cancel-confirmation

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## An out-of-date first press or confirming press that says the status has changed and offers a reload — record gap, handed on by development-specs (2026-10-19)
**Record:** `docs/UXD.md` UX-I3 ("A refusal caused by the page being out of date … says so and offers a reload") and UX-F4, failure and recovery; `docs/SDD.md` § 6 S-4 *Reached when* ("A move made from a page that is out of date is refused, says the status has changed, and offers a reload"); `docs/CONTENT.md` § Message patterns, Error, the fifth refusal example.
**Product today:** a refused move gives the task's saved status and a tail per status, and offers no reload (`web/pages.py:623-646`). After this change, a stale first press on `cancelled` or a stale confirming press is refused against the saved status with that same kind of reason (change_spec CP-331, CP-332).
**Why not this change:** the request rules it out: "There is no out-of-date-move handling". The seed's `out-of-date-move` line names this work.
**Owner:** none — for shukuba-refine
**Status:** open

## The in-place confirmation for deleting a task and deleting a project — record gap, handed on by development-specs (2026-10-19)
**Record:** `docs/UXD.md` UX-I2 (deleting a project and deleting a task each take a confirming press, in place); `docs/SDD.md` § 4 EX-6; `docs/CONTENT.md` § Needs confirming, the three delete examples ("Delete project", "Delete task").
**Product today:** no delete control exists (`grep -n -i "delete" web/routes.py web/pages.py` finds none). After this change, the confirmation exists for the move to `cancelled` only, stated with nothing particular to moves beyond its words and what it saves (change_spec CP-335).
**Why not this change:** the request rules it out: "Deleting a task or a project gets no confirmation here; the confirmation built must be reusable by that work but is not extended to it." The seed `2026-10-11_delete-and-rename` names this work.
**Owner:** none — for shukuba-refine
**Status:** open

## The overdue effect of a move to `cancelled` on the overdue filter, the summary count and the All tasks list — record gap, handed on by development-specs (2026-10-19)
**Record:** `docs/fdr.md` R-88, R-96, R-99; `docs/SRS.md` AC-13 ("The list marking, the overdue filter and the summary count agree on all three").
**Product today:** none of the three views exists. The one task list is a project's own (`web/pages.py:703-720`). After this change, a task confirmed to `cancelled` loses its "Overdue" marking on its row (change_spec CP-328).
**Why not this change:** each requirement binds a view this change leaves as it is, because that view is not built, and the request does not ask for it. The allowed-moves unit handed on the same gap for `done`, and its owners are the seeds `2026-10-11_narrow-and-sort` and `2026-10-11_project-summary`.
**Owner:** none — for shukuba-refine
**Status:** open
