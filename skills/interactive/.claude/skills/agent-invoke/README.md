# agent-invoke

Handing a task to a subagent needs four things assembled before anything runs — a model, a brief
that survives being read cold, something holding the Mac awake, and a notification that reaches an
owner who has walked away. Assembled by hand each time, the two that get forgotten are the model
choice and the notification, because their absence only shows up afterwards: a run that came back
weaker than it should have, or one that finished an hour before anyone noticed. This skill is that
launch procedure. It configures a run; it does not scope one — what the agent should do is the
owner's request, not this skill's decision.

## What It Does

- Reads the request for its **task shape** and picks the model through
  `<CORE>/doctrine/governance/model_assignment.md`, so no model name is ever written into a brief
  and a tier reassignment in doctrine reaches every future run.
- Resolves **where the output lands** before launching — existing files, `docs/proposals/<slug>/`,
  or a managed project's `docs/` — and names it in the brief rather than letting the agent invent it.
- States what every **brief** must carry, including the reasoning behind each constraint and an
  explicit instruction that ambiguity is surfaced rather than settled.
- Requires the agent to **commit its own work** through the shared builder, since only the agent
  knows what it changed and why. Research commits a written artifact too.
- Holds the Mac awake for the run, with an explicit release when it lands.
- **Verifies the return against the repo** before believing it, then sends the Telegram.

## File Structure

```
agent-invoke/
├── SKILL.md                      # the launch procedure — six steps and the boundaries
├── README.md                     # this file
└── evals/
    └── trigger_eval.json         # 20 reviewed trigger queries (10 should-trigger, 10 near-miss negatives)
```

## Depends On

Nothing at runtime. It reads `<CORE>/doctrine/governance/model_assignment.md` for the model tier and
`<CORE>/doctrine/governance/commit_via_builder.md` for commit mechanics.

## When to Use

When the owner asks for work to be handed off rather than done in the conversation — including
phrasings that never say "agent" (*"I want to research…"*, *"look into X and report back"*, *"go do
X while I'm away"*). One shape only: an Agent-tool subagent run in the background, which lives inside
the session and so reports completion reliably.

Not for work a launcher or pipeline stage already owns — the kaizen cold-read chain,
the development chain, `skill-evals` — each spawns its
own agents under its own model and notification rules. Not for work small enough to do inline: a
launch costs a brief, a verification pass, and a notification.

## Eval status

`evals/trigger_eval.json` holds the reviewed query set. It has **not** been scored: the description
optimizer in `skill-evals-trigger` returned `recall=0%` across five iterations with five different
descriptions, and a control run against the established `skill-evals-creator` skill returned
`recall=0%` as well — zero triggers on every positive query. The harness cannot currently register a
trigger for any skill, so the description here is unoptimized and honestly labelled as such.
