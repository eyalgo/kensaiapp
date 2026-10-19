#!/usr/bin/env python3
"""otel_receiver.py — an OTLP/http-json receiver that turns a Claude run's telemetry into
bytes this instance owns.

WHY THIS EXISTS
    A subagent's spend is recorded nowhere on disk today. Claude Code already emits it, per API
    request, over OTLP — both the metrics stream (`claude_code.token.usage`,
    `claude_code.cost.usage`) and the logs stream (`api_request`, `subagent_completed`) carry
    it. `OTEL_EXPORTER_OTLP_PROTOCOL=http/json` is the settled transport, because it keeps the
    receiver stdlib: the payload arrives as plain JSON POSTed to `/v1/metrics` and `/v1/logs`,
    so there is no protobuf and no grpc.

    Every probe that led here used the console exporter. This module is the first time the
    OTLP transport has to work against a receiver this instance wrote, not a vendor's own debug
    output.

    **Port, data directory and clock are handed in — nothing here names a default for any of
    them.** Whoever starts this passes `--port` and `--dir`, as the README's telemetry step
    does; the source names neither: that is what lets a test bind an ephemeral port against
    a temporary directory while the real receiver is up on its own, without the two fighting
    over the same socket or the same file.

    **The on-disk layout is one flat, append-only file per signal** — `<dir>/metrics.jsonl`,
    `<dir>/logs.jsonl`. Per-session or per-day splitting is not built here: no behaviour this
    module is tested against calls for it, and reading the stream back into a per-agent row is
    a later concern, not this one's.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from datetime import datetime, timezone
from enum import Enum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

__version__ = "1.1.1"


class Signal(str, Enum):
    """The two OTLP paths this receiver serves — closed to exactly these two, so a record's
    own tag is never a bare string standing in for a set nothing else names."""

    METRICS = "metrics"
    LOGS = "logs"


PATH_SIGNALS: dict[str, Signal] = {
    "/v1/metrics": Signal.METRICS,
    "/v1/logs": Signal.LOGS,
}

# ── What this receiver refuses to be told by a client ──────────────────────────────────
#
# Port, directory and clock are handed in because they are DEPLOYMENT facts. These two are
# not: they are the receiver's own posture toward anything that can reach its socket, and a
# posture with a permissive default is a posture nobody chose.
#
# LOOPBACK is the bind host. An empty host string is INADDR_ANY, which put this receiver on
# every interface — measured 2026-09-10 with `lsof -iTCP:<port>`, reporting `*:<port>` on a
# machine whose firewall `socketfilterfw --getglobalstate` reports disabled. `publish_endpoint()`
# below already writes `http://localhost:…`, so the module was asserting loopback in one place
# while binding the world in another.
LOOPBACK = "127.0.0.1"

# MAX_BODY_BYTES caps what a client may DECLARE, refused before a byte of it is read. The
# largest payload this receiver has actually been sent is 56,536 bytes, measured over the live
# `logs.jsonl` on 2026-09-10; this is ~148x that, so nothing a Claude run emits comes near it.
MAX_BODY_BYTES = 8 * 1024 * 1024


# ── The ports — every world-reach this receiver makes arrives through one of these two.
# Neither is constructed anywhere but `build_receiver()`, below.


class Clock:
    """The one capability this receiver takes from the outside world to stamp a record: the
    current time. Nothing else — this is not a scheduler and it does not sleep."""

    def now(self) -> str:
        """An ISO-8601 UTC timestamp — string-typed, because that is what a JSON line carries."""
        return datetime.now(timezone.utc).isoformat()


class Store:
    """The one world-reach this receiver makes to keep what it received: appending one record
    for a named `Signal`. Nothing else — no read-back, no query, no rotation.
    """

    def __init__(self, directory: Path) -> None:
        self._directory = directory
        # The server below serves requests on threads, so two exporters can be mid-append at
        # once. POSIX lets `write(2)` transfer fewer bytes than asked, and nothing documents
        # one Python `write()` of a ~56 KB record as one syscall — so without this, two
        # records can interleave into lines that parse as neither run's. An ordinary run
        # rarely shows it (twelve concurrent unguarded 40 KB appends, three runs, no
        # corruption — measured 2026-09-10); the lock is for the case the contract permits,
        # not one that has been seen. It is internal state, not a collaborator: nothing
        # outside this class can observe it or wants to hand one in.
        self._lock = threading.Lock()

    def append(self, signal: Signal, received_at: str, body: dict) -> None:
        line = json.dumps({"signal": signal.value, "received_at": received_at, "body": body})
        with self._lock:
            self._directory.mkdir(parents=True, exist_ok=True)
            path = self._directory / f"{signal.value}.jsonl"
            with path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")


class TelemetryServer(ThreadingHTTPServer):
    """The one server this receiver runs — **threading**, and that is load-bearing rather
    than incidental. On the single-threaded `HTTPServer` this started as, one client that
    promised a body it never sent held the only handler and the collector stopped answering
    anybody; the handler `timeout` below bounds that wait, but only a thread per request
    stops it being everyone's wait. Measured 2026-09-10. `store` and `clock` travel on it because
    `BaseHTTPRequestHandler` is instantiated per request by the server itself, with no
    constructor slot of its own to hand a collaborator through."""

    def __init__(self, server_address, handler_class, store: Store, clock: Clock) -> None:
        super().__init__(server_address, handler_class)
        self.store = store
        self.clock = clock


def publish_endpoint(path: str, port: int) -> None:
    """Write the endpoint a client should POST to, built from the port the receiver actually
    bound — never a port this module names itself. Called only when `--publish-endpoint` is
    given; whoever starts the receiver hands this path in, not a default here.
    """
    Path(path).expanduser().write_text(f"http://localhost:{port}\n", encoding="utf-8")


def build_receiver(port: int, directory: str, host: str = LOOPBACK) -> TelemetryServer:
    """Wire the real collaborators — the only place `Store`, `Clock` or `TelemetryServer` is
    constructed. `directory` is expanded here, never as an argparse default and never inside
    `main()`'s own body, because resolving `~` is a reach into the environment like any other.

    `host` defaults to loopback and is the one argument here that carries a default, because
    it is not a deployment fact the starter owns — it is who may reach this socket at all, and
    the permissive answer has to be typed rather than inherited.
    """
    resolved_directory = Path(directory).expanduser()
    return TelemetryServer((host, port), TelemetryHandler, Store(resolved_directory), Clock())


class TelemetryHandler(BaseHTTPRequestHandler):
    """Serves exactly the two OTLP paths this receiver understands; every other path and
    every non-POST method is refused. `store` and `clock` come from `self.server` — the
    `TelemetryServer` that constructs one of these per request — never from a module default.
    """

    # A client that opens a connection and then dribbles — or promises a body it never
    # sends — must not hold this receiver. `HTTPServer` serves one request at a time, so a
    # handler blocked in `rfile.read()` is the whole collector stopped. `StreamRequestHandler`
    # applies this to the connection, so it covers the request line and the headers too.
    timeout = 10

    def do_POST(self) -> None:
        signal = PATH_SIGNALS.get(self.path)
        if signal is None:
            self._respond(404, b'{"error": "not found"}')
            return
        length = self._declared_length()
        if length is None:
            self._respond(400, b'{"error": "invalid Content-Length"}')
            return
        if length > MAX_BODY_BYTES:
            # Refused on the claim, before the read — the point is not to accept the bytes
            # and then discard them.
            self._respond(413, b'{"error": "payload too large"}')
            return
        try:
            raw = self.rfile.read(length) if length > 0 else b""
        except OSError:
            # `socket.timeout` is an `OSError`. A client that promised bytes it never sent
            # has already cost this receiver `timeout` seconds; it does not also get to cost
            # it a traceback and an unanswered socket.
            self.close_connection = True
            return
        if not raw:
            self._respond(400, b'{"error": "empty body"}')
            return
        try:
            body = json.loads(raw)
        except (ValueError, TypeError):
            self._respond(400, b'{"error": "invalid JSON"}')
            return
        try:
            self.server.store.append(signal, self.server.clock.now(), body)
        except Exception:
            # Best-effort by contract: Task 4 requires that nothing a store does can take the
            # receiver down, so any failure here becomes a response rather than a propagated
            # exception.
            self._respond(500, b'{"error": "could not store record"}')
            return
        self._respond(200, b"{}")

    def do_GET(self) -> None:
        self._respond(405, b'{"error": "method not allowed"}')

    def _declared_length(self) -> int | None:
        """The body size a client declared: `None` when the header is present and is not a
        number, `0` when it is absent or non-positive.

        Bare `int()` here raised out of `do_POST` and closed the connection with no response
        at all — measured 2026-09-10 against `Content-Length: abc`. The receiver survived it;
        the client learned nothing.
        """
        declared = self.headers.get("Content-Length")
        if declared is None:
            return 0
        try:
            length = int(declared)
        except (TypeError, ValueError):
            return None
        return length if length > 0 else 0

    def _respond(self, status: int, payload: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:  # noqa: A002 - stdlib signature
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="otel_receiver.py",
        description=(
            "An OTLP/http-json receiver for the two paths Claude Code's telemetry exporters "
            "POST to. Port and data directory are required; neither has a default here, "
            "because whoever starts this passes them, not this module."
        ),
    )
    parser.add_argument("--port", type=int, required=True, help="TCP port to bind")
    parser.add_argument("--dir", required=True, help="directory to append records under")
    parser.add_argument(
        "--host",
        default=LOOPBACK,
        help=(
            "interface to bind. Defaults to loopback: this receiver has no authentication "
            "and appends whatever it is sent, so reaching past this machine is a choice that "
            "has to be typed."
        ),
    )
    parser.add_argument(
        "--publish-endpoint",
        help=(
            "path to write the endpoint a client should POST to, built from --port. "
            "Omitted, nothing is published."
        ),
    )
    args = parser.parse_args(argv)

    server = build_receiver(args.port, args.dir, args.host)
    if args.publish_endpoint:
        publish_endpoint(args.publish_endpoint, server.server_port)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
