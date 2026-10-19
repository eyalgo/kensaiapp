"""Integration tests of the add-comment request through the real Site, Tracker and domain (layer 3).

Checks SRS FR-28 (adding a comment under the saved name at the moment of the add), FR-30 (a rename
leaves earlier authors alone), FR-39 and FR-40 (a refusal changes nothing and gives its reason, and
the comment maximum), NFR-3 (the page read is not what the add uses), NFR-4 (a request from another
site is refused), NFR-8 (a failed save leaves the state as it was), AC-12, AC-18 and AC-20. Change
spec rules CP-249 to CP-261 and CP-268 and NFDR QC-7, QC-8, QC-31, QC-32, QC-49, QC-53, QC-56 and
QC-57 are the ones each test names. The real Site, Tracker and SavedData are used, with an injected
clock that counts its reads and a saver that can be made to fail; no product name is patched. Where
a test checks words, they are the strings of this change's text record.
"""

from __future__ import annotations

import threading
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest
from test_pages import Element, parse, textarea_value
from test_routes import FORM, HOST, POLICY, SAME_ORIGIN, get, header, page
from test_task_routes import MovableClock, SwitchedSaver, World, focused, follow, location

from application import LONG_TEXT_MAX, Comment, Tracker, TrackerState
from domain import empty_state, restore_state, restore_task
from persistence import SavedData
from web import Response, Site, pages

TITLE = "Set up CI"
ADD = "/tasks/1/comments"
CREATED = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
WRITTEN = datetime(2026, 10, 12, 12, 32, tzinfo=UTC)
COMPLETION_LINE = f"You added a comment to '{TITLE}'."
BLANK_REASON = "A comment can't be blank. Type a comment."
NO_NAME_REASON = "A comment needs your name. Set it on the People page, then add the comment."
TOO_LONG_REASON = f"A comment can't be longer than {LONG_TEXT_MAX} characters. Type a shorter one."
FAILURE_LINE = (
    f"The tracker couldn't add your comment to '{TITLE}', and nothing was changed. "
    "What you typed is still in the form. Try again."
)
FAILURE_CONSOLE = f"The tracker couldn't add your comment to '{TITLE}', and nothing was changed."
STATUSES = ("todo", "in-progress", "done", "cancelled")


class ReadCountingClock(MovableClock):
    """The instant it was given, and a count of the reads."""

    def __init__(self, instant: datetime = WRITTEN) -> None:
        super().__init__(instant)
        self.reads = 0

    def now(self) -> datetime:
        self.reads += 1
        return super().now()


def comment(text: str, author: str = "Sam") -> Comment:
    return Comment(text=text, author=author, created_at=CREATED)


def world_with(
    tmp_path: Path,
    *,
    name: str | None = "Sam",
    status: str = "todo",
    comments: tuple[Comment, ...] = (),
) -> World:
    """One project and one task, `Set up CI`, in this status holding these comments, saved to a
    real file first so the bytes on disk can be compared."""
    location_on_disk = tmp_path / "data"
    task = restore_task(1, 1, TITLE, status, "medium", None, [], None, CREATED, list(comments))
    state = restore_state(
        [(1, "Alpha", "")],
        2,
        ("Dana",),
        tasks=[task],
        next_task_id=2,
        operator_name=name,
    )
    inner = SavedData(location_on_disk)
    inner.save(state)
    saver = SwitchedSaver(inner)
    clock = ReadCountingClock()
    tracker = Tracker(state, saver, clock)
    return World(Site(tracker, HOST), tracker, saver, clock, location_on_disk)


def send(
    site: Site,
    target: str,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    **fields: str,
) -> Response:
    sent = urlencode(fields).encode("utf-8") if body is None else body
    return site.handle("POST", target, {**(headers or SAME_ORIGIN), **FORM}, sent)


def add_comment(site: Site, text: str, task: int | str = 1, **extra: str) -> Response:
    return send(site, f"/tasks/{task}/comments", text=text, **extra)


def reads(world: World) -> int:
    assert isinstance(world.clock, ReadCountingClock)
    return world.clock.reads


