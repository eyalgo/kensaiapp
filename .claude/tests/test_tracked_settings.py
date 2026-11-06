"""The tracked `.claude/settings.json` is the host's hook wiring and nothing else.

Permissions and the `worktree` setting are the machine owner's own and live in
`.claude/settings.local.json`; every pinned launch carries `worktree.bgIsolation` itself.
"""

import json
from pathlib import Path

TRACKED_SETTINGS = Path(__file__).resolve().parents[1] / "settings.json"


def test_the_tracked_settings_hold_only_the_hook_wiring():
    assert set(json.loads(TRACKED_SETTINGS.read_text())) == {"hooks"}


RUNNER = '"${CLAUDE_PROJECT_DIR}/core/tools/locked_python.sh"'
HOOKS_DIR = "${CLAUDE_PROJECT_DIR}/.claude/hooks"
HOOKS_ON_DISK = TRACKED_SETTINGS.parent / "hooks"

# (event, matcher, scripts in order) — the wiring `main` carried before the runner replaced
# `python3`; nothing about which script runs where moves.
EXPECTED_WIRING = [
    (
        "SessionStart",
        None,
        ["resolve_core.py", "task_map_salience.py", "manifest_salience.py",
         "standing_rules_salience.py"],
    ),
    (
        "SubagentStart",
        None,
        ["resolve_core.py", "task_map_salience.py", "manifest_salience.py",
         "standing_rules_salience.py"],
    ),
    ("SubagentStop", "delegate", ["subagent_stop_notify.py"]),
    ("PreToolUse", "Bash", ["development-bash-approve.py"]),
    ("PreToolUse", "Edit|Write", ["written_forward_guard.py"]),
    ("PreToolUse", "Agent", ["brief_anchor_guard.py"]),
    ("PreToolUse", "*", ["read_first_guard.py"]),
    ("PostToolUse", "Bash", ["context_cap.py"]),
    ("UserPromptSubmit", None, ["permission_mode_reminder.py"]),
]


def _entries() -> list[tuple[str, str | None, list[str]]]:
    hooks = json.loads(TRACKED_SETTINGS.read_text())["hooks"]
    return [
        (event, entry.get("matcher"), [hook["command"] for hook in entry["hooks"]])
        for event, entries in hooks.items()
        for entry in entries
    ]


def _all_commands() -> list[str]:
    return [command for _, _, commands in _entries() for command in commands]


def test_every_hook_command_runs_through_the_locked_python_runner():
    commands = _all_commands()

    assert commands
    for command in commands:
        prefix = f'{RUNNER} "{HOOKS_DIR}/'
        assert command.startswith(prefix) and command.endswith('"'), command
        script = command[len(prefix):-1]
        assert (HOOKS_ON_DISK / script).is_file(), command


def test_no_hook_command_starts_with_python3():
    assert [c for c in _all_commands() if c.startswith("python3 ")] == []


def test_the_wiring_keeps_its_fifteen_commands():
    assert len(_all_commands()) == 15
    wired = [
        (event, matcher, [c.rsplit("/", 1)[1].rstrip('"') for c in commands])
        for event, matcher, commands in _entries()
    ]
    assert wired == EXPECTED_WIRING
