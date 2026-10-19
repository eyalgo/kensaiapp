# Self-answer report — SRS.md

## Header

- **Companion:** products/tracker17/docs/SRS_open_issues.md
- **Document:** products/tracker17/docs/SRS.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-06
- **Sources re-read:**
  - https://html.spec.whatwg.org/multipage/form-elements.html, the `textarea` element. Its API value
    is "the element's raw value, with newlines normalized". Its maximum is checked against "the
    length of the value of the element's descendant text content with newlines normalized".
  - https://infra.spec.whatwg.org/. To normalize newlines is to "Replace every U+000D CR U+000A LF
    code point pair with a single U+000A LF code point". "A string's length is the number of code
    units it contains."
  - https://html.spec.whatwg.org/multipage/form-control-infrastructure.html, "Converting an entry list
    to a list of name-value pairs". It says to "Replace every occurrence of U+000D (CR) not followed
    by U+000A (LF), and every occurrence of U+000A (LF) not preceded by U+000D (CR), in value, by a
    string consisting of U+000D (CR) and U+000A (LF)."
  - `http.server` on this machine's Python 3.14.7
    (`/opt/homebrew/Cellar/python@3.14/3.14.7/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py:468-473`).
    It reads `self.rfile.readline(65537)`, then `if len(self.raw_requestline) > 65536:` and
    `self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)`.

## Items worked

### 2.1 — The SRS states the maximum length of every text field, and a longer value is refused

