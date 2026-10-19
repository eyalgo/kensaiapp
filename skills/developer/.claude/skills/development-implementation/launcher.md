# development-implementation — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh development-implementation <project> <key> [<after>]`, from the instance root.
The launcher reads only the lines that begin with a field's label; the field names and what each accepts
are stated in its own header.

**Agent:** developer
**Arguments:** <project> <key> [<after>]
**Prompt:** invoke the development-implementation skill for the {project} project, change key {key}.[ Tasks 1–{after} are committed; start at task {after}+1.]

`<after>` is the number of the last task already committed. The chain fills it from one of two places
(`<CORE>/tools/chain_development.py`): after a pause, from that run's pause commit
(`developer: <key> — implementation paused after task <N>`), and at a start, from the change branch's
landing commits (`DiskReader.resume_after`). A first launch with no task landed gives none, and the
bracketed segment is dropped whole, so the prompt is the one it always was. The launcher substitutes text and does not compute, so the prompt says
`{after}+1` and the run reads the task number off it (`SKILL.md` Step 2, the launch prompt's batch scope).

`developer` is the seat the chain runs this step in (`<CORE>/tools/chain_development.py`
`DEVELOPMENT_STEPS`). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file.
