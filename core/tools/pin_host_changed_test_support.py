"""The fake of `pin_host_changed.HostTree`, seeded by the test that makes it.

It is checked against the port's contract suite in `test_pin_host_changed.py`, beside the real
adapter, and it records what it was asked. Only tests import this module.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path


class FakeHostTree:
    """A host and a pin described by what `compare` asks of them. Files are named by their
    relpath, the form both listings give; `holds` and `same_file` are asked with whole paths and
    answer for the relpath under the host root and the pin root they were given."""

    def __init__(
        self,
        *,
        host_root: Path,
        pin_root: Path,
        host_dir: bool = True,
        host_files: Iterable[str] = (),
        held: Iterable[str] | None = None,
        pin_files: Iterable[str] = (),
        git: bool = True,
        ignored: Iterable[str] = (),
        differing: Iterable[str] = (),
    ) -> None:
        self.host_root = host_root
        self.pin_root = pin_root
        self.host_dir = host_dir
        self.listed_on_host = list(host_files)
        self.held = set(self.listed_on_host if held is None else held)
        self.listed_in_pin = list(pin_files)
        self.git = git
        self.ignore_matches = set(ignored)
        self.differing = set(differing)
        self.ignore_asks: list[list[str]] = []

    def is_dir(self, path: Path) -> bool:
        return self.host_dir if path == self.host_root else False

    def host_files(self, host_root: Path) -> list[str]:
        return list(self.listed_on_host) if host_root == self.host_root else []

    def pin_files(self, pin_root: Path) -> list[str]:
        return list(self.listed_in_pin) if pin_root == self.pin_root else []

    def holds(self, path: Path) -> bool:
        return path.relative_to(self.host_root).as_posix() in self.held

    def is_git_work_tree(self, root: Path) -> bool:
        return self.git and root == self.host_root

    def ignored(self, host_root: Path, relpaths: list[str]) -> set[str]:
        self.ignore_asks.append(list(relpaths))
        return {relpath for relpath in relpaths if relpath in self.ignore_matches}

    def same_file(self, host_file: Path, pinned_file: Path) -> bool:
        relpath = host_file.relative_to(self.host_root).as_posix()
        assert pinned_file == self.pin_root / relpath, "a host file is compared with its own copy"
        return relpath not in self.differing
