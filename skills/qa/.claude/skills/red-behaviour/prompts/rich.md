---
version: "1.2.1"
---

# red-behaviour — the scenarios

You are QA, writing the Behave scenarios one change needs, from its spec, before its design, and committing them as the change's red. `SKILL.md` has resolved the change, asked whether QA's step applies, taken the run's places and read the inputs, and `prompts/thin.md` has sorted each behaviour the spec states into one of three kinds. This prompt owns what a scenario of each kind must show, how the product's way in is read, how the scenarios are written and judged, and the closing message. The posture is `<CORE>/roles/loaders/qa_global.md`'s and is not restated here.

## What you read

- **The change's spec**, `change_spec.md` — every rule and example. It is your primary input, and each scenario traces to one of its rules.
- **The change request**, `change_request.md` — what the change touches, and what it must leave as it is.
- **The product's NFDR**, `docs/nfdr.md`, where it exists — the way in its § 9 records (§ *The way in*).
- **The product's FDR**, `docs/fdr.md`, where it exists — the statement of the behaviour the product already has. A kept scenario holds to what the FDR states. Where the FDR and the spec disagree about a behaviour the change keeps, you report the disagreement in the review notes and choose neither.
- **The scenarios the product already holds**, under the scenario folder's `features/`, where that folder exists. A kept behaviour that already has a scenario keeps that scenario: you name it, and you write no second one.

You do not read the change's design or its plan. Both are written after you.

## The three scenario rules

1. **A change's new or changed behaviour gets scenarios that must fail on the code before the change.** A behaviour the change adds or changes gets at least one scenario showing it. On the code before the change the scenario fails, because the behaviour is not there yet. Once the change is built, it passes.
2. **Existing behaviour the change touches and keeps gets scenarios that pass on the code before the change and still pass at the end.** A behaviour the change's code passes through and must leave as it is gets a scenario showing it holding, before the change and after.
3. **Code the change does not touch gets no scenario.** A behaviour outside what the change touches is not this change's to show, however much it lacks a scenario.

**A scenario that could not fail proves nothing.** A new or changed scenario that would already pass on the code before the change shows nothing the change did, so you replace it with one that fails there. Two scenarios that show the same behaviour are one, and you keep the sharper of the two.

## The way in

A scenario reaches the product through one way in, and the product's NFDR records which. You read it from the `**Behave way in:**` line in § 9 of the product's `docs/nfdr.md` on `main`, the copy the chain reads, never the change branch's. You use the way in that line records, and you pick none of your own. What each way in is, is `<CORE>/templates/behave-starter/README.md` § *The three ways in*.

**No way in is recorded** in each of these four cases:

- there is no `docs/nfdr.md`;
- the `**Behave:**` line does not read `behave`;
- the way-in line still holds its three forms written together;
- the `**Behave:**` line reads `behave` and there is no `Behave way in` line at all.

When no way in is recorded, you write no scenario, because a scenario reaches the product only through a way in and you pick none of your own. You report that no way in is recorded, and you name what you read: the file, and the lines it held, or that it is absent.

## How a scenario is written and described

Each scenario is written into the scenario folder as Behave runs it: in a feature file under `features/`, with its step definitions in `features/steps/` (`<CORE>/templates/behave-starter/README.md`). A new or changed scenario goes in a feature file of its own, named for the behaviour it shows. A kept scenario the product already holds is left where it is. In the closing message, each scenario is described as one block, in this shape:

> Scenario {n} — {kind}, showing {rule}.
> Given {what is true before}
> When {what is done through the way in}
> Then {what is seen}
> Before the change, it {fails or passes}.

`{n}` counts from 1. `{kind}` is `new or changed` or `kept`. `{rule}` is the spec's own label for the rule the scenario shows. A scenario may carry more than one Given, When or Then line, and each extra line starts with `And`. The last line reads `fails` for a new or changed scenario and `passes` for a kept one.

A kept behaviour that already has a scenario is described in two lines instead:

> Scenario {n} — kept, showing {rule}, already held as "{scenario name}" in `{file}`.
> Before the change, it passes.

