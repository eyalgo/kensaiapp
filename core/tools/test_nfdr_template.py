"""The NFDR template's way-in line, pinned.

WHY THIS EXISTS
    `core/templates/product-templates/nfdr_template.md` § 9 carries two labelled lines: the
    `**Behave:**` line, and the `**Behave way in:**` line that records how Behave reaches the
    product. The way-in line is stamped holding all three forms written together, which reads as
    the pick not made yet. These tests hold where that line sits, how often its label occurs,
    what it says, and that the Behave line beside it keeps its text.

    Everything is read from the committed template through this file's own location, as
    `test_project_template.py` does, and nothing else is touched. Every assertion anchors on a short
    label, never on a wrapped phrase.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TEMPLATE = REPO / "core" / "templates" / "product-templates" / "nfdr_template.md"

WAY_IN_LITERAL = "Behave way in"
WAY_IN_LABEL = "**Behave way in:**"
BEHAVE_LABEL = "**Behave:**"
TEST_STRATEGY_HEADING = "## 9."
VERIFICATION_MAP_HEADING = "## 10."
WAY_IN_NOT_MADE_VALUE = "command | server | browser"
BEHAVE_LINE = "**Behave:** behave | none — <reason>"


def _template_text() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def _template_lines() -> list[str]:
    return _template_text().splitlines()


def _index_of_line_starting(prefix: str) -> int:
    return next(i for i, line in enumerate(_template_lines()) if line.startswith(prefix))


def test_the_template_holds_the_way_in_literal_exactly_once_and_on_its_own_line():
    assert _template_text().count(WAY_IN_LITERAL) == 1
    assert [line for line in _template_lines() if WAY_IN_LITERAL in line] == [
        line for line in _template_lines() if line.startswith(WAY_IN_LABEL)
    ]


def test_the_way_in_line_sits_between_the_behave_line_and_the_verification_map():
    behave_at = _index_of_line_starting(BEHAVE_LABEL)
    way_in_at = _index_of_line_starting(WAY_IN_LABEL)
    map_at = _index_of_line_starting(VERIFICATION_MAP_HEADING)

    assert behave_at < way_in_at < map_at
    between = _template_lines()[behave_at + 1 : way_in_at]
    assert [line for line in between if line.startswith("**")] == []


def test_the_way_in_line_sits_inside_the_test_strategy_section():
    strategy_at = _index_of_line_starting(TEST_STRATEGY_HEADING)
    way_in_at = _index_of_line_starting(WAY_IN_LABEL)
    map_at = _index_of_line_starting(VERIFICATION_MAP_HEADING)

    assert strategy_at < way_in_at < map_at
    between = _template_lines()[strategy_at + 1 : way_in_at]
    assert [line for line in between if line.startswith("## ")] == []


def test_the_way_in_value_names_all_three_forms_and_makes_no_pick():
    line = _template_lines()[_index_of_line_starting(WAY_IN_LABEL)]

    assert line == f"{WAY_IN_LABEL} {WAY_IN_NOT_MADE_VALUE}"


def test_the_behave_line_keeps_its_present_text():
    assert _template_lines()[_index_of_line_starting(BEHAVE_LABEL)] == BEHAVE_LINE
