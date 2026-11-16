#!/usr/bin/env python3
"""The bookkeeping of a dependency-security run, as seven subcommands.

WHY THIS EXISTS: the Senior Engineer's security review and dependency repair kept the exception
record, the lapse dates and the upkeep register by hand, and a hand-written entry is how a
`window` key got into a record that was measured to hold none. This tool computes and records;
it decides nothing. It names no provider, model or agent, and behaves the same under every one.

Everything the domain reaches the machine through arrives handed in: `Files`, `Advisories` and
`Clock` are plain classes whose bodies are the real adapters, and `build_bookkeeping()` is the
one place they are built.
"""

from __future__ import annotations

import argparse
import datetime
import http.client
import json
import os
import re
import sys
import tempfile
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import TextIO

__version__ = "1.1.0"

ADVISORY_REQUEST_TIMEOUT_SECONDS = 20
ADVISORY_SERVICE_BASE_URL = "https://api.osv.dev/v1/vulns/"
MESSAGE_PREFIX = "security_bookkeeping: "
VERDICT_VALUES = {
    "Security": ("clean", "fixed", "reported", "stopped"),
    "Repair": ("unmerged", "stopped", "merged"),
}
_BARE_VERDICT_LINE = re.compile(r"^(Security|Repair): ([a-z]+)$")
SEVERITIES = ("Critical", "High", "Medium", "Low", "unscored")
DEFAULT_WINDOW_DAYS = {"Critical": 7, "unscored": 7, "High": 30, "Medium": 30, "Low": 30}
NORMALISED_KEYS = ("advisory", "package", "version", "severity", "fixed", "published")
_SEVERITY_NAMES = "Critical, High, Medium, Low or unscored"
_CALENDAR_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_WHOLE_NUMBER = re.compile(r"[0-9]+")
_MAX_WINDOW_DAYS = datetime.timedelta.max.days
_EXCEPTION_HEADER = re.compile(
    r"^[ \t]*\[\[[ \t]*exception[ \t]*\]\][ \t]*(?:#[^\r\n]*)?\r?$", re.MULTILINE
)
_RENEWAL_HEADER = re.compile(
    r"^[ \t]*\[\[[ \t]*exception[ \t]*\.[ \t]*renewal[ \t]*\]\][ \t]*(?:#[^\r\n]*)?\r?$",
    re.MULTILINE,
)
_BASIC_STRING_ESCAPES = {
    "\\": "\\\\", '"': '\\"', "\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f", "\r": "\\r",
}
UPKEEP_HEADER_ROW = (
    "| Task | Rule it serves | Cadence | Last done | Next due | What reminds the owner |"
)
UPKEEP_SEPARATOR_ROW = "|---|---|---|---|---|---|"
UPKEEP_REGISTER_INTRO = (
    "# Upkeep register\n\n"
    "The rule for this register, what it holds and what each row says, is "
    "`<CORE>/doctrine/setup/kensaiapp_structure.md` \u00a7 App-level, at the "
    "`system/upkeep.md` entry.\n\n"
)
RATING_RANKS = {
    "critical": "Critical", "high": "High", "moderate": "Medium", "medium": "Medium", "low": "Low",
}
UNRATED = "unscored"
PUBLISHED_DATE_LENGTH = 10
AUDIT_ERROR_PREFIX = "error:"
AUDIT_ADVISORY_INFORMATION = "Advisory information:"
_AUDIT_SUMMARY_LINE = re.compile(
    r"^Found (no|[0-9]+) known vulnerabilit(?:y|ies)"
    r"(?: and (no|[0-9]+) adverse project status(?:es)?)? in [0-9]+ packages?$"
)
_AUDIT_PACKAGE_HEADING = re.compile(r"^(\S+) (\S+) has [0-9]+ known vulnerabilit(?:y|ies):$")
_AUDIT_ADVISORY_LINE = re.compile(r"^- (\S+): ")
_AUDIT_FIXED_LINE = re.compile(r"^\s+Fixed in: (.+)$")
_UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")
_SEPARATOR_LINE = re.compile(r"^\|(?:\s*:?-+:?\s*\|){6}\s*$")
_PACKAGE_NAME_SEPARATORS = re.compile(r"[-_.]+")
RECORD_ENTRY_KEYS = ("advisory", "distribution", "published", "reason")
RECORD_RENEWAL_KEYS = ("on", "reason")


class BookkeepingRefusal(Exception):
    """A job refused its input. `run`, the entry point, converts it to a message on standard
    error and exit status 1; no job prints or changes a file once it has raised this."""


class Reader(str, Enum):
    """Which program printed the two streams `normalise` reads. The value is the spelling the
    command line gives it."""

    UV_AUDIT = "uv-audit"
    OSV_SCANNER = "osv-scanner"


@dataclass(frozen=True)
class Outcome:
    """What a job that succeeded gives back: the text for standard output, and any note for
    standard error."""

    stdout: str
    note: str = ""


class AdvisoryDataError(Exception):
    """The advisory data service gave no readable record. The domain turns it into a refusal
    that names the advisory."""


class FileAccessError(Exception):
    """A path could not be read as UTF-8 text, or could not be written. The domain turns it into
    a refusal that names the path."""


class Files:
    """Reads and writes whole files as UTF-8 text with no newline translation."""

    def read_text(self, path: str) -> str | None:
        """The text at `path`, or None when the path has no file."""
        try:
            with open(path, encoding="utf-8", newline="") as handle:
                return handle.read()
        except FileNotFoundError:
            return None
        except (OSError, UnicodeDecodeError) as error:
            raise FileAccessError(str(error)) from None

    def write_text(self, path: str, text: str) -> None:
        """Replace the file at `path` with `text` atomically, making the parent folder."""
        target = Path(path)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary = tempfile.mkstemp(dir=target.parent, prefix=".bookkeeping-")
        except OSError as error:
            raise FileAccessError(str(error)) from None
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
                handle.write(text)
            os.replace(temporary, target)
        except OSError as error:
            Path(temporary).unlink(missing_ok=True)
            raise FileAccessError(str(error)) from None
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise


