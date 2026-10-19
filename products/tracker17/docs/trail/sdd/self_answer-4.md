# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-06
- **Sources re-read:** six sources outside this repository, each read on 2026-10-06. The five web
  pages were read through a page fetch that returned quoted passages.
  - The machine's Python. `python3 --version` printed `Python 3.14.7`. The source of
    `http.server.BaseHTTPRequestHandler.handle_one_request`, printed with `inspect.getsource`, holds
    `self.raw_requestline = self.rfile.readline(65537)`, then `if len(self.raw_requestline) >
    65536:`, then `self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)`. `urllib.parse.quote` returned
    12 bytes for the one code point U+1F600 and 9 for U+20AC.
  - https://raw.githubusercontent.com/python/cpython/3.11/Lib/http/server.py. The same three lines
    are in Python 3.11, which is the floor `SDD.md` § 4 RT-1 sets.
  - https://chromium.googlesource.com/chromium/src/+/main/docs/security/url_display_guidelines/url_display_guidelines.md.
    Under "URL Length" it says "Chrome limits URLs to a maximum length of 2MB".
  - https://html.spec.whatwg.org/multipage/form-control-infrastructure.html. Under "Limiting user
    input length: the `maxlength` attribute" it says "User agents may prevent the user from causing
    the element's API value to be set to a value whose length is greater than the element's maximum
    allowed value length." Under "Converting an entry list to a list of name-value pairs" it has the
    browser replace each lone line break "by a string consisting of U+000D (CR) and U+000A (LF)".
  - https://html.spec.whatwg.org/multipage/form-elements.html and https://infra.spec.whatwg.org/. A
    `textarea`'s API value is "the element's raw value, with newlines normalized", and to normalize
    is to "replace every U+000D CR U+000A LF code point pair with a single U+000A LF code point".
  - tracker16-X, at `task-tracker-X`. `grep -rniE
    'max(imum)?[ _-]?len|length|characters'` over `docs/fdr.md` and `tasktracker16x/domain/*.py`
    printed no line.

The companion held one open item, 2.1, and the invocation listed none, so this run worked it.

## Items worked

### 2.1 — Every text field has a maximum length

