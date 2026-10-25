---
version: "1.0.0"
---

# senior_engineer_repair_dependencies — answering a product's dependency advisories

The Senior Engineer's rules for repairing a product's dependencies: which audit runs, the rules a repair
is held to, the one answer each advisory takes, the exception record and its upkeep row, and how a
forbidden move waits for the end of the run. Two skills read it, on different branches:

- `development-security`, on a change's branch, as the first half of its review, so the repair reaches
  `main` at the seal;
- `dependency-repair`, on a branch off a `main` gone red by itself, which it merges once the suite is
  green — the case the rules below were written for.

Each skill says which branch it works on, where its report goes and how it commits; none of that is
here. **Single source — edit here, not in the carriers.**

## The edge of a repair

A repair is yours to make only when all three hold:

- it edits **no ADR and no product record** (the exception record excepted, as ruling 4 says);
- the **suite stays green** with it;
- it needs **no redesign** — no new unit, no changed interface, no different approach.

A repair past any of the three is not yours. Where a record is what stands in the way, it is a
**forbidden move** (ruling 4, below) and becomes a question for the owner — except for an advisory the
product does not reach, which is excepted instead. Where the suite or a redesign stands in the way, it
is reported for the PM.

## The audit command is the product's, not yours

Run the dependency audit **the product's `docs/nfdr.md` names**: the obligation whose `verified by:`
names a dependency or advisory audit, usually under § 2 *Security* (supply chain) and projected as a row
of § 10 *Verification map*. Run that command as written, from where the NFDR says it runs, over the
whole resolved dependency set — a dependency audit is only meaningful over the whole set
(`<CORE>/templates/product-templates/nfdr_template.md` § 10, "Runs over").

**Where the NFDR names none** — no NFDR, or one that names no audit — do not invent a command, and do
not reach for a tool you happen to know. No advisory is answered, and the report says so in its
own words: the NFDR names no dependency audit, so none ran. That is left for the PM. Whatever else the
reading skill does still runs.

**A command that cannot run** (a missing tool, no network to the advisory database) is not a stop.
Everything else still runs, and the report says plainly, near its top, that the dependency audit did
not run and why. That is left for the PM — the owner's ruling, 2026-10-23.

## The rules you repair under

The rules are the owner's rulings of 2026-10-22, 2 to 4, written for a repair of a `main` gone red by
itself — the case `dependency-repair` is. The owner ruled that `development-security` applies the same
rules on a change's branch. They are quoted here, word for word,
because this file is read in instances that do not hold the record they were given in (host-only
provenance: that record is a seed of the host's `product-development` project; nothing below depends
on opening it):

> 2. The repair may: bump a lockfile to the audit's fixed release; match a renamed identifier; take a
>    major bump only with the suite green.
> 3. The repair may also write an **exception** for an advisory the product does not reach (the
>    affected code is not used), as the owner already does by hand. It is recorded in the product's
>    own exception record, with the reason, under that record's window, and a row in the instance's
>    **upkeep register** (`system/upkeep.md`, `kensaiapp_structure.md` § 1) names it with its lapse
>    date, so it is tracked until the fix is taken or the exception is renewed.
> 4. The repair may never: edit an ADR or a product record other than the exception record, or take a
>    fix a record blocks. A repair that needs a forbidden move halts with that one question for the
>    owner.

Where this file and those words seem to disagree, the words govern. The owner added four things on
2026-10-23: an unreached advisory is excepted even when its only fix is forbidden, as the owner did by
hand in the case these rules were measured on (below); a product with no exception record gets its
first one, under a stated default window when its NFDR names none (§ *The exception record*); an
exception the product's audit does not read is reported (same section); and the halts of ruling 4 are
gathered into one stop at the end of the run rather than taken one at a time (§ *Forbidden moves wait
for the end*).

## Each advisory takes one answer, in this order

Read every advisory the audit reported, one at a time, and ask in this order — the order the owner
confirmed, with *not reached* decided before *forbidden*:

1. **An allowed fix exists → take it (ruling 2).** The audit names a fixed release, and taking it is a lockfile
   (or pin) bump. Where the fixed release renames an identifier the product calls, match the new name
   in the product's code — that is the whole of the code edit ruling 2 allows. Where the fixed release
   is a **major** version, it is taken only when the suite is green with it; a red suite means the bump
   is undone, and the advisory goes on down this list as one with no allowed fix.
2. **No allowed fix, and the product does not reach it → an exception (ruling 3)** — whether there is
   no fix at all, or the only fix is forbidden. *Not reached* is a claim you prove, not one you assume:
   name what the advisory says is affected (the function, the module, the code path), search the
   product for every use of it, and write what the search found as the exception's reason, in the
   product's terms — the shape of "the product calls neither of the two affected functions". If you
   cannot show it is not reached, it is reached: go on to 3 or 4.
