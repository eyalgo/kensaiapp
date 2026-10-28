"""The whole request path in one process, with no socket: `Site.handle` (SDD § 3 web; NFDR QC-7).

A request is checked, routed, answered and turned into a `Response`. Page building is `pages.py`;
every rule is `application`'s and `domain`'s. The site keeps no state between requests of its own:
the one lock lives on the object and serializes the requests that reach the tracker (RT-6).
"""

from __future__ import annotations

import re
import sys
import threading
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from http import HTTPStatus
from pathlib import Path
from typing import TypeVar
from urllib.parse import parse_qs, urlencode

from application import (
    AssigneeNameInUse,
    AssigneeNotFound,
    AssigneeNotListed,
    BlankComment,
    BlankName,
    BlankTitle,
    EmptyLabel,
    FilterField,
    FilterInput,
    InvalidDueDate,
    InvalidPriority,
    InvalidTaskStatus,
    LabelNotCarried,
    MoveNotAllowed,
    NameInUse,
    OperatorNameNotSet,
    Project,
    ProjectNotFound,
    ProjectTaskList,
    SortControl,
    SortInput,
    Task,
    TaskFields,
    TaskNotFound,
    TaskStatus,
    TextField,
    TextTooLong,
    Tracker,
)
from web import pages

Code = TypeVar("Code", bound=Enum)

PAGE = "page"
SUBMISSION = "submission"

PAGE_POLICY = "default-src 'self'; script-src 'none'; form-action 'self'; frame-ancestors 'none'"
HTML_TYPE = "text/html; charset=utf-8"
CSS_TYPE = "text/css; charset=utf-8"
FORM_ENCODING = "utf-8"
STYLESHEET_FILE = Path(__file__).resolve().with_name("style.css")

REFUSED_FROM_ANOTHER_SITE = {"cross-site", "same-site"}
SAME_ORIGIN = "same-origin"

PROJECTS_ADDRESS = "/"
PEOPLE_ADDRESS = "/people"
ALL_TASKS_ADDRESS = "/tasks"
PROJECT_PATTERN = re.compile(r"/projects/([0-9]+)")
SUMMARY_PATTERN = re.compile(r"/projects/([0-9]+)/summary")
TASK_PATTERN = re.compile(r"/tasks/([0-9]+)")
ADD_TASK_PATTERN = re.compile(r"/projects/([0-9]+)/tasks")
RENAME_PATTERN = re.compile(r"/projects/([0-9]+)/rename")
ADD_LABEL_PATTERN = re.compile(r"/tasks/([0-9]+)/labels")
REMOVE_LABEL_PATTERN = re.compile(r"/tasks/([0-9]+)/labels/remove")
ADD_COMMENT_PATTERN = re.compile(r"/tasks/([0-9]+)/comments")
MOVE_PATTERN = re.compile(r"/tasks/([0-9]+)/move")
CONFIRM_MOVE_PATTERN = re.compile(r"/tasks/([0-9]+)/move/confirm")
DELETE_PATTERN = re.compile(r"/tasks/([0-9]+)/delete")
CONFIRM_DELETE_PATTERN = re.compile(r"/tasks/([0-9]+)/delete/confirm")
DELETE_CONFIRM_KEY = "delete_confirm"
DELETE_BACK_KEY = pages.DELETE_BACK_KEY
DELETE_FAILED_KEY = "delete_failed"
DELETED_TASK_KEY = "deleted_task"
NOT_STORED = ("Cache-Control", "no-store")
SHOWN_PREFIX = "shown_"
FILTER_PREFIX = "filter_"
SORT_PREFIX = "sort_"
TASK_FIELDS = ("title", "priority", "assignee", "due_date")
EDIT_FAILED = "save"
OPERATOR_NAME_FAILED = "save"
RENAME_FAILED = "save"
COMMENT_FAILED = "add"


@dataclass(frozen=True)
class Response:
    """A status, the headers, and the body bytes."""

    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes


@dataclass(frozen=True)
class Route:
    """One answered address: the method, the path as a regular expression, and its kind."""

    method: str
    pattern: str
    kind: str


@dataclass(frozen=True)
class ProjectRefusal:
    """A refused project name or description as the pages know it: the code an address carries,
    and for a too-long value the field that was too long."""

    code: pages.ProjectNameRefusal
    field: TextField | None = None


ROUTES = (
    Route("GET", "/", PAGE),
    Route("GET", "/projects/[0-9]+", PAGE),
    Route("GET", "/projects/[0-9]+/summary", PAGE),
    Route("POST", "/projects", SUBMISSION),
    Route("GET", "/people", PAGE),
    Route("GET", "/tasks", PAGE),
    Route("POST", "/assignees", SUBMISSION),
    Route("POST", "/assignees/remove", SUBMISSION),
    Route("POST", "/operator-name", SUBMISSION),
    Route("POST", "/projects/[0-9]+/tasks", SUBMISSION),
    Route("POST", "/projects/[0-9]+/rename", SUBMISSION),
    Route("GET", "/tasks/[0-9]+", PAGE),
    Route("POST", "/tasks/[0-9]+", SUBMISSION),
    Route("POST", "/tasks/[0-9]+/labels", SUBMISSION),
    Route("POST", "/tasks/[0-9]+/labels/remove", SUBMISSION),
    Route("POST", "/tasks/[0-9]+/comments", SUBMISSION),
    Route("POST", "/tasks/[0-9]+/move", SUBMISSION),
    Route("POST", "/tasks/[0-9]+/move/confirm", SUBMISSION),
    Route("POST", "/tasks/[0-9]+/delete", SUBMISSION),
    Route("POST", "/tasks/[0-9]+/delete/confirm", SUBMISSION),
    Route("GET", "/style.css", PAGE),
)


def _respond(status: int, body: bytes = b"", *extra: tuple[str, str]) -> Response:
    return Response(status, (*extra, ("Content-Security-Policy", PAGE_POLICY)), body)


