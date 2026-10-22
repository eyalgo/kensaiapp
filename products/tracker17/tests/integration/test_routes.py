"""Integration tests of web's request path, run in one process with no socket (layer 3).

Checks SRS FR-2 (only this machine's requests are answered), FR-10 and FR-11 (create and list
projects), FR-16 and FR-23 (the edit and the label actions are more actions every route check
covers), NFR-4 (a request from another site is refused), NFR-8 (a failed save leaves the state as
it was), AC-10, AC-12, AC-18 and AC-20. Change spec rules CP-16, CP-18 to CP-22, CP-25, CP-30 to
CP-38, CP-80, CP-98, CP-169, CP-177, CP-206, CP-223, CP-235 and the cancel-confirmation change's CP-326
and CP-339, and NFDR QC-7, QC-8, QC-31, QC-32, QC-34, QC-35, QC-53, QC-54, QC-56 and QC-57 are the ones each test names. The operator-name
submission (FR-27) is one more action every route check covers. The People requests are checked in
tests/integration/test_people_routes.py.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path
from urllib.parse import urlencode

import pytest
from test_pages import Element, parse

from application import Saver, Tracker, TrackerState
from domain import empty_state
from web import Response, Site, pages
from web.routes import ROUTES

HOST = "127.0.0.1:8017"
SAME_ORIGIN = {"Host": HOST, "Sec-Fetch-Site": "same-origin"}
FORM = {"Content-Type": "application/x-www-form-urlencoded"}
POLICY = "default-src 'self'; script-src 'none'; form-action 'self'; frame-ancestors 'none'"
STYLESHEET = Path(__file__).resolve().parent.parent.parent / "web" / "style.css"


class FixedClock:
    def now(self):
        from datetime import UTC, datetime

        return datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


class RecordingSaver:
    def __init__(self) -> None:
        self.saved: list[TrackerState] = []

    def save(self, state: TrackerState) -> None:
        self.saved.append(state)


class FailingAfterFirstSaver(RecordingSaver):
    """Saves the first state it is handed, then fails every save after it."""

    def __init__(self, error: Exception) -> None:
        super().__init__()
        self.error = error

    def save(self, state: TrackerState) -> None:
        if self.saved:
            raise self.error
        super().save(state)


def make_site(saver: Saver | None = None) -> tuple[Site, Tracker]:
    tracker = Tracker(empty_state(), saver or RecordingSaver(), FixedClock())
    return Site(tracker, HOST), tracker


def header(response: Response, name: str) -> str | None:
    for key, value in response.headers:
        if key.lower() == name.lower():
            return value
    return None


def get(site: Site, target: str, marks: dict[str, str] | None = None) -> Response:
    return site.handle("GET", target, SAME_ORIGIN if marks is None else marks, b"")


def post(site: Site, headers: dict[str, str] | None = None, **fields: str) -> Response:
    body = urlencode(fields).encode("utf-8")
    return site.handle("POST", "/projects", {**(headers or SAME_ORIGIN), **FORM}, body)


def page(response: Response, status: int = 200) -> str:
    """The body of a page answered with exactly this status; only a known pending confirmation
    asks for anything but the default 200 (CP-343, design § 4)."""
    assert response.status == status
    return response.body.decode("utf-8")


def follow(site: Site, response: Response) -> str:
    assert response.status == 303
    return page(get(site, header(response, "Location") or ""))


def restart(saver: RecordingSaver) -> Tracker:
    state = saver.saved[-1] if saver.saved else empty_state()
    return Tracker(state, saver, FixedClock())


def test_a_create_answers_303_to_the_project_page_and_a_reload_changes_nothing() -> None:
    """CP-18."""
    site, tracker = make_site()
    response = post(site, name="Alpha", description="d")
    assert response.status == 303
    assert header(response, "Location") == "/projects/1?created"
    first = page(get(site, "/projects/1?created"))
    second = page(get(site, "/projects/1?created"))
    assert first == second
    assert "You created 'Alpha'." in first
    assert [project.name for project in tracker.projects()] == ["Alpha"]


@pytest.mark.parametrize("duplicate", [False, True], ids=["blank", "in-use"])
def test_a_blank_or_duplicate_name_answers_with_the_page_holding_the_reason_and_both_values(
    duplicate: bool,
) -> None:
    """CP-19, CP-21."""
    saver = RecordingSaver()
    site, _ = make_site(saver)
    if duplicate:
        post(site, name="Alpha", description="first")
    saves_before = len(saver.saved)
    name = "Alpha" if duplicate else " \t "
    response = post(site, name=name, description="kept\ntext")
    assert response.status == 303
    address = header(response, "Location") or ""
    shown = follow(site, response)
    assert 'id="name-reason"' in shown
    assert "autofocus" in shown
    assert f'value="{name}"' in shown
    assert "\nkept\ntext</textarea>" in shown
    assert len(saver.saved) == saves_before
    assert page(get(site, address)) == shown


@pytest.mark.parametrize(
    ("name", "description", "field"),
    [
        ("Alpha", "ç" * 4001, "description"),
        ("ç" * 201, "d", "name"),
        (" ", "ç" * 4001, "description"),
        ("ç" * 201, "ç" * 4001, "name"),
    ],
    ids=["description", "name", "blank-name-long-description", "both"],
)
def test_an_over_long_value_names_the_right_field_and_holds_none_of_the_sent_text(
    name: str, description: str, field: str
) -> None:
    """CP-20, CP-16."""
    saver = RecordingSaver()
    site, _ = make_site(saver)
    response = post(site, name=name, description=description)
    assert response.status == 303
    address = header(response, "Location") or ""
    assert address == f"/?refused=too-long&field={field}"
    shown = follow(site, response)
    other = "description" if field == "name" else "name"
    assert f'id="{field}-reason"' in shown
    assert f'id="{other}-reason"' not in shown
    assert "ç" not in shown and "%C3%A7" not in address
    assert saver.saved == []


@pytest.mark.parametrize("mark", ["cross-site", "same-site", "none", None])
def test_a_submission_not_marked_same_origin_is_refused(mark: str | None) -> None:
    """CP-22, AC-10."""
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    marks = {"Host": HOST} if mark is None else {"Host": HOST, "Sec-Fetch-Site": mark}
    response = post(site, headers=marks, name="Alpha", description="")
    assert response.status == 403
    assert response.body == b""
    assert tracker.projects() == () and saver.saved == []


def test_a_get_is_refused_only_when_marked_from_another_site() -> None:
    """CP-22: a GET marked none opens the page; one marked cross-site is refused."""
    site, _ = make_site()
    assert get(site, "/", {"Host": HOST, "Sec-Fetch-Site": "none"}).status == 200
    assert get(site, "/", {"Host": HOST}).status == 200
    assert get(site, "/", {"Host": HOST, "Sec-Fetch-Site": "cross-site"}).status == 403
    assert get(site, "/", {"Host": HOST, "Sec-Fetch-Site": "same-site"}).status == 403


@pytest.mark.parametrize("host", ["evil.example", "127.0.0.1:9999", "localhost:8017", None])
def test_a_wrong_host_is_refused(host: str | None) -> None:
    """QC-31."""
    site, tracker = make_site()
    marks = {"Sec-Fetch-Site": "same-origin"}
    if host is not None:
        marks["Host"] = host
    assert get(site, "/", marks).status == 403
    assert post(site, headers=marks, name="Alpha", description="").status == 403
    assert tracker.projects() == ()


@pytest.mark.parametrize(
    ("error", "error_line"),
    [
        (PermissionError("the disk said no"), "PermissionError: the disk said no"),
        (OSError(), "OSError"),
    ],
    ids=["with-text", "kind-only"],
)
def test_a_failed_save_names_the_action_and_error_on_stderr_and_shows_the_failure_page(
    error: Exception, error_line: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-25, AC-18, QC-56, QC-57. The restart is built from the last state the saver kept."""
    saver = FailingAfterFirstSaver(error)
    site, tracker = make_site(saver)
    assert post(site, name="Beta", description="kept").status == 303
    capsys.readouterr()
    response = post(site, name=" Alpha ", description="d")
    assert response.status == 303
    captured = capsys.readouterr()
    lines = captured.err.splitlines()
    assert len(lines) == 2
    assert "' Alpha '" in lines[0]
    assert lines[1] == error_line
    assert captured.out == ""
    shown = follow(site, response)
    assert 'id="create-failure"' in shown
    assert 'value=" Alpha "' in shown
    for forbidden in ("Traceback", "PermissionError", "the disk said no", "OSError"):
        assert forbidden not in shown
    assert [project.name for project in tracker.projects()] == ["Beta"]
    assert [project.name for project in restart(saver).projects()] == ["Beta"]


