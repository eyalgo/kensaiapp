---
version: "4.12.1"
---

# Setting up a project

*How a new product goes from "we want to build it" to a project this instance can
steer. It is **one setup step, then the journey**: a scaffold that creates the project folder
**and** the 根回し Nemawashi seed carrying the definition chain — and that is the whole of
setup. The PRD, the Agari, and the technical requirements (SRS, then SDD) are **stations** the
journey walks, not setup steps. The rest of the chain (Delivery Plan, and the derived FDR /
ADR / NFDR) is the wider `product-definition` tier; the full direction + ownership model lives
in `core/docs/michi_agari.md`.*

**What this file owns.** The **sequence a product is defined by** — its stations, in order, with
the role that authors each, the skill that runs it, and what it produces — plus the ordering rules
that fix that shape, and which of those skills exist yet. Every other file points here and does not
restate it; a restatement that disagrees is a bug in the copy, deleted rather than reconciled
(`governance/single_source.md`).

The one deliberate copy is `templates/project-templates/setup_seed_template.md`, which cannot be a
pointer because it *is* the seed content stamped onto disk. When the sequence below changes, that
template changes in the same commit.

**What it does not own:** where an instance's files sit (`kensaiapp_structure.md`), what a stamper
may create or modify (`setup_scope.md`), or the direction + ownership model the system steers by
(`core/docs/michi_agari.md`).

**Where setup stops.** At the stamp commit: `system/projects/<name>/` exists, its
`project.md` points at a real product repo, and the seedbed holds the setup seed. The test is
that **setup produces only artifacts that are identical for every product** — a path, a
placeholder, doctrine stubs, a stamped seed. None of them says anything about *this* product.
The first artifact that could only belong to this product is the PRD, and that is station 1 of
the journey. So: the folder is set up; the product is not yet defined.

---

## The flow at a glance

Setup is one step — `project-stamp`, which creates `system/projects/<name>/` and the setup
seed in its seedbed. Everything after it is the journey: walk the seed's stations, one at a time.

| # | Station | Skill | Role | Produces | Main input |
|---|---|---|---|---|---|
| 1 | PRD | `product-prd` | CPO | `<product>/docs/PRD.md` | the product idea |
| 2 | Agari | `project-agari` | CPO | `system/projects/<name>/agari.md` | `PRD.md` |
| 3 | SRS | `product-srs` | CTO | `<product>/docs/SRS.md` | `PRD.md` |
| 4 | **EXPERIENCE** | | | | |
| 4 ↳ | UXD | `product-uxd` | CDO | `<product>/docs/UXD.md` | `PRD.md` |
| 4 ↳ | Design language | `product-design` | CDO | `<product>/docs/DESIGN.md` | `UXD.md` |
| 4 ↳ | Verbal language | `product-content` | Content Manager | `<product>/docs/CONTENT.md` | `UXD.md` |
| 4 ↳ | design run | — | owner (Claude Design) | the generated design system | the experience documents (any subset) |
| 5 | SDD | `product-sdd` | CTO | `<product>/docs/SDD.md` | `SRS.md` + `UXD.md` |

**Main input** names what a station is written *from* — not everything its skill opens.

Station 5 carries **one Role**, the CTO, and that is the difference from station 4. EXPERIENCE is
three separate runs each with its own seat; the SDD is **one** run by one seat, the CTO, who drafts
every part. The CPO and the CDO decide the parts the SDD template's *Who decides what* table gives
them, and their calls reach the document through the companion: a call the CTO cannot settle from
the inputs becomes an `SDD_open_issues.md` item carrying that seat's `Seat:`, and the answer is
folded in on the skill's next round. Do not read the row as a sequence of passes handed from
seat to seat.

Station 4 is **EXPERIENCE** — one station with four runs: the UXD, then the design language and the
verbal language off its direction call, then the owner's design run. EXPERIENCE carries **no single
Role** — each run carries its own, which is why the station row's Role cell is empty. The three
skills are not alike in what they read beyond their main input; the `Skill` column names skills and
claims nothing about how each behaves.

