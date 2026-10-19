# nemawashi-refine — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh nemawashi-refine <project> [<seed>]`, from the instance root. The
launcher reads only the lines that begin with a field's label; the field names and what each accepts
are stated in its own header.

**Agent:** principal-pm
**Arguments:** <project> [<seed>]
**Prompt:** invoke the nemawashi-refine skill for the {project} project[, answering the retired seed {seed}].

`principal-pm` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. The seed is optional
because the skill has its own answer without one — the seed the project's latest retire commit names
(`SKILL.md` § *Input*) — so the prompt names it only when the caller gives one.

It declares no Reporter, so the completion message is the `generic` one; the next moves are the
report's `## Next moves`, at `system/projects/<project>/docs/nemawashi-refine/<seed>_report.md`.

**The gates may stop the run.** A seed not in `trail/`, or a project with no retire commit and no
seed named, halts it with the reason in its log.
