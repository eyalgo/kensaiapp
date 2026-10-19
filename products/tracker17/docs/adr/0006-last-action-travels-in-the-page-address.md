# ADR-0006: Keep no session, and carry what a page says about the last action in its address

**Status:** Accepted
**Date:** 2026-10-06

## Context

The browser's back, forward and reload buttons must work on every page (UXD § 4), and reloading
must never repeat an action. The page that answers an action has to say what happened, open at the
place of the action (ADR-0003) and, after a refusal, keep what was typed (UXD UX-I3, UX-I4). The
saved data holds no record of requests (SRS NFR-6). With no login there is no session to hang any of
this on.

## Decision

The tracker keeps nothing between requests except the tracker state. There is no cookie and no
session. What a page shows is a function of the tracker state and the page's address.

Only a form submission changes the tracker state. Following a link or reloading a page never does.
Every submission is answered by sending the browser to a page address. What that page says about
the action travels in the address and nowhere else: the place the page opens at, what a completion
line names and, after a refusal or a failure, the reason and what was typed. One function in `web`
builds every such address. After the one refusal for a value longer than its field's maximum, the
address carries the reason and the place and nothing that was typed.

## Alternatives ruled out

- **A store in `web` for the outcome of the last submission.** It lost because the tracker would
  keep state between requests, and it would need a rule for what a reload shows once that outcome is
  gone (SDD § 9 TO-7).
- **Answering a refused form on the spot**, with the page itself rather than an address, so typed
  text never enters an address. It lost because every submission is answered with an address so that
  reload, back and forward never repeat an action (SDD RN-25).

## Consequences

Easier: the tracker keeps nothing between requests. Every submission is answered one way. A reload,
or a return through back, shows the same page with the same line at the same place, and never
repeats the action.

Harder (SDD § 9 TO-7): an address copied or bookmarked straight after an action shows that action's
line again. Text typed into a refused form appears in the browser's history; the CDO accepted that a
reload shows the completion line again (SDD RN-20). Typed text has to fit in an address, which is why
every text field is bounded (ADR-0007), and after the over-long refusal the page gives the reason and
not the text.

Undoing it costs a store in `web` for the last outcome, a rewrite of SDD § 4 RT-7 and RT-8, and a
rule for what a reload shows once the outcome is gone. `domain`, `application` and `persistence` are
untouched.

**Dependence:** the length of address the listener accepts. Python's `http.server` refuses a request
line longer than 65,536 bytes (SDD § 11 R-10, quoting `handle_one_request` on Python 3.14.7). The
longest form, a project's name and description together, is sized to stay under 51,000 bytes of it.
A Python that lowers the limit reopens this record and ADR-0007.

## Traces to

- `products/tracker17/docs/SDD.md` § 4 RT-7, RT-8; § 9 TO-7; § 11 R-10; SDD Review Notes RN-20,
  RN-21, RN-24, RN-25.
- `products/tracker17/docs/trail/sdd/cycle-1.md` § 2.3 and `products/tracker17/docs/trail/sdd/cycle-2.md`
  § 2.1 — the answers whose consequences RN-21 and RN-24 carry.
- `products/tracker17/docs/SRS.md` NFR-6; `products/tracker17/docs/UXD.md` § 4, UX-I3, UX-I4.

## Binds

QC-7, QC-8.
