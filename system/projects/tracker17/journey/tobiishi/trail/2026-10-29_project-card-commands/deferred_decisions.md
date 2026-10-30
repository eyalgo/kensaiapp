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

## QC-40's package-feed and graph-reading moment — record gap, handed on by development-design (2026-10-29)
**Record:** `products/tracker17/docs/nfdr.md:389-399`, § 2 QC-40, requires a review from an administrator account and a dependency-graph page or asynchronous SBOM export listing the packages fixed by `uv.lock`; the moment stays owed until that listing is read.
**Product today:** `gh api repos/kensaiapp/<the instance KensaiApp is developed in> --jq '{permissions: .permissions}'` returned `admin: true`. The Dependabot alerts endpoint returned HTTP 403, “Dependabot alerts are disabled for this repository.” An authenticated GraphQL read of `dependencyGraphManifests(first:100)` returned `totalCount: 0, nodes: []`. Opening https://github.com/kensaiapp/<the instance KensaiApp is developed in>/network/dependencies returned “Failed to fetch … Cache miss.” The required listing was not read. This change's `change_design.md` § Architect Review Notes records the bounded package and browser review separately.
**Why not this change:** The request confines implementation to the card's two command values and explicitly excludes changing QC-40's review moment (`tracker17 · tobiishi · 2026-10-29_project-card-commands`, `change_request.md`, “Not here: the review moment (QC-40)”). The missing listing is not waived, and no repository security setting is changed.
**Owner:** none — for shukuba-refine
**Status:** open
