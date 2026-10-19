# ad-hoc-plan — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh ad-hoc-plan <project>`, from the instance root. The launcher reads
only the lines that begin with a field's label; the field names and what each accepts are stated in its
own header.

**Agent:** tech-lead
**Arguments:** <project>
**Prompt:** invoke the ad-hoc-plan skill for the {project} project.

`tech-lead` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. The prompt names the project and nothing else: the change it
plans is the single active Tobiishi under that project's `journey/tobiishi/`, which the skill resolves
itself at Step 1. The skill's optional idea is not an argument. Unattended there are no owner words to
pass, and where none is given "the Request is the idea" (`SKILL.md` § *Inputs*).
