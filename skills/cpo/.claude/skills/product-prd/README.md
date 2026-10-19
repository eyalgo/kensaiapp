# product-prd

A product needs one **source of truth for what it is and why** — read cold by the CTO, the CDO,
the Principal PM, and the Principal Architect before anyone designs or builds. `product-prd`
is the CPO's tool for authoring that document, the PRD, at the head of the definition sequence
(`<CORE>/doctrine/setup/setting_up_a_project.md`, which owns that sequence). It exists to make
that authoring *repeatable and headless*: it never blocks on a live interview, so the same skill
runs in an interactive `cpo:` session or as the `cpo` agent inside the pipeline.

## Version and ratification

`product-prd` is a **two-file stack**: this orchestrating `SKILL.md` plus the fat authoring
prompt `prompts/rich.md`, which carries the diagnostic, the tag contract, and
the twelve principles the PRD is judged against. Each file's own frontmatter `metadata.version`
is its version — this README does not restate either number, so it cannot drift out of step
with them.

**Ratified at `SKILL.md` v4.11.0 with the prompt at v2.4.0 — RATIFY, no conditions.** The verdict
lives with the project that manages the skill, at
[`system/projects/product-definition/docs/product-prd_ratification_verdict.md`](../../../../../system/projects/product-definition/docs/product-prd_ratification_verdict.md)
— the home `<CORE>/doctrine/kaizen/ratification.md` § 5 names. Its reasoning,
the cases it weighed, the ratifying model, and the four watch items it leaves open are the verdict's
own and are not restated here; a second live copy of them is what
`<CORE>/doctrine/kaizen/ratification.md` forbids. The output it judged is frozen beside it in the
audit instance's vault, at `skills/cpo/.claude/skills/product-prd/evidence/v4.11.0/`.

**The stack on disk is no longer the ratified pair.** The prompt has moved since the verdict: it
gained the PRD's blurb field, authored alongside the template's `## Blurb` section. So the stack now
reads *ratified at `SKILL.md` v4.11.0 with the prompt at v2.4.0, plus a change nobody has signed* —
an honest state to sit in, and the one fact a verdict cannot carry about itself, which is why this
section exists. A verdict is a statement about the versions it judged and stays one, so a bump to
either file does not carry it forward; re-earning the claim means a fresh round on two independent
cases at the current stack. `SKILL.md` has not moved.

**One dependency sits outside the signed pair.** The round ran against
`<CORE>/templates/product-templates/prd_template.md` @ **v1.7.0**, which shapes the sections the
prompt fills — but the template is not in `stack.json`'s substance, so a template bump does not by
itself unsign the pair. Whether it should is unsettled, and worth knowing before reading the
sentence above as a full answer.

## Launching cleanly

To start a headless run, use the launcher — do **not** hand-compose a `cpo` subagent prompt:

```
<CORE>/launchers/skill/launcher.sh product-prd <project>      # run from the instance root
```

The seat, the prompt and the completion reporter are this skill's `launcher.md`; the prompt is a
**fixed literal** and a caller only passes the project name, so no stray context (prior-round
summaries, SHAs, "report the findings") can leak into the run — that padding is the one thing that
pollutes an otherwise-fresh subagent. `--dry-run` prints the command without launching.

## What It Does

- **Drafts the whole PRD best-effort** from the project's inputs and a product
  diagnostic — never a blank-page interview, never a block waiting on the owner.
- **Surfaces, rather than guesses.** What the inputs can't settle goes into a companion
  **open-issues** file in three buckets — *open issues* (a question it has no basis to
  decide), *choices to confirm* (a drafted decision the owner signs off), and *directives*
  (an external action the skill can't perform, surfaced as a **gate to confirm** — non-blocking;
  once the owner confirms it, it's recorded in the PRD body and the external action stays
  deferred). A re-run folds the owner's answers in and drops what's resolved; when nothing is
  left it clears the companion — its absence is the done-signal.
- **Keeps the owner's answers.** Every fold first retires the answered companion whole to
  `<Product path>/docs/trail/prd/`, so a decision and the owner's reasoning for it stay
  readable and citable after the companion is gone.
- **Holds product altitude** — the what and why, never the how. Architecture, system
  requirements, and delivery sequencing are kept out for the roles downstream.
- **Requires CPO posture** — halts if invoked outside a `cpo:` session or the `cpo` agent,
  so the PRD is authored under the CPO lens rather than filled in hollow.
- Resolves where its files land from the project's **Product path**.

## File Structure

```
product-prd/
├── SKILL.md                    # the orchestrator: posture, the file loop, the workflow, the commit mechanics
├── README.md                   # this file
├── stack.json                  # the two-file stack manifest (SKILL.md + the authoring prompt)
└── evals/                      # benchmark fixtures + graded runs
```

## Depends On

- `prompts/rich.md` — the diagnostic the CPO applies.
- `<CORE>/templates/product-templates/prd_template.md` — the PRD's section shape.
- `<CORE>/templates/product-templates/prd_open_issues_template.md` — the companion's shape.
- `<CORE>/doctrine/governance/commit_via_builder.md` — how it commits.

## When to Use

Reach for this when **authoring, continuing, or revising a product's PRD** — the product
source of truth at the top of the upstream chain.

Not for: per-change specs (that's `development-specs`), the project's "done" declaration
(`project-agari`), or any downstream document — the SRS, SDD, Delivery Plan, FDR, ADR, or
NFDR.
