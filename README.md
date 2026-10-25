<div align="center">

<h1>KensaiApp</h1>

<p><strong>AI roles carry a product from requirements to merged code on Claude Code. Every step leaves a file in git, and a program, not a model, decides what runs next.</strong></p>

<p>
<img alt="Runs on Claude Code" src="https://img.shields.io/badge/runs%20on-Claude%20Code-d97757?style=flat-square">
<img alt="Version 0.4.0" src="https://img.shields.io/badge/version-0.4.0-2da44e?style=flat-square">
<img alt="Uses Python 3.13 or later" src="https://img.shields.io/badge/python-3.13%2B-3776ab?style=flat-square">
<img alt="Licence: MIT" src="https://img.shields.io/badge/licence-MIT-0969da?style=flat-square">
</p>

<p><a href="#who-it-is-for">Who it is for</a> · <a href="#how-a-change-moves">How a change moves</a> · <a href="about/how-it-works.md">How it works</a> · <a href="#getting-started">Getting started</a> · <a href="#one-change-from-request-to-patch">One change, from request to patch</a> · <a href="#examples">Examples</a> · <a href="#built-with-kensaiapp">Built with KensaiApp</a> · <a href="about/architecture.md">Architecture overview</a> · <a href="about/operations.md">Operations guide</a> · <a href="#still-changing">Still changing</a></p>
<p><img src="about/images/overview.svg" alt="KensaiApp in three stacked bands. Product intent: PRD, then definition of done, then product documents. Journey: seed, then station, then change. One change: Ask by the PM, Spec by the product owner, Design by the architect, Plan by the tech lead, Content by the content editor, only when the change publishes text, Build by the developer, Prove by the senior engineer, Security by the senior engineer, Audit by the auditor, Seal by the PM. Below them: lands in git: documents, code, tests, findings, the trail of each change. On the side: the owner gives direction and makes the calls only you can make; a program decides what runs next; each role has one job." width="100%"></p>
</div>

KensaiApp started as an experimental private project, which grew into a public one. It was built as
an agentic software development system on Claude Code, and it covers the software development
lifecycle (SDLC), from requirements to merged code. The idea was to "teach" the model and its agents
software engineering principles by running their work through that full lifecycle: requirements,
design, a plan, tests written before the code, and review.

