#!/usr/bin/env python3
"""flow_usage.py — what a `/development` flow run spent, one row per step.

WHY THIS EXISTS
    `run_usage.py` already reads what a background run spent, but it cannot reach a Workflow's
    own steps: its population is `claude agents --json --all` rows (`kind != "interactive"`),
    which name no stage agent, and its join is a flat `<slug>/<sessionId>.jsonl` glob. A
    `/development` flow's stage agents live one level deeper —
    `<projects_root>/<slug>/<sessionId>/subagents/workflows/<wf_id>/` — reached through the
    parent session's own directory, and that parent is often `kind: "interactive"`, which
    `run_usage.py`'s population excludes on purpose. Two different populations, two different
    joins, one unit apiece (a run there, a step here).

    Measured against the live disk on 2026-09-07 (58 workflow runs, 593 agents):

    1. Each run holds `agent-<agentId>.jsonl` (593), `agent-<agentId>.meta.json` (593), and one
       `journal.jsonl`. The flat sibling `<sessionId>/subagents/agent-*.jsonl` (538) holds
       Agent-tool subagents — same record shape, no journal, no workflow — and is never reached
       by this reader's population.
    2. `agent-<id>.meta.json` names the agent: 593 of 593 carry `agentType`, 411 also carry
       `model`. A sidecar this reader cannot find or parse reports `None` for both rather than
       inventing a value — a different fact from a model or type named `"unknown"`.
    3. The step comes from `journal.jsonl`, and only sometimes: 593 `started`, 570 `result`, 1
       `failed`. **394 of 570 `result` records carry no `step` at all** — the majority case, not
       the exception — and this reader reports that population under a stated `agentType`
       fallback rather than dropping it.
    4. Producer and auditor share a step name and come apart only on the result payload:
       `status: "ok"` with an `artifact` is the producer, `result: "findings"` with a `findings`
       count is the auditor. Nothing else distinguishes them, and a result that fits neither
       shape is treated the same as one with no step — attributed, not guessed.
    5. The usage records need no new handling — `message.usage` on `assistant` records is
       exactly what `run_usage.usage_records` and `run_usage.spend_by_model` already split into
       five classes, imported here rather than re-implemented. The accumulator that folds two of
       those readings together — `run_usage.add_spend` / `merge_spend` — was private here until a
       third reader wanted it, and now lives beside `ModelSpend` for the same reason.
    6. 23 of the 593 started agents had no result on the day this was measured — in flight, or
       gone quiet. They are reported as unfinished, not dropped: a run read mid-flight is the
       normal case for a reader over live disk state.

    **No price model, no currency** — this counts, it does not price, exactly like its sibling.
    **This reader does not attribute the orchestrator.** A Workflow runs detached from the
    session that launched it; that parent's own spend inside the run's window is overlap, not
    the flow's, and is out of scope by the seed this reader was cut from.

Usage:  python3 <CORE>/tools/flow_usage.py [--projects-root DIR] [--wf WF_ID] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import run_usage

__version__ = "1.0.1"

FALLBACK_NOTE = (
    "Fallback: an agent whose journal result carries no step (or none this reader could "
    "attribute to a producer or an auditor) is grouped by its agentType instead, marked "
    "fallback so a reader can tell a step from a name."
)


# ── Task 1 — the workflow runs are found ───────────────────────────────


@dataclass(frozen=True)
class FlowRun:
    """One workflow run this reader can reach — its `wf_id`, the parent session id and project
    slug it is nested under, and the directory holding its `journal.jsonl` and its agents'
    transcripts. All three identity fields are read off the path itself, not guessed: the tree
    shape (`<projects_root>/<slug>/<sid>/subagents/workflows/<wf_id>/`) is the only source for
    them, because nothing inside `journal.jsonl` restates its own workflow id or parent
    session."""

    wf_id: str
    session_id: str
    slug: str
    run_dir: Path


def flow_runs(projects_root: Path, files: Files) -> tuple[FlowRun, ...]:
    """Every workflow run under `projects_root` whose directory holds a `journal.jsonl` — the
    population this reader scopes itself to. Sorted by `wf_id` for a deterministic reading. A
    `projects_root` that does not exist yields nothing, the same answer `Files.find_workflow_dirs`
    already gives for one that exists and holds none."""
    runs = []
    for run_dir in files.find_workflow_dirs(projects_root):
        # run_dir == <projects_root>/<slug>/<sid>/subagents/workflows/<wf_id>
        wf_id = run_dir.name
        session_id = run_dir.parent.parent.parent.name
        slug = run_dir.parent.parent.parent.parent.name
        runs.append(FlowRun(wf_id=wf_id, session_id=session_id, slug=slug, run_dir=run_dir))
    return tuple(sorted(runs, key=lambda r: r.wf_id))


# ── Task 2 — the journal names each agent's step and its role ─────────────


class Role(str, Enum):
    """Which side of a step an agent ran — the value is written into `--json` output, so it is
    the `(str, Enum)` form per `languages/python/conventions.md` § Constructs."""

    PRODUCE = "produce"
    AUDIT = "audit"


@dataclass(frozen=True)
class AgentStep:
    """One agent's step attribution — its journal `agentId`, the step it ran, and which side of
    that step it was."""

    agent_id: str
    step: str
    role: Role


@dataclass(frozen=True)
class StepsFromJournal:
    """`steps_from`'s whole answer. `step_less` and `unfinished` are two different reasons an
    agent carries no step: the first got a `result` whose payload named none (or named one this
    reader could not attribute to a role); the second never got a `result` or a `failed` at
    all. Conflating them would hide that a run read mid-flight (`unfinished`) is a different
    fact from a run whose step this reader could not read (`step_less`)."""

    steps: tuple[AgentStep, ...]
    step_less: tuple[str, ...]
    unfinished: tuple[str, ...]
    failed: tuple[str, ...]


def _step_and_role(payload) -> tuple[str | None, Role | None]:
    """The step and role a `result` record's payload names, or `(None, None)` when it names
    none — a plain string payload, a dict with no `step`, or (defensively) a dict that carries a
    `step` but matches neither the producer shape (`status: "ok"`) nor the auditor shape
    (`result: "findings"`): the two shapes the plan's own measurement found on the live disk. A
    third shape is not guessed a role — it is reported as step-less, the same as no step at all."""
    if not isinstance(payload, dict):
        return None, None
    step = payload.get("step")
    if not step:
        return None, None
    if payload.get("status") == "ok":
        return step, Role.PRODUCE
    if payload.get("result") == "findings":
        return step, Role.AUDIT
    return None, None


def steps_from(journal_text: str) -> StepsFromJournal:
    """Parse a `journal.jsonl`'s text into a step attribution per `agentId`, plus the agents
    that started and never reported. A malformed line is skipped rather than fatal — the same
    read-a-live-file posture `run_usage.usage_records` already takes."""
    started: set[str] = set()
    resulted: set[str] = set()
    failed: set[str] = set()
    steps: list[AgentStep] = []
    step_less: list[str] = []

    for line in journal_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except (ValueError, TypeError):
            continue
        if not isinstance(record, dict):
            continue
        agent_id = record.get("agentId")
        if not agent_id:
            continue
        record_type = record.get("type")
        if record_type == "started":
            started.add(agent_id)
        elif record_type == "failed":
            failed.add(agent_id)
        elif record_type == "result":
            resulted.add(agent_id)
            step, role = _step_and_role(record.get("result"))
            if step is None or role is None:
                step_less.append(agent_id)
            else:
                steps.append(AgentStep(agent_id=agent_id, step=step, role=role))

    unfinished = tuple(sorted(started - resulted - failed))
    return StepsFromJournal(
        steps=tuple(steps),
        step_less=tuple(step_less),
        unfinished=unfinished,
        failed=tuple(sorted(failed)),
    )


# ── Task 3 — the meta sidecar names the agent ──────────────────────────


@dataclass(frozen=True)
class AgentMeta:
    """What `agent-<id>.meta.json` says about one agent — `None` for either field it omits or a
    sidecar this reader could not read at all, never invented."""

    agent_type: str | None
    model: str | None


def agent_meta(run_dir: Path, agent_id: str, files: Files) -> AgentMeta:
    """`agentType` and `model` from `<run_dir>/agent-<agent_id>.meta.json`. A missing sidecar and
    a malformed one report the same `AgentMeta(None, None)` — this reader still reports the
    agent, just with nothing this file could tell it."""
    text = files.read_text(run_dir / f"agent-{agent_id}.meta.json")
    if text is None:
        return AgentMeta(agent_type=None, model=None)
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return AgentMeta(agent_type=None, model=None)
    if not isinstance(data, dict):
        return AgentMeta(agent_type=None, model=None)
    return AgentMeta(agent_type=data.get("agentType"), model=data.get("model"))


# ── Task 4 — an agent's spend uses the sibling's accumulator, not a copy ─────


def agent_spend(run_dir: Path, agent_id: str, files: Files) -> dict[str, run_usage.ModelSpend]:
    """One `ModelSpend` per model id found in `<run_dir>/agent-<agent_id>.jsonl` — read through
    `run_usage.usage_records` and summed by `run_usage.spend_by_model`, the sibling reader's own
    accumulator, not a second one. An agent file that does not exist reads as no records, which
    `run_usage.spend_by_model` turns into `{}` — an empty spend the caller still counts, never a
    skip."""
    path = run_dir / f"agent-{agent_id}.jsonl"
    records = run_usage.usage_records(path, files)
    return run_usage.spend_by_model(records)


# ── The assembly this reader needs between Tasks 4 and 5 ────────────────
#
# The plan cuts step attribution (Task 2), agent identity (Task 3) and agent spend (Task 4) into
# three separate functions, and `aggregate(run)` / `coverage(run)` (Tasks 5-6) both consume one
# already-assembled reading of a run. `read_run` is that assembly — it is not named by the plan,
# and exists because "aggregate(run)" and "coverage(run)" both need the same "run" to consume.


@dataclass(frozen=True)
class AgentReading:
    """One agent, fully read: its step attribution (if any), its identity from the meta
    sidecar, its spend, and whether the journal ever saw it finish."""

    agent_id: str
    step: str | None
    role: Role | None
    agent_type: str | None
    model_hint: str | None
    spend: dict[str, run_usage.ModelSpend] = field(default_factory=dict)
    unfinished: bool = False
    failed: bool = False


@dataclass(frozen=True)
class RunReading:
    """One `FlowRun`, fully read — every agent the journal named, plus the agent files the
    journal never mentioned at all (coverage's fourth figure, kept apart from the per-agent list
    because an orphan file has no step, no role and no journal-derived identity to report a row
    for)."""

    flow_run: FlowRun
    agents: tuple[AgentReading, ...]
    orphan_agent_files: tuple[str, ...]


def read_run(flow_run: FlowRun, files: Files) -> RunReading:
    """Assemble one `RunReading` for `flow_run` — parse its journal (Task 2), then look up each
    named agent's identity (Task 3) and spend (Task 4)."""
    journal_text = files.read_text(flow_run.run_dir / "journal.jsonl")
    parsed = steps_from(journal_text or "")
    step_by_agent = {s.agent_id: s for s in parsed.steps}
    journal_agent_ids = (
        set(step_by_agent) | set(parsed.step_less) | set(parsed.unfinished) | set(parsed.failed)
    )
    file_agent_ids = set(files.agent_ids_in(flow_run.run_dir))

    agents = []
    for agent_id in sorted(journal_agent_ids):
        step_entry = step_by_agent.get(agent_id)
        meta = agent_meta(flow_run.run_dir, agent_id, files)
        spend = agent_spend(flow_run.run_dir, agent_id, files)
        agents.append(
            AgentReading(
                agent_id=agent_id,
                step=step_entry.step if step_entry else None,
                role=step_entry.role if step_entry else None,
                agent_type=meta.agent_type,
                model_hint=meta.model,
                spend=spend,
                unfinished=agent_id in parsed.unfinished,
                failed=agent_id in parsed.failed,
            )
        )

    orphans = tuple(sorted(file_agent_ids - journal_agent_ids))
    return RunReading(flow_run=flow_run, agents=tuple(agents), orphan_agent_files=orphans)


