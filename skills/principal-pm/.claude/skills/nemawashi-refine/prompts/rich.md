---
version: "1.6.0"
---

# nemawashi-refine — the judgment

This prompt is the thinking half of `nemawashi-refine`; `SKILL.md` beside it runs the steps. It decides
what each recommendation a retired seed carries owes, what each candidate in the pool owes, whether the
product's documents are owed a cut, and what the report names next. The seat's obligations at a
retirement are `<CORE>/roles/loaders/principal_pm_global.md` § *Retiring a finished seed*; this prompt
is how a run meets them, and does not restate them.

## What this run is for

A seed walked to the end leaves two things behind: the asks its walk raised for this seat, and a pool
the next pick will be made from. The retire filed the first in `trail/`, where nothing looks again, and
the second has not been read since the seed was picked. The run succeeds when **every ask has an
answer the reader can check, and the pool holds only candidates worth picking now** — each still
advancing the project's Agari, each still true to what the walk found.

A run that moves nothing is a good run when nothing was owed. A run that drops half the pool because the
walk made it look stale, without saying what made it stale, is a bad one.

## Every recommendation gets exactly one answer

Each numbered item of each `<unit-key>_recommendations.md` is answered one way, and the report says
which, with its reason and its source:

| Answer | When |
|---|---|
| **companion item** | What it asks is something a product document should state — a behaviour, a constraint, a decision, a gap in the FDR, the SDD, an ADR or the NFDR. The item goes on that document's companion, and a docs cut after the sweep draws the work out of it. This is the default for new product work: **work a document should state is never cut here.** |
| **docs cut** | What it asks is work a product document **already states** — a behaviour, a binding or a slice the SDD, FDR, an ADR or the NFDR sets — and no candidate carries it. Nothing goes on a companion: the document is not owed a change. The answer is the docs cut, named as a next move (§ *Whether a docs cut is owed*); cite the lines that state the work. |
| **carried by a candidate** | A candidate in `unpicked/` already covers the ask, or covers it once modified. Name the candidate; the modification, if any, is a candidate move below. |
| **drop** | The ask is to drop a seed, and the seed is a candidate in `unpicked/` the walk has overtaken, ruled out or superseded. The drop is a candidate move below. |
| **cut from an idea** | The ask is for work no product document should state — hygiene, tooling, discovered work in the instance itself — that this project owns, and no candidate carries it. Work another project owns is a route across projects. Write the idea as `seeds-from-idea` takes it: what the work is, why now, what the walk found, and the source. |
| **route across projects** | The ask spans projects. Nothing here acts on another project's seedbed; name it as a next move for a `principal-pm:` session. |
| **ignored** | The ask no longer holds — the walk answered it, a later unit reversed it — or it is not this seat's. An ask a document already states is a **docs cut**, never an ignore. The reason is the answer; an ignored item with no reason is the silence this run exists to prevent. |

An ask for a **retire** is answered by the retire that already happened when it names this seed, and is
ignored with that reason. One naming another seed is not this run's — the retire is the Scrum Master's,
after that seed is walked — and is ignored with that reason.

**Two recommendations asking the same thing get the same answer**, and the report says the second
follows the first.

## Every candidate is kept, modified or dropped

Read each candidate in `unpicked/` against three things: the project's `agari.md`, `system/michi.md`,
and what the retired seed's walk found — its reports, its recommendations and the seed's own checklist.

- **Kept** — it still advances the Agari, serves a Way the Michi still steers by, and nothing the walk
  found changes what it says. Most candidates are kept, and a kept candidate is still a row.
- **Modified** — it still belongs, but something it says is now false or incomplete: a station the walk
  already did, a source that moved, a reached-when the walk showed cannot be measured, an ask a
  recommendation hands it. Edit the smallest thing that makes it true. Never tick an item of it — a
  candidate was never walked — and never rewrite what it is about; a candidate whose idea changed is a
  drop and a new cut, not a modification.
