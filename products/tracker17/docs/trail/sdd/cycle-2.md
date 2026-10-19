# SDD open issues — tracker17

> Companion to `SDD.md`. The CTO wrote the SDD; this file holds what that run could not settle from
> its inputs (the PRD, the SRS, the UXD, and any context or constraints), and the calls that are the
> CPO's or the CDO's to make. An item whose call is the CPO's or the CDO's carries that seat's
> `Seat:`; an item whose call is the CTO's carries `cto` or no `Seat:` field.
>
> **Answer inline** — fill each **Answer** / **Confirm or override** / **Keep or re-cut** /
> **Your call** slot — **commit this file**, then re-run `product-sdd`. It folds your answers into
> the SDD and drops the resolved items. When nothing is left open, `product-sdd` **deletes this
> file**: no file = the SDD is done.
>
> Your answers are never thrown away. Each time `product-sdd` folds them in, it first copies this
> file whole to `docs/trail/sdd/` — so what you decided, and why, stays readable and citable for good.
>
> **An item may name the seat that answers it.** Any item in any section carries an optional
> `- **Seat:** <seat>` field beside its other fields. Its value is the name of the agent whose posture
> answers the item — `cto`, `cpo` or `cdo`. An item with no usable value, whether the field is absent,
> empty or still the `<seat>` placeholder, is answered in the seat of the skill that produced this file.
> The field names the *answering* seat. It is not the seat that raised the item (`Raised by:` /
> `Held by:`), and it is not the document an answer belongs to.
>
> **An item in §§ 1–3 names the seat that raised it.** An item the CPO raised is a product call and
> an item the CTO raised is a technical one, and the answer that settles one does not settle the
> other. **§ 4 names two seats and no raiser** — a
> disagreement is not something one seat asked, it is two positions held by different seats, and the
> answer that settles it picks between them.
>
> **§ 5 names a raiser from outside the SDD's lanes entirely.** §§ 1–4 are all the SDD's own three
> lane seats; § 5 is a seat that never held a lane in it, reading it long after it settled and
> finding something only the SDD can fix. Its `Raised by:` therefore takes a wider set than §§ 1–3's,
> which stay fixed to the three lane seats on purpose.

Every `SDD §` reference below is to `products/tracker17/docs/SDD.md`, version 2. `PRD`, `SRS` and
`UXD` are `products/tracker17/docs/PRD.md`, `products/tracker17/docs/SRS.md` and
`products/tracker17/docs/UXD.md`. The first round's seven items, with their answers, are kept whole
at `products/tracker17/docs/trail/sdd/cycle-1.md`. All seven are folded into the SDD and none is
carried over. The one item below is new in this round.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — a best-effort answer was drafted; confirm or override

### 2.1 Every text field has a maximum length
- **Raised by:** CTO
- **Seat:** cpo
- **Drafted into the SDD:** SDD § 4 RT-10, § 9 TO-7, § 11 R-10 and SDD Review Notes RN-22. A
  project name, a task title, an assignee name, the operator's name and a label take at most 200
  characters. A project description and a comment take at most 4,000. The field's own `maxlength`
  attribute stops the browser at that length, so an operator typing or pasting into the tracker's
  own pages cannot send more. `domain` refuses a longer value that arrives any other way.
