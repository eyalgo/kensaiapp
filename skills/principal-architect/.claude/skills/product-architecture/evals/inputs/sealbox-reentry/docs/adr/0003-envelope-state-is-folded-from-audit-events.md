# ADR-0003: Derive envelope state by folding its audit events

**Status:** Accepted
**Date:** 2026-08-24

## Context

DR-3 makes the audit trail evidence: once written, an event is never altered. A separate mutable
status column would give an envelope two sources of truth about the same fact, and the two can
disagree without anything failing.

## Decision

`audit_events` is append-only, and an envelope's state is computed by folding its events. There is no
status column to update.

## Alternatives ruled out

- **A status column with a log table beside it** — lost because the pair can silently diverge, and the
  divergence surfaces as a customer dispute about what a signature record says.
- **A status column plus a database trigger writing the log** — lost because the trigger moves the
  invariant into the schema, where the test layers this product runs cannot reach it.

## Consequences

The trail and the state cannot disagree, and the audit record attached to the PDF is the same data the
application reads. Every state read costs a fold, and an envelope that accumulates many events will
eventually need a snapshot table.

## Traces to

SDD § 4 CN-1; SDD § 9 TO-3; SRS § 6 DR-3.

## Binds

QC-5