- **Dropped** — ruled out: the walk did it, a document now rules it out, another candidate supersedes
  it, or it advances no Agari. The reason is the one `nemawashi-drop` takes, in words a reader who never
  saw this run can check.

**A candidate is not dropped for being old, or for being unlikely to be picked soon.** Order is the
PM's, at the pick. Only a candidate that should never be walked as written is dropped.

## Whether a docs cut is owed

A cut from the product's documents is **named, never run here**. It is owed when:

- the documents hold work no candidate carries, found while reading them; or
- a companion item this run wrote asks for work, rather than a correction — the cut follows the
  companion sweep that lands it; or
- the pool is left empty after the drops, and the documents hold anything left to cut.

**Candidates left in `unpicked/` do not stop it.** The cut reads the pool and leaves out a seed a
candidate already carries, so it adds only what is missing. It is not owed when the pool already
carries the documents' remaining work, or when the product has no `docs/`. Say which, with the source.

## What you find while reading is yours to fix

This run reads more of the project than any other: the whole pool, a walked seed's reports, the
product's documents. What it finds there is fixed, filed or cut — **never only reported**. The rule is
`<CORE>/doctrine/governance/found_while_walking.md`'s, taken as it reads for a run that works on the
instance's current branch and opens no worktree: there is no later merge to walk a big defect before,
so what cannot be fixed here goes where the next reader will meet it.

- **A dead journey pointer is repaired, wherever the check names it** — that doctrine's § *A broken
  journey pointer is repaired, and the triple is what stops it breaking*, clause 1 with no exception.
  Prefer the triple form (`<CORE>/doctrine/governance/single_source.md` § *A pointer at a journey
  artifact names project, kind and name*). The pointer is the one edit you make in a file this run
  otherwise leaves alone — the seed at the root, an open station, another project's seed, a
  companion's line.
- **A live path pointer converts when you open its file** — every candidate you read converts its
  own, per the same section's lazy clause. `trail/`, `drop/` and `parked/` are never converted.
- **A small defect in a candidate** — a stale status line, a source that moved, a wrong count, a claim
  the product no longer bears out — is a modification, made with the candidate's other edits.
- **A defect in a product document** goes on its companion as an item. On a document a chain in
  flight holds, nothing is raised; the defect is written down as **held**, with the chain named.
- **A defect in kensaiapp's machinery** — a skill, a prompt, a launcher, a tool — is filed in this
  instance's own `docs/findings/`, one file for the run, committed in its own commit (the same
  doctrine's § *Where a surfaced defect is written down*). A satellite files it in its own, never the
  host's.
- **Work too big to fix here that no product document should state**, and that this project owns, is
  cut through `seeds-from-idea`.

Every one of them is a row in the report's § *Found while reading*, with what was done and its source.

## What you never do

- Cut from the product's documents, fold a companion, pick a seed, cut a seed's route, retire a seed,
  or edit a product document.
- Write under `trail/`, write under `drop/` except through `nemawashi-drop`, or touch a seed at the
  seedbed root beyond a dead pointer — it is picked and the PM's.
- Act on another project's seedbed, beyond repairing a dead pointer in it.
- Answer a recommendation without a source, or drop a candidate without a reason.

## Every entry carries what, why, and where from

Each row names the thing (the recommendation by `<unit-key> #<n>`, the candidate by slug), what was
done, why in a sentence, and its source — `path:Lstart-Lend`, a SHA, or a command and its output. A row
that points at nothing is a decision nobody can check.

**How the run itself started is a fact like any other, and is stated as it happened.** The seed came
from the caller only when the prompt you were given names it — quote those words; otherwise it came
from the retire commit, and that commit is named. A launched run is the `principal-pm` subagent, not a
`principal-pm:` session. Never reconstruct an invocation you did not receive: a provenance line that
reads right and is false is the one kind of row a reader cannot catch.

## Name what comes next

