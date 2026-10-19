"""Every page as a string, built from plain values handed in (SDD § 3 web; NFDR QC-36).

Keeps no state and decides no rule. One function, `_escape`, puts a value into a page, so a value
typed by the operator is always shown as text. Every word on a page is the content stage's
(`change_text.md` from `docs/CONTENT.md`); this module places those strings and writes none of its
own. The refusal codes below are the words an address carries between a submission and the page
that shows its reason.
"""

from __future__ import annotations

import html
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from application import (
    DEFAULT_PRIORITY,
    LONG_TEXT_MAX,
    PRIORITY_CHOICES,
    SHORT_TEXT_MAX,
    Comment,
    Project,
    Task,
    TaskEditContext,
    TaskFields,
    TaskRow,
    TaskStatus,
    TextField,
)

BLANK_NAME = "blank-name"
NAME_IN_USE = "name-in-use"
TEXT_TOO_LONG = "too-long"

PRODUCT_NAME = "tracker17"
STYLESHEET_ADDRESS = "/style.css"
PROJECTS_ADDRESS = "/"
PEOPLE_ADDRESS = "/people"
ADD_ASSIGNEE_ADDRESS = "/assignees"
REMOVE_ASSIGNEE_ADDRESS = "/assignees/remove"
OPERATOR_NAME_ADDRESS = "/operator-name"


class AssigneeRefusal(Enum):
    """The refusals People shows, valued by the code an address carries (design § 3 D)."""

    BLANK_NAME = "blank-name"
    ASSIGNEE_NAME_IN_USE = "assignee-name-in-use"
    TOO_LONG = "too-long"
    ASSIGNEE_NOT_FOUND = "assignee-not-found"


class TaskRefusal(Enum):
    """The refusals the add-task form shows, valued by the code an address carries (design § 3 D)."""

    BLANK_TITLE = "blank-title"
    TOO_LONG = "too-long"
    ASSIGNEE_NOT_LISTED = "assignee-not-listed"
    INVALID_PRIORITY = "invalid-priority"
    INVALID_DUE_DATE = "invalid-due-date"


@dataclass(frozen=True)
class TaskForm:
    """What the add-task form shows: its four field values, and the outcome it last had.

    A refusal or a failure puts focus where the outcome belongs. A too-long refusal carries no
    submitted text, so the form then shows its opening values whatever it was handed.
    """

    title: str = ""
    priority: str = ""
    assignee: str = ""
    due_date: str = ""
    refusal: TaskRefusal | None = None
    failed: bool = False


class TaskEditRefusal(Enum):
    """The refusals the task-edit form shows, valued by the code an address carries (design § 3 C).

    The vocabulary is its own, so the add form's codes stay separate from the edit's.
    """

    BLANK_TITLE = "blank-title"
    TOO_LONG = "too-long"
    INVALID_PRIORITY = "invalid-priority"
    ASSIGNEE_NOT_LISTED = "assignee-not-listed"
    INVALID_DUE_DATE = "invalid-due-date"


@dataclass(frozen=True)
class TaskEditForm:
    """What the task-edit form last had: the values to show, the values it first showed, and why.

    `fields` are the visible values retained after an outcome and `shown` the original values the
    next save compares with; either holds None for a field the request did not carry. A too-long
    refusal carries neither, so the form then opens from the saved task.
    """

    fields: TaskFields = field(default_factory=TaskFields)
    shown: TaskFields = field(default_factory=TaskFields)
    refusal: TaskEditRefusal | None = None
    failed: bool = False


class FailedAction(Enum):
    """The two actions, on People and on a task's labels, that can fail without being refused."""

    ADD = "add"
    REMOVE = "remove"


class LabelRefusal(Enum):
    """The refusals the label area shows, valued by the code an address carries (design § 3 C)."""

    EMPTY = "empty"
    TOO_LONG = "too-long"
    NOT_CARRIED = "not-carried"


@dataclass(frozen=True)
class LabelArea:
    """What the label area last had, as plain values; it decides no rule.

    `label` is the label an add or a remove was sent with. `added` and `removed` name the label a
    completed action was about. An empty or too-long refusal carries no text of its own, so the
    field then shows nothing whatever `label` holds.
    """

    label: str = ""
    refusal: LabelRefusal | None = None
    failed: FailedAction | None = None
    added: str | None = None
    removed: str | None = None


class CommentRefusal(Enum):
    """The refusals the comment form shows, valued by the code an address carries (design § 3 D)."""

    TOO_LONG = "too-long"
    BLANK = "blank"
    NO_NAME = "no-name"


@dataclass(frozen=True)
class CommentArea:
    """What the comment area last had, as plain values; it decides no rule.

    `text` is what a blank or no-name refusal, or a failed add, sent back. A too-long refusal
    carries none of it, so the field then shows nothing whatever `text` holds, and `text` beside no
    outcome is ignored. `added_position` is the one-based place of the comment a completed add
    wrote; a position the task has no comment at is no outcome.
    """

    text: str = ""
    refusal: CommentRefusal | None = None
    failed: bool = False
    added_position: int | None = None


class MoveRefusal(Enum):
    """The two refusals a move gets, valued by the code an address carries (design § 3 C, D-6)."""

    NOT_ALLOWED = "not-allowed"
    NOT_A_STATUS = "not-a-status"


@dataclass(frozen=True)
class MoveOutcome:
    """What a press of a move last had, as plain values; it decides no rule.

    `task_id` is the task the press was about. At most one of `refusal`, `failed` and `moved` is
    set: the refusal's code, the status a failed move named, or the status the task moved to. A
    task that is not on the page shown, or an outcome with none of the three, is no outcome.
    """

    task_id: int | None = None
    refusal: MoveRefusal | None = None
    failed: TaskStatus | None = None
    moved: TaskStatus | None = None


class _MoveKind(Enum):
    """Which of the three lines a move outcome shows."""

    MOVED = "moved"
    REFUSED = "refused"
    FAILED = "failed"


AllowedMoves = Callable[[TaskStatus], tuple[TaskStatus, ...]]


def _no_moves(status: TaskStatus) -> tuple[TaskStatus, ...]:
    return ()


MOVE_PLACE_LIST = "list"
MOVE_PLACE_TASK = "task"


class _CommentOutcome(Enum):
    """What the comment area has to say, and so which element its line describes."""

    REFUSED = "refused"
    FAILED = "failed"
    ADDED = "added"


class OperatorNameRefusal(str, Enum):
    """The refusals the Your name section shows, valued by the code an address carries."""

    BLANK_NAME = "blank-name"
    TOO_LONG = "too-long"


@dataclass(frozen=True)
class OperatorNameArea:
    """What the Your name section last had, as plain values; it decides no rule.

    `typed` is the text a blank refusal or a failed save sent back, with None for text the request
    did not carry (absence is not the empty string). `saved` names the name a completed action
    kept. Typed text applies only to a blank refusal or a failure, and a too-long refusal shows
    none of it whatever else is carried.
    """

    typed: str | None = None
    refusal: OperatorNameRefusal | None = None
    failed: bool = False
    saved: str | None = None


class _OperatorOutcome(Enum):
    """What an action on the Your name section left for the page to say."""

    BLANK = "blank"
    TOO_LONG = "too-long"
    FAILED = "failed"
    COMPLETED = "completed"


