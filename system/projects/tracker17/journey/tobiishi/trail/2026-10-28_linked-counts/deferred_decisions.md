# Deferred Decisions — linked-counts

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## The unreadable-saved-data page, for the Summary and the lists its counts open — record gap, handed on by development-specs (2026-10-28)
**Record:** `docs/fdr.md` R-25 and R-26: every page says the saved data couldn't be read, and offers no action and no navigation into any other area. UXD UX-S9.
**Product today:** on unreadable saved data the tracker prints the message and exits 1 without serving any page (`main.py:39-48`).
**Why not this change:** the request rules it out: "Out of scope: … the unreadable-data page (`protect-saved-data`)". The request names that station as its owner.
**Owner:** none — for shukuba-refine
**Status:** open

## CP-525's zero-count fixture placement — reading set aside by development-design (2026-10-28)
**Spec lines:** `change_spec.md:56`, CP-525: "The project must have at least one zero status or priority count" — the requirement that this be the same project used for the full-membership assertions.
**Conflict:** `change_spec.md:51`, CP-525 requires tasks in every status and every priority in that project. A populated bucket in every category cannot also have a zero in one of those categories. The spec's Examples instead put full membership on Alpha and the zero done count on populated Beta. No existing product contract is released by choosing between those fixture placements.
**Reading taken:** Alpha retains every status/priority and the complete assignee/due-date fixture. Populated Beta supplies the zero status, priority and overdue link cases, alongside Gamma's no-tasks case. This delivers the request's AC-14 link-to-membership proof and the zero-link no-match proof without losing any category or changing the Tasks view. The alternatives — omitting one Alpha category, or requiring both contradictory fixture properties together — are not carried.
**Owner:** none — for shukuba-refine
**Status:** open
