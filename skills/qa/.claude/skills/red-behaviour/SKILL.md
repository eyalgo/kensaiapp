---
name: red-behaviour
description: >-
  QA-posture skill that writes one change's behaviour scenarios from its change_spec.md, after the
  spec and before the design, and commits them as the change's red. It first asks the chain whether
  QA's step applies to the change, and where it does not, it writes no file, makes no commit and
  names the line that decided it. It sorts each behaviour the spec states into new or changed, kept,
  or untouched, and writes Behave scenarios for the first two kinds and none for the third, each
  reaching the product only through the way in the product's docs/nfdr.md on main records. A new or changed
  behaviour's scenario must fail on the code before the change, and a kept behaviour's scenario
  passes before the change and still passes at the end. It asks the chain's red verdict before it
  commits, commits its red only on an accepted verdict or on main's red, then writes QA's record and
  commits it. Where the recorded way in reaches none of the behaviours the sort finds, it writes no
  scenario and makes no red commit, and commits QA's record alone, with a No reach line saying why.
  Where the NFDR records no way in, it writes no scenario and reports what it read. Halts outside a
  qa session or the qa subagent.
when_to_use: >-
  Run on a change whose spec is written and whose design is not, or when asked to describe a
  change's behaviour scenarios. Trigger phrases are "describe the scenarios for this change",
  "write the change's red behaviour", "red-behaviour". Do not use for writing the spec
  (development-specs), picking the product's way in (product-architecture), designing the change
  (development-design), or writing the Developer's own tests (development-implementation).
license: MIT
metadata:
  author: Eyal Golan
  version: "1.3.1"
  created: "2026-11-13"
  category: execution
  tags: behave, scenarios, qa, red, pipeline
  risk: safe
---

# red-behaviour

## Purpose

Write the Behave scenarios one change needs, from its spec, before its design is written, and commit them as the change's red. A scenario shows from outside the code what the product does, through the way in the product's NFDR records. A change gets scenarios of two kinds: for what it adds or changes, which must fail on the code before the change, and for existing behaviour it touches and keeps, which pass before the change and still pass at the end. Code the change does not touch gets none.

**This file is the orchestrator.** It owns the posture gate, resolving the change, what the run reads and the order of the steps. **The method is the two prompts beside it.** `prompts/thin.md` sorts each behaviour the spec states into one of three kinds. `prompts/rich.md` owns the scenario rules, the way-in reading and the closing message. Read each in full at its step and apply it. None of it is repeated here.

**What a run does.** It asks the chain whether QA's step applies to the change, and ends there when it does not. Where the step applies, the run writes the scenarios into the product's scenario folder, asks the chain's red verdict, and commits the scenarios as the change's red. Then it writes QA's record and commits it. Where the recorded way in reaches none of the behaviours the change adds, changes, or touches and keeps, the run writes no scenario and makes no red commit. It writes QA's record as a no-reach record, whose `No reach:` line says why, asks the same verdict, and commits the record alone. The chain passes QA's step on a no-reach record the verdict accepts. Every repository and path the run writes to or commits in comes from one command, and the run composes none. After the security review, the chain runs the close: every scenario in the product's scenario folder, on the change's final code, in a throwaway copy, on every change whose card says `behave`, including one this skill did not run for. The close stops the walk at once when a scenario does not pass, when Behave reports none, or when a developer commit changed the scenario folder. It never runs this skill again and never asks for its red or its record. The chain takes one ask from the developer and one from the Architect, each with its reason, and runs QA's step again for an ask it accepts. Each seat's skill makes that seat's ask. Run again on an accepted ask, this skill reads the ask's reason before it writes the scenarios (Step 5).

**Whether QA's step applies to a change is not this skill's call.** One function in the chain decides it, from the project card's Behave line and the spec's Behaviour line, and the run asks it in Step 3. This skill reads neither line itself to decide it. The NFDR's own `**Behave:**` line is read for one thing only, finding the way in (`prompts/rich.md` § *The way in*).

## Posture

**QA only.** Run in a `qa:` session or as the `qa` subagent. Invoked from anywhere else, the run reads no input and ends with the posture refusal below.

