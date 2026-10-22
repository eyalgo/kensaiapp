"""Tests for `run_provenance.py` — one run's provider, model, effort and source, read back by
its run ID.

Nothing here monkeypatches the module under test. The check reaches the log through one port,
`LogSource`, and reads it through one telemetry collaborator, both handed to `run()` inside a
`Reader`; the fakes below stand in for them. The fake telemetry parses the receiver's lines the
way the gateway's contract describes — records opaque, attributes resolved record first and
resource second — so the package is not needed and the check's own decisions are what is tested.
The real port is exercised on its own, against a file in `tmp_path`.

Every log line is built here in the receiver's own shape — `{"body": {"resourceLogs": [...]}}`,
one export batch per line — so the two placements the spec verified are both constructed
deliberately: a Claude record carries `kensai.*` on the record *and* the resource, a Codex
record on the resource only.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path

import pytest

import run_provenance

LOG_PATH = Path("/home/someone/.kensaiapp/telemetry/logs.jsonl")


# ── building the receiver's lines ───────────────────────────────────────────


def _attributes(values: dict[str, str]) -> list[dict]:
    return [{"key": key, "value": {"stringValue": value}} for key, value in values.items()]


def export_line(records: list[dict[str, str]], resource: dict[str, str]) -> str:
    """One receiver line: one export batch, one resource, the given log records under it."""
    body = {
        "resourceLogs": [
            {
                "resource": {"attributes": _attributes(resource)},
                "scopeLogs": [{"logRecords": [{"attributes": _attributes(r)} for r in records]}],
            }
        ]
    }
    return json.dumps({"body": body})


def provenance(run_id: str, **values: str) -> dict[str, str]:
    """The `kensai.*` attributes a stamped run carries: `provider="codex"` → `kensai.provider`."""
    attributes = {"kensai.run_id": run_id}
    attributes.update({f"kensai.{key}": value for key, value in values.items()})
    return attributes


def claude_line(run_id: str, native: dict[str, str] | None = None, **values: str) -> str:
    """Claude's placement: `kensai.*` on the resource and the record, beside native attributes."""
    stamped = provenance(run_id, **values)
    record = {"event.name": "api_request", **(native or {}), **stamped}
    return export_line([record], resource={"service.name": "claude-code", **stamped})


def codex_line(run_id: str, **values: str) -> str:
    """Codex's placement: `kensai.*` on the resource only."""
    return export_line(
        [{"event.name": "codex.api_request"}],
        resource={"service.name": "codex", **provenance(run_id, **values)},
    )


# ── the fake port ───────────────────────────────────────────────────────────


class FakeLogSource:
    """Answers `lines_carrying` as the real port does — every line containing the needle, or
    `None` when there is no log — and records each question it was asked."""

    def __init__(self, lines: list[str] | None) -> None:
        self._lines = lines
        self.asked: list[tuple[Path, str]] = []

    def lines_carrying(self, path: Path, needle: str) -> list[str] | None:
        self.asked.append((path, needle))
        if self._lines is None:
            return None
        return [line for line in self._lines if needle in line]


@dataclass(frozen=True)
class FakeRecord:
    """An opaque log record: its own attributes and its resource's."""

    attributes: dict
    resource: dict


@dataclass(frozen=True)
class FakeLogRead:
    records: tuple
    skipped: int


class FakeTelemetry:
    """The two operations the check takes from the gateway, written by hand from its contract."""

    def __init__(self) -> None:
        self.parsed: list[list[str]] = []
        self.looked_up: list[tuple[FakeRecord, str]] = []

    @staticmethod
    def _flat(attributes: list[dict]) -> dict:
        return {item["key"]: item["value"]["stringValue"] for item in attributes}

    def parse_logs(self, lines: list[str]) -> FakeLogRead:
        self.parsed.append(list(lines))
        records, skipped = [], 0
        for line in lines:
            try:
                resources = json.loads(line)["body"]["resourceLogs"]
            except (ValueError, KeyError, TypeError):
                skipped += 1
                continue
            for resource in resources:
                shared = self._flat(resource["resource"]["attributes"])
                for scope in resource["scopeLogs"]:
                    for record in scope["logRecords"]:
                        records.append(FakeRecord(self._flat(record["attributes"]), shared))
        return FakeLogRead(records=tuple(records), skipped=skipped)

    def attribute_value(self, record: FakeRecord, key: str):
        self.looked_up.append((record, key))
        if key in record.attributes:
            return record.attributes[key]
        return record.resource.get(key)


