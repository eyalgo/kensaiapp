---
version: "1.0.0"
---

# development-implementation — Hugging Face intelligence

The model and effort a run of this skill goes at on `hf` — Claude Code aimed at Hugging Face's router.

**Model:** Qwen/Qwen3.8-2.4T-A95B:novita
**Effort:** medium

## Why

The owner's call, 2026-10-04: development runs on Qwen. Revised the same day, on the owner's approval, from `Qwen/Qwen3-Coder-Next:novita` and then
`Qwen/Qwen3-Coder-480B-A35B-Instruct:novita`, both older Qwen generations, for the work defined in
`skills/developer/.claude/skills/development-implementation/SKILL.md:L3` (frontmatter `description`).

The work is long, tool-heavy test-first coding against a Tech Lead instruction that has already settled
the design, and a later `development-code-integrity` pass on another model family validates the
result. That earns the newest and largest Qwen live on the router.

`Qwen/Qwen3.8-2.4T-A95B` (created 2026-08-08) is live on `novita` with tool calls and a 1010000-token context in
Hugging Face's catalogue (`https://router.huggingface.co/v1/models`, read 2026-10-04). The `:provider`
suffix pins the host, as `core/tools/model_assignment.py`'s `hf` table does.

The effort reaches the run twice: as `--effort` on the `claude` command and as the level in the run's
bootstrap prompt (`core/tools/agent_run.py` `_flags` and `_prompt_argument`). Whether the router turns
`--effort` into a reasoning budget for an open model is unmeasured; the prompt half is read either way.
