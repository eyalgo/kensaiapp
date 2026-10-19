"""Contract tests for the detached-run launch home."""

import json
import os
import subprocess
from pathlib import Path

import walk_stop


RUN_LIB = Path(__file__).with_name("detached_run.sh")


def _helper(tmp_path, body, **env):
    script = tmp_path / "helper.sh"
    script.write_text(f'#!/usr/bin/env bash\nset -euo pipefail\nsource "{RUN_LIB}"\n{body}\n')
    script.chmod(0o755)
    return subprocess.run([str(script)], text=True, capture_output=True,
                          env={**os.environ, "DETACH_WATCHER_ON_COMPLETE": "/chain/shim",
                               "INSTRUMENT_RUN_WALK_ID": "walk-1", "KEPT": "yes", **env})


def test_start_detached_run_withholds_the_launch_scope_and_reads_the_record(tmp_path):
    runner = tmp_path / "runner.py"
    runner.write_text(
        "import json, os\n"
        "open(os.environ['SEEN'], 'w').write(json.dumps({k: os.environ.get(k) for k in "
        "('DETACH_WATCHER_ON_COMPLETE', 'INSTRUMENT_RUN_WALK_ID', 'DETACHED_RUN_IDENTITY_FILE', "
        "'KEPT')}))\n"
        "print(json.dumps({'pid': 4242, 'session_id': 's-1', 'owner': 'process'}))\n"
    )
    seen = tmp_path / "seen.json"

    result = _helper(tmp_path, f'SEEN={seen} start_detached_run python3 {runner}\n'
                               'echo "PID=$DETACHED_RUN_PID SESSION=$DETACHED_RUN_SESSION_ID"\n'
                               'echo "HOOK=$DETACH_WATCHER_ON_COMPLETE"\n'
                               'echo "IDENTITY=$DETACHED_RUN_IDENTITY_FILE"',
                     DETACHED_RUN_IDENTITY_FILE="/chain/identity.json")

    assert result.returncode == 0, result.stderr
    assert json.loads(seen.read_text()) == {
        "DETACH_WATCHER_ON_COMPLETE": None, "INSTRUMENT_RUN_WALK_ID": None,
        "DETACHED_RUN_IDENTITY_FILE": None, "KEPT": "yes"}
    assert "PID=4242 SESSION=s-1" in result.stdout
    # The launcher's own scope keeps the hook: its watcher is what hands it on.
    assert "HOOK=/chain/shim" in result.stdout
    # So does the identity file it was handed: the launcher records it, the run never sees it.
    assert "IDENTITY=/chain/identity.json" in result.stdout


def test_start_detached_run_names_a_refusal_and_a_missing_record(tmp_path):
    refused = _helper(tmp_path, "start_detached_run sh -c 'exit 2' || echo rc=$?")
    silent = _helper(tmp_path, "start_detached_run true || echo rc=$?")

    assert "the launch was refused (exit 2)" in refused.stderr and "rc=2" in refused.stdout
    assert "printed no run record" in silent.stderr and "rc=1" in silent.stdout


def test_print_detached_run_names_a_refusal(tmp_path):
    result = _helper(tmp_path, "print_detached_run sh -c 'echo no >&2; exit 2' || echo rc=$?")

    assert "the launch was refused (exit 2)" in result.stderr and "rc=2" in result.stdout


def _a_live_process():
    return subprocess.Popen(["sleep", "30"], start_new_session=True)


def test_record_writes_the_identity_file_when_the_variable_is_set(tmp_path):
    identity = tmp_path / "launch.identity.json"
    live = _a_live_process()
    try:
        result = _helper(
            tmp_path, f'unset DETACH_PROCESS_WATCHER_PID\nDETACHED_RUN_PID={live.pid}\n'
                      'record_detached_run_identity\necho "rc=$?"',
            DETACHED_RUN_IDENTITY_FILE=str(identity))

        recorded = walk_stop.read_identity(walk_stop.DiskFiles(), str(identity))
        start = walk_stop.ProcessTable().start_time(live.pid)
    finally:
        live.kill()
        live.wait()

    assert result.returncode == 0, result.stderr
    assert "rc=0" in result.stdout
    assert recorded == walk_stop.LaunchIdentity(
        run=walk_stop.ProcessIdentity(live.pid, start), watcher=None)


def test_record_names_the_watcher_when_the_watcher_pid_is_set(tmp_path):
    identity = tmp_path / "launch.identity.json"
    run, watcher = _a_live_process(), _a_live_process()
    try:
        result = _helper(
            tmp_path, f'DETACHED_RUN_PID={run.pid}\nDETACH_PROCESS_WATCHER_PID={watcher.pid}\n'
                      'record_detached_run_identity',
            DETACHED_RUN_IDENTITY_FILE=str(identity))

        recorded = walk_stop.read_identity(walk_stop.DiskFiles(), str(identity))
    finally:
        for process in (run, watcher):
            process.kill()
            process.wait()

    assert result.returncode == 0, result.stderr
    assert (recorded.run.pid, recorded.watcher.pid) == (run.pid, watcher.pid)


def test_record_writes_nothing_when_the_variable_is_unset(tmp_path):
    result = _helper(tmp_path, 'unset DETACHED_RUN_IDENTITY_FILE\nDETACHED_RUN_PID=1\n'
                               'record_detached_run_identity\necho "rc=$?"')

    assert result.returncode == 0, result.stderr
    assert "rc=0" in result.stdout and result.stderr == ""
    assert [path.name for path in tmp_path.iterdir()] == ["helper.sh"]


def test_record_returns_zero_when_the_record_cannot_be_written(tmp_path):
    missing_directory = tmp_path / "no-such-directory" / "launch.identity.json"

    result = _helper(tmp_path, 'DETACHED_RUN_PID=1\nrecord_detached_run_identity\necho "rc=$?"',
                     DETACHED_RUN_IDENTITY_FILE=str(missing_directory))

    assert result.returncode == 0, result.stderr
    assert "rc=0" in result.stdout
    assert len(result.stderr.strip().splitlines()) == 1
    assert str(missing_directory) in result.stderr
    assert not missing_directory.exists()


def _a_runner_that_reports_the_receipt_key(tmp_path):
    runner = tmp_path / "runner.py"
    runner.write_text(
        "import json, os\n"
        "open(os.environ['SEEN'], 'w').write(json.dumps(os.environ.get('DETACHED_RUN_RESULT_FILE')))\n"
        "print(json.dumps({'pid': 4242, 'session_id': 's-1', 'owner': 'process'}))\n"
    )
    return runner


def test_a_stub_provider_does_not_inherit_the_receipt_destination(tmp_path):
    runner = _a_runner_that_reports_the_receipt_key(tmp_path)
    seen = tmp_path / "seen.json"

    result = _helper(tmp_path, f"SEEN={seen} start_detached_run python3 {runner}",
                     DETACHED_RUN_RESULT_FILE="/queue/receipt.json")

    assert result.returncode == 0, result.stderr
    assert json.loads(seen.read_text()) is None


def test_the_launcher_and_watcher_environment_retains_the_receipt_destination(tmp_path):
    runner = _a_runner_that_reports_the_receipt_key(tmp_path)

    result = _helper(tmp_path, f"SEEN={tmp_path / 'seen.json'} start_detached_run python3 {runner}\n"
                               'echo "RECEIPT=$DETACHED_RUN_RESULT_FILE"',
                     DETACHED_RUN_RESULT_FILE="/queue/receipt.json")

    assert "RECEIPT=/queue/receipt.json" in result.stdout
