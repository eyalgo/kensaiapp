"""Tests for `otel_receiver.py` — the OTLP/http-json receiver that turns a Claude run's
telemetry into bytes on disk.

`core/doctrine/engineering/languages/python/conventions.md` § Constructs: "A module is given
its collaborators; it constructs none." These tests hold that against `otel_receiver.py` itself
— by effect, via `ast`/`inspect`, never by re-deriving what the ports do from their own bodies.
The live receiver holds one port and one directory, so a suite that binds either fights the
daemon or proves nothing; every end-to-end test below binds an ephemeral port (`0`) against a
`tmp_path`, never the real `4318` / `~/.kensaiapp/telemetry`.
"""

from __future__ import annotations

import ast
import http.client
import inspect
import json
import plistlib
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

import otel_receiver


# ── The seam every end-to-end test below drives requests against ──────────


@pytest.fixture
def running_receiver(tmp_path):
    """A real `TelemetryServer` bound to an ephemeral port (`0`), serving out of a temporary
    directory, in a background thread — torn down after the test whatever it did. Yields
    `(server, tmp_path)`; the port to connect on is `server.server_port`."""
    server = otel_receiver.build_receiver(0, str(tmp_path))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, tmp_path
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _post(port: int, path: str, body: bytes) -> tuple[int, bytes]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request("POST", path, body=body)
        response = conn.getresponse()
        return response.status, response.read()
    finally:
        conn.close()


