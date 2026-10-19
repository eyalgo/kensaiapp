# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-06
- **Sources re-read:** MDN, `<input type="date">` (https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/date), fetched 2026-10-06. Item 1.1 relies on it. The page says: "The displayed date format will differ from the actual `value` — the displayed date is formatted _based on the locale of the user's browser_, but the parsed `value` is always formatted `yyyy-mm-dd`." The page says nothing about a page author setting the displayed format, and this run's answer does not assume the author can. The companion's own quotation of the page matches.

## Items worked

### 1.1 — The date field shows the browser's own date format, and every other date the tracker writes is `YYYY-MM-DD`

- **Bucket:** 1. Open issues
- **Verdict:** answered
- **Why:** Accept the mismatch, and narrow the date rule so it stays true. The date field is the browser's own control, and `CONTENT.md` should say that its displayed form is not a tracker string. No change goes to the CDO.

  *Seat.* This item is `CONTENT.md`'s to answer. The item offered two ways out. Accepting lands in this document, as a scope sentence on the date rule. Changing the control would land in `UXD.md` UX-F3 and `DESIGN.md`, which is another seat's. I chose the first, so nothing is raised upstream. Nothing here binds a person or an outside party, and I could name no ground the owner holds that I cannot see.

  *Why accepting holds.* The control is the settled design: UX-F3 says "a date picker", `DESIGN.md` styles "date field" and keeps the picker's pop-up in the product's mode, and the owner confirmed plain HTML with the browser's own controls (`UXD.md` § 9, confirmed at `trail/uxd/cycle-1.md` § 2.1). Replacing it with a text field that forced `YYYY-MM-DD` would add a format check and a refusal for a malformed date, which is an addition to the SRS and the UXD, against the PRD's first risk ("a web interface adds parts"). It would also give up the picker's own keyboard handling. The mismatch itself does not make a reader misread a date: `YYYY-MM-DD` has one reading in any locale, and a native field only accepts a date in the reader's own locale form. The cost is that a reader sees two forms of one date, and that is a small cost.

  *Why the source holds.* The MDN sentence above states that the displayed form follows the browser's locale and the value is always `yyyy-mm-dd`. That is the whole premise of the item, and it stands as the companion quoted it.

  *What changes in `CONTENT.md`.* Two scope sentences, one in § Grammar and mechanics (Dates and times) and one in § Localization. The date rule governs every date the tracker writes as text, a refusal message included. The date field's displayed form is the browser's and is not a tracker string. No string tells the reader how to type or pick a date, because the field's format is not the tracker's to state.

  *Named and not covered.* Empty: an empty date field shows whatever the browser shows, which this run did not verify and does not state. Refused: a due-date range refusal quotes `YYYY-MM-DD` while the fields show the locale form. Both forms name the same date, so the refusal still reads alone. Stale and concurrent: not reached, since the field holds a value only until it is submitted.

  *Decided together with 2.3.* This answer and 2.3's confirmation fit: the rule stays `YYYY-MM-DD` for text the tracker writes, and the field is outside it. Had 2.3 been overridden to another form, this item would have changed with it.

  *Close call.* I considered asking the CDO for a control that displays `YYYY-MM-DD`. What would have tipped it is a source showing that readers mistake the two forms for different dates. None was found, and the item cites none.

