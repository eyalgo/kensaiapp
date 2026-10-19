# product-uxd — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh product-uxd <project>`, from the instance root. The launcher reads
only the lines that begin with a field's label; the field names and what each accepts are stated in its
own header.

**Agent:** cdo
**Arguments:** <project>
**Prompt:** invoke the product-uxd skill for the {project} project.
**Reporter:** uxd
**Reads:** product

`cdo` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. The prompt names the project and nothing else: where the files land
is the project's Product path, which the skill resolves itself.

The completion message is the `uxd` reporter's, reading the project's Product path.
