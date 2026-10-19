---
version: "1.7.1"
---

# The Flow — the change pipeline

*One change enters, runs the stages on a blackboard, and merges — advancing the project toward
its Agari. This file represents the flow: the loop and the stages. How state passes between stages
is the handoff (`folder_state_handoff.md`); how a step reports its result to the orchestrator is
the outcome contract (`step_outcome_contract.md`).*

## The loop
1. A change is placed as a **Tobiishi** in the project.
2. **The chain** (`core/launchers/chain-development/launcher.sh <project>` → `core/tools/chain_development.py`) is launched on the project.
3. The **PO opens the branch** — all work lands there.
4. The flow runs and **ends with the PM merge**.
5. The **PM seals the Tobiishi** — records the result and moves `<key>/` to `journey/tobiishi/trail/`
   on the branch, *then* merges, so the seal rides into `main` (2 commits/change: open + sealed merge).

## The stages

The chain sequences the stages — roles never route. Stage order is a fixed linear
sequence; it starts a step once the previous run has ended and its artifact is on disk, and it reads
the outcome off disk (`step_outcome_contract.md` § *The chain's on-disk transport*), not from a
returned message.
Every iteration change is classified on two axes — Category × Behaviour
(`change_classification.md`): Category drives routing, Behaviour drives the mechanism.

The `fdr.md`, `adr/` and `nfdr.md` the stages below read are written **before** any of this, in the
**foundation step** — its own seed, one per product, seeded after the SDD settles.
`<CORE>/doctrine/setup/setting_up_a_project.md` § *The foundation step* owns who authors each and what
each is written from; this file does not restate it.

### Iteration (every change, whatever its Category)
| Stage | Role | Skill | Reads | Writes |
|---|---|---|---|---|
| 1 | Product Owner | `development-specs` | `fdr.md` + the Tobiishi | `change_spec.md` |
| 2 | Architect | `development-design` | `change_spec.md` + `adr/`/`fdr.md`/`nfdr.md` + `SDD.md` § 3 | `change_design.md` with its `Publishes text:` line |
| 3 | Tech Lead | `development-plan` | `change_spec.md` + `change_design.md` + `adr/`/`fdr.md`/`nfdr.md` + `SDD.md` § 3 | `tl_instruction.md` |
| 4 | Content Editor | `development-content` | `change_spec.md` + `change_design.md` (its `Publishes text:` line) + `CONTENT.md` + the writing bar | `change_text.md` |
| 5 | Developer | `development-implementation` | `tl_instruction.md` + `change_text.md` when Stage 4 ran + `change_design.md` (cross-check) + `SDD.md` § 3 + `project.md` (execution context) | code (green suite) |
| 6 | Senior Engineer | `development-code-integrity` | Stage-5 code + `change_spec.md` + `SDD.md` § 3 | `code-integrity-report.md` + green suite |
| 7 | PM | `tobiishi-seal` | the change key + Stage-6 green suite | take `main`'s advance + suite green on it, then seal (result + move `<key>/` to `trail/` on branch) + `--no-ff` merge to `main` |

**Stage 4 runs only for a change that publishes text.** The architect writes a `Publishes text:` line in
`change_design.md`, and the chain reads its first word when the walk reaches the step. `yes` runs the
step once: the Content Editor writes `change_text.md`, and the Developer places that text and writes none
of its own. `no` passes the step with no launch, and a resume finds it done. A line that is missing, or
whose first word is neither `yes` nor `no`, halts the walk before any launch, with the reason
`missing-text-verdict`. A change already past Stage 4 on disk is never entered there.

A product with no code has no suite. Its card reads `Test command: none`, and wherever the table says
"green suite" it means `Suite: none` and no suite run (`step_outcome_contract.md` § What passes).

The flow carries **one Tobiishi at a time**: each stage adds its artifact to the Tobiishi, the
developer writes code into the codebase (Stage 5), the Senior Engineer proves it against its intent
(Stage 6), and `tobiishi-seal` merges it (Stage 7). How the
Tobiishi's artifacts pass between stages: `folder_state_handoff.md`.

## Code goes where the parts table puts it

**A change that adds logic puts it in the part that owns it, in the change that writes it** — the
owner's call, 2026-10-01: *"Code goes where the architecture says it goes, in the change that writes
it."* The owner's ruling names the table the *module table*. This file calls it the parts table, after
the template's own heading.

The parts table is `docs/SDD.md` § 3, *The parts, and the seams between them*
(`<CORE>/templates/product-templates/sdd_template.md` § 3). Each row is one part. `Owns` and
`Must not own` say which logic belongs to it. `Lives in` names the unit its code sits in, and several
parts may share one unit.

**The owning part** of a piece of logic is the part whose `Owns` covers it and whose `Must not own`
does not name it. **A misplacement** is new logic written into code outside its owning part. The usual
case is logic written inline where it is first called. On this reading of the ruling, which covers
logic "the product's module table assigns", logic that no part owns is outside the rule.

**The import graph does not show a misplacement.** `docs/nfdr.md` § 1.2 is the import graph
(`<CORE>/templates/product-templates/nfdr_template.md` § 1.2, "Forbidden imports"). On this reading,
misplaced logic usually needs no import the graph forbids, so a check run over the graph passes it.
Placement is checked by reading the parts table, at these stages:

- **Stage 2, `development-design`,** names the owning part of each new piece of logic in the blast
  radius.
- **Stage 3, `development-plan`,** puts each piece of logic in the task that writes its owning part's
  code.
- **Stage 5, `development-implementation`,** writes each piece of logic in its owning part's code,
  including logic the instruction placed elsewhere.
- **Stage 6, `development-code-integrity`,** moves any misplacement still in the code, in the same
  change and before it seals.
- **`development-audit` on the implementation step** records a misplacement still in the code as a
  `blocking` finding.

**What no stage after the design does to place logic: create a unit the design did not list, or add
an import `docs/nfdr.md` § 1.2 forbids and the design did not allow.** Both are design decisions, made
at Stage 2 and recorded there. A later stage that would need one to place a piece of logic records the
case in its own output and leaves the placement as it found it. At Stage 6
the same case is a redesign, and code-integrity stops under its existing condition for one. The
stopped walk then waits for the owner.

**The audit does not block; the PM reads it** — the owner's call, 2026-10-01. The chain records the
audit's findings without reading them (`<CORE>/tools/chain_development.py` `_settle_audit`), so a
`blocking` finding does not hold the seal. It reaches the PM through `shukuba-refine`, whose method
takes the `blocking` findings first (`<CORE>/../skills/pm/.claude/skills/shukuba-refine/prompts/rich.md`, "A `blocking` finding is
the first thing to account for").

A product with no `docs/SDD.md` § 3 parts table has nothing to check placement against. Each stage
above says so in its output rather than inferring a table.

## Where it's going
- **More stages + a merge ceremony** — the flow gains steps and logic beyond the happy path.
- **The selection layer** — a PM loop that decides the next Tobiishi from the project's Shukuba +
  Agari, places it, and approves the result before choosing the next.
  (Direction: hoshin `product-leadership` · kaizen `pm-two-mode`.)
