# dependency-repair — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh dependency-repair <project>`, from the instance root. The launcher
reads only the lines that begin with a field's label; the field names and what each accepts are stated
in its own header.

**Agent:** senior-engineer
**Arguments:** <project>
**Prompt:** invoke the dependency-repair skill for the {project} project.

`senior-engineer` is the seat this skill is gated to (`SKILL.md` § *Posture*). This launch is a first run
on a red `main`; a relaunch carries the owner's answers to a report's questions (`SKILL.md` § *Input*),
which this prompt does not, so a relaunch is started from a `senior-engineer:` session. The model and
effort it runs on are `intelligence/<provider>.md`'s, beside this file.
