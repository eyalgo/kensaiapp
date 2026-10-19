<!-- Changed from Anthropic's skill-creator (Apache-2.0, https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator); this file is not the original. -->

# JSON Schemas

This document defines the JSON schemas used by skill-evals.

---

## evals.json

Defines the evals for a skill. Located at `evals/evals.json` within the skill directory.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "name": "basic-case",
      "prompt": "User's example prompt",
      "expected_output": "Description of expected result",
      "files": ["evals/files/sample1.pdf"],
      "assertions": [
        {
          "name": "output-file-exists",
          "description": "The output includes a correctly named file",
          "tier": "structural"
        },
        {
          "name": "content-is-correct",
          "description": "The output content is semantically correct and complete",
          "tier": "nuanced"
        }
      ]
    }
  ]
}
```

**Fields:**
- `skill_name`: Name matching the skill's frontmatter
- `evals[].id`: Unique integer identifier
- `evals[].name`: Kebab-case eval name (used as directory name in workspace)
- `evals[].prompt`: The task to execute
- `evals[].expected_output`: Human-readable description of success
- `evals[].files`: Optional list of input file paths (relative to skill root)
- `evals[].assertions[]`: List of assertions to grade
  - `name`: Kebab-case assertion identifier
  - `description`: The verifiable statement (translated to `text` when passed to grader)
  - `tier`: `"structural"` (graded by Haiku — file presence, section headers, absent placeholder text) or `"nuanced"` (graded by Sonnet — architectural correctness, semantic quality, layer isolation)

---

## grading.json

Output from the grader agent. Located at `<eval-name>/{with_skill|without_skill}/grading.json`.

```json
{
  "expectations": [
    {
      "text": "The output includes the name 'John Smith'",
      "passed": true,
      "evidence": "Found in transcript Step 3: 'Extracted names: John Smith, Sarah Johnson'"
    },
    {
      "text": "The spreadsheet has a SUM formula in cell B10",
      "passed": false,
      "evidence": "No spreadsheet was created. The output was a text file."
    }
  ],
  "summary": {
    "passed": 2,
    "failed": 1,
    "total": 3,
    "pass_rate": 0.67
  },
  "execution_metrics": {
    "tool_calls": {
      "Read": 5,
      "Write": 2,
      "Bash": 8
    },
    "total_tool_calls": 15,
    "total_steps": 6,
    "errors_encountered": 0,
    "output_chars": 12450,
    "transcript_chars": 3200
  },
  "timing": {
    "executor_duration_seconds": 165.0,
    "grader_duration_seconds": 26.0,
    "total_duration_seconds": 191.0
  },
  "claims": [
    {
      "claim": "The form has 12 fillable fields",
      "type": "factual",
      "verified": true,
      "evidence": "Counted 12 fields in field_info.json"
    }
  ],
  "user_notes_summary": {
    "uncertainties": ["Used 2023 data, may be stale"],
    "needs_review": [],
    "workarounds": ["Fell back to text overlay for non-fillable fields"]
  },
  "eval_feedback": {
    "suggestions": [
      {
        "assertion": "The output includes the name 'John Smith'",
        "reason": "A hallucinated document that mentions the name would also pass"
      }
    ],
    "overall": "Assertions check presence but not correctness."
  }
}
```

**Fields:**
- `expectations[]`: Graded expectations with evidence
  - `text`: The assertion description (translated from `description` in evals.json)
  - `passed`: Boolean verdict
  - `evidence`: Specific quote or description supporting the verdict
- `summary`: Aggregate pass/fail counts
- `execution_metrics`: Tool usage and output size (from executor's metrics.json)
- `timing`: Wall clock timing (from timing.json)
- `claims`: Extracted and verified claims from the output
- `user_notes_summary`: Issues flagged by the executor
- `eval_feedback`: (optional) Improvement suggestions for the evals

---

## metrics.json

Output from the executor agent. Located at `<eval-name>/{with_skill|without_skill}/outputs/metrics.json`.

```json
{
  "tool_calls": {
    "Read": 5,
    "Write": 2,
    "Bash": 8,
    "Edit": 1,
    "Glob": 2,
    "Grep": 0
  },
  "total_tool_calls": 18,
  "total_steps": 6,
  "files_created": ["filled_form.pdf", "field_values.json"],
  "errors_encountered": 0,
  "output_chars": 12450,
  "transcript_chars": 3200
}
```

**Fields:**
- `tool_calls`: Count per tool type
- `total_tool_calls`: Sum of all tool calls
- `total_steps`: Number of major execution steps
- `files_created`: List of output files created
- `errors_encountered`: Number of errors during execution
- `output_chars`: Total character count of output files
- `transcript_chars`: Character count of transcript

---

## eval_metadata.json

Written by the workflow, in **two variants** — the same filename at two levels, which is deliberate and
worth knowing before reading either.

**Eval-level**, at `<eval-name>/eval_metadata.json`: carries the prompt **as authored** in `evals.json`.
`aggregate_benchmark.py` reads this one for its `eval_id` lookup, so it is left alone by staging.

**Per-configuration**, at `<eval-name>/{with_skill|without_skill}/eval_metadata.json`: carries the prompt
the executor **actually received** under `prompt` — the staged one, rewritten to name that run's private
fixture copy — and the authored one under `authored_prompt`. The viewer's `build_run` prefers a
config-level file over its eval-level parent, so this is what is displayed as "what ran". A run archive is
the only record of what a past run did; recording both means it says which prompt ran, not only which
prompt was written.

```json
{
  "eval_id": 1,
  "eval_name": "<eval-name>",
  "prompt": "the prompt this executor received",
  "authored_prompt": "the prompt as written in evals.json (per-configuration file only)"
}
```

Assertions are deliberately absent from both: an executor must never see what it is graded against.

---

## timing.json

Wall clock timing for a run. Located at `<eval-name>/{with_skill|without_skill}/timing.json`.

**How to capture:** When a subagent task completes, the task notification includes `total_tokens` and `duration_ms`. Save these immediately — they are not persisted anywhere else and cannot be recovered after the fact.

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3,
  "executor_start": "2026-01-15T10:30:00Z",
  "executor_end": "2026-01-15T10:32:45Z",
  "executor_duration_seconds": 165.0,
  "grader_start": "2026-01-15T10:32:46Z",
  "grader_end": "2026-01-15T10:33:12Z",
  "grader_duration_seconds": 26.0
}
```

