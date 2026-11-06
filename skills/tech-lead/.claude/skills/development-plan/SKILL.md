---
name: development-plan
description: Tech Lead-posture skill for ongoing work; halts outside a tech-lead session or the tech-lead subagent. Reads change_spec.md + change_design.md + docs/adr/ + docs/fdr.md + docs/nfdr.md + the parts table of docs/SDD.md § 3 + the resolved language packet, critically reviews the design against the spec, puts each new piece of logic in the task for the part that owns it, plans no task its language packet forbids, and produces tl_instruction.md — a scaffold the developer implements from failing tests.
license: MIT
metadata:
  version: "3.3.0"
  category: planning
  risk: safe
---

# Development Plan

## Purpose

Read `change_spec.md` (what was asked), `change_design.md` (the design delta), `docs/adr/` (the decision log — why the system is shaped as it is), `docs/fdr.md` (the behavioural contract, if it exists), `docs/nfdr.md` (the constraint set — the module set and its import graph, § 1.2), `docs/SDD.md` § 3 (the parts table — which part owns which logic), and the language packet the product resolves to (the practice every task's code follows), then produce `tl_instruction.md` — a **scaffold** the developer implements from failing tests.

**This file says how the run reaches its inputs. How the plan is made is
`<CORE>/prompts/tech_lead_create_tl_instruction.md`** — the planning body this skill shares with
`ad-hoc-plan`, which reaches the same point from a brief instead. Read it in full and follow it once
§ *Enter the worktree* below has `$WORKTREE`. None of it is restated here.

## When to Use

- `development-design` has produced `change_design.md` in `system/projects/<project>/journey/tobiishi/<YYYY-MM-DD>_<slug>/` (the records under `docs/adr/`, `docs/nfdr.md` and `docs/SDD.md` are used when present, but are not required — see the shared body's § *Pre-flight — Read decision files*)
- A `tl_instruction.md` is needed
- `development-plan` is explicitly requested

## Posture

**Tech Lead only.** Run in a `tech-lead:` session or as the `tech-lead` subagent. Invoked from anywhere else,
halt at once, say the posture is wrong, and name the way in — open a session with the `tech-lead:`
prefix, or run the `tech-lead` subagent. The seat's contract is `<CORE>/roles/loaders/tech_lead_global.md`.

The gate is here because the run writes and commits the plan with nobody answering (`<CORE>/doctrine/setup/authoring_layers.md` § *A skill that acts
unattended gates to its seat*).

## Enter the worktree

development-specs created an isolated worktree for this change and landed the spec arc on the branch — it is **not** on `main`. development-design then committed `change_design.md` there. Before reading anything, derive the worktree from the **change key** and operate inside it for the whole run.

The **change key** is `<YYYY-MM-DD>_<slug>` — the Tobiishi folder (`journey/tobiishi/<key>/`) / branch name. You know it from the invocation (the change you were asked to plan). If multiple worktrees exist under `<repo>/.worktrees/` and the intended change is ambiguous, ask which one — once.

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
WORKTREE="$REPO_ROOT/.worktrees/<key>"
test -d "$WORKTREE" || echo "No worktree for <key> — development-specs must run first."
```

If `$WORKTREE` does not exist, **STOP**: the upstream stages have not run for this change. Do not create it here and do not fall back to `main`.

**From here on, the worktree is the working root:** read every input from `$WORKTREE/` (`change_spec.md`, `change_design.md`, and the decision files), write `tl_instruction.md` under `$WORKTREE/`, and commit with `git -C "$WORKTREE"`. The change arc stays on the branch, never `main`. The path is derived from the key alone — identical convention to development-specs Step 4, development-design, and `ad-hoc-plan`; nothing is handed between sessions.

## Then plan

**A record names no machine.** No line this skill writes into a record names the home folder or the login name of the machine it runs on, or the repository's own `<owner>/<name>` address. Terminal output pasted into a record, and the commands an evidence line quotes, are the cases to look at first. The rule, with the placeholders to write instead, is `<CORE>/doctrine/governance/records_name_no_machine.md`. The pre-commit hook refuses a commit that adds such a line.

Follow `<CORE>/prompts/tech_lead_create_tl_instruction.md` from § *Resolve the product* to its
Step 4, with `--skill development-plan` at the commit. Where that file's § *A records defect is
raised, not planned around* ends the plan first, it ends in the halt report that section writes, in
place of Step 4.

The run ends in one of two ways:

- **The plan is made.** It ends when the plan commit lands.
- **The halt is `records-owed`.** It ends when the halt report is committed on the change branch.
  Commit it through the shared builder, `<CORE>/doctrine/governance/commit_via_builder.md`, with
  `<repo>` = `$WORKTREE`, the change folder's `halt_report.md` staged, `--actor tech-lead` and
  `--skill development-plan`. No `tl_instruction.md` is left beside it.

## Critical Rules

- **The worktree is upstream's.** If `$WORKTREE` is absent, STOP — do not create it and do not fall
  back to `main`.
- **The planning rules are the shared body's.** Every other rule this run follows is
  `<CORE>/prompts/tech_lead_create_tl_instruction.md` § *Critical Rules*.