### 2.1 — The voice is plain, quiet and not casual, with no exclamation marks, apologies, "please" or "successfully"

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed
- **Why:** The draft is confirmed as written.

  *Seat.* The voice is this document's to set. `<CORE>/doctrine/governance/where_taste_appears.md` § The rule puts the standard a product's words are written to in the Content Manager's `CONTENT.md`, and the instance fence sets no tone (`system/experience/voice_restrictions.md` § 3, "Tone and humour: n/a ... Each product decides in its own `CONTENT.md`"). I found no ground the owner holds and this run cannot see.

  *The draft holds, for the reasons it gives.* `UXD.md` § 1 reads the product as "plain, quiet, utilitarian". The PRD's first risk is that "a web interface adds parts that a command-line tool never needed" (`PRD.md` § Risks). One voice words both a routine status move and a project deletion that takes every task with it (`UXD.md` UX-I2), so a register that could joke at one could joke beside the other. The bans on "please" and "successfully" hold on their stated reasons: "please" adds a word with no information, and a completion line is shown only once the result is saved (`UXD.md` UX-I4), so the adverb repeats it. The ban on "simple", "easy" and "just" rests on `PRD.md` § Risks, "The only judge is the owner", which I re-read in the PRD and which says it. The ban on a welcome rests on the PRD's first-run note and `UXD.md` § 10, which exclude onboarding beyond the empty states.

  *Failure paths.* Failure and the unreadable-data state carry no apology and no reassurance, and the document states why (§ Tone). First run has no welcome. The stale-page refusal and the not-found page say the smaller true thing (RN-11). I found no state the voice cannot word.

  *Close call.* I considered whether the ban on every apology was too strict for the unreadable-data page, where the reader's work may be at stake. It stays, because the page's job is to say what the tracker knows, and "nothing in it was changed" does that better than an apology can.

### 2.2 — A line reporting an action starts with "You", for example "You moved 'Set up CI' to done."

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed
- **Why:** The draft is confirmed as written.

  *Seat.* This item is `CONTENT.md`'s. It changes the wording of an example the UXD gave and no rule: `UXD.md` UX-I4 requires only that the line "names what changed", and its "Moved 'Set up CI' to done" is an example.

  *The draft holds, for the reason it gives.* The inherited first fallback is "Say who acted and what state the thing is in" (`system/experience/voice_direction.md` § 1), with the check "can a reader say who did it and what happened now?". "Moved 'Set up CI' to done" fails the first half and "You moved 'Set up CI' to done" passes both. The fallback is marked `may be replaced` and nothing here replaces it. In a one-person tool the actor is always the reader, so the word adds little by itself. What it adds is the pairing: a completion line starts "You" and a failure starts "The tracker couldn't", so the first words of an announcement say which of the two happened, as the accessibility rule on status messages asks (§ Accessibility of text). I also checked the shape against the UXD and `DESIGN.md`: UX-F4 asks for "a one-line confirmation", UX-F10 for "a confirmation naming the deleted project", and `DESIGN.md` § Components describes `note-done` as "UX-I4's one-line confirmation". A one-sentence "You…" line meets all three.

  *Failure paths.* Stale and concurrent: a completion line is shown once and not updated, and "You moved" stays true in every tab because there is one operator. Refused: a refused action has its own pattern and never starts with "You". Empty: not reached. I found no case where the actor is someone other than the reader.

  *Close call.* The case against is one extra word per line against the PRD's "adds parts" risk. I confirmed because the pairing with the failure pattern is worth more than that word. A UXD rule that completion lines name no actor would have tipped it, and none exists.

### 2.3 — Dates are `YYYY-MM-DD` and times are `HH:MM` on a 24-hour clock, with no relative words

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed
- **Why:** The draft is confirmed as written. This answer was decided together with 1.1: the rule governs text the tracker writes, and the date field's own display is outside it. 1.1 carries that scope sentence, so this answer adds nothing under it.

  *Seat.* The form is `CONTENT.md`'s: `UXD.md` § Open Questions says "`CONTENT.md` settles it". I found no ground the owner holds and this run cannot see.

  *The draft holds, for the reasons it gives.* The PRD fixes dates as "calendar dates in the machine's local day" (`PRD.md` § UX Notes, Defaults) and SRS NFR-14 says due dates show as calendar dates and a comment's time shows in the machine's local time. `YYYY-MM-DD` is a calendar date in one order that has one reading everywhere. `DESIGN.md` § Typography switches on tabular figures for due dates and times (RN-11 there), and a fixed-width numeric date suits that. Pages do not update themselves (`UXD.md` UX-I9, SRS NFR-3), so "today" or "5 minutes ago" would be wrong by the next reload. The SRS states no display form, so nothing there conflicts (searched `SRS.md` for "iso", "locale" and "yyyy": no match).

  *Failure paths.* Named and not covered: at a clock change, one hour repeats, so two comments can show the same `HH:MM` with no seconds and no zone. The comment list is oldest first by written order (SRS FR-29), so the list still reads in order, and I left the form as it is. Empty: a task with no due date has no date to write. Stale: the Overdue marker is as of the page's load, which relative words would have hidden.