---

## benchmark.json

Output from aggregate_benchmark.py. Located at `evals/workspace/iteration-N/benchmark.json`.

```json
{
  "metadata": {
    "skill_name": "pdf",
    "skill_path": "/path/to/pdf",
    "executor_model": "claude-sonnet-4-20250514",
    "analyzer_model": "most-capable-model",
    "timestamp": "2026-01-15T10:30:00Z",
    "evals_run": [1, 2, 3],
    "runs_per_configuration": 3
  },

  "runs": [
    {
      "eval_id": 1,
      "eval_name": "Ocean",
      "configuration": "with_skill",
      "run_number": 1,
      "result": {
        "pass_rate": 0.85,
        "passed": 6,
        "failed": 1,
        "total": 7,
        "time_seconds": 42.5,
        "tokens": 3800,
        "tool_calls": 18,
        "errors": 0
      },
      "expectations": [
        {"text": "...", "passed": true, "evidence": "..."}
      ],
      "notes": [
        "Used 2023 data, may be stale"
      ]
    }
  ],

  "run_summary": {
    "with_skill": {
      "pass_rate": {"mean": 0.85, "stddev": 0.05, "min": 0.80, "max": 0.90},
      "time_seconds": {"mean": 45.0, "stddev": 12.0, "min": 32.0, "max": 58.0},
      "tokens": {"mean": 3800, "stddev": 400, "min": 3200, "max": 4100}
    },
    "without_skill": {
      "pass_rate": {"mean": 0.35, "stddev": 0.08, "min": 0.28, "max": 0.45},
      "time_seconds": {"mean": 32.0, "stddev": 8.0, "min": 24.0, "max": 42.0},
      "tokens": {"mean": 2100, "stddev": 300, "min": 1800, "max": 2500}
    },
    "delta": {
      "pass_rate": "+0.50",
      "time_seconds": "+13.0",
      "tokens": "+1700"
    }
  },

  "notes": [
    "Assertion 'Output is a PDF file' passes 100% in both configurations - may not differentiate skill value",
    "Without-skill runs consistently fail on table extraction expectations",
    "Skill adds 13s average execution time but improves pass rate by 50%"
  ]
}
```

