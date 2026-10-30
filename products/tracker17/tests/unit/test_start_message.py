"""Unit tests of the ready line's location field (layer 1).

Checks SRS FR-1 (the start prints where to open the tracker and where the data is) and NFR-11 (the
unit layer of the suite). Change spec rules CP-748 (each non-text byte of the path is written as a
backslash, an x and two lowercase hex digits, never a replacement mark or the form `\\udce9`),
CP-749 (every byte the file-name decoding could not turn into text, wherever it sits, and every
other character as it is) and CP-751 (a path with no such byte gives the line it gave before) are
what each test names. The expected text of every case is written out here, independently of the
code under test. NFDR QC-11 (a test module names the rules and obligations it checks).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import main

HOST = "127.0.0.1"
PORT = 8017
ADDRESS = "http://127.0.0.1:8017"
LINE_BEFORE_LOCATION = (
    f"The tracker is running. Open {ADDRESS} in your browser. Saved data is kept at "
)
SURROGATE_ESCAPE_BASE = 0xDC00
FIRST_NON_TEXT_BYTE = 0x80
LAST_NON_TEXT_BYTE = 0xFF


def ready_line(location: str) -> str:
    return main._ready_line(HOST, PORT, Path(location))


def expected_line(location: str) -> str:
    return f"{LINE_BEFORE_LOCATION}{location}."


@pytest.mark.parametrize(
    "byte", range(FIRST_NON_TEXT_BYTE, LAST_NON_TEXT_BYTE + 1), ids=lambda byte: f"{byte:#04x}"
)
def test_ready_line_escapes_each_filename_byte(byte: int) -> None:
    """CP-748, CP-749: every marker from U+DC80 through U+DCFF, both endpoints included, is
    written as its own byte in a backslash, an x and two lowercase hex digits."""
    marker = chr(SURROGATE_ESCAPE_BASE + byte)
    digits = "0123456789abcdef"
    escape = "\\x" + digits[byte // 16] + digits[byte % 16]

    assert ready_line(f"/tmp/a{marker}b/data") == expected_line(f"/tmp/a{escape}b/data")


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
    ],
)
def test_ready_line_preserves_byte_positions_and_other_text(location: str, shown: str) -> None:
    """CP-748, CP-749: each marker is replaced where it stands and every other character of the
    path stays, in its order; no replacement mark and no surrogate spelling appears."""
    line = ready_line(location)

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
def test_ready_line_keeps_ordinary_paths_verbatim(location: str) -> None:
    """CP-751: a path with no filename-decoding marker gives the whole line it gave before, the
    address ahead of the location, a real backslash and a valid character untouched."""
    assert ready_line(location) == expected_line(location)


@pytest.mark.parametrize(
    "character",
    [
        pytest.param("\udc7f", id="just-below-the-range"),
        pytest.param("\udd00", id="just-above-the-range"),
        pytest.param("\ud800", id="high-surrogate"),
    ],
)
def test_ready_line_escapes_only_the_filename_byte_range(character: str) -> None:
    """CP-749: a surrogate outside U+DC80 through U+DCFF is no file-name byte, so it is written
    as it is and never as an escape."""
    location = f"/tmp/a{character}b/data"

    assert ready_line(location) == expected_line(location)
