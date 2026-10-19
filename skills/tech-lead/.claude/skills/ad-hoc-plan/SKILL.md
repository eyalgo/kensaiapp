---
name: ad-hoc-plan
description: >-
  Tech Lead-posture skill that plans a hand-opened 飛び石 Tobiishi end to end, so the chain can
  carry it from the content step, or from implementation when the change publishes no text, onward. Takes an idea — something said in passing, a note, or a seed
  someone set down — beside the change folder's change_request.md, grounds every claim against the
  repository, opens the change's worktree, and writes the three files the later stages read — a thin
  change_spec.md, a thin change_design.md, and a full tl_instruction.md in exactly the shape
  development-plan produces. Requires Tech Lead posture and halts outside a tech-lead session or the
  tech-lead subagent. It never interviews — when the repository cannot settle something it stops
  before writing anything and says what would settle it. Use when a change has been opened by hand
  and should be planned in one pass rather than walked through development-specs, development-design
  and development-plan.
when_to_use: >-
  Trigger phrases — "ad-hoc-plan", "plan this tobiishi", "write the tl_instruction for this change",
  "plan the change I just opened", "spec, design and plan this in one go". It also fires when a
  Tobiishi folder holds only a change_request.md and the ask is to make it ready for implementation.
  Do not use for opening the Tobiishi (tobiishi-open, or by hand), cutting an idea into seeds
  (seeds-from-idea), planning inside a running change pipeline (development-plan), executing a plan
  (development-implementation), or a change whose branch already exists.
license: MIT
metadata:
  author: Eyal Golan
  version: "1.9.0"
  created: "2026-09-11"
  category: planning
  tags: tobiishi, tl_instruction, change_design, change_spec, tech-lead, development
  risk: safe
---

# ad-hoc-plan

## Purpose

A change opened by hand has a `change_request.md` and nothing else. The change pipeline would spend
three stages turning it into a plan — a spec, a design, an instruction, each written by a different
seat.
This skill writes all three in one pass, as one author, so the pipeline can start at the first stage after planning: the Content Editor's `content` step when the
change publishes text, and the stage that writes code when it does not.

What arrives: a project, its one active Tobiishi, and optionally an idea that says more than the
request does. What leaves, committed on the change's own branch in its own worktree:

| File | Shape | Who reads it next |
|---|---|---|
| `change_spec.md` | **thin** — § *The thin spec* | `development-code-integrity`, as the behavioural intent behind the plan |
| `change_design.md` | **thin** — § *The thin design* | `development-implementation` Step 1b, which cross-checks the instruction against it |
| `tl_instruction.md` | **full** — exactly `development-plan`'s output | `development-implementation`, as its primary contract |

**This file owns the run, not the shapes.** Every rule about what a `tl_instruction.md` contains —
its header, its layout, its task shapes and their exact `#### Implement` markers, its review notes,
its corrections — is `<CORE>/../skills/tech-lead/.claude/skills/development-plan/SKILL.md`, and its shape is that skill's
`references/tl_instruction_template.md`. The design's shape is
`<CORE>/../skills/architect/.claude/skills/development-design/references/change_design_template.md` (or `.preserving.md`); the
spec's is `<CORE>/../skills/product-owner/.claude/skills/development-specs/references/change_spec_template.md` (or `.preserving.md`).
None of them is restated here. What is this skill's own is which parts of the spec and design a thin
file keeps, how the three are written as one decision, and when the run stops.

## Posture

**Tech Lead only.** Run in a `tech-lead:` session or as the `tech-lead` subagent. Invoked from
anywhere else, halt at once, say the posture is wrong, and name the way in.

The gate exists because the run writes and commits with nobody answering part-way through: its
judgment is the seat's, so the seat is checked (`<CORE>/doctrine/setup/authoring_layers.md`
§ *A skill that acts unattended gates to its seat*). The instruction is the Tech Lead's artifact; the
thin spec and design exist so the instruction has what the next stages cross-check it against.

## Inputs

- **The project** `<project>` — the `system/projects/<project>/` folder. Required.
- **The active Tobiishi** — the single `<key>/` folder under
  `system/projects/<project>/journey/tobiishi/` (ignore `trail/`) holding a `change_request.md`. It
  may have been placed by `tobiishi-open` or by hand; either is fine. Its **Request**, **Category**
  and **Behaviour** are read, never set.
- **The idea** — optional. The owner's words in the invoking message, a note, or a seed or station
  by path. Where none is given, the Request is the idea.
- **The repository as it stands** — every file, symbol, command and count the Request and the idea
  name. **Where the idea and the repository disagree, the repository wins.**
