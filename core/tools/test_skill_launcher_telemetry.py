"""The skill launcher hands a Codex or Gemini run the same telemetry it hands a Claude run.

`core/launchers/skill/launcher.sh` tags every run with `run_telemetry`
(`core/tools/run_telemetry.sh`, over the configured package's `turn-on`), which prints a
`Telemetry:` line carrying the run's `kensai.run_id` and builds `INSTRUMENT_RUN_SETTINGS`. The
Claude branch has always handed that document to the adapter as `--settings`; the Codex branch,
and later the Gemini branch, handed it nothing, so each printed a run ID no record of the run ever
carried. Neither
`codex` nor `agy` takes a settings file, so the adapter turns the document's `env` into a leading
`env KEY=value …` on the command. These cases drive the real launcher's `--dry-run` — defined to
print "the exact provider command" (its own USAGE) — and read the hand-over off what it prints.

**Why here and not beside the launcher.** A launcher's suite sits in its own folder
(`core/launchers/skill/test_skill.py`), but the changes these cases guard name `pytest core/tools/`
as the command that must fail when the Codex or Gemini branch stops carrying its run ID, and that
command does not collect `core/launchers/`. `core/tools/test_chain.py` drives the same launcher's
dry run from here for the same reason.

Isolation: the real launcher against this repository's real skills, run under the session pin
`core/tools/conftest.py` makes, from a scratch instance in `tmp_path` that holds its own project and
its own `.providers.toml` — so no case depends on a project or a provider file this repository
happens to carry. `HOME` and the endpoint file point into `tmp_path`, so nothing reads this
machine's published endpoint and nothing launches.

**The package command is a fixture here.** An isolated `HOME` cannot reach the installed package,
so each case installs a neutral executable (`install_telemetry_command`) under
`$HOME/.kensaiapp/venv/bin/` and names it through `KENSAIAPP_TELEMETRY_COMMAND`, which is how the
helper finds any command. It prints the package-shaped settings document and its stderr notices and
logs each call it receives; the real package is held to the helper's contract by
`test_run_telemetry.py`, never here, so this file proves the launcher's side of the boundary only.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from instance_test_support import scratch_instance

_REPO = Path(__file__).resolve().parents[2]
_LAUNCHER = _REPO / "core" / "launchers" / "skill" / "launcher.sh"
_SKILL = "tobiishi-open"
_PROJECT = "example-product"
_ENDPOINT = "http://127.0.0.1:4318"
_RUN_ID = re.compile(
    r"kensai\.run_id=([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
)
_DRY_RUN_HEADING = "DRY RUN — would launch:"


def _scratch_instance(tmp_path):
    return scratch_instance(tmp_path, _PROJECT)


COMMAND_VARIABLE = "KENSAIAPP_TELEMETRY_COMMAND"
FIXTURE_COMMAND = "fixture-turn-on"
FIXTURE_MODE_VARIABLE = "FIXTURE_TURN_ON_MODE"

# A neutral stand-in for the package's `turn-on --print`: the same argv, the same stdout document,
# and the same stderr notices for the three endpoint causes, so the helper reads it as it reads the
# package. It logs each call as one JSON line beside itself. `FIXTURE_TURN_ON_MODE` makes it fail:
# `exit-3` exits 3, `garbage` prints text that is no document, `incomplete` prints a document
# missing its base keys.
_FIXTURE_COMMAND_SOURCE = """\
#!{python}
import json, os, subprocess, sys, uuid
from pathlib import Path
from urllib.parse import urlparse

args = sys.argv[1:]
log = Path(sys.argv[0]).resolve().parent.parent / "fixture-calls.log"
with log.open("a") as handle:
    handle.write(json.dumps({{"argv": args, "cwd": os.getcwd()}}) + "\\n")
mode = os.environ.get("FIXTURE_TURN_ON_MODE", "")
if mode == "exit-3":
    sys.exit(3)
if mode == "garbage":
    print("this is not a settings document")
    sys.exit(0)
endpoint_file = Path(args[args.index("--endpoint-file") + 1])
labels = [args[i + 1] for i, word in enumerate(args) if word == "--label"]


def decline(cause):
    print("          (" + cause + " — run uninstrumented)", file=sys.stderr)
    sys.exit(0)


if not endpoint_file.exists():
    decline("no published telemetry endpoint at " + str(endpoint_file))
endpoint = endpoint_file.read_text().strip()
parsed = urlparse(endpoint)
if parsed.scheme not in ("http", "https") or not parsed.hostname:
    decline("telemetry endpoint at " + str(endpoint_file) + " is unreadable or malformed")
if parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
    decline(
        "telemetry endpoint at " + str(endpoint_file)
        + " is not on this machine (loopback only)"
    )
if mode == "incomplete":
    print(json.dumps({{"env": {{"OTEL_RESOURCE_ATTRIBUTES": "kensai.run_id=x"}}}}))
    sys.exit(0)
pairs = ["kensai.run_id=" + str(uuid.uuid4())]
common = subprocess.run(
    ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
    capture_output=True, text=True,
)
if common.returncode == 0:
    root = Path(common.stdout.strip())
    pairs.append("kensai.instance=" + (root.parent if root.name == ".git" else root).name)
for label in labels:
    key, _, value = label.partition("=")
    pairs.append("kensai." + key + "=" + value.replace("%", "%000025"))