_YOUR_NAME_ID = "your-name"
_YOUR_NAME_HEADING_ID = "your-name-heading"
_OPERATOR_FIELD_ID = "operator-name"
_OPERATOR_SAVE_ID = "save-operator-name"
_OPERATOR_OUTCOME_ID = "operator-name-outcome"
_NAME_REASON_ID = "name-reason"
_DESCRIPTION_REASON_ID = "description-reason"
_DESCRIPTION_NOTE_ID = "description-note"
_CREATE_FAILURE_ID = "create-failure"
_CREATED_LINE_ID = "created-line"
_ASSIGNEES_HEADING_ID = "assignees-heading"
_OUTCOME_LINE_ID = "assignees-outcome"
_ASSIGNEE_NAME_FIELD_ID = "assignee-name"
_ASSIGNEE_REASON_ID = "assignee-name-reason"
_ADD_FAILURE_ID = "add-failure"
_REMOVE_FAILURE_ID = "remove-failure"
_TASK_TITLE_ID = "task-title"
_TASK_PRIORITY_ID = "task-priority"
_TASK_ASSIGNEE_ID = "task-assignee"
_TASK_DUE_DATE_ID = "task-due-date"
_TASK_FAILURE_ID = "add-task-failure"
_ADDED_LINE_ID = "added-line"
_SAVED_LINE_ID = "saved-line"
_EDIT_TITLE_ID = "edit-title"
_EDIT_PRIORITY_ID = "edit-priority"
_EDIT_ASSIGNEE_ID = "edit-assignee"
_EDIT_DUE_DATE_ID = "edit-due-date"
_EDIT_FAILURE_ID = "edit-failure"
_EDIT_NOTICE_ID = "edit-assignee-notice"
_LABELS_ID = "labels"
_LABEL_FIELD_ID = "new-label"
_LABEL_REASON_ID = "label-reason"
_LABEL_FAILURE_ID = "label-failure"
_LABEL_ADDED_LINE_ID = "label-added-line"
_LABEL_REMOVED_LINE_ID = "label-removed-line"
_COMMENTS_ID = "comments"
_COMMENT_FIELD_ID = "comment-text"
_COMMENT_NOTE_ID = "comment-note"
_COMMENT_REASON_ID = "comment-reason"
_COMMENT_FAILURE_ID = "comment-failure"
_COMMENT_ADDED_LINE_ID = "comment-added-line"
_ADD_COMMENT_ID = "add-comment"
_MOVE_LINE_ID = "move-line"
_STATUS_ID = "status"
_TASK_STATUS_ID = "task-status"
_EDIT_REASON_IDS = {
    TaskEditRefusal.BLANK_TITLE: "edit-title-reason",
    TaskEditRefusal.TOO_LONG: "edit-title-reason",
    TaskEditRefusal.INVALID_PRIORITY: "edit-priority-reason",
    TaskEditRefusal.ASSIGNEE_NOT_LISTED: "edit-assignee-reason",
    TaskEditRefusal.INVALID_DUE_DATE: "edit-due-date-reason",
}
_TASK_REASON_IDS = {
    TaskRefusal.BLANK_TITLE: "task-title-reason",
    TaskRefusal.TOO_LONG: "task-title-reason",
    TaskRefusal.ASSIGNEE_NOT_LISTED: "task-assignee-reason",
    TaskRefusal.INVALID_PRIORITY: "task-priority-reason",
    TaskRefusal.INVALID_DUE_DATE: "task-due-date-reason",
}


EMPTY_ASSIGNEES = "There are no assignees yet. Tasks can be assigned only to names on this list."


def _escape(value: str) -> str:
    """The one place a value enters a page (SEC-4)."""
    return html.escape(value, quote=True)


def _characters(count: int) -> str:
    return "1 character" if count == 1 else f"{count} characters"


def _textarea(attributes: str, value: str) -> str:
    """A textarea holding the value. The HTML parser drops one line feed straight after the start
    tag, so one is written, and a value's own leading line feed survives."""
    return f"<textarea {attributes}>\n{_escape(value)}</textarea>\n"


def _written(instant: datetime) -> str:
    """The one date-and-time form the tracker writes: machine-local, 24-hour, no seconds."""
    return instant.astimezone().strftime("%Y-%m-%d %H:%M")


def _document(title: str, body: str) -> str:
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        f"<title>{_escape(title)}</title>\n"
        f'<link rel="stylesheet" href="{STYLESHEET_ADDRESS}">\n'
        "</head>\n"
        "<body>\n"
        '<header class="site-header">'
        f'<span class="product-name">{PRODUCT_NAME}</span>'
        f'<nav><a href="{PROJECTS_ADDRESS}">Projects</a>'
        f'<a href="{PEOPLE_ADDRESS}">People</a></nav>'
        "</header>\n"
        f"<main>\n{body}</main>\n"
        "</body>\n"
        "</html>\n"
    )


def _name_reason(refusal: str | None, field: TextField | None, name: str) -> str | None:
    if refusal == BLANK_NAME:
        return "A project needs a name. Type one."
    if refusal == NAME_IN_USE:
        return f"A project named '{_escape(name)}' already exists. Choose a different name."
    if refusal == TEXT_TOO_LONG and field is TextField.NAME:
        return (
            f"A project name can't be longer than {_characters(SHORT_TEXT_MAX)}. "
            "Type a shorter one."
        )
    return None


def _description_reason(refusal: str | None, field: TextField | None) -> str | None:
    if refusal == TEXT_TOO_LONG and field is TextField.DESCRIPTION:
        return (
            f"A description can't be longer than {_characters(LONG_TEXT_MAX)}. Type a shorter one."
        )
    return None


def _projects_list(projects: Sequence[Project]) -> str:
    if not projects:
        return (
            '<p class="empty">There are no projects yet. '
            "Type a name for your first project and press Create.</p>\n"
        )
    items = []
    for project in projects:
        description = (
            f'<p class="description pre-wrap">{_escape(project.description)}</p>'
            if project.description
            else ""
        )
        items.append(
            f'<li><a class="project-name pre-wrap" href="/projects/{project.id}">'
            f"{_escape(project.name)}</a>{description}</li>\n"
        )
    return '<ul class="project-list">\n' + "".join(items) + "</ul>\n"


def _create_form(
    refusal: str | None, field: TextField | None, failed: bool, name: str, description: str
) -> str:
    name_reason = _name_reason(refusal, field, name)
    description_reason = _description_reason(refusal, field)
    name_attributes = f'type="text" id="name" name="name" maxlength="{SHORT_TEXT_MAX}"'
    name_attributes += f' value="{_escape(name)}"'
    name_block = ""
    if name_reason is not None:
        name_attributes += f' autofocus aria-describedby="{_NAME_REASON_ID}"'
        name_block = f'<p class="reason" id="{_NAME_REASON_ID}">{name_reason}</p>\n'
    description_describers = [_DESCRIPTION_NOTE_ID]
    description_attributes = (
        f'id="description" name="description" rows="4" maxlength="{LONG_TEXT_MAX}"'
    )
    description_block = ""
    if description_reason is not None:
        description_describers.append(_DESCRIPTION_REASON_ID)
        description_attributes += " autofocus"
        description_block = (
            f'<p class="reason" id="{_DESCRIPTION_REASON_ID}">{description_reason}</p>\n'
        )
    description_attributes += f' aria-describedby="{" ".join(description_describers)}"'
    button_attributes = 'type="submit"'
    button_block = ""
    if failed:
        button_attributes += f' autofocus aria-describedby="{_CREATE_FAILURE_ID}"'
        button_block = (
            f'<p class="reason" id="{_CREATE_FAILURE_ID}">'
            f"The tracker couldn't create '{_escape(name)}', and nothing was changed. "
            "What you typed is still in the form. Try again.</p>\n"
        )
    return (
        '<form method="post" action="/projects" class="create-form">\n'
        '<div class="field">\n'
        '<label for="name">Name</label>\n'
        f"{name_block}"
        f"<input {name_attributes}>\n"
        "</div>\n"
        '<div class="field">\n'
        '<label for="description">Description</label>\n'
        f'<p class="note" id="{_DESCRIPTION_NOTE_ID}">'
        "You can't change the description after you create the project. "
        f"A description can hold up to {_characters(LONG_TEXT_MAX)}.</p>\n"
        f"{description_block}"
        f"{_textarea(description_attributes, description)}"
        "</div>\n"
        f"{button_block}"
        f"<button {button_attributes}>Create</button>\n"
        "</form>\n"
    )


