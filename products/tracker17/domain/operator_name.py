"""The operator name: the one scalar rule and the outcome of setting it.

Realizes SRS FR-27 (the operator's name), FR-39 and FR-40 (refusals and the maximum length) and
DR-5 (the one operator name, which no action clears). The name is kept exactly as typed and is
compared exactly, so a space or a letter-case difference makes a different name. It is not the
Comments feature entry and builds nothing about comments.

Taking part: domain/state.py holds the name and applies check_operator_name when a saved name is
restored; application/tracker.py applies set_operator_name and saves the result; web/pages.py and
web/routes.py show the Your name section and map each refusal to its reason by type.

Checked by: tests/unit/test_operator_name.py and tests/unit/test_state.py (the rule and
restoration), tests/integration/test_operator_name_tracker.py (the action),
tests/integration/test_saved_data.py and tests/integration/test_start.py (the saved name),
tests/integration/test_people_pages.py and tests/integration/test_people_routes.py (the page and
the requests) and tests/e2e/test_people.py (the browser).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from domain.refusals import BlankName, TextField
from domain.text import SHORT_TEXT_MAX, ensure_within

if TYPE_CHECKING:
    from domain.state import TrackerState


@dataclass(frozen=True)
class OperatorNameOutcome:
    """What setting the name did: the submitted name, and whether it differs from the saved one."""

    name: str
    changed: bool


def check_operator_name(name: str) -> str:
    """The name unchanged, or the refusal of it.

    Checked in order: too long, then blank. A name is as long as its Unicode code points, and is
    blank when it is empty or every character is whitespace, the set a project name and an assignee
    name already use. Nothing is trimmed or case-folded.
    """
    ensure_within(TextField.NAME, name, SHORT_TEXT_MAX)
    if all(character.isspace() for character in name):
        raise BlankName()
    return name


def set_operator_name(state: TrackerState, name: str) -> tuple[TrackerState, OperatorNameOutcome]:
    """The state holding the name, and the outcome, or raise the refusal of the name.

    A name exactly equal to the saved one returns the original state and `changed=False`. Any other
    valid name returns a state that differs from the original only in the name. There is no
    operation that clears the name.
    """
    checked = check_operator_name(name)
    if checked == state.operator_name:
        return state, OperatorNameOutcome(name=checked, changed=False)
    return replace(state, operator_name=checked), OperatorNameOutcome(name=checked, changed=True)
