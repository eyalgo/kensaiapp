"""The change design templates' way-in section, pinned.

WHY THIS EXISTS
    `change_design_template.md` carries one unnumbered section, between `## 5. Test Additions`
    and `## Records this change makes false`, that reads the way in the product's NFDR records
    and picks none. The two preserving templates beside it carry no such text. These tests hold
    the headings' order, where the section reads the way in from, that the section offers no
    choice among the three ways in, and that the preserving templates stay clear of it.

    The new section's heading text is the content step's to write, so the tests find the section
    by its position between two headings that are named here, never by its own text. Everything
    is read from committed files through this file's own location, and nothing else is touched.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REFERENCES = (
    REPO / "skills" / "architect" / ".claude" / "skills" / "development-design" / "references"
)
CHANGING_TEMPLATE = REFERENCES / "change_design_template.md"
PRESERVING_TEMPLATES = (
    REFERENCES / "change_design_template.preserving.md",
    REFERENCES / "change_design_template.preserving_docs.md",
)

WAY_IN_LITERAL = "Behave way in"
WAY_IN_FORMS = ("command", "server", "browser")
HEADING_BEFORE_SECTION = "## 5. Test Additions"
HEADING_AFTER_SECTION = "## Records this change makes false"
EXPECTED_HEADINGS_BEFORE = [
    "## 1. Change Summary",
    "## 2. Blast Radius",
    "## 3. Sub-jobs",
    "## 4. Code Strategy",
    HEADING_BEFORE_SECTION,
]
EXPECTED_HEADINGS_AFTER = [HEADING_AFTER_SECTION, "## Architect Review Notes"]


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _headings(path: Path) -> list[str]:
    return [line for line in _lines(path) if line.startswith("## ")]


def _new_section_lines() -> list[str]:
    lines = _lines(CHANGING_TEMPLATE)
    start = lines.index(HEADING_BEFORE_SECTION)
    end = lines.index(HEADING_AFTER_SECTION)
    return lines[start + 1 : end]


def _new_section_heading() -> str:
    return next(line for line in _new_section_lines() if line.startswith("## "))


def test_the_changing_template_headings_keep_their_order_with_exactly_one_new_section():
    headings = _headings(CHANGING_TEMPLATE)

    assert headings[: len(EXPECTED_HEADINGS_BEFORE)] == EXPECTED_HEADINGS_BEFORE
    assert headings[-len(EXPECTED_HEADINGS_AFTER) :] == EXPECTED_HEADINGS_AFTER
    assert len(headings) == len(EXPECTED_HEADINGS_BEFORE) + 1 + len(EXPECTED_HEADINGS_AFTER)


def test_the_new_section_names_the_way_in_line_it_reads():
    section = "\n".join(_new_section_lines())
    whole_template = CHANGING_TEMPLATE.read_text(encoding="utf-8")

    assert WAY_IN_LITERAL in section
    assert whole_template.count(WAY_IN_LITERAL) == section.count(WAY_IN_LITERAL)


def test_the_new_section_offers_no_choice_among_the_three_forms():
    section_lines = _new_section_lines()
    named_in_a_line = [
        [form for form in WAY_IN_FORMS if re.search(rf"\b{form}\b", line)]
        for line in section_lines
    ]

    assert any(line.startswith("## ") for line in section_lines), "the section is absent"
    assert [forms for forms in named_in_a_line if len(forms) >= 2] == []


def test_the_new_section_names_no_two_of_the_three_forms_even_across_its_lines():
    section_lines = _new_section_lines()
    section = "\n".join(section_lines)
    named = [form for form in WAY_IN_FORMS if re.search(rf"\b{form}\b", section)]

    assert any(line.startswith("## ") for line in section_lines), "the section is absent"
    assert len(named) <= 1, f"the section names {named} as ways in"


def test_the_preserving_templates_carry_no_way_in_text():
    heading = _new_section_heading()

    for template in PRESERVING_TEMPLATES:
        text = template.read_text(encoding="utf-8")
        assert WAY_IN_LITERAL not in text
        assert heading not in _lines(template)