attributes = ",".join(pairs)
print(json.dumps({{"env": {{
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
    "OTEL_EXPORTER_OTLP_ENDPOINT": endpoint,
    "OTEL_RESOURCE_ATTRIBUTES": attributes,
}}}}, separators=(",", ":")))
print("          Telemetry:    " + attributes + " → " + endpoint, file=sys.stderr)
"""


def install_telemetry_command(home, env, name=FIXTURE_COMMAND):
    """Install the neutral fixture command under `home`'s venv bin and name it in `env`. Returns
    the file that logs one JSON line per call it receives."""
    bin_dir = Path(home) / ".kensaiapp" / "venv" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    command = bin_dir / name
    command.write_text(_FIXTURE_COMMAND_SOURCE.format(python=sys.executable))
    command.chmod(0o755)
    env[COMMAND_VARIABLE] = name
    return bin_dir.parent / "fixture-calls.log"


def fixture_calls(home):
    """The calls the fixture command received, as `{"argv": [...], "cwd": ...}` dicts in order."""
    log = Path(home) / ".kensaiapp" / "venv" / "fixture-calls.log"
    return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


def _isolated_env(tmp_path, endpoint_file):
    """The environment every dry run here shares: `HOME` and the endpoint under `tmp_path`, the
    fixture command installed and named, and no provider forced."""
    env = dict(os.environ)
    env["HOME"] = str(tmp_path)
    env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    env.pop("KENSAIAPP_AGENT_PROVIDER", None)
    env.pop(FIXTURE_MODE_VARIABLE, None)
    env.pop("INSTRUMENT_RUN_SETTINGS", None)
    env.pop("KENSAIAPP_CONTEXT_CAP", None)
    install_telemetry_command(tmp_path, env)
    return env


def _dry_run(tmp_path, provider, endpoint_file, **env_changes):
    env = _isolated_env(tmp_path, endpoint_file)
    _apply(env, env_changes)
    return subprocess.run(
        [str(_LAUNCHER), _SKILL, _PROJECT, "--provider", provider, "--dry-run"],
        cwd=str(_scratch_instance(tmp_path)),
        capture_output=True,
        text=True,
        env=env,
    )


def _apply(env, changes):
    """`changes` applied to `env`: a `None` value removes the variable."""
    for name, value in changes.items():
        if value is None:
            env.pop(name, None)
        else:
            env[name] = value


def _published_endpoint(tmp_path, content=f"{_ENDPOINT}\n"):
    endpoint_file = tmp_path / "endpoint"
    endpoint_file.write_text(content)
    return endpoint_file


def _printed_run_id(stdout):
    telemetry = [line for line in stdout.splitlines() if "Telemetry:" in line]
    assert len(telemetry) == 1, stdout
    match = _RUN_ID.search(telemetry[0])
    assert match, telemetry[0]
    return match.group(1)


def _printed_command(stdout):
    """The provider command the dry run printed, as the tokens it would run."""
    lines = stdout.splitlines()
    assert _DRY_RUN_HEADING in lines, stdout
    command = "\n".join(lines[lines.index(_DRY_RUN_HEADING) + 1 :]).strip()
    assert command, stdout
    return shlex.split(command)


def test_codex_dry_run_prints_the_run_id_in_the_command(tmp_path):
    result = _dry_run(tmp_path, "codex", _published_endpoint(tmp_path))

    assert result.returncode == 0, result.stderr
    run_id = _printed_run_id(result.stdout)
    command = _printed_command(result.stdout)
    resource_attributes = [
        token for token in command if token.startswith("OTEL_RESOURCE_ATTRIBUTES=")
    ]
    assert len(resource_attributes) == 1, command
    assert f"kensai.run_id={run_id}" in resource_attributes[0].split("=", 1)[1].split(",")


def test_codex_dry_run_prints_the_exporter_config_for_the_published_endpoint(tmp_path):
    result = _dry_run(tmp_path, "codex", _published_endpoint(tmp_path))

    assert result.returncode == 0, result.stderr
    command = _printed_command(result.stdout)
    exporter = [token for token in command if token.startswith("otel.exporter=")]
    assert exporter == [
        f'otel.exporter={{otlp-http={{endpoint="{_ENDPOINT}/v1/logs",protocol="json"}}}}'
    ]
    assert command[command.index(exporter[0]) - 1] == "--config"


# --- the paths the Codex hand-over must leave as they were (CP-184, CP-185) ---------------------

_INTELLIGENCE = (
    _REPO / "skills" / "pm" / ".claude" / "skills" / _SKILL / "intelligence" / "claude.md"
)
# Every flag the Claude command carried before the Codex branch was given the settings. The fence
# is the whole set, so a flag this hand-over adds to or drops from the Claude command fails it.
_CLAUDE_FLAGS = {
    "--print",
    "--output-format",
    "--verbose",
    "--session-id",
    "--agent",
    "--model",
    "--effort",
    "--permission-mode",
    "--permission-prompts",
    "--setting-sources",
    "--plugin-dir",
    "--settings",
    "--agents",
    "--append-system-prompt-file",
    "--add-dir",
}


def _intelligence_value(label):
    """The `**<label>:**` value the launcher reads from the skill's Claude intelligence file."""
    match = re.search(rf"^\*\*{label}:\*\* *(\S+)", _INTELLIGENCE.read_text(), re.MULTILINE)
    assert match, _INTELLIGENCE
    return match.group(1)


def _flag_value(command, flag):
    assert command.count(flag) == 1, command
    return command[command.index(flag) + 1]


