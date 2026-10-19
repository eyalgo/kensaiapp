# SRS open issues — tracker17

> Companion to `SRS.md`. The CTO authored the SRS non-interactively; this file holds
> what it could not settle from the inputs (the PRD and any context/constraints).
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this
> file**, then re-run `product-srs`. It folds your answers into the SRS and drops the
> resolved items. When nothing is left open, `product-srs` **deletes this file**: no file =
> the SRS is done.
>
> Your answers are never thrown away. Each time the CTO folds them in, it first copies this
> file whole to `docs/trail/srs/` — so what you decided, and why, stays readable and citable
> for good.
>
> **§§ 1–2 are the CTO's own questions; § 3 is somebody else's.** A seat reading the SRS long after
> it settled can find a gap the authoring run had no way to see, and § 3 is where it says so.

> **Opened by a `companion-self-answer` run on 2026-10-06, not written by a `product-srs` run.** The
> SRS was settled and had no companion. The run was answering item 2.1 of
> `products/tracker17/docs/SDD_open_issues.md`, "Every text field has a maximum length", in the
> CPO's seat, and it confirmed the lengths. A length with a refusal behind it is a system
> requirement, and `products/tracker17/docs/SDD.md` § 12 says the SDD "changes no system
> requirement, which are the SRS's". The first item of `SRS.md` § Open Questions still reads "No
> maximum length is set". So the run opened this file to carry the change, and left `SRS.md`
> unchanged. Its reasoning is in `products/tracker17/docs/trail/sdd/self_answer-4.md`, under item
> 2.1.

Every `SDD §` reference below is to `products/tracker17/docs/SDD.md`, version 2. `SRS.md`,
`UXD.md`, `DESIGN.md` and `CONTENT.md` are the files of those names in `products/tracker17/docs/`.

---

## 1. Open issues — technical questions with no answer yet

None.

## 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override

### 2.1 The SRS states the maximum length of every text field, and a longer value is refused
- **Drafted into the SRS:** nothing yet. `SRS.md` § Open Questions, the first item, reads "No
  maximum length is set for a title, a name, a label, a description or a comment", and ends "A
  bound the operator would see goes back through the open-issues file." The bound came back that
  way, as item 2.1 of `products/tracker17/docs/SDD_open_issues.md`. That item was answered on
  2026-10-06 in the CPO's seat: confirmed, with two additions. The proposed change makes the answer
  a requirement of the SRS, in four places.
  - **A new requirement in § 3 states the lengths.** A project name, a task title, an assignee
    name, the operator's name and a label take at most 200 characters. A project description and a
    comment take at most 4,000. A longer value is refused under FR-39. The tracker never shortens
    a value.
  - **The same requirement protects what the form accepted.** A value that the tracker's own field
    let the operator enter is never refused as too long. The known case is a line break in a
    comment or a description, which the field counts as one character and the browser sends as
    two.
  - **FR-39's list gains the over-long value, and AC-12 then tests it.** This is the one refusal
    that does not show the typed text again. It still shows its reason.
  - **The first open question closes.** DR-6's examples of a broken rule may gain a saved value
    longer than its maximum, because SDD § 4 SD-5 already makes every data rule a check at start.
