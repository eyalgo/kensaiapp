"""Integration test of what the ignored-SIGINT proof test does to the machine's shared temp root
(layer 2), through real pytest processes.

Checks SRS NFR-11 (the automated suite has an integration layer that drives the real start, and
its proof that a start stops on SIGINT holds in a full run). SDD § 4 TS-2 (a test patches no name
inside a part) and NFDR QC-11 (a test module names what it checks) are the other clauses the test
answers to.

The cause this test measures: a pytest started with no base folder of its own takes its base from
the temp root that every pytest session on the machine shares, a folder named for the user, under
the system temp folder. When that pytest exits it deletes each earlier session folder that is three
or more numbers below the newest and holds no live lock, and a lock older than three days counts as
dead. How long that takes depends on what other sessions left behind, and all of it runs inside
the outer deadline of the proof test in tests/integration/test_sigint_launch.py. The 30 seconds
its selected case waits for the tracker to stop are not involved, because the clean-up runs after
that case has finished.

The test measures that dependence by its effect, so it needs no slow machine and no full run. It
points the shared temp root at a private one under tmp_path, plants in it a leftover session that
pytest would delete, and runs the proof test against it. The proof test passes only when the pytest
it launches leaves the private root exactly as it found it. Nothing is patched: the temp root
reaches the processes through their environment, and each base folder is a path handed to them.
"""

from __future__ import annotations

import getpass
import os
import signal
import subprocess
import sys
from pathlib import Path

from test_sigint_launch import ONE_CASE_PASSED, OUTER_DEADLINE_SECONDS, PRODUCT_ROOT

PROOF_TEST = (
    "tests/integration/test_sigint_launch.py"
    "::test_real_start_stops_when_pytest_launch_ignores_sigint"
)
TEMP_ROOT_VARIABLE = "PYTEST_DEBUG_TEMPROOT"
# Longer than the proof test's own deadline, for the same reason that one is longer than the
# selected case's 30 seconds: the proof test's report reaches this test's failure message instead
# of an outer timeout hiding it.
NESTED_DEADLINE_SECONDS = OUTER_DEADLINE_SECONDS + 60


def listing_of(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def test_launched_pytest_leaves_the_shared_temp_root_alone(tmp_path: Path) -> None:
    """NFR-11: the proof test's launched pytest makes and deletes nothing in the shared temp root."""
    temp_root = tmp_path / "shared-temp-root"
    user_folder = temp_root / f"pytest-of-{getpass.getuser()}"
    leftover = user_folder / "pytest-1"
    leftover.mkdir(parents=True)
    (leftover / "leftover-entry").write_text("left by an earlier session\n", encoding="utf-8")
    (user_folder / "pytest-5").mkdir()
    before = listing_of(temp_root)

    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "--basetemp",
        str(tmp_path / "nested-base"),
        PROOF_TEST,
    ]
    nested = subprocess.Popen(
        command,
        cwd=PRODUCT_ROOT,
        env={**os.environ, TEMP_ROOT_VARIABLE: str(temp_root)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        output, errors = nested.communicate(timeout=NESTED_DEADLINE_SECONDS)
    except subprocess.TimeoutExpired:
        os.killpg(nested.pid, signal.SIGKILL)
        output, errors = nested.communicate()
        raise AssertionError(
            f"the nested pytest outlasted {NESTED_DEADLINE_SECONDS} seconds\n"
            f"standard output:\n{output}\nstandard error:\n{errors}"
        ) from None
    finally:
        if nested.poll() is None:
            os.killpg(nested.pid, signal.SIGKILL)
            nested.wait()

    report = f"standard output:\n{output}\nstandard error:\n{errors}"
    assert nested.returncode == 0, report
    assert ONE_CASE_PASSED.search(output) is not None, report
    assert listing_of(temp_root) == before, report
