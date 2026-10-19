---
version: "1.0.0"
---

# ad-hoc-plan — Gemini intelligence

This file owns this skill's Gemini model and effort selection.

**Model:** gemini-3.1-pro-low
**Effort:** low

## Why

The owner's call, 2026-10-17: this skill runs at Opus, medium effort. `gemini-3.1-pro-low` is the
model `core/doctrine/governance/model_assignment.md` binds the Opus tier to on Gemini. Gemini's Pro
model is catalogued at `-low` and `-high` only, so there is no medium to take, and the Opus tier's
binding is the nearest. There is no cross-vendor table
(`core/doctrine/governance/skill_intelligence.md` § *Where a skill declares it*); the tier is the
starting point for the decision made here.
