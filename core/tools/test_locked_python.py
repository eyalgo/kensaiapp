"""Contract tests for `locked_python.sh` — the one runner every kensaiapp hook and launch goes
through.

Each test runs the real script as a subprocess, with a stub `python3` first on `PATH` that only
exits 1: if the runner ever reached the machine's `python3`, the stub would be what ran and the
test would see its exit status instead of the pinned Python's.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RUNNER = Path(__file__).resolve().parent / "locked_python.sh"
REPO_ROOT = RUNNER.parents[2]

# `change_text.md`'s message, with what did not run in place of {script}: the script's file name,
# `-c` for inline code, or `-` for a script on stdin.
MISSING_UV_MESSAGE = """\
kensaiapp: uv was not found on PATH, so {script} did not run.
kensaiapp's hooks, skills' commands and launches run on the Python the instance pins, through uv, and never fall back to python3.
Until uv is found, none of them runs, and a commit the git hooks check is refused.
Install uv with one of:
  brew install uv
  curl -LsSf https://astral.sh/uv/install.sh | sh
If uv is already installed, add the directory that holds it to PATH.
Guide: https://docs.astral.sh/uv/getting-started/installation/
"""

# `change_text.md`'s launch message, with the launcher's name in place of {launcher}.
LAUNCH_MISSING_UV_MESSAGE = """\
{launcher}: uv was not found on PATH, so nothing was launched.
kensaiapp's launchers run their Python through uv, on the Python that the instance's .python-version names, and never fall back to python3.
Until uv is found, no kensaiapp launcher runs.
Install uv with one of:
  brew install uv
  curl -LsSf https://astral.sh/uv/install.sh | sh
If uv is already installed, add the directory that holds it to PATH.
Guide: https://docs.astral.sh/uv/getting-started/installation/
"""

# The variables `uv run` rewrites or adds for the command it runs (measured 2026-10-26).
UV_REWRITTEN = ("PATH", "VIRTUAL_ENV", "UV", "UV_RUN_RECURSION_DEPTH")


def _stub_python3_dir(tmp_path: Path, marker: Path | None = None) -> Path:
    """A directory holding an executable `python3` that only exits 1 (and marks that it ran)."""
    stub_dir = tmp_path / "stub-bin"
    stub_dir.mkdir()
    stub = stub_dir / "python3"
    marking = f'echo ran > "{marker}"\n' if marker else ""
    stub.write_text(f"#!/bin/sh\n{marking}exit 1\n")
    stub.chmod(0o755)
    return stub_dir


def _run(
    args: list[str],
    *,
    path: str,
    cwd: Path,
    runner: Path = RUNNER,
    stdin: str = "",
    caller_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    # A hook starts outside any virtual environment. The suite itself runs under `uv run`, which
    # sets VIRTUAL_ENV to the repository's `.venv`; passed on, uv would fall back to that
    # environment when the runner names a root with no project, and a wrong root would still
    # print the repository's prefix. The same run also sets UV and UV_RUN_RECURSION_DEPTH, so a
    # caller of the runner starts without those too unless a test gives it them.
    env = {key: value for key, value in os.environ.items() if key not in UV_REWRITTEN}
    env["PATH"] = path
    env.update(caller_env or {})
    return subprocess.run(
        [str(runner), *args],
        cwd=str(cwd),
        env=env,
        input=stdin,
        capture_output=True,
        text=True,
    )


def _script(tmp_path: Path, body: str) -> Path:
    script = tmp_path / "hook_script.py"
    script.write_text(body)
    return script


def test_runs_on_the_python_the_root_names(tmp_path: Path) -> None:
    pinned = (REPO_ROOT / ".python-version").read_text().strip()
    stub_dir = _stub_python3_dir(tmp_path)
    workdir = tmp_path / "no-project-here"
    workdir.mkdir()
    script = _script(
        tmp_path, "import sys\nprint('%d.%d' % sys.version_info[:2])\n"
    )

    result = _run(
        [str(script)],
        path=f"{stub_dir}{os.pathsep}{os.environ['PATH']}",
        cwd=workdir,
    )

    assert (result.returncode, result.stdout.strip()) == (0, pinned), result.stderr


@pytest.mark.parametrize("status", [2, 3])
def test_stdin_args_streams_and_status_pass_through(tmp_path: Path, status: int) -> None:
    script = _script(
        tmp_path,
        "import sys\n"
        "print('stdin=' + sys.stdin.read())\n"
        "print('args=' + ','.join(sys.argv[1:]))\n"
        "print('to-stderr', file=sys.stderr)\n"
        f"sys.exit({status})\n",
    )

    result = _run(
        [str(script), "alpha", "two words"],
        path=os.environ["PATH"],
        cwd=tmp_path,
        stdin="payload",
    )

    assert result.returncode == status
    assert result.stdout == "stdin=payload\nargs=alpha,two words\n"
    assert result.stderr == "to-stderr\n"


def test_the_root_is_the_runners_own_not_the_cwd(tmp_path: Path) -> None:
    script = _script(tmp_path, "import sys\nprint(sys.prefix)\n")
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()

    result = _run([str(script)], path=os.environ["PATH"], cwd=unrelated)

    assert result.returncode == 0, result.stderr
    assert Path(result.stdout.strip()).resolve() == (REPO_ROOT / ".venv").resolve()


MISSING_UV_PATH = f"{os.pathsep}/usr/bin{os.pathsep}/bin"


def _skip_if_uv_cannot_be_hidden() -> None:
    if shutil.which("uv", path="/usr/bin:/bin"):
        pytest.skip("uv is installed in /usr/bin or /bin, so it cannot be hidden from PATH")


def _refused_run(
    tmp_path: Path, args: list[str], *, stdin: str = "", cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run the real runner with uv hidden and a marking `python3` stub first on PATH."""
    _skip_if_uv_cannot_be_hidden()
    stub_dir = _stub_python3_dir(tmp_path, marker=tmp_path / "fallback-ran")
    return _run(
        args,
        path=f"{stub_dir}{MISSING_UV_PATH}",
        cwd=cwd or tmp_path,
        stdin=stdin,
    )


