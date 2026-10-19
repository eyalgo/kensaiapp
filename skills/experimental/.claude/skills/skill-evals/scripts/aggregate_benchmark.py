#!/usr/bin/env python3
# Changed from Anthropic's skill-creator (Apache-2.0, https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator); this file is not the original.
"""
Aggregate individual run results into benchmark summary statistics.

Reads grading.json files from run directories and produces:
- run_summary with mean, stddev, min, max for each metric
- delta between with_skill and without_skill configurations

Usage:
    python aggregate_benchmark.py <benchmark_dir>

Example:
    python aggregate_benchmark.py path/to/skill/workspace/iteration-1/

Supported directory layouts:

    New named layout (preferred):
    <benchmark_dir>/
    └── <eval-name>/          (e.g. bloom-filter, task-tracker)
        ├── eval_metadata.json
        ├── with_skill/
        │   ├── grading.json
        │   └── timing.json
        └── without_skill/
            ├── grading.json
            └── timing.json

    Legacy eval-N layout:
    <benchmark_dir>/
    └── eval-N/
        ├── eval_metadata.json
        ├── with_skill/
        │   └── run-1/grading.json
        └── without_skill/
            └── run-1/grading.json

    Legacy runs/ layout:
    <benchmark_dir>/
    └── runs/
        └── eval-N/
            ├── with_skill/run-1/grading.json
            └── without_skill/run-1/grading.json
"""

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

# This module is invoked BOTH ways and must import the same under each: as a package module
# (`python -m scripts.aggregate_benchmark`, which SKILL.md § Step 3 documents) and as a plain script
# (`python3 scripts/aggregate_benchmark.py`, which the tests and the workflow use). The script form
# puts `scripts/` on sys.path automatically; the `-m` form does not, so a bare `import arm_isolation`
# raises ModuleNotFoundError under exactly the invocation the skill tells a caller to run — which is
# how it shipped, since every test drives the script form. Adding the module's own directory makes
# both forms resolve identically. Deliberately not `from . import arm_isolation`: that fixes `-m` and
# breaks the script form, trading one broken invocation for the other.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import arm_isolation  # noqa: E402  (import follows the sys.path line it depends on)


def calculate_stats(values: list[float]) -> dict:
    """Calculate mean, stddev, min, max for a list of values."""
    if not values:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}

    n = len(values)
    mean = sum(values) / n

    if n > 1:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        stddev = math.sqrt(variance)
    else:
        stddev = 0.0

    return {
        "mean": round(mean, 4),
        "stddev": round(stddev, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4)
    }


def _load_timing_into(result: dict, timing_file: Path) -> None:
    """Merge timing.json into result if time_seconds is missing."""
    if result["time_seconds"] == 0.0 and timing_file.exists():
        try:
            with open(timing_file) as tf:
                td = json.load(tf)
            result["time_seconds"] = td.get("total_duration_seconds") or 0.0
            result["tokens"] = td.get("total_tokens") or 0
        except json.JSONDecodeError:
            pass


# Gradings that could not be parsed this run. Surfaced in the benchmark and in the exit code, so a
# hole in the data is never mistaken for a complete measurement.
MALFORMED_GRADINGS: list[tuple[str, str]] = []

# Arms that were expected but produced no parseable grading.json at all — an arm directory sitting
# there without one, or a whole eval that lost every arm. Same treatment as MALFORMED_GRADINGS: a
# gradingless arm was never *excluded*, it was never *seen* (_is_config_dir requires a grading.json
# to exist at all, `:152-160`), so this is the complementary hole MALFORMED_GRADINGS cannot catch.
ABSENT_ARMS: list[tuple[str, str]] = []