def check(argv: list[str], lines: list[str] | None) -> tuple[int, FakeLogSource]:
    source = FakeLogSource(lines)
    reader = run_provenance.Reader(source=source, log_path=LOG_PATH, telemetry=FakeTelemetry())
    return run_provenance.run(argv, reader), source


def five_lines(run_id: str, provider: str, model: str, effort: str, source: str) -> str:
    return (
        f"run_id: {run_id}\nprovider: {provider}\nmodel: {model}\n"
        f"effort: {effort}\nsource: {source}\n"
    )


# ── CP-197 — the five lines ─────────────────────────────────────────────────


def test_claude_shaped_record_prints_the_five_lines_and_exits_0(capsys):
    run_id = str(uuid.uuid4())
    line = claude_line(
        run_id, provider="claude", model="claude-opus-5-5", effort="high", source="intelligence"
    )

    code, source = check([run_id], [line])

    out = capsys.readouterr()
    assert code == 0
    assert out.out == five_lines(run_id, "claude", "claude-opus-5-5", "high", "intelligence")
    assert out.err == ""
    assert source.asked == [(LOG_PATH, run_id)]


def test_codex_shaped_record_prints_the_five_lines_and_exits_0(capsys):
    run_id = str(uuid.uuid4())
    lines = [
        codex_line(run_id, provider="codex", model="gpt-5.6-terra", effort="medium", source="tier")
        for _ in range(3)
    ]

    code, _ = check([run_id], lines)

    out = capsys.readouterr()
    assert code == 0
    assert out.out == five_lines(run_id, "codex", "gpt-5.6-terra", "medium", "tier")


def test_absent_model_effort_or_source_prints_none(capsys):
    run_id = str(uuid.uuid4())

    code, _ = check([run_id], [codex_line(run_id, provider="codex")])

    assert code == 0
    assert capsys.readouterr().out == five_lines(run_id, "codex", "(none)", "(none)", "(none)")


def test_native_model_and_effort_are_never_read(capsys):
    stamped_id, unstamped_id = str(uuid.uuid4()), str(uuid.uuid4())
    native = {"model": "claude-native-model", "effort": "max"}
    lines = [
        claude_line(stamped_id, native=native, provider="claude", model="claude-opus-5-5"),
        claude_line(unstamped_id, native=native, provider="claude", source="default"),
    ]

    stamped_code, _ = check([stamped_id], lines)
    stamped_out = capsys.readouterr().out
    unstamped_code, _ = check([unstamped_id], lines)
    unstamped_out = capsys.readouterr().out

    assert stamped_code == 0
    assert stamped_out == five_lines(stamped_id, "claude", "claude-opus-5-5", "(none)", "(none)")
    assert unstamped_code == 0
    assert unstamped_out == five_lines(unstamped_id, "claude", "(none)", "(none)", "default")


# ── CP-198 — never landed ───────────────────────────────────────────────────


def test_fresh_uuid_is_not_found(capsys):
    landed = str(uuid.uuid4())
    fresh = str(uuid.uuid4())

    code, _ = check([fresh], [codex_line(landed, provider="codex")])

    out = capsys.readouterr()
    assert code == 1
    assert out.err == f"not found: {fresh} in {LOG_PATH}\n"
    assert out.out == ""


def test_absent_log_prints_no_telemetry_log(capsys):
    code, _ = check([str(uuid.uuid4())], None)

    out = capsys.readouterr()
    assert code == 1
    assert out.err == f"no telemetry log at {LOG_PATH}\n"
    assert out.out == ""


def test_a_longer_id_containing_the_id_is_not_a_match(capsys):
    run_id = str(uuid.uuid4())
    longer = f"{run_id}-retry"

    code, _ = check([run_id], [codex_line(longer, provider="codex", source="default")])

    assert code == 1
    assert capsys.readouterr().err == f"not found: {run_id} in {LOG_PATH}\n"


