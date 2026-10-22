"""telemetry_gateway.py — the one door from kensaiapp to the optional telemetry package.

WHY THIS EXISTS
    Four readers (the context-cap hook, `chain_usage.py`, `run_provenance.py` and the
    cache-read measurement) used to import the telemetry code as sibling modules. The package
    now holds that code, and kensaiapp must run with the package absent, so the package cannot
    be a hard dependency of anything that is imported at start-up.

    This file is the only Python file that names the package. It imports it inside
    `build_telemetry`, never at module top, so importing this module builds nothing, prints
    nothing and raises nothing whether or not the package is installed. A caller asks for a
    `Telemetry` and receives either the facade below, under kensaiapp's own names, or
    `TelemetryUnavailable`, and says what it does without the package.

    **A facade, not a wrapper of behaviour.** Values are translated into the plain frozen
    types below with nothing recounted, re-sorted or re-defaulted; the package keeps owning
    every counting, parsing and de-duplication rule. A log record is opaque to a caller. The one
    attribute lookup the provenance check needs is a public method here, so the package's
    private lookup is called from a single place.

    **Both dependency messages live here** because no other tracked `.py` file may spell the
    package's import name, in code, comments or strings. A caller prints
    `dependency_message(ReaderName.X)` and the hook prints `CONTEXT_UNAVAILABLE`.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

__version__ = "1.0.0"

CONTEXT_UNAVAILABLE = (
    "context cap: the cap needs the ka_telemetry package, which this Python cannot import; "
    "this run is not capped"
)

_DEPENDENCY_MESSAGE = "{reader}: needs the ka_telemetry package, which this Python cannot import"


class ReaderName(str, Enum):
    """The readers that print the dependency message, a closed set whose value is also the
    prefix of the line written out."""

    CHAIN_USAGE = "chain_usage"
    RUN_PROVENANCE = "run_provenance"
    MEASURE = "measure"


def dependency_message(reader: ReaderName) -> str:
    """The one line `reader` prints on standard error when the package cannot be imported, with
    no trailing newline."""
    return _DEPENDENCY_MESSAGE.format(reader=reader.value)


class TelemetryUnavailable(Exception):
    """The package could not be imported, so no `Telemetry` can be built. Raised only for an
    import failure; any other error out of wiring keeps its own type."""


# ── the values a caller sees ────────────────────────────────────────────────


@dataclass(frozen=True)
class Spend:
    """One model's totals: five usage classes kept apart, and `thinking`, a share of `output`
    that is `None` when no record said anything about it."""

    input: int
    output: int
    cache_read: int
    cache_write_1h: int
    cache_write_5m: int
    thinking: int | None


@dataclass(frozen=True)
class Run:
    """One non-interactive run from the saved agents listing."""

    session_id: str
    name: str | None
    cwd: str | None
    state: str | None
    started_at: int | None


@dataclass(frozen=True)
class RunListing:
    """The kept runs in listing order, and how many rows were left out and why."""

    runs: tuple[Run, ...]
    interactive_excluded: int
    dropped_no_session: int
    total_seen: int


@dataclass(frozen=True)
class LogRead:
    """The log records found, opaque to a caller, and how many lines could not be read."""

    records: tuple[Any, ...]
    skipped: int


# ── the backend, and the facade over it ─────────────────────────────────────


@dataclass(frozen=True)
class Backend:
    """What the facade reads the package through: `runs` supplies the run-usage functions and
    the file and process constructors, `gauge` the current-context reading and `logs` the log
    parser and its attribute lookup. The real package modules fill it, and a test fills it with
    fakes."""

    runs: Any
    gauge: Any
    logs: Any


class Telemetry:
    """Every operation a reader takes from the package, under kensaiapp's own names. It is given
    its backend and its two ports; it constructs none of them."""

    def __init__(self, *, backend: Backend, files: Any, processes: Any):
        self._backend = backend
        self.files = files
        self.processes = processes

    def parse_runs(self, agents_json_text: str) -> RunListing:
        """`claude agents --json --all` text → the non-interactive runs, in listing order."""
        parsed = self._backend.runs.runs_from(agents_json_text)
        return RunListing(
            runs=tuple(
                Run(
                    session_id=run.session_id,
                    name=run.name,
                    cwd=run.cwd,
                    state=run.state,
                    started_at=run.started_at,
                )
                for run in parsed.runs
            ),
            interactive_excluded=parsed.interactive_excluded,
            dropped_no_session=parsed.dropped_no_session,
            total_seen=parsed.total_seen,
        )

    def find_transcript(self, session_id: str, projects_root: Path, files: Any) -> Path | None:
        """The transcript of `session_id` under `projects_root`, or `None`."""
        return self._backend.runs.transcript_for(session_id, projects_root, files)

    def read_usage(self, path: Path, files: Any) -> Iterator[Any]:
        """The usage records of the transcript at `path`, one per API response, lazily."""
        return self._backend.runs.usage_records(path, files)

    def spend_by_model(self, records: Iterable[Any]) -> dict[str, Spend]:
        """Usage records → one `Spend` per model, in the order the package gives them."""
        return {
            model: Spend(
                input=amount.input,
                output=amount.output,
                cache_read=amount.cache_read,
                cache_write_1h=amount.cache_write_1h,
                cache_write_5m=amount.cache_write_5m,
                thinking=amount.thinking,
            )
            for model, amount in self._backend.runs.spend_by_model(records).items()
        }

    def span_seconds(self, records: Iterable[Any]) -> float | None:
        """Usage records → the run's wall time in seconds, or `None` when none is timestamped."""
        return self._backend.runs.span_seconds(records)

    def current_context(self, path: Path, files: Any) -> int | None:
        """The size of the context the newest request in the transcript at `path` carried, or
        `None` when the transcript is unreadable or holds no usage."""
        return self._backend.gauge.current_context(path, files)

    def parse_logs(self, lines: list[str]) -> LogRead:
        """Telemetry log lines → their records, opaque, and the count of lines skipped."""
        parsed = self._backend.logs.read_log_lines(lines)
        return LogRead(records=tuple(parsed.records), skipped=parsed.skipped)

    def attribute_value(self, record: Any, key: str) -> Any:
        """`key`'s value on `record` itself first, on its resource second, else `None`. The only
        call anywhere to the package's private lookup."""
        return self._backend.logs._attr(record, key)


def build_telemetry(backend: Backend | None = None) -> Telemetry:
    """The composition root: the only place the package is imported and the only place a port
    is constructed. With no `backend` the real package is loaded here; a test passes its own
    and the package is never touched.

    Raises `TelemetryUnavailable` when the package cannot be imported, and nothing else for it.
    """
    if backend is None:
        try:
            from ka_telemetry import context_gauge, run_usage, stream_usage
        except ImportError as exc:
            raise TelemetryUnavailable("the telemetry package cannot be imported") from exc
        backend = Backend(runs=run_usage, gauge=context_gauge, logs=stream_usage)
    return Telemetry(
        backend=backend, files=backend.runs.Files(), processes=backend.runs.Processes()
    )
