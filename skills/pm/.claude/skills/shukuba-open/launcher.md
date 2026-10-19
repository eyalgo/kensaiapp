# shukuba-open — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh shukuba-open <project>`, from the instance root. The launcher
reads only the lines that begin with a field's label; the field names and what each accepts are
stated in its own header.

**Agent:** pm
**Arguments:** <project>
**Prompt:** invoke the shukuba-open skill for the {project} project.

`pm` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. The prompt names the project and nothing else: the station it
opens is the next unticked item on that project's active seed, which the skill's script resolves
itself at Step 1.
