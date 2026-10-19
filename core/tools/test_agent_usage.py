"""Tests for `agent_usage.py` — one row per agent, off the OTLP telemetry stream.

**The captured fixture below is a real payload, not invented.** `CAPTURED_LOGS_LINE` is cut from
`~/.kensaiapp/telemetry/logs.jsonl` on this machine, read 2026-09-11:

- Its `api_request` and `subagent_completed` records are line 398, counted from 1 (`received_at`
  `2026-09-10T16:03:12.507333+00:00`), session `41a62ae0-6d62-47b0-a0b5-3614fe3411d6` — one export
  that happened to carry both kinds for the same agent. The line's other records
  (`user_prompt`, `hook_execution_start`, `hook_execution_complete`, `assistant_response`) are
  dropped; neither carries spend or agent identity, and `assistant_response` and `user_prompt`
  carry redacted prompt/response text this station never keeps.
- Its one `hook_registered` record is spliced in from line 12 (`received_at`
  `2026-09-10T07:30:04.379949+00:00`), session `4d893290-19b6-4f47-b6d0-67bd73f315d3` — chosen
  because line 398 carries no `hook_registered` of its own, and this one carries `kensai.arm` /
  `kensai.run_id` at the record level, real values for the same attributes Task 2 reads. The plan
  asks for one payload line; none holds all three kinds (0 of 2,020 lines, counted 2026-09-11), so
  two real lines are the nearest a real capture can come.
- `user.*` and `organization.id` are stripped off all three records, per the guardrail. Every
  other attribute, and its exact OTLP envelope (`stringValue` / `intValue` / `doubleValue` /
  `boolValue`), is what the receiver actually stored — including `safe_mode`, which arrived as
  the *string* `"false"`, not a bool.

`_attr(key, value)` below is a compaction, not an invention: it picks the OTLP envelope key by
the Python type of `value`, and every value it is called with is the real one the payload
carried — the helper only saves re-typing `{"key": ..., "value": {"stringValue": ...}}` by hand.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

import agent_usage


# ── The real capture (see module docstring) ────────────────────────────────


def _attr(key: str, value) -> dict:
    if isinstance(value, bool):
        kind = "boolValue"
    elif isinstance(value, int):
        kind = "intValue"
    elif isinstance(value, float):
        kind = "doubleValue"
    else:
        kind = "stringValue"
    return {"key": key, "value": {kind: value}}


_API_REQUEST_RECORD = {
    "timeUnixNano": "1789056188302000000",
    "observedTimeUnixNano": "1789056188302000000",
    "body": {"stringValue": "claude_code.api_request"},
    "attributes": [
        _attr("session.id", "41a62ae0-6d62-47b0-a0b5-3614fe3411d6"),
        _attr("terminal.type", "Apple_Terminal"),
        _attr("event.name", "api_request"),
        _attr("event.timestamp", "2026-09-10T16:03:08.302Z"),
        _attr("event.sequence", 547),
        _attr("prompt.id", "012a824f-5de0-4363-a5a6-07e69167cc54"),
        _attr("model", "claude-opus-5"),
        _attr("input_tokens", 32),
        _attr("output_tokens", 2315),
        _attr("cache_read_tokens", 295809),
        _attr("cache_creation_tokens", 1684),
        _attr("cost_usd", 0.2164645),
        _attr("cost_usd_micros", 216465),
        _attr("duration_ms", 25645),
        _attr("request_id", "req_011Cev3Jqf1hwhuxPxZ7DJUU"),
        _attr("client_request_id", "1b531883-efae-4e87-ba97-6b30b19fdc41"),
        _attr("speed", "normal"),
        _attr("query_source", "agent:custom"),
        _attr("effort", "high"),
        _attr("agent.name", "custom"),
    ],
    "droppedAttributesCount": 0,
}

_SUBAGENT_COMPLETED_RECORD = {
    "timeUnixNano": "1789056188304000000",
    "observedTimeUnixNano": "1789056188304000000",
    "body": {"stringValue": "claude_code.subagent_completed"},
    "attributes": [
        _attr("session.id", "41a62ae0-6d62-47b0-a0b5-3614fe3411d6"),
        _attr("terminal.type", "Apple_Terminal"),
        _attr("event.name", "subagent_completed"),
        _attr("event.timestamp", "2026-09-10T16:03:08.304Z"),
        _attr("event.sequence", 549),
        _attr("prompt.id", "012a824f-5de0-4363-a5a6-07e69167cc54"),
        _attr("agent_type", "custom"),
        _attr("agent.source", "projectSettings"),
        _attr("is_built_in", False),
        _attr("is_async", True),
        _attr("total_tokens", 299840),
        _attr("total_tool_uses", 77),
        _attr("duration_ms", 278394),
        _attr("model", "claude-opus-5[1m]"),
        _attr("final_model", "claude-opus-5[1m]"),
        _attr("model_swapped", False),
    ],
    "droppedAttributesCount": 0,
}

_HOOK_REGISTERED_RECORD = {
    "timeUnixNano": "1789025401255000000",
    "observedTimeUnixNano": "1789025401255000000",
    "body": {"stringValue": "claude_code.hook_registered"},
    "attributes": [
        _attr("kensai.arm", "fg-control-093000"),
        _attr("kensai.run_id", "ab3b5267-3f21-404b-9015-3fa7ddcf74f1"),
        _attr("session.id", "4d893290-19b6-4f47-b6d0-67bd73f315d3"),
        _attr("terminal.type", "Apple_Terminal"),
        _attr("event.name", "hook_registered"),
        _attr("event.timestamp", "2026-09-10T07:30:01.255Z"),
        _attr("event.sequence", 0),
        _attr("hook_event", "PreToolUse"),
        _attr("hook_type", "command"),
        _attr("hook_source", "userSettings"),
        _attr("safe_mode", "false"),  # arrived as a string, not a bool — kept faithfully
    ],
    "droppedAttributesCount": 0,
}

CAPTURED_LOGS_LINE = {
    "signal": "logs",
    "received_at": "2026-09-10T16:03:12.507333+00:00",
    "body": {
        "resourceLogs": [
            {
                "resource": {
                    "attributes": [
                        _attr("host.arch", "arm64"),
                        _attr("os.type", "darwin"),
                        _attr("os.version", "25.6.0"),
                        _attr("service.name", "claude-code"),
                        _attr("service.version", "2.1.267"),
                    ],
                    "droppedAttributesCount": 0,
                },
                "scopeLogs": [
                    {
                        "scope": {
                            "name": "com.anthropic.claude_code.events",
                            "version": "2.1.267",
                        },
                        "logRecords": [
                            _API_REQUEST_RECORD,
                            _SUBAGENT_COMPLETED_RECORD,
                            _HOOK_REGISTERED_RECORD,
                        ],
                    }
                ],
            }
        ]
    },
}


# ── Task 1 — a value is read whatever envelope it arrives in ───────────────


class TestDecodeValue:
    def test_reads_a_string_value(self):
        assert agent_usage.decode_value({"stringValue": "agent:custom"}) == "agent:custom"

    def test_reads_an_int_value_arriving_as_a_json_number(self):
        assert agent_usage.decode_value({"intValue": 43}) == 43

    def test_reads_an_int_value_arriving_as_a_json_string_the_same_as_a_number(self):
        assert agent_usage.decode_value({"intValue": "43"}) == agent_usage.decode_value(
            {"intValue": 43}
        )

    def test_reads_a_double_value(self):
        assert agent_usage.decode_value({"doubleValue": 0.0503237}) == 0.0503237

    def test_reads_a_bool_value(self):
        assert agent_usage.decode_value({"boolValue": True}) is True

    def test_an_envelope_with_none_of_the_four_keys_decodes_to_none(self):
        assert agent_usage.decode_value({}) is None

    def test_a_non_dict_value_decodes_to_none_rather_than_raising(self):
        assert agent_usage.decode_value(None) is None


class TestAsNumber:
    def test_an_int_passes_through(self):
        assert agent_usage.as_number(43) == 43

    def test_a_float_passes_through(self):
        assert agent_usage.as_number(0.5) == 0.5

    def test_a_numeric_string_value_reads_as_that_number_when_summed(self):
        assert agent_usage.as_number("1") == 1
        assert agent_usage.as_number("2.5") == 2.5

    def test_a_non_numeric_string_reads_as_zero_rather_than_raising(self):
        assert agent_usage.as_number("normal") == 0

    def test_none_reads_as_zero(self):
        assert agent_usage.as_number(None) == 0


class TestReadLogLines:
    def test_reads_the_real_capture_into_three_records(self):
        result = agent_usage.read_log_lines([json.dumps(CAPTURED_LOGS_LINE)])
        assert len(result.records) == 3
        assert result.skipped == 0

    def test_the_api_request_record_decodes_its_typed_fields_correctly(self):
        result = agent_usage.read_log_lines([json.dumps(CAPTURED_LOGS_LINE)])
        api_request = next(
            r for r in result.records if r.record_attrs.get("event.name") == "api_request"
        )
        assert api_request.record_attrs["cost_usd"] == 0.2164645
        assert api_request.record_attrs["input_tokens"] == 32
        assert api_request.record_attrs["session.id"] == "41a62ae0-6d62-47b0-a0b5-3614fe3411d6"

    def test_the_resource_attributes_are_carried_on_every_record_from_that_body(self):
        result = agent_usage.read_log_lines([json.dumps(CAPTURED_LOGS_LINE)])
        for record in result.records:
            assert record.resource_attrs["service.name"] == "claude-code"

    def test_a_line_that_is_not_json_is_skipped_and_counted(self):
        result = agent_usage.read_log_lines(["not json at all {"])
        assert result.records == ()
        assert result.skipped == 1

    def test_a_line_whose_outer_object_has_no_body_is_skipped_and_counted(self):
        result = agent_usage.read_log_lines([json.dumps({"signal": "logs"})])
        assert result.records == ()
        assert result.skipped == 1

    def test_a_line_whose_body_is_an_empty_object_is_skipped_and_counted(self):
        result = agent_usage.read_log_lines([json.dumps({"signal": "logs", "body": {}})])
        assert result.records == ()
        assert result.skipped == 1

    def test_a_blank_line_is_neither_a_record_nor_a_skip(self):
        result = agent_usage.read_log_lines(["", "   "])
        assert result.records == ()
        assert result.skipped == 0

    def test_one_bad_line_never_stops_the_read_of_the_rest(self):
        result = agent_usage.read_log_lines(["garbled", json.dumps(CAPTURED_LOGS_LINE)])
        assert len(result.records) == 3
        assert result.skipped == 1

    def test_an_empty_list_of_lines_reads_as_no_records_and_no_skips(self):
        result = agent_usage.read_log_lines([])
        assert result.records == ()
        assert result.skipped == 0


# ── Task 2 — one row per agent ──────────────────────────────────────────────


def _record(record_attrs: dict, resource_attrs: dict | None = None) -> agent_usage.LogRecord:
    return agent_usage.LogRecord(record_attrs=record_attrs, resource_attrs=resource_attrs or {})


def _api_request(**overrides) -> agent_usage.LogRecord:
    attrs = {
        "event.name": "api_request",
        "session.id": "sid-1",
        "query_source": "agent:custom",
        "agent.name": "custom",
        "model": "claude-opus-5",
        "input_tokens": 10,
        "output_tokens": 20,
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
        "cost_usd": 0.1,
        "duration_ms": 100,
    }
    attrs.update(overrides)
    return _record(attrs)


class TestAgentRows:
    def test_only_api_request_records_become_rows(self):
        result = agent_usage.read_log_lines([json.dumps(CAPTURED_LOGS_LINE)])
        rows = agent_usage.agent_rows(result.records)
        assert len(rows) == 1
        assert rows[0].session_id == "41a62ae0-6d62-47b0-a0b5-3614fe3411d6"

    def test_the_fixtures_hook_registered_record_changes_no_figure(self):
        result = agent_usage.read_log_lines([json.dumps(CAPTURED_LOGS_LINE)])
        rows = agent_usage.agent_rows(result.records)
        assert rows[0].cost_usd == pytest.approx(0.2164645)
        assert rows[0].request_count == 1

    def test_records_sharing_the_key_fold_into_one_row_summing_and_listing_models(self):
        records = (
            _api_request(model="claude-opus-5", input_tokens=10, cost_usd=0.1, duration_ms=100),
            _api_request(model="claude-haiku-4-5", input_tokens=5, cost_usd=0.05, duration_ms=50),
        )
        rows = agent_usage.agent_rows(records)
        assert len(rows) == 1
        row = rows[0]
        assert row.request_count == 2
        assert row.input_tokens == 15
        assert row.cost_usd == pytest.approx(0.15)
        assert row.duration_ms == 150
        assert row.models == ("claude-haiku-4-5", "claude-opus-5")

    def test_kensai_attrs_are_read_off_the_record_first_and_the_resource_second(self):
        record = _record(
            {
                "event.name": "api_request",
                "session.id": "sid-1",
                "query_source": "sdk",
                "kensai.arm": "record-arm",
                "cost_usd": 0.1,
            },
            resource_attrs={"kensai.arm": "resource-arm", "kensai.run_id": "rid-1"},
        )
        rows = agent_usage.agent_rows((record,))
        assert rows[0].kensai == {"kensai.arm": "record-arm", "kensai.run_id": "rid-1"}

    def test_a_row_whose_records_disagree_on_a_kensai_value_is_split_never_merged(self):
        records = (
            _api_request(**{"kensai.arm": "arm-a"}),
            _api_request(**{"kensai.arm": "arm-b"}),
        )
        # both share session.id/query_source/agent.name via _api_request's defaults
        rows = agent_usage.agent_rows(records)
        assert len(rows) == 2
        arms = {row.kensai.get("kensai.arm") for row in rows}
        assert arms == {"arm-a", "arm-b"}
        for row in rows:
            assert row.request_count == 1

    def test_where_filters_on_any_attribute_including_session_id(self):
        records = (
            _api_request(**{"session.id": "sid-1"}),
            _api_request(**{"session.id": "sid-2"}),
        )
        rows = agent_usage.agent_rows(records, where=(("session.id", "sid-1"),))
        assert len(rows) == 1
        assert rows[0].session_id == "sid-1"

    def test_where_filters_on_a_kensai_attribute(self):
        records = (
            _record(
                {"event.name": "api_request", "session.id": "sid-1", "kensai.arm": "keep"},
            ),
            _record(
                {"event.name": "api_request", "session.id": "sid-2", "kensai.arm": "drop"},
            ),
        )
        rows = agent_usage.agent_rows(records, where=(("kensai.arm", "keep"),))
        assert len(rows) == 1
        assert rows[0].session_id == "sid-1"

    def test_an_unseen_query_source_value_gets_a_row_like_any_other(self):
        records = (_api_request(query_source="a-brand-new-source"),)
        rows = agent_usage.agent_rows(records)
        assert len(rows) == 1
        assert rows[0].query_source == "a-brand-new-source"


# ── Task 3 — the metrics check ──────────────────────────────────────────────
#
# `_cost_datapoint` mirrors the real shape captured from `~/.kensaiapp/telemetry/metrics.jsonl`
# on 2026-09-11 — `claude_code.cost.usage`'s `sum.dataPoints[].asDouble`, `aggregationTemporality:
# 1` (delta) — e.g. session `cf05030e-112f-4665-89cb-3e15ec7dcf67` reported `asDouble: 0.0503237`
# for `query_source: "main"`. The values below are synthesized in that same real shape to drive
# the specific arithmetic this task's behaviours name (two exports summing, a session with no
# export, a >1% mismatch) — Task 1's "cut from one payload line" rule binds `logs.jsonl` only.


def _cost_metric(data_points: list[dict]) -> dict:
    return {
        "resourceMetrics": [
            {
                "scopeMetrics": [
                    {
                        "metrics": [
                            {
                                "name": "claude_code.cost.usage",
                                "unit": "USD",
                                "sum": {"aggregationTemporality": 1, "dataPoints": data_points},
                            }
                        ]
                    }
                ]
            }
        ]
    }


def _cost_datapoint(session_id: str, value: float) -> dict:
    return {
        "attributes": [_attr("session.id", session_id), _attr("query_source", "main")],
        "startTimeUnixNano": "1788989273064000000",
        "timeUnixNano": "1788989273225000000",
        "asDouble": value,
    }


def _metrics_line(body: dict) -> str:
    return json.dumps({"signal": "metrics", "received_at": "2026-09-11T00:00:00+00:00", "body": body})


class TestReadMetricLines:
    def test_reads_cost_usage_datapoints_carrying_session_id(self):
        line = _metrics_line(_cost_metric([_cost_datapoint("sid-1", 0.0503237)]))
        points = agent_usage.read_metric_lines([line])
        assert len(points) == 1
        assert points[0].attrs["session.id"] == "sid-1"
        assert points[0].value == pytest.approx(0.0503237)

    def test_datapoints_of_any_other_metric_name_are_ignored(self):
        other_metric = {
            "resourceMetrics": [
                {
                    "scopeMetrics": [
                        {
                            "metrics": [
                                {
                                    "name": "claude_code.token.usage",
                                    "unit": "tokens",
                                    "sum": {
                                        "aggregationTemporality": 1,
                                        "dataPoints": [_cost_datapoint("sid-1", 10)],
                                    },
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        points = agent_usage.read_metric_lines([_metrics_line(other_metric)])
        assert points == ()

    def test_a_missing_metrics_file_reads_as_no_points(self):
        assert agent_usage.read_metric_lines(None) == ()


class TestMetricsCheck:
    def _row(self, session_id: str, cost_usd: float) -> agent_usage.AgentRow:
        return agent_usage.AgentRow(
            session_id=session_id,
            workflow_run_id=None,
            query_source="main",
            agent_name=None,
            kensai={},
            models=("claude-opus-5",),
            request_count=1,
            input_tokens=0,
            output_tokens=0,
            cache_read_tokens=0,
            cache_creation_tokens=0,
            cost_usd=cost_usd,
            duration_ms=0,
        )

    def test_two_delta_exports_for_one_session_are_summed_never_reading_only_the_last(self):
        rows = (self._row("sid-1", 0.07),)
        points = agent_usage.read_metric_lines(
            [
                _metrics_line(_cost_metric([_cost_datapoint("sid-1", 0.05)])),
                _metrics_line(_cost_metric([_cost_datapoint("sid-1", 0.02)])),
            ]
        )
        checks = agent_usage.metrics_check(rows, points)
        assert len(checks) == 1
        assert checks[0].metric_cost_usd == pytest.approx(0.07)
        assert checks[0].within_tolerance is True

    def test_a_session_with_requests_and_no_metric_export_is_named_as_such(self):
        rows = (self._row("sid-no-export", 0.05),)
        checks = agent_usage.metrics_check(rows, ())
        assert len(checks) == 1
        assert checks[0].session_id == "sid-no-export"
        assert checks[0].metric_cost_usd is None
        assert checks[0].within_tolerance is None

    def test_a_greater_than_one_percent_difference_is_flagged(self):
        rows = (self._row("sid-1", 1.00),)
        points = agent_usage.read_metric_lines([_metrics_line(_cost_metric([_cost_datapoint("sid-1", 1.02)]))])
        checks = agent_usage.metrics_check(rows, points)
        assert checks[0].within_tolerance is False

    def test_a_one_percent_or_smaller_difference_is_not_flagged(self):
        rows = (self._row("sid-1", 1.00),)
        points = agent_usage.read_metric_lines([_metrics_line(_cost_metric([_cost_datapoint("sid-1", 1.005)]))])
        checks = agent_usage.metrics_check(rows, points)
        assert checks[0].within_tolerance is True


# ── Task 4 — the Agent-tool agent count ─────────────────────────────────────


def _subagent_completed(**overrides) -> agent_usage.LogRecord:
    attrs = {
        "event.name": "subagent_completed",
        "session.id": "sid-1",
        "agent_type": "custom",
        "duration_ms": 100,
        "total_tool_uses": 5,
        "total_tokens": 999,
    }
    attrs.update(overrides)
    return _record(attrs)


class TestSubagentRows:
    def test_the_real_captures_subagent_completed_record_becomes_one_row(self):
        result = agent_usage.read_log_lines([json.dumps(CAPTURED_LOGS_LINE)])
        rows = agent_usage.subagent_rows(result.records)
        assert len(rows) == 1
        row = rows[0]
        assert row.session_id == "41a62ae0-6d62-47b0-a0b5-3614fe3411d6"
        assert row.agent_type == "custom"
        assert row.count == 1
        assert row.duration_ms == 278394
        assert row.total_tool_uses == 77

    def test_api_request_and_hook_registered_records_produce_no_subagent_row(self):
        result = agent_usage.read_log_lines([json.dumps(CAPTURED_LOGS_LINE)])
        rows = agent_usage.subagent_rows(result.records)
        assert all(row.session_id == "41a62ae0-6d62-47b0-a0b5-3614fe3411d6" for row in rows)

    def test_records_sharing_session_id_and_agent_type_fold_into_one_row(self):
        records = (
            _subagent_completed(duration_ms=100, total_tool_uses=5),
            _subagent_completed(duration_ms=50, total_tool_uses=2),
        )
        rows = agent_usage.subagent_rows(records)
        assert len(rows) == 1
        assert rows[0].count == 2
        assert rows[0].duration_ms == 150
        assert rows[0].total_tool_uses == 7

    def test_different_agent_types_in_one_session_stay_separate_rows(self):
        records = (
            _subagent_completed(agent_type="custom"),
            _subagent_completed(agent_type="general-purpose"),
        )
        rows = agent_usage.subagent_rows(records)
        assert len(rows) == 2

    def test_total_tokens_is_not_a_field_on_the_row_the_lumped_shape_is_forbidden(self):
        field_names = {f.name for f in dataclasses.fields(agent_usage.SubagentRow)}
        assert "total_tokens" not in field_names

    def test_the_coverage_note_states_a_workflow_step_emits_none(self):
        assert "workflow" in agent_usage.SUBAGENT_COVERAGE_NOTE.lower()
        assert "agent-tool" in agent_usage.SUBAGENT_COVERAGE_NOTE.lower()


# ── Task 5 — `--compare ATTR A B` ────────────────────────────────────────────


class TestCompare:
    def test_rows_are_grouped_by_the_attribute_and_only_a_and_b_are_kept(self):
        records = (
            _api_request(**{"kensai.arm": "launch-skill-evals"}, cost_usd=0.10),
            _api_request(**{"kensai.arm": "product-sdd"}, cost_usd=0.20),
            _api_request(**{"kensai.arm": "unrelated-arm"}, cost_usd=99.0),
        )
        result = agent_usage.compare(records, "kensai.arm", "launch-skill-evals", "product-sdd")
        assert result.a.value == "launch-skill-evals"
        assert result.b.value == "product-sdd"
        assert result.a.totals.cost_usd == pytest.approx(0.10)
        assert result.b.totals.cost_usd == pytest.approx(0.20)

    def test_a_run_is_one_kensai_run_id_when_a_record_carries_one(self):
        records = (
            _api_request(**{"kensai.arm": "A", "kensai.run_id": "run-1"}, cost_usd=0.10),
            _api_request(**{"kensai.arm": "A", "kensai.run_id": "run-1"}, cost_usd=0.05),
            _api_request(**{"kensai.arm": "A", "kensai.run_id": "run-2"}, cost_usd=0.10),
        )
        result = agent_usage.compare(records, "kensai.arm", "A", "B")
        assert result.a.run_count == 2
        assert result.a.totals.cost_usd == pytest.approx(0.25)
        assert result.a.mean_cost_per_run == pytest.approx(0.125)

    def test_a_run_falls_back_to_session_id_when_a_record_carries_no_run_id(self):
        records = (
            _api_request(**{"kensai.arm": "A", "session.id": "sid-1"}, cost_usd=0.10),
            _api_request(**{"kensai.arm": "A", "session.id": "sid-2"}, cost_usd=0.10),
        )
        result = agent_usage.compare(records, "kensai.arm", "A", "B")
        assert result.a.run_count == 2

    def test_it_reports_b_minus_a_and_b_over_a_for_the_per_run_mean_cost(self):
        records = (
            _api_request(**{"kensai.arm": "A", "session.id": "sid-1"}, cost_usd=0.10),
            _api_request(**{"kensai.arm": "B", "session.id": "sid-2"}, cost_usd=0.30),
        )
        result = agent_usage.compare(records, "kensai.arm", "A", "B")
        assert result.diff == pytest.approx(0.20)
        assert result.ratio == pytest.approx(3.0)

    def test_a_group_with_no_runs_is_named_empty_and_prints_no_ratio(self):
        records = (_api_request(**{"kensai.arm": "A", "session.id": "sid-1"}, cost_usd=0.10),)
        result = agent_usage.compare(records, "kensai.arm", "A", "no-such-value")
        assert result.a is not None
        assert result.b is None
        assert result.diff is None
        assert result.ratio is None

    def test_where_applies_before_the_grouping(self):
        records = (
            _api_request(**{"kensai.arm": "A", "session.id": "sid-1", "speed": "normal"}, cost_usd=0.10),
            _api_request(**{"kensai.arm": "A", "session.id": "sid-2", "speed": "fast"}, cost_usd=0.90),
        )
        result = agent_usage.compare(
            records, "kensai.arm", "A", "B", where=(("speed", "normal"),)
        )
        assert result.a.totals.cost_usd == pytest.approx(0.10)


# ── Task 6 — the command ─────────────────────────────────────────────────────


class TestFiles:
    def test_reads_a_real_files_lines(self, tmp_path):
        path = tmp_path / "logs.jsonl"
        path.write_text("a\nb\n")
        files = agent_usage.Files()
        assert files.read_lines(path) == ["a", "b"]

    def test_returns_none_for_a_missing_file(self, tmp_path):
        files = agent_usage.Files()
        assert files.read_lines(tmp_path / "does-not-exist") is None


class TestCompositionRoot:
    def test_no_module_level_name_holds_the_expanded_default_directory(self):
        default_dir = Path.home() / ".kensaiapp" / "telemetry"
        holders = [
            name
            for name, value in vars(agent_usage).items()
            if value == default_dir or value == str(default_dir)
        ]
        assert holders == []

    def test_build_reader_resolves_the_default_directory(self):
        reader = agent_usage.build_reader()
        assert reader.directory == Path.home() / ".kensaiapp" / "telemetry"
        assert isinstance(reader.files, agent_usage.Files)

    def test_build_reader_honors_an_explicit_directory(self, tmp_path):
        reader = agent_usage.build_reader(tmp_path)
        assert reader.directory == tmp_path

    def test_only_build_reader_constructs_a_files(self):
        import ast as _ast

        source = Path(agent_usage.__file__).read_text()
        tree = _ast.parse(source)
        constructing_functions = set()
        for node in _ast.walk(tree):
            if isinstance(node, _ast.FunctionDef):
                for call in _ast.walk(node):
                    if isinstance(call, _ast.Call) and isinstance(call.func, _ast.Name):
                        if call.func.id == "Files":
                            constructing_functions.add(node.name)
        assert constructing_functions == {"build_reader"}

    def test_main_obtains_ports_from_build_reader_and_constructs_none_itself(self):
        import inspect as _inspect

        source = _inspect.getsource(agent_usage.main)
        assert "build_reader(" in source
        assert "Files(" not in source


def _write_stream(tmp_path: Path, logs_lines: list[str] | None, metrics_lines: list[str] | None = None) -> Path:
    if logs_lines is not None:
        (tmp_path / "logs.jsonl").write_text("\n".join(logs_lines) + "\n")
    if metrics_lines is not None:
        (tmp_path / "metrics.jsonl").write_text("\n".join(metrics_lines) + "\n")
    return tmp_path


class TestMain:
    def test_a_directory_holding_no_logs_jsonl_exits_0_and_names_the_path(self, tmp_path, capsys):
        exit_code = agent_usage.main(["--dir", str(tmp_path)])
        assert exit_code == 0
        out = capsys.readouterr().out
        assert str(tmp_path) in out

    def test_a_missing_metrics_jsonl_skips_the_check_and_says_so(self, tmp_path, capsys):
        _write_stream(tmp_path, [json.dumps(CAPTURED_LOGS_LINE)])
        exit_code = agent_usage.main(["--dir", str(tmp_path)])
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "metrics.jsonl" in out
        assert "skipped" in out.lower()

    def test_rows_are_led_by_cost_usd_highest_first_and_the_total_is_stated(self, tmp_path, capsys):
        cheap = _api_request(**{"session.id": "sid-cheap"}, cost_usd=0.01)
        expensive = _api_request(**{"session.id": "sid-expensive"}, cost_usd=9.0)
        lines = [
            json.dumps(
                {
                    "signal": "logs",
                    "received_at": "2026-09-11T00:00:00+00:00",
                    "body": {
                        "resourceLogs": [
                            {
                                "resource": {"attributes": []},
                                "scopeLogs": [
                                    {
                                        "scope": {},
                                        "logRecords": [
                                            {
                                                "attributes": [
                                                    _attr(k, v) for k, v in r.record_attrs.items()
                                                ]
                                            }
                                            for r in (cheap, expensive)
                                        ],
                                    }
                                ],
                            }
                        ]
                    },
                }
            )
        ]
        _write_stream(tmp_path, lines)
        agent_usage.main(["--dir", str(tmp_path)])
        out = capsys.readouterr().out
        assert out.index("sid-expensive") < out.index("sid-cheap")
        assert "Total cost_usd: 9.010000" in out

    def test_json_reports_the_same_total_as_the_table(self, tmp_path, capsys):
        _write_stream(tmp_path, [json.dumps(CAPTURED_LOGS_LINE)])
        agent_usage.main(["--dir", str(tmp_path)])
        table_out = capsys.readouterr().out
        assert "0.216465" in table_out or "0.2164645" in table_out

        agent_usage.main(["--dir", str(tmp_path), "--json"])
        json_out = capsys.readouterr().out
        payload = json.loads(json_out)
        assert payload["rows"][0]["cost_usd"] == pytest.approx(0.2164645)

    def test_where_flag_filters_the_agent_rows(self, tmp_path, capsys):
        # --where is Task 2's own rule (and Task 5's --compare shares it) — it is never claimed
        # of Task 4's subagent count, so this checks the "0 agent row(s)" line, not the whole
        # output.
        _write_stream(tmp_path, [json.dumps(CAPTURED_LOGS_LINE)])
        agent_usage.main(["--dir", str(tmp_path), "--where", "session.id=no-such-session"])
        out = capsys.readouterr().out
        assert "0 agent row(s)" in out

    def test_a_where_value_carrying_no_equals_sign_is_a_clear_error_not_a_crash(self, tmp_path):
        _write_stream(tmp_path, [json.dumps(CAPTURED_LOGS_LINE)])
        with pytest.raises(SystemExit, match="KEY=VALUE"):
            agent_usage.main(["--dir", str(tmp_path), "--where", "no-equals-sign-here"])

    def test_compare_flag_is_threaded_through_main(self, tmp_path, capsys):
        a = _api_request(**{"kensai.arm": "A", "session.id": "sid-1"}, cost_usd=0.10)
        b = _api_request(**{"kensai.arm": "B", "session.id": "sid-2"}, cost_usd=0.30)
        lines = [
            json.dumps(
                {
                    "signal": "logs",
                    "received_at": "2026-09-11T00:00:00+00:00",
                    "body": {
                        "resourceLogs": [
                            {
                                "resource": {"attributes": []},
                                "scopeLogs": [
                                    {
                                        "scope": {},
                                        "logRecords": [
                                            {
                                                "attributes": [
                                                    _attr(k, v) for k, v in r.record_attrs.items()
                                                ]
                                            }
                                            for r in (a, b)
                                        ],
                                    }
                                ],
                            }
                        ]
                    },
                }
            )
        ]
        _write_stream(tmp_path, lines)
        exit_code = agent_usage.main(["--dir", str(tmp_path), "--compare", "kensai.arm", "A", "B"])
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "A" in out and "B" in out
        assert "0.200000" in out  # B - A


# ── Integrity review — tests derived from the station plan, not the code ─────
#
# Added by `development-code-integrity` on 2026-09-11. Each test states a behaviour the plan at
# `system/projects/tools/journey/shukuba/2026-09-11_agent-usage-reads-a-run.md` names, at the level a
# person running the command sees it, where the suite above stopped at the unit.


def _logs_line(record_attr_maps: list[dict], resource_attrs: dict | None = None) -> str:
    return json.dumps(
        {
            "signal": "logs",
            "received_at": "2026-09-11T00:00:00+00:00",
            "body": {
                "resourceLogs": [
                    {
                        "resource": {
                            "attributes": [_attr(k, v) for k, v in (resource_attrs or {}).items()]
                        },
                        "scopeLogs": [
                            {
                                "scope": {},
                                "logRecords": [
                                    {"attributes": [_attr(k, v) for k, v in attrs.items()]}
                                    for attrs in record_attr_maps
                                ],
                            }
                        ],
                    }
                ]
            },
        }
    )


class TestIntegrityTask1:
    def test_numeric_fields_arriving_as_strings_are_summed_as_numbers_from_file_to_row(self):
        def envelope(key: str, value: dict) -> dict:
            return {"key": key, "value": value}

        base = [
            envelope("event.name", {"stringValue": "api_request"}),
            envelope("session.id", {"stringValue": "sid-1"}),
        ]
        records = [
            {
                "attributes": base
                + [
                    envelope("cost_usd", {"stringValue": "0.5"}),
                    envelope("duration_ms", {"stringValue": "1200"}),
                    envelope("input_tokens", {"intValue": "7"}),
                ]
            },
            {
                "attributes": base
                + [
                    envelope("cost_usd", {"doubleValue": 0.25}),
                    envelope("duration_ms", {"intValue": 300}),
                    envelope("input_tokens", {"intValue": 3}),
                ]
            },
        ]
        line = json.dumps(
            {"signal": "logs", "body": {"resourceLogs": [{"scopeLogs": [{"logRecords": records}]}]}}
        )
        rows = agent_usage.agent_rows(agent_usage.read_log_lines([line]).records)
        assert len(rows) == 1
        assert rows[0].cost_usd == pytest.approx(0.75)
        assert rows[0].duration_ms == 1500
        assert rows[0].input_tokens == 10

    def test_the_skipped_line_count_is_reported_by_the_command(self, tmp_path, capsys):
        _write_stream(
            tmp_path,
            ["not json {", json.dumps({"signal": "logs"}), json.dumps(CAPTURED_LOGS_LINE)],
        )
        agent_usage.main(["--dir", str(tmp_path)])
        text = capsys.readouterr().out
        assert any("skipped" in line and "2" in line for line in text.splitlines())

        agent_usage.main(["--dir", str(tmp_path), "--json"])
        assert json.loads(capsys.readouterr().out)["skipped_lines"] == 2


class TestIntegrityTask2:
    def test_the_fold_sums_every_token_class_not_only_input(self):
        records = (
            _api_request(output_tokens=20, cache_read_tokens=300, cache_creation_tokens=40),
            _api_request(output_tokens=5, cache_read_tokens=100, cache_creation_tokens=2),
        )
        row = agent_usage.agent_rows(records)[0]
        assert (row.output_tokens, row.cache_read_tokens, row.cache_creation_tokens) == (25, 400, 42)

    @pytest.mark.parametrize(
        "key, first, second",
        [
            ("session.id", "sid-1", "sid-2"),
            ("workflow.run_id", "wf-1", "wf-2"),
            ("query_source", "agent:custom", "repl_main_thread"),
            ("agent.name", "custom", "general-purpose"),
        ],
    )
    def test_records_differing_on_any_one_part_of_the_key_land_on_separate_rows(
        self, key, first, second
    ):
        rows = agent_usage.agent_rows((_api_request(**{key: first}), _api_request(**{key: second})))
        assert len(rows) == 2

    def test_repeated_where_keeps_only_rows_matching_every_pair(self):
        records = (
            _api_request(**{"session.id": "sid-1", "kensai.arm": "x"}),
            _api_request(**{"session.id": "sid-1", "kensai.arm": "y"}),
            _api_request(**{"session.id": "sid-2", "kensai.arm": "x"}),
        )
        rows = agent_usage.agent_rows(
            records, where=(("session.id", "sid-1"), ("kensai.arm", "x"))
        )
        assert [(r.session_id, r.kensai["kensai.arm"]) for r in rows] == [("sid-1", "x")]

    def test_where_reads_a_kensai_attribute_carried_only_on_the_resource(self):
        keep = _record(
            {"event.name": "api_request", "session.id": "sid-1"}, resource_attrs={"kensai.arm": "keep"}
        )
        drop = _record(
            {"event.name": "api_request", "session.id": "sid-2"}, resource_attrs={"kensai.arm": "drop"}
        )
        rows = agent_usage.agent_rows((keep, drop), where=(("kensai.arm", "keep"),))
        assert [r.session_id for r in rows] == ["sid-1"]

    def test_where_is_repeatable_on_the_command_line(self, tmp_path, capsys):
        _write_stream(
            tmp_path,
            [
                _logs_line(
                    [
                        {"event.name": "api_request", "session.id": "sid-1", "kensai.arm": "x", "cost_usd": 0.1},
                        {"event.name": "api_request", "session.id": "sid-1", "kensai.arm": "y", "cost_usd": 0.2},
                        {"event.name": "api_request", "session.id": "sid-2", "kensai.arm": "x", "cost_usd": 0.4},
                    ]
                )
            ],
        )
        agent_usage.main(
            ["--dir", str(tmp_path), "--json", "--where", "session.id=sid-1", "--where", "kensai.arm=x"]
        )
        rows = json.loads(capsys.readouterr().out)["rows"]
        assert len(rows) == 1
        assert rows[0]["cost_usd"] == pytest.approx(0.1)


class TestIntegrityTask3:
    def test_the_command_reports_both_figures_names_a_silent_session_and_flags_a_gap(
        self, tmp_path, capsys
    ):
        logs = [
            _logs_line(
                [
                    {"event.name": "api_request", "session.id": "sid-silent", "cost_usd": 0.05},
                    {"event.name": "api_request", "session.id": "sid-off", "cost_usd": 1.0},
                    {"event.name": "api_request", "session.id": "sid-ok", "cost_usd": 1.0},
                ]
            )
        ]
        metrics = [
            _metrics_line(_cost_metric([_cost_datapoint("sid-off", 1.5), _cost_datapoint("sid-ok", 0.6)])),
            _metrics_line(_cost_metric([_cost_datapoint("sid-ok", 0.4)])),
        ]
        _write_stream(tmp_path, logs, metrics)

        agent_usage.main(["--dir", str(tmp_path)])
        text = capsys.readouterr().out
        silent_lines = [
            line for line in text.splitlines() if "sid-silent" in line and "log_cost" in line
        ]
        assert silent_lines and "no metric" in silent_lines[0]

        agent_usage.main(["--dir", str(tmp_path), "--json"])
        checks = {c["session_id"]: c for c in json.loads(capsys.readouterr().out)["metrics_check"]}
        assert checks["sid-silent"]["metric_cost_usd"] is None
        assert checks["sid-off"]["log_cost_usd"] == pytest.approx(1.0)
        assert checks["sid-off"]["metric_cost_usd"] == pytest.approx(1.5)
        assert checks["sid-off"]["within_tolerance"] is False
        assert checks["sid-ok"]["metric_cost_usd"] == pytest.approx(1.0)
        assert checks["sid-ok"]["within_tolerance"] is True


class TestIntegrityTask4:
    def test_the_coverage_note_is_output_and_the_lumped_total_tokens_never_is(
        self, tmp_path, capsys
    ):
        _write_stream(tmp_path, [json.dumps(CAPTURED_LOGS_LINE)])
        agent_usage.main(["--dir", str(tmp_path)])
        text = capsys.readouterr().out
        agent_usage.main(["--dir", str(tmp_path), "--json"])
        json_text = capsys.readouterr().out

        assert agent_usage.SUBAGENT_COVERAGE_NOTE in text
        assert agent_usage.SUBAGENT_COVERAGE_NOTE in json.loads(json_text).values()
        for out in (text, json_text):
            assert "total_tokens" not in out
            assert "299840" not in out  # the real capture's lumped total_tokens value


class TestIntegrityTask5:
    FIGURES = (
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_creation_tokens",
        "cost_usd",
        "duration_ms",
    )

    def _stream(self, tmp_path: Path) -> Path:
        records = [
            {"event.name": "api_request", "session.id": "sid-1", "kensai.arm": "A", "kensai.run_id": "r1",
             "input_tokens": 1001, "output_tokens": 1100, "cache_read_tokens": 50000,
             "cache_creation_tokens": 4100, "cost_usd": 0.10, "duration_ms": 60000},
            {"event.name": "api_request", "session.id": "sid-2", "kensai.arm": "A", "kensai.run_id": "r2",
             "input_tokens": 2002, "output_tokens": 2200, "cache_read_tokens": 70000,
             "cache_creation_tokens": 4200, "cost_usd": 0.30, "duration_ms": 80000},
            {"event.name": "api_request", "session.id": "sid-3", "kensai.arm": "B", "kensai.run_id": "r3",
             "input_tokens": 7, "output_tokens": 8, "cache_read_tokens": 9,
             "cache_creation_tokens": 11, "cost_usd": 0.50, "duration_ms": 13},
        ]
        return _write_stream(tmp_path, [_logs_line(records)])

    def test_json_emits_each_groups_totals_and_mean_per_run_over_every_figure(self, tmp_path, capsys):
        self._stream(tmp_path)
        agent_usage.main(["--dir", str(tmp_path), "--json", "--compare", "kensai.arm", "A", "B"])
        compared = json.loads(capsys.readouterr().out)["compare"]
        a = compared["a"]
        assert a["run_count"] == 2
        expected_totals = dict(zip(self.FIGURES, (3003, 3300, 120000, 8300, 0.40, 140000)))
        for figure, total in expected_totals.items():
            assert a["totals"][figure] == pytest.approx(total), figure
            assert a["mean_per_run"][figure] == pytest.approx(total / 2), figure
        assert compared["diff"] == pytest.approx(0.50 - 0.20)
        assert compared["ratio"] == pytest.approx(0.50 / 0.20)

    def test_the_table_prints_each_groups_token_and_duration_totals(self, tmp_path, capsys):
        self._stream(tmp_path)
        agent_usage.main(["--dir", str(tmp_path), "--compare", "kensai.arm", "A", "B"])
        out = capsys.readouterr().out
        block = out[out.index("--compare"):]
        for total in ("3003", "3300", "120000", "8300", "140000"):
            assert total in block, total

    def test_an_empty_group_is_named_and_no_ratio_is_printed(self, tmp_path, capsys):
        self._stream(tmp_path)
        agent_usage.main(["--dir", str(tmp_path), "--compare", "kensai.arm", "A", "no-such-value"])
        out = capsys.readouterr().out
        block = out[out.index("--compare"):]
        assert any(
            "no-such-value" in line and "--compare" not in line for line in block.splitlines()
        )
        assert " / " not in block

        agent_usage.main(
            ["--dir", str(tmp_path), "--json", "--compare", "kensai.arm", "A", "no-such-value"]
        )
        compared = json.loads(capsys.readouterr().out)["compare"]
        assert compared["b"] is None
        assert compared["ratio"] is None


class TestIntegrityTask6:
    def test_a_path_nothing_occupies_exits_0_with_one_line_naming_it_and_no_row(
        self, tmp_path, capsys
    ):
        missing = tmp_path / "nothing" / "here"
        assert agent_usage.main(["--dir", str(missing)]) == 0
        out = capsys.readouterr().out
        assert len(out.strip().splitlines()) == 1
        assert str(missing) in out

    def test_a_directory_with_no_logs_jsonl_prints_exactly_one_line(self, tmp_path, capsys):
        assert agent_usage.main(["--dir", str(tmp_path)]) == 0
        assert len(capsys.readouterr().out.strip().splitlines()) == 1


class TestSurfacedByIntegrity:
    """The three items `code-integrity-report.md` § Surfaced, not fixed raised, fixed by hand:
    a non-numeric `intValue` must not stop the read, a missing key must not match `--where KEY=None`,
    and a `--where` narrower than a session must not report a false metrics gap."""

    def test_a_non_numeric_int_value_string_decodes_to_none_rather_than_stopping_the_read(self):
        assert agent_usage.decode_value({"intValue": "abc"}) is None
        payload = json.loads(_logs_line([{"event.name": "api_request", "session.id": "sid-1", "cost_usd": 0.2}]))
        record = payload["body"]["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]
        record["attributes"].append({"key": "event.sequence", "value": {"intValue": "abc"}})
        rows = agent_usage.agent_rows(agent_usage.read_log_lines([json.dumps(payload)]).records)
        assert sum(r.cost_usd for r in rows) == pytest.approx(0.2)

    def test_where_key_equals_none_does_not_match_a_record_lacking_the_key(self):
        rows = agent_usage.agent_rows((_api_request(),), (("workflow.run_id", "None"),))
        assert rows == ()

    def test_a_where_narrower_than_a_session_is_held_against_the_whole_session(self, tmp_path, capsys):
        logs = [
            _logs_line(
                [
                    {"event.name": "api_request", "session.id": "sid-1", "query_source": "agent:custom", "cost_usd": 0.3},
                    {"event.name": "api_request", "session.id": "sid-1", "query_source": "repl_main_thread", "cost_usd": 0.7},
                ]
            )
        ]
        metrics = [_metrics_line(_cost_metric([_cost_datapoint("sid-1", 1.0)]))]
        _write_stream(tmp_path, logs, metrics)

        agent_usage.main(["--dir", str(tmp_path), "--where", "query_source=agent:custom", "--json"])
        checks = {c["session_id"]: c for c in json.loads(capsys.readouterr().out)["metrics_check"]}
        assert checks["sid-1"]["log_cost_usd"] == pytest.approx(1.0)
        assert checks["sid-1"]["within_tolerance"] is True
