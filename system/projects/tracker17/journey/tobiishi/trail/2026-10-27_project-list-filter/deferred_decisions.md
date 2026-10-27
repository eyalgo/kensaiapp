# Deferred Decisions — project-list-filter

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## Sorting a task list — record gap, handed on by development-specs (2026-10-27)
**Record:** `fdr.md` R-89 to R-93; SRS FR-36; UXD UX-F5 (the sort field and direction)
**Product today:** no sort control; the list is always earliest due first, undated last, then by identity (`domain/tasks.py:372-380`)
**Why not this change:** the request rules it out: "no sorting", and "the list's order stays as it is today"
**Owner:** none — for shukuba-refine
**Status:** open

## The All tasks list and its header link — record gap, handed on by development-specs (2026-10-27)
**Record:** `fdr.md` R-81, second sentence; UXD UX-S7; SDD § 4 EX-12 and § 6 S-5 *Behaviour*
**Product today:** no list across projects and no All tasks link; the routes are the project, task and People pages only (`web/routes.py:98-116`)
**Why not this change:** the request rules it out: "no All tasks list or header link"
**Owner:** none — for shukuba-refine
**Status:** open

## The summary's overdue count agreeing with the filter, and its links into a filtered list — record gap, handed on by development-specs (2026-10-27)
**Record:** `fdr.md` R-99 (the summary's leg); SRS AC-13; UXD UX-F6
**Product today:** no summary page or route (`web/routes.py:98-116`)
**Why not this change:** the request rules it out: "no summary"; this change checks the list marking against the filter only (change_spec CP-415)
**Owner:** none — for shukuba-refine
**Status:** open
