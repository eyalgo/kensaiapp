"""Integration tests of web's listener over a real loopback socket (layer 3).

Checks SRS FR-1 and FR-2 (the tracker answers on the machine's own address and stops when asked),
FR-3 (an address something else holds is told apart from every other bind failure) and NFR-4 (a
page that cannot be served carries no text the browser did not get from this product). Change spec
rules CP-23, CP-30 to CP-38 and CP-39 to CP-46, NFDR QC-30 and QC-58, and the console's silence
while it serves (SDD § 4 OB-1) are what each test names. The cooperative listening tests check
SRS NFR-11's integration layer for change spec rules CP-644, CP-650 and CP-651: serving that ends
when a handed-in predicate turns true, without a client to wake it, and leaves the closing to the
caller.
"""

from __future__ import annotations

import http.client
import socket
import threading
from collections.abc import Callable, Iterator
from datetime import UTC, datetime

import pytest

from application import Tracker, TrackerState
from domain import empty_state
from errors import AppError
from web import AddressTaken, Listener, listen, listen_unreadable, pages
from web.routes import CSS_TYPE, HTML_TYPE, PAGE_POLICY, STYLESHEET_FILE

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


def test_a_filter_apply_over_a_real_socket_is_a_page_with_no_python_text(
    served: tuple[str, int],
) -> None:
    """CP-417: Apply is a GET with a query, read by the real listener like any project address."""
    for target in ("/projects/1?filter_status=todo", "/projects/1?filter_status=a&filter_status=b"):
        status, body = request(served, "GET", target)
        text = body.decode("utf-8", errors="replace")
        assert status == 404  # this tracker holds no project; the query changes nothing about it
        assert not any(word in text for word in PYTHON_TEXT)


JOIN_SCALE = 10


class SentinelFailure(Exception):
    """A failure no product code raises, so a test knows whose it is."""


class Serving:
    """A listener serving cooperatively in a thread, with whatever failure ended it kept."""

    def __init__(self, listener: Listener, predicate: Callable[[], bool]) -> None:
        self.failure: Exception | None = None
        self._listener = listener
        self._predicate = predicate
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            self._listener.serve_until(self._predicate)
        except Exception as error:  # noqa: BLE001 - kept for the test to read, never swallowed
            self.failure = error

    def is_serving(self) -> bool:
        return self._thread.is_alive()

    def finish(self) -> None:
        """Wait for serving to end within the suite's scale; it must end without failing."""
        self._thread.join(timeout=JOIN_SCALE)
        assert not self._thread.is_alive()
        assert self.failure is None


def _cooperative_listener() -> Listener:
    return listen(("127.0.0.1", 0), Tracker(empty_state(), NullSaver(), FixedClock()))


def _address_of(listener: Listener) -> tuple[str, int]:
    return str(listener.server_address[0]), int(listener.server_address[1])


def test_cooperative_listener_returns_when_stop_is_already_requested() -> None:
    """CP-644: a true predicate at entry returns at once, and the caller still owns the port."""
    listener = _cooperative_listener()
    try:
        Serving(listener, lambda: True).finish()
        assert listener.socket.fileno() != -1
    finally:
        listener.server_close()


def test_cooperative_listener_observes_stop_while_idle_without_a_client() -> None:
    """CP-644: a stop that turns true during an idle wait is seen with no client to wake it."""
    listener = _cooperative_listener()
    stop = threading.Event()
    asked_again = threading.Event()
    asks: list[None] = []

    def predicate() -> bool:
        asks.append(None)
        if len(asks) >= 2:
            asked_again.set()
        return stop.is_set()

    try:
        serving = Serving(listener, predicate)
        assert asked_again.wait(timeout=JOIN_SCALE)
        assert serving.is_serving()
        stop.set()
        serving.finish()
    finally:
        listener.server_close()


def test_cooperative_listener_serves_a_real_request(capfd: pytest.CaptureFixture[str]) -> None:
    """FR-1, OB-1: a real request gets the page while the predicate is false; nothing is printed."""
    listener = _cooperative_listener()
    stop = threading.Event()
    try:
        serving = Serving(listener, stop.is_set)
        status, body = request(_address_of(listener), "GET", "/")
        assert status == 200
        assert b"<h1>Projects</h1>" in body
        stop.set()
        serving.finish()
    finally:
        listener.server_close()
    captured = capfd.readouterr()
    assert captured.out == "" and captured.err == ""


def test_cooperative_listener_stops_after_a_request() -> None:
    """FR-2: a stop latched after a request ends serving; the caller's close frees the port."""
    listener = _cooperative_listener()
    address = _address_of(listener)
    stop = threading.Event()
    serving = Serving(listener, stop.is_set)
    try:
        assert request(address, "GET", "/")[0] == 200
        stop.set()
        serving.finish()
    finally:
        listener.server_close()
    with pytest.raises(ConnectionRefusedError):
        socket.create_connection(address, timeout=5).close()