def untouched(world: World) -> tuple[bytes, int, tuple[Comment, ...]]:
    """What a refused or failed request must leave as it was: the file, the saves and the task's
    comments."""
    task = world.tracker.task(1)
    assert task is not None
    return world.bytes_on_disk(), world.saver.saves, task.comments


def saved_comments(world: World) -> tuple[Comment, ...]:
    state = SavedData(world.location).load()
    assert state is not None
    return state.tasks[0].comments


def refusal_code(response: Response) -> str:
    """The one refusal code the answer's address carries."""
    (code,) = parse_qs(urlsplit(location(response)).query)["comment_refused"]
    return code


def description(element: Element) -> str:
    return " ".join(found.text() for found in element.described_by())


def comment_field(root: Element) -> Element:
    found = root.by_id("comment-text")
    assert found is not None
    return found


def test_comment_post_saves_then_redirects_to_the_added_comment(tmp_path: Path) -> None:
    """CP-249, CP-250, CP-263: the text goes after the earlier comments under the saved name and
    the clock's instant, the answer is a plain 303 to the comment's position, and nothing else in
    the saved data moves."""
    earlier = (comment("first", "Dana"), comment("second", "Lee"))
    world = world_with(tmp_path, comments=earlier)
    before = SavedData(world.location).load()
    assert before is not None
    response = add_comment(world.site, "Looks good")
    assert location(response) == "/tasks/1?comment_added=3"
    assert "#" not in location(response)
    root = parse(follow(world.site, response))
    (target,) = focused(root)
    assert target.attrs["id"] == "comment-3"
    assert description(target) == COMPLETION_LINE
    after = SavedData(world.location).load()
    assert after is not None
    assert after.tasks[0].comments == (*earlier, Comment("Looks good", "Sam", WRITTEN))
    assert replace(after.tasks[0], comments=()) == replace(before.tasks[0], comments=())
    assert replace(after, tasks=()) == replace(before, tasks=())
    assert world.saver.saves == 1 and reads(world) == 1
    assert world.restarted().tracker.task(1) == world.tracker.task(1)


def test_comment_post_reads_the_name_at_submission_time(tmp_path: Path) -> None:
    """CP-251, CP-252: a page read under Sam adds as Lee after a rename, a page read with no name
    adds as Sam once a name is saved, a later rename leaves the earlier authors, and an author,
    an instant or a shown name sent with the form supplies neither."""
    world = world_with(tmp_path, name="Sam")
    stale = page(get(world.site, "/tasks/1"))
    assert "You need a name to comment" not in stale
    world.tracker.set_operator_name("Lee")
    forged = {
        "author": "Forger",
        "created_at": "2000-01-01T00:00:00Z",
        "shown_author": "Sam",
        "shown_name": "Sam",
    }
    assert location(add_comment(world.site, "as Lee", **forged)) == "/tasks/1?comment_added=1"
    world.tracker.set_operator_name("Ari")
    assert location(add_comment(world.site, "as Ari")).endswith("comment_added=2")
    assert saved_comments(world) == (
        Comment("as Lee", "Lee", WRITTEN),
        Comment("as Ari", "Ari", WRITTEN),
    )
    unnamed = world_with(tmp_path / "unnamed", name=None)
    assert "You need a name to comment" in page(get(unnamed.site, "/tasks/1"))
    unnamed.tracker.set_operator_name("Sam")
    assert location(add_comment(unnamed.site, "now named")) == "/tasks/1?comment_added=1"
    assert saved_comments(unnamed) == (Comment("now named", "Sam", WRITTEN),)


@pytest.mark.parametrize("status", STATUSES)
def test_comment_post_accepts_all_task_statuses_and_repeated_text(
    tmp_path: Path, status: str
) -> None:
    """CP-249, CP-253: any status accepts, and identical text adds another comment that has its
    own position."""
    world = world_with(tmp_path, status=status)
    first = add_comment(world.site, "same")
    second = add_comment(world.site, "same")
    assert location(first) == "/tasks/1?comment_added=1"
    assert location(second) == "/tasks/1?comment_added=2"
    assert [item.text for item in saved_comments(world)] == ["same", "same"]
    task = world.tracker.task(1)
    assert task is not None and task.status.value == status
    assert world.saver.saves == 2