def _assert_refused(
    result: subprocess.CompletedProcess[str], tmp_path: Path, name: str
) -> None:
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == MISSING_UV_MESSAGE.format(script=name)
    assert not (tmp_path / "fallback-ran").exists()
    assert not (tmp_path / "payload-ran").exists()


def test_without_uv_it_prints_the_install_message_and_exits_1(tmp_path: Path) -> None:
    marker = tmp_path / "payload-ran"
    script = _script(
        tmp_path, f"from pathlib import Path\nPath({str(marker)!r}).write_text('x')\n"
    )

    result = _refused_run(tmp_path, [str(script)])

    _assert_refused(result, tmp_path, script.name)


@pytest.mark.parametrize(
    "invocation", ["absolute", "relative-from-a-folder", "relative-from-the-instance-root"]
)
def test_missing_uv_names_the_scripts_last_path_component(
    tmp_path: Path, invocation: str
) -> None:
    nested = tmp_path / "deeper" / "still"
    nested.mkdir(parents=True)
    script = nested / "suite_map.py"
    script.write_text("print('would run')\n")
    args, cwd = {
        "absolute": ([str(script)], tmp_path),
        "relative-from-a-folder": (["deeper/still/suite_map.py"], tmp_path),
        # The example of the refusal's rule: the script need not exist, since nothing runs.
        "relative-from-the-instance-root": (["core/tools/suite_map.py"], REPO_ROOT),
    }[invocation]

    result = _refused_run(tmp_path, args, cwd=cwd)

    _assert_refused(result, tmp_path, "suite_map.py")
    assert result.stderr.splitlines()[0] == (
        "kensaiapp: uv was not found on PATH, so suite_map.py did not run."
    )


@pytest.mark.parametrize(
    "code",
    [
        "print(1)",
        "from pathlib import Path; Path('payload-ran').write_text('x')",
    ],
)
def test_missing_uv_inline_code_is_refused_without_running_python(
    tmp_path: Path, code: str
) -> None:
    result = _refused_run(tmp_path, ["-c", code])

    _assert_refused(result, tmp_path, "-c")
    assert "basename" not in result.stderr


