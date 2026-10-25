# development-security — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh development-security <project> <key>`, from the instance root.
The launcher reads only the lines that begin with a field's label; the field names and what each accepts
are stated in its own header.

**Agent:** senior-engineer
**Arguments:** <project> <key>
**Prompt:** invoke the development-security skill for the {project} project, change key {key}.

`senior-engineer` is the seat this skill is gated to (`SKILL.md` § *Posture*). The chain runs it as its
`security` step, after `code-integrity`. The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file.
