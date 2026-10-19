"""Integration tests of web's listener over a real loopback socket (layer 3).

Checks SRS FR-1 and FR-2 (the tracker answers on the machine's own address and stops when asked),
FR-3 (an address something else holds is told apart from every other bind failure) and NFR-4 (a
page that cannot be served carries no text the browser did not get from this product). Change spec
rules CP-23, CP-30 to CP-38 and CP-39 to CP-46, NFDR QC-30 and QC-58, and the console's silence
while it serves (SDD § 4 OB-1) are what each test names.
"""

from __future__ import annotations

import http.client
import socket
import threading
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from application import Tracker, TrackerState
from domain import empty_state
from errors import AppError
from web import AddressTaken, listen, pages

PYTHON_TEXT = (
    "Error response",
    "Error code",
    "Message:",
    "BaseHTTP",
    "Python",
    "Unsupported method",
)


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


class NullSaver:
    def save(self, state: TrackerState) -> None:
        return None


@pytest.fixture
def served() -> Iterator[tuple[str, int]]:
    tracker = Tracker(empty_state(), NullSaver(), FixedClock())
    listener = listen(("127.0.0.1", 0), tracker)
    thread = threading.Thread(target=listener.serve_forever, daemon=True)
    thread.start()
    host, port = listener.server_address[:2]
    try:
        yield str(host), int(port)
    finally:
        listener.shutdown()
        thread.join(timeout=10)
        listener.server_close()


def request(address: tuple[str, int], method: str, target: str) -> tuple[int, bytes]:
    connection = http.client.HTTPConnection(address[0], address[1], timeout=10)
    try:
        connection.request(method, target)
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def raw_exchange(address: tuple[str, int], payload: bytes) -> bytes:
    with socket.create_connection(address, timeout=10) as connection:
        connection.sendall(payload)
        chunks = []
        while chunk := connection.recv(4096):
            chunks.append(chunk)
    return b"".join(chunks)


def test_a_request_over_a_real_socket_gets_the_page(served: tuple[str, int]) -> None:
    status, body = request(served, "GET", "/")
    assert status == 200
    assert b"<h1>Projects</h1>" in body


def test_a_request_writes_nothing_to_stdout_or_stderr(
    served: tuple[str, int], capfd: pytest.CaptureFixture[str]
) -> None:
    """OB-1."""
    assert request(served, "GET", "/")[0] == 200
    assert request(served, "GET", "/nowhere")[0] == 404
    captured = capfd.readouterr()
    assert captured.out == "" and captured.err == ""


def test_a_project_address_too_long_to_read_as_a_number_gets_the_not_found_page_and_writes_nothing(
    served: tuple[str, int], capfd: pytest.CaptureFixture[str]
) -> None:
    """OB-1, CP-30: over a real socket an identity no project holds gets the not-found page."""
    status, body = request(served, "GET", "/projects/" + "9" * 5000)
    assert status == 404
    assert body == pages.not_found_page().encode("utf-8")
    captured = capfd.readouterr()
    assert captured.out == "" and captured.err == ""


@pytest.mark.parametrize("method", ["PUT", "DELETE", "HEAD", "PATCH", "OPTIONS"])
def test_an_unsupported_method_gets_an_empty_body_and_no_python_text(
    served: tuple[str, int], method: str
) -> None:
    """CP-23."""
    status, body = request(served, method, "/")
    assert status == 404
    assert body == b""


def test_an_unknown_method_gets_no_python_text(served: tuple[str, int]) -> None:
    """CP-23: a method the handler has no name for."""
    answer = raw_exchange(served, b"FROB / HTTP/1.0\r\n\r\n")
    _head, _, body = answer.partition(b"\r\n\r\n")
    assert body == b""
    for text in PYTHON_TEXT:
        assert text.encode() not in answer


