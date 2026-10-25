---
version: "2.23.1"
---

# The Michi / Agari system — how kensaiapp expresses direction

This explains how a kensaiapp instance says *where it is going* and *when it is done* — and why
those are two different things at two different altitudes — and the loop we walk to get from a
project's ideas to its done. It is an explanatory doc for the foundation (`core/`), and it is **the
reference for the journey model** — cite this file for how Michi, Agari, Nemawashi, Shukuba and
Tobiishi relate and who owns each step.

---

## The one idea

Direction lives at **two altitudes**, and kensaiapp names them with two different words because
they are not the same kind of thing:

- **Global (the instance)** steers by a **道 Michi** — a *Way*. A bearing you hold forever and
  never finish.
- **A project** aims at an **上がり Agari** — a *done*. A terminus you reach, and then the project
  settles.

A bearing has no finish line; a terminus is nothing but a finish line. That asymmetry is the whole
model. Everything below follows from it.

The picture kensaiapp uses is a **solar system**: the Michi is the star an instance turns around
and never reaches; each planet (a project) settles at its own Agari when done.

---

## 道 Michi — the global bearing

**What it is.** The instance-level declaration of the endless guiding goal(s) the whole instance
commits to and never finishes. It is the bearing the instance steers by.

- **A declaration, not a queue.** You declare it once. You do not "work it" and "retire" it — a Way
  is not a task that completes.
- **1..N Ways.** An instance may hold several Ways at once, each with a short slug.
- **No Agari at instance level.** Nothing reaches the Michi. There is no "the instance is done."
- **Lives at** `system/michi.md`, stamped from `core/templates/michi_template.md`. Mandatory —
  every instance has one.
- The `Michi:` commit trailer references a Way's slug, so commits can say which bearing they served.

**Example (this instance's actual Ways):** `sharpen-by-living` (improve kensaiapp on the running
pipeline before it flows downstream), `nothing-unproven` (nothing leaves dev unless the pipeline
itself ratified it), `production-grade` (what we deliver is finished, even when minimal).

## 上がり Agari — the project terminus

**What it is.** The project-level declaration of when *that product* is done — the terminus. It is
set by the **CPO** — the project's executive product role, distinct from the delivery-tier **Product
Owner** who later writes each change's spec.

- **A declaration, not a queue.** Like Michi, it is a statement, not a checklist you burn down. It
  names the finish line; the work that reaches it lives in the journey (below).
- **Exactly one per project.** A project has a single "done."
- **No Michi at project level.** A project does not carry its own bearing — it *serves the
  instance's Way*. The project's job is to reach its Agari in a way that advances the Michi.
- **Lives at** `system/projects/<name>/agari.md`, stamped from `core/templates/project-templates/agari_template.md`.
  Mandatory — every managed project has one.
- It **mirrors the instance's Michi one level down**: same "declaration of direction" shape, but a
  terminus instead of a bearing.

---

## Global vs project — side by side

