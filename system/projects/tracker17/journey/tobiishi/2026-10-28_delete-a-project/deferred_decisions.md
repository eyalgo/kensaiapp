# Deferred Decisions — delete-a-project

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## A project submission for a deleted project answered by a redirect — record gap, handed on by development-specs (2026-10-28)
**Record:** `products/tracker17/docs/SDD.md` § 4 RT-11: "a submission naming a deleted target is answered by a redirect to that address and saves nothing (`delete-and-rename`'s deleted-target refusals)".
**Product today:** adding a task and the rename, sent for a project no project holds, answer the not-found page directly, 404, with no redirect, and save nothing: `products/tracker17/web/routes.py:805-807` and `:834-836`, `if project is None: return self._not_found_page()`. Probed at `e9c600016` (`change_spec.md` § Verified Claims).
**Why not this change:** this change leaves both submissions as they are. It only adds a deleted project as new data that reaches their existing refusal. The request asks only that such an action "is refused and changes nothing", which both already do. The two presses this change adds are built to the redirect (`change_spec.md` CP-582).
**Owner:** none — for shukuba-refine
**Status:** open
