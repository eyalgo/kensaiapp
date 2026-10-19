"""Integration tests of the timed harness at task volume (layer 3).

Checks SRS NFR-1 (an action stays fast with 1,000 tasks of 20 comments each, editing a task's fields
included, a label added or removed too, the operator's name saved, a comment added, and a name added
to or removed from the assignee list) and AC-15 (the response time). Change spec rules CP-143 (the
add), CP-179 (the edit), CP-208 (the label add and remove), CP-237 (the name save) and CP-276 to
CP-289 (the comment add and the assignee add and remove) and NFDR QC-48 are the ones each test
names. The harness is tests/timed_run.py; it is loaded by its path and handed its own
collaborators (a request site, a timer, a location), so no product name is patched. A script that
only exits 0 could time the wrong path, so these tests prove it exercises the real one and refuses
a wrong one.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import re
import sys
from collections.abc import Callable, Iterator
from dataclasses import replace
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from types import ModuleType
from urllib.parse import parse_qs, urlencode

import pytest

from application import Tracker
from domain import Comment, Priority, find_task
from persistence import SavedData
from web import Response, Site

TESTS_DIRECTORY = Path(__file__).resolve().parent.parent
PRODUCT_ROOT = TESTS_DIRECTORY.parent
LIMIT = 1.0


@pytest.fixture(scope="module")
def harness() -> Iterator[ModuleType]:
    """tests/timed_run.py, imported by its path: it is a script, not a package member."""
    spec = importlib.util.spec_from_file_location("timed_run", TESTS_DIRECTORY / "timed_run.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["timed_run"] = module
    spec.loader.exec_module(module)
    yield module
    del sys.modules["timed_run"]


class Ticks:
    """A timer that returns each value it was given, one per read, in order."""

    def __init__(self, *values: float) -> None:
        self._values = iter(values)

    def __call__(self) -> float:
        return next(self._values)


class ScriptedSite:
    """A site that answers each request with the next response it was given, and records them."""

    def __init__(self, *responses: Response) -> None:
        self._responses = iter(responses)
        self.requests: list[tuple[str, str]] = []

    def handle(self, method: str, target: str, headers: object, body: bytes) -> Response:
        self.requests.append((method, target))
        return next(self._responses)


def _found(location: str) -> Response:
    return Response(303, (("Location", location),), b"")


def _page(text: str) -> Response:
    return Response(200, (("Content-Type", "text/html; charset=utf-8"),), text.encode("utf-8"))


def _seeded(harness: ModuleType, tmp_path: Path):
    saved_data = SavedData(tmp_path / "data")
    site, seeded = harness.open_task_volume(saved_data)
    return site, saved_data, seeded


def test_timed_run_exercises_and_reports_task_volume(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-143, QC-48: 1,000 tasks of 20 comments are seeded; add and landing are timed apart."""
    status = harness.main(tmp_path)

    report = capsys.readouterr().out
    assert status == 0
    after = SavedData(tmp_path / "task-volume").load()
    assert after is not None
    assert len(after.tasks) == 1001
    assert [len(task.comments) for task in after.tasks[:1000]] == [20] * 1000
    assert after.tasks[1000].id == 1001
    assert "1000 tasks" in report and "20 comments" in report
    for label in ("add a task at 1000 tasks", "landing page at 1000 tasks"):
        assert f"{label}: " in report
    assert "ordinary create 50:" in report and "create at both maximums:" in report
    assert f"title of {len(after.tasks[0].title)} characters" in report
    assert f"comment of {len(after.tasks[0].comments[0].text)} characters" in report
    assert "over" not in report and "refused" not in report


def test_timed_task_add_rejects_refusal_or_failure(harness: ModuleType, tmp_path: Path) -> None:
    """CP-143: a refused or failed add, or a redirect to no saved new task, is not a pass."""
    _, saved_data, _ = _seeded(harness, tmp_path)
    ticks = [0.0, 0.1, 0.2, 0.3]
    refused = ScriptedSite(_found("/projects/1?task_refused=blank_title"), _page("<h1>x</h1>"))
    failed = ScriptedSite(Response(500, (), b""), _page("<h1>x</h1>"))
    nothing_saved = ScriptedSite(_found("/tasks/1001?added"), _page("<h1>Volume task</h1>"))

    for site in (refused, failed, nothing_saved):
        results = harness.measure_task_volume(site, saved_data, Ticks(*ticks))
        assert results[0].label == "add a task at 1000 tasks"
        assert results[0].created is False
        assert harness.verdict(results, LIMIT) == 1


