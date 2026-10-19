# skill-evals

**Benchmark any Claude Code skill with parallel baselines, tiered grading, and a browser-based reviewer.**

`skill-evals` is a standalone benchmarking harness for measuring whether a skill actually improves Claude's outputs. Given a skill and a set of test prompts, it runs with-skill and without-skill agents in parallel, grades outputs against typed assertions, aggregates results into a benchmark, and opens an interactive review UI.

## Why It Exists

Writing a skill is easy. Knowing if it works — and by how much — is harder. `skill-evals` gives you a quantitative before/after measurement so skill improvement is iterative rather than guesswork.

## Core Loop

```
Load evals.json
     ↓
Spawn in parallel for each test case:
  with_skill agent  +  without_skill (baseline) agent
     ↓
Draft assertions while runs are in progress  ← no idle time
     ↓
Grade in parallel:
  structural tier (Haiku)  +  nuanced tier (Sonnet)
     ↓
Merge → grading.json
     ↓
Aggregate → benchmark.json + benchmark.md
     ↓
Launch browser reviewer (Outputs + Benchmark tabs)
     ↓
Read feedback.json → skill-creator picks up improvements
```

## Key Design Decisions

**Tiered grading.** Assertions carry a required `tier` field — `"structural"` or `"nuanced"`. Structural checks (file presence, section headers, absent placeholder text) run on Haiku for speed. Nuanced checks (architectural correctness, layer isolation, semantic quality) run on Sonnet for depth. Both graders run in parallel; results are merged into a single `grading.json`.

**Always-parallel baselines.** Every eval run spawns a `without_skill` agent alongside the `with_skill` run. You measure the delta, not the absolute score. This guards against test prompts that are easy regardless of the skill.

**Assertions during runs.** The grading step doesn't wait for runs to complete. While subagents execute, assertions are drafted from `evals.json` and reviewed with the user — no dead time between spawn and grade.

**Self-contained.** Scripts (aggregation, optimization loop, trigger eval, packaging), the grader agent, and the eval viewer all live here. `skill-evals` runs independently — no other skill required.

## File Structure

```
skill-evals/
├── SKILL.md                         # Workflow instructions for Claude
├── agents/
│   └── grader.md                    # Grades assertions against transcripts and outputs
├── eval-viewer/
│   ├── generate_review.py           # Serves browser review UI (Outputs + Benchmark tabs)
│   └── viewer.html                  # Viewer HTML template
└── scripts/
    └── aggregate_benchmark.py        # Rolls up grading.json → benchmark.json + .md
```

The optimization scripts and the packaging scripts no longer live under
`skill-evals/scripts/` — they were relocated so no skill reaches into a sibling's
`scripts/` folder. They now live in two other homes:

```
.claude/scripts/                     # neutral shared home (the run_loop cluster)
├── run_eval.py                       # Trigger eval runner (claude -p subprocess)
├── run_loop.py                       # Description optimization loop (60/40 train/test)
├── improve_description.py            # Claude extended-thinking description improver
├── generate_report.py                # HTML report for the optimization loop
└── utils.py                          # Shared helpers

skills/interactive/.claude/skills/skill-creator/scripts/ # skill-creator owns these
├── package_skill.py                  # Creates distributable .skill files
└── quick_validate.py                 # Validates SKILL.md frontmatter
```

Eval workspace for a skill lives inside the skill directory:

```
<skill-dir>/
└── evals/
    ├── evals.json                    # Test definitions: prompt, assertions, tier
    └── workspace/
        └── iteration-N/
            ├── <eval-name>/
            │   ├── eval_metadata.json
            │   ├── with_skill/       # outputs/, grading.json, timing.json
            │   └── without_skill/    # outputs/, grading.json, timing.json
            ├── benchmark.json
            ├── benchmark.md
            └── feedback.json         # Written by the browser reviewer
```

## Usage

```bash
# Aggregate grading results into a benchmark
cd "<CORE>/../skills/experimental/.claude/skills/skill-evals"
python -m scripts.aggregate_benchmark \
  <skill-dir>/evals/workspace/iteration-1 \
  --skill-name <skill-name>

# Run description optimization loop (now in the .claude shared home)
cd "${CLAUDE_PROJECT_DIR}/.claude"
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model claude-sonnet-4-6 \
  --max-iterations 5 \
  --verbose

# Validate SKILL.md frontmatter before packaging (now owned by skill-creator)
cd "<CORE>/../skills/interactive/.claude/skills/skill-creator"
python -m scripts.quick_validate <path-to-skill>

# Package a skill into a distributable .skill file (now owned by skill-creator)
python -m scripts.package_skill <path/to/skill-folder>
```

## Dependencies

No external skills required. All components are bundled:
- `agents/grader.md` — grades assertions against transcripts and output files
- `eval-viewer/generate_review.py` — serves the browser-based review UI
- `scripts/` — aggregation, optimization loop, trigger eval, packaging

## Metadata

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Created | 2026-05-30 |
| Updated | 2026-05-30 |
| Platforms | Claude Code |
| Category | meta |
| Tags | evals, benchmarking, skill-testing, description-optimization |
| Risk | safe |
