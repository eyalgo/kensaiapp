---
version: "1.0.0"
---

# development-implementation — Claude intelligence

The model and effort a run of this skill goes at on Claude — the file `<CORE>/launchers/skill/launcher.sh` reads.

**Model:** claude-sonnet-5-5
**Effort:** medium

## Why

This is the main developer execution skill: it critically reviews the Tech Lead instruction, runs per-task TDD cycles, repairs inherited work, enforces verification gates, manages pause/continue behavior across context caps, and produces the self-owned closing commit. Sonnet at medium effort carries it, because the Tech Lead instruction has already settled the design and a later Senior Engineer `development-code-integrity` pass independently validates the result. The owner's call, 2026-10-01.