**Refused for posture — the session is not a QA session or the `qa` subagent**

> red-behaviour wrote no file and made no commit.

> It needs QA posture.

> Open a session or subagent as `qa` and run red-behaviour again.

## Workflow

### Step 1 — Check the posture

Before reading any input, confirm this session is a `qa` session or the `qa` subagent. If it is not, end with the posture refusal.

### Step 2 — Resolve the change

The run is given a project and a change key, `<YYYY-MM-DD>_<slug>`. The change's spec is on the change's branch, in its worktree, and not on `main`.

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
WORKTREE="$REPO_ROOT/.worktrees/<key>"
test -d "$WORKTREE" || echo "No worktree for <key>"
```

If the worktree does not exist, end with the no-worktree refusal in `prompts/rich.md` § *The closing message*. Do not create the worktree, and do not fall back to `main`. Write the absolute value of `$WORKTREE` down before any `cd`, because a shell variable does not survive from one command to the next, and read every input through it. The change folder is `$WORKTREE/system/projects/<project>/journey/tobiishi/<key>/`.

Resolve the product with the path tool, every run, and never compose a product path by hand:

```bash
"<CORE>/tools/locked_python.sh" "<CORE>/tools/development_path.py" resolve --format json \
  --worktree "$WORKTREE" --project <project> --key <key>
```

A non-zero exit ends the run with the path-tool refusal, carrying the tool's `message`. From the tool's `product_path`, `product_repo` and `product_worktree`: `<sub>` is `product_path` when it is relative, else `product_path` relative to `product_repo` (`.` when the two are the same), and `PRODUCT_ROOT` is `<product_worktree>/<sub>`. `MAIN_PRODUCT_ROOT` is `<product_repo>/<sub>`, the product on its main checkout.

### Step 3 — Ask whether QA's step applies

```bash
"<CORE>/tools/locked_python.sh" "<CORE>/tools/chain_development.py" --qa-applies <key> \
  --instance-root "$REPO_ROOT" --project <project>
```

Exit 1 means QA's step does not apply. End with the does-not-apply closing in `prompts/rich.md` § *The closing message*, carrying the line the command printed after `does not apply — `. Read no further input, write no file, make no commit and run no scenario. Exit 2 ends the run with the command refusal, carrying the command's message. Exit 0 means the step applies, and the run goes on.

### Step 4 — Take the places the run uses

```bash
"<CORE>/tools/locked_python.sh" "<CORE>/tools/development_path.py" target --kind qa --format json \
  --worktree "$WORKTREE" --project <project> --key <key>
