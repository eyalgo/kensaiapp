# refactor-for-optimize

Improves the performance profile of working code — without changing what it does. Covers algorithmic complexity, data structure selection, unnecessary I/O, hot-path improvement, and memory usage. The skill ensures the optimizer fixes the right thing (algorithm before constant-factor tuning) and doesn't undo prior clarity or reuse improvements in the process.

## What It Does

- Identifies the correct bottleneck (algorithmic, data structure, I/O, or memory) before touching code
- Applies the highest-leverage fix first — algorithm before constant-factor tuning
- Preserves behavior exactly: all tests pass, signatures unchanged, edge cases intact
- Treats extracted helpers as non-negotiable — optimizes helper *bodies*, never inlines or removes them
- Names the complexity gain explicitly (e.g., "O(n²) → O(n)") so the improvement is auditable

## File Structure

```
refactor-for-optimize/
├── SKILL.md          — skill instructions and language-specific patterns
├── README.md         — this file
└── evals/
    └── evals.json    — 5 benchmark cases: set lookup, string building + regex,
                        loop hoisting, helper-body optimization, shared-call hoisting
```

## When to Use

- In the REFACTOR phase of TDD when the developer identifies a measurable hot path
- When profiling reveals a specific function or loop is the bottleneck
- When algorithmic complexity is clearly wrong (O(n²) scan that should be O(1) set lookup)
- When unnecessary I/O occurs inside a loop (N+1 reads, repeated pure computations, `re.compile` inside a function)
- When string building inside a loop creates O(n²) allocation pressure

**Not for:** naming/nesting/structural issues (→ `refactor-for-clarity`), duplication/dead code (→ `refactor-for-reuse`), or code that isn't correct yet.
