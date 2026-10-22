"""Tests for telemetry_command.py — the one resolver of the telemetry command's name.

Every case builds a real scratch host (or pin) under ``tmp_path`` and reads it through the real
``pin`` and ``env_file`` collaborators: the resolver's whole job is how those two are combined, so
a stand-in for either would prove the stand-in. Nothing here names the package's own command; each
case writes a neutral name of its own.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import pin
import telemetry_command

TOOL = Path(__file__).resolve().parent / "telemetry_command.py"
KEY = "KENSAIAPP_TELEMETRY_COMMAND"
SETTING_FILE = ".telemetry.env"

pytestmark = pytest.mark.skipif(
    os.geteuid() == 0, reason="permission-denied cases cannot be staged as root"
)


def _host(root: Path, name: str, setting: str | None) -> Path:
    """A live host: ``<root>/<name>/core`` beside an optional setting file."""
    host = root / name
    (host / "core").mkdir(parents=True)
    if setting is not None:
        (host / SETTING_FILE).write_text(setting, encoding="utf-8")
    return host


def _pin(root: Path, host: Path, manifest: object | None = None) -> Path:
    """A pin of ``host``: ``<root>/pins/p1/core`` with a manifest naming ``host`` as its source."""
    pin_root = root / "pins" / "p1"
    (pin_root / "core").mkdir(parents=True)
    if manifest is None:
        manifest = {"id": "p1", "source_host_root": str(host)}
    (pin_root / "pin.json").write_text(
        manifest if isinstance(manifest, str) else json.dumps(manifest), encoding="utf-8"
    )
    return pin_root / "core"


def _setting(name: str) -> str:
    return f"{KEY}={name}\n"


def test_explicit_environment_wins_without_filesystem_access(tmp_path):
    unavailable = tmp_path / "no-such-core" / "core"
    for value in ("explicit-name", "not a plain/name", ""):
        assert telemetry_command.resolve(unavailable, {KEY: value}) == value
    host = _host(tmp_path, "host", _setting("from-setting"))
    for value in ("explicit-name", "-bad", ""):
        assert telemetry_command.resolve(host / "core", {KEY: value}) == value


def test_direct_core_reads_only_its_physical_source_host(tmp_path, monkeypatch):
    host = _host(tmp_path, "host", _setting("host-name"))
    unrelated = _host(tmp_path, "unrelated", _setting("cwd-name"))
    monkeypatch.chdir(unrelated)
    assert telemetry_command.resolve(host / "core", {}) == "host-name"
    link = tmp_path / "link-to-core"
    link.symlink_to(host / "core", target_is_directory=True)
    assert telemetry_command.resolve(link, {}) == "host-name"
    # A core reached through a symlinked host directory resolves the physical host too.
    host_link = tmp_path / "link-to-host"
    host_link.symlink_to(host, target_is_directory=True)
    assert telemetry_command.resolve(host_link / "core", {}) == "host-name"
    # The core's own folder holds no setting: only the host root is read.
    (host / "core" / SETTING_FILE).write_text(_setting("inside-core"), encoding="utf-8")
    assert telemetry_command.resolve(host / "core", {}) == "host-name"


def test_pinned_core_uses_manifest_source_host(tmp_path, monkeypatch):
    host = _host(tmp_path, "host", _setting("host-name"))
    satellite = _host(tmp_path, "satellite", _setting("satellite-name"))
    core = _pin(tmp_path, host)
    # The pin's parent holds a conflicting setting, and so do the launch cwd and an inherited pin.
    (core.parent / SETTING_FILE).write_text(_setting("pin-parent-name"), encoding="utf-8")
    (core.parent.parent / SETTING_FILE).write_text(_setting("pins-home-name"), encoding="utf-8")
    other_pin = _pin_elsewhere(tmp_path / "other", satellite)
    monkeypatch.chdir(satellite)
    monkeypatch.setenv("KENSAIAPP_PIN", str(other_pin.parent))
    ambient = {key: value for key, value in os.environ.items() if key != KEY}
    assert telemetry_command.resolve(core, ambient) == "host-name"


def _pin_elsewhere(root: Path, host: Path) -> Path:
    root.mkdir()
    return _pin(root, host)


def test_unreadable_or_absent_setting_returns_empty(tmp_path):
    no_file = _host(tmp_path, "no-file", None)
    no_key = _host(tmp_path, "no-key", "OTHER=value\n")
    empty = _host(tmp_path, "empty", f"{KEY}=\n")
    bad_utf8 = _host(tmp_path, "bad-utf8", "")
    (bad_utf8 / SETTING_FILE).write_bytes(b"\xff\xfe\x00 not utf-8")
    denied = _host(tmp_path, "denied", _setting("denied-name"))
    (denied / SETTING_FILE).chmod(0o000)
    try:
        for host in (no_file, no_key, empty, bad_utf8, denied):
            assert telemetry_command.resolve(host / "core", {}) == "", host.name
    finally:
        (denied / SETTING_FILE).chmod(0o600)
    # A host that is not there at all: the core directory itself is absent.
    assert telemetry_command.resolve(tmp_path / "vanished" / "core", {}) == ""


@pytest.mark.parametrize(
    "manifest",
    [
        "{not json",
        "[]",
        "null",
        '"a string"',
        {"id": "p1"},
        {"source_host_root": "/somewhere"},
        {"id": "p1", "source_host_root": 7},
        {"id": "p1", "source_host_root": None},
        {"id": "p1", "source_host_root": ["/a"]},
        {"id": "p1", "source_host_root": "relative/host"},
        {"id": "p1", "source_host_root": ""},
    ],
)
def test_malformed_manifest_returns_empty_without_fallback(tmp_path, monkeypatch, manifest):
    neighbour = _host(tmp_path, "neighbour", _setting("neighbour-name"))
    host = _host(tmp_path, "host", _setting("host-name"))
    core = _pin(tmp_path, host, manifest)
    (core.parent.parent / SETTING_FILE).write_text(_setting("pins-home-name"), encoding="utf-8")
    monkeypatch.chdir(neighbour)
    assert telemetry_command.resolve(core, {}) == ""


def test_unreadable_manifest_returns_empty_without_fallback(tmp_path):
    host = _host(tmp_path, "host", _setting("host-name"))
    core = _pin(tmp_path, host)
    manifest = core.parent / "pin.json"
    manifest.chmod(0o000)
    try:
        assert telemetry_command.resolve(core, {}) == ""
    finally:
        manifest.chmod(0o600)


def test_setting_is_data_and_command_validation_stays_with_helper(tmp_path, monkeypatch):
    marker = tmp_path / "executed"
    data = f"$(touch {marker}); `touch {marker}` ../not/a/name"
    host = _host(tmp_path, "host", f'{KEY}="{data}"\n')

    def refuse(*args, **kwargs):
        raise AssertionError("the resolver must not launch a process")

    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(subprocess, "Popen", refuse)
    monkeypatch.setattr(os, "system", refuse)
    imported_before = set(sys.modules)
    assert telemetry_command.resolve(host / "core", {}) == data
    assert not marker.exists()
    assert not [m for m in set(sys.modules) - imported_before if "telemetry" in m.lower()]


def _run_cli(*arguments: str, environ: dict[str, str] | None = None):
    env = {key: value for key, value in os.environ.items() if key != KEY}
    env.update(environ or {})
    return subprocess.run(
        [sys.executable, str(TOOL), *arguments],
        capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL,
    )


def test_cli_prints_only_the_selected_name(tmp_path):
    host = _host(tmp_path, "host", _setting("host-name"))
    populated = _run_cli("--core", str(host / "core"))
    assert (populated.returncode, populated.stdout, populated.stderr) == (0, "host-name\n", "")
    empty_host = _host(tmp_path, "empty-host", None)
    empty = _run_cli("--core", str(empty_host / "core"))
    assert (empty.returncode, empty.stdout, empty.stderr) == (0, "\n", "")
    explicit = _run_cli("--core", str(host / "core"), environ={KEY: "env-name"})
    assert (explicit.returncode, explicit.stdout, explicit.stderr) == (0, "env-name\n", "")
    blank = _run_cli("--core", str(host / "core"), environ={KEY: ""})
    assert (blank.returncode, blank.stdout, blank.stderr) == (0, "\n", "")


def test_cli_answers_empty_for_an_unusable_core_argument(tmp_path):
    answer = _run_cli("--core", str(tmp_path / "vanished" / "core"))
    assert (answer.returncode, answer.stdout, answer.stderr) == (0, "\n", "")


# --- the resolver over injected collaborators ----------------------------------------------------
#
# The cases above drive `resolve` over the real `pin` and `env_file` readers on real scratch trees.
# The cases below hand the resolver recording fakes for its three ways into the filesystem — the
# physical path of a core, the pin manifest beside it and the setting file — and assert on what
# each fake was asked, which a real tree cannot show: that an explicit value asks nothing at all.


class _Recorder:
    """Fakes for the resolver's three collaborators, each recording what it was asked."""

    def __init__(self, *, physical=None, manifest=None, setting=None):
        self.asked: list[tuple[str, object]] = []
        self._physical = physical or (lambda path: path)
        self._manifest = manifest or (lambda core: None)
        self._setting = setting or (lambda path, key: None)

    def physical_path(self, path: Path) -> Path:
        self.asked.append(("physical", path))
        return self._physical(path)

    def pin_of_core(self, core: Path):
        self.asked.append(("manifest", core))
        return self._manifest(core)

    def read_setting(self, path: Path, key: str):
        self.asked.append(("setting", (path, key)))
        return self._setting(path, key)

    def resolver(self) -> telemetry_command.Resolver:
        return telemetry_command.Resolver(
            physical_path=self.physical_path,
            pin_of_core=self.pin_of_core,
            read_setting=self.read_setting,
        )


