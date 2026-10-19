---
version: "1.13.2"
---

# Authoring the machinery

Governs **what may be written into a kensaiapp's own machinery** — agent files, loaders, skills,
prompts, launchers. Each is a **carrier** (stamped, shared, read first) or a **body** (authored once,
read on demand). A builder who does not know which one they hold writes the body's content into the
carrier.

> **Owns:** which of the two a file is, and what may be written in it. **Does not own:** paths
> (`kensaiapp_structure.md`), the order of the steps of adding a role (`adding_a_role.md`), hardening
> a skill that exists (`kaizen/skills.md`), a skill's intelligence (`skill_intelligence.md`), a no-skill run's model (`model_assignment.md`).

The machinery instance of `governance/single_source.md`, which owns why a copy drifts.

---

## The rule

**Every carrier is thin and points at exactly one body.**

Exactly one is the load-bearing half: a carrier pointing at two must say which governs where they
disagree, and saying that is teaching.

## Why a teaching carrier fails harder than a copy elsewhere

- **Stamped** — agent bodies are substitution-identical (`agent_template.md:12-15`), so a sentence
  added to one diverges from every other and from the template that stamps the next.
- **Read first, by a reader who then stops** — the registry surfaces an agent's `description` before
  any loader (`agent_template.md:29-31`). A taught carrier means the body goes unread.
- **Different change rates** — mechanics change with the pipeline, authoring content every kaizen
  round. Cohabiting, the fast side accretes into the slow side's file, and a rebuild resets the line
  count without changing that.

---

## The carriers

| Carrier | Body | Which file owns this pair |
|---|---|---|
| `skills/<role>/.claude/agents/<role>.md` | the loader stack | `adding_a_role.md` § Step 4, and `agent_template.md`'s block |
| `skills/interactive/.claude/agents/delegate.md` | `<CORE>/roles/delegate_contract.md` | declared both sides, at `delegate.md`'s body and `delegate_contract.md`'s opening |
| `system/loaders/<role>.md` | `<CORE>/roles/loaders/<role_file>_global.md` | `adding_a_role.md` § Step 3, and `overlay_template.md`'s block |
| `.claude/skills/<name>/SKILL.md` | the skill's own `prompts/<name>.md` (`rich.md` for an authoring body), `<CORE>/prompts/<name>.md` when more than one skill reads it, or `.claude/workflows/<name>.js` | below |
| `<CORE>/launchers/<name>/launcher.sh` | the skill, lens, or `.claude/workflows/<name>.js` it invokes | below |

Ownership is **declared** on both sides, never inferred — `single_source.md:15-17` makes the
declaration load-bearing. A file that declares nothing has not adopted the rule; it has happened to be
short.

The two stamped pairs — the role agent and its overlay — are stated where they fire, at the moment of
stamping; read them there. The two at the foot of the table have no other owner and are stated below.

**One agent has a body that is not a loader stack** — `delegate` — because it holds no posture to
load, and it is in the table for that reason rather than as an exception to it. What it points at
is what it is: `delegate` is one agent serving many tasks, so its body is a contract. An agent
with no body has nowhere to put what it owes, so it accretes into the carrier: before its contract
existed, `delegate.md` was 79 lines of method — the largest agent file in the galaxy, and the rule's
clearest violation. Loader or not, a carrier points at exactly one body.

**A posture-free agent is not a seat, and nothing may read it as one.** `delegate` carries a `tools:`
grant, which is the whole of what it is — no chair, no `Role:`,
no loader. A reader that derives a seat from a launcher's `--agent` value must satisfy itself that the
name has a loader behind it — its global loader, `<CORE>/roles/loaders/<role_file>_global.md`, the
body every seat's overlay points at (the table above), and the one copy a pinned run carries; the name
alone cannot tell a seat from a tool grant. `<CORE>/launchers/companion-self-answer/launcher.sh` is the one reader doing this today and
states the check where it makes it.

**The skill and its prompt** — skill = orchestrator (posture, file loop, commit mechanics); prompt =
thinking (diagnostic, contracts, principles); template = section shape. Declared both sides at
`skills/cpo/.claude/skills/product-prd/SKILL.md:26-32` and `skills/cpo/.claude/skills/product-prd/prompts/rich.md:11-18`. The test for
which side a sentence falls on is `kaizen/lenses/locate_layer.md` § *Read the layer as it stood*,
which states it as the boundary test — applied here before writing rather than after a defect.
Not every skill earns a prompt: the trigger is the change-rate mechanism above, not size.
*Tell:* a numbered principle or quality bar in a SKILL.md.

**The launcher** — hands the run what only the launcher knows: which skill or lens, which file, which
version, which of N parallel readers, where to write. Never the method. **Not a length rule:**
`skills/cdo/.claude/skills/product-design/launcher.md`'s `**Prompt:**` sends one line, while
`cold-read/launcher.sh:296` composes a page and is equally thin — every sentence is a derived value,
and each says so in its own text (*"never free prose"*; *"nothing here restates either of them"*).
Fan-out shape is the launcher's own, because only the thing that spawned N readers knows there are N.
*Tell:* a sentence that would still be true on the next run.

**The workflow** — a saved Workflow script is a **body**, never a carrier, and that is the answer to
the question its shape invites. It looks like a carrier: `meta` is a read-first metadata block, the same
shape `agent_template.md`'s `description` has. It is not one. A carrier's whole reason is `:33-35` —
mechanics and authoring content change at different rates, so they live in different files — and `meta`
points at nothing outside its own file. It is the harness's routing key
(`kensaiapp_structure.md` § Workflows), not a second layer.

