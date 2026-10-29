# Deferred Decisions — project-card-commands

What this change held back, for `shukuba-refine` to place after the unit lands. Each entry is stamped with the stage that wrote it.

**Collection, read after the unit lands.** Later stages append their own entries. `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Each entry fills only the fields of its own kind.

---

## NFDR § 10's account of the card's Test command — record gap, handed on by development-specs (2026-10-29)
**Record:** `products/tracker17/docs/nfdr.md` § 10, preamble (`:633-634`): "run with the project card's `Test command:`; typed from the product root, as every row here is, that command is `pytest tests/`. SDD § 6 names `pytest tests/e2e/` beside it as the second suite, and the layer-5 rows need both."
**Product today:** Once this change lands, the card's `Test command:` (`system/projects/tracker17/project.md`) runs both suites through uv, so the "Suite" gate covers the layer-5 rows on its own. The sentence still says the card's command is `pytest tests/`, with the end-to-end suite beside it. NFDR § 8 (`:543`) already says the suite command belongs to the card.
**Why not this change:** The request keeps the diff to the card: "the diff touches `system/projects/tracker17/project.md` and nothing under `products/tracker17/` beyond a README sentence the edit makes false". The NFDR is a definition document that no delivery change edits. Its seat should hear about it through a companion item.
**Owner:** none — for shukuba-refine
**Status:** open
