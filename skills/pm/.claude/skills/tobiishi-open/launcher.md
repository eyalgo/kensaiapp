# tobiishi-open — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh tobiishi-open <project>`, from the instance root. The launcher
reads only the lines that begin with a field's label; the field names and what each accepts are
stated in its own header.

**Agent:** pm
**Arguments:** <project>
**Prompt:** invoke the tobiishi-open skill for the {project} project.

`pm` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. The prompt names the project and nothing else: which path the run
takes — the change an open station determines, or the one next move when none is open — is the
skill's own Step 3, and it asks nothing on either.
