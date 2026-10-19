# experience-visual — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh experience-visual`, from the instance root. The launcher
reads only the lines that begin with a field's label; the field names and what each accepts are stated
in its own header.

**Agent:** cdo
**Prompt:** invoke the experience-visual skill.
**Reporter:** experience-visual
**Reads:** instance
**Requires:** npx node

`cdo` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are
`intelligence/<provider>.md`'s, beside this file. The run takes no argument: the
instance is the one it is started in, and where the files land is that instance's own
`system/experience/`, which the skill resolves itself.

`npx` and `node` are required because the skill's machine gate shells out to
`npx @google/design.md@<version> lint`; an unattended run without them would reach that step with
nothing to run.

The completion message is the `experience-visual` reporter's, reading the instance root.
