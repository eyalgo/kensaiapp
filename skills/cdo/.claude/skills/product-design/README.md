# product-design

Once a product knows what its experience must be — the CDO's UXD, whose design-system direction
call names the system and the constraints — someone has to hold **every visual value** that
satisfies it. That is the design language, `DESIGN.md`, and `product-design` is the CDO's tool
for authoring it: written off the settled UXD
(`<CORE>/doctrine/setup/setting_up_a_project.md`, which owns that sequence — station 4's second
run, after `product-uxd`), and read cold by implementing agents so the product is styled against
grounded tokens rather than an agent's defaults at code time. It exists to make that derivation
*repeatable and headless* — it never blocks on a live interview, so the same skill runs in an
interactive `cdo:` session or as the `cdo` agent.

Unlike its siblings' documents, the format is **external and machine-checked**: Google's
DESIGN.md, linted by `@google/design.md`. That is why this skill's workflow carries a fifth step
the UXD's does not — the machine gate — and why the schema's authority is the vendor, never this
stack.

## Version and ratification

`product-design` is a **two-file stack**: this orchestrating `SKILL.md` plus the fat
authoring prompt `prompts/rich.md`, which carries the design-language
completeness lens, the evidence gate, the anti-default discipline, the provenance gate, the
machine gate's bar, and the stability rule the design language is judged against. Each file's
own frontmatter `metadata.version` is its version — this README does not restate either number,
so it cannot drift out of step with them. `stack.json` is the manifest of the two.

**Nothing here is ratified.** One benchmark round is recorded — iteration-1, `39ad5ff`, 93% with
the skill against a 35% baseline — but it measured the skill alone: the authoring prompt did not
exist when it ran, so the number grades the orchestration and not the substance the prompt owns.
Read it as a floor for the eventual stack. A reader deciding how far to trust this stack's output
should weigh that directly rather than infer standing from a sibling's verdict —
`product-uxd`'s ratification is its own and says nothing about this pair.

## Launching

To start a headless run, use the launcher — do **not** hand-compose a `cdo` subagent prompt:

```
<CORE>/launchers/skill/launcher.sh product-design <project>     # run from the instance root
```

The seat, the prompt and the completion reporter are this skill's `launcher.md`; the prompt is a
**fixed literal** and a caller only passes the project name, so no stray context can leak into an
otherwise-fresh subagent. `--dry-run` prints the command without launching.

The posture gate accepts either that launcher's cdo subagent or an interactive `cdo:` session, so a
round can also be run by hand when that suits.

## What It Does

- **Derives the whole design language best-effort** from the UXD's direction call, the product's
  own source, its brand assets, and whatever context the owner handed over — never a blank-page
  interview, never a block waiting on an answer.
- **Grounds where there is evidence, and designs where there is none.** A value the product
  already states is a fact it carries and cites; everything else it decides, with a reason. What
  goes to the owner is not every invented value but the **load-bearing calls** — each naming what
  moves underneath it if overridden — in a companion **open-issues** file, in the buckets
  `design_open_issues_template.md` defines: a call drafted for sign-off, which a category declared
  omitted also is, and the rarer question it has no basis to answer.
- **Verifies with the format's own linter** before committing, and never reports a design
  language finished on a file that has not met the prompt's bar — which is not the linter's
  exit code; the prompt owns what clean means.
- **Keeps the owner's answers.** Every fold first retires the answered companion whole to
  `<Product path>/docs/trail/design/`, so a decision and the reasoning behind it stay readable
  and citable after the companion is gone. A re-run folds the answers in and drops what's
  resolved; when nothing is left it clears the companion — its absence is the done signal.
- **Holds the design-language altitude** — every token value lives here and only here. The
  experience structure is the UXD's; product intent is the PRD's; the direction call it answers
  is the UXD's § Design-System Direction.
- **Requires CDO posture** — halts if invoked outside a `cdo:` session or the `cdo` agent, so
  the values are grounded under the CDO lens rather than filled in hollow.
- Resolves where its files land from the project's **Product path**.

## File Structure

```
product-design/
├── SKILL.md          # the skill: posture, the file loop, path resolution, the machine gate, the commit
├── README.md         # this file
├── evals/            # the behavior eval set and its fixtures (workspace output is gitignored)
└── stack.json        # the two-file stack manifest (SKILL.md + the authoring prompt)
```

## Depends On

- `prompts/rich.md` — how the CDO grounds, sorts, and records — and what
  a clean lint means.
- `<CORE>/templates/product-templates/design_template.md` — the design language's section
  shape and token schema as stamped.
- `<CORE>/templates/product-templates/design_open_issues_template.md` — the companion's shape.
- `<CORE>/../skills/cdo/.claude/skills/product-uxd/SKILL.md` — where the UXD lands; the path is resolved from there,
  never remembered here.
- `<CORE>/../skills/cpo/.claude/skills/product-prd/SKILL.md` — where the PRD lands; resolved the same way.
- `<CORE>/doctrine/governance/commit_via_builder.md` — how it commits.

## When to Use

Reach for this when **authoring, continuing, or revising a product's design language** — the
visual source of truth, written off the UXD's direction call.

Not for: the experience definition (`product-uxd`, upstream), per-change specs
(`development-specs`), the PRD (`product-prd`), the SRS (`product-srs`), the project's "done"
declaration (`project-agari`), or any downstream document — the SDD, Delivery Plan, FDR, ADR,
or NFDR.
