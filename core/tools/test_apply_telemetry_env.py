"""Tests for `core/tools/apply_telemetry_env.py` — the command a session runs once per machine
to merge (or remove) the telemetry `env` entry into a Claude Code settings file.

The entry itself is `instrument_run.sh`'s own `instrument_run_user_entry` — this module's own
job is the merge/remove and the settings-file handling, never a second copy of the variable set.
Every test of that job hands `run` a fake library; only `TestUserEntryHelper` starts real bash.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import apply_telemetry_env as ate

_TELEMETRY_KEYS = (
    "CLAUDE_CODE_ENABLE_TELEMETRY",
    "OTEL_METRICS_EXPORTER",
    "OTEL_LOGS_EXPORTER",
    "OTEL_EXPORTER_OTLP_PROTOCOL",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
)
_ENDPOINT = "http://localhost:4318"


def _entry(endpoint: str) -> dict[str, str]:
    return {
        "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
        "OTEL_METRICS_EXPORTER": "otlp",
        "OTEL_LOGS_EXPORTER": "otlp",
        "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
        "OTEL_EXPORTER_OTLP_ENDPOINT": endpoint,
    }


def _library_like(endpoint_file: Path | None) -> ate.LibraryAnswer:
    """A fake of the library's contract: an entry for a published endpoint, silence and 0 for none."""
    if endpoint_file is None or not endpoint_file.is_file():
        return ate.LibraryAnswer(0, "", "")
    return ate.LibraryAnswer(0, json.dumps(_entry(endpoint_file.read_text().strip())), "")


def _endpoint_file(tmp_path: Path) -> Path:
    endpoint_file = tmp_path / "endpoint"
    endpoint_file.write_text(_ENDPOINT + "\n")
    return endpoint_file


def _run_main(argv: list[str], run_library=_library_like) -> int:
    return ate.run(argv, run_library=run_library)