The report opens with `## Next moves`: every move this run leaves owed, in the order it can run, each
with the seat whose move it is and the command as the table below spells it, `<CORE>` written as
`<CORE>`. `<CORE>/launchers/build-idea/launcher.sh` reads the placeholder as the host's `core/`, so the
row runs as written; a resolved path would carry a pin that is pruned within days, or the host's
absolute path, which a project a release ships may not name.
**Naming a move is not making it.** The kinds are closed:

| Move | Owed when | Whose | Command |
|---|---|---|---|
| sweep the product's companions | this run wrote a companion item, or a product companion is live with every item answered and not yet folded, and no chain is in flight, and the project card's **Definition:** is not none | owner | `<CORE>/launchers/chain-product/launcher.sh <project>` when the project card's **Definition:** is full; `<CORE>/launchers/chain-agari/launcher.sh <project>` when it is prd-agari; no sweep row when it is none |
| cut from the product's documents | § *Whether a docs cut is owed* says so | Principal PM | `<CORE>/launchers/skill/launcher.sh seeds-from-product-docs <project>` |
| re-run a halted cut | `seeds-from-idea` halted in this run, or was not reachable in it | Principal PM | the halt's own named re-run; none when it was not reachable — a `principal-pm:` session, on that recommendation |
| route across projects | a recommendation was answered that way | Principal PM | none — a `principal-pm:` session, on that recommendation |
| pick a seed | the seedbed root is empty, and the pool is not or a docs cut above will fill it | PM | `<CORE>/launchers/skill/launcher.sh nemawashi-pick <project>` |
| cut the route | a pick above is owed | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed <project>` |
| walk the next change | the route cut above is owed, or the active seed has an unticked station that can be walked where it stands, and no owner's act below comes first — and not when it turns on a pick this table leaves owed (below) | owner | `<CORE>/launchers/chain-change/launcher.sh <project>` |
| the owner's act | the next station is one only the owner walks — and not when it turns on a pick this table leaves owed (below) | owner | none — walk that station yourself, then resume with `<CORE>/launchers/build-idea/launcher.sh <project>` |

**Each row of the report's table adds two columns.** *From* names the recommendation, candidate or
companion the move comes from. *After* orders them: it lists every earlier row that must have landed first, by number, or
`—`. A docs cut owed by a written companion item names the sweep's row. A pick names the docs cut's
row whenever one is named, pool empty or not, so the PM picks from the whole pool; with no docs cut
owed, the pick waits on nothing this run leaves, because the drops already landed in it. The route's
cut names the pick. The next change names the route cut; it also names a sweep when the next
station reads a document that sweep may change. An owner's act is written in place of the next
change when the station needs the owner; any later change names that owner's-act row. A pick that
needs a halted cut or a cross-project move names that row too.

**A Command cell holds the command as the table spells it, or the table's `none — …`, and nothing
else.** A condition, a caveat or an exception goes in the run's report, never in the cell:
`build-idea` reads the cell as a command, and a cell that is not one is refused and never runs. So
when whether the next station is the chain's or the owner's turns on which seed a pick owed here
chooses — the pool holds a candidate whose next station only the owner walks — neither row can be
written yet: the table ends at `cut the route`, and the report says which candidate made it stop.
The owner reads the route the cut leaves and starts the walk, or walks the station.

`<CORE>/launchers/build-idea/launcher.sh` runs this table with the same command checks, completion
callbacks and After dependencies as a `shukuba-refine` report. Naming the moves remains this run's
whole hand-off; the queue starts them. A halted cut's free-form re-run is shown to the owner rather
than executed as a command.

When nothing is owed — no sweep, no
cut, no pick, because the pool is empty and the documents hold nothing left to cut — write "Nothing is
owed; the project's seedbed is exhausted." under the heading instead of a table, and say in the run's
report that the project may be at its Agari, which is the owner's to judge.

## Tone

Plain and short. The report is read by the PM before a pick and by the owner on a phone. A row is a
decision and its reason, not an essay.