class Advisories:
    """Fetches one advisory's published record from the service at `base_url`."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url

    def fetch(self, advisory_id: str) -> dict:
        """The record the service publishes for `advisory_id`, as its JSON object."""
        url = self._base_url + urllib.parse.quote(advisory_id, safe="")
        try:
            with urllib.request.urlopen(url, timeout=ADVISORY_REQUEST_TIMEOUT_SECONDS) as reply:
                body = reply.read()
            record = json.loads(body)
        except urllib.error.HTTPError as error:
            raise AdvisoryDataError(str(error)) from None
        except urllib.error.URLError as error:
            raise AdvisoryDataError(str(error.reason)) from None
        except (TimeoutError, OSError) as error:
            raise AdvisoryDataError(str(error) or "timed out") from None
        except http.client.HTTPException as error:
            # A reply cut short or malformed is not an OSError, and is still no readable record.
            raise AdvisoryDataError(repr(error)) from None
        except ValueError as error:
            raise AdvisoryDataError(f"the body is not JSON: {error}") from None
        if not isinstance(record, dict):
            raise AdvisoryDataError("the body is not a JSON object")
        return record


class Clock:
    """Today's date on the machine's local calendar."""

    def today(self) -> datetime.date:
        return datetime.date.today()


@dataclass(frozen=True)
class Renewal:
    on: datetime.date
    reason: str


@dataclass(frozen=True)
class RecordEntry:
    advisory: str
    distribution: str
    published: datetime.date
    reason: str
    renewals: tuple[Renewal, ...]

    def as_json_object(self) -> dict:
        return {
            "advisory": self.advisory,
            "distribution": self.distribution,
            "published": self.published.isoformat(),
            "reason": self.reason,
            "renewals": [
                {"on": renewal.on.isoformat(), "reason": renewal.reason}
                for renewal in self.renewals
            ],
        }


def _is_bare_date(value: object) -> bool:
    # A date-time subclasses date, so an isinstance test would let one through.
    return type(value) is datetime.date


def _check_renewal(path: str, entry_name: str, position: int, table: object) -> Renewal:
    where = f"{path}, entry {entry_name}, renewal {position}"
    if not isinstance(table, dict):
        raise BookkeepingRefusal(f'{where}: no "on" key.')
    for key in RECORD_RENEWAL_KEYS:
        if key not in table:
            raise BookkeepingRefusal(f'{where}: no "{key}" key.')
    for key in table:
        if key not in RECORD_RENEWAL_KEYS:
            raise BookkeepingRefusal(f'{where}: the key "{key}" is not in the record\'s shape.')
    if not isinstance(table["reason"], str):
        raise BookkeepingRefusal(f'{where}: "reason" is not a string.')
    if not _is_bare_date(table["on"]):
        raise BookkeepingRefusal(
            f'{where}: "on" is not a bare TOML date, written YYYY-MM-DD with no quotes and no time.'
        )
    return Renewal(table["on"], table["reason"])


def _check_entry(path: str, position: int, table: object) -> RecordEntry:
    name = str(position)
    if isinstance(table, dict) and isinstance(table.get("advisory"), str):
        name = table["advisory"]
    where = f"{path}, entry {name}"
    if not isinstance(table, dict):
        raise BookkeepingRefusal(f'{where}: no "advisory" key.')
    for key in RECORD_ENTRY_KEYS:
        if key not in table:
            raise BookkeepingRefusal(f'{where}: no "{key}" key.')
    for key in table:
        if key not in (*RECORD_ENTRY_KEYS, "renewal"):
            raise BookkeepingRefusal(f'{where}: the key "{key}" is not in the record\'s shape.')
    for key in ("advisory", "distribution", "reason"):
        if not isinstance(table[key], str):
            raise BookkeepingRefusal(f'{where}: "{key}" is not a string.')
    if not _is_bare_date(table["published"]):
        raise BookkeepingRefusal(
            f'{where}: "published" is not a bare TOML date, written YYYY-MM-DD with no quotes '
            "and no time."
        )
    tables = table.get("renewal", [])
    if not isinstance(tables, list):
        raise BookkeepingRefusal(f'{where}: the key "renewal" is not in the record\'s shape.')
    renewals = tuple(
        _check_renewal(path, name, index, renewal) for index, renewal in enumerate(tables, 1)
    )
    return RecordEntry(
        table["advisory"], table["distribution"], table["published"], table["reason"], renewals
    )


def parse_record(path: str, text: str) -> list[RecordEntry]:
    """The entries of the exception record at `path`, in file order, or a refusal naming the
    first entry and key that depart from the measured shape."""
    try:
        document = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise BookkeepingRefusal(f"{path} is not valid TOML: {error}") from None
    for key in document:
        if key != "exception":
            raise BookkeepingRefusal(
                f'{path} holds the top-level key "{key}", and the record holds only '
                "[[exception]] tables."
            )
    tables = document.get("exception", [])
    if not isinstance(tables, list):
        raise BookkeepingRefusal(f'{path}: "exception" is not a list of [[exception]] tables.')
    entries: list[RecordEntry] = []
    for position, table in enumerate(tables, 1):
        entry = _check_entry(path, position, table)
        if any(held.advisory == entry.advisory for held in entries):
            raise BookkeepingRefusal(
                f"{path} holds two entries for {entry.advisory}, and the record holds one per "
                "advisory."
            )
        entries.append(entry)
    return entries


def _json_text(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def calendar_date(text: object) -> datetime.date | None:
    """The date `text` spells as YYYY-MM-DD, or None when it is not a real calendar date."""
    # The pattern comes first: from 3.11 the standard parser also accepts other spellings.
    if not isinstance(text, str) or _CALENDAR_DATE.fullmatch(text) is None:
        return None
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        return None


@dataclass(frozen=True)
class Window:
    """The days each severity is given before an exception lapses: the owner's default, or the
    counts a product's NFDR names and the caller passed in."""

    given: dict[str, int] | None = None

    @classmethod
    def parse(cls, values: Sequence[str] | None) -> Window:
        if not values:
            return cls()
        given: dict[str, int] = {}
        for value in values:
            severity, separator, count = value.partition("=")
            if not separator:
                raise BookkeepingRefusal(f"--window {value} is not written as Severity=days.")
            if severity not in SEVERITIES:
                raise BookkeepingRefusal(
                    f'--window names the severity "{severity}", which is not {_SEVERITY_NAMES}.'
                )
            digits = count.lstrip("0")
            if _WHOLE_NUMBER.fullmatch(count) is None or not digits:
                raise BookkeepingRefusal(
                    f"--window gives {severity} the count {count}, which is not a positive "
                    "whole number of days."
                )
            # The length is checked before int(): Python refuses to read a whole number of more
            # than 4,300 digits, and a day difference holds no more than _MAX_WINDOW_DAYS.
            if len(digits) > len(str(_MAX_WINDOW_DAYS)) or int(digits) > _MAX_WINDOW_DAYS:
                raise BookkeepingRefusal(
                    f"--window gives {severity} the count {count}, which runs past the last date "
                    "the calendar holds."
                )
            if severity in given:
                raise BookkeepingRefusal(f"--window names {severity} twice.")
            given[severity] = int(count)
        return cls(given)

    @property
    def label(self) -> str:
        return "default" if self.given is None else "given"

    def days_for(self, severity: str, advisory: str) -> int:
        if self.given is None:
            return DEFAULT_WINDOW_DAYS[severity]
        if severity not in self.given:
            raise BookkeepingRefusal(
                f"the window given has no count for {severity}, the severity of {advisory}."
            )
        return self.given[severity]


