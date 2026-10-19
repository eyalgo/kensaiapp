# nemawashi-pick — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh nemawashi-pick <project>`, from the instance root. The launcher
reads only the lines that begin with a field's label; the field names and what each accepts are
stated in its own header.

**Agent:** pm
**Arguments:** <project>
**Prompt:** invoke the nemawashi-pick skill for the {project} project.

`pm` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. The prompt names the project and nothing else: the seed it picks
is chosen from that project's `journey/nemawashi/unpicked/` pool by the skill's own prompt at Step 2,
and its script refuses a pick that may not be made.
