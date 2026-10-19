---
version: "1.0.0"
---

# development-audit — Hugging Face intelligence

The model and effort a run of this skill goes at on `hf` — Claude Code aimed at Hugging Face's router.

**Model:** moonshotai/Kimi-K3:together
**Effort:** high

## Why

Proposed 2026-10-04 and approved by the owner, for the work defined in `skills/kensaiapp-auditor/.claude/skills/development-audit/SKILL.md:L3-L7`
(frontmatter `description`).

The work is a blind read for flow defects that the step's own author missed — coverage gaps, altitude leaks, coincidental contracts. It fans out to five runs at once, each of them long, so what a run costs decides whether a walk finishes at all.

Moved 2026-10-05, on the owner's approval, from `deepseek-ai/DeepSeek-V4-Pro-0813:novita`. The account's Inference Providers usage page (`https://huggingface.co/settings/inference-providers/overview`, read 2026-10-05) billed DeepSeek-V4-Pro-0813 $24.28 for 304 requests across one audit fan-out, which ran the monthly credit out twice, and Kimi-K3 $0.39 for 40 requests across a whole `development-code-integrity` run. Kimi-K3 is the model `development-code-integrity` already runs on, the closest work to this one; the price of that is losing a model family the integrity checker does not share.

`moonshotai/Kimi-K3` is live on `together` with tool calls in Hugging Face's catalogue (`https://router.huggingface.co/v1/models`, read 2026-10-04), and answered a one-token probe there on 2026-10-05; `fireworks-ai` refuses pay-as-you-go on this account. The `:provider` suffix pins the host, as `core/tools/model_assignment.py`'s `hf` table does.

The effort reaches the run twice: as `--effort` on the `claude` command and as the level in the run's bootstrap prompt (`core/tools/agent_run.py` `_flags` and `_prompt_argument`). Whether the router turns `--effort` into a reasoning budget for an open model is unmeasured; the prompt half is read either way.
