"""One fake per port of `security_bookkeeping.py`, each seeded by the test that makes it.

Each is checked against its port's contract suite in `test_security_bookkeeping.py`, and each
records what it received. Only tests import this module.
"""

from __future__ import annotations

import datetime
import json

import security_bookkeeping as sb


class FakeFiles:
    """Files held as text in a dict, so "byte-identical" is an equality on that text."""

    def __init__(self, held: dict[str, str] | None = None) -> None:
        self.held: dict[str, str] = dict(held or {})
        self.written: list[str] = []
        self.reads: list[str] = []
        self._failing_reads: dict[str, str] = {}
        self._failing_writes: dict[str, str] = {}

    def fail_read(self, path: str, reason: str) -> None:
        """Make every read of `path` raise the port's error with `reason`."""
        self._failing_reads[path] = reason

    def fail_write(self, path: str, reason: str) -> None:
        """Make every write of `path` raise the port's error with `reason`, holding nothing."""
        self._failing_writes[path] = reason

    def read_text(self, path: str) -> str | None:
        self.reads.append(path)
        if path in self._failing_reads:
            raise sb.FileAccessError(self._failing_reads[path])
        return self.held.get(path)

    def write_text(self, path: str, text: str) -> None:
        if path in self._failing_writes:
            raise sb.FileAccessError(self._failing_writes[path])
        self.held[path] = text
        self.written.append(path)


class FakeAdvisories:
    """Advisory records held by id as the raw text the service would send."""

    def __init__(self) -> None:
        self._held: dict[str, str] = {}
        self._failures: dict[str, str] = {}
        self.fetched: list[str] = []

    def serve(self, advisory_id: str, body: str) -> None:
        self._held[advisory_id] = body

    def serve_record(self, advisory_id: str, record: dict) -> None:
        self.serve(advisory_id, json.dumps(record))

    def fail(self, advisory_id: str, reason: str) -> None:
        self._failures[advisory_id] = reason

    def fetch(self, advisory_id: str) -> dict:
        self.fetched.append(advisory_id)
        if advisory_id in self._failures:
            raise sb.AdvisoryDataError(self._failures[advisory_id])
        if advisory_id not in self._held:
            raise sb.AdvisoryDataError("HTTP Error 404: Not Found")
        try:
            record = json.loads(self._held[advisory_id])
        except ValueError:
            raise sb.AdvisoryDataError("the body is not JSON") from None
        if not isinstance(record, dict):
            raise sb.AdvisoryDataError("the body is not a JSON object")
        return record


class FakeClock:
    def __init__(self, today: datetime.date) -> None:
        self._today = today

    def today(self) -> datetime.date:
        return self._today
