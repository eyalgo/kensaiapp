"""The Tasks feature entry point: the task entity and the rules that create, edit, restore and
order one.

Realizes SRS FR-15 (creating a task: its defaults and its fields), FR-16 (editing a task's title,
priority, assignee and due date, writing only the fields that differ from what the form showed),
FR-23 (adding a label to a task and removing one, replacing that task's labels alone), FR-28
(adding a comment to a task, after the comments it already holds), FR-39 and
FR-40 (refusals and the title maximum), FR-36 (the order a project's list is read in) and DR-2 (the
Task entity, one identity across all projects, issued from a counter held in the state).

Taking part: application/tracker.py applies these rules and saves the result, and prepares the
rows of a project's list and the edit's page values; web/pages.py shows the form, the list and a
task with its edit form, and web/routes.py turns a submission into an add or an edit and each
refusal into its reason. persistence/saved_data.py restores a saved task through restore_task and
the saved state through restore_state.

Checked by: tests/unit/test_tasks.py, tests/unit/test_priorities.py, tests/unit/test_due_dates.py
and tests/unit/test_state.py (the rules and restoration), and tests/integration/test_saved_data.py
and tests/integration/test_start.py (the saved task shape and the start on saved data), and
tests/integration/test_task_tracker.py (the add, the edit, the lookup and the list through the
Tracker), tests/integration/test_task_routes.py, tests/integration/test_routes.py and
tests/integration/test_task_pages.py (the requests and pages), tests/e2e/test_tasks.py (the
browser), and tests/integration/test_timed_run.py (the timed harness at task volume).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING

from domain.comments import Comment, check_saved_comments, create_comment
from domain.due_dates import parse_calendar_date
from domain.labels import add_label, check_saved_labels, remove_label
from domain.priorities import DEFAULT_PRIORITY, Priority, parse_priority
from domain.projects import Project, find_project
from domain.refusals import (
    AssigneeNotListed,
    BlankName,
    BlankTitle,
    InvalidTaskStatus,
    ProjectNotFound,
    TaskNotFound,
    TextField,
)
from domain.text import SHORT_TEXT_MAX, ensure_within

if TYPE_CHECKING:
    from domain.state import TrackerState


class TaskStatus(str, Enum):
    """A task's status, valued by the word the page and the saved data use."""

    TODO = "todo"
    IN_PROGRESS = "in-progress"
    DONE = "done"
    CANCELLED = "cancelled"

    @property
    def is_open(self) -> bool:
        """A task that is neither done nor cancelled can still become overdue."""
        return self not in (TaskStatus.DONE, TaskStatus.CANCELLED)


@dataclass(frozen=True)
class Task:
    """A task. Unassigned and undated are None; labels and comments are in the order held."""

    id: int
    project_id: int
    title: str
    status: TaskStatus
    priority: Priority
    assignee: str | None
    labels: tuple[str, ...]
    due_date: date | None
    created_at: datetime
    comments: tuple[Comment, ...]


@dataclass(frozen=True)
class TaskFields:
    """The four editable values of a task as strings. None is absent; an empty string is a value.

    One carries the values a form submitted and another the values that form showed, so the edit
    can tell a field the operator changed from one left alone.
    """

    title: str | None = None
    priority: str | None = None
    assignee: str | None = None
    due_date: str | None = None


@dataclass(frozen=True)
class TaskEditOutcome:
    """The task as it stands after an edit, and whether any supplied pair differed.

    `changed` reports a difference between submitted and shown values, so it is true even when the
    submitted value is what the task already holds.
    """

    task: Task
    changed: bool


@dataclass(frozen=True)
class TaskLabelOutcome:
    """The task as it stands after a label action, and whether the action changed its labels.

    `changed` is the domain's own verdict, so a part that saves can tell a repeated add, which
    changes nothing, from an add or a remove that does.
    """

    task: Task
    changed: bool


@dataclass(frozen=True)
class TaskEditContext:
    """What a task's edit form is built from: the task, its project and its saved values.

    The saved values are strings, empty when the task is unassigned or undated. The assignee
    choices are the empty string for none, then the listed names in their saved order, then the
    name the task carries when that name has left the list, in which case `assignee_unlisted`.
    """

    task: Task
    project: Project
    fields: TaskFields
    assignee_choices: tuple[str, ...]
    assignee_unlisted: bool


