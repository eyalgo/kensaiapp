---
version: "1.0.0"
---

# stations-from-seed — Ollama intelligence

The model a run of this skill goes at on `ollama` — Claude Code aimed at the Ollama server on the
owner's own machine.

**Model:** qwen3-coder:30b

## Why

The owner's call, 2026-10-08: every skill with an `intelligence/` folder runs on a local model when
routed to `ollama`. This skill's `claude.md` names `claude-sonnet-5-5`, so it takes the model
`core/tools/model_assignment.py`'s `ollama` table gives the sonnet tier. There is no cross-vendor
table (`core/doctrine/governance/skill_intelligence.md` § *Where a skill declares it*); the tier is
the starting point for a decision made here, in this file.

No effort is set. Whether Ollama turns Claude Code's `--effort` into a thinking budget is unmeasured.
