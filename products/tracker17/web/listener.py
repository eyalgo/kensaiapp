"""The listener: binds the loopback address and hands each request to a handler's `handle` (SDD § 3
web): `Site` in front of a tracker, or `UnreadableSite` when the saved data could not be read.

Decides no rule and builds no page. It writes nothing to the console while it serves (OB-1), and
every answer it writes itself, an error included, carries no text the standard library made up
(CP-23). `listen` and `listen_unreadable` raise `AddressTaken` when something else already holds
the address and let every other bind failure propagate; they word nothing for the operator.

`Listener.serve_until` serves until a predicate the caller hands in turns true (SRS FR-1 and FR-2,
change spec rules CP-644, CP-650 and CP-651; checked at SRS NFR-11's integration layer). It knows
no signal, no saved data and no clock, and it leaves closing the listener to its caller.
"""

from __future__ import annotations

import errno
from collections.abc import Callable, Mapping
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Protocol

from application import Tracker
from errors import AppError
from web.routes import PAGE_POLICY, Response, Site, UnreadableSite


class AddressTaken(AppError):
    """The address cannot be bound because another program already holds it."""


IDLE_WAIT_SECONDS = 0.5  # how long cooperative serving waits for a request before asking again


class Answers(Protocol):
    """What the transport needs from a request handler: one request in, one response out."""

    def handle(
        self, method: str, target: str, headers: Mapping[str, str], body: bytes
    ) -> Response: ...


class _Handler(BaseHTTPRequestHandler):
    site: Answers

    def log_message(self, format: str, *args: object) -> None:
        """Write nothing: a request leaves no line on the console (OB-1)."""

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        """Answer an error the library found with the status alone and an empty body."""
        self._write(Response(code, (("Content-Security-Policy", PAGE_POLICY),), b""))

    def _serve(self) -> None:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            self.send_error(HTTPStatus.BAD_REQUEST)
            return
        body = self.rfile.read(length) if length > 0 else b""
        self._write(self.site.handle(self.command, self.path, dict(self.headers.items()), body))

    def _write(self, response: Response) -> None:
        self.send_response_only(response.status, HTTPStatus(response.status).phrase)
        for name, value in response.headers:
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(response.body)))
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(response.body)

    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = do_PATCH = do_OPTIONS = _serve


class Listener(ThreadingHTTPServer):
    """A listening server. `serve_forever` answers requests; `server_close` releases the port."""

    daemon_threads = True
    server_address: tuple[str, int]  # The loopback IPv4 address `listen` binds: a host and a port.

    def serve_until(self, stop_requested: Callable[[], bool]) -> None:
        """Answer requests until `stop_requested()` is true, asking again within half a second.

        Returns without closing the listener; the caller calls `server_close`. A request already
        accepted is answered on its own thread. Whatever `stop_requested` raises propagates, and the
        listener's timeout is put back as found either way.
        """
        timeout_before = self.timeout
        self.timeout = IDLE_WAIT_SECONDS
        try:
            while not stop_requested():
                self.handle_request()
        finally:
            self.timeout = timeout_before


def listen(address: tuple[str, int], tracker: Tracker) -> Listener:
    """Bind and listen on the address, answering through a `Site` built for the bound host.

    Raises `AddressTaken` when the address is in use; any other bind failure propagates unchanged.
    """
    return _bind(address, lambda own_host: Site(tracker, own_host))


def listen_unreadable(address: tuple[str, int], location: str) -> Listener:
    """Bind and listen on the address, answering every request through an `UnreadableSite`.

    The location is the saved data's absolute path as text. Binds and fails exactly as `listen`
    does, and no tracker is involved.
    """
    return _bind(address, lambda own_host: UnreadableSite(location, own_host))


def _bind(address: tuple[str, int], answers_for: Callable[[str], Answers]) -> Listener:
    """The one binding: a listener whose own handler class answers via `answers_for(host:port)`."""

    class Handler(_Handler):
        """This listener's own handler class, so its `site` is not shared with another listener."""

    try:
        listener = Listener(address, Handler)
    except OSError as error:
        if error.errno == errno.EADDRINUSE:
            raise AddressTaken from error
        raise
    host, port = listener.server_address[:2]
    Handler.site = answers_for(f"{host}:{port}")
    return listener