class TestMerge:
    def test_merges_the_five_keys_creating_env_if_absent(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps({"permissions": {"allow": ["Bash"]}}))

        rc = _run_main(["--settings-file", str(settings_file), "--endpoint-file", str(_endpoint_file(tmp_path))])
        assert rc == 0

        result = json.loads(settings_file.read_text())
        assert result["permissions"] == {"allow": ["Bash"]}
        assert result["env"] == _entry(_ENDPOINT)

    def test_other_env_keys_and_other_top_level_keys_survive_byte_for_byte(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        original = {
            "env": {"SOME_OTHER_VAR": "kept", "OTEL_RESOURCE_ATTRIBUTES": "kensai.arm=x"},
            "hooks": {"PreToolUse": [{"matcher": "Bash"}]},
            "aNumber": 7,
            "unicode": "café",
        }
        settings_file.write_text(json.dumps(original))

        rc = _run_main(["--settings-file", str(settings_file), "--endpoint-file", str(_endpoint_file(tmp_path))])
        assert rc == 0

        result = json.loads(settings_file.read_text())
        assert result["hooks"] == original["hooks"]
        assert result["aNumber"] == 7
        assert result["unicode"] == "café"
        assert result["env"]["SOME_OTHER_VAR"] == "kept"
        assert result["env"]["OTEL_RESOURCE_ATTRIBUTES"] == "kensai.arm=x"
        for key in _TELEMETRY_KEYS:
            assert result["env"][key]

    def test_running_twice_changes_nothing(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps({"env": {"KEEP": "me"}}))
        argv = ["--settings-file", str(settings_file), "--endpoint-file", str(_endpoint_file(tmp_path))]

        assert _run_main(argv) == 0
        first = settings_file.read_text()
        assert _run_main(argv) == 0
        assert settings_file.read_text() == first

    def test_given_no_published_endpoint_it_writes_nothing_and_exits_zero(self, tmp_path, capsys):
        settings_file = tmp_path / "settings.json"
        original_text = json.dumps({"env": {"KEEP": "me"}})
        settings_file.write_text(original_text)

        rc = _run_main(["--settings-file", str(settings_file), "--endpoint-file", str(tmp_path / "does-not-exist")])
        assert rc == 0
        assert settings_file.read_text() == original_text
        assert "no receiver" in capsys.readouterr().out

    def test_given_settings_file_that_is_not_valid_json_it_writes_nothing_and_exits_nonzero(self, tmp_path, capsys):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text("not json at all")

        rc = _run_main(["--settings-file", str(settings_file), "--endpoint-file", str(_endpoint_file(tmp_path))])
        assert rc != 0
        assert settings_file.read_text() == "not json at all"
        assert str(settings_file) in capsys.readouterr().err

    def test_given_settings_bytes_that_are_not_utf8_it_writes_nothing_and_names_the_file(self, tmp_path, capsys):
        # JSON is UTF-8 (RFC 8259 §8.1), so bytes that do not decode are "not valid JSON" — the
        # same refusal, naming the file, not a traceback.
        settings_file = tmp_path / "settings.json"
        original_bytes = b'{"env": {"A": "\xff"}}'
        settings_file.write_bytes(original_bytes)

        rc = _run_main(["--settings-file", str(settings_file), "--endpoint-file", str(_endpoint_file(tmp_path))])
        assert rc != 0
        assert settings_file.read_bytes() == original_bytes
        assert str(settings_file) in capsys.readouterr().err

    def test_given_no_published_endpoint_a_missing_settings_file_is_not_created(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        rc = _run_main(["--settings-file", str(settings_file), "--endpoint-file", str(tmp_path / "does-not-exist")])
        assert rc == 0
        assert not settings_file.exists()

    def test_a_settings_file_that_does_not_exist_yet_is_treated_as_empty(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        rc = _run_main(["--settings-file", str(settings_file), "--endpoint-file", str(_endpoint_file(tmp_path))])
        assert rc == 0
        assert json.loads(settings_file.read_text())["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == _ENDPOINT


class TestYourOwnValuesAreNotOverwritten:
    """A user who already set one of the five keys to something else keeps it unless they say so."""

    def _settings(self, tmp_path: Path) -> Path:
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(
            json.dumps({"env": {"OTEL_EXPORTER_OTLP_ENDPOINT": "https://collector.corp.example"}})
        )
        return settings_file

    def test_a_different_value_already_there_is_refused_by_name_and_nothing_is_written(self, tmp_path, capsys):
        settings_file = self._settings(tmp_path)
        before = settings_file.read_text()

        rc = _run_main(["--settings-file", str(settings_file), "--endpoint-file", str(_endpoint_file(tmp_path))])

        assert rc != 0
        assert settings_file.read_text() == before
        err = capsys.readouterr().err
        assert "OTEL_EXPORTER_OTLP_ENDPOINT" in err
        assert "collector.corp.example" not in err
        assert "--replace" in err

    def test_replace_overwrites_it(self, tmp_path):
        settings_file = self._settings(tmp_path)
        rc = _run_main(
            ["--settings-file", str(settings_file), "--endpoint-file", str(_endpoint_file(tmp_path)), "--replace"]
        )
        assert rc == 0
        assert json.loads(settings_file.read_text())["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == _ENDPOINT


class TestRemove:
    def _argv(self, settings_file: Path, tmp_path: Path, *extra: str) -> list[str]:
        return ["--settings-file", str(settings_file), "--endpoint-file", str(_endpoint_file(tmp_path)), "--remove", *extra]

    def test_deletes_exactly_the_five_keys_and_leaves_everything_else(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps({"env": {**_entry(_ENDPOINT), "KEEP_ME": "yes"}, "permissions": {"allow": ["Bash"]}}))

        assert _run_main(self._argv(settings_file, tmp_path)) == 0

        result = json.loads(settings_file.read_text())
        assert result["permissions"] == {"allow": ["Bash"]}
        assert result["env"] == {"KEEP_ME": "yes"}

    def test_env_key_is_dropped_entirely_when_no_other_keys_remain_in_it(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps({"env": _entry(_ENDPOINT), "permissions": {"allow": ["Bash"]}}))

        assert _run_main(self._argv(settings_file, tmp_path)) == 0

        result = json.loads(settings_file.read_text())
        assert "env" not in result
        assert result["permissions"] == {"allow": ["Bash"]}

    def test_nothing_to_remove_leaves_the_file_byte_for_byte(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        original_text = '{"permissions":{"allow":["Bash"]},"env":{"KEEP":"me"}}'
        settings_file.write_text(original_text)

        assert _run_main(self._argv(settings_file, tmp_path)) == 0
        assert settings_file.read_text() == original_text

    def test_a_missing_settings_file_is_not_created(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        assert _run_main(self._argv(settings_file, tmp_path)) == 0
        assert not settings_file.exists()

    def test_remove_deletes_exactly_what_merge_wrote(self, tmp_path):
        # A merge then a remove returns the original, so the remove path's own key list cannot
        # drift from the library's variable set unseen.
        settings_file = tmp_path / "settings.json"
        original = {"env": {"KEEP": "me"}, "permissions": {"allow": ["Bash"]}}
        settings_file.write_text(json.dumps(original))

        assert _run_main(["--settings-file", str(settings_file), "--endpoint-file", str(_endpoint_file(tmp_path))]) == 0
        assert _run_main(self._argv(settings_file, tmp_path)) == 0
        assert json.loads(settings_file.read_text()) == original

    def test_a_value_this_command_would_not_have_written_is_left_and_named(self, tmp_path, capsys):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(
            json.dumps({"env": {**_entry(_ENDPOINT), "OTEL_EXPORTER_OTLP_ENDPOINT": "https://collector.corp.example"}})
        )

        assert _run_main(self._argv(settings_file, tmp_path)) == 0

        env = json.loads(settings_file.read_text())["env"]
        assert env == {"OTEL_EXPORTER_OTLP_ENDPOINT": "https://collector.corp.example"}
        out = capsys.readouterr().out
        assert "OTEL_EXPORTER_OTLP_ENDPOINT" in out
        assert "collector.corp.example" not in out

    def test_with_no_published_endpoint_it_refuses_rather_than_guess(self, tmp_path, capsys):
        settings_file = tmp_path / "settings.json"
        before = json.dumps({"env": {**_entry(_ENDPOINT), "KEEP": "me"}})
        settings_file.write_text(before)

        rc = _run_main(["--settings-file", str(settings_file), "--endpoint-file", str(tmp_path / "nope"), "--remove"])

        assert rc != 0
        assert settings_file.read_text() == before
        assert "--force" in capsys.readouterr().err

    def test_force_deletes_the_five_keys_whoever_set_them(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(
            json.dumps({"env": {**_entry("https://collector.corp.example"), "KEEP": "me"}})
        )

        rc = _run_main(
            ["--settings-file", str(settings_file), "--endpoint-file", str(tmp_path / "nope"), "--remove", "--force"]
        )

        assert rc == 0
        assert json.loads(settings_file.read_text())["env"] == {"KEEP": "me"}


class TestALibraryFailureIsNotNoReceiver:
    """The library says "no receiver" by printing nothing and exiting 0. Anything else it does
    that is not an entry is a failure, and is reported as one."""

    @pytest.mark.parametrize(
        "answer",
        [
            ate.LibraryAnswer(127, "", "bash: python3: command not found"),
            ate.LibraryAnswer(0, "", "python3: something broke"),
            ate.LibraryAnswer(0, "not json", ""),
        ],
        ids=["nonzero-exit", "stderr-only", "not-json"],
    )
    def test_it_exits_nonzero_says_the_library_failed_and_writes_nothing(self, tmp_path, capsys, answer):
        settings_file = tmp_path / "settings.json"
        before = json.dumps({"env": {"KEEP": "me"}})
        settings_file.write_text(before)

        rc = _run_main(
            ["--settings-file", str(settings_file), "--endpoint-file", str(_endpoint_file(tmp_path))],
            run_library=lambda _endpoint_file: answer,
        )

        assert rc != 0
        assert settings_file.read_text() == before
        captured = capsys.readouterr()
        assert "no receiver" not in captured.out + captured.err
        assert "instrument_run.sh" in captured.err


class TestRunIsGivenItsRunner:
    def test_run_has_no_default_library(self, tmp_path):
        with pytest.raises(TypeError):
            ate.run(["--settings-file", str(tmp_path / "settings.json")])  # type: ignore[call-arg]


class TestUserEntryIsGivenItsRunner:
    """`user_entry` is given the runner that calls the library; it starts no process and reads no
    environment of its own."""

    def test_it_hands_the_endpoint_file_to_the_runner_and_returns_its_answer(self, tmp_path):
        received = []

        def fake_runner(endpoint_file):
            received.append(endpoint_file)
            return ate.LibraryAnswer(0, '{"OTEL_EXPORTER_OTLP_ENDPOINT": "http://example.invalid"}\n', "")

        entry = ate.user_entry(tmp_path / "endpoint", run_library=fake_runner)
        assert received == [tmp_path / "endpoint"]
        assert entry == {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://example.invalid"}

    def test_no_endpoint_file_reaches_the_runner_as_none(self):
        received = []

        def fake_runner(endpoint_file):
            received.append(endpoint_file)
            return ate.LibraryAnswer(0, "", "")

        ate.user_entry(None, run_library=fake_runner)
        assert received == [None]

    def test_an_empty_answer_from_the_runner_is_none(self, tmp_path):
        assert ate.user_entry(tmp_path / "endpoint", run_library=lambda _: ate.LibraryAnswer(0, "  \n", "")) is None

    def test_a_failed_answer_raises(self, tmp_path):
        with pytest.raises(ate.LibraryFailed):
            ate.user_entry(tmp_path / "endpoint", run_library=lambda _: ate.LibraryAnswer(1, "", "boom"))


class TestNotAnObject:
    """A settings file that parses but is not a JSON object is refused like invalid JSON — `[]`
    would otherwise be replaced by `{"env": …}`."""

    @pytest.mark.parametrize("text", ["[1, 2]\n", "[]\n", '"a string"\n'])
    @pytest.mark.parametrize("remove", [False, True])
    def test_it_writes_nothing_exits_nonzero_and_names_the_file(self, tmp_path, capsys, text, remove):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(text)
        argv = ["--settings-file", str(settings_file), "--endpoint-file", str(_endpoint_file(tmp_path))]
        code = _run_main(argv + (["--remove"] if remove else []))
        assert code != 0
        assert settings_file.read_text() == text
        assert str(settings_file) in capsys.readouterr().err


class TestUserEntryHelper:
    """Through the concrete runner, `user_entry` reaches instrument_run.sh's own
    `instrument_run_user_entry` and never rebuilds the variable set itself."""

    @staticmethod
    def _runner(environ=None):
        return ate.library_runner(ate._INSTRUMENT_RUN_LIB, dict(os.environ) if environ is None else environ)

    def test_given_a_published_endpoint_it_returns_the_five_keys(self, tmp_path):
        entry = ate.user_entry(_endpoint_file(tmp_path), run_library=self._runner())
        assert entry == _entry(_ENDPOINT)

    def test_given_no_published_endpoint_it_returns_none(self, tmp_path):
        assert ate.user_entry(tmp_path / "does-not-exist", run_library=self._runner()) is None

    def test_given_a_malformed_endpoint_file_it_returns_none(self, tmp_path):
        garbage = tmp_path / "garbage"
        garbage.write_text("not a url\n")
        assert ate.user_entry(garbage, run_library=self._runner()) is None

    def test_a_bash_env_file_in_the_environment_cannot_reach_the_library(self, tmp_path):
        noisy = tmp_path / "bash_env.sh"
        noisy.write_text('echo "noise from BASH_ENV"\n')
        environ = {**os.environ, "BASH_ENV": str(noisy), "ENV": str(noisy)}
        assert ate.user_entry(_endpoint_file(tmp_path), run_library=self._runner(environ)) == _entry(_ENDPOINT)


def test_module_names_no_port_and_no_user_specific_path():
    source = Path(ate.__file__).read_text()
    assert "4318" not in source
    assert "/Users/" not in source


def test_the_settings_file_is_always_named_by_the_caller():
    # This module carries no default settings-file path of its own — --settings-file is required.
    with pytest.raises(SystemExit):
        ate._build_parser().parse_args([])
