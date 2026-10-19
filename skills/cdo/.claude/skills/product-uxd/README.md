# product-uxd

Once a product knows **what it is and why** — the CPO's PRD — someone has to say what the
**experience** must therefore be. That is the UXD, and `product-uxd` is the CDO's tool for
authoring it — written off the settled PRD alongside the CTO's SRS
(`<CORE>/doctrine/setup/setting_up_a_project.md`, which owns that sequence), and read cold by the
SDD so the architecture is designed against a settled experience rather than the other
way round. It exists to make that derivation *repeatable and headless* — it never blocks on a live
interview, so the same skill runs in an interactive `cdo:` session or as the `cdo` agent.

## Version and ratification

`product-uxd` is a **two-file stack**: this orchestrating `SKILL.md` plus the fat authoring prompt
`prompts/rich.md`, which carries the completeness lens, the anti-default
discipline, the sorting test, the provenance gate, and the stability rule the UXD is judged
against. Each file's own frontmatter `metadata.version` is its version — this README does not
restate either number, so it cannot drift out of step with them. `stack.json` is the manifest of
the two.

**Ratified at `SKILL.md` v0.4.0 with the prompt at v1.8.0 — RATIFY, no conditions.** The verdict
lives with the project that manages the skill, at
[`system/projects/product-definition/docs/product-uxd_ratification_verdict.md`](../../../../../system/projects/product-definition/docs/product-uxd_ratification_verdict.md)
— the home `<CORE>/doctrine/kaizen/ratification.md` § 5 names. Its reasoning,
the cases it weighed, the ratifying model, and the six open items it leaves bounded are the
verdict's own and are not restated here; a second live copy of them is what
`<CORE>/doctrine/kaizen/ratification.md` forbids. The output it judged is frozen beside it in the
audit instance's vault, at `skills/cdo/.claude/skills/product-uxd/evidence/v0.4.0/`.

**The stack on disk is no longer the signed pair.** Both files in `stack.json`'s substance have
moved since the verdict, so the stack now reads *ratified at `SKILL.md` v0.4.0 with the prompt at
v1.8.0, plus changes nobody has signed*. That is the one fact a verdict cannot carry about itself,
which is why this section states it rather than leaving it to be inferred. Any bump to either file
ends the standing claim, whatever the edit changed, and this section stops claiming it **in the same
session as the bump** (`<CORE>/doctrine/kaizen/ratification.md` § *The claim is about versions, and a
bump ends it*). What ends is the claim, not the verdict — it stays true about the versions it judged,
and re-earning the claim is a fresh round at the current stack, not a repair.

**Two bumps ended it, and the first went unrecorded.** `0578e65` moved the prompt off v1.8.0 and did
not touch this file, so the claim above stood falsely from that commit until this one. The second is
v9's `product-uxd` kaizen round: its step 1 moved both substance files — the fourth design dial, the
two instance-fence reads in Step 1's read list, and the design-run flow-back contract.

**No blind audit ran — read that absence as decided.** Audits advise and the owner ratifies
(`<CORE>/doctrine/kaizen/skills.md` § Ratify), so the verdict weighed the absence of a fan-out as a
fact rather than a gate and did the substantive examination itself, on three independent cases.

**Benchmark evals now exist, and the first run is in.** Five cases, both arms, against the signed
stack — `SKILL.md` v0.4.0 and the prompt v1.8.0, which the run did not touch. It predates the kaizen
round above, so read every figure in this paragraph as measured on the signed pair, not on the stack
a reader finds today. With-skill passed **22 of 22** assertions, the blind baseline **9 of 22**: a pass
rate of 100% against 39%, delta **+0.61**, with no case tied. The sharpest of them is
`design-read-dials-and-states`, where the baseline scored **0/4** — that case checks only the
skill's named literals (`Reading this as`, the dials, four states per screen row, a
design-direction section carrying no token values), and a capable model writes a serviceable UX
specification while hitting none of them. Read the re-entry case's 4/7 baseline with suspicion
rather than as a weak result: its fixture hands the agent a Version-1 UXD already in the skill's
idiom, so discrimination belongs to the fresh-create cases. The record, the per-assertion evidence
and the produced outputs are at `evidence/iteration-1/` in the audit instance's vault, at
`skills/cdo/.claude/skills/product-uxd/` — the live workspace is gitignored, so that folder is the
only durable copy.

