---
version: "1.0.0"
---

# red-behaviour — Claude intelligence

The model and effort a run of this skill goes at on Claude — the file `<CORE>/launchers/skill/launcher.sh` reads.

**Model:** claude-opus-5-5
**Effort:** high

## Why

The scenarios QA describes are acted on as written: the design step makes their behaviour testable from outside, and each new or changed scenario must fail on the code before the change. A scenario that would already pass there proves nothing the change did. Selected in the design of the change that added this skill, 2026-11-13: the top tier other skills give a judgment whose output is acted on as written, as `stations-blind-review` and `development-design` do. A run of this skill has not been measured.
