---
version: "1.0.0"
---

# ad-hoc-plan — Hugging Face intelligence

The model and effort a run of this skill goes at on `hf` — Claude Code aimed at Hugging Face's router.

**Model:** zai-org/GLM-5.3:novita
**Effort:** medium

## Why

The owner's call, 2026-10-17: this skill runs at Opus, medium effort. `zai-org/GLM-5.3:novita` is
the model `core/tools/model_assignment.py`'s `hf` table gives the opus tier, and the one
`development-plan` runs on here. There is no cross-vendor table
(`core/doctrine/governance/skill_intelligence.md` § *Where a skill declares it*); the tier is the
starting point for the decision made here.

The effort reaches the run twice: as `--effort` on the `claude` command and as the level in the run's bootstrap prompt (`core/tools/agent_run.py` `_flags` and `_prompt_argument`). Whether the router turns `--effort` into a reasoning budget for an open model is unmeasured; the prompt half is read either way.
