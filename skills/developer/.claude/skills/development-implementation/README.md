---
version: "1.1.0"
---

# Development implementation

Use this skill for the developer stage of a change. Its input contract, execution
procedure, invoked skills and closing records are owned by [SKILL.md](SKILL.md).

- [SKILL.md](SKILL.md) — the developer workflow.
- [launcher.md](launcher.md) — unattended invocation and batch arguments.
- [evals/evals.json](evals/evals.json) — read-only execution-decision cases; these do not substitute for a live chain run.

The change pipeline and its sequencing live in
`<CORE>/tools/chain_development.py`; this folder supplies the implementation step.