def _check_title(title: str) -> None:
    """Over-long comes before blank, so 201 spaces gets the too-long reason (CP-118)."""
    ensure_within(TextField.TITLE, title, SHORT_TEXT_MAX)
    if all(character.isspace() for character in title):
        raise BlankTitle()


def _check_saved_assignee(name: str) -> None:
    ensure_within(TextField.NAME, name, SHORT_TEXT_MAX)
    if all(character.isspace() for character in name):
        raise BlankName()


def _parse_status(value: str) -> TaskStatus:
    try:
        return TaskStatus(value)
    except ValueError:
        raise InvalidTaskStatus() from None


def add_task(
    state: TrackerState,
    project_id: int,
    title: str,
    priority: str,
    assignee: str,
    due_date: str,
    created_at: datetime,
) -> tuple[TrackerState, Task]:
    """Return the state after adding the task, and the task, or raise a refusal.

    Priority, assignee and due date arrive as the form's strings, empty when the form sent none;
    empty means medium, unassigned and undated. The checks run in this order: project, title length,
    title blankness, priority, assignee, due date. A refusal consumes no identity.
    """
    if find_project(state, project_id) is None:
        raise ProjectNotFound()
    _check_title(title)
    chosen_priority = parse_priority(priority) if priority else DEFAULT_PRIORITY
    if assignee and assignee not in state.assignees:
        raise AssigneeNotListed(assignee)
    chosen_due_date = parse_calendar_date(due_date) if due_date else None
    task = Task(
        id=state.next_task_id,
        project_id=project_id,
        title=title,
        status=TaskStatus.TODO,
        priority=chosen_priority,
        assignee=assignee or None,
        labels=(),
        due_date=chosen_due_date,
        created_at=created_at,
        comments=(),
    )
    new_state = replace(state, tasks=(*state.tasks, task), next_task_id=state.next_task_id + 1)
    return new_state, task


def _changed_value(submitted: str | None, shown: str | None) -> str | None:
    """The submitted value when both are present and differ exactly, else None (unchanged)."""
    if submitted is None or shown is None or submitted == shown:
        return None
    return submitted


def edit_task(
    state: TrackerState, task_id: int, submitted: TaskFields, shown: TaskFields
) -> tuple[TrackerState, TaskEditOutcome]:
    """Return the state after applying the changed fields to the task, and the outcome, or refuse.

    A field is changed when its submitted and shown values are both present and differ; only
    changed fields are checked and written, against the state as it is now. The checks run in this
    order: task found, title length, title blankness, priority, assignee, due date. An empty
    priority is refused, and an empty assignee or due date clears the field. Nothing changed
    returns the state as it came.
    """
    current = find_task(state, task_id)
    if current is None:
        raise TaskNotFound()
    title = _changed_value(submitted.title, shown.title)
    priority = _changed_value(submitted.priority, shown.priority)
    assignee = _changed_value(submitted.assignee, shown.assignee)
    due_date = _changed_value(submitted.due_date, shown.due_date)
    if title is priority is assignee is due_date is None:
        return state, TaskEditOutcome(task=current, changed=False)
    if title is not None:
        _check_title(title)
    new_priority = current.priority if priority is None else parse_priority(priority)
    if assignee and assignee not in state.assignees:
        raise AssigneeNotListed(assignee)
    new_due_date = current.due_date if due_date is None else _parse_optional_date(due_date)
    edited = replace(
        current,
        title=current.title if title is None else title,
        priority=new_priority,
        assignee=current.assignee if assignee is None else assignee or None,
        due_date=new_due_date,
    )
    edited_tasks = tuple(edited if task.id == task_id else task for task in state.tasks)
    return replace(state, tasks=edited_tasks), TaskEditOutcome(task=edited, changed=True)


def add_task_label(
    state: TrackerState, task_id: int, label: str
) -> tuple[TrackerState, TaskLabelOutcome]:
    """Return the state with the label added to the task's labels, and the outcome, or refuse.

    The task is found first, then the label is checked against the labels it carries now. A label
    the task already carries is no change: the state comes back as it was.
    """
    current = _find_task_or_refuse(state, task_id)
    labels, changed = add_label(current.labels, label)
    if not changed:
        return state, TaskLabelOutcome(task=current, changed=False)
    return _with_labels(state, current, labels)