def _assert_codex_launch_is_uninstrumented(result, reason):
    assert result.returncode == 0, result.stderr
    assert f"({reason} — run uninstrumented)" in result.stdout
    command = _printed_command(result.stdout)
    assert not any("otel.exporter" in token for token in command), command
    assert not any(token.startswith("OTEL_RESOURCE_ATTRIBUTES=") for token in command), command
    assert "--skill-name" in command


def test_codex_dry_run_with_no_endpoint_stays_uninstrumented(tmp_path):
    missing = tmp_path / "no-endpoint"

    result = _dry_run(tmp_path, "codex", missing)

    _assert_codex_launch_is_uninstrumented(
        result, f"no published telemetry endpoint at {missing}"
    )


def test_codex_dry_run_with_a_malformed_endpoint_stays_uninstrumented(tmp_path):
    endpoint_file = _published_endpoint(tmp_path, "not-a-url\n")

    result = _dry_run(tmp_path, "codex", endpoint_file)

    _assert_codex_launch_is_uninstrumented(
        result, f"telemetry endpoint at {endpoint_file} is unreadable or malformed"
    )


def test_claude_dry_run_still_carries_the_run_id(tmp_path):
    result = _dry_run(tmp_path, "claude", _published_endpoint(tmp_path))

    assert result.returncode == 0, result.stderr
    run_id = _printed_run_id(result.stdout)
    command = _printed_command(result.stdout)
    assert "claude" in command
    flags = {token.split("=", 1)[0] for token in command if token.startswith("--")}
    assert flags == _CLAUDE_FLAGS
    assert _flag_value(command, "--model") == _intelligence_value("Model")
    assert _flag_value(command, "--effort") == _intelligence_value("Effort")
    assert not any("otel.exporter" in token for token in command), command
    assert run_id in Path(_flag_value(command, "--settings")).read_text()


# The six variables `run_telemetry` hands a run. A test module keeps its own copy of the set
# rather than importing one.
_TELEMETRY_KEYS = (
    "CLAUDE_CODE_ENABLE_TELEMETRY",
    "OTEL_METRICS_EXPORTER",
    "OTEL_LOGS_EXPORTER",
    "OTEL_EXPORTER_OTLP_PROTOCOL",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "OTEL_RESOURCE_ATTRIBUTES",
)


def test_claude_dry_run_settings_still_carry_the_telemetry_keys(tmp_path):
    """CP-185: a Claude run's telemetry "still carries the same keys" — every one of them in the
    settings its printed `--settings` names, aimed at the published endpoint, with the printed run
    ID on the resource."""
    result = _dry_run(tmp_path, "claude", _published_endpoint(tmp_path))

    assert result.returncode == 0, result.stderr
    run_id = _printed_run_id(result.stdout)
    command = _printed_command(result.stdout)
    env = json.loads(Path(_flag_value(command, "--settings")).read_text())["env"]
    assert set(_TELEMETRY_KEYS) <= env.keys(), env
    assert env["OTEL_EXPORTER_OTLP_ENDPOINT"] == _ENDPOINT
    pairs = env["OTEL_RESOURCE_ATTRIBUTES"].split(",")
    assert f"kensai.run_id={run_id}" in pairs
    # CP-196: every kensai.* key a skill-launcher run carried before the provenance keys is still
    # there, beside them.
    keys = {pair.partition("=")[0] for pair in pairs}
    assert set(_PRE_CHANGE_KEYS) <= keys, keys
    assert {"kensai.provider", "kensai.source"} <= keys, keys


# --- provenance: the provider, model and effort a run goes at, and where they came from ----------
#     (change 2026-09-30_runs-record-provider-model-effort-and-source, CP-188 … CP-196)

# The kensai.* keys a skill-launcher run into a git checkout carried before the provenance keys,
# in the order it printed them (`run_telemetry skill=… project=…`, plus the derived instance and
# product).
_PRE_CHANGE_KEYS = (
    "kensai.arm",
    "kensai.run_id",
    "kensai.instance",
    "kensai.skill",
    "kensai.project",
    "kensai.product",
)
_PROVENANCE_KEYS = ("kensai.provider", "kensai.model", "kensai.effort", "kensai.source")
# A shipped skill with no `intelligence/` folder, and the arguments its launcher takes — its dry
# run makes no journey move and names no satellite.
_NO_INTELLIGENCE_SKILL = "nemawashi-unpick"
_NO_INTELLIGENCE_ARGS = (_PROJECT, "a reason")


def _launch_dry(tmp_path, *cli, skills_root=None):
    env = _isolated_env(tmp_path, _published_endpoint(tmp_path))
    if skills_root is not None:
        env["LAUNCH_SKILL_SKILLS_ROOT"] = str(skills_root)
    return subprocess.run(
        [str(_LAUNCHER), *cli, "--dry-run"],
        cwd=str(_scratch_instance(tmp_path)),
        capture_output=True,
        text=True,
        env=env,
    )


def _telemetry_pairs(stdout):
    """The `kensai.*` pairs on the one printed `Telemetry:` line, in printed order."""
    telemetry = [line for line in stdout.splitlines() if "Telemetry:" in line]
    assert len(telemetry) == 1, stdout
    listed = telemetry[0].split("Telemetry:", 1)[1].split("→", 1)[0].strip()
    return listed.split(",")


def _provenance(pairs):
    """The four provenance keys' values off a pair list — absent keys absent."""
    found = dict(pair.split("=", 1) for pair in pairs)
    return {key: found[key] for key in _PROVENANCE_KEYS if key in found}


def _intelligence_of(provider, label):
    path = _INTELLIGENCE.with_name(f"{provider}.md")
    match = re.search(rf"^\*\*{label}:\*\* *(\S+)", path.read_text(), re.MULTILINE)
    assert match, path
    return match.group(1)


