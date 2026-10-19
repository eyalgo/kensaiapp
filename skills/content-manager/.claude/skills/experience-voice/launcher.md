# experience-voice — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh experience-voice`, from the instance root. The launcher
reads only the lines that begin with a field's label; the field names and what each accepts are stated
in its own header.

**Agent:** content-manager
**Prompt:** invoke the experience-voice skill.
**Reporter:** experience-voice
**Reads:** instance

`content-manager` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are
`intelligence/<provider>.md`'s, beside this file. The run takes no
argument: the instance is the one it is started in, and where the files land is that instance's own
`system/experience/`, which the skill resolves itself.

The completion message is the `experience-voice` reporter's, reading the instance root.
