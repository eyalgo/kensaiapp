#!/usr/bin/env python3
"""install_behave_starter.py — write the Behave starter into a product and commit it on main.

WHY THIS EXISTS
    The start-of-run Behave check in `pin_run.sh` used to copy the starter into a product and
    commit nothing, so the copy read as "already there" on the next launch and was never
    committed. The install is now a transaction: write every file, commit exactly those files on
    `main`, and where the commit cannot land put the product back as it was found. That needs an
    undo and the builder's captured output, which is past what bash does well, so the work crosses
    to Python (`shell/toolchain.md` § When bash is not enough).

    Two outcomes stop the launch, with status 1. A `.behave` already there that holds a path the
    work tree holding the product has not committed (untracked, staged, modified or deleted) or
    ignores stops it, each such path named, and nothing is written. What the starter's own
    `.gitignore` ignores, the environment and caches a scenario run leaves, does not count. And a
    stage or a commit git refuses stops it once what the install wrote is undone, quoting the
    refusal. Every other case where no commit can land on `main` leaves the product as it was
    found, and the launch goes on.

    The commit holds the starter's files and nothing else staged in the product. It goes through
    `commit_builder.py commit --only`, the one place a trailer block is built, and never
    `git commit-tree`, which would skip the `commit-msg` hook.

    Everything the install touches is handed to it: a filesystem, git and a committer, one port
    each. `build_installer` is the only place a real adapter is constructed.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

__version__ = "1.0.0"


# ── what crosses the committer port ──────────────────────────────────────────

@dataclass(frozen=True)
class CommitRequest:
    """One commit: the paths to hold (relative to `repository`) and the words and trailers."""

    repository: Path
    paths: tuple[str, ...]
    subject: str
    body: str
    directional: str
    role: str
    surface: str


@dataclass(frozen=True)
class CommitOutcome:
    """`refusal` is None when the commit landed, else the reason, one line."""

    refusal: str | None


# ── what crosses the git port ────────────────────────────────────────────────

@dataclass(frozen=True)
class UncommittedPath:
    """A path git holds uncommitted, relative to the folder asked about, and what it holds about
    it, in this order where more than one applies: `untracked`, `staged`, `modified`, `deleted`,
    `unmerged`."""

    path: str
    how: tuple[str, ...]


@dataclass(frozen=True)
class IgnoredPath:
    """A path git ignores, relative to the folder asked about, a folder ending in `/`, and the file
    holding the rule that ignores it: relative to that folder when it lies inside it, else as git
    names it."""

    path: str
    rule_file: str


# ── the ports ────────────────────────────────────────────────────────────────

class Filesystem:
    """The files the install writes, reads, probes and removes."""

    def list_files(self, root: Path) -> list[Path]:
        """Every file under `root`, dotfiles included, as paths relative to `root`, sorted."""
        raise NotImplementedError

    def read_bytes(self, path: Path) -> bytes:
        raise NotImplementedError

    def write_bytes(self, path: Path, data: bytes) -> None:
        """Write `data`, creating the parent folders. Raises an OSError it cannot write."""
        raise NotImplementedError

    def is_present(self, path: Path) -> bool:
        """True for a file, a folder, a link or a dangling link."""
        raise NotImplementedError

    def remove_tree(self, path: Path) -> None:
        raise NotImplementedError


class Git:
    """What the install asks git, and the one thing it tells git to undo."""

    def work_tree(self, folder: Path) -> Path | None:
        """The work tree holding `folder`, or None when it is in no repository."""
        raise NotImplementedError

    def branch(self, folder: Path) -> str | None:
        """The checked-out branch's name, or None on a detached HEAD."""
        raise NotImplementedError

    def has_tip(self, folder: Path) -> bool:
        """False for a branch with no commit yet."""
        raise NotImplementedError

    def unstage(self, folder: Path, paths: list[str]) -> None:
        """Take `paths` (relative to `folder`) out of the index and leave every other entry."""
        raise NotImplementedError

    def short_id(self, folder: Path) -> str:
        """The short id of the checked-out commit."""
        raise NotImplementedError

    def uncommitted(self, folder: Path, inside: str) -> list[UncommittedPath]:
        """Every path under `inside`, which is relative to `folder`, that is untracked, staged,
        modified or deleted in the work tree holding `folder`, sorted by path."""
        raise NotImplementedError

    def ignored(self, folder: Path, inside: str) -> list[IgnoredPath]:
        """Every path under `inside` that the work tree holding `folder` ignores, sorted by path.
        A folder whose own name a rule matches is one entry, and what it holds is not listed."""
        raise NotImplementedError


