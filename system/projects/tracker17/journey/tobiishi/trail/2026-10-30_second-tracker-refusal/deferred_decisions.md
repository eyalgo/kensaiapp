# Deferred Decisions — second-tracker-refusal

What this change held back, for `shukuba-refine` to place after the unit lands.

---

## The unreadable-data page — record gap, handed on by development-specs (2026-10-30)
**Record:** SRS FR-8 and DR-6; SDD § 6 `protect-saved-data` (the page, its console message, the set-aside restart, AC-7's one test per break, and the README's description of an unreadable start)
**Product today:** a start on unreadable saved data prints one line and exits 1 (`products/tracker17/main.py:104-113`)
**Why not this change:** the request rules it out: "Not here: the unreadable-data page, its console message, the set-aside restart, the one-test-per-DR-6-break work and the README's unreadable-data description (the seed's item 2, `unreadable-data-page`)."
**Owner:** none — for shukuba-refine
**Status:** open

## Observing the package feed's return — record gap, handed on by development-design (2026-10-30)
**Record:** `products/tracker17/docs/nfdr.md:389-398`, QC-40, requires a review to read the dependency graph listing the locked packages and surface the feed's return.
**Product today:** the 2026-10-30 authenticated check confirmed repository admin access, then `gh api repos/<owner>/<repository>/dependabot/alerts` returned HTTP 403, `Dependabot alerts are disabled for this repository.` The asynchronous export request, `gh api repos/<owner>/<repository>/dependency-graph/sbom/generate-report`, returned HTTP 404, `Not Found`. Neither result supplies a graph listing. The advisory review itself is recorded in `change_design.md`, Architect Review Notes.
**Why not this change:** `change_request.md`, Request, asks for location locking, its proofs and the README passage. It authorizes no repository-security setting change. QC-40 already keeps the graph observation owed until a review reads the listing; the failed export does not settle it.
**Owner:** none — for shukuba-refine
**Status:** open