def _raise(error: BaseException):
    def collaborator(*_arguments):
        raise error

    return collaborator


def _a_pin(host: object) -> pin.Pin:
    return pin.Pin(
        root=Path("/pins/p1"), core=Path("/pins/p1/core"), source_host_root=host, id="p1"
    )


@pytest.mark.parametrize("value", ["explicit-name", "not a plain/name", ""])
def test_an_explicit_value_asks_no_collaborator(value):
    recorder = _Recorder()

    assert recorder.resolver().resolve(Path("/any/core"), {KEY: value}) == value
    assert recorder.asked == []


def test_a_direct_core_reads_the_setting_beside_its_physical_core():
    recorder = _Recorder(
        physical=lambda path: Path("/real/host/core"),
        setting=lambda path, key: "host-name",
    )

    assert recorder.resolver().resolve(Path("/linked/core"), {}) == "host-name"
    assert recorder.asked == [
        ("physical", Path("/linked/core")),
        ("manifest", Path("/real/host/core")),
        ("setting", (Path("/real/host") / SETTING_FILE, KEY)),
    ]


def test_a_pinned_core_reads_the_setting_of_its_manifest_host():
    recorder = _Recorder(
        manifest=lambda core: _a_pin(Path("/the/source/host")),
        setting=lambda path, key: "host-name",
    )

    assert recorder.resolver().resolve(Path("/pins/p1/core"), {}) == "host-name"
    assert recorder.asked[-1] == ("setting", (Path("/the/source/host") / SETTING_FILE, KEY))


