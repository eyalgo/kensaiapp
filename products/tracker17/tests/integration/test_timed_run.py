"""Integration tests of the timed harness at task volume (layer 3).

Checks SRS NFR-1 (an action stays fast with 1,000 tasks of 20 comments each, editing a task's fields
included, a label added or removed too, the operator's name saved, a comment added, a name added
to or removed from the assignee list, a task moved from `todo` to `in-progress`, and a project
list filtered by a status, which realizes FR-32, and sorted by priority, which realizes FR-36) and AC-15 (the response time). Change spec rules CP-143 (the add), CP-179 (the edit), CP-208 (the label add and
remove), CP-237 (the name save), CP-276 to CP-289 (the comment add and the assignee add and remove)
CP-371 to CP-392 (the status move), CP-418 to CP-423 (the status filter) and CP-451 to CP-456 (the sort), CP-543 (the task deletion, FR-17), CP-566 (the project rename, FR-12) and NFDR QC-48 are the ones each test names. The harness is
tests/timed_run.py; it is loaded by its path and handed its own collaborators (a request site, a
timer, a location), so no product name is patched. A script that only exits 0 could time the wrong
path, so these tests prove it exercises the real one and refuses a wrong one.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import sys
from collections.abc import Callable, Iterator
from dataclasses import replace
from datetime import UTC, date, datetime
from html import escape, unescape
from pathlib import Path
from types import ModuleType
from urllib.parse import parse_qs, urlencode

import pytest

from application import Tracker
from domain import Comment, Priority, TaskStatus, find_task, restore_state
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
        tmp_path,
        Ticks(
            *add_ticks,
            *edit_ticks,
            *label_ticks,
            *QUICK,
            *NEW_ACTIONS_QUICK,
            *MOVE_QUICK,
            *FILTER_QUICK,
            *SORT_QUICK,
            *SUMMARY_QUICK,
            *DELETE_QUICK,
            *RENAME_QUICK,
        ),
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
    ticks = Ticks(
        *quick,
        *quick,
        *slow_total,
        *quick,
        *quick,
        *NEW_ACTIONS_QUICK,
        *MOVE_QUICK,
        *FILTER_QUICK,
        *SORT_QUICK,
        *SUMMARY_QUICK,
        *DELETE_QUICK,
        *RENAME_QUICK,
    )

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
# The status move's four readings, taken after every earlier action's: all under the limit.
MOVE_QUICK = QUICK
FILTER_QUICK = QUICK
# The sort's four readings, taken after the filter's: all under the limit.
SORT_QUICK = QUICK
# The Summary's two readings, taken after the sort's: one interval round its one GET, under the limit.
SUMMARY_QUICK = (0.0, 0.1)
# The deletion's four readings, taken after the Summary's: all under the limit (CP-543).
DELETE_QUICK = QUICK
# The rename's four readings, taken after the deletion's: all under the limit (CP-566).
RENAME_QUICK = QUICK
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
            tmp_path / str(position),
            Ticks(
                *old,
                *name_ticks,
                *NEW_ACTIONS_QUICK,
                *MOVE_QUICK,
                *FILTER_QUICK,
                *SORT_QUICK,
                *SUMMARY_QUICK,
                *DELETE_QUICK,
                *RENAME_QUICK,
            ),
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


def _run_readings(**slow: tuple[float, ...]) -> Ticks:
    """The timer readings of one whole run: every action under the limit, except those named.

    The five old actions read first, in the order the run times them, then the comment add, the
    assignee add, the assignee remove, the status move, the status filter and the sort, as the
    run appends them, then the Summary's one interval of two readings (CP-509), and last the
    deletion's four (CP-543) and, after the deletion, the rename's four (CP-566).
    """
    order = ("comment", "assignee add", "assignee remove", "move", "filter", "sort")
    new = [slow.get(name, QUICK) for name in order]
    summary = slow.get("summary", SUMMARY_QUICK)
    delete = slow.get("delete", DELETE_QUICK)
    rename = slow.get("rename", RENAME_QUICK)
    return Ticks(
        *QUICK * OLD_ACTION_READINGS,
        *[value for each in new for value in each],
        *summary,
        *delete,
        *rename,
    )


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
    """CP-276, CP-285: every old line keeps its label and place, then the new blocks, no more."""
    _, status, lines, _, _ = whole_run

    assert status == 0
    assert [line.split(":")[0] for line in lines] == [
        *OLD_RUN_LABELS,
        *NEW_RUN_LABELS,
        *MOVE_RUN_LABELS,
        *FILTER_RUN_LABELS,
        *SORT_RUN_LABELS,
        *SUMMARY_RUN_LABELS,
        *DELETE_RUN_LABELS,
        *RENAME_RUN_LABELS,
    ]
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


# --- The status move, timed on its own 1,000-task fixture (CP-371 to CP-381, CP-384, CP-385) -----

MOVE_TASK = 4
MOVE_POST = f"/tasks/{MOVE_TASK}/move"
MOVE_LANDING = f"/projects/1?moved=in-progress&move_task={MOVE_TASK}"
MOVE_LABELS = (
    "move a task at 1000 tasks",
    "move landing page at 1000 tasks",
    "move total at 1000 tasks",
)
MOVE_RUN_LABELS = ("move fixture", *MOVE_LABELS)
FILTER_LABELS = (
    "filter a task list at 1000 tasks",
    "filter landing page at 1000 tasks",
    "filter total at 1000 tasks",
)
FILTER_RUN_LABELS = ("filter fixture", *FILTER_LABELS)
SORT_LABELS = (
    "sort a task list at 1000 tasks",
    "sort landing page at 1000 tasks",
    "sort total at 1000 tasks",
)
SORT_RUN_LABELS = ("sort fixture", *SORT_LABELS)
SUMMARY_LABEL = "open a project summary at 1000 tasks"
SUMMARY_RUN_LABELS = ("summary fixture", SUMMARY_LABEL)
DELETE_LABELS = (
    "delete a task at 1000 tasks",
    "delete landing page at 1000 tasks",
    "delete total at 1000 tasks",
)
DELETE_RUN_LABELS = ("delete fixture", *DELETE_LABELS)
RENAME_LABELS = (
    "rename a project at 1000 tasks",
    "rename landing page at 1000 tasks",
    "rename total at 1000 tasks",
)
RENAME_RUN_LABELS = ("rename fixture", *RENAME_LABELS)
MOVE_OPERATOR = "Jordan Rivera"
MOVE_ASSIGNEES = ("Zed Quinn", "Mara Lopez")


def _moved_line(title: str, status: str = "in-progress") -> str:
    return f"You moved '{escape(title)}' to {status}."


def _move_page(title: str) -> Response:
    """The landing a real move shows: the title as a heading and the completion line."""
    return _page(f"<h1>{escape(title)}</h1><p>{_moved_line(title)}</p>")


def _with_task(state, task_id: int, **changes):
    """The state with these fields of the one task replaced, and nothing else."""
    return replace(
        state,
        tasks=tuple(replace(t, **changes) if t.id == task_id else t for t in state.tasks),
    )


def _after_the_move(state):
    """What a correct move leaves: the task's status replaced by `in-progress`, nothing else."""
    return _with_task(state, MOVE_TASK, status=TaskStatus.IN_PROGRESS)


def _populated(harness: ModuleType, tasks: int = 50, comments: int = 2):
    """A small fixture with a saved operator name and listed assignees, so their preservation
    counts."""
    state = replace(harness.seeded_state(), assignees=MOVE_ASSIGNEES, operator_name=MOVE_OPERATOR)
    return _shrunk(state, tasks=tasks, comments=comments)


def _move_fixture(harness: ModuleType, location: Path, state=None):
    """The real site over this state (the run's own fixture by default), saved and loaded."""
    saved_data = SavedData(location)
    site, loaded = _site_over(
        harness, saved_data, harness.seeded_state() if state is None else state
    )
    return site, saved_data, loaded


def _answer_move(
    saved_data: SavedData,
    redirect: str | None,
    landing: Response | None,
    change: Callable | None = lambda state: state,
) -> Callable[[str, str], Response | None]:
    """Answer the POST with `redirect` after `change` rewrote the file (removed it when `change` is
    None) and the GET with `landing`; None leaves that request to the real site."""

    def answer(method: str, target: str) -> Response | None:
        if method == "GET":
            return landing
        if change is None:
            (saved_data.location / SAVED_FILE).unlink()
        else:
            state = saved_data.load()
            assert state is not None
            saved_data.save(change(state))
        return None if redirect is None else _found(redirect)

    return answer