def _parse_grading(grading_file: Path, eval_id: int, run_number: int) -> dict | None:
    """Parse a single grading.json and return a result dict, or None on error.

    An unreadable grading is recorded as a hard failure, not skipped. Skipping it silently drops one
    arm of one case out of the benchmark and still prints a confident round number for the rest — which
    is exactly what happened when a grader emitted an unescaped quote inside an evidence string. The
    grader model is deliberately the cheap tier for structural checks (see run-skill-evals.js), so an
    occasional serialization slip is expected; what must never be silent is the resulting hole.
    """
    try:
        with open(grading_file) as f:
            grading = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        MALFORMED_GRADINGS.append((str(grading_file), str(e)))
        print(f"ERROR: unreadable grading, excluded from the benchmark: {grading_file}: {e}")
        return None

    result = {
        "eval_id": eval_id,
        "run_number": run_number,
        "pass_rate": grading.get("summary", {}).get("pass_rate", 0.0),
        "passed": grading.get("summary", {}).get("passed", 0),
        "failed": grading.get("summary", {}).get("failed", 0),
        "total": grading.get("summary", {}).get("total", 0),
        "time_seconds": (grading.get("timing") or {}).get("total_duration_seconds", 0.0),
    }

    metrics = grading.get("execution_metrics", {}) or {}
    result["tool_calls"] = metrics.get("total_tool_calls") or 0
    result["tokens"] = metrics.get("output_chars") or 0
    result["errors"] = metrics.get("errors_encountered") or 0

    raw_expectations = grading.get("expectations", [])
    for exp in raw_expectations:
        if "text" not in exp or "passed" not in exp:
            print(f"Warning: expectation in {grading_file} missing required fields (text, passed): {exp}")
    result["expectations"] = raw_expectations

    notes_summary = grading.get("user_notes_summary") or {}
    notes = []
    notes.extend(notes_summary.get("uncertainties", []))
    notes.extend(notes_summary.get("needs_review", []))
    notes.extend(notes_summary.get("workarounds", []))
    result["notes"] = notes

    return result


def _is_config_dir(d: Path) -> bool:
    """Return True if d looks like a config directory (has grading.json at flat or nested level)."""
    if not d.is_dir():
        return False
    if (d / "grading.json").exists():
        return True
    if list(d.glob("run-*/grading.json")):
        return True
    return False


def _is_eval_dir(d: Path) -> bool:
    """Return True if d is an eval directory (contains at least one config dir)."""
    if not d.is_dir():
        return False
    return any(_is_config_dir(sub) for sub in d.iterdir())


def _has_eval_metadata(d: Path) -> bool:
    """True when d carries eval_metadata.json — the one signal an eval directory that lost every
    arm still leaves behind (it fails both _is_config_dir and _is_eval_dir, and would otherwise
    vanish from the walk whole)."""
    return (d / "eval_metadata.json").exists()


def _record_incomplete_arms(eval_dir: Path) -> None:
    """Record every subdirectory of eval_dir that is a directory but not a config dir — an arm the
    harness created that never received a parseable grading. A stray grading.json sitting directly
    in eval_dir is named as the likely misplacement: the exact shape of the one real occurrence,
    and naming the file is what turns the error into a one-move recovery instruction."""
    stray = eval_dir / "grading.json"
    for sub in sorted(d for d in eval_dir.iterdir() if d.is_dir()):
        if _is_config_dir(sub):
            continue
        identifier = f"{eval_dir.name}/{sub.name}"
        reason = "no grading.json found for this arm"
        if stray.exists():
            reason += (
                f"; a stray grading.json sits at {eval_dir.name}/grading.json — likely "
                "misplaced from this arm"
            )
        ABSENT_ARMS.append((identifier, reason))
        print(f"ERROR: no grading found, excluded from the benchmark: {identifier}: {reason}")


def _read_eval_id(eval_dir: Path, fallback_idx: int) -> int:
    """Read eval_id from eval_metadata.json, falling back to directory name or index."""
    meta = eval_dir / "eval_metadata.json"
    if meta.exists():
        try:
            with open(meta) as mf:
                return json.load(mf).get("eval_id", fallback_idx)
        except (json.JSONDecodeError, OSError):
            pass
    if eval_dir.name.startswith("eval-"):
        try:
            return int(eval_dir.name.split("-")[1])
        except (ValueError, IndexError):
            pass
    return fallback_idx