**Fields:**
- `metadata`: Information about the benchmark run
- `runs[]`: Individual run results
  - `configuration`: Must be `"with_skill"` or `"without_skill"` (viewer uses this exact string for grouping and colour coding)
  - `result`: Nested object with `pass_rate`, `passed`, `total`, `time_seconds`, `tokens`, `errors`
- `run_summary`: Statistical aggregates per configuration with `mean`, `stddev`, `min`, `max`
- `notes`: Freeform observations from the analyzer

**Important:** The viewer reads these field names exactly. Using `config` instead of `configuration`, or putting `pass_rate` at the top level of a run instead of nested under `result`, will cause the viewer to show empty/zero values.

---

## stage_manifest.json

Output from `stage_fixtures.py`, one per run. Located at `evals/workspace/iteration-N/stage_manifest.json`.

Records where each (case × configuration) got its private fixture copy, and the prompt rewritten to point
at it. `harvest_run.py` walks up to this file to find `fixture_root`; the workflow reads `cases` to hand
each executor its staged prompt. `fixture_root` is `null` for a skill with no `evals/inputs/` tree, and
`cases` is then `{}` — that pair is the no-fixture signal the workflow branches on.

```json
{
  "schema_version": 1,
  "repo_root": "/abs/path/to/repo",
  "fixture_root": "/abs/path/to/<skill-dir>/evals/inputs",
  "cases": {
    "<eval-name>": {
      "with_skill": {
        "inputs_root": "/abs/path/to/.../with_skill/inputs",
        "inputs_root_rel": ".claude/skills/<skill>/evals/workspace/iteration-N/<eval-name>/with_skill/inputs",
        "bindings": { "<product-dir>": "<repo-relative path to the staged product>" },
        "prompt": "the authored prompt, rewritten to name the staged tree"
      }
    }
  }
}
```

The staged `Product path:` stays **repo-relative**: an absolute one would flip a producer skill to its
"the repo *is* the product" branch and change which repo its commit step targets, so the eval would
exercise a different code path than production.

---

## staged_manifest.json

Output from `stage_fixtures.py`, one per configuration. Located at
`<eval-name>/{with_skill|without_skill}/staged_manifest.json` — beside `inputs/`, not inside it.

Per-file hash of the staged copy, taken **after** the `project.md` binding rewrite. This is the baseline
`harvest_run.py` diffs against: diffing the pristine fixture instead would report staging's own edit to
every `project.md` as a change the run made.

```json
{
  "schema_version": 1,
  "files": { "<path relative to inputs/>": "<sha256>" }
}
```

---

## run_delta.json

Output from `harvest_run.py`, one per configuration. Located at
`<eval-name>/{with_skill|without_skill}/outputs/run_delta.json` — at the **top** of `outputs/`, where
every reader already looks.

What the run did to its staged product, as product-relative paths. An assertion about *where* a file
landed is checked against this rather than by walking `outputs/`: nothing reads that directory
recursively — not the grading prompt, not `agents/grader.md`, not the viewer's `build_run`.

Alongside it, harvest writes two trees: `outputs/product/<relpath>` holds what the run wrote, path
preserved; `outputs/reference/<relpath>` holds the pristine pre-run version of anything it **modified or
deleted**. That pair is what makes a "retired whole" style assertion checkable without reaching outside
`outputs/` — and note the consequence of the population rule: a file the run created but never modified
or deleted has no `reference/` counterpart, so a before/after comparison is only available once the
original left its place. `reference_unavailable` lists any path whose pristine copy could not be found.

`deleted` is the entry that earns the most: a skill whose done-signal is *removing* a file could never be
tested for it while executors wrote into a sandbox, because the file was never there to remove.

```json
{
  "schema_version": 1,
  "product_root": "/abs/path/to/.../with_skill/inputs",
  "fixture_root": "/abs/path/to/<skill-dir>/evals/inputs",
  "created": ["<product-relative path>"],
  "modified": ["<product-relative path>"],
  "deleted": ["<product-relative path>"],
  "reference_unavailable": []
}
```