class Committer:
    """Commits declared paths and nothing else."""

    def commit_only(self, request: CommitRequest) -> CommitOutcome:
        raise NotImplementedError


# ── the real adapters ────────────────────────────────────────────────────────

class DiskFilesystem(Filesystem):
    def list_files(self, root: Path) -> list[Path]:
        return sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file())

    def read_bytes(self, path: Path) -> bytes:
        return path.read_bytes()

    def write_bytes(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def is_present(self, path: Path) -> bool:
        return path.exists() or path.is_symlink()

    def remove_tree(self, path: Path) -> None:
        shutil.rmtree(path)


class GitCli(Git):
    def _run(
        self, folder: Path, *args: str, stdin: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(folder), *args], capture_output=True, text=True, input=stdin
        )

    def work_tree(self, folder: Path) -> Path | None:
        result = self._run(folder, "rev-parse", "--show-toplevel")
        return Path(result.stdout.strip()) if result.returncode == 0 else None

    def branch(self, folder: Path) -> str | None:
        result = self._run(folder, "symbolic-ref", "--quiet", "--short", "HEAD")
        return result.stdout.strip() if result.returncode == 0 else None

    def has_tip(self, folder: Path) -> bool:
        return self._run(folder, "rev-parse", "--verify", "--quiet", "HEAD").returncode == 0

    def unstage(self, folder: Path, paths: list[str]) -> None:
        if not paths:
            return
        result = self._run(folder, "reset", "--quiet", "--", *paths)
        if result.returncode != 0:
            raise RuntimeError(
                f"git could not unstage the install's paths: {result.stderr.strip()}"
            )

    def short_id(self, folder: Path) -> str:
        result = self._run(folder, "rev-parse", "--short", "HEAD")
        if result.returncode != 0:
            raise RuntimeError(f"git could not name the new commit: {result.stderr.strip()}")
        return result.stdout.strip()

    def uncommitted(self, folder: Path, inside: str) -> list[UncommittedPath]:
        entries = self._status(folder, inside)
        return sorted(
            (UncommittedPath(path, _how(code)) for code, path in entries if code != _IGNORED),
            key=lambda held: held.path,
        )

    def ignored(self, folder: Path, inside: str) -> list[IgnoredPath]:
        paths = sorted(path for code, path in self._status(folder, inside, ignored=True)
                       if code == _IGNORED)
        if not paths:
            return []
        rules = self._rule_files(folder, paths)
        return [IgnoredPath(path, rules.get(path, "")) for path in paths]

    def _prefix(self, folder: Path) -> str:
        """Where `folder` sits in its work tree, ending in `/`, or empty at the work tree's root."""
        result = self._run(folder, "rev-parse", "--show-prefix")
        if result.returncode != 0:
            raise RuntimeError(f"git could not place {folder}: {result.stderr.strip()}")
        return result.stdout.strip()

    def _status(self, folder: Path, inside: str, *, ignored: bool = False) -> list[tuple[str, str]]:
        """`(code, path)` per status entry under `inside`, the path relative to `folder`."""
        prefix = self._prefix(folder)
        args = ["--literal-pathspecs", "status", "--porcelain=v1", "-z", "--no-renames",
                "--untracked-files=all"]
        if ignored:
            args.append("--ignored=matching")
        result = self._run(folder, *args, "--", inside)
        if result.returncode != 0:
            raise RuntimeError(f"git could not read the status of {inside}: "
                               f"{result.stderr.strip()}")
        entries = []
        for entry in filter(None, result.stdout.split("\0")):
            entries.append((entry[:2], entry[3:].removeprefix(prefix)))
        return entries

    def _rule_files(self, folder: Path, paths: list[str]) -> dict[str, str]:
        """For each path (relative to `folder`), the file holding the rule that ignores it."""
        prefix = self._prefix(folder)
        result = self._run(folder, "check-ignore", "-z", "-v", "--stdin",
                           stdin="".join(f"{path}\0" for path in paths))
        if result.returncode not in (0, 1):
            raise RuntimeError(f"git could not say which rule ignores each path: "
                               f"{result.stderr.strip()}")
        fields = result.stdout.split("\0")
        rules = {}
        for start in range(0, len(fields) - 3, 4):
            source, _line, _pattern, path = fields[start:start + 4]
            rules[path] = source.removeprefix(prefix) if source.startswith(prefix) else source
        return rules


