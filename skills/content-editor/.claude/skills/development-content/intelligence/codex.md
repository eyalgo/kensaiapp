---
version: "1.0.0"
---

# development-content — Codex intelligence

This file owns this skill's Codex model and effort selection.

**Model:** gpt-6.1-sol
**Effort:** high

## Why

Chosen by the design of the change that added this step (`change_design.md` § Architect Review Notes, *Intelligence*), not by the vendor: the Content Editor is the last quality gate on the words, and nothing downstream re-judges the prose, so its output is consumed as authored. High effort fits that judgement work, and the step runs only on a change that publishes text, which bounds the cost. All three vendors carry a file for parity, so a forced walk is not refused at this step.
