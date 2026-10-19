#!/usr/bin/env python3
"""run_usage.py — what a background run used, and what this reader could not read.

WHY THIS EXISTS
    Every background run already leaves its own receipt: `claude agents --json --all` names the
    run, and its transcript under `~/.claude/projects/<slug>/<sessionId>.jsonl` carries a
    `usage` block on every `assistant` record. Nothing sums that up today, so a run's usage is
    only visible by opening its transcript by hand. This reads what is already there; it writes
    nothing.

    Measured against the live disk on 2026-09-04 (474 rows, 10,028 usage records sampled):

    1. The run population is `kind != "interactive"` — 471 `background` rows and 3
       `interactive` ones (the owner's own sessions). There is no structured "launcher" field,
       so that is the population this reader defines, and it says so in its own output.
    2. The join is by `sessionId`, one-to-one with a `<sessionId>.jsonl` file under
       `~/.claude/projects/*/`.
    3. **The unit is an API response, not a transcript record.** The harness writes one
       `assistant` record per CONTENT BLOCK of one response — thinking, then tool_use, then
       text — and every one of them repeats that response's `message.usage` verbatim under the
       same `message.id`. Counting per record therefore counted a response two and three times.
       Measured 2026-09-09 on runner transcript `abcf33f9`: 128 usage records, 72 distinct
       `message.id` values, and every one of the 51 repeated ids carrying byte-identical usage.
       The factor is not constant — 1.74x on one population and 3.35x on another — so it never
       cancelled out of a comparison between two of them, which is what this reader is for. The
       figures in the paragraph above were taken before this was found and are per record.
    4. There are five spend classes, not four: `input_tokens`, `output_tokens`,
       `cache_read_input_tokens`, and `usage.cache_creation`'s own split of
       `ephemeral_1h_input_tokens` from `ephemeral_5m_input_tokens` — priced differently, so
       reported apart. `cache_creation_input_tokens` is their sum and is never carried as a
       sixth class.
    5. `output_tokens_details.thinking_tokens` is a subset of `output_tokens`, never an addend.
    6. There is no `durationMs` on any record; wall time is a span — first transcript
       timestamp to last — never a sum of per-message latencies that do not exist.
    7. Spend is kept apart per model id, and `<synthetic>` (a record the CLI itself emits, not
       a billed model) is its own key, never folded into a real model's totals.
    8. Not every run has a readable transcript. Coverage — read / unreadable / total — is
       stated, with the unreadable session ids named, rather than silently undercounted.

    **No price model, no currency.** Rates belong to a vendor and change without this reader
    changing; it counts, it does not price. And **no output anywhere sums the five classes** —
    a cache read and a completion token are not the same thing priced the same way, so adding
    them would report a number nobody can price back apart.

    **A second population, since 2026-09-25: a `claude --print` run's own log.** The chains now
    start every Claude run as a detached `claude --print --output-format stream-json` process
    (`agent_run.py`, `Shape.TURN`), and such a run never appears in `claude agents` — "`--print`
    never starts the interactive session that `claude agents` attaches to"
    (https://code.claude.com/docs/en/agent-view.md). Its run log,
    `<instance>/system/logs/claude-*.jsonl`, names its session, and the session joins its
    transcript exactly as a listed row does. `--run-logs DIR` adds those runs; a session in both
    populations is one run.

Usage:  python3 <CORE>/tools/run_usage.py [--agents-json FILE] [--projects-root DIR]
                                          [--run-logs DIR] [--json]
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import agent_turn

__version__ = "2.3.0"

POPULATION_NOTE = (
    'Population: background runs only (rows with kind != "interactive"), and — with --run-logs — '
    "every claude --print run whose run log names its session."
)


# ── Task 1 — the population is named, and interactive is out of it ────────


@dataclass(frozen=True)
class Run:
    """One row of the population this reader scopes itself to — a non-interactive agent, with
    a session id to join its transcript on."""

    session_id: str
    name: str | None
    cwd: str | None
    state: str | None
    started_at: int | None


@dataclass(frozen=True)
class ParsedRuns:
    """`runs_from`'s whole answer — the kept population, plus what was excluded and why.

    `interactive_excluded` and `dropped_no_session` are two different reasons a row is not a
    `Run`: the first is out of scope by definition, the second is in scope but unjoinable.
    Conflating them would hide the second, which is the undercount this reader exists to name.
    """

    runs: tuple[Run, ...]
    interactive_excluded: int
    dropped_no_session: int
    total_seen: int


def runs_from(agents_json_text: str) -> ParsedRuns:
    """Parse `claude agents --json --all` output into the population this reader scopes itself
    to — `kind != "interactive"`, with a `sessionId` to join a transcript on."""
    try:
        rows = json.loads(agents_json_text)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"run_usage: could not parse `claude agents --json --all` output as JSON: {exc}"
        ) from exc
    if not isinstance(rows, list):
        raise ValueError(
            "run_usage: `claude agents --json --all` output was not a JSON array "
            f"(got {type(rows).__name__})"
        )

    runs: list[Run] = []
    interactive_excluded = 0
    dropped_no_session = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("kind") == "interactive":
            interactive_excluded += 1
            continue
        session_id = row.get("sessionId")
        if not session_id:
            dropped_no_session += 1
            continue
        runs.append(
            Run(
                session_id=session_id,
                name=row.get("name"),
                cwd=row.get("cwd"),
                state=row.get("state"),
                started_at=row.get("startedAt"),
            )
        )

    return ParsedRuns(
        runs=tuple(runs),
        interactive_excluded=interactive_excluded,
        dropped_no_session=dropped_no_session,
        total_seen=len(rows),
    )


def runs_from_run_logs(logs_dir: Path, files: Files) -> tuple[Run, ...]:
    """One `Run` per `claude-*.jsonl` run log under `logs_dir` that names its session, oldest
    name first. The log is read by `agent_turn.inspect_claude_log`, the one reader of a Claude
    stream-json log; the `cwd` is the `system/init` event's own. A log that never named its
    session — a process that died before its first event — has nothing to join and is left out."""
    runs = []
    for path in files.find_run_logs(logs_dir):
        lines = files.read_lines(path) or []
        turn = agent_turn.inspect_claude_log("\n".join(lines))
        if not turn.session_id:
            continue
        cwd = None
        for line in lines:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") == "system" and event.get("subtype") == "init":
                cwd = event.get("cwd")
                break
        runs.append(Run(session_id=turn.session_id, name=path.stem, cwd=cwd,
                        state=turn.state, started_at=None))
    return tuple(runs)


def with_run_log_runs(parsed: ParsedRuns, extra: tuple[Run, ...]) -> ParsedRuns:
    """`parsed` plus every run of `extra` whose session it does not already hold."""
    held = {run.session_id for run in parsed.runs}
    added = tuple(run for run in extra if run.session_id not in held)
    return dataclasses.replace(
        parsed, runs=parsed.runs + added, total_seen=parsed.total_seen + len(added)
    )


# ── Task 2 — a session id resolves to one transcript or to none ─────────


def transcript_for(session_id: str, projects_root: Path, files: Files) -> Path | None:
    """The single `<sid>.jsonl` under `<projects_root>/*/`, or `None`.

    A missing `projects_root` is not an error here — `Files.find_transcripts` over a
    nonexistent directory returns no matches rather than raising, which is exactly the "nothing
    to read" answer this function owes. A session id duplicated under two project slugs (not
    observed on this machine, but not ruled out either) resolves to the lexicographically first
    match rather than raising — deterministic, not correct-by-construction, because there is no
    fact on disk that says which of the two is the real one.
    """
    matches = sorted(files.find_transcripts(session_id, projects_root))
    return matches[0] if matches else None


# ── Task 3 — one API response yields one figure ────────────


def usage_records(path: Path, files: Files):
    """Yield `(usage, model, timestamp)` once per API RESPONSE in `path` — never once per
    `assistant` record, which is a content block of one.

    The harness splits one response across a record per content block (thinking, tool_use, text)
    and repeats its `message.usage` verbatim on each, keyed by a shared `message.id`. Summing per
    record inflated every figure this module has ever produced, by a factor that differs per
    population, so `message.id` is remembered and a repeat is skipped.

    **A record carrying no `message.id` is always yielded.** It has no identity to compare, so two
    of them are two responses as far as anything here can tell; dropping the second would trade an
    overcount for a silent undercount, which is the worse of the two — a missing figure cannot be
    noticed afterwards, and an inflated one at least shows up against a re-derivation.

    A transcript being read while its own run is still writing to it is the normal case, not an
    edge case — this reads a live agent's own file — so a truncated or malformed final line is
    skipped rather than fatal, and a missing file yields nothing rather than raising.
    """
    lines = files.read_lines(path)
    if lines is None:
        return
    seen_response_ids: set[str] = set()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except (ValueError, TypeError):
            continue
        if record.get("type") != "assistant":
            continue
        message = record.get("message") or {}
        usage = message.get("usage")
        if not usage:
            continue
        response_id = message.get("id")
        if response_id is not None:
            if response_id in seen_response_ids:
                continue
            seen_response_ids.add(response_id)
        yield usage, message.get("model"), record.get("timestamp")


# ── Task 4 — the five classes stay apart, and thinking is a share ─────────


@dataclass(frozen=True)
class ModelSpend:
    """One model's totals over a run — five classes, kept apart, none of them the others'
    sum. `thinking` is a share of `output`, never an addend to it, and is `None` when nothing
    this model produced carried `output_tokens_details` — a run whose records are all silent on
    thinking is a different fact from a run that spent zero of it."""

    input: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write_1h: int = 0
    cache_write_5m: int = 0
    thinking: int | None = None


def spend_by_model(records) -> dict[str, ModelSpend]:
    """One `ModelSpend` per model id found in `records` — `(usage, model, timestamp)` triples,
    as `usage_records` yields them. `usage.cache_creation_input_tokens` is never read directly:
    it is the sum of the two `cache_creation` ephemeral figures this reports apart, so reading
    it too would be a sixth class standing in for the other two.
    """
    totals: dict[str, dict] = {}
    thinking_seen: dict[str, bool] = {}
    for usage, model, _timestamp in records:
        acc = totals.setdefault(
            model,
            {
                "input": 0,
                "output": 0,
                "cache_read": 0,
                "cache_write_1h": 0,
                "cache_write_5m": 0,
                "thinking": 0,
            },
        )
        acc["input"] += usage.get("input_tokens") or 0
        acc["output"] += usage.get("output_tokens") or 0
        acc["cache_read"] += usage.get("cache_read_input_tokens") or 0
        creation = usage.get("cache_creation") or {}
        acc["cache_write_1h"] += creation.get("ephemeral_1h_input_tokens") or 0
        acc["cache_write_5m"] += creation.get("ephemeral_5m_input_tokens") or 0
        details = usage.get("output_tokens_details")
        if details is not None:
            thinking_seen[model] = True
            acc["thinking"] += details.get("thinking_tokens") or 0

    return {
        model: ModelSpend(
            input=acc["input"],
            output=acc["output"],
            cache_read=acc["cache_read"],
            cache_write_1h=acc["cache_write_1h"],
            cache_write_5m=acc["cache_write_5m"],
            thinking=acc["thinking"] if thinking_seen.get(model) else None,
        )
        for model, acc in totals.items()
    }


def add_spend(a: ModelSpend, b: ModelSpend) -> ModelSpend:
    """One model's two `ModelSpend`s, added class by class — never a class summed with another
    class, only the same class across two readings. `thinking` stays `None` only when neither side
    carried any, matching `ModelSpend`'s own rule that `None` means "nothing this model produced
    carried `output_tokens_details`", not zero.

    Public and here, rather than private in a reader, because this module owns what a spend IS.
    It was `flow_usage._add_spend` while that reader was the only one folding two readings
    together; a third reader wanting the same arithmetic is what a private name cannot serve.
    """
    thinking = None
    if a.thinking is not None or b.thinking is not None:
        thinking = (a.thinking or 0) + (b.thinking or 0)
    return ModelSpend(
        input=a.input + b.input,
        output=a.output + b.output,
        cache_read=a.cache_read + b.cache_read,
        cache_write_1h=a.cache_write_1h + b.cache_write_1h,
        cache_write_5m=a.cache_write_5m + b.cache_write_5m,
        thinking=thinking,
    )


def merge_spend(
    a: dict[str, ModelSpend], b: dict[str, ModelSpend]
) -> dict[str, ModelSpend]:
    """Two per-model spend dicts, merged model by model with `add_spend`. A model present in only
    one side passes through unchanged, and neither argument is mutated — a caller folding many
    readings into one accumulator would otherwise corrupt the first as it went.
    """
    merged = dict(a)
    for model, spend in b.items():
        merged[model] = add_spend(merged[model], spend) if model in merged else spend
    return merged


# ── Task 5 — the span is measured, never summed ───────────────


def span_seconds(records) -> float | None:
    """The run's wall time — its last transcript timestamp minus its first — never a sum of
    per-message latencies, which no record on disk carries (`durationMs` is on none of them).
    Timestamps are read out of order-of-arrival, not order-in-the-file: min to max over the
    whole set, so a transcript whose lines are not chronological still gives the true span.
    """
    timestamps = []
    for _usage, _model, timestamp in records:
        if not timestamp:
            continue
        try:
            timestamps.append(datetime.fromisoformat(timestamp.replace("Z", "+00:00")))
        except (ValueError, TypeError):
            continue
    if not timestamps:
        return None
    return (max(timestamps) - min(timestamps)).total_seconds()


# ── Task 6 — the ledger states what it could not read ─────────────


@dataclass(frozen=True)
class Coverage:
    """How much of the population this reading actually covered — never implied, always
    stated, so a run with nothing to report and a run whose transcript is gone read as the
    two different facts they are. `dropped_no_session` is a third, earlier fact — a row
    `runs_from` never admitted to the population at all, for having no `sessionId` to join a
    transcript on — kept apart from `unreadable` (in scope but unjoinable) the same way
    `ParsedRuns` keeps it apart from `interactive_excluded`.
    `read + unreadable + dropped_no_session` equals the population before dropping."""

    read: int
    unreadable: int
    total: int
    unreadable_ids: tuple[str, ...]
    dropped_no_session: int = 0


@dataclass(frozen=True)
class LedgerRow:
    """One run's reading: its identity from `claude agents --json --all`, its wall time, and
    its spend by model. `spend == {}` means a transcript that read cleanly and reported
    nothing — never the same fact as the run being absent from the ledger altogether."""

    session_id: str
    name: str | None
    cwd: str | None
    state: str | None
    started_at: int | None
    span_seconds: float | None
    spend: dict[str, ModelSpend]


@dataclass(frozen=True)
class Ledger:
    rows: tuple[LedgerRow, ...]
    coverage: Coverage


def ledger(runs, projects_root: Path, files: Files, *, dropped_no_session: int = 0) -> Ledger:
    """One `LedgerRow` per run whose transcript is readable, plus a `Coverage` naming every run
    this could not read by session id — a transcript that resolves but holds no usage records
    still produces a row (read, zero spend); only a run with no transcript at all is unreadable.

    `dropped_no_session` carries `ParsedRuns.dropped_no_session` through to `Coverage` — this
    function never computes it, since `runs` has already had those rows dropped by the time it
    arrives here. A caller that does not pass it gets `0`, a stated count rather than an absent
    field.
    """
    rows: list[LedgerRow] = []
    unreadable_ids: list[str] = []
    runs = list(runs)
    for run in runs:
        path = transcript_for(run.session_id, projects_root, files)
        if path is None:
            unreadable_ids.append(run.session_id)
            continue
        records = list(usage_records(path, files))
        rows.append(
            LedgerRow(
                session_id=run.session_id,
                name=run.name,
                cwd=run.cwd,
                state=run.state,
                started_at=run.started_at,
                span_seconds=span_seconds(records),
                spend=spend_by_model(records),
            )
        )

    return Ledger(
        rows=tuple(rows),
        coverage=Coverage(
            read=len(rows),
            unreadable=len(unreadable_ids),
            total=len(runs),
            unreadable_ids=tuple(unreadable_ids),
            dropped_no_session=dropped_no_session,
        ),
    )


# ── Task 7 — the two renderings, and neither one totals ────────────


def _coverage_line(coverage: Coverage) -> str:
    line = (
        f"Coverage: {coverage.read} read / {coverage.unreadable} unreadable / "
        f"{coverage.total} total"
    )
    if coverage.unreadable_ids:
        line += " — unreadable: " + ", ".join(coverage.unreadable_ids)
    return line


def render(ledger: Ledger) -> str:
    """The human summary. Every number here is one of the five classes or a plain count — never
    their sum, so a rendered figure is always traceable back to one thing that was actually
    metered.
    """
    lines = [
        POPULATION_NOTE,
        _coverage_line(ledger.coverage),
        f"Dropped (no sessionId): {ledger.coverage.dropped_no_session}",
        "",
    ]
    if not ledger.rows:
        lines.append("No runs read.")
        return "\n".join(lines).rstrip() + "\n"

    for row in ledger.rows:
        lines.append(
            f"{row.session_id}  {row.name or '(unnamed)'}  cwd={row.cwd}  state={row.state}"
        )
        span = "n/a" if row.span_seconds is None else f"{row.span_seconds:g}s"
        lines.append(f"  started={row.started_at}  span={span}")
        if not row.spend:
            lines.append("  no usage records")
        for model, spend in row.spend.items():
            thinking = "" if spend.thinking is None else f" thinking={spend.thinking}"
            lines.append(
                f"  {model}: input={spend.input} output={spend.output}{thinking} "
                f"cache_read={spend.cache_read} cache_write_1h={spend.cache_write_1h} "
                f"cache_write_5m={spend.cache_write_5m}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_json(ledger: Ledger) -> str:
    """The machine rows — same population sentence and coverage as `render`, one object per
    readable run, and the same never-summed five classes (`thinking` stays `null`, not `0`,
    when nothing this model produced carried it)."""
    payload = {
        "population": POPULATION_NOTE,
        "coverage": {
            "read": ledger.coverage.read,
            "unreadable": ledger.coverage.unreadable,
            "total": ledger.coverage.total,
            "unreadable_ids": list(ledger.coverage.unreadable_ids),
            "dropped_no_session": ledger.coverage.dropped_no_session,
        },
        "rows": [
            {
                "session_id": row.session_id,
                "name": row.name,
                "cwd": row.cwd,
                "state": row.state,
                "started_at": row.started_at,
                "span_seconds": row.span_seconds,
                "spend": {
                    model: {
                        "input": spend.input,
                        "output": spend.output,
                        "thinking": spend.thinking,
                        "cache_read": spend.cache_read,
                        "cache_write_1h": spend.cache_write_1h,
                        "cache_write_5m": spend.cache_write_5m,
                    }
                    for model, spend in row.spend.items()
                },
            }
            for row in ledger.rows
        ],
    }
    return json.dumps(payload, indent=2)


# ── The ports ───────────────────────────
#
# Every world-reach this reader makes — the filesystem, a subprocess — arrives through one of
# these two. Neither is constructed anywhere but `build_reader()`, below.


class Files:
    """Every filesystem touch this reader makes: finding a session's transcript files under a
    projects root, finding an instance's `claude-*.jsonl` run logs, and reading a file's lines.
    Nothing else."""

    def find_transcripts(self, session_id: str, projects_root: Path) -> list[Path]:
        """Every `<session_id>.jsonl` under `<projects_root>/*/`, in no particular order — the
        caller decides how to pick one. A `projects_root` that does not exist yields no matches
        rather than raising, the same answer as one that exists and holds none."""
        return list(projects_root.glob(f"*/{session_id}.jsonl"))

    def find_run_logs(self, logs_dir: Path) -> list[Path]:
        """Every `claude-*.jsonl` run log directly under `logs_dir`, sorted by name — nothing
        when the directory does not exist."""
        return sorted(logs_dir.glob("claude-*.jsonl"))

    def read_lines(self, path: Path) -> list[str] | None:
        """`path`'s lines, or `None` when it cannot be read at all — an absence this reader
        always has a decision for, never an exception every call site would have to catch."""
        try:
            return path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return None


class Processes:
    """Every process this reader starts."""

    def run(self, argv: list[str]) -> str:
        """`argv`'s stdout, decoded as text. Raises `SystemExit` naming the exit code and the
        captured stderr on a non-zero exit — this reader has no caller above it to report to."""
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            raise SystemExit(
                f"error: `{' '.join(argv)}` exited {proc.returncode}: {proc.stderr.strip()}"
            )
        return proc.stdout


# ── Task 8 — the CLI, the docstring and the version ─────────────


def _agents_json_text(agents_json_path: Path | None, files: Files, processes: Processes) -> str:
    """The `claude agents --json --all` text this run reads: a saved file when one is given —
    the seam a test uses to shell out to nothing — else the live command.

    A saved file is read through the same two-capability `Files` port `transcript_for` and
    `usage_records` use — `read_lines`, joined back into text — rather than a third filesystem
    reach of its own. A missing saved file is a usage error a caller can act on, so it is
    `SystemExit` here rather than a silent empty ledger.
    """
    if agents_json_path is not None:
        lines = files.read_lines(agents_json_path)
        if lines is None:
            raise SystemExit(f"error: could not read {agents_json_path}")
        return "\n".join(lines)
    return processes.run(["claude", "agents", "--json", "--all"])


# ── The composition root: the only place a concrete implementation is constructed ────


@dataclass(frozen=True)
class Reader:
    """The reader's whole environment: both ports it reaches the world through, plus the
    projects root resolved to a concrete `Path` — the one environment reach `build_reader`
    performs itself, because expanding a home directory is a reach into the environment like
    any other and belongs at the composition root, not in an argparse default or a unit's own
    body."""

    files: Files
    processes: Processes
    projects_root: Path


def build_reader(projects_root: Path | None = None) -> Reader:
    """Wire the real ports. The only place `Files()` or `Processes()` is constructed. A
    `projects_root` of `None` resolves to `~/.claude/projects`, here rather than at an argparse
    default or inside a unit's own body."""
    default_root = Path.home() / ".claude" / "projects"
    return Reader(
        files=Files(),
        processes=Processes(),
        projects_root=projects_root if projects_root is not None else default_root,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_usage.py",
        description=(
            "What a background run used, read off its own transcript. No price model and no "
            "currency — this counts, it does not price. Five usage classes are kept apart and "
            "never summed: input, output, cache_read, and usage.cache_creation's own "
            "cache_write_1h / cache_write_5m split."
        ),
    )
    parser.add_argument(
        "--agents-json",
        type=Path,
        default=None,
        help="path to saved `claude agents --json --all` output (default: shell out to it)",
    )
    parser.add_argument(
        "--projects-root",
        type=Path,
        default=None,
        help="root holding <slug>/<sessionId>.jsonl transcripts (default: ~/.claude/projects)",
    )
    parser.add_argument(
        "--run-logs",
        type=Path,
        default=None,
        help="an instance's system/logs: add every claude --print run whose run log names its "
        "session (such a run is in no `claude agents` listing)",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit the ledger as JSON instead of the human summary"
    )
    args = parser.parse_args(argv)

    reader = build_reader(args.projects_root)

    text = _agents_json_text(args.agents_json, reader.files, reader.processes)

    try:
        parsed = runs_from(text)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.run_logs is not None:
        parsed = with_run_log_runs(parsed, runs_from_run_logs(args.run_logs, reader.files))

    led = ledger(
        parsed.runs,
        reader.projects_root,
        reader.files,
        dropped_no_session=parsed.dropped_no_session,
    )
    if args.json:
        print(render_json(led))
    else:
        print(render(led), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
