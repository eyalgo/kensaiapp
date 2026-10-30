# ADR-0016: Hold a readable state in memory in one process, read the file only at start, and apply one action at a time

**Status:** Accepted
**Date:** 2026-10-30

## Context

One operator, and at most 1,000 tasks with 20 comments each (SRS NFR-1, NFR-7), fit in one process
and in memory. SRS NFR-3 requires every action to be "checked against the saved data at the moment
it is applied". SRS DR-6 defines unreadable saved data only "at start". No number in the SRS argues
for more than one process (SDD § 2, force 5).

ADR-0005 decided this on 2026-10-06. A tracker that starts on saved data it cannot read now stays up
and shows one page (SDD § 4 EX-13). It builds no `application` and holds no state, so ADR-0005's
"`application` holds the current state" and "overwritten by the next save" do not reach it. This
record carries ADR-0005 with those two sentences qualified, as SDD § 9 TO-4 now reads.

## Decision

The saved data is read once, at start, and never again while the tracker runs. `application` holds
a readable state. A single lock is held from the moment a request's check begins until its result
is saved, so no two actions interleave. At most one running tracker uses a saved-data location.

NFR-3's check against the saved data is met by checking against the state held in memory, which the
read at start, the save before the state becomes current (ADR-0004), the request lock and the
one-tracker lock keep identical to the saved data at every moment an action is applied (SDD RN-6).

## Alternatives ruled out

- **Read the file at the top of each request.** It lost because it adds a disk read to every page,
  and it would need a decision the SRS does not make: what the tracker does with saved data that turns
  out unreadable in the middle of a sitting (SDD § 9 TO-4).
- **More than one process, or a database serving concurrent writers.** It lost because one operator
  applies one action at a time, and NFR-3's single check-and-apply is simplest when one process does
  so (SDD § 2, force 5; the shape table's third row).
- **One shared record for the unreadable-data mode**, in place of a successor to each record it
  narrows. It lost because a log of one decision per file has no status for a partial narrowing:
  ADR-0005 would stay Accepted and read as universal.

## Consequences

Easier: pages need no disk read. There is no moment in a sitting at which the data can turn out
unreadable. A refusal for a stale page compares against one state.

Harder: while the tracker serves its saved data, a change made to the file by hand is overwritten by
the next save (SDD § 9 TO-4; FDR R-20, OOS-16). While the saved data cannot be read, the tracker holds
no state and makes no save, so the change stays and the next start reads it, and no page changes
before then. Requests wait for each other, which one operator does not notice.

Undoing it costs a read at the top of each request in `application`, and an SRS decision about
unreadable data found mid-run.

**Dependence:** the one-tracker lock, which is an operating-system facility and is recorded in
ADR-0009. It is held on both startup paths.

## Traces to

- Supersedes `products/tracker17/docs/adr/0005-state-in-memory-one-action-at-a-time.md`, whose
  decision, alternatives and consequences this record carries whole.
- `products/tracker17/docs/trail/architecture/cycle-22.md` § 3.5 — the answer that settled this
  supersession, raised by the PM, with its reasoning at
  `products/tracker17/docs/trail/architecture/self_answer-26.md` §§ 3.3 and 3.5.
- `products/tracker17/docs/SDD.md` § 2, force 5; § 4 SD-1, SD-2, SD-4, RT-6, EX-13; § 9 TO-4; SDD Review
  Notes RN-6, RN-72.
- `products/tracker17/docs/SRS.md` NFR-1, NFR-3, NFR-7, DR-6; `products/tracker17/docs/fdr.md` R-20,
  R-27.
- `products/tracker17/main.py`, `_serve_claimed`; `products/tracker17/web/routes.py`, `UnreadableSite`;
  `products/tracker17/README.md`, "The tracker keeps showing the page until you stop it, even if you
  repair the saved data."; read 2026-10-30 at `b13b5e86b`.

## Binds

QC-3, QC-52, QC-53, QC-54.