@dataclass(frozen=True)
class ListedAdvisory:
    """The part of one object of `normalise`'s list that a lapse date needs."""

    advisory: str
    severity: str
    published: datetime.date


def read_listed_advisory(obj: object) -> ListedAdvisory:
    """One object of `normalise`'s list, checked whole, or a refusal naming the advisory."""
    if not isinstance(obj, dict):
        raise BookkeepingRefusal("--entry is not a JSON object.")
    if "advisory" not in obj:
        raise BookkeepingRefusal('the entry has no "advisory" key.')
    advisory = str(obj["advisory"])
    for key in NORMALISED_KEYS:
        if key not in obj:
            raise BookkeepingRefusal(f'the entry for {advisory} has no "{key}" key.')
    if obj["published"] is None:
        raise BookkeepingRefusal(
            f'the entry for {advisory} has no publication date: "published" is null.'
        )
    published = calendar_date(obj["published"])
    if published is None:
        raise BookkeepingRefusal(
            f"the entry for {advisory} has the publication date {obj['published']}, which is "
            "not a real calendar date written YYYY-MM-DD."
        )
    if obj["severity"] not in SEVERITIES:
        raise BookkeepingRefusal(
            f'the entry for {advisory} has the severity "{obj["severity"]}", which is not '
            f"{_SEVERITY_NAMES}."
        )
    return ListedAdvisory(advisory, obj["severity"], published)


@dataclass(frozen=True)
class Lapse:
    advisory: str
    lapses: datetime.date
    start: datetime.date
    days: int
    window: str

    def as_json_object(self) -> dict:
        return {
            "advisory": self.advisory,
            "lapses": self.lapses.isoformat(),
            "from": self.start.isoformat(),
            "days": self.days,
            "window": self.window,
        }


def compute_lapse(
    listed: ListedAdvisory, renewals: Sequence[Renewal], window: Window
) -> Lapse:
    """The date `listed`'s window lapses, counted from its publication or, where the record
    holds renewals for it, from the greatest renewal date wherever it sits in the file."""
    start = max((renewal.on for renewal in renewals), default=listed.published)
    days = window.days_for(listed.severity, listed.advisory)
    try:
        lapses = start + datetime.timedelta(days=days)
    except OverflowError:
        raise BookkeepingRefusal(
            f"the window gives {listed.advisory} {days} days from {start.isoformat()}, which runs "
            "past the last date the calendar holds."
        ) from None
    return Lapse(listed.advisory, lapses, start, days, window.label)


def _toml_basic_string(text: str) -> str:
    """`text` as one-line TOML basic string: the standard escapes, \\uXXXX for every other
    control character and DEL, and non-ASCII characters as themselves."""
    pieces = []
    for character in text:
        if character in _BASIC_STRING_ESCAPES:
            pieces.append(_BASIC_STRING_ESCAPES[character])
        elif ord(character) < 0x20 or ord(character) == 0x7F:
            pieces.append(f"\\u{ord(character):04X}")
        else:
            pieces.append(character)
    return '"' + "".join(pieces) + '"'