def projects_page(
    projects: Sequence[Project],
    *,
    refusal: str | None = None,
    field: TextField | None = None,
    failed: bool = False,
    name: str = "",
    description: str = "",
) -> str:
    """The Projects page: the list, and the create form with a reason or a failure when given.

    `refusal` is one of the three refusal codes; `field` says which field was too long. A refused
    or failed page puts focus on the control used. Over-long refusals carry no typed values, so the
    caller hands none.
    """
    body = (
        "<h1>Projects</h1>\n"
        f"{_projects_list(projects)}"
        f"{_create_form(refusal, field, failed, name, description)}"
    )
    return _document("Projects - tracker17", body)


def _task_reason(form: TaskForm, project: Project) -> str | None:
    """The words of the form's refusal, or None when it was not refused."""
    if form.refusal is TaskRefusal.BLANK_TITLE:
        return "A task needs a title. Type one."
    if form.refusal is TaskRefusal.TOO_LONG:
        return (
            f"A task title can't be longer than {_characters(SHORT_TEXT_MAX)}. Type a shorter one."
        )
    if form.refusal is TaskRefusal.ASSIGNEE_NOT_LISTED:
        return (
            f"The name '{_escape(form.assignee)}' is no longer on the assignee list. "
            f"Open '<a href=\"/projects/{project.id}\">{_escape(project.name)}</a>' again "
            "to reload the page."
        )
    if form.refusal is TaskRefusal.INVALID_PRIORITY:
        return "A task's priority has to be low, medium, high or critical. Pick one of the four."
    if form.refusal is TaskRefusal.INVALID_DUE_DATE:
        return "A due date has to be a calendar date. Pick one, or leave the due date empty."
    return None


def _option(value: str, label: str, selected: bool) -> str:
    chosen = " selected" if selected else ""
    return f'<option value="{_escape(value)}"{chosen}>{_escape(label)}</option>\n'


def _task_field(
    identifier: str, label: str, control: str, reason: str | None, reason_id: str, note: str = ""
) -> str:
    """One labelled field of the add form; a reason, when given, sits above the control."""
    reason_block = f'<p class="reason" id="{reason_id}">{reason}</p>\n' if reason else ""
    return (
        '<div class="field">\n'
        f'<label for="{identifier}">{label}</label>\n'
        f"{reason_block}{control}{note}"
        "</div>\n"
    )


def _add_task_form(
    project: Project, assignees: Sequence[str], priority_choices: Sequence[str], form: TaskForm
) -> str:
    """The persistent add-task form, with the reason or failure its outcome gives (CP-106)."""
    if form.refusal is TaskRefusal.TOO_LONG:
        form = TaskForm(refusal=form.refusal)
    reason = _task_reason(form, project)
    reason_id = _TASK_REASON_IDS[form.refusal] if form.refusal is not None else ""

    def focus(*refusals: TaskRefusal) -> str:
        if form.refusal in refusals:
            return f' autofocus aria-describedby="{reason_id}"'
        return ""

    def reason_for(*refusals: TaskRefusal) -> str | None:
        return reason if form.refusal in refusals else None

    title_control = (
        f'<input type="text" id="{_TASK_TITLE_ID}" name="title" maxlength="{SHORT_TEXT_MAX}" '
        f'value="{_escape(form.title)}"'
        f"{focus(TaskRefusal.BLANK_TITLE, TaskRefusal.TOO_LONG)}>\n"
    )
    priority = form.priority if form.priority in priority_choices else DEFAULT_PRIORITY.value
    options = "".join(_option(word, word, word == priority) for word in priority_choices)
    priority_control = (
        f'<select id="{_TASK_PRIORITY_ID}" name="priority"{focus(TaskRefusal.INVALID_PRIORITY)}>\n'
        f"{options}</select>\n"
    )
    assignee = form.assignee if form.assignee in assignees else ""
    names = "".join(_option(name, name, name == assignee) for name in assignees)
    assignee_control = (
        f'<select id="{_TASK_ASSIGNEE_ID}" name="assignee"'
        f"{focus(TaskRefusal.ASSIGNEE_NOT_LISTED)}>\n"
        f"{_option('', 'unassigned', assignee == '')}{names}</select>\n"
    )
    no_assignees = (
        ""
        if assignees
        else (
            '<p class="note">There are no assignees yet. '
            f'Open <a href="{PEOPLE_ADDRESS}">People</a> to add one.</p>\n'
        )
    )
    date_control = (
        f'<input type="date" id="{_TASK_DUE_DATE_ID}" name="due_date" '
        f'value="{_escape(form.due_date)}"{focus(TaskRefusal.INVALID_DUE_DATE)}>\n'
    )
    form_attributes = f'method="post" action="/projects/{project.id}/tasks" class="create-form"'
    failure_block = ""
    if form.failed:
        form_attributes += f' tabindex="-1" autofocus aria-describedby="{_TASK_FAILURE_ID}"'
        failure_block = (
            f'<p class="reason" id="{_TASK_FAILURE_ID}">'
            f"The tracker couldn't add '{_escape(form.title)}', and nothing was changed. "
            "What you typed is still in the form. Try again.</p>\n"
        )
    fields = (
        _task_field(
            _TASK_TITLE_ID,
            "Title",
            title_control,
            reason_for(TaskRefusal.BLANK_TITLE, TaskRefusal.TOO_LONG),
            reason_id,
        )
        + _task_field(
            _TASK_PRIORITY_ID,
            "Priority",
            priority_control,
            reason_for(TaskRefusal.INVALID_PRIORITY),
            reason_id,
        )
        + _task_field(
            _TASK_ASSIGNEE_ID,
            "Assignee",
            assignee_control,
            reason_for(TaskRefusal.ASSIGNEE_NOT_LISTED),
            reason_id,
            no_assignees,
        )
        + _task_field(
            _TASK_DUE_DATE_ID,
            "Due date",
            date_control,
            reason_for(TaskRefusal.INVALID_DUE_DATE),
            reason_id,
        )
    )
    return f'<form {form_attributes}>\n{fields}{failure_block}<button type="submit">Add</button>\n</form>\n'


def _due_date_cell(row: TaskRow) -> str:
    """The date as `YYYY-MM-DD` or `none`, with the Overdue word after it when the row says so."""
    shown = row.task.due_date.isoformat() if row.task.due_date is not None else "none"
    marker = ' <span class="overdue">Overdue</span>' if row.overdue else ""
    return f"{shown}{marker}"


_WITHHELD_MOVES = (TaskStatus.CANCELLED,)


def _move_forms(task: Task, place: str, allowed: tuple[TaskStatus, ...]) -> str:
    """One form and one button per move the page offers: the allowed ones in the order given,
    less the moves this slice withholds (D-10). Which moves are allowed is not decided here."""
    offered = [move for move in allowed if move not in _WITHHELD_MOVES]
    title = _escape(task.title)
    forms = "".join(
        f'<form method="post" action="/tasks/{task.id}/move">'
        f'<input type="hidden" name="status" value="{move.value}">'
        f'<input type="hidden" name="place" value="{place}">'
        f'<button type="submit" class="move-button" '
        f"aria-label=\"Move '{title}' to {move.value}\">{move.value}</button>"
        "</form>"
        for move in offered
    )
    return f'<div class="moves">{forms}</div>' if forms else ""


_REFUSAL_TAILS = {
    TaskStatus.TODO: "The moves shown are the ones you can press.",
    TaskStatus.IN_PROGRESS: "The moves shown are the ones you can press.",
    TaskStatus.DONE: "A task in done can't be moved.",
    TaskStatus.CANCELLED: "A task in cancelled can't be moved.",
}