def load_run_results(benchmark_dir: Path) -> dict:
    """
    Load all run results from a benchmark directory.

    Returns dict keyed by config name (e.g. with_skill / without_skill),
    each containing a list of run result dicts.
    """
    # Legacy runs/ layout
    runs_dir = benchmark_dir / "runs"
    search_dir = runs_dir if runs_dir.exists() else benchmark_dir

    eval_dirs = sorted(d for d in search_dir.iterdir() if _is_eval_dir(d))

    if not eval_dirs:
        print(f"No eval directories found in {search_dir}")
        return {}

    # An eval directory that lost every arm fails _is_eval_dir (no subdir passes _is_config_dir)
    # and is invisible to the loop above. Walked here only to flag its missing arms (Task 1) — it
    # contributes nothing to results either way, so eval_dirs (and the early return above) stays
    # exactly as it read before this detector existed.
    eval_dir_names = {d.name for d in eval_dirs}
    extra_metadata_dirs = sorted(
        d for d in search_dir.iterdir()
        if d.is_dir() and d.name not in eval_dir_names and _has_eval_metadata(d)
    )

    results: dict[str, list] = {}

    for idx, eval_dir in enumerate(eval_dirs):
        eval_id = _read_eval_id(eval_dir, idx)
        _record_incomplete_arms(eval_dir)

        for config_dir in sorted(d for d in eval_dir.iterdir() if _is_config_dir(d)):
            config = config_dir.name
            if config not in results:
                results[config] = []

            # New flat layout: <config>/grading.json
            flat_grading = config_dir / "grading.json"
            if flat_grading.exists():
                result = _parse_grading(flat_grading, eval_id, 1)
                if result:
                    _load_timing_into(result, config_dir / "timing.json")
                    results[config].append(result)
                continue

            # Legacy nested layout: <config>/run-N/grading.json
            for run_dir in sorted(config_dir.glob("run-*")):
                try:
                    run_number = int(run_dir.name.split("-")[1])
                except (ValueError, IndexError):
                    run_number = 1
                grading_file = run_dir / "grading.json"
                if not grading_file.exists():
                    print(f"Warning: grading.json not found in {run_dir}")
                    continue
                result = _parse_grading(grading_file, eval_id, run_number)
                if result:
                    _load_timing_into(result, run_dir / "timing.json")
                    results[config].append(result)

    for eval_dir in extra_metadata_dirs:
        _record_incomplete_arms(eval_dir)

    return results


def aggregate_results(results: dict) -> dict:
    """
    Aggregate run results into summary statistics.

    Returns run_summary with stats for each configuration and delta.
    """
    run_summary = {}
    configs = list(results.keys())

    for config in configs:
        runs = results.get(config, [])

        if not runs:
            run_summary[config] = {
                "pass_rate": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
                "time_seconds": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
                "tokens": {"mean": 0, "stddev": 0, "min": 0, "max": 0}
            }
            continue

        run_summary[config] = {
            "pass_rate": calculate_stats([r["pass_rate"] for r in runs]),
            "time_seconds": calculate_stats([r["time_seconds"] for r in runs]),
            "tokens": calculate_stats([r.get("tokens", 0) for r in runs]),
        }

    if len(configs) >= 2:
        primary = run_summary.get(configs[0], {})
        baseline = run_summary.get(configs[1], {})
    else:
        primary = run_summary.get(configs[0], {}) if configs else {}
        baseline = {}

    run_summary["delta"] = {
        "pass_rate": f"{primary.get('pass_rate', {}).get('mean', 0) - baseline.get('pass_rate', {}).get('mean', 0):+.2f}",
        "time_seconds": f"{primary.get('time_seconds', {}).get('mean', 0) - baseline.get('time_seconds', {}).get('mean', 0):+.1f}",
        "tokens": f"{primary.get('tokens', {}).get('mean', 0) - baseline.get('tokens', {}).get('mean', 0):+.0f}",
    }

    return run_summary


