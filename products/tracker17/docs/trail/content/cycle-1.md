# CONTENT open issues — tracker17

> Companion to `CONTENT.md`. The Content Manager authored the verbal language non-interactively;
> this file holds the calls it made and wants your sign-off on — each with the reason behind it,
> and what moves underneath it if you override — plus the few things it genuinely could not
> settle.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**,
> then re-run `product-content`. It folds your answers into `CONTENT.md` and drops the resolved
> items. When nothing is left open, `product-content` **deletes this file**: no file = the verbal
> language is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git refuses
> to remove a file with uncommitted edits in it — so an uncommitted answer stops that run before
> it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the Content Manager folds them in, it first copies
> this file whole to `docs/trail/content/` — so what you decided, and why, stays readable and
> citable for good.
>
> **§ 3 comes from outside this run.** The verbal language is read by everyone who writes a string,
> and a seat downstream can find a pattern it has no rule for. It is recorded there, answered here,
> and folded by the same run.

---

## 1. Open issues

### 1.1 The date field shows the browser's own date format, and every other date the tracker writes is `YYYY-MM-DD`
- **Why it matters:** `CONTENT.md` § Grammar and mechanics fixes every date the tracker writes as `YYYY-MM-DD`. The add-task and edit-task forms use a date picker (`UXD.md` UX-F3), and a native date input displays its date by the browser's locale, while its value is always `yyyy-mm-dd`. So a reader could type or pick a date shown as `10/06/2026` and then see the same date in the task table as `2026-10-06`. Words can't make the two agree, and the choice of control is the CDO's, not the Content Manager's.
- **What was searched:** `UXD.md` UX-F3 ("due date (optional, a date picker)") and `DESIGN.md` § Components for how the date field is specified. MDN, `<input type="date">`: "The displayed date format will differ from the actual `value` — the displayed date is formatted based on the locale of the user's browser, but the parsed `value` is always formatted `yyyy-mm-dd`." (https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/date). Neither the UXD nor `DESIGN.md` states a displayed format for the field.
- **Answer:** Accept the mismatch, and narrow the date rule so it stays true. The date field is the browser's own control, which `UXD.md` UX-F3 and `DESIGN.md` already settle, and the owner confirmed the browser's own controls (`UXD.md` § 9). A text field that forced `YYYY-MM-DD` would add a format check and a refusal for a malformed date. Two scope sentences go into `CONTENT.md`, in § Grammar and mechanics (Dates and times) and in § Localization. The date rule governs every date the tracker writes as text, a refusal message included. The date field's displayed form is the browser's and is not a tracker string. No string tells the reader how to type or pick a date. Nothing goes to the CDO. Reasoning in `docs/trail/content/self_answer-1.md`.

## 2. Choices to confirm

### 2.1 The voice is plain, quiet and not casual, with no exclamation marks, apologies, "please" or "successfully"
- **Written into CONTENT.md:** § Voice (the paragraph, the conversational-not-casual ruling and the behaviour table), § Terminology (the banned lexicon), § Grammar and mechanics (banned punctuation, sentence length).
- **Grounds:** `UXD.md` § 1 ("plain, quiet, utilitarian"), `PRD.md` § Risks ("a web interface adds parts"), and the fact that one voice words both a routine move and an irreversible deletion. No corpus exists, so this is a call.
- **What moves if you override:** the tone maps (§ Tone), every message pattern's examples, the banned lexicon and the reading bar all derive from it. A casual voice would change the empty states, the completion lines and the failure messages. An allowed first-run welcome would add an exception to the no-exclamation rule.
- **Confirm or override:** confirm. Reasoning in `docs/trail/content/self_answer-1.md`.

### 2.2 A line reporting an action starts with "You", for example "You moved 'Set up CI' to done."
- **Written into CONTENT.md:** § Voice (first behaviour row), § Message patterns (Completed), § Localization (each action is its own string).
- **Grounds:** the fallback in `CONTENT.md` § Voice, that a reader can say who acted and what state the thing is in. `UXD.md` UX-I4 gives "Moved 'Set up CI' to done" as an example, which names no actor. The UXD's rule requires only that the line "names what changed", so this changes an example and no rule.
- **What moves if you override:** the Completed pattern and its verbs, the first row of the behaviour table, and the failure pattern's "The tracker couldn't…" opening, which pairs with it.
- **Confirm or override:** confirm. Reasoning in `docs/trail/content/self_answer-1.md`.

### 2.3 Dates are `YYYY-MM-DD` and times are `HH:MM` on a 24-hour clock, with no relative words
- **Written into CONTENT.md:** § Grammar and mechanics (dates and times), § Localization (one formatter). This answers the first open question in `UXD.md`.
- **Grounds:** `PRD.md` § UX Notes, Defaults fixes dates as calendar dates in the machine's local day. `DESIGN.md` § Typography sets table figures to line up, which suits a fixed-width numeric date. Pages don't update themselves (`UXD.md` UX-I9), so "today" or "5 minutes ago" would be wrong by the next reload. The form itself is a call.
- **What moves if you override:** the Overdue marker's date, a comment's meta line, the summary, the setup instructions if they show a date, and open issue 1.1.
- **Confirm or override:** confirm. The date field's own display is outside this rule, as open issue 1.1 settles. Reasoning in `docs/trail/content/self_answer-1.md`.

