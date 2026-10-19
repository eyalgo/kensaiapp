# shukuba-refine — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh shukuba-refine <project> [<unit-key>]`, from the instance root. The
launcher reads only the lines that begin with a field's label; the field names and what each accepts
are stated in its own header.

**Agent:** pm
**Arguments:** <project> [<unit-key>]
**Prompt:** invoke the shukuba-refine skill for the {project} project[, reviewing the sealed or halted unit {unit-key}].
**Reporter:** shukuba-refine
**Reads:** project

`pm` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. The unit key is optional because the skill has its own answer
without one — the unit `contexts/CONTEXT_PM.md` names as sealed, or a stop saying which is missing
(`SKILL.md` § *Input*) — so the prompt names the key only when the caller gives one, and leaves the
rest to that section.

The completion message is the `shukuba-refine` reporter's (`<CORE>/tools/reporters.py`). It reads the
project's directory for the report this run committed and puts that report's `## Next moves` in the
message — each move, whose it is and its command — so the owner learns what to launch without opening
the file. A run that committed nothing, or committed no report, says that instead.
