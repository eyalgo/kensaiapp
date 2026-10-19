---
version: "1.0.0"
---

# development-plan — Hugging Face intelligence

The model and effort a run of this skill goes at on `hf` — Claude Code aimed at Hugging Face's router.

**Model:** zai-org/GLM-5.3:novita
**Effort:** high

## Why

Proposed 2026-10-04 and approved by the owner, for the work defined in `skills/tech-lead/.claude/skills/development-plan/SKILL.md:L3`
(frontmatter `description`).

The work is a critical review of a design against its spec and a placement decision for every new piece of logic, written into the instruction the developer builds from. A plan error is built as-is, so the work earns a strong general reasoner rather than a coding specialist.

`zai-org/GLM-5.3` is live on `novita` with tool calls and a 1048576-token context in Hugging Face's catalogue (`https://router.huggingface.co/v1/models`, read 2026-10-04). The `:provider` suffix pins the host, as
`core/tools/model_assignment.py`'s `hf` table does.

The effort reaches the run twice: as `--effort` on the `claude` command and as the level in the run's bootstrap prompt (`core/tools/agent_run.py` `_flags` and `_prompt_argument`). Whether the router turns `--effort` into a reasoning budget for an open model is unmeasured; the prompt half is read either way.