def _address(path: str, *flags: str, **query: str | tuple[str, ...]) -> str:
    """The one place an address is built, for every redirect a submission answers with (RT-8).

    A flag is a bare word in the query (`?created`); a value is a `key=value` pair. A tuple is a
    key repeated once for each value in it, in order and with empty values kept, as the filter's
    carried choices need.
    """
    encoded = urlencode(query, doseq=True)
    parts = [*flags, encoded] if encoded else list(flags)
    return f"{path}?{'&'.join(parts)}" if parts else path


def _first(values: Mapping[str, list[str]], key: str) -> str:
    found = values.get(key)
    return found[0] if found else ""


def _form(body: bytes) -> dict[str, list[str]] | None:
    """The form body read as strict UTF-8, or None when its bytes are not UTF-8 (a 400)."""
    try:
        return parse_qs(
            body.decode(FORM_ENCODING),
            keep_blank_values=True,
            encoding=FORM_ENCODING,
            errors="strict",
        )
    except UnicodeDecodeError:
        return None


def _optional(values: Mapping[str, list[str]], key: str) -> str | None:
    """The first value for a key, or None when the request does not carry the key at all."""
    found = values.get(key)
    return _line_feeds(found[0]) if found else None


def _fields(values: Mapping[str, list[str]], prefix: str = "") -> TaskFields:
    """The four task fields a form or an address carries, absence kept apart from empty (CP-151)."""
    return TaskFields(**{name: _optional(values, prefix + name) for name in TASK_FIELDS})


def _carried(submitted: TaskFields, shown: TaskFields) -> dict[str, str]:
    """The query that carries both field sets through a redirect, leaving out what was absent."""
    carried = {name: value for name, value in asdict(submitted).items() if value is not None}
    carried.update(
        {SHOWN_PREFIX + name: value for name, value in asdict(shown).items() if value is not None}
    )
    return carried


def _filter_input(values: Mapping[str, list[str]]) -> FilterInput:
    """The seven filter keys an address carries, every value of each kept as sent (CP-405).

    A key the address lacks is an empty tuple; any other key is not a filter and is not read.
    """
    return FilterInput(
        **{field.value: tuple(values.get(FILTER_PREFIX + field.value, ())) for field in FilterField}
    )


def _sort_input(values: Mapping[str, list[str]]) -> SortInput:
    """The two sort keys an address carries, every value of each kept as sent: blank values stay,
    repeats stay, and nothing is trimmed, folded or aliased (CP-441).

    A key the address lacks is an empty tuple; any other key is not a sort and is not read.
    """
    return SortInput(
        **{
            control.value: tuple(values.get(SORT_PREFIX + control.value, ()))
            for control in SortControl
        }
    )


def _carried_filters(values: Mapping[str, list[str]]) -> dict[str, str | tuple[str, ...]]:
    """The filter keys a move form carries back to its list, every value kept as sent, in control
    order. A key the form lacks is left out; nothing else the form carries is read."""
    return {
        key: tuple(values[key])
        for key in (FILTER_PREFIX + field.value for field in FilterField)
        if key in values
    }


def _carried_sorts(values: Mapping[str, list[str]]) -> dict[str, str | tuple[str, ...]]:
    """The sort keys a move form carries back to its list, every value kept as sent, blank and
    repeated ones too (CP-439). A key the form lacks stays absent."""
    return {
        key: tuple(values[key])
        for key in (SORT_PREFIX + control.value for control in SortControl)
        if key in values
    }


def _closed(vocabulary: type[Code], value: str) -> Code | None:
    """The member of a closed vocabulary an address names, or None for a code it does not know."""
    try:
        return vocabulary(value)
    except ValueError:
        return None


def _position(digits: str) -> int | None:
    """The one-based place an address names, or None for anything but ASCII digits that make one."""
    if not (digits.isascii() and digits.isdigit()):
        return None
    try:
        position = int(digits)
    except ValueError:
        # More digits than Python reads as an int: a place nothing holds.
        return None
    return position if position >= 1 else None


def _line_feeds(value: str) -> str:
    """CR LF and a lone CR are both saved as LF (RT-10)."""
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _project_refusal(error: BlankName | NameInUse | TextTooLong) -> ProjectRefusal:
    """The one translation of a project's typed refusal, for creation and rename alike. It reads
    the type of the refusal, never its message (CP-555)."""
    if isinstance(error, TextTooLong):
        return ProjectRefusal(pages.ProjectNameRefusal.TOO_LONG, error.field)
    if isinstance(error, NameInUse):
        return ProjectRefusal(pages.ProjectNameRefusal.NAME_IN_USE)
    return ProjectRefusal(pages.ProjectNameRefusal.BLANK_NAME)


