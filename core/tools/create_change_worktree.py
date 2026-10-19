#!/usr/bin/env python3
"""create_change_worktree.py — creates a change's branch and worktree, or says why it cannot.

WHY THIS EXISTS. A change's worktree used to be made by a shell procedure written out in prose
(`development-worktree`, Steps 1 to 3b): path derivation, the branch and path guards, the local
exclude and the `git worktree add` calls, each one a step a model had to carry out. For an external
product that procedure made the instance's worktree first and only then resolved and guarded the
product repository, so a refusal in the product left the instance changed. One command removes that
ordering, and a caller reads one JSON object instead of judging a transcript.

Six phases. **Resolve** places the topology through `development_path` and changes nothing.
**Preflight** checks every repository, instance first, and changes nothing. **Create** makes the
branch and worktree in each repository, instance first, after appending the local exclude line when
git's own matcher says none matches. **Confirm** runs `development_path.validate_contract` on the
result. **Setup** runs the card's `Setup command:` once, in the product directory of the new
worktree, so the suite its `Test command:` names can run there. **Check** then refuses a
worktree whose `Test command:` names a relative interpreter, such as `.venv/bin/python3`, with
nothing at it. Both come last because they can fail after every worktree exists: that refusal is
one after a change, reported as such. Every outcome but a missing flag is one JSON object on
stdout; a missing flag is argparse's exit 2, because there is no caller-supplied value to report.

Create-only: nothing this command made is ever removed, reset or reused (a failure after the first
change leaves it and reports it), and `development_path.py` stays resolve-and-validate only.

Stdlib only. Git and the repository's own files are reached through the injected `WorktreeGit`,
never by a call anywhere else, and the setup command through the injected `ShellRunner`, so a
test can hand in a collaborator that fails where it chooses.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Sequence, TextIO

import development_path
from development_path import ToolError

__version__ = "1.1.0"

class RepositoryRole(str, Enum):
    INSTANCE = "instance"
    PRODUCT = "product"


class ShellRunner:
    """The setup command's way out: a shell command run in a directory. The command's output is
    captured whole, so nothing it prints reaches this command's own stdout, which carries the one
    JSON object. Raises `OSError` when the command cannot be started at all."""

    def run(self, command: str, directory: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(command, shell=True, executable="/bin/sh", cwd=directory,
                              stdin=subprocess.DEVNULL, capture_output=True, text=True)

    def exists(self, path: str) -> bool:
        """Something is at `path` once symlinks are followed, so a broken link is nothing."""
        return os.path.exists(path)


class WorktreeGit(development_path.Git):
    """Every question this command asks git or a repository's own files, and every change it makes.
    Each method raises `OSError` when git or the filesystem cannot answer, so a caller that has to
    report an observation can tell "no" from "could not look"."""

    def run(self, repo: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)

    def _checked(self, repo: str, *args: str) -> str:
        result = self.run(repo, *args)
        if result.returncode != 0:
            raise OSError(f"git {' '.join(args)} exited {result.returncode} in '{repo}': "
                          f"{result.stderr.strip()}")
        return result.stdout.strip()

    def exclude_path(self, repo: str) -> Path:
        """Where the repository's `info/exclude` is, whether or not the file exists."""
        located = Path(self._checked(repo, "rev-parse", "--git-path", "info/exclude"))
        return located if located.is_absolute() else Path(repo) / located

    def head_commit(self, repo: str) -> str | None:
        """The commit `HEAD` names in `repo`, or `None` when it names none (an unborn branch)."""
        result = self.run(repo, "rev-parse", "--verify", "--quiet", "HEAD^{commit}")
        return result.stdout.strip() if result.returncode == 0 else None

    def valid_branch_name(self, repo: str, key: str) -> bool:
        return self.run(repo, "check-ref-format", "--branch", key).returncode == 0

    def branch_exists(self, repo: str, key: str) -> bool:
        result = self.run(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{key}")
        if result.returncode not in (0, 1):
            raise OSError(f"git show-ref exited {result.returncode} in '{repo}': "
                          f"{result.stderr.strip()}")
        return result.returncode == 0

    def conflicting_branch(self, repo: str, key: str) -> str | None:
        """An existing branch whose namespace prevents creating `key`, including packed refs."""
        refs = self._checked(repo, "for-each-ref", "--format=%(refname)", "refs/heads/")
        wanted = f"refs/heads/{key}"
        for ref in refs.splitlines():
            if ref.startswith(wanted + "/") or wanted.startswith(ref + "/"):
                return ref.removeprefix("refs/heads/")
        return None

    def _entries(self, repo: str) -> list[tuple[str, str | None]]:
        """`git worktree list --porcelain` as `(worktree path, branch name or None)` pairs."""
        entries: list[tuple[str, str | None]] = []
        for line in self._checked(repo, "worktree", "list", "--porcelain").splitlines():
            if line.startswith("worktree "):
                entries.append((line[len("worktree "):], None))
            elif line.startswith("branch refs/heads/") and entries:
                entries[-1] = (entries[-1][0], line[len("branch refs/heads/"):])
        return entries

    def _entry(self, repo: str, worktree: str) -> tuple[str, str | None] | None:
        """The listing entry for `worktree`, by the resolved parent plus the name: git prints
        resolved paths, and an entry whose directory is gone cannot be resolved whole."""
        wanted = _identity(worktree)
        return next((entry for entry in self._entries(repo) if _identity(entry[0]) == wanted),
                    None)

    def listed_worktree(self, repo: str, worktree: str) -> str | None:
        """`worktree` as `git worktree list` prints it, or `None` when not registered there."""
        entry = self._entry(repo, worktree)
        return entry[0] if entry else None

    def listed_branch(self, repo: str, worktree: str) -> str | None:
        """The branch `git worktree list` shows checked out in `worktree`."""
        entry = self._entry(repo, worktree)
        return entry[1] if entry else None

    def append_exclude_line(self, repo: str) -> None:
        """Append `.worktrees/` to `info/exclude`, creating the file and its folder when missing
        and starting a new line first when the last one has no newline, so every existing line
        stays as it was."""
        target = self.exclude_path(repo)
        target.parent.mkdir(parents=True, exist_ok=True)
        existing = target.read_bytes() if target.exists() else b""
        separator = b"" if not existing or existing.endswith(b"\n") else b"\n"
        with target.open("ab") as handle:
            handle.write(separator + f"{development_path.WORKTREES_DIR}/\n".encode())

    def add_worktree(self, repo: str, worktree: str, key: str, commit: str) -> None:
        """A new branch `key` at `commit`, checked out in a new worktree at `worktree`."""
        self._checked(repo, "worktree", "add", "-b", key, worktree, commit)

    def occupied(self, path: str) -> bool:
        """Something is at `path` — a directory, a file or a symlink, broken or not."""
        location = Path(path)
        return location.is_symlink() or location.exists()

    def worktrees_dir_blocked(self, repo: str) -> bool:
        """`<repo>/.worktrees` exists and is not a directory."""
        location = Path(repo) / development_path.WORKTREES_DIR
        return (location.is_symlink() or location.exists()) and not location.is_dir()

    def worktree_parent_writable(self, worktree: str) -> bool:
        """The nearest existing parent permits creation of the worktree directory."""
        parent = Path(worktree).parent
        while not parent.exists():
            parent = parent.parent
        return parent.is_dir() and os.access(parent, os.W_OK | os.X_OK)

    def in_commit_tree(self, repo: str, commit: str, directory: Path) -> bool:
        """`directory` is a tree of `commit` in `repo`."""
        if directory == Path("."):
            return True
        result = self.run(repo, "cat-file", "-t", f"{commit}:{directory.as_posix()}")
        return result.returncode == 0 and result.stdout.strip() == "tree"

    def exclude_matches(self, repo: str, key: str) -> bool:
        """Whether a line of `info/exclude` already matches `.worktrees/<key>`, answered by git's
        own matcher with only that file able to speak: an empty work tree, so no tracked
        `.gitignore` is read, and no global excludes file."""
        git_dir = self._checked(repo, "rev-parse", "--absolute-git-dir")
        with tempfile.TemporaryDirectory() as empty:
            result = subprocess.run(
                ["git", "-c", "core.excludesFile=/dev/null", "check-ignore", "--no-index", "-q",
                 f"{development_path.WORKTREES_DIR}/{key}"],
                cwd=empty, env={**os.environ, "GIT_DIR": git_dir, "GIT_WORK_TREE": empty},
                capture_output=True, text=True)
        if result.returncode not in (0, 1):
            raise OSError(f"git check-ignore exited {result.returncode} in '{repo}': "
                          f"{result.stderr.strip()}")
        return result.returncode == 0

    def exclude_writable(self, repo: str) -> bool:
        """The exclude file can be appended to, or created where it is missing."""
        target = self.exclude_path(repo)
        if target.is_dir():
            return False
        if target.exists():
            return os.access(target, os.W_OK)
        ancestor = target.parent
        while not ancestor.exists():
            ancestor = ancestor.parent
        return ancestor.is_dir() and os.access(ancestor, os.W_OK | os.X_OK)

    def snapshot(self, repo: str) -> Snapshot:
        """The three things a run could change in `repo`, read now."""
        exclude = self.exclude_path(repo)
        return Snapshot(branches=self._checked(repo, "branch", "--list"),
                        worktrees=self._checked(repo, "worktree", "list", "--porcelain"),
                        exclude=exclude.read_bytes() if exclude.exists() else None)


def _identity(path: str) -> Path:
    """A path by the resolved directory it sits in plus its own name."""
    location = Path(path)
    return location.parent.resolve() / location.name


@dataclass(frozen=True)
class Snapshot:
    """A repository's branch list, worktree list and `info/exclude` bytes (`None` when the file
    does not exist). Two snapshots differing in any field is what "changed" means."""

    branches: str
    worktrees: str
    exclude: bytes | None


@dataclass(frozen=True)
class Target:
    """One repository of the topology and the change worktree it is to hold."""

    role: RepositoryRole
    repo: str
    worktree: str


@dataclass(frozen=True)
class Topology:
    """The repositories a run touches, instance first, the contract the result must satisfy, the
    directory the product's suite runs in, and the card's setup and test commands (each `None`
    when the card declares none)."""

    contract: development_path.Contract
    targets: tuple[Target, ...]
    product_directory: str
    setup: str | None
    test: str | None


@dataclass(frozen=True)
class Plan:
    """What preflight settled for one repository: the commit the branch is cut from, and whether
    the exclude file needs the line appended."""

    target: Target
    commit: str
    append_exclude: bool


class Attempt:
    """What a run knows when it stops: the topology once it is resolved, and the snapshot taken
    of each repository before anything was checked or changed."""

    def __init__(self) -> None:
        self.topology: Topology | None = None
        self.before: dict[str, Snapshot] = {}


# --- resolve ------------------------------------------------------------------------------------

SETUP_COMMAND_FIELD = "**Setup command:**"
TEST_COMMAND_FIELD = "**Test command:**"
NO_COMMAND = "none"


def _card_command(card: str, field: str) -> str | None:
    """The value of the first line of the card starting with `field`, trailing HTML comments
    removed, or `None` when there is no such line, its value is empty, or it is `none`."""
    for line in card.splitlines():
        if line.startswith(field):
            value = development_path._strip_trailing_comments(line[len(field):])
            return None if value in ("", NO_COMMAND) else value
    return None



def _checked_argument(check: Callable[[str], str], value: str, code: str) -> str:
    """`value` through one of the path tool's argument validators, its refusal as a `ToolError` so
    the caller gets a JSON report rather than argparse's usage message."""
    try:
        return check(value)
    except argparse.ArgumentTypeError as error:
        raise ToolError(code, f"{error}") from None


def resolve_topology(instance_path: str, project: str, key: str, git: WorktreeGit,
                     home: str) -> Topology:
    """The repositories a run touches and the contract they must satisfy, resolved against the
    instance's main working tree — the change's worktree does not exist yet, and the path tool
    refuses a missing one — and then rebuilt for the worktree this command is about to make."""
    project = _checked_argument(development_path._project_name, project, "invalid-project-name")
    key = _checked_argument(development_path._change_key, key, "invalid-change-key")
    instance_repo = git.main_worktree(instance_path)
    if instance_repo is None:
        raise ToolError("instance-repo-unresolved",
                        f"--instance '{instance_path}' is not inside a git repository; pass any "
                        f"path inside the instance repository")
    card = development_path._read_project_doc(instance_repo, project)
    resolved = development_path.resolve(
        card, instance_repo, project, key, development_path.GitRepos(git), home)
    instance_worktree = str(Path(instance_repo) / development_path.WORKTREES_DIR / key)
    relative = resolved["kind"] == development_path.RELATIVE
    contract = development_path.build_contract(
        kind=resolved["kind"], project=project, key=key, product_path=resolved["product_path"],
        instance_repo=resolved["instance_repo"], instance_worktree=instance_worktree,
        product_repo=resolved["product_repo"],
        product_worktree=instance_worktree if relative else resolved["product_worktree"])
    targets = [Target(RepositoryRole.INSTANCE, contract["instance_repo"],
                      contract["instance_worktree"])]
    if not relative:
        targets.append(Target(RepositoryRole.PRODUCT, contract["product_repo"],
                              contract["product_worktree"]))
    product_directory = Path(contract["product_worktree"]) / _product_directory(
        contract, contract["product_repo"])
    return Topology(contract=contract, targets=tuple(targets),
                    product_directory=str(product_directory),
                    setup=_card_command(card, SETUP_COMMAND_FIELD),
                    test=_card_command(card, TEST_COMMAND_FIELD))


# --- preflight ----------------------------------------------------------------------------------


def _product_directory(contract: development_path.Contract, repo: str) -> Path:
    """The in-repo product's directory, relative to the repository root."""
    declared = Path(contract["product_path"])
    if not declared.is_absolute():
        return declared
    try:
        return declared.resolve().relative_to(Path(repo).resolve())
    except ValueError:
        return declared


def _preflight_repo(topology: Topology, target: Target, git: WorktreeGit) -> Plan:
    """The checks for one repository, none of which changes anything; the first failure raises."""
    key, where = topology.contract["key"], f"the {target.role.value} repository '{target.repo}'"
    commit = git.head_commit(target.repo)
    if commit is None:
        raise ToolError("head-unborn",
                        f"HEAD of {where} names no commit, so there is nothing to cut the branch "
                        f"from; make a first commit there, then run again")
    if not git.valid_branch_name(target.repo, key):
        raise ToolError("invalid-branch-name",
                        f"change key '{key}' is not a branch name git accepts, so {where} cannot "
                        f"hold branch '{key}'; pass the change's own key")
    if git.branch_exists(target.repo, key):
        raise ToolError("branch-exists",
                        f"branch '{key}' already exists in {where}; this command never reuses "
                        f"one — delete the branch, or pass a different key")
    conflicting = git.conflicting_branch(target.repo, key)
    if conflicting is not None:
        raise ToolError("branch-exists",
                        f"branch '{conflicting}' in {where} conflicts with the namespace for "
                        f"'{key}'; move that branch, or pass a different key")
    if git.occupied(target.worktree) or git.listed_worktree(target.repo, target.worktree):
        raise ToolError("worktree-exists",
                        f"a worktree path '{target.worktree}' is already taken in {where}, by "
                        f"something at the path or by a registered worktree; this command never "
                        f"reuses one — remove it (git worktree prune for a registered one whose "
                        f"directory is gone), or pass a different key")
    if git.worktrees_dir_blocked(target.repo):
        raise ToolError("worktrees-dir-blocked",
                        f"'{Path(target.repo) / development_path.WORKTREES_DIR}' in {where} exists "
                        f"and is not a directory; remove or move it, then run again")
    if not git.worktree_parent_writable(target.worktree):
        raise ToolError("worktrees-dir-blocked",
                        f"the parent of '{target.worktree}' in {where} cannot hold a new "
                        f"directory; make its existing parent writable and searchable, "
                        f"then run again")
    append = not git.exclude_matches(target.repo, key)
    if append and not git.exclude_writable(target.repo):
        raise ToolError("exclude-unwritable",
                        f"'{git.exclude_path(target.repo)}' in {where} cannot be written or "
                        f"created, and it needs the line '{development_path.WORKTREES_DIR}/'; "
                        f"make it writable, then run again")
    if topology.contract["kind"] == development_path.RELATIVE:
        directory = _product_directory(topology.contract, target.repo)
        if not git.in_commit_tree(target.repo, commit, directory):
            raise ToolError("product-path-not-at-head",
                            f"the product directory '{directory}' is not a directory of HEAD "
                            f"({commit}) in {where}, so a worktree cut from it would not hold the "
                            f"product; commit it there, or fix **Product path:** in project.md")
    return Plan(target=target, commit=commit, append_exclude=append)


def preflight(topology: Topology, git: WorktreeGit) -> tuple[Plan, ...]:
    """Every repository's checks, instance first, stopping at the first failure. Nothing is changed,
    so a refusal anywhere leaves every repository of the topology as it was."""
    return tuple(_preflight_repo(topology, target, git) for target in topology.targets)


# --- create and confirm ------------------------------------------------------------------------


def create(topology: Topology, plans: tuple[Plan, ...], git: WorktreeGit) -> None:
    """In each repository, instance first: the exclude line when preflight said one is needed, then
    the branch and worktree at the commit preflight captured — never at the literal `HEAD`, which
    may have moved. Nothing made here is removed, reset or reused when a later step fails."""
    for plan in plans:
        target, key = plan.target, topology.contract["key"]
        where = f"the {target.role.value} repository '{target.repo}'"
        if plan.append_exclude:
            try:
                git.append_exclude_line(target.repo)
            except OSError as error:
                raise ToolError("exclude-write-failed",
                                f"could not append '{development_path.WORKTREES_DIR}/' to the "
                                f"exclude file of {where}: {error}; fix the file's permissions or "
                                f"space, then run again") from None
        try:
            git.add_worktree(target.repo, target.worktree, key, plan.commit)
        except OSError as error:
            raise ToolError("worktree-add-failed",
                            f"git could not add worktree '{target.worktree}' on a new branch "
                            f"'{key}' in {where}: {error}; read the report for what exists, "
                            f"remove what you do not want, then run again") from None


def success_report(topology: Topology, git: WorktreeGit) -> dict[str, object]:
    """What a successful run prints: for each repository, the identities `git worktree list` and
    `git branch` give now — read back, because git prints resolved paths and a computed one can
    differ from them in text."""
    contract = topology.contract
    repos = []
    for target in topology.targets:
        worktree = git.listed_worktree(target.repo, target.worktree)
        branch = git.listed_branch(target.repo, target.worktree)
        main = git.main_worktree(target.repo)
        if worktree is None or branch != contract["key"] or main is None:
            raise ToolError("worktree-add-failed",
                            f"git does not list '{target.worktree}' on branch '{contract['key']}' "
                            f"in the {target.role.value} repository '{target.repo}' after "
                            f"creating it; inspect it with git worktree list")
        repos.append({"role": target.role, "repo": main, "branch": branch, "worktree": worktree})
    return {"status": "created", "project": contract["project"], "key": contract["key"],
            "kind": contract["kind"], "repos": repos}


# --- setup --------------------------------------------------------------------------------------

OUTPUT_TAIL_LINES = 10


def _tail(text: str) -> str:
    return "\n".join(text.rstrip().splitlines()[-OUTPUT_TAIL_LINES:])


def _setup_output_note(result: subprocess.CompletedProcess[str]) -> str:
    """What the failed setup wrote, as the line that follows the refusal's opening."""
    if result.stderr.strip():
        return f"last lines of its error output:\n{_tail(result.stderr)}"
    if result.stdout.strip():
        return ("it wrote no error output; last lines of its standard output:\n"
                f"{_tail(result.stdout)}")
    return "it wrote no output"


def run_setup(topology: Topology, runner: ShellRunner) -> None:
    """The card's setup command, once, in the product directory. A card declaring none runs
    nothing. A command that exits non-zero, is stopped by a signal or cannot be started is
    `setup-failed`; nothing the run made is removed."""
    command, directory = topology.setup, topology.product_directory
    if command is None:
        return
    remedy = (f"fix {SETUP_COMMAND_FIELD} in project.md or the environment it needs, remove the "
              f"branch '{topology.contract['key']}' and its worktree from every repository this "
              f"report lists, then run again")
    try:
        result = runner.run(command, directory)
    except OSError as error:
        raise ToolError("setup-failed",
                        f"the setup command '{command}' could not be started in '{directory}': "
                        f"{error}; {remedy}") from None
    if result.returncode == 0:
        return
    if result.returncode > 0:
        stopped = f"exited with status {result.returncode}"
    else:
        stopped = f"was stopped by signal {-result.returncode}"
    raise ToolError("setup-failed",
                    f"the setup command '{command}' {stopped} in '{directory}'; {remedy}\n"
                    f"{_setup_output_note(result)}")


# --- check --------------------------------------------------------------------------------------

_ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")


def _relative_interpreter(test_command: str) -> str | None:
    """The first shell word of `test_command` after any leading `NAME=value` words, when it is a
    relative path (it holds a `/`, is not absolute and does not start with `~`); `None` for
    anything else, including a command that cannot be split into shell words."""
    try:
        words = shlex.split(test_command)
    except ValueError:
        return None
    interpreter = next((word for word in words if not _ASSIGNMENT.match(word)), None)
    if interpreter is None or "/" not in interpreter:
        return None
    if interpreter.startswith(("/", "~")):
        return None
    return interpreter


def check_interpreter(topology: Topology, runner: ShellRunner) -> None:
    """The card's test command must be able to find its relative interpreter in the product
    directory, where the suite runs. A symlink whose target is gone does not count."""
    interpreter = None if topology.test is None else _relative_interpreter(topology.test)
    if interpreter is None:
        return
    path = os.path.join(topology.product_directory, interpreter)
    if runner.exists(path):
        return
    seen = f"the test command's interpreter '{interpreter}' is not at '{path}' "
    seen += "(a symlink counts only when its target exists)"
    after = ("remove the branch '" + topology.contract["key"] + "' and its worktree from every "
             "repository this report lists, then run again")
    if topology.setup is None:
        raise ToolError("test-interpreter-missing",
                        f"{seen}, and project.md declares no {SETUP_COMMAND_FIELD} to create it; "
                        f"declare one that does or correct {TEST_COMMAND_FIELD} in project.md, "
                        f"{after}")
    raise ToolError("test-interpreter-missing",
                    f"{seen} after the setup command '{topology.setup}' ran; make "
                    f"{SETUP_COMMAND_FIELD} in project.md create it or correct "
                    f"{TEST_COMMAND_FIELD} in project.md, {after}")


# --- the command line ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="create_change_worktree.py",
        description="Create a change's branch and worktree, and the product repository's pair "
                    "for an external product. Prints one JSON object.")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--instance", required=True,
                        help="any path inside the instance repository")
    parser.add_argument("--project", required=True,
                        help="project name under system/projects/<project>/")
    parser.add_argument("--key", required=True,
                        help="change key — the branch and .worktrees/<key> directory name")
    parser.add_argument("--pretty", action="store_true", help="indent the JSON output")
    return parser


