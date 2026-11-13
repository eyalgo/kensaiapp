# Change Text — a project's summary shows the due-on-date count

**Date:** 2026-11-13
**Category:** feature
**Behaviour:** changing

---

## Text

### The label of the new row in the Summary page's "Due dates" group

**Every Summary, a project with no tasks included (the row sits between "Overdue" and "No due date", and its count is a bare numeral, 0 included)**

> Due on {date}

`{date}` is the summary's date, the same date the "Overdue" count on that page was worked out against, written `YYYY-MM-DD`. Example as the person reads it: `Due on 2026-11-13`. Nothing else goes in the label: no quotes, no colon, no full stop at the end.

When the person sees it: they've opened a project's Summary and read the count of its open tasks due on that one date. The label stays true on every later read of the same page, because it names a date and not "today". There's nothing to do from this row, since it's a plain count and not a link.

---

## Wording decisions

- The design names "the words before its date" as the place. The text above gives the whole label as one string, `Due on {date}`, with the date as a marked placeholder. — CONTENT § Localization says "No string is assembled from fragments" and "Placeholders may be reordered by a translator". If "Due on" were handed over alone, the word order would be fixed in code. What the person reads on the page is the same either way.
- The label is "Due on {date}" exactly, and not "Due today", "Today", "Due now", "Due soon", "Upcoming" or "Due" alone. — CONTENT § Terminology fixes the term for this concept and rejects each of those. § Grammar and mechanics bars "today", because a summary built before midnight and read after it would be wrong. The request's own phrasing already matched the term, so nothing changed from the request.
- No string is written for the count cell or for an empty project. — The count is a numeral, "0" in a summary cell (CONTENT § Grammar and mechanics, Numbers). The cell takes no accessible name of its own (CONTENT § Accessibility of text, "A plain count that is not a link ... takes no accessible name of its own"). An empty project shows the same label with 0, beside the existing invitation, which this change leaves unchanged (spec CP-813). So the label is the one string this change publishes.
- Banned-word check: the string was searched for every word in CONTENT § Terminology, "Banned in anything a person sees", and for the relative date words § Grammar and mechanics bars ("today", "yesterday", "tomorrow", "now", "ago", "recently"). None appears. The product has no check of its own that enforces its vocabulary (its architecture tests check imports and reach, not words), so there was nothing further to run.

---

## Findings for the Content Manager

None