def test_timed_task_landing_rejects_missing_or_wrong_page(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-143: a bad landing response or a page without the saved task's title is not a pass."""
    for landing in (Response(404, (), b""), _page("<h1>Some other task</h1>")):
        site, saved_data, _ = _seeded(harness, tmp_path / str(landing.status))
        real = site.handle
        answered = ScriptedSite(landing)

        def handle(method, target, headers, body, real=real, answered=answered):
            return (
                real(method, target, headers, body)
                if method == "POST"
                else answered.handle(method, target, headers, body)
            )

        site.handle = handle  # type: ignore[method-assign]
        results = harness.measure_task_volume(site, saved_data, Ticks(0.0, 0.1, 0.2, 0.3))
        assert results[0].created is True
        assert results[1].label == "landing page at 1000 tasks"
        assert results[1].created is False
        assert harness.verdict(results, LIMIT) == 1


def test_timed_task_requires_each_duration_strictly_below_limit(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-143: each of the add and the landing is under one second, and fails on its own."""
    cases = [
        ((0.0, 0.5, 1.0, 1.4), 0, ""),
        ((0.0, 1.0, 2.0, 2.2), 1, "add a task at 1000 tasks"),
        ((0.0, 0.2, 1.0, 2.0), 1, "landing page at 1000 tasks"),
        ((0.0, 1.5, 2.0, 3.5), 1, "both"),
    ]
    for position, (values, expected, failing) in enumerate(cases):
        site, saved_data, _ = _seeded(harness, tmp_path / str(position))
        results = harness.measure_task_volume(site, saved_data, Ticks(*values))
        assert all(result.created for result in results)
        capsys.readouterr()
        assert harness.verdict(results, LIMIT) == expected
        lines = capsys.readouterr().out.splitlines()
        over = [line.split(":")[0] for line in lines if "over" in line]
        if failing == "both":
            assert len(over) == 2
        else:
            assert over == ([failing] if failing else [])


def test_timed_fixture_preserves_whole_state_without_touching_product_data(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-143, QC-48: the add keeps the fixture's tasks and comments, in its own location."""
    product_data = PRODUCT_ROOT / "data"
    existed = product_data.exists()
    site, saved_data, seeded = _seeded(harness, tmp_path)

    results = harness.measure_task_volume(site, saved_data, Ticks(0.0, 0.1, 0.2, 0.3))

    after = saved_data.load()
    assert after is not None
    assert [result.created for result in results] == [True, True]
    assert after.tasks[:1000] == seeded.tasks
    assert find_task(after, 1001) is not None
    assert after.next_task_id == 1002
    assert saved_data.location.parent == tmp_path
    assert product_data.exists() == existed


EDIT_LABEL = "edit a task at 1000 tasks"
EDIT_LANDING_LABEL = "edit landing page at 1000 tasks"
FORM_ADDRESS = "/tasks/{id}"
FIELDS = ("title", "priority", "assignee", "due_date")


class Intercept:
    """The real site, with chosen requests answered by a script instead; every request is kept."""

    def __init__(self, site, answer: Callable[[str, str], Response | None] = lambda m, t: None):
        self._site = site
        self._answer = answer
        self.requests: list[tuple[str, str, dict[str, str], bytes]] = []

    def handle(self, method: str, target: str, headers: dict[str, str], body: bytes) -> Response:
        self.requests.append((method, target, dict(headers), body))
        scripted = self._answer(method, target)
        return (
            scripted if scripted is not None else self._site.handle(method, target, headers, body)
        )


def _edit_id(harness: ModuleType) -> int:
    return harness.EDIT_TASK_ID


def test_timed_run_reports_edit_and_landing_at_exact_volume(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-179, QC-48: the edit and its landing are reported apart, at 1,000 tasks of 20 comments."""
    status = harness.main(tmp_path)

    report = capsys.readouterr().out
    assert status == 0
    for label in (EDIT_LABEL, EDIT_LANDING_LABEL, "add a task at 1000 tasks"):
        assert f"{label}: " in report
    edited = SavedData(tmp_path / "edit-volume").load()
    assert edited is not None
    assert len(edited.tasks) == 1000
    assert [len(task.comments) for task in edited.tasks] == [20] * 1000
    task = find_task(edited, _edit_id(harness))
    assert task is not None and task.title == harness.EDITED_TITLE
    assert f"edited title of {len(harness.EDITED_TITLE)} characters" in report
    assert "edit fixture: 1000 tasks, 20 comments each" in report
    assert "ordinary create 50:" in report and "landing page at 1000 tasks: " in report
    assert "over" not in report and "refused" not in report


def test_timed_edit_uses_loaded_form_baseline_and_same_origin(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-179: the form is read before the timed POST, whose shown values come from it."""
    site, saved_data, seeded = _seeded(harness, tmp_path)
    recording = Intercept(site)
    task_id = _edit_id(harness)
    form_page = site.handle("GET", f"/tasks/{task_id}", {"Host": "127.0.0.1:8017"}, b"")

    results = harness.measure_task_edit(recording, saved_data, Ticks(0.0, 0.1, 0.2, 0.3))

    original = find_task(seeded, task_id)
    assert original is not None
    address = FORM_ADDRESS.format(id=task_id)
    methods = [(method, target) for method, target, _, _ in recording.requests]
    assert methods == [("GET", address), ("POST", address), ("GET", f"{address}?saved")]
    _, _, headers, body = recording.requests[1]
    assert headers["Sec-Fetch-Site"] == "same-origin" and headers["Host"]
    sent = {
        key: values[0]
        for key, values in parse_qs(body.decode("utf-8"), keep_blank_values=True).items()
    }
    form_page = form_page.body.decode("utf-8")
    shown = dict(re.findall(r'name="(shown_[a-z_]+)" value="([^"]*)"', form_page))
    assert set(shown) == {"shown_title", "shown_priority", "shown_assignee", "shown_due_date"}
    assert {key: sent[key] for key in shown} == shown
    assert shown["shown_title"] == original.title
    changed = [name for name in FIELDS if sent[name] != shown[f"shown_{name}"]]
    assert changed == ["title"] and sent["title"] == harness.EDITED_TITLE
    assert [result.label for result in results] == [EDIT_LABEL, EDIT_LANDING_LABEL]
    assert [result.created for result in results] == [True, True]


def test_timed_edit_preserves_every_other_fixture_value(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-179, QC-48: the saved file differs from the fixture by the one title, in its own place."""
    product_data = PRODUCT_ROOT / "data"
    existed = product_data.exists()
    site, saved_data, seeded = _seeded(harness, tmp_path)

    results = harness.measure_task_edit(site, saved_data, Ticks(0.0, 0.1, 0.2, 0.3))

    after = saved_data.load()
    assert after is not None and [result.created for result in results] == [True, True]
    edited = [
        replace(task, title=harness.EDITED_TITLE) if task.id == _edit_id(harness) else task
        for task in seeded.tasks
    ]
    assert after == replace(seeded, tasks=tuple(edited))
    assert len(after.tasks) == 1000 and after.next_task_id == seeded.next_task_id
    assert saved_data.location.parent == tmp_path
    assert product_data.exists() == existed


def _wrong_delta(saved_data: SavedData, change: Callable) -> Callable[[str, str], Response | None]:
    """A script that answers the POST with a saved-looking redirect after `change` rewrote the file."""

    def answer(method: str, target: str) -> Response | None:
        if method != "POST":
            return None
        state = saved_data.load()
        assert state is not None
        saved_data.save(change(state))
        return _found(f"{target}?saved")

    return answer


def test_timed_edit_fails_on_refusal_failure_or_false_success(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-179: a refusal, a failure, or a success that saved nothing, or the wrong thing, fails."""
    task_id = _edit_id(harness)
    address = FORM_ADDRESS.format(id=task_id)

    def retitled(title: str) -> Callable:
        return lambda state: replace(
            state,
            tasks=tuple(replace(t, title=title) if t.id == task_id else t for t in state.tasks),
        )

    def also_touches_another(state):
        edited = retitled(harness.EDITED_TITLE)(state)
        return replace(
            edited,
            tasks=tuple(
                replace(t, priority=Priority.CRITICAL) if t.id == task_id + 1 else t
                for t in edited.tasks
            ),
        )

    cases: dict[str, Callable[[SavedData], Callable[[str, str], Response | None]]] = {
        "refused": lambda d: (
            lambda m, t: _found(f"{address}?edit_refused=blank-title") if m == "POST" else None
        ),
        "failed": lambda d: (
            lambda m, t: _found(f"{address}?edit_failed=save") if m == "POST" else None
        ),
        "server error": lambda d: lambda m, t: Response(500, (), b"") if m == "POST" else None,
        "nothing saved": lambda d: lambda m, t: _found(f"{address}?saved") if m == "POST" else None,
        "wrong title": lambda d: _wrong_delta(d, retitled("Some other title")),
        "unrelated mutation": lambda d: _wrong_delta(d, also_touches_another),
    }
    for name, make in cases.items():
        site, saved_data, _ = _seeded(harness, tmp_path / name.replace(" ", "-"))
        results = harness.measure_task_edit(
            Intercept(site, make(saved_data)), saved_data, Ticks(0.0, 0.1, 0.2, 0.3)
        )
        assert results[0].label == EDIT_LABEL, name
        assert results[0].created is False, name
        assert harness.verdict(results, LIMIT) == 1, name


def test_timed_edit_landing_fails_on_missing_or_wrong_page(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-179: a missing page, a non-200 landing or a wrong title fails; a bad address is no landing."""
    task_id = _edit_id(harness)
    for name, landing in (("missing", Response(404, (), b"")), ("wrong", _page("<h1>Other</h1>"))):
        site, saved_data, _ = _seeded(harness, tmp_path / name)
        recording = Intercept(
            site,
            lambda m, t, landing=landing: landing if m == "GET" and t.endswith("?saved") else None,
        )
        results = harness.measure_task_edit(recording, saved_data, Ticks(0.0, 0.1, 0.2, 0.3))
        assert results[0].created is True
        assert results[1].label == EDIT_LANDING_LABEL and results[1].created is False
        assert harness.verdict(results, LIMIT) == 1
    for name, address in (("bad", "/tasks/999999?saved"), ("elsewhere", "/projects/1")):
        site, saved_data, _ = _seeded(harness, tmp_path / name)
        recording = Intercept(
            site, lambda m, t, address=address: _found(address) if m == "POST" else None
        )
        results = harness.measure_task_edit(recording, saved_data, Ticks(0.0, 0.1))
        assert [r.created for r in results] == [False, False]
        assert [method for method, *_ in recording.requests] == ["GET", "POST"]
        assert results[1].seconds == 0.0
        assert harness.verdict(results, LIMIT) == 1
    assert task_id == harness.EDIT_TASK_ID


def test_timed_edit_requires_each_duration_below_one_second(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-179: the edit and its landing each pass strictly under one second, and fail on their own."""
    cases = [
        ((0.0, 0.5, 1.0, 1.4), 0, ""),
        ((0.0, 1.0, 2.0, 2.2), 1, EDIT_LABEL),
        ((0.0, 0.2, 1.0, 2.0), 1, EDIT_LANDING_LABEL),
        ((0.0, 1.5, 2.0, 3.5), 1, "both"),
    ]
    for position, (values, expected, failing) in enumerate(cases):
        site, saved_data, _ = _seeded(harness, tmp_path / str(position))
        results = harness.measure_task_edit(site, saved_data, Ticks(*values))
        assert all(result.created for result in results)
        capsys.readouterr()
        assert harness.verdict(results, LIMIT) == expected
        lines = capsys.readouterr().out.splitlines()
        over = [line.split(":")[0] for line in lines if "over" in line]
        assert len(over) == 2 if failing == "both" else over == ([failing] if failing else [])


def test_timed_run_fails_when_only_the_edit_fails(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-179: the run itself fails on the edit's verdict, even when every other action passes."""
    add_ticks, edit_ticks = (0.0, 0.1, 0.2, 0.3), (0.0, 1.5, 2.0, 2.1)
    label_ticks = (0.0, 0.1, 0.2, 0.3) * 2
    status = harness.main(
        tmp_path, Ticks(*add_ticks, *edit_ticks, *label_ticks, *QUICK, *NEW_ACTIONS_QUICK)
    )

    over = [line.split(":")[0] for line in capsys.readouterr().out.splitlines() if "over" in line]
    assert over == [EDIT_LABEL]
    assert status == 1


def test_timed_edit_and_add_have_independent_volume_fixtures(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-179: the edit starts and ends with 1,000 tasks; the add still starts at 1,000 and ends at 1,001."""
    edit_data, add_data = SavedData(tmp_path / "edit"), SavedData(tmp_path / "add")
    edit_site, edit_seeded = harness.open_task_volume(edit_data)
    add_site, add_seeded = harness.open_task_volume(add_data)
    assert len(edit_seeded.tasks) == len(add_seeded.tasks) == 1000

    harness.measure_task_edit(edit_site, edit_data, Ticks(0.0, 0.1, 0.2, 0.3))
    unchanged = add_data.load()
    assert unchanged is not None and len(unchanged.tasks) == 1000
    harness.measure_task_volume(add_site, add_data, Ticks(0.0, 0.1, 0.2, 0.3))

    edited, added = edit_data.load(), add_data.load()
    assert edited is not None and added is not None
    assert len(edited.tasks) == 1000 and len(added.tasks) == 1001
    assert added.tasks[:1000] == add_seeded.tasks
    assert edited.next_task_id == 1001 and added.next_task_id == 1002


LABEL_ACTIONS = ("add", "remove")
LABEL_REPORT_LABELS = {
    "add": (
        "add a label at 1000 tasks",
        "label add landing page at 1000 tasks",
        "label add total at 1000 tasks",
    ),
    "remove": (
        "remove a label at 1000 tasks",
        "label remove landing page at 1000 tasks",
        "label remove total at 1000 tasks",
    ),
}


def _label_measure(harness: ModuleType, action: str) -> Callable:
    return getattr(harness, f"measure_label_{action}")


def _label_task_labels(task) -> tuple[str, ...]:
    return tuple(task.labels)


def _label_delta(harness: ModuleType, action: str, state):
    """The fixture with the label action's one intended change to the one task, and no more."""
    task_id = harness.LABEL_TASK_ID

    def changed(task):
        labels = _label_task_labels(task)
        if action == "add":
            return replace(task, labels=(*labels, harness.LABEL_ADDED))
        return replace(task, labels=tuple(each for each in labels if each != harness.LABEL_REMOVED))

    return replace(state, tasks=tuple(changed(t) if t.id == task_id else t for t in state.tasks))


def _label_address(harness: ModuleType, action: str) -> tuple[str, str]:
    """The POST address and the exact landing address the action must redirect to."""
    post = f"/tasks/{harness.LABEL_TASK_ID}/labels" + ("/remove" if action == "remove" else "")
    label = harness.LABEL_ADDED if action == "add" else harness.LABEL_REMOVED
    flag = "label_added" if action == "add" else "label_removed"
    return post, f"/tasks/{harness.LABEL_TASK_ID}?{urlencode({flag: label})}"


def test_timed_run_reports_label_add_and_remove_at_volume(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-208, QC-48: both label actions run at 1,000 tasks of 20 comments, each reported in three
    lines."""
    status = harness.main(tmp_path)

    report = capsys.readouterr().out
    assert status == 0
    for action in LABEL_ACTIONS:
        for label in LABEL_REPORT_LABELS[action]:
            assert f"{label}: " in report, label
        saved = SavedData(tmp_path / f"label-{action}-volume").load()
        assert saved is not None
        assert len(saved.tasks) == 1000
        assert [len(task.comments) for task in saved.tasks] == [20] * 1000
        assert f"label {action} fixture: 1000 tasks, 20 comments each" in report
    assert f"label added of {len(harness.LABEL_ADDED)} characters" in report
    assert f"label removed of {len(harness.LABEL_REMOVED)} characters" in report
    assert "over" not in report and "refused" not in report


def test_timed_label_requests_are_same_origin(harness: ModuleType, tmp_path: Path) -> None:
    """CP-208, QC-32: each label request is the marked POST to its route, then the exact landing
    GET."""
    for action in LABEL_ACTIONS:
        site, saved_data, _ = _seeded(harness, tmp_path / action)
        recording = Intercept(site)

        results = _label_measure(harness, action)(recording, saved_data, Ticks(0.0, 0.1, 0.2, 0.3))

        post, landing = _label_address(harness, action)
        assert [(m, t) for m, t, _, _ in recording.requests] == [("POST", post), ("GET", landing)]
        _, _, headers, body = recording.requests[0]
        assert headers["Sec-Fetch-Site"] == "same-origin" and headers["Host"]
        label = harness.LABEL_ADDED if action == "add" else harness.LABEL_REMOVED
        assert parse_qs(body.decode("utf-8"), keep_blank_values=True) == {"label": [label]}
        assert [result.label for result in results] == list(LABEL_REPORT_LABELS[action])
        assert [result.created for result in results] == [True, True, True]


def test_timed_label_actions_require_exact_saved_delta(harness: ModuleType, tmp_path: Path) -> None:
    """CP-208, QC-48: the saved file is the fixture with the one intended label change, and no
    more."""
    product_data = PRODUCT_ROOT / "data"
    existed = product_data.exists()
    for action in LABEL_ACTIONS:
        site, saved_data, seeded = _seeded(harness, tmp_path / action)

        results = _label_measure(harness, action)(site, saved_data, Ticks(0.0, 0.1, 0.2, 0.3))

        after = saved_data.load()
        assert after is not None and [result.created for result in results] == [True] * 3
        assert after == _label_delta(harness, action, seeded)
        task = find_task(after, harness.LABEL_TASK_ID)
        assert task is not None
        if action == "add":
            assert task.labels[-1] == harness.LABEL_ADDED
        else:
            assert harness.LABEL_REMOVED not in task.labels
    assert product_data.exists() == existed


def test_timed_label_actions_fail_on_a_false_or_wrong_delta(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-208: a 303 with nothing saved, or the wrong thing saved, is not a success."""
    for action in LABEL_ACTIONS:
        _, landing = _label_address(harness, action)

        def other_label(state, action=action):
            task = find_task(state, harness.LABEL_TASK_ID)
            assert task is not None
            return replace(
                state,
                tasks=tuple(
                    replace(t, labels=(*t.labels, "unrelated")) if t.id == task.id else t
                    for t in state.tasks
                ),
            )

        def also_touches_another(state, action=action):
            changed = _label_delta(harness, action, state)
            return replace(
                changed,
                tasks=tuple(
                    replace(t, priority=Priority.CRITICAL)
                    if t.id == harness.LABEL_TASK_ID + 1
                    else t
                    for t in changed.tasks
                ),
            )

        cases = {
            "nothing saved": lambda d, landing=landing: (
                lambda m, t: _found(landing) if m == "POST" else None
            ),
            "wrong label": lambda d: _wrong_delta(d, other_label),
            "unrelated mutation": lambda d: _wrong_delta(d, also_touches_another),
        }
        for name, make in cases.items():
            site, saved_data, _ = _seeded(harness, tmp_path / action / name.replace(" ", "-"))
            results = _label_measure(harness, action)(
                Intercept(site, make(saved_data)), saved_data, Ticks(0.0, 0.1, 0.2, 0.3)
            )
            assert results[0].label == LABEL_REPORT_LABELS[action][0], name
            assert results[0].created is False, name
            assert harness.verdict(results, LIMIT) == 1, name


def test_timed_label_refusal_or_failure_is_not_success(harness: ModuleType, tmp_path: Path) -> None:
    """CP-208: a refused or failed label action, or a server error, fails and is never timed as a
    pass."""
    for action in LABEL_ACTIONS:
        task = f"/tasks/{harness.LABEL_TASK_ID}"
        answers = {
            "empty refusal": _found(f"{task}?label_refused=empty&label="),
            "not carried": _found(f"{task}?label_refused=not-carried&label=x"),
            "failed": _found(f"{task}?label_failed={action}&label=x"),
            "server error": Response(500, (), b""),
            "task not found": Response(404, (), b""),
        }
        for name, answer in answers.items():
            site, saved_data, _ = _seeded(harness, tmp_path / action / name.replace(" ", "-"))
            recording = Intercept(site, lambda m, t, answer=answer: answer if m == "POST" else None)

            results = _label_measure(harness, action)(
                recording, saved_data, Ticks(0.0, 0.1, 0.2, 0.3)
            )

            assert results[0].created is False, (action, name)
            assert harness.verdict(results, LIMIT) == 1, (action, name)


def test_timed_label_landing_must_show_intended_result(harness: ModuleType, tmp_path: Path) -> None:
    """CP-208: a missing or wrong landing address, status, task or shown label result fails."""
    for action in LABEL_ACTIONS:
        label = harness.LABEL_ADDED if action == "add" else harness.LABEL_REMOVED
        seeded_title = "Seeded task {}: write up the work for this part"
        title = seeded_title.format(harness.LABEL_TASK_ID)

        def line(shown_label: str, shown_title: str, action: str = action) -> str:
            if action == "add":
                return f"<p>You added the label '{shown_label}' to '{shown_title}'.</p>"
            return f"<p>You removed the label '{shown_label}' from '{shown_title}'.</p>"

        # Each wrong page differs from the right one, line(label, title), in one value alone, so a
        # harness that skipped checking the task or the label would let that case pass. The right
        # page is checked first: it must pass, or the wrong ones prove nothing.
        site, saved_data, _ = _seeded(harness, tmp_path / action / "right-page")
        right = _page(line(label, title))
        recording = Intercept(
            site, lambda m, t, right=right: right if m == "GET" and "?label_" in t else None
        )
        results = _label_measure(harness, action)(recording, saved_data, Ticks(0.0, 0.1, 0.2, 0.3))
        assert [r.created for r in results] == [True, True, True], (action, "right page")
        pages = {
            "missing page": Response(404, (), b""),
            "wrong task": _page(line(label, seeded_title.format(harness.LABEL_TASK_ID + 1))),
            "wrong label": _page(line("wrong", title)),
            "no result shown": _page("<h1>Plain page</h1>"),
        }
        for name, page in pages.items():
            site, saved_data, _ = _seeded(harness, tmp_path / action / name.replace(" ", "-"))
            recording = Intercept(
                site, lambda m, t, page=page: page if m == "GET" and "?label_" in t else None
            )
            results = _label_measure(harness, action)(
                recording, saved_data, Ticks(0.0, 0.1, 0.2, 0.3)
            )
            assert results[0].created is True, (action, name)
            assert results[1].label == LABEL_REPORT_LABELS[action][1]
            assert results[1].created is False, (action, name)
            assert harness.verdict(results, LIMIT) == 1, (action, name)
        for name, address in (
            ("wrong redirect task", f"/tasks/{harness.LABEL_TASK_ID + 1}?label_added=x"),
            ("elsewhere", "/projects/1"),
            ("no flag", f"/tasks/{harness.LABEL_TASK_ID}"),
        ):
            site, saved_data, _ = _seeded(harness, tmp_path / action / name.replace(" ", "-"))
            recording = Intercept(
                site, lambda m, t, address=address: _found(address) if m == "POST" else None
            )
            results = _label_measure(harness, action)(recording, saved_data, Ticks(0.0, 0.1))
            assert [method for method, *_ in recording.requests] == ["POST"], (action, name)
            assert [r.created for r in results] == [False, False, False], (action, name)
            assert harness.verdict(results, LIMIT) == 1


def test_timed_label_total_is_strictly_below_one_second(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-208: submission plus landing is under one second; two short intervals can still fail."""
    cases = [
        ((0.0, 0.4, 1.0, 1.5), 0, []),
        ((0.0, 0.5, 1.0, 1.5), 1, ["total"]),
        ((0.0, 0.6, 1.0, 1.6), 1, ["total"]),
        ((0.0, 1.0, 2.0, 2.1), 1, ["submission", "total"]),
        ((0.0, 0.1, 1.0, 2.0), 1, ["landing", "total"]),
    ]
    for action in LABEL_ACTIONS:
        names = dict(zip(("submission", "landing", "total"), LABEL_REPORT_LABELS[action]))
        for position, (values, expected, failing) in enumerate(cases):
            site, saved_data, _ = _seeded(harness, tmp_path / action / str(position))
            results = _label_measure(harness, action)(site, saved_data, Ticks(*values))
            assert all(result.created for result in results)
            assert results[2].seconds == pytest.approx(results[0].seconds + results[1].seconds), (
                action,
                values,
            )
            capsys.readouterr()
            assert harness.verdict(results, LIMIT) == expected, (action, values)
            lines = capsys.readouterr().out.splitlines()
            over = [line.split(":")[0] for line in lines if "over" in line]
            assert over == [names[each] for each in failing], (action, values)


def test_timed_run_fails_when_only_a_label_action_fails(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-208: the run exits non-zero on a label action's verdict alone."""
    quick = (0.0, 0.1, 0.2, 0.3)
    slow_total = (0.0, 0.5, 1.0, 1.5)
    ticks = Ticks(*quick, *quick, *slow_total, *quick, *quick, *NEW_ACTIONS_QUICK)

    status = harness.main(tmp_path, ticks)

    over = [line.split(":")[0] for line in capsys.readouterr().out.splitlines() if "over" in line]
    assert over == [LABEL_REPORT_LABELS["add"][2]]
    assert status == 1


def test_timed_label_fixtures_leave_product_data_untouched(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-208, QC-48: each label action has a fixture of its own in the harness's own location."""
    product_data = PRODUCT_ROOT / "data"
    existed = product_data.exists()
    add_data, remove_data = SavedData(tmp_path / "add"), SavedData(tmp_path / "remove")
    add_site, add_seeded = harness.open_task_volume(add_data)
    remove_site, remove_seeded = harness.open_task_volume(remove_data)

    harness.measure_label_add(add_site, add_data, Ticks(0.0, 0.1, 0.2, 0.3))
    unchanged = remove_data.load()
    assert unchanged == remove_seeded
    harness.measure_label_remove(remove_site, remove_data, Ticks(0.0, 0.1, 0.2, 0.3))

    assert add_data.load() == _label_delta(harness, "add", add_seeded)
    assert remove_data.load() == _label_delta(harness, "remove", remove_seeded)
    assert add_data.location.parent == tmp_path and remove_data.location.parent == tmp_path
    assert product_data.exists() == existed


QUICK = (0.0, 0.1, 0.2, 0.3)
# The readings of the comment add and the two assignee actions: four each, all under the limit.
NEW_ACTIONS_QUICK = (*QUICK, *QUICK, *QUICK)
NAME_LABEL = "set your name at 1000 tasks"
NAME_LANDING_LABEL = "name landing page at 1000 tasks"
NAME_ADDRESS = "/operator-name"


def _name_landing(harness: ModuleType) -> str:
    return f"/people?{urlencode({'operator_saved': harness.NAME_VALUE})}"


def _with_name(harness: ModuleType, state):
    return replace(state, operator_name=harness.NAME_VALUE)


def test_timed_run_reports_name_save_and_landing_at_exact_volume(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-237, QC-48: the name save and its landing are two rows, at 1,000 tasks of 20 comments."""
    status = harness.main(tmp_path)

    report = capsys.readouterr().out
    assert status == 0
    for label in (NAME_LABEL, NAME_LANDING_LABEL, EDIT_LABEL, "add a task at 1000 tasks"):
        assert f"{label}: " in report
    after = SavedData(tmp_path / "name-volume").load()
    assert after is not None
    assert after.operator_name == harness.NAME_VALUE
    assert len(after.tasks) == 1000
    assert [len(task.comments) for task in after.tasks] == [20] * 1000
    assert "name fixture: 1000 tasks, 20 comments each" in report
    assert f"name of {len(harness.NAME_VALUE)} characters" in report
    assert "over" not in report and "refused" not in report


def test_timed_name_request_is_same_origin_and_uses_real_readback(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-237: the accepted POST then the exact landing GET; the persisted name is read back."""
    site, saved_data, seeded = _seeded(harness, tmp_path)
    recording = Intercept(site)

    results = harness.measure_operator_name(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )

    methods = [(method, target) for method, target, _, _ in recording.requests]
    assert methods == [("POST", NAME_ADDRESS), ("GET", _name_landing(harness))]
    _, _, headers, body = recording.requests[0]
    assert headers["Sec-Fetch-Site"] == "same-origin" and headers["Host"]
    assert parse_qs(body.decode("utf-8")) == {"name": [harness.NAME_VALUE]}
    assert [(result.label, result.created) for result in results] == [
        (NAME_LABEL, True),
        (NAME_LANDING_LABEL, True),
    ]
    assert saved_data.load() == _with_name(harness, seeded)


def _name_delta(
    saved_data: SavedData, change: Callable, landing: str
) -> Callable[[str, str], Response | None]:
    """A script that answers the POST with the landing redirect after `change` rewrote the file."""

    def answer(method: str, target: str) -> Response | None:
        if method != "POST":
            return None
        state = saved_data.load()
        assert state is not None
        saved_data.save(change(state))
        return _found(landing)

    return answer


def _answer_post(response: Callable[[SavedData], Response]):
    def make(saved_data: SavedData) -> Callable[[str, str], Response | None]:
        return lambda method, target: response(saved_data) if method == "POST" else None

    return make


def test_timed_name_false_save_or_unrelated_delta_is_failure(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-237: a plausible 303 with no write, the wrong name, or an unrelated change fails."""
    landing = _name_landing(harness)

    def renamed(name: str | None) -> Callable:
        return lambda state: replace(state, operator_name=name)

    def also_touches_a_task(state):
        named = _with_name(harness, state)
        first = named.tasks[0]
        return replace(named, tasks=(replace(first, title="Changed"), *named.tasks[1:]))

    cases: dict[str, Callable[[SavedData], Callable[[str, str], Response | None]]] = {
        "nothing saved": _answer_post(lambda d: _found(landing)),
        "name unchanged": lambda d: _name_delta(d, renamed(None), landing),
        "wrong name": lambda d: _name_delta(d, renamed("Someone Else"), landing),
        "unrelated mutation": lambda d: _name_delta(d, also_touches_a_task, landing),
        "saved but wrong address": lambda d: _name_delta(
            d, lambda state: _with_name(harness, state), "/people?operator_saved=Someone+Else"
        ),
        "saved but plain redirect": lambda d: _name_delta(
            d, lambda state: _with_name(harness, state), "/people"
        ),
    }
    for name, make in cases.items():
        site, saved_data, _ = _seeded(harness, tmp_path / name.replace(" ", "-"))
        results = harness.measure_operator_name(
            site=Intercept(site, make(saved_data)), saved_data=saved_data, timer=Ticks(*QUICK)
        )
        assert results[0].label == NAME_LABEL, name
        assert results[0].created is False, name
        assert harness.verdict(results, LIMIT) == 1, name


def test_timed_name_refusal_failure_or_wrong_redirect_is_failure(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-237: refusal or failure metadata, a server error, a no-change redirect, or a wrong
    address."""
    cases = {
        "blank": _found("/people?operator_refused=blank-name&operator_typed="),
        "too long": _found("/people?operator_refused=too-long"),
        "failure": _found(f"/people?operator_failed=save&operator_typed={harness.NAME_VALUE}"),
        "server error": Response(500, (), b""),
        "no change": _found("/people"),
        "wrong address": _found("/people?operator_saved=Someone+Else"),
        "missing address": Response(303, (), b""),
    }
    for name, response in cases.items():
        site, saved_data, _ = _seeded(harness, tmp_path / name.replace(" ", "-"))
        results = harness.measure_operator_name(
            site=Intercept(site, _answer_post(lambda d, response=response: response)(saved_data)),
            saved_data=saved_data,
            timer=Ticks(*QUICK),
        )
        assert results[0].created is False, name
        assert harness.verdict(results, LIMIT) == 1, name
        assert results[1].created is False, name


def test_timed_name_landing_requires_intended_saved_result(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-237: after a real save, a wrong status, or a page without the name's field or line,
    fails."""
    name = harness.NAME_VALUE
    field = f'<input type="text" id="operator-name" name="name" value="{name}">'
    line = f"You set your name to '{name}'."
    cases = {
        "wrong status": Response(404, (), b""),
        "no field": _page(f"<p>{line}</p>"),
        "no completion": _page(field),
        "wrong name": _page(field.replace(name, "Other") + f"<p>{line.replace(name, 'Other')}</p>"),
    }
    for label, landing in cases.items():
        site, saved_data, _ = _seeded(harness, tmp_path / label.replace(" ", "-"))
        real = site.handle
        answered = ScriptedSite(landing)

        def handle(method, target, headers, body, real=real, answered=answered):
            return (
                real(method, target, headers, body)
                if method == "POST"
                else answered.handle(method, target, headers, body)
            )

        site.handle = handle  # type: ignore[method-assign]
        results = harness.measure_operator_name(
            site=site, saved_data=saved_data, timer=Ticks(*QUICK)
        )
        assert results[0].created is True, label
        assert results[1].label == NAME_LANDING_LABEL
        assert results[1].created is False, label
        assert harness.verdict(results, LIMIT) == 1, label


def test_timed_name_requires_each_duration_strictly_below_one_second(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-237: each of the save and the landing is under one second, and fails on its own."""
    cases = [
        ((0.0, 0.5, 1.0, 1.4), 0, []),
        ((0.0, 1.0, 2.0, 2.2), 1, [NAME_LABEL]),
        ((0.0, 0.2, 1.0, 2.0), 1, [NAME_LANDING_LABEL]),
        ((0.0, 1.5, 2.0, 3.5), 1, [NAME_LABEL, NAME_LANDING_LABEL]),
    ]
    for position, (values, expected, failing) in enumerate(cases):
        site, saved_data, _ = _seeded(harness, tmp_path / str(position))
        results = harness.measure_operator_name(
            site=site, saved_data=saved_data, timer=Ticks(*values)
        )
        assert all(result.created for result in results)
        capsys.readouterr()
        assert harness.verdict(results, LIMIT) == expected, values
        lines = capsys.readouterr().out.splitlines()
        assert [line.split(":")[0] for line in lines if "over" in line] == failing, values


def test_full_timed_run_fails_when_only_name_measurement_fails(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-237: the run exits non-zero on either name row alone while every old row passes."""
    for position, name_ticks in enumerate(((0.0, 1.5, 2.0, 2.1), (0.0, 0.1, 0.2, 1.5))):
        old = (*QUICK, *QUICK, *QUICK, *QUICK)
        status = harness.main(
            tmp_path / str(position), Ticks(*old, *name_ticks, *NEW_ACTIONS_QUICK)
        )
        lines = capsys.readouterr().out.splitlines()
        over = [line.split(":")[0] for line in lines if "over" in line]
        assert over == [(NAME_LABEL, NAME_LANDING_LABEL)[position]]
        assert status == 1


def test_timed_name_fixture_does_not_touch_product_data_or_other_fixtures(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-237, QC-48: the name fixture is a real file of its own; the other fixtures stay as
    seeded."""
    product_data = PRODUCT_ROOT / "data"
    existed = product_data.exists()
    name_data, add_data = SavedData(tmp_path / "name"), SavedData(tmp_path / "add")
    name_site, name_seeded = harness.open_task_volume(name_data)
    add_site, add_seeded = harness.open_task_volume(add_data)

    harness.measure_operator_name(site=name_site, saved_data=name_data, timer=Ticks(*QUICK))

    assert add_data.load() == add_seeded
    assert name_data.load() == _with_name(harness, name_seeded)
    assert name_seeded.operator_name is None
    harness.measure_task_volume(add_site, add_data, Ticks(*QUICK))
    named = name_data.load()
    assert named is not None and len(named.tasks) == 1000
    assert name_data.location.parent == tmp_path and add_data.location.parent == tmp_path
    assert product_data.exists() == existed


# --- The comment add, timed on its own 1,000-task fixture (CP-277 to CP-288) ---------------------

SITE_HOST = "127.0.0.1:8017"
SAVED_FILE = "tracker.json"
FIXED_INSTANT = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)
COMMENT_TASK = 250
COMMENT_POST = f"/tasks/{COMMENT_TASK}/comments"
COMMENT_LANDING = f"/tasks/{COMMENT_TASK}?comment_added=21"
COMMENT_LABELS = (
    "add a comment at 1000 tasks",
    "comment landing page at 1000 tasks",
    "comment total at 1000 tasks",
)
SEEDED_TITLE = "Seeded task {}: write up the work for this part"


def _site_over(harness: ModuleType, saved_data: SavedData, state):
    """The real site over a state saved and loaded through the real saved data."""
    saved_data.save(state)
    loaded = saved_data.load()
    assert loaded is not None
    return Site(Tracker(loaded, saved_data, harness.RealClock()), SITE_HOST), loaded


def _comment(text: str, author: str) -> Comment:
    return Comment(text, author, FIXED_INSTANT)


def _with_comments(state, task_id: int, *added: Comment):
    """The state with these comments after the task's own, and nothing else changed."""
    return replace(
        state,
        tasks=tuple(
            replace(task, comments=(*task.comments, *added)) if task.id == task_id else task
            for task in state.tasks
        ),
    )


def _with_new_comment_time_masked(state, task_id: int):
    """The state with the task's last comment's time set to a fixed instant, to compare the rest."""

    def mask(task):
        *earlier, last = task.comments
        return replace(task, comments=(*earlier, replace(last, created_at=FIXED_INSTANT)))

    return replace(state, tasks=tuple(mask(t) if t.id == task_id else t for t in state.tasks))


def _retitled(state, task_id: int, title: str):
    return replace(
        state, tasks=tuple(replace(t, title=title) if t.id == task_id else t for t in state.tasks)
    )


def _comment_landing_page(title: str, text: str) -> Response:
    """The page a real add lands on: its completion line and the comment's text, both escaped."""
    return _page(
        f"<h1>{escape(title)}</h1><p>You added a comment to '{escape(title)}'.</p>"
        f"<li><p>{escape(text)}</p></li>"
    )


def _comment_fixture(harness: ModuleType, tmp_path: Path):
    """The comment fixture as the harness opens it: its saved data, the real site and the state."""
    saved_data = SavedData(tmp_path / "comment")
    site, seeded = harness.open_comment_volume(saved_data)
    return site, saved_data, seeded


def test_timed_comment_fixture_saves_full_volume_and_operator(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-277: 1,000 tasks of 20 comments and a saved operator name, loaded before any request."""
    saved_data = SavedData(tmp_path / "comment")

    site, loaded = harness.open_comment_volume(saved_data)

    assert saved_data.load() == loaded
    assert len(loaded.tasks) == 1000
    assert [len(task.comments) for task in loaded.tasks] == [20] * 1000
    assert loaded.operator_name == harness.COMMENT_OPERATOR_NAME == "Jordan Rivera"
    assert harness.COMMENT_TASK_ID == COMMENT_TASK
    seeded_texts = {comment.text for task in loaded.tasks for comment in task.comments}
    assert harness.COMMENT_TEXT.strip() and harness.COMMENT_TEXT not in seeded_texts
    page = site.handle("GET", f"/tasks/{COMMENT_TASK}", {"Host": SITE_HOST}, b"")
    assert page.status == 200
    assert SEEDED_TITLE.format(COMMENT_TASK) in page.body.decode("utf-8")


def test_timed_comment_submission_saves_exact_delta_and_lands(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-278, CP-279: one marked POST of text, the exact landing GET, one final comment saved."""
    site, saved_data, seeded = _comment_fixture(harness, tmp_path)
    recording = Intercept(site)

    results = harness.measure_comment_add(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )

    assert [(m, t) for m, t, _, _ in recording.requests] == [
        ("POST", COMMENT_POST),
        ("GET", COMMENT_LANDING),
    ]
    _, _, post_headers, body = recording.requests[0]
    assert post_headers["Host"] == SITE_HOST and post_headers["Sec-Fetch-Site"] == "same-origin"
    assert parse_qs(body.decode("utf-8"), keep_blank_values=True) == {
        "text": [harness.COMMENT_TEXT]
    }
    assert recording.requests[1][2]["Host"] == SITE_HOST
    assert [(r.label, r.created) for r in results] == [(label, True) for label in COMMENT_LABELS]
    after = saved_data.load()
    assert after is not None
    task = find_task(after, COMMENT_TASK)
    assert task is not None and len(task.comments) == 21
    assert task.comments[-1].text == harness.COMMENT_TEXT
    assert task.comments[-1].author == "Jordan Rivera"
    expected = _with_comments(seeded, COMMENT_TASK, _comment(harness.COMMENT_TEXT, "Jordan Rivera"))
    assert _with_new_comment_time_masked(after, COMMENT_TASK) == expected


def _no_name_fixture(harness: ModuleType, tmp_path: Path):
    saved_data = SavedData(tmp_path / "no-name")
    site, loaded = _site_over(
        harness, saved_data, replace(harness.seeded_state(), operator_name=None)
    )
    return site, saved_data, loaded


def test_timed_comment_refusal_or_wrong_redirect_never_requests_landing(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-282, CP-288: any answer but the exact 303 gives three failed rows and no landing GET."""
    task = f"/tasks/{COMMENT_TASK}"
    scripted = {
        "failure redirect": _found(f"{task}?comment_failed=save&comment_text=x"),
        "server error": Response(500, (), b""),
        "another status": Response(200, (), b""),
        "non-303 with the right location": Response(302, (("Location", COMMENT_LANDING),), b""),
        "missing location": Response(303, (), b""),
        "wrong task": _found(f"/tasks/{COMMENT_TASK + 1}?comment_added=21"),
        "wrong count": _found(f"{task}?comment_added=22"),
        "plain redirect": _found(task),
        "unrelated address": _found("/projects/1"),
    }
    cases = {}
    for name, answer in scripted.items():
        site, saved_data, _ = _comment_fixture(harness, tmp_path / name.replace(" ", "-"))
        cases[name] = (
            Intercept(site, lambda m, t, answer=answer: answer if m == "POST" else None),
            saved_data,
        )
    site, saved_data, _ = _no_name_fixture(harness, tmp_path)
    cases["real no-name refusal"] = Intercept(site), saved_data

    for name, (recording, saved_data) in cases.items():
        results = harness.measure_comment_add(
            site=recording, saved_data=saved_data, timer=Ticks(0.0, 0.1)
        )

        assert [(r.label, r.created) for r in results] == [(l, False) for l in COMMENT_LABELS], name
        assert [method for method, *_ in recording.requests] == ["POST"], name
        assert results[1].seconds == 0.0, name
        assert results[0].seconds == pytest.approx(0.1) == results[2].seconds, name
        assert harness.verdict(results, LIMIT) == 1, name


def test_timed_comment_plausible_redirect_requires_exact_saved_change(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-279, CP-282: a correct redirect and a plausible page need the saved delta to count."""
    title = SEEDED_TITLE.format(COMMENT_TASK)
    text, operator = "the new text", "Jordan Rivera"

    def after_one_comment(*comments: Comment):
        return lambda state: _with_comments(state, COMMENT_TASK, *comments)

    def old_comment_altered(state):
        added = _with_comments(state, COMMENT_TASK, _comment(harness.COMMENT_TEXT, operator))
        return replace(
            added,
            tasks=tuple(
                replace(t, comments=(replace(t.comments[0], text="Altered"), *t.comments[1:]))
                if t.id == COMMENT_TASK
                else t
                for t in added.tasks
            ),
        )

    def wrong_order(state):
        return replace(
            state,
            tasks=tuple(
                replace(t, comments=(_comment(harness.COMMENT_TEXT, operator), *t.comments))
                if t.id == COMMENT_TASK
                else t
                for t in state.tasks
            ),
        )

    right = _comment(harness.COMMENT_TEXT, operator)
    cases = {
        "nothing saved": lambda state: state,
        "state missing": None,
        "wrong text": after_one_comment(_comment(text, operator)),
        "wrong author": after_one_comment(_comment(harness.COMMENT_TEXT, "Someone Else")),
        "wrong task": lambda state: _with_comments(state, COMMENT_TASK + 1, right),
        "wrong order": wrong_order,
        "two comments": after_one_comment(right, right),
        "an earlier comment altered": old_comment_altered,
        "an unrelated field changed": lambda state: _retitled(
            _with_comments(state, COMMENT_TASK, right), COMMENT_TASK + 1, "Changed"
        ),
    }
    for name, change in cases.items():
        site, saved_data, _ = _comment_fixture(harness, tmp_path / name.replace(" ", "-"))

        def answer(method, target, saved_data=saved_data, change=change):
            if method == "GET":
                return _comment_landing_page(title, harness.COMMENT_TEXT)
            if change is None:
                (saved_data.location / SAVED_FILE).unlink()
            else:
                state = saved_data.load()
                assert state is not None
                saved_data.save(change(state))
            return _found(COMMENT_LANDING)

        results = harness.measure_comment_add(
            site=Intercept(site, answer), saved_data=saved_data, timer=Ticks(*QUICK)
        )

        assert [r.created for r in results] == [False, True, False], name
        assert harness.verdict(results, LIMIT) == 1, name


def test_timed_comment_landing_requires_completion_and_new_text(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-279, CP-283, CP-288: after a real POST the landing needs a 200, its line and the text."""
    title, text = SEEDED_TITLE.format(COMMENT_TASK), harness.COMMENT_TEXT
    line = f"<p>You added a comment to '{escape(title)}'.</p>"
    pages = {
        "not found": Response(404, (), b""),
        "server error": Response(500, (), b""),
        "no line": _page(f"<h1>{escape(title)}</h1><p>{escape(text)}</p>"),
        "another action's line": _page("<p>You added 'x' to the assignees.</p>" + escape(text)),
        "wrong title": _page("<p>You added a comment to 'Other title'.</p>" + escape(text)),
        "line without the text": _page(line),
        "text without the line": _page(f"<p>{escape(text)}</p>"),
    }
    for name, landing in pages.items():
        site, saved_data, _ = _comment_fixture(harness, tmp_path / name.replace(" ", "-"))
        recording = Intercept(site, lambda m, t, landing=landing: landing if m == "GET" else None)

        results = harness.measure_comment_add(
            site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
        )

        assert [r.created for r in results] == [True, False, False], name
        assert harness.verdict(results, LIMIT) == 1, name
    site, saved_data, _ = _comment_fixture(harness, tmp_path / "control")
    control = _comment_landing_page(title, text)
    recording = Intercept(site, lambda m, t: control if m == "GET" else None)
    results = harness.measure_comment_add(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )
    assert [r.created for r in results] == [True, True, True]


def test_timed_comment_checks_escaped_title_and_the_loaded_operator_name(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-283: a title and a saved name full of markup are compared as the page escapes them."""
    title = "Tricky <b> & \"double\" 'single' 😀"
    operator = "Ana <i> & Co 😀"
    state = _retitled(replace(harness.seeded_state(), operator_name=operator), COMMENT_TASK, title)
    saved_data = SavedData(tmp_path / "escaped")
    site, _ = _site_over(harness, saved_data, state)

    results = harness.measure_comment_add(site=site, saved_data=saved_data, timer=Ticks(*QUICK))

    assert [r.created for r in results] == [True, True, True]
    after = saved_data.load()
    assert after is not None
    added = find_task(after, COMMENT_TASK).comments[-1]  # type: ignore[union-attr]
    assert added.author == operator
    raw = _page(f"<p>You added a comment to '{title}'.</p><p>{harness.COMMENT_TEXT}</p>")
    saved_data = SavedData(tmp_path / "unescaped")
    site, _ = _site_over(harness, saved_data, state)
    recording = Intercept(site, lambda m, t: raw if m == "GET" else None)
    results = harness.measure_comment_add(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )
    assert [r.created for r in results] == [True, False, False]


class EventLog:
    """Timer reads, requests and saved-data loads, in the order they happened."""

    def __init__(self) -> None:
        self.events: list[str] = []

    def timer(self, *values: float) -> Callable[[], float]:
        readings = iter(values)

        def read() -> float:
            self.events.append("tick")
            return next(readings)

        return read

    def site(self, real):
        log = self

        class LoggedSite:
            def handle(self, method, target, headers, body):
                log.events.append(method)
                return real.handle(method, target, headers, body)

        return LoggedSite()

    def saved_data(self, real: SavedData):
        log = self

        class LoggedSavedData:
            def load(self):
                log.events.append("load")
                return real.load()

        return LoggedSavedData()


def _timed_between_ticks(events: list[str]) -> list[list[str]]:
    """The events between the first and second tick, and between the third and fourth."""
    ticks = [position for position, event in enumerate(events) if event == "tick"]
    assert len(ticks) == 4
    return [events[ticks[0] + 1 : ticks[1]], events[ticks[2] + 1 : ticks[3]]]


def test_timed_comment_intervals_exclude_setup_and_readback(
    harness: ModuleType, tmp_path: Path
) -> None:
    """Design measurement contract: only the one POST and the one GET sit between timer reads."""
    site, saved_data, _ = _comment_fixture(harness, tmp_path)
    log = EventLog()

    harness.measure_comment_add(
        site=log.site(site), saved_data=log.saved_data(saved_data), timer=log.timer(*QUICK)
    )

    assert _timed_between_ticks(log.events) == [["POST"], ["GET"]]
    first_tick = log.events.index("tick")
    assert "load" in log.events[:first_tick]
    assert "load" in log.events[first_tick + 2 :]
    assert log.events.count("load") >= 2


BOUNDARY_CASES = (
    ((0.0, 0.4, 1.0, 1.5), 0, ()),
    ((0.0, 0.5, 1.0, 1.5), 1, ("total",)),
    ((0.0, 0.6, 1.0, 1.6), 1, ("total",)),
    ((0.0, 1.0, 2.0, 2.1), 1, ("submission", "total")),
    ((0.0, 0.1, 1.0, 2.0), 1, ("landing", "total")),
)


def test_timed_comment_each_interval_and_total_are_strictly_below_limit(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-284 to CP-287: 0.4 s and 0.5 s pass; 0.5 s and 0.5 s fail the total; 1.0 s fails a row."""
    names = dict(zip(("submission", "landing", "total"), COMMENT_LABELS))
    for position, (values, expected, failing) in enumerate(BOUNDARY_CASES):
        site, saved_data, _ = _comment_fixture(harness, tmp_path / str(position))

        results = harness.measure_comment_add(
            site=site, saved_data=saved_data, timer=Ticks(*values)
        )

        assert [r.label for r in results] == list(COMMENT_LABELS)
        assert all(result.created for result in results)
        timed = (values[1] - values[0]) + (values[3] - values[2])
        assert results[2].seconds == pytest.approx(timed), values
        capsys.readouterr()
        assert harness.verdict(results, LIMIT) == expected, values
        lines = capsys.readouterr().out.splitlines()
        over = [line for line in lines if "over" in line]
        assert [line.split(":")[0] for line in over] == [names[each] for each in failing], values
        assert all(line.endswith(" — at or over 1 s") for line in over), values
        assert all("refused" not in line for line in lines), values


def test_timed_comment_rows_print_milliseconds_to_one_decimal(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-285: a passing row is its label, a colon and the time, with no suffix."""
    site, saved_data, _ = _comment_fixture(harness, tmp_path)
    results = harness.measure_comment_add(
        site=site, saved_data=saved_data, timer=Ticks(0.0, 0.4, 1.0, 1.5)
    )

    harness.verdict(results, LIMIT)

    assert capsys.readouterr().out.splitlines() == [
        "add a comment at 1000 tasks: 400.0 ms",
        "comment landing page at 1000 tasks: 500.0 ms",
        "comment total at 1000 tasks: 900.0 ms",
    ]


def _shrunk(state, tasks: int, comments: int):
    """The same fixture at another uniform volume: fewer tasks, each with fewer comments."""
    return replace(
        state,
        tasks=tuple(replace(t, comments=t.comments[:comments]) for t in state.tasks[:tasks]),
    )


def test_comment_fixture_report_uses_loaded_values_and_code_points(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-286: every count is read from the loaded fixture; a character is one code point."""
    _, _, loaded = _comment_fixture(harness, tmp_path)
    task = find_task(loaded, COMMENT_TASK)
    assert task is not None
    added = len(harness.COMMENT_TEXT)

    assert harness.comment_fixture_report(loaded) == (
        "comment fixture: 1000 tasks, 20 comments each (20000 in all); "
        f"title of {len(task.title)} characters, "
        f"comment of {len(task.comments[0].text)} characters, "
        f"name of {len('Jordan Rivera')} characters, added comment of {added} characters"
    )

    varied = _shrunk(replace(loaded, operator_name="Ana 😀"), tasks=300, comments=3)
    selected = find_task(varied, COMMENT_TASK)
    assert selected is not None
    comments = (replace(selected.comments[0], text="Note 😀"), *selected.comments[1:])
    varied = replace(
        varied,
        tasks=tuple(
            replace(t, title="Plan 😀😀", comments=comments) if t.id == COMMENT_TASK else t
            for t in varied.tasks
        ),
    )
    assert harness.comment_fixture_report(varied) == (
        "comment fixture: 300 tasks, 3 comments each (900 in all); "
        "title of 7 characters, comment of 6 characters, "
        f"name of 5 characters, added comment of {added} characters"
    )


def test_comment_fixture_report_refuses_a_fixture_with_unequal_comment_counts(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-286: "N comments each" is only true of a uniform fixture; any other is refused."""
    _, _, loaded = _comment_fixture(harness, tmp_path)
    ragged = replace(loaded, tasks=(replace(loaded.tasks[0], comments=()), *loaded.tasks[1:]))

    with pytest.raises(harness.FixtureShapeError):
        harness.comment_fixture_report(ragged)


def test_timed_comment_redirect_counts_the_tasks_own_comments(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-279: `{n}` is the added comment's one-based place on its task, so a task that held three
    comments lands on `comment_added=4`; the place is read from the fixture, never fixed at 21."""
    state = _shrunk(
        replace(harness.seeded_state(), operator_name="Jordan Rivera"), tasks=1000, comments=3
    )
    saved_data = SavedData(tmp_path / "three-comments")
    site, _ = _site_over(harness, saved_data, state)
    recording = Intercept(site)

    results = harness.measure_comment_add(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )

    assert [(m, t) for m, t, _, _ in recording.requests] == [
        ("POST", COMMENT_POST),
        ("GET", f"/tasks/{COMMENT_TASK}?comment_added=4"),
    ]
    assert [(r.label, r.created) for r in results] == [(label, True) for label in COMMENT_LABELS]


# --- The People assignee add, timed on its own 1,000-task fixture (CP-277 to CP-288) -------------

ASSIGNEE = "Avery Chen"
OTHER_NAMES = ("Zed Quinn", "Mara Lopez")
ASSIGNEE_ADD_POST = "/assignees"
ASSIGNEE_ADD_LANDING = "/people?added=Avery+Chen"
ASSIGNEE_ADD_LINE = f"You added '{ASSIGNEE}' to the assignees."
ASSIGNEE_ADD_LABELS = (
    "add an assignee at 1000 tasks",
    "assignee add landing page at 1000 tasks",
    "assignee add total at 1000 tasks",
)


def _people_fixture(harness: ModuleType, location: Path, *, listed: tuple[str, ...] = ()):
    """The real site over the fixture with these names listed, the first carried by the first task.

    Returns the site, the saved data and the loaded state, so a case can hold other names and a task
    that already carries one.
    """
    state = replace(harness.seeded_state(), assignees=listed)
    if listed:
        first = replace(state.tasks[0], assignee=listed[0])
        state = replace(state, tasks=(first, *state.tasks[1:]))
    saved_data = SavedData(location)
    site, loaded = _site_over(harness, saved_data, state)
    return site, saved_data, loaded


def _write_then_redirect(
    saved_data: SavedData, change: Callable | None, redirect: str, landing: Response
) -> Callable[[str, str], Response | None]:
    """Answer the POST with `redirect` after `change` rewrote the saved file, or removed it when
    `change` is None, and answer the landing GET with `landing`."""

    def answer(method: str, target: str) -> Response | None:
        if method == "GET":
            return landing
        if change is None:
            (saved_data.location / SAVED_FILE).unlink()
        else:
            state = saved_data.load()
            assert state is not None
            saved_data.save(change(state))
        return _found(redirect)

    return answer


def _assert_not_done_and_never_lands(
    harness: ModuleType,
    measure: Callable,
    labels: tuple[str, str, str],
    recording,
    saved_data,
    name,
) -> None:
    """Three failed rows, one POST and no GET, a zero landing and a total equal to the POST."""
    results = measure(site=recording, saved_data=saved_data, timer=Ticks(0.0, 0.1))

    assert [(r.label, r.created) for r in results] == [(label, False) for label in labels], name
    assert [method for method, *_ in recording.requests] == ["POST"], name
    assert results[1].seconds == 0.0, name
    assert results[0].seconds == pytest.approx(0.1) == results[2].seconds, name
    assert harness.verdict(results, LIMIT) == 1, name


def _assert_boundary_matrix(
    harness: ModuleType,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    open_volume: Callable,
    measure: Callable,
    labels: tuple[str, str, str],
) -> None:
    """Strictly below the limit passes; at it fails that row, and a total at it fails alone."""
    names = dict(zip(("submission", "landing", "total"), labels))
    for position, (values, expected, failing) in enumerate(BOUNDARY_CASES):
        saved_data = SavedData(tmp_path / str(position))
        site, _ = open_volume(saved_data)

        results = measure(site=site, saved_data=saved_data, timer=Ticks(*values))

        assert [r.label for r in results] == list(labels)
        assert all(result.created for result in results)
        timed = (values[1] - values[0]) + (values[3] - values[2])
        assert results[2].seconds == pytest.approx(timed), values
        capsys.readouterr()
        assert harness.verdict(results, LIMIT) == expected, values
        lines = capsys.readouterr().out.splitlines()
        over = [line for line in lines if "over" in line]
        assert [line.split(":")[0] for line in over] == [names[each] for each in failing], values
        assert all(line.endswith(" — at or over 1 s") for line in over), values


def test_timed_assignee_add_fixture_starts_without_submitted_name(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-277: real save and load, 1,000 tasks of 20 comments, the name to add not yet listed."""
    saved_data = SavedData(tmp_path / "add")

    site, loaded = harness.open_assignee_add_volume(saved_data)

    assert saved_data.load() == loaded
    assert len(loaded.tasks) == 1000
    assert [len(task.comments) for task in loaded.tasks] == [20] * 1000
    assert harness.ASSIGNEE_NAME == ASSIGNEE and ASSIGNEE not in loaded.assignees
    page = site.handle("GET", "/people", {"Host": SITE_HOST}, b"")
    assert page.status == 200


def test_timed_assignee_add_saves_only_requested_name_and_lands(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-278, CP-280: one marked POST of name, the exact landing GET, the name added last."""
    site, saved_data, seeded = _people_fixture(harness, tmp_path / "plain")
    recording = Intercept(site)

    results = harness.measure_assignee_add(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )

    assert [(m, t) for m, t, _, _ in recording.requests] == [
        ("POST", ASSIGNEE_ADD_POST),
        ("GET", ASSIGNEE_ADD_LANDING),
    ]
    _, _, headers, body = recording.requests[0]
    assert headers["Host"] == SITE_HOST and headers["Sec-Fetch-Site"] == "same-origin"
    assert parse_qs(body.decode("utf-8"), keep_blank_values=True) == {"name": [ASSIGNEE]}
    assert recording.requests[1][2]["Host"] == SITE_HOST
    assert [(r.label, r.created) for r in results] == [(l, True) for l in ASSIGNEE_ADD_LABELS]
    assert saved_data.load() == replace(seeded, assignees=(ASSIGNEE,))

    site, saved_data, seeded = _people_fixture(harness, tmp_path / "listed", listed=OTHER_NAMES)
    results = harness.measure_assignee_add(site=site, saved_data=saved_data, timer=Ticks(*QUICK))
    assert [r.created for r in results] == [True, True, True]
    assert saved_data.load() == replace(seeded, assignees=(*OTHER_NAMES, ASSIGNEE))
    assert seeded.tasks[0].assignee == OTHER_NAMES[0]


def test_timed_assignee_add_refusal_or_wrong_redirect_never_requests_landing(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-282, CP-288: any answer but the exact 303 gives three failed rows and no landing GET."""
    scripted = {
        "failure redirect": _found(f"/people?failed=add&name={ASSIGNEE}"),
        "server error": Response(500, (), b""),
        "another status": Response(200, (), b""),
        "non-303 with the right location": Response(
            302, (("Location", ASSIGNEE_ADD_LANDING),), b""
        ),
        "missing location": Response(303, (), b""),
        "wrong name": _found("/people?added=Someone+Else"),
        "plain redirect": _found("/people"),
        "unrelated address": _found("/projects/1"),
    }
    for name, answer in scripted.items():
        site, saved_data, _ = _people_fixture(harness, tmp_path / name.replace(" ", "-"))
        recording = Intercept(site, lambda m, t, answer=answer: answer if m == "POST" else None)
        _assert_not_done_and_never_lands(
            harness, harness.measure_assignee_add, ASSIGNEE_ADD_LABELS, recording, saved_data, name
        )
    site, saved_data, _ = _people_fixture(harness, tmp_path / "duplicate", listed=(ASSIGNEE,))
    _assert_not_done_and_never_lands(
        harness,
        harness.measure_assignee_add,
        ASSIGNEE_ADD_LABELS,
        Intercept(site),
        saved_data,
        "real duplicate-name refusal",
    )


def test_timed_assignee_add_plausible_redirect_requires_exact_saved_change(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-280, CP-282: the right address and a plausible page need the saved delta to count."""
    plausible = _page(f"<p>{ASSIGNEE_ADD_LINE}</p>")
    cases = {
        "nothing saved": lambda state: state,
        "state missing": None,
        "wrong name": lambda state: replace(state, assignees=(*state.assignees, "Someone Else")),
        "name added twice over": lambda state: replace(
            state, assignees=(*state.assignees, ASSIGNEE, "Someone Else")
        ),
        "name added first": lambda state: replace(state, assignees=(ASSIGNEE, *state.assignees)),
        "listed names reordered": lambda state: replace(
            state, assignees=(OTHER_NAMES[1], OTHER_NAMES[0], ASSIGNEE)
        ),
        "a listed name removed": lambda state: replace(state, assignees=(OTHER_NAMES[0], ASSIGNEE)),
        "an unrelated field changed": lambda state: _retitled(
            replace(state, assignees=(*state.assignees, ASSIGNEE)), 2, "Changed"
        ),
    }
    for name, change in cases.items():
        site, saved_data, _ = _people_fixture(
            harness, tmp_path / name.replace(" ", "-"), listed=OTHER_NAMES
        )
        answer = _write_then_redirect(saved_data, change, ASSIGNEE_ADD_LANDING, plausible)

        results = harness.measure_assignee_add(
            site=Intercept(site, answer), saved_data=saved_data, timer=Ticks(*QUICK)
        )

        assert [r.created for r in results] == [False, True, False], name
        assert harness.verdict(results, LIMIT) == 1, name


def test_timed_assignee_add_landing_requires_its_completion(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-283, CP-288: after a real save the landing needs a 200 and this action's own line."""
    removed = f"You removed '{ASSIGNEE}' from the assignees, and tasks that already carry the name"
    pages = {
        "not found": Response(404, (), b""),
        "server error": Response(500, (), b""),
        "no completion": _page("<h1>People</h1>"),
        "another action's line": _page(f"<p>{removed} keep it.</p>"),
        "wrong name": _page("<p>You added 'Someone Else' to the assignees.</p>"),
    }
    for name, landing in pages.items():
        site, saved_data, _ = _people_fixture(harness, tmp_path / name.replace(" ", "-"))
        recording = Intercept(site, lambda m, t, landing=landing: landing if m == "GET" else None)

        results = harness.measure_assignee_add(
            site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
        )

        assert [r.created for r in results] == [True, False, False], name
        assert harness.verdict(results, LIMIT) == 1, name
    site, saved_data, _ = _people_fixture(harness, tmp_path / "control")
    control = _page(f"<p>{ASSIGNEE_ADD_LINE}</p>")
    recording = Intercept(site, lambda m, t: control if m == "GET" else None)
    results = harness.measure_assignee_add(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )
    assert [r.created for r in results] == [True, True, True]


def test_timed_assignee_add_intervals_exclude_setup_and_readback(
    harness: ModuleType, tmp_path: Path
) -> None:
    """Design measurement contract: only the one POST and the one GET sit between timer reads."""
    site, saved_data, _ = _people_fixture(harness, tmp_path)
    log = EventLog()

    harness.measure_assignee_add(
        site=log.site(site), saved_data=log.saved_data(saved_data), timer=log.timer(*QUICK)
    )

    assert _timed_between_ticks(log.events) == [["POST"], ["GET"]]
    first_tick = log.events.index("tick")
    assert "load" in log.events[:first_tick]
    assert "load" in log.events[first_tick + 2 :]


def test_timed_assignee_add_each_interval_and_total_are_strictly_below_limit(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-284 to CP-287: the comment add's boundary matrix, with this action's three labels."""
    _assert_boundary_matrix(
        harness,
        capsys,
        tmp_path,
        harness.open_assignee_add_volume,
        harness.measure_assignee_add,
        ASSIGNEE_ADD_LABELS,
    )


def test_assignee_add_fixture_report_uses_loaded_values_and_code_points(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-286: every count is read from the loaded fixture; a character is one code point."""
    _, loaded = harness.open_assignee_add_volume(SavedData(tmp_path))
    first = loaded.tasks[0]

    assert harness.assignee_add_fixture_report(loaded) == (
        "assignee add fixture: 1000 tasks, 20 comments each (20000 in all); "
        f"title of {len(first.title)} characters, comment of {len(first.comments[0].text)} "
        "characters, name added of 10 characters"
    )

    varied = _shrunk(loaded, tasks=300, comments=3)
    note = replace(varied.tasks[0].comments[0], text="Note 😀")
    retitled = replace(
        varied.tasks[0], title="Plan 😀😀", comments=(note, *varied.tasks[0].comments[1:])
    )
    varied = replace(varied, tasks=(retitled, *varied.tasks[1:]))
    assert harness.assignee_add_fixture_report(varied) == (
        "assignee add fixture: 300 tasks, 3 comments each (900 in all); "
        "title of 7 characters, comment of 6 characters, name added of 10 characters"
    )


# --- The People assignee remove, timed on its own 1,000-task fixture (CP-277 to CP-288) ----------

ASSIGNEE_REMOVE_POST = "/assignees/remove"
ASSIGNEE_REMOVE_LANDING = "/people?removed=Avery+Chen"
ASSIGNEE_REMOVE_LINE = (
    f"You removed '{ASSIGNEE}' from the assignees, and tasks that already carry the name keep it."
)
ASSIGNEE_REMOVE_LABELS = (
    "remove an assignee at 1000 tasks",
    "assignee remove landing page at 1000 tasks",
    "assignee remove total at 1000 tasks",
)
LISTED_AROUND = (OTHER_NAMES[0], ASSIGNEE, OTHER_NAMES[1])


def _remove_fixture(
    harness: ModuleType,
    location: Path,
    *,
    listed: tuple[str, ...] = (ASSIGNEE,),
    carrier: str | None = None,
):
    """The real site over the fixture with these names listed and the first task assigned `carrier`.

    Returns the site, the saved data and the loaded state.
    """
    state = replace(harness.seeded_state(), assignees=listed)
    if carrier is not None:
        first = replace(state.tasks[0], assignee=carrier)
        state = replace(state, tasks=(first, *state.tasks[1:]))
    saved_data = SavedData(location)
    site, loaded = _site_over(harness, saved_data, state)
    return site, saved_data, loaded


def test_timed_assignee_remove_fixture_starts_with_submitted_name(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-277: real save and load, 1,000 tasks of 20 comments, the name to remove already listed."""
    saved_data = SavedData(tmp_path / "remove")

    site, loaded = harness.open_assignee_remove_volume(saved_data)

    assert saved_data.load() == loaded
    assert len(loaded.tasks) == 1000
    assert [len(task.comments) for task in loaded.tasks] == [20] * 1000
    assert harness.ASSIGNEE_NAME == ASSIGNEE and ASSIGNEE in loaded.assignees
    page = site.handle("GET", "/people", {"Host": SITE_HOST}, b"")
    assert page.status == 200


def test_timed_assignee_remove_changes_only_list_and_lands(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-278, CP-281: one marked POST of name, the exact landing GET, only that name gone."""
    site, saved_data, seeded = _remove_fixture(harness, tmp_path / "plain")
    recording = Intercept(site)

    results = harness.measure_assignee_remove(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )

    assert [(m, t) for m, t, _, _ in recording.requests] == [
        ("POST", ASSIGNEE_REMOVE_POST),
        ("GET", ASSIGNEE_REMOVE_LANDING),
    ]
    _, _, headers, body = recording.requests[0]
    assert headers["Host"] == SITE_HOST and headers["Sec-Fetch-Site"] == "same-origin"
    assert parse_qs(body.decode("utf-8"), keep_blank_values=True) == {"name": [ASSIGNEE]}
    assert recording.requests[1][2]["Host"] == SITE_HOST
    assert [(r.label, r.created) for r in results] == [(l, True) for l in ASSIGNEE_REMOVE_LABELS]
    assert saved_data.load() == replace(seeded, assignees=())

    site, saved_data, seeded = _remove_fixture(
        harness, tmp_path / "around", listed=LISTED_AROUND, carrier=ASSIGNEE
    )
    results = harness.measure_assignee_remove(site=site, saved_data=saved_data, timer=Ticks(*QUICK))
    assert [r.created for r in results] == [True, True, True]
    after = saved_data.load()
    assert after == replace(seeded, assignees=OTHER_NAMES)
    assert after is not None and after.tasks[0].assignee == ASSIGNEE


def test_timed_assignee_remove_refusal_or_wrong_redirect_never_requests_landing(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-282, CP-288: any answer but the exact 303 gives three failed rows and no landing GET."""
    scripted = {
        "failure redirect": _found(f"/people?failed=remove&name={ASSIGNEE}"),
        "server error": Response(500, (), b""),
        "another status": Response(200, (), b""),
        "non-303 with the right location": Response(
            302, (("Location", ASSIGNEE_REMOVE_LANDING),), b""
        ),
        "missing location": Response(303, (), b""),
        "wrong name": _found("/people?removed=Someone+Else"),
        "plain redirect": _found("/people"),
        "unrelated address": _found("/projects/1"),
    }
    for name, answer in scripted.items():
        site, saved_data, _ = _remove_fixture(harness, tmp_path / name.replace(" ", "-"))
        recording = Intercept(site, lambda m, t, answer=answer: answer if m == "POST" else None)
        _assert_not_done_and_never_lands(
            harness,
            harness.measure_assignee_remove,
            ASSIGNEE_REMOVE_LABELS,
            recording,
            saved_data,
            name,
        )
    site, saved_data, _ = _remove_fixture(harness, tmp_path / "unlisted", listed=OTHER_NAMES)
    _assert_not_done_and_never_lands(
        harness,
        harness.measure_assignee_remove,
        ASSIGNEE_REMOVE_LABELS,
        Intercept(site),
        saved_data,
        "real unlisted-name refusal",
    )


def test_timed_assignee_remove_plausible_redirect_requires_exact_saved_change(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-281, CP-282: the right address and a plausible page need the saved delta to count."""
    plausible = _page(f"<p>{ASSIGNEE_REMOVE_LINE}</p>")
    zed, mara = OTHER_NAMES
    cases = {
        "nothing saved": lambda state: state,
        "state missing": None,
        "requested name still present": lambda state: replace(state, assignees=(ASSIGNEE, mara)),
        "wrong name removed": lambda state: replace(state, assignees=(ASSIGNEE, zed)),
        "extra name removed": lambda state: replace(state, assignees=(zed,)),
        "all names removed": lambda state: replace(state, assignees=()),
        "unrelated name reordered": lambda state: replace(state, assignees=(mara, zed)),
        "task assignee cleared": lambda state: replace(
            state,
            assignees=(zed, mara),
            tasks=(replace(state.tasks[0], assignee=None), *state.tasks[1:]),
        ),
        "an unrelated field changed": lambda state: _retitled(
            replace(state, assignees=(zed, mara)), 2, "Changed"
        ),
    }
    for name, change in cases.items():
        site, saved_data, _ = _remove_fixture(
            harness, tmp_path / name.replace(" ", "-"), listed=LISTED_AROUND, carrier=ASSIGNEE
        )
        answer = _write_then_redirect(saved_data, change, ASSIGNEE_REMOVE_LANDING, plausible)

        results = harness.measure_assignee_remove(
            site=Intercept(site, answer), saved_data=saved_data, timer=Ticks(*QUICK)
        )

        assert [r.created for r in results] == [False, True, False], name
        assert harness.verdict(results, LIMIT) == 1, name


def test_timed_assignee_remove_landing_requires_its_completion(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-283, CP-288: after a real removal the landing needs a 200 and this action's own line."""
    pages = {
        "not found": Response(404, (), b""),
        "server error": Response(500, (), b""),
        "no completion": _page("<h1>People</h1>"),
        "another action's line": _page(f"<p>{ASSIGNEE_ADD_LINE}</p>"),
        "wrong name": _page(
            "<p>You removed 'Someone Else' from the assignees, and tasks that already carry "
            "the name keep it.</p>"
        ),
    }
    for name, landing in pages.items():
        site, saved_data, _ = _remove_fixture(harness, tmp_path / name.replace(" ", "-"))
        recording = Intercept(site, lambda m, t, landing=landing: landing if m == "GET" else None)

        results = harness.measure_assignee_remove(
            site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
        )

        assert [r.created for r in results] == [True, False, False], name
        assert harness.verdict(results, LIMIT) == 1, name
    site, saved_data, _ = _remove_fixture(harness, tmp_path / "control")
    control = _page(f"<p>{ASSIGNEE_REMOVE_LINE}</p>")
    recording = Intercept(site, lambda m, t: control if m == "GET" else None)
    results = harness.measure_assignee_remove(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )
    assert [r.created for r in results] == [True, True, True]


def test_timed_assignee_remove_intervals_exclude_setup_and_readback(
    harness: ModuleType, tmp_path: Path
) -> None:
    """Design measurement contract: only the one POST and the one GET sit between timer reads."""
    site, saved_data, _ = _remove_fixture(harness, tmp_path)
    log = EventLog()

    harness.measure_assignee_remove(
        site=log.site(site), saved_data=log.saved_data(saved_data), timer=log.timer(*QUICK)
    )

    assert _timed_between_ticks(log.events) == [["POST"], ["GET"]]
    first_tick = log.events.index("tick")
    assert "load" in log.events[:first_tick]
    assert "load" in log.events[first_tick + 2 :]


def test_timed_assignee_remove_each_interval_and_total_are_strictly_below_limit(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-284 to CP-287: the comment add's boundary matrix, with this action's three labels."""
    _assert_boundary_matrix(
        harness,
        capsys,
        tmp_path,
        harness.open_assignee_remove_volume,
        harness.measure_assignee_remove,
        ASSIGNEE_REMOVE_LABELS,
    )


def test_assignee_remove_fixture_report_uses_loaded_values_and_code_points(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-286: every count is read from the loaded fixture; a character is one code point."""
    _, loaded = harness.open_assignee_remove_volume(SavedData(tmp_path))
    first = loaded.tasks[0]

    assert harness.assignee_remove_fixture_report(loaded) == (
        "assignee remove fixture: 1000 tasks, 20 comments each (20000 in all); "
        f"title of {len(first.title)} characters, comment of {len(first.comments[0].text)} "
        "characters, name removed of 10 characters"
    )

    varied = _shrunk(loaded, tasks=300, comments=3)
    note = replace(varied.tasks[0].comments[0], text="Note 😀")
    retitled = replace(
        varied.tasks[0], title="Plan 😀😀", comments=(note, *varied.tasks[0].comments[1:])
    )
    varied = replace(varied, tasks=(retitled, *varied.tasks[1:]))
    assert harness.assignee_remove_fixture_report(varied) == (
        "assignee remove fixture: 300 tasks, 3 comments each (900 in all); "
        "title of 7 characters, comment of 6 characters, name removed of 10 characters"
    )


# --- The whole run with the three new action blocks appended (CP-276, CP-285 to CP-289) ----------

OLD_RUN_LABELS = (
    *[f"ordinary create {n}" for n in range(1, 51)],
    "create at both maximums",
    "task fixture",
    "add a task at 1000 tasks",
    "landing page at 1000 tasks",
    "edit fixture",
    EDIT_LABEL,
    EDIT_LANDING_LABEL,
    "label add fixture",
    *LABEL_REPORT_LABELS["add"],
    "label remove fixture",
    *LABEL_REPORT_LABELS["remove"],
    "name fixture",
    NAME_LABEL,
    NAME_LANDING_LABEL,
)
NEW_RUN_LABELS = (
    "comment fixture",
    *COMMENT_LABELS,
    "assignee add fixture",
    *ASSIGNEE_ADD_LABELS,
    "assignee remove fixture",
    *ASSIGNEE_REMOVE_LABELS,
)
NEW_ACTION_NAMES = ("comment", "assignee add", "assignee remove")
NEW_ACTION_LABELS = {
    "comment": COMMENT_LABELS,
    "assignee add": ASSIGNEE_ADD_LABELS,
    "assignee remove": ASSIGNEE_REMOVE_LABELS,
}
OLD_ACTION_READINGS = (
    5  # the add, the edit, two label actions and the name save, four readings each
)


def _run_readings(**slow: tuple[float, float, float, float]) -> Ticks:
    """The timer readings of one whole run: every action under the limit, except those named.

    The five old actions read first, in the order the run times them, then the comment add, the
    assignee add and the assignee remove, as the run appends them.
    """
    order = ("comment", "assignee add", "assignee remove")
    new = [slow.get(name, QUICK) for name in order]
    return Ticks(*QUICK * OLD_ACTION_READINGS, *[value for each in new for value in each])


def _product_data_snapshot() -> dict[str, bytes] | None:
    """The product's data directory as it is: every file's bytes, or None when it is absent."""
    data = PRODUCT_ROOT / "data"
    if not data.exists():
        return None
    return {
        str(p.relative_to(data)): p.read_bytes() for p in sorted(data.rglob("*")) if p.is_file()
    }


@pytest.fixture(scope="module")
def whole_run(harness: ModuleType, tmp_path_factory: pytest.TempPathFactory):
    """One passing whole run: its directory, status, printed lines and the data around it."""
    directory = tmp_path_factory.mktemp("whole-run")
    before = _product_data_snapshot()
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        status = harness.main(directory, _run_readings())
    return directory, status, printed.getvalue().splitlines(), before, _product_data_snapshot()


def test_timed_run_appends_exactly_three_ordered_action_blocks(whole_run) -> None:
    """CP-276, CP-285: every old line keeps its label and place, then the three blocks, no more."""
    _, status, lines, _, _ = whole_run

    assert status == 0
    assert [line.split(":")[0] for line in lines] == [*OLD_RUN_LABELS, *NEW_RUN_LABELS]
    assert "over" not in "\n".join(lines) and "refused" not in "\n".join(lines)


def test_new_timed_fixtures_are_independent_and_preserve_name_save_precondition(
    harness: ModuleType, whole_run, tmp_path: Path
) -> None:
    """CP-277: three distinct locations under the supplied directory, each at 1,000 by 20, each
    changed only by its own action; the name save's fixture still starts without a name."""
    directory, _, _, _, _ = whole_run
    comment_data, add_data, remove_data = (
        SavedData(directory / name)
        for name in ("comment-volume", "assignee-add-volume", "assignee-remove-volume")
    )
    assert len({comment_data.location, add_data.location, remove_data.location}) == 3
    for saved in (comment_data, add_data, remove_data):
        loaded = saved.load()
        assert loaded is not None
        assert saved.location.parent == directory
        assert len(loaded.tasks) == 1000
        assert [len(t.comments) for t in loaded.tasks if t.id != COMMENT_TASK] == [20] * 999

    _, comment_before = harness.open_comment_volume(SavedData(tmp_path / "comment"))
    _, add_before = harness.open_assignee_add_volume(SavedData(tmp_path / "add"))
    _, remove_before = harness.open_assignee_remove_volume(SavedData(tmp_path / "remove"))
    comment_after = comment_data.load()
    assert comment_after is not None
    assert _with_new_comment_time_masked(comment_after, COMMENT_TASK) == (
        _with_new_comment_time_masked(
            _with_comments(
                comment_before, COMMENT_TASK, _comment(harness.COMMENT_TEXT, "Jordan Rivera")
            ),
            COMMENT_TASK,
        )
    )
    assert add_data.load() == replace(add_before, assignees=(ASSIGNEE,))
    assert remove_data.load() == replace(remove_before, assignees=())

    _, name_before = harness.open_task_volume(SavedData(tmp_path / "name"))
    assert name_before.operator_name is None

    # Acting on one fixture leaves another as it was saved.
    one_site, one_data, one_before = _people_fixture(harness, tmp_path / "one")
    _other_site, other_data, other_before = _remove_fixture(harness, tmp_path / "other")
    harness.measure_assignee_add(site=one_site, saved_data=one_data, timer=Ticks(*QUICK))
    assert other_data.load() == other_before
    assert one_data.load() == replace(one_before, assignees=(ASSIGNEE,))


def test_new_timed_actions_leave_product_data_unchanged(whole_run) -> None:
    """CP-277: the product's data directory is as the run found it, absent or byte for byte."""
    _, _, _, before, after = whole_run

    assert after == before


def test_timed_run_reports_actual_fixture_lengths_for_all_three_actions(
    harness: ModuleType, whole_run, tmp_path: Path
) -> None:
    """CP-285, CP-286, CP-288: each fixture line states its loaded volume and actual lengths."""
    _, _, lines, _, _ = whole_run
    by_label = {line.split(":")[0]: line for line in lines}
    _, comment_state = harness.open_comment_volume(SavedData(tmp_path / "comment"))
    _, plain_state = harness.open_assignee_add_volume(SavedData(tmp_path / "plain"))
    selected = find_task(comment_state, COMMENT_TASK)
    assert selected is not None
    first = plain_state.tasks[0]
    volume = "1000 tasks, 20 comments each (20000 in all)"
    assert sum(len(t.comments) for t in comment_state.tasks) == 20000

    assert by_label["comment fixture"] == (
        f"comment fixture: {volume}; title of {len(selected.title)} characters, "
        f"comment of {len(selected.comments[0].text)} characters, "
        f"name of {len('Jordan Rivera')} characters, "
        f"added comment of {len(harness.COMMENT_TEXT)} characters"
    )
    for label, name_length in (
        ("assignee add fixture", "name added of 10 characters"),
        ("assignee remove fixture", "name removed of 10 characters"),
    ):
        assert by_label[label] == (
            f"{label}: {volume}; title of {len(first.title)} characters, "
            f"comment of {len(first.comments[0].text)} characters, {name_length}"
        )


@pytest.mark.parametrize("action", NEW_ACTION_NAMES)
def test_timed_run_fails_when_only_a_new_action_total_reaches_limit(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str], action: str
) -> None:
    """CP-284, CP-287: a total at 1.0 with both parts under it is the only row over, and exit 1."""
    status = harness.main(tmp_path, _run_readings(**{action: (0.0, 0.5, 1.0, 1.5)}))

    over = [line for line in capsys.readouterr().out.splitlines() if "over" in line]
    assert [line.split(":")[0] for line in over] == [NEW_ACTION_LABELS[action][2]]
    assert over[0].endswith(" — at or over 1 s")
    assert status == 1


@pytest.mark.parametrize("action", NEW_ACTION_NAMES)
def test_timed_run_propagates_new_submission_and_landing_timing_failures(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str], action: str
) -> None:
    """CP-287: a slow POST or a slow GET makes exactly its row and its total slow, and exit 1."""
    submission, landing, total = NEW_ACTION_LABELS[action]
    slow = {
        "post": ((0.0, 1.5, 2.0, 2.1), [submission, total]),
        "get": ((0.0, 0.1, 1.0, 2.5), [landing, total]),
    }
    for position, (kind, (readings, expected)) in enumerate(slow.items()):
        status = harness.main(tmp_path / str(position), _run_readings(**{action: readings}))

        lines = capsys.readouterr().out.splitlines()
        over = [line.split(":")[0] for line in lines if "over" in line]
        assert over == expected, (action, kind)
        assert status == 1


# --- What the three new actions share: printed refusals and the readback's place (CP-282, CP-285) --


def _new_action(harness: ModuleType, action: str) -> tuple[Callable, Callable]:
    """The fixture opener and the measurement of one of the three new actions, by its name."""
    return {
        "comment": (harness.open_comment_volume, harness.measure_comment_add),
        "assignee add": (harness.open_assignee_add_volume, harness.measure_assignee_add),
        "assignee remove": (harness.open_assignee_remove_volume, harness.measure_assignee_remove),
    }[action]


def _real_refusal(harness: ModuleType, action: str, location: Path):
    """A fixture the real tracker refuses the action on: no saved name, a listed name, an unlisted
    one. Returns the site and its saved data."""
    if action == "comment":
        site, saved_data, _ = _no_name_fixture(harness, location)
    elif action == "assignee add":
        site, saved_data, _ = _people_fixture(harness, location, listed=(ASSIGNEE,))
    else:
        site, saved_data, _ = _remove_fixture(harness, location, listed=OTHER_NAMES)
    return site, saved_data


@pytest.mark.parametrize("action", NEW_ACTION_NAMES)
def test_new_timed_action_refusal_prints_each_rows_problems(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str], action: str
) -> None:
    """CP-282, CP-285: a refused submission taking 1.0 s prints both problems on its row and on the
    total, joined by a comma; the landing never requested reads 0.0 ms and is refused or failed."""
    site, saved_data = _real_refusal(harness, action, tmp_path / "refused")
    submission, landing, total = NEW_ACTION_LABELS[action]
    _, measure = _new_action(harness, action)

    results = measure(site=site, saved_data=saved_data, timer=Ticks(0.0, 1.0))

    capsys.readouterr()
    assert harness.verdict(results, LIMIT) == 1
    assert capsys.readouterr().out.splitlines() == [
        f"{submission}: 1000.0 ms — refused or failed, at or over 1 s",
        f"{landing}: 0.0 ms — refused or failed",
        f"{total}: 1000.0 ms — refused or failed, at or over 1 s",
    ]


@pytest.mark.parametrize("action", NEW_ACTION_NAMES)
def test_new_timed_action_reads_the_saved_state_back_before_the_landing_interval(
    harness: ModuleType, tmp_path: Path, action: str
) -> None:
    """Design § 3, measurement contract point 5: the saved-state check is made before the landing
    interval, so the fresh load sits between the POST's closing reading and the GET's opening one."""
    open_volume, measure = _new_action(harness, action)
    saved_data = SavedData(tmp_path / "volume")
    site, _ = open_volume(saved_data)
    log = EventLog()

    results = measure(
        site=log.site(site), saved_data=log.saved_data(saved_data), timer=log.timer(*QUICK)
    )

    assert [r.created for r in results] == [True, True, True]
    ticks = [position for position, event in enumerate(log.events) if event == "tick"]
    assert len(ticks) == 4
    assert "load" in log.events[ticks[1] + 1 : ticks[2]]