**Its two templates sit outside the stack.** The round ran against
`<CORE>/templates/product-templates/uxd_template.md` @ **v1.4.1** and `uxd_open_issues_template.md`
@ **v1.1.1**, which shape the sections the prompt fills — but neither is in `stack.json`'s
substance, matching the sibling stacks, so a template bump does not by itself unsign the pair.
Whether it should is unsettled there too, and worth knowing before reading the paragraph above as a
full answer.

## Launching

To start a headless run, use the launcher — do **not** hand-compose a `cdo` subagent prompt:

```
<CORE>/launchers/skill/launcher.sh product-uxd <project>     # run from the instance root
```

The seat, the prompt and the completion reporter are this skill's `launcher.md`; the prompt is a
**fixed literal** and a caller only passes the project name, so no stray context can leak into an
otherwise-fresh subagent. `--dry-run` prints the command without launching.

The posture gate accepts either that launcher's cdo subagent or an interactive `cdo:` session, so a
round can also be run by hand when that suits.

## What It Does

- **Derives the whole UXD best-effort** from the PRD and whatever context and constraints the owner
  handed over — never a blank-page interview, never a block waiting on an answer.
- **Surfaces, rather than guesses.** What the inputs can't settle goes into a companion
  **open-issues** file, in the buckets `uxd_open_issues_template.md` defines — an experience
  question it has no basis to decide, kept apart from a best-effort call drafted into the UXD for
  the owner to sign off or override. Which of them an item is, and how it is led, is the prompt's
  sorting test.
- **Keeps the owner's answers.** Every fold first retires the answered companion whole to
  `<Product path>/docs/trail/uxd/`, so a decision and the reasoning behind it stay readable and
  citable after the companion is gone. A re-run folds the answers in and drops what's resolved;
  when nothing is left it clears the companion — its absence is the done signal.
- **Holds UXD altitude** — the experience-level *what*, traceable to the PRD, never the *how*.
  Technical feasibility and system requirements are the SRS's; architecture is the SDD's; the
  product intent the experience serves is the PRD's.
- **Never halts on a flawed PRD.** It reads its input critically — contradictions, intent too vague
  to design against, an implied experience the PRD never states — and resolves at the UXD tier or
  surfaces to the owner, visibly, and keeps going.
- **Requires CDO posture** — halts if invoked outside a `cdo:` session or the `cdo` agent, so the
  UXD is derived under the CDO lens rather than filled in hollow.
- Resolves where its files land from the project's **Product path**.

## File Structure

```
product-uxd/
├── SKILL.md          # the skill: posture, the file loop, path resolution, staging, the commit
├── README.md         # this file
└── stack.json        # the two-file stack manifest (SKILL.md + the authoring prompt)
```

## Depends On

- `prompts/rich.md` — how the CDO derives, sorts, and records.
- `<CORE>/templates/product-templates/uxd_template.md` — the UXD's section shape.
- `<CORE>/templates/product-templates/uxd_open_issues_template.md` — the companion's shape.
- `<CORE>/../skills/cpo/.claude/skills/product-prd/SKILL.md` — where the PRD lands; the path is resolved from there,
  never remembered here.
- `<CORE>/doctrine/governance/commit_via_builder.md` — how it commits.

## When to Use

Reach for this when **authoring, continuing, or revising a product's UXD** — the experience source
of truth, written off the PRD in parallel with the SRS.

Not for: per-change specs (that's `development-specs`), the PRD itself (`product-prd`, upstream),
the SRS (`product-srs`, its sibling), the design language that follows from the UXD's direction
call (`product-design`), the project's "done" declaration (`project-agari`), or any downstream
document — the SDD, Delivery Plan, FDR, ADR, or NFDR.
