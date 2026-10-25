---
version: "3.2.0"
---

# Model assignment

The four stable Kensaiapp tiers, how each binds to a provider, and how a run with **no skill behind
it** chooses one and, from an interactive session, how it is started. **Fable / Opus / Sonnet /
Haiku are stable Kensaiapp tiers, not universal provider model IDs.** This file is the policy; provider bindings are mechanism, resolved by
`<CORE>/tools/model_assignment.py`. The `AGENT_ROLE` map in `<CORE>/tools/commit_builder.py` records
the role independently.

**An agent slot carries no model.** A chain run's model and effort are its skill's, declared in the
skill's own `intelligence/<provider>.md` in that vendor's terms — `skill_intelligence.md` owns that
rule, and nothing on this page applies to a chain run. The per-slot table this file kept until
2026-09-29, which pinned a tier to each `.claude/agents/*.md`, was retired that day with the pins
themselves: the owner's call, 2026-09-29.

## Provider bindings

The resolver is the machine source of truth for these replaceable bindings. A caller passes
`--model-tier` to `<CORE>/tools/agent_run.py`; the selected adapter turns it into the provider's model
and, where meaningful, its reasoning effort. A caller may instead pass `--model` as an intentional
raw provider override, but never both. The tier path serves the runs outside the chains (§ *Runs with
no standing slot*). A chain launcher passes its skill's declared model as `--model`
(`skill_intelligence.md`), never a tier.

| Kensaiapp tier | Claude binding | Codex binding | Gemini binding |
|---|---|---|---|
| Fable | `fable` | `gpt-5.6-sol`, `xhigh` reasoning | `gemini-3.1-pro-high`, `high` reasoning |
| Opus | `opus` | `gpt-5.6-sol`, `high` reasoning | `gemini-3.1-pro-low`, `low` reasoning |
| Sonnet | `sonnet` | `gpt-5.6-terra`, `medium` reasoning | `gemini-3.8-flash-medium`, `medium` reasoning |
| Haiku | `haiku` | `gpt-5.6-luna`, `low` reasoning | `gemini-3.8-flash-low`, `low` reasoning |

These are equivalence by **workload posture**, not a claim that the provider models are technically
identical. Fable buys the strongest available Codex model at its highest documented reasoning effort;
Opus uses the same model with a smaller reasoning budget; Sonnet selects the balanced worker model;
Haiku selects the efficient model. Gemini follows the same
posture against the models catalogued by `agy models`: Fable takes `gemini-3.1-pro-high` at `high`
reasoning; Opus takes `gemini-3.1-pro-low` at `low` reasoning; Sonnet takes `gemini-3.8-flash-medium` at
`medium` reasoning; Haiku takes `gemini-3.8-flash-low` at `low` reasoning. Provider upgrades change
the resolver and this small table, not the reasoning that picked a run's tier.

The tiers, in one line: **executive strategy, and decisions others execute verbatim → Fable ·
senior reasoning, review, and audit → Opus · implementation and process coordination → Sonnet ·
lightweight automation → Haiku.** § *Runs with no standing slot* reads a task against these.

## Runs with no standing slot

Some runs have no skill's intelligence file behind them: a bare `claude --bg` session, an ad-hoc
subagent, a `delegate` run started through `agent-invoke`. No agent slot carries a model either, so the
model is a **per-run choice** made by the caller — by *where the judgment lives*, read against the task
rather than a role, on the tiers above:

- **Authoring or deciding** something consumed as-authored → top tiers (Fable / Opus).
- **Applying an already-decided plan**, with a reviewer to gate it → the worker tier (Sonnet).
- **One checkable transformation at volume** → the cheap tier (Haiku).
- Caveat: an autonomous **tool-loop** wants at least the worker tier even when each step is simple —
  driving the loop is itself judgment.

**Where an interactive session would start the provider's built-in general-purpose agent, it runs
`agent-invoke` instead**, which starts `delegate` with the tier chosen above — the owner's call,
2026-10-23. The rule holds on every provider. The skill is in the `interactive` group, and where that
group lives and how a session loads it is `kensaiapp_structure.md` § Skills. When the session does not
have `agent-invoke`, the group is not loaded: suggest the owner load it before any agent starts, and
wait for the answer. If the owner declines, the work is done inline, never by the built-in agent. A
read-only search agent and a posture agent are not this case and start as before, and work a
launcher or a pipeline stage already owns keeps its own launch, as the skill's `when_to_use` says.

**Recording the model it ran on.** A no-slot run has no declared model to inherit, so the model it
*actually* ran must be self-reported in its commit — per `commit_format.md` §Filling the model. This
file owns *which tier* a no-slot run picks; that file owns *how* the chosen model is recorded.

The concrete no-slot runs today:

