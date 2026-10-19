"""Unit tests of the operator name rule in domain (layer 1), with no file, no clock, no network.

Checks SRS FR-27 (the operator's name), FR-39 and FR-40 (refusals and the maximum length) and DR-5
(the one operator name, which no action clears). Change spec rules CP-217 to CP-221 and CP-229 to
CP-231 are the ones each test names. The rule lives in domain/operator_name.py; restoration of a
saved name goes through domain/state.py, which tests/unit/test_state.py checks.
"""

from __future__ import annotations

import dataclasses

import pytest

from domain import (
    SHORT_TEXT_MAX,
    BlankName,
    OperatorNameOutcome,
    TextField,
    TextTooLong,
    TrackerState,
    add_assignee,
    check_operator_name,
    create_project,
    empty_state,
    set_operator_name,
)

BLANK_FORMS = ("", "   ", "\t", "\u00a0", "\u3000")
NON_BMP = "\U0001f600"


def _rich_state(operator_name: str | None = None) -> TrackerState:
    """A state holding a project, an assignee and both counters, so a name change can be seen to
    touch nothing else."""
    state, _ = create_project(empty_state(), "Alpha", "first")
    state = add_assignee(state, "Dana")
    return dataclasses.replace(state, operator_name=operator_name, next_task_id=7)


@pytest.mark.parametrize("blank", BLANK_FORMS)
def test_operator_name_refuses_each_blank_value(blank: str):
    """CP-220: empty, spaces, a tab, U+00A0 and U+3000 are blank, through both entry points."""
    state = _rich_state()

    with pytest.raises(BlankName):
        check_operator_name(blank)
    with pytest.raises(BlankName):
        set_operator_name(state, blank)

    assert state == _rich_state()


def test_operator_name_keeps_surrounding_spaces_and_case():
    """CP-217, CP-220: a valid string comes back verbatim; U+200B alone is not whitespace."""
    for name in (" Sam ", "sAM", "Sam  Lee", "\u200b"):
        assert check_operator_name(name) == name
        new_state, outcome = set_operator_name(empty_state(), name)
        assert new_state.operator_name == name
        assert outcome == OperatorNameOutcome(name=name, changed=True)


def test_operator_name_accepts_200_code_points_including_non_bmp():
    """CP-217: the boundary is accepted, spaces count, and a character outside the BMP counts
    once."""
    name = " " + "a" * 197 + NON_BMP + " "
    assert len(name) == SHORT_TEXT_MAX

    assert check_operator_name(name) == name
    assert set_operator_name(empty_state(), name)[0].operator_name == name


def test_operator_name_refuses_201_code_points_before_blankness():
    """CP-221: one over the maximum is too long, and 201 spaces are too long rather than blank."""
    for over_long in ("a" * 201, " " * 201, "a" * 200 + NON_BMP):
        with pytest.raises(TextTooLong) as refused:
            check_operator_name(over_long)
        assert refused.value.field is TextField.NAME
        assert refused.value.maximum == SHORT_TEXT_MAX

        with pytest.raises(TextTooLong):
            set_operator_name(empty_state(), over_long)


def test_first_name_and_replacement_change_only_the_name():
    """CP-216, CP-229: a first name and a replacement each report a change; nothing else moves."""
    before = _rich_state()

    first_state, first = set_operator_name(before, "Sam")
    replaced_state, replaced = set_operator_name(first_state, "Sam Lee")

    assert first == OperatorNameOutcome(name="Sam", changed=True)
    assert replaced == OperatorNameOutcome(name="Sam Lee", changed=True)
    assert first_state == dataclasses.replace(before, operator_name="Sam")
    assert replaced_state == dataclasses.replace(before, operator_name="Sam Lee")
    assert before == _rich_state()
    assert replaced_state.projects == before.projects
    assert replaced_state.assignees == before.assignees
    assert replaced_state.tasks == before.tasks
    assert replaced_state.next_project_id == before.next_project_id
    assert replaced_state.next_task_id == before.next_task_id


def test_same_name_returns_unchanged_outcome_and_original_state():
    """CP-218: an exact match changes nothing; a space or a case difference is a different name."""
    state = _rich_state("Sam")

    same_state, same = set_operator_name(state, "Sam")
    assert same == OperatorNameOutcome(name="Sam", changed=False)
    assert same_state is state

    for different in ("Sam ", "sam", " Sam"):
        new_state, outcome = set_operator_name(state, different)
        assert outcome == OperatorNameOutcome(name=different, changed=True)
        assert new_state.operator_name == different


@pytest.mark.parametrize("saved", (None, "Sam"))
@pytest.mark.parametrize("blank", BLANK_FORMS)
def test_blank_name_cannot_clear_a_saved_name(saved: str | None, blank: str):
    """CP-219, CP-220: each blank form is refused from an unset and from a set state, and the
    state it was refused on still holds what it held."""
    state = _rich_state(saved)

    with pytest.raises(BlankName):
        set_operator_name(state, blank)

    assert state.operator_name == saved


def test_operator_name_outcome_is_immutable():
    """CP-230 (QC-6): the outcome is a frozen value."""
    outcome = OperatorNameOutcome(name="Sam", changed=True)

    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.name = "Other"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.changed = False  # type: ignore[misc]
