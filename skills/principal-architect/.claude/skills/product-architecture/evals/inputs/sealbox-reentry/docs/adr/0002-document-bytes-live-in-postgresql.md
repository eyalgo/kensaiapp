# ADR-0002: Keep document bytes in PostgreSQL rather than beside it

**Status:** Accepted
**Date:** 2026-08-24

## Context

An envelope is a PDF plus signature images plus an audit trail, all of which must be encrypted at rest
(SRS NFR-3) and all of which must be erasable together (FR-6). C-1 allows one binary and one database
and nothing else on the host.

## Decision

Document bytes and signature images are stored in PostgreSQL, encrypted, and are read and written only
through the `EnvelopeStore` port.

## Alternatives ruled out

- **An object store beside the binary (S3 or MinIO)** — lost on C-1: it is a second service on a host
  the customer supervises, and it splits erasure across two systems.
- **The local filesystem** — lost because the backup story splits in two. A database dump would stop
  being a complete backup, and the operator would not find that out until a restore.

## Consequences

One dump restores an entire deployment, and erasure is one transaction. The database carries the
document volume, with a practical ceiling near 50 MB per document, and undoing this needs a second
`EnvelopeStore` adapter plus a migration of every stored envelope.

## Traces to

SDD § 2, the storage table (Taken row); SDD § 9 TO-1; SRS § 7 C-1, § 4.3 NFR-3.

## Binds

QC-4