def test_timed_move_saves_only_status_and_lands_at_full_volume(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """T1, CP-371, CP-372, CP-377, CP-378: one marked POST of two fields, one exact GET, one
    status."""
    site, saved_data, seeded = _move_fixture(harness, tmp_path)
    recording = Intercept(site)
    task = find_task(seeded, MOVE_TASK)
    assert task is not None and task.status is TaskStatus.TODO
    assert len(seeded.tasks) == 1000
    assert [len(t.comments) for t in seeded.tasks] == [20] * 1000
    capsys.readouterr()

    results = harness.measure_task_move(site=recording, saved_data=saved_data, timer=Ticks(*QUICK))

    assert capsys.readouterr().out == ""
    assert [(m, t) for m, t, _, _ in recording.requests] == [
        ("POST", MOVE_POST),
        ("GET", MOVE_LANDING),
    ]
    _, _, headers, body = recording.requests[0]
    assert headers["Host"] == SITE_HOST and headers["Sec-Fetch-Site"] == "same-origin"
    assert headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert parse_qs(body.decode("utf-8"), keep_blank_values=True) == {
        "status": ["in-progress"],
        "place": ["list"],
    }
    assert recording.requests[1][2]["Host"] == SITE_HOST
    assert [(r.label, r.created) for r in results] == [(label, True) for label in MOVE_LABELS]
    assert saved_data.load() == _after_the_move(seeded)
    assert harness.verdict(results, LIMIT) == 0


def test_timed_move_uses_loaded_task_identity_and_project(
    harness: ModuleType, tmp_path: Path
) -> None:
    """TL addition: the task is found by its identity, and its project is the one it carries."""
    base = _populated(harness)
    moved = find_task(_with_task(base, MOVE_TASK, project_id=2), MOVE_TASK)
    tasks = tuple(reversed([moved if t.id == MOVE_TASK else t for t in base.tasks]))
    state = restore_state(
        [(1, "Volume project", "One."), (2, "Second project", "Two.")],
        3,
        MOVE_ASSIGNEES,
        tasks=tasks,
        next_task_id=base.next_task_id,
        operator_name=MOVE_OPERATOR,
    )
    site, saved_data, seeded = _move_fixture(harness, tmp_path, state)
    assert seeded.tasks[0].id != 1 and seeded.tasks[MOVE_TASK - 1].id != MOVE_TASK
    recording = Intercept(site)

    results = harness.measure_task_move(site=recording, saved_data=saved_data, timer=Ticks(*QUICK))

    assert [(m, t) for m, t, _, _ in recording.requests] == [
        ("POST", MOVE_POST),
        ("GET", f"/projects/2?moved=in-progress&move_task={MOVE_TASK}"),
    ]
    assert [r.created for r in results] == [True, True, True]
    assert saved_data.load() == _after_the_move(seeded)


def test_timed_move_refusal_never_requests_landing(harness: ModuleType, tmp_path: Path) -> None:
    """T2, CP-379, CP-381, CP-384: the real product refuses a move to the status already held."""
    state = _with_task(_populated(harness), MOVE_TASK, status=TaskStatus.IN_PROGRESS)
    site, saved_data, seeded = _move_fixture(harness, tmp_path, state)
    recording = Intercept(site)

    results = harness.measure_task_move(
        site=recording, saved_data=saved_data, timer=Ticks(0.0, 0.1)
    )

    assert [(m, t) for m, t, _, _ in recording.requests] == [("POST", MOVE_POST)]
    assert saved_data.load() == seeded
    assert [(r.label, r.created) for r in results] == [(label, False) for label in MOVE_LABELS]
    assert results[1].seconds == 0.0
    assert results[0].seconds == pytest.approx(0.1) == results[2].seconds
    assert harness.verdict(results, LIMIT) == 1


def test_timed_move_requires_todo_even_with_plausible_success(
    harness: ModuleType, tmp_path: Path
) -> None:
    """TL addition: a task already `in-progress` cannot be shown moved by a plausible answer."""
    state = _with_task(_populated(harness), MOVE_TASK, status=TaskStatus.IN_PROGRESS)
    site, saved_data, seeded = _move_fixture(harness, tmp_path, state)
    title = find_task(seeded, MOVE_TASK).title  # type: ignore[union-attr]
    answer = _answer_move(saved_data, MOVE_LANDING, _move_page(title))
    recording = Intercept(site, answer)

    results = harness.measure_task_move(site=recording, saved_data=saved_data, timer=Ticks(*QUICK))

    assert saved_data.load() == _after_the_move(seeded)
    assert [(m, t) for m, t, _, _ in recording.requests] == [
        ("POST", MOVE_POST),
        ("GET", MOVE_LANDING),
    ]
    assert [r.created for r in results] == [False, True, False]
    assert harness.verdict(results, LIMIT) == 1


BAD_ANSWERS = {
    "forbidden": Response(403, (), b""),
    "server error": Response(500, (), b""),
    "ok with the exact location": Response(200, (("Location", MOVE_LANDING),), b""),
    "found with the exact location": Response(302, (("Location", MOVE_LANDING),), b""),
    "no location": Response(303, (), b""),
    "wrong project": _found(f"/projects/2?moved=in-progress&move_task={MOVE_TASK}"),
    "wrong task": _found(f"/projects/1?moved=in-progress&move_task={MOVE_TASK + 1}"),
    "wrong destination": _found(f"/tasks/{MOVE_TASK}?moved=in-progress&move_task={MOVE_TASK}"),
    "wrong status": _found(f"/projects/1?moved=done&move_task={MOVE_TASK}"),
    "missing field": _found("/projects/1?moved=in-progress"),
    "extra field": _found(f"{MOVE_LANDING}&x=1"),
    "reordered fields": _found(f"/projects/1?move_task={MOVE_TASK}&moved=in-progress"),
    "refusal address": _found(f"/projects/1?move_refused=not-allowed&move_task={MOVE_TASK}"),
    "confirmation address": _found(f"/projects/1?move_confirm=cancelled&move_task={MOVE_TASK}"),
}


def _assert_never_lands(harness: ModuleType, recording, saved_data, seeded) -> None:
    results = harness.measure_task_move(
        site=recording, saved_data=saved_data, timer=Ticks(0.0, 0.1)
    )

    assert [method for method, *_ in recording.requests] == ["POST"]
    assert saved_data.load() == seeded
    assert [(r.label, r.created) for r in results] == [(label, False) for label in MOVE_LABELS]
    assert results[1].seconds == 0.0
    assert results[0].seconds == pytest.approx(0.1) == results[2].seconds
    assert harness.verdict(results, LIMIT) == 1


@pytest.mark.parametrize("answer", BAD_ANSWERS.values(), ids=BAD_ANSWERS.keys())
def test_timed_move_invalid_response_never_requests_landing(
    harness: ModuleType, tmp_path: Path, answer: Response
) -> None:
    """T3, CP-371, CP-377, CP-379: any answer but the exact 303 gives no landing request."""
    site, saved_data, seeded = _move_fixture(harness, tmp_path, _populated(harness))
    recording = Intercept(site, lambda m, t: answer if m == "POST" else None)

    _assert_never_lands(harness, recording, saved_data, seeded)


def test_timed_move_unmarked_submission_is_refused_and_never_lands(
    harness: ModuleType, tmp_path: Path
) -> None:
    """T3, CP-371: the same submission without its same-origin mark is a 403 that saves nothing."""
    site, saved_data, seeded = _move_fixture(harness, tmp_path, _populated(harness))
    forwarded: list[int] = []

    class Unmarked(Intercept):
        def handle(self, method, target, headers, body):
            without = {k: v for k, v in headers.items() if k != "Sec-Fetch-Site"}
            response = super().handle(method, target, without, body)
            forwarded.append(response.status)
            return response

    recording = Unmarked(site)

    _assert_never_lands(harness, recording, saved_data, seeded)
    assert forwarded == [403]


def _renamed_project(state):
    first, *rest = state.projects
    return replace(state, projects=(replace(first, name="Renamed"), *rest))


SAVED_DELTAS = {
    "missing readback": None,
    "unchanged state": lambda state: state,
    "wrong moved status": lambda state: _with_task(state, MOVE_TASK, status=TaskStatus.DONE),
    "second task changed too": lambda state: _with_task(
        _after_the_move(state), MOVE_TASK + 1, priority=Priority.CRITICAL
    ),
    "second task moved too": lambda state: _with_task(
        _after_the_move(state), MOVE_TASK + 1, status=TaskStatus.DONE
    ),
    "moved task retitled": lambda state: _with_task(
        _after_the_move(state), MOVE_TASK, title="Changed"
    ),
    "moved task comment changed": lambda state: _with_task(
        _after_the_move(state),
        MOVE_TASK,
        comments=(
            replace(
                find_task(state, MOVE_TASK).comments[0],  # type: ignore[union-attr]
                text="Altered",
            ),
            *find_task(state, MOVE_TASK).comments[1:],  # type: ignore[union-attr]
        ),
    ),
    "moved task comment dropped": lambda state: _with_task(
        _after_the_move(state), MOVE_TASK, comments=()
    ),
    "project changed": lambda state: _renamed_project(_after_the_move(state)),
    "task counter changed": lambda state: replace(
        _after_the_move(state), next_task_id=state.next_task_id + 1
    ),
    "project counter changed": lambda state: replace(
        _after_the_move(state), next_project_id=state.next_project_id + 1
    ),
    "assignee list changed": lambda state: replace(
        _after_the_move(state), assignees=state.assignees[:1]
    ),
    "operator name changed": lambda state: replace(
        _after_the_move(state), operator_name="Someone Else"
    ),
}


@pytest.mark.parametrize("change", SAVED_DELTAS.values(), ids=SAVED_DELTAS.keys())
def test_timed_move_requires_exact_saved_delta_but_still_lands(
    harness: ModuleType, tmp_path: Path, change: Callable | None
) -> None:
    """T4, CP-377 (b): a correct redirect still gets its GET, and a wrong saved state fails the
    POST."""
    site, saved_data, seeded = _move_fixture(harness, tmp_path, _populated(harness))
    title = find_task(seeded, MOVE_TASK).title  # type: ignore[union-attr]
    answer = _answer_move(saved_data, MOVE_LANDING, _move_page(title), change)
    recording = Intercept(site, answer)

    results = harness.measure_task_move(site=recording, saved_data=saved_data, timer=Ticks(*QUICK))

    assert [(m, t) for m, t, _, _ in recording.requests] == [
        ("POST", MOVE_POST),
        ("GET", MOVE_LANDING),
    ]
    assert [r.created for r in results] == [False, True, False]
    assert harness.verdict(results, LIMIT) == 1


def _landing_title(harness: ModuleType) -> str:
    return harness.seeded_state().tasks[MOVE_TASK - 1].title


def test_timed_move_landing_requires_200_and_completion(
    harness: ModuleType, tmp_path: Path
) -> None:
    """T5, CP-378, CP-385: after a real POST the landing needs a 200 and this move's own line."""
    title = _landing_title(harness)
    other = f"Seeded task {MOVE_TASK + 1}: write up the work for this part"
    pages = {
        "non-200 with the line": Response(404, (), _moved_line(title).encode("utf-8")),
        "server error with the line": Response(500, (), _moved_line(title).encode("utf-8")),
        "200 without the line": _page("<h1>Tasks</h1>"),
        "title only": _page(f"<h1>{escape(title)}</h1>"),
        "another task's line": _page(f"<p>{_moved_line(other)}</p>"),
        "another destination": _page(f"<p>{_moved_line(title, 'done')}</p>"),
    }
    for name, landing in pages.items():
        site, saved_data, _ = _move_fixture(
            harness, tmp_path / name.replace(" ", "-"), _populated(harness)
        )
        recording = Intercept(site, lambda m, t, landing=landing: landing if m == "GET" else None)

        results = harness.measure_task_move(
            site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
        )

        assert [r.created for r in results] == [True, False, False], name
        assert harness.verdict(results, LIMIT) == 1, name
    site, saved_data, _ = _move_fixture(harness, tmp_path / "control", _populated(harness))
    control = _page(f"<p>{_moved_line(title)}</p>")
    recording = Intercept(site, lambda m, t: control if m == "GET" else None)
    results = harness.measure_task_move(site=recording, saved_data=saved_data, timer=Ticks(*QUICK))
    assert [r.created for r in results] == [True, True, True]


def test_timed_move_completion_escapes_loaded_title(harness: ModuleType, tmp_path: Path) -> None:
    """T5, CP-378: a title full of markup is compared as the page shows it, never raw."""
    title = "Tricky <b> & \"double\" 'single' é"
    state = _with_task(_populated(harness), MOVE_TASK, title=title)
    site, saved_data, _ = _move_fixture(harness, tmp_path / "real", state)
    results = harness.measure_task_move(site=site, saved_data=saved_data, timer=Ticks(*QUICK))
    assert [r.created for r in results] == [True, True, True]

    wrong = {
        "raw": f"<p>You moved '{title}' to in-progress.</p>",
        "quotes left raw": f"<p>You moved '{escape(title, quote=False)}' to in-progress.</p>",
    }
    for name, text in wrong.items():
        site, saved_data, _ = _move_fixture(harness, tmp_path / name.replace(" ", "-"), state)
        recording = Intercept(site, lambda m, t, text=text: _page(text) if m == "GET" else None)
        results = harness.measure_task_move(
            site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
        )
        assert [r.created for r in results] == [True, False, False], name


def test_timed_move_excludes_setup_readback_and_gap_from_intervals(
    harness: ModuleType, tmp_path: Path
) -> None:
    """T6, CP-376: setup before tick 1, the POST between 1-2, the readback between 2-3, the GET
    between 3-4; a large gap between the intervals changes neither duration nor the total."""
    site, saved_data, _ = _move_fixture(harness, tmp_path, _populated(harness))
    log = EventLog()

    results = harness.measure_task_move(
        site=log.site(site),
        saved_data=log.saved_data(saved_data),
        timer=log.timer(0.0, 0.1, 50.0, 50.2),
    )

    assert log.events == ["load", "tick", "POST", "tick", "load", "tick", "GET", "tick"]
    assert [r.seconds for r in results] == [
        pytest.approx(0.1),
        pytest.approx(0.2),
        pytest.approx(0.3),
    ]
    assert [r.created for r in results] == [True, True, True]


MOVE_TIMING = {
    "all fast": ((0.0, 0.4, 5.0, 5.5), ()),
    "total exactly 1 s": ((0.0, 0.5, 5.0, 5.5), ("total",)),
    "total above 1 s": ((0.0, 0.6, 5.0, 5.6), ("total",)),
    "post exactly 1 s": ((0.0, 1.0, 5.0, 5.1), ("post", "total")),
    "post 1.5 s": ((0.0, 1.5, 5.0, 5.1), ("post", "total")),
    "get exactly 1 s": ((0.0, 0.1, 5.0, 6.0), ("landing", "total")),
    "get above 1 s": ((0.0, 0.1, 5.0, 6.5), ("landing", "total")),
    "just below 1 s": ((0.0, 0.99996, 5.0, 5.00001), ()),
}


@pytest.mark.parametrize("readings,failing", MOVE_TIMING.values(), ids=MOVE_TIMING.keys())
def test_timed_move_requires_each_interval_and_total_below_limit(
    harness: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    readings: tuple[float, float, float, float],
    failing: tuple[str, ...],
) -> None:
    """T7, CP-375, CP-380: raw durations select the problems before one-decimal formatting."""
    site, saved_data, _ = _move_fixture(harness, tmp_path, _populated(harness))
    first, second, third, fourth = readings

    results = harness.measure_task_move(site=site, saved_data=saved_data, timer=Ticks(*readings))

    assert all(result.created for result in results)
    post, landing = second - first, fourth - third
    assert [r.seconds for r in results] == [
        pytest.approx(post),
        pytest.approx(landing),
        pytest.approx(post + landing),
    ]
    capsys.readouterr()
    assert harness.verdict(results, LIMIT) == (1 if failing else 0)
    lines = capsys.readouterr().out.splitlines()
    names = dict(zip(("post", "landing", "total"), MOVE_LABELS))
    assert [line.split(":")[0] for line in lines if "over" in line] == [
        names[each] for each in failing
    ]
    assert all(line.endswith(" — at or over 1 s") for line in lines if "over" in line)
    assert all("refused" not in line for line in lines)
    if readings[1] == 0.99996:
        assert lines[0] == "move a task at 1000 tasks: 1000.0 ms"


def test_timed_move_rows_print_exact_times_and_ordered_problems(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """T8, CP-375, CP-379, CP-380: the printed rows, success and refusal, to one decimal place."""
    site, saved_data, _ = _move_fixture(harness, tmp_path / "ok", _populated(harness))
    results = harness.measure_task_move(
        site=site, saved_data=saved_data, timer=Ticks(0.0, 0.0265, 5.0, 5.0031)
    )
    capsys.readouterr()
    assert harness.verdict(results, LIMIT) == 0
    assert capsys.readouterr().out.splitlines() == [
        "move a task at 1000 tasks: 26.5 ms",
        "move landing page at 1000 tasks: 3.1 ms",
        "move total at 1000 tasks: 29.6 ms",
    ]

    refused = _with_task(_populated(harness), MOVE_TASK, status=TaskStatus.IN_PROGRESS)
    for seconds, text in ((1.0, "1000.0"), (1.5, "1500.0")):
        site, saved_data, _ = _move_fixture(harness, tmp_path / text, refused)
        results = harness.measure_task_move(
            site=site, saved_data=saved_data, timer=Ticks(0.0, seconds)
        )
        capsys.readouterr()
        assert harness.verdict(results, LIMIT) == 1
        assert capsys.readouterr().out.splitlines() == [
            f"move a task at 1000 tasks: {text} ms — refused or failed, at or over 1 s",
            "move landing page at 1000 tasks: 0.0 ms — refused or failed",
            f"move total at 1000 tasks: {text} ms — refused or failed, at or over 1 s",
        ]


def test_move_fixture_report_uses_loaded_full_volume(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """T9, CP-374, CP-386: the whole line from the fixture as loaded back; the report prints
    nothing."""
    _, _, loaded = _move_fixture(harness, tmp_path)
    task = find_task(loaded, MOVE_TASK)
    assert task is not None
    capsys.readouterr()

    report = harness.move_fixture_report(loaded)

    assert capsys.readouterr().out == ""
    assert report == (
        "move fixture: 1000 tasks, 20 comments each (20000 in all); "
        f"title of {len(task.title)} characters, "
        f"comment of {len(task.comments[0].text)} characters"
    )


def test_move_fixture_report_uses_varied_loaded_counts_and_code_points(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """T9, CP-374, CP-386: counts and lengths come from the loaded task, not constants or
    position."""
    shrunk = _shrunk(harness.seeded_state(), tasks=300, comments=3)
    selected = find_task(shrunk, MOVE_TASK)
    assert selected is not None
    note = replace(selected.comments[0], text="Note 😀")
    varied = _with_task(
        shrunk, MOVE_TASK, title="Plan 😀😀", comments=(note, *selected.comments[1:])
    )
    varied = replace(varied, tasks=tuple(reversed(varied.tasks)))
    _, _, loaded = _move_fixture(harness, tmp_path, varied)
    first = loaded.tasks[0]
    assert first.id != MOVE_TASK and len(first.title) != 7
    assert len(first.comments[0].text) != 6
    capsys.readouterr()

    report = harness.move_fixture_report(loaded)

    assert capsys.readouterr().out == ""
    assert report == (
        "move fixture: 300 tasks, 3 comments each (900 in all); "
        "title of 7 characters, comment of 6 characters"
    )


# --- The status move appended to the whole run (CP-372, CP-373, CP-380, CP-381) ------------------

EARLIER_FIXTURES = (
    "data",
    "task-volume",
    "edit-volume",
    "label-add-volume",
    "label-remove-volume",
    "name-volume",
    "comment-volume",
    "assignee-add-volume",
    "assignee-remove-volume",
)


def test_timed_run_appends_exact_move_block_and_nothing_after(
    harness: ModuleType, whole_run, tmp_path: Path
) -> None:
    """T10, CP-373, CP-375, CP-381, CP-423: every older line, the move's four lines, then exactly the
    filter's four, then exactly the sort's four, then the Summary's two, the deletion's four and no
    footer."""
    _, status, lines, _, _ = whole_run
    _, fresh = harness.open_task_volume(SavedData(tmp_path / "fresh"))

    assert status == 0
    assert [line.split(":")[0] for line in lines[:-22]] == [*OLD_RUN_LABELS, *NEW_RUN_LABELS]
    assert lines[-22:-18] == [
        harness.move_fixture_report(fresh),
        "move a task at 1000 tasks: 100.0 ms",
        "move landing page at 1000 tasks: 100.0 ms",
        "move total at 1000 tasks: 200.0 ms",
    ]
    assert lines[-18:-14] == [
        harness.filter_fixture_report(fresh),
        "filter a task list at 1000 tasks: 100.0 ms",
        "filter landing page at 1000 tasks: 100.0 ms",
        "filter total at 1000 tasks: 200.0 ms",
    ]
    assert lines[-14:-10] == [
        harness.sort_fixture_report(fresh),
        "sort a task list at 1000 tasks: 100.0 ms",
        "sort landing page at 1000 tasks: 100.0 ms",
        "sort total at 1000 tasks: 200.0 ms",
    ]
    assert lines[-10].startswith("summary fixture: ")


def test_timed_move_fixture_is_independent_and_product_data_unchanged(
    harness: ModuleType, whole_run, tmp_path: Path
) -> None:
    """T10, CP-372: a location of its own under the run's directory, one status changed, and the
    product's data directory as the run found it."""
    directory, _, _, before, after = whole_run
    moved = SavedData(directory / "move-volume")
    _, seeded = harness.open_task_volume(SavedData(tmp_path / "fresh"))

    state = moved.load()
    assert state is not None
    assert len(state.tasks) == 1000
    assert [len(t.comments) for t in state.tasks] == [20] * 1000
    assert state == _after_the_move(seeded)
    assert moved.location.parent == directory
    earlier = {SavedData(directory / name).location for name in EARLIER_FIXTURES}
    assert moved.location not in earlier and len(earlier) == len(EARLIER_FIXTURES)
    assert after == before


@pytest.mark.parametrize(
    "readings",
    [(0.0, 0.5, 1.0, 1.5), (0.0, 0.6, 1.0, 1.6)],
    ids=["total exactly 1 s", "total above 1 s"],
)
def test_timed_run_fails_when_only_move_total_reaches_limit(
    harness: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    readings: tuple[float, float, float, float],
) -> None:
    """T12, CP-380, CP-381: both parts under the limit, the total over it: only that row, exit 1."""
    status = harness.main(tmp_path, _run_readings(move=readings))

    over = [line for line in capsys.readouterr().out.splitlines() if "over" in line]
    assert [line.split(":")[0] for line in over] == [MOVE_LABELS[2]]
    assert over[0].endswith(" — at or over 1 s")
    assert status == 1


@pytest.mark.parametrize(
    "readings,expected",
    [
        ((0.0, 1.0, 5.0, 5.1), [MOVE_LABELS[0], MOVE_LABELS[2]]),
        ((0.0, 1.5, 5.0, 5.1), [MOVE_LABELS[0], MOVE_LABELS[2]]),
        ((0.0, 0.1, 5.0, 6.0), [MOVE_LABELS[1], MOVE_LABELS[2]]),
        ((0.0, 0.1, 5.0, 7.5), [MOVE_LABELS[1], MOVE_LABELS[2]]),
    ],
    ids=["post exactly 1 s", "post 1.5 s", "get exactly 1 s", "get 2.5 s"],
)
def test_timed_run_propagates_move_submission_and_landing_timing_failures(
    harness: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    readings: tuple[float, float, float, float],
    expected: list[str],
) -> None:
    """T12, CP-380, CP-381: a slow POST or a slow GET makes exactly its row and the total slow."""
    status = harness.main(tmp_path, _run_readings(move=readings))

    lines = capsys.readouterr().out.splitlines()
    assert [line.split(":")[0] for line in lines if "over" in line] == expected
    assert status == 1


# --- The status filter appended to the whole run (CP-418 to CP-423) -------------------------------

FILTER_ADDRESS = (
    "/projects/1?filter_status=in-progress&filter_priority=&filter_assignee=&filter_label="
    "&filter_due_from=&filter_due_to="
)


def _in_progress_ids(state) -> list[int]:
    """The ids of the fixture's `in-progress` tasks, in the order a project list shows them."""
    held = [t for t in state.tasks if t.status is TaskStatus.IN_PROGRESS]
    return [
        t.id for t in sorted(held, key=lambda t: (t.due_date is None, t.due_date or date.min, t.id))
    ]


def _filter_page(ids: list[int], count: int | None = None) -> Response:
    """A project list as the product writes it: one title link per id, under the count line."""
    shown = len(ids) if count is None else count
    words = "1 task matches this filter." if shown == 1 else f"{shown} tasks match this filter."
    rows = "".join(
        f'<tr><td><a class="pre-wrap" href="/tasks/{each}" aria-label="t">t</a></td></tr>'
        for each in ids
    )
    return _page(f'<p class="match-count" id="filter-count">{words}</p><table>{rows}</table>')


def _filter_fixture(harness: ModuleType, location: Path, state=None):
    return _move_fixture(harness, location, state)


def test_timed_filter_uses_independent_loaded_fixture(
    harness: ModuleType, whole_run, tmp_path: Path
) -> None:
    """T12, CP-418: a location of its own under the run's directory, saved data as seeded, both
    requests same-origin GETs, and the product's data directory as the run found it."""
    directory, _, _, before, after = whole_run
    filtered = SavedData(directory / "filter-volume")
    _, seeded = harness.open_task_volume(SavedData(tmp_path / "fresh"))
    assert filtered.load() == seeded
    earlier = {directory / name for name in (*EARLIER_FIXTURES, "move-volume")}
    assert filtered.location not in earlier and filtered.location.parent == directory
    assert after == before

    site, saved_data, _ = _filter_fixture(harness, tmp_path / "recorded")
    recording = Intercept(site)
    harness.measure_task_filter(site=recording, saved_data=saved_data, timer=Ticks(*QUICK))
    assert [(m, t) for m, t, _, _ in recording.requests] == [
        ("GET", FILTER_ADDRESS),
        ("GET", FILTER_ADDRESS),
    ]
    for _, _, headers, body in recording.requests:
        assert headers["Sec-Fetch-Site"] == "same-origin" and body == b""


def test_timed_filter_reports_loaded_counts_and_first_displayed_lengths(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """T12, CP-419: counts, matching number and the title and first comment of the first listed
    match, not the first stored; the report prints nothing."""
    shrunk = _shrunk(harness.seeded_state(), tasks=300, comments=3)
    first = _in_progress_ids(shrunk)[0]
    note = replace(find_task(shrunk, first).comments[0], text="Note 😀")  # type: ignore[union-attr]
    varied = _with_task(
        shrunk,
        first,
        title="Plan 😀😀",
        comments=(note, *find_task(shrunk, first).comments[1:]),  # type: ignore[union-attr]
    )
    varied = replace(varied, tasks=tuple(reversed(varied.tasks)))
    _, _, loaded = _filter_fixture(harness, tmp_path, varied)
    stored_first = next(t for t in loaded.tasks if t.status is TaskStatus.IN_PROGRESS).id
    assert first != stored_first
    capsys.readouterr()

    report = harness.filter_fixture_report(loaded)

    assert capsys.readouterr().out == ""
    assert report == (
        "filter fixture: 300 tasks, 3 comments each (900 in all); "
        f"title of 7 characters, comment of 6 characters; status in-progress, "
        f"{len(_in_progress_ids(loaded))} matching"
    )
    _, fresh = harness.open_task_volume(SavedData(tmp_path / "fresh"))
    assert harness.filter_fixture_report(fresh).endswith("status in-progress, 250 matching")


REFUSED_APPLIES = {
    "field refusal, a 200 without a result": _page('<p id="filter-status-reason">No.</p>'),
    "action failure": Response(500, (), b"<p>The tracker couldn't.</p>"),
    "not found": Response(404, (), b""),
    "forbidden": Response(403, (), b""),
}


@pytest.mark.parametrize("apply", REFUSED_APPLIES.values(), ids=REFUSED_APPLIES.keys())
def test_timed_filter_rejects_refused_or_failed_apply(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str], apply: Response
) -> None:
    """T12, CP-421: no reload is requested, its row is zero and failed, and the total is Apply's."""
    site, saved_data, _ = _filter_fixture(harness, tmp_path)
    recording = Intercept(site, lambda m, t: apply)

    results = harness.measure_task_filter(
        site=recording, saved_data=saved_data, timer=Ticks(0.0, 0.7)
    )

    assert len(recording.requests) == 1
    assert [r.created for r in results] == [False, False, False]
    assert [r.seconds for r in results] == [pytest.approx(0.7), 0.0, pytest.approx(0.7)]
    capsys.readouterr()
    assert harness.verdict(results, LIMIT) == 1
    assert capsys.readouterr().out.splitlines() == [
        "filter a task list at 1000 tasks: 700.0 ms — refused or failed",
        "filter landing page at 1000 tasks: 0.0 ms — refused or failed",
        "filter total at 1000 tasks: 700.0 ms — refused or failed",
    ]


def test_timed_filter_times_apply_and_reload_destinations(
    harness: ModuleType, tmp_path: Path
) -> None:
    """T12, CP-420: a real GET Apply is reloaded at its own address; a redirect the seam supplies
    is reloaded at its Location; the four reads sit around the two requests alone."""
    site, saved_data, _ = _filter_fixture(harness, tmp_path / "plain")
    log = EventLog()
    results = harness.measure_task_filter(
        site=log.site(site), saved_data=saved_data, timer=log.timer(0.0, 0.1, 50.0, 50.2)
    )
    assert log.events == ["tick", "GET", "tick", "tick", "GET", "tick"]
    assert [r.seconds for r in results] == [
        pytest.approx(0.1),
        pytest.approx(0.2),
        pytest.approx(0.3),
    ]
    assert all(r.created for r in results)

    elsewhere = "/projects/1?filter_status=in-progress"
    site, saved_data, _ = _filter_fixture(harness, tmp_path / "redirected")
    recording = Intercept(site, lambda m, t: _found(elsewhere) if t == FILTER_ADDRESS else None)
    results = harness.measure_task_filter(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )
    assert [t for _, t, _, _ in recording.requests] == [FILTER_ADDRESS, elsewhere]
    assert all(r.created for r in results)


def _second_get(landing: Response) -> Callable[[str, str], Response | None]:
    """Answer only the second request, the reload, with this page."""
    seen: list[str] = []

    def answer(method: str, target: str) -> Response | None:
        seen.append(target)
        return landing if len(seen) == 2 else None

    return answer


def _landing_cases(matching: list[int]) -> dict[str, Response]:
    other = next(n for n in range(1, 1001) if n not in matching)
    return {
        "non-200 with the right page": Response(404, (), _filter_page(matching).body),
        "one extra nonmatch": _filter_page([*matching, other], count=len(matching)),
        "one missing match": _filter_page(matching[:-1], count=len(matching)),
        "a duplicate match row": _filter_page([*matching, matching[0]], count=len(matching)),
        "a duplicate in place of a match": _filter_page(
            [*matching[:-1], matching[0]], count=len(matching)
        ),
        "a wrong matching identity": _filter_page([*matching[:-1], other], count=len(matching)),
        "a wrong displayed count": _filter_page(matching, count=len(matching) + 1),
        "no count line": _page(_filter_page(matching).body.decode().split("</p>", 1)[1]),
    }


def test_timed_filter_rejects_inexact_landing(harness: ModuleType, tmp_path: Path) -> None:
    """T12, CP-421, CP-422: each wrong landing fails the landing and the total, never the Apply."""
    _, _, loaded = _filter_fixture(harness, tmp_path / "ids")
    matching = _in_progress_ids(loaded)
    assert len(matching) == 250
    for name, landing in _landing_cases(matching).items():
        site, saved_data, _ = _filter_fixture(harness, tmp_path / name.replace(" ", "-"))
        results = harness.measure_task_filter(
            site=Intercept(site, _second_get(landing)), saved_data=saved_data, timer=Ticks(*QUICK)
        )
        assert [r.created for r in results] == [True, False, False], name
        assert harness.verdict(results, LIMIT) == 1, name
    site, saved_data, _ = _filter_fixture(harness, tmp_path / "control")
    results = harness.measure_task_filter(
        site=Intercept(site, _second_get(_filter_page(matching))),
        saved_data=saved_data,
        timer=Ticks(*QUICK),
    )
    assert [r.created for r in results] == [True, True, True]


def _rewritten_bytes(saved_data: SavedData) -> None:
    """The same saved data written with other bytes: equivalent when decoded."""
    path = saved_data.location / SAVED_FILE
    path.write_bytes(json.dumps(json.loads(path.read_bytes()), indent=1).encode("utf-8"))


def test_timed_filter_detects_saved_byte_changes(harness: ModuleType, tmp_path: Path) -> None:
    """T12, CP-421: equivalent data with other bytes fails, whether it changed at Apply or at the
    reload."""
    site, saved_data, loaded = _filter_fixture(harness, tmp_path / "apply")
    recording = Intercept(site)

    def at_apply(method: str, target: str) -> Response | None:
        if len(recording.requests) == 1:
            _rewritten_bytes(saved_data)
        return None

    recording = Intercept(site, at_apply)
    results = harness.measure_task_filter(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )
    assert saved_data.load() == loaded
    assert [r.created for r in results] == [False, False, False]
    assert len(recording.requests) == 1

    site, saved_data, loaded = _filter_fixture(harness, tmp_path / "reload")

    def at_reload(method: str, target: str) -> Response | None:
        if len(recording.requests) == 2:
            _rewritten_bytes(saved_data)
        return None

    recording = Intercept(site, at_reload)
    results = harness.measure_task_filter(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )
    assert saved_data.load() == loaded
    assert [r.created for r in results] == [True, False, False]
    assert harness.verdict(results, LIMIT) == 1


@pytest.mark.parametrize("readings,failing", MOVE_TIMING.values(), ids=MOVE_TIMING.keys())
def test_timed_filter_requires_every_duration_below_the_limit(
    harness: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    readings: tuple[float, float, float, float],
    failing: tuple[str, ...],
) -> None:
    """T12, CP-420 to CP-422: a slow Apply, a slow reload, each part exactly 1.0 s and a sum of
    exactly 1.0 s with both parts below it fail their rows; a total below 1.0 s passes."""
    site, saved_data, _ = _filter_fixture(harness, tmp_path)
    first, second, third, fourth = readings

    results = harness.measure_task_filter(site=site, saved_data=saved_data, timer=Ticks(*readings))

    assert all(result.created for result in results)
    post, landing = second - first, fourth - third
    assert [r.seconds for r in results] == [
        pytest.approx(post),
        pytest.approx(landing),
        pytest.approx(post + landing),
    ]
    capsys.readouterr()
    assert harness.verdict(results, LIMIT) == (1 if failing else 0)
    lines = capsys.readouterr().out.splitlines()
    names = dict(zip(("post", "landing", "total"), FILTER_LABELS))
    assert [line.split(":")[0] for line in lines if "over" in line] == [
        names[each] for each in failing
    ]


@pytest.mark.parametrize(
    "readings,expected",
    [
        ((0.0, 1.0, 5.0, 5.1), [FILTER_LABELS[0], FILTER_LABELS[2]]),
        ((0.0, 0.1, 5.0, 6.0), [FILTER_LABELS[1], FILTER_LABELS[2]]),
        ((0.0, 0.5, 1.0, 1.5), [FILTER_LABELS[2]]),
    ],
    ids=["apply exactly 1 s", "reload exactly 1 s", "total exactly 1 s"],
)
def test_timed_run_propagates_filter_timing_failures(
    harness: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    readings: tuple[float, float, float, float],
    expected: list[str],
) -> None:
    """T12, CP-422: a slow filter row makes the whole run exit non-zero, earlier actions passing."""
    status = harness.main(tmp_path, _run_readings(filter=readings))

    lines = capsys.readouterr().out.splitlines()
    assert [line.split(":")[0] for line in lines if "over" in line] == expected
    assert status == 1


FILTER_REJECTIONS = {
    "refused apply": lambda site, saved_data: Intercept(site, lambda m, t: _page("<p>no</p>")),
    "inexact landing": lambda site, saved_data: Intercept(
        site, lambda m, t: _filter_page([1]) if t == FILTER_ADDRESS else None
    ),
    "changed bytes": lambda site, saved_data: Intercept(
        site, lambda m, t: _rewritten_bytes(saved_data)
    ),
}


@pytest.mark.parametrize("rejection", FILTER_REJECTIONS.values(), ids=FILTER_REJECTIONS.keys())
def test_timed_filter_failures_reach_main_verdict(
    harness: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    rejection: Callable,
) -> None:
    """T12, CP-422: each rejection class makes the complete harness return non-zero while every
    earlier action passes."""
    measure = harness.measure_task_filter

    def rejected(*, site, saved_data, timer):
        return measure(site=rejection(site, saved_data), saved_data=saved_data, timer=timer)

    monkeypatch.setattr(harness, "measure_task_filter", rejected)

    status = harness.main(tmp_path, _run_readings())

    lines = capsys.readouterr().out.splitlines()
    assert status == 1
    assert [line for line in lines if "refused or failed" in line]
    assert not [line for line in lines[:-18] if "refused" in line or "over" in line]
    assert not [line for line in lines[-14:] if "refused" in line or "over" in line]


# --- The sort appended to the whole run (CP-451 to CP-456) ----------------------------------------

SORT_ADDRESS = (
    "/projects/1?filter_status=&filter_priority=&filter_assignee=&filter_label="
    "&filter_due_from=&filter_due_to=&sort_field=priority&sort_direction=descending"
)
PRIORITY_DESCENDING_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _sorted_ids(state) -> list[int]:
    """The ids of the project's tasks, priority descending then task number, by a plain comparison
    written here and never by the product's sort (CP-454)."""
    held = [t for t in state.tasks if t.project_id == 1]
    return [
        t.id for t in sorted(held, key=lambda t: (PRIORITY_DESCENDING_RANK[t.priority.value], t.id))
    ]


def _sort_page(ids: list[int], count: int | None = None) -> Response:
    """A sorted project list as the product writes it: the count line, then one title link per
    id."""
    shown = len(ids) if count is None else count
    words = "This project has 1 task." if shown == 1 else f"This project has {shown} tasks."
    rows = "".join(
        f'<tr><td><a class="pre-wrap" href="/tasks/{each}" aria-label="t">t</a></td></tr>'
        for each in ids
    )
    return _page(f'<p class="match-count" id="filter-count">{words}</p><table>{rows}</table>')


def _sort_fixture(harness: ModuleType, location: Path, state=None):
    return _move_fixture(harness, location, state)


def test_timed_sort_uses_its_own_loaded_volume_and_two_same_origin_reads(
    harness: ModuleType, whole_run, tmp_path: Path
) -> None:
    """T12, CP-451: a location of its own under the run's directory, saved data as seeded, no
    filter choice, Priority descending sent by both same-origin GETs, and bytes untouched."""
    directory, _, _, before, after = whole_run
    sorted_data = SavedData(directory / "sort-volume")
    _, seeded = harness.open_task_volume(SavedData(tmp_path / "fresh"))
    assert sorted_data.load() == seeded
    earlier = {directory / name for name in (*EARLIER_FIXTURES, "move-volume", "filter-volume")}
    assert sorted_data.location not in earlier and sorted_data.location.parent == directory
    assert after == before

    site, saved_data, _ = _sort_fixture(harness, tmp_path / "recorded")
    recording = Intercept(site)
    saved_before = (saved_data.location / SAVED_FILE).read_bytes()
    harness.measure_task_sort(site=recording, saved_data=saved_data, timer=Ticks(*QUICK))
    assert [(m, t) for m, t, _, _ in recording.requests] == [("GET", SORT_ADDRESS)] * 2
    for _, target, headers, body in recording.requests:
        assert headers["Sec-Fetch-Site"] == "same-origin" and body == b""
        query = parse_qs(target.split("?", 1)[1], keep_blank_values=True)
        assert [v for k, v in query.items() if k.startswith("filter_")] == [[""]] * 6
        assert query["sort_field"] == ["priority"] and query["sort_direction"] == ["descending"]
    assert (saved_data.location / SAVED_FILE).read_bytes() == saved_before


def test_sort_fixture_report_reads_actual_counts_and_first_sorted_text_lengths(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """T12, CP-452: counts, listed number and the title and first comment of the first sorted
    task, not the first stored; the report prints nothing."""
    _, _, standard = _sort_fixture(harness, tmp_path / "standard")
    first = find_task(standard, _sorted_ids(standard)[0])
    assert first is not None
    assert harness.sort_fixture_report(standard) == (
        "sort fixture: 1000 tasks, 20 comments each (20000 in all); "
        f"title of {len(first.title)} characters, "
        f"comment of {len(first.comments[0].text)} characters; "
        "sort priority descending, 1000 listed"
    )

    shrunk = _shrunk(harness.seeded_state(), tasks=300, comments=3)
    top = _sorted_ids(shrunk)[0]
    note = replace(find_task(shrunk, top).comments[0], text="Note 😀")  # type: ignore[union-attr]
    varied = _with_task(
        shrunk,
        top,
        title="Plan 😀😀",
        comments=(note, *find_task(shrunk, top).comments[1:]),  # type: ignore[union-attr]
    )
    varied = replace(varied, tasks=tuple(reversed(varied.tasks)))
    _, _, loaded = _sort_fixture(harness, tmp_path / "varied", varied)
    assert top != loaded.tasks[0].id
    capsys.readouterr()

    report = harness.sort_fixture_report(loaded)

    assert capsys.readouterr().out == ""
    assert report == (
        "sort fixture: 300 tasks, 3 comments each (900 in all); "
        "title of 7 characters, comment of 6 characters; "
        "sort priority descending, 300 listed"
    )


def test_timed_sort_lists_and_counts_only_the_sorted_projects_tasks(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-452, CP-454: `{N}` is the number of the fixture's tasks in the project, the first sorted
    task is that project's, and the landing must list exactly that project's tasks in order, so a
    task of another project, even one that would sort first, is neither counted nor expected."""
    base = _shrunk(harness.seeded_state(), tasks=40, comments=2)
    elsewhere = set(_sorted_ids(base)[:3])
    tasks = tuple(
        replace(t, project_id=2, title="Elsewhere and longer than any other")
        if t.id in elsewhere
        else t
        for t in base.tasks
    )
    state = restore_state(
        [(1, "Volume project", "One."), (2, "Second project", "Two.")],
        3,
        tasks=tasks,
        next_task_id=base.next_task_id,
    )
    site, saved_data, loaded = _sort_fixture(harness, tmp_path, state)
    expected = _sorted_ids(loaded)
    assert len(expected) == 37 and not elsewhere & set(expected)
    first = find_task(loaded, expected[0])
    assert first is not None

    assert harness.sort_fixture_report(loaded) == (
        "sort fixture: 40 tasks, 2 comments each (80 in all); "
        f"title of {len(first.title)} characters, "
        f"comment of {len(first.comments[0].text)} characters; "
        "sort priority descending, 37 listed"
    )
    results = harness.measure_task_sort(site=site, saved_data=saved_data, timer=Ticks(*QUICK))
    assert [(r.label, r.created) for r in results] == [(label, True) for label in SORT_LABELS]
    assert harness.verdict(results, LIMIT) == 0


def test_timed_sort_reports_apply_landing_and_sum(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """T13, CP-453: the four readings sit around the two requests alone; the rows are Apply, the
    landing and their sum, in the existing format."""
    site, saved_data, _ = _sort_fixture(harness, tmp_path)
    log = EventLog()

    results = harness.measure_task_sort(
        site=log.site(site), saved_data=saved_data, timer=log.timer(0.0, 0.1, 50.0, 50.2)
    )

    assert log.events == ["tick", "GET", "tick", "tick", "GET", "tick"]
    assert [r.label for r in results] == list(SORT_LABELS)
    assert [r.seconds for r in results] == [
        pytest.approx(0.1),
        pytest.approx(0.2),
        pytest.approx(0.3),
    ]
    assert all(r.created for r in results)
    capsys.readouterr()
    assert harness.verdict(results, LIMIT) == 0
    assert capsys.readouterr().out.splitlines() == [
        "sort a task list at 1000 tasks: 100.0 ms",
        "sort landing page at 1000 tasks: 200.0 ms",
        "sort total at 1000 tasks: 300.0 ms",
    ]


@pytest.mark.parametrize("readings,failing", MOVE_TIMING.values(), ids=MOVE_TIMING.keys())
def test_sort_threshold_failures_reach_the_rows(
    harness: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    readings: tuple[float, float, float, float],
    failing: tuple[str, ...],
) -> None:
    """T13, CP-453: a slow Apply, a slow landing, each part exactly 1.0 s and a sum of exactly
    1.0 s with both parts below it fail their rows; a total below 1.0 s passes."""
    site, saved_data, _ = _sort_fixture(harness, tmp_path)

    results = harness.measure_task_sort(site=site, saved_data=saved_data, timer=Ticks(*readings))

    assert all(result.created for result in results)
    capsys.readouterr()
    assert harness.verdict(results, LIMIT) == (1 if failing else 0)
    lines = capsys.readouterr().out.splitlines()
    names = dict(zip(("post", "landing", "total"), SORT_LABELS))
    assert [line.split(":")[0] for line in lines if "over" in line] == [
        names[each] for each in failing
    ]


@pytest.mark.parametrize(
    "readings,expected",
    [
        ((0.0, 1.0, 5.0, 5.1), [SORT_LABELS[0], SORT_LABELS[2]]),
        ((0.0, 0.1, 5.0, 6.0), [SORT_LABELS[1], SORT_LABELS[2]]),
        ((0.0, 0.5, 1.0, 1.5), [SORT_LABELS[2]]),
    ],
    ids=["apply exactly 1 s", "landing exactly 1 s", "total exactly 1 s"],
)
def test_sort_threshold_failures_reach_main(
    harness: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    readings: tuple[float, float, float, float],
    expected: list[str],
) -> None:
    """T13, CP-453, CP-454: a slow sort row makes the whole run exit non-zero, earlier actions
    passing."""
    status = harness.main(tmp_path, _run_readings(sort=readings))

    lines = capsys.readouterr().out.splitlines()
    assert [line.split(":")[0] for line in lines if "over" in line] == expected
    assert status == 1


@pytest.mark.parametrize("apply", REFUSED_APPLIES.values(), ids=REFUSED_APPLIES.keys())
def test_failed_sort_apply_suppresses_landing(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str], apply: Response
) -> None:
    """T13, CP-454: no landing is requested, its row is zero and failed, the total is Apply's
    time, and the verdict is non-zero."""
    site, saved_data, _ = _sort_fixture(harness, tmp_path)
    recording = Intercept(site, lambda m, t: apply)

    results = harness.measure_task_sort(
        site=recording, saved_data=saved_data, timer=Ticks(0.0, 0.7)
    )

    assert len(recording.requests) == 1
    assert [r.created for r in results] == [False, False, False]
    assert [r.seconds for r in results] == [pytest.approx(0.7), 0.0, pytest.approx(0.7)]
    capsys.readouterr()
    assert harness.verdict(results, LIMIT) == 1
    assert capsys.readouterr().out.splitlines() == [
        "sort a task list at 1000 tasks: 700.0 ms — refused or failed",
        "sort landing page at 1000 tasks: 0.0 ms — refused or failed",
        "sort total at 1000 tasks: 700.0 ms — refused or failed",
    ]


def _sort_landing_cases(ids: list[int]) -> dict[str, Response]:
    swapped = [ids[0], ids[2], ids[1], *ids[3:]]
    return {
        "a refusal page": _page('<p id="sort-field-reason">No.</p>'),
        "a failure status with the right page": Response(500, (), _sort_page(ids).body),
        "two tasks swapped": _sort_page(swapped),
        "ascending order, the same set": _sort_page(list(reversed(ids))),
        "one task missing": _sort_page(ids[:-1], count=len(ids)),
        "a duplicate in place of a task": _sort_page([*ids[:-1], ids[0]]),
        "a duplicate added": _sort_page([*ids, ids[0]], count=len(ids)),
        "an extra identity": _sort_page([*ids, 1001], count=len(ids)),
        "a wrong displayed count": _sort_page(ids, count=len(ids) + 1),
        "no count line": _page(_sort_page(ids).body.decode().split("</p>", 1)[1]),
    }


def test_timed_sort_rejects_wrong_landing(harness: ModuleType, tmp_path: Path) -> None:
    """T13, CP-454: each wrong landing fails the landing and the total, never the Apply; the
    correctly ordered page passes, and set equality alone does not."""
    _, _, loaded = _sort_fixture(harness, tmp_path / "ids")
    ids = _sorted_ids(loaded)
    assert len(ids) == 1000
    for name, landing in _sort_landing_cases(ids).items():
        site, saved_data, _ = _sort_fixture(harness, tmp_path / name.replace(" ", "-"))
        results = harness.measure_task_sort(
            site=Intercept(site, _second_get(landing)), saved_data=saved_data, timer=Ticks(*QUICK)
        )
        assert [r.created for r in results] == [True, False, False], name
        assert harness.verdict(results, LIMIT) == 1, name
    site, saved_data, _ = _sort_fixture(harness, tmp_path / "control")
    results = harness.measure_task_sort(
        site=Intercept(site, _second_get(_sort_page(ids))),
        saved_data=saved_data,
        timer=Ticks(*QUICK),
    )
    assert [r.created for r in results] == [True, True, True]


class _SlowSavedData:
    """The saved data, handed to the measurement in place of the real one, where every reach for
    its location (each readback of the saved bytes) costs 50 seconds on the shared clock."""

    def __init__(self, saved_data: SavedData, clock: list[float]) -> None:
        self._saved_data = saved_data
        self._clock = clock

    @property
    def location(self) -> Path:
        self._clock[0] += 50.0
        return self._saved_data.location

    def load(self):
        return self._saved_data.load()


def test_timed_sort_detects_saved_byte_changes_during_either_read(
    harness: ModuleType, tmp_path: Path
) -> None:
    """T12, T13, CP-454: equivalent data with other bytes fails, whether it changed at Apply or at
    the landing; the byte reads never lengthen either measured interval."""
    site, saved_data, loaded = _sort_fixture(harness, tmp_path / "apply")
    recording = Intercept(site)

    def at_apply(method: str, target: str) -> Response | None:
        if len(recording.requests) == 1:
            _rewritten_bytes(saved_data)
        return None

    recording = Intercept(site, at_apply)
    results = harness.measure_task_sort(site=recording, saved_data=saved_data, timer=Ticks(*QUICK))
    assert saved_data.load() == loaded
    assert [r.created for r in results] == [False, False, False]
    assert len(recording.requests) == 1

    site, saved_data, loaded = _sort_fixture(harness, tmp_path / "landing")

    def at_landing(method: str, target: str) -> Response | None:
        if len(recording.requests) == 2:
            _rewritten_bytes(saved_data)
        return None

    recording = Intercept(site, at_landing)
    results = harness.measure_task_sort(site=recording, saved_data=saved_data, timer=Ticks(*QUICK))
    assert saved_data.load() == loaded
    assert [r.created for r in results] == [True, False, False]
    assert harness.verdict(results, LIMIT) == 1

    site, saved_data, _ = _sort_fixture(harness, tmp_path / "intervals")
    clock = [0.0]

    def advance(method: str, target: str) -> Response | None:
        clock[0] += 0.1
        return None

    results = harness.measure_task_sort(
        site=Intercept(site, advance),
        saved_data=_SlowSavedData(saved_data, clock),
        timer=lambda: clock[0],
    )
    assert [r.seconds for r in results] == [
        pytest.approx(0.1),
        pytest.approx(0.1),
        pytest.approx(0.2),
    ]
    assert all(r.created for r in results)


SORT_REJECTIONS = {
    "refused apply": lambda site, saved_data: Intercept(site, lambda m, t: _page("<p>no</p>")),
    "inexact landing": lambda site, saved_data: Intercept(
        site, lambda m, t: _sort_page([1]) if t == SORT_ADDRESS else None
    ),
    "changed bytes": lambda site, saved_data: Intercept(
        site, lambda m, t: _rewritten_bytes(saved_data)
    ),
}


@pytest.mark.parametrize("rejection", SORT_REJECTIONS.values(), ids=SORT_REJECTIONS.keys())
def test_timed_sort_failures_reach_main_verdict(
    harness: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    rejection: Callable,
) -> None:
    """T13, CP-454: each rejection class makes the complete harness return non-zero while every
    earlier action passes."""
    measure = harness.measure_task_sort

    def rejected(*, site, saved_data, timer):
        return measure(site=rejection(site, saved_data), saved_data=saved_data, timer=timer)

    monkeypatch.setattr(harness, "measure_task_sort", rejected)

    status = harness.main(tmp_path, _run_readings())

    lines = capsys.readouterr().out.splitlines()
    assert status == 1
    assert [line for line in lines[-13:-10] if "refused or failed" in line]
    assert not [line for line in lines[:-14] if "refused" in line or "over" in line]
    assert not [line for line in lines[-10:] if "refused" in line or "over" in line]


def test_full_run_keeps_the_sort_block_before_the_summary_block(
    harness: ModuleType, whole_run, tmp_path: Path
) -> None:
    """T12, CP-452: every earlier line in its place and unchanged, then the sort's four lines, with
    only the Summary's two and the deletion's four after them."""
    _, status, lines, _, _ = whole_run
    _, fresh = harness.open_task_volume(SavedData(tmp_path / "fresh"))

    assert status == 0
    assert [line.split(":")[0] for line in lines] == [
        *OLD_RUN_LABELS,
        *NEW_RUN_LABELS,
        *MOVE_RUN_LABELS,
        *FILTER_RUN_LABELS,
        *SORT_RUN_LABELS,
        *SUMMARY_RUN_LABELS,
        *DELETE_RUN_LABELS,
        *RENAME_RUN_LABELS,
    ]
    assert lines[-14:-10] == [
        harness.sort_fixture_report(fresh),
        "sort a task list at 1000 tasks: 100.0 ms",
        "sort landing page at 1000 tasks: 100.0 ms",
        "sort total at 1000 tasks: 200.0 ms",
    ]
    assert lines[-14].endswith("sort priority descending, 1000 listed")


# --- The project Summary appended to the whole run (CP-503, CP-509) -------------------------------

SUMMARY_ADDRESS = "/projects/1/summary"
# The test's own reader of a count cell, which is a bare numeral or the numeral inside one anchor
# (the real page's anchor carries a class, an address and an accessible name). It is written apart
# from the harness's reader and shares nothing with it.
SUMMARY_ROW = re.compile(
    r'<tr><th scope="row" class="pre-wrap">(.*?)</th>'
    r"<td>(<a [^>]*>)?([0-9]+)(</a>)?</td></tr>"
)
REAL_COUNT_ANCHOR = re.compile(
    r'<td><a class="count-link" href="([^"]*)" aria-label="([^"]*)">([0-9]+)</a></td>'
)
SUMMARY_HEADINGS = (
    "Tasks by status",
    "Tasks by priority",
    "Due dates",
    "Open tasks by assignee",
)
STATUS_WORDS = ("todo", "in-progress", "done", "cancelled")
OPEN_STATUS_WORDS = ("todo", "in-progress")
PRIORITY_WORDS = ("low", "medium", "high", "critical")
SUMMARY_HARNESS_TEXT = (TESTS_DIRECTORY / "timed_run.py").read_text(encoding="utf-8")


def _local_today() -> date:
    return datetime.now().astimezone().date()


def _summary_oracle(state, today: date) -> list[tuple[str, int]]:
    """The rows the Summary of project 1 must show, worked out here by plain comparison of each
    task: never by the product's Summary, its project filter or its application read."""
    held = [t for t in state.tasks if t.project_id == 1]
    open_tasks = [t for t in held if t.status.value in OPEN_STATUS_WORDS]
    rows = [("Total", len(held))]
    rows += [(word, sum(t.status.value == word for t in held)) for word in STATUS_WORDS]
    rows += [(word, sum(t.priority.value == word for t in held)) for word in PRIORITY_WORDS]
    rows.append(("Overdue", sum(1 for t in open_tasks if t.due_date and t.due_date < today)))
    rows.append(("No due date", sum(1 for t in held if t.due_date is None)))
    listed = list(state.assignees)
    unlisted = sorted(
        {t.assignee for t in open_tasks if t.assignee is not None} - set(listed),
        key=lambda name: (name.casefold(), name),
    )
    rows += [(name, sum(t.assignee == name for t in open_tasks)) for name in [*listed, *unlisted]]
    rows.append(("(unassigned)", sum(t.assignee is None for t in open_tasks)))
    return rows


def _summary_row(label: str, count: int) -> str:
    return f'<tr><th scope="row" class="pre-wrap">{escape(label)}</th><td>{count}</td></tr>'


# The nine count cells that may hold an anchor, by the group that holds them. The rest of the page
# (the total, no due date, every assignee count and every label) may not.
SELECTED_COUNT_ROWS = {
    "Tasks by status": STATUS_WORDS,
    "Tasks by priority": PRIORITY_WORDS,
    "Due dates": ("Overdue",),
}


SELECTED_CELLS = {(h, label) for h, labels in SELECTED_COUNT_ROWS.items() for label in labels}


def _count_href(label: str) -> str:
    if label == "Overdue":
        return "/projects/1?filter_overdue=on"
    field = "filter_status" if label in STATUS_WORDS else "filter_priority"
    return f"/projects/1?{field}={label}"


def _in_group(body: str, heading: str, edit: Callable[[str], str]) -> str:
    """The body with `edit` applied to the one group under this heading; the edit must change it."""
    start = body.index(f"<h2>{heading}</h2>")
    end = body.index("</section>", start)
    changed = edit(body[start:end])
    assert changed != body[start:end], f"nothing changed in {heading}"
    return body[:start] + changed + body[end:]


def _edit_cell(
    body: str, heading: str, label: str, inner: Callable[[str], str], occurrences: int = 1
) -> str:
    """The body with the content of this label's count cell, in this group, replaced by
    `inner(old content)`; the first such row, or every one when `occurrences` is 0. The row is
    located by its group and label, never by the number."""
    pattern = (
        rf'(<tr><th scope="row" class="pre-wrap">{re.escape(escape(label))}</th><td>)'
        r"(.*?)(</td></tr>)"
    )
    return _in_group(
        body,
        heading,
        lambda section: re.sub(
            pattern, lambda m: m[1] + inner(m[2]) + m[3], section, count=occurrences
        ),
    )


def _unlink_selected_counts(body: str) -> str:
    """The real linked page projected to bare counts: each of its nine anchored count cells made a
    bare numeral, the rest untouched. This is the second accepted shape; the real page is the
    first."""
    bare, replaced = REAL_COUNT_ANCHOR.subn(lambda m: f"<td>{m[3]}</td>", body)
    assert replaced == 9 and "</a></td>" not in bare
    return bare


def _served_linked(body: str) -> str:
    """The real page as served: nine anchored count cells, in the selected rows only."""
    assert len(REAL_COUNT_ANCHOR.findall(body)) == 9
    return body


def _set_count(body: str, heading: str, label: str, count: int) -> str:
    """The body with this row's numeral replaced, whether the cell is bare or anchored."""
    return _edit_cell(
        body,
        heading,
        label,
        lambda old: re.sub(r"(^|>)[0-9]+($|<)", lambda m: f"{m[1]}{count}{m[2]}", old, count=1),
    )


def _drop_row(body: str, heading: str, label: str) -> str:
    """The body without this row of this group."""
    pattern = rf'<tr><th scope="row" class="pre-wrap">{re.escape(escape(label))}</th>.*?</tr>'
    return _in_group(body, heading, lambda section: re.sub(pattern, "", section, count=1))


SUMMARY_SHAPES = {"bare": _unlink_selected_counts, "linked": _served_linked}


def _summary_fixture(harness: ModuleType, location: Path, state=None):
    """The real site over a small Summary fixture (or the given state), saved and loaded."""
    chosen = _shrunk(harness.summary_state(), tasks=120, comments=2) if state is None else state
    return _move_fixture(harness, location, chosen)


def _real_summary(harness: ModuleType, site) -> Response:
    return site.handle("GET", SUMMARY_ADDRESS, harness.FILTER_HEADERS, b"")


def _edited(response: Response, edit: Callable[[str], str]) -> Response:
    body = edit(response.body.decode("utf-8")).encode("utf-8")
    return Response(response.status, response.headers, body)


@pytest.mark.parametrize("shape", SUMMARY_SHAPES)
def test_summary_oracle_reads_the_real_page_as_the_fixture_says(
    harness: ModuleType, tmp_path: Path, shape: str
) -> None:
    """CP-503, CP-509, CP-527, T14: the test's own oracle and the page agree on the fixture, in
    order, in both accepted shapes: the real page, with an anchor in each of the nine selected count
    cells, and its projection to bare counts. Only those nine cells hold an anchor in the linked
    shape, and each reaches the project's one-choice address."""
    site, _, loaded = _summary_fixture(harness, tmp_path)

    real = _real_summary(harness, site).body.decode("utf-8")
    body = SUMMARY_SHAPES[shape](real)

    found = SUMMARY_ROW.findall(body)
    rows = [(unescape(label), int(count)) for label, _, count, _ in found]
    assert rows == _summary_oracle(loaded, _local_today())
    assert re.findall(r"<h2>(.*?)</h2>", body) == list(SUMMARY_HEADINGS)
    assert len({count for _, count in rows[1:5]}) > 1 and len(rows) > 14
    linked = [unescape(label) for label, opened, _, closed in found if opened and closed]
    nine = [*STATUS_WORDS, *PRIORITY_WORDS, "Overdue"]
    assert linked == ([] if shape == "bare" else nine)
    assert (body != real) == (shape == "bare")
    addresses = [unescape(m[0]) for m in REAL_COUNT_ANCHOR.findall(body)]
    assert addresses == ([] if shape == "bare" else [_count_href(label) for label in nine])


def test_timed_summary_reads_real_full_volume_once(harness: ModuleType, tmp_path: Path) -> None:
    """T14, CP-509: a real Summary over the loaded 1,000 by 20 fixture passes, and the handed-in
    recorder sees exactly one same-origin GET of the target Summary."""
    saved_data = SavedData(tmp_path / "volume")
    site, loaded = harness.open_summary_volume(saved_data)
    assert len(loaded.tasks) == 1000
    assert [len(task.comments) for task in loaded.tasks] == [20] * 1000
    recording = Intercept(site)

    results = harness.measure_project_summary(
        site=recording, saved_data=saved_data, timer=Ticks(*SUMMARY_QUICK)
    )

    assert [(m, t) for m, t, _, _ in recording.requests] == [("GET", SUMMARY_ADDRESS)]
    _, _, headers, body = recording.requests[0]
    assert headers["Sec-Fetch-Site"] == "same-origin" and body == b""
    assert [(r.label, r.created) for r in results] == [(SUMMARY_LABEL, True)]
    assert harness.verdict(results, LIMIT) == 0


def _created(harness: ModuleType, site, saved_data: SavedData, response: Response) -> bool:
    """Whether the measurement counts this response, served in place of the real Summary."""
    results = harness.measure_project_summary(
        site=Intercept(site, lambda method, target: response),
        saved_data=saved_data,
        timer=Ticks(*SUMMARY_QUICK),
    )
    assert len(results) == 1
    return results[0].created


@pytest.mark.parametrize("empty", [False, True], ids=["varied fixture", "empty fixture"])
def test_timed_summary_accepts_bare_and_selected_linked_counts(
    harness: ModuleType, tmp_path: Path, empty: bool
) -> None:
    """T14, CP-509, CP-527: the measurement counts the real Summary, with an anchor in each of the
    four status, four priority and the overdue count cells, and the same page with those cells bare,
    with the group, label and count of every row agreeing in order. On an empty fixture all nine
    counts are zero, and the nine anchors still pass."""
    state = _shrunk(harness.summary_state(), tasks=120, comments=2)
    state = replace(state, tasks=()) if empty else state
    site, saved_data, loaded = _summary_fixture(harness, tmp_path, state)
    linked = _real_summary(harness, site)
    bare = _edited(linked, _unlink_selected_counts)

    assert linked.body != bare.body
    assert linked.body.decode("utf-8").count("</a></td>") == 9
    for response in (bare, linked):
        found = SUMMARY_ROW.findall(response.body.decode("utf-8"))
        assert [(unescape(label), int(count)) for label, _, count, _ in found] == _summary_oracle(
            loaded, _local_today()
        )
        assert _created(harness, site, saved_data, response)
    if empty:
        assert {count for _, count in _summary_oracle(loaded, _local_today())} == {0}
        assert linked.body.decode("utf-8").count('">0</a></td>') == 9


LOOKALIKES = ("todo", "low", "Overdue", "(unassigned)")
LOOKALIKE_LAYOUTS = {
    "todo and (unassigned) listed": ("todo", "(unassigned)"),
    "low and Overdue listed": ("low", "Overdue"),
}
OUTSIDE_THE_NINE = [
    ("Tasks by status", "Total"),
    ("Due dates", "No due date"),
]


@pytest.mark.parametrize("layout", LOOKALIKE_LAYOUTS)
def test_timed_summary_forbids_links_outside_selected_count_cells(
    harness: ModuleType, tmp_path: Path, layout: str
) -> None:
    """T15, CP-514, CP-527: an anchor in the total, the no-due-date count, any assignee count or
    any row label fails the measurement, in the linked shape. Assignees spelled `todo`, `low`,
    `Overdue` and `(unassigned)`, listed or not, sit beside the real categories and the real
    unassigned bucket: the page that links only the nine real cells passes, and an anchor on an
    assignee of the same name fails, so a cell is told by its group and row, not its label."""
    listed = LOOKALIKE_LAYOUTS[layout]
    state = _shrunk(harness.summary_state(), tasks=120, comments=2)
    for number, name in enumerate(LOOKALIKES, start=1):
        state = _with_task(state, number, status=TaskStatus.TODO, assignee=name)
    state = replace(state, assignees=listed)
    site, saved_data, loaded = _summary_fixture(harness, tmp_path, state)
    linked = _real_summary(harness, site)
    bare = _edited(linked, _unlink_selected_counts)
    oracle = _summary_oracle(loaded, _local_today())
    assignees = oracle[oracle.index(("No due date", dict(oracle)["No due date"])) + 1 :]
    assert set(LOOKALIKES) <= {label for label, _ in assignees}
    assert [label for label, _ in assignees].count("(unassigned)") == 2

    assert _created(harness, site, saved_data, bare)
    assert _created(harness, site, saved_data, linked)

    def anchored(old: str) -> str:
        return f'<a href="/projects/1">{old}</a>'

    cells = [*OUTSIDE_THE_NINE, *[("Open tasks by assignee", label) for label, _ in assignees]]
    for heading, label in cells:
        edited = _edited(
            linked, lambda t, h=heading, label=label: _edit_cell(t, h, label, anchored, 0)
        )
        assert edited.body != linked.body, (heading, label)
        assert not _created(harness, site, saved_data, edited), (heading, label)
    every_label = [
        (heading, label)
        for heading, rows in (
            ("Tasks by status", ["Total", *STATUS_WORDS]),
            ("Tasks by priority", PRIORITY_WORDS),
            ("Due dates", ["Overdue", "No due date"]),
            ("Open tasks by assignee", [label for label, _ in assignees]),
        )
        for label in rows
    ]
    for heading, label in every_label:
        cell = f'class="pre-wrap">{escape(label)}</th>'
        edited = _edited(
            linked,
            lambda t, h=heading, cell=cell, label=label: _in_group(
                t,
                h,
                lambda section: section.replace(
                    cell, f'class="pre-wrap"><a href="/projects/1">{escape(label)}</a></th>'
                ),
            ),
        )
        assert edited.body != linked.body, (heading, label)
        assert not _created(harness, site, saved_data, edited), (heading, label)


AMBIGUOUS_COUNT_CELLS = {
    "two anchors": lambda n, href: f'<a href="{href}">{n}</a><a href="{href}">{n}</a>',
    "an anchor and trailing text": lambda n, href: f'<a href="{href}">{n}</a> more',
    "text before an anchor": lambda n, href: f'see <a href="{href}">{n}</a>',
    "nested markup in the anchor": lambda n, href: f'<a href="{href}"><b>{n}</b></a>',
    "markup around a bare numeral": lambda n, href: f"<b>{n}</b>",
    "a numeral and a second markup": lambda n, href: f"{n}<span>0</span>",
    "a numeral and a word": lambda n, href: f"{n} tasks",
    "a split numeral": lambda n, href: f'<a href="{href}">{n}</a>{n}',
    "an empty cell": lambda n, href: "",
    "an empty anchor": lambda n, href: f'<a href="{href}"></a>',
    "a nonnumeric anchor": lambda n, href: f'<a href="{href}">many</a>',
    "a nonnumeric bare cell": lambda n, href: "many",
    "a signed numeral": lambda n, href: f"-{n}",
}
AMBIGUOUS_TARGETS = [
    ("Tasks by status", "todo"),
    ("Tasks by status", "cancelled"),
    ("Tasks by priority", "high"),
    ("Due dates", "Overdue"),
    ("Tasks by status", "Total"),
    ("Due dates", "No due date"),
]


@pytest.mark.parametrize("variant", AMBIGUOUS_COUNT_CELLS)
def test_timed_summary_rejects_ambiguous_count_cells(
    harness: ModuleType, tmp_path: Path, variant: str
) -> None:
    """T15, CP-514, CP-527, design 4 B: a count cell that is not one bare numeral, or one anchor
    holding one numeral, fails the measurement, in a selected cell and in a plain one. No digit
    substring is recovered from extra markup, extra text or a second anchor, and no group loses
    its identity because the cell's markup was stripped. In every case the edited page differs from
    the page it was made from."""
    site, saved_data, _ = _summary_fixture(harness, tmp_path)
    linked = _real_summary(harness, site)
    bare = _edited(linked, _unlink_selected_counts)
    assert _created(harness, site, saved_data, linked)

    for heading, label in AMBIGUOUS_TARGETS:
        href = _count_href(label) if (heading, label) in SELECTED_CELLS else "/projects/1"

        def make(old: str, href: str = href) -> str:
            numeral = re.search(r"[0-9]+", old)
            assert numeral is not None
            return AMBIGUOUS_COUNT_CELLS[variant](numeral[0], href)

        for page in (bare, linked):
            edited = _edited(page, lambda t, h=heading, label=label: _edit_cell(t, h, label, make))
            assert edited.body != page.body, (variant, heading, label)
            assert not _created(harness, site, saved_data, edited), (variant, heading, label)


@pytest.mark.parametrize(
    "readings,failing",
    [
        ((0.0, 0.1), False),
        ((0.0, 0.99996), False),
        ((0.0, 1.0), True),
        ((5.0, 6.0), True),
        ((0.0, 1.5), True),
    ],
    ids=["fast", "just below 1 s", "exactly 1 s", "exactly 1 s later", "1.5 s"],
)
def test_timed_summary_enforces_the_strict_one_second_limit(
    harness: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    readings: tuple[float, float],
    failing: bool,
) -> None:
    """T14, CP-509: one measurement, passing strictly below 1 second, failing at it and above."""
    site, saved_data, _ = _summary_fixture(harness, tmp_path)

    results = harness.measure_project_summary(
        site=site, saved_data=saved_data, timer=Ticks(*readings)
    )

    assert [(r.label, r.created) for r in results] == [(SUMMARY_LABEL, True)]
    assert results[0].seconds == pytest.approx(readings[1] - readings[0])
    capsys.readouterr()
    assert harness.verdict(results, LIMIT) == (1 if failing else 0)
    assert ("over" in capsys.readouterr().out) == failing


def _summary_rejections(harness: ModuleType, site, saved_data, loaded, shape: str = "bare"):
    """Each way a fast answer is still wrong, as the Intercept that serves it, over the page in
    this shape. Each wrong answer is the real page in that shape with one edit, located by its group
    and label, and it must differ from the real page."""
    real = _edited(_real_summary(harness, site), SUMMARY_SHAPES[shape])
    oracle = dict(_summary_oracle(loaded, _local_today()))
    todo, total = oracle["todo"], oracle["Total"]
    name = loaded.projects[0].name
    page_headers = real.headers

    def serve(response: Response) -> Intercept:
        return Intercept(site, lambda method, target: response)

    def wrong(edit: Callable[[str], str]) -> Intercept:
        edited = _edited(real, edit)
        assert edited.body != real.body
        return serve(edited)

    return {
        "the Tasks view instead": serve(
            site.handle("GET", "/projects/1", harness.FILTER_HEADERS, b"")
        ),
        "another project's Summary": wrong(lambda t: t.replace(name, "Other project")),
        "a heading of another project": wrong(
            lambda t: t.replace(
                f'<h1 class="pre-wrap">{escape(name)}</h1>', '<h1 class="pre-wrap">Other</h1>'
            )
        ),
        "a missing group heading": wrong(lambda t: t.replace("<h2>Due dates</h2>", "")),
        "a title of another view": wrong(
            lambda t: t.replace(": Summary - tracker17", ": Tasks - tracker17")
        ),
        "a project not found": serve(
            site.handle("GET", "/projects/99/summary", harness.FILTER_HEADERS, b"")
        ),
        "a body that is not HTML": serve(
            Response(200, (("Content-Type", "text/plain"),), real.body)
        ),
        "forbidden": serve(Response(403, page_headers, real.body)),
        "failed": serve(Response(500, page_headers, real.body)),
        "a redirect": serve(Response(303, (("Location", "/projects/1"),), b"")),
        "a missing row": wrong(lambda t: _drop_row(t, "Due dates", "Overdue")),
        "a wrong count": wrong(lambda t: _set_count(t, "Tasks by status", "todo", todo + 1)),
        "a linked count": wrong(
            lambda t: t.replace(
                f"<td>{total}</td>", f'<td><a href="/projects/1">{total}</a></td>', 1
            )
        ),
        "a linked label": wrong(
            lambda t: t.replace(
                '<th scope="row" class="pre-wrap">Total</th>',
                '<th scope="row" class="pre-wrap"><a href="/projects/1">Total</a></th>',
            )
        ),
        "changed saved bytes": Intercept(site, lambda method, target: _rewritten_bytes(saved_data)),
    }


SUMMARY_REJECTION_NAMES = (
    "the Tasks view instead",
    "another project's Summary",
    "a heading of another project",
    "a missing group heading",
    "a title of another view",
    "a project not found",
    "a body that is not HTML",
    "forbidden",
    "failed",
    "a redirect",
    "a missing row",
    "a wrong count",
    "a linked count",
    "a linked label",
    "changed saved bytes",
)


@pytest.mark.parametrize("shape", SUMMARY_SHAPES)
@pytest.mark.parametrize("rejection", SUMMARY_REJECTION_NAMES)
def test_timed_summary_rejects_fast_incorrect_responses(
    harness: ModuleType, tmp_path: Path, rejection: str, shape: str
) -> None:
    """T14, T15, CP-503, CP-509, CP-514, CP-527: each wrong answer fails the measurement even with a
    fast timer, whether the page it was made from has bare counts or the selected anchored ones."""
    site, saved_data, loaded = _summary_fixture(harness, tmp_path)
    served = _summary_rejections(harness, site, saved_data, loaded, shape)[rejection]

    results = harness.measure_project_summary(
        site=served, saved_data=saved_data, timer=Ticks(*SUMMARY_QUICK)
    )

    assert [(r.label, r.created) for r in results] == [(SUMMARY_LABEL, False)]
    assert results[0].seconds == pytest.approx(0.1)
    assert harness.verdict(results, LIMIT) == 1


def _swapped_counts(
    heading: str, first: tuple[str, int], second: tuple[str, int]
) -> Callable[[str], str]:
    """The edit that gives each of two rows of one group the other's count, whichever shape the
    cells are in."""
    (a, count_a), (b, count_b) = first, second
    assert count_a != count_b

    def edit(text: str) -> str:
        return _set_count(_set_count(text, heading, a, count_b), heading, b, count_a)

    return edit


@pytest.mark.parametrize("shape", SUMMARY_SHAPES)
def test_timed_summary_validates_rows_independently(
    harness: ModuleType, tmp_path: Path, shape: str
) -> None:
    """T14, CP-509, CP-527: equal totals do not pass. A page whose category counts or assignee rows
    differ from what the loaded fixture holds fails, in both accepted shapes, and the expectation is
    worked out from the loaded saved data and never from the Summary, the project filter or the
    application read. Each edit is located by its group and label and must change the page."""
    site, saved_data, loaded = _summary_fixture(harness, tmp_path / "rows")
    real = _edited(_real_summary(harness, site), SUMMARY_SHAPES[shape])
    oracle = _summary_oracle(loaded, _local_today())
    named = [(label, count) for label, count in oracle if label in (*STATUS_WORDS,)]
    priorities = [(label, count) for label, count in oracle if label in PRIORITY_WORDS]
    assignees = oracle[oracle.index(("No due date", dict(oracle)["No due date"])) + 1 :]
    assert len(assignees) >= 3
    assignee_group = "Open tasks by assignee"
    wrong = {
        "two status counts swapped": _swapped_counts("Tasks by status", named[0], named[1]),
        "two priority counts swapped": _swapped_counts(
            "Tasks by priority", priorities[0], priorities[1]
        ),
        "two assignee counts swapped": _swapped_counts(assignee_group, assignees[0], assignees[1]),
        "an assignee name in another case": lambda t: t.replace(
            _summary_row(assignees[1][0], assignees[1][1]),
            _summary_row(assignees[1][0].swapcase(), assignees[1][1]),
        ),
        "two assignee rows in the other order": lambda t: t.replace(
            _summary_row(*assignees[0]) + "\n" + _summary_row(*assignees[1]),
            _summary_row(*assignees[1]) + "\n" + _summary_row(*assignees[0]),
        ),
        "the unassigned row missing": lambda t: t.replace(_summary_row(*assignees[-1]), ""),
    }
    for name, edit in wrong.items():
        edited = _edited(real, edit)
        assert edited.body != real.body, name
        results = harness.measure_project_summary(
            site=Intercept(site, lambda method, target, edited=edited: edited),
            saved_data=saved_data,
            timer=Ticks(*SUMMARY_QUICK),
        )
        assert [r.created for r in results] == [False], name
    control = harness.measure_project_summary(
        site=Intercept(site, lambda method, target: real),
        saved_data=saved_data,
        timer=Ticks(*SUMMARY_QUICK),
    )
    assert [r.created for r in control] == [True]

    other_site, other_data, other = _summary_fixture(harness, tmp_path / "other")
    served = _edited(_real_summary(harness, other_site), SUMMARY_SHAPES[shape])
    changed = _with_task(other, 1, status=TaskStatus.CANCELLED, assignee=None)
    assert changed != other
    other_data.save(changed)
    stale = harness.measure_project_summary(
        site=Intercept(other_site, lambda method, target: served),
        saved_data=other_data,
        timer=Ticks(*SUMMARY_QUICK),
    )
    assert [r.created for r in stale] == [False]

    oracle_names = r"(?<![A-Za-z_])(summarize_project|project_summary|filter_project_tasks)\b"
    assert re.findall(oracle_names, SUMMARY_HARNESS_TEXT) == []


def test_timed_summary_checks_fixture_and_saved_bytes_outside_the_interval(
    harness: ModuleType, tmp_path: Path
) -> None:
    """T14, CP-509: only the GET lies between the two readings, and no byte readback or fixture
    load lengthens the measured interval, however long it takes."""
    site, saved_data, _ = _summary_fixture(harness, tmp_path / "events")
    log = EventLog()

    results = harness.measure_project_summary(
        site=log.site(site), saved_data=saved_data, timer=log.timer(0.0, 0.1)
    )

    assert log.events == ["tick", "GET", "tick"]
    assert [r.created for r in results] == [True]

    site, saved_data, _ = _summary_fixture(harness, tmp_path / "intervals")
    clock = [0.0]

    def advance(method: str, target: str) -> Response | None:
        clock[0] += 0.1
        return None

    results = harness.measure_project_summary(
        site=Intercept(site, advance),
        saved_data=_SlowSavedData(saved_data, clock),
        timer=lambda: clock[0],
    )
    assert [r.seconds for r in results] == [pytest.approx(0.1)]
    assert [r.created for r in results] == [True]

    for name in ("forbidden", "a wrong count", "changed saved bytes"):
        site, saved_data, loaded = _summary_fixture(harness, tmp_path / name)
        served = _summary_rejections(harness, site, saved_data, loaded)[name]
        results = _measured_with_slow_readbacks(harness, served, saved_data)
        assert [r.seconds for r in results] == [pytest.approx(0.1)], name
        assert [r.created for r in results] == [False], name


class _SlowGet:
    """A site whose every request takes 0.1 s on the shared clock, whatever answers it."""

    def __init__(self, inner: Intercept, clock: list[float]) -> None:
        self._inner = inner
        self._clock = clock

    def handle(self, method: str, target: str, headers: dict[str, str], body: bytes) -> Response:
        self._clock[0] += 0.1
        return self._inner.handle(method, target, headers, body)


def _measured_with_slow_readbacks(harness: ModuleType, served: Intercept, saved_data: SavedData):
    """The measurement over a site whose GET takes 0.1 s and whose every readback takes 50 s."""
    clock = [0.0]
    return harness.measure_project_summary(
        site=_SlowGet(served, clock),
        saved_data=_SlowSavedData(saved_data, clock),
        timer=lambda: clock[0],
    )


@pytest.mark.parametrize("shape", SUMMARY_SHAPES)
def test_timed_summary_accepts_a_run_that_crosses_midnight(
    harness: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, shape: str
) -> None:
    """T14, CP-497, CP-509, CP-527: the overdue row is counted on the local day, so a GET answered
    on either of the two days that bracket the request passes with that day's row, and a row that
    fits neither day fails. The edited cell is the overdue count, anchored in the linked shape."""
    site, saved_data, loaded = _summary_fixture(harness, tmp_path)
    real = _edited(_real_summary(harness, site), SUMMARY_SHAPES[shape])
    first, next_day = date(2000, 1, 1), date(2000, 1, 2)
    overdue_first = dict(_summary_oracle(loaded, first))["Overdue"]
    overdue_next = dict(_summary_oracle(loaded, next_day))["Overdue"]
    assert overdue_first != overdue_next

    shown_now = {
        unescape(label): int(count)
        for label, _, count, _ in SUMMARY_ROW.findall(real.body.decode("utf-8"))
    }["Overdue"]

    def with_overdue(count: int) -> Response:
        """The real page showing this overdue count; the page itself when it shows it already."""
        if count == shown_now:
            return real
        edited = _edited(real, lambda t: _set_count(t, "Due dates", "Overdue", count))
        assert edited.body != real.body
        return edited

    earlier = with_overdue(overdue_first)
    later = with_overdue(overdue_next)
    neither = with_overdue(overdue_first + overdue_next + 1)
    for page in (earlier, later, neither):
        shown = f'href="{_count_href("Overdue")}"'
        assert (shown in page.body.decode("utf-8")) == (shape == "linked")
    assert neither.body != real.body and neither.body not in (earlier.body, later.body)
    assert earlier.body != later.body

    def passes(days: tuple[date, date], page: Response) -> bool:
        readings = iter(days)
        monkeypatch.setattr(harness, "_local_today", lambda: next(readings))
        return _created(harness, site, saved_data, page)

    assert passes((first, next_day), earlier) and passes((first, next_day), later)
    assert not passes((first, next_day), neither)
    assert passes((first, first), earlier) and not passes((first, first), later)
    assert passes((next_day, next_day), later) and not passes((next_day, next_day), earlier)
    assert not passes((first, first), neither)


def test_timed_run_appends_summary_after_all_existing_blocks(
    harness: ModuleType, whole_run, tmp_path: Path
) -> None:
    """T15, CP-509, Locked Answer f-4: every older block keeps its labels and place, and only the
    published Summary fixture and result lines follow, the fixture description first, and then
    the deletion's four."""
    directory, status, lines, before, after = whole_run
    summary_data = SavedData(directory / "summary-volume")
    loaded = summary_data.load()
    assert loaded is not None
    _, fresh = harness.open_summary_volume(SavedData(tmp_path / "fresh"))

    assert status == 0
    assert [line.split(":")[0] for line in lines[:-10]] == [
        *OLD_RUN_LABELS,
        *NEW_RUN_LABELS,
        *MOVE_RUN_LABELS,
        *FILTER_RUN_LABELS,
        *SORT_RUN_LABELS,
    ]
    assert loaded == fresh
    assert lines[-10:-8] == [
        harness.summary_fixture_report(fresh),
        f"{SUMMARY_LABEL}: 100.0 ms",
    ]
    earlier = {
        directory / name
        for name in (*EARLIER_FIXTURES, "move-volume", "filter-volume", "sort-volume")
    }
    assert summary_data.location not in earlier and summary_data.location.parent == directory
    assert after == before


SUMMARY_FAILURES = {
    "slow": lambda site, saved_data: site,
    "refused": lambda site, saved_data: Intercept(site, lambda m, t: _page("<p>no</p>")),
    "failed": lambda site, saved_data: Intercept(
        site, lambda m, t: Response(500, (("Content-Type", "text/html"),), b"<p>no</p>")
    ),
    "corrupt": lambda site, saved_data: Intercept(site, lambda m, t: _page("<html></html>")),
    "mutating": lambda site, saved_data: Intercept(site, lambda m, t: _rewritten_bytes(saved_data)),
}


@pytest.mark.parametrize("readings", [(0.0, 1.5), (0.0, 1.0)], ids=["slow", "at the limit"])
def test_timed_run_fails_on_a_slow_or_at_limit_summary(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str], readings
) -> None:
    """T15, CP-509: a Summary at or over 1 second alone makes the whole run exit non-zero."""
    status = harness.main(tmp_path, _run_readings(summary=readings))

    lines = capsys.readouterr().out.splitlines()
    assert status == 1
    assert [line.split(":")[0] for line in lines if "over" in line] == [SUMMARY_LABEL]


@pytest.mark.parametrize(
    "failure", ["refused", "failed", "corrupt", "mutating"], ids=lambda name: name
)
def test_timed_run_includes_summary_failure_in_exit_status(
    harness: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    """T15, CP-509: a refused, failed, corrupt or mutating Summary alone makes the full run exit
    non-zero, while every earlier status is unchanged."""
    measure = harness.measure_project_summary

    def rejected(*, site, saved_data, timer):
        return measure(
            site=SUMMARY_FAILURES[failure](site, saved_data), saved_data=saved_data, timer=timer
        )

    monkeypatch.setattr(harness, "measure_project_summary", rejected)

    status = harness.main(tmp_path, _run_readings())

    lines = capsys.readouterr().out.splitlines()
    assert status == 1
    assert "refused or failed" in lines[-9] and lines[-9].startswith(SUMMARY_LABEL)
    others = [*lines[:-9], *lines[-8:]]
    assert not [line for line in others if "refused" in line or "over" in line]


def test_summary_fixture_report_uses_loaded_volume_and_text_lengths(
    harness: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """T15, CP-509: volume, the first task's title and first comment and the timed project's
    name, all read back from the loaded fixture and counted in code points; nothing is printed."""
    _, _, standard = _summary_fixture(harness, tmp_path / "standard", harness.summary_state())
    first = find_task(standard, 1)
    assert first is not None
    assert harness.summary_fixture_report(standard) == (
        "summary fixture: 1000 tasks, 20 comments each (20000 in all); "
        f"title of {len(first.title)} characters, "
        f"comment of {len(first.comments[0].text)} characters; "
        f"project name of {len(standard.projects[0].name)} characters"
    )
    assert len(standard.projects[0].name) == 14

    shrunk = _shrunk(harness.summary_state(), tasks=300, comments=3)
    note = replace(find_task(shrunk, 1).comments[0], text="Note 😀")  # type: ignore[union-attr]
    varied = _with_task(
        shrunk,
        1,
        title="Plan 😀😀",
        comments=(note, *find_task(shrunk, 1).comments[1:]),  # type: ignore[union-attr]
    )
    varied = replace(
        varied,
        tasks=tuple(reversed(varied.tasks)),
        projects=(replace(varied.projects[0], name="Näme 😀"),),
    )
    _, _, loaded = _summary_fixture(harness, tmp_path / "varied", varied)
    assert loaded.tasks[0].id != 1
    capsys.readouterr()

    report = harness.summary_fixture_report(loaded)

    assert capsys.readouterr().out == ""
    assert report == (
        "summary fixture: 300 tasks, 3 comments each (900 in all); "
        "title of 7 characters, comment of 6 characters; project name of 6 characters"
    )
    uneven = _with_task(shrunk, 2, comments=find_task(shrunk, 2).comments[:1])  # type: ignore[union-attr]
    with pytest.raises(harness.FixtureShapeError):
        harness.summary_fixture_report(uneven)


def test_summary_fixture_is_varied_and_its_own(harness: ModuleType, tmp_path: Path) -> None:
    """CP-509: the Summary's fixture holds every status and priority, past-due and undated tasks
    and listed and unlisted assignees, so a swapped row cannot hide; it is built apart from the
    task-volume fixture."""
    state = harness.summary_state()
    held = [t for t in state.tasks if t.project_id == 1]

    assert {t.status.value for t in held} == set(STATUS_WORDS)
    assert {t.priority.value for t in held} == set(PRIORITY_WORDS)
    assert any(t.due_date is None for t in held)
    assert any(t.due_date == date(2000, 1, 1) for t in held)
    assert state.assignees
    named = {t.assignee for t in held if t.assignee is not None}
    assert set(state.assignees) < named
    assert state != harness.seeded_state()


# --- The task deletion appended to the whole run (CP-543; T15) -------------------------------------

DELETE_TASK = 500
DELETE_OPENING = f"/tasks/{DELETE_TASK}/delete"
DELETE_CONFIRMING = f"/tasks/{DELETE_TASK}/delete/confirm"
DELETE_WRONG_STATES = {
    "no deletion": lambda before, after: before,
    "comments retained": lambda before, after: replace(
        after,
        tasks=tuple(
            replace(t, comments=(*t.comments, *find_task(before, DELETE_TASK).comments))
            if t.id == DELETE_TASK + 1
            else t
            for t in after.tasks
        ),
    ),
    "another task removed": lambda before, after: replace(after, tasks=after.tasks[1:]),
    "another task field altered": lambda before, after: replace(
        after,
        tasks=(replace(after.tasks[0], title="Another title"), *after.tasks[1:]),
    ),
    "another task comment altered": lambda before, after: replace(
        after,
        tasks=(
            replace(after.tasks[0], comments=after.tasks[0].comments[:-1]),
            *after.tasks[1:],
        ),
    ),
    "project changed": lambda before, after: replace(
        after, projects=(replace(after.projects[0], name="Another project"),)
    ),
    "assignee list changed": lambda before, after: replace(after, assignees=("Avery Chen",)),
    "operator name changed": lambda before, after: replace(after, operator_name="Jordan Rivera"),
    "task counter changed": lambda before, after: replace(
        after, next_task_id=after.next_task_id + 1
    ),
    "project counter changed": lambda before, after: replace(
        after, next_project_id=after.next_project_id + 1
    ),
}


def _without_target(state):
    """The expected state, worked out here by dropping one task: its comments go with it."""
    return replace(state, tasks=tuple(t for t in state.tasks if t.id != DELETE_TASK))


def _delete_title(state) -> str:
    task = find_task(state, DELETE_TASK)
    assert task is not None
    return task.title


class AfterDelete:
    """The real site, with the saved state rewritten once the confirming request has been answered."""

    def __init__(self, site, saved_data: SavedData, change: Callable) -> None:
        self._site = site
        self._saved_data = saved_data
        self._change = change
        self._before = saved_data.load()

    def handle(self, method: str, target: str, headers: dict[str, str], body: bytes) -> Response:
        response = self._site.handle(method, target, headers, body)
        if method == "POST" and target == DELETE_CONFIRMING:
            after = self._saved_data.load()
            assert after is not None and self._before is not None
            self._saved_data.save(self._change(self._before, after))
        return response


def test_full_volume_deletion_measures_post_landing_and_total(
    harness: ModuleType, whole_run, tmp_path: Path
) -> None:
    """CP-543, T15: the fixture line states the volume and actual lengths, then three rows in order,
    each under the limit, and the whole run exits 0."""
    _, status, lines, _, _ = whole_run
    _, fresh = harness.open_task_volume(SavedData(tmp_path / "fresh"))
    task = find_task(fresh, DELETE_TASK)
    assert task is not None

    assert status == 0
    assert lines[-8:-4] == [
        (
            "delete fixture: 1000 tasks, 20 comments each (20000 in all); "
            f"title of {len(task.title)} characters, "
            f"comment of {len(task.comments[0].text)} characters"
        ),
        "delete a task at 1000 tasks: 100.0 ms",
        "delete landing page at 1000 tasks: 100.0 ms",
        "delete total at 1000 tasks: 200.0 ms",
    ]
    assert harness.delete_fixture_report(fresh) == lines[-8]

    site, saved_data, seeded = _seeded(harness, tmp_path / "one")
    results = harness.measure_task_delete(site=site, saved_data=saved_data, timer=Ticks(*QUICK))
    assert [(r.label, r.created) for r in results] == [(label, True) for label in DELETE_LABELS]
    assert [r.seconds for r in results] == pytest.approx([0.1, 0.1, 0.2])
    assert saved_data.load() == _without_target(seeded)


def test_delete_fixture_and_oracle_work_are_outside_the_intervals(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-543, T15: the opening press, the expected state and the saved readback sit outside the two
    timed requests, and the total is their sum without the gap between them."""
    site, saved_data, _ = _seeded(harness, tmp_path / "data")
    events: list[str] = []

    class Logged(Intercept):
        def handle(self, method, target, headers, body):  # type: ignore[no-untyped-def]
            events.append(f"{method} {target}")
            return super().handle(method, target, headers, body)

    class LoggedData:
        location = saved_data.location

        @staticmethod
        def load():  # type: ignore[no-untyped-def]
            events.append("load")
            return saved_data.load()

    readings = iter((0.0, 0.2, 5.0, 5.3))

    def timer() -> float:
        events.append("tick")
        return next(readings)

    results = harness.measure_task_delete(site=Logged(site), saved_data=LoggedData(), timer=timer)

    assert events.index("tick") > events.index(f"POST {DELETE_OPENING}")
    ticks = [i for i, event in enumerate(events) if event == "tick"]
    assert len(ticks) == 4
    assert events[ticks[0] + 1 : ticks[1]] == [f"POST {DELETE_CONFIRMING}"]
    assert events[ticks[1] + 1 : ticks[2]] == ["load"]
    assert [e.split(" ")[0] for e in events[ticks[2] + 1 : ticks[3]]] == ["GET"]
    assert [r.seconds for r in results] == pytest.approx([0.2, 0.3, 0.5])


def test_timed_delete_is_same_origin_and_a_real_change(
    harness: ModuleType, whole_run, tmp_path: Path
) -> None:
    """CP-543, T15: the confirming POST is marked same-origin and lands on the owning project with
    its completion; the saved file is exactly the fixture minus the task and its comments."""
    directory, _, _, _, _ = whole_run
    site, saved_data, seeded = _seeded(harness, tmp_path / "data")
    recording = Intercept(site)

    results = harness.measure_task_delete(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )

    assert all(r.created for r in results)
    opening, confirming, landing = recording.requests
    assert opening[:2] == ("POST", DELETE_OPENING)
    assert confirming[:2] == ("POST", DELETE_CONFIRMING)
    assert confirming[2]["Sec-Fetch-Site"] == "same-origin"
    title = _delete_title(seeded)
    assert landing[0] == "GET" and landing[1] == f"/projects/1?{urlencode({'deleted_task': title})}"
    assert saved_data.load() == _without_target(seeded)
    run_data = SavedData(directory / "delete-volume").load()
    assert run_data == _without_target(seeded)
    assert find_task(run_data, DELETE_TASK) is None  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "readings,expected",
    [
        ((0.0, 0.4, 5.0, 5.5), []),
        ((0.0, 1.0, 5.0, 5.1), [DELETE_LABELS[0], DELETE_LABELS[2]]),
        ((0.0, 0.1, 5.0, 6.0), [DELETE_LABELS[1], DELETE_LABELS[2]]),
        ((0.0, 0.5, 5.0, 5.5), [DELETE_LABELS[2]]),
        ((0.0, 1.5, 5.0, 5.1), [DELETE_LABELS[0], DELETE_LABELS[2]]),
    ],
    ids=["just below", "post exactly 1 s", "landing exactly 1 s", "sum exactly 1 s", "post over"],
)
def test_delete_time_limits_are_strict(
    harness: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    readings: tuple[float, float, float, float],
    expected: list[str],
) -> None:
    """CP-543, T15: each interval and the total are held to strictly below one second; equality
    fails, including two passing intervals whose sum reaches the limit."""
    status = harness.main(tmp_path, _run_readings(delete=readings))

    lines = capsys.readouterr().out.splitlines()
    assert [line.split(":")[0] for line in lines if "over" in line] == expected
    assert status == (1 if expected else 0)


@pytest.mark.parametrize("wrong", DELETE_WRONG_STATES.keys())
def test_timed_delete_rejects_wrong_saved_results(
    harness: ModuleType, tmp_path: Path, wrong: str
) -> None:
    """CP-543, T15: a saved state that is not exactly the fixture minus the task and its comments
    fails the deletion, and the landing's total with it. The oracle is built here, not by the rule."""
    site, saved_data, _ = _seeded(harness, tmp_path / "data")
    mutated = AfterDelete(site, saved_data, DELETE_WRONG_STATES[wrong])

    results = harness.measure_task_delete(site=mutated, saved_data=saved_data, timer=Ticks(*QUICK))

    assert not results[0].created
    assert not results[2].created


DELETE_REFUSALS = {
    "refused": lambda m, t: _page("<p>no</p>") if (m, t) == ("POST", DELETE_CONFIRMING) else None,
    "failed": lambda m, t: (
        Response(500, (("Content-Type", "text/html"),), b"<p>no</p>")
        if (m, t) == ("POST", DELETE_CONFIRMING)
        else None
    ),
    "another project": lambda m, t: (
        _found("/projects/2?deleted_task=x") if (m, t) == ("POST", DELETE_CONFIRMING) else None
    ),
    "a wrong title": lambda m, t: (
        _found("/projects/1?deleted_task=Another")
        if (m, t) == ("POST", DELETE_CONFIRMING)
        else None
    ),
    "the task page again": lambda m, t: (
        _found(f"/tasks/{DELETE_TASK}") if (m, t) == ("POST", DELETE_CONFIRMING) else None
    ),
}


@pytest.mark.parametrize("refusal", DELETE_REFUSALS.keys())
def test_timed_delete_rejects_refusal_failure_or_wrong_landing(
    harness: ModuleType, tmp_path: Path, refusal: str
) -> None:
    """CP-543, T15: a refused or failed action, a wrong redirect, project or title is not a
    passing duration; the landing is not requested, and the total fails."""
    site, saved_data, _ = _seeded(harness, tmp_path / "data")
    recording = Intercept(site, DELETE_REFUSALS[refusal])

    results = harness.measure_task_delete(
        site=recording, saved_data=saved_data, timer=Ticks(0.0, 0.1)
    )

    assert [r.created for r in results] == [False, False, False]
    assert [r.label for r in results] == list(DELETE_LABELS)
    assert not [r for r in recording.requests if r[0] == "GET"]


@pytest.mark.parametrize("landing", ["wrong status", "no completion", "wrong project"])
def test_timed_delete_landing_must_show_the_completion_on_the_project(
    harness: ModuleType, tmp_path: Path, landing: str
) -> None:
    """CP-543, T15: a landing that is not a 200, omits the completion line or is another project's
    page fails the landing row and the total; the POST row alone still counts."""
    site, saved_data, seeded = _seeded(harness, tmp_path / "data")
    line = escape(f"You deleted '{_delete_title(seeded)}'.")
    pages = {
        "wrong status": Response(404, (("Content-Type", "text/html"),), b"<p>no</p>"),
        "no completion": _page("<h1 class='pre-wrap'>Volume project</h1>"),
        "wrong project": _page(f"<h1>Other</h1><p>{line}</p>"),
    }
    recording = Intercept(site, lambda m, t: pages[landing] if m == "GET" else None)

    results = harness.measure_task_delete(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )

    assert [r.created for r in results] == [True, False, False]


def test_timed_delete_opening_press_must_be_the_confirmation(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-543, T15: a refused opening press is no confirmation to measure; nothing is timed."""
    site, saved_data, seeded = _seeded(harness, tmp_path / "data")
    recording = Intercept(site, lambda m, t: _page("<p>no</p>") if t == DELETE_OPENING else None)

    results = harness.measure_task_delete(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )

    assert [r.created for r in results] == [False, False, False]
    assert recording.requests[0][:2] == ("POST", DELETE_OPENING)
    assert len(recording.requests) == 1
    assert saved_data.load() == seeded


@pytest.mark.parametrize("failure", ["refused", "wrong landing"])
def test_a_failed_deletion_fails_the_verdict_the_whole_run_returns(
    harness: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    failure: str,
) -> None:
    """CP-543, T15: a refused deletion, or one that lands wrong, is printed as refused or failed
    and makes the deletion's verdict 1, however quick. That verdict is the one the whole run
    returns: test_delete_time_limits_are_strict drives `main` to 1 on the deletion's rows alone.
    The failure comes through the fake site handed to the measurement, not a patched module."""
    site, saved_data, _ = _seeded(harness, tmp_path / "data")
    answers = {
        "refused": DELETE_REFUSALS["refused"],
        "wrong landing": lambda m, t: (
            _page("<p>no</p>") if m == "GET" and "deleted_task" in t else None
        ),
    }
    results = harness.measure_task_delete(
        site=Intercept(site, answers[failure]), saved_data=saved_data, timer=Ticks(*QUICK)
    )

    status = harness.verdict(results, harness.LIMIT_SECONDS)

    lines = capsys.readouterr().out.splitlines()
    assert status == 1
    assert [line.split(":")[0] for line in lines] == list(DELETE_LABELS)
    assert [line for line in lines if line.endswith(" — refused or failed")]
    assert not [line for line in lines if "over" in line]


def test_whole_run_keeps_earlier_blocks_and_appends_deletion(whole_run) -> None:
    """CP-543, T15: the Summary immediately precedes the deletion, every earlier block keeps its
    order and labels, and nothing follows the deletion's rows."""
    _, status, lines, _, _ = whole_run
    labels = [line.split(":")[0] for line in lines]

    assert status == 0
    assert labels[-10:-8] == list(SUMMARY_RUN_LABELS)
    assert labels[-8:-4] == list(DELETE_RUN_LABELS)
    assert labels[-4:] == list(RENAME_RUN_LABELS)
    assert labels == [
        *OLD_RUN_LABELS,
        *NEW_RUN_LABELS,
        *MOVE_RUN_LABELS,
        *FILTER_RUN_LABELS,
        *SORT_RUN_LABELS,
        *SUMMARY_RUN_LABELS,
        *DELETE_RUN_LABELS,
        *RENAME_RUN_LABELS,
    ]


# --- The project rename appended to the whole run (CP-566; T15) -----------------------------------

RENAME_PROJECT = 1
RENAME_OLD = "Volume project"
RENAME_NEW = "Renamed volume project"
RENAME_ADDRESS = f"/projects/{RENAME_PROJECT}/rename"
RENAME_LANDING = f"/projects/{RENAME_PROJECT}?{urlencode({'rename_saved': RENAME_NEW, 'rename_from': RENAME_OLD})}"
RENAME_LINE = f"You renamed '{escape(RENAME_OLD)}' to '{escape(RENAME_NEW)}'."
RENAME_WRONG_STATES = {
    "no rename": lambda before, after: before,
    "a different name": lambda before, after: replace(
        after, projects=(replace(after.projects[0], name="Another name"),)
    ),
    "description changed": lambda before, after: replace(
        after, projects=(replace(after.projects[0], description="Another description."),)
    ),
    "another project added": lambda before, after: replace(
        after,
        projects=(*after.projects, replace(after.projects[0], id=2, name="Other project")),
        next_project_id=3,
    ),
    "a task removed": lambda before, after: replace(after, tasks=after.tasks[1:]),
    "a task field altered": lambda before, after: replace(
        after, tasks=(replace(after.tasks[0], title="Another title"), *after.tasks[1:])
    ),
    "a comment removed": lambda before, after: replace(
        after,
        tasks=(replace(after.tasks[0], comments=after.tasks[0].comments[:-1]), *after.tasks[1:]),
    ),
    "assignee list changed": lambda before, after: replace(after, assignees=("Avery Chen",)),
    "operator name changed": lambda before, after: replace(after, operator_name="Jordan Rivera"),
    "task counter changed": lambda before, after: replace(
        after, next_task_id=after.next_task_id + 1
    ),
    "project counter changed": lambda before, after: replace(
        after, next_project_id=after.next_project_id + 1
    ),
}


def _renamed(state):
    """The expected state, worked out here by replacing only the target project's name."""
    return replace(
        state,
        projects=tuple(
            replace(p, name=RENAME_NEW) if p.id == RENAME_PROJECT else p for p in state.projects
        ),
    )


def _renamed_landing(heading: str = RENAME_NEW, line: str = RENAME_LINE) -> Response:
    return _page(f'<h1 class="pre-wrap">{escape(heading)}</h1><p>{line}</p>')


class AfterRename:
    """The real site, with the saved state rewritten once the rename request has been answered."""

    def __init__(self, site, saved_data: SavedData, change: Callable) -> None:
        self._site = site
        self._saved_data = saved_data
        self._change = change
        self._before = saved_data.load()

    def handle(self, method: str, target: str, headers: dict[str, str], body: bytes) -> Response:
        response = self._site.handle(method, target, headers, body)
        if method == "POST" and target == RENAME_ADDRESS:
            after = self._saved_data.load()
            assert after is not None and self._before is not None
            self._saved_data.save(self._change(self._before, after))
        return response


def test_timed_rename_records_request_landing_and_total(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-566, T15: a same-origin POST of the new name saves exactly the renamed state and answers
    the exact redirect; the 200 landing shows the new heading and the completion. Four readings
    give three results, and the disk readback is outside every interval."""
    site, saved_data, seeded = _seeded(harness, tmp_path / "data")
    events: list[str] = []

    class Logged(Intercept):
        def handle(self, method, target, headers, body):  # type: ignore[no-untyped-def]
            events.append(f"{method} {target}")
            return super().handle(method, target, headers, body)

    class LoggedData:
        location = saved_data.location

        @staticmethod
        def load():  # type: ignore[no-untyped-def]
            events.append("load")
            return saved_data.load()

    recording = Logged(site)
    readings = iter((0.0, 0.2, 5.0, 5.3))

    def timer() -> float:
        events.append("tick")
        return next(readings)

    results = harness.measure_project_rename(site=recording, saved_data=LoggedData(), timer=timer)

    assert [(r.label, r.created) for r in results] == [(label, True) for label in RENAME_LABELS]
    assert [r.seconds for r in results] == pytest.approx([0.2, 0.3, 0.5])
    post, landing = recording.requests
    assert post[:2] == ("POST", RENAME_ADDRESS)
    assert post[2]["Sec-Fetch-Site"] == "same-origin"
    assert parse_qs(post[3].decode("utf-8")) == {"name": [RENAME_NEW]}
    assert landing[:2] == ("GET", RENAME_LANDING)
    assert saved_data.load() == _renamed(seeded)
    ticks = [i for i, event in enumerate(events) if event == "tick"]
    assert len(ticks) == 4 and events[: ticks[0]] == ["load"]
    assert events[ticks[0] + 1 : ticks[1]] == [f"POST {RENAME_ADDRESS}"]
    assert events[ticks[1] + 1 : ticks[2]] == ["load"]
    assert events[ticks[2] + 1 : ticks[3]] == [f"GET {RENAME_LANDING}"]


@pytest.mark.parametrize("wrong", RENAME_WRONG_STATES.keys())
def test_timed_rename_requires_the_exact_saved_delta(
    harness: ModuleType, tmp_path: Path, wrong: str
) -> None:
    """CP-566, T15: no rename, a wrong name, or any other change to the saved state fails the
    request and the total, however the page answers. The expected state is built here, by
    replacing one project's name, never by the rename rule."""
    site, saved_data, _ = _seeded(harness, tmp_path / "data")
    mutated = AfterRename(site, saved_data, RENAME_WRONG_STATES[wrong])

    results = harness.measure_project_rename(
        site=mutated, saved_data=saved_data, timer=Ticks(*QUICK)
    )

    assert not results[0].created
    assert not results[2].created


RENAME_REFUSALS = {
    "refused": lambda m, t: _page("<p>no</p>") if (m, t) == ("POST", RENAME_ADDRESS) else None,
    "failed": lambda m, t: (
        Response(500, (("Content-Type", "text/html"),), b"<p>no</p>")
        if (m, t) == ("POST", RENAME_ADDRESS)
        else None
    ),
    "a refusal address": lambda m, t: (
        _found(f"/projects/1?rename_refused=name_in_use&rename_typed={RENAME_NEW}")
        if (m, t) == ("POST", RENAME_ADDRESS)
        else None
    ),
    "a failure address": lambda m, t: (
        _found("/projects/1?rename_failed=save") if (m, t) == ("POST", RENAME_ADDRESS) else None
    ),
    "the bare address": lambda m, t: (
        _found("/projects/1") if (m, t) == ("POST", RENAME_ADDRESS) else None
    ),
    "another project": lambda m, t: (
        _found(RENAME_LANDING.replace("/projects/1?", "/projects/2?"))
        if (m, t) == ("POST", RENAME_ADDRESS)
        else None
    ),
    "a wrong name": lambda m, t: (
        _found("/projects/1?rename_saved=Another&rename_from=Volume+project")
        if (m, t) == ("POST", RENAME_ADDRESS)
        else None
    ),
    "not a see-other": lambda m, t: (
        Response(302, (("Location", RENAME_LANDING),), b"")
        if (m, t) == ("POST", RENAME_ADDRESS)
        else None
    ),
}


@pytest.mark.parametrize("refusal", RENAME_REFUSALS.keys())
def test_timed_rename_rejects_bad_request_outcomes(
    harness: ModuleType, tmp_path: Path, refusal: str
) -> None:
    """CP-566, T15: a refusal, a failure, a status that is not 303 or a wrong Location is not a
    completed rename; the landing is not requested and the total fails."""
    site, saved_data, _ = _seeded(harness, tmp_path / "data")
    recording = Intercept(site, RENAME_REFUSALS[refusal])

    results = harness.measure_project_rename(
        site=recording, saved_data=saved_data, timer=Ticks(0.0, 0.1)
    )

    assert [r.created for r in results] == [False, False, False]
    assert [r.label for r in results] == list(RENAME_LABELS)
    assert not [r for r in recording.requests if r[0] == "GET"]


RENAME_LANDINGS = {
    "wrong status": Response(404, (("Content-Type", "text/html"),), b"<p>no</p>"),
    "old heading": _renamed_landing(heading=RENAME_OLD),
    "no completion": _page(f'<h1 class="pre-wrap">{escape(RENAME_NEW)}</h1>'),
    "wrong completion": _renamed_landing(line=f"You renamed '{RENAME_NEW}' to '{RENAME_OLD}'."),
    "wrong previous name": _renamed_landing(line=f"You renamed 'Another' to '{RENAME_NEW}'."),
}


@pytest.mark.parametrize("landing", RENAME_LANDINGS.keys())
def test_timed_rename_requires_the_correct_landing(
    harness: ModuleType, tmp_path: Path, landing: str
) -> None:
    """CP-566, T15: a landing that is not a 200, carries the old heading, or lacks or misstates the
    completion fails the landing row and the total; the request row alone still counts."""
    site, saved_data, _ = _seeded(harness, tmp_path / "data")
    recording = Intercept(site, lambda m, t: RENAME_LANDINGS[landing] if m == "GET" else None)

    results = harness.measure_project_rename(
        site=recording, saved_data=saved_data, timer=Ticks(*QUICK)
    )

    assert [r.created for r in results] == [True, False, False]


@pytest.mark.parametrize(
    "readings,expected",
    [
        ((0.0, 0.4, 5.0, 5.5), []),
        ((0.0, 1.0, 5.0, 5.1), [RENAME_LABELS[0], RENAME_LABELS[2]]),
        ((0.0, 0.1, 5.0, 6.0), [RENAME_LABELS[1], RENAME_LABELS[2]]),
        ((0.0, 0.5, 5.0, 5.5), [RENAME_LABELS[2]]),
        ((0.0, 1.5, 5.0, 5.1), [RENAME_LABELS[0], RENAME_LABELS[2]]),
    ],
    ids=[
        "just below",
        "request exactly 1 s",
        "landing exactly 1 s",
        "sum exactly 1 s",
        "request over",
    ],
)
def test_timed_rename_enforces_each_interval_and_total(
    harness: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    readings: tuple[float, float, float, float],
    expected: list[str],
) -> None:
    """CP-566, T15: the request, the landing and their sum each pass only strictly below one
    second; equality fails, and so does a sum over the limit with each part below it."""
    status = harness.main(tmp_path, _run_readings(rename=readings))

    lines = capsys.readouterr().out.splitlines()
    assert [line.split(":")[0] for line in lines if "over" in line] == expected
    assert status == (1 if expected else 0)


def test_rename_fixture_report_states_real_volume_and_lengths(
    harness: ModuleType, tmp_path: Path
) -> None:
    """CP-566, T15: the report is worked out from the loaded fixture: its task and comment counts,
    the target project's nonempty task set, and the ordinary text and name lengths."""
    _, _, fresh = _seeded(harness, tmp_path / "data")
    held = [t for t in fresh.tasks if t.project_id == RENAME_PROJECT]
    project = next(p for p in fresh.projects if p.id == RENAME_PROJECT)
    first = min(held, key=lambda t: t.id)

    assert len(fresh.tasks) == 1000 and len(held) == 1000
    assert {len(t.comments) for t in fresh.tasks} == {20}
    assert project.name == RENAME_OLD
    assert harness.rename_fixture_report(fresh) == (
        "rename fixture: 1000 tasks, 20 comments each (20000 in all); "
        f"title of {len(first.title)} characters, "
        f"comment of {len(first.comments[0].text)} characters, "
        f"old name of {len(RENAME_OLD)} characters, new name of {len(RENAME_NEW)} characters"
    )


def test_whole_run_keeps_older_actions_and_appends_rename(
    harness: ModuleType, whole_run, tmp_path: Path
) -> None:
    """CP-566, T15: the deletion immediately precedes the rename, every earlier block keeps its
    place, the rename's fixture is its own and holds the renamed state, and nothing follows it."""
    directory, status, lines, _, _ = whole_run
    _, fresh = harness.open_task_volume(SavedData(tmp_path / "fresh"))

    assert status == 0
    assert lines[-4:] == [
        harness.rename_fixture_report(fresh),
        "rename a project at 1000 tasks: 100.0 ms",
        "rename landing page at 1000 tasks: 100.0 ms",
        "rename total at 1000 tasks: 200.0 ms",
    ]
    assert [line.split(":")[0] for line in lines][-8:-4] == list(DELETE_RUN_LABELS)
    rename_data = SavedData(directory / "rename-volume")
    delete_data = SavedData(directory / "delete-volume")
    assert rename_data.location != delete_data.location
    assert rename_data.load() == _renamed(fresh)
    assert delete_data.load() == _without_target(fresh)


@pytest.mark.parametrize("failing", ["rename", "delete"])
def test_a_failed_rename_or_older_action_makes_the_run_exit_nonzero(
    harness: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    failing: str,
) -> None:
    """CP-566, T15: a refused rename, or a refused older action, alone makes the whole run exit 1,
    and a complete success (the whole_run fixture) exits 0. The failure comes through the site
    handed to the measurement, not a patched product module."""
    name, refused = {
        "rename": ("measure_project_rename", RENAME_REFUSALS["refused"]),
        "delete": ("measure_task_delete", DELETE_REFUSALS["refused"]),
    }[failing]
    measure = getattr(harness, name)

    def rejected(*, site, saved_data, timer):
        return measure(site=Intercept(site, refused), saved_data=saved_data, timer=timer)

    monkeypatch.setattr(harness, name, rejected)

    status = harness.main(tmp_path, _run_readings())

    lines = capsys.readouterr().out.splitlines()
    assert status == 1
    assert [line for line in lines if line.endswith(" — refused or failed")]
