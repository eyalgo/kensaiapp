# Deferred Decisions — history-after-confirm

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## A move refusal reached with no press, worded as a fact about the task — record gap, handed on by development-specs (2026-10-20)
**Record:** `docs/CONTENT.md` version 12, § Message patterns, Error (a refusal the reader reached "by a reload, Back, or a saved or typed address" states its reason as a fact about the task, never about a press, and "names the move the address asks for"), and RN-26; `docs/UXD.md` UX-I3 ("A refusal reached by an address and no control is a case of its own"), UX-F4 (the second way a move refusal arises) and RN-33.
**Product today:** every move refusal says "…which doesn't allow the move you pressed." (`web/pages.py:760`), including the one a fresh load of a confirmation's address shows once the task is `done` or `cancelled`. `tests/e2e/test_moves.py:130-137` pins those words. After this change, Back to that address shows the same refusal in place of the cached confirmation (change_spec CP-343, which pins no words).
**Why not this change:** the refusal page for that address exists today, reached by a reload or a bookmark. This change only widens when it is reached, so Back now gets it, and it leaves its words as they are. The request asks for "the saved-status refusal" and does not ask for new words.
**Owner:** none — for shukuba-refine
**Status:** open
