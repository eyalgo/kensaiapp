"""Unit tests of the lifetime `main` runs once the tracker is ready (layer 1).

Checks SRS FR-1 (the tracker answers until it is stopped) and NFR-11 (the unit layer of the
suite). Change spec rules CP-644 (every Ctrl-C from the ready line until the start returns is a
quiet stop, a further one included), CP-645 (nothing more is written) and CP-650 (each part is
handed its collaborators, and no name inside a part is patched) are what each test names. The
listener, the ready announcement and the interrupt are hand-written recorders passed in as
arguments; the real signal adapter is exercised in tests/integration/test_start_stop.py.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from types import FrameType

import pytest

import main

READY_LINE = "The tracker is running."
PHASES = (
    "announced",
    "serve-entry",
    "serving",
    "close-entry",
    "closing",
    "after-close",
    "before-return",
)
CLEANUP_PHASES = ("close-entry", "closing", "after-close", "before-return")


class SentinelFailure(Exception):
    """A failure no product code raises, so a test knows whose it is."""


class RecordingStops:
    """The interrupt collaborator: a latch that a delivered stop sets and nothing resets."""

    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.stopped = False

    def arm(self) -> None:
        self.events.append("arm")

    def stop_requested(self) -> bool:
        return self.stopped

    def deliver(self) -> None:
        """A callback of the real handler: it only latches, whatever came before."""
        self.stopped = True


class Delivery:
    """Delivers a stop at each named phase, as the process would at that point."""

    def __init__(self, stops: RecordingStops, phases: tuple[str, ...]) -> None:
        self.stops = stops
        self.phases = phases
        self.reached: list[str] = []

    def reach(self, phase: str) -> None:
        self.reached.append(phase)
        if phase in self.phases:
            self.stops.deliver()


class RecordingListener:
    def __init__(self, events: list[str], delivery: Delivery) -> None:
        self.events = events
        self.delivery = delivery
        self.predicate: Callable[[], bool] | None = None
        self.serving_failure: Exception | None = None

    def serve_until(self, stop_requested: Callable[[], bool]) -> None:
        self.events.append("serve")
        self.predicate = stop_requested
        self.delivery.reach("serve-entry")
        self.delivery.reach("serving")
        if self.serving_failure is not None:
            raise self.serving_failure

    def server_close(self) -> None:
        self.events.append("close")
        self.delivery.reach("close-entry")
        self.delivery.reach("closing")
        self.delivery.reach("after-close")


class Lifetime:
    """One coordinator run over recorders, with the phases at which a stop is delivered."""

    def __init__(self, phases: tuple[str, ...] = ()) -> None:
        self.events: list[str] = []
        self.stops = RecordingStops(self.events)
        self.delivery = Delivery(self.stops, phases)
        self.listener = RecordingListener(self.events, self.delivery)
        self.announcement_failure: Exception | None = None

    def announce(self) -> None:
        self.events.append("announce")
        print(READY_LINE, flush=True)
        if self.announcement_failure is not None:
            raise self.announcement_failure
        self.delivery.reach("announced")

    def run(self) -> int:
        """Run the coordinator; a stop due just before its return is delivered from its frame."""
        previous = sys.getprofile()

        def before_return(frame: FrameType, event: str, argument: object) -> None:
            if event == "return" and frame.f_code is main.serve_until_stopped.__code__:
                self.delivery.reach("before-return")

        sys.setprofile(before_return)
        try:
            return main.serve_until_stopped(
                listener=self.listener, announce=self.announce, stops=self.stops
            )
        finally:
            sys.setprofile(previous)


def test_lifecycle_arms_before_announcing_and_passes_the_stop_predicate() -> None:
    """CP-644: arm, announce, serve and close in that order, and the listener gets the predicate."""
    lifetime = Lifetime()

    result = lifetime.run()

    assert result == 0
    assert lifetime.events == ["arm", "announce", "serve", "close"]
    assert lifetime.listener.predicate == lifetime.stops.stop_requested


@pytest.mark.parametrize("phase", PHASES)
def test_lifecycle_stops_quietly_at_each_phase(
    phase: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-644, CP-645: a stop at any phase gives result 0, one close and only the ready line."""
    lifetime = Lifetime((phase,))

    result = lifetime.run()

    assert result == 0
    assert lifetime.delivery.reached.count(phase) == 1
    assert lifetime.stops.stopped
    assert lifetime.events.count("close") == 1
    captured = capsys.readouterr()
    assert captured.out == READY_LINE + "\n" and captured.err == ""


def test_lifecycle_accepts_the_first_stop_during_normal_cleanup(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CP-644: serving ends on its own, and the first stop arrives while the listener closes."""
    lifetime = Lifetime(("closing",))

    result = lifetime.run()

    assert result == 0
    assert lifetime.events == ["arm", "announce", "serve", "close"]
    assert lifetime.delivery.reached.index("serving") < lifetime.delivery.reached.index("closing")
    assert lifetime.stops.stopped
    captured = capsys.readouterr()
    assert captured.out == READY_LINE + "\n" and captured.err == ""


@pytest.mark.parametrize("phase", CLEANUP_PHASES)
def test_lifecycle_accepts_further_stops_during_cleanup_and_return(
    phase: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-644: after an earlier stop, one more delivered at this point leaves the latch true."""
    lifetime = Lifetime(("announced", phase))

    result = lifetime.run()

    assert result == 0
    assert lifetime.delivery.reached.count(phase) == 1
    assert lifetime.stops.stopped
    assert lifetime.events.count("close") == 1
    captured = capsys.readouterr()
    assert captured.out == READY_LINE + "\n" and captured.err == ""


def test_lifecycle_closes_once_and_propagates_unrelated_announcement_failure() -> None:
    """A failure that is not a stop closes the listener once and surfaces unchanged."""
    lifetime = Lifetime()
    failure = SentinelFailure()
    lifetime.announcement_failure = failure

    with pytest.raises(SentinelFailure) as caught:
        lifetime.run()

    assert caught.value is failure
    assert lifetime.events == ["arm", "announce", "close"]


def test_lifecycle_closes_once_and_propagates_unrelated_serving_failure() -> None:
    """A serving failure surfaces as itself after one close, never as a quiet result 0."""
    lifetime = Lifetime()
    failure = SentinelFailure()
    lifetime.listener.serving_failure = failure

    with pytest.raises(SentinelFailure) as caught:
        lifetime.run()

    assert caught.value is failure
    assert lifetime.events == ["arm", "announce", "serve", "close"]