@pytest.mark.parametrize("host", [Path("relative/host"), Path("")], ids=["relative", "empty"])
def test_a_manifest_host_that_is_not_absolute_reads_no_setting(host):
    recorder = _Recorder(manifest=lambda core: _a_pin(host), setting=_raise(AssertionError()))

    assert recorder.resolver().resolve(Path("/pins/p1/core"), {}) == ""
    assert [kind for kind, _ in recorder.asked] == ["physical", "manifest"]


@pytest.mark.parametrize(
    ("collaborator", "error"),
    [
        ("physical", OSError("loop")),
        ("physical", RuntimeError("symlink loop")),
        ("manifest", OSError("unreadable")),
        ("manifest", ValueError("not json")),
        ("manifest", KeyError("source_host_root")),
        ("manifest", TypeError("wrong shape")),
        ("setting", OSError("unreadable")),
    ],
)
def test_a_failing_collaborator_answers_empty(collaborator, error):
    recorder = _Recorder(**{collaborator: _raise(error)})

    assert recorder.resolver().resolve(Path("/a/core"), {}) == ""


@pytest.mark.parametrize("answer", [None, ""], ids=["no-assignment", "empty-assignment"])
def test_a_setting_that_names_nothing_answers_empty(answer):
    recorder = _Recorder(setting=lambda path, key: answer)

    assert recorder.resolver().resolve(Path("/a/host/core"), {}) == ""
