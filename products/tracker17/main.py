"""The composition root — the only place this product wires a concrete implementation to an
abstraction. Every other module receives its collaborators through its constructor; nothing
outside this module builds one.

`start` claims the saved-data location, loads the saved data once, and serves until Ctrl-C; the
claim is released after the listener is closed. Readable data, or none, is served as the tracker
over its current state. Data that cannot be read is served as one plain page at every address and
is never written to (SRS FR-4 and AC-7; change spec rules CP-710 to CP-715). Either way the
listener is bound before anything is announced, and the announcement is one line on standard
output. From that line until `start` returns, every Ctrl-C only records that a stop was asked for
(SRS FR-1; change spec rules CP-644, CP-645 and CP-712): serving ends at its next look, the
listener is closed, and `start` returns 0 with nothing more written. `main` starts it on the fixed
loopback address and the saved data's default location.
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
from persistence import DEFAULT_LOCATION, LocationInUse, LocationUse, SavedData, UnreadableData
from web import AddressTaken, Listener, listen, listen_unreadable

ADDRESS = ("127.0.0.1", 8017)
ANOTHER_TRACKER_LINE = (
    "The tracker didn't start, because another tracker is already running on the same saved data. "
    "Stop that one first, then start this one."
)
SURROGATE_ESCAPE_BASE = 0xDC00
FIRST_SURROGATE_ESCAPE = SURROGATE_ESCAPE_BASE + 0x80
LAST_SURROGATE_ESCAPE = SURROGATE_ESCAPE_BASE + 0xFF


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

    Returns 0. The listener is closed once, also when arming, the announcement or serving fails;
    such a failure propagates unchanged. A stop asked for during the announcement ends serving at
    once.
    """
    try:
        stops.arm()
        announce()
        listener.serve_until(stops.stop_requested)
    finally:
        listener.server_close()
    return 0


def start(address: tuple[str, int], location: Path) -> int:
    """Serve the saved data at the location on the address until Ctrl-C.

    The location is claimed first and the claim is held until the listener is closed, whatever
    ends the start. Returns 1, having written one message and changed nothing, when another tracker
    holds the location. After that, returns 1 with one message when something else already holds
    the address, whether or not the saved data can be read. Saved data that cannot be read does not
    stop the start: the page is served instead of the tracker (`_serve_claimed`). A claim that could
    not be made for any other reason changes nothing here: the start goes on without it.
    """
    try:
        with LocationUse(location) as claim:
            return _serve_claimed(address, location, claim)
    except LocationInUse:
        print(ANOTHER_TRACKER_LINE, file=sys.stderr)
        return 1


def _serve_claimed(address: tuple[str, int], location: Path, claim: LocationUse) -> int:
    saved_data = SavedData(location)
    shown_location = location.absolute()
    try:
        state = saved_data.load()
    except UnreadableData:
        opened = _bind(lambda: listen_unreadable(address, str(shown_location)), address)
        announcement = _unreadable_line
    else:
        tracker = Tracker(empty_state() if state is None else state, saved_data, SystemClock())
        opened = _bind(lambda: listen(address, tracker), address)
        announcement = _ready_line
    if opened is None:
        return 1
    claim.mark_started()
    host, port = opened.server_address[:2]

    def announce() -> None:
        print(announcement(host, port, shown_location), flush=True)

    return serve_until_stopped(listener=opened, announce=announce, stops=SigintStopRequests())


def _bind(open_listener: Callable[[], Listener], address: tuple[str, int]) -> Listener | None:
    """The bound listener, or None after the one address line when something else holds the address.

    Any other bind failure propagates unchanged.
    """
    try:
        return open_listener()
    except AddressTaken:
        host, port = address
        print(
            "The tracker didn't start, because something else is already using the address "
            f"{host}:{port}. Stop that program, then start the tracker again.",
            file=sys.stderr,
        )
        return None


def _shown_location(location: Path) -> str:
    """The location as the ready line writes it, whatever the console's encoding.

    Python decodes a file-name byte it cannot read as text into one marker from U+DC80 to U+DCFF.
    Each marker is written as a backslash, an x and the byte's two lowercase hex digits; every
    other character, a valid one beyond ASCII and a real backslash included, is written as it is.
    The location itself, which the claim, the load and the saves use, is not changed.
    """
    return "".join(
        f"\\x{ord(character) - SURROGATE_ESCAPE_BASE:02x}"
        if FIRST_SURROGATE_ESCAPE <= ord(character) <= LAST_SURROGATE_ESCAPE
        else character
        for character in str(location)
    )


def _ready_line(host: str, port: int, location: Path) -> str:
    return (
        f"The tracker is running. Open http://{host}:{port} in your browser. "
        f"Saved data is kept at {_shown_location(location)}."
    )


def _unreadable_line(host: str, port: int, location: Path) -> str:
    return (
        f"The tracker couldn't read its saved data at {location}, and nothing in it was changed. "
        f"Open http://{host}:{port} in your browser to read this on a page. "
        "To start fresh on purpose, follow Setting saved data aside in the setup instructions."
    )


def main(argv: list[str] | None = None) -> int:
    """Entry point. Reads no argument: the tracker always starts on its one address."""
    return start(ADDRESS, DEFAULT_LOCATION)


if __name__ == "__main__":
    sys.exit(main())