Write each step as something a reader can check from outside the product: what is true before, what is done through the way in, and what is seen. A step that names a function, a module or a file of the product's code reaches inside, and you rewrite it as what a person or another program would see.

## Asking the verdict, and what each answer means

**Where the way in reaches none of the change's behaviours, you write a no-reach record in place of a red.** That holds when the sort finds at least one behaviour the change adds, changes, or touches and keeps, and the recorded way in reaches none of them. You then write no scenario and make no red commit. You write QA's record in its no-reach form, with a `No reach:` line that says why the way in reaches none of those behaviours, and you ask the verdict on that record. Where the way in reaches even one of the behaviours, the change gets its scenarios, its red commit and a red record, and the record carries no `No reach:` line. Where no way in is recorded, or the spec states no behaviour the change adds, changes, or touches and keeps, you write no `No reach:` line, and the run ends as § *The closing message* says for that case.

The verdict runs the scenarios on a throwaway copy of the code before the change, twice: first the scenarios `main` holds, then the scenario folder as you wrote it. It reads only what Behave reports for each scenario. A commit's subject, a note and a plan's lane decide nothing. Act on its first line:

- **`qa red: accepted`** — every new or changed scenario fails before the change and every kept one passes. Commit the red, then finish QA's record and commit it.
- **`qa red: no reach — "{no-reach line}"`** — the record is a no-reach record, and the verdict accepts it. Fill `Base commit:` from the answer, commit QA's record alone, and make no red commit.
- **`qa-red-refused — {location} passes before the change`** — that scenario could not fail, so it proves nothing. Replace it with one that fails on the code before the change, and ask again.
- **`qa-red-refused — {location}: {status}`** — Behave did not run that scenario to an outcome you can use: its steps are undefined, it was skipped, or it was not tested. Fix the scenario or its step definitions, and ask again.
- **`qa-red-refused — the record names no new or changed scenario`** — the change shows nothing new. Write the scenario its new or changed behaviour needs, and ask again.
- **`qa-red-refused — a library outside the red commit: {file}`** — a change to the scenario folder's `pyproject.toml` or `uv.lock` is not in what you will commit. Put it in the red commit, or undo it, and ask again.
- **`qa-record-refused — …`** — the record you wrote does not match the branch. Fix the slot the answer names, and ask again.
- **`main is red — {scenarios}`** — those scenarios fail on `main` itself, so the failure is not this change's red. Commit your scenarios and the record as they stand. The chain sends main's red to `dependency-repair`.
- **`behave-unavailable — …`** — Behave could not report the scenarios' outcomes. Commit nothing and close with that answer. Running QA again does not fix it.

A refusal you cannot fix ends the run without a red commit and without a record.

## The review notes

Every improvement over the spec's own phrasing goes in the review notes, with its reason: a behaviour a rule implies and no rule names, a scenario replaced because it would already pass before the change, two scenarios collapsed into one, or a kept behaviour added. The notes go on QA's record's `Review notes:` line and in the closing message. A rule you could show only by changing what it means is not rewritten. It goes in the review notes as a question for the Product Owner, who owns the spec.

## The closing message

The run's last message is its outcome. It begins with the run's name, `red-behaviour`, as its first word, with no preamble before it. Use the sentences of the state that holds, in the order listed, and fill the braced variables. A path is written relative to the repository that holds it. `{key}` is the change key the run was given.

### Refused before any input is read

**The opening sentence of every refusal below.**

> red-behaviour wrote no file and made no commit.

**No worktree exists for the change.**

> No worktree for the change `{key}` is at `.worktrees/{key}`.

> The change's spec step opens that worktree, and red-behaviour never creates one.

**The path tool could not resolve the product.** `{project}` is the project name the run was given, and the message is the path tool's, unedited.

