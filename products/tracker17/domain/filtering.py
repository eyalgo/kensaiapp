"""The Filtering feature entry point: the rules that narrow a task list, a project's or all tasks.

Realizes SRS FR-31 (the All tasks list, every task of every project in one place, narrowed by the
same rules), FR-32 (a list is filtered by any combination of status, priority, assignee, label, a
due-date range and overdue), FR-33 (the assignee filter accepts only a name on the current list),
FR-34 (the due-date range, either end optional, and the refusal of a reversed one), FR-35 (the
overdue filter shows the tasks that are overdue under FR-25), FR-39 (every refusal is typed and
leaves the saved data unchanged) and NFR-9 (the trace from the requirement to this code).

Taking part: application/tracker.py reads the clock once, applies these rules to the current state
and projects the result for the page, and application/__init__.py hands the values and refusal types
to the web part. Nothing here reads a clock or a file: today arrives as an argument. The request and
the page that carry the choices are web/routes.py, web/pages.py and web/style.css, which decode the
address, map each refusal type to its reason and place the words. A project's list and the All tasks
list reach one validator, one matcher and one label computation; only the scope differs.

Checked by: tests/unit/test_filtering.py (the rules), tests/integration/test_filter_tracker.py (the
read through the Tracker), tests/integration/test_filter_routes.py (the request),
tests/integration/test_filter_pages.py (the page), tests/integration/test_filter_move_routes.py
(the moves pressed on a filtered list), tests/integration/test_tracker.py,
tests/integration/test_pages.py, tests/integration/test_routes.py, tests/e2e/test_filters.py (the
browser), and tests/architecture/test_trace.py and tests/architecture/test_shapes.py (the entry and
the shape).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import TypeVar

from domain.due_dates import is_overdue, parse_calendar_date
from domain.priorities import Priority, parse_priority
from domain.refusals import (
    FilterAssigneeNotListed,
    FilterField,
    FilterFieldRefusal,
    InvalidDueDate,
    InvalidFilterDueFrom,
    InvalidFilterDueTo,
    InvalidFilterOverdue,
    InvalidFilterPriority,
    InvalidFilterStatus,
    InvalidPriority,
    Refusal,
    RepeatedFilterValue,
    ReversedFilterRange,
)
from domain.state import TrackerState
from domain.tasks import Task, TaskStatus, list_all_tasks, list_project_tasks

Chosen = TypeVar("Chosen")

OVERDUE_ON = "on"
_CONTROL_ORDER = {field: position for position, field in enumerate(FilterField)}


@dataclass(frozen=True)
class FilterInput:
    """The raw choices of a request: for each field, every value it was sent with, as sent.

    An absent field is an empty tuple. Duplicate, empty and spaced values are kept exactly until
    a filter entry point checks them, whichever list it is for. It is a plain value with no request, address or markup in it.
    """

    status: tuple[str, ...] = ()
    priority: tuple[str, ...] = ()
    assignee: tuple[str, ...] = ()
    label: tuple[str, ...] = ()
    due_from: tuple[str, ...] = ()
    due_to: tuple[str, ...] = ()
    overdue: tuple[str, ...] = ()

    def values(self, field: FilterField) -> tuple[str, ...]:
        """The values the field was sent with."""
        return getattr(self, field.value)  # type: ignore[no-any-return]


@dataclass(frozen=True)
class TaskFilter:
    """The validated choices. None is a field that narrows nothing; overdue is off by default."""

    status: TaskStatus | None = None
    priority: Priority | None = None
    assignee: str | None = None
    label: str | None = None
    due_from: date | None = None
    due_to: date | None = None
    overdue: bool = False

    @property
    def narrows(self) -> bool:
        """Whether any choice is set, so the list is narrowed and a count or an empty state is owed."""
        return self != TaskFilter()


@dataclass(frozen=True)
class FilterOptions:
    """What a list's scope offers the controls: how many tasks it holds, the current assignee names
    in list order, and the exact labels its tasks carry, once each, in code-point order."""

    task_count: int
    assignees: tuple[str, ...]
    labels: tuple[str, ...]


@dataclass(frozen=True)
class FilterSelection:
    """A valid filter applied: the matching tasks in list order, and how many, beside the scope's
    whole task count, the validated choices and the options of the whole scope."""

    task_count: int
    tasks: tuple[Task, ...]
    match_count: int
    filter: TaskFilter
    assignees: tuple[str, ...]
    labels: tuple[str, ...]


class FilterRefused(Refusal):
    """One or more filter fields were refused. Carries the refusals, one per refused condition in
    the order the controls stand, and the raw input that was refused."""

    def __init__(self, refusals: tuple[FilterFieldRefusal, ...], fields: FilterInput) -> None:
        super().__init__(refusals, fields)
        self.refusals = refusals
        self.fields = fields


def project_filter_options(state: TrackerState, project_id: int) -> FilterOptions:
    """The project's task count and the choices its controls offer, whatever filter is applied.

    Labels come from every task of the project, never from the matches, so filtering a labelled
    task out does not remove its choice.
    """
    return _options(state, list_project_tasks(state, project_id))


def all_filter_options(state: TrackerState) -> FilterOptions:
    """The whole tracker's task count and the choices the All tasks controls offer.

    Labels come from every task of every project, never from the matches.
    """
    return _options(state, list_all_tasks(state))


def filter_project_tasks(
    state: TrackerState, project_id: int, fields: FilterInput, today: date
) -> FilterSelection:
    """The project's tasks that match every field set, in list order, or raise FilterRefused.

    A project with no tasks returns its empty selection without checking the choices. Otherwise
    every field is checked, and all refused fields are reported together. `today` is the date the
    overdue verdict is worked out against; nothing here reads a clock.
    """
    return _select(state, list_project_tasks(state, project_id), fields, today)


def filter_all_tasks(state: TrackerState, fields: FilterInput, today: date) -> FilterSelection:
    """Every task of every project that matches every field set, in list order, or raise
    FilterRefused.

    A tracker with no tasks returns its empty selection without checking the choices. Otherwise
    the rules are the project entry point's, applied to the whole scope.
    """
    return _select(state, list_all_tasks(state), fields, today)


def _options(state: TrackerState, scope: tuple[Task, ...]) -> FilterOptions:
    """The task count and the controls' choices of the scope, which is in list order."""
    labels = sorted({label for task in scope for label in task.labels})
    return FilterOptions(task_count=len(scope), assignees=state.assignees, labels=tuple(labels))


