# Deferred Decisions — project-list-sort

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## The All tasks list, its filter and sort controls, and its header link — record gap, handed on by development-specs (2026-10-27)
**Record:** `fdr.md` R-81, second sentence; UXD UX-S7; SDD § 4 EX-12 and § 6 S-5 *Behaviour*
**Product today:** no list across projects and no All tasks link; the routes are the project, task and People pages only (`web/routes.py:102-119`)
**Why not this change:** the request rules it out: "no All tasks list or header link"
**Owner:** none — for shukuba-refine
**Status:** open

## The project summary and its links into a filtered list — record gap, handed on by development-specs (2026-10-27)
**Record:** UXD UX-F6; SRS FR-38
**Product today:** no summary page or route (`web/routes.py:102-119`)
**Why not this change:** the request rules it out: "no summary"
**Owner:** none — for shukuba-refine
**Status:** open