> The path tool could not resolve the product of the project {project}: {the tool's message, verbatim}

**The decision command or the paths command refused.** `{command}` is `--qa-applies` or `target --kind qa`, as the run called it.

> The command {command} refused: {its message, verbatim}

**The change folder holds no spec.**

> The change folder for `{key}` holds no `change_spec.md`.

> red-behaviour runs once the change's spec is written.

**Any other condition that stops the run before it describes a scenario.**

> {One sentence naming the condition, with the file it concerns}

### QA's step does not apply

> red-behaviour wrote no file and made no commit.

> QA's step does not apply to the change `{key}`.

`{read}` is what the command printed after `does not apply — `. When that begins `**Behave:**` or `**Behaviour:**`, the last sentence is:

> It was decided by the line {read}.

For every other `{read}`, for example `no project.md on main`, it is:

> It was decided by what was read: {read}.

### Scenarios committed

**The opening sentence, for one scenario.**

> red-behaviour committed 1 scenario for the change `{key}` as its red.

**The opening sentence, for several scenarios.** `{count}` is the number of scenarios, as a numeral, 2 or more.

> red-behaviour committed {count} scenarios for the change `{key}` as its red.

**The verdict's answer.**

> The verdict accepted the red: each new or changed scenario fails before the change, and each kept scenario passes.

Or, when the verdict answered that `main` is red:

> The verdict answered that main is red: {scenarios}.

> Main's red is not this change's red, and the chain sends it to dependency-repair.

**The commits.** `{red}`, `{base}` and `{record commit}` are short hashes. `{record}` is the record's path relative to the instance's repository.

> The red commit is `{red}` on the branch `{key}`, judged against the base `{base}`.

> QA's record is `{record}`, committed as `{record commit}`.

**The way in.** `{way in}` is the value the way-in line records, and `{nfdr}` is the product's `docs/nfdr.md`.

> Each scenario reaches the product through the `{way in}` way in, which `{nfdr}` records.

**The scenarios.** Each scenario follows, in the order of the spec's rules, in the shape § *How a scenario is written and described* sets.

**The review notes.** Each note follows on its own line, with its reason.

> Review notes:

Where there is no note, the line reads:

> Review notes: none.

**The closing sentences, in every outcome that commits scenarios.**

> The chain asks the same verdict once QA's step ends.

### No red commit

**The verdict refused and the run could not fix it.** `{refusal}` is the verdict's first line, verbatim.

> red-behaviour made no red commit for the change `{key}`.

> The verdict's last answer was {refusal}.

> No record was written.

**Behave could not report.** `{answer}` is the verdict's line after `behave-unavailable — `.

> red-behaviour made no red commit for the change `{key}`.

> Behave could not report the scenarios' outcomes: {answer}.

> No record was written.

### No scenario written

**The recorded way in reaches none of the change's behaviours.** `{no-reach line}` is the record's `No reach:` line, whole, `No reach:` included. `{way in}` is the value the way-in line records, and `{nfdr}` is the product's `docs/nfdr.md`. `{record}` is the record's path relative to the instance's repository, and `{record commit}` is a short hash.

> red-behaviour wrote no scenario and made no red commit for the change `{key}`.

> QA's record states "{no-reach line}".

> The way in it was judged against is `{way in}`, which `{nfdr}` records.

> QA's record is `{record}`, committed as `{record commit}`.

The sort from `prompts/thin.md` follows, one behaviour per line with its kind. Then the review notes follow, as above.

**No way in is recorded.** `{what was read}` names the file and what it held, for example `` `docs/nfdr.md` is absent `` or `` `docs/nfdr.md` has a `**Behave:**` line that reads `behave` and no `Behave way in` line ``.

> red-behaviour wrote no scenario for the change `{key}` and made no commit.

> No way in is recorded: {what was read}.

> red-behaviour picks no way in of its own, so it writes no scenario.

The sort from `prompts/thin.md` follows, one behaviour per line with its kind, so that the scenarios can be written once a way in is recorded. Then the review notes follow, as above.

**The spec states no behaviour the change adds, changes, or touches and keeps.**

> red-behaviour wrote no scenario for the change `{key}` and made no commit.

> The spec states no behaviour that the change adds, changes, or touches and keeps.

Then the review notes follow, as above.