_IGNORED = "!!"


def _how(code: str) -> tuple[str, ...]:
    """What a two-letter porcelain status code says git holds uncommitted about a path."""
    if code == "??":
        return ("untracked",)
    if "U" in code or code in ("AA", "DD"):
        return ("unmerged",)
    staged, worktree = code[0], code[1]
    how = []
    if staged != " ":
        how.append("staged")
    if worktree in ("M", "T"):
        how.append("modified")
    if worktree == "D":
        how.append("deleted")
    return tuple(how)


class BuilderCommitter(Committer):
    """Runs `commit_builder.py commit --only` as a process on `python`.

    A process, because git's own output reaches the descriptors directly and an in-process
    `main` cannot capture it; the install prints nothing but its one line."""

    def __init__(self, *, builder: Path, python: str) -> None:
        self._builder = builder
        self._python = python

    def commit_only(self, request: CommitRequest) -> CommitOutcome:
        argv = [
            self._python, str(self._builder), "--repo", str(request.repository), "commit",
            "--only", "--add", *request.paths,
            "--subject", request.subject, "--body", request.body,
            "--role", request.role, "--directional", request.directional,
            "--surface", request.surface,
        ]
        result = subprocess.run(argv, capture_output=True, text=True)
        if result.returncode == 0:
            return CommitOutcome(refusal=None)
        return CommitOutcome(refusal=_refusal_reason(result))


def _refusal_reason(result: subprocess.CompletedProcess[str]) -> str:
    """One line of the builder's captured output, never the output whole.

    The last non-blank line of stderr, where the builder and a refusing hook say why, and of
    stdout when stderr is empty."""
    for stream in (result.stderr, result.stdout):
        lines = [line.strip() for line in stream.splitlines() if line.strip()]
        if lines:
            return lines[-1]
    return f"the commit builder exited with status {result.returncode}"


# ── the install ──────────────────────────────────────────────────────────────

MAIN_BRANCH = "main"
COMMIT_ROLE = "Product"
COMMIT_SURFACE = "behave-check"


