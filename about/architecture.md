# Architecture overview

This overview is the reference behind the [README](../README.md) on how KensaiApp is organised, the
journey's names, how a project gets from its documents to its done, and the rules the system enforces.

## How KensaiApp is organised

You work in an instance: one git repository that holds KensaiApp's shared core, its roles and
skills, and your projects. An instance has a *bearing*: one or more long-term directions, declared
once and never finished. KensaiApp's word for it is Michi 道, one of [the Japanese names](#the-japanese-names).

A project is the work of building one product: its card, its journey and
its open questions, under `system/projects/<name>/`. The product is what gets built: its code and its
own decision documents, such as its requirements and its architecture records. A product can be a
whole application or only part of one. The project's card points at the product by path. The product can sit inside the instance, under `products/`, or in a git
repository of its own. One instance can hold several projects, each with its own product.

### Roles and overlays

The work is split between roles, as in a software team: a PM, a product owner, an architect, a tech
lead, a developer, a senior engineer and others. Every run works as one of them. A
role is defined once, in the shared core. An instance can lay an overlay over it: a short file that
states only what is different about that role in that instance, such as the files it reads there
first. The rules the roles follow are layered the same way: the core's, then the instance's, then a
project's.

### The instance's experience

Each instance also has an experience layer: what every product under it may and may not look like
and sound like, in a visual pair and a voice pair of files under `system/experience/`. The skills
`experience-visual` and `experience-voice` write them, in that order. Neither asks you anything while it
runs; what it cannot settle it leaves as open questions beside the files. Run them from your shell:

```bash
core/launchers/skill/launcher.sh experience-visual
core/launchers/skill/launcher.sh experience-voice
```

Or in a session, as the role that owns each:

```text
/add-dir skills/cdo
> cdo: /experience-visual

/add-dir skills/content-manager
> content-manager: /experience-voice
```

### One mechanism, several instances

