---
version: "1.0.1"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

<!-- The single source of the ADR index's shape. Lands at `<Product path>/docs/adr/README.md`, beside
     the records it lists. One record's own shape is `adr_record_template.md` next to this file.

     MODEL-FACING: the `product-architecture` skill reads this file and authors a fresh index, so
     everything here may explain itself and none of it survives into the result.

     WHAT THIS FILE OWNS: the index's columns, their order, and the ordering of its rows. Nothing else.
     When the index is rewritten and what a run does when it finds the log and the index disagreeing are
     `<CORE>/../skills/principal-architect/.claude/skills/product-architecture/prompts/rich.md`'s.

     WHY AN INDEX EXISTS AT ALL, given the records are files in one directory: the read pattern the
     consumers need is headline-first. The CTO's next SDD run opens the log to check it is not
     re-surfacing a decision already recorded, and a delivery session opens it to find the decision
     behind a constraint — both are skims for a title, not reads of a body. A directory listing gives
     filenames; it does not give status, and a superseded record is exactly the one a skimmer must not
     act on.

     THE INDEX IS THE ONE FILE HERE THAT IS REWRITTEN. The records are append-only; this is a
     projection of them and is regenerated whenever one lands or changes status. That makes it the
     copy: where a row and the record it names disagree, the RECORD is right and the row is stale.
     Say so in the file, because a reader who does not know which is the copy will trust the table. -->

# Architecture decision log — <product name>

> The decision log for <product>. One file per architecturally significant decision, in this
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
| [ADR-0001](0001-<slug>.md) | <the decision, as a short active phrase> | Accepted | <YYYY-MM-DD> |
| [ADR-0002](0002-<slug>.md) | <…> | Superseded by ADR-0007 | <YYYY-MM-DD> |

<!-- Rows in ascending number order — the log reads as a history, and a reader scanning for the latest
     decision on a subject wants the supersession chain to run down the page. Superseded records stay
     listed: removing a row would hide exactly the history the log exists to hold. -->
