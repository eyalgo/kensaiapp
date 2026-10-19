"""Unit tests of the project rules in domain (layer 1).

Checks SRS FR-10 (create a project), FR-11 (list projects), FR-39 and FR-40 (refusals and maximum
lengths), DR-1 (the project entity) and AC-12 (each refusal gives its own reason). Change spec rules
CP-12 to CP-16 and CP-20 are the ones each test names.
"""

from __future__ import annotations

import dataclasses

import pytest

from domain import (
    LONG_TEXT_MAX,
    SHORT_TEXT_MAX,
    BlankName,
    NameInUse,
    Project,
    Refusal,
    TextField,
    TextTooLong,
    create_project,
    empty_state,
    find_project,
    list_projects,
)
from errors import AppError


def _state_with(*names: str):
    state = empty_state()
    for name in names:
        state, _ = create_project(state, name, "")
    return state


def test_list_orders_names_ignoring_letter_case():
    state = _state_with("beta", "Alpha", "alpha")

    assert [project.name for project in list_projects(state)] == ["Alpha", "alpha", "beta"]


def test_list_orders_non_ascii_names_ignoring_letter_case():
    state = _state_with("émile", "Émile", "Zed", "Ägir")

    assert [project.name for project in list_projects(state)] == ["Zed", "Ägir", "Émile", "émile"]


def test_name_and_description_are_kept_exactly_as_given():
    _, project = create_project(empty_state(), "  Alpha  ", "line one\nline two")

    assert project.name == "  Alpha  "
    assert project.description == "line one\nline two"


@pytest.mark.parametrize(
    "blank",
    ["", "   ", "\t", "\n", " \t\n ", "  "],
    ids=["empty", "three-spaces", "tab", "line-break", "mixed", "two-no-break-spaces"],
)
def test_a_blank_name_is_refused(blank):
    with pytest.raises(BlankName):
        create_project(empty_state(), blank, "")


def test_a_name_in_use_is_refused_by_exact_text():
    state = _state_with("Alpha")

    with pytest.raises(NameInUse):
        create_project(state, "Alpha", "")
    create_project(state, "alpha", "")
    create_project(state, "Alpha ", "")


def test_length_limits_are_inclusive():
    _, project = create_project(empty_state(), "n" * 200, "d" * 4000)
    assert len(project.name) == 200 and len(project.description) == 4000

    with pytest.raises(TextTooLong) as name_error:
        create_project(empty_state(), "n" * 201, "")
    assert name_error.value.field is TextField.NAME
    assert name_error.value.maximum == 200

    with pytest.raises(TextTooLong) as description_error:
        create_project(empty_state(), "Alpha", "d" * 4001)
    assert description_error.value.field is TextField.DESCRIPTION
    assert description_error.value.maximum == 4000


def test_the_maximums_are_stated_in_domain():
    assert SHORT_TEXT_MAX == 200
    assert LONG_TEXT_MAX == 4000


def test_a_character_outside_the_basic_plane_counts_as_one():
    emoji = "\U0001f600"
    create_project(empty_state(), emoji * 200, "")
    with pytest.raises(TextTooLong):
        create_project(empty_state(), emoji * 201, "")
    create_project(empty_state(), "Alpha", emoji * 4000)


def test_a_line_break_counts_as_one_character():
    create_project(empty_state(), "Alpha", "\n" * 4000)
    with pytest.raises(TextTooLong):
        create_project(empty_state(), "Alpha", "\n" * 4001)


def test_over_long_wins_over_blank_and_in_use():
    state = _state_with("Alpha")

    with pytest.raises(TextTooLong) as over_long_name_and_blank_name:
        create_project(state, " " * 201, "")
    assert over_long_name_and_blank_name.value.field is TextField.NAME

    with pytest.raises(TextTooLong) as blank_name_and_long_description:
        create_project(state, "   ", "d" * 4001)
    assert blank_name_and_long_description.value.field is TextField.DESCRIPTION

    with pytest.raises(TextTooLong) as in_use_and_long_description:
        create_project(state, "Alpha", "d" * 4001)
    assert in_use_and_long_description.value.field is TextField.DESCRIPTION

    with pytest.raises(TextTooLong) as both_long:
        create_project(state, "n" * 201, "d" * 4001)
    assert both_long.value.field is TextField.NAME


def test_identities_rise_from_one_and_the_counter_moves_on():
    state, first = create_project(empty_state(), "Alpha", "")
    assert first.id == 1
    assert state.next_project_id == 2

    state, second = create_project(state, "Beta", "")
    assert second.id == 2
    assert state.next_project_id == 3


def test_a_refused_create_returns_no_new_state():
    state = _state_with("Alpha")
    before = (state.projects, state.next_project_id)

    for name, description in [("", ""), ("Alpha", ""), ("n" * 201, "")]:
        with pytest.raises(Refusal):
            create_project(state, name, description)

    assert (state.projects, state.next_project_id) == before


def test_find_project_returns_none_for_an_unknown_identity():
    state, project = create_project(empty_state(), "Alpha", "")

    assert find_project(state, project.id) == project
    assert find_project(state, 99) is None


def test_the_predecessors_project_name_rules_come_over():
    # tracker16-X's project-name tests (SDD § 11 R-5), re-expressed for these rules.
    project = Project(id=1, name="alpha", description="")
    with pytest.raises(dataclasses.FrozenInstanceError):
        project.name = "beta"  # type: ignore[misc]
    assert (project.id, project.name, project.description) == (1, "alpha", "")

    with pytest.raises(BlankName):
        create_project(empty_state(), "", "")
    with pytest.raises(BlankName):
        create_project(empty_state(), "   ", "")
    _, kept = create_project(empty_state(), "  alpha  ", "")
    assert kept.name == "  alpha  "


def test_every_refusal_is_an_app_error_and_a_refusal():
    for refusal in (BlankName, NameInUse, TextTooLong):
        assert issubclass(refusal, Refusal)
        assert issubclass(refusal, AppError)