def test_cooperative_listener_preserves_threaded_dispatch() -> None:
    """FR-1: a client that holds its request open does not keep a second client waiting."""
    listener = _cooperative_listener()
    address = _address_of(listener)
    stop = threading.Event()
    serving = Serving(listener, stop.is_set)
    holder = socket.create_connection(address, timeout=JOIN_SCALE)
    try:
        holder.sendall(b"GET / HTTP/1.1\r\nHost: held\r\n")  # the headers never end
        status, body = request(address, "GET", "/")
        assert status == 200
        assert b"<h1>Projects</h1>" in body
    finally:
        holder.close()
        stop.set()
        serving.finish()
        listener.server_close()


@pytest.mark.parametrize("before", [None, 3.0], ids=["no-timeout", "a-timeout"])
def test_cooperative_listener_restores_timeout_after_return(before: float | None) -> None:
    """The cooperative lifetime borrows the listener's timeout and gives back the one it found."""
    listener = _cooperative_listener()
    listener.timeout = before
    try:
        Serving(listener, lambda: True).finish()
        assert listener.timeout == before
    finally:
        listener.server_close()


def test_cooperative_listener_restores_timeout_and_propagates_failure() -> None:
    """A failing predicate surfaces as itself, with the timeout back and the closing left alone."""
    listener = _cooperative_listener()
    listener.timeout = 3.0
    failure = SentinelFailure()

    def predicate() -> bool:
        raise failure

    try:
        with pytest.raises(SentinelFailure) as caught:
            listener.serve_until(predicate)
        assert caught.value is failure
        assert listener.timeout == 3.0
        assert listener.socket.fileno() != -1
    finally:
        listener.server_close()


UNREADABLE_LOCATION = "/Users/sam/copy/products/tracker17/data"
OTHER_UNREADABLE_LOCATION = "/Users/sam/elsewhere/data"
SUPPORTED_METHODS = ("GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS")


@pytest.fixture
def serve_unreadable() -> Iterator[Callable[[str], tuple[str, int]]]:
    """Start unreadable-mode listeners on ephemeral ports; every one is stopped and closed."""
    started: list[tuple[Listener, threading.Thread]] = []

    def start(location: str) -> tuple[str, int]:
        listener = listen_unreadable(("127.0.0.1", 0), location)
        thread = threading.Thread(target=listener.serve_forever, daemon=True)
        thread.start()
        started.append((listener, thread))
        host, port = listener.server_address[:2]
        return str(host), int(port)

    try:
        yield start
    finally:
        for listener, thread in started:
            listener.shutdown()
            thread.join(timeout=10)
            listener.server_close()


def exchange(
    address: tuple[str, int],
    method: str,
    target: str,
    *,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
) -> tuple[int, dict[str, str], bytes]:
    connection = http.client.HTTPConnection(address[0], address[1], timeout=10)
    try:
        connection.request(method, target, body=body, headers=headers or {})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def test_unreadable_listener_uses_its_actual_bound_host(
    serve_unreadable: Callable[[str], tuple[str, int]],
) -> None:
    """CP-721: its own Host is answered; a wrong or missing one is refused and shows no location."""
    address = serve_unreadable(UNREADABLE_LOCATION)
    page = pages.unreadable_data_page(UNREADABLE_LOCATION).encode("utf-8")

    status, _, body = exchange(address, "GET", "/")
    assert (status, body) == (503, page)
    status, _, body = exchange(address, "GET", "/", headers={"Host": "example.com"})
    assert (status, body) == (403, b"")
    status, _, body = exchange(address, "GET", "/", headers={"Host": "127.0.0.1:1"})
    assert (status, body) == (403, b"")
    answer = raw_exchange(address, b"GET / HTTP/1.0\r\n\r\n")
    assert answer.startswith(b"HTTP/1.0 403")
    assert answer.partition(b"\r\n\r\n")[2] == b""
    assert UNREADABLE_LOCATION.encode() not in answer


def test_unreadable_listener_transports_the_method_contract(
    serve_unreadable: Callable[[str], tuple[str, int]],
) -> None:
    """CP-718 to CP-722: each supported method over real HTTP is answered as the handler says."""
    address = serve_unreadable(UNREADABLE_LOCATION)
    page = pages.unreadable_data_page(UNREADABLE_LOCATION).encode("utf-8")
    same_origin = {"Sec-Fetch-Site": "same-origin"}

    for method in ("GET", "PUT", "DELETE", "PATCH", "OPTIONS"):
        status, headers, body = exchange(address, method, "/people?x=1", headers=same_origin)
        assert (status, body) == (503, page), method
        assert headers["Content-Type"] == HTML_TYPE
        assert headers["Cache-Control"] == "no-store"
        assert headers["Content-Security-Policy"] == PAGE_POLICY
    status, headers, body = exchange(address, "GET", "/style.css")
    assert (status, body) == (200, STYLESHEET_FILE.read_bytes())
    assert headers["Content-Type"] == CSS_TYPE
    status, headers, body = exchange(
        address, "POST", "/projects", headers=same_origin, body=b"name=needle"
    )
    assert (status, body) == (303, b"")
    assert headers["Location"] == "/"
    assert headers["Content-Security-Policy"] == PAGE_POLICY
    status, headers, body = exchange(address, "POST", "/projects", body=b"name=needle")
    assert (status, body) == (403, b"")
    assert headers["Content-Security-Policy"] == PAGE_POLICY
    for method in SUPPORTED_METHODS:
        _, headers, _ = exchange(address, method, "/", headers={"Sec-Fetch-Site": "cross-site"})
        assert "Set-Cookie" not in headers


