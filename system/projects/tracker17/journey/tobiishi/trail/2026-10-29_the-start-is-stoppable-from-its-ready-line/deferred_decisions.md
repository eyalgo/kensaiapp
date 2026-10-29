# Deferred Decisions — the-start-is-stoppable-from-its-ready-line

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## The test suite's environment made by uv — record gap, handed on by development-specs (2026-10-29)
**Record:** SDD.md § 4 RT-4 (the suite's environment made by uv: `uv.lock` committed beside `pyproject.toml` in place of `tests/requirements.txt`, `uv sync --locked`, every suite command typed through `uv run`); nfdr.md QC-39 (`uv.lock` and `uv lock --check`, which the entry says "starts unmet") and § 10's preamble (suite commands typed through `uv run`)
**Product today:** the written setup instructions make the environment with `venv` and `pip` from `tests/requirements.txt` (`products/tracker17/README.md:97-99`); no `uv.lock` is tracked; `tests/architecture/test_pins.py:40` reads `tests/requirements.txt`
**Why not this change:** the requirement binds the suite's environment and its test dependencies, which this change leaves as they are — it adds and moves no test dependency — and QC-39 names the change that moves the product to RT-4 as the one that moves the pin test with the file. The request asks for the suites to run "in the product's own test environment as the setup instructions make it", which today is `venv` and `pip`.
**Owner:** none — for shukuba-refine
**Status:** open
