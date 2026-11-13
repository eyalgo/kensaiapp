"""The test-support module: the one fake for the `Saver` contract, written once (NFDR QC-64).

`FakeSaver` satisfies `Saver` by having `save`, and inherits from nothing. Its behaviour is checked
against the contract in the contract suite filed with layer 2's tests, so a test that hands it in
relies on a verified stand-in. Each control below replaces a stand-in a test once wrote for itself.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
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
