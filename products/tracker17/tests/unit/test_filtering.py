"""Unit tests of the filter rules in domain/filtering.py (layer 1), with no file and no clock.

Checks SRS FR-32 (a task list is filtered by any combination of status, priority, assignee, label,
a due-date range and overdue), FR-33 (the assignee filter accepts only a listed name), FR-34 (the
due-date range, either end optional, a reversed range refused), FR-35 (the overdue filter uses the
FR-25 rule), FR-39 (each refusal is typed) and AC-12, AC-14 (the refusals and the filter tests).
Change spec rules CP-393, CP-394, CP-396, CP-397, CP-402 to CP-406, CP-411, CP-413, CP-414 and
CP-415 are the ones each test names. The design rows T1 to T3 are the coverage references.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from dataclasses import fields as dataclass_fields
from datetime import UTC, date, datetime

import pytest

from domain import (
    FilterAssigneeNotListed,
    FilterField,
    FilterInput,
    FilterOptions,
    FilterRefused,
    FilterSelection,
    InvalidFilterDueFrom,
    InvalidFilterDueTo,
    InvalidFilterOverdue,
    InvalidFilterPriority,
    InvalidFilterStatus,
    Priority,
    Project,
    Refusal,
    RepeatedFilterValue,
    ReversedFilterRange,
    Task,
    TaskFilter,
    TaskStatus,
    TrackerState,
    filter_project_tasks,
    list_project_tasks,
    project_filter_options,
)

TODAY = date(2026, 10, 6)
CREATED = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
FIELD_NAMES = ("status", "priority", "assignee", "label", "due_from", "due_to", "overdue")


def make_task(
    task_id: int,
    *,
    project_id: int = 1,
    status: TaskStatus = TaskStatus.TODO,
    priority: Priority = Priority.MEDIUM,
    assignee: str | None = None,
    labels: tuple[str, ...] = (),
    due: date | None = None,
) -> Task:
    return Task(
        id=task_id,
        project_id=project_id,
        title=f"task {task_id}",
        status=status,
        priority=priority,
        assignee=assignee,
        labels=labels,
        due_date=due,
        created_at=CREATED,
        comments=(),
    )


def make_state(*tasks: Task, assignees: tuple[str, ...] = ("dana", "ali")) -> TrackerState:
    return TrackerState(
        projects=(Project(1, "One", ""), Project(2, "Two", ""), Project(3, "Three", "")),
        next_project_id=4,
        assignees=assignees,
        tasks=tasks,
        next_task_id=max((task.id for task in tasks), default=0) + 1,
    )


def ids(selection: FilterSelection) -> list[int]:
    return [task.id for task in selection.tasks]


def select(state: TrackerState, fields: FilterInput, today: date = TODAY) -> FilterSelection:
    return filter_project_tasks(state, 1, fields, today)


def refused(state: TrackerState, fields: FilterInput, today: date = TODAY) -> FilterRefused:
    with pytest.raises(FilterRefused) as caught:
        select(state, fields, today)
    return caught.value


def one(field: str, *values: str) -> FilterInput:
    return FilterInput(**{field: tuple(values)})


MIXED = make_state(
    make_task(
        1,
        status=TaskStatus.TODO,
        priority=Priority.LOW,
        assignee="dana",
        labels=("Bug",),
        due=date(2026, 10, 1),
    ),
    make_task(
        2,
        status=TaskStatus.IN_PROGRESS,
        priority=Priority.HIGH,
        assignee="ali",
        labels=("bug",),
        due=date(2026, 10, 5),
    ),
    make_task(3, status=TaskStatus.DONE, priority=Priority.CRITICAL),
    make_task(
        4,
        status=TaskStatus.CANCELLED,
        priority=Priority.MEDIUM,
        assignee="dana",
        labels=("Bug", "ui"),
        due=date(2026, 10, 10),
    ),
    make_task(
        5,
        project_id=2,
        status=TaskStatus.TODO,
        priority=Priority.LOW,
        assignee="dana",
        labels=("Bug",),
        due=date(2026, 10, 5),
    ),
)


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        (one("status", "todo"), [1]),
        (one("status", "in-progress"), [2]),
        (one("status", "done"), [3]),
        (one("status", "cancelled"), [4]),
        (one("priority", "high"), [2]),
        (one("priority", "low"), [1]),
        (one("assignee", "dana"), [1, 4]),
        (one("assignee", "ali"), [2]),
        (one("label", "Bug"), [1, 4]),
        (one("label", "bug"), [2]),
        (one("due_from", "2026-10-05"), [2, 4]),
        (one("due_to", "2026-10-05"), [1, 2]),
        (FilterInput(due_from=("2026-10-02",), due_to=("2026-10-09",)), [2]),
        (one("overdue", "on"), [1, 2]),
    ],
)
def test_each_filter_selects_only_matching_project_tasks(fields, expected):
    """CP-396, CP-412, CP-414: six filters and both date controls, with another project's
    matching task (task 5) never shown, from the supplied state and date alone."""
    selection = select(MIXED, fields)

    assert ids(selection) == expected
    assert selection.match_count == len(expected)
    assert selection.task_count == 4


def test_filter_fields_combine_as_and():
    """CP-396: one task matches every field, and one task missing each predicate in turn does not."""
    matching = make_task(
        10,
        status=TaskStatus.IN_PROGRESS,
        priority=Priority.HIGH,
        assignee="ali",
        labels=("bug",),
        due=date(2026, 10, 5),
    )
    near_misses = [
        replace(matching, id=11, status=TaskStatus.TODO),
        replace(matching, id=12, priority=Priority.LOW),
        replace(matching, id=13, assignee="dana"),
        replace(matching, id=14, labels=("Bug",)),
        replace(matching, id=15, due_date=date(2026, 9, 30)),
        replace(matching, id=16, due_date=date(2026, 11, 1)),
        replace(matching, id=17, due_date=None),
        replace(matching, id=18, due_date=date(2026, 10, 7)),
    ]
    fields = FilterInput(
        status=("in-progress",),
        priority=("high",),
        assignee=("ali",),
        label=("bug",),
        due_from=("2026-10-01",),
        due_to=("2026-10-31",),
        overdue=("on",),
    )

    selection = select(make_state(*near_misses, matching), fields)

    assert ids(selection) == [10]
    assert selection.filter == TaskFilter(
        status=TaskStatus.IN_PROGRESS,
        priority=Priority.HIGH,
        assignee="ali",
        label="bug",
        due_from=date(2026, 10, 1),
        due_to=date(2026, 10, 31),
        overdue=True,
    )


def test_absent_and_singleton_empty_fields_do_not_narrow():
    """CP-396, CP-404: an absent field and a single empty value leave the ordered list as it is;
    Overdue absent or empty is off and `on` is on."""
    everything = list(list_project_tasks(MIXED, 1))
    empties = FilterInput(**{name: ("",) for name in FIELD_NAMES})

    for fields in (FilterInput(), empties):
        selection = select(MIXED, fields)
        assert list(selection.tasks) == everything
        assert selection.filter == TaskFilter()
        assert selection.match_count == 4

    assert select(MIXED, one("overdue", "on")).filter.overdue is True
    assert select(MIXED, one("overdue", "")).filter.overdue is False


def test_exact_labels_and_names_keep_case_and_spaces():
    """CP-396, CP-403, CP-404, CP-411: exact comparison keeps surrounding spaces and case; a single
    label no task carries is valid and matches nothing."""
    state = make_state(
        make_task(1, labels=("Bug",), assignee="dana"),
        make_task(2, labels=(" Bug",), assignee=" dana"),
        make_task(3, labels=("bug",), assignee="Dana"),
        make_task(4, labels=("Bug ",), assignee="dana "),
        assignees=("dana", " dana", "Dana", "dana "),
    )

    assert ids(select(state, one("label", "Bug"))) == [1]
    assert ids(select(state, one("label", " Bug"))) == [2]
    assert ids(select(state, one("label", "bug"))) == [3]
    assert ids(select(state, one("assignee", " dana"))) == [2]
    assert ids(select(state, one("assignee", "Dana"))) == [3]
    unknown = select(state, one("label", "nothing carries this"))
    assert unknown.tasks == ()
    assert unknown.match_count == 0
    assert unknown.task_count == 4


def test_date_ranges_include_both_boundaries():
    """CP-396, CP-402, T1: lower only, upper only, both and equal ends include their boundary date,
    and every nonempty range excludes an undated task."""
    state = make_state(
        make_task(1, due=date(2026, 10, 1)),
        make_task(2, due=date(2026, 10, 5)),
        make_task(3, due=date(2026, 10, 10)),
        make_task(4, due=None),
    )

    assert ids(select(state, one("due_from", "2026-10-05"))) == [2, 3]
    assert ids(select(state, one("due_to", "2026-10-05"))) == [1, 2]
    both = FilterInput(due_from=("2026-10-01",), due_to=("2026-10-10",))
    assert ids(select(state, both)) == [1, 2, 3]
    equal = FilterInput(due_from=("2026-10-05",), due_to=("2026-10-05",))
    assert ids(select(state, equal)) == [2]
    assert 4 not in ids(select(state, one("due_from", "2026-01-01")))
    assert 4 not in ids(select(state, one("due_to", "2026-12-31")))


def test_overdue_uses_the_supplied_day_and_open_status():
    """CP-415: yesterday and open is overdue; today, undated, and yesterday done or cancelled are
    not, and the supplied day moves the verdict."""
    yesterday, today = date(2026, 10, 5), TODAY
    state = make_state(
        make_task(1, status=TaskStatus.TODO, due=yesterday),
        make_task(2, status=TaskStatus.TODO, due=today),
        make_task(3, status=TaskStatus.TODO, due=None),
        make_task(4, status=TaskStatus.DONE, due=yesterday),
        make_task(5, status=TaskStatus.CANCELLED, due=yesterday),
        make_task(6, status=TaskStatus.IN_PROGRESS, due=yesterday),
    )

    assert ids(select(state, one("overdue", "on"))) == [1, 6]
    assert ids(select(state, one("overdue", "on"), date(2026, 10, 7))) == [1, 6, 2]
    assert ids(select(state, one("overdue", "on"), date(2026, 10, 5))) == []


@pytest.mark.parametrize(
    ("fields", "refusal", "field"),
    [
        (one("status", "blocked"), InvalidFilterStatus, FilterField.STATUS),
        (one("status", "Todo"), InvalidFilterStatus, FilterField.STATUS),
        (one("priority", "urgent"), InvalidFilterPriority, FilterField.PRIORITY),
        (one("assignee", "carol"), FilterAssigneeNotListed, FilterField.ASSIGNEE),
        (one("assignee", "Dana"), FilterAssigneeNotListed, FilterField.ASSIGNEE),
        (one("due_from", "2026/10/01"), InvalidFilterDueFrom, FilterField.DUE_FROM),
        (one("due_from", "2026-02-30"), InvalidFilterDueFrom, FilterField.DUE_FROM),
        (one("due_to", "20261001"), InvalidFilterDueTo, FilterField.DUE_TO),
        (one("due_to", "2026-02-30"), InvalidFilterDueTo, FilterField.DUE_TO),
        (one("overdue", "off"), InvalidFilterOverdue, FilterField.OVERDUE),
        (one("overdue", "true"), InvalidFilterOverdue, FilterField.OVERDUE),
        (
            FilterInput(due_from=("2026-10-10",), due_to=("2026-10-01",)),
            ReversedFilterRange,
            FilterField.DUE_FROM,
        ),
    ],
)
def test_each_invalid_filter_has_its_own_typed_refusal(fields, refusal, field):
    """CP-402, CP-403, CP-404, CP-406, T2: each condition is its own type, carrying its field
    inside the aggregate, and no other type is raised beside it."""
    problem = refused(MIXED, fields)

    assert [type(item) for item in problem.refusals] == [refusal]
    assert problem.refusals[0].field is field
    assert all(isinstance(item, Refusal) for item in problem.refusals)
    assert problem.fields == fields


def test_the_refusals_carry_what_the_page_names():
    """CP-405, CP-406: the values a reason quotes come from the refusal and not from a message."""
    status = refused(MIXED, one("status", "blocked")).refusals[0]
    assert isinstance(status, InvalidFilterStatus)
    assert status.value == "blocked"
    name = refused(MIXED, one("assignee", "carol")).refusals[0]
    assert isinstance(name, FilterAssigneeNotListed)
    assert name.name == "carol"
    reversed_range = refused(
        MIXED, FilterInput(due_from=("2026-10-10",), due_to=("2026-10-01",))
    ).refusals[0]
    assert isinstance(reversed_range, ReversedFilterRange)
    assert (reversed_range.due_from, reversed_range.due_to) == (
        date(2026, 10, 10),
        date(2026, 10, 1),
    )
    repeated = refused(MIXED, one("label", "a", "b", "c")).refusals[0]
    assert isinstance(repeated, RepeatedFilterValue)
    assert repeated.count == 3


def test_a_removed_name_still_on_a_task_is_refused_as_a_filter():
    """CP-403: a name removed from the assignee list but still carried by a task cannot be found by
    its assignee."""
    state = make_state(make_task(1, assignee="carol"), make_task(2, assignee="dana"))

    problem = refused(state, one("assignee", "carol"))

    assert [type(item) for item in problem.refusals] == [FilterAssigneeNotListed]


@pytest.mark.parametrize("field", FIELD_NAMES)
@pytest.mark.parametrize("values", [("a", "b"), ("a", "a"), ("", ""), ("", "a"), ("a", "b", "c")])
def test_repeated_values_are_refused_for_every_field(field, values):
    """CP-404, T2: every field, equal and blank duplicates included, is refused as a repetition
    before its value is parsed; one value never is."""
    problem = refused(MIXED, one(field, *values))

    assert [type(item) for item in problem.refusals] == [RepeatedFilterValue]
    repeated = problem.refusals[0]
    assert isinstance(repeated, RepeatedFilterValue)
    assert repeated.field is FilterField(field)
    assert repeated.count == len(values)


@pytest.mark.parametrize("field", FIELD_NAMES)
def test_a_singleton_empty_value_is_unset_not_repeated(field):
    """CP-404: a single empty value is an unset field in every field."""
    selection = select(MIXED, one(field, ""))

    assert selection.filter == TaskFilter()


def test_multiple_filter_problems_follow_control_order():
    """CP-405, T2: every bad field is collected in control order; a reversed range is reported on
    Due from, and a bad or repeated date end gives no reversed-range refusal."""
    status_and_range = refused(
        MIXED, FilterInput(status=("blocked",), due_from=("2026-10-10",), due_to=("2026-10-01",))
    )
    assert [(type(item), item.field) for item in status_and_range.refusals] == [
        (InvalidFilterStatus, FilterField.STATUS),
        (ReversedFilterRange, FilterField.DUE_FROM),
    ]
    range_then_overdue = refused(
        MIXED, FilterInput(due_from=("2026-10-10",), due_to=("2026-10-01",), overdue=("no",))
    )
    assert [item.field for item in range_then_overdue.refusals] == [
        FilterField.DUE_FROM,
        FilterField.OVERDUE,
    ]
    everything = refused(
        MIXED,
        FilterInput(
            status=("x",),
            priority=("y",),
            assignee=("carol",),
            label=("a", "b"),
            due_from=("nope",),
            due_to=("nope",),
            overdue=("maybe",),
        ),
    )
    assert [item.field for item in everything.refusals] == list(FilterField)
    bad_end = refused(MIXED, FilterInput(due_from=("2026-02-30",), due_to=("2026-10-01",)))
    assert [type(item) for item in bad_end.refusals] == [InvalidFilterDueFrom]
    repeated_end = refused(
        MIXED, FilterInput(due_from=("2026-10-10", "2026-10-11"), due_to=("2026-10-01",))
    )
    assert [type(item) for item in repeated_end.refusals] == [RepeatedFilterValue]


def test_filter_results_preserve_explicit_due_then_identity_order():
    """CP-397, T3: shuffled storage, tied due dates and undated ties keep the order of
    `list_project_tasks`, ascending identity within a tie."""
    state = make_state(
        make_task(9, due=None),
        make_task(7, due=date(2026, 10, 9)),
        make_task(3, due=date(2026, 10, 9)),
        make_task(8, due=date(2026, 10, 2)),
        make_task(1, due=None),
        make_task(5, due=date(2026, 10, 9)),
    )

    selection = select(state, FilterInput())

    assert ids(selection) == [8, 3, 5, 7, 1, 9]
    assert list(selection.tasks) == list(list_project_tasks(state, 1))
    narrowed = select(state, one("due_from", "2026-10-09"))
    assert ids(narrowed) == [3, 5, 7]


def test_filter_options_cover_the_whole_project():
    """CP-394, T3: `ui`, `Bug`, `bug` and duplicates give `Bug`, `bug`, `ui`; another project's
    labels are absent; filtering a labelled task out keeps its option; assignees keep list order."""
    state = make_state(
        make_task(1, labels=("ui", "Bug")),
        make_task(2, labels=("bug", "ui")),
        make_task(3, labels=("Bug",)),
        make_task(4, project_id=2, labels=("other",)),
        assignees=("dana", "ali"),
    )

    options = project_filter_options(state, 1)

    assert isinstance(options, FilterOptions)
    assert options.labels == ("Bug", "bug", "ui")
    assert options.assignees == ("dana", "ali")
    assert options.task_count == 3
    narrowed = select(state, one("label", "ui"))
    assert narrowed.labels == ("Bug", "bug", "ui")
    assert narrowed.assignees == ("dana", "ali")
    none_match = select(state, one("label", "unseen"))
    assert none_match.labels == ("Bug", "bug", "ui")


def test_filter_option_labels_are_in_code_point_order_not_case_folded_order():
    """CP-394: capitals sort before lower case, and a leading space before both."""
    state = make_state(make_task(1, labels=("apple", "Zed", " pad", "Bug")))

    assert project_filter_options(state, 1).labels == (" pad", "Bug", "Zed", "apple")


def test_empty_project_ignores_filter_validation():
    """CP-393, design § 3 A: a project with no tasks returns its empty selection even for
    malformed or repeated choices, with a full-project count of zero."""
    state = make_state(make_task(1))
    malformed = FilterInput(
        status=("blocked", "x"), due_from=("2026-10-10",), due_to=("2026-10-01",), overdue=("no",)
    )

    selection = filter_project_tasks(state, 3, malformed, TODAY)

    assert selection.task_count == 0
    assert selection.tasks == ()
    assert selection.match_count == 0
    assert project_filter_options(state, 3).task_count == 0


def test_filtering_changes_no_input_value():
    """CP-413, T2: a valid, a refused and an empty-project query leave the supplied state and the
    raw input as they were, and the values filtering returns are immutable."""
    state = MIXED
    valid = one("status", "todo")
    bad = FilterInput(status=("blocked",), label=("a", "b"))
    before = (state, valid, bad)

    selection = select(state, valid)
    problem = refused(state, bad)
    filter_project_tasks(state, 3, bad, TODAY)

    assert (state, valid, bad) == before
    assert isinstance(selection.tasks, tuple)
    assert isinstance(problem.refusals, tuple)
    for frozen in (valid, selection, selection.filter, project_filter_options(state, 1)):
        with pytest.raises(FrozenInstanceError):
            setattr(frozen, dataclass_fields(frozen)[0].name, None)


def test_filter_field_is_the_closed_control_order():
    """CP-405, design § 3 A: the seven fields, in the order the controls stand."""
    assert [field.value for field in FilterField] == list(FIELD_NAMES)
    assert FilterInput().values(FilterField.LABEL) == ()
    assert one("label", "x").values(FilterField.LABEL) == ("x",)


def test_a_filter_narrows_only_when_a_choice_is_set():
    """CP-395, CP-398, design § 3 A: the domain says whether the validated choices narrow anything,
    so no other part compares them. A singleton empty field and an unset Overdue narrow nothing."""
    assert TaskFilter().narrows is False
    assert select(MIXED, FilterInput(status=("",), overdue=("",))).filter.narrows is False
    for field, value in (
        ("status", "todo"),
        ("priority", "high"),
        ("label", "x"),
        ("overdue", "on"),
        ("due_from", "2026-10-01"),
        ("due_to", "2026-10-01"),
    ):
        assert select(MIXED, one(field, value)).filter.narrows is True, field
