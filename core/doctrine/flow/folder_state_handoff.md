---
version: "1.12.0"
---

# Handoff via folder state

How a change moves through the pipeline. The change folder is the handoff medium; the
orchestrator derives sequencing from it. Roles never route.

Canonical stage list (roles, skills, artifacts) lives in `development_flow.md` § The stages — this
document references it rather than restating it, and owns only the **handoff mechanism**.

---

## Ratification status (2026-06-22)

**Ratified by Product — the linear/happy-path slice is LIVE doctrine; the rest is forward-design,
parked → [[orchestrator-hardening]].** The PoC orchestrator (roadmap step 2) runs the happy-path
linear arc with no `_flow.md` ledger: the merge commit is the terminal marker and `development-audit` is
observability-only. The live slice is the blackboard model plus happy-path derivation; the parked
machinery (the ledger, retry/loopback routing) stays in this document as forward-design and is tagged
in place. **Parallel lanes are partly live** — the chain launches one `development-audit` run per
audited step (`chain_development.py`'s `Step.fans_out_over`, launched by `DevelopmentChain._launch_step`),
each on its own branch (`ChangeLayout.audit_branch`), each outcome recorded by
`DevelopmentChain._settle_audit` and the branches joined into the change branch at `tobiishi-seal`
(its Step 1b); every other parallel lane remains forward-design (the table row below
states that).

| What | Status |
|---|---|
| Blackboard model — folder = source of truth, roles pure functions | **LIVE** |
| Stage sequencing — happy-path order (specs→design→planning→content→executing→integrity→done) | **LIVE as a fixed linear sequence, by two routes.** `core/launchers/chain-development/` and `core/launchers/chain-change/` (one engine, `core/tools/chain_development.py`, holding a step table each) **derive** it: a step is done when its artifact is on disk — the folder artifacts § State is derived, not tracked names, the `Publishes text:` line that passes or runs the content step, the developer's closing marker for the code stage, each audit's findings on its own branch, the sealed folder under `trail/` — and a walk enters at the first step whose artifact is missing, applying the bad-verdict and explicit-restart rules in § State is derived, not tracked |
| Roles orchestration-blind | **LIVE** |
| Orchestrator owns sequencing/spawning | **LIVE** |
| Halt-and-surface on hard failure (subagent error / red suite) | **LIVE** |
| Supersedes / leaves-intact + migration | **LIVE** (partly done via thin-loaders + qa-out) |
| The `_flow.md` ledger (whole section) | ⏸ forward-design (terminal marker = merge commit) |
| Retry / loopback routing | ⏸ forward-design |
| Parallel lanes | **LIVE** for `development-audit`'s fan-out — four runs, five when the change publishes text — the chain launches one run per audited step (`chain_development.py`'s `Step.fans_out_over`, launched by `DevelopmentChain._launch_step`), each on its own branch (`ChangeLayout.audit_branch`), recorded by `DevelopmentChain._settle_audit`, joined at `tobiishi-seal` (its Step 1b); every other parallel lane remains ⏸ forward-design |

---

## Model — blackboard

Handoff is a **blackboard**: all work for one change lives in one folder, and roles never route to
one another.

```
system/projects/<name>/journey/tobiishi/<YYYY-MM-DD>_<slug>/
```

- The **folder** is the shared workspace and the single source of truth for the change's progress.
- **Roles are pure functions**: read the input artifact from the folder, write the output to its
  designated location — the folder for spec/design/plan artifacts, the codebase for implementation
  — then stop. A role names no successor, touches no queue, and reads no inbox.
- A separate **orchestrator** reads the folder, decides who acts next from the manifest, and
  spawns the role. Only the orchestrator knows the topology.

Each phase produces exactly **one action file**, read-only to the next phase and immutable once
written — the producer is ignorant of its successor, naming no next role and touching no queue.

---

## State is derived, not tracked