| Run | Model | Why |
|---|---|---|
| Ratification (`<CORE>/prompts/ratify_skill.md`) | Fable | an independent second opinion on a hardened skill version — must not run on the Opus that drove the hardening; a bare model-pinned session, no `--agent` |
| Audit launchers (`launch-audit.sh`, `launch-fix-author.sh`) | inherits | the session fans out to `kensaiapp-auditor` slots. Since 2026-09-29 that slot pins no model, so the auditors run on the provider's default; which model they should run on is not yet decided |
| `<CORE>/launchers/cold-read/launcher.sh` | provider default — not yet decided | it spawns `kensaiapp-auditor` slots directly, and since 2026-09-29 that slot pins no model. Which model a cold-read auditor should run on is not yet decided |
| Ad-hoc subagent (Agent tool / bg) | per task-shape | no slot to inherit — pick by where the judgment lives (above) |
| Eval executor (`run-skill-evals`) | the skill's own intelligence | measure the skill on the intelligence it ships with — see § Eval runs |
| Eval grader — structural | Haiku | one checkable transformation at volume — see § Eval runs |
| Eval grader — nuanced | Sonnet | applies a written criterion no pattern can approximate — see § Eval runs |
| Eval utility — plumbing | Haiku | writes a string the harness already composed, or runs a script and returns its stdout — see § Eval runs |
| Eval utility — `read-evals` | Sonnet | the one plumbing call whose slip is unrecoverable: it computes the next iteration number — see § Eval runs |

"Seal" is a different thing and not on this table: `tobiishi-seal` is the PM's terminal change-merge, a
chain skill whose intelligence is its own (`skill_intelligence.md`). Ratification is the skill-version
verdict; the two share neither a model nor a name.

## Eval runs

A `skill-evals` run spawns only no-slot agents — an executor per (case × arm), a grader per assertion
tier, and the utility agents that set the run up and record what it did — so every one of them is a
per-run choice. For the executor and the graders that choice is **part of the measurement**: a run whose
models are unknown cannot be compared to another run.

**The utility agents are plumbing, and are pinned cheap — explicitly, never inherited.** They neither
execute the skill nor grade it: they read `evals.json`, write files whose contents the harness has
already composed, and run `stage_fixtures.py` / `harvest_run.py` and hand back the output. That is "one
checkable transformation at volume", so it is Haiku work. The pin has to be written down rather than
left to inherit, because an unpinned agent takes the model of whatever session drove the run — which
makes a round's cost a function of its launcher instead of its work, and on the day a Fable session
drove one, put fourteen agents per run on the top tier to call `Write`.

`read-evals` is the single exception, at Sonnet, and only for this reason: it derives the next iteration
number as *highest + 1*, and `evals/workspace/` is gitignored, so an iteration overwritten by a
miscount is unrecoverable. Every other utility call can be re-run for free. The exception is bought by
the irreversibility, not by the difficulty — if that ever stops being true, the exception goes with it.

**The executor pins the model, not the agent slot.** A skill declares it in its own
`evals/evals.json` (`{"executor": {"model": …}}`), and the value is the model the skill's own
`intelligence/claude.md` declares (`skill_intelligence.md`) — the model it ships with. Both arms
get the same pin: the measured delta must isolate the skill, and a different brain per arm would
conflate the two.

Pinning the slot instead (`agentType: 'cto'`) is **wrong for a posture-gated skill**, and the reason
generalizes: an agent slot injects its loader stack before the task, and a role loader legitimately
restates what its skills do. For `product-srs` that stack names the companion filename, the two-file
loop and the done-signal — the very things the assertions grade — and names the skill's template and
prompt at paths *outside* `skills/`, which the baseline's "read nothing under `skills/`" does not
reach. A blind baseline under a role slot is not blind. Where a skill's posture gate is itself under
test, a real slot also satisfies the gate the case is built to withhold.

**Graders are tiered by the kind of check. This is not a quality ranking.**

| Tier | Model | Because |
|---|---|---|
| `structural` | Haiku | a binary, mechanical check — phrase present, file exists, count ≥ N |
| `nuanced` | Sonnet | applies a written criterion that no pattern approximates |

`structural` is the **preferred** tier — `skill-evals-creator`'s SKILL.md owns that rule and the
justification an assertion owes before it may be nuanced. It is cheap *because* it is mechanically
verifiable, and that is the same property that makes it preferred. **Do not "upgrade" the structural
grader.** Levelling the tiers erases the distinction the split exists to draw, and giving the
discouraged tier the better model creates an incentive to mark assertions nuanced — inverting the rule.

**A cheap grader will occasionally emit malformed output; that is an aggregation problem, not a model
problem.** The answer is a loud failure — the run reports the hole and exits non-zero — never a bigger
model bought to hide it. A silently dropped grading is worse than a slow one, because the benchmark
still prints a confident number for whatever parsed.

**Hold the graders constant across rounds.** They are the instrument, not the subject. Changing a
grader in the same round as the thing under test leaves the round unable to say which change moved the
result — the attribution control `kaizen/skills.md` § *Why every round starts clean* exists to protect.

**Recording.** The run writes its requested pins into `run_manifest.json` and the benchmark reports
them. These are *requests*, not runtime self-reports: per `commit_format.md` § Filling the model, a
model literal handed to an agent is the spawner's guess at what would run. A run that pinned nothing
records "unrecorded" rather than a guess.
