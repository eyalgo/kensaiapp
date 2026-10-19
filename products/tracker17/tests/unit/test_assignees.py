"""Unit tests of the assignee rules in domain (layer 1), with no file and no clock.

Checks SRS FR-20 (the assignee list), FR-22 (a removed name stays on the tasks that carry it, so
removal here touches only the list), FR-39 and FR-40 (refusals and maximum lengths) and DR-4 (one
list of unique names compared exactly). Change spec rules CP-82, CP-86, CP-88 to CP-92, CP-95,
CP-96 and CP-105 are the ones each test names.
"""

from __future__ import annotations

import pytest

from domain import (
    SHORT_TEXT_MAX,
    AssigneeNameInUse,
    AssigneeNotFound,
    BlankName,
    Refusal,
    TextField,
    TextTooLong,
    TrackerState,
    add_assignee,
    create_project,
    empty_state,
    list_assignees,
    remove_assignee,
)


def _state_with(*names: str) -> TrackerState:
    state = empty_state()
    for name in names:
        state = add_assignee(state, name)
    return state


def test_assignees_start_empty_and_append_in_order():
    """CP-82, CP-86: earliest first, whatever the alphabetical order."""
    state = empty_state()
    assert list_assignees(state) == ()

    for name in ("Dana", "Ari", "Bo"):
        state = add_assignee(state, name)

    assert list_assignees(state) == ("Dana", "Ari", "Bo")


def test_assignee_names_match_exactly():
    """CP-88, CP-95: case, surrounding or repeated spaces and markup each make a name distinct."""
    names = ("Dana", "dana", "Dana ", " Dana", "Dana  Lee", "Dana Lee", "<b>Dana</b>", "A&B")

    state = _state_with(*names)
    assert list_assignees(state) == names

    after_removal = remove_assignee(state, "Dana")
    assert list_assignees(after_removal) == tuple(name for name in names if name != "Dana")

    with pytest.raises(AssigneeNotFound):
        remove_assignee(state, "DANA")
    with pytest.raises(AssigneeNotFound):
        remove_assignee(state, "Dana   Lee")


def test_remove_preserves_survivor_order_and_readd_appends():
    """CP-82, CP-96: a removed name added again goes to the end."""
    state = _state_with("Dana", "Ari", "Bo", "Cy")

    assert list_assignees(remove_assignee(state, "Dana")) == ("Ari", "Bo", "Cy")
    assert list_assignees(remove_assignee(state, "Ari")) == ("Dana", "Bo", "Cy")
    assert list_assignees(remove_assignee(state, "Cy")) == ("Dana", "Ari", "Bo")

    readded = add_assignee(remove_assignee(state, "Dana"), "Dana")
    assert list_assignees(readded) == ("Ari", "Bo", "Cy", "Dana")


def test_assignee_actions_preserve_the_input_and_projects():
    """CP-105: an action returns a new state and keeps every project and the identity counter."""
    state, _ = create_project(empty_state(), "Alpha", "first")
    state, _ = create_project(state, "Beta", "")
    state = add_assignee(state, "Dana")

    added = add_assignee(state, "Ari")
    removed = remove_assignee(state, "Dana")

    assert list_assignees(state) == ("Dana",)
    for result in (added, removed):
        assert result.projects == state.projects
        assert result.next_project_id == state.next_project_id
    with pytest.raises(BlankName):
        add_assignee(state, "  ")
    with pytest.raises(AssigneeNotFound):
        remove_assignee(state, "Ari")
    assert list_assignees(state) == ("Dana",)


@pytest.mark.parametrize(
    "blank",
    ["", " ", "   ", "\t", "\n", " \t\r\n ", " ", "　", "  "],
    ids=[
        "empty",
        "one-space",
        "three-spaces",
        "tab",
        "line-break",
        "mixed-ascii",
        "no-break-space",
        "ideographic-space",
        "unicode-spaces",
    ],
)
def test_blank_assignee_is_refused(blank):
    """CP-89: empty and whitespace-only names raise BlankName, and nothing is added."""
    state = _state_with("Dana")

    with pytest.raises(BlankName):
        add_assignee(state, blank)
    assert list_assignees(state) == ("Dana",)


def test_exact_duplicate_assignee_is_refused():
    """CP-90: only the exact listed value is a duplicate."""
    state = _state_with("Dana")

    with pytest.raises(AssigneeNameInUse):
        add_assignee(state, "Dana")

    for different in ("dana", "Dana ", " Dana", "DANA"):
        assert list_assignees(add_assignee(state, different)) == ("Dana", different)


def test_assignee_length_is_in_unicode_code_points():
    """CP-91: 200 code points pass, 201 do not; length is checked before blank."""
    assert SHORT_TEXT_MAX == 200
    longest = "n" * SHORT_TEXT_MAX
    assert list_assignees(add_assignee(empty_state(), longest)) == (longest,)

    astral = "\U0001d11e" * SHORT_TEXT_MAX
    assert list_assignees(add_assignee(empty_state(), astral)) == (astral,)

    for too_long in ("n" * 201, "\U0001d11e" * 201, " " * 201):
        with pytest.raises(TextTooLong) as refusal:
            add_assignee(empty_state(), too_long)
        assert refusal.value.field is TextField.NAME
        assert refusal.value.maximum == SHORT_TEXT_MAX


def test_assignee_actions_use_the_state_given_now():
    """CP-92, CP-96: each action is decided by the list it is given, not by an earlier one."""
    stale = _state_with("Dana")
    current = add_assignee(stale, "Eve")

    add_assignee(stale, "Eve")
    with pytest.raises(AssigneeNameInUse):
        add_assignee(current, "Eve")

    removed = remove_assignee(current, "Dana")
    with pytest.raises(AssigneeNotFound):
        remove_assignee(removed, "Dana")

    readded = add_assignee(removed, "Dana")
    assert list_assignees(remove_assignee(readded, "Dana")) == ("Eve",)


def test_the_assignee_refusals_are_typed_refusals_with_no_wording():
    """FR-39: a part tells a refusal by type alone, and the domain carries no operator wording."""
    for refusal in (AssigneeNameInUse, AssigneeNotFound):
        assert issubclass(refusal, Refusal)
        assert str(refusal()) == ""
