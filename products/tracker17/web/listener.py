"""The listener: binds the loopback address and hands each request to `Site.handle` (SDD § 3 web).

Decides no rule and builds no page. It writes nothing to the console while it serves (OB-1), and
every answer it writes itself, an error included, carries no text the standard library made up
(CP-23). `listen` raises `AddressTaken` when something else already holds the address and lets
every other bind failure propagate; it words nothing for the operator.
"""

from __future__ import annotations

import errno
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from application import Tracker
from errors import AppError
from web.routes import PAGE_POLICY, Response, Site


class AddressTaken(AppError):
    """The address cannot be bound because another program already holds it."""


class _Handler(BaseHTTPRequestHandler):
    site: Site

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


def listen(address: tuple[str, int], tracker: Tracker) -> Listener:
    """Bind and listen on the address, answering through a `Site` built for the bound host.

    Raises `AddressTaken` when the address is in use; any other bind failure propagates unchanged.
    """

    class Handler(_Handler):
        """This listener's own handler class, so its `site` is not shared with another listener."""

    try:
        listener = Listener(address, Handler)
    except OSError as error:
        if error.errno == errno.EADDRINUSE:
            raise AddressTaken from error
        raise
    host, port = listener.server_address[:2]
    Handler.site = Site(tracker, f"{host}:{port}")
    return listener
