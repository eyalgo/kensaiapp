---
version: "1.9.1"
---
<!-- The version above is template-file metadata; it is not copied into the report. Nor is this block.

     What this is: the shape of ONE `shukuba-refine` report — what a review after a seal or a halt did, why, and
     from which source. A model reads this and writes a fresh file. Nothing here is copied.

     Lands at `journey/nemawashi/<seed>/<unit-key>_report.md`, inside the seed the reviewed unit
     walked, beside `seed.md` and the run's `<unit-key>_recommendations.md` (its shape is
     `shukuba_refine_recommendations_template.md` beside this file). Written by `shukuba-refine`,
     every run, whether or not anything moved.

     It is a RECORD, not a live journey file: nothing edits it after the run that wrote it, and a
     later run on another unit writes its own. A later review of the same unit replaces it whole, and
     the earlier one stays in git.

     The judgment behind every row is `<CORE>/../skills/pm/.claude/skills/shukuba-refine/prompts/rich.md`; this file is the shape
     only. Every row carries its source — a path with a line range, a commit SHA, or a command and
     its output. A source that is a seed, a station or a change unit is its triple in one span,
     `<project> · <kind> · <name>` — the name a folder-seed's or a change unit's folder name, with no
     `.md` — never a path, with any line it cites after the span as
     `(line N)`: a path spells the artifact's state, and the next pick, retire or park breaks it
     (`<CORE>/doctrine/governance/single_source.md` § *A pointer at a journey artifact names project,
     kind and name*). This report sits in a live seed folder, where
     `<CORE>/tools/test_journey_pointers_are_triples.py` refuses a path-form pointer. A section with
     nothing in it says "None." rather than being dropped.

     `## Next moves` stands first because it is what the owner reads first. The completion message
     (`<CORE>/tools/reporters.py`) and the queue `<CORE>/launchers/build-idea/launcher.sh` both parse
     it: keep its heading and its six columns as they are here. After names the rows that must have
     landed first; From points at the reasoning, which is not restated here. -->


# 宿場 Shukuba refine — `<unit-key>`

*Unit `<unit-key>`, <sealed Tobiishi | halted Tobiishi | ad-hoc merge | commits naming the key>, reviewed <YYYY-MM-DD>.
Station `<station-slug>` (<root | trail/ | parked/>). Seed `<seed-slug>`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | <a kind from the prompt's § Name what comes next, as written there> | <owner · Scrum Master · Principal PM · PM> | `<the command as the prompt's kind table spells it, <CORE> written as <CORE> — never a pin's or the host's resolved path>` or none — <where it is run> | <— · or the earlier rows that must land first: 1 · 1, 2> | <Moves row n · Considered row n · recommendation n · the companion item raised> |

<Or "None — <why>.">

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | <path, one row per step, or "absent — <why>"> | <blocking / change-local / skill-general counts, and what each blocking one names> |
| code-integrity report | <path, or "absent — <why>"> | <verdict, and anything it surfaced but did not fix> |
| developer's closing commit | <SHA, or "absent — <why>"> | <its divergence notes, in a line> |
| deferred decisions | <path, or "absent — <why>"> | <each entry and whether it still has an owner> |
| the closing commit's `Deferred:` lines | <SHA, or "absent — <why>"> | <each line and where the refine routed it: (a) the companion item raised, (b) the next change's spec, or read as a (c) finding> |
| corrections owed | <`tl_instruction.md` § Corrections owed while there, or "absent — <why>"> | <each *Owed outside this change's reach* line, and the companion item or non-move it became> |
| work handed on | <`change_spec.md` § Out of Scope, or "absent — <why>"> | <each piece of work handed on, and where on the route it now lands> |

## Upstream

<What changed under the product's `docs/` since the seed was first committed — the command and its
output — and every live `*_open_issues.md`. Or: "No `docs/` under the Product path — no upstream.">

## Held

| Seed or station | Held by | Source |
|---|---|---|
| `<project> · <kind> · <name>` | <the document a chain in flight may move, or the open unit walking it> | <state file field and value, or the open unit's triple> |

<Or "None.">

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| <one of the six> | `<project> · <kind> · <name>` | <one sentence> | <path:Lstart-Lend, a journey artifact's triple and (line N), SHA, or command and output> | <SHA> |

<Or "None — no move was owed; see below.">

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `<project> · <kind> · <name>`, or a document's path | <one sentence> | <path:Lstart-Lend, a journey artifact's triple and (line N), SHA, or command and output> |

## Absent

<Every input the run could not read, and why — an artifact the unit's shape does not produce, a
document with no companion, a command that failed. Or "None.">