- **Rationale:** SDD § 4 RT-7 keeps nothing between requests, and RT-8 answers every form
  submission by sending the browser to a page address. What that page says about the action
  therefore travels in the address: the place the page opens at, the name a completion line gives,
  and, after a refusal, the reason and the text that was typed. The first round's answer on the
  page model rests on the same reading (`products/tracker17/docs/trail/sdd/self_answer-3.md`, "so
  the place and the line travel in the address"). An address has a limit. Python's listener
  refuses a request line longer than 65,536 bytes: on the machine's Python 3.14.7, `http.server`'s
  `handle_one_request` reads `if len(self.raw_requestline) > 65536:` followed by
  `self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)`. No document bounds any text today. SRS § Open
  Questions says "No maximum length is set for a title, a name, a label, a description or a
  comment", and `products/tracker17/docs/DESIGN.md` § Layout says "Long text wraps, and the
  stylesheet shortens nothing". With no bound, a refused comment that is long enough, or the
  deletion of a task whose title is long enough, sends the browser to an address the tracker
  cannot open. The same SRS item says where a bound goes: "A bound the operator would see goes
  back through the open-issues file." The two lengths are the SDD's own values. They are sized so
  that the longest form, a project's name and description together, fits: 4,200 characters at no
  more than 12 bytes each in an address is 50,400 bytes.
- **If overridden:** three other answers are open, and each moves different text.
  - *Other lengths.* Only the numbers in SDD § 4 RT-10 change. The fields of any one form must
    still fit together in 65,536 bytes, which is about 5,000 characters in the worst case.
  - *No bound.* SDD § 4 RT-10 is removed and § 11 R-10 stays as a risk with no response. Past the
    limit, the page an action opens cannot carry the typed text or the deleted thing's name. Two
    UXD sentences then stop holding at those lengths: UX-I3's "Everything the operator typed stays
    in the form", and UX-F9's "a confirmation naming the deleted task". That is an experience
    cost, so this answer also needs the CDO, and the SDD needs a rule for what `web` sends
    instead.
  - *The tracker remembers the last action.* `web` keeps the outcome of the last submission in
    memory. SDD § 4 RT-7 and RT-8 are rewritten and § 9 TO-7 is undone. A reload after a later
    action, or after a restart, no longer shows the line, which changes what the first round's
    answer on the page model accepted (SDD Review Notes RN-20). That is an experience cost too.

  If the draft is confirmed, the SDD records the bound as its own addition. The SRS has no
  requirement for it: SRS FR-39's list of refusals and AC-12's tests would gain the over-long
  value, and the SRS open question quoted above would close. `products/tracker17/docs/CONTENT.md`
  would gain the refusal's words. Those are revisions of those documents, made by their own seats.
  No slice in SDD § 6 changes its slug or its place under any of the four answers.
- **Confirm or override:** confirm, with two additions. Every text field has a maximum length, at the drafted values: 200 characters for a project name, a task title, an assignee name, the operator's name and a label, and 4,000 for a project description and a comment. A longer value is refused, and the tracker never shortens one. (1) A value that the tracker's own field let the operator enter is never refused as too long. The known case is a line break in a comment or a description: the field counts it as one character and the browser sends it as two, so the field and `domain` must count the same text the same way. RT-10 states that rule, and says what it counts as one character, so that its 12 bytes for each character holds. The means are the CTO's. (2) The over-long refusal is the one refusal whose page does not carry the typed text, because that text is what an address cannot hold. Its page still opens and still says why. RT-8 and RT-10 say so. Only a request the tracker's own pages did not send can reach this refusal, so UXD UX-I3's "Everything the operator typed stays in the form" holds for every form. Two changes belong to other documents and are carried there. The lengths are a system requirement, and `products/tracker17/docs/SRS_open_issues.md` § 2.1 carries them to the SRS. Until the SRS states them, RT-10 stands on this answer. Whether a page tells the operator a field's maximum is an experience call, and `products/tracker17/docs/UXD_open_issues.md` § 2.1 carries it to the UXD. Reasoning in `products/tracker17/docs/trail/sdd/self_answer-4.md`.

### 2.2 The SDD's references to the SRS catch up with SRS version 3

> **Raised by a `companion-self-answer` run on 2026-10-06, not written by a `product-sdd` run.** That
> run was answering item 2.2 of `products/tracker17/docs/SRS_open_issues.md`, and read `SDD.md` while
> checking it. `SRS.md` version 3 now states the maximum text lengths as FR-40 and adds AC-20, and its
> first open question has closed. The SDD has not seen that. This item is unrelated to item 2.1 above,
> whose answer stands as written. This run's reasoning is in
> `products/tracker17/docs/trail/srs/self_answer-3.md`, under § Companions opened.

- **Raised by:** CTO
- **Seat:** cto
- **Drafted into the SDD:** nothing yet. The proposed change makes three edits:
  - § 4 RT-10 serves SRS FR-40, with FR-39 and DR-6. Its sentence "No SRS requirement states a bound
    today, and SRS § Open Questions, the first item, sends 'A bound the operator would see' back
    through the open-issues file" is removed.
  - SDD Review Notes RN-4 and RN-22 cite "SRS § Open Questions, the first item". That item no longer
    exists. They cite where it closed instead, `products/tracker17/docs/trail/srs/cycle-2.md` § 2.1.
    § 4 RT-1 says "settles SRS § Open Questions, the second item", and RN-3 says the open question
    "hands the runtime to this document". Both name the question by what it asked, the runtime that
    FR-4's prerequisites follow from, and not by its place in the list.
  - § 6 gives the new SRS items a slice. FR-40 is named in *Traces to* in each slice whose forms
    take text. AC-20's end-to-end test goes in `comment-on-a-task`. That slice adds comments, the
    later of the two fields AC-20 fills, and the description arrives earlier, in `first-project`. AC-7's test of an over-long saved value goes in
    `protect-saved-data`, the slice that already owns the page for saved data that cannot be read.

  No requirement changes, no slice changes its slug or its place, and RT-10's lengths stay as item
  2.1's answer leaves them.
- **Rationale:** RT-10 contains a statement that is now false. `SRS.md` FR-40 reads "A project name, a
  task title, an assignee name, the operator's name and a label each take at most 200 characters",
  and the SRS's Version line reads "the first open question closes". Item 2.1's answer says "Until
  the SRS states them, RT-10 stands on this answer", and the SRS now states them. The
  positional reference in RT-1 is already wrong: `SRS.md` § Open Questions has one item, not two.
  `SRS_open_issues.md` § 2.2 proposes closing that last item. A reference by subject stays true
  whichever of `product-srs` and `product-sdd` folds first. A reference by position breaks under either
  order. No slice in § 6 names FR-40 or AC-20 today. `grep -n "FR-40\|AC-20" SDD.md` returned
  nothing on 2026-10-06. Without a slice, no slice's test delivers the requirement, and the trace in
  § 4 TS-3 cannot reach its code.
- **If overridden:** the SDD keeps citing SRS items that no longer exist, and RT-10 keeps saying no
  requirement bounds the text. If a different slice placement is chosen, only the § 6 edit changes.
  The other two edits do not depend on it.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

## 3. Cut calls to confirm — where the slicing could reasonably have gone another way

None.

---

## 4. Disagreements — two seats hold different positions and neither yields

None.

## 5. Raised from downstream — an item from a seat that did not write the SDD

None.
