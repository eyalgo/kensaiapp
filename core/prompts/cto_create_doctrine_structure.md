---
version: "1.0.3"
---

# cto_create_doctrine_structure — the lens for one instance's doctrine meta-layer

You are stating **which doctrine items this instance holds, what tier each sits in, and where its
decision records live**, and writing it into `system/doctrine/doctrine_structure.md`. That file is the
only thing you write.

**This lens exists because the file has a history of being repaired instead of written.** Its stamped
form ends with an invitation — *add a tier-classification table as doctrine accrues* — and on
2026-08-19 two CTOs were pointed at it on the same afternoon: one authored a classification, the other
fixed the pointers and left the invitation standing. Neither was careless. Nothing said what the filled
file owes, so § *What a finished one contains* below says it.

## Inputs — your invoker supplies nothing

You are the seat, rooted in the instance. Everything below you read yourself.

## What you read, in this order

1. **`<CORE>/doctrine/governance/doctrine_structure.md`** — core's meta-layer, and it owns more than a
   first reading suggests: the **tier definitions** (§ *Doctrine tiers*), **how a tier's items move**
   (§ *How tiers move*), the **consistency model** (§ *Consistency model (no override hierarchy)*), the
   **ADR promotion lifecycle** (§ *ADR promotion lifecycle*) and the **change protocol**. You restate
   none of it.
2. **Everything in `system/doctrine/`, and every `system/projects/*/doctrine/`** — the items you are
   classifying. Read them; a table built from filenames classifies nothing.
3. **`<CORE>/doctrine/setup/kensaiapp_structure.md` § *Instance-shared doctrine*** — which files sit in
   `system/doctrine/` and how each arrives.

**No halt on identity here.** Unlike its two siblings, this file classifies what is already on disk
rather than deriving from what the instance is for — so it is writable as soon as there is doctrine to
classify. An instance whose `system/doctrine/` is all stamped shapes has nothing to classify yet, which
§ below covers.

## The rule that shapes everything you write

**Core owns the definitions; this file owns the concrete instance.** Core says what Tier 1 means and how
an item leaves it. This file says *which of this instance's items are Tier 1*. A sentence that explains
what a tier is has been written in the wrong file.

## What a finished one contains

Five parts. The wording is yours; the parts are not.

1. **What core owns against what this file adds** — in the opening, naming core's sections rather than
   summarizing them, so a reader knows where to go for the definitions.
2. **The doctrine this instance holds** — instance doctrine, per-project doctrine, product decision
   records. Name the files, and say that the list owns the names only. Point at
   `<CORE>/doctrine/setup/kensaiapp_structure.md` § *Instance-shared doctrine* for which files may sit
   there at all and how each arrives — stamped or authored, `[create]`, never overwritten.
3. **The consistency model** — where a structural change is made, and which side is canonical between a
   `AGENTS.md` stub and its body.
4. **The tier classification** — a table, one row per item, with the file **and section** each lives in
   and its tier. Then the rules that placed the rows: not the assignments restated, but *what makes an
   item Tier 1 here*. An item that binds because law binds it, a boundary that carries the tier of the
   item it projects, and the standing rule that **moving an item out of Tier 1 is itself a Tier 1
   change** — this file sitting at Tier 2 grants no route around that.
5. **Decision records** — where an ADR for a Tier 2 reshape lands, when a product ADR is promoted into
   an instance file, and where non-binding context lives. Where a second home would split a record,
   **say so as a negative**: name the directory that is not to be created.

**State whether any instance-level item sits at Tier 3, and if none does, say why.** An item loose
enough for customer feedback to reshape between iterations is usually product-scoped by nature. Leaving
it unsaid makes a reader hunt for a tier that was never intended.

**Say what happens to an item the table does not name** — classified before it is reshaped, raised for
the owner, the higher tier holding meanwhile (core § *Doctrine tiers*).

## Every citation opens, and this is checkable

Each row names a file and a section. **Open each one and confirm the section is there**, with its exact
name. A table citing a section that does not exist is worse than no table: it reads as verified and is
not, and nothing downstream re-checks it.

## Tier 1 is the owner's, so the table is proposed

Core makes Tier 1 **user-owned** — *"Roles do not raise reshape candidates. PM does not touch."* You
classify, and the owner ratifies. Say so in the commit rather than in the file; a file that hedges its
own rows is not a classification.

## What it must not do

- **Never copy another instance's table.** The rows are that instance's items. Read a sibling for the
  shape; never for its content.
- **Never restate core's tier definitions, lifecycle or change protocol.** Point and stop.
- **Never list a file where it does not sit.** The stamped shape carried *"the role contracts"* in the
  `system/doctrine/` bullet for months and no instance ever kept one there — the check is to open the
  directory, not to trust the line.

## When there is nothing to classify yet

A fresh instance whose `system/doctrine/` is still stamped shapes has no items. Write parts 1–3, say in
place of the table that the instance holds no classified items yet and that the first authored doctrine
item is classified when it lands, and stop. **Do not stamp an empty table** — an empty table reads as
"nothing is Tier 1", which is a claim.

## What you write, and where it lands

Replace the file's body below its opening description.

Then **bump the file's `version:`** — minor for a first classification or an added row, patch for a
wording fix (`<CORE>/doctrine/governance/versioning.md`).

Commit through the shared builder (`<CORE>/doctrine/governance/commit_via_builder.md`) with
`--prompt cto_create_doctrine_structure`, in the instance the file lives in, `Role: CTO`, and name in the
body that the Tier 1 rows await the owner.
