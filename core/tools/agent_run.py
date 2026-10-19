#!/usr/bin/env python3
"""Build and execute an unattended agent run through a provider adapter.

This module is the provider-neutral boundary between Kensaiapp machinery and
an agent CLI.  Callers describe the run in Kensaiapp terms; an adapter owns
the provider-specific executable, flags, and ordering.  The Claude adapter builds
a ``claude`` command in three shapes and carries the pin delivery when a pin is in
force; the hf adapter builds one of its own, aimed at Hugging Face's router, with
the token kept out of argv, env and written files. The ollama adapter builds the same
command aimed at the Ollama server on the owner's machine, with the vendor's placeholder
credential, and refuses to build one when no server answers. The Codex adapter translates
``agent`` and ``settings`` into Codex terms. Skill runs use native app-server selection; other
runs use ``codex exec``. It refuses ``name`` and ``add_dirs on
resume`` rather than silently weakening a run. The Gemini adapter builds
``agy -p --mode accept-edits --output-format stream-json``, passes the tier's
model and reasoning effort, and turns directory grants into ``--add-dir``.

Foreground execution inherits the caller's working directory and stdio, and its
environment too, except that an hf run's child, foreground or background, receives no
``HF_TOKEN`` (an ollama run's child withholds nothing). Background execution always writes
to a caller-supplied new log.
Who owns the detach is the adapter's to say, per request: a Claude
``Shape.BACKGROUND`` run (``claude --bg``) detaches itself and is owned by
Claude after its launch command returns; a Claude ``Shape.TURN`` run
(``claude --print --output-format stream-json``) and every Codex or Gemini run are
detached by this tool and identified by their local process id, with a
``kensai.exit`` record appended to the log once the process ends. Both return
one normalized JSON record to the caller.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import http.client
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import urllib.request
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal, Protocol, Sequence

import env_file
import hook_wiring
import model_assignment
import pin
import task_context

__version__ = "2.13.0"

BackgroundOwner = Literal["provider", "process"]


class Shape(Enum):
    """The three `claude` command shapes `ClaudeAdapter.command` builds. Never written out or
    read back anywhere a caller sees — only compared against by identity — so a bare `Enum`,
    not `(str, Enum)`."""

    BACKGROUND = "background"
    PRINT = "print"
    TURN = "turn"


class Effort(str, Enum):
    """The reasoning-effort vocabulary's one home — `low`, `medium`, `high`, and Claude's own two
    above them, `xhigh` and `max` (`CLAUDE_ONLY_EFFORTS`); the CLI's `--effort` choices are drawn
    from it and the Claude adapter emits any of the five. Codex and Gemini take the first three
    and refuse the rest. Its value is written
    onto the provider command and read back from the CLI's string, so `(str, Enum)`, not the bare
    `Enum` of `Shape`, which is only ever compared."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"
    MAX = "max"


CLAUDE_ONLY_EFFORTS = frozenset({Effort.XHIGH, Effort.MAX})


@dataclass(frozen=True)
class RunRequest:
    """Provider-independent description of one unattended agent run."""

    prompt: str
    agent: str | None = None
    name: str | None = None
    resume_session_id: str | None = None
    model: str | None = None
    model_tier: str | None = None
    add_dirs: tuple[str, ...] = ()
    settings: str | None = None
    core_root: Path | None = None
    shape: Shape = Shape.BACKGROUND
    session_id: str | None = None
    instance_root: Path | None = None
    pin: pin.Pin | None = None
    effort: Effort | None = None
    skill_name: str | None = None
    skill_path: Path | None = None
    granted_skills: tuple[str, ...] = ()


class ProviderAdapter(Protocol):
    """Translate a neutral run request into one provider command.

    An adapter may also carry `withheld_environment: frozenset[str]`, the variable names its
    child must not inherit. It is optional: an adapter without it withholds nothing, and the
    runner reads it with a default (`AgentRunner._withhold_keyword`).
    """

    def background_owner(self, request: RunRequest) -> BackgroundOwner: ...

    def command(self, request: RunRequest) -> tuple[str, ...]: ...

    def background_command(self, request: RunRequest) -> tuple[str, ...]: ...


class Processes(Protocol):
    """The process port used by ``AgentRunner``.

    Each method takes a keyword-only ``withhold``, the variable names the child must not
    inherit. The child gets the process's environment as it stands at the call, less those
    names; an empty ``withhold`` is today's start, the whole environment inherited.
    """

    def run(self, argv: Sequence[str], *, withhold: frozenset[str] = frozenset()) -> int: ...

    def run_to_log(
        self, argv: Sequence[str], log_path: Path, *, withhold: frozenset[str] = frozenset()
    ) -> int: ...

    def start_detached(
        self, argv: Sequence[str], log_path: Path, *, withhold: frozenset[str] = frozenset()
    ) -> int: ...


# A detached `--print` run ends with its turn: nothing wakes it afterwards, the way a `claude --bg`
# session was woken when its background work finished. So a command may not wait in the background
# (https://code.claude.com/docs/en/headless.md § Background tasks at exit — a background command
# "ends shortly after the run's final result"; tools-reference.md § Background commands — a command
# that reaches its timeout is moved to the background):
# - `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` — no `run_in_background`, no auto-backgrounding; a
#   subagent runs in the foreground (sub-agents.md § Run subagents in foreground or background). A
#   command that reaches its timeout is then stopped and reported to the run (measured 2026-09-25:
#   "Command timed out after 5s", exit 143), which can run it again with a longer `timeout`. It
#   leaves `Monitor`, `ScheduleWakeup` and `CronCreate` in the tool list; no step the chains launch
#   uses them (measured over this machine's 756 launcher-started transcripts, 2026-09-25).
# - `BASH_DEFAULT_TIMEOUT_MS` — ten minutes, the documented ceiling's own default, so a long test
#   suite runs to its end in the foreground rather than being stopped at two.
# - `BASH_MAX_TIMEOUT_MS` — six hours, the length of the run watcher's own deadline
#   (`watch_process.py --timeout-seconds`): the longest one command may ask for.
# - `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` — a workflow the run starts is waited on to its end
#   (headless.md § Background tasks at exit); the watcher bounds the run instead.
_DETACHED_PRINT_ENV = {
    "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
    "BASH_DEFAULT_TIMEOUT_MS": "600000",
    "BASH_MAX_TIMEOUT_MS": "21600000",
    "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0",
}


def _env_prefix(env: dict[str, str]) -> tuple[str, ...]:
    """A leading `env KEY=value …` that hands a detached provider process its own variables, in
    `env`'s order — nothing when `env` is empty."""
    if not env:
        return ()
    return ("env", *(f"{key}={value}" for key, value in env.items()))