def test_line_breaks_in_a_description_are_saved_as_lf() -> None:
    """RT-10."""
    saver = RecordingSaver()
    site, _ = make_site(saver)
    post(site, name="Alpha", description="a\r\nb\rc\nd")
    assert saver.saved[-1].projects[0].description == "a\nb\nc\nd"


def test_an_undecodable_body_answers_400_with_an_empty_body() -> None:
    saver = RecordingSaver()
    site, _ = make_site(saver)
    response = site.handle(
        "POST", "/projects", {**SAME_ORIGIN, **FORM}, b"name=\xff\xfe&description="
    )
    assert response.status == 400
    assert response.body == b""
    assert saver.saved == []


@pytest.mark.parametrize(
    "body",
    [b"name=%FF&description=", b"name=Alpha&description=%C3", b"name=%ED%A0%80&description="],
    ids=["name-byte-ff", "description-cut-sequence", "encoded-surrogate"],
)
def test_a_percent_encoded_value_that_is_not_utf_8_answers_400_with_an_empty_body(
    body: bytes,
) -> None:
    """Design § 4 (form values, strict UTF-8) and QC-9: no typed value is changed, so a value
    whose bytes are not UTF-8 is not saved with a replacement character in their place."""
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    response = site.handle("POST", "/projects", {**SAME_ORIGIN, **FORM}, body)
    assert response.status == 400
    assert response.body == b""
    assert saver.saved == [] and tracker.projects() == ()


SAMPLE_ADDRESS = {
    "/": "/",
    "/projects/[0-9]+": "/projects/1",
    "/projects": "/projects",
    "/people": "/people",
    "/assignees": "/assignees",
    "/assignees/remove": "/assignees/remove",
    "/operator-name": "/operator-name",
    "/projects/[0-9]+/tasks": "/projects/1/tasks",
    "/tasks/[0-9]+": "/tasks/1",
    "/tasks/[0-9]+/labels": "/tasks/1/labels",
    "/tasks/[0-9]+/labels/remove": "/tasks/1/labels/remove",
    "/tasks/[0-9]+/comments": "/tasks/1/comments",
    "/tasks/[0-9]+/move": "/tasks/1/move",
    "/tasks/[0-9]+/move/confirm": "/tasks/1/move/confirm",
    "/style.css": "/style.css",
}
SUBMITTED_BODY = {
    "/projects": b"name=Beta",
    "/assignees": b"name=Cy",
    "/assignees/remove": b"name=Dana",
    "/operator-name": b"name=Sam",
    "/projects/1/tasks": b"title=Write+it&priority=high&assignee=Dana&due_date=2026-12-01",
    "/tasks/1": b"title=Renamed&shown_title=Seed+task&priority=high&shown_priority=medium",
    "/tasks/1/labels": b"label=bug",
    "/tasks/1/labels/remove": b"label=ui",
    "/tasks/1/comments": b"text=Looks+good",
    "/tasks/1/move": b"status=in-progress&place=list",
    "/tasks/1/move/confirm": b"place=list",
}
AUDIT_OPERATOR_NAME = "Lee"


