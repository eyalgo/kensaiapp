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

> **No producing run wrote this file.** It was opened on 2026-10-30 by the PM, to carry § 3.
> `product-content` has no record of writing it.

---

## 1. Open issues

None.

## 2. Choices to confirm

None.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 Terminal messages has no pattern for a start that serves on unreadable data, and its third example is false
- **Raised by:** PM — 2026-10-30
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. A published line has no rule behind it, and the rule's example describes nothing the tracker does.
- **Where it shows:** `docs/CONTENT.md:L258-L267` covers "A start that fails", and its third example is "The tracker didn't start, because it couldn't read its saved data at …". That start now stays up and prints "The tracker couldn't read its saved data at {location}, and nothing in it was changed. Open {address} in your browser to read this on a page. To start fresh on purpose, follow Setting saved data aside in the setup instructions." (`main.py:L170`; `README.md`, "Starting the tracker again"). The example wants replacing and the formula extending: location, unchanged data, address, section pointer.
- **If a document has to be written:** none — `CONTENT.md` itself, by `product-content`.
- **Answer:** Confirmed with addition: replace the third example under Terminal messages, and give the line its own pattern, because it is not a start that fails. The parts, in order: the tracker couldn't read its saved data and where it is, with the path written as item 3.2 rules; nothing in it was changed; the address to open to read this on a page; and the setup instructions' section on starting fresh, named exactly. Three sentences, the first carrying the first two parts. It begins "The tracker couldn't read", not "The tracker didn't start", because the tracker did start. Example: "The tracker couldn't read its saved data at /Users/sam/tracker17/data, and nothing in it was changed. Open http://127.0.0.1:8017 in your browser to read this on a page. To start fresh on purpose, follow Setting saved data aside in the setup instructions." Three additions the item did not name. The sentence "Where saved data is the reason, it names the location" leaves the failed-start paragraph, because no failed start has that reason now. Loading says the terminal prints this line in place of the ready line when the data can't be read. The Traceability rows for UX-S2 and UX-S9 name the terminal line. Reasoning: `docs/trail/content/self_answer-19.md`.

### 3.2 No rule says how a message shows a location whose path is not valid text
- **Raised by:** PM — 2026-10-30
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** the words are what a fix waits on. Until a form is ruled, a start from such a location ends with a traceback.
- **Where it shows:** `docs/nfdr.md` § 9 lets the tracker run on Linux, where a path may hold bytes that are not UTF-8, and every start message names the location. Measured 2026-10-30 from the product root: `web.UnreadableSite(os.fsdecode(b'/tmp/caf\xe9/data'), '127.0.0.1:8017')` raised `UnicodeEncodeError: 'utf-8' codec can't encode character '\udce9'`, and printing the same text to a UTF-8 standard output raised the same error, so the ready line carries the same risk. Such a path has no faithful text, so showing it at all is a wording call for both starts.
- **If a document has to be written:** none — `CONTENT.md` itself, by `product-content`.
- **Answer:** Answered: a path the tracker prints is written as the machine names it, and a byte in it that is not text is written as a backslash, an x and the byte's two hex digits, such as \xe9. Nothing else in the path changes. It is one form in every place a path is written: the ready line, the line for unreadable saved data, and the unreadable-data page. No message leaves the path out for this reason, and none replaces the byte with a mark that stands for a character, such as the Unicode replacement character. Example: "/tmp/caf\xe9/data". No sentence is added to explain the form, because the ready line is already at the three-sentence cap. The rule lands as one bullet in Grammar and mechanics, and Localization already keeps file paths out of translation. Not covered: a folder name that really holds a backslash, an x and two hex digits reads the same as the escaped byte, and a valid character that the terminal's own encoding can't write is a different cause with the same traceback. Reasoning: `docs/trail/content/self_answer-19.md`.

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
