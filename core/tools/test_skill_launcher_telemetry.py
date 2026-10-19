"""The skill launcher hands a Codex or Gemini run the same telemetry it hands a Claude run.

`core/launchers/skill/launcher.sh` tags every run with `instrument_run`, which prints a `Telemetry:`
line carrying the run's `kensai.run_id` and builds `INSTRUMENT_RUN_SETTINGS`. The Claude branch has
always handed that document to the adapter as `--settings`; the Codex branch, and later the Gemini
branch, handed it nothing, so each printed a run ID no record of the run ever carried. Neither
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
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
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


def _dry_run(tmp_path, provider, endpoint_file):
    env = dict(os.environ)
    env["HOME"] = str(tmp_path)
    env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    env.pop("KENSAIAPP_AGENT_PROVIDER", None)
    return subprocess.run(
        [str(_LAUNCHER), _SKILL, _PROJECT, "--provider", provider, "--dry-run"],
        cwd=str(_scratch_instance(tmp_path)),
        capture_output=True,
        text=True,
        env=env,
    )


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


# The variables `instrument_run` hands a run (the set `core/tools/test_instrument_run.py` pins as
# `TELEMETRY_KEYS`); a test module keeps its own copy, as `test_apply_telemetry_env.py` does.
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
# in the order it printed them (`instrument_run skill=… project=…`, plus the derived instance and
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
    env = dict(os.environ)
    env["HOME"] = str(tmp_path)
    env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(_published_endpoint(tmp_path))
    env.pop("KENSAIAPP_AGENT_PROVIDER", None)
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
    `env` prefix (`instrument_run.sh` `_instrument_run_cap_settings`); it is not telemetry."""
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
    env = dict(os.environ)
    env["HOME"] = str(tmp_path)
    env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(_published_endpoint(tmp_path))
    env.pop("KENSAIAPP_AGENT_PROVIDER", None)
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
    effort" — the `OTEL_*` set `instrument_run` hands every run, aimed at the published endpoint,
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