def _check_result_matrix(results: dict, manifest: dict | None) -> None:
    """Verify the results form a full matrix: for every configuration found and every eval id found
    (the union across configurations), the cell holds the expected number of runs. Catches an arm
    directory that is entirely absent from disk (nothing for the disk walk to see) and a
    nested-layout cell that has some runs but fewer than expected — neither of which the disk walk
    in load_run_results can see. Not deduplicated against that walk's findings: the identifiers
    differ (directory names vs configuration × eval id), and two lines naming one hole cost nothing.

    Expected runs per cell is the manifest's runs_per_configuration when the manifest exists and
    carries it — the one expectation the workflow records independently of the results — else the
    maximum observed cell count. A declared expectation always outranks the data it checks; observed
    uniformity is only a fallback for workspaces that predate the manifest."""
    if not results:
        return

    eval_ids = sorted(set(r["eval_id"] for config_runs in results.values() for r in config_runs))
    if not eval_ids:
        return

    configs = sorted(results.keys())

    def _cell_count(config: str, eval_id: int) -> int:
        return len([r for r in results[config] if r["eval_id"] == eval_id])

    declared = manifest.get("runs_per_configuration") if manifest else None
    expected = declared if declared is not None else max(
        (_cell_count(config, eid) for config in configs for eid in eval_ids),
        default=0,
    )

    for config in configs:
        for eid in eval_ids:
            found = _cell_count(config, eid)
            if found < expected:
                identifier = f"{config} / eval {eid}"
                reason = f"found {found} of {expected} expected run(s)"
                ABSENT_ARMS.append((identifier, reason))
                print(
                    f"ERROR: incomplete result matrix, excluded from the benchmark: "
                    f"{identifier}: {reason}"
                )


def generate_benchmark(benchmark_dir: Path, skill_name: str = "", skill_path: str = "") -> dict:
    """Generate complete benchmark.json from run results."""
    results = load_run_results(benchmark_dir)
    manifest = _read_run_manifest(benchmark_dir)
    _check_result_matrix(results, manifest)
    run_summary = aggregate_results(results)

    runs = []
    for config in results:
        for result in results[config]:
            runs.append({
                "eval_id": result["eval_id"],
                "configuration": config,
                "run_number": result["run_number"],
                "result": {
                    "pass_rate": result["pass_rate"],
                    "passed": result["passed"],
                    "failed": result["failed"],
                    "total": result["total"],
                    "time_seconds": result["time_seconds"],
                    "tokens": result.get("tokens", 0),
                    "tool_calls": result.get("tool_calls", 0),
                    "errors": result.get("errors", 0)
                },
                "expectations": result["expectations"],
                "notes": result["notes"]
            })

    eval_ids = sorted(set(
        r["eval_id"]
        for config in results.values()
        for r in config
    ))

    # The models the run declared, read from the manifest the workflow wrote (read once, above, and
    # reused here). Absent manifest means the run predates model recording (or skipped it) — say
    # "unrecorded" rather than invent a name, since a benchmark whose model is guessed is worse than
    # one that admits it does not know.
    requested = manifest.get("models_requested", {}) if manifest else {}

    # Derive the real count instead of asserting 3. One run per (eval × configuration) is what the
    # workflow creates; deriving it means the number cannot drift from the harness again.
    runs_per_config = max(
        (len([r for r in config_runs if r["eval_id"] == eid])
         for config_runs in results.values() for eid in eval_ids),
        default=0,
    )

    # Advisory only: this never changes run_summary, eval_ids, or the caller's exit code — it
    # annotates the round with what it found (arm_isolation.py's own module docstring).
    isolation_root = benchmark_dir / "runs" if (benchmark_dir / "runs").exists() else benchmark_dir
    isolation = arm_isolation.check_arm_isolation(isolation_root)

    return {
        "metadata": {
            "skill_name": skill_name or "<skill-name>",
            "skill_path": skill_path or "<path/to/skill>",
            "executor_model": requested.get("executor") or "unrecorded (inherited session model)",
            "executor_agent_type": requested.get("executor_agent_type") or "none (no agent slot)",
            "grader_structural_model": requested.get("grader_structural") or "unrecorded",
            "grader_nuanced_model": requested.get("grader_nuanced") or "unrecorded",
            "analyzer_model": requested.get("grader_structural") or "unrecorded",
            "models_are": "requested pins, not runtime self-reports (commit_format.md § Filling the model)",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evals_run": eval_ids,
            "runs_per_configuration": runs_per_config,
        },
        "runs": runs,
        "run_summary": run_summary,
        "arm_isolation": isolation.to_dict(),
        "notes": [
            f"MALFORMED GRADING excluded: {path} ({err})"
            for path, err in MALFORMED_GRADINGS
        ] + [
            f"ABSENT ARM: {identifier} ({reason})"
            for identifier, reason in ABSENT_ARMS
        ],
    }