Some of its skills were inspired by published work: [agent-skills](https://github.com/addyosmani/agent-skills)
by Addy Osmani, [claude-superskills](https://github.com/ericgandrade/claude-superskills) by Eric
Andrade, and Anthropic's [skill-creator](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator).
[NOTICE](NOTICE) lists the parts that come from them, each under its own licence.

One of the first ideas was that it would build itself, as dogfooding: Claude wrote all of
KensaiApp's code through KensaiApp's own mechanics. The code of the products it builds is written
entirely by KensaiApp.

It is maintained privately, so there is no promise of support and no roadmap.

The [how-to guide](about/how-to.md) adds step-by-step detail to this README, for when you need it. The
[glossary](about/glossary.md) explains each word, and the
[agentic description](about/agentic_description.md) maps KensaiApp onto agentic-engineering terms.
[How it works](about/how-it-works.md) explains how a change is checked, what follows the checks and how
the next step is decided.
The [architecture overview](about/architecture.md) says how KensaiApp is organised, what the journey's
Japanese names mean, how a project gets from its documents to its done, and which rules the system
enforces. The [operations guide](about/operations.md) covers running it: where things stand,
interactive sessions, choosing a provider, using launchers, more than one instance, findings and the
additional features.

## Who it is for

KensaiApp was written for its author's own use, and it has not been compared with other
solutions. In its author's view, it can still help two groups: people looking for a spec-driven,
multi-agent system that builds apps, and AI and software engineers looking for ideas.

The author believes that, with the right adjustments, it can support other workflows too, not only
automating the software development lifecycle.

### What it does not promise

KensaiApp is maintained privately, so it comes without formal support: there is no promised timeline
for a fix, no stability promise and no roadmap. Issues are welcome: open one for a problem you hit or
an idea you have, and it will be read. Outside contributions, pull requests included, are not accepted for now, maybe later.

KensaiApp's output has not been evaluated against the output of another way of working, such as a
developer working without it.

## How a change moves

A project's product is built one change at a time. How a project's documents become its changes is in
[From requirements to a product](about/architecture.md#from-requirements-to-a-product).

Every change goes through the same pipeline. Each box is a separate agent run with its own role,
and a program, not a model, decides which step runs next: it starts a step only once the run before
it has ended and left its result on disk.

```
ASK             SPEC            DESIGN          PLAN            CONTENT *
┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
│ PM        │──▶│ Product   │──▶│ Architect │──▶│ Tech lead │──▶│ Content   │
│           │   │ owner     │   │           │   │           │   │ editor    │
└───────────┘   └───────────┘   └───────────┘   └───────────┘   └───────────┘
                                                                      │
                                                                      ▼
SEAL            AUDIT           SECURITY        PROVE           BUILD
┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
│ PM        │◀──│ Auditor   │◀──│ Senior    │◀──│ Senior    │◀──│ Developer │
│           │   │           │   │ engineer  │   │ engineer  │   │           │
└───────────┘   └───────────┘   └───────────┘   └───────────┘   └───────────┘

* the content step runs only when the change's design says it publishes text
```

| Step | Role | What it leaves |
|---|---|---|
| Ask | PM | A change request: the next change the project's current work calls for |
| Spec | Product owner | A testable specification of the change |
| Design | Architect | How the change is structured against the system that exists |
| Plan | Tech lead | An executable plan, with the gaps in the design filled |
| Content | Content editor | The exact words the change puts in front of a person |
| Build | Developer | The code, each test written before the code it checks |
| Prove | Senior engineer | Proof that the code does what the change intends, with the tests nobody wrote |
| Security | Senior engineer | A security report: the product's dependency audit answered, and the change's code read for security holes, fixed where its rules allow |
| Audit | Auditor | One findings file per step it reviews: how well that step did its job. It checks KensaiApp, not the product, and never fixes what it finds |
| Seal | PM | The change merged into `main`, and its folder moved to where sealed changes are kept |

[How it works](about/how-it-works.md) explains the three checks, where what they find goes and how
the next step is decided.

## How the work is kept in check

Each point is stated in full in the section it links to.

- A program, not a model, decides which step runs next. It starts a step only once the run before
  it has ended and left its result on disk ([How a change moves](#how-a-change-moves)).
- Every run works as one role, as in a software team, and each step of a change is a separate agent
  run with its own role ([Roles and overlays](about/architecture.md#roles-and-overlays)).
- Each step leaves its result in a file. A sealed change is merged into `main`, and its folder is
  kept where sealed changes are kept, so its files can be read afterwards
  ([One change, from request to patch](#one-change-from-request-to-patch)).
- The developer writes the code, each test before the code it checks. The senior engineer proves that
  the code does what the change intends, and then reviews it for security. The auditor lists the
  defects it finds in how each step did its job, and never fixes them ([How a change moves](#how-a-change-moves)).
- What the checks find is read before the next change: the route ahead can change, but what was asked
  for, and the product's documents, do not ([How it works](about/how-it-works.md#the-route-is-re-decided-after-every-change)).
- A walk stops when it needs you, for an act only you can do or a question only you can answer, when
  a step fails, or when you stop it ([From requirements to a product](about/architecture.md#from-requirements-to-a-product)).
- Some rules are held by code rather than by the model: hooks, a commit check and the launchers.
  Where an AI decision and a mechanical rule conflict, the rule wins
  ([Rules the system enforces](about/architecture.md#rules-the-system-enforces)).

## Getting started

### 1. Install what KensaiApp uses

- Claude Code
- Python 3.13 or later, as `python3`
- pytest and pytest-xdist, for that same `python3`
- git

KensaiApp's hooks and launchers run whichever `python3` your shell finds first, so
`python3 --version` must show 3.13 or later. On a Mac, the `python3` that Apple's command-line
tools install is older, and the launchers fail on it.

KensaiApp's own code uses only Python's standard library. Its tests, and a walk's closing gate on a
product with Python tests, run under pytest with pytest-xdist:

```bash
python3 -m pip install pytest pytest-xdist
```

What only some parts need is in the how-to guide's
[How to install what KensaiApp uses](about/how-to.md#how-to-install-what-kensaiapp-uses).

### 2. Clone, and make your provider file

```bash
git clone https://github.com/eyalgo/kensaiapp.git
cd kensaiapp
cp .providers.toml.example .providers.toml
```

### 3. Open Claude Code in the clone

The first session switches on KensaiApp's commit hooks. If the clone already has hooks of its own,
they are kept, and KensaiApp's commit check then runs only in runs a launcher starts.

### 4. Set up your first project

```
/add-dir skills/interactive-product
/project-setup
```

`/project-setup` turns your product idea into a project in one plain-language conversation, then
starts the chain that writes the project's requirements document (PRD) and its definition of done.

It asks for the project's name first, then what kind of project it is, and whether you have
anything to start from: notes, documents, a CV, old code.
Give their paths or links, with one line on what they are. The project's card records them, and the
run that writes the PRD reads them. They are read as source material, not taken as finished
documents. The [how-to guide](about/how-to.md) takes it from there. Your first run has worked when the project's PRD and its definition of done are written, with any open questions in a companion file beside each.

<p align="center"><a href="about/images/getting-started.mp4"><img src="about/images/getting-started.png" alt="A Claude Code session in a fresh clone, asked to follow the README's setup steps. Claude reports the tools present, the provider file made, the commit hooks switched on, the panel already set, and the first project left to start. Then /project-setup asks for the project's name and the questions about it. On the right, the kensaiapp pane: nothing waiting on you, nothing running." width="100%"></a></p>
<p align="center"><sub>A fresh clone set up in a container, then <code>/project-setup</code> for a new project. Click for the recording: 48 seconds, no sound. A real session.</sub></p>

#### Types of projects

Some of the setup's answers decide a project's shape.

<details>
<summary>Where the product lives, and how much is written down before the code</summary>

Where the product lives:

| Answer | What it means |
|---|---|
| Here (internal) | The product is a folder in the instance, `products/<name>` |
| Its own repo (external) | The product is a git repository that already exists, at an absolute path. The setup commits once in the instance and once in the product's repository |

How much of the product is written down before the code, on the card's `Definition:` line:

| Value | Chain | What it writes |
|---|---|---|
| `full` | `chain-product` | Every product document, from the PRD to the architecture records (see [Product documents chains](about/architecture.md#product-documents-chains)) |
| `prd-agari` | `chain-agari` | The PRD and the definition of done only |
| `none` | none | No product documents. Each change is built from its own request |

`/project-setup` sets `full` for software and `prd-agari` for a product with no code. To choose
another, edit the line on the card.

</details>

Steps 5 and 6, the panel and telemetry, are optional: everything else works without them.

### 5. Turn on the panel

The panel is a Claude Code mod, a plugin that ships in `core/tools/kensaiapp-panel/`. Nothing in the
clone turns it on. Add its absolute path to the `env` block of your own `~/.claude/settings.json`,
then restart Claude Code:

```json
"env": { "CLAUDE_CODE_PLUGIN_DIRS": "/absolute/path/to/kensaiapp/core/tools/kensaiapp-panel" }
```

`/kensaiapp-panel` then opens the pane in any session inside an instance. Everything else works without it.

### 6. Collect telemetry

This step is there if you want to collect telemetry: what each run costs in tokens and money, and each
request it makes to the model. It runs on [ka-telemetry](#built-with-kensaiapp), installed once into
KensaiApp's own environment in your home folder. The how-to guide's
[How to collect telemetry](about/how-to.md#how-to-collect-telemetry) installs it, starts its receiver
and has your own sessions send theirs. Everything else works without it.

## One change, from request to patch

The release keeps the files of every sealed change in the swe-benchmark-poc example
([Examples](#examples)), so one change can be read from its request to its patch. In
`2026-10-10_sympy-11618`, the request asks for a fix to an issue in SymPy: `Point.distance` gives the
wrong answer for two points of different dimensions.

The product is SymPy's own repository, worked in a local clone, so the release holds the change's
code as its patch. For publication, the issue's text is replaced by its link and a summary, and a
path on the machine the change ran on reads `<the issue's clone>`.

The files, in the order the pipeline wrote them:

1. [The change request](system/projects/swe-benchmark-poc/journey/tobiishi/trail/2026-10-10_sympy-11618/change_request.md): the issue, linked and
   summarised, and what must not be done. Its last line says when the change was sealed and merged
   into `main`.
2. [The spec](system/projects/swe-benchmark-poc/journey/tobiishi/trail/2026-10-10_sympy-11618/change_spec.md): the product owner's testable
   specification, its rules and examples.
3. [The design](system/projects/swe-benchmark-poc/journey/tobiishi/trail/2026-10-10_sympy-11618/change_design.md): the architect's account of
   where the change goes and what it touches. It says the change publishes no text, so the content
   step did not run.
4. [The plan](system/projects/swe-benchmark-poc/journey/tobiishi/trail/2026-10-10_sympy-11618/tl_instruction.md): the tech lead's instruction to
   the developer, task by task, with the behaviours each task's tests must verify.
5. [The patch](products/swe-benchmark-poc/sympy__sympy-11618/patch.diff): the developer's code and
   tests, as the change was sealed.
6. [The code-integrity report](system/projects/swe-benchmark-poc/journey/tobiishi/trail/2026-10-10_sympy-11618/code-integrity-report.md): the
   senior engineer's check of the code against the request, the spec, the design and the plan.
7. [The audit's findings](system/projects/swe-benchmark-poc/journey/tobiishi/trail/2026-10-10_sympy-11618/flow_findings/): one file for each step
   the auditor reviewed, the spec, the design, the plan and the implementation. Each lists the defects
   found in that step's output.

## Examples

KensaiApp ships with these examples.

- tracker17, in `products/tracker17` and `system/projects/tracker17`: a simple task-tracking app.
  KensaiApp built it, and it was used to build KensaiApp. It is a work in progress, developed
  alongside KensaiApp, and published as an example of KensaiApp's output.
- swe-benchmark-poc, in `products/swe-benchmark-poc` and `system/projects/swe-benchmark-poc`: a proof
  of concept of how KensaiApp handles a different kind of input. It holds issues from the public
  benchmark SWE-bench Verified, chosen from those KensaiApp worked on 2026-10-10 and
  2026-10-11. KensaiApp was given only each repository as it stood before the fix, and the issue's
  text. Each issue keeps its patch, and its change's trail from the request to the integrity report.
  The project's card sets `Definition: none`, so each change was built from its own request.

## Built with KensaiApp

Products KensaiApp built that are published on their own.

- [ka-telemetry](https://github.com/eyalgo/ka-telemetry): per-agent tokens, time and cost for Claude
  Code, from its telemetry and transcripts, on your own machine. A Python command-line tool and
  library, on PyPI as [`ka-telemetry`](https://pypi.org/project/ka-telemetry/). KensaiApp's own
  telemetry and context cap run on it ([step 6](#6-collect-telemetry)). What building it cost, in
  Claude runs, tokens and money, is in its [build cost report](https://github.com/eyalgo/ka-telemetry/blob/main/docs/build_cost.md).

## Still changing

KensaiApp changes as it is used. None of what follows has a date, and none of it is in this release.

- Satellites are stood up by a script, with no skill or launcher around it yet.
- The priority was to build it first, and later to add evals and improve its prompts, skills and more.

## From the author

Very early after I started working with Claude, I noticed that although Claude can finish a coding
task, the code it writes is probably not the best. As everyone knows, that comes back to bite us
later.

I started by searching for skills and tools to automate a development process. Inspired by the work
of Addy Osmani on agent-skills, Eric Andrade on claude-superskills and others, it slowly became a
spec-driven, multi-agent development system that can build apps.

<details>
<summary>The name</summary>

Kensai, also written kensei (剣聖), is a Japanese honorary title for a master swordsman of the
highest level. It translates literally as "sword saint". The name came to me on one of those
sleepless nights.

</details>

## Licence

KensaiApp's own work is licensed under MIT, in [LICENSE](LICENSE). Some parts come from other people's
published work, each under its own licence; [NOTICE](NOTICE) lists them.

---

<p align="center">
<a href="about/how-to.md">How-to guide</a> ·
<a href="about/glossary.md">Glossary</a> ·
<a href="about/agentic_description.md">Agentic description</a> ·
<a href="about/how-it-works.md">How it works</a> ·
<a href="about/architecture.md">Architecture overview</a> ·
<a href="about/operations.md">Operations guide</a> ·
<a href="LICENSE">Licence</a> ·
<a href="NOTICE">Notices</a>
</p>
<p align="center"><sub>Made by Eyal</sub></p>
