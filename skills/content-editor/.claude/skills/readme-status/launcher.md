# readme-status — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh readme-status <project>`, from the instance root. The
launcher reads only the lines that begin with a field's label; the field names and what each accepts
are stated in its own header.

**Agent:** content-editor
**Arguments:** <project>
**Prompt:** invoke the readme-status skill for the {project} project.

`content-editor` is the one seat the skill runs in (`SKILL.md` § *When to Use*). The run takes its model and effort from the skill's `intelligence/` file for the provider it goes to.