# ── Task 5 — a run aggregates per step, and step-less agents fall back by name ──


@dataclass(frozen=True)
class AggregateRow:
    """One row of a run's aggregated spend — keyed by `(label, role)` when a step is known, or
    by `label` alone (an `agentType`) when it is not, in which case `is_fallback` is `True`.
    `spend` is summed class-by-class across every agent in `agent_ids`, never across classes.

    `agent_types` is a column of its own, not a restatement of `label`: on a step row the label
    is the step, so without this a reader sees that `development-specs` ran and never which
    agent ran it. It carries the distinct types across the row's agents — a `(step, role)` row
    can hold several — and keeps `None` as the stated absence `agent_meta` reports for a sidecar
    that named no type, rather than dropping it or inventing one."""

    label: str
    role: Role | None
    is_fallback: bool
    agent_ids: tuple[str, ...]
    agent_types: tuple[str | None, ...]
    spend: dict[str, run_usage.ModelSpend]


def _distinct_agent_types(agents: list[AgentReading]) -> tuple[str | None, ...]:
    """The distinct `agentType`s across `agents`, named ones first in name order and the stated
    `None` last — `sorted` cannot order `None` against a `str` directly, and dropping it would
    turn "this sidecar named no type" into "this row has no agents without one"."""
    seen = {a.agent_type for a in agents}
    named = sorted(t for t in seen if t is not None)
    return tuple(named) + ((None,) if None in seen else ())