def _observed(look: Callable[[], bool]) -> bool | None:
    """The answer `look` gives, or `None` when the looking itself failed."""
    try:
        return look()
    except OSError:
        return None


def _repo_state(git: WorktreeGit, target: Target, key: str) -> dict[str, object]:
    """One repository as it is right now, read from git: never from what the run believes it did.
    A worktree "exists" in CP-203's sense — something at its path, or registered in git's list."""
    try:
        listed, looked = git.listed_worktree(target.repo, target.worktree), True
    except OSError:
        listed, looked = None, False
    if git.occupied(target.worktree) or listed:
        worktree_exists: bool | None = True
    else:
        worktree_exists = False if looked else None
    return {"role": target.role, "repo": target.repo, "worktree": listed or target.worktree,
            "branch_exists": _observed(lambda: git.branch_exists(target.repo, key)),
            "worktree_exists": worktree_exists}


def _changed(git: WorktreeGit, attempt: Attempt) -> bool:
    """Whether any repository differs from its snapshot. A repository that cannot be read again
    cannot be proved unchanged, so it counts as changed."""
    if attempt.topology is None:
        return False
    try:
        return any(git.snapshot(target.repo) != attempt.before[target.role]
                   for target in attempt.topology.targets)
    except (OSError, KeyError):
        return True


