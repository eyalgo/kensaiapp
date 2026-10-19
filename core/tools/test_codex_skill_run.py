"""Native protocol contract; the server is the external boundary."""
from pathlib import Path

import pytest

import agent_run


def test_codex_skill_uses_native_runner_and_preserves_selected_pin(tmp_path):
    skill = tmp_path / 'pins' / 'renewed' / '.claude' / 'skills' / 'example' / 'SKILL.md'
    skill.parent.mkdir(parents=True)
    skill.write_text('---\nname: example\ndescription: example\n---\nbody\n')
    request = agent_run.RunRequest(prompt='task', skill_name='example', skill_path=skill)
    command = agent_run.CodexAdapter().background_command(request)
    assert Path(command[1]).name == 'codex_skill_run.py'
    assert command[command.index('--skill-path') + 1] == str(skill.resolve())


def test_native_turn_discovers_then_loads_canonical_skill_and_preserves_permissions(tmp_path):
    from codex_skill_run import run_skill
    skill = tmp_path / 'pin' / '.claude' / 'skills' / 'example' / 'SKILL.md'
    calls = []
    events = []
    class Server:
        def request(self, method, params):
            calls.append((method, params))
            if method == 'skills/list':
                return {'data': [{'cwd': str(tmp_path), 'skills': [{'name': 'example', 'path': str(skill.resolve()), 'enabled': True}], 'errors': []}]}
            if method == 'thread/start':
                return {'thread': {'id': 'thread'}}
            if method == 'turn/start':
                return {'turn': {'id': 'turn'}}
            return {}
        def receive(self):
            return {'method': 'turn/completed', 'params': {'threadId': 'thread', 'turn': {'id': 'turn', 'status': 'completed', 'error': None}}}
    assert run_skill(Server(), cwd=tmp_path, name='example', path=skill, roots=[skill.parent.parent], prompt='task', model='chosen-model', effort='high', add_dirs=['/product'], emit=events.append) == 0
    methods = [method for method, _ in calls]
    assert methods.index('skills/extraRoots/set') < methods.index('thread/start') < methods.index('turn/start')
    thread = dict(calls)['thread/start']
    assert thread['sandbox'] == 'workspace-write'
    assert thread['approvalPolicy'] == 'on-request'
    assert thread['approvalsReviewer'] == 'auto_review'
    assert thread['config']['sandbox_workspace_write']['writable_roots'] == ['/product']
    turn = dict(calls)['turn/start']
    instructions = (Path(__file__).parents[1] / "prompts" / "codex_execution.md").read_text()
    assert turn["input"][0] == {"type": "text", "text": instructions}
    assert turn["input"][1] == {"type": "text", "text": "task"}
    assert {'type': 'skill', 'name': 'example', 'path': str(skill.resolve())} in turn['input']
    assert turn['effort'] == 'high'
    assert events[-1]['type'] == 'turn.completed'


def test_native_turn_refuses_missing_skill_before_start(tmp_path):
    from codex_skill_run import run_skill, ProtocolError
    class Server:
        def request(self, method, params):
            assert method not in ('thread/start', 'turn/start')
            return {'data': []} if method == 'skills/list' else {}
    with pytest.raises(ProtocolError, match='not discovered'):
        run_skill(Server(), cwd=tmp_path, name='missing', path=tmp_path/'SKILL.md', roots=[tmp_path], prompt='task', model=None, effort=None, add_dirs=[], emit=lambda event: None)


def test_stdio_keeps_notifications_arriving_before_response():
    import io
    import json
    from codex_skill_run import StdioServer
    notification = {'method': 'turn/completed', 'params': {'threadId': 'thread'}}
    reader = io.StringIO(json.dumps(notification) + '\n' + json.dumps({'id': 1, 'result': {'ok': True}}) + '\n')
    writer = io.StringIO()
    server = StdioServer(reader, writer)
    assert server.request('test', {}) == {'ok': True}
    assert server.receive() == notification
    assert json.loads(writer.getvalue()) == {'id': 1, 'method': 'test', 'params': {}}


@pytest.mark.parametrize('response', ['', '{"id":1,"error":{"message":"unsupported"}}\n'])
def test_stdio_reports_early_exit_and_protocol_refusal(response):
    import io
    from codex_skill_run import StdioServer, ProtocolError
    with pytest.raises(ProtocolError):
        StdioServer(io.StringIO(response), io.StringIO()).request('skills/extraRoots/set', {})


@pytest.mark.parametrize("method", [
    "item/commandExecution/requestApproval",
    "item/fileChange/requestApproval",
    "item/permissions/requestApproval",
])
def test_stdio_does_not_accept_interactive_approval(method):
    import io
    import json
    from codex_skill_run import StdioServer, ProtocolError
    writer = io.StringIO()
    server = StdioServer(io.StringIO(json.dumps({"id": 9, "method": method}) + "\n"), writer)
    with pytest.raises(ProtocolError, match="interactive-approval-required"):
        server.receive()
    assert 'error' in json.loads(writer.getvalue())


