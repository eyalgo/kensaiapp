"""Contract tests for the structured-process watcher detach home."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import chain_usage
import pytest


LIB = Path(__file__).with_name("detach_process_watcher.sh")
# A generous ceiling, not a speed bar: a loaded full-suite run (16 workers) once missed 5 s by 5 ms.
WAIT_SECONDS = 30


@pytest.mark.parametrize("delayed_write", [False, True])
def test_completion_hook_survives_launcher_process_group_cleanup(tmp_path, delayed_write):
    run_log = tmp_path / "run.jsonl"
    run_log.write_text('{"type":"thread.started","thread_id":"fixture"}\n')
    receipt = tmp_path / "hook-result"
    hook = tmp_path / "hook.sh"
    delay = f': > "{receipt}"\nsleep 0.1\n' if delayed_write else ""
    hook.write_text(f'#!/bin/bash\n{delay}printf "%s" "$1" > "{receipt}"\n')
    hook.chmod(0o755)
    wrapper = tmp_path / "launch.sh"
    wrapper.write_text(
        f'#!/bin/bash\nset -euo pipefail\nsource "{LIB}"\n'
        'detach_process_watcher "$@"\necho "PID=$DETACH_PROCESS_WATCHER_PID"\n'
    )
    watcher_pid = None
    watched = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"], start_new_session=True,
    )
    launcher = subprocess.Popen(
        ["bash", str(wrapper), "--watcher", str(LIB.with_name("watch_process.py")),
         "--provider", "codex", "--instance-root", str(tmp_path), "--label", "fixture",
         "--log-stem", "fixture", "--reporter", "generic", "--pid", str(watched.pid),
         "--run-log", str(run_log), "--on-complete", str(hook), "--poll-seconds", "0.01"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
    )
    try:
        stdout, stderr = launcher.communicate(timeout=10)
        assert launcher.returncode == 0, stderr
        watcher_pid = int(next(line[4:] for line in stdout.splitlines() if line.startswith("PID=")))
        observer_log = next((tmp_path / "system" / "logs").glob("watch-fixture-*.log"))
        deadline = time.monotonic() + WAIT_SECONDS
        while "watch_process: watching" not in observer_log.read_text():
            assert time.monotonic() < deadline, observer_log.read_text()
            time.sleep(0.01)

        # Reproduce the launching tool's group cleanup after its command has returned.
        try:
            os.killpg(launcher.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        run_log.write_text('{"type":"turn.completed"}\n')
        deadline = time.monotonic() + WAIT_SECONDS
        while not receipt.exists() or receipt.read_text() != "completed":
            assert time.monotonic() < deadline, observer_log.read_text()
            time.sleep(0.01)
        assert receipt.read_text() == "completed"
    finally:
        watched.terminate()
        watched.wait(timeout=5)
        if launcher.poll() is None:
            launcher.kill()
            launcher.wait(timeout=5)
        if watcher_pid is not None:
            try:
                os.kill(watcher_pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


def test_detaches_watcher_with_hook_marker_and_artifact(tmp_path):
    watcher = tmp_path / "watcher.py"
    argv_log = tmp_path / "argv"
    watcher.write_text(
        "import os,sys\nopen(os.environ['ARGV_LOG'],'w').write('\\n'.join(sys.argv[1:]))\n"
    )
    wrapper = tmp_path / "call.sh"
    wrapper.write_text(
        f'#!/usr/bin/env bash\nset -euo pipefail\nsource "{LIB}"\n'
        'detach_process_watcher "$@"\necho "PID=$DETACH_PROCESS_WATCHER_PID"\n'
    )
    wrapper.chmod(0o755)
    env = {
        **os.environ,
        "ARGV_LOG": str(argv_log),
        "DETACH_WATCHER_ON_COMPLETE": "/hook",
    }
    result = subprocess.run(
        [str(wrapper), "--watcher", str(watcher), "--provider", "claude",
         "--notifier", "/usr/bin/true",
         "--instance-root", str(tmp_path), "--label", "demo", "--log-stem", "demo",
         "--reporter", "generic", "--pid", "77", "--run-log", "/run.jsonl",
         "--artifact-path", "/product", "--done-when-exists", "/done",
         "--multi-turn", "--poll-seconds", "0"],
        text=True, capture_output=True, env=env,
    )
    assert result.returncode == 0, result.stderr
    # The watcher is a detached process: under a loaded parallel run its interpreter can take well
    # over a second to start, and the file exists before its one write lands.
    deadline = time.monotonic() + 30
    while not (argv_log.exists() and argv_log.read_text()) and time.monotonic() < deadline:
        time.sleep(0.05)
    argv = argv_log.read_text().splitlines()
    assert argv[argv.index("--pid") + 1] == "77"
    assert argv[argv.index("--log") + 1] == "/run.jsonl"
    assert argv[argv.index("--on-complete") + 1] == "/hook"
    assert argv[argv.index("--done-when-exists") + 1] == "/done"
    assert argv[argv.index("--provider") + 1] == "claude"
    assert "--multi-turn" in argv
    observer_logs = list((tmp_path / "system" / "logs").glob("watch-*.log"))
    assert len(observer_logs) == 1
    assert chain_usage.watch_log_name(observer_logs[0].name, "demo") is not None


def test_missing_required_pid_is_refused(tmp_path):
    wrapper = tmp_path / "call.sh"
    wrapper.write_text(
        f'#!/usr/bin/env bash\nsource "{LIB}"\n'
        'detach_process_watcher --watcher /w --provider codex --instance-root /i --label l '
        '--log-stem s --reporter generic --run-log /log\n'
    )
    wrapper.chmod(0o755)

    result = subprocess.run([str(wrapper)], text=True, capture_output=True)

    assert result.returncode == 1
    assert "--pid is required" in result.stderr


def test_missing_required_provider_is_refused(tmp_path):
    wrapper = tmp_path / "call.sh"
    wrapper.write_text(
        f'#!/usr/bin/env bash\nsource "{LIB}"\n'
        'detach_process_watcher --watcher /w --instance-root /i --label l '
        '--log-stem s --reporter generic --pid 1 --run-log /log\n'
    )
    wrapper.chmod(0o755)

    result = subprocess.run([str(wrapper)], text=True, capture_output=True)

    assert result.returncode == 1
    assert "--provider is required" in result.stderr


def _detach_twice(tmp_path, stem):
    watcher = tmp_path / "watcher.py"
    watcher.write_text("import time; time.sleep(0)\n")
    wrapper = tmp_path / "call.sh"
    wrapper.write_text(
        f'#!/usr/bin/env bash\nset -euo pipefail\nsource "{LIB}"\n'
        'for n in 1 2; do detach_process_watcher "$@"; done\n'
    )
    wrapper.chmod(0o755)
    return subprocess.run(
        [str(wrapper), "--watcher", str(watcher), "--provider", "codex",
         "--notifier", "/usr/bin/true", "--instance-root", str(tmp_path), "--label", "demo",
         "--log-stem", stem, "--reporter", "generic", "--pid", "77", "--run-log", "/run.jsonl"],
        text=True, capture_output=True,
    )


def test_two_watches_of_one_stem_in_one_second_keep_two_logs(tmp_path):
    result = _detach_twice(tmp_path, "development-audit")

    assert result.returncode == 0, result.stderr
    logs = sorted((tmp_path / "system" / "logs").glob("watch-development-audit-*.log"))
    assert len(logs) == 2
    assert all(chain_usage.watch_log_name(log.name, "development-audit") for log in logs)
