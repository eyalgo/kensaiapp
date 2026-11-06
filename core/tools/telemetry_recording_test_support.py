"""The telemetry package, as recorded — what a test calls instead of the package installed in the
owner's home.

A test reads nothing of the machine it runs on (`core/doctrine/engineering/testing_doctrine.md`).
The suites that hold `run_telemetry.sh` and the launchers to the package's real behaviour used to
link the owner's installed package into a scratch home, and skipped where it was not installed. They
now call this stand-in, installed into the scratch home under the command's name. It answers each
call with what the real package answered the same call, from `RECORDINGS`, committed beside it.

**One call, one key.** The package is run as `<command> turn-on --print --endpoint-file <file>
--prefix kensai --label …` in the caller's working folder. What can change its answer is the key:
the arguments (the endpoint file by its content, not its path), the working folder, the files of the
git repository that folder sits in, and the `OTEL_` and `INSTRUMENT_RUN_` variables. Every pytest
temporary folder in them is written `<TMP>`, so a recording made in one run matches the next; every
UUID is written by its order of appearance, so a run id the package makes is a fresh one on replay,
and one the caller passed in comes back as the caller's.

**A call with no recording fails**, exit 97 and a line naming its key — never a skip. Recording is
the one moment the real package is read: run the suites with `KENSAIAPP_RECORD_TELEMETRY_PACKAGE`
set to the real command's absolute path, and each call runs the package and adds its answer to
`RECORDINGS`.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

RECORDINGS = Path(__file__).with_name("telemetry_package_recordings.json")
RECORD_VARIABLE = "KENSAIAPP_RECORD_TELEMETRY_PACKAGE"
MISSING_STATUS = 97
KEY_ENV_PREFIXES = ("OTEL_", "INSTRUMENT_RUN_")

_TMP = re.compile(r"(?:/private)?/[^\s\"',]*?/pytest-of-[^/\s\"',]+/pytest-\d+/(?:popen-gw\d+/)?[^/\s\"',]+")
_UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")

_STAND_IN = """#!{python}
import sys
sys.path.insert(0, {tools!r})
import telemetry_recording_test_support as recording
sys.exit(recording.main(sys.argv[1:], real_command={real!r}))
"""


def install(home: Path, command: str) -> Path:
    """The stand-in, at `<home>/.kensaiapp/venv/bin/<command>` — where `run_telemetry.sh` runs the
    package from. It records only when `RECORD_VARIABLE` names the real command in this process's
    environment; otherwise it replays."""
    path = home / ".kensaiapp" / "venv" / "bin" / command
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_STAND_IN.format(
        python=sys.executable, tools=str(Path(__file__).resolve().parent),
        real=os.environ.get(RECORD_VARIABLE) or None,
    ))
    path.chmod(0o755)
    return path


class _Neutral:
    """Writes temporary folders and UUIDs out of a text, and back in."""

    def __init__(self) -> None:
        self.tmp: str | None = None
        self.uuids: list[str] = []

    def out(self, text: str) -> str:
        def tmp(match: re.Match) -> str:
            self.tmp = self.tmp or match.group(0)
            return "<TMP>"

        def uid(match: re.Match) -> str:
            value = match.group(0)
            if value not in self.uuids:
                self.uuids.append(value)
            return f"<UUID-{self.uuids.index(value)}>"

        return _UUID.sub(uid, _TMP.sub(tmp, text))

    def back(self, text: str) -> str:
        fresh: dict[str, str] = {}

        def uid(match: re.Match) -> str:
            index = int(match.group(1))
            if index < len(self.uuids):
                return self.uuids[index]
            return fresh.setdefault(match.group(0), str(uuid.uuid4()))

        text = re.sub(r"<UUID-(\d+)>", uid, text)
        return text.replace("<TMP>", self.tmp) if self.tmp else text


def _read(path: Path) -> str:
    """A file's text, or a mark saying it could not be read — a case may make one unreadable on
    purpose, and that is part of what the package was asked."""
    if path.is_dir():
        return "<DIRECTORY>"
    try:
        return path.read_text(errors="replace")
    except OSError:
        return "<UNREADABLE>"


def _tree(folder: Path, neutral: _Neutral) -> str:
    """A digest of the files of the git repository `folder` sits in — the instance the package
    reads — or nothing when it sits in none: a test's own scratch folder fills with logs while it
    runs, and is no instance."""
    done = subprocess.run(["git", "-C", str(folder), "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True)
    if done.returncode != 0:
        return ""
    root = Path(done.stdout.strip())
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if ".git" in path.relative_to(root).parts or not path.is_file():
            continue
        digest.update(str(path.relative_to(root)).encode() + b"\0")
        digest.update(neutral.out(_read(path)).encode() + b"\0")
    return digest.hexdigest()


def key(argv: list[str], cwd: Path, environ: dict[str, str], neutral: _Neutral) -> dict:
    args = list(argv)
    endpoint = None
    if "--endpoint-file" in args:
        at = args.index("--endpoint-file") + 1
        if at < len(args):
            file = Path(args[at])
            endpoint = _read(file) if file.exists() else None
            args[at] = "<ENDPOINT-FILE>"
    return {
        "argv": [neutral.out(arg) for arg in args],
        "endpoint": endpoint,
        "cwd": neutral.out(str(cwd)),
        "tree": _tree(cwd, neutral),
        "env": {name: neutral.out(value) for name, value in sorted(environ.items())
                if name.startswith(KEY_ENV_PREFIXES)},
    }


def _digest(entry_key: dict) -> str:
    return hashlib.sha256(json.dumps(entry_key, sort_keys=True).encode()).hexdigest()


def _record(entry_key: dict, answer: dict) -> None:
    RECORDINGS.touch()
    with RECORDINGS.open("r+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        text = handle.read()
        recordings = json.loads(text) if text.strip() else {}
        recordings[_digest(entry_key)] = {"key": entry_key, **answer}
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps(recordings, indent=1, sort_keys=True) + "\n")


def main(argv: list[str], *, real_command: str | None) -> int:
    neutral = _Neutral()
    environ = dict(os.environ)
    entry_key = key(argv, Path.cwd(), environ, neutral)
    if real_command:
        done = subprocess.run([real_command, *argv], capture_output=True, text=True)
        answer = {"stdout": neutral.out(done.stdout), "stderr": neutral.out(done.stderr),
                  "status": done.returncode}
        _record(entry_key, answer)
    else:
        recordings = json.loads(RECORDINGS.read_text()) if RECORDINGS.is_file() else {}
        answer = recordings.get(_digest(entry_key))
        if answer is None:
            print(f"no recording of this telemetry package call — record with {RECORD_VARIABLE}: "
                  f"{json.dumps(entry_key, sort_keys=True)}", file=sys.stderr)
            return MISSING_STATUS
    sys.stdout.write(neutral.back(answer["stdout"]))
    sys.stderr.write(neutral.back(answer["stderr"]))
    return answer["status"]