def _free_port() -> int:
    """A port nothing is listening on — for the one test that must hand a port to a *separate
    process* on a command line, where `0` cannot be read back off a bound socket."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _get(port: int, path: str) -> int:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request("GET", path)
        response = conn.getresponse()
        response.read()
        return response.status
    finally:
        conn.close()


# ── Task 1 — the two ports exist, and one function builds them ────────


class TestPortsAndTheCompositionRoot:
    def test_store_exposes_exactly_one_capability(self):
        # "appending one record for a named signal. Nothing else." — no read-back, no query.
        assert {name for name in vars(otel_receiver.Store) if not name.startswith("_")} == {
            "append"
        }

    def test_clock_exposes_exactly_one_capability(self):
        # "the current time, as the value written onto a record." — nothing else.
        assert {name for name in vars(otel_receiver.Clock) if not name.startswith("_")} == {
            "now"
        }

    def test_clock_now_returns_a_string_timestamp(self):
        assert isinstance(otel_receiver.Clock().now(), str)

    def test_only_build_receiver_constructs_a_store_clock_or_server(self):
        # By effect, not by name: walk every function body in the module and record which one
        # names `Store(`, `Clock(` or `TelemetryServer(` as a call — `build_receiver` should be
        # the only hit.
        source = Path(otel_receiver.__file__).read_text()
        tree = ast.parse(source)
        constructing_functions = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for call in ast.walk(node):
                    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name):
                        if call.func.id in ("Store", "Clock", "TelemetryServer"):
                            constructing_functions.add(node.name)
        assert constructing_functions == {"build_receiver"}

    def test_main_obtains_its_collaborators_from_build_receiver_and_constructs_none_itself(self):
        source = inspect.getsource(otel_receiver.main)
        assert "build_receiver(" in source
        assert "Store(" not in source
        assert "Clock(" not in source
        assert "TelemetryServer(" not in source

    def test_build_receiver_is_the_last_top_level_function_ahead_of_main(self):
        # "sits at the bottom of the module" — the composition root is the last thing defined
        # before the CLI entry point.
        source = Path(otel_receiver.__file__).read_text()
        tree = ast.parse(source)
        top_level_funcs = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
        assert top_level_funcs[-2:] == ["build_receiver", "main"]

    def test_build_receiver_resolves_a_home_relative_directory(self, monkeypatch, tmp_path):
        # Expanding `~` is an environment reach, and Task 1 puts it inside `build_receiver()`
        # — never as an argparse default, never in a unit's own body.
        monkeypatch.setenv("HOME", str(tmp_path))
        server = otel_receiver.build_receiver(0, "~/nested/telemetry")
        try:
            assert server.store._directory == tmp_path / "nested" / "telemetry"
        finally:
            server.server_close()

    def test_dir_argument_carries_no_default_and_is_required(self):
        # "never as an argparse default" — the CLI declares `--dir` required, with nothing to
        # fall back to.
        source = Path(otel_receiver.__file__).read_text()
        match = ast.parse(source)
        add_argument_calls = [
            node
            for node in ast.walk(match)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_argument"
        ]
        dir_calls = [
            call
            for call in add_argument_calls
            if call.args
            and isinstance(call.args[0], ast.Constant)
            and call.args[0].value == "--dir"
        ]
        assert len(dir_calls) == 1
        keywords = {kw.arg: kw.value for kw in dir_calls[0].keywords}
        assert "default" not in keywords
        assert isinstance(keywords["required"], ast.Constant) and keywords["required"].value is True

    def test_main_does_not_expand_the_directory_itself(self):
        # The reach lives in `build_receiver()`; `main()` only hands the raw string through.
        source = inspect.getsource(otel_receiver.main)
        assert "expanduser" not in source


# ── Task 2 — the two OTLP paths are served, and nothing else is ────────


class TestPathsServed:
    def test_post_metrics_returns_2xx_and_appends_one_record_tagged_metrics(
        self, running_receiver
    ):
        server, tmp_path = running_receiver
        status, _ = _post(server.server_port, "/v1/metrics", b'{"a": 1}')
        assert 200 <= status < 300
        lines = (tmp_path / "metrics.jsonl").read_text().splitlines()
        assert len(lines) == 1
        # "tagged `metrics`" is half the stated behaviour — the file it lands in is the other
        # half, and a record that lands in the right file under the wrong tag still fails it.
        assert json.loads(lines[0])["signal"] == "metrics"

    def test_post_logs_returns_2xx_and_appends_one_record_tagged_logs(self, running_receiver):
        server, tmp_path = running_receiver
        status, _ = _post(server.server_port, "/v1/logs", b'{"a": 1}')
        assert 200 <= status < 300
        lines = (tmp_path / "logs.jsonl").read_text().splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["signal"] == "logs"

    def test_get_on_metrics_is_refused_and_the_store_is_untouched(self, running_receiver):
        server, tmp_path = running_receiver
        status = _get(server.server_port, "/v1/metrics")
        assert status >= 400
        assert not (tmp_path / "metrics.jsonl").exists()

    def test_get_on_logs_is_refused_and_the_store_is_untouched(self, running_receiver):
        server, tmp_path = running_receiver
        status = _get(server.server_port, "/v1/logs")
        assert status >= 400
        assert not (tmp_path / "logs.jsonl").exists()

    def test_post_to_an_unknown_path_returns_404_and_the_store_is_untouched(
        self, running_receiver
    ):
        server, tmp_path = running_receiver
        status, _ = _post(server.server_port, "/v1/traces", b'{"a": 1}')
        assert status == 404
        assert list(tmp_path.iterdir()) == []


# ── Task 3 — a stored record keeps the body verbatim ────────


class TestRecordShape:
    def test_written_line_is_json_carrying_signal_received_at_and_the_body(
        self, running_receiver
    ):
        server, tmp_path = running_receiver
        status, _ = _post(
            server.server_port, "/v1/metrics", json.dumps({"cost_usd": 0.4}).encode()
        )
        assert status // 100 == 2
        record = json.loads((tmp_path / "metrics.jsonl").read_text().splitlines()[0])
        assert record["signal"] == "metrics"
        assert record["received_at"]  # a non-empty timestamp from Clock
        assert record["body"]["cost_usd"] == 0.4

    def test_received_at_comes_from_the_injected_clock_not_the_wall_clock(self, tmp_path):
        class FixedClock:
            def now(self) -> str:
                return "2026-09-09T00:00:00+00:00"

        store = otel_receiver.Store(tmp_path)
        store.append(otel_receiver.Signal.METRICS, FixedClock().now(), {"x": 1})
        record = json.loads((tmp_path / "metrics.jsonl").read_text().splitlines()[0])
        assert record["received_at"] == "2026-09-09T00:00:00+00:00"

    def test_two_posts_append_two_lines_neither_rewriting_the_other(self, running_receiver):
        server, tmp_path = running_receiver
        _post(server.server_port, "/v1/metrics", b'{"n": 1}')
        _post(server.server_port, "/v1/metrics", b'{"n": 2}')
        lines = (tmp_path / "metrics.jsonl").read_text().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["body"]["n"] == 1
        assert json.loads(lines[1])["body"]["n"] == 2

    def test_a_body_containing_a_newline_does_not_split_into_two_records(self, running_receiver):
        server, tmp_path = running_receiver
        body = json.dumps({"note": "line one\nline two"}).encode()
        _post(server.server_port, "/v1/metrics", body)
        lines = (tmp_path / "metrics.jsonl").read_text().splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["body"]["note"] == "line one\nline two"


# ── Task 4 — a bad request cannot take the receiver down ────────


class TestResilience:
    def test_malformed_json_body_returns_4xx_appends_nothing_and_serves_the_next_request(
        self, running_receiver
    ):
        server, tmp_path = running_receiver
        status, _ = _post(server.server_port, "/v1/metrics", b"{not json")
        assert 400 <= status < 500
        assert not (tmp_path / "metrics.jsonl").exists()
        status2, _ = _post(server.server_port, "/v1/metrics", b'{"ok": true}')
        assert status2 // 100 == 2

    def test_empty_body_returns_4xx_appends_nothing_and_serves_the_next_request(
        self, running_receiver
    ):
        server, tmp_path = running_receiver
        status, _ = _post(server.server_port, "/v1/metrics", b"")
        assert 400 <= status < 500
        assert not (tmp_path / "metrics.jsonl").exists()
        status2, _ = _post(server.server_port, "/v1/metrics", b'{"ok": true}')
        assert status2 // 100 == 2

    def test_a_store_that_raises_on_append_does_not_take_the_receiver_down(self):
        class RaisingStore:
            def append(self, signal, received_at, body):
                raise RuntimeError("boom")

        server = otel_receiver.TelemetryServer(
            ("127.0.0.1", 0), otel_receiver.TelemetryHandler, RaisingStore(), otel_receiver.Clock()
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            status1, _ = _post(server.server_port, "/v1/metrics", b'{"ok": true}')
            assert status1 >= 500
            # The receiver is still up: a second request against the same (still-raising)
            # store is served rather than the connection failing outright.
            status2, _ = _post(server.server_port, "/v1/logs", b'{"ok": true}')
            assert status2 >= 500
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_a_header_the_receiver_cannot_parse_does_not_take_it_down(self, running_receiver):
        # Task 4's intent is the whole sentence — "the receiver outlives *anything* a client
        # sends it" — not only the three bodies its bullets name. A Content-Length that is not
        # a number is the nearest thing a client can send that the bullets do not cover.
        server, tmp_path = running_receiver
        raw = socket.create_connection(("127.0.0.1", server.server_port), timeout=5)
        try:
            raw.sendall(
                b"POST /v1/metrics HTTP/1.0\r\nContent-Length: banana\r\n\r\n{}"
            )
            raw.recv(256)
        finally:
            raw.close()
        status, _ = _post(server.server_port, "/v1/metrics", b'{"ok": true}')
        assert status // 100 == 2


# ── Found while walking — what a client may not do to this receiver ────────
#
# A review on 2026-09-10 read this module and reported it network-exposed with an unbounded
# body. Two of its four sub-claims were already handled — a missing and a negative
# `Content-Length` both reached the empty-body 400. Two were real, and the second was worse
# than reported: `HTTPServer` serves one request at a time, so a handler blocked in
# `rfile.read()` is not one slow client, it is the collector down for everybody.
#
# `<CORE>/doctrine/governance/found_while_walking.md` clause 1 — small, fixed on the branch
# that found it.


class TestWhatAClientMayNotDo:
    def test_the_receiver_binds_loopback_and_not_every_interface(self, running_receiver):
        # The defect, stated as the bar that would have caught it: an empty host string is
        # INADDR_ANY, and `server_address[0]` reported `0.0.0.0` before this.
        server, _ = running_receiver
        assert server.server_address[0] == otel_receiver.LOOPBACK
        assert server.server_address[0] != "0.0.0.0"

    def test_a_wider_bind_is_available_but_has_to_be_asked_for(self, tmp_path):
        # Loopback is a default, not a prohibition — an operator who means it can say so.
        server = otel_receiver.build_receiver(0, str(tmp_path), "0.0.0.0")
        try:
            assert server.server_address[0] == "0.0.0.0"
        finally:
            server.server_close()

    def test_host_carries_a_loopback_default_and_is_not_required(self):
        # The same AST idiom `test_dir_argument_carries_no_default_and_is_required` uses.
        # `--host` is the one argument here that SHOULD carry a default, and the default has
        # to be the loopback constant rather than a second spelling of it.
        tree = ast.parse(Path(otel_receiver.__file__).read_text())
        host_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_argument"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "--host"
        ]
        assert len(host_calls) == 1
        keywords = {kw.arg: kw.value for kw in host_calls[0].keywords}
        assert "required" not in keywords
        assert isinstance(keywords["default"], ast.Name)
        assert keywords["default"].id == "LOOPBACK"

    def test_a_declared_length_over_the_cap_is_refused_before_the_body_is_read(
        self, running_receiver
    ):
        server, tmp_path = running_receiver
        oversize = otel_receiver.MAX_BODY_BYTES + 1
        raw = socket.create_connection(("127.0.0.1", server.server_port), timeout=5)
        try:
            # The body is never sent. If the receiver reads before it checks, this hangs and
            # the recv below times out instead of returning a status line.
            raw.sendall(
                b"POST /v1/logs HTTP/1.0\r\nContent-Length: %d\r\n\r\n" % oversize
            )
            first_line = raw.recv(256).split(b"\r\n")[0]
        finally:
            raw.close()
        assert b"413" in first_line, first_line
        assert not list(tmp_path.iterdir())

    def test_one_client_promising_a_body_it_never_sends_does_not_stop_the_collector(
        self, running_receiver
    ):
        # The sharp one. The attacker holds the socket open, so the handler cannot be
        # unblocked by a disconnect — which is what an earlier probe accidentally did,
        # masking the stall.
        server, _ = running_receiver
        held = socket.create_connection(("127.0.0.1", server.server_port), timeout=5)
        try:
            held.sendall(
                b"POST /v1/logs HTTP/1.0\r\nContent-Length: 4096\r\n\r\n{"
            )
            # A second, entirely ordinary client. Before the fix this got no response at all.
            status, _body = _post(server.server_port, "/v1/logs", b'{"ok": true}')
            assert status // 100 == 2
        finally:
            held.close()

    def test_a_content_length_that_is_not_a_number_is_answered_rather_than_dropped(
        self, running_receiver
    ):
        # `test_a_header_the_receiver_cannot_parse_does_not_take_it_down` already pins that
        # the receiver survives this. It did — by letting `int()` raise out of `do_POST`,
        # closing the connection with no response. Surviving and answering are different
        # promises.
        server, tmp_path = running_receiver
        raw = socket.create_connection(("127.0.0.1", server.server_port), timeout=5)
        try:
            raw.sendall(b"POST /v1/logs HTTP/1.0\r\nContent-Length: banana\r\n\r\n{}")
            first_line = raw.recv(256).split(b"\r\n")[0]
        finally:
            raw.close()
        assert b"400" in first_line, first_line
        assert not list(tmp_path.iterdir())

    def test_a_missing_or_negative_length_still_reaches_the_empty_body_refusal(self):
        # The two sub-claims the review got wrong, pinned so a later change cannot quietly
        # make them true.
        assert otel_receiver.TelemetryHandler._declared_length is not None
        for declared, expected in ((None, 0), ("-1", 0), ("0", 0), ("12", 12)):
            headers = {} if declared is None else {"Content-Length": declared}
            assert _declared_length_of(headers) == expected

    def test_one_record_is_one_uninterrupted_append_even_when_the_os_writes_in_pieces(
        self, tmp_path, monkeypatch
    ):
        # What serving on threads costs, paid. POSIX lets `write(2)` transfer fewer bytes than
        # asked, and nothing documents one Python `write()` of a ~56 KB line as one syscall.
        # An ordinary run rarely shows the interleave — twelve concurrent unguarded 40 KB
        # appends, three runs, no corruption, measured 2026-09-10 — so a test that hopes for
        # it passes with the lock deleted, which the first version of this one did. This one
        # forces the case the contract permits: every write lands in 1 KB pieces with a yield
        # between them.
        real_open = Path.open

        class _Piecewise:
            def __init__(self, handle):
                self._handle = handle

            def write(self, data):
                for start in range(0, len(data), 1024):
                    self._handle.write(data[start : start + 1024])
                    self._handle.flush()
                    time.sleep(0.0005)
                return len(data)

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                self._handle.close()

        monkeypatch.setattr(
            Path, "open", lambda self, *args, **kwargs: _Piecewise(real_open(self, *args, **kwargs))
        )
        store = otel_receiver.Store(tmp_path)
        bodies = [{"who": index, "pad": "x" * 8_000} for index in range(8)]
        threads = [
            threading.Thread(target=store.append, args=(otel_receiver.Signal.LOGS, "t", body))
            for body in bodies
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        monkeypatch.undo()

        lines = (tmp_path / "logs.jsonl").read_text().splitlines()
        assert len(lines) == len(bodies)
        recovered = sorted(json.loads(line)["body"]["who"] for line in lines)
        assert recovered == list(range(len(bodies)))

    def test_the_cap_is_far_above_anything_a_real_run_emits(self):
        # 56,536 bytes is the largest payload measured on the live stream, 2026-09-10.
        assert otel_receiver.MAX_BODY_BYTES > 100 * 56_536


def _declared_length_of(headers: dict) -> int | None:
    handler = otel_receiver.TelemetryHandler.__new__(otel_receiver.TelemetryHandler)
    handler.headers = headers
    return handler._declared_length()


# ── Task 5 — the module names neither the port nor the directory ────────


class TestNoHardcodedPortOrDirectory:
    def test_module_source_names_neither_the_real_port_nor_the_real_directory(self):
        source = Path(otel_receiver.__file__).read_text()
        matches = re.findall(r"4318|\.claude/telemetry|\.kensaiapp/telemetry", source)
        assert matches == []

    def test_port_and_dir_are_required_cli_arguments(self):
        with pytest.raises(SystemExit):
            otel_receiver.main([])
        with pytest.raises(SystemExit):
            otel_receiver.main(["--port", "0"])
        with pytest.raises(SystemExit):
            otel_receiver.main(["--dir", "/tmp/does-not-matter"])

    def test_receiver_runs_end_to_end_on_an_ephemeral_port_against_a_temp_dir(self, tmp_path):
        server = otel_receiver.build_receiver(0, str(tmp_path))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            status, _ = _post(
                server.server_port, "/v1/logs", json.dumps({"cost_usd": 0.1}).encode()
            )
            assert status // 100 == 2
            record = json.loads((tmp_path / "logs.jsonl").read_text().splitlines()[0])
            assert record["body"]["cost_usd"] == 0.1
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


# ── `a-launcher-tags-its-own-run` Task 1 — the receiver publishes where it is listening ────────
#
# The port is authored once, by whoever starts the receiver; the receiver writes it where a client can read it, so
# no launcher and no library ever names the number. `--publish-endpoint` is optional and carries no
# default of its own, exactly like `--port` and `--dir` carry no defaults of their own (they are
# merely *required*, where this one is merely *absent when omitted*) — the singleton is still
# whoever starts the receiver, not this module.


class TestPublishedEndpoint:
    def test_publish_endpoint_argument_carries_no_default_and_is_optional(self):
        source = Path(otel_receiver.__file__).read_text()
        tree = ast.parse(source)
        add_argument_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_argument"
        ]
        publish_calls = [
            call
            for call in add_argument_calls
            if call.args
            and isinstance(call.args[0], ast.Constant)
            and call.args[0].value == "--publish-endpoint"
        ]
        assert len(publish_calls) == 1
        keywords = {kw.arg for kw in publish_calls[0].keywords}
        assert "default" not in keywords
        assert "required" not in keywords

    def test_publish_endpoint_is_the_only_new_top_level_function_and_sits_ahead_of_build_receiver(
        self,
    ):
        # The composition-root ordering Task 1 (station 1) pinned — `top_level_funcs[-2:] ==
        # ["build_receiver", "main"]` — must still hold: a new function earns a home ahead of
        # `build_receiver`, never between it and `main`.
        source = Path(otel_receiver.__file__).read_text()
        tree = ast.parse(source)
        top_level_funcs = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
        assert top_level_funcs[-2:] == ["build_receiver", "main"]
        assert "publish_endpoint" in top_level_funcs

    def test_started_without_publish_endpoint_writes_nothing_and_serves_as_before(self, tmp_path):
        port = _free_port()
        data_dir = tmp_path / "data"
        process = subprocess.Popen(
            [sys.executable, str(Path(otel_receiver.__file__)), "--port", str(port), "--dir", str(data_dir)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            deadline = time.monotonic() + 10
            status = None
            while True:
                if process.poll() is not None:
                    _, stderr = process.communicate()
                    pytest.fail(f"receiver exited before serving: {stderr.decode(errors='replace')}")
                try:
                    status, _ = _post(port, "/v1/logs", b'{"ok": true}')
                    break
                except OSError:
                    if time.monotonic() > deadline:
                        pytest.fail("receiver never started serving")
                    time.sleep(0.1)
            assert status // 100 == 2
            # Nothing named like a published endpoint appears anywhere under the data directory —
            # the whole of "writes nothing" for an argument nobody handed it a path for.
            assert list(data_dir.rglob("*endpoint*")) == []
        finally:
            process.terminate()
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()

    def test_started_with_publish_endpoint_writes_the_built_endpoint_and_it_round_trips(
        self, tmp_path
    ):
        port = _free_port()
        pub_file = tmp_path / "endpoint"
        data_dir = tmp_path / "data"
        process = subprocess.Popen(
            [
                sys.executable,
                str(Path(otel_receiver.__file__)),
                "--port",
                str(port),
                "--dir",
                str(data_dir),
                "--publish-endpoint",
                str(pub_file),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            # The file is created empty before its line is written, so it is read until the
            # whole line (ending in a newline) has arrived, under one deadline.
            deadline = time.monotonic() + 30.0
            published = ""
            while True:
                try:
                    published = pub_file.read_text()
                except FileNotFoundError:
                    published = ""
                if published.endswith("\n"):
                    break
                if process.poll() is not None:
                    _, stderr = process.communicate()
                    pytest.fail(
                        f"receiver exited before publishing an endpoint: {stderr.decode(errors='replace')}"
                    )
                if time.monotonic() >= deadline:
                    pytest.fail("receiver never published an endpoint")
                time.sleep(0.05)

            endpoint = published.strip()
            # Built from the port it was handed — the same port passed on the command line, since
            # this test hands a real (non-zero) port rather than an ephemeral 0.
            assert endpoint == f"http://localhost:{port}"

            # The round trip: a client reads the published file and POSTs to what it names.
            status, _ = _post(port, "/v1/logs", json.dumps({"cost_usd": 0.3}).encode())
            assert status // 100 == 2
            record = json.loads((data_dir / "logs.jsonl").read_text().splitlines()[0])
            assert record["body"]["cost_usd"] == 0.3
        finally:
            process.terminate()
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()

    def test_publish_endpoint_function_writes_the_built_url_from_the_bound_port(self, tmp_path):
        # Exercises `publish_endpoint()` directly against a live, ephemeral-port receiver — the
        # "driven end to end on an ephemeral port" half of the behaviour, without a subprocess.
        server = otel_receiver.build_receiver(0, str(tmp_path / "data"))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        pub_file = tmp_path / "endpoint"
        try:
            otel_receiver.publish_endpoint(str(pub_file), server.server_port)
            assert pub_file.read_text().strip() == f"http://localhost:{server.server_port}"
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_module_source_still_names_neither_the_real_port_nor_the_real_directory(self):
        # Task 1's own guard, re-asserted here because the new code is what could have
        # reintroduced a literal.
        source = Path(otel_receiver.__file__).read_text()
        matches = re.findall(r"4318|\.claude/telemetry|\.kensaiapp/telemetry", source)
        assert matches == []


# ── Task 6 — the machine can start it, by hand ────────


class TestInstallMaterials:
    """The install materials are **machine state**, not repo files —
    `<CORE>/doctrine/setup/kensaiapp_structure.md` § Machine state — never `[create]`. They name this
    machine's user and this machine's checkout, which is why they cannot be vendored.

    That same doctrine says no tool may *require* machine state to exist, so every test here skips
    when the plist has not been installed. A fresh satellite, or a checkout on another machine, runs
    this suite green without it — and on a machine where it IS installed, these run for real.
    """

    INSTALL_DIR = Path.home() / ".claude" / "tools" / "otel-receiver"
    PLIST_PATH = next(INSTALL_DIR.glob("*.plist"), INSTALL_DIR / "absent.plist")
    INSTALL_PATH = INSTALL_DIR / "INSTALL.md"

    @pytest.fixture(autouse=True)
    def _skip_when_not_installed(self):
        if not self.PLIST_PATH.is_file():
            pytest.skip(f"no receiver installed at {self.INSTALL_DIR} — machine state, not repo state")

    def test_a_keepalive_plist_and_an_install_md_sit_together(self):
        assert self.PLIST_PATH.is_file()
        assert self.INSTALL_PATH.is_file()

    def test_plist_names_the_label_port_and_directory_each_exactly_once(self):
        text = self.PLIST_PATH.read_text()
        plist = plistlib.loads(text.encode())
        # The label is machine state's to choose; core asserts its SHAPE, not this machine's
        # name. Pinning the literal would put a person's name in the vendored layer.
        assert plist["Label"] == self.PLIST_PATH.stem
        assert re.fullmatch(r"[a-z0-9]+(\.[a-z0-9-]+)+", plist["Label"])
        assert plist["KeepAlive"] is True
        assert len(re.findall(r"4318", text)) == 1
        assert len(re.findall(r"\.kensaiapp/telemetry", text)) == 1

    def test_plist_publishes_the_endpoint_where_instrument_run_reads_it(self):
        # The receiver and the launchers meet at one file. The plist names where the receiver
        # writes it and `instrument_run.sh` names where it reads it; if the two ever disagree,
        # every launcher runs uninstrumented and says so politely, which is easy to miss.
        command = plistlib.loads(self.PLIST_PATH.read_bytes())["ProgramArguments"][-1]
        library = (Path(otel_receiver.__file__).parent / "instrument_run.sh").read_text()
        assert "--publish-endpoint" in command
        assert ".claude/tools/otel-receiver/endpoint" in command
        assert ".claude/tools/otel-receiver/endpoint" in library

    def test_install_md_states_the_launchctl_commands_and_that_they_are_the_owners_move(self):
        text = self.INSTALL_PATH.read_text()
        assert "launchctl bootstrap" in text
        assert "launchctl kickstart" in text
        assert "launchctl bootout" in text
        assert re.search(r"owner", text, re.IGNORECASE)

    def test_the_plists_own_command_starts_a_serving_receiver(self, tmp_path):
        """Task 6's intent is that **the machine can start it**. Counting the strings in the
        plist cannot see whether the command it hands launchd is one launchd can run — and a
        `KeepAlive` agent whose command cannot exec does not fail loudly, it respawns forever
        while every run's telemetry goes nowhere.

        So: drive the plist's *own* `ProgramArguments`, swapping only the three values it pins
        to this machine — the script path, the port and the directory — for test-safe ones. The
        shape of the command bash is handed is the plist's, untouched.
        """
        plist = plistlib.loads(self.PLIST_PATH.read_bytes())
        argv = list(plist["ProgramArguments"])
        port = _free_port()
        # Each substitution replaces the path/port *token* only and leaves whatever quoting
        # the plist puts around it exactly as it is — the quoting is the thing under test.
        command = argv[-1]
        command = re.sub(r"[^\s\"']*otel_receiver\.py", str(Path(otel_receiver.__file__)), command)
        command = command.replace("4318", str(port))
        command = re.sub(r"[^\s\"']*\.kensaiapp/telemetry", str(tmp_path), command)
        # The fourth value the plist pins to this machine: where the receiver publishes its
        # endpoint for `instrument_run.sh` to read. Left unswapped, this test's receiver would
        # write a throwaway port into the LIVE file, and every launcher after it would POST to
        # a port nothing listens on.
        command = re.sub(
            r"[^\s\"']*\.claude/tools/otel-receiver/endpoint",
            str(tmp_path / "published-endpoint"),
            command,
        )
        assert ".claude/tools/otel-receiver" not in command, command
        argv[-1] = command

        process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 15
            while True:
                if process.poll() is not None:
                    _, stderr = process.communicate()
                    pytest.fail(
                        "the plist's command exited with "
                        f"{process.returncode} instead of serving: "
                        f"{stderr.decode(errors='replace').strip()}"
                    )
                try:
                    status, _ = _post(port, "/v1/logs", b'{"cost_usd": 0.2}')
                    break
                except OSError:
                    if time.monotonic() > deadline:
                        pytest.fail("the plist's command never started serving")
                    time.sleep(0.2)
            assert status // 100 == 2
            record = json.loads((tmp_path / "logs.jsonl").read_text().splitlines()[0])
            assert record["body"]["cost_usd"] == 0.2
        finally:
            process.terminate()
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()

    def test_nothing_under_launchagents_is_referenced_by_the_module_itself(self):
        source = Path(otel_receiver.__file__).read_text()
        assert "LaunchAgents" not in source
        assert "launchctl" not in source
