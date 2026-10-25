# KensaiApp's agentic description

This file maps KensaiApp onto the terms of agentic engineering. Each section names a term, says
what it usually means, with a public source, and then says which part of KensaiApp plays it and
where that part lives in the repository.

KensaiApp started as an experimental private project, which grew into a public one. It was built as
an agentic software development system on Claude Code, and it covers the software development
lifecycle, from requirements to merged code. AI roles carry a product through that lifecycle, under
tests and review. Claude wrote all of KensaiApp's code through KensaiApp's own mechanics. The code of
the products it builds is written entirely by KensaiApp. It is maintained privately, with no promise
of support. Start with the [README](../README.md).

Each term is the nearest match, not an exact one. Where KensaiApp departs from a term's usual
meaning, the section says so. Nothing here compares KensaiApp with another system: it has not been
compared with other solutions, and its output has not been evaluated against another way
of working ([What it does not promise](../README.md#what-it-does-not-promise)). The words KensaiApp
uses for its own parts are in the [glossary](glossary.md).

## How a change moves, in short

Every role named below is an AI agent that KensaiApp runs, not a person. A change starts when the
PM writes a change request. The product owner turns it into a spec, the architect into a design and
the tech lead into a plan. When the design says the change publishes text, the content editor
writes its words. The developer writes the code, each test before the code it checks. The
senior engineer proves the code does what the change intends. An auditor reviews the spec, the
design, the plan, the words and the code, each in a run of its own. The PM seals the change by
merging it into `main`. Each step is a separate run.
[How a change moves](../README.md#how-a-change-moves) has the diagram and the table, and
[One change, from request to patch](../README.md#one-change-from-request-to-patch) walks the files
one sealed change left.

## A workflow, not an agent choosing its path

Anthropic separates two kinds of system. In a *workflow*, "LLMs and tools are orchestrated through
predefined code paths"; in an *agent*, the model directs its own process. One workflow it names is
prompt chaining: each call works on the output of the one before, with programmatic checks, or
gates, between the steps ([Building effective agents](https://www.anthropic.com/research/building-effective-agents)).

KensaiApp's change pipeline is a workflow of that kind. A program, `core/tools/chain_development.py`,
holds the steps in a fixed table, `DEVELOPMENT_STEPS`, and binds each step to one role. It starts a
step only once the run before it has ended and left its result on disk. No model decides what runs
next. Inside a step, the run is an agent: it reads, writes and runs commands on its own, within its
skill.

The program's gates read what the runs left:

- The developer's closing commit must not report a red suite, unless every failing test belongs to a
  task the run deferred. Each task built test-first must have a failing-test commit older than its
  code. Otherwise the walk halts.
- The senior engineer's report must declare `Integrity: pass` and name the environment the tests
  ran in. Otherwise the walk halts.
- The security report must declare `clean`, `fixed` or `reported`. `stopped`, or no such line, halts
  the walk.
- A red closing commit on a product with an NFDR first starts `dependency-repair` once, for a main
  branch an advisory turned red with no commit behind it. The walk halts only when the repair does
  not merge.
- A run that leaves new uncommitted changes in the product's checkout halts the walk at its step,
  and nothing is relaunched over them.

The program runs no tests itself. It reads what the runs recorded, in their commits and reports.

The product's documents are walked by a second program, `core/tools/chain.py`, in a fixed order,
upstream first. Each document goes through the same cycle: its writer runs, an answering run takes
the questions it left open, and the writer runs again.

## A plan written by a model, run by a program

Lilian Weng names planning as one part of an agent: "The agent breaks down large tasks into smaller,
manageable subgoals" ([LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/)).

KensaiApp splits that across two hands. Above the single change, models do the breaking down. The
Principal PM cuts the product's documents into seeds, and the PM cuts a picked seed into stations.
After each sealed change, the PM's refine writes the next moves as a table, with rows such as: close
the station, retire the seed, pick, cut, or the next change
([From requirements to a product](architecture.md#from-requirements-to-a-product)).

A program, `core/tools/build_idea.py`, then runs that table as a queue. Each row's kind maps to one
launcher in the program's own table, and a kind it does not know is refused before anything starts.
The row's command is checked against that table and never executed as written. A row starts only
when the rows it waits on have landed, which the program reads off the disk, not off a launcher's
exit.

## Roles in a multi-agent system

A multi-agent system is "a computational system composed of multiple interacting intelligent
agents" ([Wikipedia](https://en.wikipedia.org/wiki/Multi-agent_system)). In KensaiApp the agents do
not message each other. Each is a separate run, and each reads what earlier runs left on disk
([Hand-off and memory](#hand-off-and-memory)).

The names below are the ones agentic systems are often described by. Each row says what plays it in
KensaiApp.

| Role | What plays it in KensaiApp | Where |
|---|---|---|
| Orchestrator | Programs, not a model: the change pipeline, the documents chain and the queue of next moves | `core/tools/chain_development.py`, `core/tools/chain.py`, `core/tools/build_idea.py` |
| Planner | The tech lead, who reviews the design against the spec and writes the plan the developer builds from | `skills/tech-lead/.claude/skills/development-plan/` |
| Executor | The developer, who builds each task from failing tests and makes the closing commit itself | `skills/developer/.claude/skills/development-implementation/` |
| Verifier | The senior engineer, who proves the finished code does what the change intends | `skills/senior-engineer/.claude/skills/development-code-integrity/` |
| Critic | The auditor, fresh eyes over work it did not produce, which lists defects and never fixes them | `skills/kensaiapp-auditor/.claude/skills/development-audit/` |
| Observer | The completion watchers, which follow a detached run to its end and report how it ended | `core/tools/watch_process.py`, `core/tools/watch_agent.py` |

An agent's definition file holds no behaviour of its own. It tells the run to read its role's
loader, the instance's overlay for that role and the cross-role contract before anything else. A
hook, `read_first_guard.py`, refuses every call that is not a read until the run has read them.

A delegated agent is the one exception: it carries no role, and its brief is the whole assignment
([Delegating work](operations.md#delegating-work)).

## Spec-driven development

Birgitta Böckeler defines spec-driven development as "writing a 'spec' before writing code with
AI", where "the spec becomes the source of truth for the human and the AI". She names three levels:
spec-first, spec-anchored, where the spec is kept after the task "for evolution and maintenance",
and spec-as-source, where the human edits only the spec
([Understanding Spec-Driven-Development](https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)).

KensaiApp writes specs at two levels. For the product, a documents chain writes the PRD, the SRS,
the SDD and the other documents before the first change
([Product documents chains](architecture.md#product-documents-chains)). They are kept, and the chain
runs again before each change, so a later change is built against them. That is closest to what
Böckeler calls spec-anchored. For each change, the product owner writes a spec, and the design and
the plan follow before any code. A project whose card sets `Definition: none` has no product
documents, and each change is built from its own request.

The code is still written and edited by the agents. It is not generated from the specs alone, so
KensaiApp is not spec-as-source in Böckeler's sense.

## Test-driven development

Martin Fowler describes test-driven development as "a technique for building software that guides
software development by writing tests" ([TestDrivenDevelopment](https://martinfowler.com/bliki/TestDrivenDevelopment.html)).

The developer builds each task in a red, green and refactor cycle: a commit for the failing test,
one for the code that makes it pass, and one for the refactor where there is one
(`skills/developer/.claude/skills/development-implementation/SKILL.md`). The change pipeline checks
the shape afterwards: a task in the test-first lane that landed with no failing-test commit before
its code halts the walk. A task the plan does not put in that lane, such as a structural one with no
behaviour to test, lands in one plain commit.

## Review by a separate agent

The auditor reviews the spec, the design, the plan, the content step where it ran, and the
implementation, each in a run of its own. It judges how well each step of the pipeline did its job,
not whether the product is right (`skills/kensaiapp-auditor/.claude/skills/development-audit/SKILL.md`). For a change planned by hand with `ad-hoc-plan`, it reviews
the plan, the content and the implementation, not the short spec and design. The runs are started together, which matches what
Anthropic calls parallelization by sectioning: "Breaking a task into independent subtasks run in
parallel" ([Building effective agents](https://www.anthropic.com/research/building-effective-agents)).

The audit is not a gate, because it checks KensaiApp rather than the product. Its findings are kept
on branches of their own and joined into the change at the seal. The PM reads them first when it
refines the station, with the code-integrity and security reports. A product issue among them goes
back into the plan: the stations that follow can be re-cut, parked or dropped, or work left for the
Principal PM. A finding about a skill is raised to improve that skill
([Where what the checks find goes](how-it-works.md#where-what-the-checks-find-goes)). No step sends a sealed change back to be reworked from its findings. Retry and loop-back
routing are recorded in `core/doctrine/flow/folder_state_handoff.md` as forward design, not as built.
So the audit is not the evaluator-optimizer loop Anthropic describes, where one call generates and
another gives feedback "in a loop".

The senior engineer's proof is the review that does gate the change
([A workflow, not an agent choosing its path](#a-workflow-not-an-agent-choosing-its-path)). Its
security review, between the proof and the audit, fixes what its rules allow and halts the walk
only on a fix it may not make.

## Human in the loop

Anthropic writes that agents "can then pause for human feedback at checkpoints or when encountering
blockers" ([Building effective agents](https://www.anthropic.com/research/building-effective-agents)).

KensaiApp's runs do not stop to ask you a question. A run that cannot settle something writes it as
an open question beside the document it was writing. An answering run, `companion-self-answer`,
then decides each item it is allowed to decide. An item only you may settle stays open, with the
answer it would have given
([How a document's open questions get answered](architecture.md#how-a-documents-open-questions-get-answered)).

A walk does stop, and waits for you, on an act only you can do, such as pushing a branch. The pane
from `/kensaiapp-panel` shows what it needs ([See where things stand](operations.md#see-where-things-stand)),
and a notifier you set up can message you when a chain starts and ends
([Notifications](operations.md#notifications)). Some decisions are yours by rule: ratifying a skill,
and approving a fix packet before a fixer applies it.

Where an AI decision and a mechanical rule conflict, the rule wins, and the AI says so rather than
working around it (`core/doctrine/governance/ai_responsibility.md`).

## Rules held by code

Claude Code's hooks are commands that "execute automatically at specific points in Claude Code's
lifecycle". A hook that runs before a tool call can block it ([Hooks](https://code.claude.com/docs/en/hooks)).

KensaiApp's hooks, its commit check and its launchers are listed in
[Rules the system enforces](architecture.md#rules-the-system-enforces). Two more rules sit in the
launchers:

- A launched Claude run uses Claude Code's auto permission mode. In that mode a classifier model
  reviews each action instead of a person, and in a run with no prompt an action it blocks does not
  run while the run carries on
  ([Choose a permission mode](https://code.claude.com/docs/en/permission-modes)). No launcher starts
  a Claude run with the permission checks skipped.
- A run that leaves new uncommitted changes in the product's checkout stops the walk, or fails its
  row in the queue of next moves.

## Choosing a model for the work

Anthropic's routing pattern "classifies an input and directs it to a specialized followup task",
for example easy questions to a smaller model
([Building effective agents](https://www.anthropic.com/research/building-effective-agents)).

KensaiApp does not route at run time. The choice is declared ahead of time, by the work. Each skill
names the model and the effort it runs at, in one file per provider, and a role's agent carries no
model ([Each skill runs at its own model and effort](operations.md#each-skill-runs-at-its-own-model-and-effort)).
A run with no skill behind it, such as a delegated agent, takes one of four tiers, chosen by where
the judgment in the work lives (`core/doctrine/governance/model_assignment.md`). Which provider each
step runs on is set in one file per instance ([Choosing a provider](operations.md#choosing-a-provider)).

## Context engineering

Anthropic defines context engineering as "the set of strategies for curating and maintaining the
optimal set of tokens (information) during LLM inference"
([Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)).

In KensaiApp, hooks set the start of every session and every subagent, because a subagent inherits
no context from its parent. They inject the path of the shared core, an index of which rule governs
which task, and an index of where each kind of file lives. They also inject the rules that bind
without being looked up, and the rules for replying to you
([How a session talks to you](operations.md#how-a-session-talks-to-you)).
Each index is read from its source file when the hook runs, so it cannot drift from it.

The developer's run, which can be long, is given a context cap. Past it, a hook tells the run to finish the task it is on, commit, and stop. The program then
starts a fresh developer run from the next task. What carries over is on disk: the plan and the
commits.

One rule keeps the written context small: a fact has one owner, and every other file points at it
rather than repeating it (`core/doctrine/governance/single_source.md`).

## Progressive disclosure

Anthropic calls progressive disclosure "the core design principle" of Agent Skills. A skill's name
and description are loaded at start, its full instructions when it is relevant, and its other files
only as needed ([Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)).

KensaiApp applies the same idea at three levels. A session sees only the skill groups you give it
([Loading skills and agents](operations.md#loading-skills-and-agents)). Each instance's `AGENTS.md`
loads in every session and carries short stubs of the rules; the full rule files are read when a
task calls for them (`core/doctrine/README.md`). Inside a skill, the three loading levels above are
the ones its own guide to writing skills sets out (`skills/interactive/.claude/skills/skill-creator/SKILL.md`).

## Hand-off and memory

In a blackboard system, specialists each update a shared store "with a partial solution", and a
control component decides the order in which they contribute
([Wikipedia](https://en.wikipedia.org/wiki/Blackboard_system)).

KensaiApp's hand-off is a blackboard by its own description: all the work for one change lives in
one folder, and roles never route to one another (`core/doctrine/flow/folder_state_handoff.md`).
So the programs in the orchestrator's row play the control component's part. A detached run returns nothing to
the program that started it, so the only record of a step is what it left: the files in the
change's folder, the developer's closing commit, each auditor's branch and the sealed folder.

Weng describes an agent's long-term memory as the ability "to retain and recall (infinite)
information over extended periods", usually through an external vector store
([LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/)). KensaiApp
has no vector store. What it remembers between runs is files in git: the product's documents, the
project's journey, and the trail of every sealed change. The rules for how a session conducts itself
are kept apart, per instance and outside every repository, one file per rule with an index
(`core/doctrine/governance/corrections_store.md`).

## Retrieval

Retrieval-augmented generation combines a model's "parametric and non-parametric memory for
language generation": the model is given passages retrieved from an external index
([Lewis et al., 2020](https://arxiv.org/abs/2005.11401)).

KensaiApp has no embedding or vector-store retrieval in its `core`, `.claude` and `skills` folders.
That rests on a search of those folders, `git grep -i -E 'embedding|vector store|faiss|chroma|pinecone|retrieval-augmented|pgvector' HEAD -- core .claude skills`.
Its one match is a test where "embedding" means a script carried inside a launcher. A run finds what
it needs by path instead: the indexes the hooks inject point at the files, and the run opens them.

## Durable execution

Temporal defines durable execution as the ability of a workflow execution "to maintain its state
and progress even in the face of failures, crashes, or server outages"
([What is Temporal?](https://docs.temporal.io/temporal)).

KensaiApp's walks survive a stop in a simpler way:

- Each walk keeps its state in one file under `system/logs/`, and each run's end is read off the
  disk, not off a message.
- Advancing a walk is idempotent: the same end delivered twice moves it once (`core/tools/chain.py`,
  `core/tools/chain_development.py`).
- Running the same launcher again carries on from what is on disk, rather than starting over.
- A developer run that stops on its context cap is relaunched from the next task. One that ends with
  no closing commit gets one more run from the first unfinished task. One reported as failed is
  resumed once from its newest task commit. A second failure halts the walk.
- Each launch runs on a pinned copy of the shared core, so an edit made after the launch cannot
  reach a walk in flight.

Unlike Temporal, KensaiApp keeps no event history to replay. A resumed walk works out where it is
from its state file and from what is on disk.

## Evals and self-improvement

This part is experimental, as the architecture overview says.

Anthropic defines an eval as "a test for an AI system": "give an AI an input, then apply grading
logic to its output to measure success". Its graders can be code, a model or a person
([Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)).

KensaiApp's eval workflow, `.claude/workflows/run-skill-evals.js`, runs each case in a skill's
`evals.json` twice, once with the skill and once with no skill guidance, and model graders grade
each run. Kaizen, the Japanese word for improvement that management theory uses for continuous
improvement ([Wikipedia](https://en.wikipedia.org/wiki/Kaizen)), is KensaiApp's name for its loop:
exercise a skill on a real case, audit what it produced, improve the skill, and run it again. You run
it round by round. It is not an automated workflow (`core/doctrine/kaizen/skills.md`).

Deciding a fix and applying it are kept in separate hands. A fix-author decides the fix and writes
its exact text; a fixer applies it. In a kaizen round, the fixer acts only on a fix packet you have
marked approved (`core/doctrine/kaizen/fix_packet.md`). The eval-fix pass,
`.claude/workflows/eval-fix.js`, runs unattended, so it hands the decision to the fixer directly. It
stops for you on a rebuild verdict, or on a call the fix-author will not settle.

## Observability and provenance

Claude Code can export its usage through OpenTelemetry: metrics such as tokens and cost, and events
such as each API request ([Monitoring](https://code.claude.com/docs/en/monitoring-usage)).

KensaiApp receives that export through ka-telemetry, an open-source package it built, and sends a
run's telemetry only to a loopback address ([Telemetry](operations.md#telemetry)). A launcher can tag each run with its provider, model and effort.
`core/tools/run_provenance.py` reads those back by run ID, from "what landed, not what the launcher
meant to send". A run whose records carry no provider, or two values for one field, gets a refusal
rather than a guess.

## Isolation

A git worktree is one of "multiple working trees attached to the same repository"
([git-worktree](https://git-scm.com/docs/git-worktree)).

Each change gets its own branch and worktree, made by `core/tools/create_change_worktree.py`, which
checks every repository it will touch before it changes any of them. A product's tests run where its
CI runs: a Podman container, one for each version of a matrix, a macOS virtual machine, or your own
Mac when the product has no CI or you ask for it ([Testing in isolation](operations.md#testing-in-isolation)).

The agents themselves run on your machine, not in a container. The shared core holds a contract for
running autonomous sessions in a Docker sandbox, which binds a run that skips permission checks
(`core/doctrine/sandbox.md`). No launcher starts a Claude run that skips them.

## Shared core across instances

A satellite is an instance with no core of its own, which reads its host's
([One mechanism, several instances](architecture.md#one-mechanism-several-instances)). It runs the
host's hooks and reads the host's skills, so an edit in the host is seen at once. The one copy it keeps is its hook settings file, written from the host's and brought
level again by `core/tools/link_satellite.py`. A finding about the host's core is written in the
satellite's own `docs/findings/`, and nothing carries it to the host automatically
([Findings](operations.md#findings)).