class Site:
    """The request path in front of one tracker, for one host."""

    ROUTES = ROUTES

    def __init__(self, tracker: Tracker, own_host: str) -> None:
        self._tracker = tracker
        self._own_host = own_host
        self._lock = threading.Lock()

    def handle(self, method: str, target: str, headers: Mapping[str, str], body: bytes) -> Response:
        """Answer one request. Holds the lock from the check until the response is built."""
        marks = {name.lower(): value for name, value in headers.items()}
        with self._lock:
            if marks.get("host") != self._own_host:
                return _respond(HTTPStatus.FORBIDDEN)
            fetch_site = marks.get("sec-fetch-site")
            if fetch_site in REFUSED_FROM_ANOTHER_SITE:
                return _respond(HTTPStatus.FORBIDDEN)
            path, _, query = target.partition("?")
            route = self._route(method, path)
            if route is None:
                # The page is a fallback for GET, not a route: any other method keeps an empty 404.
                if method == "GET":
                    return self._not_found_page()
                return _respond(HTTPStatus.NOT_FOUND)
            if route.kind == SUBMISSION and fetch_site != SAME_ORIGIN:
                return _respond(HTTPStatus.FORBIDDEN)
            if route.kind == SUBMISSION:
                return self._submit(path, body)
            return self._page(path, parse_qs(query, keep_blank_values=True))

    def _submit(self, path: str, body: bytes) -> Response:
        form = _form(body)
        if form is None:
            return _respond(HTTPStatus.BAD_REQUEST)
        add_task = ADD_TASK_PATTERN.fullmatch(path)
        if add_task:
            return self._add_task(add_task.group(1), form)
        rename = RENAME_PATTERN.fullmatch(path)
        if rename:
            return self._rename_project(rename.group(1), form)
        edit_task = TASK_PATTERN.fullmatch(path)
        if edit_task:
            return self._edit_task(edit_task.group(1), form)
        add_label = ADD_LABEL_PATTERN.fullmatch(path)
        if add_label:
            return self._add_label(add_label.group(1), form)
        remove_label = REMOVE_LABEL_PATTERN.fullmatch(path)
        if remove_label:
            return self._remove_label(remove_label.group(1), form)
        add_comment = ADD_COMMENT_PATTERN.fullmatch(path)
        if add_comment:
            return self._add_comment(add_comment.group(1), form)
        confirm_move = CONFIRM_MOVE_PATTERN.fullmatch(path)
        if confirm_move:
            return self._move_task(confirm_move.group(1), form, confirming=True)
        move = MOVE_PATTERN.fullmatch(path)
        if move:
            return self._move_task(move.group(1), form)
        confirm_delete = CONFIRM_DELETE_PATTERN.fullmatch(path)
        if confirm_delete:
            return self._delete_task(confirm_delete.group(1), confirming=True)
        delete = DELETE_PATTERN.fullmatch(path)
        if delete:
            return self._delete_task(delete.group(1))
        actions = {
            "/projects": self._create,
            "/assignees": self._add_assignee,
            "/assignees/remove": self._remove_assignee,
            "/operator-name": self._set_operator_name,
        }
        return actions[path](form)

    @staticmethod
    def _route(method: str, path: str) -> Route | None:
        for route in ROUTES:
            if route.method == method and re.fullmatch(route.pattern, path):
                return route
        return None

    def _page(self, path: str, query: Mapping[str, list[str]]) -> Response:
        if path == "/style.css":
            return _respond(HTTPStatus.OK, STYLESHEET_FILE.read_bytes(), ("Content-Type", CSS_TYPE))
        if path == PROJECTS_ADDRESS:
            return self._html(self._projects_page(query))
        if path == PEOPLE_ADDRESS:
            return self._html(self._people_page(query))
        if path == ALL_TASKS_ADDRESS:
            return self._all_tasks_page(query)
        task_match = TASK_PATTERN.fullmatch(path)
        if task_match:
            return self._task_page(task_match.group(1), query)
        summary_match = SUMMARY_PATTERN.fullmatch(path)
        if summary_match:
            return self._summary_page(summary_match.group(1))
        match = PROJECT_PATTERN.fullmatch(path)
        project = self._project_named_by(match.group(1)) if match else None
        if project is None:
            return self._not_found_page()
        return self._project_page(project, query)

    @staticmethod
    def _identity(digits: str) -> int | None:
        try:
            return int(digits)
        except ValueError:
            # More digits than Python reads as an int: an identity nothing holds.
            return None

    def _project_named_by(self, digits: str) -> Project | None:
        identity = self._identity(digits)
        return None if identity is None else self._tracker.project(identity)

    def _task_page(self, digits: str, query: Mapping[str, list[str]]) -> Response:
        """Read the edit form's outcome from the address and build the task's page; no change."""
        identity = self._identity(digits)
        context = None if identity is None else self._tracker.task_edit_context(identity)
        if context is None:
            return Site._html(pages.task_not_found_page(), HTTPStatus.NOT_FOUND)
        shown = context.task
        delete_area = self._delete_area(query)
        if delete_area.mode is pages.DeleteMode.ORDINARY:
            move = self._move_view(query, lambda found: shown if found == shown.id else None)
            if move is None:
                return Site._html(pages.task_not_found_page(), HTTPStatus.NOT_FOUND)
            move_outcome, move_interaction = move
        else:
            # An active deletion state wins over every move marker, even one naming no task.
            move_outcome, move_interaction = pages.MoveOutcome(), None
        return self._html(
            pages.task_page(
                context,
                form=self._edit_form(query),
                added="added" in query,
                saved="saved" in query,
                label_area=self._label_area(query),
                comment_area=self._comment_area(query),
                operator_name=self._tracker.operator_name(),
                allowed_moves=self._tracker.allowed_moves,
                move_outcome=move_outcome,
                move_interaction=move_interaction,
                delete_area=delete_area,
            ),
            Site._pending_status(move_interaction),
            extra=self._stored_as_asked(
                query, deleting=delete_area.mode is not pages.DeleteMode.ORDINARY
            ),
        )

    @staticmethod
    def _delete_area(query: Mapping[str, list[str]]) -> pages.DeleteArea:
        """The Delete task area's state from the address, by the presence of each key: a failure
        before a confirmation before a back-out. Any other key, or none, is the ordinary area."""
        if DELETE_FAILED_KEY in query:
            return pages.DeleteArea(pages.DeleteMode.FAILED)
        if DELETE_CONFIRM_KEY in query:
            return pages.DeleteArea(pages.DeleteMode.CONFIRMATION)
        if DELETE_BACK_KEY in query:
            return pages.DeleteArea(pages.DeleteMode.BACKED_OUT)
        return pages.DeleteArea()

    @staticmethod
    def _pending_status(interaction: pages.MoveInteraction | None) -> HTTPStatus:
        """202 for a page that actually renders a pending confirmation, 200 for every other page.

        The decision reads the resolved view, after outcome precedence, task membership and the
        saved workflow answer, so an address that only asks for a confirmation changes nothing.
        """
        pending = interaction is not None and interaction.mode is pages.MoveInteractionMode.CONFIRM
        # 202, not a page script or a cache-clearing header: the browser's history cache admits only
        # 200 main documents, so a pending move intent, accepted and awaiting the person, is never
        # replayed from history (CP-343).
        return HTTPStatus.ACCEPTED if pending else HTTPStatus.OK

    @staticmethod
    def _stored_as_asked(
        query: Mapping[str, list[str]], *, deleting: bool = False
    ) -> tuple[tuple[str, str], ...]:
        """A page that carries a move's interaction or outcome is never stored (design § 3 A.3),
        nor one showing a deletion's interaction or outcome (`deleting`, design § 3 C)."""
        return (NOT_STORED,) if "move_task" in query or deleting else ()

    def _move_view(
        self, query: Mapping[str, list[str]], on_page: Callable[[int], Task | None]
    ) -> tuple[pages.MoveOutcome, pages.MoveInteraction | None] | None:
        """The one move state an address asks for, read against the saved state, or None when the
        address opens or backs out of a task no task holds (a not-found page).

        A recognized outcome wins, in the order refusal, failure, completion; then opening, then
        backing out. A task that is on another page, an unknown code or a task value that is no
        number changes nothing. Where the workflow no longer offers cancelled, the answer is the
        current-status refusal, in the address context, rather than a button the page would
        fabricate.
        """
        outcome = self._move_outcome(query)
        if outcome.refusal or outcome.failed or outcome.moved:
            return outcome, None
        mode = self._interaction_mode(query)
        digits = _first(query, "move_task")
        if mode is None or not (digits.isascii() and digits.isdigit()):
            return outcome, None
        identity = self._identity(digits)
        if identity is None or self._tracker.task(identity) is None:
            return None
        task = on_page(identity)
        if task is None:
            return outcome, None
        if TaskStatus.CANCELLED not in self._tracker.allowed_moves(task.status):
            refused = pages.MoveOutcome(
                identity,
                refusal=pages.MoveRefusal.NOT_ALLOWED,
                refusal_context=pages.MoveRefusalContext.CANCELLATION_ADDRESS,
            )
            return refused, None
        return outcome, pages.MoveInteraction(identity, mode)

    @staticmethod
    def _interaction_mode(query: Mapping[str, list[str]]) -> pages.MoveInteractionMode | None:
        cancelled = TaskStatus.CANCELLED.value
        if _first(query, "move_confirm") == cancelled:
            return pages.MoveInteractionMode.CONFIRM
        if _first(query, "move_back") == cancelled:
            return pages.MoveInteractionMode.BACK_OUT
        return None

    @staticmethod
    def _move_outcome(query: Mapping[str, list[str]]) -> pages.MoveOutcome:
        """The move outcome from the address: the first recognized of the refusal, failure and
        completion keys, read with the closed vocabularies. Unknown words, and a task identity that
        is no place, give no outcome (the page then shows only a task the outcome is about)."""
        identity = _position(_first(query, "move_task"))
        if identity is None:
            return pages.MoveOutcome()
        refusal = _closed(pages.MoveRefusal, _first(query, "move_refused"))
        if refusal is not None:
            return pages.MoveOutcome(identity, refusal=refusal)
        failed = _closed(TaskStatus, _first(query, "move_failed"))
        if failed is not None:
            return pages.MoveOutcome(identity, failed=failed)
        return pages.MoveOutcome(identity, moved=_closed(TaskStatus, _first(query, "moved")))

    @staticmethod
    def _edit_form(query: Mapping[str, list[str]]) -> pages.TaskEditForm | None:
        """The edit form's retained outcome from the address, or None for any other address.

        A too-long outcome carries no field. Fields beside no recognized outcome are ignored.
        """
        refusal = _closed(pages.TaskEditRefusal, _first(query, "edit_refused"))
        failed = refusal is None and _first(query, "edit_failed") == EDIT_FAILED
        if refusal is None and not failed:
            return None
        if refusal is pages.TaskEditRefusal.TOO_LONG:
            return pages.TaskEditForm(refusal=refusal)
        return pages.TaskEditForm(
            fields=_fields(query),
            shown=_fields(query, SHOWN_PREFIX),
            refusal=refusal,
            failed=failed,
        )

    @staticmethod
    def _label_area(query: Mapping[str, list[str]]) -> pages.LabelArea:
        """The label area's outcome from the address, by the presence of each key (ADR-0006).

        Only a recognized outcome consumes the retained label, and a too-long refusal carries and
        shows none of it, so a label forged beside that code is dropped. Unknown codes are ignored.
        """
        refusal = _closed(pages.LabelRefusal, _first(query, "label_refused"))
        if refusal is pages.LabelRefusal.TOO_LONG:
            return pages.LabelArea(refusal=refusal)
        return pages.LabelArea(
            label=_first(query, "label"),
            refusal=refusal,
            failed=_closed(pages.FailedAction, _first(query, "label_failed")),
            added=_first(query, "label_added") if "label_added" in query else None,
            removed=_first(query, "label_removed") if "label_removed" in query else None,
        )

    @staticmethod
    def _comment_area(query: Mapping[str, list[str]]) -> pages.CommentArea:
        """The comment area's outcome from the address, by the presence of each key (ADR-0006).

        Only a recognized outcome is decoded: an unknown code, a malformed position and a failure
        word other than `add` are ignored. A too-long refusal carries and shows none of the text,
        so a text forged beside that code is dropped.
        """
        refusal = _closed(pages.CommentRefusal, _first(query, "comment_refused"))
        if refusal is pages.CommentRefusal.TOO_LONG:
            return pages.CommentArea(refusal=refusal)
        return pages.CommentArea(
            text=_first(query, "comment_text"),
            refusal=refusal,
            failed=_first(query, "comment_failed") == COMMENT_FAILED,
            added_position=_position(_first(query, "comment_added")),
        )

    def _project_page(self, project: Project, query: Mapping[str, list[str]]) -> Response:
        """Read the add form's outcome from the address and build the page; it changes nothing."""
        listing = self._tracker.project_task_list(
            project.id, _filter_input(query), sort_fields=_sort_input(query)
        )
        deleted_task = _first(query, DELETED_TASK_KEY)
        if deleted_task:
            # The deletion's completion wins over every move marker, even one naming no task.
            move_outcome, move_interaction = pages.MoveOutcome(), None
        else:
            move = self._move_view(query, lambda found: self._project_task(project, found))
            if move is None:
                return Site._html(pages.task_not_found_page(), HTTPStatus.NOT_FOUND)
            move_outcome, move_interaction = move
        shown = {row.task.id for row in listing.rows}
        if move_interaction is not None and move_interaction.task_id not in shown:
            # A confirmation is offered only on a row the page shows.
            move_interaction = None
        return self._html(
            pages.project_page(
                project,
                listing.rows,
                self._tracker.assignees(),
                listing=listing,
                form=self._task_form(query),
                created="created" in query,
                allowed_moves=self._tracker.allowed_moves,
                move_outcome=move_outcome,
                move_interaction=move_interaction,
                off_list_task=self._off_list_task(
                    lambda found: self._project_task(project, found), listing, move_outcome, shown
                ),
                deleted_task=deleted_task or None,
                rename_area=self._rename_area(query),
            ),
            Site._pending_status(move_interaction),
            extra=self._stored_as_asked(query, deleting=bool(deleted_task)),
        )

    def _summary_page(self, digits: str) -> Response:
        """Build a project's Summary from one read of the tracker; no choice in the address matters."""
        identity = self._identity(digits)
        summary = None if identity is None else self._tracker.project_summary(identity)
        if summary is None:
            return self._not_found_page()
        return self._html(pages.summary_page(summary))

    def _all_tasks_page(self, query: Mapping[str, list[str]]) -> Response:
        """Read the choices from the address and build the All tasks page; it changes nothing.

        The read, the move state and the off-list task are the project page's, over every task.
        """
        listing = self._tracker.all_task_list(_filter_input(query), sort_fields=_sort_input(query))
        move = self._move_view(query, self._tracker.task)
        if move is None:
            return Site._html(pages.task_not_found_page(), HTTPStatus.NOT_FOUND)
        move_outcome, move_interaction = move
        shown = {row.task.id for row in listing.rows}
        if move_interaction is not None and move_interaction.task_id not in shown:
            # A confirmation is offered only on a row the page shows.
            move_interaction = None
        return self._html(
            pages.all_tasks_page(
                listing,
                self._tracker.projects(),
                allowed_moves=self._tracker.allowed_moves,
                move_outcome=move_outcome,
                move_interaction=move_interaction,
                off_list_task=self._off_list_task(self._tracker.task, listing, move_outcome, shown),
            ),
            Site._pending_status(move_interaction),
            extra=self._stored_as_asked(query),
        )

    def _project_task(self, project: Project, identity: int) -> Task | None:
        """The task with this identity when it belongs to this project, shown or not."""
        task = self._tracker.task(identity)
        return task if task is not None and task.project_id == project.id else None

    @staticmethod
    def _off_list_task(
        find: Callable[[int], Task | None],
        listing: ProjectTaskList,
        outcome: pages.MoveOutcome,
        shown: set[int],
    ) -> Task | None:
        """The task a move outcome is about when `find` holds it for this list and the list does not
        show it: a project's list finds its own tasks, All tasks finds any.

        Membership is the read model's selected identities; no filter rule is tested here. A refused
        filter has no list, so it has no such task.
        """
        if listing.problems or outcome.task_id is None or outcome.task_id in shown:
            return None
        if outcome.refusal is None and outcome.failed is None and outcome.moved is None:
            return None
        return find(outcome.task_id)

    @staticmethod
    def _task_form(query: Mapping[str, list[str]]) -> pages.TaskForm:
        """The form's outcome and fields from the address. A too-long outcome carries no field,
        and fields beside no outcome are ignored."""
        refusal = _closed(pages.TaskRefusal, _first(query, "task_refused"))
        failed = refusal is None and _first(query, "task_failed") == "add"
        if refusal is pages.TaskRefusal.TOO_LONG or (refusal is None and not failed):
            return pages.TaskForm(refusal=refusal)
        return pages.TaskForm(
            title=_first(query, "title"),
            priority=_first(query, "priority"),
            assignee=_first(query, "assignee"),
            due_date=_first(query, "due_date"),
            refusal=refusal,
            failed=failed,
        )

    @staticmethod
    def _html(
        page: str, status: int = HTTPStatus.OK, *, extra: tuple[tuple[str, str], ...] = ()
    ) -> Response:
        return _respond(status, page.encode("utf-8"), ("Content-Type", HTML_TYPE), *extra)

    @staticmethod
    def _not_found_page() -> Response:
        return Site._html(pages.not_found_page(), HTTPStatus.NOT_FOUND)

    def _projects_page(self, query: Mapping[str, list[str]]) -> str:
        projects = self._tracker.projects()
        refusal = _first(query, "refused")
        if refusal in (pages.BLANK_NAME, pages.NAME_IN_USE):
            return pages.projects_page(
                projects,
                refusal=refusal,
                name=_first(query, "name"),
                description=_first(query, "description"),
            )
        if refusal == pages.TEXT_TOO_LONG:
            fields = {field.value: field for field in TextField}
            field = fields.get(_first(query, "field"))
            return pages.projects_page(projects, refusal=refusal, field=field)
        if not refusal and _first(query, "failed") == "create":
            return pages.projects_page(
                projects,
                failed=True,
                name=_first(query, "name"),
                description=_first(query, "description"),
            )
        return pages.projects_page(projects)

    def _people_page(self, query: Mapping[str, list[str]]) -> str:
        """Read the outcome from the address and build the page; the address changes nothing."""
        return pages.people_page(
            self._tracker.assignees(),
            added=_first(query, "added") or None,
            removed=_first(query, "removed") or None,
            refusal=_closed(pages.AssigneeRefusal, _first(query, "refused")),
            failed=_closed(pages.FailedAction, _first(query, "failed")),
            name=_first(query, "name"),
            operator_name=self._tracker.operator_name(),
            operator_area=self._operator_area(query),
        )

    @staticmethod
    def _operator_area(query: Mapping[str, list[str]]) -> pages.OperatorNameArea:
        """The Your name section's outcome from the address, by the presence of each key.

        Unknown codes are ignored; an empty typed value is kept apart from none. The page decides
        which outcome the typed text belongs to, so a forged value beside a too-long code is
        dropped there.
        """
        return pages.OperatorNameArea(
            typed=_first(query, "operator_typed") if "operator_typed" in query else None,
            refusal=_closed(pages.OperatorNameRefusal, _first(query, "operator_refused")),
            failed=_first(query, "operator_failed") == OPERATOR_NAME_FAILED,
            saved=_first(query, "operator_saved") or None,
        )

    @staticmethod
    def _rename_area(query: Mapping[str, list[str]]) -> pages.ProjectRenameArea:
        """The Rename area's outcome from the address, by the presence of each key.

        Unknown codes are ignored and an empty typed value is kept apart from none. The page
        decides which outcome the typed text belongs to, so a forged value beside a too-long code
        is dropped there.
        """
        return pages.ProjectRenameArea(
            typed=_first(query, "rename_typed") if "rename_typed" in query else None,
            refusal=_closed(pages.ProjectNameRefusal, _first(query, "rename_refused")),
            failed=_first(query, "rename_failed") == RENAME_FAILED,
            saved=_first(query, "rename_saved") or None,
            previous=_first(query, "rename_from") or None,
        )

    def _create(self, form: Mapping[str, list[str]]) -> Response:
        name = _line_feeds(_first(form, "name"))
        description = _line_feeds(_first(form, "description"))

        def create() -> Response:
            try:
                project = self._tracker.create_project(name, description)
            except (BlankName, NameInUse, TextTooLong) as error:
                refusal = _project_refusal(error)
                if refusal.field is not None:
                    return self._redirect(
                        PROJECTS_ADDRESS, refused=refusal.code.value, field=refusal.field.value
                    )
                return self._redirect(
                    PROJECTS_ADDRESS, refused=refusal.code.value, name=name, description=description
                )
            return self._redirect(f"/projects/{project.id}", "created")

        return self._guarded(
            f"The tracker couldn't create '{name}', and nothing was changed.",
            create,
            lambda: self._redirect(
                PROJECTS_ADDRESS, failed="create", name=name, description=description
            ),
        )

    def _rename_project(self, digits: str, form: Mapping[str, list[str]]) -> Response:
        """Rename the project its route names to the typed name and land on its Tasks view.

        The target is fixed by the route. The new name, the refusals and the no-change answer are
        the tracker's: this method reads only what the outcome says. A refusal carries the typed
        text back for a blank or in-use name only; an unexpected failure is reported once, by the
        guarded site, and carries the typed text.
        """
        project = self._project_named_by(digits)
        if project is None:
            return self._not_found_page()
        name = _line_feeds(_first(form, "name"))
        address = f"/projects/{project.id}"

        def rename() -> Response:
            try:
                outcome = self._tracker.rename_project(project.id, name)
            except ProjectNotFound:
                return self._not_found_page()
            except (BlankName, NameInUse, TextTooLong) as error:
                refusal = _project_refusal(error)
                if refusal.field is not None:
                    return self._redirect(address, rename_refused=refusal.code.value)
                return self._redirect(address, rename_refused=refusal.code.value, rename_typed=name)
            if not outcome.changed:
                return self._redirect(address)
            return self._redirect(
                address, rename_saved=outcome.project.name, rename_from=outcome.previous_name
            )

        return self._guarded(
            f"The tracker couldn't rename the project to '{name}', and nothing was changed.",
            rename,
            lambda: self._redirect(address, rename_failed=RENAME_FAILED, rename_typed=name),
        )

    def _add_task(self, digits: str, form: Mapping[str, list[str]]) -> Response:
        project = self._project_named_by(digits)
        if project is None:
            return self._not_found_page()
        fields = {name: _line_feeds(_first(form, name)) for name in TASK_FIELDS}
        project_address = f"/projects/{project.id}"

        def refused(refusal: pages.TaskRefusal, *kept: str) -> Response:
            retained = {name: fields[name] for name in kept}
            return self._redirect(project_address, task_refused=refusal.value, **retained)

        def add() -> Response:
            try:
                task = self._tracker.add_task(project.id, **fields)
            except ProjectNotFound:
                return self._not_found_page()
            except TextTooLong:
                return refused(pages.TaskRefusal.TOO_LONG)
            except BlankTitle:
                return refused(pages.TaskRefusal.BLANK_TITLE, *TASK_FIELDS)
            except InvalidPriority:
                return refused(pages.TaskRefusal.INVALID_PRIORITY, "title", "assignee", "due_date")
            except AssigneeNotListed:
                return refused(pages.TaskRefusal.ASSIGNEE_NOT_LISTED, *TASK_FIELDS)
            except InvalidDueDate:
                return refused(pages.TaskRefusal.INVALID_DUE_DATE, "title", "priority", "assignee")
            return self._redirect(f"/tasks/{task.id}", "added")

        return self._guarded(
            f"The tracker couldn't add '{fields['title']}', and nothing was changed.",
            add,
            lambda: self._redirect(project_address, task_failed="add", **fields),
        )

    def _edit_task(self, digits: str, form: Mapping[str, list[str]]) -> Response:
        identity = self._identity(digits)
        if identity is None:
            return Site._html(pages.task_not_found_page(), HTTPStatus.NOT_FOUND)
        submitted, shown = _fields(form), _fields(form, SHOWN_PREFIX)
        address = f"/tasks/{identity}"
        task = self._tracker.task(identity)
        saved_title = "" if task is None else task.title

        def refused(refusal: pages.TaskEditRefusal, *, retain: bool = True) -> Response:
            carried = _carried(submitted, shown) if retain else {}
            return self._redirect(address, edit_refused=refusal.value, **carried)

        def edit() -> Response:
            try:
                outcome = self._tracker.edit_task(identity, submitted, shown)
            except TaskNotFound:
                return self._redirect(address)
            except TextTooLong:
                return refused(pages.TaskEditRefusal.TOO_LONG, retain=False)
            except BlankTitle:
                return refused(pages.TaskEditRefusal.BLANK_TITLE)
            except InvalidPriority:
                return refused(pages.TaskEditRefusal.INVALID_PRIORITY)
            except AssigneeNotListed:
                return refused(pages.TaskEditRefusal.ASSIGNEE_NOT_LISTED)
            except InvalidDueDate:
                return refused(pages.TaskEditRefusal.INVALID_DUE_DATE)
            return self._redirect(address, "saved") if outcome.changed else self._redirect(address)

        return self._guarded(
            f"The tracker couldn't save changes to '{saved_title}', and nothing was changed.",
            edit,
            lambda: self._redirect(address, edit_failed=EDIT_FAILED, **_carried(submitted, shown)),
        )

    def _add_label(self, digits: str, form: Mapping[str, list[str]]) -> Response:
        identity = self._identity(digits)
        if identity is None:
            return Site._html(pages.task_not_found_page(), HTTPStatus.NOT_FOUND)
        label = _line_feeds(_first(form, "label"))
        address = f"/tasks/{identity}"

        def add() -> Response:
            try:
                outcome = self._tracker.add_task_label(identity, label)
            except TaskNotFound:
                return self._redirect(address)
            except EmptyLabel:
                return self._redirect(
                    address, label_refused=pages.LabelRefusal.EMPTY.value, label=""
                )
            except TextTooLong:
                return self._redirect(address, label_refused=pages.LabelRefusal.TOO_LONG.value)
            return (
                self._redirect(address, label_added=label)
                if outcome.changed
                else self._redirect(address)
            )

        return self._guarded(
            self._label_failure_line("add", label, identity),
            add,
            lambda: self._redirect(address, label_failed=pages.FailedAction.ADD.value, label=label),
        )

    def _remove_label(self, digits: str, form: Mapping[str, list[str]]) -> Response:
        identity = self._identity(digits)
        if identity is None:
            return Site._html(pages.task_not_found_page(), HTTPStatus.NOT_FOUND)
        label = _line_feeds(_first(form, "label"))
        address = f"/tasks/{identity}"

        def remove() -> Response:
            try:
                self._tracker.remove_task_label(identity, label)
            except TaskNotFound:
                return self._redirect(address)
            except LabelNotCarried:
                return self._redirect(
                    address, label_refused=pages.LabelRefusal.NOT_CARRIED.value, label=label
                )
            return self._redirect(address, label_removed=label)

        return self._guarded(
            self._label_failure_line("remove", label, identity),
            remove,
            lambda: self._redirect(
                address, label_failed=pages.FailedAction.REMOVE.value, label=label
            ),
        )

    def _label_failure_line(self, action: str, label: str, identity: int) -> str:
        """The console's first line for a failed label action, naming the task when it is read."""
        task = self._tracker.task(identity)
        preposition = "to" if action == "add" else "from"
        subject = f"the label '{label}'" + (
            f" {preposition} '{task.title}'" if task is not None else ""
        )
        return f"The tracker couldn't {action} {subject}, and nothing was changed."

    def _move_task(
        self, digits: str, form: Mapping[str, list[str]], *, confirming: bool = False
    ) -> Response:
        """Move the task to the status the form names and answer at the place the button was on.

        The status goes to the tracker as sent, whatever it is; the place word only says which of
        three addresses the answer goes to (QC-38): the task's page, its project's list or All
        tasks. An unknown or missing word means the task's page. A refusal is mapped to its code by type. A move
        to cancelled is saved only by the confirming submission, whose target is fixed: the
        ordinary address only opens the confirmation, reading the workflow's answer and saving
        nothing.
        """
        identity = self._identity(digits)
        if identity is None:
            return Site._html(pages.task_not_found_page(), HTTPStatus.NOT_FOUND)
        task_address = f"/tasks/{identity}"
        task = self._tracker.task(identity)
        if task is None:
            return self._redirect(task_address)
        status = TaskStatus.CANCELLED.value if confirming else _first(form, "status")
        destination = _closed(pages.MovePlace, _first(form, "place"))
        on_all_tasks = destination is pages.MovePlace.ALL_TASKS
        on_list = destination is pages.MovePlace.LIST
        if on_all_tasks:
            place = ALL_TASKS_ADDRESS
        elif on_list:
            place = f"/projects/{task.project_id}"
        else:
            place = task_address
        carried = (
            {**_carried_filters(form), **_carried_sorts(form)} if on_list or on_all_tasks else {}
        )
        about: dict[str, str | tuple[str, ...]] = {"move_task": str(identity), **carried}
        if on_all_tasks:
            problems = self._tracker.all_task_list(
                _filter_input(form), sort_fields=_sort_input(form)
            ).problems
        elif on_list:
            problems = self._tracker.project_task_list(
                task.project_id, _filter_input(form), sort_fields=_sort_input(form)
            ).problems
        else:
            problems = ()
        if problems:
            # A malformed filter or sort stops the move before it can save or open a
            # confirmation (CP-405, CP-440, CP-477).
            return self._redirect(place, **about)
        if status == TaskStatus.CANCELLED.value and not confirming:
            if TaskStatus.CANCELLED in self._tracker.allowed_moves(task.status):
                return self._redirect(place, **about, move_confirm=TaskStatus.CANCELLED.value)
            return self._redirect(place, move_refused=pages.MoveRefusal.NOT_ALLOWED.value, **about)

        def move() -> Response:
            try:
                moved = self._tracker.move_task(identity, status)
            except TaskNotFound:
                return self._redirect(task_address)
            except MoveNotAllowed:
                return self._redirect(
                    place, move_refused=pages.MoveRefusal.NOT_ALLOWED.value, **about
                )
            except InvalidTaskStatus:
                return self._redirect(
                    place, move_refused=pages.MoveRefusal.NOT_A_STATUS.value, **about
                )
            return self._redirect(place, moved=moved.status.value, **about)

        return self._guarded(
            f"The tracker couldn't move '{task.title}' to {status}, and nothing was changed.",
            move,
            lambda: self._redirect(place, move_failed=status, **about),
        )

    def _delete_task(self, digits: str, *, confirming: bool = False) -> Response:
        """Open the deletion's confirmation, or delete the task its route names and land on the
        project it belonged to.

        The target is fixed by the route: nothing a form carries chooses it, or the title the
        landing shows, which is the removed task's as the tracker held it when the deletion ran.
        The opening press only reads the task and saves nothing. A task nothing holds is the
        typed missing-task answer; any other failure is reported once, by the guarded site.
        """
        identity = self._identity(digits)
        if identity is None:
            return Site._html(pages.task_not_found_page(), HTTPStatus.NOT_FOUND)
        task_address = f"/tasks/{identity}"
        task = self._tracker.task(identity)
        if task is None:
            return self._redirect(task_address)
        if not confirming:
            return self._redirect(task_address, DELETE_CONFIRM_KEY)

        def delete() -> Response:
            try:
                removed = self._tracker.delete_task(identity)
            except TaskNotFound:
                return self._redirect(task_address)
            return self._redirect(
                f"/projects/{removed.project_id}", **{DELETED_TASK_KEY: removed.title}
            )

        return self._guarded(
            f"The tracker couldn't delete '{task.title}', and nothing was changed.",
            delete,
            lambda: self._redirect(task_address, DELETE_FAILED_KEY),
        )

    def _add_comment(self, digits: str, form: Mapping[str, list[str]]) -> Response:
        """Add the typed text as a comment; the saved name and the instant are the tracker's.

        Only `text` crosses the form: whatever else a request carries is not read. A refusal is
        mapped to its code by type, and the address carries the text back for a blank or unnamed
        one only.
        """
        identity = self._identity(digits)
        if identity is None:
            return Site._html(pages.task_not_found_page(), HTTPStatus.NOT_FOUND)
        text = _line_feeds(_first(form, "text"))
        address = f"/tasks/{identity}"

        def refused(refusal: pages.CommentRefusal) -> Response:
            return self._redirect(address, comment_refused=refusal.value, comment_text=text)

        def add() -> Response:
            try:
                task = self._tracker.add_task_comment(identity, text)
            except TaskNotFound:
                return self._redirect(address)
            except TextTooLong:
                return self._redirect(address, comment_refused=pages.CommentRefusal.TOO_LONG.value)
            except BlankComment:
                return refused(pages.CommentRefusal.BLANK)
            except OperatorNameNotSet:
                return refused(pages.CommentRefusal.NO_NAME)
            return self._redirect(address, comment_added=str(len(task.comments)))

        return self._guarded(
            self._comment_failure_line(identity),
            add,
            lambda: self._redirect(address, comment_failed=COMMENT_FAILED, comment_text=text),
        )

    def _comment_failure_line(self, identity: int) -> str:
        """The console's first line for a failed comment add, naming the task when it is read."""
        task = self._tracker.task(identity)
        subject = "your comment" + (f" to '{task.title}'" if task is not None else "")
        return f"The tracker couldn't add {subject}, and nothing was changed."

    def _add_assignee(self, form: Mapping[str, list[str]]) -> Response:
        name = _line_feeds(_first(form, "name"))

        def add() -> Response:
            try:
                added = self._tracker.add_assignee(name)
            except BlankName:
                return self._redirect(
                    PEOPLE_ADDRESS, refused=pages.AssigneeRefusal.BLANK_NAME.value, name=name
                )
            except AssigneeNameInUse:
                return self._redirect(
                    PEOPLE_ADDRESS,
                    refused=pages.AssigneeRefusal.ASSIGNEE_NAME_IN_USE.value,
                    name=name,
                )
            except TextTooLong:
                return self._redirect(PEOPLE_ADDRESS, refused=pages.AssigneeRefusal.TOO_LONG.value)
            return self._redirect(PEOPLE_ADDRESS, added=added)

        return self._guarded(
            f"The tracker couldn't add '{name}' to the assignees, and nothing was changed.",
            add,
            lambda: self._redirect(PEOPLE_ADDRESS, failed=pages.FailedAction.ADD.value, name=name),
        )

    def _set_operator_name(self, form: Mapping[str, list[str]]) -> Response:
        name = _line_feeds(_first(form, "name"))

        def set_name() -> Response:
            try:
                outcome = self._tracker.set_operator_name(name)
            except BlankName:
                return self._redirect(
                    PEOPLE_ADDRESS,
                    operator_refused=pages.OperatorNameRefusal.BLANK_NAME.value,
                    operator_typed=name,
                )
            except TextTooLong:
                return self._redirect(
                    PEOPLE_ADDRESS, operator_refused=pages.OperatorNameRefusal.TOO_LONG.value
                )
            if not outcome.changed:
                return self._redirect(PEOPLE_ADDRESS)
            return self._redirect(PEOPLE_ADDRESS, operator_saved=outcome.name)

        return self._guarded(
            f"The tracker couldn't set your name to '{name}', and nothing was changed.",
            set_name,
            lambda: self._redirect(
                PEOPLE_ADDRESS, operator_failed=OPERATOR_NAME_FAILED, operator_typed=name
            ),
        )

    def _remove_assignee(self, form: Mapping[str, list[str]]) -> Response:
        name = _line_feeds(_first(form, "name"))

        def remove() -> Response:
            try:
                removed = self._tracker.remove_assignee(name)
            except AssigneeNotFound:
                return self._redirect(
                    PEOPLE_ADDRESS,
                    refused=pages.AssigneeRefusal.ASSIGNEE_NOT_FOUND.value,
                    name=name,
                )
            return self._redirect(PEOPLE_ADDRESS, removed=removed)

        return self._guarded(
            f"The tracker couldn't remove '{name}' from the assignees, and nothing was changed.",
            remove,
            lambda: self._redirect(
                PEOPLE_ADDRESS, failed=pages.FailedAction.REMOVE.value, name=name
            ),
        )

    @staticmethod
    def _guarded(
        message: str, act: Callable[[], Response], failed: Callable[[], Response]
    ) -> Response:
        """Run an action; the one place an unexpected failure is caught and reported (QC-56).

        A refusal is expected and is answered inside `act`, by its type. Anything else leaves the
        state as it was, is reported on the console, and answers with the action's failure page.
        """
        try:
            return act()
        except Exception as error:  # noqa: BLE001 - QC-56's one catch site (QC-62)
            Site._report_failure(message, error)
            return failed()

    @staticmethod
    def _redirect(path: str, *flags: str, **query: str | tuple[str, ...]) -> Response:
        return _respond(HTTPStatus.SEE_OTHER, b"", ("Location", _address(path, *flags, **query)))

    @staticmethod
    def _report_failure(message: str, error: Exception) -> None:
        """The one place an unexpected failure is reported: the action, then the error (OB-3)."""
        kind = type(error).__name__
        text = str(error)
        sys.stderr.write(f"{message}\n")
        sys.stderr.write(f"{kind}: {text}\n" if text else f"{kind}\n")
