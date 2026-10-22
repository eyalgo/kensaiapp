"""The layer-5 harness: a tracker run as a child process, and Chromium driven through Playwright.

Each tracker is started through `main.start` on a free port with its own saved-data location, from a
working directory that is not the product root, and stopped with SIGINT, as an operator stops one.
Realizes SRS FR-1 and FR-2 for the end-to-end tests (docs/nfdr.md § 9, layer 5).
"""

from __future__ import annotations

import os
import queue
import signal
import socket
import subprocess
import sys
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page, Playwright, sync_playwright

PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent
READY_TIMEOUT_SECONDS = 30
STOP_TIMEOUT_SECONDS = 30
START_PROGRAM = (
    "import sys\n"
    "from pathlib import Path\n"
    "import main\n"
    "raise SystemExit(main.start((sys.argv[1], int(sys.argv[2])), Path(sys.argv[3])))\n"
)


@dataclass
class RunningTracker:
    """One tracker process. `first_line` is the first thing it wrote to stdout."""

    process: subprocess.Popen[str]
    host: str
    port: int
    location: Path
    first_line: str
    lines: queue.Queue[str] = field(default_factory=queue.Queue)

    @property
    def address(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def saved_file(self) -> Path:
        return self.location / "tracker.json"

    def stop(self) -> tuple[int, str]:
        """Send SIGINT, as Ctrl-C does, and return the exit status and what it wrote to stderr."""
        self.process.send_signal(signal.SIGINT)
        try:
            _, stderr = self.process.communicate(timeout=STOP_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            self.process.kill()
            raise
        return self.process.returncode, stderr or ""


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class TrackerFactory:
    """Starts trackers and stops any still running when the test ends."""

    def __init__(self, working_directory: Path) -> None:
        self._working_directory = working_directory
        self._running: list[RunningTracker] = []

    def start(self, location: Path) -> RunningTracker:
        host, port = "127.0.0.1", _free_port()
        process = subprocess.Popen(
            [sys.executable, "-c", START_PROGRAM, host, str(port), str(location)],
            cwd=self._working_directory,
            env={**os.environ, "PYTHONPATH": str(PRODUCT_ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert process.stdout is not None
        first: queue.Queue[str] = queue.Queue()
        threading.Thread(target=lambda: first.put(process.stdout.readline()), daemon=True).start()
        try:
            first_line = first.get(timeout=READY_TIMEOUT_SECONDS).rstrip("\n")
        except queue.Empty:
            process.kill()
            raise AssertionError("the tracker wrote nothing before the timeout") from None
        tracker = RunningTracker(process, host, port, location, first_line)
        self._running.append(tracker)
        return tracker

    def stop_all(self) -> None:
        for tracker in self._running:
            if tracker.process.poll() is None:
                tracker.process.kill()
                tracker.process.communicate()


@pytest.fixture
def trackers(tmp_path: Path) -> Iterator[TrackerFactory]:
    working_directory = tmp_path / "elsewhere"
    working_directory.mkdir()
    factory = TrackerFactory(working_directory)
    yield factory
    factory.stop_all()


@pytest.fixture
def location(tmp_path: Path) -> Path:
    return tmp_path / "data"


@pytest.fixture
def tracker(trackers: TrackerFactory, location: Path) -> RunningTracker:
    return trackers.start(location)


@pytest.fixture(scope="session")
def playwright_instance() -> Iterator[Playwright]:
    with sync_playwright() as instance:
        yield instance


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Iterator[Browser]:
    chromium = playwright_instance.chromium.launch()
    yield chromium
    chromium.close()


# The one launch default the driver sets that bears on history traversal: it turns the browser's
# back/forward cache off. Read from the pinned driver's `chromiumSwitches` (playwright 1.63.0,
# `--disable-back-forward-cache`); every other default is left in place. The headless shell the
# default launch uses never restores a page from that cache even without the switch (measured with
# a plain page: `pageshow.persisted` stayed false), so the history proof launches the full Chromium
# the same lock installs, through its `chromium` channel.
HISTORY_CACHE_SWITCH = "--disable-back-forward-cache"


@pytest.fixture(scope="session")
def history_browser(playwright_instance: Playwright) -> Iterator[Browser]:
    """A browser whose history cache is available, for the history-traversal proof alone."""
    chromium = playwright_instance.chromium.launch(
        channel="chromium", ignore_default_args=[HISTORY_CACHE_SWITCH]
    )
    yield chromium
    chromium.close()


@pytest.fixture
def history_page(history_browser: Browser) -> Iterator[Page]:
    context = history_browser.new_context()
    context.set_default_timeout(15000)
    yield context.new_page()
    context.close()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    context = browser.new_context()
    context.set_default_timeout(15000)
    yield context.new_page()
    context.close()