def _move_line(outcome: MoveOutcome | None, task: Task) -> tuple[_MoveKind, str] | None:
    """The one line a move outcome shows for this task, or None when it is not about the task.

    A refusal is chosen before a failure and a failure before a completion. The title is the one
    the state holds now; the status is the one the address names.
    """
    if outcome is None or outcome.task_id != task.id:
        return None
    title = _escape(task.title)
    if outcome.refusal is not None:
        status = task.status.value
        line = (
            f"The status of '{title}' is {status}, which doesn't allow the move you pressed. "
            f"{_REFUSAL_TAILS[task.status]}"
        )
        return _MoveKind.REFUSED, line
    if outcome.failed is not None:
        line = (
            f"The tracker couldn't move '{title}' to {outcome.failed.value}, and nothing was "
            "changed. Try again."
        )
        return _MoveKind.FAILED, line
    if outcome.moved is not None:
        return _MoveKind.MOVED, f"You moved '{title}' to {outcome.moved.value}."
    return None


def _move_line_block(line: tuple[_MoveKind, str] | None) -> str:
    if line is None:
        return ""
    kind, text = line
    css = "outcome" if kind is _MoveKind.MOVED else "reason"
    return f'<p class="{css}" id="{_MOVE_LINE_ID}">{text}</p>\n'


def _status_word(task: Task, line: tuple[_MoveKind, str] | None, tag: str, attributes: str) -> str:
    """The task's status in words, in an element of its own. On a landing it is the one element
    that takes focus: not a control, so it carries `tabindex="-1"`, and the line describes it."""
    if line is not None:
        attributes += f' tabindex="-1" autofocus aria-describedby="{_MOVE_LINE_ID}"'
    return f"<{tag}{attributes}>{task.status.value}</{tag}>"


def _task_row(
    position: int,
    row: TaskRow,
    allowed: AllowedMoves,
    line: tuple[_MoveKind, str] | None,
) -> str:
    task = row.task
    title = _escape(task.title)
    labels = ", ".join(_escape(label) for label in task.labels) or "none"
    assignee = _escape(task.assignee) if task.assignee is not None else "unassigned"
    status = _status_word(task, line, "span", ' class="status-word"') if line else task.status.value
    moves = _move_forms(task, MOVE_PLACE_LIST, allowed(task.status))
    return (
        "<tr>"
        f'<td><a class="pre-wrap" href="/tasks/{task.id}" '
        f'aria-label="{title}, number {position} on the task list">{title}</a></td>'
        f"<td>{status}</td>"
        f"<td>{task.priority.value}</td>"
        f'<td class="pre-wrap">{assignee}</td>'
        f'<td class="pre-wrap">{labels}</td>'
        f"<td>{_due_date_cell(row)}</td>"
        f"<td>{moves}{_move_line_block(line)}</td>"
        "</tr>\n"
    )


_TASK_COLUMNS = ("Title", "Status", "Priority", "Assignee", "Labels", "Due date", "Moves")


def _task_list(rows: Sequence[TaskRow], allowed: AllowedMoves, outcome: MoveOutcome | None) -> str:
    """The seven-column table in the order given, or the first-task invitation when there is none."""
    if not rows:
        return (
            '<p class="no-tasks">This project has no tasks yet. '
            "Give the first task a title and press Add.</p>\n"
        )
    headers = "".join(f'<th scope="col">{name}</th>' for name in _TASK_COLUMNS)
    body = "".join(
        _task_row(position, row, allowed, _move_line(outcome, row.task))
        for position, row in enumerate(rows, start=1)
    )
    return (
        '<table class="task-list">\n'
        f"<thead><tr>{headers}</tr></thead>\n"
        f"<tbody>\n{body}</tbody>\n"
        "</table>\n"
    )


def project_page(
    project: Project,
    rows: Sequence[TaskRow] = (),
    assignees: Sequence[str] = (),
    *,
    priority_choices: Sequence[str] = PRIORITY_CHOICES,
    form: TaskForm | None = None,
    created: bool = False,
    allowed_moves: AllowedMoves = _no_moves,
    move_outcome: MoveOutcome | None = None,
) -> str:
    """One project's page: its add-task form, and its tasks in the order and with the overdue
    flags handed in. With `created`, it opens on its heading and the created line.

    Deciding no order and no overdue state, it shows the rows exactly as given. Each row offers the
    moves `allowed_moves` gives for its status. A `move_outcome` about one of the rows takes
    precedence over every other outcome: the page then shows only its line, and its focus.
    """
    if any(_move_line(move_outcome, row.task) is not None for row in rows):
        created, form = False, None
    heading_attributes = ' tabindex="-1"'
    created_line = ""
    if created:
        heading_attributes += f' autofocus aria-describedby="{_CREATED_LINE_ID}"'
        created_line = (
            f'<p class="created" id="{_CREATED_LINE_ID}">You created '
            f"'{_escape(project.name)}'.</p>\n"
        )
    description = (
        f'<p class="description pre-wrap">{_escape(project.description)}</p>\n'
        if project.description
        else ""
    )
    body = (
        f'<h1 class="pre-wrap"{heading_attributes}>{_escape(project.name)}</h1>\n'
        f"{created_line}"
        f"{description}"
        f"{_add_task_form(project, assignees, priority_choices, form or TaskForm())}"
        f"{_task_list(rows, allowed_moves, move_outcome)}"
    )
    return _document(f"{project.name} - tracker17", body)


def _edit_reason(
    refusal: TaskEditRefusal | None, context: TaskEditContext, name: str
) -> str | None:
    """The words of the edit form's refusal, or None when it was not refused."""
    if refusal is TaskEditRefusal.BLANK_TITLE:
        return "A task needs a title. Type one."
    if refusal is TaskEditRefusal.TOO_LONG:
        return (
            f"A task title can't be longer than {_characters(SHORT_TEXT_MAX)}. Type a shorter one."
        )
    if refusal is TaskEditRefusal.ASSIGNEE_NOT_LISTED:
        return (
            f"The name '{_escape(name)}' is no longer on the assignee list, so this page is out "
            f'of date. Open \'<a href="/tasks/{context.task.id}">{_escape(context.task.title)}'
            "</a>' again to reload the page."
        )
    if refusal is TaskEditRefusal.INVALID_PRIORITY:
        return "A task's priority has to be low, medium, high or critical. Pick one of the four."
    if refusal is TaskEditRefusal.INVALID_DUE_DATE:
        return "A due date has to be a calendar date. Give one, or leave the due date empty."
    return None


def _described_by(*identifiers: str) -> str:
    return f' aria-describedby="{" ".join(identifiers)}"' if identifiers else ""


def _edit_assignee_notice(name: str) -> str:
    return (
        f'<p class="note" id="{_EDIT_NOTICE_ID}">'
        f"The name '{_escape(name)}' is no longer on the assignee list. "
        "Picking another assignee or unassigned replaces it. "
        f"After that, '{_escape(name)}' can't be assigned to a task until it's added back on People."
        "</p>\n"
    )


