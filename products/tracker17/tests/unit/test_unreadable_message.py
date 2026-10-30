"""Unit tests of the unreadable-data line's location field (layer 1).

Checks SRS FR-1 (the start prints where to open the tracker and what happened), NFR-4 (an
unreadable start tells the person why) and AC-7 (the unreadable-data answer). Change spec rules
CP-757 (the whole line), CP-760 (each non-text byte of the path is written as a backslash, an x and
two lowercase hex digits, never a replacement mark or the form `\\udce9`, and the line encodes as
UTF-8), CP-761 (every byte the file-name decoding could not turn into text, wherever it sits, and
every other character as it is), CP-763 (a path with no such byte gives the line it gave before)
and CP-765 (the line for `/tmp/caf\\xe9/data`) are what each test names. The expected text of every
case is written out here, independently of the code under test. NFDR QC-11 (a test module names the
rules and obligations it checks).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import main

HOST = "127.0.0.1"
PORT = 8017
LINE_BEFORE_LOCATION = "The tracker couldn't read its saved data at "
LINE_AFTER_LOCATION = (
    ", and nothing in it was changed. "
    "Open http://127.0.0.1:8017 in your browser to read this on a page. "
    "To start fresh on purpose, follow Setting saved data aside in the setup instructions."
)
SURROGATE_ESCAPE_BASE = 0xDC00
FIRST_NON_TEXT_BYTE = 0x80
LAST_NON_TEXT_BYTE = 0xFF
HEX_DIGITS = "0123456789abcdef"


def unreadable_line(location: str) -> str:
    return main._unreadable_line(HOST, PORT, Path(location))


def expected_line(location: str) -> str:
    return f"{LINE_BEFORE_LOCATION}{location}{LINE_AFTER_LOCATION}"


def test_unreadable_line_displays_a_decoded_byte_as_four_characters() -> None:
    """CP-757, CP-760, CP-765: the line for the path decoded from `/tmp/caf` `e9` `/data` holds
    the literal `/tmp/caf\\xe9/data`, with no replacement mark, no character in U+DC80–U+DCFF and
    no `\\udce9`, and encodes as strict UTF-8."""
    line = main._unreadable_line(HOST, PORT, Path(os.fsdecode(b"/tmp/caf\xe9/data")))

    assert line == expected_line("/tmp/caf" + "\\" + "xe9" + "/data")
    assert "/tmp/caf\\xe9/data" in line
    assert "�" not in line
    assert not any(0xDC80 <= ord(character) <= 0xDCFF for character in line)
    assert "\\udce9" not in line
    line.encode("utf-8")


@pytest.mark.parametrize(
    "byte", range(FIRST_NON_TEXT_BYTE, LAST_NON_TEXT_BYTE + 1), ids=lambda byte: f"{byte:#04x}"
)
def test_unreadable_line_escapes_each_filename_byte(byte: int) -> None:
    """CP-760, CP-761: every marker from U+DC80 through U+DCFF, both endpoints included, is
    written as its own byte in a backslash, an x and two lowercase hex digits."""
    marker = chr(SURROGATE_ESCAPE_BASE + byte)
    escape = "\\x" + HEX_DIGITS[byte // 16] + HEX_DIGITS[byte % 16]

    assert unreadable_line(f"/tmp/a{marker}b/data") == expected_line(f"/tmp/a{escape}b/data")


@pytest.mark.parametrize(
    ("location", "shown"),
    [
        pytest.param("/tmp/a\udce9\udcff/data", "/tmp/a\\xe9\\xff/data", id="consecutive"),
        pytest.param("/tmp/a\udce9b\udcffc/data", "/tmp/a\\xe9b\\xffc/data", id="separated"),
        pytest.param("/tmp/\udce9/\udcff/data", "/tmp/\\xe9/\\xff/data", id="two-components"),
        pytest.param("/tmp/\udc80x\udcff", "/tmp/\\x80x\\xff", id="at-both-ends"),
        pytest.param("/tmp/\udce9\udce9/data", "/tmp/\\xe9\\xe9/data", id="the-same-byte-twice"),
        pytest.param("/tmp/café\udce9/data", "/tmp/café\\xe9/data", id="after-valid-text"),
        pytest.param("/tmp/\udce9café/data", "/tmp/\\xe9café/data", id="before-valid-text"),
        pytest.param("/tmp/a\\b\udce9\\x41/d", "/tmp/a\\b\\xe9\\x41/d", id="beside-backslashes"),
        pytest.param(
            os.fsdecode(b"/tmp/a\xe9\xff/data"), "/tmp/a\\xe9\\xff/data", id="two-byte-example"
        ),
    ],
)
def test_unreadable_line_preserves_positions_and_other_characters(
    location: str, shown: str
) -> None:
    """CP-760, CP-761: each marker is replaced where it stands and every other character of the
    path stays, in its order; no replacement mark and no surrogate spelling appears."""
    line = unreadable_line(location)

    assert line == expected_line(shown)
    assert "�" not in line
    assert "\\udc" not in line
    line.encode("utf-8")


@pytest.mark.parametrize(
    "location",
    [
        pytest.param("/Users/sam/tracker17/data", id="plain-text"),
        pytest.param("/tmp/café/data", id="valid-non-ascii"),
        pytest.param("/tmp/a\\xe9b/data", id="literal-backslash-folder-name"),
    ],
)
def test_unreadable_line_keeps_ordinary_paths_verbatim(location: str) -> None:
    """CP-763: a path with no filename-decoding marker gives the whole line it gave before, a real
    backslash and a valid character untouched."""
    assert unreadable_line(location) == expected_line(location)


@pytest.mark.parametrize(
    "character",
    [
        pytest.param("\udc7f", id="just-below-the-range"),
        pytest.param("\udd00", id="just-above-the-range"),
        pytest.param("\ud800", id="high-surrogate"),
    ],
)
def test_unreadable_line_leaves_other_surrogates_untouched(character: str) -> None:
    """CP-761: a surrogate outside U+DC80 through U+DCFF is no file-name byte, so it is written as
    it is and never as an escape."""
    location = f"/tmp/a{character}b/data"

    assert unreadable_line(location) == expected_line(location)
