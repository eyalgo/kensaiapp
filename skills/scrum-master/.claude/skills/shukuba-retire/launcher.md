# shukuba-retire — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh shukuba-retire <project> [<station>]`, from the instance root. The launcher
reads only the lines that begin with a field's label; the field names and what each accepts are
stated in its own header.

**Agent:** scrum-master
**Arguments:** <project> [<station>]
**Prompt:** invoke the shukuba-retire skill for the {project} project[, closing the station {station}].

`scrum-master` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. The prompt names the
project, and the station's dated stem when the caller gives one; which station the run closes is
what the skill's Step 1 script prints, from the stem or from the project alone.