def _edit_form(context: TaskEditContext, form: TaskEditForm) -> str:
    """The persistent edit form: the visible values, the original values it compares with, and the
    reason or failure its last outcome gives. Neither a value nor a name is checked here."""
    refusal, saved = form.refusal, context.fields
    if refusal is TaskEditRefusal.TOO_LONG:
        form = TaskEditForm(saved, saved, refusal, form.failed)
    reason = _edit_reason(refusal, context, form.fields.assignee or "")
    reason_id = _EDIT_REASON_IDS[refusal] if refusal is not None else ""

    def visible(name: str) -> str:
        for source in (form.fields, form.shown, saved):
            value: str | None = getattr(source, name)
            if value is not None:
                return value
        return ""

    def focus(*refusals: TaskEditRefusal) -> str:
        return f" autofocus{_described_by(reason_id)}" if refusal in refusals else ""

    def reason_for(*refusals: TaskEditRefusal) -> str | None:
        return reason if refusal in refusals else None

    title_control = (
        f'<input type="text" id="{_EDIT_TITLE_ID}" name="title" maxlength="{SHORT_TEXT_MAX}" '
        f'value="{_escape(visible("title"))}"'
        f"{focus(TaskEditRefusal.BLANK_TITLE, TaskEditRefusal.TOO_LONG)}>\n"
    )
    chosen_priority = visible("priority")
    options = "".join(_option(word, word, word == chosen_priority) for word in PRIORITY_CHOICES)
    priority_control = (
        f'<select id="{_EDIT_PRIORITY_ID}" name="priority"'
        f"{focus(TaskEditRefusal.INVALID_PRIORITY)}>\n{options}</select>\n"
    )
    chosen_assignee = visible("assignee")
    choices = context.assignee_choices
    if chosen_assignee not in choices:
        # A refused name is echoed as the failed choice only; it is never an eligible one.
        choices = (*choices, chosen_assignee)
    names = "".join(
        _option(name, "unassigned" if name == "" else name, name == chosen_assignee)
        for name in choices
    )
    notice_ids = (_EDIT_NOTICE_ID,) if context.assignee_unlisted else ()
    assignee_describers = (
        *([reason_id] if refusal is TaskEditRefusal.ASSIGNEE_NOT_LISTED else []),
        *notice_ids,
    )
    assignee_focus = " autofocus" if refusal is TaskEditRefusal.ASSIGNEE_NOT_LISTED else ""
    assignee_control = (
        f'<select id="{_EDIT_ASSIGNEE_ID}" name="assignee"{assignee_focus}'
        f"{_described_by(*assignee_describers)}>\n{names}</select>\n"
    )
    notice = _edit_assignee_notice(saved.assignee or "") if context.assignee_unlisted else ""
    date_control = (
        f'<input type="date" id="{_EDIT_DUE_DATE_ID}" name="due_date" '
        f'value="{_escape(visible("due_date"))}"{focus(TaskEditRefusal.INVALID_DUE_DATE)}>\n'
    )
    form_attributes = f'method="post" action="/tasks/{context.task.id}" class="create-form"'
    failure_block = ""
    if form.failed:
        form_attributes += f' tabindex="-1" autofocus{_described_by(_EDIT_FAILURE_ID)}'
        failure_block = (
            f'<p class="reason" id="{_EDIT_FAILURE_ID}">'
            f"The tracker couldn't save changes to '{_escape(context.task.title)}', and nothing "
            "was changed. What you typed is still in the form. Try again.</p>\n"
        )
    shown = form.shown if refusal is not None or form.failed else saved
    hidden = "".join(
        f'<input type="hidden" name="shown_{name}" value="{_escape(value)}">\n'
        for name in ("title", "priority", "assignee", "due_date")
        if (value := getattr(shown, name)) is not None
    )
    fields = (
        _task_field(
            _EDIT_TITLE_ID,
            "Title",
            title_control,
            reason_for(TaskEditRefusal.BLANK_TITLE, TaskEditRefusal.TOO_LONG),
            reason_id,
        )
        + _task_field(
            _EDIT_PRIORITY_ID,
            "Priority",
            priority_control,
            reason_for(TaskEditRefusal.INVALID_PRIORITY),
            reason_id,
        )
        + _task_field(
            _EDIT_ASSIGNEE_ID,
            "Assignee",
            assignee_control,
            reason_for(TaskEditRefusal.ASSIGNEE_NOT_LISTED),
            reason_id,
            notice,
        )
        + _task_field(
            _EDIT_DUE_DATE_ID,
            "Due date",
            date_control,
            reason_for(TaskEditRefusal.INVALID_DUE_DATE),
            reason_id,
        )
    )
    return (
        f"<form {form_attributes}>\n{fields}{failure_block}{hidden}"
        '<button type="submit">Save</button>\n</form>\n'
    )


NO_LABELS = "This task has no labels. Type a label and press Add."


class _LabelOutcome(Enum):
    """What the label area has to say, and so which element its line describes."""

    FIELD_REASON = "field-reason"
    STALE_REMOVE = "stale-remove"
    FAILED_ADD = "failed-add"
    FAILED_REMOVE = "failed-remove"
    ADDED = "added"
    REMOVED = "removed"


def _label_outcome(area: LabelArea, task: Task) -> tuple[_LabelOutcome, str] | None:
    """The one outcome to show: refusal, then failure, then added, then removed.

    Returns the outcome and its line, or None for a plain page. An added label the task does not
    carry has nothing to take focus, so it is no outcome.
    """
    title = _escape(task.title)
    label = _escape(area.label)
    if area.refusal is LabelRefusal.EMPTY:
        return _LabelOutcome.FIELD_REASON, "A label needs at least one character. Type a label."
    if area.refusal is LabelRefusal.TOO_LONG:
        line = f"A label can't be longer than {_characters(SHORT_TEXT_MAX)}. Type a shorter one."
        return _LabelOutcome.FIELD_REASON, line
    if area.refusal is LabelRefusal.NOT_CARRIED:
        line = (
            f"The label '{label}' isn't on '{title}'. "
            "The labels shown are the ones the task carries."
        )
        return _LabelOutcome.STALE_REMOVE, line
    if area.failed is FailedAction.ADD:
        line = (
            f"The tracker couldn't add the label '{label}' to '{title}', and nothing was changed. "
            "What you typed is still in the form. Try again."
        )
        return _LabelOutcome.FAILED_ADD, line
    if area.failed is FailedAction.REMOVE:
        line = (
            f"The tracker couldn't remove the label '{label}' from '{title}', and nothing was "
            "changed. Try again."
        )
        return _LabelOutcome.FAILED_REMOVE, line
    if area.added is not None and area.added in task.labels:
        return _LabelOutcome.ADDED, f"You added the label '{_escape(area.added)}' to '{title}'."
    if area.removed is not None:
        line = f"You removed the label '{_escape(area.removed)}' from '{title}'."
        return _LabelOutcome.REMOVED, line
    return None


def _label_row(position: int, task: Task, label: str, focus: bool) -> str:
    """One carried label and its Remove; `focus` says the added-label outcome lands on this row."""
    text_attributes = f'class="label-text pre-wrap" id="label-{position}"'
    if focus:
        text_attributes += f' tabindex="-1" autofocus aria-describedby="{_LABEL_ADDED_LINE_ID}"'
    name = f"Remove label '{_escape(label)}' from '{_escape(task.title)}'"
    return (
        "<li>"
        f"<span {text_attributes}>{_escape(label)}</span>\n"
        f'<form method="post" action="/tasks/{task.id}/labels/remove" class="remove-form">'
        f'<button type="submit" id="remove-label-{position}" aria-label="{name}">Remove</button>'
        f'<input type="hidden" name="label" value="{_escape(label)}">'
        "</form></li>\n"
    )


def _label_section(task: Task, area: LabelArea, outcome: tuple[_LabelOutcome, str] | None) -> str:
    """The label area: its heading, the labels or the no-labels sentence, and the Add form.

    Where an outcome lands: a field reason on the label field, a failed add on the Add form, a
    stale or failed remove on this section, an added label on that label's text. A removal's line
    is the task heading's, so the section shows none.
    """
    kind, line = outcome if outcome is not None else (None, "")
    section_attributes = f'id="{_LABELS_ID}" class="sheet"'
    if kind in (_LabelOutcome.STALE_REMOVE, _LabelOutcome.FAILED_REMOVE):
        reason_id = _LABEL_REASON_ID if kind is _LabelOutcome.STALE_REMOVE else _LABEL_FAILURE_ID
        section_attributes += f' tabindex="-1" autofocus aria-describedby="{reason_id}"'
        outcome_block = f'<p class="reason" id="{reason_id}">{line}</p>\n'
    elif kind is _LabelOutcome.ADDED:
        outcome_block = f'<p class="outcome" id="{_LABEL_ADDED_LINE_ID}">{line}</p>\n'
    else:
        outcome_block = ""
    added = task.labels.index(area.added) if kind is _LabelOutcome.ADDED and area.added else None
    if task.labels:
        rows = "".join(
            _label_row(position, task, label, added == position - 1)
            for position, label in enumerate(task.labels, start=1)
        )
        shown = f'<ul class="label-list">\n{rows}</ul>\n'
    else:
        shown = f'<p class="empty">{NO_LABELS}</p>\n'
    return (
        f"<section {section_attributes}>\n"
        "<h2>Labels</h2>\n"
        f"{outcome_block}{shown}{_label_add_form(task, area, kind, line)}"
        "</section>\n"
    )


