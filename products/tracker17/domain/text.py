"""The two text maximums and the length check, stated once (SRS FR-40; ADR-0007).

A length is the number of Unicode code points in the value as it would be saved, so a character
outside the Basic Multilingual Plane counts one and a line break counts one. No part ever shortens a
value to make it fit.
"""

from __future__ import annotations

from domain.refusals import TextField, TextTooLong

SHORT_TEXT_MAX = 200
LONG_TEXT_MAX = 4000


def ensure_within(field: TextField, value: str, maximum: int) -> None:
    """Raise TextTooLong when the value is longer than the maximum."""
    if len(value) > maximum:
        raise TextTooLong(field, maximum)