def aggregate(run: RunReading) -> tuple[AggregateRow, ...]:
    """One row per `(step, role)` where an agent's step is known, one row per `agentType` where
    it is not (marked `is_fallback`). Two agents sharing a `(step, role)` merge into one row;
    two agents on the same step with different roles stay two rows. A run with no agents
    returns no rows."""
    grouped: dict[tuple[str, Role | None, bool], list[AgentReading]] = {}
    for agent in run.agents:
        if agent.step is not None and agent.role is not None:
            key = (agent.step, agent.role, False)
        else:
            key = (agent.agent_type or "(unknown)", None, True)
        grouped.setdefault(key, []).append(agent)

    rows = []
    for (label, role, is_fallback), agents in grouped.items():
        spend: dict[str, run_usage.ModelSpend] = {}
        for agent in agents:
            spend = run_usage.merge_spend(spend, agent.spend)
        rows.append(
            AggregateRow(
                label=label,
                role=role,
                is_fallback=is_fallback,
                agent_ids=tuple(a.agent_id for a in agents),
                agent_types=_distinct_agent_types(agents),
                spend=spend,
            )
        )
    return tuple(rows)


# ── Task 6 — coverage is stated, never implied ─────────────────────────


@dataclass(frozen=True)
class Coverage:
    """How much of one run's population this reading actually covered. `with_step` +
    `without_step` accounts for every agent the journal named at all; `without_step` and
    `started_no_result` overlap on purpose — an agent that never got a result is both. A file
    on disk the journal never mentioned counts only in `files_with_no_journal_entry`, which is
    what tells a reader the journal is not the whole truth."""

    with_step: int
    without_step: int
    started_no_result: int
    files_with_no_journal_entry: int


