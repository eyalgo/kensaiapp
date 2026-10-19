# ADR-0008: Issue every identity from a counter kept in the saved state

**Status:** Accepted
**Date:** 2026-10-06

## Context

A task's identity is unique across all projects and is never reused, even after the task is deleted
(SRS FR-15). The order tasks were created in must hold independently of their recorded time, so two
tasks created in the same instant still have a fixed order (FR-15). Every page has its own address
(UXD § 4), so a project's address has to survive a rename (FR-12). SRS DR-1 lists no identity for a
project, and DR-2 lists a task's identity and its place in creation order as two fields.

## Decision

Projects and tasks each take their identity from a counter that only rises. Both counters are part
of the tracker state and are saved with it, so a deleted identity stays retired across a restart.
A task's identity is also its place in creation order: one number carries two of DR-2's fields. A
project's identity is this design's addition, and it is what a project's address names.

## Alternatives ruled out

- **Address a project by its name.** It lost because a project's address would change on a rename,
  and the UXD gives every page its own address (SDD RN-7).
- **A separate creation-order field beside the task's identity**, as DR-2 lists them. It lost
  because a counter that only rises already gives FR-15's order independently of the recorded time,
  so a second field would only be a second thing to keep in step (SDD RN-7).

## Consequences

Easier: addresses are stable through a rename. A deleted task's identity is never issued again,
including after a restart. Sorting by created time, and breaking ties, needs no clock.

Harder: the saved data's format and every address depend on these numbers. A reused identity in the
saved data makes it unreadable (SRS DR-6). Changing the scheme would mean migrating saved data and
breaking bookmarked addresses.

## Traces to

- `products/tracker17/docs/SDD.md` § 3, *What the system holds*; SDD Review Notes RN-7.
- `products/tracker17/docs/SRS.md` FR-12, FR-15, DR-1, DR-2, DR-6.

## Binds

QC-10.
