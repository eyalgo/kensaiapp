# ADR-0011: Keep no session, carry what a page says about the last action in its address, and count only a `post` form as a submission

**Status:** Superseded by ADR-0014
**Date:** 2026-10-27

## Context

The browser's back, forward and reload buttons must work on every page (UXD § 4), and reloading
must never repeat an action. The page that answers an action has to say what happened, open at the
place of the action (ADR-0003) and, after a refusal, keep what was typed (UXD UX-I3, UX-I4). The
saved data holds no record of requests (SRS NFR-6). With no login there is no session to hang any of
this on.

ADR-0006 decided this on 2026-10-06 and said every form submission is answered by sending the
browser to a page address. It did not say what a submission is. The project page then gained a
filter form sent with `method="get"` (`web/pages.py`, the form `_filter_area` builds), whose Apply,
reload and Clear are answered with the page itself, 200. The HTML standard's form submission
algorithm covers a `get` form too: for `http` and `https` its GET column is "Mutate action URL"
(https://html.spec.whatwg.org/multipage/form-control-infrastructure.html, read 2026-10-27). Held to
that word, ADR-0006 owed the filter form a redirect, and it owes one to the sort controls and the
All tasks list's controls (SRS FR-36; UXD UX-S7) that come next. SDD version 12 § 4 RT-8 defines the
word (SDD RN-53), and this record follows it.

## Decision

The tracker keeps nothing between requests except the tracker state. There is no cookie and no
session. What a page shows is a function of the tracker state and the page's address.

A submission is a form sent with `method="post"`: a request that asks the tracker for a change.
Only a submission changes the tracker state. Following a link, reloading a page or sending a form
with `method="get"` never does.

Every submission is answered by sending the browser to a page address. What that page says about the
action travels in the address and nowhere else: the place the page opens at, what a completion line
names and, after a refusal or a failure, the reason and what was typed. One function in `web` builds
every such address. After the one refusal for a value longer than its field's maximum, the address
carries the reason and the place and nothing that was typed.

A form sent with `method="get"` is a read. The browser builds its address from the form's values
(SDD § 4 EX-3; UXD UX-I7), and the tracker answers that address with the page, 200, as it answers a
link: it saves nothing and sends no redirect. Its refusal — a from-date after the to-date, a name not
on the list, a value its control cannot hold — is answered with the page at the asked address, the
reason beside the control (SDD § 4 EX-4). No address is built for it, because the address already
carries what was typed. A `post` sent from a narrowed list takes the redirect, and the narrowed page
it lands on is a read.

The redirect exists so that an action is never repeated. A `get` form changes nothing, and a read
repeated is what UXD UX-I7 asks for.

## Alternatives ruled out

- **A store in `web` for the outcome of the last submission.** It lost because the tracker would
  keep state between requests, and it would need a rule for what a reload shows once that outcome is
  gone (SDD § 9 TO-7).
- **Answering a refused `post` form on the spot**, with the page itself rather than an address, so
  typed text never enters an address. It lost because every submission is answered with an address
  so that reload, back and forward never repeat an action (SDD RN-25).
- **Counting a `get` form as a submission**, the standard's word, and redirecting it. It lost because
  SDD § 4 SEC-2 marks a request opened from a bookmark `none` "so a page opens on it and a submission
  does not", and UXD UX-I7 and SDD § 4 EX-3 require a bookmarked narrowed list to open: a `get` form
  counted as a submission would be refused where the UXD has it open. The redirect would also buy
  nothing, because a `get` form has no action to repeat (SDD RN-53).
- **Keeping ADR-0006 and leaving the word undefined.** It lost because ADR-0006's Decision is a
  standing rule the delivery tier reads as fixed. A change cut from it alone, held to the standard's
  word, would owe every `get` form a redirect.

## Consequences

Easier: the tracker keeps nothing between requests. Every submission is answered one way. A reload,
or a return through back, shows the same page with the same line at the same place, and never
repeats the action. A narrowed or ordered list is a page address the operator can reload, share
with themselves through a bookmark, or reach through back, with nothing saved.

Harder (SDD § 9 TO-7): an address copied or bookmarked straight after an action shows that action's
line again. Text typed into a refused form appears in the browser's history; the CDO accepted that a
reload shows the completion line again (SDD RN-20). Typed text has to fit in an address, which is why
every text field is bounded (ADR-0007), and after the over-long refusal the page gives the reason and
not the text. A reader holding the browser's word meets a form the browser calls submitted and this
record calls a read, and has to read the definition. A `get` form that changes state is refused by
this record, and the route test that enumerates `web`'s routes catches it.

Undoing the address rule costs a store in `web` for the last outcome, a rewrite of SDD § 4 RT-7 and
RT-8, and a rule for what a reload shows once the outcome is gone. Undoing the definition — counting
a `get` form as a submission — costs a redirect for every list control, a move of SDD § 4 SEC-2's
marking rule, and a UXD change, because a bookmarked narrowed list would no longer open. `domain`,
`application` and `persistence` are untouched by either.

**Dependence:** the length of address the listener accepts. Python's `http.server` refuses a request
line longer than 65,536 bytes (SDD § 11 R-10, quoting `handle_one_request` on Python 3.14.7). The
longest `post` form, a project's name and description together, is sized to stay under 51,000 bytes
of it. A `get` form's values travel in the address too: the filter's seven keys stay under 6,000
bytes, and only an address hand-typed with a key repeated, which the tracker's own pages do not
send, can pass the limit (SDD § 11 R-10). A Python that lowers the limit reopens this record and
ADR-0007. The word "submission" rests on the HTML standard's form submission algorithm, which this
record departs from on purpose; a change to that algorithm does not move this decision.

## Traces to

- Supersedes `products/tracker17/docs/adr/0006-last-action-travels-in-the-page-address.md`, whose
  decision, alternatives and consequences this record carries whole.
- `products/tracker17/docs/SDD.md` § 4 RT-7, RT-8, SEC-2, EX-3, EX-4; § 9 TO-7; § 11 R-10; SDD
  Review Notes RN-20, RN-21, RN-24, RN-25, RN-53.
- `products/tracker17/docs/trail/architecture/cycle-14.md` § 3.1 — the answer that settled the
  supersession, raised by the PM from the filter form, with its reasoning at
  `products/tracker17/docs/trail/architecture/self_answer-18.md` § 3.1.
- `products/tracker17/docs/trail/sdd/cycle-9.md` § 5.1 — the CTO-seat answer that defined the word,
  reasoning at `products/tracker17/docs/trail/sdd/self_answer-12.md` § 5.1.
- `products/tracker17/docs/trail/sdd/cycle-1.md` § 2.3 and `products/tracker17/docs/trail/sdd/cycle-2.md`
  § 2.1 — the answers whose consequences RN-21 and RN-24 carry.
- `products/tracker17/docs/SRS.md` NFR-4, NFR-6, FR-33, FR-34, FR-36; `products/tracker17/docs/UXD.md`
  § 4, UX-I3, UX-I4, UX-I6, UX-I7, UX-S7.
- `products/tracker17/web/pages.py`, the `method="get"` form `_filter_area` builds;
  `products/tracker17/web/routes.py`, `ROUTES` (every `POST` route `SUBMISSION`) and
  `_carried_filters`, read 2026-10-27 at `c838e9b62`.

## Binds

QC-7, QC-8.
