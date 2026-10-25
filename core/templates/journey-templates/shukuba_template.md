---
version: "1.7.0"
---
<!-- The version above is template-file metadata; it is not copied into the station. Nor is this block.

     What this is: the shape of ONE 宿場 Shukuba — a station. Not the folder that holds stations.

     THE FILES WITH THIS NAME, AND WHY. `journey-templates/` holds the shape of a journey ARTIFACT,
     read by a model that then authors a fresh one. The top level holds the shape of the FOLDER'S
     README, copied byte-for-byte by `spawn_satellite.py`. Two consumers, opposite formats —
     `core/templates/README.md` § the two-consumer table. So:

       journey-templates/shukuba_template.md   <- this file: one station
       journey_shukuba_template.md             <- a project station folder's README
       system_shukuba_template.md              <- the instance router's README

     A model reads this and writes a fresh file. Nothing here is copied.

     Lands at `journey/shukuba/<YYYY-MM-DD>_<slug>.md`, authored by the **PM** when it opens the
     station (`<CORE>/docs/michi_agari.md` § *Who owns each step — and where the seeds come from*, the row *Open the station*). Project level only — the instance's `system/shukuba/`
     is a router, a different kind, and is never walked.

     THE THREE PARTS ARE MANDATORY, and the seedbed README names them: a station file holds "the
     station in full: what it is, its reached-when, and its guardrail." A file missing any of the
     three is not a station.

     `## Reached when` — that spelling, not `Reached-when`. 54 stations on disk say "Reached when" and
     2 say otherwise; the drift is a copied sibling, which is what this template exists to end.

     WRITE THE REACHED-WHEN SO SOMEONE ELSE CAN CHECK IT. It is the bar the PM verifies against before
     closing, and `shukuba-retire` refuses a station whose reached-when is not met. State it as
     conditions observable on disk or by running something — not as "the work is done", which cannot
     fail. It is preserved verbatim if the station is parked and taken up again, so a station is always
     walked against the bar it was opened against. A condition that states a count states the
     invocation that produced it — the pattern literal, the case sensitivity, and the matcher. A bare
     figure from the author's throwaway command is the one defect the worker cannot re-run: four v9
     bars carried one before this clause (2026-08-12). A condition that runs a grep is tried against
     the tree BEFORE the work: a pattern the target already satisfies — its own title, a pre-existing
     sibling, a substring of the very name being checked for — passes on a file that does nothing the
     bar asks, and a bar keyed to a skill's NAME cannot see a claim that states the CONCEPT without
     naming it. Both shipped in one chain (2026-09-02): one bar grepped `principal_pm_cut_seeds`
     against a file whose own H1 contains it, another grepped a skill name for a claim two files made
     without it. If the bar would pass before the work, it is not a bar. And a condition that asserts
     an absence names a fixture in which the thing could have appeared — an absence over a fixture
     that could never produce it is true before any fix lands and is reported met forever by workers
     doing exactly what they were told: it appeared twice in one v9 chain, a station bar and a test
     one level down, before this clause (2026-08-12).

     AND SO IT CAN BE MET WHERE THE STATION STANDS. Read the bar through to what defines each thing it
     requires. A gate it names is read to the product document's row that defines it — the whole
     clause, not the gate's name, and not the check's code, which this station may be the one to
     write; where no document defines the gate, the bar's own words are its definition. Everything
     that definition requires exists already, is this station's own work, or was landed by a station
     before it. Where a later station lands it, or no station on the route does, the bar cannot pass
     here, and the defect is in the route, not in this station's wording — the one
     `<CORE>/../skills/pm/.claude/skills/stations-from-seed/prompts/rich.md` hunts as defect 6. It is never fixed by writing a narrower bar at
     the open.

     TERSE. A station is a working note, not a report — `<CORE>/docs/journey_move.md` § Don't bloat the
     journey. Read while walking, by someone who needs to know what "reached" means here.

     ONE STATION AT A TIME. Exactly one file sits at `journey/shukuba/`'s root. Reached → `trail/`
     (`shukuba-retire`, which also ticks the seed's item). Set down unreached → `parked/`
     (`shukuba-park`, which leaves the item unticked). Never `trail/` for an unreached station: the
     record is read by looking at which folder things are in, and a note inside the file does not
     correct it.
-->

# 宿場 Shukuba — <what this station reaches, in a phrase>

*Item <n> on the active 根回し Nemawashi `<project> · nemawashi · <name>`. Slug: `<slug>`.*

## What it is

<The work of this leg, in a few sentences. Enough that the agent walking it knows what to build without
reading the seed, and enough that a reader six weeks later knows why this was one station rather than
two.>

## Reached when

<The bar, stated so someone who did not do the work can check it. Name the files that must exist, the
command that must pass, the condition that must hold. If any part of it turns on something unobservable,
that is a defect in the reached-when, not a judgment call to make later.>

## Guardrail

<What this station must NOT become — the adjacent work it will otherwise absorb, the decision that is
not its to make, the file it must leave byte-identical. One bullet each. This is where a station's scope
is actually held; "What it is" describes the work, the guardrail is what keeps it from growing.

A guardrail names what must not be weakened: the scope, a file left byte-identical, a property the
work may not trade away. A file is held byte-identical only where the seed or a ruling says so — a
seed's "not here" names whose work it is, not a file nobody may touch. Even then it never bars a
sentence the station's own change makes false: that correction is `found_while_walking.md` clause 1,
made on the branch, and a guardrail forbidding it defers a found defect while looking like scope. It is never a stop. A condition that would block the work is written as what
must hold (where an author's first draft says "if the fixture is missing, stop", the guardrail says
"the fixture must exist"). A task that cannot hold it is deferred downstream, and the change is not
halted.>

- **Not here:** <the neighbouring stations or seeds that own the rest, each by its triple —
  `<project> · <kind> · <name>`, one backtick span. A slug alone names nothing: the triple's third
  part is the whole dated stem, `<YYYY-MM-DD>_<slug>` — the slug by itself is missing both the date
  and the two parts that disambiguate it.>

## Attempts

<!-- Only when a run has been tried and failed. Omit the section entirely until then. -->

<Per attempt: the date, who ran it and on what tier, what it produced, why it failed, and the revert
SHA if it was reverted. This is what makes a failed station worth taking up again, and the journey has
no other verb for failure — `no-verb-for-work-that-failed`. Do not soften it and do not delete it when
the next attempt succeeds.>