```

Write down the five values it prints: `repo`, the product repository the verdict copies; `worktree`, the product's checkout for this change, where the red commit lands; `branch`, the change branch; `scenario_folder`, the product's scenario folder in that worktree; and `record`, the path of QA's record in the change folder. Every repository and path the run writes to or commits in is one of these. A non-zero exit ends the run with the path-tool refusal, carrying the tool's `message`.

### Step 5 — Read the inputs

Read these, in this order:

1. `change_spec.md` in the change folder — every rule and every example. If it does not exist, end with the no-spec refusal.
2. `change_request.md` in the change folder.
3. `MAIN_PRODUCT_ROOT/docs/nfdr.md`, when it exists, for the way in. This is `main`'s copy, the one the chain reads to decide whether a way in is recorded; the change branch's copy may have been cut before the way-in line was written, so it is not read for the way in.
4. `PRODUCT_ROOT/docs/fdr.md`, when it exists.
5. The scenarios the product already holds, under the scenario folder's `features/`, when that folder exists.

Read no `change_design.md` and no `tl_instruction.md`. Both are written after this step, and a scenario fitted to them would show how the change is built rather than what it does.

**A run the chain launched again on an accepted ask reads that ask's reason before it writes the scenarios.** The chain launches that re-run exactly as it launches a first run. So the run tells the two apart from the change's ask record, `$REPO_ROOT/system/logs/chain-qa-<project>-<key>.json`, which the chain writes before it launches the re-run. Read the record as a file. A record that is absent, or that does not parse, holds no open ask. Where the record's `open` entry has the phase `re-run`, the run is a re-run. The reason is then the `reason` of the one `answered` entry whose `step` is the `open` entry's `asker` and whose `answer` is `accepted`. On every other run no reason is read, and the run's inputs are the five above. **The reason is read beside the spec, never in its place.** The scenarios are still written from `change_spec.md` as written. Where the reason asks for a scenario that would change what a rule means, raise it as a question in the review notes, and do not rewrite the rule.

### Step 6 — Sort the behaviours

Read `prompts/thin.md` in full and apply it to every behaviour the spec states.

### Step 7 — Write the scenarios

Read `prompts/rich.md` in full and apply it to the sort from Step 6. It says what each scenario must show and how to write it into the scenario folder.

### Step 8 — Ask the verdict

Before you ask, write QA's record at the `record` path Step 4 printed, from `references/qa_record_template.md`, in the form `prompts/rich.md` § *Asking the verdict, and what each answer means* sets for the sort. A red record fills every slot but `Base commit:` and `Red commit:`. The verdict reads each scenario's kind from the record, and the two commit slots wait for the answer and the red commit. A no-reach record fills every slot but `Base commit:`, which waits for the answer, and carries no `Red commit:` line and no `Scenario:` line.

```bash
"<CORE>/tools/locked_python.sh" "<CORE>/tools/chain_development.py" --check-qa-red <key> --draft \
  --instance-root "$REPO_ROOT" --project <project>
```

The first line it prints is the answer. Act on it as `prompts/rich.md` § *Asking the verdict, and what each answer means* says. Keep the `Base commit:` line of the answer you act on, and, for a red record, its `Scenario:` lines: QA's record is written from them. Exit 2 ends the run with the command refusal.

### Step 9 — Commit the red

On `qa red: no reach — …` there is no red to commit. Skip this step and go to Step 10.

Only on `qa red: accepted`, or on an answer that begins `main is red`. Commit through the shared builder: read `<CORE>/doctrine/governance/commit_via_builder.md` and supply its variables. `<repo>` is the `worktree` Step 4 printed. The files to stage are the paths under its `scenario_folder`, each given relative to that repository, and no other path. Pass `--actor qa` and `--skill red-behaviour`. The subject is `qa: <key> — red scenarios`. Never hand-write `git commit` or a trailer. Write down the red commit's full hash.

### Step 10 — Write and commit QA's record

Finish QA's record at the `record` path Step 4 printed: fill `Base commit:` from the verdict's last answer, and, in a red record, `Red commit:` with the red commit's full hash. Commit it through the shared builder the same way, with `<repo>` the change's worktree, `$WORKTREE`, the record as the one file to stage, `--actor qa`, `--skill red-behaviour`, and the subject `qa: <key> — QA record`.

A no-reach record is committed the same way, alone, with no red commit before it.

### Step 11 — Close

End with the closing message `prompts/rich.md` § *The closing message* sets for the outcome that holds.

## Critical Rules

- **A reason only on a re-run, and never in the spec's place.** A run the chain launched again on an accepted ask reads that ask's reason from the change's ask record (Step 5). Every other run reads none.
- **QA posture only.** Outside it, the run reads no input.
- **This skill does not decide whether it applies.** It asks the chain (Step 3) and reads neither the card's Behave line nor the spec's Behaviour line for that.
- **No path of its own.** Every repository and path the run writes to or commits in comes from the paths command (Step 4).
- **No commit before the verdict.** The red is committed only on an accepted answer or on main's red, and QA's record only after the red. A no-reach record is the one exception: it is committed alone, only on `qa red: no reach — …`, and no red is committed with it.
- **No library outside the red commit.** A change to the scenario folder's `pyproject.toml` or `uv.lock` goes in the red commit, or not at all.
- **No way in of its own.** The way in is the one the product's NFDR records, or there is none.
- **No `change_design.md` and no `tl_instruction.md`.**
- **Every core reference is `<CORE>`, and no file here names a real product.**
