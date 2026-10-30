# Deferred Decisions — unreadable-start-non-text-path

What this change held back, for `shukuba-refine` to place after the unit lands. Collection, read after the unit lands; downstream stages append their own entries.

---

## The failed-action console message's path form — record gap, handed on by development-specs (2026-10-30)
**Record:** `docs/CONTENT.md` § *A path the tracker prints* ("one form in every place a path is written")
**Product today:** `products/tracker17/web/routes.py:1327-1332` writes the error text as it comes, so a save failure at such a path prints `OSError: [Errno 92] Illegal byte sequence: '<scratch>/caf\udce9'`, not the `\xe9` form
**Why not this change:** the request's words rule it out: "The failed-action console message is the seed's next item and stays out"
**Owner:** none — for shukuba-refine
**Status:** open

## The package feed's return check — review obligation, handed on by development-design (2026-10-30)
**Record:** `docs/nfdr.md` QC-40, “The moment stays owed until a review reads the graph listing those packages” (lines 404–415)
**Review evidence:** `gh api repos/kensaiapp/<the instance KensaiApp is developed in> --jq '{admin: .permissions.admin}'` returned `{"admin":true}`. `gh api repos/kensaiapp/<the instance KensaiApp is developed in>/dependabot/alerts --jq 'length'` returned HTTP 403, `Dependabot alerts are disabled for this repository.` `gh api --method POST repos/kensaiapp/<the instance KensaiApp is developed in>/dependency-graph/sbom/generate-report` returned HTTP 404, `Not Found`.
**Why not this change:** QC-40 explicitly leaves its return check owed on these outcomes and raises no discrepancy. This change changes path display and authorizes no repository security-setting change.
**Owner:** none — for shukuba-refine
**Status:** open
