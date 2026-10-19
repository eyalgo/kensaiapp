#!/usr/bin/env python3
"""companion_items.py — lists a companion's open items, each with the seat tag it carries.

WHY THIS EXISTS

A companion's open items used to be answered in one run, in one seat. An item may now name the seat
that answers it (`- **Seat:** <seat>`), so the self-answer launcher has to know, before it starts
anything, which items are still open and which seat each asks for. The header's slot labels wrap
across quoted lines and one slot's placeholder nests angle brackets, which a line-oriented shell
read gets wrong; this module reads the whole text instead.

It resolves nothing. The tag comes back as written, case and all; matching it against the agent
files and the loader check is the launcher's, where those checks already have one owner.

An open item is a `### ` item with a slot the header's "fill each **X** / **Y** ... slot" sentence
names, whose value is still one angle-bracketed placeholder. The labels are read from the header of
the file in hand, never from a list kept here, so a companion whose header names other slots is read
by its own words and one whose header names none has no open item.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

__version__ = "1.0.0"

SEAT_LABEL = "Seat"

_SLOT_INSTRUCTION = re.compile(r"fill each\s+(.+?)\s+slot")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_FIELD = re.compile(r"^- \*\*(?P<label>[^*]+?):\*\*[ \t]*(?P<value>.*)$")
_ITEM_HEADING = re.compile(r"^### (?P<number>\S+)")
_ANY_HEADING = re.compile(r"^#{2,3} ")


@dataclass(frozen=True)
class Item:
    """One open item: its number (the heading's leading token) and its raw seat tag, if usable."""

    number: str
    seat: str | None


def _quoted_header(lines: list[str]) -> str:
    """Join header blockquotes before the first section or item heading."""
    quoted: list[str] = []
    for line in lines:
        if _ANY_HEADING.match(line):
            break
        if line.startswith(">"):
            quoted.append(re.sub(r"^>\s?", "", line).strip())
    return " ".join(part for part in quoted if part)


def slot_labels(text: str) -> tuple[str, ...]:
    """The slot labels the header's fill-each instruction names; empty when it names none."""
    found = _SLOT_INSTRUCTION.search(_quoted_header(text.splitlines()))
    if found is None:
        return ()
    return tuple(label.strip() for label in _BOLD.findall(found.group(1)))


def _is_placeholder(value: str) -> bool:
    """One angle-bracketed span from its first character to its last, nested brackets included."""
    return len(value) >= 2 and value.startswith("<") and value.endswith(">")


def _fields(block: list[str]) -> list[tuple[str, str]]:
    """The item's `- **Label:** value` bullets; a value takes its indented continuations."""
    fields: list[tuple[str, str]] = []
    for line in block:
        field = _FIELD.match(line)
        if field is not None:
            fields.append((field.group("label").strip(), field.group("value").strip()))
        elif fields and line[:1] in (" ", "\t") and line.strip():
            label, value = fields[-1]
            fields[-1] = (label, f"{value} {line.strip()}".strip())
    return fields


def _item_blocks(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Each `### ` item as (number, its lines), ended by the next `## ` or `### ` heading."""
    blocks: list[tuple[str, list[str]]] = []
    current: list[str] | None = None
    for line in lines:
        item = _ITEM_HEADING.match(line)
        if item is not None:
            current = []
            blocks.append((item.group("number"), current))
        elif _ANY_HEADING.match(line):
            current = None
        elif current is not None:
            current.append(line)
    return blocks


def open_items(text: str) -> tuple[Item, ...]:
    """The companion's open items in file order; empty when its header names no slot."""
    labels = slot_labels(text)
    if not labels:
        return ()
    items: list[Item] = []
    for number, block in _item_blocks(text.splitlines()):
        fields = _fields(block)
        if not any(label in labels and _is_placeholder(value) for label, value in fields):
            continue
        first_seat = next((value for label, value in fields if label == SEAT_LABEL), "")
        seat = None if not first_seat or _is_placeholder(first_seat) else first_seat
        items.append(Item(number=number, seat=seat))
    return tuple(items)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List a companion's open items.")
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("open-items", help="print `<number>\\t<tag>` per open item")
    listing.add_argument("companion", help="path to the companion file")
    args = parser.parse_args(argv)

    try:
        text = Path(args.companion).read_text()
    except OSError as exc:
        print(f"companion_items: cannot read {args.companion}: {exc.strerror}", file=sys.stderr)
        return 1
    for item in open_items(text):
        print(f"{item.number}\t{item.seat or ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
