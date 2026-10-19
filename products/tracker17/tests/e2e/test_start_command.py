"""End-to-end test of the real start command with its address held by another program (layer 5).

Checks SRS FR-3 (a start whose address something else holds says so in one plain line and
leaves the tracker's data alone). Change spec rules CP-39, CP-40, CP-41 and CP-46 and NFDR QC-58 are
the ones the test names.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import threading
from pathlib import Path

PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent
ADDRESS = ("127.0.0.1", 8017)
TIMEOUT_SECONDS = 60
HELD_ANSWER = b"held"
EXPECTED_LINE = (
    "The tracker didn't start, because something else is already using the address "
    "127.0.0.1:8017. Stop that program, then start the tracker again.\n"
)


def _record(directory: Path) -> tuple[bool, list[str], dict[str, bytes]]:
    if not directory.exists():
        return False, [], {}
    listing = sorted(str(path.relative_to(directory)) for path in directory.rglob("*"))
    contents = {
        str(path.relative_to(directory)): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }
    return True, listing, contents


def test_the_real_start_command_with_the_address_held() -> None:
    """CP-39, CP-40, CP-41, CP-46: the process ends by itself, with one line and nothing changed."""
    held = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # The last run's connection leaves this address in TIME_WAIT for a few seconds; without this a
    # second run straight after the first cannot hold it.
    held.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        try:
            held.bind(ADDRESS)
        except OSError as error:
            message = f"the test cannot hold {ADDRESS[0]}:{ADDRESS[1]}: {error}"
            raise AssertionError(message) from error
        held.listen()
        before = _record(PRODUCT_ROOT / "data")
        result = subprocess.run(
            [sys.executable, "main.py"],
            cwd=PRODUCT_ROOT,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
        after = _record(PRODUCT_ROOT / "data")

        def serve_one() -> None:
            connection, _ = held.accept()
            with connection:
                connection.sendall(HELD_ANSWER)

        thread = threading.Thread(target=serve_one, daemon=True)
        thread.start()
        with socket.create_connection(ADDRESS, timeout=10) as connection:
            answer = connection.recv(16)
        thread.join(timeout=10)
    finally:
        held.close()
    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == EXPECTED_LINE
    assert after == before
    assert answer == HELD_ANSWER
