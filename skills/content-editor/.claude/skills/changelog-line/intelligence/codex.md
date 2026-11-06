---
version: "1.0.2"
---

# changelog-line — Codex intelligence

This file owns this skill's Codex model and effort selection.

**Model:** gpt-6.1-sol
**Effort:** medium

## Why

I take `gpt-6.1-sol` because the skill's first job is a judgement: comparing a what-left want with built work and removing the entry only when the whole want is built. Its second job, writing a changelog entry from a branch diff, is a short piece of user-facing prose to a grammar the template fixes. Medium effort fits work that is bounded to the changelogs of the product paths the change touches and one what-left file, where each cited commit is checkable on the branch. The step runs on every change and most changes earn little to write, so a higher effort would be spent where it buys nothing. Selection guidance: [OpenAI models — Choosing a model and Pick a reasoning effort](https://learn.chatgpt.com/docs/models#choosing-a-model).
