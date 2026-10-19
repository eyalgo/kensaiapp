#!/usr/bin/env python3
"""Deliver a caller's development-path contract, keeping deletion behind observed landing.

WHY THIS EXISTS
A process exit cannot prove that main holds a merge or that a worktree disappeared. The engine
keeps those observations separate, and receives every process/filesystem collaborator explicitly.
It owns no seal content or recovery policy. The callable contract is in deliver_change.md.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import development_path

__version__ = "1.2.0"


class Role(str, Enum):
    PRODUCT = "product"
    INSTANCE = "instance"

    def __str__(self) -> str:
        return self.value


class State(str, Enum):
    COMPLETE = "complete"
    HALT = "halt"


class Halt(str, Enum):
    PRECONDITION = "deliver-precondition-failed"
    CONFLICT = "merge-conflict"
    HOOK = "merge-hook-failed"
    PARTIAL = "instance-merge-after-product"
    TEARDOWN = "teardown-failed"
    DELIVERY = "delivery-failed"


class DeliveryError(ValueError):
    """An actionable failure; Delivery converts it to a result and main chooses the exit."""

    def __init__(self, code: Halt, cause: str) -> None:
        super().__init__(cause)
        self.code = code


@dataclass(frozen=True)
class Result:
    state: State
    delivered: tuple[Role, ...]
    code: Halt | None = None
    diagnostics: tuple[str, ...] = ()
    empty: tuple[Role, ...] = ()


@dataclass
class Progress:
    delivered: list[Role] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)
    landings: dict[Role, str] = field(default_factory=dict)
    role: str = "contract"
    operation: str = "preflight"


class Files:
    """Filesystem port: caller-owned inputs, canonical paths and private ephemeral evidence."""

    def load(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def canonical(self, path: str | Path) -> Path:
        return Path(path).resolve()

    def exists(self, path: Path) -> bool:
        return path.exists()

    def readable(self, path: Path) -> bool:
        return path.is_file() and os.access(path, os.R_OK)

    def new_trace(self) -> Path:
        descriptor, name = tempfile.mkstemp(prefix="deliver-change-", suffix=".jsonl")
        os.close(descriptor)
        return Path(name)

    def read_trace(self, path: Path) -> list[dict[str, Any]]:
        events = [json.loads(line) for line in path.read_text().splitlines()]
        if any(not isinstance(event, dict) or "event" not in event or
               ("sid" in event and not isinstance(event["sid"], str)) or
               ("child_id" in event and not isinstance(event["child_id"], int))
               for event in events):
            raise ValueError("Trace2 produced no readable EVENT records")
        return events

    def dispose_trace(self, path: Path) -> None:
        path.unlink(missing_ok=True)


class Processes(development_path.Git):
    """Process port: captured literal argv, git observations and non-force cleanup commands."""

    def __init__(self, *, environ: dict[str, str]) -> None:
        self.environ = environ

    def run(self, argv: list[str], *, cwd: Path | None = None,
            trace: Path | None = None) -> subprocess.CompletedProcess[str]:
        environment = dict(self.environ)
        if trace is not None:
            # A fresh root sid is needed to exclude nested hook commands. Git's EVENT protocol:
            # https://git-scm.com/docs/api-trace2 (sid, cmd_name, child_start and child_exit).
            for key in tuple(environment):
                if key.startswith("GIT_TRACE2"):
                    del environment[key]
            environment["GIT_TRACE2_EVENT"] = str(trace)
        return subprocess.run(argv, cwd=cwd, env=environment, capture_output=True, text=True)

    def git(self, repo: Path, *args: str, trace: Path | None = None) -> str:
        result = self.run(["git", "-C", str(repo), *args], trace=trace)
        if result.returncode:
            raise OSError(
                f"git {' '.join(args)} exited {result.returncode}: {result.stderr.strip()}"
            )
        return result.stdout.strip()

    def _ask(self, path: str, *args: str) -> str | None:
        result = self.run(["git", "-C", path, *args])
        return result.stdout.strip() if result.returncode == 0 else None

    def executable(self, name: str, cwd: Path) -> bool:
        if "/" in name:
            location = Path(name)
            if not location.is_absolute():
                location = cwd / location
            return location.is_file() and os.access(location, os.X_OK)
        return shutil.which(name, path=self.environ.get("PATH")) is not None

    def valid_branch(self, key: str) -> bool:
        result = self.run(["git", "check-ref-format", "--branch", key])
        return result.returncode == 0 and key != "main" and not key.startswith("-")

    def registrations(self, repo: Path) -> list[Path]:
        return [Path(line[9:]).resolve() for line in self.git(
            repo, "worktree", "list", "--porcelain",
        ).splitlines() if line.startswith("worktree ")]

    def merge_head(self, repo: Path) -> bool:
        result = self.run(["git", "-C", str(repo), "rev-parse", "-q", "--verify", "MERGE_HEAD"])
        if result.returncode not in (0, 1):
            raise OSError(f"cannot read MERGE_HEAD: {result.stderr.strip()}")
        return result.returncode == 0

    def ancestor(self, repo: Path, first: str, second: str) -> bool:
        result = self.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", first, second])
        if result.returncode not in (0, 1):
            raise OSError(f"cannot read ancestry: {result.stderr.strip()}")
        return result.returncode == 0

    def builder(self, builder: Path, repo: Path, key: str, metadata: dict[str, Any], *,
                check_only: bool, trace: Path | None = None) -> subprocess.CompletedProcess[str]:
        argv = [sys.executable, str(builder), "--repo", str(repo), "merge", "--branch", key,
                "--target-branch", "main"]
        for name, value in metadata.items():
            flag = "--" + name.replace("_", "-")
            if isinstance(value, list):
                argv.extend([flag, *value])
            else:
                argv.extend([flag, value])
        if check_only:
            argv.append("--check-only")
        return self.run(argv, trace=trace)

    def seal(self, argv: list[str], worktree: Path) -> subprocess.CompletedProcess[str]:
        return self.run(argv, cwd=worktree)

    def remove_worktree(self, repo: Path, worktree: Path) -> subprocess.CompletedProcess[str]:
        # No --force: https://git-scm.com/docs/git-worktree#_commands
        return self.run(["git", "-C", str(repo), "worktree", "remove", str(worktree)])

    def delete_branch(self, repo: Path, key: str) -> subprocess.CompletedProcess[str]:
        return self.run(["git", "-C", str(repo), "branch", "-d", key])

    def status_entries(self, repo: Path) -> str:
        """The checkout's raw NUL-separated porcelain, unstripped: a first ` M path` keeps its
        leading space, which is what tells an unstaged edit from a staged one."""
        result = self.run(["git", "-C", str(repo), "status", "--porcelain=v1", "-z",
                           "--untracked-files=all"])
        if result.returncode:
            raise OSError(f"cannot read checkout status: {result.stderr.strip()}")
        return result.stdout

    def branch_paths(self, repo: Path, key: str) -> str:
        """Raw NUL-separated paths the branch changed since it left main, both sides of a move."""
        result = self.run(["git", "-C", str(repo), "diff", "--name-only", "--no-renames", "-z",
                           f"main...{key}"])
        if result.returncode:
            raise OSError(f"cannot read branch paths: {result.stderr.strip()}")
        return result.stdout

    def reflog(self, repo: Path, key: str) -> list[tuple[str, str]]:
        """The branch's own reflog, newest first, as (commit sha, message) pairs.

        Empty output is a missing reflog: https://git-scm.com/docs/git-reflog
        """
        result = self.run(["git", "-C", str(repo), "reflog", "show", "--format=%H%x09%gs",
                           f"refs/heads/{key}"])
        if result.returncode:
            raise OSError(f"cannot read branch reflog: {result.stderr.strip()}")
        return [tuple(line.split("\t", 1)) for line in result.stdout.splitlines() if line]

    def branch_exists(self, repo: Path, key: str) -> bool:
        result = self.run(["git", "-C", str(repo), "show-ref", "--verify", "--quiet",
                           f"refs/heads/{key}"])
        if result.returncode not in (0, 1):
            raise OSError(f"cannot read change ref: {result.stderr.strip()}")
        return result.returncode == 0


_CONTRACT_FIELDS = set(development_path.Contract.__annotations__)
_PATH_FIELDS = ("instance_repo", "instance_worktree", "product_repo", "product_worktree",
                "code_repo", "code_worktree", "pipeline_repo", "pipeline_worktree")
_REQUIRED_MERGE_FIELDS = {"description", "merge_context", "surface"}
_LIST_MERGE_FIELDS = {"branch_commits", "bump"}
_OPTIONAL_MERGE_FIELDS = {"actor", "authorizer", "co_authored_by", "reasoning_effort",
                          "claude_session", *_LIST_MERGE_FIELDS}
_BLOCKING_HOOKS = {"pre-merge-commit", "prepare-commit-msg", "commit-msg", "pre-commit"}
_CREATION_MESSAGE = "branch: Created from"


def _require(condition: bool, cause: str) -> None:
    if not condition:
        raise DeliveryError(Halt.PRECONDITION, cause)


def _strings(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(entry, str) for entry in value)


class Cause(str, Enum):
    STAGED = "staged"
    COLLISION = "collides with a path the merge writes"


@dataclass(frozen=True)
class Entry:
    """One porcelain record: its two status columns, its path and a rename/copy source."""
    status: str
    path: str
    source: str | None = None


def parse_entries(raw: str) -> list[Entry]:
    """Read `git status --porcelain=v1 -z` records from unstripped output."""
    fields = raw.split("\0")
    entries, index = [], 0
    while index < len(fields) and fields[index]:
        record = fields[index]
        status, path = record[:2], record[3:]
        index += 1
        source = None
        if "R" in status or "C" in status:
            source = fields[index]
            index += 1
        entries.append(Entry(status, path, source))
    return entries


def _collides(first: str, second: str) -> bool:
    return first == second or first.startswith(second + "/") or second.startswith(first + "/")


def refusing_entries(entries: list[Entry], merge_paths: set[str]) -> list[tuple[Entry, Cause]]:
    """The entries a primary checkout may not hold: staged, or colliding with a merge path."""
    refusing = []
    for entry in entries:
        if entry.status[0] not in " ?":
            refusing.append((entry, Cause.STAGED))
        elif any(_collides(path, written) for path in (entry.path, entry.source) if path
                 for written in merge_paths):
            refusing.append((entry, Cause.COLLISION))
    return refusing


def _describe(entry: Entry, cause: Cause) -> str:
    name = f"{entry.source} -> {entry.path}" if entry.source else entry.path
    return f"`{name}` ({cause.value})"


def blocking_hook(events: list[dict[str, Any]]) -> str | None:
    """Identify rejection only in a root merge/commit session, keyed by sid plus child_id.

    Nested git failure is not the outer hook's verdict; post-merge is non-blocking:
    https://git-scm.com/docs/githooks#_post_merge
    """
    sessions = {e.get("sid") for e in events if e.get("event") == "cmd_name"
                and e.get("name") in ("merge", "commit")
                and isinstance(e.get("sid"), str) and "/" not in e["sid"]}
    children = {(e.get("sid"), e.get("child_id")): e.get("hook_name") for e in events
                if e.get("event") == "child_start" and e.get("sid") in sessions
                and e.get("child_class") == "hook" and e.get("hook_name") in _BLOCKING_HOOKS}
    for event in events:
        key = (event.get("sid"), event.get("child_id"))
        if event.get("event") == "child_exit" and event.get("code", 0) != 0 and key in children:
            return children[key]
    return None


class Delivery:
    """One invocation, with no stored phase or retry. All world-facing collaborators are given."""

    def __init__(self, *, files: Files, processes: Processes, builder: Path,
                 input_paths: tuple[Path, ...] = ()) -> None:
        self.files = files
        self.processes = processes
        self.builder_path = builder
        self.input_paths = input_paths

    def _contract(self, supplied: Any) -> dict[str, Any]:
        _require(isinstance(supplied, dict) and set(supplied) == _CONTRACT_FIELDS,
                 "contract must carry exactly the complete development-path fields")
        contract = dict(supplied)
        for name in _CONTRACT_FIELDS - {"delivery_repos"}:
            _require(isinstance(contract[name], str) and bool(contract[name].strip()),
                     f"contract field {name} must be a nonempty string")
        _require(contract["kind"] in ("relative", "fixed"), "unsupported contract kind")
        _require(self.processes.valid_branch(contract["key"]),
                 "key must be a legal change branch, not main")
        for name in _PATH_FIELDS:
            _require(Path(contract[name]).is_absolute(), f"contract field {name} must be absolute")
            contract[name] = str(self.files.canonical(contract[name]))
        if Path(contract["product_path"]).is_absolute():
            contract["product_path"] = str(self.files.canonical(contract["product_path"]))
        projected = development_path.build_contract(**{name: contract[name] for name in (
            "kind", "project", "key", "product_path", "instance_repo", "instance_worktree",
            "product_repo", "product_worktree",
        )})
        _require(contract == projected, "inconsistent aliases or unsupported delivery role order")
        same_repo = contract["instance_repo"] == contract["product_repo"]
        if contract["kind"] == "relative":
            _require(same_repo and contract["instance_worktree"] == contract["product_worktree"],
                     "relative requires one repository and one worktree")
        else:
            _require(not same_repo and Path(contract["product_path"]).is_absolute(),
                     "fixed requires distinct repositories and an absolute product path")
        for role in contract["delivery_repos"]:
            _require(contract[f"{role}_repo"] != contract[f"{role}_worktree"],
                     f"{role} change worktree cannot be its primary checkout")
        development_path.validate_contract(contract, self.processes)
        return contract

    def _inputs(self, contract: dict[str, Any], merges: Any, seal: Any) -> None:
        _require(isinstance(merges, dict) and set(merges) == set(contract["delivery_repos"]),
                 "merge entries must match delivery roles exactly")
        for role, request in merges.items():
            _require(isinstance(request, dict), f"{role} merge must be an object")
            _require(_REQUIRED_MERGE_FIELDS <= set(request) and
                     set(request) <= _REQUIRED_MERGE_FIELDS | _OPTIONAL_MERGE_FIELDS,
                     f"{role} merge has missing or unknown fields")
            _require(("actor" in request) != ("authorizer" in request),
                     f"{role} merge requires exactly one actor or authorizer")
            for name, value in request.items():
                _require(_strings(value) if name in _LIST_MERGE_FIELDS else isinstance(value, str),
                         f"{role} merge {name} has the wrong type")
        _require(isinstance(seal, dict) and set(seal) == {"argv"},
                 "seal must carry exactly argv")
        _require(_strings(seal["argv"]) and bool(seal["argv"]) and bool(seal["argv"][0]),
                 "seal argv must be a nonempty string array with an executable")

    def _primary_entries(self, role: Role, repo: Path, key: str, bump: list[str]) -> None:
        """Refuse only what this delivery's own merge cannot carry past; read fresh every call."""
        merge_paths = {path for path in self.processes.branch_paths(repo, key).split("\0") if path}
        merge_paths.update(spec.rsplit("=", 1)[0] for spec in bump)
        refusing = refusing_entries(parse_entries(self.processes.status_entries(repo)),
                                    merge_paths)
        if refusing:
            noun = "uncommitted entries" if len(refusing) > 1 else "an uncommitted entry"
            listed = ", ".join(_describe(entry, cause) for entry, cause in refusing)
            raise DeliveryError(Halt.PRECONDITION, (
                f"{role} primary checkout {repo} holds {noun} this delivery refuses: {listed}"))

    def _live(self, contract: dict[str, Any], role: Role,
              bump: list[str] | None = None) -> tuple[Path, Path]:
        repo, worktree = Path(contract[f"{role}_repo"]), Path(contract[f"{role}_worktree"])
        for path, branch in ((repo, "main"), (worktree, contract["key"])):
            _require(self.processes.toplevel(str(path)) == str(path), f"{role} not a root: {path}")
            _require(self.processes.main_worktree(str(path)) == str(repo),
                     f"{role} foreign repository: {path}")
            _require(path in self.processes.registrations(repo), f"{role} unregistered: {path}")
            _require(self.processes.branch(str(path)) == branch,
                     f"{role} {path} must be on {branch}")
            _require(not self.processes.merge_head(path), f"{role} {path} MERGE_HEAD=present")
            if path == repo:
                self._primary_entries(role, repo, contract["key"], bump or [])
            else:
                _require(not self.processes.git(
                    path, "status", "--porcelain", "--untracked-files=all"),
                    f"{role} dirty checkout: {path}")
        return repo, worktree

    def _empty_branch(self, repo: Path, key: str) -> bool:
        """A contained branch is empty when its reflog is exactly its creation, at its tip."""
        entries = self.processes.reflog(repo, key)
        return (len(entries) == 1 and entries[0][1].startswith(_CREATION_MESSAGE)
                and entries[0][0] == self.processes.git(repo, "rev-parse", key))

    def _check(self, contract: dict[str, Any], merges: dict[str, Any], role: Role,
               progress: Progress) -> None:
        progress.role, progress.operation = role.value, "builder check-only"
        result = self.processes.builder(
            self.builder_path, Path(contract[f"{role}_repo"]), contract["key"],
            merges[role], check_only=True,
        )
        self._capture(result, progress)
        _require(result.returncode == 0, f"builder check exited {result.returncode}")

    def _trace_preflight(self, repo: Path) -> None:
        trace = self.files.new_trace()
        try:
            self.processes.git(repo, "rev-parse", "HEAD", trace=trace)
            events = self.files.read_trace(trace)
            _require(any(e.get("event") == "cmd_name" for e in events),
                     "Trace2 produced no readable EVENT records")
        finally:
            self.files.dispose_trace(trace)

    def _capture(self, result: subprocess.CompletedProcess[str], progress: Progress) -> None:
        for output in (result.stdout, result.stderr):
            if output:
                progress.diagnostics.append(output.rstrip())

    def _halt(self, error: DeliveryError, progress: Progress, contract: dict[str, Any]) -> Result:
        code = error.code
        diagnostic = f"{progress.role}: {progress.operation}: {code.value}: {error}"
        if code != Halt.TEARDOWN and Role.PRODUCT in progress.delivered \
                and Role.INSTANCE not in progress.delivered:
            code = Halt.PARTIAL
            diagnostic += (f"; product merge {progress.landings[Role.PRODUCT]} retained on main; "
                           f"instance unlanded; retained worktree {contract['instance_worktree']}")
        return Result(State.HALT, tuple(progress.delivered), code,
                      (*progress.diagnostics, diagnostic))

    def _seal(self, contract: dict[str, Any], seal: dict[str, Any], progress: Progress) -> None:
        progress.role, progress.operation = "instance", "seal"
        worktree = Path(contract["instance_worktree"])
        before = self.processes.git(worktree, "rev-parse", "HEAD")
        try:
            result = self.processes.seal(seal["argv"], worktree)
            self._capture(result, progress)
            if result.returncode:
                raise ValueError(f"action exited {result.returncode}")
            self._live_change(contract, Role.INSTANCE)
            after = self.processes.git(worktree, "rev-parse", "HEAD")
            if before == after:
                raise ValueError("action created no new commit")
            if not self.processes.ancestor(worktree, before, after):
                raise ValueError("new commit rewrote rather than extended the recorded tip")
        except (OSError, ValueError) as error:
            raise DeliveryError(Halt.DELIVERY, f"seal-failed: {error}") from error

    def _live_change(self, contract: dict[str, Any], role: Role) -> None:
        repo, worktree = Path(contract[f"{role}_repo"]), Path(contract[f"{role}_worktree"])
        _require(self.processes.toplevel(str(worktree)) == str(worktree),
                 f"{role} change worktree is missing or not a root: {worktree}")
        _require(self.processes.main_worktree(str(worktree)) == str(repo),
                 f"{role} change worktree ownership changed: {worktree}")
        _require(worktree in self.processes.registrations(repo),
                 f"{role} change worktree is unregistered: {worktree}")
        _require(self.processes.branch(str(worktree)) == contract["key"],
                 f"{role} change worktree switched branch: {worktree}")
        _require(not self.processes.merge_head(worktree), f"{role} MERGE_HEAD=present")
        _require(not self.processes.git(worktree, "status", "--porcelain", "--untracked-files=all"),
                 f"{role} change worktree has leftover edits: {worktree}")

    def _merge(self, contract: dict[str, Any], merges: dict[str, Any], role: Role,
               progress: Progress) -> None:
        progress.role, progress.operation = role.value, "merge preflight"
        repo, _ = self._live(contract, role, merges[role].get("bump"))
        _require(not self.processes.ancestor(repo, contract["key"], "main"),
                 "change branch is already contained in main")
        self._check(contract, merges, role, progress)
        progress.operation = "builder merge and landing evidence"
        before = self.processes.git(repo, "rev-parse", "main")
        intended = self.processes.git(repo, "rev-parse", contract["key"])
        trace = self.files.new_trace()
        try:
            execution_error = None
            result = None
            try:
                result = self.processes.builder(
                    self.builder_path, repo, contract["key"], merges[role],
                    check_only=False, trace=trace,
                )
                self._capture(result, progress)
            except (OSError, ValueError) as error:
                execution_error = error
            observed = self.processes.git(repo, "rev-parse", "main")
            parents = self.processes.git(repo, "show", "-s", "--format=%P", "main").split()
            merge_in_progress = self.processes.merge_head(repo)
            landed = observed != before and parents == [before, intended] and not merge_in_progress
            if landed:
                delivered_role = Role(role)
                progress.delivered.append(delivered_role)
                progress.landings[delivered_role] = observed
            merge_state = "present" if merge_in_progress else "absent"
            try:
                events = self.files.read_trace(trace)
            except (OSError, ValueError) as error:
                raise DeliveryError(Halt.DELIVERY,
                                    f"merge evidence unreadable: {error}; MERGE_HEAD={merge_state}")
            if execution_error is not None:
                raise DeliveryError(Halt.DELIVERY,
                                    f"process launch: {execution_error}; MERGE_HEAD={merge_state}")
            if result.returncode == 0 and landed:
                return
            if landed:
                raise DeliveryError(Halt.DELIVERY,
                                    f"process exited {result.returncode} after verified merge "
                                    f"{observed}; MERGE_HEAD={merge_state}; recovery retained")
            cause = (f"exit {result.returncode}, ordered merge parents unproved; "
                     f"MERGE_HEAD={merge_state}")
            if self.processes.git(repo, "ls-files", "-u"):
                raise DeliveryError(Halt.CONFLICT, cause)
            hook = blocking_hook(events)
            if hook is not None:
                raise DeliveryError(Halt.HOOK, f"blocking hook {hook} rejected; {cause}")
            if result.returncode and result.stderr.startswith("commit_builder:"):
                raise DeliveryError(Halt.PRECONDITION, f"builder refusal: {result.stderr}; {cause}")
            raise DeliveryError(Halt.DELIVERY, cause)
        finally:
            self.files.dispose_trace(trace)

    def _survivors(self, repo: Path, worktree: Path, key: str) -> list[str]:
        survivors = []
        try:
            if self.files.exists(worktree):
                survivors.append(f"disk {worktree}")
        except OSError as error:
            survivors.append(f"disk evidence unavailable: {error}")
        try:
            if worktree in self.processes.registrations(repo):
                survivors.append(f"registration {worktree}")
        except OSError as error:
            survivors.append(f"registration evidence unavailable: {error}")
        try:
            if self.processes.branch_exists(repo, key):
                survivors.append(f"branch {key}")
        except OSError as error:
            survivors.append(f"branch evidence unavailable: {error}")
        return survivors

    def _cleanup(self, contract: dict[str, Any], merges: dict[str, Any], role: Role,
                 progress: Progress) -> None:
        progress.role, progress.operation = role.value, "verified teardown"
        repo, worktree = Path(contract[f"{role}_repo"]), Path(contract[f"{role}_worktree"])
        try:
            self._live(contract, role, merges[role].get("bump"))
            # _live refused tracked and untracked edits in the change worktree. Ignored content,
            # such as a suite's caches, goes with the worktree, as non-force removal takes it:
            # https://git-scm.com/docs/git-worktree#_commands
            removal = self.processes.remove_worktree(repo, worktree)
            self._capture(removal, progress)
            if removal.returncode:
                raise ValueError(f"worktree remove exited {removal.returncode}")
            if self.files.exists(worktree) or worktree in self.processes.registrations(repo):
                raise ValueError("worktree removal reported success but disk/registration survives")
            deletion = self.processes.delete_branch(repo, contract["key"])
            self._capture(deletion, progress)
            if deletion.returncode:
                raise ValueError(f"safe branch deletion exited {deletion.returncode}")
            survivors = self._survivors(repo, worktree, contract["key"])
            if survivors:
                raise ValueError("cleanup remains incomplete")
        except (OSError, ValueError) as error:
            survivors = self._survivors(repo, worktree, contract["key"])
            raise DeliveryError(Halt.TEARDOWN,
                                f"{error}; remaining: {', '.join(survivors) or 'none observed'}")

    def deliver(self, contract: Any, merges: Any, seal: Any) -> Result:
        """Validate inputs/targets, deliver product, seal once, deliver instance and clean up."""
        progress = Progress()
        empty: list[Role] = []
        contract = contract if isinstance(contract, dict) else {}
        try:
            contract = self._contract(contract)
            self._inputs(contract, merges, seal)
            for path in self.input_paths:
                _require(not any(path.is_relative_to(Path(contract[f"{role}_worktree"]))
                                 for role in contract["delivery_repos"]),
                         f"caller input {path} lies inside a worktree scheduled for teardown")
            if contract["kind"] == "fixed":
                _require(not self.builder_path.is_relative_to(Path(contract["product_worktree"])),
                         "builder lies inside product worktree removed before instance delivery")
            _require(self.files.readable(self.builder_path),
                     f"unreachable builder {self.builder_path}")
            _require(
                self.processes.executable(seal["argv"][0], Path(contract["instance_worktree"])),
                f"unreachable seal executable {seal['argv'][0]}",
            )
            self._trace_preflight(Path(contract["instance_repo"]))
            for role_name in contract["delivery_repos"]:
                role = Role(role_name)
                progress.role, progress.operation = role.value, "live preflight"
                repo, _ = self._live(contract, role, merges[role].get("bump"))
                if self.processes.ancestor(repo, contract["key"], "main"):
                    _require(role == Role.PRODUCT and contract["kind"] == "fixed"
                             and self._empty_branch(repo, contract["key"]),
                             f"{role} change branch is already contained in main")
                    empty.append(role)
                    continue
                self._check(contract, merges, role, progress)
        except (DeliveryError, development_path.ToolError, OSError, ValueError) as error:
            cause = error.message if isinstance(error, development_path.ToolError) else str(error)
            return self._halt(DeliveryError(Halt.PRECONDITION, cause), progress, contract)
        try:
            if contract["kind"] == "fixed":
                if Role.PRODUCT not in empty:
                    self._merge(contract, merges, Role.PRODUCT, progress)
                self._cleanup(contract, merges, Role.PRODUCT, progress)
            self._seal(contract, seal, progress)
            self._merge(contract, merges, Role.INSTANCE, progress)
            self._cleanup(contract, merges, Role.INSTANCE, progress)
            return Result(State.COMPLETE, tuple(progress.delivered),
                          diagnostics=tuple(progress.diagnostics), empty=tuple(empty))
        except DeliveryError as error:
            return self._halt(error, progress, contract)
        except (OSError, ValueError) as error:
            return self._halt(DeliveryError(Halt.DELIVERY, str(error)), progress, contract)


