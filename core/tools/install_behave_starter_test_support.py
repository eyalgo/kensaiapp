"""Fakes for `install_behave_starter.py`: one per port, over one shared world.

The engine is handed a filesystem, git and a committer. Each fake here keeps its state in a
`FakeWorld` and records every effect there in order, so a test reads both the final state and the
order things happened in. A fake is held to its port by the contract suites in
`test_install_behave_starter.py`, which run against the real adapter and against the fake.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from install_behave_starter import CommitOutcome, CommitRequest, IgnoredPath, UncommittedPath

__version__ = "1.0.0"

SEED_ID = "0" * 40


@dataclass(frozen=True)
class FakeCommit:
    """A commit the fake world holds: its id, its parent, the paths it changed and its message."""

    full_id: str
    parent: str | None
    changed: tuple[str, ...]
    message: str


@dataclass
class FakeWorld:
    """The state the three fakes share.

    `work_tree` is None for a product folder in no repository. `branch` is None for a detached
    HEAD. `index` holds the repository paths that are staged, relative to the product folder, in
    the form the engine hands them over. `uncommitted` maps a path relative to the product folder
    to what git holds uncommitted about it, and `ignored` maps an ignored path to the file holding
    its rule, both as the git port reports them."""

    work_tree: Path | None = Path("/scratch")
    branch: str | None = "main"
    commits: list[FakeCommit] = field(default_factory=list)
    index: set[str] = field(default_factory=set)
    files: dict[Path, bytes] = field(default_factory=dict)
    links: set[Path] = field(default_factory=set)
    uncommitted: dict[str, tuple[str, ...]] = field(default_factory=dict)
    ignored: dict[str, str] = field(default_factory=dict)
    events: list[tuple] = field(default_factory=list)

    def add_commit(self, changed: tuple[str, ...], message: str) -> FakeCommit:
        parent = self.commits[-1].full_id if self.commits else None
        commit = FakeCommit(
            full_id=f"{len(self.commits) + 1:07d}".ljust(40, "a"),
            parent=parent,
            changed=changed,
            message=message,
        )
        self.commits.append(commit)
        return commit


class FakeFilesystem:
    """Files in memory. `fail_on_write` makes the nth write raise an OSError."""

    def __init__(self, world: FakeWorld, *, fail_on_write: int | None = None) -> None:
        self._world = world
        self._fail_on_write = fail_on_write
        self.write_count = 0

    def list_files(self, root: Path) -> list[Path]:
        found = [path.relative_to(root) for path in self._world.files if path.is_relative_to(root)]
        return sorted(found)

    def read_bytes(self, path: Path) -> bytes:
        try:
            return self._world.files[path]
        except KeyError:
            raise FileNotFoundError(f"no such file: {path}") from None

    def write_bytes(self, path: Path, data: bytes) -> None:
        self.write_count += 1
        if self._fail_on_write == self.write_count:
            raise OSError(f"scripted write failure on write {self.write_count}")
        if any(parent in self._world.files for parent in path.parents):
            raise NotADirectoryError(f"a parent of {path} is a file")
        self._world.files[path] = data
        self._world.events.append(("write", path))

    def is_present(self, path: Path) -> bool:
        if path in self._world.files or path in self._world.links:
            return True
        return any(held.is_relative_to(path) for held in self._world.files)

    def remove_tree(self, path: Path) -> None:
        for held in [held for held in self._world.files if held.is_relative_to(path)]:
            del self._world.files[held]
        self._world.links.discard(path)
        self._world.events.append(("remove", path))


class FakeGit:
    """Git answers read from the world. `raise_on` names a method that raises RuntimeError."""

    def __init__(self, world: FakeWorld, *, raise_on: str | None = None) -> None:
        self._world = world
        self._raise_on = raise_on

    def _maybe_raise(self, method: str) -> None:
        if self._raise_on == method:
            raise RuntimeError(f"scripted failure in git.{method}")

    def work_tree(self, folder: Path) -> Path | None:
        self._maybe_raise("work_tree")
        tree = self._world.work_tree
        if tree is None or not folder.is_relative_to(tree):
            return None
        return tree

    def branch(self, folder: Path) -> str | None:
        self._maybe_raise("branch")
        return self._world.branch

    def has_tip(self, folder: Path) -> bool:
        self._maybe_raise("has_tip")
        return bool(self._world.commits)

    def unstage(self, folder: Path, paths: list[str]) -> None:
        self._maybe_raise("unstage")
        self._world.index -= set(paths)
        self._world.events.append(("unstage", tuple(paths)))

    def short_id(self, folder: Path) -> str:
        self._maybe_raise("short_id")
        return self._world.commits[-1].full_id[:7]

    def uncommitted(self, folder: Path, inside: str) -> list[UncommittedPath]:
        self._maybe_raise("uncommitted")
        return [
            UncommittedPath(path, how)
            for path, how in sorted(self._world.uncommitted.items())
            if _is_under(path, inside)
        ]

    def ignored(self, folder: Path, inside: str) -> list[IgnoredPath]:
        self._maybe_raise("ignored")
        return [
            IgnoredPath(path, rule_file)
            for path, rule_file in sorted(self._world.ignored.items())
            if _is_under(path, inside)
        ]


def _is_under(path: str, inside: str) -> bool:
    return path == inside or path.startswith(f"{inside}/")


class FakeCommitter:
    """Commits the declared paths into the world's repository.

    `refuse_with` makes every commit be refused with that reason, leaving the declared paths
    staged as the real builder does when a hook refuses. `raise_error` makes it raise."""

    def __init__(
        self,
        world: FakeWorld,
        *,
        refuse_with: str | None = None,
        raise_error: Exception | None = None,
    ) -> None:
        self._world = world
        self._refuse_with = refuse_with
        self._raise_error = raise_error
        self.requests: list[CommitRequest] = []

    def commit_only(self, request: CommitRequest) -> CommitOutcome:
        self.requests.append(request)
        self._world.events.append(("commit", request))
        if self._raise_error is not None:
            raise self._raise_error
        self._world.index |= set(request.paths)
        if self._refuse_with is not None:
            return CommitOutcome(refusal=self._refuse_with)
        message = "\n".join([
            request.subject, "", request.body, "", request.directional,
            f"Role: {request.role}", f"Surface: {request.surface}",
        ])
        self._world.add_commit(request.paths, message)
        self._world.index -= set(request.paths)
        return CommitOutcome(refusal=None)
