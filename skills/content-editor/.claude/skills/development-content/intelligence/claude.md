---
version: "1.0.0"
---

# development-content — Claude intelligence

The model and effort a run of this skill goes at on Claude — the file `<CORE>/launchers/skill/launcher.sh` reads.

**Model:** claude-opus-5-5
**Effort:** high

## Why

Chosen by the design of the change that added this step (`change_design.md` § Architect Review Notes, *Intelligence*), not by the vendor: the Content Editor is the last quality gate on the words, and nothing downstream re-judges the prose, so its output is consumed as authored. Opus at high effort fits that judgement work, and the step runs only on a change that publishes text, which bounds the cost.
