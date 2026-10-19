"""The `warm_executables` facility in `conftest.py`, checked against what it is for.

Why the facility exists is `conftest.py`'s module docstring. What it must do, checked here: one
warm file per distinct stub body, exec'd once while it is linked and never again;
per-case data reaching the stub from the environment; a case reaching the stub by name through a
symlink in its own `bin/`; a warm-up that leaves no trace in any case's log; a warm file no case
can write through; and no two workers sharing a file.

Each case that must see the warm-up happen builds its own instance over a fresh directory, because
the session fixture has already warmed any body another case linked, and a body that is already
warm is never exec'd again.
"""

from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

import pytest


def _fresh(warm_executables, directory: Path):
    """A facility of its own over `directory` — how a second worker would hold one."""
    directory.mkdir()
    return type(warm_executables)(directory)


def _unique_body(*lines: str) -> str:
    """A body no other case links, so linking it is its first warm-up."""
    return "#!/usr/bin/env bash\n# " + uuid.uuid4().hex + "\n" + "\n".join(lines) + "\n"


def test_a_linked_stub_runs_by_name_from_the_case_bin_with_the_case_data(warm_executables,
                                                                        tmp_path):
    bin_dir = tmp_path / "bin"
    log = tmp_path / "case.log"
    warm_executables.link(bin_dir / "caffeinate",
                          '#!/usr/bin/env bash\necho "$@" >> "$CAFFEINATE_ARGV_LOG"\n')

    env = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
               CAFFEINATE_ARGV_LOG=str(log))
    result = subprocess.run(["caffeinate", "-dimsu", "-w", "123"], env=env,
                            capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    assert (bin_dir / "caffeinate").is_symlink()
    assert log.read_text() == "-dimsu -w 123\n"


def test_one_body_is_one_warm_file_however_many_cases_link_it(warm_executables, tmp_path):
    body = _unique_body("exit 0")
    first = warm_executables.link(tmp_path / "a" / "bin" / "claude", body)
    second = warm_executables.link(tmp_path / "b" / "bin" / "claude", body)
    other = warm_executables.link(tmp_path / "c" / "bin" / "claude", _unique_body("exit 0"))

    assert first.resolve() == second.resolve()
    assert other.resolve() != first.resolve()


def test_the_warm_file_is_exec_d_once_while_linking_and_never_again(warm_executables, tmp_path):
    warm = _fresh(warm_executables, tmp_path / "warm")
    runs = tmp_path / "runs.log"
    body = _unique_body(f'echo ran >> "{runs}"')

    warm.link(tmp_path / "a" / "stub", body)
    assert runs.read_text() == "ran\n", "the first exec happens while the stub is linked"

    warm.link(tmp_path / "b" / "stub", body)
    assert runs.read_text() == "ran\n", "a body already warm is not exec'd again"


def test_the_warm_up_leaves_no_trace_in_a_case_log(warm_executables, tmp_path, monkeypatch):
    case_log = tmp_path / "case.log"
    monkeypatch.setenv("WARM_TEST_CASE_LOG", str(case_log))
    warm = _fresh(warm_executables, tmp_path / "warm")
    ran = tmp_path / "ran"
    body = _unique_body(f'touch "{ran}"', 'echo warm-up >> "$WARM_TEST_CASE_LOG"')

    warm.link(tmp_path / "bin" / "stub", body)

    assert ran.exists(), "the warm-up ran the body"
    assert not case_log.exists(), "the warm-up wrote where a case reads"


def test_a_write_through_a_link_fails_and_leaves_the_shared_stub_as_it_was(warm_executables,
                                                                          tmp_path):
    body = _unique_body("exit 0")
    link = warm_executables.link(tmp_path / "bin" / "claude", body)

    with pytest.raises(PermissionError):
        link.write_text("#!/usr/bin/env bash\nexit 1\n")

    assert link.resolve().read_text() == body


def test_a_stub_that_never_exits_neither_holds_linking_nor_outlives_it(warm_executables,
                                                                       tmp_path):
    warm = _fresh(warm_executables, tmp_path / "warm")
    marker = f"86399.{uuid.uuid4().int % 10**9}"
    body = _unique_body(f"sleep {marker} &", f"exec sleep {marker}")

    warm.link(tmp_path / "bin" / "caffeinate", body)

    left = subprocess.run(["pgrep", "-f", f"sleep {marker}"], capture_output=True, text=True)
    assert left.stdout == "", f"the warm-up left processes behind: {left.stdout!r}"


def test_two_workers_never_share_a_warm_file(warm_executables, tmp_path):
    body = _unique_body("exit 0")
    one = _fresh(warm_executables, tmp_path / "gw0")
    two = _fresh(warm_executables, tmp_path / "gw1")

    first = one.link(tmp_path / "a" / "stub", body).resolve()
    second = two.link(tmp_path / "b" / "stub", body).resolve()

    assert first != second
    assert first.parent == (tmp_path / "gw0").resolve()
    assert second.parent == (tmp_path / "gw1").resolve()
