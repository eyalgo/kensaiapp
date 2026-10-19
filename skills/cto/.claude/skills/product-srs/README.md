# product-srs

Once a product knows **what it is and why** — the CPO's PRD — someone has to say what the
**system** must therefore do. That is the SRS, and `product-srs` is the CTO's tool for authoring
it — written off the settled PRD alongside the CDO's UXD
(`<CORE>/doctrine/setup/setting_up_a_project.md`, which owns that sequence), and read cold by the
Principal PM and the Principal Architect before anyone designs or builds. It exists to make that
derivation *repeatable and headless* — it never blocks on a live interview, so the same skill runs
in an interactive `cto:` session or as the `cto` agent inside the pipeline.

## Version and ratification

`product-srs` is a **two-file stack**: this orchestrating `SKILL.md` plus the fat authoring prompt
`prompts/rich.md`, which carries the completeness lens, the sorting test, the
provenance gate, and the stability rule the SRS is judged against. Each file's own frontmatter
`metadata.version` is its version — this README does not restate either number, so it cannot drift
out of step with them. `stack.json` is the manifest of the two.

**Ratified at `SKILL.md` v4.4.0 with the prompt at v3.2.0 — RATIFY, no conditions.** The verdict
lives with the project that manages the skill, at
[`system/projects/product-definition/docs/product-srs_ratification_verdict.md`](../../../../../system/projects/product-definition/docs/product-srs_ratification_verdict.md)
— the home `<CORE>/doctrine/kaizen/ratification.md` § 5 names. Its reasoning,
the cases it weighed, the ratifying model, and the four bounded findings it leaves open are the
verdict's own and are not restated here; a second live copy of them is what
`<CORE>/doctrine/kaizen/ratification.md` forbids. The output it judged is frozen beside it in the
audit instance's vault, at `skills/cto/.claude/skills/product-srs/evidence/v4.4.0/`.

**The stack on disk has moved past the ratified pair.** Both files have been bumped since the
verdict — that is the one fact a verdict cannot carry about itself, and the reason this section
exists. A verdict is a statement about the versions it judged and stays one, so the bumps do not
carry it forward: the stack now reads *ratified at v4.4.0 with the prompt at v3.2.0, plus changes
nobody has signed*. Compare each file's frontmatter against those two numbers to see the distance.
Re-earning the verdict means a fresh round on two independent cases at the new stack.

**No blind audit has run over this version either, and that is settled rather than pending.**
Audits advise and the owner ratifies (`<CORE>/doctrine/kaizen/skills.md` § Ratify), so the verdict
weighed the absence as a fact rather than a gate and did the substantive examination itself. v4.3.0
carried no `audit.md` by the owner's deliberate call; v4.4.0 carries none on the same footing. Read
the absence as decided, not as unfinished work.

**One dependency sits outside the signed pair.** The round ran against
`<CORE>/templates/product-templates/srs_template.md` @ **v1.7.0** and `srs_open_issues_template.md`
@ **v1.1.0**, which shape the sections the prompt fills — but neither is in `stack.json`'s
substance, so a template bump does not by itself unsign the pair. Whether it should is unsettled,
and worth knowing before reading the sentence above as a full answer.

## Launching cleanly

To start a headless run, use the launcher — do **not** hand-compose a `cto` subagent prompt:

```
<CORE>/launchers/skill/launcher.sh product-srs <project>     # run from the instance root
```

The seat, the prompt and the completion reporter are this skill's `launcher.md`; the prompt is a
**fixed literal** and a caller only passes the project name, so no stray context can leak into an
otherwise-fresh subagent. `--dry-run` prints the command without launching.

## What It Does

- **Derives the whole SRS best-effort** from the PRD and whatever context and constraints the owner
  handed over — never a blank-page interview, never a block waiting on an answer.
- **Surfaces, rather than guesses.** What the inputs can't settle goes into a companion
  **open-issues** file in two buckets — *open issues* (a technical question it has no basis to
  decide) and *choices to confirm* (a best-effort call drafted into the SRS for the owner to sign
  off or override). The line between them is the prompt's derivability test: a bar computed from a
  PRD fact is the CTO's to state with its derivation recorded; a bar that is a promise about what
  the product feels like is the owner's.
- **Keeps the owner's answers.** Every fold first retires the answered companion whole to
  `<Product path>/docs/trail/srs/`, so a decision and the reasoning behind it stay readable and
  citable after the companion is gone. A re-run folds the answers in and drops what's resolved;
  when nothing is left it clears the companion — its absence is the done signal.
- **Holds SRS altitude** — the system-level *what*, traceable to the PRD, never the *how*.
  Architecture and component design are the SDD's; delivery sequencing is the Delivery Plan's.
- **Never halts on a flawed PRD.** It reads its input critically — contradictions, goals too vague
  to test, false precision — and resolves at the SRS tier or surfaces to the owner, visibly, and
  keeps going.
- **Requires CTO posture** — halts if invoked outside a `cto:` session or the `cto` agent, so the
  SRS is derived under the CTO lens rather than filled in hollow.
- Resolves where its files land from the project's **Product path**.

## File Structure

```
product-srs/
├── SKILL.md          # the skill: posture, the file loop, path resolution, staging, the commit
├── README.md         # this file
├── stack.json        # the two-file stack manifest (SKILL.md + the authoring prompt)
└── evals/            # benchmark fixtures + graded runs
```

## Depends On

- `prompts/rich.md` — how the CTO derives, sorts, and records.
- `<CORE>/templates/product-templates/srs_template.md` — the SRS's section shape.
- `<CORE>/templates/product-templates/srs_open_issues_template.md` — the companion's shape.
- `<CORE>/../skills/cpo/.claude/skills/product-prd/SKILL.md` — where the PRD lands; the path is resolved from there,
  never remembered here.
- `<CORE>/doctrine/governance/commit_via_builder.md` — how it commits.

## When to Use

Reach for this when **authoring, continuing, or revising a product's SRS** — the technical source
of truth, one step below the PRD in the upstream chain.

Not for: per-change specs (that's `development-specs`), the PRD itself (`product-prd`, upstream),
the project's "done" declaration (`project-agari`), or any downstream document — the SDD, Delivery
Plan, FDR, ADR, or NFDR.