class ClaudeAdapter:
    """Claude Code's unattended run command, in three shapes (`Shape.BACKGROUND`, `Shape.PRINT`,
    `Shape.TURN`)."""

    def background_owner(self, request: RunRequest) -> BackgroundOwner:
        """`claude --bg` detaches itself; a `--print` run is an ordinary process this tool
        detaches and watches, exactly as it does a Codex one."""
        return "provider" if request.shape is Shape.BACKGROUND else "process"

    def command(self, request: RunRequest) -> tuple[str, ...]:
        if request.shape is Shape.TURN:
            argv = self._turn_command(request)
        else:
            verb = ("claude", "--bg") if request.shape is Shape.BACKGROUND else ("claude", "-p")
            argv = self._background_or_print_command(request, verb=verb)
        if request.pin is not None:
            argv = argv + _pin_delivery(request)
        return argv

    def background_command(self, request: RunRequest) -> tuple[str, ...]:
        if self.background_owner(request) == "provider":
            return self.command(request)
        return (*_env_prefix(_DETACHED_PRINT_ENV), *self.command(request))

    def _prompt_argument(self, request: RunRequest) -> str:
        """The one argument carrying the launch's prompt, in every shape. The level it names is
        read from `request.effort`, the same field the `--effort` token is, so the two cannot
        differ; with no effort it is the prompt alone."""
        level = request.effort.value if request.effort is not None else None
        return task_context.claude_bootstrap(request.prompt, level)

    def _background_or_print_command(
        self, request: RunRequest, *, verb: tuple[str, ...]
    ) -> tuple[str, ...]:
        """`Shape.BACKGROUND` (`claude --bg`) and `Shape.PRINT` (`claude -p`) share every flag
        and its position — only the leading verb and `PRINT`'s `--permission-prompts none` differ. This is today's pre-`Shape`
        `ClaudeAdapter.command` order, unchanged, for `BACKGROUND`; `product-card/launcher.sh`'s
        own `-p` order collapses onto the same order once its absent fields (name, model,
        resume) are left out."""
        argv = list(verb)
        if request.name:
            argv.extend(("--name", request.name))
        if request.resume_session_id:
            argv.extend(("--resume", request.resume_session_id))
        argv.append(self._prompt_argument(request))
        if request.agent:
            argv.extend(("--agent", request.agent))
        assignment = _assignment("claude", request)
        if assignment:
            argv.extend(("--model", assignment.model))
        if request.effort is not None:
            argv.extend(("--effort", request.effort.value))
        # A detached run has nobody present to answer an interactive prompt.
        argv.extend(("--permission-mode", "auto"))
        # `--permission-prompts` is a `--print` flag. A `--bg` run passed it on 2026-09-25 and still
        # stopped on an `rm -rf` prompt, so it was reverted from `BACKGROUND`, and `BACKGROUND` goes
        # without it.
        if request.shape is Shape.PRINT:
            argv.extend(("--permission-prompts", "none"))
        for directory in request.add_dirs:
            argv.append(f"--add-dir={directory}")
        if request.settings and request.pin is None:
            argv.extend(("--settings", request.settings))
        return tuple(argv)

    def _turn_command(self, request: RunRequest) -> tuple[str, ...]:
        """`Shape.TURN` — the same shape `agent_turn.claude_command` builds today. Resuming is
        decided by `resume_session_id` (as it already is for `BACKGROUND`/`PRINT`'s own
        `--resume`); starting uses `request.session_id` as the turn's own fresh identity."""
        argv = ["claude", "--print", "--output-format", "stream-json", "--verbose"]
        resuming = bool(request.resume_session_id)
        if resuming:
            argv.extend(("--resume", request.resume_session_id))
        else:
            argv.extend(("--session-id", request.session_id))
        if not resuming:
            if request.name:
                argv.extend(("--name", request.name))
            if request.agent:
                argv.extend(("--agent", request.agent))
        assignment = _assignment("claude", request)
        if assignment:
            argv.extend(("--model", assignment.model))
        if request.effort is not None:
            argv.extend(("--effort", request.effort.value))
        argv.extend(("--permission-mode", "auto", "--permission-prompts", "none"))
        if not resuming:
            for directory in request.add_dirs:
                argv.append(f"--add-dir={directory}")
            if request.settings and request.pin is None:
                argv.extend(("--settings", request.settings))
        argv.append(self._prompt_argument(request))
        return tuple(argv)


class UnsupportedRequest(ValueError):
    pass


def _refuse_a_claude_only_effort(provider: str, request: RunRequest) -> None:
    if request.effort in CLAUDE_ONLY_EFFORTS:
        raise UnsupportedRequest(
            f"provider {provider!r} does not support effort {request.effort.value!r}"
        )


def _assignment(
    provider: str, request: RunRequest
) -> model_assignment.ModelAssignment | None:
    if request.model and request.model_tier:
        raise UnsupportedRequest(
            "request fields model and model_tier are mutually exclusive"
        )
    if request.model:
        return model_assignment.ModelAssignment(request.model)
    if request.model_tier:
        return model_assignment.resolve(provider, request.model_tier)
    return None


def _instance_key(instance_root: Path) -> str:
    """A filesystem-safe identifier for `instance_root`, stable across repeated calls so two
    calls for the same (pin, instance) pair find the plugin and merged settings already built
    rather than colliding with, or overwriting, another instance's own owned set."""
    digest = hashlib.sha256(str(Path(instance_root).resolve()).encode("utf-8")).hexdigest()
    return digest[:16]


def _link_owned(target_dir: Path, owned: pin.Ownership) -> None:
    """`target_dir` holds one symlink per name in `owned`, and nothing else — rebuilt fresh each
    call so a name dropped since the last build does not linger."""
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True)
    for name in owned:
        (target_dir / name).symlink_to(owned[name])


def _grant_key(groups: frozenset[str]) -> str:
    """A filesystem-safe identifier for one set of granted skill groups — a digest of the sorted
    names, so two grants that reach the same groups share a plugin directory and two that reach
    different groups never do."""
    digest = hashlib.sha256("\0".join(sorted(groups)).encode("utf-8")).hexdigest()
    return digest[:16]