| | **Global — the instance** | **Project** |
|---|---|---|
| Direction word | 道 **Michi** — a *Way* | 上がり **Agari** — a *done* |
| Nature | **bearing** — endless, held forever | **terminus** — reached, then settles |
| Count | **1..N** Ways | exactly **1** Agari |
| Set by | the instance owner | the **CPO** (project's executive product role) |
| Settles / finishes? | **never** | **yes**, when the Agari is reached |
| Carries the other? | **no Agari** | **no Michi** (serves the instance's Way) |
| File | `system/michi.md` | `system/projects/<name>/agari.md` |
| Kind | a declaration, not a queue | a declaration, not a queue |

**How they connect.** Each project's Agari is chosen so that reaching it advances the instance's
Michi. Planets settle; the solar system keeps turning. When one project is done, its Agari is
reached and the project settles — but the instance's Michi is unchanged, and the next project
takes up the same bearing. The Michi is why the projects exist; each Agari is one project's
contribution to it.

---

## Where the *work* lives — the journey (context)

Michi and Agari only *name* direction. The work that moves toward them is the **journey**
(根回し Nemawashi → 宿場 Shukuba → 飛び石 Tobiishi). The two altitudes carry different amounts of it:

- **Global (instance).** Carries a **bearing** (`michi.md`), a **seedbed** (`system/nemawashi/` —
  ideas that could become projects or cross-project changes) and a **router 宿場 Shukuba**
  (`system/shukuba/` — the coordination point for when several projects are pushing on one thing).
  There is **no Tobiishi and no Agari** at instance level — nothing reaches the Michi, so it has no
  terminus and no change-pipeline of its own. Shukuba therefore exists at both levels **as two
  different kinds**: a project's is *walked*, and the instance's *coordinates* — it names the shared
  thing, its cross-project reached-when and which project is currently active, and is never crossed
  by Tobiishi, because the contributing projects do the crossing in their own journeys.
- **Project.** Carries an **Agari** plus the **full journey** under `journey/`:
  - **根回し Nemawashi** — the seedbed of ideas that will carry this product toward its Agari.
  - **宿場 Shukuba** — the one current station: the concrete stretch being worked now.
  - **飛び石 Tobiishi** — the change units (stepping stones) that the change pipeline carries
    from first ask to sealed-on-main.

So: **global = bearing + seedbed + router; project = terminus + full journey.** Same reason as Michi
vs Agari — the instance never finishes, a project does.

---

## How we work — walking a project's journey

This is the operating loop we run, session after session, to move a project toward its Agari. It is
entirely **project-level** — the global instance takes no part in it beyond providing the bearing
(the Michi that the project's Agari serves). It assumes the project already has **at least one seed**
in its 根回し Nemawashi; putting seeds there is a separate, ongoing act, not part of this loop.

One turn of the loop:

1. **Pick one seed — the PM's call.** The project's Nemawashi (`journey/nemawashi/`) holds a
   candidate pool in `nemawashi/unpicked/` — one or more **idea seeds**, candidate directions toward
   the Agari. The **PM** chooses the single idea to work now and lifts it out of `unpicked/` to the
   seedbed root; no other candidate moves. The elected idea becomes the one active seed and carries a
   checklist of the stations it will take. That checklist arrives as the cutter's **proposal**, and
   re-cutting it — where the station boundaries fall, and in what order they are walked — is the PM's
   first act on the picked seed. A divergence from the proposal is logged in the seed.

   **Quality comes before features at the pick.** When a seed that makes the product's footing
   hold — its tests, its harness, its CI, its security, a tree left clean — competes with a feature
   seed, the PM picks the quality seed, even where a queued or implied feature order put the feature
   first. A seed cut to close what a change's security report left for the PM is a quality seed. The
   pick says so in one line and is not raised to the owner. An order the owner stated outright still
   wins. The owner's call of 2026-10-21; security named in it 2026-10-23.

2. **Open a station — 宿場 Shukuba.** The **PM** opens the current station: a concrete stretch of
   work with its own reached-when. **Exactly one** station is active at a time. A single idea usually
   needs **more than one** station — they are walked in sequence, each station one leg of that idea's
   route.

3. **Development — walk the station through the pipeline.** The building inside a station runs as one
   or more 飛び石 Tobiishi (change units). Each is opened (`tobiishi-open`, PM) and carried
   end-to-end by the chain (`core/launchers/chain-development/launcher.sh` → `core/tools/chain_development.py`)
   (specs → design → plan → content → implementation → code-integrity → security → audit → seal),
   landing sealed-on-main (each change unit is **sealed** by `tobiishi-seal`). A station may take
   several Tobiishi before its reached-when is met.

   What a walk **finds along the way** — a defect surfaced while working on something else — is
   `<CORE>/doctrine/governance/found_while_walking.md`'s, not this loop's.

4. **Refine the route — the PM's call again; then close the station — the Scrum Master's, save the one case the PM takes.** After each
   change unit lands, the **PM** runs `shukuba-refine`: it re-reads the route against what the unit
   left and what moved upstream, and leaves a report and recommendations with the seed
   (`<CORE>/../skills/pm/.claude/skills/shukuba-refine/prompts/rich.md` owns the method). The report's `## Next moves` is then run
   by `<CORE>/launchers/build-idea/launcher.sh`, and a `chain-change` walk's end starts it.
   The queue's continuation and stopping contract is `core/tools/build_idea.py`'s.
   When the station's
   reached-when is met,
   the **Scrum Master** closes it with `shukuba-retire` — or the **PM** does, only when its
   `shukuba-park` finds the station already reached: the shukuba file moves to `shukuba/trail/` and the
   idea's checklist item is ticked. Then either the **next station** on the same idea's checklist
   opens (back to step 2), or — when the idea's whole checklist is walked — the **idea itself** is
   retired to `nemawashi/trail/` by the **Scrum Master** (`nemawashi-retire`, a mechanical move that
   restores nothing — the root is left empty). Then the **Principal PM** answers it with
   `nemawashi-refine`: every recommendation `shukuba-refine` left in the retired seed's folder is
   processed, the candidate pool is re-read — the drops made there — and a report lands at
   `system/projects/<project>/docs/nemawashi-refine/<seed>_report.md`. The moves its `## Next moves`
   names run: the companion sweep (`chain-product` when the project card's `**Definition:**` line in
   `system/projects/<project>/project.md` reads `full`, `chain-agari` when it reads `prd-agari`, and
   no sweep when it reads `none`) and the docs cut (`seeds-from-product-docs`) where
   owed — a docs cut is owed whenever the documents hold work no candidate carries, candidates left or
   not — and the PM picks the next seed after them and cuts its route (back to step 1). **The retire is a step of this loop the
   PM hands off rather than takes** — the move is the Scrum Master's, the owner's call of 2026-09-24;
   answering the recommendations `shukuba-refine` left in the folder it moves into `trail/` is the
   Principal PM's, the owner's call of 2026-09-12, made after the move, the owner's call of
   2026-09-25.

   **What the audit finds is answered here, not in the walk.** The audit is not a gate
   (`<CORE>/../skills/pm/.claude/skills/tobiishi-seal/SKILL.md` § *Step 1b — Join the audit branches*), so a change
   it faults still seals. Its findings, with the code-integrity report and the security report, are what `shukuba-refine`
   reads first, and its moves are the response: the route re-cut, a station parked or a halted unit dropped
   where the work cannot go on as written, a question raised on an upstream document. What the PM may
   not move goes to the Principal PM as a recommendation, and `nemawashi-refine` answers it. Which
   finding gets which move is `shukuba-refine`'s prompt, § *Read the unit before the route* and
   § *The six moves*. The response lands one unit later, never inside the change it faults. A finding
   about the machinery rather than the product — a skill, a prompt, the pipeline — is not the PM's to
   move on, and no step reads it yet.

   **A walk is not the only way an idea leaves the root.** One killed instead — ruled out or
   superseded — is **dropped** to `nemawashi/drop/` (`nemawashi-drop`), and one set down unfinished is
   **un-picked** back to `unpicked/` (`nemawashi-unpick`). Neither is a turn of this loop; both leave
   the root empty the same way, and the Quick reference below keeps all five verbs apart — seal,
   close, retire and drop in one bullet, park and un-pick in the next.

The loop repeats until the project reaches its **Agari**, at which point the project settles. **Settling is a
folder move, not only a metaphor** — where a stopped project goes, and the one other way a project
stops, are `<CORE>/doctrine/setup/kensaiapp_structure.md` § When a project stops. Two
things stay the PM's throughout: **which** seed is active, and **when** a station is done. Everything
between — the actual building — is the change pipeline's many roles.

---

## Who owns each step — and where the seeds come from

The loop above shows *how* a project is walked. This adds *who* owns each step, and *where the seeds
that feed the loop come from* — the seam where the executive tier hands into the journey.

**Seeds are cut, from an idea or from a product's settled documents.** An idea arrives with no
structure and no trace — something the owner said, something a run surfaced, something written down in
passing. A product's documents arrive as the opposite: settled, designed and ordered, with nobody
having drawn the work out of them. Either way the **Principal PM** cuts it into 根回し Nemawashi seeds,
each carrying the checklist of stations it will take and each owned by a
project (`<CORE>/roles/loaders/principal_pm_global.md` § *Cutting seeds from an idea*, through
`seeds-from-idea`, and § *Cutting seeds from a product's documents*, through
`seeds-from-product-docs`). A retirement decides which: `nemawashi-refine`'s `## Next moves` names a docs cut where the documents carry work
no seed does — candidates left in `unpicked/` do not stop it — and the PM's pick
after it. This is where the "put
seeds in the Nemawashi" act (noted above as separate from the loop) comes from.

**The seedbed is free-standing, and no document is its master.** Seeds arise **organically** — hygiene,
discovered work, an ad-hoc idea — and that is the path itself, not an exception to one. The executive
document chain (`PRD → (SRS ∥ UXD) → SDD` — the SRS and the UXD are siblings, both written off the
settled PRD, and the SDD needs both; see the `product-planning` project) settles what a product **is**
and grounds the FDR; it does not dictate what is seeded.

**Ownership, step by step** (in the journey's real vocabulary):

| Step | Role | Output → where it lands |
|---|---|---|
| Author the product source of truth | **CPO** | PRD → `<product>/docs/PRD.md` (head of the upstream chain; defines what the product is) |
| Set the finish line | **CPO** (CTO supports on technical constraints) | 上がり Agari → `agari.md` (set once, off the back of the PRD) |
| Define what the system must do | **CTO** | SRS → `<product>/docs/SRS.md` (off the settled PRD, alongside the UXD) |
| Define the experience | **CDO** | UXD → `<product>/docs/UXD.md` (off the settled PRD, alongside the SRS, feeding the SDD), then the design language → `<product>/docs/DESIGN.md` (off the **UXD**; nothing in this chain reads it, so it may settle after the SDD) |
| Define the product's words | **Content Manager** | verbal language → `<product>/docs/CONTENT.md` (off the **UXD**, the design language's peer; nothing in this chain reads it, so it may settle after the SDD) |
| Design the system | the seats named at `<CORE>/doctrine/setup/setting_up_a_project.md` § *The flow at a glance*, row 5 | SDD → `<product>/docs/SDD.md` (needs both the SRS and the UXD) |
| Lock the product's behaviour | **Principal PM** | FDR → `<product>/docs/fdr.md` (via `product-fdr`, gated to that seat; part of the **foundation step** — its own seed, one per product, seeded after the SDD settles) |
| Lock the structure and the quality constraints | **Principal Architect** | the decision log → `<product>/docs/adr/` (one append-only record per decision, plus an index), NFDR → `<product>/docs/nfdr.md` (via `product-architecture`, gated to that seat; the same foundation step; shape at `<CORE>/doctrine/setup/setting_up_a_project.md` § *The foundation step*) |
| Cut an idea, or a product's settled documents, into seeds | **Principal PM** (`seeds-from-idea` / `seeds-from-product-docs`) | 根回し Nemawashi seeds → `journey/nemawashi/unpicked/<seed>.md`, each with its **proposed** station checklist and an owning project — the candidate pool, never a seedbed root, because lifting one to the root is the PM's pick |
| Pick the active idea | **PM** (`nemawashi-pick`) | the elected seed → `journey/nemawashi/<seed>.md`, lifted from `unpicked/` to the seedbed root; the pick appended to `## Picked seeds` in `system/contexts/CONTEXT_PPM.md` when the instance has one |
| Re-cut its checklist into the stations that will be walked | **PM** (`stations-from-seed`) | the active seed's `## Stations — dynamic checklist`, re-cut from the proposal it arrived with |
| Open the station | **PM** (`shukuba-open`) | 宿場 Shukuba → `journey/shukuba/<station>.md` |
| Open a change unit | **PM** (`tobiishi-open`) | 飛び石 Tobiishi `change_request` → `journey/tobiishi/<key>/change_request.md` |
| Turn the request into a spec | **Product Owner** (`development-specs`) | `change_spec` → `journey/tobiishi/<key>/change_spec.md` |
| Re-read the route after a unit lands | **PM** (`shukuba-refine`) | the route's moves, a report and recommendations → `journey/nemawashi/<seed>/<unit-key>_report.md` and `…_recommendations.md`; companion items on upstream documents |
| Close the station once its reached-when is met | **Scrum Master** (`shukuba-retire`, gated to that seat — or the **PM**, only when its `shukuba-park` finds the station already reached) | the station → `journey/shukuba/trail/<station>.md`, its item ticked on the seed |
| Drop a halted change unit whose intake will not be walked as written | **PM** (`tobiishi-drop`, gated to that seat, run from `shukuba-refine`) | the unit → `journey/tobiishi/drop/<key>/`, its worktrees closed and its branches kept |
| Retire the seed once its whole checklist is walked | **Scrum Master** (`nemawashi-retire`, gated to that seat) | the seed → `journey/nemawashi/trail/<seed>`. Project level only |
| Answer the retired seed and re-read the pool | **Principal PM** (`nemawashi-refine`, gated to that seat) | every recommendation processed, candidates kept, modified or dropped, companion items on product documents → `system/projects/<project>/docs/nemawashi-refine/<seed>_report.md`. Project level only |

This table is the **planning tier's**, and its hand-off is complete at the spec. From `change_spec`
onward the change runs through the rest of the change pipeline (design → plan → content → implementation → code-integrity → security → audit → seal) and
the station is closed by the seat the table's close row names — see the loop above. The last five rows sit after that stretch,
or leave it: the route is re-read once a unit has landed, the station is closed once its
reached-when is met, a unit that will not be finished is dropped instead of sealed, and the seed is
retired once its whole route is walked, then answered by the Principal PM.

**Three easy-to-confuse pairs, kept straight:** the **Principal PM** cuts the seeds (from an idea),
**authors the FDR** and answers what a walked seed's folder carries; the **PM** works the journey (picks
the active idea, opens each station, opens each Tobiishi) — the **Scrum Master** closes a reached station
(the PM only when its `shukuba-park` finds one already reached) and retires each walked seed.
The cutting is one seat's and the
walking is the other's; the seat that stocked the pool answers what came out of it, and the Scrum
Master files it.
The **CPO** who sets the Agari is the executive product role — distinct from the
delivery-tier **Product Owner** who writes each change's spec. And the **CDO** defines the whole
product's experience once, before any change unit exists — distinct from the delivery-tier
**Architect**, who designs one change at a time against the system that already exists. The word
"design" collides; the altitude does not.

---

## Quick reference

- **"Where is this instance going, forever?"** → its **Michi** (`system/michi.md`).
- **"When is this product done?"** → that project's **Agari**
  (`system/projects/<name>/agari.md`).
- **Instance has no Agari; project has no Michi.** If you find yourself wanting an instance-level
  "done" or a project-level "Way," you are at the wrong altitude.
- **Both are declarations, not queues** — set them, don't burn them down. The burning-down happens
  in the journey.
- **Where seeds come from:** the **Principal PM**, cutting an idea — or a product's settled
  documents — into 根回し Nemawashi seeds. See "Who owns each step."
- **Verbs, kept straight:** you **seal** a Tobiishi (`tobiishi-seal`), **drop** an unsealed one
  (`tobiishi-drop` — moves it to `tobiishi/drop/` and keeps its branches), **close** a station
  (`shukuba-retire` — moves it to `shukuba/trail/` and ticks the idea's checklist item), **retire** a
  walked project seed (`nemawashi-retire` — moves it to `nemawashi/trail/` and restores nothing), and
  **drop** a killed one (`nemawashi-drop` — moves it to `nemawashi/drop/`, and restores nothing
  either). A different word for each part: the archive move is the same underneath, but what each
  part owes *after* the move is not.
- **Retire and drop differ in what the record claims, not in what the move does.** An idea reaches
  `trail/` by **ripening into work** — walked to the end at project level, or, at instance level,
  **cut** into the project seeds that will walk it (`seeds-from-idea`), which is the same claim made
  one altitude up and is why the instance seedbed states the criterion that way
  (`<CORE>/templates/nemawashi_template.md`). One reaches `drop/` by being ruled out, superseded, or
  abandoned before it was ever picked. Filing a killed idea in `trail/` claims a walk that never
  happened, which is the same overstatement as filing a parked station there.
- **You park a station you are setting down unreached** (`shukuba-park` — moves it to
  `shukuba/parked/`, where it waits to be opened again), and you **unpick** an idea you are setting down
  unfinished (`nemawashi-unpick` — moves the seed from the root to `unpicked/`, leaving the root
  empty). Neither ticks or marks anything: the checklist item a parked station came from stays `[ ]`,
  and an un-picked idea keeps its whole checklist, because that work is waiting, not done. Filing
  either in a `trail/` would claim a walk that never happened, and no note inside the file corrects it.
- **Un-picking an idea moves exactly one file — the seed.** `unpicked/` is the candidate pool: it may
  hold any number of seeds at any time, whether or not an idea is active, and its count is never a
  function of the pick. A pick lifts one seed out of it to the root; an un-pick puts exactly that seed
  back, leaving the root empty. `nemawashi-retire` moves the seed to `trail/` and restores nothing —
  it moves nothing in `unpicked/`; dropping a candidate is `nemawashi-drop`'s move. **An empty root means no idea is active; an occupied root means
  exactly one is — and at most one ever sits there: a pick is made only into an empty root.** A pick
  against an occupied root is refused, at either level, until the active idea leaves the root —
  retired, dropped, or un-picked. **The pick belongs to the seedbed, not to the project level** — it works the same
  way in `system/nemawashi/`, differing only in who performs it: a project's pick and un-pick run
  through a skill, the instance's by hand.
