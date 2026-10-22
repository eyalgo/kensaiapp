#!/usr/bin/env python3
"""telemetry_command.py — the one resolver of the telemetry command's name.

It answers the name `run_telemetry.sh` runs as the telemetry command.

WHY THIS EXISTS: the helper runs a package's command, and a launch nobody configured by hand names
none. Six launchers and the skill launcher all need the same answer, so one tool owns it rather than
each launcher owning a copy. The invoking environment's ``KENSAIAPP_TELEMETRY_COMMAND`` wins when
it holds one — the *membership* is tested, not the truth of the value, so an empty or invalid value
still wins and is how a single launch switches telemetry off. Otherwise the name is read, as data,
from the single dotenv file at the root of the core's source host.

Which host that is comes from the core alone, never from the caller's working directory: a core with
no pin beside it is its own host's ``core/``, and a pinned core's host is the one its ``pin.json``
names (``pin.of_core``). Nothing searches upward, falls back to a neighbouring root, or reads a
satellite's file. A missing or unreadable file, a missing key, an empty value or a manifest that
cannot be read answers the empty string, and the empty string is an answer, never an error.

This tool never runs, checks or searches for a command and never imports the package. Whether the
name is a legal command name, and whether it is executable, stay with the helper.

Its three ways into the filesystem — a core's physical path, the pin manifest beside it and the
setting file — are handed to `Resolver`; `build()` is the one place the real ones are named, and
`resolve()` is the designed entry point over them.

CLI: ``telemetry_command.py --core <absolute core directory>`` prints the name and a newline, and
exits 0 for an empty answer too.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

import env_file
import pin

__version__ = "1.0.0"

COMMAND_VARIABLE = "KENSAIAPP_TELEMETRY_COMMAND"
SETTING_FILE = ".telemetry.env"


@dataclass(frozen=True)
class Resolver:
    """The resolver over the three ways it reaches the filesystem, each handed to it.

    ``physical_path`` answers a core's real path, ``pin_of_core`` the pin a core belongs to (or
    None) and ``read_setting`` a key's value in a dotenv file (or None).
    """

    physical_path: Callable[[Path], Path]
    pin_of_core: Callable[[Path], pin.Pin | None]
    read_setting: Callable[[Path, str], str | None]

    def _source_host(self, core_dir: Path) -> Path | None:
        """The host root whose setting file governs ``core_dir``, or None when it cannot be told.

        A manifest that is present but unusable answers None; it never falls back to the pin's
        neighbours, because a neighbour's setting would belong to some other host.
        """

        physical_core = self.physical_path(core_dir)
        try:
            manifest_pin = self.pin_of_core(physical_core)
        except (OSError, ValueError, KeyError, TypeError):
            return None
        if manifest_pin is None:
            return physical_core.parent
        host = manifest_pin.source_host_root
        # A relative host would be read against the caller's working directory.
        return host if host.is_absolute() else None

    def resolve(self, core_dir: Path, environ: Mapping[str, str]) -> str:
        """The command name for a launch running on ``core_dir`` with environment ``environ``."""

        if COMMAND_VARIABLE in environ:
            return environ[COMMAND_VARIABLE]
        try:
            host = self._source_host(Path(core_dir))
            if host is None:
                return ""
            return self.read_setting(host / SETTING_FILE, COMMAND_VARIABLE) or ""
        except (OSError, RuntimeError):
            return ""


def build() -> Resolver:
    """The composition root: the only place the real collaborators are named."""

    return Resolver(
        physical_path=Path.resolve, pin_of_core=pin.of_core, read_setting=env_file.value
    )


def resolve(core_dir: Path, environ: Mapping[str, str]) -> str:
    """The command name for a launch running on ``core_dir`` with environment ``environ``."""

    return build().resolve(core_dir, environ)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the telemetry command name for a core.")
    parser.add_argument("--core", required=True, type=Path, help="absolute core directory")
    arguments = parser.parse_args(argv)
    print(build().resolve(arguments.core, os.environ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
