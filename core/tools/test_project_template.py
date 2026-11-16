"""The project card template's field lines, pinned.

WHY THIS EXISTS
    `core/templates/project_template.md` is the one shape every project card is stamped from, and
    a field it carries is a field every card carries. The `**Behave:**` line says whether a
    product's behaviour is tested with Behave; it is stamped holding both forms, `behave` and
    `none — <reason>`, which reads as the call not made yet. These tests hold that line where it
    sits, what it says, and the one list in doctrine that names the card's fields.

    Everything is read from committed files through this file's own location, as
    `test_templates_are_instance_neutral.py` does, and nothing else is touched.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TEMPLATE = REPO / "core" / "templates" / "project_template.md"
SETUP_SCOPE = REPO / "core" / "doctrine" / "setup" / "setup_scope.md"

BEHAVE_LABEL = "**Behave:**"
TEST_COMMAND_LABEL = "**Test command:**"
BEHAVE_VALUE = "behave | none — <reason>"
REQUIRED_FIELD = "Product path"
CARD_SECTION_HEADING = "### `system/projects/<name>/project.md`"


def _template_lines() -> list[str]:
    return TEMPLATE.read_text(encoding="utf-8").splitlines()


def _behave_line() -> str:
    return next(line for line in _template_lines() if line.startswith(BEHAVE_LABEL))


def _behave_comment() -> str:
    return _behave_line().split("<!--", 1)[1]


def test_the_card_template_holds_exactly_one_behave_line():
    behave_lines = [line for line in _template_lines() if line.startswith(BEHAVE_LABEL)]
    assert len(behave_lines) == 1


def test_the_behave_line_directly_follows_the_test_command_line():
    lines = _template_lines()
    test_command_at = next(i for i, line in enumerate(lines) if line.startswith(TEST_COMMAND_LABEL))
    assert lines[test_command_at + 1].startswith(BEHAVE_LABEL)


def test_the_behave_value_names_both_forms_and_makes_no_call():
    value = _behave_line().split(BEHAVE_LABEL, 1)[1].split("<!--")[0].strip()
    assert value == BEHAVE_VALUE


def test_the_behave_line_ends_with_an_inline_comment():
    line = _behave_line()
    assert "<!--" in line
    assert line.rstrip().endswith("-->")


def test_the_behave_comment_states_the_four_facts():
    comment = _behave_comment()
    anchors = {
        "what the line answers": "tested with Behave",
        "who makes the call": "Principal Architect",
        "the call is per product": "per product",
        "behave means needed": "`behave` means",
        "none means not needed, with the reason": "`none — <reason>` means",
        "one tool for every language": "one tool for every language",
        "no Behave per language": "no Behave per language",
    }
    missing = [fact for fact, anchor in anchors.items() if anchor not in comment]
    assert not missing, f"the Behave comment lost: {missing}"


def test_the_behave_comment_names_no_core_path():
    assert "core/" not in _behave_comment()


def _template_field_names() -> set[str]:
    labels = (re.match(r"\*\*([^:*]+):\*\*", line) for line in _template_lines())
    return {label.group(1) for label in labels if label}


def _card_section() -> str:
    lines = SETUP_SCOPE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(CARD_SECTION_HEADING))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("###")), len(lines))
    return " ".join(lines[start + 1 : end])


def _not_drift_checked_names() -> set[str]:
    listed = re.search(r"\(([^)]*)\) are \*\*not\*\* drift-checked", _card_section())
    assert listed, "the section no longer lists the fields that are not drift-checked"
    return set(re.findall(r"`([^`]+)`", listed.group(1)))


def test_the_not_drift_checked_list_names_every_template_field_but_product_path():
    assert _not_drift_checked_names() == _template_field_names() - {REQUIRED_FIELD}


def test_product_path_is_absent_from_the_not_drift_checked_list():
    assert REQUIRED_FIELD not in _not_drift_checked_names()


def test_the_section_still_states_the_required_field_and_the_not_drift_checked_sentence():
    section = _card_section()
    assert "Required field: `Product path:`" in section
    assert "**not** drift-checked" in section
