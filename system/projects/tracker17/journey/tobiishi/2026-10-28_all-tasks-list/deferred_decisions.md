# Deferred Decisions — all-tasks-list

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## The project summary and its links into a filtered list — record gap, handed on by development-specs (2026-10-28)
**Record:** UXD UX-F6 and UX-S5; SRS FR-38; `fdr.md` R-96 to R-99; SDD § 6 S-6
**Product today:** no summary page or route; the routes are the Projects, project, task and People pages and their submissions (`web/routes.py:105-123`)
**Why not this change:** the request rules it out: "The project summary and its links into a filtered list are a later seed and are not here."
**Owner:** none — for shukuba-refine
**Status:** open