def failure_report(args: argparse.Namespace, error: ToolError, git: WorktreeGit,
                   attempt: Attempt) -> dict[str, object]:
    """What a failed run prints. `repos` is `None` while no topology is known, and a run that has
    not resolved one has changed nothing; once one is known, `changed` and every repository's state
    are observed now, never taken from how far the run got."""
    topology = attempt.topology
    repos = None if topology is None else [
        _repo_state(git, target, topology.contract["key"]) for target in topology.targets]
    return {"status": "failed", "error": error.code, "message": error.message,
            "project": args.project, "key": args.key, "changed": _changed(git, attempt),
            "repos": repos}


def _run(args: argparse.Namespace, git: WorktreeGit, runner: ShellRunner, home: str,
         attempt: Attempt) -> dict[str, object]:
    """The six phases, returning the success report."""
    topology = resolve_topology(args.instance, args.project, args.key, git, home)
    attempt.topology = topology
    attempt.before = {target.role: git.snapshot(target.repo) for target in topology.targets}
    create(topology, preflight(topology, git), git)
    development_path.validate_contract(topology.contract, git)
    run_setup(topology, runner)
    check_interpreter(topology, runner)
    return success_report(topology, git)


def main(argv: Sequence[str] | None = None, *, git: WorktreeGit | None = None,
         runner: ShellRunner | None = None, stdout: TextIO | None = None,
         home: str | None = None) -> int:
    """The composition root: the one place a concrete `WorktreeGit` and `ShellRunner` are built,
    and where the home directory a `~/` product path expands against is read from the environment.

    Whatever happens it prints exactly one JSON object and returns `0` or `1`; the broad `except`
    below is that contract, so a caller reading JSON never meets a traceback."""
    git = git if git is not None else WorktreeGit()
    runner = runner if runner is not None else ShellRunner()
    home = home if home is not None else str(Path.home())
    out = stdout if stdout is not None else sys.stdout
    args = build_parser().parse_args(argv)
    attempt = Attempt()
    try:
        report, code = _run(args, git, runner, home, attempt), 0
    except ToolError as error:
        report, code = failure_report(args, error, git, attempt), 1
    except Exception as error:  # noqa: BLE001 — a JSON caller still gets JSON
        report, code = failure_report(args, ToolError(
            "unknown", f"unexpected {type(error).__name__}: {error}; not a failure this command "
                       f"anticipates — report the command line with this message"),
            git, attempt), 1
    print(json.dumps(report, indent=2 if args.pretty else None), file=out)
    return code


if __name__ == "__main__":
    sys.exit(main())