@pytest.mark.parametrize(
    "payload", ["", "from pathlib import Path\nPath('payload-ran').write_text('x')\n"]
)
def test_missing_uv_stdin_is_refused_without_running_python(
    tmp_path: Path, payload: str
) -> None:
    result = _refused_run(tmp_path, ["-"], stdin=payload)

    _assert_refused(result, tmp_path, "-")
    assert "basename" not in result.stderr


FORMER_HOOKS_ONLY_LINE = (
    "kensaiapp's hooks run on the Python the instance pins, through uv, "
    "and never fall back to python3."
)

# CP-939's prohibited pattern: nothing in the runner may say or imply that only hooks use it.
ONLY_HOOKS_PATTERN = re.compile(
    r"only (the )?hooks?|hooks? (only|alone)|kensaiapp.s hooks run on", re.I
)


@pytest.mark.parametrize("form", ["script", "inline", "stdin"])
def test_missing_uv_refusal_names_every_stopped_run(tmp_path: Path, form: str) -> None:
    script = _script(tmp_path, "print('would run')\n")
    args, name = {
        "script": ([str(script)], script.name),
        "inline": (["-c", "print(1)"], "-c"),
        "stdin": (["-"], "-"),
    }[form]

    result = _refused_run(tmp_path, args)

    lines = result.stderr.splitlines()
    assert lines[0] == f"kensaiapp: uv was not found on PATH, so {name} did not run."
    assert lines[-5:] == MISSING_UV_MESSAGE.splitlines()[-5:]
    for category in ("hook", "skill", "launch"):
        assert category in result.stderr.lower()
    assert FORMER_HOOKS_ONLY_LINE not in lines
    # CP-937 on what is printed, not only on the runner's source: no line says hooks alone use it.
    assert not [line for line in lines if ONLY_HOOKS_PATTERN.search(line)]


def _runner_header() -> str:
    lines = RUNNER.read_text().splitlines()
    end = next(i for i, line in enumerate(lines) if line.startswith("set -euo pipefail"))
    return "\n".join(lines[:end])


def test_runner_header_names_every_supported_use() -> None:
    assert not [
        line for line in RUNNER.read_text().splitlines() if ONLY_HOOKS_PATTERN.search(line)
    ]
    header = _runner_header()
    introduction = header.split("# Version:")[0].lower()
    why = header.split("WHY THIS EXISTS")[1].split("\n#\n")[0].lower()
    for text in (introduction, why):
        for category in ("hook", "skill", "launch"):
            assert category in text


def test_inline_print_runs_when_uv_is_found(tmp_path: Path) -> None:
    result = _run(["-c", "print(1)"], path=os.environ["PATH"], cwd=tmp_path)

    assert (result.returncode, result.stdout, result.stderr) == (0, "1\n", "")


def test_a_first_run_prints_nothing_of_uvs_own(tmp_path: Path) -> None:
    root = tmp_path / "instance"
    runner = root / "core" / "tools" / "locked_python.sh"
    runner.parent.mkdir(parents=True)
    shutil.copy2(RUNNER, runner)
    for name in (".python-version", "pyproject.toml", "uv.lock"):
        shutil.copy2(REPO_ROOT / name, root / name)
    script = _script(tmp_path, "pass\n")

    result = _run([str(script)], path=os.environ["PATH"], cwd=tmp_path, runner=runner)

    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    assert (root / ".venv").is_dir()



def test_a_first_run_installs_nothing_into_the_roots_venv(tmp_path: Path) -> None:
    root = tmp_path / "instance"
    runner = root / "core" / "tools" / "locked_python.sh"
    runner.parent.mkdir(parents=True)
    shutil.copy2(RUNNER, runner)
    for name in (".python-version", "pyproject.toml", "uv.lock"):
        shutil.copy2(REPO_ROOT / name, root / name)
    script = _script(tmp_path, "pass\n")

    result = _run([str(script)], path=os.environ["PATH"], cwd=tmp_path, runner=runner)

    assert result.returncode == 0, result.stderr
    installed = [p.name for p in (root / ".venv").glob("lib/python*/site-packages/*pytest*")]
    assert installed == []


def _other_minor(pinned: str) -> str:
    """A Python minor version that is not the pinned one, for a working directory to pin."""
    major, minor = pinned.split(".")[:2]
    return f"{major}.{int(minor) - 1}"


