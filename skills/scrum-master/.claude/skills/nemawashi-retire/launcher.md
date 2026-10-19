# nemawashi-retire — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh nemawashi-retire <project>`, from the instance root. The launcher
reads only the lines that begin with a field's label; the field names and what each accepts are
stated in its own header.

**Agent:** scrum-master
**Arguments:** <project>
**Prompt:** invoke the nemawashi-retire skill for the {project} project.

`scrum-master` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. It is launched by hand.
The prompt names the project and nothing else: the seed it retires is the single item at that project's
`journey/nemawashi/` root, which the skill resolves itself at Step 1.

**The gates may stop the run.** A seed with open items, no checklist, or an open station or change
unit halts it with the reason in its log — the same halt any caller gets, reached with no one reading.
