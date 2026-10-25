"""record_declarations.py — the one parser of a record's declared lines, and the table of the
fields those lines declare.

WHY THIS EXISTS
    The chain (`chain_development.DiskReader`) and the commit builder (`commit_builder`) each read
    the declared lines of a closing marker and of a code-integrity or security report. The scan
    existed twice, the builder's copy "kept here without importing the chain", and every caller
    passed its own bare prefix and chose first-or-all for itself, so where a declaration may appear
    and how many of its lines are read was written wherever a caller happened to read one. This
    module is the one scan both import, and `FIELDS` is the one place each prefix is written.

    A record is parsed once into an immutable `ParsedRecord`, and a caller asks it for a field.
    `FIELDS` states each field's prefix, where in a record its lines may appear (`Place`) and how
    many are read (`Count`). A field's lines are read either from anywhere in the record or only
    from its first run of consecutive matching lines, so a sentence further down that opens with a
    quoted prefix is not a declaration of a field read that way.

HOW A LINE IS READ
    Both bodies the scan reads are markdown written by a model, and every place the skills name a
    declared line shows it inside backticks, so `**Integrity: pass**` is the natural way to write
    one. A walk was halted `missing-integrity` by exactly that, on a green suite the step had just
    proved (a `chain-change` walk, 2026-09-17). A line is undressed before its prefix is matched:
    its surrounding whitespace is removed, then `*`, `_` and the backtick from both ends
    (`EMPHASIS`), then whitespace again. What counts as a value is not widened by an inch:
    `Integrity: Pass` and `Integrity: passed` still halt. A mention elsewhere in a line is not a
    declaration, because only the start of the undressed line is matched. A line comes back in both
    forms, `Line.raw` as written and `Line.text` undressed, and callers take a value from the
    undressed one.

WHAT IT IMPORTS
    No other tool. The builder imports it and never the chain, and it imports neither of them.
"""

from __future__ import annotations

import types
from dataclasses import dataclass
from enum import Enum, auto

__version__ = "1.2.0"

EMPHASIS = "*_`"


class Place(Enum):
    """Where in a record a field's lines may appear: anywhere in it, or only in its first run.
    The first run is the first line that matches the field and every line directly after it that
    also matches. The first line after them that does not match ends it, so a later matching line
    is not a declaration."""

    ANYWHERE = auto()
    FIRST_RUN = auto()


class Count(Enum):
    """How many of a field's matching lines are read: the first in body order, or every one."""

    FIRST = auto()
    ALL = auto()


@dataclass(frozen=True)
class Field:
    """One declared field: what its lines start with, where they may appear, how many are read."""

    name: str
    prefix: str
    place: Place
    count: Count


@dataclass(frozen=True)
class Line:
    """One line of a record: `raw` as written, `text` with its whitespace and emphasis removed."""

    raw: str
    text: str


SUITE = Field("SUITE", "Suite:", Place.ANYWHERE, Count.FIRST)
LANGUAGE_RESOLUTION = Field("LANGUAGE_RESOLUTION", "Language resolution", Place.ANYWHERE, Count.ALL)
ENVIRONMENT = Field("ENVIRONMENT", "Environment:", Place.FIRST_RUN, Count.ALL)
DEFERRED = Field("DEFERRED", "Deferred:", Place.ANYWHERE, Count.ALL)
FAILING = Field("FAILING", "Failing:", Place.FIRST_RUN, Count.ALL)
RELANE_NOTE = Field("RELANE_NOTE", "- Task ", Place.ANYWHERE, Count.ALL)
INTEGRITY = Field("INTEGRITY", "Integrity:", Place.ANYWHERE, Count.FIRST)
SECURITY = Field("SECURITY", "Security:", Place.ANYWHERE, Count.FIRST)
PUBLISHES_TEXT = Field("PUBLISHES_TEXT", "Publishes text:", Place.ANYWHERE, Count.FIRST)
PLANNED_BY = Field("PLANNED_BY", "Planned by:", Place.ANYWHERE, Count.FIRST)
REPAIR = Field("REPAIR", "Repair:", Place.ANYWHERE, Count.FIRST)

FIELDS: tuple[Field, ...] = (
    SUITE, LANGUAGE_RESOLUTION, ENVIRONMENT, DEFERRED, FAILING, RELANE_NOTE, INTEGRITY, SECURITY,
    PUBLISHES_TEXT, PLANNED_BY, REPAIR,
)

BY_PREFIX = types.MappingProxyType({field.prefix: field for field in FIELDS})


@dataclass(frozen=True)
class ParsedRecord:
    """A record's lines, parsed once. `read` and `one` query it by field."""

    lines: tuple[Line, ...]

    def read(self, field: Field) -> tuple[Line, ...]:
        """The lines `field` declares, in body order: those its place admits whose undressed text
        starts with its prefix, the first only for a `FIRST` field and every one for an `ALL`."""
        if field.place is Place.FIRST_RUN:
            admitted = self._first_run(field)
        else:
            admitted = (line for line in self.lines if line.text.startswith(field.prefix))
        if field.count is Count.FIRST:
            return tuple(line for _, line in zip(range(1), admitted))
        return tuple(admitted)

    def _first_run(self, field: Field) -> tuple[Line, ...]:
        """The first matching line and every line directly after it that also matches."""
        run: list[Line] = []
        for line in self.lines:
            if line.text.startswith(field.prefix):
                run.append(line)
            elif run:
                break
        return tuple(run)

    def one(self, field: Field) -> Line | None:
        """The one line of a `FIRST` field, or `None` when the record declares none. Asked of an
        `ALL` field it raises `ValueError`: such a field has no single line to give."""
        if field.count is not Count.FIRST:
            raise ValueError(f"{field.name} is read in full, so it has no single line: use read()")
        found = self.read(field)
        return found[0] if found else None


def parse(body: str) -> ParsedRecord:
    """Parse `body` once into its lines, each undressed as `Line.text`."""
    return ParsedRecord(tuple(
        Line(raw, raw.strip().strip(EMPHASIS).strip()) for raw in body.splitlines()))
