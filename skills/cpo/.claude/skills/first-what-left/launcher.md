# first-what-left — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh first-what-left <project>`, from the instance root. The launcher reads
only the lines that begin with a field's label; the field names and what each accepts are stated in its
own header.

**Agent:** cpo
**Arguments:** <project>
**Prompt:** invoke the first-what-left skill for the {project} project.

`cpo` is the one seat the skill runs in (`SKILL.md` § *When to Use*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. The prompt names the project and nothing else: the file the run writes is that project's product's `docs/what_left.md` (`SKILL.md` § *Workflow*).