def test_a_working_directory_that_pins_another_python_is_not_read(tmp_path: Path) -> None:
    """CP-879 — a git hook runs in whichever repository is committing, and a satellite's root may
    pin a Python of its own. Its `pyproject.toml` and `.python-version` play no part: the script
    runs on the runner's own root's Python, in that root's `.venv`."""
    pinned = (REPO_ROOT / ".python-version").read_text().strip()
    other = _other_minor(pinned)
    satellite = tmp_path / "satellite"
    satellite.mkdir()
    (satellite / ".python-version").write_text(f"{other}\n")
    (satellite / "pyproject.toml").write_text(
        f'[project]\nname = "satellite"\nversion = "0"\nrequires-python = ">={other}"\n'
    )
    script = _script(
        tmp_path, "import sys\nprint('%d.%d' % sys.version_info[:2])\nprint(sys.prefix)\n"
    )

    result = _run([str(script)], path=os.environ["PATH"], cwd=satellite)

    assert result.returncode == 0, result.stderr
    version, prefix = result.stdout.splitlines()
    assert version == pinned
    assert Path(prefix).resolve() == (REPO_ROOT / ".venv").resolve()
    assert not (satellite / ".venv").exists()


def test_a_runner_reached_through_a_symlinked_core_finds_the_real_root(tmp_path: Path) -> None:
    """Task 1 — the root is two directories above the runner's *real* directory. A runner reached
    through a link to this core (a `core` link in a directory that holds no lock) still runs on
    this root's Python, not on whatever uv finds for the link's own directory."""
    linked_root = tmp_path / "linked"
    linked_root.mkdir()
    (linked_root / "core").symlink_to(REPO_ROOT / "core", target_is_directory=True)
    linked_runner = linked_root / "core" / "tools" / "locked_python.sh"
    script = _script(tmp_path, "import sys\nprint(sys.prefix)\n")

    result = _run(
        [str(script)], path=os.environ["PATH"], cwd=linked_root, runner=linked_runner
    )

    assert result.returncode == 0, result.stderr
    assert Path(result.stdout.strip()).resolve() == (REPO_ROOT / ".venv").resolve()
    assert not (linked_root / ".venv").exists()


def test_a_run_leaves_the_roots_lock_and_project_files_as_they_were(tmp_path: Path) -> None:
    """Out of scope: `uv.lock` is not regenerated, and nothing is added to `pyproject.toml`. A
    hook runs at every session start, so a runner that let uv re-lock would rewrite a tracked
    file of the root it reads — even where `pyproject.toml` no longer matches `uv.lock`."""
    root = tmp_path / "instance"
    runner = root / "core" / "tools" / "locked_python.sh"
    runner.parent.mkdir(parents=True)
    shutil.copy2(RUNNER, runner)
    for name in (".python-version", "pyproject.toml", "uv.lock"):
        shutil.copy2(REPO_ROOT / name, root / name)
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text().replace("dependencies = [", 'dependencies = [\n    "idna",', 1)
    )
    before = {name: (root / name).read_bytes() for name in ("pyproject.toml", "uv.lock")}
    assert b'"idna"' in before["pyproject.toml"], "the fixture must make the lock stale"
    script = _script(tmp_path, "pass\n")

    result = _run([str(script)], path=os.environ["PATH"], cwd=tmp_path, runner=runner)

    assert result.returncode == 0, result.stderr
    after = {name: (root / name).read_bytes() for name in ("pyproject.toml", "uv.lock")}
    assert after == before