**Which of these exist today.** Every station is built and runnable, stations 1 through 4 with all
four of EXPERIENCE's `4 ↳` runs, and **station 5 since 2026-08-26**. **Seven skills** are on disk
under `.claude/skills/`: `product-prd`, `project-agari`, `product-srs`, `product-uxd`,
`product-design`, `product-content` and `product-sdd`. The design run is the one `4 ↳` with no skill of
its own — it is the owner's handoff out to Claude Design and back, which is why its `Skill` cell is
`—` rather than a gap waiting to be filled. The **CDO role is wired** (`system/loaders/cdo.md`,
`skills/cdo/.claude/agents/cdo.md`, `roles/loaders/cdo_global.md`, and a `cdo:` entry in the instance's
`AGENTS.md` loader map), and so is the **Content Manager** (`system/loaders/content_manager.md`,
`skills/content-manager/.claude/agents/content-manager.md`, `roles/loaders/content_manager_global.md`, and a
`content-manager:` entry in that same map).

**Every skill on disk has a launcher**, which is how they are meant to be run.
§ "How the definition skills run" names them and says why the launcher is the way.

**The foundation step is built on both halves.** `product-fdr` is on disk, is the
FDR's producer, gates to **Principal PM** posture, and declares its launch in its own `launcher.md` —
that half of the step is a stack like the definition skills above.
`product-architecture` is on disk and produces both records, gates to **Principal Architect**
posture, and reads the SRS, the SDD and the FDR. The **Principal Architect is wired** as of
2026-08-30 — a posture body at `<CORE>/roles/loaders/principal_architect_global.md`, the instance
overlay `system/loaders/principal_architect.md`, `skills/principal-architect/.claude/agents/principal-architect.md`, and a `principal-architect:` loader-map row. (Its tier row in
`<CORE>/doctrine/governance/model_assignment.md` was retired with every other slot pin on 2026-09-29.)

**Each half carries a launcher**, so the sentence above about every skill having a launcher reaches
the foundation step whole: both run through `<CORE>/launchers/skill/launcher.sh` from their own
`launcher.md` — `product-architecture`'s invokes the skill as a `principal-architect` subagent and
reports on `docs/adr/`, `docs/nfdr.md` and the companion beside them.

This section is the only place either fact is recorded — which stations are built, and which have a
launcher. A file that needs to know whether a station is runnable reads it here rather than carrying
its own parenthetical — which is how the same station came to be described as "not yet wired" in
three places long after the role existed, and how this section itself went on calling station 4 half
built after both its skills had shipped.

Three things follow from that last column, and they are why the chain has the shape it does:

- **3 and 4 are written at the same time.** Both come off the settled PRD and **neither derives
  from the other** — no entry in either traces to the other, and neither waits on it. That is what
  makes them siblings rather than a sequence; the shape itself is the table above. Whichever is
  written second **may read the first**, and should — to notice a collision and surface it as an
  open issue, never to silently retreat its own design. The sibling is a check, never a source,
  and its absence is normal rather than a reason to wait.
- **5 waits for both.** The architecture cannot be designed until it knows what the system must do
  *and* what the experience must be. That is what keeps structural design upstream of the
  architecture instead of arriving after it has locked.
- **Nothing in this chain reads `DESIGN.md` or `CONTENT.md`.** Both are written off the UXD and read
  later — the design language by whoever implements the screens, the verbal language by whoever
  writes the product's strings — so either can settle after the SDD without holding anything up. The
  design run reads them rather than being read by them, which is why it sits last inside EXPERIENCE
  and still holds nothing up.

One scaffold session, and setup is done. Nothing has to be remembered across that line: the
seed carrying the definition chain is stamped by `project-stamp`, so the seedbed of a new
project is never empty and the chain is never re-typed from memory.

---

## Setup — `project-stamp`