- **Rationale:** the lengths exist because of how a page learns what the last action did. SDD § 4
  RT-8 puts the typed text in the address of the page that answers a form, and Python's listener
  refuses an address longer than 65,536 bytes (SDD § 11 R-10). The answer on the SDD's item
  confirmed 200 and 4,000 characters as what the product accepts.

  Three things make the SRS the place for the rule, and each is this run's reasoning from the
  sentence quoted.
  - SDD § 12 says the SDD "changes no system requirement, which are the SRS's". A refusal the
    operator can meet is a requirement of the kind FR-39 lists.
  - AC-12 tests "Each refusal FR-39 lists". A refusal the list does not carry has no acceptance
    test.
  - SDD § 4 TS-3 has each feature module name "the SRS requirements the module realizes", and
    TS-4's test fails when "a requirement identifier named there is not in" `SRS.md`. A rule the
    code enforces with no identifier here is a rule the trace of PRD § Success Metrics, Simple to
    read, cannot reach.

  The requirement would be marked the way the SRS marks a call the PRD does not make. The PRD
  names the fields and sets no length (PRD § Core Features), and the confirmation is in the
  answered round that `product-sdd` copies to `products/tracker17/docs/trail/sdd/` when it folds.

  The line-break case rests on the HTML standard. A multi-line field's length is taken from its
  value "with newlines normalized"
  (https://html.spec.whatwg.org/multipage/form-elements.html, the `textarea` element), and to
  normalize is to "replace every U+000D CR U+000A LF code point pair with a single U+000A LF code
  point" (https://infra.spec.whatwg.org/). On submission the standard has the browser replace each
  lone line break "by a string consisting of U+000D (CR) and U+000A (LF)"
  (https://html.spec.whatwg.org/multipage/form-control-infrastructure.html, "Converting an entry
  list to a list of name-value pairs"). `DESIGN.md` § Components says "a comment is multi-line and
  keeps the line breaks the operator typed". So a comment the field counted at 4,000 characters
  arrives longer by one character for each line break. How the tracker counts is the SDD's. That
  the operator is never refused for it is the requirement.

  The over-long refusal cannot show the typed text again, because that text is what an address
  cannot hold. Only a request the tracker's own pages did not send can reach it, since the field
  stops at its length. UXD UX-I3's "Everything the operator typed stays in the form" is therefore
  untouched for every form.
- **If overridden:** if the SRS takes no requirement, the lengths stay in the SDD alone. The first
  open question then says no length is set while SDD § 4 RT-10 sets one. No acceptance criterion
  tests the refusal, and no requirement identifier exists for the code to name.

  The lengths themselves are the answer already given on the SDD's item, and SDD § 4 RT-10 sizes
  them to the address. An override that changes a length moves RT-10 with it, and the fields of
  any one form must still fit one address, which the SDD's item puts at "about 5,000 characters in
  the worst case".

  Three sentences downstream lean on the open question this item closes, and none of them is this
  run's to change.
  - `UXD.md` § Open Questions, the second item, says "No maximum length is set upstream".
    `products/tracker17/docs/UXD_open_issues.md` § 2.1 carries that to the UXD.
  - `DESIGN.md` RN-14 gives "no maximum length is set upstream" as one reason that long text
    wraps. The rule it supports does not change: a value of 200 or 4,000 characters still wraps.
  - `CONTENT.md` § Error has a refusal quote "any typed value". The over-long refusal cannot quote
    its value. The words of that refusal are written with the change that builds it, and whether
    the formula needs an exception is the Content Manager's.
- **Confirm or override:** confirm, with three additions and one narrowing. The SRS states the lengths as drafted: at most 200 characters for a project name, a task title, an assignee name, the operator's name and a label, and at most 4,000 for a project description and a comment. A longer value is refused under FR-39, and the tracker never shortens a value. A value the tracker's own field let the operator enter is never refused as too long. How a character is counted is the SDD's (RT-10), within that rule. (1) NFR-1 keeps its measurement at ordinary lengths. The open question that closes is also where the SRS says "NFR-1 is measured at ordinary lengths", and SDD RN-4 answers for NFR-1 on that reading only. So NFR-1 says that its bar is not set at the new maximums, and AC-15 says that its timed run states the text lengths it uses. 1,000 tasks with 20 comments of 4,000 characters is 80,000,000 characters, a volume nobody set NFR-1 against. (2) The protected case gets its own test. An end-to-end test fills a comment and a project description to their field's maximum, with line breaks, through the browser, and both are saved. Without it, the rule that protects what the form accepted has no acceptance criterion. (3) DR-6 does gain "a saved value longer than its maximum", so AC-7 tests it, as SDD § 4 SD-5 already requires. Narrowing: FR-39's new entry says only that the value is refused with its reason. The draft's "the one refusal that does not show the typed text again" stays out of FR-39. The SRS states no refusal's typed-text behaviour today, which is UXD UX-I3's and SDD RT-8's. The reason can go in a review note. The first open question closes in full: SDD RN-4 answers its NFR-1 half, and this answer closes its bound half. Downstream, once this is folded, the SDD is owed one change. RT-10 serves the new requirement, its sentence "No SRS requirement states a bound today" goes, and § 4 TS-3's table names the new identifier. Reasoning in `products/tracker17/docs/trail/srs/self_answer-2.md`.

### 2.2 The second open question is answered, and closes

> **Raised by a `companion-self-answer` run on 2026-10-06, not written by a `product-srs` run.** That
> run was answering item 2.1 and read `SRS.md` whole. The second item of `SRS.md` § Open Questions
> still reads as open, but the SDD has answered it. This run's reasoning is in
> `products/tracker17/docs/trail/srs/self_answer-2.md`, under § Raised on this document.

- **Drafted into the SRS:** nothing yet. The second item of `SRS.md` § Open Questions reads "The
  prerequisites FR-4 names follow from the SDD's choice of runtime, and C-7's ten-minute bound is
  measured against them. AC-3 is the check once the SDD has chosen." The proposed change removes
  that item. No requirement changes. FR-4 already lists the prerequisites in general terms, C-7
  already sets the bound, and AC-3 already checks it.
- **Rationale:** the SDD has made the choice the item waits for. SDD § 4 RT-1 reads "The tracker
  runs on Python 3.11 or later and imports nothing outside the Python standard library". It ends
  "*settles SRS § Open Questions, the second item*", and it is confirmed in
  `products/tracker17/docs/trail/sdd/cycle-1.md` § 2.1. An item marked `[OPEN]` that is no longer
  open says the SRS still waits on something. The runtime itself stays the SDD's, because it is
  how the system is built and not what it must do. So this change closes the question and copies
  nothing from RT-1 into the SRS.
- **If overridden:** the item stays, and the SRS keeps reading as if it waits on a choice already
  made. Copying the runtime into FR-4 is the other option. It would put a design choice in the
  SRS, and the SRS's own header keeps the how out ("Keep the **how** … out").
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

## 3. Raised from downstream — an item from a seat that did not write the SRS

None.