### 2.4 The back-out control is "Back out", the confirming control repeats the action as a verb phrase, and the confirmation has two sentences
- **Written into CONTENT.md:** § Message patterns (Needs confirming), § Terminology ("Back out"). The UXD leaves the back-out word to this document and forbids one that reads as the status `cancelled` (`UXD.md` UX-I2).
- **Grounds:** "Back out" is the UXD's own phrase for the control. "Cancel" is rejected because it reads as the status. A confirming control labelled "Confirm" or "Yes" says nothing about what it does. The second sentence ("You can't undo this.", or why a cancelled task can't be moved again) states the irreversibility, which the UXD requires the confirmation to guard.
- **What moves if you override:** the three confirmation examples, the accessible names of the confirming and back-out controls, and the "Back out" row in the banned lexicon.
- **Confirm or override:** confirm, with one addition. A completion line that reports a project deletion gives the count of tasks the action deleted, read when it ran. It does not repeat the count the confirmation showed, because that count is the page's as loaded (`UXD.md` UX-I9) and another tab may have added a task since. Reasoning in `docs/trail/content/self_answer-1.md`.

### 2.5 Status and priority words are written as the PRD fixes them, lowercase, including as button labels
- **Written into CONTENT.md:** § Grammar and mechanics (case), § Terminology (the four statuses and three priorities).
- **Grounds:** `PRD.md` § Core Features, Status workflow fixes `todo`, `in-progress`, `done` and `cancelled`, and the UXD names each move button by the status it moves to (`UXD.md` UX-I1). A capitalised "Done" on a button beside a lowercase `done` in the row would be two spellings of one value. The rule is a call about the buttons, since the PRD says nothing about capitalisation.
- **What moves if you override:** the case rule, the accessible names of the move buttons, and the rule that no string starts with a status word.
- **Confirm or override:** confirm, with one addition. The exception to "no string starts with a status or priority word" covers any string whose whole text is that word: a control label, a table cell, a list option or a summary row label, not only a control. Reasoning in `docs/trail/content/self_answer-1.md`.

### 2.6 The Partial message pattern is declared absent
- **Reason written into `omitted:`** nothing in tracker17 is applied in part. A refused or failed action changes nothing (`UXD.md` UX-I3, UX-I5), and a cut-off save reads as the state before or after (`SRS.md` NFR-2).
- **Confirm or override:** confirm. Reasoning in `docs/trail/content/self_answer-1.md`.

### 2.7 The Recovered message pattern is declared absent
- **Reason written into `omitted:`** nothing in tracker17 comes back by itself. Pages don't update themselves, and there are no retries or open connections (`UXD.md` UX-I9, `PRD.md` § Out of Scope).
- **Confirm or override:** confirm, with the reason in `omitted:` restated. None of `PRD.md`, `UXD.md`, `SRS.md` and `DESIGN.md` has the tracker retry an action or hold a connection open, and `UXD.md` UX-I9 and `PRD.md` § Out of Scope close pages that update themselves. So no state exists in which a failure clears without the reader's own action, and that action gets its own Completed line. The sentence "there are no retries" comes out of the reason, because no cited source states it. Reasoning in `docs/trail/content/self_answer-1.md`.

### 2.8 A colon appears only in a page title, yet the time rule, the ready line and a terminal message each carry one
> Raised by a `companion-self-answer` run on 2026-10-06, not written by a `product-content` run. The run was answering this file and read `CONTENT.md` whole to do it. No item asked about this. It found that § Grammar and mechanics (Banned punctuation) and three of the document's own strings contradict each other. The run left `CONTENT.md` unchanged and raised the change here. Its reasoning is in `docs/trail/content/self_answer-1.md` § Raised on this document.
- **Written into CONTENT.md:** § Grammar and mechanics, Banned punctuation, says "A colon appears only in a page title." The same section's Dates and times rule writes a time as `HH:MM`, such as `14:32`. § Message patterns, Loading, gives the ready line "Open http://127.0.0.1:8000 in your browser." § Message patterns, Error, gives a terminal message naming "127.0.0.1:8000".
- **Grounds:** a reader applying the colon rule to a comment's meta line, the ready line or the address-in-use message has two rules that can't both hold, and the Content Editor has no basis to pick. The strings are required: SRS NFR-8 requires the terminal to give the address to open. A time needs a separator and an address needs its port. A colon in a time or an address is not punctuation in a sentence. § Localization already treats addresses and file paths as values the tracker never translates, which is the line this change would draw. The proposed change reads: a colon appears in a page title, inside a time, and inside an address or a path the tracker prints.
- **What moves if you override:** to keep the rule as written, the time would need another separator and the address another form, which changes open issue 2.3's accepted form and the strings the SRS requires. On this reading, the rule's purpose is no colon joining two clauses in a sentence, and that is the same either way.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

## 3. Raised from downstream — an item from a seat that did not write the verbal language

None.