@pytest.mark.parametrize(
    ("name", "text", "reason_code", "reason", "retained"),
    [
        (None, "Hi", "no-name", NO_NAME_REASON, "Hi"),
        ("Sam", "", "blank", BLANK_REASON, ""),
        ("Sam", "   \n \t ", "blank", BLANK_REASON, "   \n \t "),
        ("Sam", "\n 　", "blank", BLANK_REASON, "\n 　"),
        ("Sam", "x" * (LONG_TEXT_MAX + 1), "too-long", TOO_LONG_REASON, ""),
    ],
    ids=["no-name", "empty", "whitespace", "unicode-whitespace", "over-long"],
)
def test_comment_post_refuses_each_rule_without_saving(
    tmp_path: Path,
    name: str | None,
    text: str,
    reason_code: str,
    reason: str,
    retained: str,
) -> None:
    """CP-255 to CP-257, CP-268: each rule gives its typed reason, nothing is saved, the file's
    bytes are as they were, a blank or unnamed refusal keeps the text and an over-long one keeps
    none of it."""
    world = world_with(tmp_path, name=name, comments=(comment("earlier"),))
    before = untouched(world)
    response = add_comment(world.site, text)
    expected = {"comment_refused": reason_code}
    if reason_code != "too-long":
        expected["comment_text"] = text
    assert location(response) == f"/tasks/1?{urlencode(expected)}"
    root = parse(follow(world.site, response))
    (target,) = focused(root)
    assert target is comment_field(root)
    assert description(target) == reason
    assert textarea_value(target) == retained
    assert untouched(world) == before
    assert saved_comments(world) == before[2]


@pytest.mark.parametrize(
    ("name", "text", "reason_code"),
    [
        (None, " " * (LONG_TEXT_MAX + 1), "too-long"),
        (None, "", "blank"),
        (None, "\n \n", "blank"),
        ("Sam", " " * (LONG_TEXT_MAX + 1), "too-long"),
    ],
    ids=["4001-spaces-no-name", "empty-no-name", "whitespace-no-name", "4001-spaces-named"],
)
def test_comment_post_uses_length_blank_name_precedence(
    tmp_path: Path, name: str | None, text: str, reason_code: str
) -> None:
    """CP-258, CP-259: exactly one reason, chosen too long then blank then no name, and a missing
    task wins over every text and name."""
    world = world_with(tmp_path, name=name)
    response = add_comment(world.site, text)
    assert refusal_code(response) == reason_code
    root = parse(follow(world.site, response))
    assert len([e for e in root.walk() if e.attrs.get("class") == "reason"]) == 1
    assert refusal_code(send(world.site, ADD, body=b"")) == "blank"
    for absent_text in (text, "valid text", ""):
        answer = add_comment(world.site, absent_text, task=99)
        assert location(answer) == "/tasks/99"
    assert world.saver.saves == 0
    assert saved_comments(world) == ()


@pytest.mark.parametrize(
    "sent",
    [b"a%0D%0Ab", b"a%0Db", b"a%0Ab"],
    ids=["crlf", "lone-cr", "lf"],
)
def test_comment_post_normalizes_line_breaks_before_domain_counting(
    tmp_path: Path, sent: bytes
) -> None:
    """CP-249, CP-254, RT-10: CR LF and a lone CR are saved as LF; a value whose normalized length
    is the maximum saves whole though it was sent longer; the code-point maximum with a character
    outside the Basic Multilingual Plane saves whole, and one more refuses."""
    world = world_with(tmp_path)
    assert location(send(world.site, ADD, body=b"text=" + sent + b"+")).endswith("comment_added=1")
    assert saved_comments(world)[0].text == "a\nb "
    wire = "a\r\n" * 1000 + "b" * 2000
    normalized = "a\n" * 1000 + "b" * 2000
    assert len(wire) > LONG_TEXT_MAX == len(normalized)
    assert location(add_comment(world.site, wire)).endswith("comment_added=2")
    code_points = "x" * (LONG_TEXT_MAX - 1) + "\U0001f600"
    assert len(code_points) == LONG_TEXT_MAX
    assert location(add_comment(world.site, code_points)).endswith("comment_added=3")
    texts = [item.text for item in saved_comments(world)]
    assert texts[1:] == [normalized, code_points]
    over = add_comment(world.site, code_points + "x")
    assert location(over) == "/tasks/1?comment_refused=too-long"
    assert len(saved_comments(world)) == 3


