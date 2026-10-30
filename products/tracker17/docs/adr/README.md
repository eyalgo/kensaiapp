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
| [ADR-0002](0002-standard-library-only-no-web-framework.md) | Run on Python's standard library alone, with no web framework and no template engine | Superseded by ADR-0013 | 2026-10-06 |
| [ADR-0003](0003-no-script-in-any-page.md) | Run no script in any page, and answer every action with a whole page | Accepted | 2026-10-06 |
| [ADR-0004](0004-whole-state-saved-atomically-on-every-change.md) | Save the whole tracker state on every change, and replace the file in one step | Accepted | 2026-10-06 |
| [ADR-0005](0005-state-in-memory-one-action-at-a-time.md) | Hold the state in memory in one process, read the file only at start, and apply one action at a time | Superseded by ADR-0016 | 2026-10-06 |
| [ADR-0006](0006-last-action-travels-in-the-page-address.md) | Keep no session, and carry what a page says about the last action in its address | Superseded by ADR-0011 | 2026-10-06 |
| [ADR-0007](0007-text-counted-once-in-domain-in-code-points.md) | Count typed text once, in `domain`, in code points, after `web` turns each line break back into one character | Accepted | 2026-10-06 |
| [ADR-0008](0008-identities-issued-from-counters-in-the-state.md) | Issue every identity from a counter kept in the saved state | Accepted | 2026-10-06 |
| [ADR-0009](0009-one-unix-lock-no-windows.md) | Build for macOS and Linux only, with one locking path, and do not support Windows | Accepted | 2026-10-06 |
| [ADR-0010](0010-pending-confirmation-answered-202-move-pages-not-stored.md) | Answer a page that shows a pending confirmation with 202, and store no move page | Superseded by ADR-0012 | 2026-10-21 |
| [ADR-0011](0011-a-submission-is-a-post-form-and-its-outcome-travels-in-the-address.md) | Keep no session, carry what a page says about the last action in its address, and count only a `post` form as a submission | Superseded by ADR-0014 | 2026-10-27 |
| [ADR-0012](0012-pending-confirmation-answered-202-confirmed-action-pages-not-stored.md) | Answer a page that shows a pending confirmation of any confirmed action with 202, and store no page of a confirmed action | Superseded by ADR-0015 | 2026-10-28 |
| [ADR-0013](0013-standard-library-only-no-web-framework-suite-environment-made-by-uv.md) | Run on Python's standard library alone, with no web framework and no template engine, and make the test suite's environment with uv | Accepted | 2026-10-29 |
| [ADR-0014](0014-a-submission-is-a-post-form-and-a-page-reads-the-state-only-while-data-is-served.md) | Keep no session, carry what a page says about the last action in its address, count only a `post` form as a submission, and read a page off the tracker state only while the saved data is served | Accepted | 2026-10-30 |
| [ADR-0015](0015-pending-confirmation-answered-202-while-data-is-served-confirmed-action-pages-not-stored.md) | While the saved data is served, answer a page that shows a pending confirmation of any confirmed action with 202, and store no page of a confirmed action | Accepted | 2026-10-30 |
| [ADR-0016](0016-readable-state-in-memory-one-action-at-a-time.md) | Hold a readable state in memory in one process, read the file only at start, and apply one action at a time | Accepted | 2026-10-30 |