- **`system/projects/<project>/project.md`** — `Product path:`, `Execution type:`, `Test command:`,
  `Languages:`, and `Setup command:`, which Step 4's command runs in the new worktree.
- **The product's decision files, where they exist** — `adr/`, `nfdr.md`, `fdr.md` and the parts
  table of `SDD.md` § 3, under the product's `docs/`. Read, and bound by, exactly as
  `development-plan` § *Pre-flight — Read decision files* says: optional context, and their absence
  is never an error. The product is in this repository (a relative `Product path:`) or in its own
  (an absolute one); both are planned.

## Workflow

Steps 1–3 read and decide; nothing is written until Step 4. **A stop in Steps 1–3 leaves no
worktree, no branch and no file behind.** Step 4's stop — the worktree command or the path tool
refusing — can come after something exists, and reports what does (§ *When you stop*).

**The checkout is the instance's main working tree** — the first entry `git worktree list` prints,
the same answer from any linked worktree of it. Step 4's command cuts the branch from that tree's
`HEAD`, so Steps 1 and 2 read that tree and no other.

### Step 1 — Gate, then resolve the change

1. Check the posture (§ *Posture*).
2. Find the active Tobiishi. None → stop. More than one → stop and name every key found; picking one
   would plan a change nobody asked for now.
3. **`change_request.md` is committed on the main working tree.** The change's branch forks from its `HEAD`
   (`<CORE>/tools/create_change_worktree.py`, which Step 4 runs), and `tobiishi-seal` Step 1
   refuses to seal a branch where the file is missing. Check `git ls-files --error-unmatch` on it
   and that `git status --porcelain` shows it clean; if not, stop and say so — committing the
   opener's file is the opener's move.
4. **The change has not entered the pipeline.** If branch `<key>` or `.worktrees/<key>` already
   exists — in this repository, or in the repository holding an absolute `Product path:` — stop: this
   skill plans a fresh change, and Step 4's command would refuse anyway.
5. **Read the classification; do not make it.** `Category` and `Behaviour` come from
   `change_request.md` and are validated against the closed vocabulary in
   `<CORE>/doctrine/flow/change_classification.md`. Missing, out of vocabulary, `refactor` with
   `changing`, or `feature` with `preserving` → stop. Classification is set at entry, by whoever opened the change, and every later
   file copies it verbatim.
6. **Resolve the idea** to what the spec will cite: a repo-relative path where it is a file, or the
   owner's words with the date they were said where it was conversation.

### Step 2 — Ground every claim

Resolve the product for reading on the main working tree, which holds what the branch will fork
from (for a product in its own repository, its checkout at `Product path:`): `PROJECT_DOCS` = `<Product path>/docs` and `PROJECT_ROOT` = its parent, a relative
`Product path:` resolving from the instance root and an absolute one read as written
(`development-specs` Step 1). Read the decision files that exist, as `development-plan`
§ *Pre-flight — Read decision files* does.

Then open everything the Request and the idea name, and resolve each claim the way
`<CORE>/prompts/principal_pm_cut_seeds.md` § *Ground every claim before you cut — holds, holds
smaller, does not hold* resolves an idea's — with "the plan" in place of "the seed":

- **It holds** → plan against it.
- **It holds smaller** → plan the smaller thing, and record the measurement and the divergence in the
  spec's `## Locked Answers`.
- **It does not hold** → stop.

A claim about what a command *decides* is verified by running the command, never by reading it — the
reason is `development-specs` Step 6, *Claims about existing code (both modes)*. And run the card's
`Test command:` once: a gate copied from a card that runs nothing passes every task
(`development-plan` Step 2, the last row of its review table). A card reading `none` is a product
with no code: run nothing, and gate each task on the command or reading its claim names.

### Step 3 — Decide the change as one decision

The spec, the design and the task list are three views of one decision, and this run makes it once.
Settle, in this order:

1. **One change.** If removing part of the request would leave a shippable, independently testable
   change, it is two changes → stop.
2. **What is observable** — the rules (changing) or the invariants and structural goal (preserving),
   at the altitude `development-specs` Step 5 holds a spec to. Rule identifiers continue the project's
   `CP-<n>` series, per that step's *The series belongs to the project, not to the change*.
   A direction the request leaves open is picked conservatively where the pick is reversible, and
   recorded in `## Locked Answers`; where no safe default exists → stop.
3. **Where it lands** — blast radius, sub-jobs, build order, a hint only where the approach is
   non-obvious, and the tests each sub-job adds. Each new piece of logic goes in the part that owns
   it, by `development-plan` Step 2's placement row. Where `nfdr.md § 1.2` fixes the module set, it binds:
   a change that needs a module the set does not have → stop, since that decision belongs to the
   records' owner. Where no records exist, the design's module boundaries are this run's to decide.
