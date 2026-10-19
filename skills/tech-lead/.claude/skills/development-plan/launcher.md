# development-plan — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh development-plan <project> <key>`, from the instance root. The
launcher reads only the lines that begin with a field's label; the field names and what each accepts
are stated in its own header.

**Agent:** tech-lead
**Arguments:** <project> <key>
**Prompt:** invoke the development-plan skill for the {project} project, change key {key}.

`tech-lead` is the seat the chain runs this step in (`<CORE>/tools/chain_development.py`
`DEVELOPMENT_STEPS`, `:117-129`). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file.