def test_intelligence_skill_claude_stamps_provider_model_effort_and_intelligence_source(tmp_path):
    result = _launch_dry(tmp_path, _SKILL, _PROJECT, "--provider", "claude")

    assert result.returncode == 0, result.stderr
    expected = {
        "kensai.provider": "claude",
        "kensai.model": _intelligence_of("claude", "Model"),
        "kensai.effort": _intelligence_of("claude", "Effort"),
        "kensai.source": "intelligence",
    }
    assert _provenance(_telemetry_pairs(result.stdout)) == expected
    command = _printed_command(result.stdout)
    settings_env = json.loads(Path(_flag_value(command, "--settings")).read_text())["env"]
    assert _provenance(settings_env["OTEL_RESOURCE_ATTRIBUTES"].split(",")) == expected


def test_intelligence_skill_codex_stamps_the_codex_files_model_and_effort(tmp_path):
    result = _launch_dry(tmp_path, _SKILL, _PROJECT, "--provider", "codex")

    assert result.returncode == 0, result.stderr
    assert _provenance(_telemetry_pairs(result.stdout)) == {
        "kensai.provider": "codex",
        "kensai.model": _intelligence_of("codex", "Model"),
        "kensai.effort": _intelligence_of("codex", "Effort"),
        "kensai.source": "intelligence",
    }


def test_intelligence_file_without_effort_stamps_no_effort(tmp_path):
    """No shipped intelligence file omits **Effort:**, so this skill is a fixture, looked up
    through the launcher's own host-root override; the instance, its agents and its project stay
    this repository's."""
    skill_dir = tmp_path / "host" / ".claude" / "skills" / "no-effort-demo"
    (skill_dir / "intelligence").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: no-effort-demo\n---\n")
    (skill_dir / "launcher.md").write_text(
        "**Agent:** pm\n**Arguments:** <project>\n**Prompt:** demo for {project}.\n"
    )
    (skill_dir / "intelligence" / "claude.md").write_text("**Model:** claude-opus-5-5\n")

    result = _launch_dry(
        tmp_path, "no-effort-demo", _PROJECT, "--provider", "claude",
        skills_root=tmp_path / "host",
    )

    assert result.returncode == 0, result.stderr
    assert _provenance(_telemetry_pairs(result.stdout)) == {
        "kensai.provider": "claude",
        "kensai.model": "claude-opus-5-5",
        "kensai.source": "intelligence",
    }


def test_tier_codex_sonnet_stamps_gpt_5_6_terra_medium_tier(tmp_path):
    result = _launch_dry(
        tmp_path, _NO_INTELLIGENCE_SKILL, *_NO_INTELLIGENCE_ARGS, "--provider", "codex", "--model-tier", "sonnet"
    )

    assert result.returncode == 0, result.stderr
    assert _provenance(_telemetry_pairs(result.stdout)) == {
        "kensai.provider": "codex",
        "kensai.model": "gpt-5.6-terra",
        "kensai.effort": "medium",
        "kensai.source": "tier",
    }
    command = _printed_command(result.stdout)
    assert _flag_value(command, "--model") == "gpt-5.6-terra"
    assert 'model_reasoning_effort="medium"' in command
    assert "Intelligence: none — provider default" not in result.stdout


def test_tier_claude_haiku_stamps_model_and_no_effort(tmp_path):
    result = _launch_dry(
        tmp_path, _NO_INTELLIGENCE_SKILL, *_NO_INTELLIGENCE_ARGS, "--provider", "claude", "--model-tier", "haiku"
    )

    assert result.returncode == 0, result.stderr
    assert _provenance(_telemetry_pairs(result.stdout)) == {
        "kensai.provider": "claude",
        "kensai.model": "haiku",
        "kensai.source": "tier",
    }
    command = _printed_command(result.stdout)
    assert _flag_value(command, "--model") == "haiku"
    assert "--effort" not in command


def test_tier_codex_fable_is_accepted_and_runs_at_xhigh(tmp_path):
    """The tier's own `xhigh` reaches Codex; a raw `--effort xhigh` would be refused for it."""
    result = _launch_dry(
        tmp_path, _NO_INTELLIGENCE_SKILL, *_NO_INTELLIGENCE_ARGS, "--provider", "codex", "--model-tier", "fable"
    )

    assert result.returncode == 0, result.stderr
    command = _printed_command(result.stdout)
    assert _flag_value(command, "--model") == "gpt-5.6-sol"
    assert 'model_reasoning_effort="xhigh"' in command
    assert _provenance(_telemetry_pairs(result.stdout))["kensai.effort"] == "xhigh"


def test_no_intelligence_no_tier_stamps_default_source_only(tmp_path):
    result = _launch_dry(tmp_path, _NO_INTELLIGENCE_SKILL, *_NO_INTELLIGENCE_ARGS, "--provider", "codex")

    assert result.returncode == 0, result.stderr
    assert "Intelligence: none — provider default" in result.stdout
    assert _provenance(_telemetry_pairs(result.stdout)) == {
        "kensai.provider": "codex",
        "kensai.source": "default",
    }


# --- the Gemini hand-over (change 2026-09-30_gemini-runs-emit-to-the-receiver, CP-207 … CP-215) ---


def _gemini_env_prefix(command):
    """The `env KEY=value …` assignments the adapter puts in front of `agy` — the settings
    document's `env`, in the one place a provider with no settings flag can carry it."""
    assert command.count("env") == 1 and command[0] == "env", command
    assert command.count("agy") == 1, command
    return command[1 : command.index("agy")]