Creates the management folder `system/projects/<name>/` — the `project.md` binding
(the load-bearing `Product path:`), an `agari.md` placeholder, the project doctrine
stubs, the `journey/` folders, and the **setup seed** at
`journey/nemawashi/<date>_define-the-product.md`. It does **not** create the product's docs or
code; it only points at the product.

- Runs as a plain session — no role prefix. Its commits are `Role: Meta`.
- You'll be asked whether the product is **internal** (lives in this instance) or
  **external** (its own repo, absolute path). External also wires the Claude Code
  directory grant automatically.
- The setup seed is a **recommendation**, stamped from
  `<CORE>/templates/project-templates/setup_seed_template.md`. It is the ordinary way a
  product gets defined, not a rule — edit it, reorder it, or delete it if this product
  starts somewhere else.
- Full details: the `project-stamp` skill.

Nothing about the product's *content* is decided here — that's what the seed's stations are for.

**The front door — `project-setup`.** For an owner who would rather answer questions than run
skills, `project-setup` wraps this step and the first two stations into one conversation: it
interviews the owner in plain words, runs `project-stamp`'s script, writes the answers as round 0 of
the PRD's and the Agari's companions, and starts `core/launchers/chain-agari/`, which writes the documents of stations 1 and 2 — the PRD,
then the Agari. The documents are the same; only who types the commands changes.

## Then the journey — walk the setup seed's stations

The seed arrives with every station **unwalked** — `[ ]`, no 宿場 Shukuba opened. Walking a station
is a separate act: it materializes as the single active Shukuba, one at a time; when its
reached-when is met the Shukuba file moves to `shukuba/trail/` and the item is checked.

- **product-prd** — author the PRD, the product source of truth: what the product is, who
  it's for, the problem it removes, what success looks like, what's out of scope. Lands at
  `<product>/docs/PRD.md` (CPO posture — `product-prd` **requires** it and halts without it).
  Commits as `Role: CPO`. Launcher: `core/launchers/skill/launcher.sh product-prd <project>`.
- **project-agari** — declare the project's Agari, its finish line ("the product is done
  when …"). Fills `agari.md` (CPO posture — required, and it halts without it). Non-interactive
  and round-based like the others, but its files are **management** artifacts in the instance
  repo (`system/projects/<name>/agari.md`, its companion, and `trail/agari/`), not product docs.
  Launcher: `core/launchers/skill/launcher.sh project-agari <project>`.
- **product-srs** — author the SRS from the settled PRD: the technical answer to the PRD's
  *what* — system requirements, interfaces, data, constraints. Lands at
  `<product>/docs/SRS.md` (CTO posture). Launcher: `core/launchers/skill/launcher.sh product-srs <project>`.
- **product-uxd** — author the UXD from the settled PRD: users and their contexts, the
  information architecture, the key flows, the screen inventory with its states, the interaction
  patterns, and the accessibility bar. Lands at `<product>/docs/UXD.md` (CDO posture).
  Launcher: `core/launchers/skill/launcher.sh product-uxd <project>`.
- **product-design** — author the design language off the UXD's direction call: the product's
  tokens and the rules that apply them. Lands at `<product>/docs/DESIGN.md` (CDO posture). Nothing
  downstream in this chain reads it, so it can settle after the SDD.
  Launcher: `core/launchers/skill/launcher.sh product-design <project>`.
- **product-content** — author the verbal language off the UXD: voice and tone, grammar and
  mechanics, terminology, the message patterns for the states the UXD names, the accessibility bar
  for text, and localization rules. Lands at `<product>/docs/CONTENT.md` (**Content Manager**
  posture — required, and it halts without it). The **peer of the design language**: how something
  looks belongs to `DESIGN.md`, what it says belongs here, and a value carried in both is a defect
  of whichever document copied it. Nothing downstream in this chain reads it either. Launcher:
  `core/launchers/skill/launcher.sh product-content <project> [--dry-run] [--keep-awake]`.
