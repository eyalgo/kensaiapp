# Deferred Decisions — out-of-date-move

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## A refused press's landing page, reopened by a reload, Back or a bookmark — record gap, handed on by development-specs (2026-10-21)
**Record:** `docs/CONTENT.md` RN-26: "A refusal shown after a redirect from a real press and then reloaded has the same property. No occurrence is cited for it, so it waits until one occurs."
**Product today:** the landing address carries the refusal, and reopening it shows the same line again (`web/routes.py:378-391`; fdr R-106, PD-11). Today that line is "the move you pressed". After this change it is the overtaken press's line, which says the status has changed (change_spec CP-359).
**Why not this change:** the request names two refusals, the overtaken press and the one reached by a confirmation or back-out address. The landing address of a refused press is neither, and CONTENT.md itself defers it until an occurrence is cited. This change's landing page is now such an occurrence.
**Owner:** none — for shukuba-refine
**Status:** open
