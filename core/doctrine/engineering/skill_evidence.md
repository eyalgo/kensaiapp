---
version: "1.3.1"
---

# Skill evidence — versioned worked examples

Real output from a pipeline skill, kept as evidence of how **that version** of
the skill behaves. Distinct from eval fixtures (`evals/inputs/`, which are synthetic test inputs)
and from eval runs (`evals/workspace/`, which are graded against assertions). Evidence is a
faithful capture of a real run, organized so behaviour can be compared **across skill versions**.

## Location and key

```
skills/<group>/.claude/skills/<skill>/evidence/v<version>/
```

**Evidence is kept in the producer satellite — the audit instance, which holds the record — at the
path the skill has in the host.** The host does not carry it: a release ships the host's tree, and
evidence names the products and runs it was captured from. The folder is keyed by the **producing skill version** — the `version:` in the skill's `SKILL.md`
frontmatter at the time it produced the artifact. **Not** by the Tobiishi folder name, change
slug, project, or date. Those are incidental to a single run; the skill version is the evidence's
identity.

**Why version, not Tobiishi slug.** The question evidence answers is *"what does development-specs
v1.4.0 produce?"* — not *"what happened to that one project-list change?"* When a skill is
fixed and bumped, a fresh run files its output under the new `v<version>/` folder, sitting beside
the old one. The before/after is the version diff, with no date/slug bookkeeping and no collision.

## What a `v<version>/` folder holds

- The **output artifact(s)** the skill produced (e.g. development-specs → `change_spec.md`).
- The **input artifact(s)** the skill consumed, for context — labelled with the version of the
  upstream skill that produced them (e.g. development-design v1.3.0's evidence holds the `change_spec.md`
  produced by development-specs v1.4.0). This makes the evidence chain version-stamped end to end.
- A **`README.md`** that leads with the version, lists each file as input/output with its source
  commit, and records the version's known limitations (the reason a later version supersedes it).
- The **owner's answers**, when the skill surfaced work to them — the answered companion file, whole,
  for every cycle the round took. **A skill that surfaces work retires each answered file whole to a
  permanent trail in the product, copied before the companion is rewritten** — that is the
  convention, not a per-skill choice. Without it the answers are destroyed twice: folding rewrites
  the companion, and the close deletes it. The trail lives in the case, so snapshot it before 6.
  It is not a courtesy copy: it is the **authorization record** — the only thing that
  distinguishes a change the owner asked for from one the skill made up, which is what the audit's
  comparison passes check every delta against. Missing, they cannot run.
- The **ratification verdict**, when that version was ratified — a frozen copy of the verdict file,
  under its own name. The live verdict stays with the managing project (`../kaizen/ratification.md`
  owns its one home); this copy is the permanent one, and it is owed because the verdict cites the
  case's live outputs, which the next version overwrites. A verdict whose evidence has been
  overwritten is an assertion about files nobody can read.
- An **`audit.md`** when the run was audited — the blind fan-out's findings and the comparison
  against the previous version. Optional in general; mandatory under kaizen, where the audit is the
  round (`kaizen/skills.md`).
- A **`fix_packet.md`** when those findings were acted on — the decided fix in the shape
  `kaizen/fix_packet.md` owns: the verdict, the entries applied, what each subtracted, and what was
  declined. It sits beside the `audit.md` it answers, and is the only record of the *deliberate drops* —
  which is what the escape hatch's rule-by-rule walk (`kaizen/skills.md` § *A fix subtracts or trades*)
  has to account for and cannot recover from the audits, since audits record only what failed.
- An **`owner_answers.md`** when the packet raised something only the owner could settle — their
  adjudication calls, any broader ruling, and the entry dispositions those imply, in the shape
  `kaizen/fix_packet.md` owns. Written by the owner, never by the author, and kept because a ruling
  outlives its round: the next audit meets the same finding with no memory of the decision.

## Rules

- **Key by producing version, never by Tobiishi slug / date / project.**
- **Copied artifacts are faithful — do not edit them.** Their in-body dates, project names, and
  relative paths are the captured content, not the organizing key. (See also: mention that files
  came from a source repo is fine; pointing at live paths into that repo from skill prose is not.)
- **The snapshot mirrors the case's own filenames — never rename a captured file.** A file keeps the
  name it had in the case: the PRD is `PRD.md`, the companion `PRD_open_issues.md`, each retired answer
  `trail/prd/cycle-N.md`, the inputs their own names. Inventing a snapshot-only name
  (`*.answered.roundN.md`, `*.final.md`) breaks the faithful-capture rule above — a reader can no longer
  see that the snapshot *is* the case. The filename is the organizing key, and it is corrected only to
  match the case, never to a scheme the case never used. A reader should be able to `diff` the snapshot
  against the case and see only what the round produced, not a renaming.
- **One representative example per version.** If a version needs more than one exercising case,
  sub-key inside `v<version>/`; do not fall back to slug/date at the top level.
- **Capture fresh evidence when the skill is bumped** — a new `v<version>/`, not an overwrite of
  the old. Old versions' evidence is the comparison baseline.

## Relationship to other docs

- `folder_state_handoff.md` — the action-file output each phase produces; evidence captures
  those files per version.
- `evals/` (per skill) — synthetic fixtures + graded runs; a different artifact class from
  real-run evidence.