### 2.4 — The back-out control is "Back out", the confirming control repeats the action as a verb phrase, and the confirmation has two sentences

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed with addition
- **Why:** The draft is confirmed, with one addition from the failure paths.

  *Seat.* The words are this document's: `UXD.md` UX-I2 says "the word itself is `CONTENT.md`'s" and fixes the three parts and their order. I found no ground the owner holds and this run cannot see.

  *The draft holds, for the reasons it gives.* UX-I2 forbids a back-out word that reads as the status `cancelled`, so "Cancel" is out, and "Back out" is the UXD's own verb for the control ("a control that backs out and changes nothing"). A confirming control labelled "Confirm" or "Yes" names no action, and the labelling rule already bans both. The second sentence states why the step can't be undone, which is what the UXD requires the confirmation to guard: a project delete removes every task (`PRD.md` § Core Features, Projects) and `done` and `cancelled` are final (`PRD.md` § Core Features, Status workflow). I also checked that the first button and the confirming control for a delete carry the same label, "Delete project". The sentence stands between them and covers the first button's spot (UX-I2), so a reader meets words before the second press.

  *Addition: the count goes stale.* The confirmation's count ("its 12 tasks") is the page's as loaded, and another tab could add a task before the confirming press. `UXD.md` UX-I9 governs that and the UXD round that settled UX-I2 named it (`trail/uxd/self_answer-2.md`, "Named and not covered", stale). What that round left to this document is the wording after the press. The deletion removes every task, so a completion line repeating "12" would be wrong when the real count is 13. The line has to report the count the action deleted, read when it ran. The confirmation keeps the loaded count, which is the one it can know. Both sentences then say only what the tracker established.

  *Failure paths.* Empty: a project with no tasks has its own form already. Refused: a confirming press on a task another tab already moved or deleted is refused with the reason or shows the not-found page, both of which have patterns. Concurrent: covered by the addition.

  *Close call.* I nearly confirmed with no addition, since the count question sits in the UXD's settled UX-I9. I added it because a number in a line the tracker writes after the fact is a claim the tracker has to keep.

### 2.5 — Status and priority words are written as the PRD fixes them, lowercase, including as button labels

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed with addition
- **Why:** The draft is confirmed, with one addition to the exception in the rule.

  *Seat.* Spelling a term is this document's. The PRD fixes the four status words and the three priority words as values and says nothing about their capitalisation, which the item says. I found no ground the owner holds and this run cannot see.

  *The draft holds, for the reasons it gives.* `PRD.md` § Core Features, Status workflow writes `todo`, `in-progress`, `done` and `cancelled` as fixed values, and `UXD.md` UX-I1 names each move button by the status it moves to. A button reading "Done" beside a row cell reading `done` would be two spellings of one value. `DESIGN.md` does not capitalise either: it sets no text-transform (searched `DESIGN.md` for "text-transform", "uppercase" and "capitali": no match) and says column headers are "never set in capitals" (§ Typography).

  *Addition: the exception is too narrow.* The rule says "No string starts with a status or priority word, except a control whose whole label is that word." A status cell in a task row, an option in the status filter and a row label in the summary also start with a status word and are not controls, so as written the rule forbids the strings the UXD requires (`UXD.md` UX-S4, UX-F5 and UX-F6). The exception has to cover any string whose whole text is that word. The rule's purpose, that a sentence doesn't open with a lowercase value, is unchanged.

  *Failure paths.* Empty: not reached. A status word that ends a sentence, such as "You moved 'Set up CI' to done.", is untouched by the rule.

  *Close call.* The case for capitalising button labels is the sentence-case rule. I confirmed lowercase because it keeps one spelling per value across every surface.

