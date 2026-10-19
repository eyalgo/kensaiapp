---
version: "1.2.2"
---

# System anatomy — brain, hands, skeleton, muscles, reflexes

The mental model the rest of the system instantiates. Five layers, each with one job. The
load-bearing rule is the dependency direction: **each layer may depend downward but never names
upward.** Orchestration knowledge lives in one layer; every other layer is ignorant of it.

---

## Ratification status (2026-06-22)

**Ratified by Product as the conceptual frame — LIVE doctrine.** The five-layer model and the
downward-only dependency rule stand as the model the rest of the system instantiates. Caveat: the
**reflexes layer** (write-scope hook) and **lanes** describe machinery the PoC does not build yet —
they are forward-design → [[orchestrator-hardening]]. The framing is ratified; those two
instantiations land later.

---

## The five layers

**Brain — decides.** Two parts, bound from two different places. **Knowledge** is the standing
context: role loaders (global + project overlay), `AGENTS.md` and `kensaiapp.md` context, `CROSS_ROLE.md`, and the
doctrine. It knows what is true and what good looks like, and it arrives through the role. The
knowledge is *loaded, not embedded* — agent definitions are thin pointers to it (see the role agents, each in its group at `skills/<role>/.claude/agents/<role>.md`). That thinness is a runtime fact here; what may be written into a pointer, and
what belongs in the body it points at, is `setup/authoring_layers.md`. **Intelligence** is the model
and the effort it reasons at. It arrives through the work: the skill being run declares it, not the
role running it (`skill_intelligence.md`).

**Hands — execute capabilities.** Skills and tools. Pure effectors: a skill states *what to do*
and reads its arguments (`$ARGUMENTS`), nothing more. A hand does not know which body wields it or
how it is isolated. It is invokable identically by an interactive `prefix:` session, by a human
typing `/skill`, or by the orchestrator.

**Skeleton — holds the shape.** The static structure that defines what connects to what and
constrains range of motion, but does not act on its own: the **agent definitions** (role slots),
the change-folder + lane layout, the pipeline manifest (`development_flow.md` § The stages), and the handoff contract
(`folder_state_handoff.md`). The skeleton defines *where* movement is allowed; it is the frame
muscle attaches to.

**Muscles — move work through the frame.** The orchestrator and the *live subagent instances* it
spawns. The orchestrator reads folder state and decides the next contraction; each running
subagent is a contraction that advances artifact state along the skeletal pipeline. Force, not
form. **All orchestration knowledge lives here** — sequencing, fan-out/fan-in, spawning, retries,
halts.

**Reflexes — enforce automatically.** Hooks. They fire on events (`PreToolUse`, `TaskCreated`,
`TaskCompleted`, `TeammateIdle`) and can veto by exiting non-zero. They hold the skeleton's
constraints and stop bad motion regardless of what the brain reasoned — e.g. the write-scope guard
that rejects a lane writing outside its declared files.

---

## Component map

| Component | Layer |
|---|---|
| Intelligence — model + effort, declared per skill in `<skill dir>/intelligence/<provider>.md` | Brain |
| Role loaders, `CROSS_ROLE.md`, `AGENTS.md`, `kensaiapp.md`, doctrine — as *knowledge* | Brain |
| Skills, tools | Hands |
| Hooks | Reflexes |
| Agent definitions (`skills/*/.claude/agents/*.md`) — role slots | Skeleton |
| Change-folder / lane layout, pipeline manifest, `folder_state_handoff.md` | Skeleton |
| Orchestrator + live subagent instances | Muscles |

The doctrine that *describes* a structure (manifest, handoff contract) is brain-knowledge by
content but skeleton by what it shapes; this is not a contradiction — the brain reads the contract,
the skeleton is the shape the contract imposes.

---

## Constraints (standing rules)

**A subagent spans skeleton and muscle — definition vs. invocation is the line.** The agent
*definition* (`skills/tech-lead/.claude/agents/tech-lead.md`) is skeleton: a fixed role slot, a bone where a capability attaches. The *running instance* is muscle: a contraction that does work. This is why
"subagents" felt like they belonged to two layers — they do.

**Intelligence follows the work, not the worker.** A role and its agent definition are context:
posture, trusted documents, tools and authority. A skill and its prompt are the work. How much
intelligence a run gets — model and effort — is set by the work, so an agent definition carries no
`model:` and a skill carries its own intelligence file. The owner's call, 2026-09-29; the mechanics
are `skill_intelligence.md`'s. Declaring intelligence does not break the rule below: an intelligence
file says what the work needs, never which body runs it.

**Hands are orchestration-blind. A skill carries no `context: fork` and no `agent:`.** A skill
states its procedure and reads `$ARGUMENTS`; it never declares which body runs it or how it is
isolated. Those are muscle decisions: the orchestrator's spawn call (`Agent`/`Task`) carries
`subagent_type` (which body) and the isolation (the subagent itself), and its prompt names the
skill and the lane. Binding fork/agent into the skill would make a hand reach into the skeleton —
the coupling this layering exists to prevent. *(Decision locked this session.)*

**Each layer depends downward, names upward never.** The brain reasons over knowledge; a hand does
not know the brain that called it; the skeleton does not know which muscle moves it; a skill does
not know it is running in a fork. This is the same producer-ignorant principle that runs through
the whole system (`folder_state_handoff.md`: producer ignorant of successor) — generalized to every layer.

**Orchestration is a single layer.** Sequencing, fan-out/fan-in, forks, retries, and halts live
in the muscles (the orchestrator) and nowhere else. A subagent cannot spawn a subagent, so any
fork originates one level up. Every other layer is built to not know the pipeline shape.

---

## Relationship to the other pipeline docs

- `folder_state_handoff.md` is the skeleton+muscle contract: the folder/lane layout is skeleton,
  the orchestrator that derives state from it is muscle.
- `development_flow.md` § The stages is skeleton — the static stage list muscle moves work along.
- Role loaders (brain-knowledge) attach to agent definitions (skeleton slots); this file frames why.
- `skill_intelligence.md` is the brain's other half — the intelligence a hand's work declares.

This document is the framing layer; the others are its instantiation.

---

*Drafted 2026-06-19. **Ratified by Product 2026-06-22** as the conceptual frame (reflexes + lanes
forward-design → [[orchestrator-hardening]]; see Ratification status, top). Sibling to
`folder_state_handoff.md`; promote to `system/doctrine/` if it should sit above the pipeline rather
than within it.*
