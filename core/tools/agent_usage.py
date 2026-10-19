#!/usr/bin/env python3
"""agent_usage.py — what each agent spent, one row per agent, off the OTLP telemetry stream.

WHY THIS EXISTS
    A subagent's spend is recorded nowhere else on disk: `run_usage.py` and `flow_usage.py` both
    read a transcript, and a Workflow-spawned agent leaves none. `otel_receiver.py` already writes
    every request Claude Code makes to `~/.kensaiapp/telemetry/logs.jsonl` and
    `metrics.jsonl` — this is the fourth reader in the family, the first that reads the stream
    rather than a transcript.

    Measured 2026-09-11 over the live stream (1,824 `api_request` records, 26 sessions):

    1. **The logs carry the rows.** `api_request` carries `session.id`, `query_source`,
       `agent.name`, `workflow.run_id`, `model`, the four token classes, `cost_usd` and
       `duration_ms`. `kensai.*` rides on both the record and the resource. `query_source` is not
       a closed set — 12 distinct values were seen, among them `agent:custom`, `repl_main_thread`,
       `agent:builtin:workflow-subagent`, `agent_summary` and `sdk` — and this reader assumes none
       of them.
    2. **The metrics are the check, not the source.** `claude_code.cost.usage` datapoints carry
       `aggregationTemporality: 1` (delta), so a reader that reads the last export undercounts;
       summed per session, they agreed with summed `api_request` `cost_usd` within 1% on 24 of 26
       sessions. The two that disagreed did so for stated reasons — one session made a single
       request shorter than the metrics export interval and exported no metric at all; the other
       was still running when measured.
    3. **`subagent_completed` counts Agent-tool agents only** — every sampled record carried
       `is_async: true`, and none of the 239 `agent:builtin:workflow-subagent` `api_request`
       records had a matching one. Its own `total_tokens` is a single lumped figure this reader
       never presents beside the four token classes it keeps apart everywhere else.
    4. **Every value arrives inside a typed envelope**, and the key is not fixed per field: an
       int64 may arrive as `{"intValue": "43"}` as easily as `{"intValue": 43}` (OTLP/JSON allows
       both), and a numeric field has been observed arriving as a `stringValue` on another event
       entirely. A reader that trusts one key per field silently reads nothing on the day the
       vendor picks the other one.

    **No price model, no currency.** `cost_usd` is the vendor's own figure; this counts it, and
    prices nothing itself.

Usage:  python3 <CORE>/tools/agent_usage.py [--dir DIR] [--where KEY=VALUE ...]
                                              [--compare ATTR A B] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

__version__ = "1.0.0"

EVENT_API_REQUEST = "api_request"
EVENT_SUBAGENT_COMPLETED = "subagent_completed"


# ── Task 1 — a value is read whatever envelope it arrives in ──────────────


def decode_value(value: dict[str, Any] | None) -> Any:
    """An OTLP attribute `value` object, decoded from whichever of `stringValue`, `intValue`,
    `doubleValue` or `boolValue` it carries — never assumed to be one fixed key. `intValue` is
    read as an `int` whether it arrived as a JSON number or (OTLP/JSON's other legal shape for an
    int64) a JSON string. A value carrying none of the four keys, that is not itself a dict, or an
    `intValue` string that is not a number, decodes to `None` rather than raising — a record this
    reader cannot make sense of is a record it reports nothing for, not one that stops the read."""
    if not isinstance(value, dict):
        return None
    if "stringValue" in value:
        return value["stringValue"]
    if "intValue" in value:
        raw = value["intValue"]
        if not isinstance(raw, str):
            return raw
        try:
            return int(raw)
        except ValueError:
            return None
    if "doubleValue" in value:
        return value["doubleValue"]
    if "boolValue" in value:
        return value["boolValue"]
    return None


def as_number(raw: Any) -> int | float:
    """Coerce a decoded attribute value to a number for summing. An `int`/`float` passes through;
    a `str` that parses as one is parsed (the numeric-field-arriving-as-a-string case `decode_value`
    itself cannot rule out); anything else — `None`, a non-numeric string, a `bool` — reads as
    zero. A summary that stops on one malformed field is worse than one that under-counts a
    single field it could not read."""
    if isinstance(raw, bool):
        return 0
    if isinstance(raw, (int, float)):
        return raw
    if isinstance(raw, str):
        try:
            return int(raw)
        except ValueError:
            try:
                return float(raw)
            except ValueError:
                return 0
    return 0


def _flatten_attributes(attrs: list[dict] | None) -> dict[str, Any]:
    """An OTLP `attributes` list — `[{"key": ..., "value": {...}}, ...]` — flattened to
    `{key: decoded value}`. A malformed entry (not a dict, or carrying no `key`) is skipped
    rather than raising."""
    flat: dict[str, Any] = {}
    for attr in attrs or []:
        if not isinstance(attr, dict):
            continue
        key = attr.get("key")
        if key is None:
            continue
        flat[key] = decode_value(attr.get("value"))
    return flat


@dataclass(frozen=True)
class LogRecord:
    """One OTLP log record, flattened to two attribute maps: its own, and the resource attributes
    of the export batch it arrived in. Kept apart rather than merged, because Task 2's `kensai.*`
    rule reads the record first and the resource second — merging here would discard which side a
    value came from."""

    record_attrs: dict[str, Any]
    resource_attrs: dict[str, Any]


@dataclass(frozen=True)
class LogLines:
    """`read_log_lines`'s whole answer — the records found, and how many lines could not be read
    at all. `skipped` is reported, never silent: a line skipped for being malformed is a
    different fact from a line that legitimately carried no log records."""

    records: tuple[LogRecord, ...]
    skipped: int


def read_log_lines(lines: list[str]) -> LogLines:
    """Parse `logs.jsonl`'s lines into flattened records. A blank line is ignored. A line that is
    not JSON, whose outer object is not a dict, or whose `body` is missing or empty (`{}` — the
    receiver's own shape for an export it had nothing to store) is skipped and counted; it never
    stops the read of the rest. A `body` naming no `resourceLogs`, or a malformed
    `resourceLogs`/`scopeLogs`/`logRecords` entry, is walked past rather than raised on."""
    records: list[LogRecord] = []
    skipped = 0
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        try:
            outer = json.loads(line)
        except (ValueError, TypeError):
            skipped += 1
            continue
        if not isinstance(outer, dict):
            skipped += 1
            continue
        body = outer.get("body")
        if not isinstance(body, dict) or not body:
            skipped += 1
            continue
        for resource_log in body.get("resourceLogs") or []:
            if not isinstance(resource_log, dict):
                continue
            resource_attrs = _flatten_attributes(
                (resource_log.get("resource") or {}).get("attributes")
            )
            for scope_log in resource_log.get("scopeLogs") or []:
                if not isinstance(scope_log, dict):
                    continue
                for log_record in scope_log.get("logRecords") or []:
                    if not isinstance(log_record, dict):
                        continue
                    records.append(
                        LogRecord(
                            record_attrs=_flatten_attributes(log_record.get("attributes")),
                            resource_attrs=resource_attrs,
                        )
                    )
    return LogLines(records=tuple(records), skipped=skipped)


# ── Task 2 — one row per agent ─────────────────────────────────────────────


def _attr(record: LogRecord, key: str) -> Any:
    """`key`'s value read off `record`'s own attributes first, the resource's second — the
    resolution the `kensai.*` rule, `--where` and `--compare` all share."""
    if key in record.record_attrs:
        return record.record_attrs[key]
    return record.resource_attrs.get(key)


def _kensai_attrs(record: LogRecord) -> dict[str, Any]:
    """Every `kensai.*` attribute this record carries, resolved via `_attr` — record first,
    resource second — over the union of keys either side names."""
    keys = {k for k in record.record_attrs if k.startswith("kensai.")}
    keys |= {k for k in record.resource_attrs if k.startswith("kensai.")}
    return {key: _attr(record, key) for key in keys}


def _where_matches(record: LogRecord, where: tuple[tuple[str, str], ...]) -> bool:
    """A record lacking `key` never matches — `str(None)` is `"None"`, and `--where KEY=None` must
    not select every record that carries no such key."""
    return all(
        (actual := _attr(record, key)) is not None and str(actual) == value for key, value in where
    )


def _summed_field(records: tuple[LogRecord, ...], field: str) -> int | float:
    """`field` summed across `records`' own attributes via `as_number` — the one summation
    `agent_rows` and Task 5's `_compare_group` both perform over the same four token classes,
    `cost_usd` and `duration_ms`, on two different groupings of the same records."""
    return sum(as_number(r.record_attrs.get(field)) for r in records)


def api_request_records(
    records: tuple[LogRecord, ...], where: tuple[tuple[str, str], ...] = ()
) -> tuple[LogRecord, ...]:
    """Every `api_request` record in `records`, `--where`-filtered before anything groups
    them — Task 5's `--compare` filters through this same function, on the same rule."""
    return tuple(
        r
        for r in records
        if r.record_attrs.get("event.name") == EVENT_API_REQUEST and _where_matches(r, where)
    )


@dataclass(frozen=True)
class AgentRow:
    """One agent's spend, folded from every `api_request` record sharing its key — `session.id`,
    `workflow.run_id`, `query_source` and `agent.name`, further split (never merged) when the
    group's records disagree on a `kensai.*` value. The four token classes, `cost_usd` and
    `duration_ms` are sums; `models` is the distinct set of models seen, sorted."""

    session_id: str | None
    workflow_run_id: str | None
    query_source: str | None
    agent_name: str | None
    kensai: dict[str, Any]
    models: tuple[str, ...]
    request_count: int
    input_tokens: int | float
    output_tokens: int | float
    cache_read_tokens: int | float
    cache_creation_tokens: int | float
    cost_usd: int | float
    duration_ms: int | float


def agent_rows(
    records: tuple[LogRecord, ...], where: tuple[tuple[str, str], ...] = ()
) -> tuple[AgentRow, ...]:
    """One `AgentRow` per distinct (`session.id`, `workflow.run_id`, `query_source`,
    `agent.name`, kensai-signature) key among `records`'s `api_request` records. The kensai
    signature — the sorted `(key, value)` pairs `_kensai_attrs` reads — is part of the grouping
    key precisely so two records that would otherwise share a row, but disagree on a `kensai.*`
    value, land on two rows instead of one merged (and therefore wrong) row."""
    groups: dict[tuple, list[LogRecord]] = {}
    for record in api_request_records(records, where):
        kensai_items = tuple(sorted(_kensai_attrs(record).items()))
        key = (
            record.record_attrs.get("session.id"),
            record.record_attrs.get("workflow.run_id"),
            record.record_attrs.get("query_source"),
            record.record_attrs.get("agent.name"),
            kensai_items,
        )
        groups.setdefault(key, []).append(record)

    rows = []
    for key, group in groups.items():
        session_id, workflow_run_id, query_source, agent_name, kensai_items = key
        seen_models = {
            g.record_attrs.get("model") for g in group if g.record_attrs.get("model") is not None
        }
        models = tuple(sorted(seen_models))
        rows.append(
            AgentRow(
                session_id=session_id,
                workflow_run_id=workflow_run_id,
                query_source=query_source,
                agent_name=agent_name,
                kensai=dict(kensai_items),
                models=models,
                request_count=len(group),
                input_tokens=_summed_field(tuple(group), "input_tokens"),
                output_tokens=_summed_field(tuple(group), "output_tokens"),
                cache_read_tokens=_summed_field(tuple(group), "cache_read_tokens"),
                cache_creation_tokens=_summed_field(tuple(group), "cache_creation_tokens"),
                cost_usd=_summed_field(tuple(group), "cost_usd"),
                duration_ms=_summed_field(tuple(group), "duration_ms"),
            )
        )
    return tuple(rows)


# ── Task 3 — the metrics check ──────────────────────────────────────────────

METRIC_COST_USAGE = "claude_code.cost.usage"


@dataclass(frozen=True)
class MetricPoint:
    """One `claude_code.cost.usage` datapoint — its attributes, flattened, and its `asDouble` /
    `asInt` value, decoded through `as_number` the same as any other numeric field. A datapoint
    of any other metric name is never turned into one of these — `read_metric_lines` filters
    before this type is ever built."""

    attrs: dict[str, Any]
    value: float


def read_metric_lines(lines: list[str] | None) -> tuple[MetricPoint, ...]:
    """Parse `metrics.jsonl`'s lines into `claude_code.cost.usage` datapoints only — every other
    metric name is walked past. `lines` of `None` (the file does not exist) reads as no points,
    the same "nothing to report" answer a malformed line gives. Each export is one delta reading
    (`aggregationTemporality: 1`); summing across every export, never reading only the last one,
    is `metrics_check`'s job — this function only decodes what is there."""
    if lines is None:
        return ()
    points: list[MetricPoint] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        try:
            outer = json.loads(line)
        except (ValueError, TypeError):
            continue
        if not isinstance(outer, dict):
            continue
        body = outer.get("body")
        if not isinstance(body, dict):
            continue
        for resource_metric in body.get("resourceMetrics") or []:
            if not isinstance(resource_metric, dict):
                continue
            for scope_metric in resource_metric.get("scopeMetrics") or []:
                if not isinstance(scope_metric, dict):
                    continue
                for metric in scope_metric.get("metrics") or []:
                    if not isinstance(metric, dict) or metric.get("name") != METRIC_COST_USAGE:
                        continue
                    for point in (metric.get("sum") or {}).get("dataPoints") or []:
                        if not isinstance(point, dict):
                            continue
                        raw_value = point.get("asDouble")
                        if raw_value is None:
                            raw_value = point.get("asInt")
                        points.append(
                            MetricPoint(
                                attrs=_flatten_attributes(point.get("attributes")),
                                value=float(as_number(raw_value)),
                            )
                        )
    return tuple(points)


@dataclass(frozen=True)
class SessionMetricsCheck:
    """One session's cost held against the vendor's own metric — the summed `api_request`
    `cost_usd` from the log stream, and the summed `claude_code.cost.usage` datapoints from the
    metrics stream. `metric_cost_usd` and `within_tolerance` are both `None` for a session with
    requests but no metric export at all — a different fact from a metric that agrees."""

    session_id: str
    log_cost_usd: float
    metric_cost_usd: float | None
    within_tolerance: bool | None


def metrics_check(
    rows: tuple[AgentRow, ...],
    metric_points: tuple[MetricPoint, ...],
    tolerance: float = 0.01,
) -> tuple[SessionMetricsCheck, ...]:
    """Every session named by `rows`, held against `metric_points` summed per `session.id` —
    across every export the points came from, never only the last. A session absent from
    `metric_points` entirely reports `metric_cost_usd=None`; one present is flagged when the two
    figures differ by more than `tolerance` (relative to the log figure, or to the metric figure
    when the log figure is exactly zero)."""
    log_cost_by_session: dict[str, float] = {}
    for row in rows:
        if row.session_id is None:
            continue
        prior = log_cost_by_session.get(row.session_id, 0.0)
        log_cost_by_session[row.session_id] = prior + row.cost_usd

    metric_cost_by_session: dict[str, float] = {}
    for point in metric_points:
        session_id = point.attrs.get("session.id")
        if session_id is None:
            continue
        prior = metric_cost_by_session.get(session_id, 0.0)
        metric_cost_by_session[session_id] = prior + point.value

    checks = []
    for session_id in sorted(log_cost_by_session):
        log_cost = log_cost_by_session[session_id]
        metric_cost = metric_cost_by_session.get(session_id)
        if metric_cost is None:
            checks.append(SessionMetricsCheck(session_id, log_cost, None, None))
            continue
        denominator = log_cost if log_cost else metric_cost
        relative_gap = abs(metric_cost - log_cost) / denominator if denominator else 0.0
        within = relative_gap <= tolerance
        checks.append(SessionMetricsCheck(session_id, log_cost, metric_cost, within))
    return tuple(checks)


# ── Task 4 — the Agent-tool agent count ─────────────────────────────────────

SUBAGENT_COVERAGE_NOTE = (
    "subagent_completed counts Agent-tool agents only — a Workflow step's own requests "
    '(query_source "agent:builtin:workflow-subagent") emit no subagent_completed record, so '
    "this count does not cover them."
)


def subagent_records(records: tuple[LogRecord, ...]) -> tuple[LogRecord, ...]:
    """Every `subagent_completed` record in `records`."""
    return tuple(r for r in records if r.record_attrs.get("event.name") == EVENT_SUBAGENT_COMPLETED)


@dataclass(frozen=True)
class SubagentRow:
    """One `(session.id, agent_type)`'s Agent-tool agent count — `duration_ms` and
    `total_tool_uses` summed across every `subagent_completed` record sharing that key.
    **Carries no `total_tokens`** — that figure is a single lumped total on the source record,
    the one shape this reader forbids beside the four token classes it keeps apart everywhere
    else, so it is never read onto this row at all."""

    session_id: str | None
    agent_type: str | None
    count: int
    duration_ms: int | float
    total_tool_uses: int | float


def subagent_rows(records: tuple[LogRecord, ...]) -> tuple[SubagentRow, ...]:
    """One `SubagentRow` per distinct `(session.id, agent_type)` among `records`'s
    `subagent_completed` records, sorted for a deterministic reading. See `SUBAGENT_COVERAGE_NOTE`
    for what this count does not reach."""
    groups: dict[tuple, list[LogRecord]] = {}
    for record in subagent_records(records):
        key = (record.record_attrs.get("session.id"), record.record_attrs.get("agent_type"))
        groups.setdefault(key, []).append(record)

    rows = [
        SubagentRow(
            session_id=session_id,
            agent_type=agent_type,
            count=len(group),
            duration_ms=_summed_field(tuple(group), "duration_ms"),
            total_tool_uses=_summed_field(tuple(group), "total_tool_uses"),
        )
        for (session_id, agent_type), group in groups.items()
    ]
    return tuple(sorted(rows, key=lambda r: (r.session_id or "", r.agent_type or "")))


# ── Task 5 — `--compare ATTR A B` ────────────────────────────────────────────


@dataclass(frozen=True)
class CompareTotals:
    """The four token classes, `cost_usd` and `duration_ms`, summed over one `--compare` group's
    `api_request` records — the same figures `AgentRow` sums, over a different grouping."""

    input_tokens: int | float = 0
    output_tokens: int | float = 0
    cache_read_tokens: int | float = 0
    cache_creation_tokens: int | float = 0
    cost_usd: int | float = 0.0
    duration_ms: int | float = 0


@dataclass(frozen=True)
class CompareGroup:
    """One side of a `--compare` — the attribute value it matched, how many runs it covers, its
    summed totals, and each of those totals' mean per run. `mean_cost_per_run` is
    `mean_per_run.cost_usd`, kept by name because the `B − A` and `B / A` figures are taken on it."""

    value: str
    run_count: int
    totals: CompareTotals
    mean_per_run: CompareTotals
    mean_cost_per_run: float


@dataclass(frozen=True)
class CompareResult:
    """`compare`'s whole answer. `a`/`b` are `None` exactly when that value matched no records —
    "no runs," never a zero-filled group standing in for absence. `diff` and `ratio` are `None`
    together whenever either side is empty; `ratio` is `None` alone when `a`'s mean is zero,
    since dividing by it would be the exact zero-division this reader refuses."""

    attr: str
    a_value: str
    b_value: str
    a: CompareGroup | None
    b: CompareGroup | None
    diff: float | None
    ratio: float | None


def _run_key(record: LogRecord) -> str:
    """A run's identity for the per-run mean — one `kensai.run_id` (record first, resource
    second), or one `session.id` when the record carries none."""
    run_id = _attr(record, "kensai.run_id")
    if run_id is not None:
        return str(run_id)
    return str(record.record_attrs.get("session.id"))


def _compare_group(records: tuple[LogRecord, ...], attr: str, value: str) -> CompareGroup | None:
    matching = tuple(r for r in records if str(_attr(r, attr)) == value)
    if not matching:
        return None
    run_count = len({_run_key(r) for r in matching})
    totals = CompareTotals(
        input_tokens=_summed_field(matching, "input_tokens"),
        output_tokens=_summed_field(matching, "output_tokens"),
        cache_read_tokens=_summed_field(matching, "cache_read_tokens"),
        cache_creation_tokens=_summed_field(matching, "cache_creation_tokens"),
        cost_usd=_summed_field(matching, "cost_usd"),
        duration_ms=_summed_field(matching, "duration_ms"),
    )
    mean_per_run = CompareTotals(
        **{
            figure.name: (getattr(totals, figure.name) / run_count if run_count else 0.0)
            for figure in fields(CompareTotals)
        }
    )
    return CompareGroup(
        value=value,
        run_count=run_count,
        totals=totals,
        mean_per_run=mean_per_run,
        mean_cost_per_run=mean_per_run.cost_usd,
    )


def compare(
    records: tuple[LogRecord, ...],
    attr: str,
    a_value: str,
    b_value: str,
    where: tuple[tuple[str, str], ...] = (),
) -> CompareResult:
    """Group `api_request` records — `--where`-filtered first, the same rule `agent_rows` uses —
    by `attr`'s value (record first, resource second), keeping only the `a_value` and `b_value`
    groups, and difference their per-run mean `cost_usd`."""
    filtered = api_request_records(records, where)
    a = _compare_group(filtered, attr, a_value)
    b = _compare_group(filtered, attr, b_value)
    diff = None
    ratio = None
    if a is not None and b is not None:
        diff = b.mean_cost_per_run - a.mean_cost_per_run
        if a.mean_cost_per_run:
            ratio = b.mean_cost_per_run / a.mean_cost_per_run
    return CompareResult(
        attr=attr, a_value=a_value, b_value=b_value, a=a, b=b, diff=diff, ratio=ratio
    )


# ── Task 6 — the command ─────────────────────────────────────────────────────


class Files:
    """Every filesystem touch this reader makes: reading a stream file's lines whole, or
    reporting `None` when it does not exist."""

    def read_lines(self, path: Path) -> list[str] | None:
        try:
            return path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return None


@dataclass(frozen=True)
class Reader:
    """The reader's whole environment: the one port it reaches the world through, plus the
    telemetry directory resolved to a concrete `Path` — the one environment reach `build_reader`
    performs itself, per `flow_usage.py`'s own `Reader`/`build_reader` shape."""

    files: Files
    directory: Path


def build_reader(directory: Path | None = None) -> Reader:
    """Wire the real port. The only place `Files()` is constructed, and the only place the
    default telemetry directory (`~/.kensaiapp/telemetry`) is named — never an argparse default,
    never resolved again inside `main()`'s own body."""
    default_directory = Path.home() / ".kensaiapp" / "telemetry"
    return Reader(
        files=Files(),
        directory=directory if directory is not None else default_directory,
    )


def _parse_where(pairs: list[str] | None) -> tuple[tuple[str, str], ...]:
    parsed = []
    for pair in pairs or []:
        key, sep, value = pair.partition("=")
        if not sep:
            raise SystemExit(f"error: --where expects KEY=VALUE, got {pair!r}")
        parsed.append((key, value))
    return tuple(parsed)


def _row_label(row: AgentRow) -> str:
    return (
        f"session={row.session_id} workflow_run_id={row.workflow_run_id} "
        f"query_source={row.query_source} agent={row.agent_name}"
    )


def render(
    rows: tuple[AgentRow, ...],
    sub_rows: tuple[SubagentRow, ...],
    checks: tuple[SessionMetricsCheck, ...] | None,
    skipped_lines: int,
    compare_result: CompareResult | None,
) -> str:
    """The human table — agent rows led by `cost_usd`, highest first, with the total stated;
    the Agent-tool agent count, always carrying `SUBAGENT_COVERAGE_NOTE`; the metrics
    cross-check, or a stated reason it did not run; and, when asked for, the `--compare` block.
    Every section states its own absence in words rather than rendering an empty table."""
    ordered = tuple(sorted(rows, key=lambda r: r.cost_usd, reverse=True))
    total_cost = sum(r.cost_usd for r in ordered)

    lines: list[str] = [f"{len(ordered)} agent row(s), {skipped_lines} unreadable line(s) skipped."]
    for row in ordered:
        lines.append(
            f"  {_row_label(row)}  requests={row.request_count}  "
            f"models={','.join(row.models) or '(none)'}  cost_usd={row.cost_usd:.6f}"
        )
        lines.append(
            f"    input={row.input_tokens} output={row.output_tokens} "
            f"cache_read={row.cache_read_tokens} cache_creation={row.cache_creation_tokens} "
            f"duration_ms={row.duration_ms}"
        )
        if row.kensai:
            kensai_text = ", ".join(f"{k}={v}" for k, v in sorted(row.kensai.items()))
            lines.append(f"    kensai: {kensai_text}")
    lines.append(f"Total cost_usd: {total_cost:.6f}")
    lines.append("")

    lines.append(SUBAGENT_COVERAGE_NOTE)
    if not sub_rows:
        lines.append("No subagent_completed records read.")
    for sub_row in sub_rows:
        lines.append(
            f"  session={sub_row.session_id} agent_type={sub_row.agent_type} "
            f"count={sub_row.count} duration_ms={sub_row.duration_ms} "
            f"total_tool_uses={sub_row.total_tool_uses}"
        )
    lines.append("")

    if checks is None:
        lines.append("No metrics.jsonl found — metrics cross-check skipped.")
    else:
        lines.append("Metrics cross-check (claude_code.cost.usage vs summed cost_usd):")
        if not checks:
            lines.append("  No sessions to check.")
        for check in checks:
            if check.metric_cost_usd is None:
                lines.append(
                    f"  session={check.session_id}  log_cost_usd={check.log_cost_usd:.6f}  "
                    "no metric export"
                )
            else:
                flag = "" if check.within_tolerance else "  MISMATCH >1%"
                lines.append(
                    f"  session={check.session_id}  log_cost_usd={check.log_cost_usd:.6f}  "
                    f"metric_cost_usd={check.metric_cost_usd:.6f}{flag}"
                )
    lines.append("")

    if compare_result is not None:
        lines.extend(_render_compare(compare_result))

    return "\n".join(lines).rstrip() + "\n"


def _compare_figures_text(figures: CompareTotals) -> str:
    """The four token classes, `cost_usd` and `duration_ms` on one line — a summed count prints
    as the integer it is, a per-run mean to two places, and cost to six, as everywhere else."""

    def count(value: int | float) -> str:
        return str(value) if isinstance(value, int) else f"{value:.2f}"

    return (
        f"input={count(figures.input_tokens)} output={count(figures.output_tokens)} "
        f"cache_read={count(figures.cache_read_tokens)} "
        f"cache_creation={count(figures.cache_creation_tokens)} "
        f"cost_usd={figures.cost_usd:.6f} duration_ms={count(figures.duration_ms)}"
    )


def _render_compare(result: CompareResult) -> list[str]:
    lines = [f"--compare {result.attr} {result.a_value} {result.b_value}:"]
    for group, label in ((result.a, result.a_value), (result.b, result.b_value)):
        if group is None:
            lines.append(f"  {label}: no runs")
        else:
            lines.append(
                f"  {label}: runs={group.run_count}  "
                f"mean_cost_per_run={group.mean_cost_per_run:.6f}  "
                f"total_cost_usd={group.totals.cost_usd:.6f}"
            )
            lines.append(f"    totals:  {_compare_figures_text(group.totals)}")
            lines.append(f"    per run: {_compare_figures_text(group.mean_per_run)}")
    if result.diff is not None:
        lines.append(f"  {result.b_value} - {result.a_value} = {result.diff:.6f}")
        if result.ratio is not None:
            lines.append(f"  {result.b_value} / {result.a_value} = {result.ratio:.6f}")
        else:
            lines.append(f"  {result.b_value} / {result.a_value}: ratio undefined (zero mean)")
    return lines


def _compare_group_json(group: CompareGroup | None) -> dict[str, Any] | None:
    """One `--compare` side keyed for `--json` — the figures the table prints, or `None` for a
    value that matched no runs."""
    if group is None:
        return None
    return {
        "run_count": group.run_count,
        "mean_cost_per_run": group.mean_cost_per_run,
        "total_cost_usd": group.totals.cost_usd,
        "totals": asdict(group.totals),
        "mean_per_run": asdict(group.mean_per_run),
    }


def render_json(
    rows: tuple[AgentRow, ...],
    sub_rows: tuple[SubagentRow, ...],
    checks: tuple[SessionMetricsCheck, ...] | None,
    skipped_lines: int,
    compare_result: CompareResult | None,
) -> str:
    """The machine rows — the same figures `render` prints, keyed rather than columned."""
    ordered = tuple(sorted(rows, key=lambda r: r.cost_usd, reverse=True))
    payload: dict[str, Any] = {
        "skipped_lines": skipped_lines,
        "total_cost_usd": sum(r.cost_usd for r in ordered),
        "rows": [
            {
                "session_id": row.session_id,
                "workflow_run_id": row.workflow_run_id,
                "query_source": row.query_source,
                "agent_name": row.agent_name,
                "kensai": row.kensai,
                "models": list(row.models),
                "request_count": row.request_count,
                "input_tokens": row.input_tokens,
                "output_tokens": row.output_tokens,
                "cache_read_tokens": row.cache_read_tokens,
                "cache_creation_tokens": row.cache_creation_tokens,
                "cost_usd": row.cost_usd,
                "duration_ms": row.duration_ms,
            }
            for row in ordered
        ],
        "subagent_coverage_note": SUBAGENT_COVERAGE_NOTE,
        "subagent_rows": [
            {
                "session_id": r.session_id,
                "agent_type": r.agent_type,
                "count": r.count,
                "duration_ms": r.duration_ms,
                "total_tool_uses": r.total_tool_uses,
            }
            for r in sub_rows
        ],
        "metrics_check": None
        if checks is None
        else [
            {
                "session_id": c.session_id,
                "log_cost_usd": c.log_cost_usd,
                "metric_cost_usd": c.metric_cost_usd,
                "within_tolerance": c.within_tolerance,
            }
            for c in checks
        ],
    }
    if compare_result is not None:
        payload["compare"] = {
            "attr": compare_result.attr,
            "a_value": compare_result.a_value,
            "b_value": compare_result.b_value,
            "a": _compare_group_json(compare_result.a),
            "b": _compare_group_json(compare_result.b),
            "diff": compare_result.diff,
            "ratio": compare_result.ratio,
        }
    return json.dumps(payload, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent_usage.py",
        description=(
            "What each agent spent, one row per agent, off the OTLP log stream — plus a "
            "metrics cross-check, the Agent-tool agent count, and a --compare mode. No price "
            "model: cost is the vendor's own cost_usd."
        ),
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="the telemetry directory holding logs.jsonl / metrics.jsonl "
        "(default: ~/.kensaiapp/telemetry)",
    )
    parser.add_argument(
        "--where",
        action="append",
        default=None,
        metavar="KEY=VALUE",
        help="keep only records whose attribute KEY equals VALUE (repeatable)",
    )
    parser.add_argument(
        "--compare",
        nargs=3,
        default=None,
        metavar=("ATTR", "A", "B"),
        help="difference two values of ATTR's per-run mean cost",
    )
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    args = parser.parse_args(argv)

    reader = build_reader(args.dir)
    logs_path = reader.directory / "logs.jsonl"
    metrics_path = reader.directory / "metrics.jsonl"

    log_lines = reader.files.read_lines(logs_path)
    if log_lines is None:
        print(f"No stream at {reader.directory} — no {logs_path.name} there.")
        return 0

    parsed = read_log_lines(log_lines)
    where = _parse_where(args.where)
    rows = agent_rows(parsed.records, where)
    sub_rows = subagent_rows(parsed.records)

    metric_lines = reader.files.read_lines(metrics_path)
    if metric_lines is None:
        checks: tuple[SessionMetricsCheck, ...] | None = None
    else:
        # The metric is a whole session's, so it is held against the session's whole log cost —
        # never the `--where`-narrowed rows, which would report a false gap for every session a
        # filter narrower than a session touches. `--where` still decides which sessions are shown.
        shown = {row.session_id for row in rows}
        checks = tuple(
            check
            for check in metrics_check(agent_rows(parsed.records), read_metric_lines(metric_lines))
            if check.session_id in shown
        )

    compare_result = None
    if args.compare:
        attr, a_value, b_value = args.compare
        compare_result = compare(parsed.records, attr, a_value, b_value, where)

    if args.json:
        print(render_json(rows, sub_rows, checks, parsed.skipped, compare_result))
    else:
        print(render(rows, sub_rows, checks, parsed.skipped, compare_result), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
