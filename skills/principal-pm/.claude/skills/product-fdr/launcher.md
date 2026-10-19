# product-fdr — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh product-fdr <project>`, from the instance root. The launcher reads
only the lines that begin with a field's label; the field names and what each accepts are stated in its
own header.

**Agent:** principal-pm
**Arguments:** <project>
**Prompt:** invoke the product-fdr skill for the {project} project.
**Reporter:** fdr
**Reads:** product

`principal-pm` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. The prompt names the
project and nothing else: where the files land is the project's Product path, which the skill resolves
itself.

The completion message is the `fdr` reporter's, reading the project's Product path.