The chain computes the next action on every invocation from two signals: which action artifacts are
present in the folder, and the declared lines it reads from them — the design's `Publishes text:`
line, the code-integrity report's `Integrity:` line, and the closing marker's `Suite:` and
`Language resolution:` lines
(`step_outcome_contract.md` § *The chain's on-disk transport*). There is no status field for a role to
update and no queue to drift out of sync.

An explicit new start after integrity stops a change with declared developer deferrals returns to
implementation to reassess and finish that work. It preserves the old marker and report, requires a
new developer closing marker, then runs integrity again before audits or sealing. The stop itself
launches no recovery; this is owner-started re-entry, not automatic retry/loopback routing. Other bad
verdicts retain their refusal. `chain_development.py`'s start/describe decision owns the mechanics.

| Folder state | Next action | Who |
|---|---|---|
| no `change_spec.md` | `development-specs` | Product Owner |
| `change_spec.md`, no `change_design.md` | `development-design` | Architect |
| `change_design.md`, no `tl_instruction.md` | `development-plan` | Tech Lead |
| `tl_instruction.md`, no `change_text.md`, `change_design.md` declaring `Publishes text: yes` | `development-content` | Content Editor |
| `tl_instruction.md`, `change_design.md` declaring `Publishes text: no`, or `change_text.md` on the branch, code stage open | `development-implementation` | Developer |
| `tl_instruction.md`, `change_design.md` with no `Publishes text:` line, or a first word other than `yes` or `no` | halts `missing-text-verdict`, no launch | — |
| the closing marker declaring a passing `Suite:` verdict (`step_outcome_contract.md` § What passes) and a `Language resolution:` line | `development-code-integrity` | Senior Engineer |
| `code-integrity-report.md` declaring `Integrity: pass` | `development-audit`, once per audited step (`development-specs`, `development-design`, `development-plan`, `development-content` when it ran, `development-implementation`), each finding on its own branch — not a gate | kensaiapp-auditor |
| `Integrity: pass`, with every audit run ended, whatever it returned | `tobiishi-seal` (seal: move `<key>/` to `trail/` on branch + `--no-ff` merge) | PM |

Action artifacts are immutable once written and read-only downstream.

---

## The ledger — the only thing not derivable from artifacts

> ⏸ **Forward-design (parked → [[orchestrator-hardening]]).** The PoC writes no `_flow.md`; the
> `--no-ff` merge commit is the terminal marker. This section lands with resumability /
> loopback-routing hardening.

Artifacts express *what has been produced*. A few things they cannot express live in one
orchestrator-owned file per folder:

```
system/projects/<name>/journey/tobiishi/<YYYY-MM-DD>_<slug>/_flow.md
```

It records only: the current-stage pointer (denormalized, for fast read and observability), the
halt/pause flag and reason, the per-stage retry count, terminal completion of `development-implementation`
(suite green — there is no stage-5 action artifact in the folder to derive it from), and an
append-only event log with timestamps.

**The orchestrator is the sole writer of `_flow.md`. No role reads or writes it.** The artifacts
remain the source of truth for what is produced — if the ledger and the filesystem ever disagree on
that, the filesystem wins and the ledger is corrected. (The ledger is in principle reconstructable
from git history; the file exists for convenience, not authority.)

---

## Constraints (standing rules)

**Roles are orchestration-blind.** A role/skill reads its input artifact from the folder it is
pointed at and writes its output to its designated location — the change folder for spec/design/plan
artifacts, the codebase for implementation. It never reads or writes a queue, inbox, or `_flow.md`,
and never names a successor. The orchestrator's spawn prompt gives the role its working folder —
knowing your folder is not knowing the pipeline.

> The developer is the asymmetric case: it *reads* `tl_instruction.md` (+ cross-check artifacts)
> from the change folder but *writes code into the codebase*, not the folder. That is why stage-5
> completion ("code committed, suite green") is the one progress signal recorded in `_flow.md`
> rather than derived from folder contents — the output deliberately lives outside the blackboard.

**The folder is the unit of work and the source of truth for progress.** Stage is derived from
artifact presence, recomputed on every orchestrator invocation. No separate queue tracks where a
change is. This makes runs idempotent and resumable for free: re-invoking recomputes the same next
action.

**Artifacts are immutable; `_flow.md` is the only mutable file and the orchestrator owns it
exclusively.** Filesystem beats ledger on any disagreement about produced artifacts.

**The orchestrator owns sequencing.** Stage sequencing, retry loops, and halts originate in the
orchestrator, derived from the manifest — not in any role. A role never spawns the next stage; the
orchestrator does, one level up. The producer stays successor-ignorant.

**A `Deferred:` line on the closing marker is a declaration the orchestrator reads — not a halt, and
not the origin of one.** The developer that cannot land a task says so on the marker it closes with, and
the orchestrator reads that line as fact about the work: a red suite owned wholly by deferred tasks
lands instead of halting (`step_outcome_contract.md` § *The chain's on-disk transport*). The role halts
nothing and routes nothing by writing it; the halts stay the orchestrator's, derived from the manifest.

**A constraint handed down is stated as a property, never as an instruction.** A producer regularly
knows something its successor is bound by and must not decide for it — that two files have no green
point between them, that a task's red phase is probabilistic, that a value set must span a domain
whose members this stage does not fix. Successor-ignorance forbids the obvious move: naming the next
role and telling it what to do. So state the **property of the work** and let the successor derive
its own action from it. *No green point exists between these two* is a fact about the change;
*development-plan must shape each as one task* is an instruction to a role this artifact is not
permitted to know exists. Both carry the same constraint; only the first survives the model, and the
second is not a wording slip but a producer deciding a successor's business. **Where a stage's own
vocabulary cannot express such a property, the vocabulary is what changes** — the two ways out that
are not available are dropping the property, and reaching past the artifact into the successor's
decisions.

**Halt and surface on ambiguity.** An exceeded retry bound or any stop condition (`CROSS_ROLE.md`
iteration stops, user pause, kill-switch) → the orchestrator records the halt and yields to the
human. It never advances past a gate on ambiguity.

---

## Relationship to existing doctrine

**Leaves intact:**
- `development_flow.md` § The stages — the canonical stage list is unchanged; this doctrine consumes it.
- `change_classification.md` — Category × Behaviour are still set at entry and stamped in the
  `change_spec.md` header; the orchestrator reads them there.
- `role_handoff_boundaries.md` — the decision-authority boundaries (what each role locks, adds, and
  never crosses) are **orthogonal** to this doctrine and unchanged. Only the *routing* mechanism
  changes, never who-owns-what.

---

*Drafted 2026-06-19. **Ratified by Product 2026-06-22** — linear/happy-path slice LIVE, the rest
forward-design → [[orchestrator-hardening]] (see Ratification status, top). Orthogonal to `role_handoff_boundaries.md`.*