def _launch_check(args: list[str], path: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return _run(["--check", *args], path=path, cwd=cwd)


def test_the_check_is_silent_when_uv_is_found(tmp_path: Path) -> None:
    result = _launch_check(["skill"], os.environ["PATH"], tmp_path)

    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_the_check_without_uv_prints_the_launch_message_and_exits_1(tmp_path: Path) -> None:
    if shutil.which("uv", path="/usr/bin:/bin"):
        pytest.skip("uv is installed in /usr/bin or /bin, so it cannot be hidden from PATH")
    marker = tmp_path / "stub-ran"
    stub_dir = _stub_python3_dir(tmp_path, marker=marker)

    result = _launch_check(
        ["skill"], f"{stub_dir}{os.pathsep}/usr/bin{os.pathsep}/bin", tmp_path
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == LAUNCH_MISSING_UV_MESSAGE.format(launcher="skill")
    assert not marker.exists()


def test_the_check_names_the_launcher_it_was_given(tmp_path: Path) -> None:
    if shutil.which("uv", path="/usr/bin:/bin"):
        pytest.skip("uv is installed in /usr/bin or /bin, so it cannot be hidden from PATH")

    result = _launch_check(["launch-audit"], "/usr/bin:/bin", tmp_path)

    assert result.stderr == LAUNCH_MISSING_UV_MESSAGE.format(launcher="launch-audit")


def test_the_check_without_a_launcher_name_is_refused_and_runs_no_python(tmp_path: Path) -> None:
    marker = tmp_path / "stub-ran"
    stub_dir = _stub_python3_dir(tmp_path, marker=marker)

    result = _launch_check([], f"{stub_dir}{os.pathsep}{os.environ['PATH']}", tmp_path)

    assert result.returncode == 1
    assert result.stdout == ""
    assert "--check" in result.stderr
    assert not marker.exists()


CHILD_REPORT = """\
import json
import subprocess

report = {}
for name in ("PATH", "VIRTUAL_ENV", "UV", "UV_RUN_RECURSION_DEPTH"):
    probe = 'if [ "${%s+x}" ]; then printf "set:%%s" "$%s"; else printf unset; fi' % (name, name)
    seen = subprocess.run(["/bin/sh", "-c", probe], capture_output=True, text=True).stdout
    report[name] = None if seen == "unset" else seen[len("set:"):]
print(json.dumps(report))
"""


def _child_environment(
    tmp_path: Path, *, path: str, caller_env: dict[str, str] | None = None
) -> dict[str, str | None]:
    """What a process the script starts sees of the variables `uv run` rewrites; None is unset."""
    result = _run(
        [str(_script(tmp_path, CHILD_REPORT))], path=path, cwd=tmp_path, caller_env=caller_env
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_a_child_of_the_script_sees_the_callers_path(tmp_path: Path) -> None:
    # The suite itself runs under `uv run`, so its own PATH already leads to the root's `.venv`;
    # the caller here has none, which is what makes an added `.venv/bin` show.
    venv_bin = str(REPO_ROOT / ".venv" / "bin")
    inherited = [entry for entry in os.environ["PATH"].split(os.pathsep) if entry != venv_bin]
    caller_path = os.pathsep.join([str(tmp_path / "caller-bin"), *inherited])

    seen = _child_environment(tmp_path, path=caller_path)

    assert seen["PATH"] == caller_path


@pytest.mark.parametrize("caller_value", [None, "/caller/venv", ""])
def test_a_child_sees_virtual_env_as_the_caller_had_it(
    tmp_path: Path, caller_value: str | None
) -> None:
    caller_env = None if caller_value is None else {"VIRTUAL_ENV": caller_value}

    seen = _child_environment(tmp_path, path=os.environ["PATH"], caller_env=caller_env)

    assert seen["VIRTUAL_ENV"] == caller_value


def test_a_child_sees_no_uv_recursion_variable(tmp_path: Path) -> None:
    seen = _child_environment(tmp_path, path=os.environ["PATH"])

    assert seen["UV_RUN_RECURSION_DEPTH"] is None
    assert seen["UV"] is None


def test_a_child_sees_uvs_variables_as_the_caller_had_them(tmp_path: Path) -> None:
    caller_env = {"UV": "/caller/uv", "UV_RUN_RECURSION_DEPTH": "7"}

    seen = _child_environment(tmp_path, path=os.environ["PATH"], caller_env=caller_env)

    assert (seen["UV"], seen["UV_RUN_RECURSION_DEPTH"]) == ("/caller/uv", "7")


def test_the_runners_own_handover_variables_do_not_reach_a_child(tmp_path: Path) -> None:
    script = _script(
        tmp_path,
        "import os\nprint(sorted(k for k in os.environ if k.startswith('KENSAIAPP_CALLER_')))\n",
    )

    result = _run([str(script)], path=os.environ["PATH"], cwd=tmp_path)

    assert (result.returncode, result.stdout) == (0, "[]\n"), result.stderr


def test_the_script_still_runs_on_the_pinned_python_with_python3_stubbed(tmp_path: Path) -> None:
    pinned = (REPO_ROOT / ".python-version").read_text().strip()
    marker = tmp_path / "stub-ran"
    stub_dir = _stub_python3_dir(tmp_path, marker=marker)
    script = _script(tmp_path, "import sys\nprint('%d.%d' % sys.version_info[:2])\n")

    result = _run(
        [str(script)], path=f"{stub_dir}{os.pathsep}{os.environ['PATH']}", cwd=tmp_path
    )

    assert (result.returncode, result.stdout.strip()) == (0, pinned), result.stderr
    assert not marker.exists()


def test_inline_code_and_a_script_on_stdin_run_as_python3_ran_them(tmp_path: Path) -> None:
    inline = _run(
        ["-c", "import sys; print(sys.argv[1])", "arg"], path=os.environ["PATH"], cwd=tmp_path
    )
    piped = _run(
        ["-", "arg"], path=os.environ["PATH"], cwd=tmp_path,
        stdin="import sys\nprint(sys.argv[1])\n",
    )

    assert (inline.returncode, inline.stdout) == (0, "arg\n"), inline.stderr
    assert (piped.returncode, piped.stdout) == (0, "arg\n"), piped.stderr


LOCK_FILES = (".python-version", "pyproject.toml", "uv.lock")


def _preparation_roots(tmp_path: Path, *, bootstrap: bool = True) -> tuple[Path, Path]:
    host = tmp_path / "source host"
    target = tmp_path / "copied pin"
    for root in (host, target):
        runner = root / "core" / "tools" / "locked_python.sh"
        runner.parent.mkdir(parents=True)
        shutil.copy2(RUNNER, runner)
        for name in LOCK_FILES:
            shutil.copy2(REPO_ROOT / name, root / name)
    if bootstrap:
        result = _run(
            ["-c", "pass"], path=os.environ["PATH"], cwd=tmp_path,
            runner=host / "core" / "tools" / "locked_python.sh",
        )
        assert result.returncode == 0, result.stderr
    return host, target


def _prepare(host: Path, target: Path, tmp_path: Path, *, caller_env=None, path=None):
    return _run(
        ["--prepare-pin", str(target)], path=path or os.environ["PATH"], cwd=tmp_path,
        runner=host / "core" / "tools" / "locked_python.sh", caller_env=caller_env,
    )


def _python_report(root: Path) -> dict:
    result = subprocess.run(
        [str(root / ".venv" / "bin" / "python"), "-c",
         "import json,sys; print(json.dumps([sys.version, sys.prefix]))"],
        capture_output=True, text=True, check=True,
    )
    version, prefix = json.loads(result.stdout)
    return {"version": version, "prefix": Path(prefix).resolve()}


def _forwarding_python3(tmp_path: Path) -> tuple[str, Path]:
    """A `python3` first on PATH that logs whoever runs it, then runs the suite's own Python.

    The log is the proof that nothing discovered a Python on PATH; the Python it forwards to only
    keeps a caller that may use one working. It is the suite's own, not a path on the machine."""
    forward = Path(sys.executable)
    directory = tmp_path / "forward-bin"
    directory.mkdir()
    marker = tmp_path / "full-parent-log"
    probe = directory / "python3"
    probe.write_text(
        f'#!/bin/sh\nps -o command= -p $PPID >> "{marker}"\nexec "{forward}" "$@"\n'
    )
    probe.chmod(0o755)
    return f"{directory}{os.pathsep}{os.environ['PATH']}", marker


def test_preparing_a_pin_uses_the_source_hosts_python_without_path_discovery(tmp_path):
    host, target = _preparation_roots(tmp_path)
    path, marker = _forwarding_python3(tmp_path)
    store = tmp_path / "managed-python"
    store.mkdir()
    result = _prepare(
        host, target, tmp_path, path=path,
        caller_env={"UV_PYTHON_INSTALL_DIR": str(store)},
    )
    assert result.returncode == 0, result.stderr
    assert _python_report(host)["version"] == _python_report(target)["version"]
    assert _python_report(target)["prefix"] == (target / ".venv").resolve()
    assert not marker.exists() or marker.read_text() == ""


def test_preparing_a_pin_installs_no_tools_or_python(tmp_path):
    host, target = _preparation_roots(tmp_path)
    store = tmp_path / "managed-python"
    store.mkdir()
    before = sorted(p.relative_to(store) for p in store.rglob("*"))
    result = _prepare(host, target, tmp_path, caller_env={"UV_PYTHON_INSTALL_DIR": str(store)})
    assert result.returncode == 0, result.stderr
    assert sorted(p.relative_to(store) for p in store.rglob("*")) == before
    assert (target / ".venv").is_dir() and not (target / ".venv").is_symlink()
    assert _python_report(target)["prefix"] != _python_report(host)["prefix"]
    assert list((target / ".venv").glob("lib/python*/site-packages/*pytest*")) == []


def test_preparing_a_pin_is_silent_and_preserves_stdin_and_lock_files(tmp_path):
    host, target = _preparation_roots(tmp_path)
    before = {(root, name): (root / name).read_bytes()
              for root in (host, target) for name in LOCK_FILES}
    result = subprocess.run(
        ["/bin/bash", "-c", '"$1" --prepare-pin "$2" || exit $?; cat', "prepare",
         str(host / "core" / "tools" / "locked_python.sh"), str(target)],
        cwd=tmp_path, input="stdin remains", text=True, capture_output=True,
        env={k: v for k, v in os.environ.items()
             if k not in UV_REWRITTEN or k == "PATH"},
    )
    assert (result.returncode, result.stdout, result.stderr) == (0, "stdin remains", "")
    assert before == {(root, name): (root / name).read_bytes()
                      for root in (host, target) for name in LOCK_FILES}


def test_preparing_a_pin_targets_the_pin_despite_nested_uv_settings(tmp_path):
    host, target = _preparation_roots(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    values = {"VIRTUAL_ENV": str(elsewhere), "UV_PROJECT_ENVIRONMENT": str(elsewhere),
              "UV_RUN_RECURSION_DEPTH": "1", "UV": "caller-uv"}
    result = subprocess.run(
        ["/bin/bash", "-c",
         '\"$1\" --prepare-pin \"$2\" || exit $?; '
         'printf \"%s\\n\" \"$VIRTUAL_ENV\" \"$UV_PROJECT_ENVIRONMENT\" '
         '\"$UV_RUN_RECURSION_DEPTH\" \"$UV\"',
         "prepare", str(host / "core" / "tools" / "locked_python.sh"), str(target)],
        cwd=tmp_path, text=True, capture_output=True, env={**os.environ, **values},
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout.splitlines() == list(values.values())
    assert _python_report(target)["prefix"] == (target / ".venv").resolve()
    assert not elsewhere.exists()


def test_preparing_a_pin_bootstraps_a_host_without_an_environment(tmp_path):
    host, target = _preparation_roots(tmp_path, bootstrap=False)
    assert not (host / ".venv").exists()
    result = _prepare(host, target, tmp_path)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    assert _python_report(host)["version"] == _python_report(target)["version"]


@pytest.mark.parametrize("bootstrap", [True, False])
def test_preparation_failure_preserves_uv_status_without_retry(tmp_path, bootstrap):
    host, target = _preparation_roots(tmp_path, bootstrap=bootstrap)
    directory = tmp_path / "fake-uv-bin"
    directory.mkdir()
    log = tmp_path / "uv-argv"
    uv = directory / "uv"
    uv.write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" >> "{log}"\n'
                  'echo chosen-diagnostic >&2\nexit 37\n')
    uv.chmod(0o755)
    path, marker = _forwarding_python3(tmp_path)
    result = _prepare(host, target, tmp_path, path=f"{directory}{os.pathsep}{path}")
    assert (result.returncode, result.stdout, result.stderr) == (37, "", "chosen-diagnostic\n")
    if bootstrap:
        assert log.read_text().splitlines() == [
            "run", "--quiet", "--no-sync", "--python", str(host / ".venv" / "bin" / "python"),
            "--no-python-downloads", "--project", str(target), "/bin/sh", "-c", ":",
        ]
    else:
        assert log.read_text().splitlines() == [
            "run", "--quiet", "--no-sync", "--project", str(host), "/bin/sh", "-c", ":",
        ]
        assert not (host / ".venv").exists()
    assert not (target / ".venv").exists()
    assert not marker.exists()