def test_records_of_other_runs_in_the_same_export_are_ignored(capsys):
    run_id, other = str(uuid.uuid4()), str(uuid.uuid4())
    line = export_line(
        [
            provenance(run_id, provider="claude", model="claude-opus-5-5"),
            provenance(other, provider="codex", model="gpt-6.1-sol"),
        ],
        resource={"service.name": "claude-code"},
    )

    code, _ = check([run_id], [line])

    assert code == 0
    assert capsys.readouterr().out == five_lines(
        run_id, "claude", "claude-opus-5-5", "(none)", "(none)"
    )


# ── CP-199 — landed without provenance ──────────────────────────────────────


def test_found_without_provider_exits_3(capsys):
    run_id = str(uuid.uuid4())

    code, _ = check([run_id], [codex_line(run_id)])

    out = capsys.readouterr()
    assert code == 3
    assert out.err == f"no provider recorded: {run_id}\n"
    assert out.out == ""


def test_no_provider_wins_over_a_conflict(capsys):
    run_id = str(uuid.uuid4())
    lines = [codex_line(run_id, model="a"), codex_line(run_id, model="b")]

    code, _ = check([run_id], lines)

    assert code == 3
    assert capsys.readouterr().err == f"no provider recorded: {run_id}\n"


# ── CP-200 — disagreeing records ────────────────────────────────────────────


def test_conflicting_model_prints_values_in_first_appearance_order_and_exits_3(capsys):
    run_id = str(uuid.uuid4())
    lines = [
        codex_line(run_id, provider="codex", model="zeta", source="tier"),
        codex_line(run_id, provider="codex", model="alpha", source="default"),
        codex_line(run_id, provider="codex", model="zeta", source="tier"),
        codex_line(run_id, provider="codex", model="mid", source="tier"),
    ]

    code, _ = check([run_id], lines)

    out = capsys.readouterr()
    assert code == 3
    assert out.err == (
        f"conflicting kensai.model for {run_id}: zeta, alpha, mid\n"
        f"conflicting kensai.source for {run_id}: tier, default\n"
    )
    assert out.out == ""


def test_a_record_lacking_effort_is_not_a_conflict(capsys):
    run_id = str(uuid.uuid4())
    lines = [
        codex_line(run_id, provider="codex", model="m"),
        codex_line(run_id, provider="codex", model="m", effort="high"),
    ]

    code, _ = check([run_id], lines)

    assert code == 0
    assert capsys.readouterr().out == five_lines(run_id, "codex", "m", "high", "(none)")


def test_the_same_value_on_two_records_is_not_a_conflict(capsys):
    run_id = str(uuid.uuid4())
    lines = [codex_line(run_id, provider="codex", model="m", source="tier")] * 2

    code, _ = check([run_id], lines)

    assert code == 0
    assert capsys.readouterr().out == five_lines(run_id, "codex", "m", "(none)", "tier")


# ── the read ────────────────────────────────────────────────────────────────


def test_malformed_and_blank_lines_are_skipped(capsys):
    run_id = str(uuid.uuid4())
    lines = [
        f"not json {run_id}",
        "   ",
        json.dumps({"body": {}, "note": run_id}),
        codex_line(run_id, provider="codex", model="m", effort="low", source="tier"),
    ]

    code, _ = check([run_id], lines)

    assert code == 0
    assert capsys.readouterr().out == five_lines(run_id, "codex", "m", "low", "tier")


# ── CP-201 — usage ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("argv", [[], ["one", "two"]], ids=["no-argument", "two-arguments"])
def test_no_argument_prints_usage_and_exits_2(capsys, argv):
    code, source = check(argv, [])

    out = capsys.readouterr()
    assert code == 2
    assert out.err.startswith("usage: ")
    assert "run_provenance.py <run-id>" in out.err
    assert out.out == ""
    assert source.asked == []


# ── the real port and the wiring ────────────────────────────────────────────


def test_the_real_log_source_keeps_only_lines_carrying_the_id(tmp_path):
    run_id = str(uuid.uuid4())
    kept = [codex_line(run_id, provider="codex"), claude_line(f"{run_id}-retry", provider="c")]
    log = tmp_path / "logs.jsonl"
    log.write_text("\n".join([codex_line(str(uuid.uuid4())), *kept, ""]) + "\n", encoding="utf-8")

    assert run_provenance.LogSource().lines_carrying(log, run_id) == kept


def test_the_real_log_source_answers_none_for_an_absent_log(tmp_path):
    assert run_provenance.LogSource().lines_carrying(tmp_path / "logs.jsonl", "x") is None