def _command_resource_attributes(tokens):
    """The pairs of the one `OTEL_RESOURCE_ATTRIBUTES=` token among `tokens`."""
    carried = [token for token in tokens if token.startswith("OTEL_RESOURCE_ATTRIBUTES=")]
    assert len(carried) == 1, tokens
    return carried[0].split("=", 1)[1].split(",")


def test_gemini_dry_run_prints_the_run_id_in_the_command(tmp_path):
    """CP-211, CP-215: the printed run ID reaches `agy`, with the endpoint it exports to, as the
    `env` prefix — never as a `--settings` flag `agy` does not have, nor Codex's exporter config."""
    result = _dry_run(tmp_path, "gemini", _published_endpoint(tmp_path))

    assert result.returncode == 0, result.stderr
    run_id = _printed_run_id(result.stdout)
    command = _printed_command(result.stdout)
    prefix = _gemini_env_prefix(command)
    attributes = _command_resource_attributes(command)
    assert attributes == _command_resource_attributes(prefix)
    assert f"kensai.run_id={run_id}" in attributes
    assert f"OTEL_EXPORTER_OTLP_ENDPOINT={_ENDPOINT}" in prefix
    assert "OTEL_LOGS_EXPORTER=otlp" in prefix
    assert not any(token.startswith("otel.exporter") for token in command), command
    assert "--settings" not in command
    assert _provenance(attributes) == _provenance(_telemetry_pairs(result.stdout))


def test_tier_gemini_sonnet_stamps_flash_medium_tier(tmp_path):
    """CP-207, CP-208, CP-210: a tier-sourced Gemini launch runs at, stamps and carries the same
    pair `model_assignment.py --provider gemini --tier sonnet` resolves."""
    result = _launch_dry(
        tmp_path, _NO_INTELLIGENCE_SKILL, *_NO_INTELLIGENCE_ARGS, "--provider", "gemini", "--model-tier", "sonnet"
    )

    assert result.returncode == 0, result.stderr
    expected = {
        "kensai.provider": "gemini",
        "kensai.model": "gemini-3.8-flash-medium",
        "kensai.effort": "medium",
        "kensai.source": "tier",
    }
    assert _provenance(_telemetry_pairs(result.stdout)) == expected
    command = _printed_command(result.stdout)
    assert _flag_value(command, "--model") == "gemini-3.8-flash-medium"
    assert _flag_value(command, "--effort") == "medium"
    assert _provenance(_command_resource_attributes(_gemini_env_prefix(command))) == expected


def test_no_intelligence_no_tier_gemini_stamps_default_source_only(tmp_path):
    """CP-207, CP-210: with nothing resolved, `agy` gets no model or effort, and neither the line
    nor the command's resource attributes claims one."""
    result = _launch_dry(tmp_path, _NO_INTELLIGENCE_SKILL, *_NO_INTELLIGENCE_ARGS, "--provider", "gemini")

    assert result.returncode == 0, result.stderr
    assert "Intelligence: none — provider default" in result.stdout
    expected = {"kensai.provider": "gemini", "kensai.source": "default"}
    assert _provenance(_telemetry_pairs(result.stdout)) == expected
    command = _printed_command(result.stdout)
    assert "--model" not in command
    assert "--effort" not in command
    assert _provenance(_command_resource_attributes(_gemini_env_prefix(command))) == expected


def _assert_gemini_launch_is_uninstrumented(result, reason):
    """CP-212: the one uninstrumented line, then the launch as it would be anyway — `agy`, with
    no `OTEL_` variable handed to it. A `KENSAIAPP_CONTEXT_CAP` the caller exported may ride the
    `env` prefix (`run_telemetry.sh` keeps it when the run is uninstrumented); it is not
    telemetry."""
    assert result.returncode == 0, result.stderr
    lines = [line.strip() for line in result.stdout.splitlines()]
    assert f"({reason} — run uninstrumented)" in lines, result.stdout
    assert _DRY_RUN_HEADING in lines, result.stdout
    command = _printed_command(result.stdout)
    assert command.count("agy") == 1, command
    assert not any(token.startswith("OTEL_") for token in command), command
    assert "--settings" not in command


def test_gemini_dry_run_with_no_endpoint_stays_uninstrumented(tmp_path):
    missing = tmp_path / "no-endpoint"

    result = _dry_run(tmp_path, "gemini", missing)

    _assert_gemini_launch_is_uninstrumented(
        result, f"no published telemetry endpoint at {missing}"
    )


def test_gemini_dry_run_with_a_malformed_endpoint_stays_uninstrumented(tmp_path):
    endpoint_file = _published_endpoint(tmp_path, "not-a-url\n")

    result = _dry_run(tmp_path, "gemini", endpoint_file)

    _assert_gemini_launch_is_uninstrumented(
        result, f"telemetry endpoint at {endpoint_file} is unreadable or malformed"
    )


def test_gemini_launch_stamps_provider_and_source(tmp_path):
    """CP-207, CP-208, CP-210: the intelligence file's pair is what `agy` is launched at, what the
    `Telemetry:` line stamps, and what the command's own resource attributes carry."""
    result = _launch_dry(tmp_path, _SKILL, _PROJECT, "--provider", "gemini")

    assert result.returncode == 0, result.stderr
    expected = {
        "kensai.provider": "gemini",
        "kensai.model": _intelligence_of("gemini", "Model"),
        "kensai.effort": _intelligence_of("gemini", "Effort"),
        "kensai.source": "intelligence",
    }
    assert _provenance(_telemetry_pairs(result.stdout)) == expected
    command = _printed_command(result.stdout)
    assert _flag_value(command, "--model") == expected["kensai.model"]
    assert _flag_value(command, "--effort") == expected["kensai.effort"]
    assert _provenance(_command_resource_attributes(_gemini_env_prefix(command))) == expected


