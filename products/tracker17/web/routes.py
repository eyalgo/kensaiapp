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
    InvalidDueDate,
    InvalidPriority,
    LabelNotCarried,
    NameInUse,
    OperatorNameNotSet,
    Project,
    ProjectNotFound,
    TaskFields,
    TaskNotFound,
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
PROJECT_PATTERN = re.compile(r"/projects/([0-9]+)")
TASK_PATTERN = re.compile(r"/tasks/([0-9]+)")
ADD_TASK_PATTERN = re.compile(r"/projects/([0-9]+)/tasks")
ADD_LABEL_PATTERN = re.compile(r"/tasks/([0-9]+)/labels")
REMOVE_LABEL_PATTERN = re.compile(r"/tasks/([0-9]+)/labels/remove")
ADD_COMMENT_PATTERN = re.compile(r"/tasks/([0-9]+)/comments")
SHOWN_PREFIX = "shown_"
TASK_FIELDS = ("title", "priority", "assignee", "due_date")
EDIT_FAILED = "save"
OPERATOR_NAME_FAILED = "save"
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


ROUTES = (
    Route("GET", "/", PAGE),
    Route("GET", "/projects/[0-9]+", PAGE),
    Route("POST", "/projects", SUBMISSION),
    Route("GET", "/people", PAGE),
    Route("POST", "/assignees", SUBMISSION),
    Route("POST", "/assignees/remove", SUBMISSION),
    Route("POST", "/operator-name", SUBMISSION),
    Route("POST", "/projects/[0-9]+/tasks", SUBMISSION),
    Route("GET", "/tasks/[0-9]+", PAGE),
    Route("POST", "/tasks/[0-9]+", SUBMISSION),
    Route("POST", "/tasks/[0-9]+/labels", SUBMISSION),
    Route("POST", "/tasks/[0-9]+/labels/remove", SUBMISSION),
    Route("POST", "/tasks/[0-9]+/comments", SUBMISSION),
    Route("GET", "/style.css", PAGE),
)


def _respond(status: int, body: bytes = b"", *extra: tuple[str, str]) -> Response:
    return Response(status, (*extra, ("Content-Security-Policy", PAGE_POLICY)), body)


def _address(path: str, *flags: str, **query: str) -> str:
    """The one place an address is built, for every redirect a submission answers with (RT-8).

    A flag is a bare word in the query (`?created`); a value is a `key=value` pair.
    """
    parts = [*flags, urlencode(query)] if query else list(flags)
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
        task_match = TASK_PATTERN.fullmatch(path)
        if task_match:
            return self._task_page(task_match.group(1), query)
        match = PROJECT_PATTERN.fullmatch(path)
        project = self._project_named_by(match.group(1)) if match else None
        if project is None:
            return self._not_found_page()
        return self._html(self._project_page(project, query))

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
        return self._html(
            pages.task_page(
                context,
                form=self._edit_form(query),
                added="added" in query,
                saved="saved" in query,
                label_area=self._label_area(query),
                comment_area=self._comment_area(query),
                operator_name=self._tracker.operator_name(),
            )
        )

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

    def _project_page(self, project: Project, query: Mapping[str, list[str]]) -> str:
        """Read the add form's outcome from the address and build the page; it changes nothing."""
        return pages.project_page(
            project,
            self._tracker.project_tasks(project.id),
            self._tracker.assignees(),
            form=self._task_form(query),
            created="created" in query,
        )

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
    def _html(page: str, status: int = HTTPStatus.OK) -> Response:
        return _respond(status, page.encode("utf-8"), ("Content-Type", HTML_TYPE))

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

    def _create(self, form: Mapping[str, list[str]]) -> Response:
        name = _line_feeds(_first(form, "name"))
        description = _line_feeds(_first(form, "description"))

        def create() -> Response:
            try:
                project = self._tracker.create_project(name, description)
            except BlankName:
                return self._redirect(
                    PROJECTS_ADDRESS, refused=pages.BLANK_NAME, name=name, description=description
                )
            except NameInUse:
                return self._redirect(
                    PROJECTS_ADDRESS, refused=pages.NAME_IN_USE, name=name, description=description
                )
            except TextTooLong as refusal:
                return self._redirect(
                    PROJECTS_ADDRESS, refused=pages.TEXT_TOO_LONG, field=refusal.field.value
                )
            return self._redirect(f"/projects/{project.id}", "created")

        return self._guarded(
            f"The tracker couldn't create '{name}', and nothing was changed.",
            create,
            lambda: self._redirect(
                PROJECTS_ADDRESS, failed="create", name=name, description=description
            ),
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
    def _redirect(path: str, *flags: str, **query: str) -> Response:
        return _respond(HTTPStatus.SEE_OTHER, b"", ("Location", _address(path, *flags, **query)))

    @staticmethod
    def _report_failure(message: str, error: Exception) -> None:
        """The one place an unexpected failure is reported: the action, then the error (OB-3)."""
        kind = type(error).__name__
        text = str(error)
        sys.stderr.write(f"{message}\n")
        sys.stderr.write(f"{kind}: {text}\n" if text else f"{kind}\n")
