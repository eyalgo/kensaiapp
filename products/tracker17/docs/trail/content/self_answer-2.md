# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-06
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Every claim it leans on was re-read in `CONTENT.md`, `SRS.md` and `UXD.md` on 2026-10-06.

## Items worked

### 2.8 — A colon appears only in a page title, yet the time rule, the ready line and a terminal message each carry one

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed with addition
- **Why:** The proposed change is confirmed, and one addition covers a case it missed. The colon sentence in § Grammar and mechanics (Banned punctuation) is widened to a page title, a time, and an address or a path the tracker prints. The addition is that the bans in that bullet govern the tracker's own words. They don't reach a value the reader typed, or the underlying error text a terminal diagnostic carries verbatim.

  *Seat.* This item is `CONTENT.md`'s. The change lands in one bullet of its Grammar and mechanics section. It binds no person and no outside party, and I could name no ground the owner holds that I cannot see. This run raised the item itself (`trail/content/self_answer-1.md` § Raised on this document), and that run left the slot at its placeholder on purpose, so deciding it now is the next round and not a second decision on the same reasoning.

  *The draft holds, for the reasons it gives.* I re-measured the contradiction on 2026-10-06. Line 109 of `CONTENT.md` says "A colon appears only in a page title." Line 122 writes a time as `HH:MM`, and open issue 2.3 confirmed that form (`trail/content/cycle-1.md` § 2.3). Line 243 carries "127.0.0.1:8000" and line 271 carries "http://127.0.0.1:8000". A Content Editor applying the rule to a comment's meta line or to the ready line has two rules that can't both hold. The strings are required: SRS NFR-8 says the tracker "writes to the console it was started from the address to open and the saved-data location" (`SRS.md` line 329). A time needs a separator and an address needs its port, and neither is a colon joining two clauses in a sentence. § Localization already lists addresses and file paths as values the tracker never translates (`CONTENT.md` line 385), which is the same line.

  *Why "path" stays in the wording.* No source names the platform: I searched `PRD.md`, `SRS.md`, `UXD.md` and `DESIGN.md` for "windows", "macos", "linux" and "platform" and found no match. The examples show POSIX paths with no colon. But NFR-8 makes the tracker print a location it doesn't control, and a drive path would carry a colon. Wording the rule for the printed location costs nothing and avoids a second contradiction later.

  *Addition: a typed value and the verbatim error text.* A reader can type a title such as 'Fix: login'. § Voice says to write the reader's typed words back exactly, in quotes, and § Quotes says the value is shown whole. So "You added 'Fix: login'." carries a colon the tracker did not write, and the widened rule still contradicts it. The terminal's underlying error text has the same property: it is printed "exactly as the system reported it" and is not the tracker's wording (§ Error, terminal messages, and RN-12). The other banned marks fail on the same case, since a title can end in an exclamation mark and the system's text can carry a semicolon or an ellipsis. So the fold states the exemption once for the whole bullet, and does not patch it mark by mark. This changes no rule's purpose. Both texts were already written back exactly, and the bullet never said whose words it banned.

  *Failure paths.* Absent: no address or location can be missing from the ready line, because NFR-8 requires both. Refused: a refusal that quotes a typed value is covered by the addition. A date quoted in the due-date refusal is `YYYY-MM-DD`, with hyphens and no colon. An address with several colons, such as an IPv6 form, is inside "an address". Empty, stale and concurrent: not reached, since the rule concerns the characters in a string. Named and not covered: no platform is stated in the definition documents, so whether a drive-letter path ever appears is not established here, and the wording covers it either way. I also searched `UXD.md`, `PRD.md` and `DESIGN.md` for a quoted string carrying a colon and found none that the tracker writes, so no further string needs the rule widened.

  *Close call.* I considered answering with the draft as written, because its conclusion is right. I added the typed-value case because a rule widened for three cases and still contradicting a fourth that the document's own Voice section requires would be raised again by the next reader of a comment or a task title.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