def test_new_keys_follow_the_old_keys_on_the_telemetry_line(tmp_path):
    result = _launch_dry(tmp_path, _SKILL, _PROJECT, "--provider", "codex")

    assert result.returncode == 0, result.stderr
    keys = [pair.partition("=")[0] for pair in _telemetry_pairs(result.stdout)]
    assert keys == [*_PRE_CHANGE_KEYS, *_PROVENANCE_KEYS]


# --- surfaced by development-code-integrity (same change) -----------------------------------------


def _instance_with_the_delivered_file(tmp_path):
    """The scratch instance, named for what these cases read off it: the delivered template as its
    own `.providers.toml`."""
    return _scratch_instance(tmp_path)


def _launch_dry_env(tmp_path, *cli, provider_env=None, skills_root=None, instance=None):
    """`_launch_dry`, but with `KENSAIAPP_AGENT_PROVIDER` set to `provider_env` (or cleared), and
    run from `instance` when one is given (the scratch instance otherwise)."""
    env = _isolated_env(tmp_path, _published_endpoint(tmp_path))
    if provider_env is not None:
        env["KENSAIAPP_AGENT_PROVIDER"] = provider_env
    if skills_root is not None:
        env["LAUNCH_SKILL_SKILLS_ROOT"] = str(skills_root)
    return subprocess.run(
        [str(_LAUNCHER), *cli, "--dry-run"],
        cwd=str(instance or _scratch_instance(tmp_path)),
        capture_output=True,
        text=True,
        env=env,
    )


def test_provider_stamp_falls_back_to_the_env_then_to_the_skill_entry(tmp_path):
    """CP-188: `<provider>` is `--provider`, else `KENSAIAPP_AGENT_PROVIDER`, else the
    `launchers.skill` entry of the central provider file (`claude` as delivered)."""
    from_env = _launch_dry_env(tmp_path, _NO_INTELLIGENCE_SKILL, *_NO_INTELLIGENCE_ARGS, provider_env="codex")
    assert from_env.returncode == 0, from_env.stderr
    assert _provenance(_telemetry_pairs(from_env.stdout))["kensai.provider"] == "codex"

    flag_wins = _launch_dry_env(
        tmp_path, _NO_INTELLIGENCE_SKILL, *_NO_INTELLIGENCE_ARGS, "--provider", "gemini", provider_env="codex"
    )
    assert flag_wins.returncode == 0, flag_wins.stderr
    assert _provenance(_telemetry_pairs(flag_wins.stdout))["kensai.provider"] == "gemini"

    # Neither is given, so the stamp is the `launchers.skill` entry's value — `claude` as delivered.
    neither = _launch_dry_env(tmp_path, _NO_INTELLIGENCE_SKILL, *_NO_INTELLIGENCE_ARGS,
                              instance=_instance_with_the_delivered_file(tmp_path))
    assert neither.returncode == 0, neither.stderr
    assert _provenance(_telemetry_pairs(neither.stdout)) == {
        "kensai.provider": "claude",
        "kensai.source": "default",
    }


def test_an_unexportable_resolved_model_drops_that_key_and_the_launch_proceeds(tmp_path):
    """CP-194 through a launch: a model `OTEL_RESOURCE_ATTRIBUTES` cannot carry drops
    `kensai.model` alone, named on one line; the rest is stamped and the launch is not failed."""
    skill_dir = tmp_path / "host" / ".claude" / "skills" / "comma-model-demo"
    (skill_dir / "intelligence").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: comma-model-demo\n---\n")
    (skill_dir / "launcher.md").write_text(
        "**Agent:** pm\n**Arguments:** <project>\n**Prompt:** demo for {project}.\n"
    )
    (skill_dir / "intelligence" / "codex.md").write_text("**Model:** a,b\n**Effort:** high\n")

    result = _launch_dry_env(
        tmp_path, "comma-model-demo", _PROJECT, "--provider", "codex",
        skills_root=tmp_path / "host",
    )

    assert result.returncode == 0, result.stderr
    assert _provenance(_telemetry_pairs(result.stdout)) == {
        "kensai.provider": "codex",
        "kensai.effort": "high",
        "kensai.source": "intelligence",
    }
    naming = [line for line in result.stdout.splitlines() if "kensai.model" in line]
    assert len(naming) == 1, result.stdout
    assert _DRY_RUN_HEADING in result.stdout.splitlines()


# --- surfaced by development-code-integrity (change 2026-09-30_gemini-runs-emit-to-the-receiver) -


