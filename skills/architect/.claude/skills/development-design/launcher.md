# development-design — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh development-design <project> <key>`, from the instance root. The
launcher reads only the lines that begin with a field's label; the field names and what each accepts
are stated in its own header.

**Agent:** architect
**Arguments:** <project> <key>
**Prompt:** invoke the development-design skill for the {project} project, change key {key}.

`architect` is the one seat the skill runs in (`SKILL.md` § *When to Use*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file.
