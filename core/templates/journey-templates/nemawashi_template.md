---
version: "1.4.1"
---
<!-- The version above is template-file metadata; it is not copied into the seed. Nor is this block.

     What this is: the shape of ONE 根回し Nemawashi — an idea. Not the folder that holds ideas.

     THE TWO FILES WITH THIS NAME, AND WHY. `journey-templates/` holds the shape of a journey
     ARTIFACT, read by a model that then authors a fresh one. The top level holds the shape of the
     FOLDER'S README, copied byte-for-byte by `spawn_satellite.py`. Two consumers, opposite formats —
     `core/templates/README.md` § the two-consumer table. So:

       journey-templates/nemawashi_template.md   <- this file: one idea
       nemawashi_template.md                     <- the instance seedbed's README
       journey_nemawashi_template.md             <- a project seedbed's README

     A model reads this and writes a fresh file. Nothing here is copied.

     Lands at `journey/nemawashi/<YYYY-MM-DD>_<slug>.md` (project, authored by the PM or the Principal
     PM materializing a plan) or `system/nemawashi/<YYYY-MM-DD>_<slug>.md` (instance, the Principal
     PM's — no PM can reach it). Date is the day it was seeded; slug is a few words in kebab-case.
     The same idea becomes `journey/nemawashi/<idea>/seed.md` once a `shukuba-refine` run first
     writes a per-unit report beside it — this file's own shape either way, never the report's.

     THE TWO RULES THAT ARE NOT NEGOTIABLE, both from the seedbed README this stamps beside:

     1. ONE IDEA PER FILE, moved whole. A finished seed is relocated to `trail/`, never struck
        through and never marked done in place.
     2. TERSE. A seed is a working note, not a report — `<CORE>/docs/journey_move.md` § Don't bloat the
        journey. It is read while walking, by someone who needs one thing from it. A seed that grew
        into a report buries the thing they opened it for. Source case: a 62-line entry cut to 25
        with nothing lost.

     SECTIONS. `## What it is` and `## Source` are always written. `## Stations` is there whenever the
     route is KNOWN — which follows how the seed arrived, not whether it is picked. An idea seeded as
     it arises usually has no route yet and gets no checklist; inventing one before the work is picked
     is the fixed-plan the checklist exists to avoid. It gains one when it is picked and keeps it if it
     is later un-picked (`<CORE>/docs/michi_agari.md` § *How we work — walking a project's journey*, step 1 — the pick — and the
     Quick reference's un-pick bullet). A seed materialized from a plan, or stamped
     by a script, arrives with its route and carries the checklist from the start
     (`<CORE>/docs/michi_agari.md` § *Who owns each step — and where the seeds come from*, the row *Cut an idea, or a product's
     settled documents, into seeds*; `project-stamp`'s setup seed is the stamped case). The last
     two are written only when they say something; an empty heading is worse than no heading.

     THE CHECKLIST IS THE PLAN. There is no separate plan folder. Each unchecked item opens one 宿場
     Shukuba when it is worked; `shukuba-retire` ticks it when that station is reached. Grow and refine
     it as the work reveals stations — it is not fixed up front. Never append a marker to a line:
     `[ ]` and `[x]` are the only states, and a parked station leaves its item `[ ]` because that leg
     is still unwalked.
-->

# 根回し Nemawashi seed — <the idea, in a phrase>

## What it is

<The idea itself, in a few sentences. What is wrong or missing today, and what the world looks like
once this is done. Write it so someone who has never seen it can act on it — a seed may sit in the
candidate pool for weeks before it is picked.>

## Source

<Where this came from, cited: the run that surfaced it, a `path:Lstart-Lend`, a commit SHA, an owner
decision with its date — or, where it came from a seed or a station, that artifact by its triple, per
§ *Relation to existing work* below, never by path. A seed with no source is an assertion, and the session that picks it up cannot
check it.>

## Stations — dynamic checklist

<!-- One line per station. Present from the start or written later — SECTIONS above says which.
     `<station slug>` is fenced rather than the triple `single_source.md` requires elsewhere: the
     item is written before the station file exists, so there is no dated stem yet to name — the
     triple's `<name>` is `<YYYY-MM-DD>_<slug>`, and the date is only fixed the day the PM opens the
     station. Once a station is open, a *reference to it* from elsewhere is the triple; this
     checklist's own line is the one place that necessarily still names the slug alone. -->

- [ ] <station slug> — <what it reaches, in a clause>
- [ ] <station slug> — <what it reaches, in a clause>

## Relation to existing work

<Optional. What this depends on, what depends on it, and which sibling seeds it must not duplicate.
Name each one by its triple — `<project> · <kind> · <name>`, one backtick span, per
`<CORE>/doctrine/governance/single_source.md` § *A pointer at a journey artifact names project, kind
and name*. Never by path: a path spells the position, and a pick or a retire moves it. Omit the
section if there is nothing true to say.>

## Out (later / elsewhere)

<Optional but usually earned. What this idea is deliberately NOT — the adjacent work someone will
reasonably assume is included. A fence here is what stops the first station from growing to fill the
idea. Omit if nothing is at risk of being assumed in.>
