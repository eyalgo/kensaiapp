# Deferred Decisions — rename-a-project

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## Deleting a project — record gap, handed on by development-specs (2026-10-28)
**Record:** `products/tracker17/docs/fdr.md` R-37, R-38; SRS FR-13; UXD UX-F10 and UX-S4, "the rename and delete controls"; SDD § 6 S-7 *Behaviour*.
**Product today:** no project can be deleted. The route table at `products/tracker17/web/routes.py:114-133` holds no project deletion route, and the Tasks view offers no Delete project control.
**Why not this change:** the request rules it out: "Deleting a project … not part of this change".
**Owner:** none — for shukuba-refine
**Status:** open

## The slice's docstring bar — record gap, handed on by development-specs (2026-10-28)
**Record:** SDD § 6 S-7 *Artifact*: "The opening docstrings of `domain/projects.py` and `domain/tasks.py` name the tests this slice adds."
**Product today:** the opening docstring at `products/tracker17/domain/projects.py:1-13` names the tests of creating and listing projects, ending with `tests/e2e/test_first_project.py`, and no test of the slice's rename or project deletion.
**Why not this change:** the request rules it out: "the `domain/projects.py` / `domain/tasks.py` docstring bar … not part of this change". NFDR QC-11 still holds for what this change adds (`change_spec.md` CP-568).
**Owner:** none — for shukuba-refine
**Status:** open
