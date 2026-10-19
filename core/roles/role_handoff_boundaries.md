---
version: "1.2.0"
---

# Role handoff boundaries

Defines what each role locks, what the next role adds, and what must never cross the boundary.

Pipeline: **PM → Product Owner → Architect → Tech Lead → Content Editor (a change that publishes
text) → Developer → Senior Engineer → PM**

Skill names and per-stage artifact paths are owned by the pipeline manifest
(`../doctrine/flow/development_flow.md` § The stages). This document owns the **boundary contracts** —
what each role locks, the next role's decision space, what must never cross, and the boundary test.

---

## Foundation vs delta

The architecture is set once, then each change is a delta against it.

- **Foundation (written once per product, before any change):** `fdr.md`, `adr/` and `nfdr.md`
  lock the product definition and the system structure — modules, schema, dependency graph,
  forbidden imports. Who authors each, and when the step runs, is
  `<CORE>/doctrine/setup/setting_up_a_project.md` § *The foundation step*.
- **Delta (every change, in iteration):** the boundaries below operate on per-change artifacts
  (`change_spec.md`, `change_design.md`, `tl_instruction.md`) that *read* the locked foundation
  but never edit it. A change that needs the foundation altered escalates to its owning role
  (**Principal PM** for `fdr.md`, **Principal Architect** for `adr/` / `nfdr.md`) before proceeding.

---

## PM → Product Owner

**Locked:** `fdr.md` + change request

**What the PM locks:**
- Change request — the specific change: scope, affected rules, new behaviour, or scope expansion
- `fdr.md` — the functional definition, authored by the **Principal PM** and locked here as given. The PM validates against it; it does not author or move it.

**The Product Owner's decision space:**
- Expand the change request into a precise, testable spec
- Validate it against `fdr.md` — confirm the change is in scope
- Produce `change_spec.md` and its acceptance gate

**The Product Owner does NOT:**
- Edit `fdr.md` — it is the **Principal PM**'s (`<CORE>/roles/loaders/principal_pm_global.md` § *The FDR*)
- Resolve an fdr-conflict silently — if the change contradicts `fdr.md`, escalate to PM first

**The PM does NOT:**
- Write `change_spec.md` — acceptance criteria are PO territory
- Hand off a change request that contradicts `fdr.md` — resolve the conflict first
- Edit `fdr.md` to resolve that conflict — return `fdr-update-needed` to the **Principal PM** and let the request wait

**Boundary test:** *"Does this define what the product IS, or specify what a CHANGE must do?"*
Product identity, constraints, scope → the **Principal PM**, in `fdr.md`. Which change is opened now, and against which locked scope → PM. Behaviour of a specific change → PO.

**fdr-conflict escalation:** if expanding the change surfaces a conflict with `fdr.md`, the PO
stops and returns it to PM with a specific question. PM resolves by narrowing the request, or
returns `fdr-update-needed` to the **Principal PM** where the FDR itself must move. The PO does
not proceed until resolution.

---

## Product Owner → Architect

**Locked:** `change_spec.md` (+ `acceptance_change_spec.md`)

**What the Product Owner locks:**
- Description — what the change produces and why
- Rules — business rules, atomic and testable, every `[OPEN]` resolved
- Locked answers — every gap resolved, precise enough to derive a test from
- Examples — user-visible input/output (CLI invocations, not code)
- Product constraints — language version, dependency restrictions
- Error conditions and named exception types
- Acceptance gate — what the change's tests must cover, in `acceptance_change_spec.md`

**The Architect's decision space** (design against the locked foundation — not translation):
- Read the foundation (`adr/` module design + dependency graph, `nfdr.md` forbidden imports)
  and the spec; determine **blast radius** — which modules the change touches
- Decompose into **sub-jobs** with interface contracts and a build sequence
- Assign **code strategy** — Simple / Complex per sub-job, hints for Complex
- Specify **test additions** for the change
- Produce `change_design.md` — the delta, not a re-statement of the whole system

**The Architect does NOT:**
- Change business rules or product constraints locked in `change_spec.md`
- Edit the foundation (`adr/` / `fdr.md` / `nfdr.md`) — a structural change belongs to the
  foundation step and its owning role, not to a per-change delta
- Re-interview the user about decisions already in Locked answers
- Carry forward any `[OPEN]` item — return it to the Product Owner

**Boundary test:** *"Does this prescribe how the system is built, or describe what the system
must do?"* Construction (modules, files, sub-jobs, dependency order) → Architect.
User-visible behaviour, rules, constraints → Product Owner.

---

