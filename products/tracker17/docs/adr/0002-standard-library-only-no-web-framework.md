# ADR-0002: Run on Python's standard library alone, with no web framework and no template engine

**Status:** Accepted
**Date:** 2026-10-06

## Context

Setup is bounded at three commands and ten minutes, with no account, key or sign-up (SRS C-2,
C-7). The SRS names no runtime and leaves it to the SDD (SRS RN-23). The predecessor whose code is
the preferred starting point requires Python 3.11 or later and has no run-time dependency (SDD
RN-3). Every package the tracker runs on is code the reader has to read or take on trust (SRS
NFR-10). The UXD had already turned down a design-system package for that reason (UXD § 9, quoted
in SDD RN-3).

## Decision

The tracker runs on Python 3.11 or later and imports nothing outside the Python standard library.
It uses no web framework and no template engine. `web` carries its own routing, request reading,
page building and escaping over the standard library's HTTP server, and accepts connections while
one is being served (SDD § 4 RT-6, § 11 R-4). The running tracker needs no network connection at
any point. Only the tests have dependencies. They are fixed to exact versions, locked with
everything they pull in, and installed into a virtual environment made with Python's `venv`. The
end-to-end layer drives Chromium.

The owner confirmed the runtime and added four things: the tracker needs no network at all, the test
dependencies go into a `venv`, a `python3` below 3.11 is a missing prerequisite the setup
instructions explain, and the unchecked floor is a named risk.

## Alternatives ruled out

- **A web framework.** It would shorten the page-building code and give routing and templates a
  reader may already know. It lost because it adds packages the reader has to read or take on trust,
  and an install step that spends part of C-7's three commands. It would also make the network
  connection of SRS FR-4 a prerequisite for running the tracker, not only for setting up the tests.
- **A template engine on its own.** Its automatic escaping is the main thing given up here. It lost
  for the same reason: it is a run-time dependency, and the tracker would no longer be runnable from
  the copy alone.

## Consequences

Easier: setup is two commands. There is nothing to install, pin or audit before the tracker runs,
and every line that runs is in the copy the reader holds.

Harder: `web` owns what a framework would have owned. Escaping is the sharpest of these: one
function puts every value into a page and escapes it (SDD § 4 SEC-4), because a page built by hand
can show typed text as markup (SDD § 11 R-3). The standard library's listener is "not recommended
for production" (SDD § 11 R-7), so the loopback-only listener and the request check carry the
security weight. Nothing checks that the code runs on 3.11 itself: the suite runs only on the Python
the machine has, 3.14.7 on the owner's machine (SDD § 11 R-8).

Undoing it costs a rewrite of `web`'s page building and an install step in the setup instructions.
`domain`, `application` and `persistence` are untouched, because no HTML crosses `SM-1`.

**Dependence:** CPython's `http.server`, as shipped with the machine's Python. Two of its facts shape
other records: it refuses a request line longer than 65,536 bytes (`handle_one_request` on Python
3.14.7, quoted in SDD § 11 R-10), which bounds what an address can carry (ADR-0006, ADR-0007); and
its documentation names the threaded server as the answer to browsers that pre-open sockets (SDD
§ 11 R-4). A later Python that changes either one reopens those records.

## Traces to

- `products/tracker17/docs/SDD.md` § 4 RT-1, RT-4, SEC-4; § 9 TO-1; § 11 R-3, R-4, R-7, R-8, R-10;
  SDD Review Notes RN-3, RN-18.
- `products/tracker17/docs/trail/sdd/cycle-1.md` § 2.1 — the owner's answer, "confirm, with four
  additions".
- `products/tracker17/docs/SRS.md` C-2, C-7, C-8, NFR-10, RN-23.

## Binds

QC-19, QC-36, QC-39, QC-43, QC-59, QC-60.
