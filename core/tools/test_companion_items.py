"""Tests for companion_items.py — the reader that lists a companion's open items and seat tags.

The reader is a pure function over the companion's text and a thin CLI over it, so the cases hand it
text. Two of them stamp that text from the real SDD open-issues template, which is what ties the
reader to the field form the template documents rather than to a form this file invented.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import companion_items

TOOLS = Path(__file__).resolve().parent
SDD_TEMPLATE = TOOLS.parent / "templates" / "product-templates" / "sdd_open_issues_template.md"

SLOT_INSTRUCTION = (
    "> Companion to `SDD.md`.\n"
    ">\n"
    "> **Answer inline** — fill each **Answer** / **Confirm or override** / **Keep or re-cut** /\n"
    "> **Your call** slot — **commit this file**, then re-run `product-sdd`.\n"
)


def companion(*items: str, header: str = SLOT_INSTRUCTION) -> str:
    """A companion made of the given `### ` item blocks under the given header."""
    preface = "# Open issues — example-product\n\n" + header + "\n---\n\n## 1. Open issues\n\n"
    return preface + "\n".join(items)


def numbers(text: str) -> list[str]:
    return [item.number for item in companion_items.open_items(text)]


def test_template_seat_field_is_read_as_a_tag():
    printed = (
        "### 1.1 <the question, in one line>\n"
        "- **Raised by:** <CTO | CPO | CDO>\n"
        "- **Seat:** <seat>\n"
    )
    assert printed in SDD_TEMPLATE.read_text()
    stamped = SDD_TEMPLATE.read_text().replace(printed, printed.replace("<seat>", "CPO"))

    items = companion_items.open_items(stamped)

    assert [(item.number, item.seat) for item in items] == [
        ("1.1", "CPO"),
        ("2.1", None),
        ("3.1", None),
        ("4.1", None),
        ("5.1", None),
        ("5.2", None),
    ]


def test_answered_item_is_excluded():
    text = companion(
        "### 1.1 first\n- **Seat:** cpo\n- **Answer:** use the shared queue\n",
        "### 1.2 second\n- **Seat:** cpo\n- **Answer:** <the owner fills this in>\n",
    )

    items = companion_items.open_items(text)

    assert [(item.number, item.seat) for item in items] == [("1.2", "cpo")]


def test_empty_or_placeholder_first_seat_is_untagged():
    text = companion(
        "### 1.1 placeholder\n- **Seat:** <seat>\n- **Answer:** <fill>\n",
        "### 1.2 empty\n- **Seat:**\n- **Answer:** <fill>\n",
        "### 1.3 placeholder then a real one\n- **Seat:** <seat>\n- **Seat:** cdo\n"
        "- **Answer:** <fill>\n",
    )

    assert [item.seat for item in companion_items.open_items(text)] == [None, None, None]


def test_first_seat_field_wins():
    text = companion("### 1.1 two tags\n- **Seat:** CPO\n- **Seat:** cdo\n- **Answer:** <fill>\n")

    assert [item.seat for item in companion_items.open_items(text)] == ["CPO"]


def test_wrapped_header_names_every_open_slot():
    one_slot_per_item = companion(
        "### 1.1 a\n- **Answer:** <fill>\n",
        "### 1.2 b\n- **Confirm or override:** <fill>\n",
        "### 1.3 c\n- **Keep or re-cut:** <fill>\n",
        "### 1.4 d\n- **Your call:** <fill>\n",
    )

    assert numbers(one_slot_per_item) == ["1.1", "1.2", "1.3", "1.4"]
    real_template_numbers = numbers(SDD_TEMPLATE.read_text())
    assert real_template_numbers == ["1.1", "2.1", "3.1", "4.1", "5.1", "5.2"]


def test_nested_placeholder_is_open_but_confirm_is_answered():
    nested = '- **Confirm or override:** <"confirm", or "override: <what to do instead>">\n'
    text = companion(
        f"### 2.1 open\n{nested}",
        "### 2.2 answered\n- **Confirm or override:** confirm\n",
        "### 2.3 overridden\n- **Confirm or override:** override: use the other queue\n",
    )

    assert numbers(text) == ["2.1"]


def test_wrapped_slot_value_keeps_its_item_boundary():
    text = (
        "# Open issues\n\n"
        + SLOT_INSTRUCTION
        + "\n## 1. First section\n\n"
        "### 1.1 wrapped answer\n"
        "- **Answer:** <the owner\n  fills this in>\n\n"
        "### 1.2 answered\n- **Answer:** done\n\n"
        "## 2. Next section\n\n"
        "### 2.1 open in the next section\n- **Your call:** <fill>\n"
    )

    assert numbers(text) == ["1.1", "2.1"]
    answered_then_heading = (
        "# Open issues\n\n" + SLOT_INSTRUCTION + "\n### 1.1 answered\n- **Answer:** done\n"
        "## 2. Next section\n- **Answer:** <belongs to no item>\n"
    )
    assert numbers(answered_then_heading) == []


def test_item_without_header_named_slot_is_excluded():
    text = companion("### 1.1 unrelated\n- **Why it matters:** <something>\n- **Seat:** cpo\n")

    assert numbers(text) == []


def test_no_slot_instruction_or_no_open_items_returns_empty():
    no_instruction = (
        "# Open issues\n\n> Companion to `SDD.md`. Answer inline, then re-run.\n\n"
        "### 1.1 a\n- **Answer:** <fill>\n"
    )
    nothing_open = companion("### 1.1 a\n- **Answer:** settled\n")

    assert companion_items.open_items(no_instruction) == ()
    assert companion_items.open_items(nothing_open) == ()


def test_an_instruction_quoted_inside_an_item_cannot_supply_header_slots():
    text = companion(
        "### 1.1 discuss wording\n"
        "> Proposed wording: fill each **Answer** slot before continuing.\n"
        "- **Seat:** cpo\n- **Answer:** <fill>\n",
        header="> Companion to `SDD.md`.\n",
    )

    assert companion_items.open_items(text) == ()


def test_one_remaining_header_named_slot_keeps_an_item_open():
    text = companion(
        "### 1.1 partly answered\n- **Seat:** cpo\n"
        "- **Answer:** accepted\n- **Your call:** <fill>\n",
    )

    assert [(item.number, item.seat) for item in companion_items.open_items(text)] == [
        ("1.1", "cpo"),
    ]


def test_empty_first_seat_does_not_yield_to_a_later_filled_seat():
    text = companion(
        "### 1.1 first field is empty\n- **Seat:**\n- **Seat:** cdo\n- **Answer:** <fill>\n",
    )

    assert [(item.number, item.seat) for item in companion_items.open_items(text)] == [
        ("1.1", None),
    ]


def write_companion(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "SDD_open_issues.md"
    path.write_text(text)
    return path


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOLS / "companion_items.py"), *args],
        capture_output=True,
        text=True,
    )


def test_cli_lists_number_and_raw_tag_in_companion_order(tmp_path):
    path = write_companion(
        tmp_path,
        companion(
            "### 1.1 untagged\n- **Answer:** <fill>\n",
            "### 1.2 tagged\n- **Seat:** CPO\n- **Answer:** <fill>\n",
            "### 1.3 answered\n- **Seat:** cdo\n- **Answer:** done\n",
        ),
    )

    result = run_cli("open-items", str(path))

    assert result.returncode == 0
    assert result.stdout == "1.1\t\n1.2\tCPO\n"


def test_cli_missing_companion_reports_error(tmp_path):
    result = run_cli("open-items", str(tmp_path / "absent.md"))

    assert result.returncode != 0
    assert result.stdout == ""
    assert "absent.md" in result.stderr
