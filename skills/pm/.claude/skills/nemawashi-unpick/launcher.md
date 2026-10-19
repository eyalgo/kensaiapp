# nemawashi-unpick — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh nemawashi-unpick <project> "<reason>"`, from the instance root. The
launcher reads only the lines that begin with a field's label; the field names and what each accepts
are stated in its own header.

**Agent:** pm
**Arguments:** <project> <reason>
**Prompt:** invoke the nemawashi-unpick skill for the {project} project, with the reason "{reason}" for its commit body and its report.

`pm` is the one seat the skill runs in (`SKILL.md` § *Posture*). It carries no `intelligence/` folder, so a run starts on the provider's default model. The seed it un-picks is the single active item at that project's
`journey/nemawashi/` root, which the skill resolves itself at Step 1. The reason is why the seed is set
down; the launcher bounds it before it reaches the quoted prompt.
