# stations-blind-review — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh stations-blind-review <project>`, from the instance root. The
launcher reads only the lines that begin with a field's label; the field names and what each accepts
are stated in its own header.

**Agent:** pm
**Arguments:** <project>
**Prompt:** invoke the stations-blind-review skill for the {project} project.

`pm` is the one seat the skill runs in (`SKILL.md` § *Posture*). A detached run is a fresh process,
which is what makes the review blind. The model and effort it runs on are `intelligence/<provider>.md`'s,
beside this file. The prompt names the project and nothing else: the seed it reviews is the single
picked item at that project's `journey/nemawashi/` root, which the skill resolves itself at Step 1.