def _label_add_form(task: Task, area: LabelArea, kind: _LabelOutcome | None, line: str) -> str:
    """The Add form: a labelled field and Add, with a field reason or a failure when one landed."""
    field_attributes = (
        f'type="text" id="{_LABEL_FIELD_ID}" name="label" maxlength="{SHORT_TEXT_MAX}"'
    )
    kept = area.label if kind is _LabelOutcome.FAILED_ADD else ""
    field_attributes += f' value="{_escape(kept)}"'
    reason = None
    if kind is _LabelOutcome.FIELD_REASON:
        field_attributes += f' autofocus aria-describedby="{_LABEL_REASON_ID}"'
        reason = line
    form_attributes = f'method="post" action="/tasks/{task.id}/labels" class="create-form"'
    failure_block = ""
    if kind is _LabelOutcome.FAILED_ADD:
        form_attributes += f' tabindex="-1" autofocus aria-describedby="{_LABEL_FAILURE_ID}"'
        failure_block = f'<p class="reason" id="{_LABEL_FAILURE_ID}">{line}</p>\n'
    field = _task_field(
        _LABEL_FIELD_ID, "Label", f"<input {field_attributes}>\n", reason, _LABEL_REASON_ID
    )
    return (
        f"<form {form_attributes}>\n{field}{failure_block}"
        '<button type="submit">Add</button>\n</form>\n'
    )


NO_COMMENTS = "This task has no comments yet."
NO_COMMENTS_NEXT = f"{NO_COMMENTS} Type a comment and press Add."
COMMENT_NOTICE = (
    f'You need a name to comment. Set your name on the <a href="{PEOPLE_ADDRESS}">People</a> page.'
)
_COMMENT_REASONS = {
    CommentRefusal.TOO_LONG: (
        f"A comment can't be longer than {_characters(LONG_TEXT_MAX)}. Type a shorter one."
    ),
    CommentRefusal.BLANK: "A comment can't be blank. Type a comment.",
    CommentRefusal.NO_NAME: (
        "A comment needs your name. Set it on the People page, then add the comment."
    ),
}


def _comment_outcome(area: CommentArea, task: Task) -> tuple[_CommentOutcome, str] | None:
    """The one outcome to show: refusal, then failure, then added; None for a plain area.

    Returns the outcome and its line. An added position the task has no comment at has nothing to
    take focus, so it is no outcome.
    """
    if area.refusal is not None:
        return _CommentOutcome.REFUSED, _COMMENT_REASONS[area.refusal]
    title = _escape(task.title)
    if area.failed:
        line = (
            f"The tracker couldn't add your comment to '{title}', and nothing was changed. "
            "What you typed is still in the form. Try again."
        )
        return _CommentOutcome.FAILED, line
    if area.added_position is not None and 1 <= area.added_position <= len(task.comments):
        return _CommentOutcome.ADDED, f"You added a comment to '{title}'."
    return None


def _comment_item(position: int, comment: Comment, focus: bool) -> str:
    """One comment: its author and local time above its text; `focus` says the added-comment
    outcome lands on this one."""
    attributes = f'id="comment-{position}"'
    if focus:
        attributes += f' tabindex="-1" autofocus aria-describedby="{_COMMENT_ADDED_LINE_ID}"'
    return (
        f"<li {attributes}>\n"
        f'<p class="comment-meta pre-wrap">'
        f"{_escape(comment.author)}, {_written(comment.created_at)}</p>\n"
        f'<p class="comment-text pre-wrap">{_escape(comment.text)}</p>\n'
        "</li>\n"
    )


def _comment_add_form(
    task: Task, area: CommentArea, kind: _CommentOutcome | None, line: str
) -> str:
    """The Add form: a labelled four-line field with its maximum, and Add. A refusal focuses the
    field and describes it; a failure focuses Add and describes it. No native control stops an
    empty or unnamed submission, so the refusal is the tracker's."""
    refused = kind is _CommentOutcome.REFUSED
    keeps_text = kind is _CommentOutcome.FAILED or (
        refused and area.refusal is not CommentRefusal.TOO_LONG
    )
    field_attributes = f'id="{_COMMENT_FIELD_ID}" name="text" rows="4" maxlength="{LONG_TEXT_MAX}"'
    field_attributes += (
        f' autofocus aria-describedby="{_COMMENT_REASON_ID}"'
        if refused
        else f' aria-describedby="{_COMMENT_NOTE_ID}"'
    )
    reason_block = f'<p class="reason" id="{_COMMENT_REASON_ID}">{line}</p>\n' if refused else ""
    button_attributes = (
        f'type="submit" id="{_ADD_COMMENT_ID}"'
        f" aria-label=\"Add comment to '{_escape(task.title)}'\""
    )
    failure_block = ""
    if kind is _CommentOutcome.FAILED:
        button_attributes += f' autofocus aria-describedby="{_COMMENT_FAILURE_ID}"'
        failure_block = f'<p class="reason" id="{_COMMENT_FAILURE_ID}">{line}</p>\n'
    return (
        f'<form method="post" action="/tasks/{task.id}/comments" class="create-form">\n'
        '<div class="field">\n'
        f'<label for="{_COMMENT_FIELD_ID}">Comment</label>\n'
        f'<p class="note" id="{_COMMENT_NOTE_ID}">'
        f"A comment can hold up to {_characters(LONG_TEXT_MAX)}.</p>\n"
        f"{reason_block}"
        f"{_textarea(field_attributes, area.text if keeps_text else '')}"
        "</div>\n"
        f"{failure_block}"
        f"<button {button_attributes}>Add</button>\n"
        "</form>\n"
    )


def _comment_section(
    task: Task,
    area: CommentArea,
    operator_name: str | None,
    outcome: tuple[_CommentOutcome, str] | None,
) -> str:
    """The comments area: its heading, the comments or the no-comments line, the no-name notice
    while no name is saved, and the Add form. The comments keep the order they were added."""
    kind, line = outcome if outcome is not None else (None, "")
    added = (
        area.added_position - 1 if kind is _CommentOutcome.ADDED and area.added_position else None
    )
    completion = (
        f'<p class="outcome" id="{_COMMENT_ADDED_LINE_ID}">{line}</p>\n'
        if kind is _CommentOutcome.ADDED
        else ""
    )
    if task.comments:
        rows = "".join(
            _comment_item(position, comment, added == position - 1)
            for position, comment in enumerate(task.comments, start=1)
        )
        shown = f'<ol class="comment-list">\n{rows}</ol>\n'
    else:
        shown = (
            f'<p class="empty">{NO_COMMENTS if operator_name is None else NO_COMMENTS_NEXT}</p>\n'
        )
    notice = f'<p class="notice">{COMMENT_NOTICE}</p>\n' if operator_name is None else ""
    return (
        f'<section id="{_COMMENTS_ID}" class="sheet">\n'
        "<h2>Comments</h2>\n"
        f"{completion}{shown}{notice}{_comment_add_form(task, area, kind, line)}"
        "</section>\n"
    )


def _status_section(
    task: Task, allowed: tuple[TaskStatus, ...], line: tuple[_MoveKind, str] | None
) -> str:
    """The status area: its heading, the status in words, the moves the page offers and, after a
    press, the one line beside them."""
    word = _status_word(task, line, "p", f' class="status-word" id="{_TASK_STATUS_ID}"')
    return (
        f'<section id="{_STATUS_ID}" class="sheet">\n'
        "<h2>Status</h2>\n"
        f"{word}\n"
        f"{_move_forms(task, MOVE_PLACE_TASK, allowed)}"
        f"{_move_line_block(line)}"
        "</section>\n"
    )