def _read_run_manifest(benchmark_dir: str) -> dict | None:
    """The workflow's per-run record of which models it asked for, or None if it wrote none."""
    path = Path(benchmark_dir) / "run_manifest.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _render_isolation_section(isolation: dict) -> list[str]:
    """A contaminated case's pass rate is inside the headline number below, so this section is
    rendered before it — never below the table it caveats."""
    flagged = isolation.get("flagged", [])
    unchecked = isolation.get("unchecked", [])
    lines: list[str] = []

    if flagged:
        lines.append("## Arm Isolation — CONTAMINATED CASES")
        lines.append("")
        lines.append(
            "The following case(s) had one arm's executor operate inside the sibling arm's "
            "directory. Their pass rates are still included in the summary below — this section "
            "annotates, it does not exclude:"
        )
        lines.append("")
        for entry in flagged:
            lines.append(
                f"- `{entry['case']}` / `{entry['arm']}` names sibling arm `{entry['sibling']}` "
                f"(\"{entry['matched']}\")"
            )
    else:
        lines.append("## Arm Isolation")
        lines.append("")
        lines.append(
            f"Checked {isolation.get('arms_checked', 0)} arm(s) across "
            f"{isolation.get('cases_checked', 0)} case(s) — no cross-arm contamination found."
        )

    # Recovered arms are reported separately from contamination, and deliberately not as a caveat on
    # the numbers: the arm produced in its own tree, so its result is measurable. What it signals is a
    # harness fault upstream — something handed that arm a path outside its own tree — which is worth
    # seeing precisely because the fence hid its consequence.
    recovered = isolation.get("recovered", [])
    if recovered:
        lines.append("")
        lines.append(
            f"{len(recovered)} arm(s) were handed a path naming a sibling arm and worked in their "
            "own tree anyway — the executor fence catching a bad binding. Their results stand; the "
            "bad binding is a harness fault worth chasing:"
        )
        for entry in recovered:
            lines.append(
                f"- `{entry['case']}` / `{entry['arm']}` was pointed at `{entry['sibling']}` "
                f"(\"{entry['matched']}\")"
            )

    if unchecked:
        lines.append("")
        named = ", ".join(f"`{e['case']}`/`{e['arm']}`" for e in unchecked)
        lines.append(f"{len(unchecked)} arm(s) had no `outputs/transcript.md` and could not be checked: {named}.")

    lines.append("")
    return lines


