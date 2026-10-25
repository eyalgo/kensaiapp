# How to

This guide is the step-by-step reference behind the [README](../README.md). The README says what
KensaiApp is and how to start; the [architecture overview](architecture.md) says how it is organised. Each entry here says what to do at one step, and
where KensaiApp's own files say more.

Every command runs from the instance root. A skill lives under `skills/<group>/` of the host, the
instance whose core yours reads; an instance that carries its own core is its own host. In a
satellite, read every `core/` path in this file as `$CORE`, as the operations guide's section
[More than one instance](operations.md#more-than-one-instance) shows.

## How to install what KensaiApp uses

The README's [step 1](../README.md#1-install-what-kensaiapp-uses) lists what every clone needs.
KensaiApp's own code uses only Python's standard library, so nothing is installed with `pip` to run
it. Its tests and its telemetry need more, below.

The hooks, the launchers and the pane each run `python3`, and it must be 3.13 or later. On a Mac
with 3.11 or 3.12, stopping a walk fails. On anything older, the launchers stop with
`No module named 'tomllib'`, and one of a session's checks fails on every edit. On a Mac, the `python3` that Apple's command-line tools install is 3.9. Install a newer
Python and put it first on your `PATH`.

KensaiApp's own tests, and a walk's closing gate on a product with Python tests, run under pytest
with its pytest-xdist plugin: `core/pytest.ini` runs the tests in parallel with `-n 32`, and without
the plugin pytest stops before running a test. Install both for the same `python3` the hooks run
(a Homebrew Python also needs `--break-system-packages`):

```bash
python3 -m pip install pytest pytest-xdist
```

They belong to that one Python. After you upgrade Python, both of these must succeed again, or every
closing gate stops as a red suite with no test failing:

```bash
python3 -m pytest --version
python3 -c "import xdist"
```

The context cap and the telemetry need [ka-telemetry](https://github.com/eyalgo/ka-telemetry), an
open-source package KensaiApp built. KensaiApp looks for it in one place, its own environment in your
home folder; [How to collect telemetry](#how-to-collect-telemetry) installs it there. Without it,
KensaiApp runs, a capped run says in one line that nothing is capped, and the launchers start their
runs with no telemetry.

A clone needs no `.env`: the first session finds the `core/` folder beside it. A `.env` is for a
satellite, as the operations guide's section [More than one instance](operations.md#more-than-one-instance)
shows.

Some parts need more:

| To use | You need |
|---|---|
| Tests in a container, for a product whose CI runs on Linux | Podman. On a Mac, its machine must be running: `podman machine start` |
| Tests in a macOS guest, for a product whose CI runs on macOS or that holds Swift | Tart, and the guest the section "macOS guest provisioning" of `core/doctrine/engineering/languages/swift/environment.md` sets up |
| The `codex` provider | The `codex` command |
| The `gemini` provider | The `agy` command |
| The `ollama` provider | An Ollama server, at `http://localhost:11434` or at the address in `KENSAIAPP_OLLAMA_URL` |
| The `hf` provider | A line `HF_TOKEN=<your token>` in `~/.env`, in your home folder |

Where tests run is in the operations guide's section [Testing in isolation](operations.md#testing-in-isolation).

## How to ask a role for help

Start your message with a role's prefix, as the operations guide's section
[Asking a specific role](operations.md#asking-a-specific-role) says. Every prefix your instance
accepts is listed in the section [Loader map](../AGENTS.md#loader-map) of its `AGENTS.md`.

## How to give a session a group of skills

The operations guide's section [Loading skills and agents](operations.md#loading-skills-and-agents) shows both
ways. A run that `core/launchers/skill/launcher.sh` starts is given its skill's group by the
launcher, so you add a group only in a session you work in yourself.

## How to set up a project

The first two steps, `/add-dir skills/interactive-product` and `/project-setup`, are the README's
[step 4](../README.md#4-set-up-your-first-project). What follows them:

1. `/project-setup` asks for the project's name, then four things about it: what you are building,
   where it should live, whether it looks after something outside itself, such as a public
   repository or a domain, and whether you have anything to start from. Then it asks about the
   product, shows you what it will write, and writes it once you confirm. It then starts
   `chain-agari`, which writes the PRD and then the Agari, and answers its own questions as it goes.
2. The chain ends with a message. If it says something is left for you, answer it as the entry
   "How to answer what a run left open" says, then run `core/launchers/chain-agari/launcher.sh
   <project>` again. If it says the writing stopped before it finished, run that launcher again on
   its own. It carries on from where it stopped.
3. Once the Agari is settled, start the product's list of what is left to build:
   `core/launchers/skill/launcher.sh first-what-left <project>`. No chain runs this step. You run
   it yourself, once.

After step 3, a revised PRD adds what it newly wants to that list (`product-prd`). After each
station closes, `readme-status` removes what has merged and rewrites the Status section of the
product's README from what is left.

A project's card carries two lines that do not depend on each other:

- `Type:` says what the product is: `software`, an app or tool with code, or `no-code`, such as a
  profile or a body of writing.
- `Definition:` says how much is written down before the code. Its three values are in the README's
  section [Types of projects](../README.md#types-of-projects).

`/project-setup` asks the type and sets the definition from it. A project with `Definition: none`
can still be software with code. To choose another definition, change the line on the card.

The full steps are in `core/doctrine/setup/setting_up_a_project.md`.

## How to stop a walk, and start it again

The launchers that walk a project are in the architecture overview's section
[The chain launchers](architecture.md#the-chain-launchers). `chain-product`, `chain-agari`, `chain-change`,
`build-idea` and `chain-development` each take `--stop` in place of their other options, and the two
you use most stop in different ways:

- `chain-change --stop` stops every run in flight, in the middle of its step, ends the walk and
  keeps its state. It does not stop a documents chain the change is still waiting on. That chain's
  own launcher, `chain-product` or `chain-agari`, stops it with its own `--stop`.
- `build-idea --stop` stops the queue's own runs at once. A change it already handed to
  `chain-change` walks on to its end, and the loop then does not start again. The stop holds until
  you start `build-idea` again.

Running the same launcher again with no flag carries on from what is on disk. A step that was
stopped starts over.

## How to walk a project's journey

Running one of the loop's launchers again is usually enough. The moves the journey is made of, and
who makes each one, are in the architecture overview's section
[From requirements to a product](architecture.md#from-requirements-to-a-product), and their names in
[The Japanese names](architecture.md#the-japanese-names). How far each industry term matches is in
the glossary's section
[The journey in industry, ticketing and Jira terms](glossary.md#the-journey-in-industry-ticketing-and-jira-terms).
The full steps are in the section "How we work" of `core/docs/michi_agari.md`.

## How to run one skill on its own

`core/launchers/skill/launcher.sh <skill> [<argument>...]` starts any skill that has a `launcher.md`
file beside its `SKILL.md`, as a run in the background. That file names the role the skill runs as
and the arguments it takes. `--dry-run` prints what the launch would run and starts nothing.

Some next moves are one skill rather than a chain. Three examples:

```bash
core/launchers/skill/launcher.sh first-what-left <project>
core/launchers/skill/launcher.sh seeds-from-product-docs <project>
core/launchers/skill/launcher.sh shukuba-refine <project>
```

## How to hand work to an agent

The operations guide's section [Delegating work](operations.md#delegating-work) shows how to start one and how
the model is picked. The agent writes its report of the run, `delegate-report.md`, where its brief
says. The skill is not for work a launcher already does, such as building a change, or for work
small enough to do in the session itself.

The steps are in `skills/interactive/.claude/skills/agent-invoke/SKILL.md`. The rule for choosing the
model is in the section "Runs with no standing slot" of
`core/doctrine/governance/model_assignment.md`, and what every agent run owes is in
`core/roles/delegate_contract.md`.

## How to see where things stand

The pane and the journey page are in the operations guide's section
[See where things stand](operations.md#see-where-things-stand). Typing `/kensaiapp-panel` again reads
the chains afresh. `python3 core/tools/journey_status.py --repo .` writes its page to
`system/logs/journey_status.html` unless `--out` names another path.

## How to collect telemetry

The telemetry is what each run costs in tokens and money, and each request it makes to the model.
It runs on [ka-telemetry](https://github.com/eyalgo/ka-telemetry), an open-source package KensaiApp
built. Install it once, into KensaiApp's own environment in your home folder, which is where the
launchers look for it:

```bash
python3 -m venv ~/.kensaiapp/venv
~/.kensaiapp/venv/bin/pip install ka-telemetry
```

Start the receiver in its own terminal and leave it running. It writes what it receives to the folder
after `--dir`:

```bash
mkdir -p ~/.claude/tools/otel-receiver
~/.kensaiapp/venv/bin/ka-telemetry receive --port 4318 --dir ~/.kensaiapp/telemetry \
  --publish-endpoint ~/.claude/tools/otel-receiver/endpoint
```

Every chain a launcher starts then sends its telemetry there. For your own Claude Code sessions to
send theirs too, run this once, while the receiver is running:

```bash
~/.kensaiapp/venv/bin/ka-telemetry turn-on --settings-file ~/.claude/settings.json
```

It writes the telemetry settings into your Claude Code settings, so it holds for every session on the
machine, not only in KensaiApp. The same command with `--remove` takes them out. The receiver stops
when its terminal closes; start it the same way again. The operations guide's section
[Telemetry](operations.md#telemetry) says what is collected. The same install also gives the
developer's [context cap](glossary.md#context-cap) what it reads; without the package, nothing is
capped.

## How to tell why a run stopped, and what to do

The operations guide's section [When a run stops, it says why](operations.md#when-a-run-stops-it-says-why)
gives the rule: settle the cause, then run the same launcher again. A chain that writes a project's
documents also says what to do next. Each kind of stop is below.

### It asks you a question

The run reached a call only you can make, usually about what the product should be or do.

- A document's open item is left for you (`left_for_the_owner`). The chain records it and does not
  stop for it. Answer it when you can, as the entry "How to answer what a run left open" says.
- A change stopped with a `halt_report.md`. The message gives its path, in the change's folder
  under `journey/tobiishi/`. The report sets out what conflicts and numbers the decisions that would
  settle it. Make the decision in the document it belongs to, then run `chain-change` again.
- If the change should not be made after all, run `core/launchers/skill/launcher.sh shukuba-refine
  <project>`. The PM reviews the stopped change and decides whether to drop it.
- The security step stopped (`security-stopped`). Its `security-report.md`, in the change's folder,
  says under *Why the run stopped* which fix it needs, which record forbids it and what it would do if
  allowed. Make the call in that record, then run `chain-change` again.
- `build-idea` stopped at a row for the owner's act. That row names a station only you walk, or a
  question for you. Do what it asks, then run `core/launchers/build-idea/launcher.sh <project>`
  again.

### It stopped because the same thing kept changing

KensaiApp counts how often some things change, so that a run cannot go round for ever. When a count
runs out, the run stops and leaves the call to you.

- A station's bar, what its reached-when requires, was changed twice by the route's refines since
  you were last asked. `build-idea` stops at a row asking whether the station is done. If it is not,
  run `build-idea` again: going past that row is your answer, "not done, walk on". If it is done,
  add the group with `/add-dir skills/scrum-master`, close the station with the Scrum Master,
  `scrum-master: run shukuba-retire for my-app`, then run `build-idea` again. If the bar itself needs settling, settle it in a session with Claude in your
  instance.
- A document's round of answers left its open items unchanged (`could_not_be_settled`), or three
  rounds ended without settling it (`cap`). Read the document's trail. The fault is usually in the
  skill that writes the document, so write it down as a finding, as the entry "How to check whether
  something can be improved" says.
- A developer run paused at its context limit without getting past the task it paused on before.
  The task is too large for that limit. Run `chain-change` again with a larger
  `--context-cap <tokens>`. The default is 250000.

### It stopped because the provider did

A usage limit, an overloaded service, or a model that did not call its tools. The message names a
failed run or a missing file, and the run's log under `system/logs/` shows the provider's error. The
chain resumes a failed developer run once on its own before it stops. Wait for the limit to reset,
or choose another provider as the entry "How to choose the provider" says, then run the launcher
again.

### It stopped because the product was not ready

The product's own state stopped the change, not the change itself. Examples are tests that already
failed before the change began (`red-suite`), a product checkout missing what its tests need, a
small defect already on the main branch, or files a run left behind in the product checkout. Fix it
on the product's main branch, or fix the project's test command, then run the launcher again.

A main branch can also turn red with no commit behind it, when the product's dependency audit reads
an advisory published after the last green run. For a product with an NFDR, the chain then first
starts `dependency-repair` once, before it stops. It repairs the advisories on a branch off main, by
the security step's rules, and merges once the suite is green; the walk then carries on from main.
It stops as `red-suite` only when the repair did not merge. You can also start it yourself:
`core/launchers/skill/launcher.sh dependency-repair <project>`.

When a gate environment cannot install the product's languages or dependencies, the walk stops as
`environment-not-ready`, before any test runs. Fix the install the product's CI describes, then run
the launcher again.

One stop comes before the implementation starts: `environment-decision-owed`. The product's tests
have no place to run that KensaiApp can work out, so the product owes a decision on where its gates
run. Record it in the product's decision files (its `docs/nfdr.md`, § 8) on the product's main
branch and start the walk again, or start it again with `--gate-owners-mac` to run the gates on your
own Mac.

### It stopped because KensaiApp broke

The reason names KensaiApp's own parts rather than your product. Examples are `machinery`, a run
that produced nothing, a report not in its expected shape, a launcher that refuses a row of its own
table, or a finished change with a green suite stopped on its commit record. Read the run's log
under `system/logs/`, and write the problem down as a finding. Where the work is already done, the
next step can often be run on its own, as the entry "How to run one skill on its own" says.

### You stopped it, or it would not start

A stopped walk starts again as the entry "How to stop a walk, and start it again" says. A launcher
that refuses to start says why, such as a walk still running on the project, a project card with no
`Definition:` line, or a provider with no entry in `.providers.toml`. Fix what it names, or stop the
walk that is running, then start it again.

How the chains end is in the opening comments of `core/tools/chain.py`, under "THE SEVEN ENDS", and
of `core/tools/chain_development.py`. The stops a change can meet are in the section "The chain's
on-disk transport" of `core/doctrine/flow/step_outcome_contract.md`.

## How to choose the provider

The file and the flag are in the operations guide's section
[Choosing a provider](operations.md#choosing-a-provider). Three things it leaves out:

- An exported `KENSAIAPP_AGENT_PROVIDER` forces one provider the same way `--provider` does, and the
  flag wins over it.
- An unforced launch with no `.providers.toml` at the instance root, or with no entry for what it
  launches, is refused, naming what is missing. Nothing falls back to a default.
- These launchers run on Claude only: `cold-read`, `launch-eval-fix`, `launch-skill-evals`,
  `product-card`, and the kaizen scripts `launch-apply-packet`, `launch-audit` and
  `launch-fix-author`.

The rules for each entry are in the opening comments of `.providers.toml.example`.

## How to set a skill's intelligence

What a skill's intelligence is, and the file it is set in, are in the operations guide's section
[Each skill runs at its own model and effort](operations.md#each-skill-runs-at-its-own-model-and-effort).
A skill that has an `intelligence/` folder but no file in it for the provider you launch on is
refused, naming the missing file. The rules are in
`core/doctrine/governance/skill_intelligence.md`.

## Advanced

### How to create an instance

The operations guide's section [More than one instance](operations.md#more-than-one-instance) shows the script
that stands one up. The steps after it, in order:

1. `core/tools/spawn_satellite.py` stands the satellite up. It also files a setup seed in the new
   instance's seedbed, carrying the steps below as its checklist.
2. `kensaiapp-michi` settles what the instance is, then declares its Michi and reconciles the
   README to match. It is in the `skills/interactive-product` group.
3. `experience-visual` writes the instance's visual layer.
4. `experience-voice` writes the instance's verbal layer.

Other steps come between `kensaiapp-michi` and `experience-visual`: the instance's doctrine, each
role's domain and the writing bar. The full steps, in order, are in the section "Standing one up" of
`core/doctrine/setup/shared_core_instance.md` and the section "The steps, in order" of
`core/doctrine/setup/setting_up_an_instance.md`.

### How to answer what a run left open

How a chain answers a document's questions itself, and what it leaves for you, is in the architecture overview's
section [How a document's open questions get answered](architecture.md#how-a-documents-open-questions-get-answered).
What is left sits in a file beside the document, named like `PRD_open_issues.md`. To answer it:

1. Add the group: `/add-dir skills/interactive`.
2. Type `/companion-answer`. It walks you through the open items one at a time, writes each answer
   into the file, commits it, and names the launchers to run again. It does not run them.

`/companion-answer` is for these files only. A run that stops in any other way is answered as the
entry "How to tell why a run stopped, and what to do" says.

### How to set the instance's experience

The two skills, and how to start each, are in the architecture overview's section
[The instance's experience](architecture.md#the-instances-experience). What they write is two pairs of
files in `system/experience/`: `visual_restrictions.md` and `visual_direction.md`, then
`voice_restrictions.md` and `voice_direction.md`. The visual half runs first, because the verbal
half reads what the visual half marked in `visual_voice_contract.md`. `experience-visual` needs
`npx` and `node`, for the check it runs on `visual_direction.md`.

What a run cannot settle goes into a file beside the document it concerns, named like
`visual_direction_open_issues.md`. Answer it in place, or with `/companion-answer`, commit your
answers, and run the skill again. A document is done when no such file is left beside it.

To revise the layer later, run the same two skills again, in the same order. Each one reads what is
there, your earlier answers included, and changes only what needs changing.

What each skill writes, and its loop, are in the section "The files and the loop" of
`skills/cdo/.claude/skills/experience-visual/SKILL.md` and of
`skills/content-manager/.claude/skills/experience-voice/SKILL.md`. Why the visual half runs first is
in the section "The three rules" of `core/doctrine/setup/setting_up_an_instance.md`.

### How to get a message when a run finishes

What `KENSAIAPP_NOTIFIER` is and what sends a message are in the operations guide's section
[Notifications](operations.md#notifications). Set the variable in your shell's profile, so the
launchers you start and the Claude Code sessions you open from that shell both see it. A session
started outside a shell, such as one in the desktop app, has not been tested and may not see it.
Setting up the notifier is done by hand for now.

To have the messages arrive in Telegram:

1. In Telegram, send `/newbot` to @BotFather and answer its questions. It gives you the bot's
   token. Anyone who holds the token controls the bot, so keep it out of every repository.
2. Start a chat with the bot, or add it to the group or channel the messages should go to. Send a
   message there, then call the Bot API's `getUpdates` method. Each message in its reply carries the
   chat it belongs to, and that chat's `id`.
3. Write a short script that posts its first argument to
   `https://api.telegram.org/bot<token>/sendMessage`, with the chat's `id` as `chat_id` and the
   argument as `text`. Have it read the token from your system's keychain or the environment, never
   from the script itself, and exit non-zero when Telegram rejects the message. Telegram takes at
   most 4096 characters of text.
4. Make the script executable, and set `KENSAIAPP_NOTIFIER` to its full path.

One setup that works, the author's: the messages go to a private Telegram channel. The script reads the token from the macOS Keychain on every send, so no file holds it. It is
stored once with `security add-generic-password -a "$USER" -s <service> -w '<token>'` and read with
`security find-generic-password -s <service> -w`. The script posts with `curl --data-urlencode`,
because a message can carry newlines, `&` and `=`.

Where the notifier is read, and which agent runs are announced, are in the sections "Native
`.claude/` layer" and "Shared-tools layer" of `core/doctrine/setup/kensaiapp_structure.md`.
Telegram's own steps are at https://core.telegram.org/bots/features and
https://core.telegram.org/bots/api.

### How to check whether something can be improved

What a finding is, and where it is written, are in the operations guide's section
[Findings](operations.md#findings). After a seed is retired, ask Claude in your instance what was
written to `docs/findings/` while it was walked. Each finding names the part of KensaiApp it
concerns.

Where findings are kept is in the section on `docs/findings/` of
`core/doctrine/setup/kensaiapp_structure.md`.
