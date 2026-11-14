"""The test-support module: the one fake for each contract, written once (NFDR QC-64).

`FakeSaver` satisfies `Saver` by having `save`, and `FakeClock` satisfies `Clock` by having `now`;
neither inherits from anything. Each one's behaviour is checked against its contract in a contract
suite filed with layer 2's tests, so a test that hands one in relies on a verified stand-in. Each
control below replaces a stand-in a test once wrote for itself.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from application import Saver
from domain import TrackerState

HELD_CALL_BOUND = 10


class FakeSaver:
    """Keeps every state it is given, and records what was asked of it.

    One `save` runs in this order: count the call, call `watch`, raise `error` when set, hand the
    state on to `passes_to`, keep it, and hold when this is the held call.
    """

    def __init__(
        self,
        *,
        error: BaseException | None = None,
        passes_to: Saver | None = None,
        only_save: bool = False,
    ) -> None:
        # Every attribute `__getattr__` reads is set before anything can ask for a missing one.
        self.only_save = only_save
        self.asked_for: list[str] = []
        self.error = error
        self.passes_to = passes_to
        self.watch: Callable[[], Any] | None = None
        self.hold_save: int | None = None
        self.saved: list[TrackerState] = []
        self.calls = 0
        self.seen: list[Any] = []
        self.entered = threading.Event()
        self.release = threading.Event()

    def save(self, state: TrackerState) -> None:
        self.calls += 1
        if self.watch is not None:
            self.seen.append(self.watch())
        if self.error is not None:
            raise self.error
        if self.passes_to is not None:
            self.passes_to.save(state)
        self.saved.append(state)
        if self.hold_save == self.calls:
            self.entered.set()
            assert self.release.wait(timeout=HELD_CALL_BOUND), "the held save was never released"

    def __getattr__(self, name: str) -> Any:
        """Reached only for a name the fake lacks. With `only_save`, record it and refuse."""
        if name in ("only_save", "asked_for") or not self.only_save:
            raise AttributeError(name)
        self.asked_for.append(name)
        raise AssertionError(f"the saver was asked for {name!r}; only save is part of the contract")


def _aware_utc(instant: datetime) -> datetime:
    """The instant itself, or `ValueError` when it is not an aware datetime at UTC."""
    if not isinstance(instant, datetime) or instant.utcoffset() != timedelta(0):
        raise ValueError(f"{instant!r} is not an aware datetime at UTC; a clock gives only those")
    return instant


class FakeClock:
    """Gives the instants a test hands it, one per read, and counts the reads.

    After the last instant it gives that one again, or one `step` after the one before, or, with
    `runs_out`, fails. It has no instant of its own and keeps the contract in every configuration:
    it refuses, with `ValueError`, any instant that is not an aware datetime at UTC.
    """

    def __init__(
        self,
        first: datetime,
        *then: datetime,
        step: timedelta | None = None,
        runs_out: bool = False,
    ) -> None:
        if step is not None and runs_out:
            raise ValueError("step and runs_out cannot both decide what follows the last instant")
        self._upcoming = [_aware_utc(instant) for instant in (first, *then)]
        self._step = step
        self._runs_out = runs_out
        self.reads = 0

    def now(self) -> datetime:
        instant = self.instant
        self.reads += 1
        if len(self._upcoming) > 1:
            del self._upcoming[0]
        elif self._step is not None:
            self._upcoming[0] = instant + self._step
        elif self._runs_out:
            self._upcoming.clear()
        return instant

    @property
    def instant(self) -> datetime:
        """The instant the next read gives; setting it replaces that one, the rest stay queued."""
        assert self._upcoming, "the clock was read more times than it was given instants"
        return self._upcoming[0]

    @instant.setter
    def instant(self, instant: datetime) -> None:
        checked = _aware_utc(instant)
        if self._upcoming:
            self._upcoming[0] = checked
        else:
            self._upcoming = [checked]

    def restart(self, first: datetime, *then: datetime) -> None:
        """Hand out these instants from now on, with `reads` back at 0."""
        self._upcoming = [_aware_utc(instant) for instant in (first, *then)]
        self.reads = 0