def test_stdio_preserves_automatic_review_denial():
    import io
    import json
    from codex_skill_run import StdioServer
    event = {"method": "item/autoApprovalReview/completed", "params": {
        "threadId": "thread", "review": {"status": "denied", "rationale": "outside scope"}
    }}
    writer = io.StringIO()
    server = StdioServer(io.StringIO(json.dumps(event) + "\n"), writer)
    assert server.receive() == event
    assert writer.getvalue() == ""


@pytest.mark.parametrize('fields', [{'skill_name': 'example'}, {'skill_path': Path('/pin/SKILL.md')}])
def test_codex_refuses_incomplete_skill_selection(fields):
    with pytest.raises(agent_run.UnsupportedRequest, match='both'):
        agent_run.CodexAdapter().command(agent_run.RunRequest(prompt='task', **fields))


_FAKE_CODEX = """#!{python}
\"\"\"A stand-in `codex app-server`: records its argv and the turn/start params, answers the protocol
`run_skill` speaks, and completes the turn.\"\"\"
import json
import sys

record = {{"argv": sys.argv[1:]}}
skill = {skill!r}
answers = {{
    "skills/list": {{
        "data": [{{"skills": [{{"name": "example", "path": skill, "enabled": True}}]}}]
    }},
    "thread/start": {{"thread": {{"id": "thread"}}}},
    "turn/start": {{"turn": {{"id": "turn"}}}},
}}
for line in sys.stdin:
    message = json.loads(line)
    if message["method"] == "turn/start":
        record["turn"] = message["params"]
    # Recorded before answering: the runner terminates the server once the turn completes.
    with open({record_file!r}, "w") as out:
        json.dump(record, out)
    print(json.dumps({{"id": message["id"], "result": answers.get(message["method"], {{}})}}))
    if message["method"] == "turn/start":
        completed = {{"threadId": "thread", "turn": {{"id": "turn", "status": "completed"}}}}
        print(json.dumps({{"method": "turn/completed", "params": completed}}))
    sys.stdout.flush()
"""


def test_main_passes_an_otel_exporter_config_to_the_app_server_command(tmp_path, monkeypatch):
    """`main` forwards an `otel.exporter=…` `--config` to `codex app-server` unchanged, and takes
    no effort from it. `codex` on `PATH` is the external boundary, faked as a real executable."""
    import json
    import os
    import sys

    from codex_skill_run import main

    skill = tmp_path / "pin" / ".claude" / "skills" / "example" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: example\ndescription: example\n---\nbody\n")
    record_file = tmp_path / "codex-record.json"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_codex = fake_bin / "codex"
    fake_codex.write_text(
        _FAKE_CODEX.format(
            python=sys.executable, skill=str(skill.resolve()), record_file=str(record_file)
        )
    )
    fake_codex.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")
    exporter = (
        'otel.exporter={otlp-http={endpoint="http://h:4318/v1/logs",protocol="json"}}'
    )

    exit_code = main(
        ["--skill-name", "example", "--skill-path", str(skill), "--config", exporter, "task"]
    )

    record = json.loads(record_file.read_text())
    assert exit_code == 0
    assert record["argv"] == ["app-server", "--config", exporter]
    assert record["turn"]["effort"] is None


@pytest.mark.parametrize("instructions", ["Instructions from the selected pin.", None, " \n"])
def test_runner_uses_its_own_pinned_instructions_or_refuses_before_thread(tmp_path, instructions):
    import json
    import os
    import shutil
    import subprocess
    import sys

    pinned_core = tmp_path / "pin" / "core"
    runner = pinned_core / "tools" / "codex_skill_run.py"
    runner.parent.mkdir(parents=True)
    shutil.copyfile(Path(__file__).with_name("codex_skill_run.py"), runner)
    if instructions is not None:
        prompt = pinned_core / "prompts" / "codex_execution.md"
        prompt.parent.mkdir()
        prompt.write_text(instructions)
    skill = tmp_path / "skills" / "example" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: example\ndescription: example\n---\nPerform the task.\n")
    record_file = tmp_path / "record.json"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_codex = fake_bin / "codex"
    fake_codex.write_text(_FAKE_CODEX.format(
        python=sys.executable, skill=str(skill), record_file=str(record_file)
    ))
    fake_codex.chmod(0o755)
    result = subprocess.run(
        [sys.executable, str(runner), "--json", "--skill-name", "example",
         "--skill-path", str(skill), "task"],
        cwd=tmp_path, env={**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}"},
        capture_output=True, text=True, timeout=15,
    )
    events = [json.loads(line) for line in result.stdout.splitlines()]
    if instructions and instructions.strip():
        assert result.returncode == 0, result.stderr
        inputs = json.loads(record_file.read_text())["turn"]["input"]
        assert inputs[0] == {"type": "text", "text": instructions}
        assert inputs[1] == {"type": "text", "text": "task"}
    else:
        assert result.returncode == 1
        assert events[0]["type"] == "turn.failed"
        assert "codex_execution.md" in events[0]["error"]
        assert not record_file.exists()