def task_page(
    context: TaskEditContext,
    *,
    form: TaskEditForm | None = None,
    added: bool = False,
    saved: bool = False,
    label_area: LabelArea | None = None,
    comment_area: CommentArea | None = None,
    operator_name: str | None = None,
    allowed_moves: AllowedMoves = _no_moves,
    move_outcome: MoveOutcome | None = None,
) -> str:
    """One task: its title, its project as text, the form that edits its four fields, its labels
    and its comments.

    The form shows the saved values, or the retained ones `form` hands in after a refusal or a
    failure. With `added` or `saved` it opens on its heading, which the completion line describes;
    a refused or failed form takes focus instead, and so no completion line shows with one. A label
    outcome in `label_area` is the page's one outcome: it takes precedence, and the edit form's own
    outcomes are then not shown, so exactly one element takes focus. A comment outcome in
    `comment_area` takes precedence over all of them. `operator_name` is the name saved now, with
    None while none is: it decides whether the comments area shows its no-name notice. The status
    area offers the moves `allowed_moves` gives for the saved status; a `move_outcome` about this
    task takes precedence over every other outcome, and the status word takes the one focus.
    """
    task = context.task
    move_line = _move_line(move_outcome, task)
    if move_line is not None:
        form, added, saved, label_area, comment_area = None, False, False, None, None
    comment_area = comment_area or CommentArea()
    comment_outcome = _comment_outcome(comment_area, task)
    if comment_outcome is not None:
        form, added, saved, label_area = None, False, False, None
    label_area = label_area or LabelArea()
    label_outcome = _label_outcome(label_area, task)
    if label_outcome is not None:
        form, added, saved = None, False, False
    form = form or TaskEditForm()
    heading_attributes = ' tabindex="-1"'
    line = ""
    outcome_on_form = form.refusal is not None or form.failed
    if label_outcome is not None and label_outcome[0] is _LabelOutcome.REMOVED:
        heading_attributes += f' autofocus aria-describedby="{_LABEL_REMOVED_LINE_ID}"'
        line = f'<p class="removed" id="{_LABEL_REMOVED_LINE_ID}">{label_outcome[1]}</p>\n'
    elif added and not outcome_on_form:
        heading_attributes += f' autofocus aria-describedby="{_ADDED_LINE_ID}"'
        line = f'<p class="added" id="{_ADDED_LINE_ID}">You added \'{_escape(task.title)}\'.</p>\n'
    elif saved and not outcome_on_form:
        heading_attributes += f' autofocus aria-describedby="{_SAVED_LINE_ID}"'
        line = (
            f'<p class="saved" id="{_SAVED_LINE_ID}">'
            f"You saved changes to '{_escape(task.title)}'.</p>\n"
        )
    body = (
        f'<h1 class="pre-wrap"{heading_attributes}>{_escape(task.title)}</h1>\n'
        f"{line}"
        '<dl class="task-facts">\n'
        f'<dt>Project</dt><dd class="pre-wrap">{_escape(context.project.name)}</dd>\n'
        "</dl>\n"
        f"{_edit_form(context, form)}"
        f"{_status_section(task, allowed_moves(task.status), move_line)}"
        f"{_label_section(task, label_area, label_outcome)}"
        f"{_comment_section(task, comment_area, operator_name, comment_outcome)}"
    )
    return _document(f"{task.title} - tracker17", body)


def not_found_page() -> str:
    """The page for an address with nothing at it: the same for every address, showing none.

    It takes no argument, so no part of an address can reach it (CP-33).
    """
    body = (
        "<h1>There's no project at this address</h1>\n"
        f'<p>Open <a href="{PROJECTS_ADDRESS}">Projects</a>.</p>\n'
    )
    return _document("Not found - tracker17", body)


def task_not_found_page() -> str:
    """The page for an address shaped like a task's that names no task; it shows none of it."""
    body = (
        "<h1>There's no task at this address</h1>\n"
        f'<p>Open <a href="{PROJECTS_ADDRESS}">Projects</a>.</p>\n'
    )
    return _document("Not found - tracker17", body)


class _Outcome(Enum):
    """What an action left for the page to say, and so which element its line describes."""

    ADDED = "added"
    REMOVED = "removed"
    STALE_REMOVE = "stale-remove"
    FAILED_ADD = "failed-add"
    FAILED_REMOVE = "failed-remove"


def _field_reason(refusal: AssigneeRefusal | None, name: str) -> str | None:
    """The reason beside the name field, for the three refusals the field itself shows."""
    if refusal is AssigneeRefusal.BLANK_NAME:
        return "An assignee needs a name. Type one."
    if refusal is AssigneeRefusal.ASSIGNEE_NAME_IN_USE:
        return (
            f"An assignee named '{_escape(name)}' is already on the list. Choose a different name."
        )
    if refusal is AssigneeRefusal.TOO_LONG:
        return (
            f"An assignee name can't be longer than {_characters(SHORT_TEXT_MAX)}. "
            "Type a shorter one."
        )
    return None


def _outcome_line(
    refusal: AssigneeRefusal | None,
    failed: FailedAction | None,
    added: str | None,
    removed: str | None,
    name: str,
) -> tuple[_Outcome, str, str] | None:
    """The one outcome to show: refusal, then failure, then success (added before removed).

    Returns the outcome, the name it is about and its line, or None for a plain page.
    """
    if refusal is AssigneeRefusal.ASSIGNEE_NOT_FOUND:
        line = (
            f"The name '{_escape(name)}' is no longer on the assignee list. "
            f'Open <a href="{PEOPLE_ADDRESS}">People</a> again to reload the list.'
        )
        return _Outcome.STALE_REMOVE, name, line
    if failed is FailedAction.ADD:
        line = (
            f"The tracker couldn't add '{_escape(name)}' to the assignees, and nothing was "
            "changed. What you typed is still in the form. Try again."
        )
        return _Outcome.FAILED_ADD, name, line
    if failed is FailedAction.REMOVE:
        line = (
            f"The tracker couldn't remove '{_escape(name)}' from the assignees, and nothing was "
            "changed. Try again."
        )
        return _Outcome.FAILED_REMOVE, name, line
    if added is not None:
        return _Outcome.ADDED, added, f"You added '{_escape(added)}' to the assignees."
    if removed is not None:
        line = (
            f"You removed '{_escape(removed)}' from the assignees, "
            "and tasks that already carry the name keep it."
        )
        return _Outcome.REMOVED, removed, line
    return None


def _assignee_row(position: int, name: str, focus: _Outcome | None, line: str) -> str:
    """One listed name and its Remove; `focus` says whether the outcome lands on this row."""
    name_attributes = f'class="assignee-name pre-wrap" id="assignee-{position}"'
    if focus is _Outcome.ADDED:
        name_attributes += f' tabindex="-1" autofocus aria-describedby="{_OUTCOME_LINE_ID}"'
    button_attributes = (
        f'type="submit" id="remove-{position}" '
        f"aria-label=\"Remove '{_escape(name)}', number {position} on the assignee list\""
    )
    failure_block = ""
    if focus is _Outcome.FAILED_REMOVE:
        button_attributes += f' autofocus aria-describedby="{_REMOVE_FAILURE_ID}"'
        failure_block = f'<p class="reason" id="{_REMOVE_FAILURE_ID}">{line}</p>\n'
    return (
        "<li>"
        f"<span {name_attributes}>{_escape(name)}</span>\n"
        f"{failure_block}"
        f'<form method="post" action="{REMOVE_ASSIGNEE_ADDRESS}" class="remove-form">'
        f"<button {button_attributes}>Remove</button>"
        f'<input type="hidden" name="name" value="{_escape(name)}">'
        "</form></li>\n"
    )


