# changelog-line

The Content Editor's step on a change's branch, after implementation and before code integrity. It keeps
the changelogs of the product paths a change touches, and the what-left file at the change's own product
path, true to the work the change built. It leaves a committed report in the change folder so the chain
knows it finished.

## What It Does

- **Writes the change's entry** under `## [Unreleased]` of the `CHANGELOG.md` of each product path the
  branch changes, and of the change's own product path, when the change alters what a user of a fresh
  clone installs, runs, types or reads there. A change to a root file of the instance is logged in
  `core/tools/CHANGELOG.md`. Each changelog earns an entry or none on its own.
- **Removes what-left entries** from `docs/what_left.md` at the change's own product path, only where
  the change completes the whole want. A part-complete entry stays, and each removal's commit body cites
  the branch commit at which the want is built.
- **Passes quietly where nothing applies.** A product path with no `CHANGELOG.md` gets no entry and no
  file, and the other changelogs still get theirs. Where that is the change's own product path, its
  what-left file is left as it is. A product path with no what-left file loses nothing.
- **Commits the report**, `changelog-report.md`, in the change folder. The chain counts the step done once
  that report is committed on the branch.
- **Requires Content Editor posture** and halts outside it, before reading any project input.

## Run it

`<CORE>/launchers/skill/launcher.sh changelog-line <project> <key>`, from the instance root. The chain
launches it itself for every change. Its model and effort are `intelligence/<provider>.md`'s.

## File Structure

```
changelog-line/
├── SKILL.md          # the loop: posture, worktrees, validation, write scope and commit order
├── launcher.md       # the unattended launch contract
├── prompts/thin.md   # the judgment and the words of every outcome
├── references/changelog_report_template.md   # the four sections of the report
├── intelligence/     # claude.md, codex.md — model and effort, each with its reason
└── evals/            # evals.json and the synthetic fixture builder under inputs/
```
