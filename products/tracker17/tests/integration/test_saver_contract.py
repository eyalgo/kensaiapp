"""The one `Saver` fake is checked on its own, and the contract for `save` is run against it (layer 1).

Checks SRS NFR-10 and NFR-11: the tests are plain enough to read cold, and every test that needs a
saver hands in the one fake, which these checks hold to its own records and controls. NFDR QC-64
and SDD § 4 TS-6 are the clauses. The fake has no base class and no `now`; each control a test
used to get from a stand-in of its own is checked here, with no real file or process.
"""

from __future__ import annotations

import threading

import pytest

from domain import TrackerState, create_project, empty_state
from tests.fakes import FakeSaver

WAIT = 10


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


def test_the_held_call_keeps_its_state_and_waits_for_release() -> None:
    saver = FakeSaver()
    saver.hold_save = 1
    state = state_of("A")

    thread = save_on_a_thread(saver, state)
    assert saver.entered.wait(timeout=WAIT)
    thread.join(timeout=0.3)

    assert thread.is_alive()
    assert saver.saved == [state]
    saver.release.set()
    thread.join(timeout=WAIT)
    assert not thread.is_alive()


def test_calls_other_than_the_held_one_are_not_held() -> None:
    saver = FakeSaver()
    saver.hold_save = 2
    saver.save(state_of("A"))

    held = save_on_a_thread(saver, state_of("B"))
    assert saver.entered.wait(timeout=WAIT)
    saver.release.set()
    held.join(timeout=WAIT)
    saver.save(state_of("C"))

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
