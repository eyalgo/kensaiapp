# Deferred Decisions — summary-page

What this change held back, for `shukuba-refine` to place after the unit lands.

---

## Summary counts as links into filtered lists — record gap, handed on by development-specs (2026-10-28)
**Record:** UXD UX-F6 and UX-S5 (each status count, priority count and the overdue count links to the project's list filtered to that value); SDD § 6 S-6 *Reached when*; CONTENT.md's accessible name for a link that is only a number.
**Product today:** no Summary exists (`grep -n -i summary web/pages.py`, no match), and this change's Summary carries every count as a plain number (change_spec CP-503).
**Why not this change:** the request rules it out: "the counts stay plain numbers with no count linking anywhere, since the links into filtered lists are the next station (`linked-counts`)".
**Owner:** none — for shukuba-refine
**Status:** open

## The unreadable-saved-data page on every address — record gap, handed on by development-specs (2026-10-28)
**Record:** FDR R-25 and R-26; UXD UX-S9 (every page says the saved data could not be read, names its location, and offers no action or navigation).
**Product today:** on unreadable saved data the tracker prints its message and does not start, so it serves no page at all (`main.py:39-48`).
**Why not this change:** the requirement binds a mode the product never enters, and this change leaves that mode as it is. The request does not ask for it.
**Owner:** none — for shukuba-refine
**Status:** open
