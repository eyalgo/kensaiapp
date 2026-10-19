# Architecture decision log — sealbox

> The decision log for sealbox. One file per architecturally significant decision, in this directory,
> numbered `NNNN-slug.md` and **append-only**: a reversal is a new record that supersedes an old one,
> never an edit to it.
>
> This index is a **projection** of those records and is rewritten as they land. Where a row here and
> the record it names disagree, **the record is right and the row is stale**.
>
> Written by the Principal Architect from the settled SRS and SDD.

| # | Title | Status | Date |
|---|---|---|---|
| [ADR-0001](0001-one-process-modular-monolith.md) | Ship sealbox as one process with enforced package boundaries | Accepted | 2026-08-24 |
| [ADR-0002](0002-document-bytes-live-in-postgresql.md) | Keep document bytes in PostgreSQL rather than beside it | Accepted | 2026-08-24 |
| [ADR-0003](0003-envelope-state-is-folded-from-audit-events.md) | Derive envelope state by folding its audit events | Accepted | 2026-08-24 |
