# Glossary

This glossary explains the words KensaiApp uses. KensaiApp itself, and how to start, are in the
[README](../README.md); the steps are in the [how-to guide](how-to.md).

Each heading names one term, and its entry says what that term means in KensaiApp. The entries are
grouped by subject: an instance and its parts, the journey, the roles, the documents, the runs and
their settings. It holds KensaiApp's own words only: the industry's general terms, such as API, CI
or LLM, are not explained here. The page ends with two sections on a project's
journey. The first tells its numbered steps in KensaiApp's own words. The second is a table that sets
each step beside its nearest industry, ticketing-system and Jira term, and says where each comparison
ends.

## Contents

- **An instance and its parts:** [Instance](#instance) · [Host](#host) · [Satellite](#satellite) · [Core](#core) · [Doctrine](#doctrine) · [CORE](#core-1) · [Michi](#michi) · [Bearing](#bearing) · [Way](#way) · [Project](#project) · [Product](#product) · [Project card](#project-card) · [Agari](#agari) · [Role](#role) · [Overlay](#overlay) · [Posture](#posture) · [Skill](#skill) · [Skill group](#skill-group) · [Agent](#agent) · [Owner](#owner) · [Experience layer](#experience-layer)
- **The journey:** [Journey](#journey) · [Nemawashi](#nemawashi) · [Seedbed](#seedbed) · [Seed](#seed) · [Shukuba](#shukuba) · [Station](#station) · [Reached-when](#reached-when) · [Tobiishi](#tobiishi) · [Change](#change) · [Change request](#change-request) · [Cut](#cut) · [Pick](#pick) · [Unpick](#unpick) · [Open](#open) · [Refine](#refine) · [Next moves](#next-moves) · [Seal](#seal) · [Park](#park) · [Close](#close) · [Retire](#retire) · [Drop](#drop) · [Trail](#trail)
- **The roles:** [PM](#pm) · [Principal PM](#principal-pm) · [Scrum Master](#scrum-master) · [CPO](#cpo) · [CTO](#cto) · [CDO](#cdo) · [Content Manager](#content-manager) · [Principal Architect](#principal-architect) · [Product Owner](#product-owner) · [PO](#po) · [Architect](#architect) · [Tech Lead](#tech-lead) · [Content Editor](#content-editor) · [Developer](#developer) · [Senior Engineer](#senior-engineer) · [Auditor](#auditor) · [QA](#qa) · [Teacher](#teacher) · [Delegate](#delegate) · [Brief](#brief)
- **The documents:** [PRD](#prd) · [SRS](#srs) · [UXD](#uxd) · [DESIGN](#design) · [CONTENT](#content) · [SDD](#sdd) · [FDR](#fdr) · [NFDR](#nfdr) · [ADR](#adr) · [Companion](#companion) · [Answering run](#answering-run) · [Seat](#seat) · [Settled](#settled) · [What-left file](#what-left-file) · [Code skeleton](#code-skeleton)
- **The runs and their settings:** [Launcher](#launcher) · [Chain](#chain) · [Documents chain](#documents-chain) · [Change chain](#change-chain) · [Spine](#spine) · [Walk](#walk) · [Pipeline](#pipeline) · [Ask](#ask) · [Spec](#spec) · [Design](#design-1) · [Plan](#plan) · [Content](#content-1) · [Build](#build) · [Prove](#prove) · [Audit](#audit) · [Queue](#queue) · [Companion sweep](#companion-sweep) · [Seven ends](#seven-ends) · [Halt report](#halt-report) · [Pin](#pin) · [Context cap](#context-cap) · [Provider](#provider) · [Intelligence](#intelligence) · [Tier](#tier) · [Language packet](#language-packet) · [Gate](#gate) · [Gate environment](#gate-environment) · [Finding](#finding) · [Panel](#panel) · [Journey page](#journey-page) · [Notifier](#notifier) · [Receiver](#receiver) · [ID](#id) · [Kaizen](#kaizen) · [Lens](#lens) · [Cold read](#cold-read) · [Fix packet](#fix-packet) · [Fix-author](#fix-author) · [Fixer](#fixer) · [Ratify](#ratify)
- **The journey, told two ways:** [The journey in KensaiApp's terms](#the-journey-in-kensaiapps-terms) · [The journey in industry, ticketing and Jira terms](#the-journey-in-industry-ticketing-and-jira-terms)

## Instance

An instance is one git repository that KensaiApp runs in. It holds your projects, and either its
own copy of KensaiApp's shared core or a pointer to another instance's core, as a satellite does.
The entries below give the rest. An instance steers by a Michi, its long-term direction. It keeps a
seedbed of its own, of ideas that could become projects or changes across projects. It also keeps a
router for when several projects push on one thing. Its Michi is never reached, so the instance has
neither an Agari, a project's definition of done, nor a change pipeline of its own: those belong to
its projects.

## Host

A host is an instance that keeps the shared core in a `core/` folder of its own. Satellites read
their core from it. An instance that carries its own core is its own host.

## Satellite

A satellite is an instance with no `core/` folder of its own. It reads its host's core, through the
`CORE` line in its `.env` file. A change to the host's core reaches every satellite as soon as it
lands. A satellite may sit anywhere on the machine. The operations guide's section
[More than one instance](operations.md#more-than-one-instance) shows how to stand one up.

## Core

The core is the shared foundation every instance runs on, in the host's `core/` folder. It holds the
doctrine, the role postures, the contracts between roles, the prompts, the templates, the tools, the
launchers and the commit hooks. The skills sit beside it, under `skills/`.

## Doctrine

The doctrine is KensaiApp's written rules: the files every run is held to. The core's are under
`core/doctrine/`. An instance can add its own under `system/doctrine/`, and a project under
`system/projects/<name>/doctrine/`. They are layered as the roles are: the core's first, then the
instance's, then a project's.

## CORE

CORE, in capitals, is a setting rather than the core itself: the line in a satellite's `.env` file
whose value is the absolute path to its host's core. A hook reads that line when a session or an
agent starts, and the satellite then reads its core from that path. Once the file is loaded in a
shell, a satellite's launchers are reached as `"$CORE/launchers/<name>/launcher.sh"`.

## Michi

Michi, written 道, is an instance's bearing: one or more long-term directions the whole instance
commits to and never finishes. It is declared once, in `system/michi.md`. It is a declaration, not a
list of tasks, so nobody works it off or retires it. A project's Agari advances it, and nothing
reaches it.

## Bearing

Bearing is the English word the architecture overview gives an instance's Michi: the one or more long-term
directions the instance steers by and never finishes.

## Way

A Way is one of the directions a Michi declares. An instance may hold several, each with a short
slug, and a commit can name the Way it served by that slug in its `Michi:` trailer, a line at the end
of the commit message (see Trailer). A project has no Way of its own and serves the instance's.

## Project

A project is the work of building one product. It lives under `system/projects/<name>/`, with its
card, its Agari and its journey. A project aims at its Agari and is done when it reaches it. The
picture KensaiApp uses is a solar system: the Michi is the star an instance turns around and never
reaches, and each project is a planet whose journey ends at its own Agari.

## Product

The product is what a project builds: its code, and its own documents, such as its requirements and
its architecture records. It can be a whole application or part of one. It sits inside the instance,
under `products/<name>`, or in a git repository of its own, at an absolute path. The project's card
points at it.

## Project card

The project card is the file `system/projects/<name>/project.md`. Each line holds one field, such as
`Product path:`, `Type:`, `Definition:`, `Test command:` and `Languages:`. `Type:` says what the
product is: `software`, with code, or `no-code`, such as a profile or a body of writing.
`Definition:` says how much is written down before the code: `full`, `prd-agari` or `none`. The
README's section [Types of projects](../README.md#types-of-projects) shows what each value runs.

## Agari

Agari, written 上がり, is a project's definition of done: the declaration of when its product is
done. The CPO sets it once, after the PRD, in `system/projects/<name>/agari.md`. Each project has
exactly one. Like the Michi it is a declaration, not a checklist, and the work that reaches it is the
journey. Each project's Agari is chosen so that reaching it advances the instance's Michi.

## Role

A role is one part of the work, as in a software team: the PM, the architect, the developer and
others. Every run works as one role. A role's posture is written once, in the core, and an instance
can lay an overlay over it. Most roles also answer to a message prefix, such as `pm:`, or `ppm:` for
the Principal PM. The operations guide's section [Asking a specific role](operations.md#asking-a-specific-role)
shows how.

## Overlay

An overlay is a short file in an instance, `system/loaders/<role>.md`, that states only what is
different about one role in that instance. It points at the role's posture in the core,
`core/roles/loaders/<role>_global.md`. The section [Loader map](../AGENTS.md#loader-map) of the
`AGENTS.md` at the repository's root maps each prefix to its overlay.

## Posture

A posture is the stance a role works in, written in that role's file under `core/roles/loaders/`. A
session or an agent takes it on when it works as that role. The Teacher is a posture with no place in
the pipeline.

## Skill

A skill is a folder that holds a `SKILL.md` file, the instructions for one kind of work, with
optional folders beside it, such as its prompts, its evals and its intelligence files. Every skill
belongs to a group: it sits at `skills/<group>/.claude/skills/<skill>/`.

## Skill group

A skill group is one folder under `skills/` that holds the skills and agents of one role or one
purpose, such as `skills/pm` or `skills/interactive`. A session sees a group only after you name it
with `/add-dir`, or with `--add-dir` when Claude Code starts. A launcher grants a run the group of
the skill it starts. The operations guide's section
[Loading skills and agents](operations.md#loading-skills-and-agents) shows both ways.

## Agent

An agent is a Claude Code subagent, defined by a file in a group's `.claude/agents/` folder. Most
roles have one, such as `developer.md`, and each step of the pipeline runs as a separate agent run.
The delegate is the agent for work you hand off.

## Owner

The owner is the person an instance works for: you. Some moves are yours alone, such as a question
only you may settle, or an act no run can do for you, like pushing a product's main branch. A run
that reaches one stops and says what it needs.

## Experience layer

An instance's experience layer says what every product under it may and may not look like and sound
like. It is two pairs of files in `system/experience/`: the visual restrictions and direction, then
the voice restrictions and direction. Each restrictions file holds the limits no product may relax.
Each direction file holds how products look or sound where nothing narrower decides.
`experience-visual` writes the first pair, then `experience-voice` the second.

## Journey

The journey is how a project gets from its documents to its Agari. It has three parts, each with a
Japanese name: the seedbed of ideas, Nemawashi; the station being walked now, Shukuba; and the
changes that build it, Tobiishi. The architecture overview's section
[From requirements to a product](architecture.md#from-requirements-to-a-product) shows the loop, and
the last two sections of this page tell it step by step and set each step beside its nearest term
elsewhere.

## Nemawashi

Nemawashi, written 根回し, is the seedbed: the ideas that could carry a product toward its Agari,
each written as a seed. Candidate seeds wait in `journey/nemawashi/unpicked/`, and the one seed being
walked sits at the seedbed's root. The product's documents do not decide what is seeded: seeds come
from the documents, from an idea, or from work found along the way. An instance keeps a seedbed
too, in `system/nemawashi/`, of ideas that could become projects or changes across projects.

## Seedbed

The seedbed is the English word for a Nemawashi: the pool of seeds a project or an instance keeps. A
project's seedbed is its `journey/nemawashi/` folder.

## Seed

A seed is one idea in the seedbed: a candidate route toward the Agari. It carries a checklist of the
stations it will take. The Principal PM proposes that checklist when it cuts the seed, and the PM
re-cuts it once the seed is picked. At most one seed is active at a time.

## Shukuba

Shukuba, written 宿場, is a station: the one stretch of work being walked now. Each station has its
own reached-when. Exactly one station is open at a time in a project, and a seed's stations are
walked in sequence. An instance keeps something else under the same name: a router, in
`system/shukuba/`. The router names a thing several projects push on, and which project is active on
it. It is never walked: no change is walked in it, because the projects walk their own, and no run
closes it. Its file is moved to its trail by hand.

## Station

A station is the English word for a project's Shukuba. Its file sits in `journey/shukuba/` while it
is open, in `journey/shukuba/trail/` once it is closed, and in `journey/shukuba/parked/` while it
waits to be opened again.

## Reached-when

Each station has its own reached-when: what has to be true before the station is closed. When it is
met, the Scrum Master closes the station.

## Tobiishi

Tobiishi, written 飛び石, is a stepping stone: one change, carried by the pipeline from its change
request to sealed on `main`. A station may take several. Each change has its own folder,
`journey/tobiishi/<date>_<slug>/`, and its own branch and worktree. An instance has no Tobiishi.

## Change

A change is one Tobiishi: one unit of work, from its change request to sealed on `main`. The
architecture overview's journey diagram labels it CHANGE, and `chain-change` walks it.

## Change request

A change request is the file that opens a Tobiishi, `change_request.md` in the change's folder. The
PM writes it with `tobiishi-open`. It says in plain words what to change, and labels the kind of
change. It is the pipeline's first input.

## Cut

To cut is to turn an idea, or a product's settled documents, into seeds. The Principal PM cuts them,
with `seeds-from-idea` for an idea and `seeds-from-product-docs` for the documents. Each seed carries
its proposed station checklist, is owned by a project and lands in that project's `unpicked/` pool.
`seeds-from-idea` can also write to the instance's own seedbed.

## Pick

To pick is to choose the one seed to walk now. The PM picks with `nemawashi-pick`, which lifts the
seed from `unpicked/` to the seedbed's root, and no other seed moves. A pick is refused while another
seed sits at the root. The PM then re-cuts the picked seed's checklist into the stations to walk,
with `stations-from-seed`.

## Unpick

To unpick is to set an active seed down unfinished. `nemawashi-unpick` moves it from the root back
to `unpicked/` and leaves the root empty. It ticks nothing, so the seed keeps its whole checklist.

## Open

To open is to start a station or a Tobiishi. The PM opens a station with `shukuba-open` and a
Tobiishi with `tobiishi-open`. `chain-change` makes either move that is not made yet.

## Refine

To refine is to re-read the route after work lands. After each sealed change, the PM runs
`shukuba-refine`. It re-reads the route against what the change left and what moved upstream, and
writes a report with recommendations and the next moves. After a seed is retired, the Principal PM
runs `nemawashi-refine`. It works through every recommendation left in the seed's folder and
re-reads the pool of candidate seeds.

## Next moves

The next moves are the table at the end of a refine's report, under `## Next moves`. Each row names
one move, the role that makes it and the command that starts it. `build-idea` runs the table as a
queue.

## Seal

To seal is to land a Tobiishi. The pipeline's last step, `tobiishi-seal`, merges the change into
`main` and moves its folder to `journey/tobiishi/trail/`. A change that will not be finished is
dropped instead.

## Park

To park is to set a station down unreached. `shukuba-park` moves it to `journey/shukuba/parked/`,
where it waits to be opened again, and ticks nothing. When the PM's park finds the station already
reached, the PM closes it instead.

## Close

To close is to finish a station once its reached-when is met. The Scrum Master closes it with
`shukuba-retire`, or the PM does, in the one case where its `shukuba-park` finds the station already
reached. The station moves to `journey/shukuba/trail/`, and its item on the seed's checklist is
ticked. Then the seed's next station opens, or the seed is retired. The command is named
`shukuba-retire`, but in this glossary a station is closed, and only a seed is retired.

## Retire

To retire is to file a walked seed. When a seed's whole checklist is walked, the Scrum Master moves
it to `journey/nemawashi/trail/` with `nemawashi-retire`, and the seedbed's root is left empty. The
Principal PM then answers the retired seed with `nemawashi-refine`. A station is closed, not retired
(see Close).

## Drop

To drop is to set aside what will not be finished. The PM drops an unsealed Tobiishi with
`tobiishi-drop`, which moves it to `journey/tobiishi/drop/` and keeps its branches. A seed that was
ruled out or superseded is dropped with `nemawashi-drop`, which moves it to `journey/nemawashi/drop/`.

## Trail

A trail is a folder where finished journey items are kept: `shukuba/trail/` for closed stations,
`nemawashi/trail/` for retired seeds and `tobiishi/trail/` for sealed changes. Only walked work goes
there. A project seed earns its place by being walked to the end. An idea in the instance's seedbed
earns it by being cut into the project seeds that will walk it. What was not walked goes to a
`drop/` or a `parked/` folder instead.

## PM

The PM walks a project's journey. It picks the active seed, re-cuts its checklist, opens each
station and each Tobiishi, seals each change and refines the route after it. It closes a station only
in the one case where its `shukuba-park` finds the station already reached.

## Principal PM

The Principal PM cuts seeds, from an idea or from a product's settled documents. It writes the FDR,
and it answers each retired seed with `nemawashi-refine`. The cutting is the Principal PM's and the
walking is the PM's: they are different roles. Its prefix is `principal-pm:`, or `ppm:` for short.

## Scrum Master

The Scrum Master files what has been walked. It closes a reached station with `shukuba-retire`, and
it retires a seed whose whole checklist is walked with `nemawashi-retire`.

## CPO

The CPO is the project's executive product role. It writes the PRD and then sets the Agari, deciding
what the product is once, ahead of the changes that build it. It is not the Product Owner, who
writes each change's spec.

## CTO

The CTO is the project's executive technical role. From the PRD it writes the SRS, what the system
must do. It then writes the SDD, how the system is built, from the SRS and the UXD.

## CDO

The CDO is the project's executive design role. From the PRD it writes the UXD, the product's
experience, and then DESIGN, how the product looks. It also writes an instance's visual files, with
`experience-visual`. It defines the whole product's experience once, before any change exists,
unlike the Architect, who designs one change at a time.

## Content Manager

The Content Manager owns the product's words. From the UXD it writes CONTENT, the standard every
word the product says is written to. It also writes an instance's voice files, with
`experience-voice`. It sets the standard and does not write the words of one change, which is the
Content Editor's work.

## Principal Architect

The Principal Architect holds a product's structure over time. From the settled SRS, SDD and FDR it
writes the ADRs, one for each significant decision, and the NFDR, the rules a later change must not
break. It records the architecture the CTO designed. The Architect, who designs one change at a
time, reads its records.

## Product Owner

The Product Owner turns the PM's change request into a testable spec: the change's scope, its
behaviour and its acceptance criteria. Writing the spec is the pipeline's first step after the
request. It is not the CPO, who owns what the whole product is.

## PO

PO is the short form KensaiApp's own files use for the Product Owner, who writes each change's spec.
The PO is neither the CPO, who owns what the whole product is, nor the PM, who writes the change
request the spec is written from.

## Architect

The Architect turns a change's spec into its design: how the change is structured against the
system that already exists. Design is the pipeline's step after the spec.

## Tech Lead

The Tech Lead turns a change's design into an executable plan for the Developer, filling the gaps
the design leaves. It is accountable for what ships between the Architect's design and the
Developer's code. It also plans a change you open by hand, with `ad-hoc-plan`.

## Content Editor

The Content Editor writes the exact words one change puts in front of a person, such as its labels
and messages, to the standard in CONTENT. Its step runs only when the change's design says the
change publishes text. The Developer places those words and does not alter them. After a station
closes, the Content Editor also brings the Status section of the product's README up to date, with
`readme-status`.

## Developer

The Developer builds each change from the Tech Lead's plan, within the spec's scope. It implements
each task from its failing tests, and it delivers only when all the tests pass.

## Senior Engineer

The Senior Engineer reviews the Developer's code and proves that it does what the change intends. It
adds the tests the intent implies and nobody wrote, corrects a test that was read off the code
instead of the intent, and fixes the code where a correct test fails. Its step, code-integrity,
leaves `code-integrity-report.md` and comes before the audit and the seal.

## Auditor

The Auditor reads work it did not produce and lists the defects it finds as findings. It never
fixes them. In the pipeline it writes one findings file for each step it reviews,
`flow_findings/<step>.md`, and its findings never stop the change. In a kaizen round, each auditor
reads with one lens. Its agent is `kensaiapp-auditor`.

## QA

QA checks delivered work against what was asked, in a context separate from the role that produced
it. It derives acceptance checks from the spec, the design or the plan, and reports the gaps without
redesigning anything. It is started on demand, on committed work, and is not a step in the
pipeline.

## Teacher

The Teacher is a posture a session takes on when a message starts with `teacher:`. In it, Claude is
the teacher and you are the student, who learns by doing rather than by receiving Claude's findings.
It is not a pipeline role, and it does not apply to work you ask Claude to do for you.

## Delegate

The delegate is the agent that runs the work you hand off with `agent-invoke`. It holds no role
posture: its one standing instruction is `core/roles/delegate_contract.md`. It commits its own work
and writes a report of the run, `delegate-report.md`, where its brief says.

## Brief

A brief is the written instructions a session hands an agent when it starts it: the job, what the
agent may change, and where its report lands. The delegate takes its brief as its whole assignment.

## PRD

The PRD, the Product Requirements Document, is written by the CPO. It says what the product is for,
the problem it removes, who it is for, its goals and success metrics, and what is in and out of
scope. It is the first document written for a product, kept as `docs/PRD.md`. The SRS and the UXD
are both written from the settled PRD.

## SRS

The SRS, the Software Requirements Specification, is the CTO's statement of what the system must do:
its functional and non-functional requirements, interfaces, data, constraints and acceptance
criteria. It is written from the settled PRD and kept as `docs/SRS.md`.

## UXD

The UXD is the CDO's document of the product's experience: its users and their contexts, its
information architecture, its key flows, its screens and their states, its interaction patterns and
its accessibility bar. It is written from the settled PRD and kept as `docs/UXD.md`. DESIGN, CONTENT
and the SDD are written from it. The UXD is experimental and still changing.

## DESIGN

DESIGN is the product's design language, kept as `docs/DESIGN.md` in Google's DESIGN.md format: how
the product looks. The CDO writes it from the UXD. No later document in the chain reads it, so it
may settle after the SDD.

## CONTENT

CONTENT is the product's verbal language, kept as `docs/CONTENT.md`: the standard every word the
product says is written to. It covers voice and tone, grammar and mechanics, terminology, the
message patterns for the product's states, the accessibility bar for text and localization. The
Content Manager writes it from the UXD, and the Content Editor writes each change's words to it.

## SDD

The SDD, the System Design Document, says how the system is built: its architecture, derived from
the PRD, the SRS and the UXD. The CTO writes the whole document in one run, and the CPO and the CDO
decide the parts its template gives them. It is kept as `docs/SDD.md`.

## FDR

The FDR, Functional Design Requirements, states the product's behaviour: the product decisions
every later change is built against. The Principal PM writes it once per product, from the PRD, the
SRS and the SDD, after the SDD settles. It is kept as `docs/fdr.md`.

## NFDR

The NFDR, Non-Functional Design Requirements, is the FDR's pair: the rules a later change must not
break, such as quality floors, architectural invariants and the imports a module is forbidden. The
Principal Architect writes it from the settled SRS, SDD and FDR and keeps it as `docs/nfdr.md`. Each
entry names the upstream fact it comes from.

## ADR

An ADR, an architecture decision record, records one significant architecture decision about the
product. The Principal Architect keeps them in `docs/adr/`, with an index. The records are
append-only: a decision that reverses an earlier one is a new record that supersedes it.

## Companion

A companion is the open-issues file beside a document, named like `PRD_open_issues.md`. A run that
writes a document does not stop to ask you, and puts what it could not settle there. A document is
done when no companion is left beside it. `companion-self-answer` answers a companion with nobody
present, and `/companion-answer` walks it with you.

## Answering run

The answering run is the run a documents chain starts after a document's writer leaves open
questions: `companion-self-answer`, working in the seat of the role that owns the document. It
decides every item it is allowed to decide, and leaves an item only you may settle open, with the
answer it would have given.

## Seat

A seat is a role's place in the work, the word KensaiApp's own files often use for a role. An item
in a companion can name the seat whose call it is, and each seat's items are answered in a run of
their own.

## Settled

A document is settled when no question is left for the owner and no product question is open. Its
`Status:` line then reads `Settled`. Before that it reads `Draft`. Once the owner ratifies it as the
source of truth, it reads `Locked`. Locking is the owner's act, never a run's.

## What-left file

The what-left file, `docs/what_left.md` in the product, lists what the product still has to build.
`first-what-left` writes it once the Agari is settled, a revised PRD adds what it newly wants, and
`readme-status` removes what has merged after each station closes.

## Code skeleton

A code skeleton is the starting tree of files for one language, kept under
`core/templates/skeleton-templates/`. Once a product's documents have settled, `product-card`
places one for each unit the SDD names, as a plain copy with no model involved.

## Launcher

A launcher is a script you run from a shell, outside a Claude Code session, at
`core/launchers/<name>/launcher.sh`. Most start their work as background runs and return at once.
`core/launchers/skill/launcher.sh` starts any single skill that has a `launcher.md` beside its
`SKILL.md`. The operations guide's section [Using launchers](operations.md#using-launchers) lists them.

## Chain

A chain is a launcher that walks a sequence of runs, each starting the next when it ends.
`chain-product` and `chain-agari` walk a project's documents, and `chain-change` and
`chain-development` walk one change through the pipeline. Two engines in `core/tools/` carry them:
`chain.py` for the documents and `chain_development.py` for a change.

## Documents chain

A documents chain is a chain that writes a project's documents, one at a time, upstream first. The
card's `Definition:` line names it: `chain-product` for `full`, `chain-agari` for `prd-agari`, and
none for `none`. It walks a spine.

## Change chain

A change chain walks one change through the pipeline, following a fixed table of steps.
`chain-change` also opens the station and the change where they are not open yet.
`chain-development` starts from the spec, for a change whose request already exists.

## Spine

A spine is the ordered list of documents a documents chain is handed by its launcher, and walks in
that order. The change chains have a fixed table of steps instead.

## Walk

A walk is one run of a chain, from its start to its end. Its state is kept in one file, so a stop
keeps it, and the same command started again carries on from what is on disk. A walk ends with a
reason, such as `settled`, `sealed` or `stopped`.

## Pipeline

The pipeline is the fixed sequence every change goes through: specs, design, plan, content,
implementation, code-integrity, audit and seal. Each step is a separate agent run, in its own role,
and a program, not a model, decides which step runs next. The README's section
[How a change moves](../README.md#how-a-change-moves) names implementation Build and code-integrity
Prove, and shows what each step leaves.

## Ask

Ask is the first step in the README's pipeline diagram: the PM writes the change request with
`tobiishi-open`. It comes before the pipeline's own steps. Of the chains, only `chain-change` runs
it.

## Spec

The spec is the pipeline's first step, and the document it leaves: the Product Owner's testable
specification of the change, `change_spec.md`, with the change's scope, behaviour and acceptance
criteria.

## Design

Design is the pipeline's step after the spec: the Architect writes `change_design.md`, how the change
is structured against the system that exists. It is not DESIGN, the product's design language.

## Plan

Plan is the pipeline's step after the design: the Tech Lead writes `tl_instruction.md`, an executable
plan for the Developer, with the gaps the design leaves filled.

## Content

Content is the pipeline's step after the plan: the Content Editor writes `change_text.md`, the exact
words the change puts in front of a person. It runs only when the design says the change publishes
text. It is not CONTENT, the product's content standard.

## Build

Build is the README's name for the implementation step: the Developer writes the code, each test
before the code it checks, and makes the closing commit.

## Prove

Prove is the README's name for the code-integrity step: the Senior Engineer proves that the code
does what the change intends, and leaves `code-integrity-report.md`.

## Audit

Audit is the pipeline's step after Prove: the Auditor reviews the spec, the design, the plan, the
content where it ran, and the code, each in a run of its own. Its findings never stop the change.

## Queue

The queue is a refine's next moves, run in order by `build-idea`. A row starts only when no other row
is running and the rows it waits on have landed. `build-idea` reads that they have landed off the
disk. A row for the owner's act stops the queue until you do the act and start `build-idea` again.

## Companion sweep

The companion sweep is a run of a project's documents chain that sweeps the product's companions. It
runs where a refine's next moves say one is owed. The card's `Definition:` line picks the chain:
`chain-product` for `full`, `chain-agari` for `prd-agari`, and no sweep for `none`.

## Seven ends

The seven ends are the ways a documents chain's round on one document can end:

- `settled`: the document is settled, and nothing is left to do.
- `empty_run`: the last run produced nothing, and the chain moves on.
- `left_for_the_owner`: an item is left for you to decide, on the document's companion.
- `could_not_be_settled`: a full round left the open items unchanged, so the skill that writes the
  document owes a repair.
- `machinery`: a run failed to complete, or its report was not in the expected shape.
- `cap`: the round limit was reached without the document settling.
- `no_runnable_command`: a run named as owed has no real launcher to start it.

The first two are not failures. `left_for_the_owner` is not one either: the chain records it and
walks on. Each of the other four stops the chain. The exception is a queue
that still holds something that could change the outcome: the chain works through that first. The
opening comments of `core/tools/chain.py` list the ends under THE SEVEN ENDS.

## Halt report

A halt report, `halt_report.md`, is the account a step leaves when it stops short of its result. The
stop message gives its path, and you read the file to see why the step stopped.

## Pin

A pin is a frozen copy of the host's `core/`, `.claude/` and `skills/` that a launched run reads
instead of the live files. Every launcher enters a pin first, so an edit made after the launch
cannot reach that run. A launcher that a run starts inherits the run's pin, except `build-idea`,
which takes a new pin when the host has changed.

## Context cap

The context cap is the size of context, in tokens, past which a Developer run finishes its task,
commits and hands over to a fresh run. It is set with `--context-cap` on `chain-change` and
`build-idea`, and the default is 250000. The hook that applies it reads the run's context through
ka-telemetry, an open-source package KensaiApp built; without the package, nothing is capped.

## Provider

A provider is the service a run's model comes from: `claude`, `codex`, `gemini`, `hf` or `ollama`.
`hf` is a Claude run aimed at Hugging Face's router, and `ollama` runs on your own local Ollama
models. `.providers.toml` at the instance root names the provider for each document, step and queue
row. `--provider`, or an exported `KENSAIAPP_AGENT_PROVIDER`, forces one provider for a whole walk.
The operations guide's section [Choosing a provider](operations.md#choosing-a-provider) has the rules.

## Intelligence

A skill's intelligence is the pair of model and effort it runs at. The work sets it, not the role
that runs the work. Each skill declares it in one file per provider, `intelligence/<provider>.md`
beside its `SKILL.md`, with the reason for both. The skill launcher refuses a launch on a provider
with no file in that folder.

## Tier

A tier is one of the four model levels a run with no skill behind it is given, such as a delegated
agent's run. The judgment in the work picks it: authoring or deciding takes a top tier, applying a
plan already decided takes the worker tier, and one mechanical change made many times takes the
cheap tier. `core/doctrine/governance/model_assignment.md` binds each tier to a model of each
provider.

## Language packet

A language packet holds the engineering rules for one language, in
`core/doctrine/engineering/languages/<language>/`. Every packet answers the same concerns, and the
gate environment is one of them. There are packets for JavaScript, Python, Rust, Shell, Swift and
TypeScript. A language with no packet falls back on a floor of rules that holds for any language.

## Gate

A gate is a check that must pass before work moves on. A language packet's quality gates are the
checks run over a product's code, such as its linting, its type checks and its tests. The change
pipeline's gates are checks a program reads off what a step left, such as the senior engineer's
report declaring `Integrity: pass`. A failed one halts the walk.

## Gate environment

A gate environment is where a product's tests and other gates run. The product's CI decides it: a
Podman container when the CI runs on Linux, a macOS guest under Tart when it runs on macOS or the
product holds Swift, and your own Mac for a product with no CI. `--gate-owners-mac` on a change chain asks for your Mac instead.

## Finding

A finding is a defect in KensaiApp itself, such as in a skill, a prompt, a rule, a hook or a
launcher, noticed while doing something else. A small one is fixed in place, on the branch where it
was found, and a larger one becomes a seed. One that is not fixed is written to
`docs/findings/<date>_<slug>.md`. The audit step's findings are a separate kind, kept in each
change's `flow_findings/`.

## Panel

The panel is a pane in a Claude Code session, opened with `/kensaiapp-panel`. It lists the chains
waiting on you and the chains running now, under the headings `WAITING ON YOU` and `RUNNING NOW`, with
each one's seed, station, walk and step, and when that walk started. It reads them again every 15 seconds. It is a Claude Code plugin in `core/tools/kensaiapp-panel/`, and
you turn it on yourself.

## Journey page

The journey page is one HTML page of an instance's journey, written by `core/tools/journey_status.py`.
It shows the seedbeds, the stations and the changes, and names every place the instance has drifted
from the journey's rules. It only reads.

## Notifier

The notifier is a program you name in `KENSAIAPP_NOTIFIER`: an executable that takes a message as
its one argument. The launchers that start background runs, and the delegate when it finishes, send
their messages through it.
With the variable unset, nothing is sent.

## Receiver

The receiver is the program that takes in Claude Code's telemetry, `ka-telemetry receive`, from
ka-telemetry, an open-source package KensaiApp built. You start it yourself, as the how-to
guide's [How to collect telemetry](how-to.md#how-to-collect-telemetry) shows, and it appends what it receives to files on your machine. A launcher
finds it through the endpoint file it publishes.

## ID

A run ID names one run a launcher started, so that its telemetry can be found again. It is attached
together with the run's arm: the name of the folder of the launcher that started the run, such as
`chain-change`. A run whose arm cannot be read from that folder still gets a run ID, with no arm. The
launcher prints it on its `Telemetry:` line. `core/tools/run_provenance.py` reads the run's
provider, model and effort back by that ID, from what reached the receiver.

## Kaizen

Kaizen is how a skill is improved: it is run against a real case, what it produced is audited, the
skill is fixed, and it is run again, round after round. The owner runs each round. This part of
KensaiApp is experimental.

## Lens

A lens is one way of judging a skill through what it produced, kept as one file under
`core/doctrine/kaizen/lenses/`. Each auditor in a kaizen round loads only its own lens, so it keeps
looking for its own kind of failure.

## Cold read

A cold read is a reading by an agent that did not write what it reads, and comes to it fresh. The
cold-read launcher, `core/launchers/cold-read/launcher.sh`, opens one blind reader for each file of
a skill's own stack.

## Fix packet

A fix packet is a committed file in which the fix-author writes a skill's fix, with the exact
replacement text. The fixer applies it only once the owner has marked it approved.

## Fix-author

The fix-author decides a skill's fix and writes its exact replacement text. It applies nothing. In
a kaizen round it writes the fix in a fix packet. Its agent is `kaizen-fix-author`.

## Fixer

The fixer applies a fix the fix-author decided, and commits it. It decides nothing. In a kaizen
round it acts only on a fix packet the owner has marked approved. The eval-fix pass, which runs
unattended after a skill's evals, hands it the fix-author's decision directly. Its agent is
`kaizen-fixer`.

## Ratify

To ratify a skill is the owner's call that it is ready to ship. The auditors advise; they do not
hold the gate.

## The journey in KensaiApp's terms

1. Pick one seed. The PM chooses the single idea to work now from the candidate pool and lifts it to
   the seedbed's root. No other candidate moves. The picked idea becomes the one active seed.
2. Re-cut the checklist. The picked seed carries a checklist of the stations it will take. The
   checklist is the Principal PM's proposal, made when it cut the seed. Re-cutting it is the PM's
   first act on the picked seed: where the station boundaries fall, and in what order they are
   walked. Where the PM departs from the proposal, it logs that in the seed.
3. Open a station, a Shukuba. The PM opens the current station, a concrete stretch of work with its
   own reached-when. Exactly one station is active at a time. A single idea usually needs more than
   one, walked in sequence, each one leg of that idea's route.
4. Walk the station through the pipeline. The building inside a station runs as one or more
   Tobiishi, which are change units. The PM opens each with `tobiishi-open`, and the chain carries it
   end to end: specs → design → plan → content → implementation → code-integrity → audit → seal. A
   station may take several Tobiishi before its reached-when is met.
5. Seal each change unit. Each change unit is sealed by `tobiishi-seal`, and it lands sealed on
   `main`.
6. Refine the route. After each change unit lands, the PM runs `shukuba-refine`. It re-reads the
   route against what the unit left and what moved upstream. It leaves a report and recommendations
   with the seed.
7. Run the next moves. The report's `## Next moves` is then run by
   `core/launchers/build-idea/launcher.sh`.
8. Close the station. When the station's reached-when is met, the Scrum Master closes it with
   `shukuba-retire`. In one case the PM closes it instead: when the PM's `shukuba-park` finds the
   station already reached. Once it is closed, the station's file moves to its trail, and the idea's
   checklist item is ticked. When the idea's checklist has a next station, that station opens, back
   to step 3.
9. Retire the seed. When the idea's whole checklist is walked, the Scrum Master retires the seed to
   the Nemawashi trail with `nemawashi-retire`. It is a mechanical move that restores nothing, and
   the seedbed's root is left empty.
10. Answer the retired seed. The Principal PM answers it with `nemawashi-refine`. Every
    recommendation `shukuba-refine` left in the retired seed's folder is processed, and the candidate
    pool is re-read with the drops made there. A report lands.
11. Run what the answer names. The report's `## Next moves` names what is owed, and it runs. It can
    name the companion sweep: `chain-product` when the project card's `Definition:` line reads
    `full`, `chain-agari` when it reads `prd-agari`, and no sweep when it reads `none`. It can name a
    new cut of seeds from the product's documents, with `seeds-from-product-docs`. That cut is owed
    whenever the documents hold work that no candidate seed carries, whether candidates are left or
    not. After them, the PM picks the next seed and cuts its route, back to step 1.

## The journey in industry, ticketing and Jira terms

The table sets each step above beside its nearest term in three other vocabularies: the software
industry's, a ticketing system's and Jira's. Each column is a separate comparison, so one step can
match different things in different columns. The last column says where each comparison ends.

Jira is Atlassian's work tracker. Atlassian calls a piece of work a work item, and so does this
table. A work item's status is its current place in its space's workflow. Its key is its unique
identifier, made of the space key and a sequential number. A Story is the work item of the standard
level. A Subtask is a work item of the level below a Story, for smaller pieces of work. A resolution
is the field that records why a work item was moved to Done, and it is usually set when the status
changes.

The nearest match to a ticket id, or to a Jira key, is the triple `project · kind · name`. Kind is
nemawashi, shukuba or tobiishi, and name is the item's own date and slug. A move changes none of the
three. Where an item's file sits says where it stands, as a ticket's status does: a seed in
`unpicked/` is a candidate, and a seed at the seedbed's root is active.

| Step | Industry term | Ticketing term | Jira term | Where the comparison ends |
|---|---|---|---|---|
| 1. Pick one seed | Taking the next piece of work from a backlog | Taking one ticket from the candidates and putting it in progress | Taking a work item and giving it another status. A seed is comparable to a Story | A backlog can hold many pieces of work in progress at once; here no other candidate moves. A ticket id or a key is given when the item is created, and its status is a field. Here the place a seed's file sits says where it stands, so a pick renames the file and changes none of the three |
| 2. Re-cut the checklist | Shaping a roadmap | Breaking a ticket down into sub-tasks and putting them in order | Splitting a Story into Subtasks | A roadmap is shared as a plan of what ships when; here the checklist is the Principal PM's proposal, and the PM re-cuts it. Sub-tasks and Subtasks get ids or keys of their own; here the checklist is carried by the picked seed |
| 3. Open a station | Setting the next milestone | Starting a sub-task and putting it in progress | Moving a Subtask to a new status | Several milestones, or several sub-tasks of a ticket, can be in progress at once, and several Subtasks of a Story can hold a status at once. Here exactly one station is active at a time |
| 4. Walk the station through the pipeline | A CI pipeline carrying a change from one stage to the next | A ticket moving from one status to the next | A work item moving through the statuses of its workflow | A CI pipeline builds and tests code, and a ticket or a work item changes status when someone moves it. Here the chain carries a change unit from specs to seal |
| 5. Seal each change unit | Merging a pull request | Resolving a ticket | Filling in a work item's resolution | A pull request is a proposal that waits for a decision to merge; here the chain carries a change unit end to end, and it lands sealed on `main`. Resolving a ticket usually ends the work it tracks, and a Done work item ends it; here a station may take several change units before its reached-when is met |
| 6. Refine the route | Holding a retrospective | Editing the remaining sub-tasks of a ticket once one of them is resolved | Jira has no term of its own for this step | A retrospective is a conversation held by a group, and editing a ticket changes the ticket itself. Here the PM runs `shukuba-refine`, and the result is a report and recommendations left with the seed |
| 7. Run the next moves | Acting on the follow-up items a look back leaves | Working through the follow-up tasks listed on a ticket | Jira has no term of its own for this step | Follow-up items and tasks wait until someone takes them; here `build-idea` runs the moves the report names |
| 8. Close the station | Work meeting its definition of done | Closing a sub-task by giving it a closed status. A station set down unreached waits in `shukuba/parked/`, as a sub-task waits on hold | Moving a Subtask to a Done status, with a resolution | A definition of done is agreed for each piece of work by whoever builds it, and a sub-task is closed by whoever finishes it. In Jira a Done work item need not have a resolution. Here the station's reached-when has to be met, and the Scrum Master closes it, or the PM in its one case |
| 9. Retire the seed | Archiving a finished initiative | Moving a resolved ticket into an archived status. A seed ruled out or superseded goes to `nemawashi/drop/`, as a ticket is closed without the work being done | Moving a Story to Done once its Subtasks are done | Archiving can come with a judgement of how the work went, and in Jira moving a Story to Done is a change of status like any other. Here the seed's file moves to a trail, and `nemawashi-retire` is a mechanical move that restores nothing |
| 10. Answer the retired seed | Refining a backlog once a body of work is done | Going through the notes left on a closed ticket and re-reading the tickets that are still open | Jira has no term of its own for this step | Backlog refinement ends with the list itself reordered, and a note on a ticket is read by whoever opens that ticket. Here the Principal PM processes every recommendation left in the retired seed's folder, and the answer ends with a report |
| 11. Run what the answer names | Planning the next iteration | Running the follow-up work of a closed ticket before the next ticket is taken | Jira has no term of its own for this step | Iteration planning fixes what the next iteration holds, and the next ticket is taken straight from the open tickets. Here the companion sweep and a new cut from the documents run where owed, and then the PM picks the next seed and cuts its route |