4. **The tasks** — cut from the sub-jobs by `development-plan` Step 3 and § *TL Standards*, each in the
   one shape its § *Implement section rules* picks. **A task that fits no sanctioned shape → stop**;
   that skill's rule, and this run inherits it.

**Too thin to plan** — the request and the idea together do not say what a task would verify, and the
repository does not either → stop. Never write a plan around the gap.

### Step 4 — Open the worktree

Run the command `development-specs` Step 4 runs, with the main checkout's top level, the project and
the key:

```bash
python3 "<CORE>/tools/create_change_worktree.py" \
  --instance "$(git rev-parse --show-toplevel)" --project <project> --key <key>
```

It creates branch `<key>` and the instance worktree, and for a product in its own repository a second
worktree there on the same key. `$WORKTREE` is the `worktree` of the `repos` entry whose `role` is
`instance`, taken as printed. A non-zero exit is a stop: report the command's `error`, `message`,
`changed` and `repos` as printed, and do not retry or create anything by hand.

From here on `$WORKTREE` is the working root. Resolve `PROJECT_DOCS` and `PROJECT_ROOT` exactly as
`development-plan` § *Enter the worktree* does, from **Resolve `PROJECT_DOCS`** through **Locate the
product code**: the path tool's contract, never a path composed by hand, so an external product's
docs and code are read in its product worktree. Every file below is written under
`$WORKTREE/system/projects/<project>/journey/tobiishi/<key>/`.

### Step 5 — Write the three files

In order: spec, design, instruction.

#### The thin spec

`change_spec.md`, from the spec template for the change's `Behaviour`. Keep:

- **the header** — `Date`, `Category`, `Behaviour` and `Request` exactly as the template lays them
  out, the two labels copied verbatim from `change_request.md`, then one line more:
  `**Planned by:** ad-hoc-plan — thin spec; development-specs did not run on this change.` and,
  where an idea was given, `**Idea:** <path, or the owner's words and date>`;
- `## Change Summary`;
- `## Rules` with their `CP-<n>` identifiers (changing), or `## Invariants` and `## Structural Goal`
  (preserving);
- `## Out of Scope` — always, at least one boundary;
- `## Locked Answers` — whenever the spec went beyond the request, or a claim held smaller.

Leave out `## Examples` and `## Verified Claims`. Nothing the pipeline runs after implementation
turns on them, and the grounding they would record is carried by `## Locked Answers` and the
instruction's `## TL Review Notes`.

#### The thin design

`change_design.md`, from the design template for the change's `Behaviour`. **Thin means short, not
missing:** keep every section the template has except `## Architect Review Notes`, and write each as
briefly as the change allows. `development-implementation` Step 1b cross-checks the instruction
against §3, §4 and §5, so a section it looks for must be there to find.

