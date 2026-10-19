# development-audit — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh development-audit <project> <key> <step>`, from the instance root —
one run per audited step. The launcher reads only the lines that begin with a field's label; the field
names and what each accepts are stated in its own header.

**Agent:** kensaiapp-auditor
**Arguments:** <project> <key> <step>
**Prompt:** invoke the development-audit skill for the {project} project, change key {key}, auditing {step}.

`kensaiapp-auditor` is the seat the chain runs every audit in (`<CORE>/tools/chain_development.py`
`DEVELOPMENT_STEPS`). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. `<step>` is one of
`development-specs`, `development-design`, `development-plan`, `development-content` (only when the change
ran it) or `development-implementation` (`SKILL.md` § *Input*).