## Architect → Tech Lead

**Locked:** `change_design.md` (the delta) + the foundation it reads from (`adr/`, `fdr.md`, `nfdr.md`)

**What the Architect locks** (in `change_design.md`):
- §1 Change Summary — what changes and why
- §2 Blast Radius — which modules are new / modified
- §3 Sub-jobs — scope, interface contracts, build sequence
- §4 Code Strategy — per-sub-job Simple / Complex, hint content for Complex
- §5 Test Additions — what tests the change adds or modifies

The full system structure (module boundaries, schema, dependency graph, forbidden imports)
stays in the foundation (`adr/` / `nfdr.md`); the Tech Lead reads both the delta and the foundation.

**The Tech Lead's decision space** (improvement — not translation):
- **Spec-vs-design coverage** — read `change_spec.md` and confirm `change_design.md` delivers
  everything asked; a missing requirement is a gap the plan fixes and logs
- **Task granularity** — split a sub-job too large for one TDD cycle; merge two trivially small ones
- **Edge-case completion** — read `change_design.md §3` + the foundation's module design and
  surface edge cases not enumerated (empty inputs, boundary transitions, invalid states)
- **Sequencing risk flags** — identify blocking dependencies from the build sequence /
  `adr/` dependency graph and surface them
- **Type precision** — upgrade an imprecise construct (a string with a closed value set → enum)
- **Hint precision** — sharpen a Complex hint that is absent or too vague
- Every improvement is logged; produce `tl_instruction.md`

**The Tech Lead does NOT:**
- Override architectural decisions — module boundaries, dependency direction, topology are
  locked in `adr/`
- Add modules or dependencies not present in `adr/` / `change_design.md`
- Implement for the developer — improvements raise the scaffold, not the implementation
- Silently drop an architect decision — overrides are logged

Note: the flow-line Tech Lead **does** read `change_spec.md` (for the coverage check) alongside
`change_design.md` and the foundation — unlike the old chain, the spec is in scope.

**Boundary test:** *"Does this change an architectural decision, or add judgment within the
architecture?"* Architectural decision → return to Architect. Judgment within → Tech Lead.

---

## Tech Lead → Developer

**Locked:** `tl_instruction.md`

**What the Tech Lead locks:**
- Module responsibilities — what each module does, in one sentence
- File paths — exact paths for every source and test file
- Dependency order — task sequence and blocking relationships
- Behaviour names — test names + one-line descriptions of what each must verify
- Lane designation — which of the five shapes each task is, named by its gate header and the exact
  `#### Implement` marker `development-implementation` routes on
- Hints, where `change_design.md §4` carries one — algorithm shape, data layout, atomicity pattern,
  key library call (not working code)

**The Developer's decision space:**
- All implementation reasoning — how to satisfy the behaviours
- Test implementations — the TL names behaviours; the developer writes the suite
- Internal structure within a module — local names, helper functions, control flow
- A task whose `#### Implement` reads `Infer from failing tests.` — the developer owns the implementation entirely
- Additional tests beyond those listed

**The Developer does NOT:**
- Change module structure, file paths, or names — locked in the project layout
- Override a hint — a hint names the approach and the developer follows its direction; a task with no hint is inferred from the failing tests
- Go beyond the spec behaviours — new product behaviour is a spec change, not a developer decision
- Change the task sequence — surface a sequencing problem rather than reorder silently

**Boundary test:** *"Does this require a product or architectural judgment, or is it an
implementation decision within locked constraints?"* Product judgment → Product Owner.
Architectural judgment → Architect. Implementation decision → Developer.

---

## Content Editor → Developer

Runs only when `change_design.md` reads `**Publishes text:** yes`; otherwise the Tech Lead hands
straight to the Developer, and the section above is the whole boundary.

**Locked:** `change_text.md`

**What the Content Editor locks:**
- Every string the change publishes, verbatim and whole, one per state
- Which place in the change each string belongs to — named by the part of the change that needs it,
  never by identifier or file

**The Developer's decision space:**
- Where and how each string is stored, named and rendered
- Everything `tl_instruction.md` leaves to it, as in the section above

**The Developer does NOT:**
- Write, reword, shorten or assemble a string — a published string comes from `change_text.md` or
  nowhere; where `tl_instruction.md` carries wording of its own for the same place, `change_text.md`
  wins
- Patch a string that cannot be placed as written — it is recorded in Developer Review Notes as a
  finding for the Content Editor

**Boundary test:** *"Does this change a word a person reads, or only where the word lives?"* A word
→ Content Editor. Where it lives → Developer.
