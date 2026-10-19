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

None.

## 2. Choices to confirm

### 2.8 A colon appears only in a page title, yet the time rule, the ready line and a terminal message each carry one
> Raised by a `companion-self-answer` run on 2026-10-06, not written by a `product-content` run. The run was answering this file and read `CONTENT.md` whole to do it. No item asked about this. It found that § Grammar and mechanics (Banned punctuation) and three of the document's own strings contradict each other. The run left `CONTENT.md` unchanged and raised the change here. Its reasoning is in `docs/trail/content/self_answer-1.md` § Raised on this document.
- **Written into CONTENT.md:** § Grammar and mechanics, Banned punctuation, says "A colon appears only in a page title." The same section's Dates and times rule writes a time as `HH:MM`, such as `14:32`. § Message patterns, Loading, gives the ready line "Open http://127.0.0.1:8000 in your browser." § Message patterns, Error, gives a terminal message naming "127.0.0.1:8000".
- **Grounds:** a reader applying the colon rule to a comment's meta line, the ready line or the address-in-use message has two rules that can't both hold, and the Content Editor has no basis to pick. The strings are required: SRS NFR-8 requires the terminal to give the address to open. A time needs a separator and an address needs its port. A colon in a time or an address is not punctuation in a sentence. § Localization already treats addresses and file paths as values the tracker never translates, which is the line this change would draw. The proposed change reads: a colon appears in a page title, inside a time, and inside an address or a path the tracker prints.
- **What moves if you override:** to keep the rule as written, the time would need another separator and the address another form, which changes open issue 2.3's accepted form and the strings the SRS requires. On this reading, the rule's purpose is no colon joining two clauses in a sentence, and that is the same either way.
- **Confirm or override:** confirm, with one addition. The colon sentence in § Grammar and mechanics (Banned punctuation) is widened to a page title, a time, and an address or a path the tracker prints. The addition: the bans in that bullet govern the tracker's own words, so they don't reach a value the reader typed or the underlying error text a terminal diagnostic carries verbatim. Both are written back exactly (§ Voice, § Quotes, § Error terminal messages), and a title such as 'Fix: login' would otherwise put a colon into "You added 'Fix: login'." State that once for the whole bullet, since the other marks fail on the same case. Reasoning in `docs/trail/content/self_answer-2.md`.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

None.