- **Bucket:** 2. Choices to confirm — a best-effort answer was drafted; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft is confirmed at its own values: at most 200 characters for a project name, a
  task title, an assignee name, the operator's name and a label, and at most 4,000 for a project
  description and a comment. Two additions close cases the draft's own mechanism leaves open. Two
  consequences belong to other documents and were raised there.

  *Seat.* This item is the CPO's, and this run answered it in that seat. The item carries `Seat:
  cpo`, and `SDD.md` RN-22 says "the seat that answers is the CPO" because "What the product
  accepts as a title or a comment is product scope." The answer commits nobody outside the
  product, and I can name no ground the owner holds that this run could not see.

  *The draft holds, and the product reason is not the one it gives (check 2).* The draft argues
  from the address: `SDD.md` § 4 RT-8 puts typed text in it, and the listener refuses one longer
  than 65,536 bytes. That argument is sound, and I checked each step of it (Sources re-read). The
  limit is the same at the Python floor as on the owner's machine. The browser is not a tighter
  limit, since `SRS.md` NFR-13 supports Chromium-based browsers and Chromium takes an address up
  to 2MB. Twelve bytes is the most one code point costs in an address, and 4,200 of them is 50,400
  bytes. The item's question to this seat is a different one: does the product accept the bound?
  It does, for three reasons.
  - No upstream document names a use that needs longer text. `PRD.md` § Core Features gives each
    field and no length.
  - The predecessor has no rule to keep. Its definition and its rule code state no length (last
    source above), so `SRS.md` C-5 does not reach the question. `SRS.md` RN-19 reads a like case
    the same way: "tracker16-X has no rule here".
  - Each alternative the item lists costs the product more. With no bound, the item says "the page
    an action opens cannot carry the typed text or the deleted thing's name", so a refusal's
    reason would sit on a page that fails to open. `PRD.md` § UX Notes requires that a refusal
    "tells the operator the reason in plain words". Remembering the last action adds state
    between requests, where `SDD.md` § 4 RT-7 keeps none. That is one more part for the reader,
    and `PRD.md` § Risks names "A web interface adds parts" as the product's first risk.

  The values stand as drafted. The item puts the ceiling for one form at "about 5,000 characters
  in the worst case", so 4,000 is close to the most a comment could be given under this page
  model. I have no ground to move 200.

  *Addition (1), a case the draft's mechanism misses.* The item says the field's `maxlength`
  attribute means "an operator typing or pasting into the tracker's own pages cannot send more".
  That does not hold for a field with line breaks. The HTML standard counts a `textarea`'s length
  with each line break as one character, and has the browser send each as two (fourth and fifth
  sources). `DESIGN.md` § Components says "a comment is multi-line and keeps the line breaks the
  operator typed". So a comment the field accepted at 4,000 characters arrives longer, and
  `domain` would refuse text the page had just allowed. The addition states the outcome: a value
  the tracker's own field accepted is never refused as too long. How the two sides count is the
  CTO's. The addition also asks RT-10 to say what one character is, because its "at most 12 bytes"
  is true of one Unicode code point and not of every unit a reader might take "character" to mean.

  *Addition (2), the refusal that cannot keep its own promise (check 4, refused).* `SDD.md` § 4
  RT-8 has the page after a refusal carry "the reason and what was typed". For the over-long
  refusal, what was typed is the one thing an address cannot hold. As drafted, a hand-made request
  with a very long value is refused by `domain` and then sent to an address the listener rejects,
  which is `SDD.md` § 11 R-10 again. The addition makes this the one refusal whose page carries no
  typed text. The page still opens and still gives the reason. `UXD.md` UX-I3's "Everything the
  operator typed stays in the form" is not touched. Once addition (1) holds, the tracker's own
  forms cannot produce an over-long value: every field stops at its length, and every value a
  page puts into a field was saved under the same rule.

  *What belongs to other documents (check 1, asked of each consequence).* The item says "the SDD
  records the bound as its own addition" and that the other documents' revisions are "made by
  their own seats". Nothing would have told those seats. Two companions were opened (§ Companions
  opened).
  - **`SRS.md`.** A refusal the operator can meet is a system requirement, and `SDD.md` § 12 says
    the SDD "changes no system requirement, which are the SRS's". After the fold, the first item
    of `SRS.md` § Open Questions, "No maximum length is set", would be false. `SRS.md` AC-12 tests
    "Each refusal FR-39 lists", so an unlisted refusal has no acceptance test. `SDD.md` § 4 TS-3
    has each feature module name "the SRS requirements the module realizes", so a rule with no
    identifier breaks the trace that `PRD.md` § Success Metrics, Simple to read, checks.
  - **`UXD.md`.** A field with a maximum takes no text past it, and nothing tells the operator
    (fourth source). A comment and a project description cannot be changed once saved: `PRD.md`
    § Core Features says "Comments can't be edited or deleted", and `UXD.md` UX-F2 says "the
    description cannot be changed after the project is created". A paste cut short in either is
    permanent. Whether and how a page states a field's maximum is an experience call, so the item
    there states the need and leaves the form of it to the CDO.
  - **`PRD.md` is owed nothing.** No sentence of it becomes false. It names the fields and sets no
    length, as it sets none of the non-blank rules the SRS added (`SRS.md` RN-1, RN-19).
  - **`CONTENT.md` and `DESIGN.md` are not reopened.** `CONTENT.md` already has a formula for a
    refusal and one for an instruction beside a field. `DESIGN.md` RN-14 cites the SRS open
    question as a reason, and the rule the reason supports does not change. The SRS item names
    both sentences, so the round that closes the open question can carry them on.

  *Checked against the settled record (check 3).* `SRS.md` FR-23 has a label "stored exactly as
  typed", and the answer refuses and never shortens. `SDD.md` § 4 SD-5 says "every rule a slice
  adds is also a check at start", so saved data holding a longer value reads as unreadable. That
  follows from the settled text and needed no addition. No saved data exists yet: `ls
  products/tracker17` printed `docs` and nothing else on 2026-10-06. `SDD.md` RN-4 still stands,
  because it answers for `SRS.md` NFR-1 only. No slice in `SDD.md` § 6 moves, as the item says.

  *Failure paths (check 4).* Empty: a description is optional and may be empty, and a blank
  required field is the non-blank rule's. Absent: the answer depends on nothing that can be
  unreachable at run time. Stale: lowering a length later would make data saved under the old
  length unreadable under SD-5, so a lower length needs a plan for existing data. Raising one is
  bounded by the address. Concurrent: a length is a property of one value, and two tabs do not
  interact with it. Refused: addition (2), and the browser's own quiet stop, which is the UXD
  item.

  *Named and not covered.* The HTML standard measures a field's length in UTF-16 code units, and
  Python measures a string in code points. A character outside the basic plane counts as two in
  the field and one in `domain`. The field is the stricter, so nothing typed is refused, but a
  field may stop before the stated number. The size of a request body is not bounded by this
  answer: a hand-made request can send any amount, and the length rule refuses it only after it
  is read. Whether surrounding spaces are counted is not ruled. This run did not test what
  Chromium does with a paste longer than a field's maximum. All four are the CTO's.

  *The item's supporting text.* Two sentences are reported and not corrected. "The SDD records the
  bound as its own addition" sits against `SDD.md` § 12, as above. "`CONTENT.md` would gain the
  refusal's words" sits against `CONTENT.md`'s own header, which says it "holds **no per-change
  copy**".

  *Close calls.* I weighed overriding to hold RT-10 out of the SDD until the SRS states the
  requirement. I did not, because the SRS sent the question here ("A bound the operator would see
  goes back through the open-issues file") and R-10 needs its response whichever document states
  the rule first. I weighed leaving the UXD alone, since no sentence of it is false today. What
  tipped it is that the two fields which can be cut are the two that can never be corrected. I
  noticed a fourth alternative the item does not list: answering a refused form on the spot, so
  that typed text never enters an address. It would rewrite RT-8, which is the CTO's, and this
  seat does not weigh it.

## Left for the owner

None this run.

## Skipped

None this run. Sections 1, 3, 4 and 5 of the companion each read "None."

## Companions opened

- **products/tracker17/docs/SRS_open_issues.md** — **opened** — companion to `SRS.md`, landed in commit `c589cb948`
- **products/tracker17/docs/UXD_open_issues.md** — **opened** — companion to `UXD.md`, landed in commit `6ece08ba1`

Both were routed by item 2.1's answer, whose slot names them. Each holds one item, 2.1, under
choices to confirm, with its slot left open for that document's own round.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
- **products/tracker17/docs/SRS.md** — `<CORE>/launchers/skill/launcher.sh product-srs tracker17`
- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/skill/launcher.sh product-uxd tracker17`
