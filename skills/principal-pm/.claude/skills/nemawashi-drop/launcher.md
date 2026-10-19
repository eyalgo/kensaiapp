# nemawashi-drop — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh nemawashi-drop <project> <slug> "<reason>"`, from the instance
root. The launcher reads only the lines that begin with a field's label; the field names and what each
accepts are stated in its own header.

**Agent:** principal-pm
**Arguments:** <project> <slug> <reason>
**Prompt:** invoke the nemawashi-drop skill for the {project} project, killing the seed {slug}, reason "{reason}".

`principal-pm` is the one seat the skill runs in (`SKILL.md` § *Posture*). It carries no `intelligence/` folder, so a run starts on the provider's default model. The prompt says the kill
and carries the reason, which closes both halves of Step 1A: the reason is the caller's own words in
double quotes, and the skill never composes one. The caller writes the whole command.

**A project seed only.** The skill also takes an instance seed at `system/nemawashi/`, and this
declaration does not reach one: `<project>` is required. An instance seed is dropped from a
`principal-pm:` session instead.
