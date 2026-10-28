"""The Sorting feature entry point: the rules that order a task list, a project's or all tasks, and
the refusals.

Realizes SRS FR-31 (the All tasks list is sorted by the same rules, over every project at once),
FR-36 (a task list sorts by one field at a time, due date, priority, created time or
title, in either direction, ascending when none is chosen; tasks equal on the field keep creation
order), FR-39 (every refusal is typed and leaves the saved data unchanged) and NFR-9 (the trace from
the requirement to this code).

Taking part: application/tracker.py reads the clock once, applies these rules to the current state
and projects the result for the page, and application/__init__.py hands the values and refusal types
to the web part. The request and the page that carry the choices are web/routes.py and
web/pages.py, which decode the address, map each refusal type to its reason and place the words.
Nothing here reads a clock or a file: today arrives as an argument. A project's list and the All
tasks list reach one sort validator and one ordering; only the scope differs.

Checked by: tests/unit/test_sorting.py (the rules), tests/integration/test_sort_tracker.py (the
read the application projects), tests/integration/test_sort_pages.py and
tests/integration/test_sort_routes.py (the page and the request),
tests/integration/test_sort_move_routes.py (the moves pressed on a sorted list),
tests/integration/test_move_routes.py and tests/integration/test_move_pages.py (the move
destinations),
tests/integration/test_routes.py (the route walks), tests/integration/test_tracker.py (the read),
tests/integration/test_pages.py (the pages), tests/e2e/test_sorting.py (the browser), and
tests/architecture/test_trace.py and tests/architecture/test_shapes.py (the entry and the shape).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from enum import Enum

from domain.filtering import (
    FilterInput,
    FilterOptions,
    FilterRefused,
    FilterSelection,
    TaskFilter,
    all_filter_options,
    filter_all_tasks,
    filter_project_tasks,
    project_filter_options,
)
from domain.priorities import Priority
from domain.refusals import FilterFieldRefusal, Refusal
from domain.state import TrackerState
from domain.tasks import Task


class SortKey(str, Enum):
    """The fields a list sorts by, valued by the word an address carries."""

    DUE_DATE = "due_date"
    PRIORITY = "priority"
    CREATED_TIME = "created_time"
    TITLE = "title"


class SortDirection(str, Enum):
    """The two directions, valued by the word an address carries."""

    ASCENDING = "ascending"
    DESCENDING = "descending"


class SortControl(str, Enum):
    """The two sort controls, in the order they stand. The values name the `SortInput` members."""

    FIELD = "field"
    DIRECTION = "direction"


_PRIORITY_ASCENDING = (Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.CRITICAL)
_PRIORITY_RANK = {priority: rank for rank, priority in enumerate(_PRIORITY_ASCENDING)}


@dataclass(frozen=True)
class SortInput:
    """The raw choices of a request: for each control, every value it was sent with, as sent.

    An absent control is an empty tuple, and one empty value is an unset choice. Repeated and
    unknown values are kept exactly until `sort_project_tasks` checks them.
    """

    field: tuple[str, ...] = ()
    direction: tuple[str, ...] = ()

    def values(self, control: SortControl) -> tuple[str, ...]:
        """The values the control was sent with."""
        return getattr(self, control.value)  # type: ignore[no-any-return]


@dataclass(frozen=True)
class TaskSort:
    """The validated sort: due date ascending unless chosen, and whether a nonempty raw choice
    was supplied. An explicit default is still a supplied choice."""

    key: SortKey = SortKey.DUE_DATE
    direction: SortDirection = SortDirection.ASCENDING
    requested: bool = False


@dataclass(frozen=True)
class SortedSelection:
    """A valid filter and sort applied: the matching tasks in the sort's order, and how many,
    beside the scope's whole task count, the validated choices and the options of the whole
    scope. `count_requested` says whether the page owes the operator a count of the list."""

    task_count: int
    tasks: tuple[Task, ...]
    match_count: int
    filter: TaskFilter
    sorting: TaskSort
    assignees: tuple[str, ...]
    labels: tuple[str, ...]
    count_requested: bool


class SortFieldRefusal(Refusal):
    """Base of the refusals a sort control gets. Each one carries the control it is about."""

    def __init__(self, control: SortControl, *details: object) -> None:
        super().__init__(control, *details)
        self.control = control


class InvalidSortField(SortFieldRefusal):
    """The Sort by value is not one the control offers. Carries the value sent."""

    def __init__(self, value: str) -> None:
        super().__init__(SortControl.FIELD, value)
        self.value = value


class InvalidSortDirection(SortFieldRefusal):
    """The Direction value is not one the control offers. Carries the value sent."""

    def __init__(self, value: str) -> None:
        super().__init__(SortControl.DIRECTION, value)
        self.value = value


class RepeatedSortValue(SortFieldRefusal):
    """A sort control was sent more than once, equal and empty values included.

    Carries the control and how many values it was sent with, which is two or more.
    """

    def __init__(self, control: SortControl, count: int) -> None:
        super().__init__(control, count)
        self.count = count


class ProjectListRefused(Refusal):
    """One or more filter or sort fields were refused. Carries the refusals, the filter's in
    control order and then Sort by and Direction, and the raw input that was refused."""

    def __init__(
        self,
        refusals: tuple[FilterFieldRefusal | SortFieldRefusal, ...],
        fields: FilterInput,
        sort_fields: SortInput,
    ) -> None:
        super().__init__(refusals, fields, sort_fields)
        self.refusals = refusals
        self.fields = fields
        self.sort_fields = sort_fields


def sort_project_tasks(
    state: TrackerState,
    project_id: int,
    fields: FilterInput,
    sort_fields: SortInput,
    today: date,
) -> SortedSelection:
    """The project's tasks that match the filter, in the order the sort gives, or raise
    ProjectListRefused.

    A project with no tasks returns its empty selection without checking either input. Otherwise
    the filter and the sort are checked independently, so one refused input cannot hide the other,
    and a valid filter that matches nothing still has its sort checked. `today` is the date the
    overdue verdict is worked out against; nothing here reads a clock.
    """
    return _sorted_selection(
        project_filter_options(state, project_id),
        lambda: filter_project_tasks(state, project_id, fields, today),
        fields,
        sort_fields,
    )


def sort_all_tasks(
    state: TrackerState, fields: FilterInput, sort_fields: SortInput, today: date
) -> SortedSelection:
    """Every task of every project that matches the filter, in the one order the sort gives, or
    raise ProjectListRefused.

    The rules are the project entry point's, applied to the whole scope: a tracker with no tasks
    returns its empty selection without checking either input, and otherwise the filter and the
    sort are checked independently. The order is one order over all the matches, never project
    lists joined.
    """
    return _sorted_selection(
        all_filter_options(state),
        lambda: filter_all_tasks(state, fields, today),
        fields,
        sort_fields,
    )


def _sorted_selection(
    options: FilterOptions,
    select: Callable[[], FilterSelection],
    fields: FilterInput,
    sort_fields: SortInput,
) -> SortedSelection:
    """Filter through `select`, check the sort alongside it, and order the matches."""
    if options.task_count == 0:
        return SortedSelection(
            0, (), 0, TaskFilter(), TaskSort(), options.assignees, options.labels, False
        )
    refusals: list[FilterFieldRefusal | SortFieldRefusal] = []
    selection: FilterSelection | None = None
    try:
        selection = select()
    except FilterRefused as refused:
        refusals.extend(refused.refusals)
    sorting, sort_refusals = _validated_sort(sort_fields)
    refusals.extend(sort_refusals)
    if refusals or selection is None:
        raise ProjectListRefused(tuple(refusals), fields, sort_fields)
    tasks = _ordered(selection.tasks, sorting)
    return SortedSelection(
        task_count=selection.task_count,
        tasks=tasks,
        match_count=len(tasks),
        filter=selection.filter,
        sorting=sorting,
        assignees=selection.assignees,
        labels=selection.labels,
        count_requested=bool(tasks) and (selection.filter.narrows or sorting.requested),
    )


def _validated_sort(sort_fields: SortInput) -> tuple[TaskSort, list[SortFieldRefusal]]:
    """The sort the controls name, with each unset control at its default, and one refusal for
    every refused control in control order. A repeated control gets only its repeated-value
    refusal."""
    refusals: list[SortFieldRefusal] = []
    key = SortKey.DUE_DATE
    direction = SortDirection.ASCENDING
    requested = False
    for control in SortControl:
        values = sort_fields.values(control)
        if len(values) > 1:
            refusals.append(RepeatedSortValue(control, len(values)))
            continue
        value = values[0] if values else ""
        if value == "":
            continue
        requested = True
        if control is SortControl.FIELD:
            try:
                key = SortKey(value)
            except ValueError:
                refusals.append(InvalidSortField(value))
        else:
            try:
                direction = SortDirection(value)
            except ValueError:
                refusals.append(InvalidSortDirection(value))
    return TaskSort(key, direction, requested), refusals


def _ordered(tasks: tuple[Task, ...], sorting: TaskSort) -> tuple[Task, ...]:
    """The tasks in the sort's order. Ascending task number is the tie baseline, and Python's
    sort is stable in both directions, so tasks equal on the field keep creation order whichever
    way the field runs. Undated tasks stay in their own partition after the dated ones."""
    descending = sorting.direction is SortDirection.DESCENDING
    by_identity = sorted(tasks, key=lambda task: task.id)
    if sorting.key is SortKey.CREATED_TIME:
        return tuple(by_identity[::-1] if descending else by_identity)
    if sorting.key is SortKey.DUE_DATE:
        dated = [task for task in by_identity if task.due_date is not None]
        undated = [task for task in by_identity if task.due_date is None]
        dated.sort(key=lambda task: task.due_date or date.min, reverse=descending)
        return (*dated, *undated)
    if sorting.key is SortKey.PRIORITY:
        return tuple(
            sorted(by_identity, key=lambda task: _PRIORITY_RANK[task.priority], reverse=descending)
        )
    return tuple(sorted(by_identity, key=lambda task: task.title.casefold(), reverse=descending))
