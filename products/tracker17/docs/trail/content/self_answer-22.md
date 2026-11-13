# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-11-13
- **Sources re-read:** None. Item 3.1 rests on no source outside this repository.

## Items worked

### 3.1 — The verbal language has no word for the due-today count UXD version 12 puts on the summary

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** answered
- **Why:** The label is "Due on {date}", with the one date the summary's counts were worked out for, written `YYYY-MM-DD`. The item has no draft, so I answered it from scratch. It holds three questions with one seat, so one slot answers all three: the label, the term against its rejected words, and whether the plain number takes an accessible name. No other document is owed a change.
  1. **Whose it is.** Wording a label is this seat's craft. It commits no person and no outside party, and I can name no ground I am missing, so it is not the owner's. The label's words are handed to this document by the UXD itself (`products/tracker17/docs/UXD.md` RN-38: "its words are `products/tracker17/docs/CONTENT.md`'s").
  2. **The widening test, and how I read it.** The item asks the document to state a term it does not state, so it widens the document, and it must cite an occurrence. It cites one: the state is present in the settled UXD at `products/tracker17/docs/UXD.md` lines 255-260 (UX-F6) and line 381 (UX-S5), and the grep in the item measures the gap, `grep -ciE 'due.today'` over `CONTENT.md` giving 0. I read the settled UXD as the site, because it is the input this document derives from and § *The items are not the whole of what a document is owed* names "something upstream moved and it has not seen it" as a ground in its own right. Precedent in the document is RN-29, which folded UXD version 11 the same way. Not built yet is what the item says, so there is no code site. **The other reading, and what tips it:** if an occurrence must be built code, the answer is "not until it occurs" and the build seed waits for the count to exist. I did not take that reading, because the definition chain owes a message pattern to every state the UXD names, and the build would otherwise write a string with no standard behind it.
  3. **Check 2, the question.** The item asks for "the summary label". The obvious label is "Due today", and § Grammar and mechanics bars it: "No string says 'today'... because a page doesn't update itself (UXD UX-I9) and a relative word would be wrong by the next reload." A summary built before midnight and read after would say "today" over yesterday's count. That rule is owner-confirmed (RN-6, `trail/content/cycle-1.md` § 2.3), so the answer complies with it and does not carve an exception.
  4. **The label.** "Due on {date}", for example "Due on 2026-11-13". The date is the tracker's own established fact, the local date the counts were worked out for, so the label stays true on every later read of the same page. It uses the one date formatter (§ Localization), the placeholder stands for one date and holds nothing grammatical, and it adds no colon, no punctuation and no sentence. "Due on" sits beside the existing "Due from" and "Due to" labels.
  5. **The term and its rejected words.** One row in § Terminology: a task due on that date and neither `done` nor `cancelled`. Rejected: "Due today" and "Today" (the date rule above), "Due now", "Due soon" and "Upcoming" (each claims a time window the count does not measure), and "Due" alone (the due-date row already rejects "due", and alone it blurs the count against "Overdue" beside it). The definition documents keep "due today" as their own phrase, as they keep "console" (RN-5).
  6. **Check 3, one date for both counts.** UXD UX-F6 and RN-38 hold "one 'today' for both counts in one summary". The label's date is that same date, so it also tells the reader which day "Overdue" was measured against. "Overdue" stays a one-word label with no date. Adding one is not asked and would widen the document with no occurrence.
  7. **The accessible name.** The plain number takes none of its own. § Accessibility of text gives accessible names to controls and links, and this number is neither (UXD UX-F6: the due-today count is a plain number, not a link). The rule for a number-only link, which starts with the number and says what it counts, does not apply. What the rule owes instead is that the row's label says what it counts without help from the row beside it, and "Due on 2026-11-13" does. The fold states that in one sentence. How a screen reader associates the label with the number is markup, which is DESIGN's and the SDD's, not words.
  8. **Check 4, the failure paths.** Empty: a project with no tasks shows the label and "0" (§ Numbers, a zero in a summary cell is "0", and UXD UX-S5). Absent: the tracker always has a local date, so no case lacks one. Stale: the page was built before midnight and read after, and the label still names the date it counted, which is why the date beats "today". Concurrent and refused: no state is shared and nothing is refused. Not covered: the label shows a date no earlier summary showed. Whether the summary may carry a date in a label is an experience question, and the CDO reviews this document against the experience, so it reaches them there and not here.
  9. **What the fold writes.** One § Terminology row, one sentence in § Accessibility of text, the Traceability row for UX-S5 naming the new label, a review note, and the "Inputs read" line moving to UXD version 12. The wording is `product-content`'s.
  10. **Close to a different verdict.** I was close to "left for the owner" on the label, because a date in a label is new on the page. What tipped it is that the wording is mine, the rule that forces the date is the owner's own and I comply with it, and the experience check is the CDO's by the loader's review seam.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
