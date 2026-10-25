# ad-hoc-plan — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh ad-hoc-plan <project>`, from the instance root. The launcher reads
only the lines that begin with a field's label; the field names and what each accepts are stated in its
own header.

**Agent:** tech-lead
**Arguments:** <project>
**Prompt:** invoke the ad-hoc-plan skill for the {project} project, unattended.

`tech-lead` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. The prompt names the project and nothing else: the change it
plans is the single active Tobiishi under that project's `journey/tobiishi/`, which the skill resolves
itself at Step 1. The brief is not an argument. Unattended there is no owner to confirm one, so the
Request is the brief, and the prompt's "unattended" is what tells the run so; a brief already
committed in the change folder is read either way (`SKILL.md` § *Inputs*).