def generate_markdown(benchmark: dict) -> str:
    """Generate human-readable benchmark.md from benchmark data."""
    metadata = benchmark["metadata"]
    run_summary = benchmark["run_summary"]

    configs = [k for k in run_summary if k != "delta"]
    config_a = configs[0] if len(configs) >= 1 else "config_a"
    config_b = configs[1] if len(configs) >= 2 else "config_b"
    label_a = config_a.replace("_", " ").title()
    label_b = config_b.replace("_", " ").title()

    lines = [
        f"# Skill Benchmark: {metadata['skill_name']}",
        "",
        f"**Executor model**: {metadata['executor_model']}"
        + (f" (agent: {metadata['executor_agent_type']})" if metadata.get("executor_agent_type") else ""),
        f"**Grader models**: structural {metadata.get('grader_structural_model', 'unrecorded')}"
        f" · nuanced {metadata.get('grader_nuanced_model', 'unrecorded')}",
        f"**Date**: {metadata['timestamp']}",
        f"**Evals**: {', '.join(map(str, metadata['evals_run']))} ({metadata['runs_per_configuration']} run(s) each per configuration)",
        "",
    ]

    isolation = benchmark.get("arm_isolation")
    if isolation:
        lines.extend(_render_isolation_section(isolation))

    lines.extend([
        "## Summary",
        "",
        f"| Metric | {label_a} | {label_b} | Delta |",
        "|--------|------------|---------------|-------|",
    ])

    a_summary = run_summary.get(config_a, {})
    b_summary = run_summary.get(config_b, {})
    delta = run_summary.get("delta", {})

    a_pr = a_summary.get("pass_rate", {})
    b_pr = b_summary.get("pass_rate", {})
    lines.append(f"| Pass Rate | {a_pr.get('mean', 0)*100:.0f}% ± {a_pr.get('stddev', 0)*100:.0f}% | {b_pr.get('mean', 0)*100:.0f}% ± {b_pr.get('stddev', 0)*100:.0f}% | {delta.get('pass_rate', '—')} |")

    a_time = a_summary.get("time_seconds", {})
    b_time = b_summary.get("time_seconds", {})
    lines.append(f"| Time | {a_time.get('mean', 0):.1f}s ± {a_time.get('stddev', 0):.1f}s | {b_time.get('mean', 0):.1f}s ± {b_time.get('stddev', 0):.1f}s | {delta.get('time_seconds', '—')}s |")

    a_tokens = a_summary.get("tokens", {})
    b_tokens = b_summary.get("tokens", {})
    lines.append(f"| Tokens | {a_tokens.get('mean', 0):.0f} ± {a_tokens.get('stddev', 0):.0f} | {b_tokens.get('mean', 0):.0f} ± {b_tokens.get('stddev', 0):.0f} | {delta.get('tokens', '—')} |")

    if benchmark.get("notes"):
        lines.extend(["", "## Notes", ""])
        for note in benchmark["notes"]:
            lines.append(f"- {note}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate benchmark run results into summary statistics"
    )
    parser.add_argument("benchmark_dir", type=Path, help="Path to the benchmark directory")
    parser.add_argument("--skill-name", default="", help="Name of the skill being benchmarked")
    parser.add_argument("--skill-path", default="", help="Path to the skill being benchmarked")
    parser.add_argument("--output", "-o", type=Path,
                        help="Output path for benchmark.json (default: <benchmark_dir>/benchmark.json)")

    args = parser.parse_args()

    if not args.benchmark_dir.exists():
        print(f"Directory not found: {args.benchmark_dir}")
        sys.exit(1)

    benchmark = generate_benchmark(args.benchmark_dir, args.skill_name, args.skill_path)

    output_json = args.output or (args.benchmark_dir / "benchmark.json")
    output_md = output_json.with_suffix(".md")

    with open(output_json, "w") as f:
        json.dump(benchmark, f, indent=2)
    print(f"Generated: {output_json}")

    markdown = generate_markdown(benchmark)
    with open(output_md, "w") as f:
        f.write(markdown)
    print(f"Generated: {output_md}")

    run_summary = benchmark["run_summary"]
    configs = [k for k in run_summary if k != "delta"]
    delta = run_summary.get("delta", {})

    print(f"\nSummary:")
    for config in configs:
        pr = run_summary[config]["pass_rate"]["mean"]
        print(f"  {config.replace('_', ' ').title()}: {pr*100:.1f}% pass rate")
    print(f"  Delta: {delta.get('pass_rate', '—')}")

    # A hole in the data must not exit 0. The numbers above are real for what parsed, and that is
    # precisely why an unreadable or absent grading has to be loud: the summary looks complete
    # either way. Same exit code for both — one meaning to every consumer, do not report these
    # numbers as a complete measurement.
    if MALFORMED_GRADINGS or ABSENT_ARMS:
        total = len(MALFORMED_GRADINGS) + len(ABSENT_ARMS)
        print(
            f"\nINCOMPLETE: {total} finding(s) are missing from the numbers above:",
            file=sys.stderr,
        )
        for path, err in MALFORMED_GRADINGS:
            print(f"  MALFORMED GRADING: {path}: {err}", file=sys.stderr)
        for identifier, reason in ABSENT_ARMS:
            print(f"  ABSENT ARM: {identifier}: {reason}", file=sys.stderr)
        print(
            "  Repair or re-grade those runs, then aggregate again — do not report these numbers as "
            "a complete measurement.",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
