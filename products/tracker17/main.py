"""The composition root — the only place this product wires a concrete implementation to an
abstraction. Every other module receives its collaborators through its constructor; nothing
outside this module builds one.

`start` builds the saved data, the tracker over its current state and the listener, and serves until
Ctrl-C. `main` starts it on the fixed loopback address and the saved data's default location.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

from application import Tracker
from domain import empty_state
from persistence import DEFAULT_LOCATION, SavedData, UnreadableData
from web import AddressTaken, listen

ADDRESS = ("127.0.0.1", 8017)


class SystemClock:
    """The real clock: the current instant as an aware UTC datetime."""

    def now(self) -> datetime:
        return datetime.now(UTC)


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
    print(
        f"The tracker is running. Open http://{host}:{port} in your browser. "
        f"Saved data is kept at {shown_location}.",
        flush=True,
    )
    try:
        listener.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        listener.server_close()
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point. Reads no argument: the tracker always starts on its one address."""
    return start(ADDRESS, DEFAULT_LOCATION)


if __name__ == "__main__":
    sys.exit(main())
