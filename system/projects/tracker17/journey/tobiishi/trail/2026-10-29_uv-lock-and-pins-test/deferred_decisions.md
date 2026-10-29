# Deferred Decisions — uv-lock-and-pins-test

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## The README's suite instructions on uv — record gap, handed on by development-specs (2026-10-29)
**Record:** SDD § 4 RT-4 (the suite section says to install uv first and gives `uv sync --locked` and `uv run`) and § 6's preamble; ADR-0013 § Decision.
**Product today:** `products/tracker17/README.md:95-103` gives `python3 -m venv .venv`, `source .venv/bin/activate` and `python -m pip install -r tests/requirements.txt`. After this change the file that last line names no longer exists. `:135` names "a virtual environment made with Python's `venv`".
**Why not this change:** the request rules it out: "The README's suite section and its 'How it's built' line, and the project card's Setup and Test commands, are the next two stations'".
**Owner:** none — for shukuba-refine
**Status:** open
