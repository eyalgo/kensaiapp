# ADR-0009: Build for macOS and Linux only, with one locking path, and do not support Windows

**Status:** Accepted
**Date:** 2026-10-06

## Context

At most one running tracker may use a saved-data location, and a tracker stopped by a crash, a
killed process or a power cut must not stop the next start (SRS NFR-3). Neither the PRD nor the SRS
names an operating system. The owner's machine, where the Agari is checked, is macOS. The lock that
NFR-3 needs is an operating-system facility, built one way on macOS and Linux and another way on
Windows (`trail/sdd/cycle-1.md` § 2.2, the rationale).

## Decision

The tracker runs on macOS and Linux. Windows is not supported, and nothing is built or tested for
it. The tracker checks no operating system and carries no message for one. An unsupported system is
a missing prerequisite, which the setup instructions explain. Only macOS is checked. Linux stays
named because the tracker needs no code of its own for it.

This is the CPO's call, confirmed with three additions.

## Alternatives ruled out

- **Support Windows as well.** It lost because it means a second locking path in `persistence` and a
  run of both suites on Windows, on a machine the owner's check never touches.
- **Support macOS alone**, since the owner's check reaches only macOS. It lost because what separates
  the systems is the building, not the checking: one lock serves both Unix systems, and Windows would
  need a second (SDD RN-19).

## Consequences

Easier: `persistence` has one locking path. Setup instructions have one set of prerequisites.

Harder: Linux is named as supported and nothing checks it (SDD § 11 R-9). A Linux failure that needs
code of its own is a re-cut. Windows users are turned away by the setup instructions.

Undoing it costs a second locking path in `persistence`, both suites run on Windows, and new
prerequisites.

**Dependence:** POSIX behaviour, on two counts. The one-tracker lock is a Unix facility, and the
whole-state save of ADR-0004 relies on a rename that Python documents as atomic as "a POSIX
requirement". The SDD names neither primitive; this record names the facility and leaves the
primitive to `persistence`.

## Traces to

- `products/tracker17/docs/SDD.md` § 4 RT-3; § 11 R-9; SDD Review Notes RN-11, RN-19.
- `products/tracker17/docs/trail/sdd/cycle-1.md` § 2.2 — the CPO's answer, "confirm, with three
  additions".
- `products/tracker17/docs/SRS.md` NFR-3, FR-4.

## Binds

QC-52, QC-61.