### 2.6 — The Partial message pattern is declared absent

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed
- **Why:** The draft is confirmed as written.

  *Seat.* Whether a standing pattern is owed is this document's. I found no ground the owner holds and this run cannot see.

  *The draft holds, for the reasons it gives.* Each cited source says what the reason needs. `UXD.md` UX-I3 says "A refusal changes nothing", UX-I5 says a failure "changes nothing", and SRS NFR-2 says an interrupted save "reads as the state either before or after that action. It never reads as a partial mix of the two." `PRD.md` § Core Features, Projects says a project delete takes "all of its tasks", and SRS FR-13 says the same, so the one action that touches many records is one action, and NFR-2 covers it being cut off. A page appears "whole, or not at all" (`UXD.md` UX-I8).

  *Failure paths.* Empty: not reached. Refused and failed: both change nothing, which is the point. Concurrent: a stale edit replaces another tab's value for one field (SRS NFR-3), which is a whole change and not a partial one. Named and not covered: an action the SDD or a later change introduces that applies in part, such as a bulk move or an import. None exists in the PRD today, and the pattern is owed if one arrives.

### 2.7 — The Recovered message pattern is declared absent

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed with addition
- **Why:** The conclusion is confirmed, and the reason written into `omitted:` is restated because one clause of it does not hold.

  *Seat.* Whether a standing pattern is owed is this document's. I found no ground the owner holds and this run cannot see.

  *The conclusion holds.* A Recovered message would speak when something that had failed works again without the reader acting. Pages do not update themselves (`UXD.md` UX-I9, SRS NFR-3), real-time updates are out of scope (`PRD.md` § Out of Scope), and when the tracker is down the browser shows its own page, which the tracker can't change (`UXD.md` UX-F1). The reader's own reload or second press is a new action with its own pattern, which `omitted:` already says.

  *The reason did not hold as written.* `omitted:` says "there are no retries, and no connection is held open" and cites UX-I9 and PRD § Out of Scope. Those two sources close pages that update themselves. Neither says anything about retries. I searched `PRD.md`, `UXD.md`, `SRS.md` and `DESIGN.md` for "retry", "retries", "keep-alive", "websocket", "poll" and "open connection" on 2026-10-06 and found no match. The absence is real, but it is an absence and not a stated fact, and a later reader who inherits "there are no retries" inherits a claim nothing carries. The restated reason says what the documents do and don't contain, and names the sources that close the push paths.

  *Failure paths.* Stale: a reload that shows a changed task is the reader's action. Absent: the tracker not running is the browser's page. Named and not covered: if the SDD adds a retry or a background save, a state could clear by itself and the pattern would be owed then.

  *Close call.* I considered confirming without addition, because the conclusion is plainly right. I added the restatement because the sentence at issue is one `CONTENT.md` carries in its own frontmatter.

## Left for the owner

None this run.

## Skipped

None this run.

## Raised on this document

### 2.8 — A colon appears only in a page title, yet the time rule, the ready line and a terminal message each carry one

- **What the document is owed:** the colon rule in § Grammar and mechanics (Banned punctuation) is widened to a page title, a time and an address or path the tracker prints, so it no longer contradicts the time rule or two of the document's own strings.
- **Why it is worth a cycle:** it meets the prompt's ground "It contradicts a document it must agree with", here a document that contradicts itself, in `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` § The items are not the whole of what a document is owed. Measured on 2026-10-06 with `grep -n -E 'A colon appears|HH:MM|14:32|127\.0\.0\.1:8000' CONTENT.md`: line 109 says "A colon appears only in a page title", line 122 writes a time as `HH:MM`, line 241 carries "127.0.0.1:8000" and line 269 carries "http://127.0.0.1:8000". A Content Editor applying the rule to a comment's meta line or the ready line has no way to follow both.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