def coverage(run: RunReading) -> Coverage:
    """The four coverage figures for `run` — each counted independently over `run.agents` and
    `run.orphan_agent_files`, never derived from one another."""
    with_step = sum(1 for a in run.agents if a.step is not None)
    without_step = sum(1 for a in run.agents if a.step is None)
    started_no_result = sum(1 for a in run.agents if a.unfinished)
    return Coverage(
        with_step=with_step,
        without_step=without_step,
        started_no_result=started_no_result,
        files_with_no_journal_entry=len(run.orphan_agent_files),
    )


# ── Task 7 — the report renders, and `--json` carries the same numbers ────


def _coverage_line(cov: Coverage) -> str:
    return (
        f"Coverage: {cov.with_step} with a step / {cov.without_step} without / "
        f"{cov.started_no_result} started with no result / "
        f"{cov.files_with_no_journal_entry} agent files with no journal entry at all"
    )


def _types_column(row: AggregateRow) -> str:
    """The row's agent-type column. `None` renders as `(none)` — the parenthesised form keeps it
    apart from a real `agentType` literally named `none`, the same distinction `agent_meta`'s
    `None` draws against a type named `"unknown"`."""
    return ",".join(t if t is not None else "(none)" for t in row.agent_types) or "(none)"


def render(runs: list[RunReading]) -> str:
    """The human table — one section per run, one line per `(step, role)` or fallback
    `agentType` row, carrying the row's agent types, then per model the five classes with
    `thinking` reported as a share of `output`, never added to it. States the fallback rule and
    each run's four coverage figures in the reader's own words, never leaving them implied."""
    lines = [FALLBACK_NOTE, ""]
    if not runs:
        lines.append("No workflow runs read.")
        return "\n".join(lines).rstrip() + "\n"

    for run in runs:
        lines.append(
            f"{run.flow_run.wf_id}  session={run.flow_run.session_id}  slug={run.flow_run.slug}"
        )
        lines.append(f"  {_coverage_line(coverage(run))}")
        rows = aggregate(run)
        if not rows:
            lines.append("  No agents read for this run.")
            lines.append("")
            continue
        for row in rows:
            row_label = (
                f"{row.label} ({row.role.value})" if row.role else f"{row.label} [fallback]"
            )
            lines.append(
                f"  {row_label}  types={_types_column(row)}  "
                f"agents={','.join(row.agent_ids)}"
            )
            for model, spend in row.spend.items():
                thinking = "" if spend.thinking is None else f" thinking={spend.thinking}"
                lines.append(
                    f"    {model}: input={spend.input} output={spend.output}{thinking} "
                    f"cache_read={spend.cache_read} cache_write_1h={spend.cache_write_1h} "
                    f"cache_write_5m={spend.cache_write_5m}"
                )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_json(runs: list[RunReading]) -> str:
    """The machine rows — same fallback note and per-run coverage as `render`, the same
    never-summed five classes."""
    payload = {
        "fallback": FALLBACK_NOTE,
        "runs": [
            {
                "wf_id": run.flow_run.wf_id,
                "session_id": run.flow_run.session_id,
                "slug": run.flow_run.slug,
                "coverage": {
                    "with_step": coverage(run).with_step,
                    "without_step": coverage(run).without_step,
                    "started_no_result": coverage(run).started_no_result,
                    "files_with_no_journal_entry": coverage(run).files_with_no_journal_entry,
                },
                "rows": [
                    {
                        "label": row.label,
                        "role": row.role.value if row.role else None,
                        "is_fallback": row.is_fallback,
                        "agent_ids": list(row.agent_ids),
                        "agent_types": list(row.agent_types),
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
                    for row in aggregate(run)
                ],
            }
            for run in runs
        ],
    }
    return json.dumps(payload, indent=2)


# ── The ports ────────────────────────────
#
# Every world-reach this reader makes — all of it filesystem — arrives through `Files`. Nothing
# else is constructed anywhere but `build_reader()`.


class Files:
    """Every filesystem touch this reader makes."""

    def find_workflow_dirs(self, projects_root: Path) -> list[Path]:
        """Every `<projects_root>/<slug>/<sid>/subagents/workflows/<wf_id>/` that holds a
        `journal.jsonl` — never the flat sibling `<slug>/<sid>/subagents/agent-*.jsonl` (an
        Agent-tool subagent, no workflow) and never `<slug>/<sid>.jsonl` (an interactive
        session), because neither matches this glob's shape. A nonexistent `projects_root`
        yields no matches rather than raising, the same answer `Path.glob` gives for one that
        exists and holds none."""
        return [p.parent for p in projects_root.glob("*/*/subagents/workflows/*/journal.jsonl")]

    def agent_ids_in(self, run_dir: Path) -> list[str]:
        """Every agent id with an `agent-<id>.jsonl` transcript under `run_dir` — the left side
        of the fourth coverage figure, a file present with no journal entry at all."""
        return [p.stem[len("agent-") :] for p in run_dir.glob("agent-*.jsonl")]

    def read_text(self, path: Path) -> str | None:
        """`path`'s whole text, or `None` when it cannot be read at all — used for
        `journal.jsonl` and `agent-<id>.meta.json`, neither of which is read line-by-line."""
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    def read_lines(self, path: Path) -> list[str] | None:
        """`path`'s lines, or `None` when it cannot be read at all. The exact shape
        `run_usage.usage_records` expects of its own `files` argument — this port hands itself
        straight to that imported function rather than owning a second implementation."""
        try:
            return path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return None


# ── The composition root: the only place a concrete implementation is constructed ────


@dataclass(frozen=True)
class Reader:
    """The reader's whole environment: the one port it reaches the world through, plus the
    projects root resolved to a concrete `Path` — the one environment reach `build_reader`
    performs itself, per `run_usage.py`'s own `Reader`/`build_reader` shape."""

    files: Files
    projects_root: Path


def build_reader(projects_root: Path | None = None) -> Reader:
    """Wire the real port. The only place `Files()` is constructed. A `projects_root` of `None`
    resolves to `~/.claude/projects`, here rather than at an argparse default or inside a unit's
    own body."""
    default_root = Path.home() / ".claude" / "projects"
    return Reader(
        files=Files(),
        projects_root=projects_root if projects_root is not None else default_root,
    )


# ── Task 8 — the CLI ────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="flow_usage.py",
        description=(
            "What a `/development` flow run spent, one row per step — producer apart from "
            "auditor, in the five usage classes `run_usage.py` already keeps apart. No price "
            "model and no currency: this counts, it does not price."
        ),
    )
    parser.add_argument(
        "--projects-root",
        type=Path,
        default=None,
        help=(
            "root holding <slug>/<sid>/subagents/workflows/<wf_id>/ trees "
            "(default: ~/.claude/projects)"
        ),
    )
    parser.add_argument(
        "--wf",
        default=None,
        help="read only the workflow run with this wf_id (default: every run under the root)",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit the report as JSON instead of the human table"
    )
    args = parser.parse_args(argv)

    reader = build_reader(args.projects_root)
    all_runs = flow_runs(reader.projects_root, reader.files)

    if args.wf is not None:
        selected = [r for r in all_runs if r.wf_id == args.wf]
        if not selected:
            print(f"error: no workflow run found for --wf {args.wf}", file=sys.stderr)
            return 1
    else:
        selected = list(all_runs)

    readings = [read_run(r, reader.files) for r in selected]

    if args.json:
        print(render_json(readings))
    else:
        print(render(readings), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
