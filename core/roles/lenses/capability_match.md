---
version: "1.1.2"
---

# capability_match — the agent file does not permit what the loader requires

A seat is described in two files that are never read together. `core/roles/loaders/<role>_global.md`
states what the seat does. `skills/<role>/.claude/agents/<role>.md` states the tools it holds. Nothing checks that the second permits the first. **The tell is a loader verb with no tool behind
it** — a seat told to edit, to search the web, to converse with another seat, whose agent file grants
no such tool.

The failure is silent in the worst way: the run does not refuse, it improvises. A seat that cannot edit
rewrites the whole file; a seat that cannot reach another seat writes what it would have asked.

## What this lens reads

For one seat, exactly two files, plus the two that say what the pair must contain:

- `core/roles/loaders/<role>_global.md` — the posture, read for its verbs.
- `skills/<role>/.claude/agents/<role>.md` — the `tools:` allowlist.
- `system/loaders/<role>.md` — the overlay, which may add instance-specific work.

## The question

**For every action the loader requires of this seat, does the agent file grant a tool that performs
it?**

## What the shape looks like

| The lens finds | Which is a defect when | Must not |
|---|---|---|
| A loader verb requiring a tool the `tools:` list omits. | The verb is a requirement, not an example. | Infer a tool requirement from a verb used figuratively — "read the room" is not `Read`. |
| A seat designed to converse with another seat, with no inter-agent tool in either allowlist. | Both loaders describe the exchange as happening within a run. | Report a handoff through a committed file as a missing conversation; a file handoff needs no such tool. |
| A seat that must revise an existing document, holding `Write` but not `Edit`. | The revision is described as folding into an existing file. | Report it as fatal — a whole-file `Write` can stand in, at a cost worth naming. |
| A tool granted that no loader verb needs. | Nothing in either loader or overlay reaches for it. | Report a galaxy-wide grant as seat-specific excess. |

## Evidence this shape is real

**Instance one — the whole galaxy, measured 2026-08-25.** No role agent holds any inter-agent messaging
tool. Read across the thirteen role agents:

```
grep -H -E '^(name|tools):' skills/{architect,cdo,content-manager,cpo,cto,developer,pm,principal-architect,principal-pm,product-owner,qa,senior-engineer,tech-lead}/.claude/agents/*.md
```

Three of those seats are designed to work one run together —
`core/roles/loaders/cto_global.md:53` reads "**The SDD — one run, three seats: you, the CPO and the
CDO.**" Their allowlists in `skills/cpo/.claude/agents/cpo.md`, `skills/cto/.claude/agents/cto.md` and `skills/cdo/.claude/agents/cdo.md` are identical and contain no tool by which one reaches another.

**Instance two — one seat, found by this lens.** `skills/content-manager/.claude/agents/content-manager.md` grants
`Read, Grep, Glob, Write, Bash, Skill, WebSearch, WebFetch` and two MCP servers, with no `Edit`. The
seat's whole subject is revising existing words:
`core/doctrine/governance/commit_format.md:122` calls it "the delivery-tier role that owns the product's
**words**: whether content is needed, where it belongs, and how it is worded." Of the thirteen role
agents, eight hold `Edit` — architect, cdo, cpo, cto, developer, pm, senior-engineer and tech-lead
(re-measured 2026-09-06) — and the seat named for editing is not among them.

Two instances of different kinds, one galaxy-wide and one seat-specific, is the shape.

## What this lens may not assert

- **That a missing tool is a mistake.** A narrow allowlist can be deliberate containment. The finding
  is that the loader and the agent disagree, and the resolution may be to narrow the loader.
- **That a tool grant is seat-specific.** A grant may be galaxy-wide by decision and identical across
  every agent; that is a property of the galaxy, not evidence about this seat.
- **Which model a seat should run on.** A seat runs on no model of its own: the skill it runs sets the
  intelligence (`core/doctrine/governance/skill_intelligence.md`), so the question is not this lens's.
- **That a capability exists because a skill provides it.** A skill runs inside the agent's allowlist
  and cannot exceed it, so a skill naming an action does not establish that the seat can perform it.

## Reporting

One finding per unmet action, not per seat. Each carries the loader's requirement quoted, the agent's
`tools:` line verbatim, and which of the two the finding proposes be read as authoritative — proposed,
not decided. A finding that holds for every seat in the galaxy says so, and is reported once with the
seats listed, because eleven copies of one finding is a list nobody reads.

## The lens ran clean when

- every verb in the loader and the overlay was tested against the allowlist, not only the verbs in the
  responsibilities section;
- every finding names both files and proposes rather than decides;
- a galaxy-wide finding is reported once rather than per seat;
- the lens says so explicitly when it found nothing.
