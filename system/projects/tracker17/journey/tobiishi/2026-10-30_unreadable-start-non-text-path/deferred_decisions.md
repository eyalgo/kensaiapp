# Deferred Decisions — unreadable-start-non-text-path

What this change held back, for `shukuba-refine` to place after the unit lands. Collection, read after the unit lands; downstream stages append their own entries.

---

## The failed-action console message's path form — record gap, handed on by development-specs (2026-10-30)
**Record:** `docs/CONTENT.md` § *A path the tracker prints* ("one form in every place a path is written")
**Product today:** `products/tracker17/web/routes.py:1327-1332` writes the error text as it comes, so a save failure at such a path prints `OSError: [Errno 92] Illegal byte sequence: '<scratch>/caf\udce9'`, not the `\xe9` form
**Why not this change:** the request's words rule it out: "The failed-action console message is the seed's next item and stays out"
**Owner:** none — for shukuba-refine
**Status:** open
