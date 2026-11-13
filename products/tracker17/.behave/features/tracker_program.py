"""The tracker, started as its operator starts it: `main.py` run from the tracker's directory, then
stopped with Ctrl-C.

The scenario's tracker runs from a copy of the tracker's directory with no `data/` in it, so it
starts on no saved data and never touches the saved data of the copy it was taken from. Python's
standard library only.
"""

from __future__ import annotations

import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

# features/ -> .behave/ -> the tracker's directory, the one that holds main.py.
TRACKER_DIRECTORY = Path(__file__).resolve().parent.parent.parent
READY_TIMEOUT_SECONDS = 30
STOP_TIMEOUT_SECONDS = 30
READY_LINE_START = "The tracker is running."
ADDRESS_IN_LINE = re.compile(r"Open (http://\S+) in your browser")
# What the copy leaves out: the saved data, the test code and what a run leaves behind.
LEFT_OUT = ("data", ".behave", "tests", ".venv", "__pycache__", ".git", "docs")


@dataclass
class RunningTracker:
    process: subprocess.Popen[str]
    address: str
    directory: Path

    def stop(self) -> None:
        """Press Ctrl-C, as the operator stops it, and remove the copy it ran from."""
        try:
            if self.process.poll() is None:
                self.process.send_signal(signal.SIGINT)
                try:
                    self.process.communicate(timeout=STOP_TIMEOUT_SECONDS)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.communicate()
        finally:
            shutil.rmtree(self.directory, ignore_errors=True)


def start_tracker() -> RunningTracker:
    """Start the tracker on no saved data and give it back once it says it is running."""
    scratch = Path(tempfile.mkdtemp(prefix="tracker-scenario-"))
    directory = scratch / "tracker17"
    shutil.copytree(TRACKER_DIRECTORY, directory, ignore=shutil.ignore_patterns(*LEFT_OUT))
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=directory,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdout is not None
    stdout = process.stdout
    first: queue.Queue[str] = queue.Queue()
    threading.Thread(target=lambda: first.put(stdout.readline()), daemon=True).start()
    tracker = RunningTracker(process, "", scratch)
    try:
        line = first.get(timeout=READY_TIMEOUT_SECONDS).rstrip("\n")
    except queue.Empty:
        tracker.stop()
        raise AssertionError("The tracker wrote nothing before the timeout.") from None
    found = ADDRESS_IN_LINE.search(line)
    if not line.startswith(READY_LINE_START) or found is None:
        tracker.stop()
        _, errors = process.communicate()
        raise AssertionError(f"The tracker did not start: {line!r} {errors!r}")
    tracker.address = found.group(1)
    return tracker
