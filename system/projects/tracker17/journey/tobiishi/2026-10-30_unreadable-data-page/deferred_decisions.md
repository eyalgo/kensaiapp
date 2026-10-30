# Deferred Decisions — unreadable-data-page

What this change held back, for `shukuba-refine` to place after the unit lands.

---

## The console line on an unreadable start has no rule, and one example goes false — record gap, handed on by development-specs (2026-10-30)
**Record:** `docs/CONTENT.md` § Terminal messages, the formula and the third example (`:258-267`).
**Product today:** the example "The tracker didn't start, because it couldn't read its saved data at …" is what `main.py:124-129` prints. After this change a start on unreadable data serves, so the example describes nothing, and the formula covers only a start that fails.
**Why not this change:** `CONTENT.md` is the Content Manager's, and the request does not ask for it. CP-711 states what the line must say, and the content step writes its words for this change.
**Owner:** none — for shukuba-refine
**Status:** open

## "No header" against "the header shows the product name" — record gap, handed on by development-specs (2026-10-30)
**Record:** SDD § 4 EX-12 ("carries no header and no navigation") and `docs/DESIGN.md:427` ("the header shows the product name and no nav links").
**Product today:** the page does not exist yet. `web/pages.py:474-492` writes the one header, nav links included, on every page.
**Why not this change:** CP-717 follows the design document, and both records agree on no navigation (Locked Answers, Gap 7). Aligning the SDD's wording is the CTO's, and the request does not ask for it.
**Owner:** none — for shukuba-refine
**Status:** open