def build_delivery(builder: Path, input_paths: tuple[Path, ...]) -> Delivery:
    """The composition root: the only construction of concrete filesystem/process collaborators."""
    return Delivery(files=Files(), processes=Processes(environ=dict(os.environ)),
                    builder=builder, input_paths=input_paths)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--merges", required=True)
    parser.add_argument("--seal-action", required=True)
    parser.add_argument("--builder", default=str(Path(__file__).with_name("commit_builder.py")))
    args = parser.parse_args(argv)
    input_paths = tuple(Path(path).resolve() for path in
                        (args.contract, args.merges, args.seal_action))
    delivery = build_delivery(Path(args.builder).resolve(), input_paths)
    try:
        inputs = [delivery.files.load(path) for path in input_paths]
        result = delivery.deliver(*inputs)
    except (OSError, ValueError) as error:
        result = Result(State.HALT, (), Halt.PRECONDITION, (f"contract: input loading: {error}",))
    print(f"delivery: {result.state.value}")
    if result.code is not None:
        print(f"halt: {result.code.value}")
    print("delivered: " + (",".join(role.value for role in result.delivered) or "none"))
    for role in result.empty:
        print(f"empty: {role.value}")
    print("cleanup: " + ("complete" if result.state == State.COMPLETE else "incomplete"))
    for diagnostic in result.diagnostics:
        print(diagnostic, file=sys.stderr)
    return 0 if result.state == State.COMPLETE else 1


if __name__ == "__main__":
    sys.exit(main())
