#!/usr/bin/env python3
# Changed from Anthropic's skill-creator (Apache-2.0, https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator); this file is not the original.
"""Run trigger evaluation for a skill description.

Tests whether a skill's description causes Claude to trigger (read the skill)
for a set of queries. Outputs results as JSON.
"""

import argparse
import json
import os
import select
import subprocess
import tempfile
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from enum import Enum
from pathlib import Path

from scripts.utils import parse_skill_md


def find_project_root() -> Path:
    """Find the project root by walking up from cwd looking for .claude/.

    Mimics how Claude Code discovers its project root, so the command file
    we create ends up where claude -p will look for it.
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return current


class Outcome(str, Enum):
    """What one run of one query actually did.

    Three states, not two. A run that crashed or timed out never got to answer
    the question, and recording it as ``NOT_TRIGGERED`` makes an infrastructure
    fault look exactly like a description that failed to fire — which is how a
    broken harness reads as a wording problem. ``str`` -based so it pickles
    across the ``ProcessPoolExecutor`` boundary and prints legibly.
    """

    TRIGGERED = "triggered"
    NOT_TRIGGERED = "not_triggered"
    ERRORED = "errored"


def scan_stream_for_trigger(lines, target_name: str) -> bool:
    """Did ``target_name`` get invoked anywhere in this run?

    The question is *"did the skill fire at all"*, not *"was the skill the first
    thing this run did"*. Models orient before they act — a grep, a todo list, a
    file read — so the skill is rarely the literal first move. The previous
    detector concluded the run at the first tool that was not ``Skill``/``Read``,
    at an unrelated ``Read``, at the first ``message_stop`` (which ends every
    assistant turn, not just the last), and after the first tool-use block in a
    message. Each of those returned "did not trigger" while the skill was still
    to come, which is why every skill scored zero regardless of its description.

    So: keep watching. Return ``True`` as soon as a match is seen — there is
    nothing to learn after that and the caller is on a timeout — and let the
    ``result`` event be the one thing that ends the watch.

    Takes an iterable of raw lines so it can be unit-tested without a subprocess,
    and consumes lazily so a live stream stops being read the moment the answer
    is known.
    """
    pending_tool: str | None = None
    accumulated_json = ""

    for raw in lines:
        line = raw.strip() if isinstance(raw, str) else raw
        if not line:
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            # Partial writes and interleaved noise are normal on a streamed pipe.
            continue
        if not isinstance(event, dict):
            continue

        event_type = event.get("type")

        # The one true terminator. Anything after it belongs to no run.
        if event_type == "result":
            return False

        if event_type == "stream_event":
            stream = event.get("event") or {}
            stream_type = stream.get("type", "")

            if stream_type == "content_block_start":
                block = stream.get("content_block") or {}
                if block.get("type") == "tool_use":
                    pending_tool = block.get("name", "")
                    accumulated_json = ""

            elif stream_type == "content_block_delta" and pending_tool:
                delta = stream.get("delta") or {}
                if delta.get("type") == "input_json_delta":
                    # Arguments arrive in fragments; the name can straddle one.
                    accumulated_json += delta.get("partial_json", "")
                    if pending_tool in ("Skill", "Read") and target_name in accumulated_json:
                        return True

            elif stream_type in ("content_block_stop", "message_stop"):
                # This block is over — but the run is not. Reset and keep going.
                pending_tool = None
                accumulated_json = ""

        elif event_type == "assistant":
            # The complete message, which only arrives after the tool has run.
            message = event.get("message") or {}
            for item in message.get("content") or []:
                if not isinstance(item, dict) or item.get("type") != "tool_use":
                    continue
                tool_input = item.get("input") or {}
                name = item.get("name", "")
                if name == "Skill" and target_name in str(tool_input.get("skill", "")):
                    return True
                if name == "Read" and target_name in str(tool_input.get("file_path", "")):
                    return True

    return False


def _iter_stream_lines(process, timeout: int):
    """Yield complete lines from a running process's stdout, until it ends.

    Flushes whatever is left in the buffer before finishing, including any final
    line with no trailing newline. The previous loop read the last chunk and then
    broke *before* parsing it, so the tail — the ``result`` event among it — was
    read and discarded.
    """
    buffer = ""
    start_time = time.time()

    def drain():
        nonlocal buffer
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            yield line

    while time.time() - start_time < timeout:
        if process.poll() is not None:
            remaining = process.stdout.read()
            if remaining:
                buffer += remaining.decode("utf-8", errors="replace")
            break
        ready, _, _ = select.select([process.stdout], [], [], 1.0)
        if not ready:
            continue
        chunk = os.read(process.stdout.fileno(), 8192)
        if not chunk:
            break
        buffer += chunk.decode("utf-8", errors="replace")
        yield from drain()

    yield from drain()
    if buffer:
        yield buffer


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> Outcome:
    """Run one query and report whether ``skill_name`` fired.

    Runs `claude -p` with the raw query and watches the stream, using
    --include-partial-messages so a trigger is seen at content_block_start rather
    than waiting for the full assistant message, which only arrives after the
    tool has run.

    The description is not passed here. It has to be *installed* on the skill for
    the run to be measuring it — a description the model cannot see is not under
    test. Installing it is the caller's job, once per iteration rather than once
    per query, because these run in parallel against one file. See
    ``run_loop.installed_description``.

    ``stderr`` is captured rather than discarded. A run that crashed and a run
    that simply did not reach for the skill are different facts, and collapsing
    them is what lets a broken harness read as a bad description.
    """
    cmd = [
        "claude",
        "-p", query,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
    ]
    if model:
        cmd.extend(["--model", model])

    # Remove CLAUDECODE env var to allow nesting claude -p inside a
    # Claude Code session. The guard is for interactive terminal conflicts;
    # programmatic subprocess usage is safe.
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    with tempfile.TemporaryFile(mode="w+") as stderr_file:
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=stderr_file,
                cwd=project_root,
                env=env,
            )
        except OSError as exc:
            print(f"Warning: could not start claude: {exc}", file=sys.stderr)
            return Outcome.ERRORED

        try:
            triggered = scan_stream_for_trigger(
                _iter_stream_lines(process, timeout), skill_name
            )
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

        if triggered:
            return Outcome.TRIGGERED

        # No trigger seen — but was that an answer, or a failure to answer?
        if process.returncode not in (0, None):
            stderr_file.seek(0)
            detail = stderr_file.read().strip().splitlines()
            tail = detail[-1] if detail else "no stderr"
            print(
                f"Warning: run exited {process.returncode}: {tail[:200]}",
                file=sys.stderr,
            )
            return Outcome.ERRORED

        return Outcome.NOT_TRIGGERED


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    """Run the full eval set and return results."""
    results = []

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    description,
                    timeout,
                    str(project_root),
                    model,
                )
                future_to_info[future] = (item, run_idx)

        query_outcomes: dict[str, list[Outcome]] = {}
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            if query not in query_outcomes:
                query_outcomes[query] = []
            try:
                query_outcomes[query].append(future.result())
            except Exception as e:
                print(f"Warning: query failed: {e}", file=sys.stderr)
                query_outcomes[query].append(Outcome.ERRORED)

    for query, outcomes in query_outcomes.items():
        item = query_items[query]
        triggers = sum(1 for o in outcomes if o is Outcome.TRIGGERED)
        errors = sum(1 for o in outcomes if o is Outcome.ERRORED)
        # `runs` counts runs that answered the question. Errored runs never got
        # to answer it, so they are reported alongside rather than folded in —
        # every downstream negative cell is derived by subtracting from `runs`,
        # and a crash swept in there scores as a correct silence.
        runs = len(outcomes) - errors
        trigger_rate = (triggers / runs) if runs else 0.0
        should_trigger = item["should_trigger"]
        if runs == 0:
            did_pass = False
        elif should_trigger:
            did_pass = trigger_rate >= trigger_threshold
        else:
            did_pass = trigger_rate < trigger_threshold
        results.append({
            "query": query,
            "should_trigger": should_trigger,
            "trigger_rate": trigger_rate,
            "triggers": triggers,
            "runs": runs,
            "errors": errors,
            "pass": did_pass,
        })

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--num-workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=180, help="Timeout per query in seconds")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--model", default=None, help="Model to use for claude -p (default: user's configured model)")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, content = parse_skill_md(skill_path)
    description = args.description or original_description
    project_root = find_project_root()

    if args.verbose:
        print(f"Evaluating: {description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        project_root=project_root,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
    )

    if args.verbose:
        summary = output["summary"]
        print(f"Results: {summary['passed']}/{summary['total']} passed", file=sys.stderr)
        for r in output["results"]:
            status = "PASS" if r["pass"] else "FAIL"
            rate_str = f"{r['triggers']}/{r['runs']}"
            print(f"  [{status}] rate={rate_str} expected={r['should_trigger']}: {r['query'][:70]}", file=sys.stderr)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