def _select(
    state: TrackerState, scope: tuple[Task, ...], fields: FilterInput, today: date
) -> FilterSelection:
    """The scope's tasks that match the fields, or an empty selection for an empty scope."""
    options = _options(state, scope)
    if options.task_count == 0:
        return FilterSelection(0, (), 0, TaskFilter(), options.assignees, options.labels)
    chosen = _validated(fields, state.assignees)
    matches = tuple(task for task in scope if _matches(task, chosen, today))
    return FilterSelection(
        task_count=options.task_count,
        tasks=matches,
        match_count=len(matches),
        filter=chosen,
        assignees=options.assignees,
        labels=options.labels,
    )


def _validated(fields: FilterInput, assignees: tuple[str, ...]) -> TaskFilter:
    """The choices as a filter, or raise FilterRefused naming every refused field in order."""
    refusals: list[FilterFieldRefusal] = []
    singles: dict[FilterField, str] = {}
    for field in FilterField:
        values = fields.values(field)
        if len(values) > 1:
            refusals.append(RepeatedFilterValue(field, len(values)))
        else:
            singles[field] = values[0] if values else ""
    status = _checked(refusals, singles, FilterField.STATUS, _status)
    priority = _checked(refusals, singles, FilterField.PRIORITY, _priority)
    assignee = _checked(
        refusals, singles, FilterField.ASSIGNEE, lambda name: _assignee(name, assignees)
    )
    label = singles.get(FilterField.LABEL) or None
    due_from = _checked(refusals, singles, FilterField.DUE_FROM, _due_from)
    due_to = _checked(refusals, singles, FilterField.DUE_TO, _due_to)
    overdue = _checked(refusals, singles, FilterField.OVERDUE, _overdue) or False
    if due_from is not None and due_to is not None and due_from > due_to:
        refusals.append(ReversedFilterRange(due_from, due_to))
    if refusals:
        ordered = sorted(refusals, key=lambda refusal: _CONTROL_ORDER[refusal.field])
        raise FilterRefused(tuple(ordered), fields)
    return TaskFilter(status, priority, assignee, label, due_from, due_to, overdue)


def _checked(
    refusals: list[FilterFieldRefusal],
    singles: dict[FilterField, str],
    field: FilterField,
    parse: Callable[[str], Chosen],
) -> Chosen | None:
    """Parse the field's one value, or None for an unset or repeated field. A refusal is added."""
    value = singles.get(field)
    if not value:
        return None
    try:
        return parse(value)
    except FilterFieldRefusal as refusal:
        refusals.append(refusal)
        return None


def _status(value: str) -> TaskStatus:
    try:
        return TaskStatus(value)
    except ValueError:
        raise InvalidFilterStatus(value) from None


def _priority(value: str) -> Priority:
    try:
        return parse_priority(value)
    except InvalidPriority:
        raise InvalidFilterPriority(value) from None


def _assignee(name: str, assignees: tuple[str, ...]) -> str:
    if name not in assignees:
        raise FilterAssigneeNotListed(name)
    return name


def _due_from(value: str) -> date:
    try:
        return parse_calendar_date(value)
    except InvalidDueDate:
        raise InvalidFilterDueFrom(value) from None


def _due_to(value: str) -> date:
    try:
        return parse_calendar_date(value)
    except InvalidDueDate:
        raise InvalidFilterDueTo(value) from None


def _overdue(value: str) -> bool:
    if value != OVERDUE_ON:
        raise InvalidFilterOverdue(value)
    return True


def _matches(task: Task, chosen: TaskFilter, today: date) -> bool:
    """Whether the task holds every choice that is set."""
    return (
        (chosen.status is None or task.status is chosen.status)
        and (chosen.priority is None or task.priority is chosen.priority)
        and (chosen.assignee is None or task.assignee == chosen.assignee)
        and (chosen.label is None or chosen.label in task.labels)
        and _within(task.due_date, chosen.due_from, chosen.due_to)
        and (not chosen.overdue or is_overdue(task.due_date, task.status, today))
    )


def _within(due: date | None, lower: date | None, upper: date | None) -> bool:
    """On or after the lower end and on or before the upper, either optional. A task with no due
    date is inside no range that has an end."""
    if lower is None and upper is None:
        return True
    if due is None:
        return False
    return (lower is None or due >= lower) and (upper is None or due <= upper)
