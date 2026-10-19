#!/usr/bin/env python3
"""apply_telemetry_env.py — merges (or removes) the telemetry `env` entry into a Claude Code
settings file, so a session started by hand exports the same telemetry a launcher already hands
its spawn as `--settings`.

WHY THIS EXISTS
    `instrument_run.sh` reaches every launcher-started run, but nothing reaches a session started
    by hand, its in-process agents, or a `--bg` it starts itself — none of those pass through a
    launcher's own `--settings` hand-off. The switch for them is a one-time entry in the user
    settings file, applied once per machine, rather than a mechanism that runs on every session.
    This is the command that does the merge, so nobody edits that JSON by hand.

    The entry itself is never rebuilt here — `instrument_run.sh`'s own `instrument_run_user_entry`
    is the one place the five keys and their values are built. `run` is given a runner that reaches
    it; `library_runner` is the concrete one, and only `main` builds it.

WHAT IT WILL NOT DO
    It never overwrites a value you set yourself for one of the five keys — it names the key and
    stops, unless you pass `--replace`. `--remove` deletes only the values this command would
    write, and without a published endpoint to compare against it stops, unless you pass `--force`.
    A library that fails is reported as a failure, never as a machine with no receiver.

    Per `core/doctrine/setup/kensaiapp_structure.md` § *No tool may require machine state to
    exist* — a machine with no published telemetry endpoint runs this command and gets nothing
    written, not a POST at a closed port.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import NamedTuple

__version__ = "1.0.0"

_INSTRUMENT_RUN_LIB = Path(__file__).resolve().parent / "instrument_run.sh"

_TELEMETRY_KEYS = (
    "CLAUDE_CODE_ENABLE_TELEMETRY",
    "OTEL_METRICS_EXPORTER",
    "OTEL_LOGS_EXPORTER",
    "OTEL_EXPORTER_OTLP_PROTOCOL",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
)

# A non-interactive bash sources the file BASH_ENV names (and sh, ENV) before running anything, so
# an inherited one could print into the library's answer or change what it does.
_SHELL_STARTUP_VARIABLES = ("BASH_ENV", "ENV")


class LibraryAnswer(NamedTuple):
    returncode: int
    stdout: str
    stderr: str


class LibraryFailed(Exception):
    """The library answered with something that is neither an entry nor "no receiver"."""


# Given the endpoint-file override (or None for the library's own default), returns what
# `instrument_run_user_entry` answered.
LibraryRunner = Callable[[Path | None], LibraryAnswer]


def library_runner(lib: Path, environ: Mapping[str, str]) -> LibraryRunner:
    """The concrete runner: sources `lib` in a bash subprocess under `environ`, less the shell's
    startup-file variables, and calls `instrument_run_user_entry`. `None` passes the library's own
    default through untouched — that default is resolved exactly once, inside `instrument_run.sh`.
    """

    def run(endpoint_file: Path | None) -> LibraryAnswer:
        env = {name: value for name, value in environ.items() if name not in _SHELL_STARTUP_VARIABLES}
        if endpoint_file is not None:
            env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
        try:
            result = subprocess.run(
                ["bash", "-c", f'source "{lib}" && instrument_run_user_entry'],
                capture_output=True,
                text=True,
                env=env,
            )
        except OSError as exc:
            return LibraryAnswer(127, "", str(exc))
        return LibraryAnswer(result.returncode, result.stdout, result.stderr)

    return run


def user_entry(endpoint_file: Path | None, run_library: LibraryRunner) -> dict[str, str] | None:
    """The entry the library built, or `None` when it answered the way it says "no receiver" —
    nothing printed, nothing on stderr, exit 0. Anything else raises `LibraryFailed`. Never rebuilds
    the variable set itself.
    """
    answer = run_library(endpoint_file)
    if answer.returncode != 0 or answer.stderr.strip():
        raise LibraryFailed(answer.stderr.strip() or f"exit status {answer.returncode}")
    output = answer.stdout.strip()
    if not output:
        return None
    try:
        entry = json.loads(output)
    except json.JSONDecodeError:
        raise LibraryFailed("its answer was not JSON") from None
    if not isinstance(entry, dict):
        raise LibraryFailed("its answer was not a JSON object")
    return entry


def merge_entry(settings: dict, entry: dict[str, str]) -> dict:
    """Merges `entry` into `settings["env"]`, creating `env` if absent. Every other top-level
    key and every other `env` key is left exactly as it was.
    """
    merged = dict(settings)
    merged_env = dict(merged.get("env") or {})
    merged_env.update(entry)
    merged["env"] = merged_env
    return merged


def conflicting_keys(env: Mapping[str, str], entry: Mapping[str, str]) -> list[str]:
    """The keys `env` already sets to a value other than the one `entry` would write."""
    return [key for key in entry if key in env and env[key] != entry[key]]


def remove_keys(settings: dict, keys: list[str]) -> dict:
    """Deletes `keys` from `settings["env"]`; `env` is dropped entirely once nothing remains in it."""
    updated = dict(settings)
    env = {name: value for name, value in (updated.get("env") or {}).items() if name not in keys}
    if env:
        updated["env"] = env
    else:
        updated.pop("env", None)
    return updated


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--settings-file",
        type=Path,
        required=True,
        help="the Claude Code settings.json to merge the telemetry entry into (or remove it from)",
    )
    parser.add_argument(
        "--endpoint-file",
        type=Path,
        default=None,
        help="override for the published-endpoint file instrument_run.sh reads; unset uses "
        "that library's own default",
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="delete the telemetry keys this command writes instead of merging them in",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="with a merge: overwrite a value you already set for one of the five keys",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="with --remove: delete the five keys whatever their values, even with no published endpoint",
    )
    return parser


def _err(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def run(argv: list[str], *, run_library: LibraryRunner) -> int:
    args = _build_parser().parse_args(argv)
    settings_file: Path = args.settings_file

    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return _err(f"{settings_file} is not valid JSON ({exc}); nothing written")
        if not isinstance(settings, dict):
            return _err(f"{settings_file} is not a JSON object; nothing written")
        if not isinstance(settings.get("env") or {}, dict):
            return _err(f"{settings_file} has an env that is not a JSON object; nothing written")
    else:
        settings = {}
    env = settings.get("env") or {}

    try:
        if args.remove:
            present = [key for key in _TELEMETRY_KEYS if key in env]
            if not present:
                print("no telemetry keys to remove — nothing written")
                return 0
            if args.force:
                doomed, left = present, []
            else:
                entry = user_entry(args.endpoint_file, run_library)
                if entry is None:
                    return _err(
                        "no published telemetry endpoint — cannot tell this command's entry from values "
                        "you set yourself; nothing written. Pass --force to delete the five keys anyway."
                    )
                doomed = [key for key in present if env[key] == entry.get(key)]
                left = [key for key in present if key not in doomed]
            updated = remove_keys(settings, doomed)
        else:
            entry = user_entry(args.endpoint_file, run_library)
            if entry is None:
                where = f" at {args.endpoint_file}" if args.endpoint_file is not None else ""
                print(f"no published telemetry endpoint{where} — machine has no receiver, nothing written")
                return 0
            conflicts = conflicting_keys(env, entry)
            if conflicts and not args.replace:
                return _err(
                    f"{settings_file} already sets {', '.join(conflicts)} to other values; nothing written. "
                    "Pass --replace to overwrite them."
                )
            updated, left = merge_entry(settings, entry), []
    except LibraryFailed as exc:
        return _err(f"instrument_run.sh failed: {exc}; nothing written")

    settings_file.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n")
    if left:
        print(f"left {', '.join(left)} — not the value this command writes")
    return 0


def main() -> int:
    return run(sys.argv[1:], run_library=library_runner(_INSTRUMENT_RUN_LIB, os.environ))


if __name__ == "__main__":
    sys.exit(main())