class Installer:
    """Writes the starter under `into` and commits those files on main, or leaves the product as
    it found it, stopping the launch on a held path or a refused commit. Everything it uses is
    handed to it; it constructs nothing."""

    def __init__(
        self,
        *,
        filesystem: Filesystem,
        git: Git,
        committer: Committer,
        stderr: TextIO,
        starter: Path,
        into: Path,
        project: str,
        launch: str,
    ) -> None:
        self._filesystem = filesystem
        self._git = git
        self._committer = committer
        self._stderr = stderr
        self._starter = starter
        self._into = into
        self._project = project
        self._launch = launch
        self._product = into.parent
        self._folder = into.name

    def install(self) -> int:
        """Return 0 for every outcome the launch goes on after and 1 for a stop; raise for an
        unexpected failure."""
        if self._filesystem.is_present(self._into):
            return self._check_held()
        why_not = self._why_not()
        if why_not is not None:
            self._say(why_not)
            return 0
        relative = self._filesystem.list_files(self._starter)
        if not relative:
            raise FileNotFoundError(f"the starter at {self._starter} holds no file")
        contents = [(path, self._filesystem.read_bytes(self._starter / path)) for path in relative]
        paths = [f"{self._folder}/{path.as_posix()}" for path in relative]
        try:
            failure = self._copy_and_commit(contents, paths)
        except Exception:
            self._undo(paths)
            raise
        if failure is not None:
            self._undo(paths)
            kind, reason = failure
            if kind == "write":
                self._say(self._write_failed_line(reason))
                return 0
            self._say(self._refused_line(reason))
            return EXIT_STOP
        self._say(self._installed_line(self._git.short_id(self._product)))
        return 0

    def unexpected_error_line(self, error: Exception) -> str:
        return (
            f"{self._launch}: installing the Behave starter into {self._product}, the product "
            f"folder of project {self._project}, failed with an unexpected error, and the launch "
            f"stopped: {_one_line(str(error))}. Before the next launch, check that "
            f"{self._product} holds no uncommitted {self._folder}."
        )

    def _check_held(self) -> int:
        """The folder is already there: stop on any path in it the work tree holding the product
        has not committed or ignores, and otherwise leave it as it is. Writes nothing."""
        if self._git.work_tree(self._product) is None:
            return 0
        held = [
            f"{entry.path} ({' and '.join(entry.how)})"
            for entry in self._git.uncommitted(self._product, self._folder)
        ]
        own_rules = f"{self._folder}/.gitignore"
        held += [
            f"{entry.path} (ignored)"
            for entry in self._git.ignored(self._product, self._folder)
            if entry.rule_file != own_rules
        ]
        if not held:
            return 0
        self._say(self._held_line(held))
        return EXIT_STOP

    def _copy_and_commit(
        self, contents: list[tuple[Path, bytes]], paths: list[str]
    ) -> tuple[str, str] | None:
        """None when the commit landed, else `("write", reason)` for a write that failed or
        `("commit", reason)` for a stage or a commit git refused."""
        try:
            for path, data in contents:
                self._filesystem.write_bytes(self._into / path, data)
        except OSError as error:
            return ("write", _one_line(str(error)))
        outcome = self._committer.commit_only(self._request(tuple(paths)))
        return None if outcome.refusal is None else ("commit", outcome.refusal)

    def _undo(self, paths: list[str]) -> None:
        """Unstage the folder's paths, then remove the folder, which did not exist before."""
        try:
            self._git.unstage(self._product, paths)
        finally:
            if self._filesystem.is_present(self._into):
                self._filesystem.remove_tree(self._into)

    def _request(self, paths: tuple[str, ...]) -> CommitRequest:
        return CommitRequest(
            repository=self._product,
            paths=paths,
            subject=f"behave-check: install the Behave starter in {self._folder}",
            body=(
                "Written by the start-of-run Behave check in <CORE>/tools/pin_run.sh, during a "
                f"{self._launch} launch for project {self._project}. The project's card reads "
                f"**Behave:** behave, and the product folder held no {self._folder}. No model "
                "ran: every file is copied byte-identical from <CORE>/templates/behave-starter/. "
                "This commit holds those files only. Anything else staged in this repository "
                "was left staged."
            ),
            directional=(
                f"Finish-line: {self._project} — aside: the start-of-run check installed the "
                "Behave starter, which gives the product's scenarios a place to run and does not "
                "itself advance the product's done"
            ),
            role=COMMIT_ROLE,
            surface=COMMIT_SURFACE,
        )

    def _why_not(self) -> str | None:
        """The whole line saying why no commit can land on main, or None when one can."""
        lead = f"{self._launch}: the Behave starter was not installed, because"
        product = f"{self._product}, the product folder of project {self._project},"
        if self._git.work_tree(self._product) is None:
            return (
                f"{lead} {product} is in no git work tree, so its commit could not land on "
                f"{MAIN_BRANCH}. Nothing was written. A launch installs it once {self._product} "
                f"is in a git work tree with {MAIN_BRANCH} checked out."
            )
        branch = self._git.branch(self._product)
        if branch != MAIN_BRANCH:
            checked_out = "a detached HEAD" if branch is None else branch
            return (
                f"{lead} the git work tree holding {product} has {checked_out} checked out, "
                f"not {MAIN_BRANCH}. Nothing was written. The next launch with {MAIN_BRANCH} "
                "checked out installs it."
            )
        if not self._git.has_tip(self._product):
            return (
                f"{lead} {MAIN_BRANCH}, checked out in the git work tree holding {product} has "
                "no commit yet for the install's commit to follow. Nothing was written. The "
                f"next launch after {MAIN_BRANCH}'s first commit installs it."
            )
        return None

    def _write_failed_line(self, reason: str) -> str:
        return (
            f"{self._launch}: the Behave starter was not installed, because its commit on "
            f"{MAIN_BRANCH} in {self._product}, the product folder of project {self._project}, "
            f"did not land: {reason.removesuffix('.')}. What the install wrote was unstaged and "
            "removed, and nothing was committed. The next launch tries again."
        )

    def _refused_line(self, refusal: str) -> str:
        return (
            f"{self._launch}: the Behave starter was not installed, and the launch stopped, "
            f"because git refused its commit on {MAIN_BRANCH} in {self._product}, the product "
            f"folder of project {self._project}, so it did not land: "
            f"{refusal.removesuffix('.')}. What the install wrote was unstaged and removed, and "
            "nothing was committed. Settle what git refused, then launch again."
        )

    def _held_line(self, held: list[str]) -> str:
        return (
            f"{self._launch}: the launch stopped, because {self._folder} in {self._product}, the "
            f"product folder of project {self._project}, holds paths the git work tree holding it "
            f"has not committed or ignores: {', '.join(held)}. Nothing was written. Commit or "
            "undo each change named, and stop ignoring each path named, then launch again."
        )

    def _installed_line(self, short_id: str) -> str:
        return (
            f"{self._launch}: installed the Behave starter as {self._folder} in {self._product}, "
            f"the product folder of project {self._project}, and committed it on {MAIN_BRANCH} "
            f"as {short_id}."
        )

    def _say(self, line: str) -> None:
        print(line, file=self._stderr)


