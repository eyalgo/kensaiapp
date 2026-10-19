#!/usr/bin/env python3
"""Writes the timing.json that skill-evals has always documented and never produced.

`aggregate_benchmark.py` (_load_timing_into) and `agents/grader.md` both read a per-run `timing.json`,
and `SKILL.md`'s File Structure block lists one — but nothing ever wrote it, so every Time and Tokens
figure in every benchmark has been a structural 0.0. This closes that.

The numbers come from the workflow's own agent transcripts, which carry `timestamp` on every record and
`message.usage` on assistant records. Duration is last timestamp minus first; tokens are the summed
usage (cache reads included — they are real spend and the whole point of measuring a model change).

Mapping a transcript back to the run it graded is the awkward part, and content is the only handle:
the journal's `key` is an opaque `v2:<sha>` and `agent-*.meta.json` carries only
`{"agentType":"workflow-subagent","spawnDepth":1}`. So each transcript is matched by the workspace path
that appears in its own prompt — the executor and grader prompts both name
`<workspace>/<case>/<config>/...`. A transcript naming no run is skipped, not guessed at.

Usage:
    collect_timing.py --transcript-dir <workflow transcript dir> --workspace <iteration-N dir>

The transcript dir is the one the Workflow tool reports on launch; the caller passes it through, since
the workflow runtime has no filesystem access and cannot record its own timing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = 1

# Which phase a transcript belongs to, read off the label the workflow gave its agent. Executor labels
# are `run-<id>-<config>`; grader labels are `grade-*` / `merge-*`. The label is not in the transcript,
# so phase is inferred from the prompt's own shape instead (see classify_phase).
EXECUTOR_MARKER = "You are an executor agent."
GRADER_MARKER = "and grade this run."


def iter_records(path: Path):
    for line in path.read_text(errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def text_of(record: dict) -> str:
    """Flatten a record's message content to text, whatever shape it takes."""
    message = record.get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text") or block.get("content") or "")
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(p for p in parts if isinstance(p, str))
    return ""


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def sum_tokens(records: list[dict]) -> int:
    """Every token the run was billed for, cache reads included."""
    total = 0
    for record in records:
        usage = (record.get("message") or {}).get("usage") or {}
        for key in (
            "input_tokens",
            "output_tokens",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
        ):
            value = usage.get(key)
            if isinstance(value, int):
                total += value
    return total


def classify_phase(prompt: str) -> str:
    if EXECUTOR_MARKER in prompt:
        return "executor"
    if GRADER_MARKER in prompt or "grading.json" in prompt:
        return "grader"
    return "other"


def find_run(prompt: str, workspace: Path) -> tuple[str, str] | None:
    """The (case, config) this transcript worked on, from the workspace path in its own prompt."""
    pattern = re.escape(str(workspace)) + r"/([^/\s]+)/(with_skill|without_skill)\b"
    match = re.search(pattern, prompt)
    if not match:
        return None
    return match.group(1), match.group(2)


def collect(transcript_dir: Path, workspace: Path) -> dict[tuple[str, str], dict]:
    """Per (case, config): the executor's and graders' spans and tokens."""
    runs: dict[tuple[str, str], dict] = {}

    for transcript in sorted(transcript_dir.glob("agent-*.jsonl")):
        records = list(iter_records(transcript))
        if not records:
            continue
        prompt = text_of(records[0])
        run = find_run(prompt, workspace)
        if run is None:
            continue
        phase = classify_phase(prompt)
        if phase == "other":
            continue

        stamps = [parse_ts(r.get("timestamp")) for r in records]
        stamps = [s for s in stamps if s is not None]
        if not stamps:
            continue

        entry = runs.setdefault(
            run, {"executor": None, "graders": [], "tokens": 0}
        )
        span = {
            "start": min(stamps),
            "end": max(stamps),
            "tokens": sum_tokens(records),
        }
        entry["tokens"] += span["tokens"]
        if phase == "executor":
            # More than one executor for a run should not happen; keep the longest if it does.
            if entry["executor"] is None or (
                span["end"] - span["start"] > entry["executor"]["end"] - entry["executor"]["start"]
            ):
                entry["executor"] = span
        else:
            entry["graders"].append(span)

    return runs


def timing_payload(entry: dict) -> dict:
    executor = entry["executor"]
    graders = entry["graders"]

    def seconds(span: dict) -> float:
        return round((span["end"] - span["start"]).total_seconds(), 1)

    def iso(moment: datetime) -> str:
        return moment.astimezone().strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": "workflow agent transcripts (collect_timing.py)",
        "total_tokens": entry["tokens"],
    }

    spans = [s for s in ([executor] if executor else []) + graders]
    if spans:
        start, end = min(s["start"] for s in spans), max(s["end"] for s in spans)
        payload["duration_ms"] = int((end - start).total_seconds() * 1000)
        payload["total_duration_seconds"] = round((end - start).total_seconds(), 1)

    if executor:
        payload["executor_start"] = iso(executor["start"])
        payload["executor_end"] = iso(executor["end"])
        payload["executor_duration_seconds"] = seconds(executor)
        payload["executor_tokens"] = executor["tokens"]
    if graders:
        payload["grader_start"] = iso(min(g["start"] for g in graders))
        payload["grader_end"] = iso(max(g["end"] for g in graders))
        payload["grader_duration_seconds"] = round(
            sum((g["end"] - g["start"]).total_seconds() for g in graders), 1
        )
        payload["grader_tokens"] = sum(g["tokens"] for g in graders)
        payload["grader_agents"] = len(graders)

    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="collect_timing.py",
        description="Write per-run timing.json from a workflow's agent transcripts.",
    )
    parser.add_argument("--transcript-dir", required=True)
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args(argv)

    transcript_dir = Path(args.transcript_dir).resolve()
    workspace = Path(args.workspace).resolve()

    if not transcript_dir.is_dir():
        print(f"collect-timing: no transcript dir: {transcript_dir}", file=sys.stderr)
        return 2
    if not workspace.is_dir():
        print(f"collect-timing: no workspace: {workspace}", file=sys.stderr)
        return 2

    runs = collect(transcript_dir, workspace)
    if not runs:
        print(
            "collect-timing: no transcript named a run under this workspace — wrote nothing.\n"
            "  (a transcript is matched by the workspace path in its own prompt; check the "
            "transcript dir belongs to this iteration)",
            file=sys.stderr,
        )
        return 3

    written = 0
    for (case, config), entry in sorted(runs.items()):
        target = workspace / case / config / "timing.json"
        if not target.parent.is_dir():
            continue
        target.write_text(json.dumps(timing_payload(entry), indent=2) + "\n")
        written += 1

    print(f"collect-timing: wrote {written} timing.json file(s) under {workspace.name}")
    for (case, config), entry in sorted(runs.items()):
        payload = timing_payload(entry)
        print(
            f"  {case}/{config}: {payload.get('total_duration_seconds', 0)}s, "
            f"{payload['total_tokens']:,} tokens"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
