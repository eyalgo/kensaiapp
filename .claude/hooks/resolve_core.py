#!/usr/bin/env python3
"""SessionStart hook — resolve `<CORE>` once, inject it into session context.

Resolution (single source of truth for the whole session):
  0. When this file's own copy sits inside a pin — `<pin root>/pin.json`
     exists two directories above `<pin root>/.claude/hooks/` — `<CORE>` is
     that pin's `core/`, whatever the project dir's own `.env` says. A pinned
     run's `<CORE>` is fixed at the pin's own make time, not re-read from an
     instance that may have moved on since.
  1. Else read `CORE=` from the instance's untracked `.env` if present.
  2. Else default to the repo-relative `core/` — so a fresh clone is
     ready-to-run with no `.env` (clone-and-run holds).
  Relative values resolve against the project dir; absolute values (e.g. a
  centralized core set by `kensaiapp-set-core`) are used as-is.

Output (two channels):
  - `hookSpecificOutput.additionalContext` — the resolved path, injected into
    the model's context. Skills/loaders that reference `<CORE>` substitute it.
  - `$CLAUDE_ENV_FILE` (if set) — `export CORE=<abs>` for subsequent Bash.

Also wires `core.hooksPath` to `<resolved-core>/githooks` when it is unset, so
the git-native commit-msg trailer check is not inert in a fresh clone. That
config is local and untracked, so git never carries it across a clone; nothing
else sets it, and until it is set a commit with no trailers is accepted in
silence. Resolution owns this because the target *is* the resolved core.
Under a pin, this wiring is skipped entirely — the pin's hooks reach git
through the environment (CP-112), not through `core.hooksPath`.

Fail-open: any error still emits the default so the session is never broken.
Stdlib-only imports.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

__version__ = "1.1.0"

DEFAULT_CORE = "core/"
SENTINEL = "KENSAIAPP_CORE_RESOLVED"  # probe marker — lets a test confirm propagation


def _project_dir() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _own_pin_root() -> str | None:
    """The pin this file's own running copy sits in, or `None` outside a pin.

    `<pin root>/.claude/hooks/resolve_core.py` — the pin root is two directories above this
    file's own directory. Stdlib-only, and deliberately does not import `pin.py`: a hook runs
    with no `core/` on its path, pinned or not, so it recognizes a pin the same way it recognizes
    everything else here, by reading the filesystem for itself. A directory shaped like a pin but
    missing `pin.json` is not one — `pin.py`'s own `of_core`/`inherited` treat the manifest as
    what makes a pin a pin, and this file holds to the same rule without sharing the code.
    """
    hooks_dir = os.path.dirname(os.path.realpath(__file__))
    pin_root = os.path.dirname(os.path.dirname(hooks_dir))
    if os.path.isfile(os.path.join(pin_root, "pin.json")):
        return pin_root
    return None


def _read_core_from_env(env_path: str) -> str | None:
    try:
        with open(env_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                if key.strip() == "CORE":
                    return value.strip().strip('"').strip("'")
    except OSError:
        return None
    return None


def _resolve(project_dir: str) -> str:
    pin_root = _own_pin_root()
    if pin_root is not None:
        return os.path.join(pin_root, "core")
    raw = _read_core_from_env(os.path.join(project_dir, ".env")) or DEFAULT_CORE
    if os.path.isabs(raw):
        return os.path.normpath(raw)
    return os.path.normpath(os.path.join(project_dir, raw))


def _git(args: list[str], cwd: str) -> tuple[int, str]:
    """Run git, return (returncode, stdout). Never raises."""
    try:
        p = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=10,
        )
        return p.returncode, p.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return 1, ""


def _wire_githooks(project_dir: str, core_abs: str) -> str | None:
    """Point `core.hooksPath` at `<core>/githooks` when nothing else has.

    Five guards, each preventing a silent breakage rather than a loud one:
      0. under a pin, never — the pin's hooks reach git through the environment
         (`core.hooksPath` set via `GIT_CONFIG_*`, CP-112), and this file's own
         `core.hooksPath` write would repoint the *instance's* git config at a
         pin that can be gone by the next launch;
      1. the githooks dir must exist — never point at nothing;
      2. main working tree only — linked worktrees SHARE one `.git/config`, and
         a worktree resolves core to its own copy, so writing from inside one
         would repoint every tree at a path that dies with that worktree;
      3. never overwrite a value someone already chose;
      4. never shadow active hooks in `.git/hooks/` — `core.hooksPath` makes git
         ignore that directory entirely, so a user's own hooks would just stop.

    Returns a one-line note when it wires (the session should see what changed),
    else None. Never raises: a wiring failure must not break the session.
    """
    try:
        if _own_pin_root() is not None:
            return None  # guard 0

        githooks = os.path.join(core_abs, "githooks")
        if not os.path.isdir(githooks):
            return None

        rc_dir, git_dir = _git(["rev-parse", "--git-dir"], project_dir)
        rc_common, common_dir = _git(["rev-parse", "--git-common-dir"], project_dir)
        if rc_dir or rc_common:
            return None  # not a git repo, or git unavailable
        abs_git = os.path.realpath(os.path.join(project_dir, git_dir))
        abs_common = os.path.realpath(os.path.join(project_dir, common_dir))
        if abs_git != abs_common:
            return None  # linked worktree — see guard 2

        rc_have, have = _git(["config", "--get", "core.hooksPath"], project_dir)
        if rc_have == 0 and have:
            return None  # already chosen — see guard 3

        hooks_dir = os.path.join(abs_common, "hooks")
        if os.path.isdir(hooks_dir):
            active = [n for n in os.listdir(hooks_dir) if not n.endswith(".sample")]
            if active:
                return None  # see guard 4

        rc_set, _ = _git(["config", "core.hooksPath", githooks], project_dir)
        if rc_set:
            return None
        return (
            f"Wired `core.hooksPath` -> `{githooks}`. It was unset, which left the "
            "git-native commit-msg trailer check inert — a commit with no `Role:` "
            "or `Surface:` would have been accepted silently. This is local, "
            "untracked git config, so every fresh clone starts without it."
        )
    except Exception:  # noqa: BLE001 — fail-open by contract
        return None


def _emit_env_file(core_abs: str) -> None:
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if not env_file:
        return
    try:
        with open(env_file, "a", encoding="utf-8") as fh:
            fh.write(f"export CORE='{core_abs}'\n")
    except OSError:
        pass


def main() -> int:
    # Resolution does not depend on the payload (malformed input still resolves
    # the default), but we reflect the incoming event name so one script can
    # serve both SessionStart and SubagentStart.
    event = "SessionStart"
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if isinstance(payload, dict):
            event = payload.get("hook_event_name") or event
    except (ValueError, TypeError):
        pass

    project_dir = _project_dir()
    core_abs = _resolve(project_dir)
    _emit_env_file(core_abs)

    context = (
        f"CORE resolution ({SENTINEL}): `<CORE>` = `{core_abs}`.\n"
        "This is the foundation store the skills and role loaders resolve "
        "`<CORE>` to — doctrine (governance/flow/engineering) plus the "
        "cross-role + pipeline contracts and setup templates. Wherever a "
        "skill or loader references `<CORE>/<subpath>`, substitute this path."
    )

    wired = _wire_githooks(project_dir, core_abs)
    if wired:
        context += f"\n\n{wired}"
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": context,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
