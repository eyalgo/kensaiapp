# Deferred Decisions — what-the-start-prints

This collection carries an unmet record obligation for `tracker17 · tobiishi · 2026-10-30_what-the-start-prints`.
It is read after the unit lands, per `<CORE>/../skills/product-owner/.claude/skills/development-specs/references/deferred_decisions_template.md`, “Collection, read after the unit lands”.

## Dependency graph lists the locked packages — record gap, handed on by development-design (2026-10-30)

**Record:** `products/tracker17/docs/nfdr.md:403-415`, QC-40, the package-feed review moment.
**Product today:** The admin-account check returned `permissions.admin: true` from `gh api repos/<owner>/<repository> --jq '{full_name,permissions,security_and_analysis}'`. The alerts endpoint returned HTTP 403 with `Dependabot alerts are disabled for this repository`. The asynchronous export command `gh api repos/<owner>/<repository>/dependency-graph/sbom/generate-report` returned HTTP 404. QC-40 calls this feed down with the graph-listing moment still owed, not a discrepancy (`products/tracker17/docs/nfdr.md:409-415`).
**Why not this change:** `change_spec.md:44,98-102`, CP-745 and “Out of Scope”, limits the product edit to one README section. Enabling the feed and verifying the graph listing are outside that request. The critical-advisory and browser readings for this review stand in `change_design.md`, “Architect Review Notes”.
**Owner:** none — for shukuba-refine
**Status:** open