@pytest.mark.parametrize("payload", [b"nonsense\r\n\r\n", b"GET\r\n\r\n", b"\x00\x01\x02\r\n\r\n"])
def test_a_malformed_request_line_gets_no_python_text(
    served: tuple[str, int], payload: bytes
) -> None:
    """CP-23."""
    answer = raw_exchange(served, payload)
    _, _, body = answer.partition(b"\r\n\r\n")
    assert body == b""
    for text in PYTHON_TEXT:
        assert text.encode() not in answer


def test_the_listener_stops_on_server_close() -> None:
    tracker = Tracker(empty_state(), NullSaver(), FixedClock())
    listener = listen(("127.0.0.1", 0), tracker)
    thread = threading.Thread(target=listener.serve_forever, daemon=True)
    thread.start()
    address = (str(listener.server_address[0]), int(listener.server_address[1]))
    assert request(address, "GET", "/")[0] == 200
    listener.shutdown()
    thread.join(timeout=10)
    listener.server_close()
    with pytest.raises(ConnectionRefusedError):
        socket.create_connection(address, timeout=5).close()


HELD_ANSWER = b"held"


def _holder(host: str, port: int, *, reuse: bool) -> socket.socket:
    """A TCP socket bound to the address and listening, as another program would hold it."""
    held = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if reuse:
        held.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    held.bind((host, port))
    held.listen()
    return held


def _answer_one(held: socket.socket) -> bytes:
    thread = threading.Thread(target=lambda: _serve_one(held), daemon=True)
    thread.start()
    with socket.create_connection(held.getsockname(), timeout=10) as connection:
        answer = connection.recv(16)
    thread.join(timeout=10)
    return answer


def _serve_one(held: socket.socket) -> None:
    connection, _ = held.accept()
    with connection:
        connection.sendall(HELD_ANSWER)


@pytest.mark.parametrize("reuse", [False, True], ids=["plain-holder", "reuse-address-holder"])
def test_listen_raises_address_taken_when_a_holder_has_the_address(reuse: bool) -> None:
    """CP-39, CP-42: the holder keeps the address and still answers afterwards."""
    tracker = Tracker(empty_state(), NullSaver(), FixedClock())
    held = _holder("127.0.0.1", 0, reuse=reuse)
    try:
        address = held.getsockname()
        with pytest.raises(AddressTaken):
            listen((address[0], address[1]), tracker)
        assert _answer_one(held) == HELD_ANSWER
    finally:
        held.close()


def test_listen_leaves_another_cause_unchanged() -> None:
    """CP-42, Gap 5: an address no machine owns is a bind failure that is not an address taken."""
    tracker = Tracker(empty_state(), NullSaver(), FixedClock())
    with pytest.raises(OSError) as caught:
        listen(("192.0.2.1", 0), tracker)
    assert not isinstance(caught.value, AddressTaken)


def test_listen_takes_the_address_a_zero_address_holder_leaves_free() -> None:
    """CP-42: the expectation comes from a probe bind, never from the platform's name."""
    tracker = Tracker(empty_state(), NullSaver(), FixedClock())
    held = _holder("0.0.0.0", 0, reuse=False)
    try:
        port = held.getsockname()[1]
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
            probe_bound = True
        except OSError:
            probe_bound = False
        finally:
            probe.close()
        if probe_bound:
            listener = listen(("127.0.0.1", port), tracker)
            listener.server_close()
        else:
            with pytest.raises(AddressTaken):
                listen(("127.0.0.1", port), tracker)
    finally:
        held.close()


def test_address_taken_is_not_an_oserror() -> None:
    """CP-42: it derives from the product's base error alone, so no `except OSError` catches it."""
    assert issubclass(AddressTaken, AppError)
    assert not issubclass(AddressTaken, OSError)


def test_address_taken_carries_the_original_error_as_its_cause() -> None:
    """CP-39: the operating system's error stays on the chain for a reader of the code."""
    tracker = Tracker(empty_state(), NullSaver(), FixedClock())
    held = _holder("127.0.0.1", 0, reuse=False)
    try:
        address = held.getsockname()
        with pytest.raises(AddressTaken) as caught:
            listen((address[0], address[1]), tracker)
        assert isinstance(caught.value.__cause__, OSError)
    finally:
        held.close()
