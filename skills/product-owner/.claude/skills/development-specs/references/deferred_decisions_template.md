---
version: "1.3.1"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# Deferred Decisions — <slug>

What this change held back, for `shukuba-refine` to place after the unit lands. Four kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7);
- a **packet departure** — code a language packet line forbids, which this change could not fix without leaving its scope or its `Behaviour` (development-design Pre-flight, development-plan Step 2, development-implementation Step 1b, development-code-integrity § *When to STOP*). Code that builds its own collaborator, and a unit test that touches a real resource, are never one: the stage that meets them fixes them (`<CORE>/doctrine/engineering/languages/README.md` § *A fix that hands a collaborator in is not a topology decision*).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation, development-code-integrity) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## <element> — direction, deferred by <stage> (YYYY-MM-DD)
**Request fragment:** <the casual ask that triggered this>
**Why deferred:** <reversibility reason — e.g. "clear" could mean permanent delete (data loss) or archive; the request says neither, and the destructive reading is irreversible>
**Options seen:** <the candidate directions that were on the table>
**Owner:** none — for shukuba-refine
**Status:** open

## <behaviour> — record gap, handed on by <stage> (YYYY-MM-DD)
**Record:** <document and item, e.g. fdr.md R-25>
**Product today:** <what the product does instead, with file:line — where the change carries code over, what that code does>
**Why not this change:** <the behaviour the requirement binds, which this change leaves as it is, and that the request does not ask for it — or the request's words ruling it out>
**Owner:** none — for shukuba-refine
**Status:** open

## <spec lines> — reading set aside by <stage> (YYYY-MM-DD)
**Spec lines:** <the change_spec.md rules or Examples not carried, by id>
**Conflict:** <what they conflict with — the existing test or present behaviour, cited>
**Reading taken:** <the reading designed to, and why it delivers the request>
**Owner:** none — for shukuba-refine
**Status:** open

## <code site> — packet departure, handed on by <stage> (YYYY-MM-DD)
**Packet line:** <concern file and line, the clause quoted>
**Code:** <the site that departs from it, with file:line>
**Why not this change:** <what the fix needs that this change may not do — e.g. a changed importable signature on a `Behaviour: preserving` change>
**Owner:** none — for shukuba-refine
**Status:** open