def _build_plugin(
    request_pin: pin.Pin, instance_root: Path, groups: frozenset[str] = frozenset()
) -> Path:
    """A `.claude-plugin/plugin.json` plus `skills/<name>` and `workflows/<name>` links to the
    granted owned set (the pin's flat skills, the granted `groups`' skills, the instance's own,
    and every workflow), built inside the pin and keyed by instance and by grant so two
    instances sharing a pin never share an owned set and two grants never overwrite each
    other."""
    instance_dir = request_pin.root / "instances" / _instance_key(instance_root)
    plugin_dir = instance_dir / "plugins" / _grant_key(groups)
    _link_owned(
        plugin_dir / "skills",
        pin.owned_entries(request_pin, instance_root, pin.Kind.SKILLS, groups=groups),
    )
    _link_owned(
        plugin_dir / "workflows", pin.owned_entries(request_pin, instance_root, pin.Kind.WORKFLOWS)
    )
    plugin_json_dir = plugin_dir / ".claude-plugin"
    plugin_json_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": f"kensaiapp-pin-{request_pin.id}",
        "version": "1.0.0",
        "description": "The host's pinned skills and workflows, plus the instance's own.",
    }
    (plugin_json_dir / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return plugin_dir


def _merge_settings_layer(base, layer):
    """Objects merge key by key, arrays concatenate without duplicates, and for a scalar (or a
    type mismatch) the later layer wins."""
    if isinstance(base, dict) and isinstance(layer, dict):
        merged = dict(base)
        for key, value in layer.items():
            merged[key] = _merge_settings_layer(merged[key], value) if key in merged else value
        return merged
    if isinstance(base, list) and isinstance(layer, list):
        merged = list(base)
        for item in layer:
            if item not in merged:
                merged.append(item)
        return merged
    return layer


def _rewrite_hooks_into_pin(document, request_pin: pin.Pin):
    """Point every hook command at the pin's own hooks directory. The rewrite itself is
    `hook_wiring.rewrite_hooks_dir`'s, shared with the satellite linker."""
    return hook_wiring.rewrite_hooks_dir(document, request_pin.root / ".claude" / "hooks")


# Every pinned launch is a `--bg` candidate, and `--bg` forces worktree isolation unless this
# says otherwise. A layer of the launch itself, so no repo's tracked settings have to carry it.
_PINNED_RUN_WORKTREE_LAYER = {"worktree": {"bgIsolation": "none"}}


def _write_merged_settings(
    request_pin: pin.Pin, instance_root: Path, caller_settings: str | None
) -> Path:
    """The pinned `.claude/settings.json` (hooks rewritten into the pin), then the fixed
    `worktree` layer, then the instance's own `settings.local.json`, then the caller's
    `--settings`, then `{"env": run_env}` — merged one layer at a time and written once, inside
    the pin, keyed by instance."""
    merged: dict = {}

    pinned_settings_path = request_pin.root / ".claude" / "settings.json"
    if pinned_settings_path.is_file():
        pinned = json.loads(pinned_settings_path.read_text())
        merged = _merge_settings_layer(merged, _rewrite_hooks_into_pin(pinned, request_pin))

    merged = _merge_settings_layer(merged, _PINNED_RUN_WORKTREE_LAYER)

    instance_settings_path = Path(instance_root) / ".claude" / "settings.local.json"
    if instance_settings_path.is_file():
        merged = _merge_settings_layer(merged, json.loads(instance_settings_path.read_text()))

    if caller_settings:
        merged = _merge_settings_layer(merged, json.loads(caller_settings))

    merged = _merge_settings_layer(merged, {"env": pin.run_env(request_pin, os.environ)})

    instance_dir = request_pin.root / "instances" / _instance_key(instance_root)
    instance_dir.mkdir(parents=True, exist_ok=True)
    settings_path = instance_dir / "settings.json"
    settings_path.write_text(json.dumps(merged, indent=2) + "\n")
    return settings_path


def _read_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    """The flat `key: value` frontmatter every agent file opens with, and its body as the
    prompt. Every field this house's agent files carry (`name`, `description`, `tools`, `model`)
    is a single line — no multi-line values, no nesting — so a plain split is enough; no `yaml`
    import (`languages/python/toolchain.md` — effectively zero third-party dependencies)."""
    lines = path.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "\n".join(lines).strip()
    fields: dict[str, str] = {}
    index = 1
    while index < len(lines) and lines[index].strip() != "---":
        if ":" in lines[index]:
            key, _, value = lines[index].partition(":")
            fields[key.strip()] = value.strip()
        index += 1
    body = "\n".join(lines[index + 1 :]).strip()
    return fields, body


def _write_instance_instructions(request_pin: pin.Pin, instance_root: Path) -> Path | None:
    """The file a pinned run appends as its system prompt: the instance's `AGENTS.md` (routing)
    followed by its `kensaiapp.md` (identity), written once inside the pin, keyed by instance.
    One file because the flag takes one, and because an appended file's `@` import is not
    expanded — the identity has to arrive as bytes. Both are read live from the instance, not the
    pin. `kensaiapp.md` is what marks an instance as holding the pair: one without it that still
    holds a `CLAUDE.md` is on the single-file layout, where that file is the whole of its
    instructions and any `AGENTS.md` beside it only points back at it — so it gets `CLAUDE.md`
    as-is. An instance with none of the three gets nothing."""
    agents_md = instance_root / "AGENTS.md"
    identity = instance_root / "kensaiapp.md"
    claude_md = instance_root / "CLAUDE.md"
    if not identity.exists() and claude_md.exists():
        return claude_md
    if not agents_md.exists():
        return None
    parts = [agents_md.read_text(encoding="utf-8")]
    if identity.exists():
        parts.append(identity.read_text(encoding="utf-8"))
    instance_dir = request_pin.root / "instances" / _instance_key(instance_root)
    instance_dir.mkdir(parents=True, exist_ok=True)
    instructions_path = instance_dir / "instructions.md"
    instructions_path.write_text("\n".join(parts), encoding="utf-8")
    return instructions_path


def _agent_record(path: Path) -> dict[str, object]:
    frontmatter, body = _read_frontmatter(path)
    record: dict[str, object] = {
        "description": frontmatter.get("description", ""),
        "prompt": body,
    }
    if "tools" in frontmatter:
        record["tools"] = [tool.strip() for tool in frontmatter["tools"].split(",") if tool.strip()]
    if "model" in frontmatter:
        record["model"] = frontmatter["model"]
    return record


def _build_agents_json(request_pin: pin.Pin, instance_root: Path) -> str:
    owned = pin.owned_entries(request_pin, instance_root, pin.Kind.AGENTS)
    agents = {name: _agent_record(owned[name]) for name in owned}
    return json.dumps(agents, sort_keys=True)


def _pin_delivery(request: RunRequest) -> tuple[str, ...]:
    """The six flags a pinned run's Claude command always carries, appended once regardless of
    shape or resume state: `--setting-sources user`, `--plugin-dir`, one merged `--settings`,
    `--agents`, `--append-system-prompt-file` (only when the instance holds an `AGENTS.md`), and
    `--add-dir=<pin root>` (one token: the CLI reads a separated `--add-dir <dir>` as swallowing
    the prompt that follows it)."""
    request_pin = request.pin
    instance_root = Path(request.instance_root)
    groups = pin.granted_groups(request_pin, request.granted_skills)
    plugin_dir = _build_plugin(request_pin, instance_root, groups)
    settings_path = _write_merged_settings(request_pin, instance_root, request.settings)
    agents_json = _build_agents_json(request_pin, instance_root)

    argv = [
        "--setting-sources",
        "user",
        "--plugin-dir",
        str(plugin_dir),
        "--settings",
        str(settings_path),
        "--agents",
        agents_json,
    ]
    instructions = _write_instance_instructions(request_pin, instance_root)
    if instructions is not None:
        argv.extend(("--append-system-prompt-file", str(instructions)))
    argv.append(f"--add-dir={request_pin.root}")
    return tuple(argv)


_CODEX_ENV_KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _codex_settings_env(settings: str | None, provider: str = "codex") -> tuple[str, ...]:
    """Translation of a Claude-style `--settings` document for a provider with no settings
    file flag: every entry of its `env` object as a leading `env KEY=value …` on the argv, in
    the document's own order (CP-131). No settings, `{}`, or an empty `env` leave the argv
    unchanged — an empty tuple here (CP-134). The validation is `_settings_env`'s."""
    return _env_prefix(_settings_env(settings, provider))


def _settings_env(settings: str | None, provider: str) -> dict[str, str]:
    """The `env` object of a Claude-style `--settings` document, validated whole — empty for no
    settings, `{}`, or an empty `env`.

    Any other top-level key has no equivalent and is refused by name, sorted (CP-132). A
    document that is not a JSON object, an `env` that is not an object, or an `env` entry whose
    name is not a plain identifier or whose value is not a string, is refused as malformed
    (CP-133) — validated whole before anything is built, so a refusal never leaves a partial
    command. `provider` is the name the refusal quotes."""
    if not settings:
        return {}

    malformed = UnsupportedRequest(
        f"provider {provider!r} settings must be a JSON object whose env maps "
        "variable names to strings"
    )
    try:
        document = json.loads(settings)
    except json.JSONDecodeError:
        raise malformed from None
    if not isinstance(document, dict):
        raise malformed

    unsupported = sorted(key for key in document if key != "env")
    if unsupported:
        names = ", ".join(unsupported)
        raise UnsupportedRequest(
            f"provider {provider!r} has no equivalent for settings keys: {names}"
        )

    env = document.get("env", {})
    if not isinstance(env, dict):
        raise malformed
    for key, value in env.items():
        if not isinstance(key, str) or not _CODEX_ENV_KEY_RE.fullmatch(key):
            raise malformed
        if not isinstance(value, str):
            raise malformed

    return env


# The OTLP protocols `instrument_run` may export (`OTEL_EXPORTER_OTLP_PROTOCOL`), spelled as
# Codex's OTLP/HTTP exporter names them (https://developers.openai.com/codex/config-advanced
# § Observability and telemetry). gRPC has its own exporter kind and is not mapped here.
_CODEX_OTLP_HTTP_PROTOCOLS = {"http/json": "json", "http/protobuf": "binary"}


def _codex_otel_exporter_config(env: dict[str, str]) -> str | None:
    """The one `otel.exporter=…` `--config` value that turns on Codex's own OTLP log export, read
    off a telemetry-bearing settings `env`; `None` when the env carries no telemetry Codex can
    export. Never a refusal: telemetry never decides a run (CP-184).

    Codex exports nothing unless its `[otel]` config names an exporter, and it ignores the
    `OTEL_*` exporter variables it inherits — it reads only `OTEL_RESOURCE_ATTRIBUTES`, which
    the `env` prefix already carries (CP-182). So the exporter is configured here and the run ID
    rides the environment."""
    if env.get("OTEL_LOGS_EXPORTER") != "otlp":
        return None
    protocol = _CODEX_OTLP_HTTP_PROTOCOLS.get(env.get("OTEL_EXPORTER_OTLP_PROTOCOL", ""))
    if protocol is None:
        return None
    endpoint = env.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return None
    # Codex takes the full logs URL, not the OTLP base URL the variable holds — the base-only form
    # was never measured to reach the receiver, and the full one was (0 → 5 records, 2026-09-29).
    logs_url = f"{endpoint.removesuffix('/')}/v1/logs"
    # The value is a TOML inline table. A JSON string is a TOML basic string — every escape
    # `json.dumps` writes is one TOML reads the same — so a quote in the URL cannot end it early.
    return (
        f"otel.exporter={{otlp-http={{endpoint={json.dumps(logs_url)},"
        f"protocol={json.dumps(protocol)}}}}}"
    )


# The repo this file sits in (`core/tools/agent_run.py`, two levels down): the host whose skill
# groups hold the agents, which an instance with no `skills/` of its own is still served from.
_HOST_ROOT = Path(__file__).resolve().parents[2]


def _codex_agent_context(
    request: RunRequest,
    assignment: model_assignment.ModelAssignment | None,
    provider: str = "codex",
    host_root: Path = _HOST_ROOT,
) -> tuple[str, model_assignment.ModelAssignment | None]:
    """The sentence naming `request.agent` and its file, and `assignment` returned as it came:
    resolve the file with `pin.agent_file`, which with no pin falls back to the agent's group
    under `host_root`. An agent file's own `model:` is never read — nothing falls back to it. A
    missing instance root or an unknown agent is refused by name."""
    if request.instance_root is None:
        raise UnsupportedRequest(
            f"provider {provider!r} needs an instance root to find agent '{request.agent}'"
        )
    agent_path = pin.agent_file(
        request.pin, request.instance_root, request.agent, host_root=host_root
    )
    if agent_path is None:
        raise UnsupportedRequest(
            f"provider {provider!r} found no agent file for '{request.agent}' under "
            f"{request.instance_root}"
        )

    sentence = (
        f"You are running as the {request.agent} agent. Read {agent_path.resolve()} in full "
        "and follow it as your agent identity before doing this task:"
    )
    return sentence, assignment


class CodexAdapter:
    """Codex CLI's non-interactive workspace-writing command.

    `agent` and `settings` carry semantics in Kensaiapp, and Codex has no CLI flag for either, so
    this adapter translates both itself: `agent` becomes a sentence naming the agent and its file,
    prepended to the prompt (see `_codex_agent_context`); `settings`'s `env` object becomes a
    leading `env KEY=value …` on the argv (see `_codex_settings_env`), and when that `env` carries
    telemetry, one `--config otel.exporter=…` too (see `_codex_otel_exporter_config`). `name` has
    no Codex equivalent and is still refused.
    """

    def background_owner(self, request: RunRequest) -> BackgroundOwner:
        return "process"

    def command(self, request: RunRequest) -> tuple[str, ...]:
        return self._command(request, json_events=False)

    def background_command(self, request: RunRequest) -> tuple[str, ...]:
        return self._command(request, json_events=True)

    def _command(
        self, request: RunRequest, *, json_events: bool
    ) -> tuple[str, ...]:
        if bool(request.skill_name) != bool(request.skill_path):
            raise UnsupportedRequest("native skill requires both skill_name and skill_path")
        if request.skill_path is not None and request.resume_session_id:
            raise UnsupportedRequest("native skill selection requires a fresh run")
        unsupported = []
        if request.name:
            unsupported.append("name")
        if request.resume_session_id and request.add_dirs:
            unsupported.append("add_dirs on resume")
        if unsupported:
            names = ", ".join(unsupported)
            raise UnsupportedRequest(
                f"provider 'codex' does not support request fields: {names}"
            )

        _refuse_a_claude_only_effort("codex", request)
        settings_env = _settings_env(request.settings, "codex")
        env_prefix = _env_prefix(settings_env)
        exporter_config = _codex_otel_exporter_config(settings_env)

        assignment = _assignment("codex", request)
        agent_sentence = ""
        if request.agent:
            agent_sentence, assignment = _codex_agent_context(request, assignment)

        if request.skill_path is not None:
            argv = [
                sys.executable, str(Path(__file__).with_name("codex_skill_run.py")),
                "--skill-name", request.skill_name,
                "--skill-path", str(request.skill_path.resolve()),
            ]
        elif request.resume_session_id:
            argv = ["codex", "exec", "--approve-for-me", "resume"]
        else:
            argv = ["codex", "exec", "--approve-for-me"]
        if json_events:
            argv.append("--json")
        if assignment:
            argv.extend(("--model", assignment.model))
        effort = (
            request.effort.value
            if request.effort is not None
            else (assignment.reasoning_effort if assignment else None)
        )
        if effort:
            argv.extend(("--config", f'model_reasoning_effort="{effort}"'))
        if exporter_config:
            argv.extend(("--config", exporter_config))
        if not request.resume_session_id:
            for directory in request.add_dirs:
                argv.extend(("--add-dir", directory))
        if request.resume_session_id:
            argv.append(request.resume_session_id)
        prompt = request.prompt
        if agent_sentence:
            prompt = f"{agent_sentence} {prompt}"
        if request.core_root is not None:
            prompt = task_context.codex_bootstrap(
                request.core_root,
                prompt,
                assignment.model if assignment else None,
                effort,
            )
        if request.skill_path is not None and request.core_root is not None:
            argv.extend(("--core-dir", str(request.core_root)))
        argv.append(prompt)
        return (*env_prefix, *argv)


class GeminiAdapter:
    """Google Antigravity's unattended headless command.

    One shape, ``agy -p``. A background run asks for ``--output-format stream-json``
    and ``--mode accept-edits``. ``name`` has no flag and is refused. Each ``add_dirs``
    entry becomes ``--add-dir <directory>``. If ``skill_path`` is provided, its parent
    directory is added via ``--add-dir``. ``settings`` translates the `env` object into
    leading environment variables and refuses every other key. Model and reasoning
    effort come from the tier; a caller's ``effort`` wins over the tier's. When
    ``core_root`` is given, prepends context through ``task_context.gemini_bootstrap``.
    """

    def background_owner(self, request: RunRequest) -> BackgroundOwner:
        return "process"

    def command(self, request: RunRequest) -> tuple[str, ...]:
        return self._command(request, stream=False)

    def background_command(self, request: RunRequest) -> tuple[str, ...]:
        return self._command(request, stream=True)

    def _command(self, request: RunRequest, *, stream: bool) -> tuple[str, ...]:
        if request.name:
            raise UnsupportedRequest(
                "provider 'gemini' does not support request fields: name"
            )

        _refuse_a_claude_only_effort("gemini", request)
        env_prefix = _codex_settings_env(request.settings, "gemini")
        assignment = _assignment("gemini", request)
        agent_sentence = ""
        if request.agent:
            agent_sentence, assignment = _codex_agent_context(
                request, assignment, "gemini"
            )

        argv = ["agy", "--mode", "accept-edits"]
        if stream:
            argv.extend(("--output-format", "stream-json"))
        if request.resume_session_id:
            argv.extend(("--conversation", request.resume_session_id))
        if assignment:
            argv.extend(("--model", assignment.model))
        effort = (
            request.effort.value
            if request.effort is not None
            else (assignment.reasoning_effort if assignment else None)
        )
        if effort:
            argv.extend(("--effort", effort))
        for directory in request.add_dirs:
            argv.extend(("--add-dir", directory))
        if request.skill_path is not None:
            skill_dir = str(request.skill_path.parent)
            if skill_dir not in request.add_dirs:
                argv.extend(("--add-dir", skill_dir))

        prompt = request.prompt
        if agent_sentence:
            prompt = f"{agent_sentence} {prompt}"
        if request.core_root is not None:
            prompt = task_context.gemini_bootstrap(
                request.core_root,
                prompt,
                assignment.model if assignment else None,
                effort,
            )
        argv.extend(("-p", prompt))
        return (*env_prefix, *argv)


def _environment_without(withhold: frozenset[str]) -> dict[str, str] | None:
    """The environment a child is started with: this process's own as it stands now, less every
    name in `withhold`. `None` when nothing is withheld, so `subprocess` inherits as it always
    has. Read at the call, so a variable `main` loaded from `.env` after import is covered."""
    if not withhold:
        return None
    return {name: value for name, value in os.environ.items() if name not in withhold}


class Subprocesses:
    def run(self, argv: Sequence[str], *, withhold: frozenset[str] = frozenset()) -> int:
        return subprocess.run(argv, check=False, env=_environment_without(withhold)).returncode

    def run_to_log(
        self, argv: Sequence[str], log_path: Path, *, withhold: frozenset[str] = frozenset()
    ) -> int:
        with log_path.open("xb") as log:
            return subprocess.run(
                argv,
                check=False,
                env=_environment_without(withhold),
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
            ).returncode

    def start_detached(
        self, argv: Sequence[str], log_path: Path, *, withhold: frozenset[str] = frozenset()
    ) -> int:
        """Start `argv` in a new session, its output to `log_path`, and return the pid — which
        is the exit-record wrapper's (`_wrap_for_exit_record`): it runs `argv` and then writes
        one record, so it lives exactly as long as `argv` does, and a signal to its process
        group reaches both."""
        with log_path.open("xb") as log:
            process = subprocess.Popen(
                _wrap_for_exit_record(tuple(argv)),
                env=_environment_without(withhold),
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True,
            )
        return process.pid


# Appends one JSON `kensai.exit` record to the log once `argv` exits, so a provider process that
# dies before emitting a single event of its own still leaves a terminal record for an inspector to
# read (`agent_turn.inspect_claude_log` / `agent_session.inspect_codex_log`). `argv` is passed to
# `sh` as positional parameters and expanded with `"$@"` — never interpolated into the script text
# — so there is no shell-quoting or injection risk regardless of what `argv` contains.
_EXIT_RECORD_SCRIPT = '"$@"; printf \'{"type":"kensai.exit","code":%d}\\n\' "$?"'


def _wrap_for_exit_record(argv: tuple[str, ...]) -> tuple[str, ...]:
    return ("/bin/sh", "-c", _EXIT_RECORD_SCRIPT, "sh", *argv)


class UnknownProvider(ValueError):
    pass


class LaunchFailed(RuntimeError):
    def __init__(self, provider: str, returncode: int) -> None:
        super().__init__(
            f"provider {provider!r} launch command exited {returncode}"
        )
        self.returncode = returncode


@dataclass(frozen=True)
class BackgroundRun:
    provider: str
    owner: BackgroundOwner
    log_path: Path
    pid: int | None = None
    session_id: str | None = None

    def as_dict(self) -> dict[str, str | int | None]:
        return {
            "provider": self.provider,
            "owner": self.owner,
            "pid": self.pid,
            "session_id": self.session_id,
            "log_path": str(self.log_path),
        }


_HF_ROUTER_URL = "https://router.huggingface.co"
_HF_TOKEN_KEY = "HF_TOKEN"
# Variables the hf layer hands the child, and the two top-level keys it owns. A caller's settings
# may set none of them: the layer decides endpoint, models and credential, so a collision is
# refused instead of silently resolved in either direction.
_HF_OWNED_ENV = frozenset(
    {
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_DEFAULT_OPUS_MODEL",
        "ANTHROPIC_DEFAULT_SONNET_MODEL",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL",
        "CLAUDE_CODE_SUBAGENT_MODEL",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_MODEL",
    }
)
_HF_OWNED_KEYS = frozenset({"model", "apiKeyHelper"})


class _RoutedClaudeCode:
    """Claude Code aimed at an endpoint of the provider's own, in the three `Shape`s.

    It builds its own command: a routed endpoint needs its own models in every slot and its own
    credential route, which a command built for Anthropic's own models has no place for. What
    differs between providers is the name in each refusal, the settings layer, and the check that
    the endpoint can be used at all; a subclass supplies those, and everything else is here.
    """

    provider: str

    def background_owner(self, request: RunRequest) -> BackgroundOwner:
        return "provider" if request.shape is Shape.BACKGROUND else "process"

    def command(self, request: RunRequest) -> tuple[str, ...]:
        self._refuse_unsupported_fields(request)
        assignment = self._main_assignment(request)
        self._refuse_a_turn_without_identity(request)
        caller_settings = self._caller_settings(request.settings)
        self._refuse_an_unusable_endpoint()

        layer = self._settings_layer(assignment)
        merged = json.dumps(_merge_settings_layer(caller_settings, layer))
        settings_argv: tuple[str, ...]
        if request.pin is None:
            settings_argv = ("--settings", merged)
        else:
            settings_argv = _pin_delivery(dataclasses.replace(request, settings=merged))
        return (
            *self._flags(request, assignment),
            *settings_argv,
            self._prompt_argument(request),
        )

    def background_command(self, request: RunRequest) -> tuple[str, ...]:
        if self.background_owner(request) == "provider":
            return self.command(request)
        return (*_env_prefix(_DETACHED_PRINT_ENV), *self.command(request))

    def _refuse_an_unusable_endpoint(self) -> None:
        raise NotImplementedError

    def _settings_layer(self, assignment: model_assignment.ModelAssignment | None) -> dict:
        raise NotImplementedError

    def _flags(
        self, request: RunRequest, assignment: model_assignment.ModelAssignment | None
    ) -> tuple[str, ...]:
        if request.shape is Shape.TURN:
            argv = ["claude", "--print", "--output-format", "stream-json", "--verbose"]
        elif request.shape is Shape.BACKGROUND:
            argv = ["claude", "--bg"]
        else:
            argv = ["claude", "-p"]
        if request.name:
            argv.extend(("--name", request.name))
        if request.agent:
            argv.extend(("--agent", request.agent))
        if request.resume_session_id:
            argv.extend(("--resume", request.resume_session_id))
        elif request.session_id:
            argv.extend(("--session-id", request.session_id))
        if assignment:
            argv.extend(("--model", assignment.model))
        if request.effort is not None:
            argv.extend(("--effort", request.effort.value))
        argv.extend(("--permission-mode", "auto"))
        # Nobody is present to answer a prompt in a detached print or turn run. `BACKGROUND` goes
        # without the flag: it is a `--print` flag, and a `--bg` run that passed it on 2026-09-25
        # still stopped on an `rm -rf` prompt.
        if request.shape is not Shape.BACKGROUND:
            argv.extend(("--permission-prompts", "none"))
        argv.extend(f"--add-dir={directory}" for directory in request.add_dirs)
        return tuple(argv)

    def _prompt_argument(self, request: RunRequest) -> str:
        level = request.effort.value if request.effort is not None else None
        return task_context.claude_bootstrap(request.prompt, level)

    def _refuse_unsupported_fields(self, request: RunRequest) -> None:
        """Every field is carried or named here, in `RunRequest`'s field order."""
        refused = []
        if request.core_root is not None:
            refused.append("core_root")
        if request.session_id:
            if request.shape is Shape.BACKGROUND:
                refused.append("session_id on background")
            elif request.resume_session_id:
                refused.append("session_id on resume")
        if request.instance_root is not None and request.pin is None:
            refused.append("instance_root without pin")
        if request.pin is not None and request.instance_root is None:
            refused.append("pin without instance_root")
        if request.skill_name:
            refused.append("skill_name")
        if request.skill_path is not None:
            refused.append("skill_path")
        if request.granted_skills and request.pin is None:
            refused.append("granted_skills without pin")
        if refused:
            raise UnsupportedRequest(
                f"provider {self.provider!r} does not support request fields: "
                f"{', '.join(refused)}"
            )

    def _main_assignment(
        self, request: RunRequest
    ) -> model_assignment.ModelAssignment | None:
        try:
            return _assignment(self.provider, request)
        except model_assignment.NoModelForTier as error:
            raise UnsupportedRequest(str(error)) from error

    def _refuse_a_turn_without_identity(self, request: RunRequest) -> None:
        if (
            request.shape is Shape.TURN
            and not request.session_id
            and not request.resume_session_id
        ):
            raise UnsupportedRequest(
                f"provider {self.provider!r} needs a session_id or resume_session_id for a turn"
            )

    def _caller_settings(self, settings: str | None) -> dict:
        """The caller's document, validated whole: an object, an `env` that is an object, and
        none of the names the provider's layer owns."""
        if not settings:
            return {}
        malformed = UnsupportedRequest(
            f"provider {self.provider!r} settings must be a JSON object whose env, when "
            "present, is an object"
        )
        try:
            document = json.loads(settings)
        except json.JSONDecodeError:
            raise malformed from None
        if not isinstance(document, dict) or not isinstance(document.get("env", {}), dict):
            raise malformed
        collisions = sorted(
            (_HF_OWNED_ENV & document.get("env", {}).keys()) | (_HF_OWNED_KEYS & document.keys())
        )
        if collisions:
            raise UnsupportedRequest(
                f"provider {self.provider!r} settings may not set: {', '.join(collisions)}"
            )
        return document

    def _slot_env(self, assignment: model_assignment.ModelAssignment | None) -> dict[str, str]:
        """The three model slots, and the subagent model: the run's own, else the sonnet slot."""
        slots = model_assignment.ASSIGNMENTS[self.provider]
        return {
            "ANTHROPIC_DEFAULT_OPUS_MODEL": slots["opus"].model,
            "ANTHROPIC_DEFAULT_SONNET_MODEL": slots["sonnet"].model,
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": slots["haiku"].model,
            "CLAUDE_CODE_SUBAGENT_MODEL": assignment.model if assignment else slots["sonnet"].model,
        }


class HfAdapter(_RoutedClaudeCode):
    """Claude Code aimed at Hugging Face's router, in the three `Shape`s.

    The router needs open models in every slot and a credential that never rides argv, env or a
    written file. The token is read from `token_source` only to prove it is there; Claude Code
    fetches it itself by running `apiKeyHelper` (`env_file.py <token_source> HF_TOKEN`).
    The token does not ride the inherited environment either: `withheld_environment` names
    `HF_TOKEN`, and the runner hands that to the process port, so the child starts without it
    whatever the launching environment held.
    """

    provider = "hf"
    withheld_environment = frozenset({_HF_TOKEN_KEY})

    def __init__(self, token_source: Path) -> None:
        self._token_source = token_source

    def _refuse_an_unusable_endpoint(self) -> None:
        try:
            token = env_file.value(self._token_source, _HF_TOKEN_KEY)
        except OSError:
            token = None
        if not token:
            raise UnsupportedRequest(
                f"provider 'hf' needs a non-empty {_HF_TOKEN_KEY} in {self._token_source}"
            )

    def _settings_layer(self, assignment: model_assignment.ModelAssignment | None) -> dict:
        helper = shlex.join(
            [
                sys.executable,
                str(Path(__file__).resolve().with_name("env_file.py")),
                str(self._token_source),
                _HF_TOKEN_KEY,
            ]
        )
        return {
            "env": {"ANTHROPIC_BASE_URL": _HF_ROUTER_URL, **self._slot_env(assignment)},
            "apiKeyHelper": helper,
        }


_OLLAMA_URL_KEY = "KENSAIAPP_OLLAMA_URL"
_OLLAMA_DEFAULT_URL = "http://localhost:11434"
_OLLAMA_PLACEHOLDER_TOKEN = "ollama"
_OLLAMA_REACH_TIMEOUT_SECONDS = 2.0


def _ollama_answers(
    address: str, timeout_seconds: float = _OLLAMA_REACH_TIMEOUT_SECONDS
) -> bool:
    """True when `GET <address>/api/version` answers 200 within the timeout. Any failure to
    answer, whatever its kind, reads as not answering; nothing escapes. No proxy is consulted:
    the server is on the owner's own machine."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f"{address.rstrip('/')}/api/version", timeout=timeout_seconds) as reply:
            return reply.status == 200
    except (OSError, ValueError, http.client.HTTPException):
        return False


class OllamaAdapter(_RoutedClaudeCode):
    """Claude Code aimed at the Ollama server on the owner's machine, in the three `Shape`s.

    The server takes the vendor's fixed placeholder credential, which is no secret, so the
    settings layer carries it as variables and there is no `apiKeyHelper`; nothing is withheld
    from the inherited environment. The address is read from `environ` when a command is built,
    and `reach(address)` says whether a server answers there: it is asked last, so every other
    refusal is raised first, and a refusal writes nothing.
    """

    provider = "ollama"
    withheld_environment: frozenset[str] = frozenset()

    def __init__(
        self, environ: Mapping[str, str], reach: Callable[[str], bool]
    ) -> None:
        self._environ = environ
        self._reach = reach

    def _address(self) -> str:
        return self._environ.get(_OLLAMA_URL_KEY) or _OLLAMA_DEFAULT_URL

    def _refuse_an_unusable_endpoint(self) -> None:
        address = self._address()
        if not self._reach(address):
            raise UnsupportedRequest(
                f"provider 'ollama' needs an Ollama server answering at {address}"
            )

    def _settings_layer(self, assignment: model_assignment.ModelAssignment | None) -> dict:
        return {
            "env": {
                "ANTHROPIC_BASE_URL": self._address(),
                "ANTHROPIC_AUTH_TOKEN": _OLLAMA_PLACEHOLDER_TOKEN,
                "ANTHROPIC_API_KEY": "",
                **self._slot_env(assignment),
            }
        }


ADAPTERS: dict[str, ProviderAdapter] = {
    "claude": ClaudeAdapter(),
    "codex": CodexAdapter(),
    "gemini": GeminiAdapter(),
    "hf": HfAdapter(Path.home() / ".env"),
    "ollama": OllamaAdapter(os.environ, _ollama_answers),
}


class AgentRunner:
    def __init__(
        self,
        adapters: dict[str, ProviderAdapter],
        processes: Processes,
    ) -> None:
        self._adapters = adapters
        self._processes = processes

    def command(self, provider: str, request: RunRequest) -> tuple[str, ...]:
        return self._adapter(provider).command(request)

    def background_command(
        self, provider: str, request: RunRequest
    ) -> tuple[str, ...]:
        return self._adapter(provider).background_command(request)

    def _adapter(self, provider: str) -> ProviderAdapter:
        try:
            return self._adapters[provider]
        except KeyError as error:
            available = ", ".join(sorted(self._adapters)) or "none"
            raise UnknownProvider(
                f"unknown provider {provider!r}; available providers: {available}"
            ) from error

    @staticmethod
    def _withhold_keyword(adapter: ProviderAdapter) -> dict[str, frozenset[str]]:
        """`withhold=` for the port when the adapter names variables its child must not inherit,
        and nothing otherwise — so an adapter that names none reaches the port by today's call."""
        withheld = getattr(adapter, "withheld_environment", frozenset())
        return {"withhold": withheld} if withheld else {}

    def run(self, provider: str, request: RunRequest) -> int:
        adapter = self._adapter(provider)
        return self._processes.run(
            adapter.command(request), **self._withhold_keyword(adapter)
        )

    def background(
        self,
        provider: str,
        request: RunRequest,
        log_path: Path,
    ) -> BackgroundRun:
        adapter = self._adapter(provider)
        command = adapter.background_command(request)
        withhold = self._withhold_keyword(adapter)
        if adapter.background_owner(request) == "provider":
            returncode = self._processes.run_to_log(command, log_path, **withhold)
            if returncode != 0:
                raise LaunchFailed(provider, returncode)
            return BackgroundRun(provider, "provider", log_path)

        pid = self._processes.start_detached(command, log_path, **withhold)
        return BackgroundRun(
            provider, "process", log_path, pid=pid, session_id=request.session_id
        )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Run an unattended agent through a provider adapter."
    )
    result.add_argument("--provider", required=True)
    result.add_argument("--prompt", required=True)
    result.add_argument("--agent")
    result.add_argument("--name", help="logical provider session name")
    result.add_argument(
        "--resume-session",
        dest="resume_session_id",
        help="continue an existing provider conversation by its session ID",
    )
    model = result.add_mutually_exclusive_group()
    model.add_argument(
        "--model",
        help="explicit provider model ID; bypasses Kensaiapp tier assignment",
    )
    model.add_argument(
        "--model-tier",
        choices=model_assignment.TIERS,
        help="stable Kensaiapp workload tier resolved for the provider",
    )
    result.add_argument("--add-dir", action="append", default=[], dest="add_dirs")
    result.add_argument("--settings")
    result.add_argument("--skill-name")
    result.add_argument("--skill-path", type=Path)
    result.add_argument(
        "--grant-skill",
        action="append",
        default=[],
        dest="granted_skills",
        help="a skill this pinned Claude run is granted, with the skill groups it reaches; "
        "repeatable, and with none the plugin lists only the flat and the instance's own skills",
    )
    result.add_argument(
        "--core-dir",
        type=Path,
        help="resolved Kensaiapp core root whose task context Codex receives",
    )
    result.add_argument(
        "--shape",
        choices=[shape.value for shape in Shape],
        default=Shape.BACKGROUND.value,
        help="which claude command shape to build",
    )
    result.add_argument(
        "--session-id",
        help="this turn's own identity, used to start a Shape.TURN run",
    )
    result.add_argument(
        "--instance-root",
        type=Path,
        help="the instance this run's ownership is judged against",
    )
    result.add_argument(
        "--effort",
        choices=[effort.value for effort in Effort],
        help="reasoning-effort level; Claude and Gemini pass it as --effort, "
        "Codex as model_reasoning_effort, over the tier's own",
    )
    result.add_argument(
        "--pin",
        help="pin root to deliver from, or 'auto' to read the inherited KENSAIAPP_PIN",
    )
    result.add_argument(
        "--background",
        action="store_true",
        help="return after launch; requires --log",
    )
    result.add_argument(
        "--log",
        type=Path,
        help="new file that receives provider output for a background run",
    )
    result.add_argument(
        "--dry-run",
        action="store_true",
        help="print the provider command without executing it",
    )
    result.add_argument(
        "--print-argv",
        action="store_true",
        help="write the argv NUL-separated to stdout and launch nothing",
    )
    return result


