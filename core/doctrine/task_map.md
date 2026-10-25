---
version: "1.48.0"
---

# Task map — where to look, by what you're about to do

A routing index. Given a task you are about to perform, this says which doctrine governs it. The
one place a kensaiapp Claude reaches when it needs to *do* something and should know the rule
before acting — not after.

**What this owns:** the task → doctrine route. No other file holds that mapping. It deliberately
does **not** own what each doctrine says (the doctrine body owns that), nor where each file sits on
disk (`kensaiapp_structure.md` owns paths), nor the catalogue of what exists (`README.md` owns
that). This is `README.md`'s sibling — the same doctrine set, indexed by **task** instead of by
**subfolder**. Rows name doctrines by **bare filename**, resolvable via `README.md`, so a doctrine
that moves folders never breaks a row here.

**Keeping it current:** when a doctrine file is added, renamed, or removed, update this map in the
same commit — add a row if it governs a task, fix the bare name on a rename, drop the row on a
removal. A bare name here that resolves to no doctrine file is a bug in this map. (This is the
`single_source.md` index rule: an index owns the names of what exists, and drifts the moment the
set changes without it.)

**And the inverse, which costs more.** A task the system tells a session to look up here must
resolve to a **row**. A named trigger with no row is the same bug read from the other side, and
it is the worse half: the unresolvable name fails loudly at the file, while the missing row fails
silently at the lookup. The session consults the index exactly as instructed, gets nothing, and
proceeds as though no doctrine governs the task — which is indistinguishable, from inside, from
there being none.

For the salience hook that injects this map into every session and subagent, that invariant is now
**structural**: the hook derives its triggers from this table at run time rather than carrying a
copy of them, so a trigger it names is a row by construction and the two cannot drift. It was a
hand-maintained list of eight until 2026-09-02, and the boy-scout rule stayed invisible for exactly
as long as the list omitted it. Anything *else* that names a task — a skill, a prompt, a loader —
still owes its row here in the same commit.

**Some routes are reached by stumbling, and the map records which.** A trigger is normally
something you aim at: you know you are about to commit. A few are not — you do not decide to *find a
defect while walking*, and failing to notice is the very thing the rule exists to catch. A routing
index cannot deliver those, because consulting it is the step that never happens. Those rows carry
`unprompted` in the **Fires** column, and the hook reading this table injects them as standing rules
rather than as routes, so they bind a session that never thought to look here. The marker says **how
a route is reached** — never what its doctrine contains, which stays the body's per *What this owns*
above. It is per-row and not per-file on purpose: `kensaiapp_structure.md` governs six rows and only
one of them fires this way.

**A row pointing somewhere adjacent is worse than either.** An empty lookup and an unresolvable name
are visible dead ends; a plausible neighbour reads as answered, so the session stops looking. When
adding a row, read the destination's opening declaration and check it answers **this** task.

## The map