So the workflow's stage prompts are the body, and they are literal on purpose:
`ad-hoc-flow.js:24-26` at `a01eb180` (retired 2026-09-18) — *"This workflow is the single place these instructions live. A stage prompt
composed by whatever session happened to start the flow is exactly the leak an owner-run launcher exists
to prevent, so the launcher passes structured identifiers and nothing else."* Its launcher declared the
same boundary from the other side, and its whole prompt was three identifiers plus *"Do only that"*
(`ad-hoc-flow/launcher.sh:250`, same commit) — declared both sides, per the rule above.

The carrier pointing at one is therefore a row the table already has, which is why a workflow adds no
sixth row. Both kinds are in live use: `eval-fix.js` ← `launch-eval-fix/launcher.sh:188` is the thin
trigger — a launcher whose whole job is invoking its one workflow. `run-skill-evals.js` ←
`skills/experimental/.claude/skills/skill-evals/SKILL.md:110-113` is the other kind, and the one to
read carefully: at 236 lines that skill is not a thin trigger over its workflow — it invokes one as
**a step**, with verification and aggregation of its own around it. A carrier points at one body; a
skill that calls a workflow mid-run is doing something else, and the two are not the same relation
even though both reach a `.js` file by name.
*Tell:* a stage prompt that arrives as an argument. If what the agent reads was composed by the session
that started the flow, the method has left the file that owns it.

---

## A skill folder with more than a SKILL.md in it owes a README

**The trigger is kensaiapp's: a skill carrying `evals/` or `agents/`, or one that invokes another
skill, owes a `README.md` beside its `SKILL.md`.** A skill that is a single file owes none — its
frontmatter `metadata:` map is the whole record, and a README there would be metadata with a longer
name.

The reason is that those three things are the parts a reader cannot see from the SKILL.md. Frontmatter
describes the skill to a model deciding whether to trigger it; a folder of fixtures, a sub-agent, or a
dependency on another skill is repo structure, addressed to a person deciding whether to touch it.
`SKILL.md` is written for the first reader and makes a poor second.

**What sections it carries is `skill-creator`'s**, which is Anthropic's and generic (§ *What this is
not*): a lead paragraph saying what problem the skill solves, what it does, its file structure, what
it depends on, and when to use it. Adopted rather than restated — a copy of a vendor's shape drifts
the first time the vendor moves it, and this rule is about *whether* a README is owed, which is ours.
Where the vendor's list and a skill on disk disagree, the skill is the thing that changed late.

Stated on 2026-08-17, when three skills carrying `evals/` had no README and nine did — a convention
that was being followed without being written anywhere, which is the state where the next author
re-decides it.

## Positional `$N` is reserved in a skill body

**A `SKILL.md` body never carries a positional shell variable (`$0`–`$9`); a snippet that needs a
positional field names a variable or uses a form without one.** When the Skill tool is invoked with
`args`, the loader substitutes each `$N` token in the body with the corresponding whitespace-split
word of that string — `$0` the first word, `$1` the second — before any reader sees it; named
variables (`$REPO_ROOT`), `$(…)` command substitutions, and every token of an args-less invocation
pass through untouched. Measured 2026-08-20 by controlled invocations, after
`tobiishi-seal/SKILL.md:86`'s `awk '{print $1}'` reached the subagent sealing a real change as
`awk '{print change}'` — its `args` began `"Seal change …"`, and `$1` took the second word. The
snippet silently produced an empty variable, and the reader's reasonable reaction — treat the skill
as buggy and improvise around it — is why an altered snippet is worse than a broken one.

## The improve clause has one home, decided by tier

Loader for a delivery role, authoring prompt for an executive one, never both.
`global_loader_template.md:22-31` owns the split, the clause's five required parts, and the
no-prompt-yet case; `adding_a_role.md:37-39` points at it.

## A skill that acts unattended gates to its seat

**A skill that reaches its output without the owner in the room halts outside the posture that owns
the judgment.** A skill that ends in an owner pick does not need one: the person answering is the
check, and a gate there only refuses a seat the owner has already overruled by being present.

**The test is the run's own stopping point, not its subject.** Ask what the run does when nobody
answers. If it writes and commits, its judgment is the seat's and the seat is checked. If it waits,
the wait is the check.

The gate reads the same in every skill that has one — halt at once, say the posture is wrong, and
name the way in — and the seat's loader names the skill back, so the pair is declared on both sides
the way § *The rule* requires of any carrier.

**Codified 2026-09-06, off a case that crossed the line mid-life.** `tobiishi-open` carried a soft
nudge — *"note it and continue"* — for as long as it ended in an owner pick. The day its primary
path stopped asking, the nudge became the only thing standing between any seat and a committed
change request, and it was replaced by the gate. **So the trigger is a change in how a skill stops,
not a change in what it produces** — a skill that drops a question has acquired an obligation, and
nothing else in its file will say so.

## What this is not

- **Not a delivery mechanism.** `.claude/settings.json` already fires `task_map_salience.py` in both
  its `SubagentStart` and `SessionStart` arrays; the map routes here. (Named by array rather than by
  line: the line numbers this cited drifted twice as hooks were added around them, most recently on
  2026-09-02.)
- **Not a fork of `skill-creator`**, which is Anthropic's and stays generic. This says what a
  kensaiapp skill may contain; a run reaches it through the map and the invoking brief.
- **Not a list of each file's contents** — that is the copy this file exists to name.