_SESSION_MINTING_PROVIDERS = ("claude", "hf", "ollama")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        load_dotenv()
        load_dotenv(Path.home() / ".env")
    except ImportError:
        pass

    argument_parser = parser()
    args = argument_parser.parse_args(argv)
    if args.background and args.log is None:
        argument_parser.error("--background requires --log")
    if args.log is not None and not args.background:
        argument_parser.error("--log requires --background")

    resolved_pin = None
    if args.pin:
        try:
            if args.pin == "auto":
                resolved_pin = pin.inherited(os.environ)
            else:
                resolved_pin = pin.inherited({"KENSAIAPP_PIN": args.pin})
        except pin.PinMissing as error:
            print(f"agent-run: {error}", file=sys.stderr)
            return 3

    session_id = args.session_id
    # A turn that starts a conversation names it up front (`--session-id`), so whoever launched
    # it knows the conversation before its first event. Minted here when the caller did not.
    # `hf` and `ollama` are the Claude run aimed at another endpoint, so it is minted the same
    # way; codex and gemini name their own conversation and are left alone.
    if (
        args.provider in _SESSION_MINTING_PROVIDERS
        and Shape(args.shape) is Shape.TURN
        and not args.resume_session_id
        and not session_id
    ):
        session_id = str(uuid.uuid4())

    request = RunRequest(
        prompt=args.prompt,
        skill_name=args.skill_name,
        skill_path=args.skill_path,
        agent=args.agent,
        name=args.name,
        resume_session_id=args.resume_session_id,
        model=args.model,
        model_tier=args.model_tier,
        add_dirs=tuple(args.add_dirs),
        settings=args.settings,
        core_root=args.core_dir,
        shape=Shape(args.shape),
        session_id=session_id,
        instance_root=args.instance_root,
        pin=resolved_pin,
        effort=Effort(args.effort) if args.effort else None,
        granted_skills=tuple(args.granted_skills),
    )
    runner = AgentRunner(ADAPTERS, Subprocesses())
    try:
        command = (
            runner.background_command(args.provider, request)
            if args.background
            else runner.command(args.provider, request)
        )
    except (
        UnknownProvider,
        UnsupportedRequest,
        model_assignment.UnknownProvider,
        model_assignment.UnknownTier,
    ) as error:
        print(f"agent-run: {error}", file=sys.stderr)
        return 2

    if args.print_argv:
        for arg in command:
            sys.stdout.buffer.write(arg.encode("utf-8"))
            sys.stdout.buffer.write(b"\0")
        return 0
    if args.dry_run:
        print(shlex.join(command))
        return 0
    if args.background:
        try:
            background_run = runner.background(args.provider, request, args.log)
        except LaunchFailed as error:
            print(f"agent-run: {error}", file=sys.stderr)
            return error.returncode
        print(json.dumps(background_run.as_dict(), sort_keys=True))
        return 0
    return runner.run(args.provider, request)


if __name__ == "__main__":
    raise SystemExit(main())