def _one_line(text: str) -> str:
    """The first line of `text`, with any full stop at its end removed."""
    first = text.strip().splitlines()[0] if text.strip() else ""
    return first.removesuffix(".")


# ── the composition root and the CLI ─────────────────────────────────────────

EXIT_STOP = 1
EXIT_UNEXPECTED = 1
EXIT_USAGE = 2
BUILDER = Path(__file__).resolve().parent / "commit_builder.py"


def build_installer(
    *, starter: Path, into: Path, project: str, launch: str, stderr: TextIO
) -> Installer:
    """The only place a real adapter is constructed."""
    return Installer(
        filesystem=DiskFilesystem(),
        git=GitCli(),
        committer=BuilderCommitter(builder=BUILDER, python=sys.executable),
        stderr=stderr,
        starter=starter,
        into=into,
        project=project,
        launch=launch,
    )


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="install_behave_starter.py",
        description="Write the Behave starter into a product folder and commit it on main.",
    )
    parser.add_argument("--starter", type=Path, required=True)
    parser.add_argument("--into", type=Path, required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--launch", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Exit 0 for every outcome a launch goes on after, 1 for a stop or an unexpected failure,
    and 2 for a usage error."""
    try:
        arguments = _parse(sys.argv[1:] if argv is None else argv)
    except SystemExit as stop:
        return EXIT_USAGE if stop.code else 0
    install = build_installer(
        starter=arguments.starter, into=arguments.into, project=arguments.project,
        launch=arguments.launch, stderr=sys.stderr,
    )
    try:
        return install.install()
    except Exception as error:
        print(install.unexpected_error_line(error), file=sys.stderr)
        return EXIT_UNEXPECTED


if __name__ == "__main__":
    sys.exit(main())