def test_build_reader_reads_the_receiver_log_under_home_with_the_given_telemetry():
    telemetry = FakeTelemetry()

    reader = run_provenance.build_reader(telemetry)

    assert isinstance(reader.source, run_provenance.LogSource)
    assert reader.log_path == Path.home() / ".kensaiapp" / "telemetry" / "logs.jsonl"
    assert reader.telemetry is telemetry


def test_run_over_the_real_port_finds_a_run_in_a_real_file(tmp_path, capsys):
    run_id = str(uuid.uuid4())
    log = tmp_path / "logs.jsonl"
    log.write_text(
        codex_line(run_id, provider="codex", model="gpt-5.6-terra", effort="medium", source="tier")
        + "\n",
        encoding="utf-8",
    )
    reader = run_provenance.Reader(
        source=run_provenance.LogSource(), log_path=log, telemetry=FakeTelemetry()
    )

    code = run_provenance.run([run_id], reader)

    assert code == 0
    assert capsys.readouterr().out == five_lines(run_id, "codex", "gpt-5.6-terra", "medium", "tier")


# ── surfaced by development-code-integrity (same change) ───────────────────


def test_a_run_id_that_is_not_a_uuid_is_searched_for_not_refused(capsys):
    """CP-201: the ID's shape is not validated — any string is searched for, and one no record
    carries takes CP-198, never the usage error."""
    code, source = check(["not-a-uuid"], [codex_line(str(uuid.uuid4()), provider="codex")])

    out = capsys.readouterr()
    assert code == 1
    assert out.err == f"not found: not-a-uuid in {LOG_PATH}\n"
    assert source.asked == [(LOG_PATH, "not-a-uuid")]


def test_a_log_that_cannot_be_read_prints_no_telemetry_log(tmp_path, capsys):
    """CP-198: a log that exists but cannot be read is answered as an absent one — here, a
    directory where the log file should be, read through the real port."""
    log = tmp_path / "logs.jsonl"
    log.mkdir()
    reader = run_provenance.Reader(
        source=run_provenance.LogSource(), log_path=log, telemetry=FakeTelemetry()
    )

    code = run_provenance.run([str(uuid.uuid4())], reader)

    out = capsys.readouterr()
    assert code == 1
    assert out.err == f"no telemetry log at {log}\n"
    assert out.out == ""


# ── through the gateway (the telemetry collaborator is the only reader of the log) ──────


def test_provenance_preserves_exact_id_and_refusal_order(capsys):
    """Each refusal keeps its status and its precedence, and the exit set gains only `4`."""
    assert {member.name: int(member) for member in run_provenance.Exit} == {
        "FOUND": 0, "NOT_LANDED": 1, "USAGE": 2, "UNPROVABLE": 3, "UNAVAILABLE": 4,
    }
    run_id = str(uuid.uuid4())

    usage, source = check([], [codex_line(run_id, provider="codex")])
    assert (usage, source.asked) == (2, [])
    capsys.readouterr()

    no_log, _ = check([run_id], None)
    assert no_log == 1
    capsys.readouterr()

    longer, _ = check([run_id], [codex_line(f"{run_id}-x", provider="codex")])
    assert longer == 1
    capsys.readouterr()

    unprovable, _ = check([run_id], [codex_line(run_id, model="m")])
    assert unprovable == 3


def test_the_check_resolves_every_key_through_the_telemetry_collaborator():
    run_id = str(uuid.uuid4())
    telemetry = FakeTelemetry()
    reader = run_provenance.Reader(
        source=FakeLogSource([claude_line(run_id, provider="claude", model="m")]),
        log_path=LOG_PATH,
        telemetry=telemetry,
    )

    run_provenance.run([run_id], reader)

    keys = [key for _, key in telemetry.looked_up]
    assert keys[0] == run_provenance.RUN_ID_KEY
    assert set(run_provenance.PROVENANCE_KEYS) <= set(keys)
    assert len(telemetry.parsed) == 1


def test_main_refuses_a_wrong_argument_count_before_any_wiring(capsys):
    """The count is checked before the package is asked for: usage `2` holds with or without it."""
    for argv in ([], ["one", "two"]):
        assert run_provenance.main(argv) == 2
        captured = capsys.readouterr()
        assert captured.err == run_provenance.USAGE + "\n"
        assert captured.out == ""