def test_every_route_leaves_state_and_headers_as_the_rules_say() -> None:
    """QC-7, QC-8, QC-34, CP-80, CP-98, CP-271: the comment submission is one more route, accepted
    and saved once like every other."""
    assert {route.pattern for route in ROUTES} == set(SAMPLE_ADDRESS)
    for route in ROUTES:
        saver = RecordingSaver()
        site, tracker = make_site(saver)
        post(site, name="Alpha", description="seed")
        tracker.add_assignee("Dana")
        tracker.add_task(1, "Seed task", "", "", "")
        tracker.add_task_label(1, "ui")
        # A saved name other than the operator-name sample's, so that sample stays a real change
        # and the comment sample is accepted rather than refused for want of a name.
        tracker.set_operator_name(AUDIT_OPERATOR_NAME)
        before = (
            tracker.projects(),
            tracker.assignees(),
            tracker.project_tasks(1),
            len(saver.saved),
            tracker.operator_name(),
        )
        target = SAMPLE_ADDRESS[route.pattern]
        if route.kind == "submission":
            body = SUBMITTED_BODY[target]
            response = site.handle(route.method, target, {**SAME_ORIGIN, **FORM}, body)
            assert response.status == 303, route
            assert header(response, "Location"), route
            # Design T13: the sample is set up so each submission is accepted and saved once,
            # rather than refused, so the route's redirect is the one its action gives.
            location = header(response, "Location") or ""
            assert "refused=" not in location and "failed=" not in location, (route, location)
            assert len(saver.saved) == before[3] + 1, route
        else:
            response = site.handle(route.method, target, SAME_ORIGIN, b"")
            assert response.status == 200, route
            assert (
                tracker.projects(),
                tracker.assignees(),
                tracker.project_tasks(1),
                len(saver.saved),
                tracker.operator_name(),
            ) == before, route
        assert header(response, "Content-Security-Policy") == POLICY, route
        assert header(response, "Set-Cookie") is None, route


def test_route_audit_accepts_and_saves_the_comment_sample() -> None:
    """QC-7, CP-271: the comment route's sample pattern, address and text are in the audit, and
    with a saved name the sample is accepted and saved once, under that name."""
    pattern = "/tasks/[0-9]+/comments"
    assert ("POST", pattern) in {(route.method, route.pattern) for route in ROUTES}
    target = SAMPLE_ADDRESS[pattern]
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    post(site, name="Alpha", description="seed")
    tracker.add_task(1, "Seed task", "", "", "")
    tracker.set_operator_name(AUDIT_OPERATOR_NAME)
    saves = len(saver.saved)
    response = site.handle("POST", target, {**SAME_ORIGIN, **FORM}, SUBMITTED_BODY[target])
    assert response.status == 303 and header(response, "Location") == "/tasks/1?comment_added=1"
    assert len(saver.saved) == saves + 1
    task = tracker.task(1)
    assert task is not None
    assert [(item.text, item.author) for item in task.comments] == [
        ("Looks good", AUDIT_OPERATOR_NAME)
    ]


def test_a_saver_held_open_makes_a_second_submission_wait() -> None:
    """QC-53, RT-6."""
    entered = threading.Event()
    release = threading.Event()
    states: list[TrackerState] = []

    class HeldSaver:
        def save(self, state: TrackerState) -> None:
            states.append(state)
            if len(states) == 1:
                entered.set()
                assert release.wait(timeout=10)

    site, tracker = make_site(HeldSaver())
    first = threading.Thread(target=post, args=(site,), kwargs={"name": "A", "description": ""})
    second = threading.Thread(target=post, args=(site,), kwargs={"name": "B", "description": ""})
    first.start()
    assert entered.wait(timeout=10)
    second.start()
    second.join(timeout=0.5)
    assert second.is_alive(), "the second submission did not wait for the first"
    assert len(states) == 1
    release.set()
    first.join(timeout=10)
    second.join(timeout=10)
    assert not first.is_alive() and not second.is_alive()
    assert sorted(project.name for project in tracker.projects()) == ["A", "B"]
    assert [project.id for project in states[-1].projects] == [1, 2]


def test_assignee_and_project_requests_serialize_through_the_save() -> None:
    """QC-53, RT-6: another assignee submission and a mixed project request wait for the first."""
    entered = threading.Event()
    release = threading.Event()
    states: list[TrackerState] = []

    class HeldSaver:
        def save(self, state: TrackerState) -> None:
            states.append(state)
            if len(states) == 1:
                entered.set()
                assert release.wait(timeout=10)

    site, tracker = make_site(HeldSaver())

    def assignee(name: str) -> None:
        site.handle(
            "POST", "/assignees", {**SAME_ORIGIN, **FORM}, urlencode({"name": name}).encode()
        )

    first = threading.Thread(target=assignee, args=("Dana",))
    second = threading.Thread(target=assignee, args=("Ari",))
    third = threading.Thread(target=post, args=(site,), kwargs={"name": "Alpha", "description": ""})
    first.start()
    assert entered.wait(timeout=10)
    second.start()
    third.start()
    second.join(timeout=0.5)
    third.join(timeout=0.5)
    assert second.is_alive() and third.is_alive(), "a request did not wait for the first save"
    assert len(states) == 1
    release.set()
    for thread in (first, second, third):
        thread.join(timeout=10)
        assert not thread.is_alive()
    assert sorted(tracker.assignees()) == ["Ari", "Dana"]
    assert [project.name for project in tracker.projects()] == ["Alpha"]
    assert len(states) == 3
    assert set(states[-1].assignees) == {"Dana", "Ari"}
    assert [project.name for project in states[-1].projects] == ["Alpha"]