def remove_task_label(
    state: TrackerState, task_id: int, label: str
) -> tuple[TrackerState, TaskLabelOutcome]:
    """Return the state without the label on the task, and the outcome, or refuse.

    The task is found first; a label it does not carry, compared exactly, is refused.
    """
    current = _find_task_or_refuse(state, task_id)
    return _with_labels(state, current, remove_label(current.labels, label))


def _find_task_or_refuse(state: TrackerState, task_id: int) -> Task:
    task = find_task(state, task_id)
    if task is None:
        raise TaskNotFound()
    return task


def _with_labels(
    state: TrackerState, current: Task, labels: tuple[str, ...]
) -> tuple[TrackerState, TaskLabelOutcome]:
    labelled = replace(current, labels=labels)
    labelled_tasks = tuple(labelled if task.id == current.id else task for task in state.tasks)
    return replace(state, tasks=labelled_tasks), TaskLabelOutcome(task=labelled, changed=True)


def add_task_comment(
    state: TrackerState, task_id: int, text: str, created_at: datetime
) -> tuple[TrackerState, Task]:
    """Return the state with the comment appended to the task's comments, and the task, or refuse.

    The task is found first, so a missing task is refused whatever the text and whether a name is
    saved. The comment is then made from the text, the operator name held in the state now and the
    instant handed in, and goes after every comment the task holds, so identical text, equal
    instants and instants going backwards each add another. The task's status does not matter.
    """
    current = _find_task_or_refuse(state, task_id)
    comment = create_comment(text, state.operator_name, created_at)
    commented = replace(current, comments=(*current.comments, comment))
    commented_tasks = tuple(commented if task.id == task_id else task for task in state.tasks)
    return replace(state, tasks=commented_tasks), commented


def task_edit_context(state: TrackerState, task_id: int) -> TaskEditContext | None:
    """The edit form's values for the task, or None when no task has this identity."""
    task = find_task(state, task_id)
    project = None if task is None else find_project(state, task.project_id)
    if task is None or project is None:
        return None
    carried = task.assignee or ""
    unlisted = bool(carried) and carried not in state.assignees
    return TaskEditContext(
        task=task,
        project=project,
        fields=TaskFields(
            title=task.title,
            priority=task.priority.value,
            assignee=carried,
            due_date="" if task.due_date is None else task.due_date.isoformat(),
        ),
        assignee_choices=("", *state.assignees, *((carried,) if unlisted else ())),
        assignee_unlisted=unlisted,
    )


def _parse_optional_date(value: str) -> date | None:
    """The date the text names, or None for empty text, which clears the field."""
    return parse_calendar_date(value) if value else None


def restore_task(
    id: int,
    project_id: int,
    title: str,
    status: str,
    priority: str,
    assignee: str | None,
    labels: Sequence[str],
    due_date: str | None,
    created_at: datetime,
    comments: Sequence[Comment],
) -> Task:
    """Build a task from saved values, applying the value rules creation applies, or refuse it.

    Unlike a form, saved data has no default: an empty or unknown priority and an empty due date
    are refused. An assignee absent from the current list is readable (CP-137). Labels keep the
    rules an add applies: none empty, none over the maximum, none given twice (CP-197). Comments
    keep the comment rules, their authors the name rules, and they stay in the order saved.
    """
    _check_title(title)
    restored_status = _parse_status(status)
    restored_priority = parse_priority(priority)
    if assignee is not None:
        _check_saved_assignee(assignee)
    restored_labels = check_saved_labels(labels)
    return Task(
        id=id,
        project_id=project_id,
        title=title,
        status=restored_status,
        priority=restored_priority,
        assignee=assignee,
        labels=restored_labels,
        due_date=None if due_date is None else parse_calendar_date(due_date),
        created_at=created_at,
        comments=check_saved_comments(comments),
    )


def find_task(state: TrackerState, task_id: int) -> Task | None:
    """The task with this identity, or None."""
    for task in state.tasks:
        if task.id == task_id:
            return task
    return None


def _due_then_identity(task: Task) -> tuple[bool, date, int]:
    """Dated before undated, earliest date first, then the identity (creation order)."""
    return (task.due_date is None, task.due_date or date.min, task.id)


def list_project_tasks(state: TrackerState, project_id: int) -> tuple[Task, ...]:
    """Every task of the project in list order, whatever order the state holds them in."""
    own = (task for task in state.tasks if task.project_id == project_id)
    return tuple(sorted(own, key=_due_then_identity))
