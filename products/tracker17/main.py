"""The composition root — the only place this product wires a concrete implementation to an
abstraction. Every other module receives its collaborators through its constructor; nothing
outside this module builds one.

`start` builds the saved data, the tracker over its current state and the listener, and serves until
Ctrl-C. From the ready line until `start` returns, every Ctrl-C only records that a stop was asked
for (SRS FR-1; change spec rules CP-644 and CP-645): serving ends at its next look, the listener is
closed, and `start` returns 0 with nothing more written. `main` starts it on the fixed loopback
address and the saved data's default location.
"""

from __future__ import annotations

import signal
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from types import FrameType
from typing import Protocol

from application import Tracker
from domain import empty_state
from persistence import DEFAULT_LOCATION, SavedData, UnreadableData
from web import AddressTaken, listen

ADDRESS = ("127.0.0.1", 8017)


class StopRequests(Protocol):
    """What the successful lifetime needs from the process: arm the stop, and ask if it came."""

    def arm(self) -> None: ...

    def stop_requested(self) -> bool: ...


class Serving(Protocol):
    """What the successful lifetime needs from the listener: serve until asked, then close."""

    def serve_until(self, stop_requested: Callable[[], bool]) -> None: ...

    def server_close(self) -> None: ...


class SigintStopRequests:
    """One start's Ctrl-C: a flag that SIGINT sets and nothing clears.

    `latch` is the whole handler: it raises, prints, locks, reads and writes nothing, and calls
    neither `shutdown` nor `server_close`, so a signal at any point, repeated ones included, only
    leaves the flag true. It stays installed after `start` returns. A process that began with
    SIGINT ignored keeps it ignored.
    """

    def __init__(self) -> None:
        self._stop_requested = False

    def arm(self) -> None:
        if signal.getsignal(signal.SIGINT) is signal.SIG_IGN:
            return
        signal.signal(signal.SIGINT, self.latch)

    def latch(self, signum: int, frame: FrameType | None) -> None:
        self._stop_requested = True

    def stop_requested(self) -> bool:
        return self._stop_requested


class SystemClock:
    """The real clock: the current instant as an aware UTC datetime."""

    def now(self) -> datetime:
        return datetime.now(UTC)


def serve_until_stopped(
    *, listener: Serving, announce: Callable[[], None], stops: StopRequests
) -> int:
    """Arm the stop, announce readiness, serve until a stop is asked for, and close the listener.

    Returns 0. The listener is closed once, also when the announcement or serving fails; such a
    failure propagates unchanged. A stop asked for during the announcement ends serving at once.
    """
    stops.arm()
    try:
        announce()
        listener.serve_until(stops.stop_requested)
    finally:
        listener.server_close()
    return 0


def start(address: tuple[str, int], location: Path) -> int:
    """Serve the tracker on the address, with its saved data at the location, until Ctrl-C.

    Returns 1, having written one message and changed nothing, when the saved data cannot be read.
    Returns 1 with one message when something else already holds the address; the saved data is read
    first, so unreadable data is the message shown when both are true.
    """
    saved_data = SavedData(location)
    shown_location = location.absolute()
    try:
        state = saved_data.load()
    except UnreadableData:
        print(
            f"The tracker didn't start, because it couldn't read its saved data at "
            f"{shown_location}. Nothing in it was changed. "
            "See Setting saved data aside in the setup instructions.",
            file=sys.stderr,
        )
        return 1
    tracker = Tracker(empty_state() if state is None else state, saved_data, SystemClock())
    try:
        listener = listen(address, tracker)
    except AddressTaken:
        host, port = address
        print(
            "The tracker didn't start, because something else is already using the address "
            f"{host}:{port}. Stop that program, then start the tracker again.",
            file=sys.stderr,
        )
        return 1
    host, port = listener.server_address[:2]

    def announce() -> None:
        print(
            f"The tracker is running. Open http://{host}:{port} in your browser. "
            f"Saved data is kept at {shown_location}.",
            flush=True,
        )

    return serve_until_stopped(listener=listener, announce=announce, stops=SigintStopRequests())


def main(argv: list[str] | None = None) -> int:
    """Entry point. Reads no argument: the tracker always starts on its one address."""
    return start(ADDRESS, DEFAULT_LOCATION)


if __name__ == "__main__":
    sys.exit(main())
