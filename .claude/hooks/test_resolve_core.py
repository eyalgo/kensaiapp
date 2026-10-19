"""`resolve_core.py`'s own pin awareness — `<CORE>` under a pin is the pin's `core/`.

Complements `.claude/tests/test_resolve_core_githooks.py` (the wiring guards, unaffected here —
none of that file's fixtures carries a `pin.json`, so this change is silent on every one of them).
Runs the hook as a subprocess, driving a *copy* placed at the tested location so the running
process's own `os.path.realpath(__file__)` answers from there — matching every sibling hook test's
own convention (never import it; `test_context_cap.py`, `test_resolve_core_githooks.py`).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

_HOOKS = Path(__file__).resolve().parent
_HOOK = _HOOKS / "resolve_core.py"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)


def _hooks_path(repo: Path) -> str | None:
    p = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"], cwd=repo, capture_output=True, text=True
    )
    return p.stdout.strip() if p.returncode == 0 else None


def _run(hook: Path, *, project_dir: Path, env_file: Path | None = None) -> tuple[str, str | None]:
    """Drive the hook the way a session does; return (additionalContext, env-file text)."""
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    if env_file is not None:
        env["CLAUDE_ENV_FILE"] = str(env_file)
    else:
        env.pop("CLAUDE_ENV_FILE", None)
    done = subprocess.run(
        [sys.executable, str(hook)],
        input='{"hook_event_name": "SessionStart"}',
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    context = json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]
    text = env_file.read_text() if env_file is not None and env_file.exists() else None
    return context, text


def _pin_shaped(tmp_path: Path, *, manifest: bool) -> Path:
    """`<pin>/.claude/hooks/resolve_core.py` (a real copy) + `<pin>/core/`.

    `manifest` controls whether `<pin>/pin.json` is written.
    """
    pin = tmp_path / "pin"
    hooks_dir = pin / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True)
    shutil.copy2(_HOOK, hooks_dir / "resolve_core.py")
    (pin / "core").mkdir(parents=True)
    if manifest:
        (pin / "pin.json").write_text('{"id": "test-pin"}')
    return pin


def _instance_with_env(tmp_path: Path, core_value: str) -> Path:
    instance = tmp_path / "instance"
    instance.mkdir()
    (instance / ".env").write_text(f"CORE={core_value}\n")
    return instance


def test_inside_a_pin_core_is_the_pins(tmp_path):
    pin = _pin_shaped(tmp_path, manifest=True)
    instance = _instance_with_env(tmp_path, "/somewhere/else/core")
    env_file = tmp_path / "env_out.sh"

    context, env_text = _run(
        pin / ".claude" / "hooks" / "resolve_core.py", project_dir=instance, env_file=env_file
    )

    pin_core = str(pin / "core")
    assert pin_core in context
    assert "/somewhere/else/core" not in context
    assert env_text is not None and pin_core in env_text


def test_inside_a_pin_hooks_path_is_never_wired(tmp_path):
    """The instance's own core carries a real githooks/ (wiring would fire without the pin check).

    Under a pin, `_resolve` never reaches for the instance's own `core/` at all, and
    `_wire_githooks` refuses before it even looks — the pin's hooks reach git through the
    environment (CP-112), not through `core.hooksPath`.
    """
    pin = _pin_shaped(tmp_path, manifest=True)
    instance = tmp_path / "instance"
    (instance / "core" / "githooks").mkdir(parents=True)
    (instance / "core" / "githooks" / "commit-msg").write_text("#!/bin/sh\nexit 0\n")
    _git(instance.parent, "init", "-q", str(instance))
    _git(instance, "config", "user.email", "t@example.com")
    _git(instance, "config", "user.name", "t")
    assert _hooks_path(instance) is None, "precondition: a fresh repo carries no hooksPath"

    _run(pin / ".claude" / "hooks" / "resolve_core.py", project_dir=instance)

    assert _hooks_path(instance) is None, "the pin's hooks reach git through the environment"


def test_outside_a_pin_env_rule_is_unchanged(tmp_path):
    instance = _instance_with_env(tmp_path, "/somewhere/else/core")

    context, _ = _run(_HOOK, project_dir=instance)

    assert "/somewhere/else/core" in context


def test_outside_a_pin_default_is_unchanged(tmp_path):
    instance = tmp_path / "instance"
    instance.mkdir()

    context, _ = _run(_HOOK, project_dir=instance)

    assert str(instance / "core") in context


def test_a_directory_without_a_manifest_is_not_a_pin(tmp_path):
    pin_shaped = _pin_shaped(tmp_path, manifest=False)
    instance = _instance_with_env(tmp_path, "/somewhere/else/core")

    context, _ = _run(
        pin_shaped / ".claude" / "hooks" / "resolve_core.py", project_dir=instance
    )

    assert "/somewhere/else/core" in context
    assert str(pin_shaped / "core") not in context