- the header, `Category` and `Behaviour` copied verbatim from the spec, and the `Publishes text:` line on
  the line after `Behaviour:`, **decided by this run** from the spec: `yes — <the places the words live>`
  when the change puts text in front of a person to read, `no` otherwise, and always `no` for a
  `Behaviour: preserving` change (the rule is `development-design`'s Step 6). The chain reads its first
  word, which must be exactly `yes` or `no`;
- §1–§5 (§3 omitted when one module is affected, as the template says);
- `## Records this change makes false` — always, its zero form naming what was read.

`## Architect Review Notes` is left out because the design has nothing upstream to diverge from but a
spec written by the same run in the same pass.

#### The instruction

`tl_instruction.md`, written by `development-plan`'s rules to its template, in full — header, project
layout, review notes, corrections, and every task. `Product root:` is `$PROJECT_ROOT` as Step 4
resolved it (`development-plan` § *Plan Header*).

**The design and the instruction agree by construction.** Every §3 sub-job is covered by a task,
every §4 hint is carried as that task's `# Hint:` block, and every §5 row lands in a task's
behaviours. Where writing the instruction shows the design was wrong, **correct the design** rather
than log a divergence — both are this run's, and an instruction that diverges from its own design
without a logged reason is what `development-implementation`'s *TL divergence arbiter* stops on.
`## TL Review Notes` records divergences from the spec and the request only, and is omitted when there
are none.

### Step 6 — Check what the next stages will check

Before committing, read the three files as `development-implementation` will:

- **Coverage.** The instruction covers the design, sub-job by sub-job and row by row; every `CP-<n>`
  rule reaches a task's behaviours or its `#### Held by review`.
- **Lanes.** Every task has exactly one gate subsection, and its `#### Implement` carries one of
  `development-plan`'s sanctioned markers **verbatim** — the implementer routes on the literal text.
- **Headers.** `Category` and `Behaviour` read the same in all three files and in `change_request.md`, and
  `change_design.md` carries a `Publishes text:` line whose first word is exactly `yes` or `no`, with a
  `yes` naming its places.
- **Paths.** `Product root:` names the worktree, never the `Product path:` field — relative to
  `$WORKTREE` for an in-repo product, and the absolute product worktree for an external one
  (`development-plan` § *Plan Header*);
  `system/projects/<project>/journey/tobiishi/<key>/tl_instruction.md` resolves inside `$WORKTREE`, on
  branch `<key>`.

A miss here is this run's own output, so fix it in place and check again.

### Step 7 — Commit

One commit on the change branch, through the shared builder — read
`<CORE>/doctrine/governance/commit_via_builder.md` and supply its variables: `<repo>` = `$WORKTREE`;
`--add` the three files by **repo-relative** path; `--actor tech-lead`; `--skill ad-hoc-plan`; a
subject of `tech-lead: <key> — ad-hoc plan (spec, design, instruction)`; and the directional that
recipe's item 6 resolves for a project artifact. Never hand-write `git commit` or a trailer.

### Step 8 — Close

Report the key, the worktree, and the three files by path, and name the next move. **Do not run it**
— running the pipeline is the owner's call, as it is after `tobiishi-open`.

The next move is the chain, with no entry argument and no key:

```
<CORE>/launchers/chain-development/launcher.sh <project>
```

The chain takes the project's single active Tobiishi and enters at the first step whose artifact is
missing on the branch (`<CORE>/tools/chain_development.py` `DiskReader.is_done` and
`DiskReader.entry_step`, cited by name because their lines move). With `change_spec.md`,
`change_design.md` and `tl_instruction.md` committed on branch `<key>`, that is:

- **`content`** when the design's `Publishes text:` line reads `yes`, so the Content Editor writes
  `change_text.md` before any code, and the Developer places that text;
- **`implementation`** when it reads `no`, because the engine passes the `content` step with no launch.

This is the entry `chain_development.py --describe` prints as `entry=` for such a change. The worktree
this run opened is entered, not re-created. Code-integrity, the implementation audit and the seal run
as usual.

## When you stop

**You stop the moment the plan needs a decision the repository cannot make.** The run never
interviews: it does not ask part-way, does not park an item for later, and does not plan around the
gap. A stop reports, in the closing message, which case fired, the file or claim that fired it, the
check that produced the verdict, and what would settle it — then halts. No file is written to hold the
report.

| Case | Fired at |
|---|---|
| Wrong posture | Step 1 |
| No active Tobiishi, or more than one | Step 1 |
| `change_request.md` uncommitted | Step 1 |
| Branch or worktree `<key>` already exists | Step 1 |
| Classification missing, out of vocabulary, `refactor` + `changing`, or `feature` + `preserving` | Step 1 |
| A claim the plan rests on does not hold, or cannot be reached | Step 2 |
| Two changes in one request | Step 3 |
| An open direction with no safe default | Step 3 |
| A module the records' module set does not have | Step 3 |
| A task that fits no sanctioned shape | Step 3 |
| Too thin to plan | Step 3 |
| The worktree command refuses, or the path tool cannot resolve the product | Step 4 |

**Step 4's stop is the one that can leave something behind.** The command checks every repository
before it changes any, so a refusal in those checks leaves nothing. A refusal once it has started
changing things — writing the local exclude, adding a worktree, confirming the result, running the
setup command, checking the test interpreter — can leave a branch or a worktree, in one repository
or both, and its `changed` and `repos` say what exists. The path tool refusing comes after the
worktrees exist, so it leaves them too. Report what exists as the command printed it.

## Critical Rules

- **Tech Lead posture, or halt.**
- **Nothing is written before Step 4, and every stop but Step 4's own comes before it.**
- **It invokes no other skill.** Other skills' files are read for their rules; the worktree is
  opened by `create_change_worktree.py` and the product resolved by `development_path.py`, the
  programs the chain uses.
- **The shapes are the pipeline's.** The instruction is `development-plan`'s output, exact; the thin
  files are that stage's templates with the parts named in Step 5 kept. Never invent a section, a
  marker or a gate subsection.
- **Classification is copied, never decided.**
- **The repository wins.** Every claim is opened before it is planned against; one that holds smaller
  is planned smaller and recorded; one that does not hold stops the run.
- **One author, one decision.** The design and the instruction agree by construction; where they would
  not, the design is corrected.
- **The change arc is on the branch.** Every file is written under `$WORKTREE` and committed with
  `git -C "$WORKTREE"`, never on `main`.
- **Existing skills are read, never edited.** This skill writes three files in one change folder and
  touches nothing else.
- **The pipeline is the owner's to run.** Report the launcher command; do not run it.
