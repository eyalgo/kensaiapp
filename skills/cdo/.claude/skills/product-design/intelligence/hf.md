---
version: "1.0.0"
---

# product-design — Hugging Face intelligence

The model and effort a run of this skill goes at on `hf` — Claude Code aimed at Hugging Face's router.

**Model:** zai-org/GLM-5.3:novita
**Effort:** high

## Why

Proposed 2026-10-04 and approved by the owner, for the work defined in `skills/cdo/.claude/skills/product-design/SKILL.md:L3`
(frontmatter `description`).

The work designs a visual language in DESIGN.md format, grounded in evidence where it exists and invented where it does not, and implementing agents read it cold. It is a high-judgement document, and runs on a family other than `product-uxd`'s so the UXD it builds on gets a second reader.

`zai-org/GLM-5.3` is live on `novita` with tool calls and a 1048576-token context in Hugging Face's catalogue (`https://router.huggingface.co/v1/models`, read 2026-10-04). The `:provider` suffix pins the host, as
`core/tools/model_assignment.py`'s `hf` table does.

The effort reaches the run twice: as `--effort` on the `claude` command and as the level in the run's bootstrap prompt (`core/tools/agent_run.py` `_flags` and `_prompt_argument`). Whether the router turns `--effort` into a reasoning budget for an open model is unmeasured; the prompt half is read either way.
