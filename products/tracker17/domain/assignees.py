"""The Assignees feature entry point: the assignee list and the rules that accept or refuse a name.

Realizes SRS FR-20 and FR-22 (the list; removing a name changes the list alone), FR-39 and FR-40
(refusals and the maximum length), DR-4 (one list of unique names, compared exactly) and NFR-9 (the
trace from the requirement to this code).

Taking part: application/tracker.py applies these rules and saves the result; web/pages.py shows the
list and the Add form, and web/routes.py turns a submission into an add or a remove and a refusal
into its reason. persistence/saved_data.py restores a saved list through restore_state, which
applies check_assignee_names.

Checked by: tests/unit/test_assignees.py and tests/unit/test_state.py (the rules and restoration),
tests/integration/test_assignee_tracker.py (the actions), tests/integration/test_saved_data.py and
tests/integration/test_start.py (the saved list and the start), tests/integration/test_people_pages.py
and tests/integration/test_pages.py (the pages), tests/integration/test_people_routes.py and
tests/integration/test_routes.py (the requests) and tests/e2e/test_people.py (the browser).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from typing import TYPE_CHECKING

from domain.refusals import AssigneeNameInUse, AssigneeNotFound, BlankName, TextField
from domain.text import SHORT_TEXT_MAX, ensure_within

if TYPE_CHECKING:
    from domain.state import TrackerState


def check_assignee_names(names: Iterable[str]) -> tuple[str, ...]:
    """The names as a tuple in the order given, or the refusal of the first one that breaks a rule.

    Each name is checked in order: too long, then blank, then already given. A name is as long as
    its Unicode code points, and two names are one only when they are exactly equal. Nothing is
    sorted, case-folded or trimmed.
    """
    checked: list[str] = []
    seen: set[str] = set()
    for name in names:
        ensure_within(TextField.NAME, name, SHORT_TEXT_MAX)
        if all(character.isspace() for character in name):
            raise BlankName()
        if name in seen:
            raise AssigneeNameInUse()
        seen.add(name)
        checked.append(name)
    return tuple(checked)


def add_assignee(state: TrackerState, name: str) -> TrackerState:
    """The state with the name at the end of the list, or raise the refusal of the name."""
    return replace(state, assignees=check_assignee_names((*state.assignees, name)))


def remove_assignee(state: TrackerState, name: str) -> TrackerState:
    """The state without the name, every other name in its place, or raise AssigneeNotFound."""
    if name not in state.assignees:
        raise AssigneeNotFound()
    return replace(state, assignees=tuple(listed for listed in state.assignees if listed != name))


def list_assignees(state: TrackerState) -> tuple[str, ...]:
    """Every name, earliest added first."""
    return state.assignees