_connections: list[tuple[int, object]] = []
_window = {"open": False}


def _record(event: str, arguments: tuple[object, ...]) -> None:
    if event == "socket.connect" and _window["open"]:
        _connections.append((threading.get_ident(), arguments))


sys.addaudithook(_record)


def test_no_socket_connection_is_made() -> None:
    """QC-35. The hook cannot be removed, so it records only inside this test's own window."""
    site, _ = make_site()
    _connections.clear()
    _window["open"] = True
    try:
        post(site, name="Alpha", description="d")
        get(site, "/")
        get(site, "/projects/1?created")
        get(site, "/style.css")
        get(site, "/people?added=Dana")
        post(site, name="Alpha", description="d")
        site.handle("POST", "/assignees", {**SAME_ORIGIN, **FORM}, b"name=Dana")
        site.handle("POST", "/assignees/remove", {**SAME_ORIGIN, **FORM}, b"name=Dana")
        get(site, "/people")
        site.handle("POST", "/operator-name", {**SAME_ORIGIN, **FORM}, b"name=Sam")
        get(site, "/people?operator_saved=Sam")
        site.handle("POST", "/projects/1/tasks", {**SAME_ORIGIN, **FORM}, b"title=T")
        get(site, "/tasks/1?added")
        site.handle("POST", "/tasks/1", {**SAME_ORIGIN, **FORM}, b"title=U&shown_title=T")
        get(site, "/tasks/1?saved")
        site.handle("POST", "/tasks/1/labels", {**SAME_ORIGIN, **FORM}, b"label=ui")
        get(site, "/tasks/1?label_added=ui")
        site.handle("POST", "/tasks/1/labels/remove", {**SAME_ORIGIN, **FORM}, b"label=ui")
        get(site, "/tasks/1?label_removed=ui")
        comment = site.handle(
            "POST", "/tasks/1/comments", {**SAME_ORIGIN, **FORM}, b"text=Looks+good"
        )
        get(site, "/tasks/1?comment_added=1")
        get(site, "/tasks/99")
    finally:
        _window["open"] = False
    assert comment.status == 303 and header(comment, "Location") == "/tasks/1?comment_added=1"
    assert _connections == []


NOT_FOUND_TARGETS = [
    "/nowhere",
    "/x/y",
    "/projects",
    "/projects/abc",
    "/projects/0",
    "/projects/99",
    "/projects/99?created",
    "/projects/1/",
    "/nowhere?x=1",
]


def assert_the_not_found_answer(response: Response) -> None:
    assert response.status == 404
    assert (header(response, "Content-Type") or "").startswith("text/html")
    assert header(response, "Content-Security-Policy") == POLICY
    assert response.body == pages.not_found_page().encode("utf-8")


@pytest.mark.parametrize("target", NOT_FOUND_TARGETS)
def test_a_get_with_no_page_gets_the_not_found_page(target: str) -> None:
    """CP-30, CP-31, CP-33, CP-35."""
    site, _ = make_site()
    post(site, name="Alpha", description="d")
    assert_the_not_found_answer(get(site, target))


def test_a_project_identity_too_long_to_read_as_a_number_gets_the_not_found_page() -> None:
    """CP-30, CP-33: an identity no project holds gets the page, however many digits."""
    site, _ = make_site()
    post(site, name="Alpha", description="d")
    response = get(site, "/projects/" + "9" * 5000)
    assert_the_not_found_answer(response)
    assert b"9999" not in response.body


@pytest.mark.parametrize(
    ("method", "target"),
    [
        ("PUT", "/"),
        ("POST", "/style.css"),
        ("DELETE", "/"),
        ("HEAD", "/projects/99"),
        ("PUT", "/projects/99"),
        ("DELETE", "/projects/99"),
    ],
)
def test_a_method_not_in_routes_gets_404_with_an_empty_body(method: str, target: str) -> None:
    """CP-32."""
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    response = site.handle(method, target, {**SAME_ORIGIN, **FORM}, b"name=Alpha")
    assert response.status == 404
    assert response.body == b""
    assert tracker.projects() == () and saver.saved == []


@pytest.mark.parametrize("target", ["/projects/99", "/nowhere"])
def test_a_refused_get_stays_refused(target: str) -> None:
    """CP-32."""
    site, _ = make_site()
    for marks in (
        {**SAME_ORIGIN, "Sec-Fetch-Site": "cross-site"},
        {**SAME_ORIGIN, "Host": "evil.example:8017"},
    ):
        response = get(site, target, marks)
        assert response.status == 403
        assert response.body == b""


