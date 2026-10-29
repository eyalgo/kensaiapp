"""Integration test of the suite's launch condition, through a real start (layer 2).

Checks SRS NFR-11 (the automated suite has an integration layer that drives the real start). SDD
§ 4 TS-2 (a test patches no name inside a part) and NFDR QC-11 (a test module names what it
checks) are the other clauses the test answers to.

A suite started as a background job can arrive with SIGINT ignored, and a tracker a test starts
inherits that, so the SIGINT the test sends never stops it. The session fixture in
tests/conftest.py gives the test process Python's own interrupt handler, which that tracker does
not inherit. This test shows the fixture's effect from outside it: it starts a second pytest with
SIGINT ignored before that pytest begins, so the second pytest arrives with exactly the launch the
fixture exists to survive. The second pytest runs one real-start case of
tests/integration/test_start.py, which starts the product's own start in a child process and stops
it with a real SIGINT. That case passes only when the tracker stops, exits 0 and writes nothing to
standard error. Without the fixture the tracker keeps running and the case fails on its stop
deadline. The test patches no name in the product and starts no tracker itself.
"""

from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
from pathlib import Path

PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent
SELECTED_CASE = (
    "tests/integration/test_start.py"
    "::test_start_reads_each_legacy_form_with_every_existing_value[projects-only]"
)
# The shell ignores INT, then replaces itself with the command it was handed, so the command
# starts with the ignored disposition a background job gives it and the shell stays out of its way.
IGNORE_INTERRUPT_THEN_RUN = 'trap "" INT; exec "$@"'
# Longer than the 30 seconds the selected case waits for its tracker to stop, so that case's own
# report reaches this test's failure message instead of an outer timeout hiding it.
OUTER_DEADLINE_SECONDS = 120
ONE_CASE_PASSED = re.compile(r"^1 passed(, \d+ warnings?)? in ", re.MULTILINE)


def test_real_start_stops_when_pytest_launch_ignores_sigint() -> None:
    """NFR-11: a real start stops on SIGINT in a pytest whose launch ignored SIGINT."""
    command = [
        "/bin/sh",
        "-c",
        IGNORE_INTERRUPT_THEN_RUN,
        "sh",
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        SELECTED_CASE,
    ]
    launch = subprocess.Popen(
        command,
        cwd=PRODUCT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        output, errors = launch.communicate(timeout=OUTER_DEADLINE_SECONDS)
    except subprocess.TimeoutExpired:
        os.killpg(launch.pid, signal.SIGKILL)
        output, errors = launch.communicate()
        raise AssertionError(
            f"the launched pytest outlasted {OUTER_DEADLINE_SECONDS} seconds\n"
            f"standard output:\n{output}\nstandard error:\n{errors}"
        ) from None
    finally:
        if launch.poll() is None:
            os.killpg(launch.pid, signal.SIGKILL)
            launch.wait()

    report = f"standard output:\n{output}\nstandard error:\n{errors}"
    assert launch.returncode == 0, report
    assert ONE_CASE_PASSED.search(output) is not None, report
