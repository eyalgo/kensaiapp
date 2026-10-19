# ADR-0004: Save the whole tracker state on every change, and replace the file in one step

**Status:** Accepted
**Date:** 2026-10-06

## Context

An action is reported done only after its result is saved (SRS FR-9). A save cut off part-way must
leave the state from before or after, never a mix (NFR-2). Every action is checked and applied as
one step (NFR-3), and every data rule is checked when the saved data is read at start (DR-6).
tracker16-X's code is the preferred starting point (C-5), and its saving contract was built for none
of these: its `Repository` has one method for each kind of change, and each method reads and
rewrites the file (`task-tracker-X/tasktracker16x/domain/repository.py`,
class `Repository`, as SDD § 9 TO-5 cites it).

## Decision

`application` saves the whole tracker state on every change, through one contract at `SM-3` that
`application` states and `persistence` satisfies without inheriting from it. `application` saves
first and makes the new state current second; if the save fails, the old state stays current and
the action is reported as failed. A save writes the new state to a second file in the same
directory, forces it to disk, and renames it over the old one. No other code path writes the saved
data.

tracker17 reuses the predecessor's entities, rules and typed errors, and does not carry over its
saving contract.

## Alternatives ruled out

- **tracker16-X's per-change `Repository`**, one method per kind of change, each reading and
  rewriting the file. It lost because it gives no single check-and-apply (NFR-3), no save before the
  report (FR-9) and no check of every rule at start (DR-6) — SDD RN-5.
- **A save whose cost follows the size of the change**, through a wider `SM-3` with one operation
  for each kind of change. It lost because rules would no longer be functions from one state to the
  next, and a save would no longer be whole or absent by construction. It is the named remedy if the
  whole-state save proves too slow.
- **A database at the centre.** It lost for the reasons ADR-0001 records against it.

## Consequences

Easier: `SM-3` is one contract. Every rule is a function from one state to the next. A save is whole
or absent by construction.

Harder: a save costs the size of everything saved, not the size of the change (SDD § 9 TO-3). The
timed run at SRS NFR-1's full volume, 1,000 tasks with 20 comments each, is the measurement that
could overturn this (SDD § 11 R-1). The first remedy is a more compact file format inside
`persistence`. If that is not enough, this record is superseded.

Undoing it costs a new `persistence` and a wider `SM-3`, which every action in `application` would
then call. `domain` and `web` are untouched.

**Dependence:** the operating system's rename. Python's documentation for `os.replace` says "If
successful, the renaming will be an atomic operation (this is a POSIX requirement)", and that "The
operation may fail if *src* and *dst* are on different filesystems"
(https://docs.python.org/3/library/os.html). That is why the second file sits in the same directory,
and it is one more reason the supported systems are the POSIX ones (ADR-0009).

## Traces to

- `products/tracker17/docs/SDD.md` § 3 `SM-3`; § 4 SD-2, SD-3; § 9 TO-3, TO-5; § 11 R-1; SDD Review
  Notes RN-5.
- `products/tracker17/docs/SRS.md` FR-9, NFR-2, NFR-3, DR-6, C-5.
- https://docs.python.org/3/library/os.html, `os.replace` — read on 2026-10-06 for the dependence
  above, which the SDD does not cite.

## Binds

QC-3, QC-6, QC-25, QC-26, QC-49, QC-50.
