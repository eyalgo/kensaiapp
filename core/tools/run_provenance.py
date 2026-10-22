#!/usr/bin/env python3
"""run_provenance.py — one run's provider, model, effort and source, read back by its run ID.

WHY THIS EXISTS
    A launcher run is stamped with `kensai.provider`, `kensai.model`, `kensai.effort` and
    `kensai.source` (`run_telemetry.sh`), and prints its `kensai.run_id` on its `Telemetry:` line.
    A stamp nobody can read back proves nothing, so this takes that printed ID and answers from the
    receiver's own log, `~/.kensaiapp/telemetry/logs.jsonl` — what landed, not what the launcher
    meant to send.

    1. **Only `kensai.*` is read.** A Claude record also carries its own native `model` and
       `effort`; those are Claude's account of a request, not the launch's, and are never consulted.
    2. **Record first, resource second, per key** — the telemetry gateway's one attribute lookup,
       reused rather than copied. Claude puts `kensai.*` on the record and the resource, Codex on
       the resource only, and one resolution reads both. The log is parsed through the gateway
       too, so nothing here imports the telemetry package or its modules.
    3. **The log is ~1.2 GB and is streamed.** A line is kept only when it contains the run ID's
       bytes, before any JSON parse; the match itself is exact equality of the resolved
       `kensai.run_id`, because the substring test alone admits a longer ID.
    4. **A found run can still fail the proof.** No `kensai.provider` on any of its records (a run
       from before the stamp existed) and two different present values for one key are both exit
       3 — the ID landed, the provenance cannot be stated as one line each.

    Exits: 0 the five lines · 1 no log, or the ID never landed · 2 usage · 3 landed, unprovable
           · 4 this Python cannot import the telemetry package.
    The five lines go to stdout; every refusal to stderr.

Usage:  ~/.kensaiapp/venv/bin/python <CORE>/tools/run_provenance.py <run-id>
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any

import telemetry_gateway

__version__ = "1.1.1"

USAGE = "usage: python3 run_provenance.py <run-id>"

RUN_ID_KEY = "kensai.run_id"
PROVIDER_KEY = "kensai.provider"
# The order the five lines print in and the order conflicts are reported in (CP-197, CP-200).
PROVENANCE_KEYS = (PROVIDER_KEY, "kensai.model", "kensai.effort", "kensai.source")
ABSENT = "(none)"


class Exit(IntEnum):
    """The check's exit statuses — a closed set a caller branches on without parsing text."""

    FOUND = 0
    NOT_LANDED = 1
    USAGE = 2
    UNPROVABLE = 3
    UNAVAILABLE = 4


# ── the port ────────────────────────────────────────────────────────────────


class LogSource:
    """The one way the check reaches the receiver's log."""

    def lines_carrying(self, path: Path, needle: str) -> list[str] | None:
        """Every line of `path` containing `needle`, streamed, newline stripped — or `None` when
        the log is absent or cannot be read. A line is tested as bytes, so the gigabyte of lines
        that do not carry the needle is never decoded."""
        wanted = needle.encode("utf-8")
        try:
            with path.open("rb") as log:
                return [
                    line.decode("utf-8", errors="replace").rstrip("\r\n")
                    for line in log
                    if wanted in line
                ]
        except OSError:
            return None


@dataclass(frozen=True)
class Reader:
    """The check's whole environment: the port, the log path it reads, and the telemetry
    collaborator that parses the log and resolves a record's attributes."""

    source: LogSource
    log_path: Path
    telemetry: telemetry_gateway.Telemetry


# ── the answer ──────────────────────────────────────────────────────────────


def records_of(
    run_id: str, lines: list[str], telemetry: telemetry_gateway.Telemetry
) -> tuple[Any, ...]:
    """The records whose resolved `kensai.run_id` is exactly `run_id`, in log order. The lines
    arrive pre-filtered on the ID as a substring; this is where a longer ID is told apart."""
    parsed = telemetry.parse_logs(lines)
    return tuple(
        record
        for record in parsed.records
        if telemetry.attribute_value(record, RUN_ID_KEY) == run_id
    )


def distinct_values(
    records: tuple[Any, ...], key: str, telemetry: telemetry_gateway.Telemetry
) -> tuple[str, ...]:
    """`key`'s distinct present values across `records`, in order of first appearance. A record
    that lacks the key contributes nothing — an absence is never a disagreeing value."""
    seen: list[str] = []
    for record in records:
        value = telemetry.attribute_value(record, key)
        if value is not None and str(value) not in seen:
            seen.append(str(value))
    return tuple(seen)


# ── the command ─────────────────────────────────────────────────────────────


def refuse_usage() -> Exit:
    """Print the usage refusal; the status for a call without exactly one argument."""
    print(USAGE, file=sys.stderr)
    return Exit.USAGE


def run(argv: list[str], reader: Reader) -> int:
    """Answer for the one run ID in `argv` from `reader`'s log; return the exit status."""
    if len(argv) != 1:
        return refuse_usage()
    run_id = argv[0]
    lines = reader.source.lines_carrying(reader.log_path, run_id)
    if lines is None:
        print(f"no telemetry log at {reader.log_path}", file=sys.stderr)
        return Exit.NOT_LANDED
    records = records_of(run_id, lines, reader.telemetry)
    if not records:
        print(f"not found: {run_id} in {reader.log_path}", file=sys.stderr)
        return Exit.NOT_LANDED
    values = {key: distinct_values(records, key, reader.telemetry) for key in PROVENANCE_KEYS}
    if not values[PROVIDER_KEY]:
        print(f"no provider recorded: {run_id}", file=sys.stderr)
        return Exit.UNPROVABLE
    conflicts = [key for key in PROVENANCE_KEYS if len(values[key]) > 1]
    for key in conflicts:
        print(f"conflicting {key} for {run_id}: {', '.join(values[key])}", file=sys.stderr)
    if conflicts:
        return Exit.UNPROVABLE
    print(f"run_id: {run_id}")
    for key in PROVENANCE_KEYS:
        found = values[key]
        print(f"{key.removeprefix('kensai.')}: {found[0] if found else ABSENT}")
    return Exit.FOUND


# ── the composition root ────────────────────────────────────────────────────


def build_reader(telemetry: telemetry_gateway.Telemetry | None = None) -> Reader:
    """Wire the real port and the telemetry collaborator. The only place `LogSource()` is
    constructed and the only place the receiver's log path is named. A test passes its own
    `telemetry`; otherwise the gateway loads the package, or raises `TelemetryUnavailable`."""
    return Reader(
        source=LogSource(),
        log_path=Path.home() / ".kensaiapp" / "telemetry" / "logs.jsonl",
        telemetry=telemetry_gateway.build_telemetry() if telemetry is None else telemetry,
    )


def main(argv: list[str] | None = None) -> int:
    """Check the argument count first, then wire: a call that is refused for its arguments
    never needs the package, and a call that is not refused and cannot have it prints the
    gateway's message and exits `UNAVAILABLE` before the log is touched."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        return refuse_usage()
    try:
        reader = build_reader()
    except telemetry_gateway.TelemetryUnavailable:
        print(
            telemetry_gateway.dependency_message(telemetry_gateway.ReaderName.RUN_PROVENANCE),
            file=sys.stderr,
        )
        return Exit.UNAVAILABLE
    return run(args, reader)


if __name__ == "__main__":
    sys.exit(main())