- **Bucket:** 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The SRS takes the lengths as a requirement, as drafted. The answer adds three things and
  narrows one sentence.

  *Seat (check 1).* This item is mine, in the owner's seat. The edit lands in `SRS.md`, which is the
  CTO's document. The lengths themselves are already decided: item 2.1 of
  `products/tracker17/docs/SDD_open_issues.md` was answered in the CPO's seat, "confirm, with two
  additions". This item only asks whether the SRS carries that decision as a requirement. That
  binds nobody outside the product, and I can name no ground I cannot see.

  *The draft holds (check 2).* Each of its three reasons rests on a sentence I found where it says.
  - `SDD.md` § 12: "It changes no system requirement, which are the SRS's."
  - `SRS.md` AC-12 tests "Each refusal FR-39 lists".
  - `SDD.md` § 4 TS-4 fails "when a requirement identifier named there is not in"
    `SRS.md`.

  A rule the code enforces with no SRS identifier is a rule the trace in NFR-9 cannot reach. The
  draft's external facts also hold at their sources (Sources re-read). A `textarea` counts a line
  break as one character, and the browser sends it as CR LF. The listener refuses a request line
  over 65,536 bytes.

  *Addition (1), NFR-1 (checks 3 and 4).* The open question that closes, the first item of `SRS.md`
  § Open Questions, holds the only sentence that bounds NFR-1's text: "NFR-1 is measured at ordinary
  lengths". `SDD.md` RN-4 answers "for NFR-1 only" on that reading, and § 2.8 of
  `products/tracker17/docs/trail/srs/cycle-1.md` sets NFR-1's volume in tasks and comments, with no
  length. If the question closes and nothing replaces that sentence, NFR-1 and AC-15 could be read
  at the new maximums. That is 1,000 tasks × 20 comments × 4,000 characters, which is 80,000,000
  characters of comment text. Nobody set NFR-1 against that volume or designed for it. So NFR-1
  says its bar is not set at the maximums, and AC-15's timed run states the text lengths it uses.
  The bar itself does not move. I did not measure how the tracker performs at the maximums, and
  this answer asserts nothing about it.

  *Addition (2), a test for the protected case (check 4, refused).* The draft adds a refusal and
  tests it under AC-12. It also adds a promise: "A value that the tracker's own field let the
  operator enter is never refused as too long." Nothing tests that promise. The case it protects
  is real at the source. A comment the field counted at 4,000 characters arrives one character
  longer for each line break. The SRS's own list of requirements with no criterion does not cover
  it. So an end-to-end test fills a comment and a project description to their field's maximum,
  with line breaks, through the browser, and both are saved. An end-to-end test is the right layer
  because the case exists only between the browser's count and the tracker's (`SRS.md` NFR-11).

  *Addition (3), DR-6.* The draft says DR-6 "may gain" an over-long saved value. It does gain it.
  `SDD.md` § 4 SD-5 already makes "every rule a slice adds" a check at start, and `SRS.md` AC-7
  tests "one per kind of break DR-6 names". If DR-6 names the break, the SRS's acceptance test and
  the SDD's check agree.

  *Narrowing.* The draft has FR-39 say that this is "the one refusal that does not show the typed
  text again". The SRS states no refusal's typed-text behaviour today. A search of `SRS.md` for
  "typed" finds only line 16, the ID convention, and FR-23, "stored exactly as typed". That
  behaviour belongs to `UXD.md` UX-I3 and `SDD.md` § 4 RT-8. An exception in FR-39 would amend a
  rule the SRS never states. So FR-39's new entry says the value is refused with its reason, which
  is FR-39's existing promise, and the reason for the missing text can go in a review note.

  *What a character is.* Infra measures a string in code units, so a character outside the basic
  plane counts as two in the field. The field then stops earlier than the stated number. "At most"
  still holds, and nothing typed is refused. The answer leaves the counting to `SDD.md` § 4 RT-10,
  inside the rule that what the field accepted is never refused, which the SDD's own answer
  already asks RT-10 to state.

  *Settled record (check 3).* FR-23's "stored exactly as typed" agrees with "never shortens". The
  non-blank rules in FR-10, FR-15, FR-20, FR-27 and FR-28 are lower bounds and do not interact with
  the maximums. No saved data exists yet to be made unreadable: `ls products/tracker17` printed
  `docs` and nothing else on 2026-10-06, the same day `SDD.md`'s answer recorded that.

  *Failure paths (check 4).* Empty: a description may be empty, and a blank required field is the
  non-blank rules'. Absent: nothing here depends on something that can be unreachable. Stale: a
  later, lower maximum would make saved data unreadable under DR-6, so lowering one needs a plan
  for existing data. That is a future change's to carry, and I record it here. Concurrent: a length
  belongs to one value. Refused: the new FR-39 entry and AC-12.

  *Downstream.* Once `product-srs` folds this, `SDD.md` is owed one change. RT-10 serves the new
  requirement, its sentence "No SRS requirement states a bound today" goes, and § 4 TS-3's table
  names the new identifier. I did not raise that on the SDD's companion. The identifier does not
  exist until the fold assigns it, and an item folded before the SRS states the requirement would
  point at nothing. The slot names the consequence so that it travels with the fold. The three
  downstream sentences the item lists are left as it says. `UXD_open_issues.md` § 2.1 already
  carries the UXD's. `DESIGN.md` RN-14's rule does not change. Whether `CONTENT.md` § Error's
  formula needs an exception is the Content Manager's, and the SDD's answer reached the same view.

  *Close call.* I weighed a plain *confirmed*. Addition (1) tipped it: closing the open question as
  drafted would remove the one sentence that limits NFR-1, and that loss shows up only at the
  timed run.

## Left for the owner

None this run.

## Skipped

None this run.

## Raised on this document

### 2.2 — The second open question is answered, and closes

- **What the document is owed:** the second item of `SRS.md` § Open Questions is removed, because
  the SDD has made the runtime choice it waits on. No requirement changes.
- **Why it is worth a cycle:** "Something upstream moved and it has not seen it", applied to the
  document the SRS hands its question to. The item says "AC-3 is the check once the SDD has chosen".
  `SDD.md` § 4 RT-1 has chosen, "Python 3.11 or later", and it ends "*settles SRS § Open Questions,
  the second item*", confirmed in `products/tracker17/docs/trail/sdd/cycle-1.md` § 2.1. An `[OPEN]`
  marker on a settled question is a false fact about the SRS's own state. The SRS is already owed a
  cycle for item 2.1, so this adds no run of its own.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SRS.md** — `<CORE>/launchers/skill/launcher.sh product-srs tracker17`
