"""Unit tests of the sort rules in domain/sorting.py (layer 1), with no file and no clock.

Checks SRS FR-36 (a task list sorts by one field at a time, ties and created time follow the
creation order), FR-39 (each refusal is typed) and AC-12, AC-14 (the refusals and the sorting
tests). Change spec rules CP-428 to CP-435 and CP-441 to CP-443 and CP-447 and CP-448 are the ones
each test names. The design rows T1 to T3 are the coverage references.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime, timedelta

import pytest

from domain import (
    FilterInput,
    FilterRefused,
    InvalidFilterStatus,
    InvalidSortDirection,
    InvalidSortField,
    Priority,
    Project,
    ProjectListRefused,
    Refusal,
    RepeatedFilterValue,
    RepeatedSortValue,
    ReversedFilterRange,
    SortControl,
    SortDirection,
    SortedSelection,
    SortFieldRefusal,
    SortInput,
    SortKey,
    Task,
    TaskFilter,
    TaskSort,
    TaskStatus,
    TrackerState,
    filter_project_tasks,
    list_project_tasks,
    sort_project_tasks,
)

TODAY = date(2026, 10, 6)
CREATED = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
NO_FILTER = FilterInput()
ASCENDING = ("ascending",)
DESCENDING = ("descending",)


def make_task(
    task_id: int,
    *,
    project_id: int = 1,
    title: str | None = None,
    status: TaskStatus = TaskStatus.TODO,
    priority: Priority = Priority.MEDIUM,
    assignee: str | None = None,
    labels: tuple[str, ...] = (),
    due: date | None = None,
    created_at: datetime = CREATED,
) -> Task:
    return Task(
        id=task_id,
        project_id=project_id,
        title=f"task {task_id}" if title is None else title,
        status=status,
        priority=priority,
        assignee=assignee,
        labels=labels,
        due_date=due,
        created_at=created_at,
        comments=(),
    )


def make_state(*tasks: Task, assignees: tuple[str, ...] = ("dana", "ali")) -> TrackerState:
    return TrackerState(
        projects=(Project(1, "One", ""), Project(2, "Two", "")),
        next_project_id=3,
        assignees=assignees,
        tasks=tasks,
        next_task_id=max((task.id for task in tasks), default=0) + 1,
    )


def sort_of(field: str, direction: str = "") -> SortInput:
    return SortInput(field=(field,), direction=(direction,) if direction else ())


def ordered(
    state: TrackerState, sort_fields: SortInput, fields: FilterInput = NO_FILTER
) -> list[int]:
    return [task.id for task in sort_project_tasks(state, 1, fields, sort_fields, TODAY).tasks]


def refused(
    state: TrackerState, sort_fields: SortInput, fields: FilterInput = NO_FILTER
) -> ProjectListRefused:
    with pytest.raises(ProjectListRefused) as caught:
        sort_project_tasks(state, 1, fields, sort_fields, TODAY)
    return caught.value


def test_due_sort_keeps_undated_last_and_identity_ties() -> None:
    state = make_state(
        make_task(1, due=date(2026, 10, 9)),
        make_task(2),
        make_task(3, due=date(2026, 10, 1)),
        make_task(4, due=date(2026, 10, 9)),
        make_task(5),
        make_task(6, due=date(2026, 10, 1)),
    )
    assert ordered(state, sort_of("due_date", "ascending")) == [3, 6, 1, 4, 2, 5]
    assert ordered(state, sort_of("due_date", "descending")) == [1, 4, 3, 6, 2, 5]


def test_due_sort_of_all_undated_tasks_keeps_identity_order_in_both_directions() -> None:
    state = make_state(make_task(7), make_task(2), make_task(5))
    assert ordered(state, sort_of("due_date", "ascending")) == [2, 5, 7]
    assert ordered(state, sort_of("due_date", "descending")) == [2, 5, 7]


def test_due_sort_with_one_dated_task_among_undated_puts_it_first_in_both_directions() -> None:
    state = make_state(make_task(1), make_task(2, due=date(2026, 1, 1)), make_task(3))
    assert ordered(state, sort_of("due_date", "ascending")) == [2, 1, 3]
    assert ordered(state, sort_of("due_date", "descending")) == [2, 1, 3]


def test_priority_sort_uses_all_four_ranks_and_identity_ties() -> None:
    state = make_state(
        make_task(1, priority=Priority.HIGH),
        make_task(2, priority=Priority.LOW),
        make_task(3, priority=Priority.CRITICAL),
        make_task(4, priority=Priority.MEDIUM),
        make_task(5, priority=Priority.HIGH),
        make_task(6, priority=Priority.LOW),
    )
    assert ordered(state, sort_of("priority", "ascending")) == [2, 6, 4, 1, 5, 3]
    assert ordered(state, sort_of("priority", "descending")) == [3, 1, 5, 4, 2, 6]


def test_title_sort_casefolds_then_compares_code_points() -> None:
    state = make_state(
        make_task(1, title="beta"), make_task(2, title="Alpha"), make_task(3, title="alpha")
    )
    assert ordered(state, sort_of("title", "ascending")) == [2, 3, 1]
    assert ordered(state, sort_of("title", "descending")) == [1, 2, 3]


def test_title_sort_treats_sharp_s_and_its_expansion_as_a_tie() -> None:
    state = make_state(
        make_task(1, title="STRASSE"), make_task(2, title="Straße"), make_task(3, title="strasse")
    )
    assert ordered(state, sort_of("title", "ascending")) == [1, 2, 3]
    assert ordered(state, sort_of("title", "descending")) == [1, 2, 3]


def test_title_sort_compares_the_rest_by_code_point_not_by_language_rules() -> None:
    state = make_state(
        make_task(1, title="émile"),
        make_task(2, title="zed"),
        make_task(3, title="Zebra"),
        make_task(4, title="1 first"),
        make_task(5, title="_under"),
    )
    assert ordered(state, sort_of("title", "ascending")) == [4, 5, 3, 2, 1]
    assert ordered(state, sort_of("title", "descending")) == [1, 2, 3, 5, 4]


def test_title_sort_puts_task_10_before_task_2_ascending() -> None:
    state = make_state(make_task(1, title="Task 2"), make_task(2, title="Task 10"))
    assert ordered(state, sort_of("title", "ascending")) == [2, 1]
    assert ordered(state, sort_of("title", "descending")) == [1, 2]


def test_created_sort_follows_identity_despite_recorded_time() -> None:
    later = CREATED + timedelta(days=3)
    earlier = CREATED - timedelta(days=3)
    state = make_state(
        make_task(9, created_at=earlier),
        make_task(4, created_at=CREATED),
        make_task(6, created_at=later),
        make_task(5, created_at=CREATED),
        make_task(20, created_at=CREATED),
    )
    assert ordered(state, sort_of("created_time", "ascending")) == [4, 5, 6, 9, 20]
    assert ordered(state, sort_of("created_time", "descending")) == [20, 9, 6, 5, 4]


def test_created_sort_with_equal_recorded_times_still_follows_identity() -> None:
    state = make_state(make_task(3), make_task(1), make_task(2))
    assert ordered(state, sort_of("created_time", "ascending")) == [1, 2, 3]
    assert ordered(state, sort_of("created_time", "descending")) == [3, 2, 1]


@pytest.mark.parametrize(
    ("sort_fields", "expected_key", "expected_direction"),
    [
        (SortInput(), SortKey.DUE_DATE, SortDirection.ASCENDING),
        (SortInput(field=("",), direction=("",)), SortKey.DUE_DATE, SortDirection.ASCENDING),
        (SortInput(field=("",)), SortKey.DUE_DATE, SortDirection.ASCENDING),
        (SortInput(direction=("",)), SortKey.DUE_DATE, SortDirection.ASCENDING),
        (SortInput(field=("title",)), SortKey.TITLE, SortDirection.ASCENDING),
        (SortInput(field=("title",), direction=("",)), SortKey.TITLE, SortDirection.ASCENDING),
        (SortInput(direction=ASCENDING), SortKey.DUE_DATE, SortDirection.ASCENDING),
        (SortInput(direction=DESCENDING), SortKey.DUE_DATE, SortDirection.DESCENDING),
        (SortInput(field=("",), direction=DESCENDING), SortKey.DUE_DATE, SortDirection.DESCENDING),
        (
            SortInput(field=("priority",), direction=("",)),
            SortKey.PRIORITY,
            SortDirection.ASCENDING,
        ),
        (
            SortInput(field=("created_time",), direction=DESCENDING),
            SortKey.CREATED_TIME,
            SortDirection.DESCENDING,
        ),
    ],
)
def test_sort_defaults_each_unset_control_independently(
    sort_fields: SortInput, expected_key: SortKey, expected_direction: SortDirection
) -> None:
    state = make_state(make_task(1), make_task(2))
    chosen = sort_project_tasks(state, 1, FilterInput(), sort_fields, TODAY).sorting
    assert chosen.key is expected_key
    assert chosen.direction is expected_direction


def test_an_unset_sort_orders_as_the_list_does_today() -> None:
    state = make_state(
        make_task(1, due=date(2026, 10, 9)),
        make_task(2),
        make_task(3, due=date(2026, 10, 1)),
        make_task(4, due=date(2026, 10, 9)),
    )
    assert ordered(state, SortInput()) == [t.id for t in list_project_tasks(state, 1)]
    assert ordered(state, SortInput()) == [3, 1, 4, 2]


def test_a_direction_alone_sorts_by_due_date_in_that_direction() -> None:
    state = make_state(
        make_task(1, due=date(2026, 10, 1)), make_task(2, due=date(2026, 10, 9)), make_task(3)
    )
    assert ordered(state, SortInput(direction=DESCENDING)) == [2, 1, 3]


def test_a_field_alone_sorts_ascending() -> None:
    state = make_state(make_task(1, priority=Priority.HIGH), make_task(2, priority=Priority.LOW))
    assert ordered(state, SortInput(field=("priority",))) == [2, 1]


@pytest.mark.parametrize(
    ("sort_fields", "requested"),
    [
        (SortInput(), False),
        (SortInput(field=("",)), False),
        (SortInput(direction=("",)), False),
        (SortInput(field=("",), direction=("",)), False),
        (SortInput(field=("due_date",)), True),
        (SortInput(direction=ASCENDING), True),
        (SortInput(field=("due_date",), direction=ASCENDING), True),
        (SortInput(field=("",), direction=ASCENDING), True),
        (SortInput(field=("title",), direction=("",)), True),
    ],
)
def test_sort_request_uses_nonempty_raw_choices(sort_fields: SortInput, requested: bool) -> None:
    state = make_state(make_task(1), make_task(2))
    selection = sort_project_tasks(state, 1, FilterInput(), sort_fields, TODAY)
    assert selection.sorting.requested is requested
    assert selection.count_requested is requested


def test_count_is_requested_by_a_filter_alone_a_sort_alone_or_both() -> None:
    state = make_state(make_task(1), make_task(2, status=TaskStatus.DONE))
    filter_only = sort_project_tasks(state, 1, FilterInput(status=("done",)), SortInput(), TODAY)
    sort_only = sort_project_tasks(state, 1, FilterInput(), sort_of("title"), TODAY)
    both = sort_project_tasks(
        state, 1, FilterInput(status=("done",)), sort_of("title", "descending"), TODAY
    )
    neither = sort_project_tasks(state, 1, FilterInput(status=("",)), SortInput(), TODAY)
    assert filter_only.count_requested is True
    assert sort_only.count_requested is True
    assert both.count_requested is True
    assert neither.count_requested is False


def test_count_is_not_requested_for_a_blank_filter_beside_a_blank_sort() -> None:
    state = make_state(make_task(1))
    blank = FilterInput(status=("",), label=("",), due_from=("",))
    selection = sort_project_tasks(state, 1, blank, SortInput(field=("",), direction=("",)), TODAY)
    assert selection.count_requested is False
    assert selection.match_count == 1


def test_a_sort_with_a_nonempty_default_choice_requests_a_count_even_with_a_blank_filter() -> None:
    state = make_state(make_task(1))
    selection = sort_project_tasks(
        state, 1, FilterInput(status=("",)), sort_of("due_date", "ascending"), TODAY
    )
    assert selection.count_requested is True
    assert selection.filter == TaskFilter()


FILTERS = [
    FilterInput(status=("done",)),
    FilterInput(priority=("high",)),
    FilterInput(assignee=("dana",)),
    FilterInput(label=("red",)),
    FilterInput(due_from=("2026-10-05",)),
    FilterInput(due_to=("2026-10-05",)),
    FilterInput(due_from=("2026-10-02",), due_to=("2026-10-08",)),
    FilterInput(overdue=("on",)),
    FilterInput(status=("todo",), priority=("high",), label=("red",)),
]


def membership_state() -> TrackerState:
    return make_state(
        make_task(1, status=TaskStatus.DONE, priority=Priority.HIGH, due=date(2026, 10, 1)),
        make_task(2, assignee="dana", labels=("red",), due=date(2026, 10, 7)),
        make_task(3, priority=Priority.HIGH, labels=("red", "blue"), due=date(2026, 10, 3)),
        make_task(4, assignee="dana", due=date(2026, 10, 5)),
        make_task(5, status=TaskStatus.IN_PROGRESS, due=date(2026, 10, 2)),
        make_task(6, priority=Priority.CRITICAL),
        make_task(7, project_id=2, priority=Priority.HIGH, labels=("red",)),
    )


@pytest.mark.parametrize("fields", FILTERS)
@pytest.mark.parametrize("key", [key.value for key in SortKey])
@pytest.mark.parametrize("direction", ["ascending", "descending"])
def test_sort_keeps_filter_membership(fields: FilterInput, key: str, direction: str) -> None:
    state = membership_state()
    members = {task.id for task in filter_project_tasks(state, 1, fields, TODAY).tasks}
    result = sort_project_tasks(state, 1, fields, sort_of(key, direction), TODAY)
    assert {task.id for task in result.tasks} == members
    assert len(result.tasks) == len(members) == result.match_count


def test_sort_keeps_full_project_options_with_a_labelled_task_filtered_out() -> None:
    state = membership_state()
    selection = sort_project_tasks(
        state, 1, FilterInput(status=("in-progress",)), sort_of("title", "descending"), TODAY
    )
    assert selection.task_count == 6
    assert selection.match_count == 1
    assert selection.labels == ("blue", "red")
    assert selection.assignees == ("dana", "ali")
    assert selection.filter == TaskFilter(status=TaskStatus.IN_PROGRESS)
    assert selection.sorting == TaskSort(SortKey.TITLE, SortDirection.DESCENDING, True)


def test_sort_ignores_other_projects_tasks() -> None:
    state = membership_state()
    assert 7 not in ordered(state, sort_of("created_time", "descending"))


@pytest.mark.parametrize(
    "token",
    ["colour", "Title", "TITLE", " title", "title ", "due-date", "due date", "x", "Due_Date"],
)
def test_sort_refuses_unknown_field_tokens_by_concrete_type(token: str) -> None:
    problem = refused(make_state(make_task(1)), SortInput(field=(token,)))
    (reason,) = problem.refusals
    assert isinstance(reason, InvalidSortField)
    assert reason.control is SortControl.FIELD
    assert reason.value == token


@pytest.mark.parametrize(
    "token", ["sideways", "Ascending", "DESC", " ascending", "descending ", "asc", "up"]
)
def test_sort_refuses_unknown_direction_tokens_by_concrete_type(token: str) -> None:
    problem = refused(make_state(make_task(1)), SortInput(direction=(token,)))
    (reason,) = problem.refusals
    assert isinstance(reason, InvalidSortDirection)
    assert reason.control is SortControl.DIRECTION
    assert reason.value == token


def test_sort_refusals_derive_from_the_domain_refusal_and_name_their_control() -> None:
    state = make_state(make_task(1))
    reasons = refused(state, SortInput(field=("x",), direction=("y",))).refusals
    for reason in reasons:
        assert isinstance(reason, SortFieldRefusal)
        assert isinstance(reason, Refusal)
    assert issubclass(ProjectListRefused, Refusal)


@pytest.mark.parametrize(
    "values", [("title", "title"), ("", ""), ("title", ""), ("", "title"), ("a", "b", "c")]
)
@pytest.mark.parametrize("control", [SortControl.FIELD, SortControl.DIRECTION])
def test_sort_refuses_repeated_values_before_invalid_values(
    control: SortControl, values: tuple[str, ...]
) -> None:
    sort_fields = SortInput(**{control.value: values})
    problem = refused(make_state(make_task(1)), sort_fields)
    (reason,) = problem.refusals
    assert isinstance(reason, RepeatedSortValue)
    assert reason.control is control
    assert reason.count == len(values)


def test_a_repeated_control_gets_no_second_refusal_while_the_other_is_still_checked() -> None:
    sort_fields = SortInput(field=("title", "title"), direction=("sideways",))
    reasons = refused(make_state(make_task(1)), sort_fields).refusals
    assert [type(reason) for reason in reasons] == [RepeatedSortValue, InvalidSortDirection]
    assert [reason.control for reason in reasons] == [SortControl.FIELD, SortControl.DIRECTION]


def test_both_sort_controls_refused_report_field_then_direction() -> None:
    reasons = refused(make_state(make_task(1)), SortInput(field=("x",), direction=("y",))).refusals
    assert [type(reason) for reason in reasons] == [InvalidSortField, InvalidSortDirection]


def test_list_collects_filter_and_sort_refusals_in_control_order() -> None:
    state = make_state(make_task(1))
    fields = FilterInput(due_from=("2026-10-09",), due_to=("2026-10-01",), status=("nope",))
    sort_fields = SortInput(field=("x",), direction=("sideways",))
    problem = refused(state, sort_fields, fields)
    assert [type(reason) for reason in problem.refusals] == [
        InvalidFilterStatus,
        ReversedFilterRange,
        InvalidSortField,
        InvalidSortDirection,
    ]
    assert problem.fields == fields
    assert problem.sort_fields == sort_fields


def test_a_reversed_range_with_an_invalid_direction_reports_both_reasons() -> None:
    fields = FilterInput(due_from=("2026-10-09",), due_to=("2026-10-01",))
    reasons = refused(make_state(make_task(1)), SortInput(direction=("sideways",)), fields).refusals
    assert [type(reason) for reason in reasons] == [ReversedFilterRange, InvalidSortDirection]


def test_repeated_filter_and_sort_controls_retain_every_raw_tuple_and_reason() -> None:
    fields = FilterInput(status=("todo", "done"))
    sort_fields = SortInput(field=("title", "priority"), direction=("", ""))
    problem = refused(make_state(make_task(1)), sort_fields, fields)
    assert [type(reason) for reason in problem.refusals] == [
        RepeatedFilterValue,
        RepeatedSortValue,
        RepeatedSortValue,
    ]
    assert problem.fields.status == ("todo", "done")
    assert problem.sort_fields.field == ("title", "priority")
    assert problem.sort_fields.direction == ("", "")


def test_an_invalid_filter_does_not_hide_a_valid_sort_and_the_reverse() -> None:
    state = make_state(make_task(1))
    only_filter = refused(state, sort_of("title"), FilterInput(status=("nope",)))
    assert [type(reason) for reason in only_filter.refusals] == [InvalidFilterStatus]
    only_sort = refused(state, sort_of("nope"), FilterInput(status=("todo",)))
    assert [type(reason) for reason in only_sort.refusals] == [InvalidSortField]


def test_the_filter_refusal_is_the_one_the_filter_alone_gives() -> None:
    state = make_state(make_task(1))
    fields = FilterInput(status=("nope",), priority=("a", "b"))
    with pytest.raises(FilterRefused) as alone:
        filter_project_tasks(state, 1, fields, TODAY)
    combined = refused(state, SortInput(), fields)
    assert tuple(type(r) for r in combined.refusals) == tuple(type(r) for r in alone.value.refusals)


def test_zero_matches_still_validate_sort() -> None:
    state = make_state(make_task(1))
    fields = FilterInput(status=("done",))
    problem = refused(state, sort_of("colour"), fields)
    assert [type(reason) for reason in problem.refusals] == [InvalidSortField]


def test_a_valid_zero_match_result_has_no_requested_count_and_no_tasks() -> None:
    state = make_state(make_task(1))
    for sort_fields in (SortInput(), sort_of("title", "descending")):
        selection = sort_project_tasks(state, 1, FilterInput(status=("done",)), sort_fields, TODAY)
        assert selection.tasks == ()
        assert selection.match_count == 0
        assert selection.task_count == 1
        assert selection.count_requested is False


@pytest.mark.parametrize(
    "sort_fields",
    [SortInput(), sort_of("title", "descending"), sort_of("colour"), SortInput(field=("a", "b"))],
)
@pytest.mark.parametrize(
    "fields", [FilterInput(), FilterInput(status=("done",)), FilterInput(status=("nope",))]
)
def test_empty_project_ignores_all_choices(sort_fields: SortInput, fields: FilterInput) -> None:
    state = make_state(make_task(1, project_id=2))
    selection = sort_project_tasks(state, 1, fields, sort_fields, TODAY)
    assert isinstance(selection, SortedSelection)
    assert selection.task_count == 0
    assert selection.tasks == ()
    assert selection.match_count == 0
    assert selection.count_requested is False
    assert selection.filter == TaskFilter()
    assert selection.sorting == TaskSort()
    assert selection.assignees == ("dana", "ali")


def test_sort_handles_empty_singleton_and_repeated_reads_without_mutation() -> None:
    state = make_state(make_task(3, title="c"), make_task(1, title="a"), make_task(2, title="b"))
    before_tasks = state.tasks
    first = ordered(state, sort_of("title", "descending"))
    second = ordered(state, sort_of("title", "descending"))
    assert first == second == [3, 2, 1]
    assert state.tasks is before_tasks
    assert state.tasks == before_tasks
    one = make_state(make_task(5))
    assert ordered(one, sort_of("priority", "descending")) == [5]
    assert ordered(make_state(), sort_of("title")) == []


def test_the_order_does_not_depend_on_the_state_storage_order() -> None:
    tasks = [make_task(number, title=f"t{number % 3}") for number in range(1, 8)]
    forward = make_state(*tasks)
    shuffled = make_state(*reversed(tasks))
    for key in SortKey:
        for direction in ("ascending", "descending"):
            assert ordered(forward, sort_of(key.value, direction)) == ordered(
                shuffled, sort_of(key.value, direction)
            )


def test_values_of_a_sort_input_are_read_by_control() -> None:
    sort_fields = SortInput(field=("title",), direction=("a", "b"))
    assert sort_fields.values(SortControl.FIELD) == ("title",)
    assert sort_fields.values(SortControl.DIRECTION) == ("a", "b")
    assert SortInput().field == ()
    assert SortInput().direction == ()


def test_the_closed_vocabularies_and_defaults() -> None:
    assert [key.value for key in SortKey] == ["due_date", "priority", "created_time", "title"]
    assert [direction.value for direction in SortDirection] == ["ascending", "descending"]
    assert [control for control in SortControl] == [SortControl.FIELD, SortControl.DIRECTION]
    assert TaskSort() == TaskSort(SortKey.DUE_DATE, SortDirection.ASCENDING, False)


def test_the_sort_values_are_immutable() -> None:
    state = make_state(make_task(1))
    selection = sort_project_tasks(state, 1, FilterInput(), SortInput(), TODAY)
    with pytest.raises(FrozenInstanceError):
        selection.count_requested = True  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        SortInput().field = ("x",)  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        TaskSort().key = SortKey.TITLE  # type: ignore[misc]