def test_requests_answered_with_the_not_found_page_change_nothing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CP-36."""
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    post(site, name="Alpha", description="d")
    saved_before = len(saver.saved)
    projects_before = tracker.projects()
    capsys.readouterr()
    for target in NOT_FOUND_TARGETS:
        assert get(site, target).status == 404
    assert len(saver.saved) == saved_before
    assert tracker.projects() == projects_before
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


@pytest.mark.parametrize(
    "target",
    [
        "/?refused=nonsense",
        "/?refused=too-long&field=bogus",
        "/?refused=too-long",
        "/?failed=other",
    ],
)
def test_an_unknown_refusal_code_in_the_address_shows_the_plain_projects_page(target: str) -> None:
    site, _ = make_site()
    plain = page(get(site, "/"))
    assert page(get(site, target)) == plain
    assert "autofocus" not in plain and 'id="name-reason"' not in plain


def test_a_too_long_refusal_ignores_name_and_description_in_the_address() -> None:
    site, _ = make_site()
    shown = page(get(site, "/?refused=too-long&field=name&name=Leaked&description=Spilled"))
    assert 'id="name-reason"' in shown
    assert "Leaked" not in shown and "Spilled" not in shown


def test_the_stylesheet_is_served() -> None:
    site, _ = make_site()
    response = get(site, "/style.css")
    assert response.status == 200
    assert response.body == STYLESHEET.read_bytes()
    assert (header(response, "Content-Type") or "").startswith("text/css")
    assert header(response, "Content-Security-Policy") == POLICY


def test_a_project_page_answers_with_the_project() -> None:
    """A project that exists is shown, and a reload of the plain address shows no created line."""
    site, _ = make_site()
    post(site, name="Alpha", description="d")
    shown = page(get(site, "/projects/1"))
    assert "Alpha" in shown and "You created" not in shown


def test_every_route_and_action_includes_accepted_edit() -> None:
    """QC-7, QC-8, QC-34, CP-177: an accepted changed-pair edit is one save and a plain 303."""
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    post(site, name="Alpha", description="")
    tracker.add_task(1, "Seed", "", "", "")
    saves = len(saver.saved)
    response = site.handle("POST", "/tasks/1", {**SAME_ORIGIN, **FORM}, SUBMITTED_BODY["/tasks/1"])
    assert response.status == 303 and header(response, "Location") == "/tasks/1?saved"
    assert len(saver.saved) == saves + 1
    assert header(response, "Content-Security-Policy") == POLICY
    assert header(response, "Set-Cookie") is None
    assert ("POST", "/tasks/[0-9]+") in {(route.method, route.pattern) for route in ROUTES}


def test_task_edits_wait_for_held_save() -> None:
    """QC-53, RT-6: a second edit cannot save until the first is released, and sees its result."""
    entered = threading.Event()
    release = threading.Event()
    states: list[TrackerState] = []

    class HeldSaver:
        def save(self, state: TrackerState) -> None:
            states.append(state)
            if len(states) == 3:
                entered.set()
                assert release.wait(timeout=10)

    site, tracker = make_site(HeldSaver())
    post(site, name="Alpha", description="")
    tracker.add_task(1, "Seed", "", "", "")

    def edit(fields: bytes) -> None:
        site.handle("POST", "/tasks/1", {**SAME_ORIGIN, **FORM}, fields)

    first = threading.Thread(target=edit, args=(b"title=First&shown_title=Seed",))
    second = threading.Thread(target=edit, args=(b"priority=low&shown_priority=medium",))
    first.start()
    assert entered.wait(timeout=10)
    second.start()
    second.join(timeout=0.5)
    assert second.is_alive(), "the second edit did not wait for the first"
    assert len(states) == 3
    release.set()
    first.join(timeout=10)
    second.join(timeout=10)
    assert not first.is_alive() and not second.is_alive()
    task = tracker.task(1)
    assert task is not None and (task.title, task.priority.value) == ("First", "low")
    assert len(states) == 4
    assert [task.title for task in states[-1].tasks] == ["First"]


def test_an_edit_hands_a_recording_saver_only_saves() -> None:
    """QC-54, CP-177: edits and the pages that follow them give the saver whole states and no read."""

    class OnlySaves(RecordingSaver):
        def __getattr__(self, name: str) -> object:
            raise AssertionError(f"the saver was asked for {name}, and it is only handed saves")

    saver = OnlySaves()
    site, tracker = make_site(saver)
    post(site, name="Alpha", description="")
    tracker.add_task(1, "Seed", "", "", "")
    saves = len(saver.saved)
    sequence = [
        b"title=One&shown_title=Seed",
        b"title=One&shown_title=One",
        b"priority=low&shown_priority=medium",
        b"title=&shown_title=One",
    ]
    for body in sequence:
        site.handle("POST", "/tasks/1", {**SAME_ORIGIN, **FORM}, body)
        get(site, "/tasks/1?saved")
    assert len(saver.saved) == saves + 2
    assert [task.title for task in saver.saved[-1].tasks] == ["One"]


def test_label_actions_hand_recording_saver_only_saves() -> None:
    """QC-54, CP-206: label actions and the pages that follow them give the saver whole states and
    no read."""

    class OnlySaves(RecordingSaver):
        def __getattr__(self, name: str) -> object:
            raise AssertionError(f"the saver was asked for {name}, and it is only handed saves")

    saver = OnlySaves()
    site, tracker = make_site(saver)
    post(site, name="Alpha", description="")
    tracker.add_task(1, "Seed", "", "", "")
    saves = len(saver.saved)
    sequence = [
        ("/tasks/1/labels", b"label=ui"),
        ("/tasks/1/labels", b"label=ui"),
        ("/tasks/1/labels", b"label=bug"),
        ("/tasks/1/labels/remove", b"label=ui"),
        ("/tasks/1/labels/remove", b"label=ui"),
        ("/tasks/1/labels", b""),
    ]
    for target, body in sequence:
        site.handle("POST", target, {**SAME_ORIGIN, **FORM}, body)
        get(site, "/tasks/1?label_added=bug")
        get(site, "/projects/1")
    assert len(saver.saved) == saves + 3
    assert [task.labels for task in saver.saved[-1].tasks] == [("bug",)]


def _name_post(site: Site, headers: dict[str, str], name: str = "Sam") -> Response:
    body = urlencode({"name": name}).encode("utf-8")
    return site.handle("POST", "/operator-name", {**headers, **FORM}, body)


@pytest.mark.parametrize("mark", ["cross-site", "same-site", "none", "", None])
def test_operator_name_submission_origin_checks_run_before_action(mark: str | None) -> None:
    """CP-223, QC-32: a wrong or missing mark, or Host, gets the existing refusal and changes no
    state and no file; the same-origin mark succeeds."""
    saver = RecordingSaver()
    site, tracker = make_site(saver)
    tracker.set_operator_name("Sam")
    saves = len(saver.saved)
    marks = {"Host": HOST} if mark is None else {"Host": HOST, "Sec-Fetch-Site": mark}
    refused = _name_post(site, marks, "Lee")
    assert refused.status == 403 and refused.body == b""
    for wrong_host in ("evil.example", "127.0.0.1:9999"):
        marks = {"Host": wrong_host, "Sec-Fetch-Site": "same-origin"}
        assert _name_post(site, marks, "Lee").status == 403
    assert tracker.operator_name() == "Sam" and len(saver.saved) == saves
    accepted = _name_post(site, SAME_ORIGIN, "Lee")
    assert accepted.status == 303 and tracker.operator_name() == "Lee"
    assert len(saver.saved) == saves + 1


def test_operator_name_route_hands_recording_saver_only_saves() -> None:
    """QC-54: a name action reaches the handed saver only as saves of whole states, and nothing
    but the state crosses application: no load, no request detail, no format knowledge."""
    calls: list[tuple[str, tuple[object, ...]]] = []

    class RecordingEverything:
        def save(self, *arguments: object) -> None:
            calls.append(("save", arguments))

        def __getattr__(self, name: str) -> object:
            calls.append((name, ()))
            raise AssertionError(f"the saver was asked for {name}")

    site, tracker = make_site(RecordingEverything())  # type: ignore[arg-type]
    assert _name_post(site, SAME_ORIGIN, "Sam").status == 303
    assert _name_post(site, SAME_ORIGIN, "Sam").status == 303
    assert _name_post(site, SAME_ORIGIN, "").status == 303
    assert _name_post(site, SAME_ORIGIN, "Lee").status == 303
    assert [name for name, _ in calls] == ["save", "save"]
    assert all(len(arguments) == 1 for _, arguments in calls)
    assert all(isinstance(arguments[0], TrackerState) for _, arguments in calls)
    assert tracker.operator_name() == "Lee"


def test_recording_saver_comment_route_never_loads() -> None:
    """QC-54, CP-271: one successful comment submission reaches the saver only as a save of a
    whole state, and nothing is asked of it that reads saved data."""
    calls: list[tuple[str, tuple[object, ...]]] = []

    class RecordingEverything:
        def save(self, *arguments: object) -> None:
            calls.append(("save", arguments))

        def __getattr__(self, name: str) -> object:
            calls.append((name, ()))
            raise AssertionError(f"the saver was asked for {name}")

    site, tracker = make_site(RecordingEverything())  # type: ignore[arg-type]
    tracker.create_project("Alpha", "")
    tracker.add_task(1, "Seed", "", "", "")
    tracker.set_operator_name("Sam")
    calls.clear()
    response = site.handle("POST", "/tasks/1/comments", {**SAME_ORIGIN, **FORM}, b"text=Hi")
    assert response.status == 303 and header(response, "Location") == "/tasks/1?comment_added=1"
    get(site, "/tasks/1?comment_added=1")
    assert [name for name, _ in calls] == ["save"]
    assert all(isinstance(arguments[0], TrackerState) for _, arguments in calls)


# --- The confirming move route and the pages' cache headers (cancel-confirmation, CP-339) -------

CONFIRMING = "/tasks/1/move/confirm"


class SwitchedRecordingSaver(RecordingSaver):
    """Records every state it is handed, or raises while switched to fail."""

    def __init__(self) -> None:
        super().__init__()
        self.failing = False

    def save(self, state: TrackerState) -> None:
        if self.failing:
            raise PermissionError("the disk said no")
        super().save(state)


def site_with_one_task(saver: Saver | None = None) -> tuple[Site, Tracker, RecordingSaver]:
    recording = saver or RecordingSaver()
    site, tracker = make_site(recording)
    post(site, name="Alpha", description="seed")
    tracker.add_task(1, "Seed task", "", "", "")
    assert isinstance(recording, RecordingSaver)
    return site, tracker, recording


def confirming(site: Site, headers: dict[str, str], body: bytes = b"place=list") -> Response:
    return site.handle("POST", CONFIRMING, {**headers, **FORM}, body)


def test_the_confirming_address_is_not_read_by_a_get_and_leaves_the_state_alone() -> None:
    """CP-339: a GET to the confirming address is the empty 404 and changes nothing."""
    site, tracker, saver = site_with_one_task()
    before = (tracker.project_tasks(1), len(saver.saved))
    response = get(site, CONFIRMING)
    assert response.status == 404 and response.body == pages.not_found_page().encode("utf-8")
    assert (tracker.project_tasks(1), len(saver.saved)) == before
    other = site.handle("PUT", CONFIRMING, {**SAME_ORIGIN, **FORM}, b"place=list")
    assert other.status == 404 and other.body == b"" and len(saver.saved) == before[1]


@pytest.mark.parametrize(
    "marks",
    [
        {"Host": "evil.example:8017", "Sec-Fetch-Site": "same-origin"},
        {"Host": HOST, "Sec-Fetch-Site": "cross-site"},
        {"Host": HOST, "Sec-Fetch-Site": "same-site"},
        {"Host": HOST, "Sec-Fetch-Site": "none"},
        {"Host": HOST},
    ],
    ids=["wrong-host", "cross-site", "same-site", "none", "unmarked"],
)
def test_confirming_route_checks_origin_before_applying_the_move(marks: dict[str, str]) -> None:
    """CP-339, QC-32: only a same-origin confirming submission is applied; each other mark is
    refused with the saved data, state and save count as they were; same-origin is accepted, and
    no response carries a cookie, or a script or meta policy."""
    site, tracker, saver = site_with_one_task()
    before = (tracker.project_tasks(1), len(saver.saved))
    refused = confirming(site, marks)
    assert refused.status == 403 and (tracker.project_tasks(1), len(saver.saved)) == before
    assert header(refused, "Content-Security-Policy") == POLICY
    assert header(refused, "Set-Cookie") is None
    accepted = confirming(site, SAME_ORIGIN)
    assert accepted.status == 303 and len(saver.saved) == before[1] + 1
    assert header(accepted, "Content-Security-Policy") == POLICY
    assert header(accepted, "Set-Cookie") is None
    shown = get(site, header(accepted, "Location") or "").body.decode("utf-8")
    assert "<script" not in shown and "<meta" not in shown.replace('<meta charset="utf-8">', "")


CONFIRMATION = "move_task=1&move_confirm=cancelled"
MOVE_ADDRESSES = ("/projects/1", "/tasks/1")


STATUS_PATH = {
    "todo": [],
    "in-progress": ["in-progress"],
    "done": ["in-progress", "done"],
    "cancelled": ["cancelled"],
}


def site_with_two_tasks(status: str = "todo") -> tuple[Site, Tracker, RecordingSaver]:
    """One project, the task the strip opens on in the given status, and a second task beside it."""
    site, tracker, saver = site_with_one_task()
    tracker.add_task(1, "Other task", "", "", "")
    for step in STATUS_PATH[status]:
        tracker.move_task(1, step)
    return site, tracker, saver


def classes(element: Element) -> list[str]:
    return (element.attrs.get("class") or "").split()


def strips_of(root: Element) -> list[Element]:
    return [e for e in root.walk() if "confirm-strip" in classes(e)]


def focus_owners(root: Element) -> list[Element]:
    return [e for e in root.walk() if "autofocus" in e.attrs]


@pytest.mark.parametrize("status", ["todo", "in-progress"])
@pytest.mark.parametrize("address", MOVE_ADDRESSES)
def test_pending_confirmation_response_matches_the_rendered_page(address: str, status: str) -> None:
    """CP-343, CP-345: a GET showing one pending confirmation, from either allowed starting status
    and on both pages, is answered with exactly 202; the sentence alone owns focus, the other row
    keeps its ordinary controls, and the read changes neither the bytes, the state nor the saves."""
    site, tracker, saver = site_with_two_tasks(status)
    before = (tracker.project_tasks(1), len(saver.saved))
    response = get(site, f"{address}?{CONFIRMATION}")
    assert response.status == 202
    assert header(response, "Cache-Control") == "no-store"
    assert header(response, "Content-Security-Policy") == POLICY
    assert header(response, "Set-Cookie") is None
    root = parse(response.body.decode("utf-8"))
    (strip,) = strips_of(root)
    (owner,) = focus_owners(root)
    assert owner.attrs["id"] == "confirm-sentence" and owner.parent is strip
    if address == "/projects/1":
        buttons = [
            b.attrs["aria-label"] for b in root.find_all("button") if "aria-label" in b.attrs
        ]
        assert "Move 'Other task' to cancelled" in buttons
        assert "Move 'Seed task' to cancelled" not in buttons
    assert (tracker.project_tasks(1), len(saver.saved)) == before


@pytest.mark.parametrize(
    ("address", "status", "expected"),
    [
        ("/projects/1?move_task=1&move_back=cancelled", "todo", 200),
        ("/tasks/1?move_task=1&move_back=cancelled", "todo", 200),
        ("/projects/1?move_task=1&move_confirm=cancelled", "done", 200),
        ("/tasks/1?move_task=1&move_confirm=cancelled", "done", 200),
        ("/projects/1?move_task=1&move_confirm=cancelled", "cancelled", 200),
        ("/tasks/1?move_task=1&move_confirm=cancelled", "cancelled", 200),
        ("/tasks/1?move_task=1&move_refused=not-allowed&move_confirm=cancelled", "todo", 200),
        ("/projects/1?move_task=1&move_failed=cancelled&move_confirm=cancelled", "todo", 200),
        ("/tasks/1?move_task=1&moved=in-progress&move_confirm=cancelled", "todo", 200),
        ("/tasks/1?move_task=1&move_confirm=bogus", "todo", 200),
        ("/projects/1?move_task=1&move_confirm=", "todo", 200),
        ("/tasks/1?move_confirm=cancelled", "todo", 200),
        ("/projects/1?move_task=x&move_confirm=cancelled", "todo", 200),
        ("/projects/1?move_task=1&move_confirm=bogus&move_confirm=cancelled", "todo", 200),
        ("/projects/1?move_task=1&move_confirm=cancelled&move_confirm=bogus", "todo", 202),
        ("/tasks/1?move_task=1&move_back=cancelled&move_confirm=cancelled", "todo", 202),
        ("/tasks/1?move_task=2&move_confirm=cancelled", "todo", 200),
        ("/projects/1?move_task=3&move_confirm=cancelled", "todo", 200),
        ("/tasks/1?move_task=999&move_confirm=cancelled", "todo", 404),
        ("/projects/1?move_task=999&move_confirm=cancelled", "todo", 404),
    ],
)
def test_non_confirmation_move_views_keep_their_response_contract(
    address: str, status: str, expected: int
) -> None:
    """CP-343, CP-345: 202 goes only to a confirmation this page actually renders. Back-out, a
    saved status that refuses the move, a recognized outcome that wins, an unknown or empty value, a
    missing or malformed identity, a task from another project and a different task on a task page
    keep the existing 200 or 404; repeated values keep their first-value precedence."""
    site, tracker, saver = site_with_two_tasks(status)
    post(site, name="Beta", description="elsewhere")
    tracker.add_task(2, "Foreign task", "", "", "")
    foreign = tracker.project_tasks(2)[0].task.id
    assert foreign == 3
    before = (tracker.project_tasks(1), len(saver.saved))
    response = get(site, address)
    assert response.status == expected
    if expected == 202:
        assert len(strips_of(parse(response.body.decode("utf-8")))) == 1
    elif expected == 200:
        shown = parse(response.body.decode("utf-8"))
        assert strips_of(shown) == []
        assert len(focus_owners(shown)) <= 1
    else:
        assert response.body == pages.task_not_found_page().encode("utf-8")
    assert (tracker.project_tasks(1), len(saver.saved)) == before


NOT_STORED_ADDRESSES = [
    ("/projects/1?move_task=1&move_confirm=cancelled", 202),
    ("/tasks/1?move_task=1&move_confirm=cancelled", 202),
    ("/projects/1?move_task=1&move_back=cancelled", 200),
    ("/tasks/1?move_task=1&move_back=cancelled", 200),
    ("/projects/1?moved=cancelled&move_task=1", 200),
    ("/tasks/1?move_refused=not-allowed&move_task=1", 200),
    ("/tasks/1?move_failed=cancelled&move_task=1", 200),
]


@pytest.mark.parametrize(("address", "expected"), NOT_STORED_ADDRESSES)
def test_move_interaction_and_outcome_pages_are_not_stored(address: str, expected: int) -> None:
    """Design § 3 A.3, CP-326, CP-343: a page carrying the interaction or its outcome says
    no-store with the status the rendered page earns, and keeps the page policy and no cookie; the
    same pages without the interaction query are the unchanged control, with no no-store."""
    site, _, _ = site_with_one_task()
    response = get(site, address)
    assert response.status == expected
    assert header(response, "Cache-Control") == "no-store"
    assert header(response, "Content-Security-Policy") == POLICY
    assert header(response, "Set-Cookie") is None
    plain = get(site, address.split("?")[0])
    assert plain.status == 200 and header(plain, "Cache-Control") is None


def test_move_responses_do_not_clear_site_data() -> None:
    """CP-346: no move response clears site data, cookies or caches: not an ordinary or a
    confirming success, a first press, a refused move, an invalid status, a missing task, a failed
    save on either submission path, a GET, a back-out or a rejected origin. Redirects keep their
    Locations and outcomes; every path that saves nothing leaves the bytes, state and saves as
    they were."""
    for body, path in (
        (b"status=in-progress&place=list", "/tasks/1/move"),
        (b"place=list", CONFIRMING),
    ):
        site, tracker, saver = site_with_one_task()
        saves = len(saver.saved)
        done = site.handle("POST", path, {**SAME_ORIGIN, **FORM}, body)
        assert done.status == 303 and len(saver.saved) == saves + 1
        assert header(done, "Location") == (
            f"/projects/1?moved={tracker.task(1).status.value}&move_task=1"
        )
        assert header(done, "Clear-Site-Data") is None and header(done, "Set-Cookie") is None
    site, tracker, saver = site_with_one_task()
    saves = len(saver.saved)
    form = {**SAME_ORIGIN, **FORM}
    quiet = [
        site.handle("POST", "/tasks/1/move", form, b"status=cancelled&place=list"),
        site.handle("POST", "/tasks/1/move", form, b"status=bogus&place=list"),
        site.handle("POST", "/tasks/9/move", form, b"status=done&place=list"),
        site.handle("POST", "/tasks/9/move/confirm", form, b"place=list"),
        site.handle(
            "POST", "/tasks/1/move", {**form, "Sec-Fetch-Site": "same-site"}, b"status=done"
        ),
        site.handle("POST", CONFIRMING, {**form, "Sec-Fetch-Site": "cross-site"}, b"place=list"),
        get(site, "/tasks/1?move_task=1&move_confirm=cancelled"),
        get(site, "/tasks/1?move_task=1&move_back=cancelled"),
    ]
    assert [r.status for r in quiet] == [303, 303, 303, 303, 403, 403, 202, 200]
    assert header(quiet[0], "Location") == "/projects/1?move_task=1&move_confirm=cancelled"
    assert len(saver.saved) == saves and tracker.task(1).status.value == "todo"
    tracker.move_task(1, "cancelled")
    saves = len(saver.saved)
    after = [
        site.handle("POST", "/tasks/1/move", form, b"status=cancelled"),
        confirming(site, SAME_ORIGIN),
    ]
    assert len(saver.saved) == saves
    switched = SwitchedRecordingSaver()
    failing, _, _ = site_with_one_task(switched)
    switched.failing = True
    broken = [
        failing.handle("POST", "/tasks/1/move", form, b"status=in-progress"),
        failing.handle("POST", "/tasks/1/move/confirm", form, b"place=list"),
    ]
    for response in (*quiet, *after, *broken):
        assert header(response, "Clear-Site-Data") is None, response
        assert header(response, "Set-Cookie") is None, response
    assert [r.status for r in (*after, *broken)] == [303, 303, 303, 303]
    assert all(
        "move_failed=" in (header(r, "Location") or "")
        or "move_refused=" in (header(r, "Location") or "")
        for r in (*after, *broken)
    )


@pytest.mark.parametrize("address", [f"{base}?{CONFIRMATION}" for base in MOVE_ADDRESSES])
def test_move_pages_contain_no_executable_script(address: str) -> None:
    """CP-345, QC-34: the pending confirmation and the refusal that replaces it carry no script
    element, no event-handler attribute and no script URL, and each answers with the exact page
    policy that refuses script and framing."""
    site, tracker, _ = site_with_one_task()
    for status in (None, "cancelled"):
        if status is not None:
            tracker.move_task(1, status)
        response = get(site, address)
        assert response.status == (202 if status is None else 200)
        assert header(response, "Content-Security-Policy") == POLICY
        assert "script-src 'none'" in POLICY and "frame-ancestors 'none'" in POLICY
        for element in parse(response.body.decode("utf-8")).walk():
            assert element.tag != "script"
            for name, value in element.attrs.items():
                assert not name.lower().startswith("on"), (element.tag, name)
                assert "javascript:" not in (value or "").lower(), (element.tag, name)
