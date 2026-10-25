---
version: "1.31.1"
---

# Project doctrine directory

Standing rules the running system operates under. Distinct from the project's ADR directory (point-in-time decisions, binding from ratification) and historical findings directory (non-binding).

## Contents — by subfolder

Each subfolder groups doctrine by **what it governs**. (References use **bare filenames** as names,
resolvable via this index — they are not all relative paths.)

### `governance/` — how the system governs itself
- `commit_format.md` — how this system uses git: the commit message (trailers, Shukuba/Role/Surface) **and** the operations that produce it (the staged-set guard, never `cd` to run git, destructive ops name an explicit SHA)
- `commit_via_builder.md` — the recipe a producer skill or a prompt-reading session follows to commit through `commit_builder.py`: the flags, the identity, the stage list. Puts `commit_format.md` into practice; it states no rule of its own
- `single_source.md` — a fact has one owner; every other file points. Governs every written artifact, this index included
- `written_forward.md` — a file states what is true now: no self-narration, no build-state claim, rationale kept as a constraint rather than a story. `single_source.md` across time rather than across files
- `corrections_store.md` — the per-instance corrections store holds session-craft, this set holds rules about the system; a craft lesson the system needed more than once graduates and leaves the store. `single_source.md` across two stores
- `doctrine_structure.md` — how doctrine is structured, classified, revised (the meta layer)
- `versioning.md` — which artifacts carry a `version:` and which must not (who reads the file decides), the marker's form per kind, and the bump semantics
- `skill_intelligence.md` — a chain run's model and effort are set by the skill it runs, never by the role: each skill's `intelligence/<provider>.md`, in that vendor's terms; a missing file refuses the launch
- `model_assignment.md` — the four Kensaiapp tiers and their provider bindings, and how a run with no skill behind it (ratification, ad-hoc subagents, `agent-invoke`, eval executors and graders) chooses its model — why by tier — and that an interactive session starts a general-purpose agent through `agent-invoke`
- `ai_responsibility.md` — the AI-driven-decisions vs mechanical-rules boundary (OS-level body)
- `unsettled_inputs.md` — a run derived from an unsettled input never halts, records every input and the status it carried, in one fixed header line; why a companion escalation is not a record
- `where_taste_appears.md` — the aesthetic call is made in the run that owns it and never upstream; what a document that does not own the call may say instead
- `found_while_walking.md` — what happens to a defect found on a branch while walking something else: fixed in place, or cut as a seed and walked before the merge. Informally, the boy-scout rule
- `talking_to_the_owner.md` — how a reply to the owner reads: the answer first, in plain words, then a few short lines of why, then what happens next, and the evidence last
- `system_anatomy.md` — the mental model the rest of the system instantiates (5 layers; dependency direction). *(Agreed to promote to a top-level `core/` doc later — deferred 2026-06-29.)*

### `flow/` — the change pipeline
- `development_flow.md` — the change pipeline: the loop + the stages
- `folder_state_handoff.md` — handoff via folder state; the orchestrator derives sequencing
- `step_outcome_contract.md` — how a flow step reports its result to the orchestrator
- `change_classification.md` — the two-axis classification of a change run through the flow

### `kaizen/` — how a thing earns its quality after it exists
- `skills.md` — the loop that hardens a skill against a real case, round by round, and what a skill's
  `version:` moves by
- `lenses/` — the lenses and jobs a round audits with; one file each, loaded by the auditor agent.
  The set is `lenses/README.md` § The set — an index owns the names of what exists, not the contents
  of what it names, and this list drifted the day a job was added.
- `fix_packet.md` — the document that carries a decided fix from the author who wrote it to the fixer
  who applies it; the handoff contract both sides read
- `ratification.md` — what the owner's "ship it" costs: the preconditions, the verdict's one home, the
  three places a ratification is recorded, and what a later version bump ends

### `engineering/` — craft standards: how code (and our skills) are built
- `arch_defaults.md` — language-agnostic structural patterns the Principal Architect draws on
- `arch_defaults_python.md` — their Python spellings, the overlay to the file above
- `quality_defaults.md` — the universal quality floors an NFDR realizes, cited as their provenance
- `testing_doctrine.md` — the 7-layer test pyramid
- `testing_python.md` — Python implementation of the testing layers
- `skill_evidence.md` — versioned worked examples of how a skill behaves across versions
- `languages/` — the per-language engineering-practice family: the language registry, the fixed
  concern set, resolution, precedence, lifecycle, and the audit that keeps each router honest

### `setup/` — how an instance is structured + scaffolded
- `kensaiapp_structure.md` — the instance file-tree manifest (single source for the structure)
- `authoring_layers.md` — which machinery files are thin carriers and which are the bodies they point at, and what may be written in each
- `adding_a_role.md` — the ordered closure of adding a role: the posture pair, the overlay, the agent and its four registration surfaces, and the enumerations of the role set that are invisible from the loader directory
- `setting_up_an_instance.md` — the sequence an instance is set up by: stamp, then identity + Michi, then the experience layer; what fixes the order, and the three standing rules of instance setup
- `setting_up_a_project.md` — the sequence a product is defined by: scaffold, then the stations (PRD → Agari → SRS ∥ EXPERIENCE → SDD), who authors each, which are runnable today, and what a definition document may not say
- `setup_scope.md` — what a stamper may create/modify, and the drift criteria
- `shared_core_instance.md` — how an instance can read another's core instead of carrying its own (the shared-core sibling; a producer satellite's shape)

### flat (parked)
- `sandbox.md` — sandboxed autonomous-run doctrine (publish-excluded; host layout map)

### top-level — cross-cutting index
- `task_map.md` — the same doctrine set indexed by **task**: what you're about to do → the doctrine that governs it. Sibling to this by-subfolder index; owns the task→doctrine route and nothing else

## Runtime-contract framing

`AGENTS.md` is the runtime contract / execution kernel. It loads on every session and carries the minimum viable cognition required for stable reasoning. Doctrine bodies in the project's doctrine directory are loaded on demand.

`AGENTS.md` carries **contract-shape stubs only**; full doctrine lives in the project's doctrine directory. When `AGENTS.md` feels heavy, the trim moves doctrine bodies there and keeps contracts in `AGENTS.md` — never the reverse. Which of the two is canonical when they disagree is `doctrine_structure.md` § Consistency model.

## Cognitive sufficiency

The controlling principle for `AGENTS.md`'s size is **cognitive sufficiency** — the file should carry enough that a session can operate without immediate fetches, not less. Smaller files that break reasoning are worse than larger files that preserve behavior. Future hygiene passes measure against this principle, not against an arbitrary line count.

## Stub-vs-body drift hygiene

The rule the stub and its body answer to is `doctrine_structure.md` § Consistency model. This section owns only **when the check fires and what it costs**.

**Trigger:** any commit that modifies a project doctrine file is a drift-check trigger. The same commit (or an immediate follow-up commit, same session) must verify the corresponding `AGENTS.md` stub still summarizes the body correctly. Two outcomes:
- **Stub still agrees** — note in commit body: "drift check: AGENTS.md §<stub> still consistent with <doctrine-file>."
- **Stub diverged** — update the stub in the same commit (or immediate follow-up). Drift discovered and not fixed in the same session is itself the hygiene bug.

**Why event-based primary, time-based fallback:** doctrine bodies don't change often, but when they do, drift is most likely in the same window. Per-commit catches the high-risk moments cheaply; a quarterly fallback catches whatever the per-commit pass missed (e.g., a stub bullet that became technically still-true but no longer load-bearing).
