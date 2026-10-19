# project-agari — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh project-agari <project>`, from the instance root. The launcher reads
only the lines that begin with a field's label; the field names and what each accepts are stated in its
own header.

**Agent:** cpo
**Arguments:** <project>
**Prompt:** invoke the project-agari skill for the {project} project.
**Reporter:** agari
**Reads:** project

`cpo` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. The prompt names the project and nothing else: the file it fills is
that project's `agari.md` in this instance (`SKILL.md` § *The files and the loop*).

The completion message is the `agari` reporter's, reading the project's own directory, where `agari.md`
lives.
