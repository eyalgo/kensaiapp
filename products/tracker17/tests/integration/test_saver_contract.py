"""The one `Saver` fake is checked on its own, and the contract for `save` is run against it (layers 1, 2).

Checks SRS NFR-10 and NFR-11: the tests are plain enough to read cold, and every test that needs a
saver hands in the one fake, which these checks hold to its own records and controls. NFDR QC-64
and SDD § 4 TS-6 are the clauses. The fake has no base class and no `now`; each control a test
used to get from a stand-in of its own is checked here, with no real file or process. The contract
suite states what a `save` keeps once, and runs it twice: handed the saved data over a folder the
test makes, and handed the fake.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from domain import (
    Comment,
    TrackerState,
    create_project,
    empty_state,
    restore_state,
    restore_task,
)
from persistence import SavedData
from persistence.saved_data import PARTIAL_FILE_NAME
from tests.fakes import FakeSaver

WAIT = 10
NOW = datetime(2026, 10, 11, 9, 30, tzinfo=UTC)


def state_of(*names: str) -> TrackerState:
    state = empty_state()
    for name in names:
        state, _ = create_project(state, name, "")
    return state


def save_on_a_thread(saver: FakeSaver, state: TrackerState) -> threading.Thread:
    thread = threading.Thread(target=saver.save, args=(state,))
    thread.start()
    return thread


def test_saved_keeps_every_state_in_the_order_handed() -> None:
    saver = FakeSaver()
    states = [state_of("A"), state_of("A", "B"), state_of("C")]

    for state in states:
        saver.save(state)

    assert saver.saved == states


def test_calls_count_every_call_the_raised_ones_included() -> None:
    saver = FakeSaver(error=PermissionError("no"))

    for _ in range(3):
        with pytest.raises(PermissionError):
            saver.save(state_of("A"))

    assert saver.calls == 3
    assert saver.saved == []


def test_the_error_set_is_the_error_raised() -> None:
    first = PermissionError("from the constructor")
    later = OSError("assigned after")
    saver = FakeSaver(error=first)

    with pytest.raises(PermissionError) as raised:
        saver.save(state_of("A"))
    assert raised.value is first

    saver.error = later
    with pytest.raises(OSError) as assigned:
        saver.save(state_of("A"))
    assert assigned.value is later


def test_clearing_the_error_ends_the_raising() -> None:
    saver = FakeSaver(error=PermissionError("no"))
    with pytest.raises(PermissionError):
        saver.save(state_of("A"))

    saver.error = None
    saver.save(state_of("B"))

    assert saver.saved == [state_of("B")]


def test_watch_answer_lands_in_seen_at_each_save() -> None:
    saver = FakeSaver()
    saver.watch = lambda: len(saver.saved)

    for name in ("A", "B", "C"):
        saver.save(state_of(name))

    assert saver.seen == [0, 1, 2]


class RecordedRelease:
    """Stands in for the fake's `release` event, so a layer-1 check neither starts a thread nor
    waits on the clock: each wait records its bound and what the fake held at that moment, and
    answers as an event that was, or was not, set within the bound."""

    def __init__(self, saver: FakeSaver, *, set_in_time: bool) -> None:
        self.saver = saver
        self.set_in_time = set_in_time
        self.waits: list[tuple[float | None, bool, list[TrackerState]]] = []

    def wait(self, timeout: float | None = None) -> bool:
        self.waits.append((timeout, self.saver.entered.is_set(), list(self.saver.saved)))
        return self.set_in_time


def test_the_held_call_keeps_its_state_and_waits_for_release() -> None:
    saver = FakeSaver()
    saver.hold_save = 1
    release = RecordedRelease(saver, set_in_time=True)
    saver.release = release  # type: ignore[assignment]
    state = state_of("A")

    saver.save(state)

    assert release.waits == [(10, True, [state])]


def test_a_held_call_not_released_in_time_fails() -> None:
    saver = FakeSaver()
    saver.hold_save = 1
    saver.release = RecordedRelease(saver, set_in_time=False)  # type: ignore[assignment]

    with pytest.raises(AssertionError, match="never released"):
        saver.save(state_of("A"))

    assert saver.saved == [state_of("A")]


def test_calls_other_than_the_held_one_are_not_held() -> None:
    saver = FakeSaver()
    saver.hold_save = 2
    release = RecordedRelease(saver, set_in_time=True)
    saver.release = release  # type: ignore[assignment]

    for name in ("A", "B", "C"):
        saver.save(state_of(name))

    assert release.waits == [(10, True, [state_of("A"), state_of("B")])]
    assert saver.saved == [state_of("A"), state_of("B"), state_of("C")]
    assert saver.calls == 3


def test_a_held_call_that_raises_is_not_held() -> None:
    saver = FakeSaver(error=PermissionError("no"))
    saver.hold_save = 1

    with pytest.raises(PermissionError):
        saver.save(state_of("A"))

    assert not saver.entered.is_set()


def test_a_hold_does_not_wait_once_release_is_set() -> None:
    saver = FakeSaver()
    saver.hold_save = 1
    saver.release.set()

    saver.save(state_of("A"))

    assert saver.entered.is_set()
    assert saver.saved == [state_of("A")]


def test_passes_to_receives_each_save_before_the_fake_keeps_it() -> None:
    second = FakeSaver()
    saver = FakeSaver(passes_to=second)
    second.watch = lambda: len(saver.saved)

    saver.save(state_of("A"))
    saver.save(state_of("B"))

    assert second.saved == saver.saved == [state_of("A"), state_of("B")]
    assert second.seen == [0, 1]


def test_when_passes_to_raises_the_fake_keeps_nothing() -> None:
    error = OSError("the second saver said no")
    saver = FakeSaver(passes_to=FakeSaver(error=error))

    with pytest.raises(OSError) as raised:
        saver.save(state_of("A"))

    assert raised.value is error
    assert saver.saved == []


def test_only_save_records_any_other_attribute_and_raises_assertion_error() -> None:
    saver = FakeSaver(only_save=True)

    with pytest.raises(AssertionError, match="close"):
        saver.close  # noqa: B018
    with pytest.raises(AssertionError, match="location"):
        getattr(saver, "location", None)

    assert saver.asked_for == ["close", "location"]


def test_without_only_save_a_missing_attribute_raises_attribute_error() -> None:
    saver = FakeSaver()

    with pytest.raises(AttributeError):
        saver.close  # noqa: B018

    assert saver.asked_for == []


def test_the_fake_defines_no_now() -> None:
    assert not hasattr(FakeSaver(), "now")


def test_the_fake_has_no_base_class() -> None:
    assert FakeSaver.__mro__ == (FakeSaver, object)


def full_state() -> TrackerState:
    """A state with every field set: both counters, projects, assignees, tasks, comments, operator."""
    comment = Comment(text=" first\n<b>&</b> ", author="Dana", created_at=NOW)
    later = Comment(text="second", author="Ari", created_at=datetime(2026, 10, 12, tzinfo=UTC))
    bare = {
        "project_id": 1,
        "status": "todo",
        "priority": "medium",
        "assignee": None,
        "labels": (),
        "due_date": None,
        "created_at": NOW,
        "comments": (),
    }
    tasks = [
        restore_task(**{**bare, "id": 1, "title": " Notes ", "status": "in-progress"}),
        restore_task(
            **{
                **bare,
                "id": 2,
                "title": "Set up CI",
                "status": "done",
                "priority": "high",
                "assignee": "Dana",
                "labels": ["bug", "ui"],
                "due_date": "2026-10-20",
                "comments": [comment, later],
            }
        ),
        restore_task(**{**bare, "id": 3, "project_id": 2, "title": "Other", "priority": "low"}),
    ]
    return restore_state(
        [(1, "Alpha", "the first"), (2, "Beta", "")],
        3,
        ["Dana", " Ari "],
        tasks=tasks,
        next_task_id=4,
        operator_name="Eyal",
    )


class SaverContract:
    """What every saver keeps, stated once. A subclass supplies the run hooks and is collected."""

    def make(self, tmp_path: Path, configuration: str) -> Any:
        """A fresh saver that has kept nothing."""
        raise NotImplementedError

    def kept(self, saver: Any) -> TrackerState | None:
        """The state the saver holds now, or None."""
        raise NotImplementedError

    def break_saves(self, saver: Any) -> None:
        """From now on a save raises OSError and keeps nothing."""
        raise NotImplementedError

    def mend_saves(self, saver: Any) -> None:
        """From now on saves are kept again."""
        raise NotImplementedError

    def release(self, saver: Any) -> None:
        """Let a held save return."""
        raise NotImplementedError

    def test_nothing_is_kept_before_the_first_save(self, tmp_path: Path) -> None:
        assert self.kept(self.make(tmp_path, "plain")) is None

    def test_a_save_keeps_the_whole_state_it_was_handed(self, tmp_path: Path) -> None:
        saver = self.make(tmp_path, "plain")
        state = full_state()

        saver.save(state)

        assert self.kept(saver) == state

    def test_each_save_replaces_the_one_before_whole(self, tmp_path: Path) -> None:
        saver = self.make(tmp_path, "plain")

        for state in (state_of("A"), state_of("A", "B"), full_state()):
            saver.save(state)
            assert self.kept(saver) == state

    def test_a_save_that_cannot_be_made_raises_and_keeps_nothing(self, tmp_path: Path) -> None:
        never_saved = self.make(tmp_path / "before", "plain")
        self.break_saves(never_saved)
        with pytest.raises(OSError):
            never_saved.save(full_state())
        assert self.kept(never_saved) is None

        after_one = self.make(tmp_path / "after", "plain")
        after_one.save(state_of("A"))
        self.break_saves(after_one)
        with pytest.raises(OSError):
            after_one.save(full_state())
        assert self.kept(after_one) == state_of("A")

    def test_saves_are_kept_again_once_they_stop_failing(self, tmp_path: Path) -> None:
        saver = self.make(tmp_path, "plain")
        self.break_saves(saver)
        with pytest.raises(OSError):
            saver.save(state_of("A"))

        self.mend_saves(saver)
        saver.save(state_of("B"))

        assert self.kept(saver) == state_of("B")

    def test_a_held_save_has_kept_its_state_when_it_returns(self, tmp_path: Path) -> None:
        saver = self.make(tmp_path, "held")
        state = full_state()

        thread = save_on_a_thread(saver, state)
        self.release(saver)
        thread.join(timeout=WAIT)

        assert not thread.is_alive()
        assert self.kept(saver) == state

    @pytest.mark.parametrize("configuration", ["watch", "passes_to", "only_save"])
    def test_a_configured_saver_keeps_the_whole_state_in_turn(
        self, tmp_path: Path, configuration: str
    ) -> None:
        saver = self.make(tmp_path, configuration)
        assert self.kept(saver) is None

        saver.save(state_of("A"))
        assert self.kept(saver) == state_of("A")

        saver.save(full_state())
        assert self.kept(saver) == full_state()


class TestSavedDataKeepsTheSaverContract(SaverContract):
    """The real saver, writing only inside the folder the test makes. It has no controls."""

    def make(self, tmp_path: Path, configuration: str) -> SavedData:
        return SavedData(tmp_path / "data")

    def kept(self, saver: SavedData) -> TrackerState | None:
        return SavedData(saver.location).load()

    def break_saves(self, saver: SavedData) -> None:
        # A directory at the partial file's name makes the save's open fail for any user.
        (saver.location / PARTIAL_FILE_NAME).mkdir(parents=True)

    def mend_saves(self, saver: SavedData) -> None:
        (saver.location / PARTIAL_FILE_NAME).rmdir()

    def release(self, saver: SavedData) -> None:
        pass


class TestFakeSaverKeepsTheSaverContract(SaverContract):
    """The fake, which must keep every case the real saver keeps."""

    def make(self, tmp_path: Path, configuration: str) -> FakeSaver:
        if configuration == "watch":
            saver = FakeSaver()
            saver.watch = lambda: None
        elif configuration == "passes_to":
            saver = FakeSaver(passes_to=FakeSaver())
        elif configuration == "only_save":
            saver = FakeSaver(only_save=True)
        elif configuration == "held":
            saver = FakeSaver()
            saver.hold_save = 1
        else:
            saver = FakeSaver()
        return saver

    def kept(self, saver: FakeSaver) -> TrackerState | None:
        return saver.saved[-1] if saver.saved else None

    def break_saves(self, saver: FakeSaver) -> None:
        saver.error = PermissionError("the disk said no")

    def mend_saves(self, saver: FakeSaver) -> None:
        saver.error = None

    def release(self, saver: FakeSaver) -> None:
        saver.release.set()