| When you're about to… | Consult | Layer | Fires |
|---|---|---|---|
| Commit anything | `commit_format.md` | governance |  |
| Set or change the model and effort a chain skill runs on | `skill_intelligence.md` | governance |  |
| Pick a model for an ad-hoc / `--bg` run, an `agent-invoke` run, or any run with no skill's intelligence file behind it | `model_assignment.md` | governance |  |
| Start a general-purpose agent from an interactive session — the skill that starts it instead, and what to do when that skill is not loaded | `model_assignment.md` | governance |  |
| Restate a fact that already lives in another file | `single_source.md` | governance |  |
| Cite one of our own records — a report, an audit, a handoff — for a load-bearing claim | `single_source.md` | governance | unprompted |
| Point at a journey artifact — a 根回し Nemawashi seed, a 宿場 Shukuba station, a 飛び石 Tobiishi | `single_source.md` | governance | unprompted |
| Give a scattered fact an owner, or propose a new file to hold one | `single_source.md` | governance |  |
| Write down a correction, or decide whether one belongs in doctrine or in the corrections store | `corrections_store.md` | governance |  |
| Run a destructive or history-rewriting git operation, or stage for a commit | `commit_format.md` | governance |  |
| Copy a file into a repository that is not the run's own, or commit there | `commit_format.md` | governance |  |
| Merge a branch to `main` — what the branch owes first, who may authorize one, and what the merge commit carries | `commit_format.md` | governance |  |
| Find a defect while walking (the boy-scout rule) — decide whether it is fixed on this branch, cut as a seed and walked before the merge, or sent to `main` | `found_while_walking.md` | governance | unprompted |
| Write a file's own status, note what is unbuilt, or record why something was rejected | `written_forward.md` | governance |  |
| Classify, structure, or revise a doctrine item | `doctrine_structure.md` | governance |  |
| Finish a file that states a rule — check it against its own rule | `doctrine_structure.md` | governance | unprompted |
| Decide whether an artifact carries a `version:`, or bump one | `versioning.md` | governance |  |
| Draw the line between an AI-driven decision and a mechanical rule | `ai_responsibility.md` | governance |  |
| Decide where an aesthetic call may be made, or what a document that does not own it may say | `where_taste_appears.md` | governance |  |
| Write a document derived from an upstream one that is `Draft`, or unreadable in status | `unsettled_inputs.md` | governance | unprompted |
| Name a real product as a case or fixture in a file under `core/` or a symlinked `.claude/` layer | `setup/shared_core_instance.md` | setup |  |
| Reason about the system's layers and dependency direction | `system_anatomy.md` | governance |  |
| Run a change through the pipeline | `development_flow.md` | flow |  |
| Hand off between flow steps / let the orchestrator derive sequencing | `folder_state_handoff.md` | flow |  |
| Report a flow step's outcome to the orchestrator | `step_outcome_contract.md` | flow |  |
| Classify a change on the two axes | `change_classification.md` | flow |  |
| Author a skill, a prompt, an agent file, a loader, or a launcher — what may be written in each | `authoring_layers.md` | setup |  |
| Point from an instruction, skill, prompt, loader, agent, or launcher into shared core | `kensaiapp_structure.md` | setup |  |
| Author a language's skeleton tree — the frame a product of that language is stamped with, and which packet fixes each choice | `engineering/languages/README.md` | engineering |  |
| Harden a skill | `skills.md` | kaizen |  |
| Author or revise a skill's eval cases | `skills.md` | kaizen |  |
| Bump a skill's `version:` | `skills.md` | kaizen |  |
| Pick the lens or job for a kaizen audit | `lenses/README.md` | kaizen |  |
| Author or apply a decided fix | `fix_packet.md` | kaizen |  |
| Ratify a skill — record a verdict, freeze its evidence, or claim a stack is ratified | `ratification.md` | kaizen |  |
| Draw on a product's architectural defaults | `arch_defaults.md` (+ `arch_defaults_python.md` for Python) | engineering |  |
| Apply a quality floor the SRS did not state | `quality_defaults.md` | engineering |  |
| Write tests (the layer model / its Python implementation) | `testing_doctrine.md` / `testing_python.md` | engineering |  |
| Record versioned worked examples of how a skill behaves | `skill_evidence.md` | engineering |  |
| Write, fix, or review code — in any language, before knowing which | `languages/README.md` | engineering |  |
| Scaffold or audit an instance's file tree | `kensaiapp_structure.md` | setup |  |
| Repair a reference to a path this instance no longer uses — parked, renamed or absorbed | `kensaiapp_structure.md` | setup | unprompted |
| Add a role — its posture, overlay, agent, and every registration | `adding_a_role.md` | setup |  |
| Author a hook | `kensaiapp_structure.md` | setup |  |
| Author an ad-hoc plan, or decide which of its two homes it belongs in | `kensaiapp_structure.md` | setup |  |
| Pick the active 根回し Nemawashi seed, or un-pick one | `kensaiapp_structure.md` | setup |  |
| Split a picked seed into the 宿場 Shukuba stations that will be walked | `kensaiapp_structure.md` | setup |  |
| Open a station, close a reached one, or park an unreached one | `kensaiapp_structure.md` | setup |  |
| Open a 飛び石 Tobiishi change unit, or seal one | `kensaiapp_structure.md` | setup |  |
| Refine a project's route after a change unit lands — re-read it against what the unit left | `kensaiapp_structure.md` | setup |  |
| Retire a walked 根回し Nemawashi seed, or drop a killed one | `kensaiapp_structure.md` | setup |  |
| Answer a retired 根回し Nemawashi seed — its recommendations and the seedbed behind it | `kensaiapp_structure.md` | setup |  |
| Set up / onboard a new managed project | `kensaiapp_structure.md` | setup |  |
| Stop a managed project — settle it, or take it out of service | `kensaiapp_structure.md` | setup |  |
| Set up an instance — walk the setup sequence, or read an ordering rule it fixes | `setting_up_an_instance.md` | setup |  |
| Author or revise an instance's own doctrine — its domain rules, its AI-responsibility boundaries, or the meta-layer that classifies them | `setting_up_an_instance.md` | setup |  |
| Define a product — walk the definition sequence, or author one of its documents | `setting_up_a_project.md` | setup |  |
| Decide whether something belongs in a product-definition document — when a thing gets built, which change unit carries it, or a source an entry may cite | `setting_up_a_project.md` | setup |  |
| Know what a stamper may create or modify | `setup_scope.md` | setup |  |
| Revise an instance that was already stamped — bring a file forward against its template, or learn what may not be touched | `setup_scope.md` | setup |  |
| Stand up or work on a sibling instance that reads another's core | `shared_core_instance.md` | setup |  |
| Change a hook, `settings.json`, workflow, or agent file in a host's `.claude/` — know which satellites it reaches | `shared_core_instance.md` | setup |  |

The map routes by task and names the governing doctrine; it is the full set, extended as doctrine
grows. It intentionally omits the parked `sandbox.md` (publish-excluded).