3. **Reached, and the only fix is forbidden → a question.** A record blocks the fix (a fixed release
   that drops something an NFDR obligation or an ADR relies on), or the fix would edit an ADR or a
   product record other than the exception record. It goes on the list of questions for the owner
   (§ *Forbidden moves wait for the end*), and nothing is done to it.
4. **Reached, and no fix at all → report it for the PM.** There is no fixed release yet, or a major
   bump turned the suite red and adapting the code to it is more than matching a renamed identifier.
   The report names what is affected, why no allowed move fixes it, and what would.

## The exception record

**Where it is.** Read the product's NFDR for its *Advisory exception record* line (§ 2 *Security* of
`<CORE>/templates/product-templates/nfdr_template.md`): it names the record's path, the window an entry
stands under, and how one is renewed. With no such line, the record is at the default path,
`checks/deps/advisory_exceptions.toml` in the product's repository.

**Its shape.** Where the record exists, write the entry in its own shape (each existing entry is the
model) and write nothing its shape does not carry. **A product with no exception record gets its first
one** — the owner's words: "if none recorded and we find, why not create the first one?" — at the
path above, in the shape of the one record these rules were measured on: one table per entry with
exactly four keys, and a renewal as its own table under the entry it extends, with exactly two:

```toml
[[exception]]
advisory = "<the advisory's id>"
distribution = "<the dependency>"
published = <the advisory's publication date, YYYY-MM-DD>
reason = "<what the search found: why the product does not reach the affected code>"

[[exception.renewal]]
on = <the renewal's date, YYYY-MM-DD>
reason = "<why the exception still stands>"
```

**The record carries no window and no lapse date.** A reader of this shape derives the window from the
advisory's severity and its `published` date, and drops a renewal that has no `on` date — so a key
added to it is ignored at best and loses the renewal at worst. The report says **record created**, and
where.

**The window.** It is the one the NFDR's line names. Where the NFDR names none, use the stated default
— the owner's ruling, 2026-10-23, measured from the one record these rules were drawn from: the window
closes at the advisory's publication date plus **7 days for a Critical or unscored advisory**, or **30
days for a High one**; and, the owner's words of the same day, "30 days for Medium and Low is fine".
The window is a date you compute, not a key you write: its lapse date goes in the report and the upkeep
row, never in the record. Where you used the default, the report says **default window used**, for the
PM to raise into the product's NFDR.

**The audit must read it.** An exception the product's audit never reads is written but not honored:
the next audit reports the same advisory as if nothing were written. Check that the audit command, or
the check it runs, reads the record's path. Where it does not, the exception still stands written, the
report raises **wire the audit to honor the exception record** as an item for the PM, and that is left
for the PM. Wiring it is an edit to the product's check, which is not a move the rules give you.

**Every exception you write gets one row in the instance's upkeep register**, `system/upkeep.md`, in the
register's own columns: the task (take the fix, or renew the exception with a reason), the rule it
serves (the record and the entry), the cadence, when it was last done, when it is next due — the
exception's lapse date — and what reminds the owner. The register's rule is that a row says what to do
and when, and the rule it serves stays in its own file; keep the reason in the exception record, not
in the row. **An instance with no register gets one**, created on this first need, in the register's
shape; the report says so.

**An advisory already excepted** is answered by the record as it stands: within its window, there is
nothing to do, and the report says the exception holds. Past its window, it is a fresh advisory and
takes one of the four answers above — a renewal is ruling 3's exception written again, as a renewal
table under the entry (`on` and `reason`), and the window runs again for its own span from the
renewal's `on` date; the upkeep row's next-due date moves to that new lapse. When a fix is taken for
an advisory that had an exception, the exception has ended: remove the entry and its upkeep row, so
neither outlives what it tracked.

## Forbidden moves wait for the end

A forbidden move (ruling 4) on a reached advisory — an unreached one is excepted instead — does not
stop the run where you meet it. Note the question and carry on: every fix and every exception are done
first, and whatever else the reading skill does. Then stop **once**, with every forbidden-move question
in one list, one question per move, each naming the advisory, the move it needs, the record that
forbids it, and what you would do if the owner allowed it. The owner's ruling, 2026-10-23. When the
run is launched again after the owner answers, only those questions are picked up; everything else is
already done and committed. An audit that cannot run and an advisory left unexcepted are reported,
never stopped on.

## What you never do

- Take a dependency fix outside the edge: an ADR or product record edited (the exception record
  excepted), a red suite, or a redesign.
- Take a fix a record blocks, or a major bump without a green suite.
- Write an exception you cannot show is unreached, one with no window (the NFDR's, or the stated
  default), or one with no upkeep row.
- Edit the product's audit or check so that it reads the exception record — report it for the PM.
- Run a dependency audit the NFDR does not name.
