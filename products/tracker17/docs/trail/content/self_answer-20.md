# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-30
- **Sources re-read:** None. Item 3.1 rests on no source outside this repository.

## Items worked

### 3.1 — "Stopped" is recorded as the word for Ctrl-C, and the setup instructions also use it for a refused start

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** confirmed with addition
- **Why:** Approve "stopped" for a start that ended by itself after its refusal, written "this start has stopped", and correct the "killed" row. The item is about this document's own terminology, so the answer goes in its slot and no upstream companion is raised.
  1. **Whose it is.** The edit lands in `CONTENT.md` § Terminology. Which word names an end is wording, which is this seat's craft. It commits no person and no outside party, and I can name no ground I am missing, so it is not the owner's. No other document is owed a change.
  2. **It cites its occurrence, so "not until it occurs" does not apply.** The item names the sentence in `README.md` § "What the start prints": "A line that starts with `The tracker didn't start` means this start has stopped." I re-read it at that heading. The row it asks to correct is also a statement found incomplete, which is a correction and not a widening.
  3. **Check 2: the PM's lean is right, and its stated reason is only half the reason.** The lean says "this start" keeps the sentence apart from a tracker the reader stopped with Ctrl-C. The row's own premise is wider than that. The row says "Stopped" is "the setup instructions' word for Ctrl-C". The setup instructions use it more widely than that. § "What the start prints" says "the tracker keeps running until you stop it" and "every project you created before it stopped is still listed", the second of which covers any end. So "stopped" is the setup instructions' general word for a tracker's end, with Ctrl-C one case of it. That does not move the "killed" row's conclusion, because a general word still hides the one end that sentence is about. It does make the row's reason wrong, so the fold must replace the reason and keep the term.
  4. **The qualifier does real work, and it is the second reason.** I tested "the tracker isn't running" as the alternative, because the preceding paragraph of the setup instructions says "The tracker is still running when that line shows" for the other line. It fails. `README.md` § "Starting the tracker again" shows the refused line "The tracker didn't start, because another tracker is already running on the same saved data" and then says "The first tracker carries on". After that line a tracker is running. The thing that ended is the start, not the tracker, so "this start" is the subject the fact needs. This is not a word that needs a qualifier to mean something else. It is a word with the right subject.
  5. **Check 3, against the document.** Terminal messages already print "Stop that program, then start the tracker again" and "Stop that one first, then start this one", so "stop" is the verb the tracker's own lines use for ending a tracker. A term built on it follows the product. The same § "Starting the tracker again" says the refused start "exits". That is the same end in a second word, and one term per concept applies, so the row lists "exits" as rejected for naming a mechanism, as the "killed" row does for "process". I did not ask the sentence to change. This document's established course is a finding for a change that publishes text, not an edit here (RN-23, RN-26, RN-27). "Failed" is already banned, and "crashed" names a cause the tracker did not establish.
  6. **Check 4, the failure paths.** Concurrent: covered in 4, since "this start" names which of two starts the line is about. Refused: every "didn't start" line is a start that ended, so the term holds for the address-in-use line and the same-saved-data line alike. Empty and absent: no case reaches a term for an end. Stale: the term describes the start the reader just made, and the line is printed once, so nothing ages. Not covered: a start that ends for a reason that has no "didn't start" line, because no such line exists.
  7. **The other reading, and what tipped it.** I was close to confirming the item exactly as written, with the lean's reason. What tipped it was 3. Folding the lean's reason would leave the "killed" row stating that "Stopped" is only Ctrl-C's word, which the setup instructions contradict in two places.
  8. **What the fold writes.** A row in § Terminology for a start the tracker refused, with the term, the rejected words and the note. The "killed" row's reason replaced and its term kept. A review note for the change. The wording is `product-content`'s.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
