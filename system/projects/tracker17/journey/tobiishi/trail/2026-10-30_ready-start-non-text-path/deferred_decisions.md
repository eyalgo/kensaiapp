# Deferred Decisions — ready-start-non-text-path

What this change held back, for `shukuba-refine` to place after the unit lands. Collection, read after the unit lands; downstream stages append their own entries.

---

## The failed-action console message's path form — record gap, handed on by development-specs (2026-10-30)
**Record:** `docs/CONTENT.md` § *A path the tracker prints* ("one form in every place a path is written")
**Product today:** `products/tracker17/web/routes.py:1327-1332` writes the error text as it comes, so a save failure at such a path prints `OSError: [Errno 92] Illegal byte sequence: '/tmp/caf\udce9'`, not the `\xe9` form
**Why not this change:** the request's words rule it out: "no other message text changed"
**Owner:** none — for shukuba-refine
**Status:** open

## QC-40 package feed and graph-listing moment — reviewed by development-design (2026-10-30)

**Record:** `products/tracker17/docs/nfdr.md` QC-40 (`L399-L418`).
**Review:** The repository API reports `permissions.admin: true`; its Dependabot alerts endpoint
returns HTTP 403, `Dependabot alerts are disabled for this repository.` The asynchronous SBOM
exports read returns HTTP 404, `Not Found` (`gh api repos/kensaiapp/<the instance KensaiApp is developed in>`,
`gh api repos/kensaiapp/<the instance KensaiApp is developed in>/dependabot/alerts`,
`gh api repos/kensaiapp/<the instance KensaiApp is developed in>/dependency-graph/sbom/exports`).
**Still owed:** A review that reads the dependency graph listing the packages fixed by the
product's `uv.lock`, per QC-40. These results match the down-feed case the entry already names;
they do not establish the graph-listing moment or a feed return.
**Why not this change:** This ready-message change alters no repository security setting or
dependency. The design's QC-40 note records the direct package-advisory review and the browser's
existing dated exception separately.
**Owner:** none — for shukuba-refine.
**Status:** open
