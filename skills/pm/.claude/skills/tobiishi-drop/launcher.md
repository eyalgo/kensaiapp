# tobiishi-drop — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh tobiishi-drop <project> <key> "<reason>"`, from the instance root.
The launcher reads only the lines that begin with a field's label; the field names and what each
accepts are stated in its own header.

**Agent:** pm
**Arguments:** <project> <key> <reason>
**Prompt:** invoke the tobiishi-drop skill for the {project} project, change key {key}, reason "{reason}".

`pm` is the one seat the skill runs in (`SKILL.md` § *Posture*). It carries no `intelligence/` folder, so a run starts on the provider's default model. The reason is the
caller's own words in double quotes: the skill never composes one and has no default.