def test_comment_unknown_identity_has_the_existing_not_found_outcome(tmp_path: Path) -> None:
    """CP-259: a task the tracker does not hold lands on that task's address, which answers with
    the task not-found page, and a number too long to read is answered with that page directly;
    nothing is saved."""
    world = world_with(tmp_path)
    before = untouched(world)
    response = add_comment(world.site, "Hi", task=99)
    assert location(response) == "/tasks/99"
    answer = get(world.site, "/tasks/99")
    assert answer.status == 404 and answer.body == pages.task_not_found_page().encode("utf-8")
    huge = add_comment(world.site, "Hi", task="9" * 5000)
    assert huge.status == 404 and huge.body == pages.task_not_found_page().encode("utf-8")
    assert header(huge, "Location") is None
    assert untouched(world) == before


def test_comment_failed_save_keeps_data_and_retains_the_field(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-260, QC-49, QC-56, QC-57: nothing changes, the console names the action then the error,
    and the page says the published failure, keeps the text, focuses Add and shows no Python
    text."""
    world = world_with(tmp_path, comments=(comment("earlier"),))
    before = untouched(world)
    world.saver.failing = True
    capsys.readouterr()
    sent = " keep\nme "
    response = add_comment(world.site, sent)
    assert capsys.readouterr().err.splitlines() == [
        FAILURE_CONSOLE,
        "PermissionError: the disk said no",
    ]
    assert (
        location(response)
        == f"/tasks/1?{urlencode({'comment_failed': 'add', 'comment_text': sent})}"
    )
    landing = follow(world.site, response)
    for leaked in ("PermissionError", "disk said no", "Traceback", "You added a comment"):
        assert leaked not in landing, leaked
    root = parse(landing)
    (target,) = focused(root)
    assert target.attrs["id"] == "add-comment"
    assert description(target) == FAILURE_LINE
    assert textarea_value(comment_field(root)) == sent
    assert untouched(world) == before
    world.saver.failing = False
    assert world.restarted().tracker.task(1) == world.tracker.task(1)
    assert capsys.readouterr().err == ""


def test_comment_failure_before_the_title_is_read_uses_the_short_console_line(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CP-260: a task the tracker cannot read gives the console line that names no task."""

    class Breaking(Tracker):
        def add_task_comment(self, task_id: int, text: str):  # type: ignore[no-untyped-def]
            raise RuntimeError("boom")

    class Quiet:
        def save(self, state: TrackerState) -> None:
            return None

    site = Site(Breaking(empty_state(), Quiet(), MovableClock()), HOST)
    capsys.readouterr()
    response = add_comment(site, "Hi", task=5)
    assert capsys.readouterr().err.splitlines() == [
        "The tracker couldn't add your comment, and nothing was changed.",
        "RuntimeError: boom",
    ]
    assert (
        location(response)
        == f"/tasks/5?{urlencode({'comment_failed': 'add', 'comment_text': 'Hi'})}"
    )


@pytest.mark.parametrize(
    "marks",
    [
        {"Host": HOST, "Sec-Fetch-Site": "cross-site"},
        {"Host": HOST, "Sec-Fetch-Site": "same-site"},
        {"Host": HOST, "Sec-Fetch-Site": "none"},
        {"Host": HOST},
        {"Host": HOST, "Sec-Fetch-Site": "nonsense"},
        {"Host": "evil.example:8017", "Sec-Fetch-Site": "same-origin"},
        {"Host": "127.0.0.1:9999", "Sec-Fetch-Site": "same-origin"},
    ],
    ids=["cross-site", "same-site", "none", "absent", "unknown", "bad-host", "other-port"],
)
def test_comment_post_applies_request_policy_before_the_action(
    tmp_path: Path, marks: dict[str, str]
) -> None:
    """CP-261, QC-7, QC-31, QC-32: the Host and fetch-site checks come first, so no clock is
    read, no action runs and nothing is saved."""
    world = world_with(tmp_path)
    before = untouched(world)
    response = send(world.site, ADD, headers=marks, text="Hi")
    assert response.status == 403 and response.body == b""
    assert untouched(world) == before and reads(world) == 0


def test_comment_post_keeps_response_policy_for_success_refusal_and_failure(
    tmp_path: Path,
) -> None:
    """QC-32, QC-8: a success, a refusal and a failure each answer with the page policy and no
    cookie."""
    world = world_with(tmp_path)
    success = add_comment(world.site, "ok")
    refusal = add_comment(world.site, "")
    world.saver.failing = True
    failure = add_comment(world.site, "ok")
    for response in (success, refusal, failure):
        assert response.status == 303
        assert header(response, "Content-Security-Policy") == POLICY
        assert header(response, "Set-Cookie") is None


@pytest.mark.parametrize(
    "body",
    [b"text=%FF", b"text=\xff\xfe", b"text=ab%C3", b"text=%ED%A0%80"],
    ids=["percent-ff", "raw-bytes", "cut-sequence", "encoded-surrogate"],
)
def test_comment_invalid_utf8_request_changes_nothing(tmp_path: Path, body: bytes) -> None:
    """QC-9: a body that is not UTF-8 gets the existing empty 400, with no replacement text, no
    action and no save."""
    world = world_with(tmp_path)
    before = untouched(world)
    response = send(world.site, ADD, body=body)
    assert response.status == 400 and response.body == b""
    assert header(response, "Location") is None
    assert untouched(world) == before and reads(world) == 0


def test_comment_landing_get_and_history_never_repeat_the_add(tmp_path: Path) -> None:
    """CP-250, QC-8: a landing address read again changes nothing, and an earlier outcome's
    position still addresses the same comment after another add."""
    world = world_with(tmp_path)
    first = add_comment(world.site, "first one")
    address = location(first)
    snapshot = untouched(world)
    for _ in range(3):
        shown = page(get(world.site, address))
        assert "first one" in shown
    assert untouched(world) == snapshot
    add_comment(world.site, "second one")
    (target,) = focused(parse(page(get(world.site, address))))
    assert target.attrs["id"] == "comment-1" and "first one" in target.text()
    assert "second one" not in target.text()
    assert [item.text for item in saved_comments(world)] == ["first one", "second one"]


def test_comment_requests_serialize_through_the_save(tmp_path: Path) -> None:
    """QC-53, RT-6: a second add waits for the first one's save, and both are kept in order."""
    entered, release = threading.Event(), threading.Event()
    states: list[TrackerState] = []

    class HeldSaver:
        holding = False

        def save(self, state: TrackerState) -> None:
            states.append(state)
            if self.holding:
                entered.set()
                assert release.wait(timeout=10)

    saver = HeldSaver()
    task = restore_task(1, 1, TITLE, "todo", "medium", None, [], None, CREATED, [])
    state = restore_state(
        [(1, "Alpha", "")], 2, (), tasks=[task], next_task_id=2, operator_name="Sam"
    )
    held = Site(Tracker(state, saver, ReadCountingClock()), HOST)
    saver.holding = True
    first = threading.Thread(target=add_comment, args=(held, "one"))
    second = threading.Thread(target=add_comment, args=(held, "two"))
    first.start()
    assert entered.wait(timeout=10)
    second.start()
    second.join(timeout=0.5)
    assert second.is_alive(), "the second comment request did not wait for the first save"
    assert len(states) == 1
    release.set()
    first.join(timeout=10)
    second.join(timeout=10)
    assert not first.is_alive() and not second.is_alive()
    assert sorted(item.text for item in states[-1].tasks[0].comments) == ["one", "two"]
    assert len(states[-1].tasks[0].comments) == 2