@pytest.mark.parametrize(
    ("skill", "extra", "source"),
    [
        (_SKILL, (), "intelligence"),
        (_NO_INTELLIGENCE_SKILL, ("--model-tier", "sonnet"), "tier"),
        (_NO_INTELLIGENCE_SKILL, (), "default"),
    ],
)
def test_gemini_command_carries_the_printed_run_id_on_every_source(tmp_path, skill, extra, source):
    """CP-207 (every source, spec Gap 4), CP-210, CP-211: whichever way the launch resolved, the
    `agy` command carries the one run ID its `Telemetry:` line printed."""
    arguments = _NO_INTELLIGENCE_ARGS if skill == _NO_INTELLIGENCE_SKILL else (_PROJECT,)
    result = _launch_dry(tmp_path, skill, *arguments, "--provider", "gemini", *extra)

    assert result.returncode == 0, result.stderr
    assert _provenance(_telemetry_pairs(result.stdout))["kensai.source"] == source
    attributes = _command_resource_attributes(_gemini_env_prefix(_printed_command(result.stdout)))
    run_ids = [pair for pair in attributes if pair.startswith("kensai.run_id=")]
    assert run_ids == [f"kensai.run_id={_printed_run_id(result.stdout)}"]


def _env_assignments(command):
    """The `KEY=value` tokens between a leading `env` and the program it runs."""
    assert command[0] == "env", command
    assignments = []
    for token in command[1:]:
        if "=" not in token or not re.match(r"^[A-Z_][A-Z0-9_]*=", token):
            break
        assignments.append(token)
    return dict(token.split("=", 1) for token in assignments)


def test_codex_dry_run_still_carries_the_telemetry_keys_model_and_effort(tmp_path):
    """CP-213: a Codex command "still carries the UUID and the same `OTEL_*` keys, model and
    effort" — the `OTEL_*` set `run_telemetry` hands every run, aimed at the published endpoint,
    and the Codex intelligence file's pair as the flags Codex runs at."""
    result = _launch_dry(tmp_path, _SKILL, _PROJECT, "--provider", "codex")

    assert result.returncode == 0, result.stderr
    command = _printed_command(result.stdout)
    env = _env_assignments(command)
    otel_keys = {key for key in env if key.startswith("OTEL_")}
    assert otel_keys == {key for key in _TELEMETRY_KEYS if key.startswith("OTEL_")}, env
    assert env["OTEL_EXPORTER_OTLP_ENDPOINT"] == _ENDPOINT
    run_id = _printed_run_id(result.stdout)
    assert f"kensai.run_id={run_id}" in env["OTEL_RESOURCE_ATTRIBUTES"].split(",")
    assert _flag_value(command, "--model") == _intelligence_of("codex", "Model")
    effort = _intelligence_of("codex", "Effort")
    assert f'model_reasoning_effort="{effort}"' in command


# --- the launcher on the package's turn-on (change 2026-10-21_skill-launcher-runs-on-turn-on) -----

_PROVIDERS = ("claude", "codex", "gemini")
_FIXED_REFUSED_MODEL = (
    "          (kensai.model 'a,b' contains a character OTEL_RESOURCE_ATTRIBUTES cannot carry"
    " — not attached)"
)
_UNINSTRUMENTED = " — run uninstrumented)"


def _claude_settings(result):
    """The `env` of the merged settings document the dry-run Claude command names."""
    command = _printed_command(result.stdout)
    assert command.count("--settings") == 1, command
    return json.loads(Path(_flag_value(command, "--settings")).read_text()).get("env", {})


def _uninstrumented_lines(stdout):
    return [line for line in stdout.splitlines() if line.endswith(_UNINSTRUMENTED)]


def _carried_attributes(result, provider):
    """The attribute pairs the provider's printed command carries: the settings document for
    Claude, the `OTEL_RESOURCE_ATTRIBUTES` assignment for the two that take an `env` prefix."""
    if provider == "claude":
        return _claude_settings(result)["OTEL_RESOURCE_ATTRIBUTES"].split(",")
    return _command_resource_attributes(_printed_command(result.stdout))


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_the_helper_runs_the_package_command_once_before_the_dry_run_split(tmp_path, provider):
    result = _dry_run(tmp_path, provider, _published_endpoint(tmp_path))

    assert result.returncode == 0, result.stderr
    calls = fixture_calls(tmp_path)
    assert len(calls) == 1, calls
    argv = calls[0]["argv"]
    assert argv[:2] == ["turn-on", "--print"], argv
    assert argv[argv.index("--prefix") + 1] == "kensai"
    assert argv[argv.index("--endpoint-file") + 1] == str(tmp_path / "endpoint")
    labels = dict(argv[i + 1].split("=", 1) for i, word in enumerate(argv) if word == "--label")
    assert labels["skill"] == _SKILL and labels["project"] == _PROJECT
    assert labels["provider"] == provider and labels["source"] == "intelligence"
    assert labels["model"] == _intelligence_of(provider, "Model")
    assert labels["effort"] == _intelligence_of(provider, "Effort")
    assert os.path.realpath(calls[0]["cwd"]) == os.path.realpath(_scratch_instance(tmp_path))


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_each_provider_hands_over_one_normalized_settings_document(tmp_path, provider):
    result = _dry_run(tmp_path, provider, _published_endpoint(tmp_path))

    assert result.returncode == 0, result.stderr
    run_id = _printed_run_id(result.stdout)
    attributes = _carried_attributes(result, provider)
    assert attributes == _telemetry_pairs(result.stdout)
    assert attributes.count(f"kensai.run_id={run_id}") == 1
    assert [pair.partition("=")[0] for pair in attributes[:3]] == [
        "kensai.arm",
        "kensai.run_id",
        "kensai.instance",
    ]
    if provider == "claude":
        env = _claude_settings(result)
        assert set(_TELEMETRY_KEYS) <= env.keys(), env
        assert env["OTEL_EXPORTER_OTLP_ENDPOINT"] == _ENDPOINT
    else:
        assert "--settings" not in _printed_command(result.stdout)


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_instrumented_launch_prints_one_stdout_telemetry_line(tmp_path, provider):
    result = _dry_run(tmp_path, provider, _published_endpoint(tmp_path))

    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    printed = [line for line in lines if "Telemetry:" in line]
    assert len(printed) == 1, result.stdout
    match = re.fullmatch(r" {10}Telemetry: {4}(\S+) → (\S+)", printed[0])
    assert match, repr(printed[0])
    assert match.group(1).split(",") == _carried_attributes(result, provider)
    assert match.group(2) == _ENDPOINT
    assert lines.index(printed[0]) < lines.index(_DRY_RUN_HEADING)
    assert "Telemetry:" not in result.stderr
    assert "uninstrumented" not in result.stdout


