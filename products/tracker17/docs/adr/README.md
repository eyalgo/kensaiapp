# Architecture decision log — tracker17

> The decision log for tracker17. One file per architecturally significant decision, in this
> directory, numbered `NNNN-slug.md` and **append-only**: a reversal is a new record that supersedes
> an old one, never an edit to it.
>
> This index is a **projection** of those records and is rewritten as they land. Where a row here and
> the record it names disagree, **the record is right and the row is stale**.
>
> Written by the Principal Architect from the settled SRS and SDD. What each record contains is
> `<CORE>/templates/product-templates/adr_record_template.md`.

| # | Title | Status | Date |
|---|---|---|---|
| [ADR-0001](0001-rule-core-behind-server-rendered-pages.md) | Put the task rules in a core with no input or output, behind server-rendered pages | Accepted | 2026-10-06 |
| [ADR-0002](0002-standard-library-only-no-web-framework.md) | Run on Python's standard library alone, with no web framework and no template engine | Accepted | 2026-10-06 |
| [ADR-0003](0003-no-script-in-any-page.md) | Run no script in any page, and answer every action with a whole page | Accepted | 2026-10-06 |
| [ADR-0004](0004-whole-state-saved-atomically-on-every-change.md) | Save the whole tracker state on every change, and replace the file in one step | Accepted | 2026-10-06 |
| [ADR-0005](0005-state-in-memory-one-action-at-a-time.md) | Hold the state in memory in one process, read the file only at start, and apply one action at a time | Accepted | 2026-10-06 |
| [ADR-0006](0006-last-action-travels-in-the-page-address.md) | Keep no session, and carry what a page says about the last action in its address | Accepted | 2026-10-06 |
| [ADR-0007](0007-text-counted-once-in-domain-in-code-points.md) | Count typed text once, in `domain`, in code points, after `web` turns each line break back into one character | Accepted | 2026-10-06 |
| [ADR-0008](0008-identities-issued-from-counters-in-the-state.md) | Issue every identity from a counter kept in the saved state | Accepted | 2026-10-06 |
| [ADR-0009](0009-one-unix-lock-no-windows.md) | Build for macOS and Linux only, with one locking path, and do not support Windows | Accepted | 2026-10-06 |
