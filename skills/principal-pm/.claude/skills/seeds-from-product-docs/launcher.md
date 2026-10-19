# seeds-from-product-docs — unattended launch

What `<CORE>/launchers/skill/launcher.sh` reads to start this skill as a detached run:
`<CORE>/launchers/skill/launcher.sh seeds-from-product-docs <project>`, from the instance root. The
launcher reads only the lines that begin with a field's label; the field names and what each accepts
are stated in its own header.

**Agent:** principal-pm
**Arguments:** <project>
**Prompt:** invoke the seeds-from-product-docs skill for the {project} project.

`principal-pm` is the one seat the skill runs in (`SKILL.md` § *Posture*). The model and effort it runs on are `intelligence/<provider>.md`'s, beside this file. It is launched by hand.
The prompt names the project and nothing else: the product
whose documents are cut is the one that project's card names, which the skill resolves itself at
Step 2.

**The product grant is best-effort.** A card with no `Product path:` line, or one naming a directory
that is not there, warns at launch and the run starts anyway; the skill checks the product path holds
what its lens draws from and halts there with the reason in its log (`SKILL.md` § *What this run is
given, and how it resolves it*).
