# Deferred Decisions — deleted-project-redirect

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## A submission naming a number too long to read as an identity is answered by a redirect — record gap, handed on by development-specs (2026-10-28)
**Record:** `products/tracker17/docs/nfdr.md` QC-7 ("every submission is answered by sending the browser to a page address"), and ADR-0011, which it traces to.
**Product today:** a submission whose route number is too long for the tracker to read as an identity, such as 5,000 nines, is answered with the not-found page directly, `404`, no `Location`. Add task and Rename do this at `products/tracker17/web/routes.py:869-870` and `:898-899`, reached when `_identity` at `:402-407` reads no identity; a task's submissions do the same, e.g. the edit at `:931-933`. Delete project's presses alone redirect it, to the raw digits (`:1117-1121`).
**Why not this change:** the change alters the answer for a project the tracker reads as an identity and does not hold. The answer for a number it cannot read stays as it is, and such a number never names a deleted project, which is all the request asks about.
**Owner:** none — for shukuba-refine
**Status:** open
