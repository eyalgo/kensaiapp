# development-specs — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh development-specs <project>`, from the instance root. The launcher
reads only the lines that begin with a field's label; the field names and what each accepts are stated
in its own header.

**Agent:** product-owner
**Arguments:** <project>
**Prompt:** invoke the development-specs skill for the {project} project.

`product-owner` is the one seat the skill runs in (`SKILL.md` § *Input*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. The skill finds the single active change itself (`SKILL.md` § *Input*), so the prompt names no
key.
