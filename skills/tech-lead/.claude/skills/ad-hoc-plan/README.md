# ad-hoc-plan

A change opened by hand holds a `change_request.md` and nothing else, and the change pipeline spends
three seats — Product Owner, Architect, Tech Lead — turning that into a plan before any code is written. For
a change the owner already understands, that relay costs more than it catches. This skill is the
Tech Lead writing the whole plan in one pass: a thin spec, a thin design, and a full
`tl_instruction.md` in exactly the shape `development-plan` produces. It lands them on the change's own
branch, in its own worktree, so the pipeline starts at the stage that writes code. Every later stage
then runs unchanged.

## What It Does

- Takes an idea — conversation, a note, or a seed — beside the active Tobiishi's `change_request.md`,
  the way `seeds-from-idea` takes its input, and grounds every claim it makes against the repository
  (holds / holds smaller / does not hold) before planning against it.
- Reads the change's classification from `change_request.md` and copies it verbatim; it never
  classifies.
- Opens the change's worktree and branch with `create_change_worktree.py`, the command the chain's
  `development-specs` runs, and resolves the product with the path tool the way `development-plan`
  does, so a product in its own repository is planned in its own worktree. It invokes no other skill.
- Writes `change_spec.md` **thin** (header, summary, rules or invariants, out of scope, locked
  answers), `change_design.md` **thin** (every template section, each short; no architect review
  notes), and `tl_instruction.md` **in full** — the design and the instruction agree by construction.
- Checks the three files the way `development-implementation` will (coverage, lane markers, headers,
  paths), then commits them in one commit through the shared builder.
- Never interviews. A stop before the worktree opens leaves nothing behind; a refusal while opening
  it (the worktree command or the path tool) reports what it left.
- Ends by naming the next move — `<CORE>/launchers/chain-development/launcher.sh <project>`, with no
  entry argument — and does not run it.

## File Structure

```
ad-hoc-plan/
├── SKILL.md        # the run: posture gate, inputs, the eight steps, the thin-file shapes, the stop cases
├── launcher.md     # what <CORE>/launchers/skill/launcher.sh reads to start it unattended
├── intelligence/   # the model and effort per provider — Opus at medium, the owner's call 2026-10-17
└── README.md       # this file
```

Read on demand, owned elsewhere and never restated here:

```
<CORE>/../skills/tech-lead/.claude/skills/development-plan/SKILL.md  # every rule about tl_instruction.md
<CORE>/../skills/tech-lead/.claude/skills/development-plan/references/tl_instruction_template.md
<CORE>/../skills/architect/.claude/skills/development-design/references/change_design_template[.preserving].md
<CORE>/../skills/product-owner/.claude/skills/development-specs/references/change_spec_template[.preserving].md
<CORE>/doctrine/governance/commit_via_builder.md  # the one way a producer skill commits
<CORE>/prompts/principal_pm_cut_seeds.md  # § Ground every claim — the three verdicts
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