A host is an instance that keeps the shared core. A satellite is an instance with no core of its
own: it reads its host's, so a change to the core reaches every satellite as soon as it lands. That
lets you keep different work in different repositories, all run by the same mechanism. KensaiApp itself is
built that way, from one host with satellites beside it. You don't need satellites: a single instance works on its
own. [More than one instance](operations.md#more-than-one-instance) shows how to set one up.

## The Japanese names

The parts of a project's journey, described in the next section, have Japanese names, in the same
family as the word kensai. The table gives the
nearest industry term first.

| Industry term | KensaiApp's word | What it is |
|---|---|---|
| Long-term direction | Michi 道 | A direction the whole instance steers by and never finishes |
| Definition of done | Agari 上がり | When one project's product is done |
| Backlog of candidate work | Nemawashi 根回し | The seedbed: ideas, each a candidate route toward done |
| Milestone | Shukuba 宿場 | A station: the one stretch of work being walked now |
| Merged pull request | Tobiishi 飛び石 | A stepping stone: one change carried from ask to sealed on `main` |

Each term is the nearest match, not an exact one. Where each comparison ends is in the glossary's
section [The journey in industry, ticketing and Jira terms](glossary.md#the-journey-in-industry-ticketing-and-jira-terms).

## From requirements to a product

Once a project is set up, its journey can start. The journey is how a project gets from its
documents to its definition of done, and after the first launch it walks itself:

1. The Principal PM cuts the product's documents into seeds (`seeds-from-product-docs`). A seed is a
   candidate route toward done, with a checklist of stations.
2. The PM picks one seed (`nemawashi-pick`) and cuts its checklist into the stations to walk
   (`stations-from-seed`).
3. `chain-change` opens a station (`shukuba-open`), opens a change in it (`tobiishi-open`), and carries
   the change through [the pipeline](../README.md#how-a-change-moves) to the seal (`tobiishi-seal`). A station that is not reached can be
   parked (`shukuba-park`) and opened again later.
4. After every sealed change, the PM refines the station (`shukuba-refine`) and writes the next moves:
   another change, or closing the station. The route is decided again each time, from what the
   change found: the stations ahead can be re-cut, reordered, parked or dropped, but what was asked
   for and the product's documents do not move
   ([The route is re-decided after every change](how-it-works.md#the-route-is-re-decided-after-every-change)).
5. The Scrum Master closes a station once it is reached (`shukuba-retire`). When a seed's checklist is
   walked, the Scrum Master retires the seed (`nemawashi-retire`), and the Principal PM refines the
   seedbed (`nemawashi-refine`): a new cut from the documents, or the next pick.

```
CUT             PICK            STATIONS        CHANGE
┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
│ Principal │──▶│ PM        │──▶│ PM        │──▶│ chain-    │◀─┐
│ PM        │   │           │   │           │   │ change    │  │ next change
└───────────┘   └───────────┘   └───────────┘   └───────────┘  │
      ▲               ▲                               │        │
      │ new cut       │ next pick                     ▼        │
┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐  │
│ Principal │◀──│ Scrum     │◀──│ Scrum     │◀──│ PM        │──┘
│ PM        │   │ master    │   │ master    │   │           │
└───────────┘   └───────────┘   └───────────┘   └───────────┘
REFINE SEEDS    RETIRE SEED     CLOSE STATION   REFINE
```

Once it starts, it runs without you. It stops when it needs you, for an act only you can do or a
question only you can answer, when a step fails, or when you stop it. It ends when no seed is left and
nothing is owed. The last refine says so, and whether the product has reached its done is your call.

### Product documents chains

A project's documents are written by a chain of their own, the one its card's `Definition:` line
names. `chain-product` walks them in a fixed order, and each is written by the role that owns it:

| Document | What it is | Written by |
|---|---|---|
| PRD | The product's requirements | CPO |
| Agari | The definition of done | CPO |
| SRS | The software requirements specification | CTO |
| UXD | The user experience (experimental) | CDO |
| DESIGN | The design language | CDO |
| CONTENT | The content standard: voice, terms, message patterns | Content Manager |
| SDD | The software design | CTO |
| FDR | Functional design requirements: the behaviour every later change is built against | Principal PM |
| ADR | Architecture decision records, one per significant decision | Principal Architect |
| NFDR | Non-functional design requirements: the rules a later change must not break | Principal Architect |

`chain-agari` walks the PRD and the Agari only. A document that is settled, with no open questions, is
walked past without a run. `chain-change` runs the project's documents chain before each change, so a
document with open questions is dealt with before the next change starts.

When the documents have settled, you run one launcher yourself. A model run writes the card's fields
for the product's languages and test command, and the product's README. The launcher then copies a
code skeleton for each unit the software design names, with no model involved. It runs in the
foreground and waits for both halves, and it sends no message:

```bash
core/launchers/product-card/launcher.sh my-app
```

#### How a document's open questions get answered

A run that writes a document does not stop to ask you. What it cannot settle, it writes as open
questions in a companion file beside the document. The chain then starts an answering run,
`companion-self-answer`, in the seat of the role that owns the document. It decides every item it is
allowed to decide. An item only you may settle stays open, with the answer it would have given. It
then lists the runs now owed, and the document's writer runs again and folds the answers in. To
answer the items left for you, use `/companion-answer` in a session
([Interactive sessions](operations.md#interactive-sessions)).

### The chain launchers

Each part of the journey above has a launcher:

| Launcher | What it walks |
|---|---|
| `chain-product` | The product documents, PRD to NFDR |
| `chain-agari` | The PRD and the definition of done |
| `chain-change` | One change: open a station if none is open, open the change, the pipeline, the seal and the refine. At its end it starts `build-idea` |
| `build-idea` | The next moves a refine wrote, run as a queue: close a station, retire a seed, pick, cut, or the next change, which starts `chain-change` again |
| `chain-development` | The pipeline from the spec on, for a change whose request already exists |
| `product-card` | The card's fields, the product README and the code skeleton |

A documents chain walks a spine: the ordered list of documents its launcher hands to the chain engine.
The change chains have a fixed table of steps instead. All of them share the rest:

- A launcher starts the first run in the background and returns. Each run, when it ends, starts the next.
  `product-card` is the exception: it runs in the foreground and waits.
- The walk's state is one file under `system/logs/`, beside each run's log.
- `chain-product`, `chain-agari`, `chain-change`, `build-idea` and `chain-development` take `--stop`,
  which stops the runs in flight and keeps the state.
- Run the same command again and it carries on from what is on disk, rather than starting over.
- Each launch runs on a pinned copy of the shared core, so an edit made after the launch cannot reach
  a run in flight. `build-idea` takes a new pin when the host has changed, so the queue a walk runs at
  its end can run on newer files.

Most of the time you run one command, and the loop between `chain-change` and `build-idea` does the rest:

```bash
core/launchers/chain-change/launcher.sh my-app
```

## Rules the system enforces

Some of KensaiApp's rules are held by code rather than by the model: hooks, a commit check and the
launchers.

| Guard | What it does |
|---|---|
| `development-bash-approve.py` | Approves a Bash call only when every command is in a conservative safe set; anything else goes to the normal permission prompt |
| `read_first_guard.py` | Refuses an agent run's acting calls until it has read the files its agent file tells it to read first |
| `brief_anchor_guard.py` | Refuses to spawn an agent whose brief cites something that is not there |
| `written_forward_guard.py` | Refuses a write that narrates a file's own state into a scoped document |
| `context_cap.py` | Tells a developer run past its context cap to finish its task, commit, and hand over to a fresh run. It reads the run's context through ka-telemetry; without the package, it caps nothing and says so |
| `task_map_salience.py`, `manifest_salience.py`, `standing_rules_salience.py` | Inject, at every session and subagent start, the task-to-rule map, the map of where files live, and the rules that bind without being looked up |
| `commit-msg` check | Refuses a commit or merge that lacks its required trailers, such as `Role:` and `Surface:` |
| Permission mode | A launched Claude run uses Claude Code's auto permission mode, and no launcher bypasses permissions. A run started in the background, the default, can still stop on a prompt and wait; a print run takes none, so an action it would have to ask about is denied and the run carries on |
| Product checkout | A run that leaves new uncommitted changes in the product's checkout halts the walk, with nothing relaunched over them |
| Pins | A launched run reads a frozen copy of the shared core, so an edit made after the launch cannot reach it. `build-idea` takes a new pin when the host has changed |
| Worktrees | Each change gets its own branch and working folder |

Where an AI decision and a mechanical rule conflict, the rule wins, and the AI says so rather than
working around it.

<details>
<summary>How the skills get better: evals, cold reads and kaizen</summary>

This part is experimental.

- Evals run each case of a skill twice, once with the skill and once without it, and grade each run.
- Kaizen exercises a skill against a real case, audits what the run produced, improves the skill and
  runs it again, round after round. Each auditor loads only its own lens.
- The cold-read launcher opens blind cold reads over a skill's producing stack.
- Deciding a fix and applying it are kept in separate hands: a fix-author decides, and a fixer applies
  what it decided without deciding again. In a kaizen round, the fixer acts only on a fix packet the
  owner has marked approved; after a cold read or an eval run, it applies the fix-author's decision
  directly.
- Ratifying a skill is the owner's call, not a gate the auditors hold.

</details>