def test_unreadable_head_omits_the_representation_body(
    serve_unreadable: Callable[[str], tuple[str, int]],
) -> None:
    """CP-718, CP-719: HEAD carries the page's headers and length and no bytes, even at the CSS."""
    address = serve_unreadable(UNREADABLE_LOCATION)
    page = pages.unreadable_data_page(UNREADABLE_LOCATION).encode("utf-8")

    for target in ("/", "/people", "/style.css"):
        answer = raw_exchange(
            address, f"HEAD {target} HTTP/1.0\r\nHost: {address[0]}:{address[1]}\r\n\r\n".encode()
        )
        head, _, body = answer.partition(b"\r\n\r\n")
        assert head.startswith(b"HTTP/1.0 503"), target
        assert body == b"", target
        assert f"Content-Length: {len(page)}".encode() in head, target
        assert HTML_TYPE.encode() in head, target


def test_unreadable_listener_errors_are_empty_and_quiet(
    serve_unreadable: Callable[[str], tuple[str, int]], capfd: pytest.CaptureFixture[str]
) -> None:
    """CP-722, CP-727: the library's own errors stay empty with the policy; nothing is printed."""
    address = serve_unreadable(UNREADABLE_LOCATION)
    host = f"Host: {address[0]}:{address[1]}\r\n".encode()
    answered = (
        b"FROB / HTTP/1.0\r\n" + host + b"\r\n",
        b"POST / HTTP/1.0\r\n" + host + b"Content-Length: abc\r\n\r\n",
    )
    # The library may answer a request line it cannot read with nothing at all (as it does on the
    # normal listener); when it does answer, the answer carries the policy and no body.
    malformed = (b"nonsense\r\n\r\n", b"GET\r\n\r\n", b"\x00\x01\x02\r\n\r\n")
    for payload in (*answered, *malformed):
        answer = raw_exchange(address, payload)
        head, _, body = answer.partition(b"\r\n\r\n")
        assert body == b"", payload
        if payload in answered or answer:
            assert b"Content-Security-Policy" in head, payload
        for text in PYTHON_TEXT:
            assert text.encode() not in answer, (payload, text)
        assert UNREADABLE_LOCATION.encode() not in answer
    assert exchange(address, "GET", "/")[0] == 503
    assert exchange(address, "GET", "/style.css")[0] == 200
    captured = capfd.readouterr()
    assert captured.out == "" and captured.err == ""


def test_unreadable_listeners_do_not_share_configuration(
    serve_unreadable: Callable[[str], tuple[str, int]],
) -> None:
    """CP-724: two live listeners answer with their own location and their own host."""
    first = serve_unreadable(UNREADABLE_LOCATION)
    second = serve_unreadable(OTHER_UNREADABLE_LOCATION)
    assert first != second

    _, _, first_body = exchange(first, "GET", "/")
    _, _, second_body = exchange(second, "GET", "/")
    assert first_body == pages.unreadable_data_page(UNREADABLE_LOCATION).encode("utf-8")
    assert second_body == pages.unreadable_data_page(OTHER_UNREADABLE_LOCATION).encode("utf-8")
    status, _, _ = exchange(second, "GET", "/", headers={"Host": f"{first[0]}:{first[1]}"})
    assert status == 403


@pytest.mark.parametrize("reuse", [False, True], ids=["plain-holder", "reuse-address-holder"])
def test_unreadable_listener_retains_bind_failure_identity(reuse: bool) -> None:
    """CP-714: a held address is AddressTaken; any other bind failure propagates unchanged."""
    held = _holder("127.0.0.1", 0, reuse=reuse)
    try:
        address = held.getsockname()
        with pytest.raises(AddressTaken):
            listen_unreadable((address[0], address[1]), UNREADABLE_LOCATION)
        assert _answer_one(held) == HELD_ANSWER
    finally:
        held.close()
    with pytest.raises(OSError) as caught:
        listen_unreadable(("192.0.2.1", 0), UNREADABLE_LOCATION)
    assert not isinstance(caught.value, AddressTaken)