def test_refused_model_keeps_the_fixed_notice_and_other_tags(tmp_path):
    skill_dir = tmp_path / "host" / ".claude" / "skills" / "comma-model-demo"
    (skill_dir / "intelligence").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: comma-model-demo\n---\n")
    (skill_dir / "launcher.md").write_text(
        "**Agent:** pm\n**Arguments:** <project>\n**Prompt:** demo for {project}.\n"
    )
    (skill_dir / "intelligence" / "codex.md").write_text("**Model:** a,b\n**Effort:** high\n")

    result = _launch_dry(
        tmp_path, "comma-model-demo", _PROJECT, "--provider", "codex",
        skills_root=tmp_path / "host",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines().count(_FIXED_REFUSED_MODEL) == 1, result.stdout
    assert "kensai.model" not in result.stderr
    pairs = _telemetry_pairs(result.stdout)
    assert not any(pair.startswith("kensai.model=") for pair in pairs), pairs
    assert _provenance(pairs) == {
        "kensai.provider": "codex",
        "kensai.effort": "high",
        "kensai.source": "intelligence",
    }
    labels = [word for call in fixture_calls(tmp_path) for word in call["argv"]]
    assert not any(word.startswith("model=") for word in labels), labels


_ENDPOINT_FAILURES = (
    ("absent", None, "no published telemetry endpoint at {file}"),
    ("malformed", "not-a-url\n", "telemetry endpoint at {file} is unreadable or malformed"),
    (
        "remote",
        "http://example.com:4318\n",
        "telemetry endpoint at {file} is not on this machine (loopback only)",
    ),
)


@pytest.mark.parametrize(("kind", "content", "cause"), _ENDPOINT_FAILURES)
@pytest.mark.parametrize("cap", [None, "250000"])
def test_endpoint_failures_keep_the_launch_successful(tmp_path, kind, content, cause, cap):
    endpoint_file = tmp_path / "endpoint"
    if content is not None:
        endpoint_file.write_text(content)

    result = _dry_run(tmp_path, "claude", endpoint_file, KENSAIAPP_CONTEXT_CAP=cap)

    assert result.returncode == 0, result.stderr
    expected = f"          ({cause.format(file=endpoint_file)}{_UNINSTRUMENTED}"
    assert _uninstrumented_lines(result.stdout) == [expected], result.stdout
    assert "Telemetry:" not in result.stdout
    env = _claude_settings(result)
    assert "OTEL_EXPORTER_OTLP_ENDPOINT" not in env and "OTEL_RESOURCE_ATTRIBUTES" not in env
    assert env.get("KENSAIAPP_CONTEXT_CAP") == cap


def _package_failure(tmp_path, kind):
    """The environment changes that make the package command fail one way, and the cause line the
    launcher prints for it."""
    command = tmp_path / ".kensaiapp" / "venv" / "bin" / "absent-command"
    present = tmp_path / ".kensaiapp" / "venv" / "bin" / FIXTURE_COMMAND
    return {
        "unconfigured": (
            {COMMAND_VARIABLE: ""},
            f"no telemetry command configured in {COMMAND_VARIABLE}",
        ),
        "unavailable": (
            {COMMAND_VARIABLE: "absent-command"},
            f"no runnable telemetry command at {command}",
        ),
        "nonzero": (
            {FIXTURE_MODE_VARIABLE: "exit-3"},
            f"telemetry command at {present} exited with status 3",
        ),
        "invalid-document": (
            {FIXTURE_MODE_VARIABLE: "garbage"},
            f"telemetry command at {present} did not print a usable settings document",
        ),
        "incomplete-document": (
            {FIXTURE_MODE_VARIABLE: "incomplete"},
            f"telemetry command at {present} did not print a usable settings document",
        ),
    }[kind]


_SENTINEL = json.dumps({"env": {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://sentinel.invalid/v1"}})


@pytest.mark.parametrize(
    "kind", ["unconfigured", "unavailable", "nonzero", "invalid-document", "incomplete-document"]
)
def test_package_failures_keep_the_launch_successful(tmp_path, kind):
    changes, cause = _package_failure(tmp_path, kind)

    result = _dry_run(
        tmp_path, "claude", _published_endpoint(tmp_path), INSTRUMENT_RUN_SETTINGS=_SENTINEL,
        **changes,
    )

    assert result.returncode == 0, result.stderr
    assert _uninstrumented_lines(result.stdout) == [f"          ({cause}{_UNINSTRUMENTED}"]
    assert "Telemetry:" not in result.stdout
    env = _claude_settings(result)
    assert "OTEL_EXPORTER_OTLP_ENDPOINT" not in env and "OTEL_RESOURCE_ATTRIBUTES" not in env
    command = _printed_command(result.stdout)
    assert "sentinel" not in Path(_flag_value(command, "--settings")).read_text()
