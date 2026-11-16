# red-behaviour — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run: `<CORE>/launchers/skill/launcher.sh red-behaviour <project> <key>`, from the instance root. The launcher reads only the lines that begin with a field's label; the field names and what each accepts are stated in its own header.

**Agent:** qa
**Arguments:** <project> <key>
**Prompt:** invoke the red-behaviour skill for the {project} project, change key {key}.

`qa` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. The chain launches it as its `red-behaviour` step, directly after the spec, and the command above starts it by hand.
