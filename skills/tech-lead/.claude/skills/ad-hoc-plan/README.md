# ad-hoc-plan

A change opened by hand holds a `change_request.md` and nothing else, and the change pipeline spends
three seats — Product Owner, Architect, Tech Lead — turning that into a plan before any code is written. For
a change the owner already understands, that relay costs more than it catches. This skill is the
Tech Lead writing the whole plan in one pass: a stub spec, a stub design, and a full
`tl_instruction.md`, planned by the same body `development-plan` follows, naming itself as the planner. It lands them on the change's own
branch, in its own worktree, so the pipeline starts at the stage that writes code. Every later stage
then runs unchanged.

## What It Does

- Takes a brief beside the active Tobiishi's `change_request.md`, the way `seeds-from-idea` takes its
  input: in a session the session drafts it from `templates/brief.md` and you confirm it, its quotes
  are checked, and only your words ground the plan. Unattended, the Request is the brief. It grounds
  every claim against the repository (holds / holds smaller / does not hold) before planning against
  it.
- Reads the change's classification from `change_request.md` and copies it verbatim; it never
  classifies.
- Opens the change's worktree and branch with `create_change_worktree.py`, the command the chain's
  `development-specs` runs, and resolves the product with the path tool the way the shared planning
  body does, so a product in its own repository is planned in its own worktree. It invokes no other skill.
- Writes `change_spec.md` and `change_design.md` as **stubs** — only what the chain and the plan
  read (the spec's header, summary, rules or invariants, out of scope and locked answers; the design's
  template sections, each short) — then plans `tl_instruction.md`
  **in full** by `<CORE>/prompts/tech_lead_create_tl_instruction.md`, with those two as its input —
  the body `development-plan` follows, so the two skills differ only in their input. The chain does
  not audit the two stubs; it knows them by their `Planned by: ad-hoc-plan` line.
- Checks the stub spec and design the way the stages after it will (headers), then commits them in one commit through the shared
  builder, with a report beside the brief.
- Writes that report, `ad_hoc_plan_report.md`, in the shape of `templates/report.md`, on every run
  but three stops (`SKILL.md` § *The run's report*). A stop's report is committed on `main`.
- Never interviews. A stop before the worktree opens leaves nothing behind but its report; a refusal while opening
  it (the worktree command or the path tool) reports what it left.
- Ends by naming the next move — `<CORE>/launchers/chain-development/launcher.sh <project>`, with no
  entry argument — and does not run it.

## File Structure

```
ad-hoc-plan/
├── SKILL.md        # the run: posture gate, inputs, the nine steps, the stub shapes, the stop cases
├── launcher.md     # what <CORE>/launchers/skill/launcher.sh reads to start it unattended
├── templates/
│   ├── brief.md    # this skill's brief; extends <CORE>/templates/brief_template.md
│   └── report.md   # the report every run writes beside the brief
├── intelligence/   # the model and effort per provider — Opus at medium, the owner's call 2026-10-17
└── README.md       # this file
```

Read on demand, owned elsewhere and never restated here:

```
<CORE>/prompts/tech_lead_create_tl_instruction.md  # every rule about tl_instruction.md, shared with development-plan
<CORE>/../skills/tech-lead/.claude/skills/development-plan/references/tl_instruction_template.md
<CORE>/../skills/architect/.claude/skills/development-design/references/change_design_template[.preserving].md
<CORE>/../skills/product-owner/.claude/skills/development-specs/references/change_spec_template[.preserving].md
<CORE>/doctrine/governance/commit_via_builder.md  # the one way a producer skill commits
<CORE>/prompts/principal_pm_cut_seeds.md  # § Ground every claim — the three verdicts
<CORE>/templates/brief_template.md  # the brief's common part, and how a session drafts one
<CORE>/tools/check_brief_quotes.py  # Step 1 — every quote in the brief is at its lines
<CORE>/tools/create_change_worktree.py  # Step 4 — the change's branch and worktree(s)
<CORE>/tools/development_path.py  # Step 4 — where the product's docs and code are
```

## Depends On

No other skill. Step 4 runs two programs under `<CORE>/tools/`: `create_change_worktree.py` creates
branch `<key>` and `.worktrees/<key>`, and a second worktree in the product's own repository when it
has one; `development_path.py` resolves the product's docs and code inside them.

## When to Use

- You opened a Tobiishi by hand (or with `tobiishi-open`), it holds only `change_request.md`, and you
  want it planned in one pass rather than walked through specs, design and plan.
- You are in a `tech-lead:` session, or spawning the `tech-lead` subagent.
- The product is in this repository (a relative `Product path:`) or in its own (an absolute one).

Then carry it with:

```
<CORE>/launchers/chain-development/launcher.sh <project>
```

Do **not** use it for a change the chain is already carrying, for cutting seeds, or for executing
a plan.
