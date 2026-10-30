# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-30
- **Sources re-read:** None. Item 3.1 rests on no source outside this repository.

## Items worked

### 3.1 — Two clauses disagree on a path inside the underlying error text of a failed action

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** overridden
- **Why:** The raiser's lean was that the path form wins inside the error text. I replaced it: the verbatim text wins, and the path form governs only a path the tracker writes in its own words. The item has no companion on another document to raise, because the edit lands only in `CONTENT.md`.
  1. **Whose it is.** Which of two clauses in this document governs is wording, which is this seat's craft. It commits no person and no outside party, and I can name no ground I am missing, so it is not the owner's. No other document is owed a change.
  2. **The occurrence is cited, so "not until it occurs" does not apply.** I ran the cited case. `str(OSError(92, 'Illegal byte sequence', os.fsdecode(b'/tmp/caf\xe9')))` gives `[Errno 92] Illegal byte sequence: '/tmp/caf\udce9'`, and `web/routes.py:1327-1332` writes it after "OSError: ". The item is also a conflict between two settled clauses, which is a correction and not a widening.
  3. **Check 2: the lean's stated reason does not hold.** It says the path rule wins because its first clause says "every place" and it is the later and more specific rule. "Every place a path is written" sits in a rule headed "A path the tracker prints", and the line it governs is the tracker's own wording. The error text is the system's wording, so the phrase does not reach it. The document already draws this line three times. § Grammar and mechanics (Banned punctuation) says the bans "govern the tracker's own words" and don't reach "the underlying error text a terminal diagnostic carries verbatim". § Terminology (Banned in anything a person sees) allows the technical vocabulary in that text. § Localization lists it under "Never translated". The path form is a fourth rule of the same kind, so the same carve-out applies.
  4. **Check 2: the lean's remedy has no safe way to run.** To print `\xe9` inside the error text, the tracker would have to find the path in text it did not compose and rewrite the byte. An exception's text is free-form, and the tracker can't establish which part of it is a path, so a rewrite claims what the tracker did not establish (§ Voice, "State only what the tracker established"). It would also stop being "the error" that SRS NFR-8 requires the line to name. The text this item measures is already ASCII, so the system's own form is safe to print as it stands.
  5. **Check 3, against the record.** RN-12 gives the reason verbatim text is allowed, which is that the reader of the terminal is a developer. RN-33 says "one form everywhere" and its own list of what it does not cover leaves this case out, so the fold narrows its wording to what the tracker writes in its own words. The Terminal messages paragraph's "exactly as the system reported it" is already the rule and needs no change, beyond the one sentence that makes the boundary explicit. RN-12 says the text "may" be carried and the paragraph says it "prints", which is a difference in force and not a conflict, and I leave it.
  6. **Check 4, the failure paths.** Empty: an error with no text prints only its kind, and no path is involved. Absent: the same. Stale and concurrent: the line is written once, as the error occurs. Refused: a refusal prints nothing to the terminal. Another case: a plain sentence the tracker composes that names a path, such as a future failure that names the saved data's location, is in the tracker's own words and takes the path form, so the answer says so. Not covered: an error text that holds a raw non-text byte and not its escaped form. The terminal can't encode it, and the write itself can raise. Making that write safe is the implementation's, and no wording rule can fix it.
  7. **What the fold writes.** In § Grammar and mechanics (A path the tracker prints), "It is one form in every place a path is written" becomes "every string the tracker writes", with one sentence saying a path inside the underlying error text prints as the system reported it. One sentence of the same meaning under § Message patterns, Terminal messages. A review note for the change, and RN-33's "one form everywhere" narrowed to match. The wording is `product-content`'s.
  8. **What the answer means for the product.** The failure line as measured already prints the system's form, `\udce9`. The line has one correct form, as reported, so no product change follows from this item.
  9. **The other reading, and what tipped it.** I was close to confirming the lean. What tipped it was 4. Had the tracker composed the path into the line itself, the path would be its own words and the lean would be right. That is the condition the fold states.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