- **the design run** — hand the experience documents out to **Claude Design** and bring the
  generated design system back. The owner's run, and the one `4 ↳` with **no skill and no
  launcher**; any subset of the experience documents is a legitimate input, including documents
  that are not settled. Listed here rather than left as a footnote, because a run nothing names is
  a run nobody walks.
- **product-sdd** — author the SDD, the technical *how*. It is a CTO skill: the CTO drafts the
  whole document best-effort, and the CPO's and the CDO's calls reach it through the companion — an
  item carrying that seat's `Seat:` — and are folded in on the skill's next round, the way a
  `product-srs` resume folds an answered companion. Its launch is the skill launcher:
  `core/launchers/skill/launcher.sh product-sdd <project> [--dry-run] [--keep-awake]`.

**Ordering — declare the Agari first.** Walk `project-agari` before `product-srs`. Strictly,
neither *gates* the other — both need only the settled PRD — but they are not interchangeable
in practice, so treat Agari-first as the recommendation rather than a free choice. The Agari
says when the product is finished; the SRS says what the system must do to get there. Written
in that order, "done" is a boundary the SRS can be scoped against. Written the other way, the
SRS has no terminus to stop at and tends to spec past it, and the Agari that arrives later is
read against requirements already written rather than the other way round. It is also the
cheaper document by a wide margin — one short declaration off the settled PRD — so there is
little to gain by deferring it.

**`product-srs` and `product-uxd` are order-free with respect to each other.** Both are written
off the settled PRD and neither derives from the other, so take them in whichever order suits — or
run them at the same time, which is the point of their being siblings. Order-free in what they
*derive*, not in what they *catch*: the one written second may read the first for collisions, so it
can carry an open issue the one written first could not. `product-sdd` is the one real dependency
in the chain — it needs both — and `product-design` follows the UXD whenever it suits. The walk
itself is the table above.

**Inside EXPERIENCE, the UXD comes first and the rest are peers off it.** Everything in the station
reads the UXD, so it is written first. **`DESIGN.md` and `CONTENT.md` are peers, and the order
between them is not load-bearing** — both come off the UXD's direction call, neither gates the
other, and the flat `↳` listing does not claim the verbal language waits for the design language.
Take them in either order, or at the same time. That is a recommendation, not a gate; if a real
dependency between them ever surfaces it is a one-line correction here rather than a reshape. The
design run comes last inside the station because it reads what the other three produced.

**When the PRD station is reached, check what the round left behind.** A PRD round settles
product questions, but it can also surface work that is *not* a PRD question — a condition
deferred from a ratification, a gap someone chose to defer, product work the round revealed.
That does not belong in the PRD's companion file, and the setup seed does not carry it. Seed
it as **its own file** in the same seedbed, so it survives the round that found it.

## How the definition skills run — launchers, in rounds

The definition skills are non-interactive by design, and they are not run by hand. **Run each
through the skill launcher**, from the instance root:

```
core/launchers/skill/launcher.sh product-prd      <project> [--dry-run] [--keep-awake]
core/launchers/skill/launcher.sh project-agari    <project> [--dry-run] [--keep-awake]
core/launchers/skill/launcher.sh product-srs      <project> [--dry-run] [--keep-awake]
core/launchers/skill/launcher.sh product-uxd      <project> [--dry-run] [--keep-awake]
core/launchers/skill/launcher.sh product-design   <project> [--dry-run] [--keep-awake]
core/launchers/skill/launcher.sh product-content  <project> [--dry-run] [--keep-awake]
```

Each reads that skill's own `launcher.md` — the station's `--agent` posture, the fixed prompt and the
reporter its completion message is written by — starts a detached `claude --print` run with
`--permission-mode auto --permission-prompts none`, and detaches a completion watcher. `core/launchers/chain-product/launcher.sh
<project>` walks every product document in order instead, answering each companion it finds. Two reasons the launcher is the
way rather than a convenience:

- **The prompt is a literal, so nothing a caller types can reach the run.** Ask a session to spawn
  a subagent instead and *the session composes the prompt* — the one place stray context leaks into
  an otherwise-fresh run (a prior round's summary, commit SHAs, "report the findings"). A launcher
  takes the project name and nothing else.
- **The run outlives the launcher.** It exits in about a second while the run goes on for
  minutes, so the launcher's own exit says nothing about the run — waiting on it reports "done" at
  the wrong moment. The detached watcher reads the run's log until the run ends, then reports what
  it produced.
  `--dry-run` prints the exact command without launching; `--keep-awake` holds the
  Mac awake for the run's duration.

**Station 5 runs like the rest.** The SDD is written by the CTO skill `product-sdd`, and
`<CORE>/launchers/skill/launcher.sh product-sdd <project> [--dry-run] [--keep-awake]` starts it, the
same launcher and the same single entry point as its siblings. The CPO's and the CDO's calls reach
the run through the companion, not through a session of their own.

**Rounds.** Each skill drafts its whole document best-effort, then parks anything it
can't settle into a companion `<doc>_open_issues.md` file (open issues + choices to
confirm). You answer those inline, then re-run the same skill as the next round
(Round #2, #3, …); it folds your answers in and drops what's now resolved. When nothing
is left open it **deletes** the open-issues file — its absence is the done signal. So
"Round #N" just means "run it again after I've answered the previous round's questions,"
and you're finished when the open-issues file is gone.

---

## The definition set never names the journey

The documents this chain produces — the PRD, the Agari, the SRS, the UXD, the design language, the
verbal language, the SDD — are authored before any change unit exists. They state what the product
is, what it must do, and what it must feel like. They never state **when** a thing gets built, or by
which change unit.

**A definition document does not name a 飛び石 Tobiishi.** Not *"the first Tobiishi carries this"*,
not *"a later change unit picks it up"* — not as a decision, not as a suggestion, not as the reason
an item is being surfaced. The change units are the PM's (`<CORE>/docs/michi_agari.md` § *Who owns each step — and where the seeds come from*, the row *Open a change unit*) and are
opened after this whole chain has settled. A document that names one is writing the PM's checklist
under another name, and a route written by the seat that defined the thing anchors the seat that has
to walk it, however plainly it is labelled a suggestion. **The owner's call, 2026-08-26** — first
stated for the SDD at `<CORE>/templates/product-templates/sdd_template.md` § 8, and general to the
whole set.

**And it does not cite a file under `journey/`.** A 宿場 Shukuba station is a legitimate *input* to a
definition run: the station that opens the run carries its guardrail, and a run that ignores it is
the defect. It is not a legitimate *citation*. A product document's sources are the PRD, the
project's Agari, its doctrine, and its sibling documents — all of which settle. A journey file moves
to `trail/` the week after, so a settled product document that cites one cites a path that no longer
exists.

**The one exception is a handoff, not a reference.** `sdd_template.md` § 8 *Slice → seeds* names 根回し
Nemawashi and 宿場 Shukuba because the SDD's slices are what the Principal PM cuts into seeds. It says
where a slice's fields land; it proposes no route and names no change unit — and says so in its own
words. That is the shape of the exception: a document may describe what the journey will do **with**
it, never what the journey will do.

**Where this fires.** Each authoring prompt carries it as a boundary in the diagnostic that sorts what
its run turns up — an item whose justification is a delivery decision is not that run's to surface,
and an entry whose only source is a journey file has no source. The prompts **cite this section**
rather than restating it (`<CORE>/doctrine/governance/single_source.md`).

---

## After setup

The setup seed ends at the SDD. When its stations are all checked the seed is **finished**:
move it to `journey/nemawashi/trail/` (skill: `nemawashi-retire`). From there the chain
continues by fresh seeds — the Principal PM's Delivery Plan feeds them into the Nemawashi,
and the derived FDR / ADR / NFDR follow. See `core/docs/michi_agari.md` § "Who owns each
step".

### The foundation step — the FDR, the ADR and the NFDR

**What the three names are.** **FDR** — Functional Design Requirements. **NFDR** — Non-Functional
Design Requirements, its pair. **ADR** — Architecture Decision Record, which is the industry's own term
and the only one of the three that is. So read the trio as **two Requirements documents and one Decision
Record**, never as three of a kind: the FDR is not an ADR sibling and carries none of that form's
fields. Getting that wrong sends a reader looking for a "Functional Decision Record", which does not
exist anywhere.

**The FDR's industry counterpart is the FRD** — the Functional Requirements Document of the
BRD → FRD chain, whose content list (functional behaviour, data in and out, business rules, user roles
and permissions, system interactions, interface requirements) is close to what
`<CORE>/templates/product-templates/fdr_template.md` already asks for. The same artifact has a standards-body form, which
IEEE calls an *SRS* — **IEEE 830-1998**, superseded by **ISO/IEC/IEEE 29148**, whose current edition is **29148:2018**; the 2011 first edition it supersedes 830 through has itself been cancelled and replaced. Read the 2018 text. That is not this
stack's SRS, which is the CTO's and sits upstream of all three of these; the collision is in the
industry's name, not in our sequence. A run authoring an FDR may draw on either as prior art for what
belongs in one.

**Where ours differs from the FRD is placement**, and only that: the FRD is written before design, and
this is written after the SDD, for the reason § *Why it waits for the SDD* gives below.

**A seed of its own, one per product**, when the sequence above has settled. Not a station
on the setup seed, which ends at the SDD; and not a station on a cut seed, which *needs* these three
records rather than producing them. The **Principal PM** seeds it — § *The FDR* in
`<CORE>/roles/loaders/principal_pm_global.md` makes that seat the FDR's author.

| Record | Role | Skill | Written from |
|---|---|---|---|
| `<product>/docs/fdr.md` | **Principal PM** | `product-fdr` | the PRD, the SRS and the SDD |
| `<product>/docs/adr/` | **Principal Architect** | `product-architecture` | the SRS and the SDD |
| `<product>/docs/nfdr.md` | **Principal Architect** | `product-architecture` | the SRS, the SDD, the FDR and the ADR |

The derivations are the table's own — each record's **Written from** column above states them. One skill
produces two of the records, which is why the ADR and NFDR rows name the same one.

**The FDR's `Skill` cell and its `Role` cell name the same seat, and that is the rule the row
carries.** A skill that produces one of these records gates to the seat that owns it: `product-fdr`
requires **Principal PM** posture, because the FDR is the Principal PM's (owner, 2026-08-11). Do not
wire a foundation record to a skill gated to another seat — a document whose producer believes it
belongs to someone else is authored under the wrong contract, and the gate makes the mistake
invisible by passing. The FDR's stack is the definition tier's shape: a thin skill over
`<CORE>/../skills/principal-pm/.claude/skills/product-fdr/prompts/rich.md`, the template pair in
`<CORE>/templates/product-templates/`, and a launcher.

**Why it waits for the SDD.** These three records lock what every later change is built against —
behaviour, structure, and the quality constraints. What they lock cannot be settled before the
architecture is, so a foundation written earlier is written with the least information the product
will ever have. That is the same reason the sequence above puts the SDD last.

Whether each of these runs today is § *Which of these exist today*'s, as it is for every other
station.

## Quick reference

| I want to… | Do this |
|---|---|
| Register a new product in this instance | `project-stamp` (plain session) — creates the folder **and** the setup seed |
| Define the product | walk the seed's station 1: `core/launchers/skill/launcher.sh product-prd <project>` → `<product>/docs/PRD.md` |
| Know which skill produces which file | the table in § "The flow at a glance" |
| Know what to do next | read the setup seed's checklist — the first unchecked station |
| Walk the journey | open each seed station as the single active 宿場 Shukuba, one at a time |
| Run a definition skill | its launcher, re-run as Round #N until its open-issues file is gone |
| Keep what a PRD round deferred | seed it as its own file in the same seedbed |
| Understand the full direction + ownership model | `core/docs/michi_agari.md` |
| Know what a definition document may not say | § "The definition set never names the journey" |
