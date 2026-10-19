---
version: "1.0.0"
---

# development-code-integrity — Hugging Face intelligence

The model and effort a run of this skill goes at on `hf` — Claude Code aimed at Hugging Face's router.

**Model:** moonshotai/Kimi-K3:together
**Effort:** high

## Why

Proposed 2026-10-04 and approved by the owner, for the work defined in `skills/senior-engineer/.claude/skills/development-code-integrity/SKILL.md:L3-L6`
(frontmatter `description`).

The work decides whether a red test or the code is wrong, derives tests from intent rather than from the implementation, and is the last proof before the seal. Its value is independence from the implementer, so it runs on a model family other than the one `hf.md` gives `development-implementation`.

`moonshotai/Kimi-K3` is live on `together` with tool calls and a 1048576-token context in Hugging Face's catalogue (`https://router.huggingface.co/v1/models`, read 2026-10-04). The `:provider` suffix pins the host, as
`core/tools/model_assignment.py`'s `hf` table does.

The effort reaches the run twice: as `--effort` on the `claude` command and as the level in the run's bootstrap prompt (`core/tools/agent_run.py` `_flags` and `_prompt_argument`). Whether the router turns `--effort` into a reasoning budget for an open model is unmeasured; the prompt half is read either way.