def _assignee_list(
    assignees: Sequence[str], target: int | None, outcome: _Outcome | None, line: str
) -> str:
    """The list in the order given, or the empty text; `target` is the row the outcome lands on."""
    if not assignees:
        return f'<p class="empty">{EMPTY_ASSIGNEES}</p>\n'
    rows = [
        _assignee_row(position, name, outcome if target == position - 1 else None, line)
        for position, name in enumerate(assignees, start=1)
    ]
    return '<ul class="assignee-list">\n' + "".join(rows) + "</ul>\n"


def _assignee_form(reason: str | None, failure: str | None, name: str) -> str:
    field_attributes = (
        f'type="text" id="{_ASSIGNEE_NAME_FIELD_ID}" name="name" maxlength="{SHORT_TEXT_MAX}" '
        f'value="{_escape(name)}"'
    )
    reason_block = ""
    if reason is not None:
        field_attributes += f' autofocus aria-describedby="{_ASSIGNEE_REASON_ID}"'
        reason_block = f'<p class="reason" id="{_ASSIGNEE_REASON_ID}">{reason}</p>\n'
    button_attributes = 'type="submit"'
    failure_block = ""
    if failure is not None:
        button_attributes += f' autofocus aria-describedby="{_ADD_FAILURE_ID}"'
        failure_block = f'<p class="reason" id="{_ADD_FAILURE_ID}">{failure}</p>\n'
    return (
        f'<form method="post" action="{ADD_ASSIGNEE_ADDRESS}" class="create-form">\n'
        '<div class="field">\n'
        f'<label for="{_ASSIGNEE_NAME_FIELD_ID}">Name</label>\n'
        f"{reason_block}"
        f"<input {field_attributes}>\n"
        "</div>\n"
        f"{failure_block}"
        f"<button {button_attributes}>Add</button>\n"
        "</form>\n"
    )


def _operator_outcome(area: OperatorNameArea) -> _OperatorOutcome | None:
    """The one outcome to show: refusal, then failure, then completion; None for a plain section."""
    if area.refusal is OperatorNameRefusal.BLANK_NAME:
        return _OperatorOutcome.BLANK
    if area.refusal is OperatorNameRefusal.TOO_LONG:
        return _OperatorOutcome.TOO_LONG
    if area.failed:
        return _OperatorOutcome.FAILED
    if area.saved is not None:
        return _OperatorOutcome.COMPLETED
    return None


def _operator_field_value(
    outcome: _OperatorOutcome | None, area: OperatorNameArea, operator_name: str | None
) -> str:
    """The text in the field: what was typed after a blank refusal or a failure, else the saved
    name, or nothing when none is saved."""
    keeps_typed = outcome in (_OperatorOutcome.BLANK, _OperatorOutcome.FAILED)
    if keeps_typed and area.typed is not None:
        return area.typed
    return operator_name or ""


def _operator_line(outcome: _OperatorOutcome, shown: str, area: OperatorNameArea) -> str:
    if outcome is _OperatorOutcome.BLANK:
        return "Your name can't be blank. Type a name."
    if outcome is _OperatorOutcome.TOO_LONG:
        return f"Your name can't be longer than {_characters(SHORT_TEXT_MAX)}. Type a shorter one."
    if outcome is _OperatorOutcome.FAILED:
        return (
            f"The tracker couldn't set your name to '{_escape(shown)}', and nothing was changed. "
            "What you typed is still in the form. Try again."
        )
    return f"You set your name to '{_escape(area.saved or '')}'."


def _your_name_section(operator_name: str | None, area: OperatorNameArea) -> str:
    """The Your name section: the form, the one outcome line and, while no name is saved, the
    no-name line. Success and both refusals focus the field; a failure focuses Save."""
    outcome = _operator_outcome(area)
    shown = _operator_field_value(outcome, area, operator_name)
    field_attributes = (
        f'type="text" id="{_OPERATOR_FIELD_ID}" name="name" maxlength="{SHORT_TEXT_MAX}" '
        f'value="{_escape(shown)}"'
    )
    button_attributes = f'type="submit" id="{_OPERATOR_SAVE_ID}"'
    completion_block = reason_block = failure_block = ""
    if outcome is not None:
        line = _operator_line(outcome, shown, area)
        paragraph = f'<p class="{{}}" id="{_OPERATOR_OUTCOME_ID}">{line}</p>\n'
        description = f' autofocus aria-describedby="{_OPERATOR_OUTCOME_ID}"'
        if outcome is _OperatorOutcome.FAILED:
            button_attributes += description
            failure_block = paragraph.format("reason")
        else:
            field_attributes += description
            if outcome is _OperatorOutcome.COMPLETED:
                completion_block = paragraph.format("outcome")
            else:
                reason_block = paragraph.format("reason")
    no_name_block = (
        '<p class="empty">No name is set. You need a name to comment.</p>\n'
        if operator_name is None
        else ""
    )
    return (
        f'<section class="sheet" id="{_YOUR_NAME_ID}">\n'
        f'<h2 id="{_YOUR_NAME_HEADING_ID}">Your name</h2>\n'
        f"{completion_block}"
        f'<form method="post" action="{OPERATOR_NAME_ADDRESS}" class="create-form">\n'
        '<div class="field">\n'
        f'<label for="{_OPERATOR_FIELD_ID}">Your name</label>\n'
        '<p class="note">Comments you\'ve already written keep the name they were written '
        "under.</p>\n"
        f"{reason_block}"
        f"<input {field_attributes}>\n"
        "</div>\n"
        f"{failure_block}"
        f"<button {button_attributes}>Save</button>\n"
        "</form>\n"
        f"{no_name_block}"
        "</section>\n"
    )


def people_page(
    assignees: Sequence[str],
    *,
    added: str | None = None,
    removed: str | None = None,
    refusal: AssigneeRefusal | None = None,
    failed: FailedAction | None = None,
    name: str = "",
    operator_name: str | None = None,
    operator_area: OperatorNameArea | None = None,
) -> str:
    """The People page: the Your name section above the assignee list and the Add form.

    At most one outcome shows in each section. A recognized Your name outcome (refusal, then
    failure, then completion) takes the page's one focus and suppresses every assignee outcome. An
    assignee outcome is chosen as refusal, then failure, then success (added before removed); its
    line describes the one element that takes focus: the added name, the name field or the Add
    button, the Remove that failed, or, where that row is not listed or the list is the subject,
    the Assignees heading. A too-long refusal shows none of the submitted text.
    """
    area = operator_area or OperatorNameArea()
    if _operator_outcome(area) is not None:
        added = removed = refusal = failed = None
        name = ""
    if refusal is AssigneeRefusal.TOO_LONG:
        added = removed = failed = None
        name = ""
    reason = _field_reason(refusal, name)
    found = None if reason is not None else _outcome_line(refusal, failed, added, removed, name)
    outcome, subject, line = found if found is not None else (None, "", "")
    row_outcomes = (_Outcome.ADDED, _Outcome.FAILED_REMOVE)
    target = assignees.index(subject) if outcome in row_outcomes and subject in assignees else None
    on_heading = outcome is not None and outcome is not _Outcome.FAILED_ADD and target is None
    heading_attributes = f'id="{_ASSIGNEES_HEADING_ID}"'
    outcome_block = ""
    if on_heading:
        heading_attributes += f' tabindex="-1" autofocus aria-describedby="{_OUTCOME_LINE_ID}"'
    if on_heading or outcome is _Outcome.ADDED:
        outcome_block = f'<p class="outcome" id="{_OUTCOME_LINE_ID}">{line}</p>\n'
    kept = name if reason is not None or outcome is _Outcome.FAILED_ADD else ""
    failure = line if outcome is _Outcome.FAILED_ADD else None
    body = (
        "<h1>People</h1>\n"
        f"{_your_name_section(operator_name, area)}"
        '<section class="sheet">\n'
        f"<h2 {heading_attributes}>Assignees</h2>\n"
        f"{outcome_block}"
        f"{_assignee_list(assignees, target, outcome, line)}"
        f"{_assignee_form(reason, failure, kept)}"
        "</section>\n"
    )
    return _document("People - tracker17", body)
