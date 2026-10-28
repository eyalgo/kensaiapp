"""Unit tests of the project rules in domain (layer 1).

Checks SRS FR-10 (create a project), FR-11 (list projects), FR-12 (rename a project, leaving its
tasks the same tasks), FR-39 and FR-40 (refusals and maximum lengths), DR-1 (the project entity) and
AC-12 (each refusal gives its own reason). Change spec rules CP-12 to CP-16 and CP-20 are the ones
the creation tests name; CP-551 to CP-555 and CP-558 are the ones the rename tests name.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

import pytest

from domain import (
    LONG_TEXT_MAX,
    SHORT_TEXT_MAX,
    BlankName,
    NameInUse,
    Project,
    ProjectNotFound,
    ProjectRenameOutcome,
    Refusal,
    TextField,
    TextTooLong,
    add_assignee,
    add_task,
    add_task_comment,
    add_task_label,
    create_project,
    empty_state,
    find_project,
    list_projects,
    rename_project,
    set_operator_name,
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


WRITTEN_AT = datetime(2026, 10, 28, 9, 30, tzinfo=timezone.utc)


def _state_with_work():
    """Alpha (with a description and two tasks, one commented and labelled), Gamma and delta."""
    state, _ = create_project(empty_state(), "Alpha", "Alpha's description")
    state, _ = create_project(state, "Gamma", "")
    state, _ = create_project(state, "delta", "Another description")
    state, _ = set_operator_name(state, "Dana")
    state = add_assignee(state, "Dana")
    state, _ = add_task(state, 1, "First", "high", "Dana", "2026-11-01", WRITTEN_AT)
    state, _ = add_task(state, 1, "Second", "", "", "", WRITTEN_AT)
    state, _ = add_task(state, 2, "Elsewhere", "", "", "", WRITTEN_AT)
    state, _ = add_task_label(state, 1, "ui")
    state, _ = add_task_comment(state, 1, "Looks fine", WRITTEN_AT)
    return state


def test_rename_changes_only_the_selected_project_name():
    state = _state_with_work()
    before = dataclasses.replace(state)

    new_state, _ = rename_project(state, 1, "Zed")

    expected = dataclasses.replace(
        state,
        projects=(
            Project(id=1, name="Zed", description="Alpha's description"),
            Project(id=2, name="Gamma", description=""),
            Project(id=3, name="delta", description="Another description"),
        ),
    )
    assert new_state == expected
    assert new_state.tasks is state.tasks
    assert new_state.next_task_id == state.next_task_id
    assert new_state.next_project_id == state.next_project_id
    assert new_state.operator_name == "Dana"
    assert new_state.assignees == ("Dana",)
    assert state == before


def test_rename_reports_the_current_and_previous_name():
    state = _state_with_work()

    _, outcome = rename_project(state, 1, "Zed")

    assert outcome == ProjectRenameOutcome(
        project=Project(id=1, name="Zed", description="Alpha's description"),
        previous_name="Alpha",
        changed=True,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.changed = False  # type: ignore[misc]


def test_own_name_is_accepted_without_a_change():
    state = _state_with_work()

    new_state, outcome = rename_project(state, 1, "Alpha")

    assert new_state is state
    assert outcome == ProjectRenameOutcome(
        project=find_project(state, 1), previous_name="Alpha", changed=False
    )


def test_rename_keeps_case_spaces_and_code_points():
    state = _state_with_work()
    long_name = "\U0001f600" * 199 + "é"

    case_only, case_outcome = rename_project(state, 1, "alpha")
    spaced, spaced_outcome = rename_project(state, 1, " Alpha ")
    longest, longest_outcome = rename_project(state, 1, long_name)
    unchanged_by_trailing_space, trailing_outcome = rename_project(state, 1, "Alpha ")

    assert case_outcome.changed and find_project(case_only, 1).name == "alpha"
    assert spaced_outcome.changed and find_project(spaced, 1).name == " Alpha "
    assert longest_outcome.changed and find_project(longest, 1).name == long_name
    assert len(long_name) == SHORT_TEXT_MAX
    assert trailing_outcome.changed
    assert find_project(unchanged_by_trailing_space, 1).name == "Alpha "
    assert rename_project(state, 1, "a\nb")[1].project.name == "a\nb"


@pytest.mark.parametrize(
    "blank",
    ["", "   ", "\t", "\n", " \t\n ", "\u00a0\u00a0", "\u3000"],
    ids=["empty", "spaces", "tab", "line-break", "mixed", "no-break-spaces", "ideographic-space"],
)
def test_rename_refuses_blank_names_as_creation_does(blank):
    state = _state_with_work()
    before = dataclasses.replace(state)

    with pytest.raises(BlankName):
        rename_project(state, 1, blank)
    with pytest.raises(BlankName):
        create_project(state, blank, "")

    assert state == before


def test_rename_refuses_only_another_projects_exact_name():
    state = _state_with_work()
    before = dataclasses.replace(state)

    with pytest.raises(NameInUse):
        rename_project(state, 1, "Gamma")
    for different in ("gamma", "Gamma ", " Gamma"):
        _, outcome = rename_project(state, 1, different)
        assert outcome.changed

    assert state == before


def test_rename_refuses_overlong_before_blank():
    state = _state_with_work()
    before = dataclasses.replace(state)

    for name in ("n" * 201, " " * 201):
        with pytest.raises(TextTooLong) as refused:
            rename_project(state, 1, name)
        assert refused.value.field is TextField.NAME
        assert refused.value.maximum == SHORT_TEXT_MAX

    assert state == before


def test_missing_rename_target_precedes_name_validation():
    state = _state_with_work()
    before = dataclasses.replace(state)

    for name in ("Zed", "", "   ", "Gamma", "n" * 201):
        with pytest.raises(ProjectNotFound):
            rename_project(state, 99, name)

    assert state == before


def test_a_renamed_project_is_listed_by_the_explicit_order_not_its_position():
    state = _state_with_work()

    renamed, _ = rename_project(state, 1, "Zed")
    assert [project.name for project in renamed.projects] == ["Zed", "Gamma", "delta"]
    assert [project.name for project in list_projects(renamed)] == ["delta", "Gamma", "Zed"]

    tied, _ = rename_project(state, 1, "gamma")
    assert [project.name for project in list_projects(tied)] == ["delta", "Gamma", "gamma"]


def test_creation_still_refuses_the_description_before_a_blank_name():
    state = _state_with_work()

    with pytest.raises(TextTooLong) as refused:
        create_project(state, "   ", "d" * 4001)

    assert refused.value.field is TextField.DESCRIPTION