def _line_ending(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def _require_filled(**options: str) -> None:
    for option, value in options.items():
        if not value.strip():
            raise BookkeepingRefusal(f"--{option} is empty.")


def _require_date(option: str, value: str) -> datetime.date:
    parsed = calendar_date(value)
    if parsed is None:
        raise BookkeepingRefusal(
            f"--{option} {value} is not a real calendar date written YYYY-MM-DD."
        )
    return parsed


def _render_entry(newline: str, advisory: str, distribution: str, published: str, reason: str):
    lines = [
        "[[exception]]",
        f"advisory = {_toml_basic_string(advisory)}",
        f"distribution = {_toml_basic_string(distribution)}",
        f"published = {published}",
        f"reason = {_toml_basic_string(reason)}",
    ]
    return newline.join(lines) + newline


def _render_renewal(newline: str, on: str, reason: str) -> str:
    lines = ["[[exception.renewal]]", f"on = {on}", f"reason = {_toml_basic_string(reason)}"]
    return newline.join(lines) + newline


def _append_table(old: str, table: str, newline: str) -> str:
    """`table` after the old bytes, with a blank line between it and the table before it."""
    if not old:
        return table
    ending = ""
    if not old.endswith("\n"):
        ending += newline
    if not old.endswith(newline * 2):
        ending += newline
    return old + ending + table


def _require_entry_tables(path: str, old: str, entries: list[RecordEntry]) -> None:
    """Refuse a record whose entries are not all `[[exception]]` tables. The TOML reader returns
    an inline array of entries the same way, and a table appended after one is not valid TOML."""
    if len(_EXCEPTION_HEADER.findall(old)) < len(entries):
        raise BookkeepingRefusal(f'{path}: "exception" is not a list of [[exception]] tables.')


def _insert_renewal(path: str, old: str, entries: list[RecordEntry], advisory: str, table: str,
                    newline: str) -> str:
    """`table` placed after the target entry's last table and before the next entry header."""
    headers = [match.start() for match in _EXCEPTION_HEADER.finditer(old)]
    if len(headers) != len(entries):
        raise BookkeepingRefusal(
            f"{path} has {len(headers)} [[exception]] header lines and {len(entries)} entries, "
            "so the tool cannot tell where the renewal goes."
        )
    index = next(i for i, entry in enumerate(entries) if entry.advisory == advisory)
    cut = headers[index + 1] if index + 1 < len(headers) else len(old)
    # The TOML reader returns an inline array of renewals the same way as [[exception.renewal]]
    # tables, and a renewal table appended after an inline array is not valid TOML.
    renewal_headers = _RENEWAL_HEADER.findall(old, headers[index], cut)
    if len(renewal_headers) < len(entries[index].renewals):
        raise BookkeepingRefusal(
            f'{path}, entry {advisory}: the key "renewal" is not in the record\'s shape.'
        )
    before, after = old[:cut], old[cut:]
    lead = ""
    if before and not before.endswith("\n"):
        lead += newline
    if before and not before.endswith(newline * 2):
        lead += newline
    return before + lead + table + (newline if after else "") + after


def _upkeep_cell(value: str) -> str:
    return value.replace("|", "\\|")


def _rule_cell_of(row: str) -> str:
    cells = _UNESCAPED_PIPE.split(row)
    return cells[2].strip() if len(cells) > 2 else ""


def _place_upkeep_row(path: str, old: str, row: str, rule_cell: str) -> tuple[str, str]:
    """The register's new text and the confirmation word (`written` or `replaced`)."""
    newline = _line_ending(old)
    lines = old.splitlines(keepends=True)
    header = next((i for i, line in enumerate(lines) if line.rstrip() == UPKEEP_HEADER_ROW), None)
    if header is None:
        raise BookkeepingRefusal(f'{path} has no header row "{UPKEEP_HEADER_ROW}".')
    if header + 1 >= len(lines) or _SEPARATOR_LINE.match(lines[header + 1].rstrip()) is None:
        raise BookkeepingRefusal(
            f"{path}: the line after the header row is not the table's six-cell separator."
        )
    end = header + 2
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    matching = [
        i for i in range(header + 2, end) if _rule_cell_of(lines[i].rstrip("\r\n")) == rule_cell
    ]
    if len(matching) > 1:
        raise BookkeepingRefusal(
            f'{path} holds {len(matching)} rows whose "Rule it serves" cell is "{rule_cell}", '
            "so the tool cannot tell which one to replace."
        )
    if matching:
        kept_ending = lines[matching[0]][len(lines[matching[0]].rstrip("\r\n")) :]
        lines[matching[0]] = row + kept_ending
        return "".join(lines), "replaced"
    if end > 0 and not lines[end - 1].endswith("\n"):
        lines[end - 1] += newline
    lines.insert(end, row + newline)
    return "".join(lines), "written"


@dataclass(frozen=True)
class PrintedAdvisory:
    """One advisory as uv's audit printed it: the id, the package heading it sat under, and the
    `Fixed in:` value as printed (None where it printed none). Severity and date are not in
    uv's text."""

    advisory: str
    package: str
    version: str
    fixed: str | None


@dataclass(frozen=True)
class AuditReading:
    """What a finished uv audit or osv-scanner scan holds: its advisories in printed order, and
    how many adverse project statuses uv's summary counted (a status is not an advisory and is
    not listed; a scan reports none)."""

    advisories: tuple[PrintedAdvisory, ...]
    adverse_statuses: int


def _summary_count(word: str) -> int:
    return 0 if word == "no" else int(word)


def parse_audit(stdout_text: str, stderr_text: str) -> AuditReading:
    """Read the text uv's audit printed, standard output then standard error as one line
    sequence, or refuse input that is not a finished uv audit."""
    lines = stdout_text.splitlines() + stderr_text.splitlines()
    if not any(line.strip() for line in lines):
        raise BookkeepingRefusal(
            "both audit output files are empty, so there is no audit output to read."
        )
    error_line = next((line for line in lines if line.startswith(AUDIT_ERROR_PREFIX)), None)
    if error_line is not None:
        raise BookkeepingRefusal(
            f"the audit printed an error, and the output of a failed audit is not read: "
            f"{error_line}"
        )
    summary = None
    advisories: list[PrintedAdvisory] = []
    heading: tuple[str, str] | None = None
    for line in lines:
        text = line.rstrip()
        summary_match = _AUDIT_SUMMARY_LINE.match(text)
        if summary_match is not None:
            summary = summary if summary is not None else summary_match
            heading = None
            continue
        heading_match = _AUDIT_PACKAGE_HEADING.match(text)
        if heading_match is not None:
            heading = (heading_match.group(1), heading_match.group(2))
            continue
        if heading is None or not text.strip():
            continue
        advisory_match = _AUDIT_ADVISORY_LINE.match(text)
        fixed_match = _AUDIT_FIXED_LINE.match(text)
        if advisory_match is not None:
            advisories.append(PrintedAdvisory(advisory_match.group(1), *heading, None))
        elif fixed_match is not None and advisories:
            advisories[-1] = replace(advisories[-1], fixed=fixed_match.group(1))
        elif not text.lstrip().startswith(AUDIT_ADVISORY_INFORMATION):
            heading = None
    if summary is None:
        raise BookkeepingRefusal(
            'the audit output has no summary line "Found ... known vulnerabilities", so it '
            "cannot be read as a finished uv audit."
        )
    counted = _summary_count(summary.group(1))
    if counted != len(advisories):
        raise BookkeepingRefusal(
            f"the audit's summary counts {counted} known vulnerabilities, and its output "
            f"lists {len(advisories)} advisories."
        )
    adverse = _summary_count(summary.group(2) or "no")
    return AuditReading(tuple(advisories), adverse)


_NOT_A_SCAN = "so it cannot be read as a finished osv-scanner scan"
_NOT_A_SCAN_OUTPUT = "so the output cannot be read as a finished osv-scanner scan"


class _UnreadableAffectedData(Exception):
    """A vulnerability's `affected` data is present and is not in the shape a scan prints."""


def _normalised_package_name(name: str) -> str:
    """PEP 503: lowercase, each run of `-`, `_` or `.` becoming one `-`."""
    return _PACKAGE_NAME_SEPARATORS.sub("-", name).lower()


def _require_kind(value: object, kind: type) -> None:
    if not isinstance(value, kind):
        raise _UnreadableAffectedData


def _fixed_releases(vulnerability: dict, package_name: str) -> str | None:
    """The `fixed` events of the vulnerability's `affected` entries for `package_name`, without
    repeats and in data order, joined with `, `; None when there are none. Every entry is
    checked, the ones for other packages included."""
    wanted = _normalised_package_name(package_name)
    releases: list[str] = []
    affected = vulnerability.get("affected", [])
    _require_kind(affected, list)
    for entry in affected:
        _require_kind(entry, dict)
        package = entry.get("package", {})
        _require_kind(package, dict)
        is_for_package = isinstance(package.get("name"), str) and (
            _normalised_package_name(package["name"]) == wanted
        )
        ranges = entry.get("ranges", [])
        _require_kind(ranges, list)
        for version_range in ranges:
            _require_kind(version_range, dict)
            events = version_range.get("events", [])
            _require_kind(events, list)
            for event in events:
                _require_kind(event, dict)
                if "fixed" in event:
                    _require_kind(event["fixed"], str)
                    if is_for_package:
                        releases.append(event["fixed"])
    return ", ".join(dict.fromkeys(releases)) or None


def parse_osv_scan(stdout_text: str) -> AuditReading:
    """Read the standard output of `osv-scanner scan source --format json`, or refuse text that is
    not a finished scan. Standard error holds only progress lines and is not read. One advisory
    for each distinct (id, package, version), in the order the scan printed them."""
    if not stdout_text.strip():
        raise BookkeepingRefusal(
            "the scan's standard output is empty, so there is no osv-scanner scan to read."
        )
    try:
        document = json.loads(stdout_text)
    except ValueError as error:
        raise BookkeepingRefusal(
            f"the scan's standard output is not JSON, {_NOT_A_SCAN}: {error}"
        ) from None
    results = document.get("results") if isinstance(document, dict) else None
    if not isinstance(results, list):
        raise BookkeepingRefusal(
            "the scan's standard output is not a JSON object with a \"results\" list, "
            f"{_NOT_A_SCAN}."
        )
    advisories: dict[tuple[str, str, str], PrintedAdvisory] = {}
    for result_number, result in enumerate(results, 1):
        packages = result.get("packages") if isinstance(result, dict) else None
        if not isinstance(packages, list):
            raise BookkeepingRefusal(
                f'result {result_number} of the scan has no "packages" list, {_NOT_A_SCAN_OUTPUT}.'
            )
        for package_number, entry in enumerate(packages, 1):
            where = f"package {package_number} of result {result_number}"
            package = entry.get("package") if isinstance(entry, dict) else None
            name = package.get("name") if isinstance(package, dict) else None
            version = package.get("version") if isinstance(package, dict) else None
            if not isinstance(name, str) or not isinstance(version, str):
                raise BookkeepingRefusal(
                    f"{where} does not give the package's name and version as text, "
                    f"{_NOT_A_SCAN_OUTPUT}."
                )
            vulnerabilities = entry.get("vulnerabilities")
            if not isinstance(vulnerabilities, list):
                raise BookkeepingRefusal(
                    f'{where} has no "vulnerabilities" list, {_NOT_A_SCAN_OUTPUT}.'
                )
            for vulnerability_number, vulnerability in enumerate(vulnerabilities, 1):
                vulnerability_where = (
                    f"vulnerability {vulnerability_number} of package {package_number} "
                    f"in result {result_number}"
                )
                advisory = vulnerability.get("id") if isinstance(vulnerability, dict) else None
                if not isinstance(advisory, str):
                    raise BookkeepingRefusal(
                        f'{vulnerability_where} has no "id" as text, {_NOT_A_SCAN_OUTPUT}.'
                    )
                try:
                    fixed = _fixed_releases(vulnerability, name)
                except _UnreadableAffectedData:
                    raise BookkeepingRefusal(
                        f'{vulnerability_where} has "affected" data the tool cannot read, '
                        f"{_NOT_A_SCAN_OUTPUT}."
                    ) from None
                advisories.setdefault(
                    (advisory, name, version), PrintedAdvisory(advisory, name, version, fixed)
                )
    return AuditReading(tuple(advisories.values()), 0)


def rank_of_record(advisory: str, record: dict) -> str:
    """The advisory's own severity from its published data: the named rating first, a score
    vector alone refused, and no rating at all `unscored`. No vector is scored here."""
    specific = record.get("database_specific")
    rating = specific.get("severity") if isinstance(specific, dict) else None
    if rating is not None:
        rank = RATING_RANKS.get(rating.lower()) if isinstance(rating, str) else None
        if rank is None:
            raise BookkeepingRefusal(
                f'the published data rates {advisory} "{rating}", which the tool cannot place '
                "on Critical, High, Medium or Low."
            )
        return rank
    vectors = record.get("severity")
    if isinstance(vectors, list) and vectors:
        raise BookkeepingRefusal(
            f"the published data rates {advisory} only by a score vector, and the tool does not "
            "turn a vector into Critical, High, Medium or Low."
        )
    return UNRATED


def published_date_of_record(advisory: str, record: dict) -> datetime.date:
    """The day the advisory's data says it was published, or a refusal naming the advisory."""
    value = record.get("published")
    day = calendar_date(value[:PUBLISHED_DATE_LENGTH]) if isinstance(value, str) else None
    if day is None:
        raise BookkeepingRefusal(
            f"the published data for {advisory} carries no publication date the tool can read."
        )
    return day


def adverse_status_note(count: int) -> str:
    if count == 0:
        return ""
    if count == 1:
        return (
            f"{MESSAGE_PREFIX}the audit reported 1 adverse project status. It is not an "
            "advisory and is not in the list.\n"
        )
    return (
        f"{MESSAGE_PREFIX}the audit reported {count} adverse project statuses. They are not "
        "advisories and are not in the list.\n"
    )


class Bookkeeping:
    """The seven jobs, one method each, over the three ports it is handed."""

    def __init__(self, *, files: Files, advisories: Advisories, clock: Clock) -> None:
        self._files = files
        self._advisories = advisories
        self._clock = clock

    def _read_text(self, path: str) -> str | None:
        try:
            return self._files.read_text(path)
        except FileAccessError as error:
            raise BookkeepingRefusal(f"cannot read {path}: {error}") from None

    def _write_text(self, path: str, text: str) -> None:
        try:
            self._files.write_text(path, text)
        except FileAccessError as error:
            raise BookkeepingRefusal(f"cannot write {path}: {error}") from None

    def _read_required(self, path: str) -> str:
        text = self._read_text(path)
        if text is None:
            raise BookkeepingRefusal(f"there is no file at {path}.")
        return text

    def _read_record(self, path: str) -> list[RecordEntry]:
        """The record's entries, shape-checked; a path with no file holds none."""
        text = self._read_text(path)
        return [] if text is None else parse_record(path, text)

    def _fetch_advisory_record(self, advisory: str) -> dict:
        try:
            return self._advisories.fetch(advisory)
        except AdvisoryDataError as error:
            raise BookkeepingRefusal(
                f"cannot read the published data for {advisory}: {error}"
            ) from None

    def normalise(self, stdout_path: str, stderr_path: str, reader: Reader) -> Outcome:
        stdout_text = self._read_required(stdout_path)
        stderr_text = self._read_required(stderr_path)
        if reader is Reader.OSV_SCANNER:
            reading = parse_osv_scan(stdout_text)
        else:
            reading = parse_audit(stdout_text, stderr_text)
        records: dict[str, dict] = {}
        listed = []
        for printed in reading.advisories:
            if printed.advisory not in records:
                records[printed.advisory] = self._fetch_advisory_record(printed.advisory)
            record = records[printed.advisory]
            listed.append(
                {
                    "advisory": printed.advisory,
                    "package": printed.package,
                    "version": printed.version,
                    "severity": rank_of_record(printed.advisory, record),
                    "fixed": printed.fixed,
                    "published": published_date_of_record(printed.advisory, record).isoformat(),
                }
            )
        return Outcome(_json_text(listed), adverse_status_note(reading.adverse_statuses))

    def read_record(self, record_path: str) -> Outcome:
        entries = self._read_record(record_path)
        return Outcome(_json_text([entry.as_json_object() for entry in entries]))

    def lapse_date(
        self, entry_text: str, record_path: str | None, window_values: Sequence[str] | None
    ) -> Outcome:
        try:
            obj = json.loads(entry_text)
        except ValueError:
            raise BookkeepingRefusal("--entry is not a JSON object.") from None
        listed = read_listed_advisory(obj)
        window = Window.parse(window_values)
        entries = [] if record_path is None else self._read_record(record_path)
        renewals = next(
            (entry.renewals for entry in entries if entry.advisory == listed.advisory), ()
        )
        return Outcome(_json_text(compute_lapse(listed, renewals, window).as_json_object()))

    def write_entry(
        self, record_path: str, advisory: str, distribution: str, published: str, reason: str
    ) -> Outcome:
        _require_filled(
            record=record_path, advisory=advisory, distribution=distribution,
            published=published, reason=reason,
        )
        published_on = _require_date("published", published)
        old = self._read_text(record_path)
        entries = [] if old is None else parse_record(record_path, old)
        if any(entry.advisory == advisory for entry in entries):
            raise BookkeepingRefusal(f"{record_path} already holds an entry for {advisory}.")
        _require_entry_tables(record_path, old or "", entries)
        newline = _line_ending(old or "")
        table = _render_entry(newline, advisory, distribution, published_on.isoformat(), reason)
        self._write_text(record_path, _append_table(old or "", table, newline))
        created = f"record created: {record_path}\n" if old is None else ""
        return Outcome(f"{created}entry written: {advisory}\n")

    def write_renewal(self, record_path: str, advisory: str, on: str, reason: str) -> Outcome:
        _require_filled(record=record_path, advisory=advisory, on=on, reason=reason)
        renewed_on = _require_date("on", on)
        old = self._read_text(record_path)
        if old is None:
            raise BookkeepingRefusal(
                f"there is no record at {record_path}, so it holds no entry for {advisory}."
            )
        entries = parse_record(record_path, old)
        if not any(entry.advisory == advisory for entry in entries):
            raise BookkeepingRefusal(f"{record_path} holds no entry for {advisory}.")
        newline = _line_ending(old)
        table = _render_renewal(newline, renewed_on.isoformat(), reason)
        self._write_text(
            record_path, _insert_renewal(record_path, old, entries, advisory, table, newline)
        )
        return Outcome(f"renewal written: {advisory} on {renewed_on.isoformat()}\n")

    def _read_advisory_list(self, list_path: str) -> list[dict]:
        """`normalise`'s saved output, checked to be a list of objects naming an advisory."""
        text = self._read_required(list_path)
        refusal = BookkeepingRefusal(
            f"{list_path} does not hold a JSON list in the shape normalise prints."
        )
        try:
            listing = json.loads(text)
        except ValueError:
            raise refusal from None
        if not isinstance(listing, list) or not all(
            isinstance(item, dict) and "advisory" in item for item in listing
        ):
            raise refusal
        return listing

    def find_lapsed(
        self,
        record_path: str,
        list_path: str,
        window_values: Sequence[str] | None,
        date_text: str | None,
    ) -> Outcome:
        window = Window.parse(window_values)
        deciding_date = (
            self._clock.today() if date_text is None else _require_date("date", date_text)
        )
        listing = self._read_advisory_list(list_path)
        entries = self._read_record(record_path)
        # Objects sharing an id carry the same severity and date, so the first one answers.
        first_with_id: dict[str, dict] = {}
        for obj in listing:
            first_with_id.setdefault(str(obj["advisory"]), obj)
        groups: dict[str, list[dict]] = {"lapsed": [], "holding": [], "unreported": []}
        for entry in entries:
            obj = first_with_id.get(entry.advisory)
            item = {"advisory": entry.advisory, "distribution": entry.distribution}
            if obj is None:
                groups["unreported"].append(item)
                continue
            lapse = compute_lapse(read_listed_advisory(obj), entry.renewals, window)
            item["lapses"] = lapse.lapses.isoformat()
            groups["lapsed" if lapse.lapses <= deciding_date else "holding"].append(item)
        return Outcome(_json_text(groups))

    def write_upkeep(
        self, register_path: str, cells: dict[str, str]
    ) -> Outcome:
        for option, value in cells.items():
            if not value.strip():
                raise BookkeepingRefusal(f"--{option} is empty.")
            if "\n" in value or "\r" in value:
                raise BookkeepingRefusal(
                    f"--{option} holds a line break, and a cell of the register must sit on one "
                    "line."
                )
        _require_filled(register=register_path)
        rule = cells["rule"]
        row = "| " + " | ".join(_upkeep_cell(value) for value in cells.values()) + " |"
        old = self._read_text(register_path)
        if old is None:
            text = UPKEEP_REGISTER_INTRO + f"{UPKEEP_HEADER_ROW}\n{UPKEEP_SEPARATOR_ROW}\n{row}\n"
            self._write_text(register_path, text)
            return Outcome(f"register created: {register_path}\nrow written: {rule}\n")
        text, word = _place_upkeep_row(register_path, old, row, _upkeep_cell(rule).strip())
        self._write_text(register_path, text)
        return Outcome(f"row {word}: {rule}\n")

    def check_verdict(self, report_path: str) -> Outcome:
        lines = self._read_required(report_path).splitlines()
        if not lines or not lines[0].startswith("# "):
            raise BookkeepingRefusal(
                f'{report_path} has no title: its first line does not begin "# ".'
            )
        verdict = next((line for line in lines[1:] if line.strip()), None)
        if verdict is None:
            raise BookkeepingRefusal(
                f"{report_path} has no verdict line: nothing but blank lines follows the title."
            )
        match = _BARE_VERDICT_LINE.match(verdict)
        if match is None:
            raise BookkeepingRefusal(
                f'{report_path}: the verdict line "{verdict}" is not bare. A verdict line reads '
                'exactly "Security: <value>" or "Repair: <value>", with nothing before or after it.'
            )
        kind, value = match.groups()
        allowed = VERDICT_VALUES[kind]
        if value not in allowed:
            names = ", ".join(allowed[:-1]) + " or " + allowed[-1]
            raise BookkeepingRefusal(
                f'{report_path}: "{value}" is not a {kind} verdict. A {kind} verdict is {names}.'
            )
        return Outcome(verdict + "\n")


# ---------------------------------------------------------------------------------------------
# The entry layer
# ---------------------------------------------------------------------------------------------


class _UsageExit(Exception):
    """The parser finished the run itself: a help request (status 0) or a rejected argument
    (status 2)."""

    def __init__(self, status: int) -> None:
        super().__init__(status)
        self.status = status


class _Parser(argparse.ArgumentParser):
    """An argument parser that writes to the streams it is handed and never exits the process."""

    def __init__(self, *args, streams: tuple[TextIO, TextIO], **kwargs) -> None:
        self._streams = streams
        super().__init__(*args, **kwargs)

    @property
    def streams(self) -> tuple[TextIO, TextIO]:
        return self._streams

    def _print_message(self, message: str, file=None) -> None:
        if message:
            out, err = self._streams
            (err if file is sys.stderr else out).write(message)

    def exit(self, status: int = 0, message: str | None = None):
        if message:
            self._print_message(message, sys.stderr)
        raise _UsageExit(status)


Handler = Callable[[Bookkeeping, argparse.Namespace], Outcome]


@dataclass(frozen=True)
class _Subcommand:
    name: str
    help: str
    add_arguments: Callable[[_Parser], None]
    handler: Handler


_READER_NAMES = ", ".join(reader.value for reader in Reader)


def _reader_named(text: str) -> Reader:
    try:
        return Reader(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not one of {_READER_NAMES}.") from None


def _add_normalise_arguments(parser: _Parser) -> None:
    parser.add_argument(
        "--stdout", required=True, help="the file holding the audit's or the scan's standard output"
    )
    parser.add_argument(
        "--stderr", required=True, help="the file holding the audit's or the scan's standard error"
    )
    parser.add_argument(
        "--from", dest="reader", type=_reader_named, default=Reader.UV_AUDIT,
        metavar="{" + ",".join(reader.value for reader in Reader) + "}",
        help="which program printed the two streams: uv-audit for uv's audit, osv-scanner for "
        "an osv-scanner scan (default: uv-audit)",
    )


def _run_normalise(bookkeeping: Bookkeeping, args: argparse.Namespace) -> Outcome:
    return bookkeeping.normalise(args.stdout, args.stderr, args.reader)


def _add_check_verdict_arguments(parser: _Parser) -> None:
    parser.add_argument("--report", required=True, help="the report to check")


def _run_check_verdict(bookkeeping: Bookkeeping, args: argparse.Namespace) -> Outcome:
    return bookkeeping.check_verdict(args.report)


_RECORD_HELP = (
    "the record's path, read for the advisory's renewals (a missing file is read as an empty "
    "record)"
)


_WINDOW_HELP = (
    "one severity's window, written Severity=days; give it once for each severity the NFDR "
    "names (default: 7 days for Critical and unscored, 30 for High, Medium and Low)"
)


def _add_lapse_date_arguments(parser: _Parser) -> None:
    parser.add_argument(
        "--entry", required=True, help="one entry of normalise's list, as JSON text"
    )
    parser.add_argument("--record", help=_RECORD_HELP)
    parser.add_argument("--window", action="append", help=_WINDOW_HELP)


def _run_lapse_date(bookkeeping: Bookkeeping, args: argparse.Namespace) -> Outcome:
    return bookkeeping.lapse_date(args.entry, args.record, args.window)


_WRITE_RECORD_FORMS = (
    ("entry", "add an entry for an advisory the record does not hold yet"),
    ("renewal", "add a renewal under an entry the record holds"),
)
_WRITE_RECORD_PATH_HELP = {
    "entry": "the record's path; a missing file is created with the entry",
    "renewal": "the record's path; it must already hold the advisory's entry",
}


def _add_write_record_arguments(parser: _Parser) -> None:
    forms = parser.add_subparsers(dest="form", required=True, parser_class=_Parser)
    for name, form_help in _WRITE_RECORD_FORMS:
        form = forms.add_parser(name, help=form_help, description=form_help,
                                streams=parser.streams)
        form.add_argument("--record", required=True, help=_WRITE_RECORD_PATH_HELP[name])
        form.add_argument(
            "--advisory", required=True, help="the advisory's id, as normalise prints it"
        )
        if name == "entry":
            form.add_argument(
                "--distribution", required=True,
                help="the dependency the advisory is published against",
            )
            form.add_argument(
                "--published", required=True, help="the advisory's publication date, YYYY-MM-DD"
            )
            form.add_argument(
                "--reason", required=True,
                help="the reason the entry stands, written as given",
            )
        else:
            form.add_argument("--on", required=True, help="the renewal's date, YYYY-MM-DD")
            form.add_argument(
                "--reason", required=True,
                help="the reason the renewal stands, written as given",
            )


def _run_write_record(bookkeeping: Bookkeeping, args: argparse.Namespace) -> Outcome:
    if args.form == "entry":
        return bookkeeping.write_entry(
            args.record, args.advisory, args.distribution, args.published, args.reason
        )
    return bookkeeping.write_renewal(args.record, args.advisory, args.on, args.reason)


def _add_find_lapsed_arguments(parser: _Parser) -> None:
    parser.add_argument("--record", required=True, help=_RECORD_HELP)
    parser.add_argument("--list", required=True, help="the file holding normalise's output")
    parser.add_argument("--window", action="append", help=_WINDOW_HELP)
    parser.add_argument(
        "--date",
        help="the date to compare against, YYYY-MM-DD (default: today on this machine's calendar)",
    )


def _run_find_lapsed(bookkeeping: Bookkeeping, args: argparse.Namespace) -> Outcome:
    return bookkeeping.find_lapsed(args.record, args.list, args.window, args.date)


_UPKEEP_CELL_OPTIONS = (
    ("task", "the Task cell"),
    ("rule", "the Rule it serves cell; a row whose cell is the same is replaced"),
    ("cadence", "the Cadence cell"),
    ("last-done", "the Last done cell"),
    ("next-due", "the Next due cell"),
    ("reminds", "the What reminds the owner cell"),
)


def _add_write_upkeep_arguments(parser: _Parser) -> None:
    parser.add_argument(
        "--register", required=True,
        help="the upkeep register's path; a missing file is created with the row",
    )
    for option, option_help in _UPKEEP_CELL_OPTIONS:
        parser.add_argument(f"--{option}", required=True, help=option_help)


def _run_write_upkeep(bookkeeping: Bookkeeping, args: argparse.Namespace) -> Outcome:
    cells = {option: getattr(args, option.replace("-", "_")) for option, _ in _UPKEEP_CELL_OPTIONS}
    return bookkeeping.write_upkeep(args.register, cells)


def _add_read_record_arguments(parser: _Parser) -> None:
    parser.add_argument("--record", required=True, help=_RECORD_HELP)


def _run_read_record(bookkeeping: Bookkeeping, args: argparse.Namespace) -> Outcome:
    return bookkeeping.read_record(args.record)


SUBCOMMANDS: tuple[_Subcommand, ...] = (
    _Subcommand(
        "normalise",
        "read the two output streams of uv's audit or of an osv-scanner scan, and print the "
        "advisories as one JSON list",
        _add_normalise_arguments,
        _run_normalise,
    ),
    _Subcommand(
        "lapse-date",
        "print the date one advisory's window lapses",
        _add_lapse_date_arguments,
        _run_lapse_date,
    ),
    _Subcommand(
        "write-record",
        "add an entry or a renewal to the record",
        _add_write_record_arguments,
        _run_write_record,
    ),
    _Subcommand(
        "find-lapsed",
        "sort the record's entries into lapsed, holding and unreported",
        _add_find_lapsed_arguments,
        _run_find_lapsed,
    ),
    _Subcommand(
        "write-upkeep",
        "write one row of the upkeep register, or replace the row that serves the same rule",
        _add_write_upkeep_arguments,
        _run_write_upkeep,
    ),
    _Subcommand(
        "read-record",
        "print the record's entries and their renewals as JSON",
        _add_read_record_arguments,
        _run_read_record,
    ),
    _Subcommand(
        "check-verdict",
        "check that a report's verdict line is bare and holds an allowed value",
        _add_check_verdict_arguments,
        _run_check_verdict,
    ),
)

TOOL_DESCRIPTION = (
    "Do the bookkeeping of a dependency-security run: read the advisories uv's audit or an "
    "osv-scanner scan printed, compute lapse dates, read and write the advisory record and the "
    "upkeep register, and check a report's verdict line. The tool computes and records, and "
    "decides nothing."
)


def build_parser(stdout: TextIO, stderr: TextIO) -> argparse.ArgumentParser:
    parser = _Parser(
        prog="security_bookkeeping", description=TOOL_DESCRIPTION, streams=(stdout, stderr)
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True, parser_class=_Parser)
    for subcommand in SUBCOMMANDS:
        sub = subparsers.add_parser(
            subcommand.name, help=subcommand.help, description=subcommand.help,
            streams=(stdout, stderr),
        )
        subcommand.add_arguments(sub)
        sub.set_defaults(handler=subcommand.handler)
    return parser


def run(
    argv: Sequence[str], *, bookkeeping: Bookkeeping, stdout: TextIO, stderr: TextIO
) -> int:
    """Run one subcommand. Standard output is written only after the job has wholly succeeded."""
    parser = build_parser(stdout, stderr)
    try:
        args = parser.parse_args(list(argv))
    except _UsageExit as finished:
        return finished.status
    try:
        outcome = args.handler(bookkeeping, args)
    except BookkeepingRefusal as refusal:
        stderr.write(f"{MESSAGE_PREFIX}{refusal}\n")
        return 1
    if outcome.note:
        stderr.write(outcome.note)
    stdout.write(outcome.stdout)
    return 0


def build_bookkeeping() -> Bookkeeping:
    """The composition root: the one place the real ports are built."""
    return Bookkeeping(
        files=Files(),
        advisories=Advisories(ADVISORY_SERVICE_BASE_URL),
        clock=Clock(),
    )


def main(argv: list[str] | None = None) -> int:
    return run(
        sys.argv[1:] if argv is None else argv,
        bookkeeping=build_bookkeeping(),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


if __name__ == "__main__":
    sys.exit(main())
