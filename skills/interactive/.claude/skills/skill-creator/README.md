# skill-creator

Creating a skill is easy. Creating a skill that *actually works* — triggers when it should, produces better results than without it, and improves measurably over iterations — requires a systematic loop. skill-creator provides that loop: draft → eval → benchmark → optimize → iterate, with quantitative feedback at each step.

## What It Does

- **Create new skills from scratch** — guided interview, SKILL.md draft, test cases, first eval run
- **Improve existing skills** — load a skill, run evals against it, benchmark, optimize
- **Measure skill performance** — parallel with-skill and without-skill subagent runs, graded with assertions, aggregated into benchmark.json with pass rate, time, and token variance
- **Optimize trigger accuracy** — description optimization loop using Claude with extended thinking; 60/40 train/test split to prevent overfitting; up to 5 iterations
- **Blind A/B comparison** — independent comparator agent scores two skill versions with rubric scoring (content + structure, 1–5 scale)
- **Interactive eval review** — browser-based viewer (Outputs + Benchmark tabs) for reviewing runs and editing trigger/not-trigger query sets

## Core Loop

```
Draft/Load skill
      ↓
Write test cases → evals/evals.json
      ↓
Spawn subagents in parallel:
  with_skill run + baseline run (per test case)
      ↓
Draft assertions while runs complete
      ↓
Grade with agents/grader.md → grading.json
      ↓
Aggregate → benchmark.json + benchmark.md
      ↓
Analyst pass → agents/analyzer.md
      ↓
Launch eval-viewer/generate_review.py → browser
      ↓
User reviews outputs + benchmark tabs
      ↓
Read feedback.json → improve skill
      ↓
Repeat (next iteration-N/)
      ↓
Offer description optimization (.claude/scripts/run_loop.py)
      ↓
Optional: blind comparison (agents/comparator.md)
      ↓
Package (skill-creator/scripts/package_skill.py)
```

## File Structure

```
skill-creator/
├── SKILL.md                          # Main workflow instructions
├── README.md                         # This file
├── agents/
│   ├── analyzer.md                   # Benchmark analysis + blind comparison analysis
│   └── comparator.md                 # Blind A/B rubric scoring
├── references/
│   ├── schemas.md                    # JSON schemas (evals, grading, benchmark, etc.)
│   └── claude-superskills-conventions.md  # claude-superskills package conventions
└── assets/
    └── eval_review.html              # Trigger eval review/edit UI template
```

Scripts (aggregation, optimization loop, trigger eval, packaging) live in the `skill-evals` companion skill.

## Depends On

- `skill-evals` — runs the benchmark eval loop: eval runner, grader, aggregator, eval viewer, and description optimization scripts

## When to Use

Use skill-creator when you want to build a new skill from scratch, systematically improve an existing one, or measure whether a skill is actually making a difference. If you have a workflow you want to teach Claude, or a skill that doesn't trigger reliably, start here.

## Based On

Adapted from the [Anthropic official skill-creator](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator) (original by Eric Andrade). Agents and eval-viewer are included from the upstream; scripts have been consolidated into the companion `skill-evals` skill and extended.
