# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-11
- **Sources re-read:** MDN, `<input type="date">` (https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/date), fetched 2026-10-11. Item 3.1 leans on it. The page says: "The appearance of the date picker input UI varies based on the browser and operating system." It says: "The interfaces generally don't let you enter anything that isn't a date". It defines the value as "A string representing a date in YYYY-MM-DD format, or empty". It warns that client-side validation "is not a substitute for validating on the server" because the HTML can be bypassed. It does not describe a fallback to a text field in browsers that lack the control, so this run does not state one.

## Items worked

### 3.1 — The date rule bars telling the reader how to pick a date, and it is unclear whether a refusal may tell the reader to pick one

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** answered
- **Why:** The second reading. No tracker string tells the reader to pick or to type a date, a refusal included. A refusal names the outcome, and never the means of reaching it. The item carries no draft answer, only an example sentence, so this was decided from scratch.

  *Seat.* The item is `CONTENT.md`'s own to answer. The change lands in one rule of this document and in no other document. It binds no person and no outside party, and I could name no ground the owner holds that I cannot see. It is not a widening item either: it asks which of two readings an existing sentence has, and it cites an occurrence, the due-date refusal at `web/pages.py:276`.

  *Why the second reading.* Three things point the same way.
  1. The rule's own words are "no string tells the reader how to type or pick a date" (`CONTENT.md:129-130`), and the owner confirmed those words (`trail/content/cycle-1.md` § 1.1). Reading 1 would have to narrow a sentence the owner confirmed. Reading 2 is the sentence as written, and "Pick one" is a string telling the reader to pick a date.
  2. The rule's reason is the Voice rule that the tracker "states only what the tracker established" (`CONTENT.md` § Voice, third row). The tracker established that a date control exists, not what it looks like. MDN says its appearance "varies based on the browser and operating system". "Pick" names a mechanism the tracker did not establish.
  3. The refusal fires where that mechanism is least safe to name. MDN says the interface "generally" won't let a reader enter a non-date and that the value is a valid date or empty, so a refusal arises when something other than the control's own interface supplied the value. In that case "Pick one" tells the reader to use a control that did not decide the value.

  *The reason cycle 1 gave is narrower than the rule.* `trail/content/cycle-1.md` § 1.1 and `self_answer-1.md` say no string tells how to type or pick "because the field's format is not the tracker's to state". That reason covers a string stating a format. It does not cover the word "pick", which states no format. The conclusion held, and the argument did not carry the weight put on it. The fold should write the reason in point 2, so a later reader does not read the rule as a ban on format instructions only.

  *What the rule becomes.* § Grammar and mechanics (Dates and times) says in its own words that no string names how a date is entered, whether by typing, by picking or in a given format. A string may name what a date has to be and what the reader may do about it, such as "Give a calendar date, or leave the due date empty." The verb "give" is already in the document (`CONTENT.md:263`, "Give the first task a title and press Add."). § Grammar and mechanics (Verbs for pressing) says an option is "picked", and that stays true of a list. A date field is not an option in a list, so "picked" doesn't reach it. The Due from and Due to refusal ("Change one so Due from is the earlier date", `CONTENT.md:212`) names no means and already meets the rule.

  *The string in the product.* `web/pages.py:276` reads "A due date has to be a calendar date. Pick one, or leave the due date empty." Under this answer it doesn't meet the rule. That is a finding for a change that publishes text, where a Content Editor writes the string. This document gives no per-change copy, and the sentence in the companion is the rule's example shape and no more.

  *Failure paths.* Empty: the due date is optional (`UXD.md` UX-F3), so "leave the due date empty" is true on every page that carries the field. Absent: where the control shows no picker, the outcome wording stays true, where "pick" would not. Refused: a refusal is two sentences, the reason and one action (`CONTENT.md` § Error), and "Give a calendar date, or leave the due date empty" keeps the either-or the current string already has. Named and not covered: I did not settle whether an either-or counts as the "one action" the refusal formula names. The existing string already has the same either-or shape, which is a question about the formula and not about this item, so I left it. Stale and concurrent: not reached, because the field holds a value only until it is submitted.

  *Close call.* Reading 1 is what the cycle-1 reason supports. What would tip it back is the owner saying the date picker is a settled affordance that the tracker may name. `UXD.md` UX-F3 says "a date picker", but that fixes the design of the control and says nothing about what the tracker's strings may claim of it.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
