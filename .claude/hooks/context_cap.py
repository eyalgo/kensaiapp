#!/usr/bin/env python3
"""PostToolUse Bash hook — tell a developer run to pause once its context is over the cap.

WHY THIS EXISTS
    A developer run that reads a large `tl_instruction.md` and works a dozen tasks carries a
    context that grows until the run degrades or is cut off. The chain sets
    `KENSAIAPP_CONTEXT_CAP` for the implementation step only; this hook reads the run's own
    transcript, and once the current context is over that cap it injects one instruction: finish
    the task in progress through its last commit, make the pause commit, and end. The chain reads
    that commit as "relaunch after task N" and starts a fresh developer.

    It matches `Bash` and nothing else. The developer commits through Bash, and a task boundary
    is a commit, so a Bash call is the one event that lands at a boundary the run can name.

    **Silent unless the cap is set.** Every other session — an interactive one, another step of
    the chain — has no `KENSAIAPP_CONTEXT_CAP`, and a hook that spoke there would be noise on
    every Bash call in the fleet. The stdin is parsed and the cap validated before the telemetry
    gateway is even loaded.

    **The gauge is read through the telemetry gateway, found through `resolve_core._resolve()`,
    never a path relative to this file.** This hook runs in satellites, which hold no `core/` of
    their own; the same `.env`-then-`core/` resolution the session start uses is the only route
    that reaches `<core>/tools/telemetry_gateway.py` from there. The gateway owns the gauge; this
    file adds no calculation of its own and keeps no fallback for it.

    **The telemetry package is optional, and this hook retries once for it.** Where the Python
    running the hook cannot import the package, the hook runs itself once more under
    `~/.kensaiapp/venv/bin/python` with the same stdin and environment, and forwards that run's
    output when it succeeds. A run already inside that venv does not retry. Where no interpreter
    there can supply the package, a set cap prints one line on stdout saying the cap needs the
    telemetry package and this run is not capped, and the hook exits 0.

    **Fails open on every other path** — any error is silence and exit 0, as
    `written_forward_guard.py` does: a hook that raises must not break a session.
"""

from __future__ import annotations

import importlib
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

__version__ = "1.1.0"

CAP_VARIABLE = "KENSAIAPP_CONTEXT_CAP"
PAUSE_SUBJECT = "developer: <key> — implementation paused after task <N>"
VENV_RELATIVE = Path(".kensaiapp") / "venv"

_MESSAGE = (
    "Context is {size} tokens, over the {cap}-token cap this run was given. Finish the task in "
    "progress through its last commit, then make the pause commit — subject "
    "`" + PAUSE_SUBJECT + "`, N being the last task you committed — on the instance worktree, "
    "and end the run. A fresh developer resumes from the next task."
)

# Runs a child process: (argv, stdin bytes, environment) → (exit status, stdout text).
ChildRunner = Callable[[list[str], bytes, Mapping[str, str]], tuple[int, str]]
GatewayLoader = Callable[[], ModuleType | Any]


def _cap_from(raw: str) -> int | None:
    """`raw` as a positive integer, or `None` when it is unset or anything else."""
    raw = raw.strip()
    if not re.fullmatch(r"[0-9]+", raw) or int(raw) == 0:
        return None
    return int(raw)


def _load_gateway() -> ModuleType:
    """The wiring: import the telemetry gateway from the resolved core. Importing it builds
    nothing and needs no package. Only reached once a cap is set."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import resolve_core

    core = resolve_core._resolve(resolve_core._project_dir())
    tools = os.path.join(core, "tools")
    sys.path.insert(0, tools)
    return importlib.import_module("telemetry_gateway")


def _run_child(argv: list[str], stdin: bytes, environ: Mapping[str, str]) -> tuple[int, str]:
    """Run `argv` with `stdin` byte for byte, its streams captured; return its status and stdout."""
    done = subprocess.run(
        argv, input=stdin, capture_output=True, env=dict(environ), check=False
    )
    return done.returncode, done.stdout.decode("utf-8", errors="replace")


def _venv_python(home: Path) -> Path | None:
    """The package venv's interpreter under `home`, or `None` when it is absent or not runnable."""
    candidate = home / VENV_RELATIVE / "bin" / "python"
    return candidate if os.access(candidate, os.X_OK) and candidate.is_file() else None


def _is_inside_venv(prefix: str, home: Path) -> bool:
    """Whether the running interpreter's prefix is the package venv itself. The prefix is the
    identity: a venv's interpreter may be a link to the same binary as another Python's."""
    return os.path.realpath(prefix) == os.path.realpath(home / VENV_RELATIVE)


def _handle(payload: Any, cap: int, telemetry: Any) -> None:
    """Say so, once, when the payload's transcript is over `cap`. Silent otherwise."""
    size = telemetry.current_context(Path(payload["transcript_path"]), telemetry.files)
    if size is None or size <= cap:
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": _MESSAGE.format(size=size, cap=cap),
        }
    }))


def _without_the_package(
    gateway: Any,
    stdin: bytes,
    environ: Mapping[str, str],
    *,
    run_child: ChildRunner,
    prefix: str,
    home: Path,
) -> None:
    """The Python running this hook cannot supply the telemetry package: try the venv once, and
    otherwise say the cap does not cap. A failure of the retry itself is silence."""
    interpreter = _venv_python(home)
    if interpreter is None or _is_inside_venv(prefix, home):
        print(gateway.CONTEXT_UNAVAILABLE)
        return
    status, stdout = run_child(
        [str(interpreter), str(Path(os.path.abspath(__file__)))], stdin, environ
    )
    if status == 0:
        sys.stdout.write(stdout)


def run(
    stdin: bytes,
    environ: Mapping[str, str],
    *,
    load_gateway: GatewayLoader = _load_gateway,
    run_child: ChildRunner = _run_child,
    prefix: str = sys.prefix,
    home: Path | None = None,
) -> None:
    """The hook's whole behaviour, with every collaborator given. Raises whatever fails;
    `main` turns every failure into silence."""
    try:
        payload = json.loads(stdin)
    except ValueError:
        return  # unparseable → silence
    cap = _cap_from(environ.get(CAP_VARIABLE, ""))
    if cap is None:
        return

    gateway = load_gateway()
    try:
        telemetry = gateway.build_telemetry()
    except gateway.TelemetryUnavailable:
        _without_the_package(
            gateway, stdin, environ,
            run_child=run_child, prefix=prefix, home=home or Path(os.path.expanduser("~")),
        )
        return
    _handle(payload, cap, telemetry)


def main(stdin: bytes | None = None, environ: Mapping[str, str] | None = None, **wiring) -> None:
    """Best-effort by contract: any failure is silence and exit 0, because a hook that raises
    must not break the session it watches. This is also the composition root — the one place
    the real stdin and environment are read; a test passes its own and any collaborator `run`
    takes."""
    try:
        run(
            sys.stdin.buffer.read() if stdin is None else stdin,
            os.environ if environ is None else environ,
            **wiring,
        )
    except Exception:
        return  # fail-open — a hook that raises must not break a session


if __name__ == "__main__":
    main()
