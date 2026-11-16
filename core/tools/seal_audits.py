#!/usr/bin/env python3
"""The seal's audit join, as a tool rather than a thing a model remembers to do.

WHY THIS EXISTS: `tobiishi-seal` was meant to merge every `<key>__audit-<step>` branch into the
change branch before delivery, so the sealed folder holds `flow_findings/`, and to remove those
branches and their worktrees once delivery was proved. It left both to the model following prose,
and three sealed changes got neither, each differently: one never ran the join and then glob-fed
its removal; one never ran it and stopped after delivery; one found the branches before delivery
and merged none of them. This tool makes the join one call that cannot be skipped by a run that
reaches delivery, and the removal one call that acts only on what the join reported and only on
proved delivery.

The skill still decides when each call runs. The tool commits no seal, never runs
`deliver_change.py` and never merges into `main`.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn, TextIO

__version__ = "1.0.0"

JOIN_FAILED = "deliver-precondition-failed"
MERGE_CONFLICT = "merge-conflict"
MERGE_HOOK_FAILED = "merge-hook-failed"
TEARDOWN_FAILED = "teardown-failed"

AUDIT_INFIX = "__audit-"
HEADS = "refs/heads/"


class SealAuditsError(Exception):
    """A refusal, carrying the halt code the skill reports. `main` converts it to an exit."""

    def __init__(self, code: str, reason: str) -> None:
        super().__init__(f"{code}: {reason}")
        self.code = code
        self.reason = reason


class Processes:
    """Starts a command and returns what it did."""

    def run(self, argv: list[str], *, cwd: Path | str | None) -> subprocess.CompletedProcess:
        return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                              errors="surrogateescape", check=False)


class Files:
    """Reads text files and asks whether a directory exists."""

    def read_text(self, path: Path) -> str:
        return Path(path).read_text(encoding="utf-8")

    def is_dir(self, path: Path) -> bool:
        return Path(path).is_dir()


@dataclass(frozen=True)
class Attribution:
    """The identity the builder records on each merge; an optional value left out is not passed."""

    actor: str
    surface: str
    co_authored_by: str | None = None
    reasoning_effort: str | None = None
    claude_session: str | None = None

    def builder_arguments(self) -> list[str]:
        arguments = ["--actor", self.actor, "--surface", self.surface]
        for flag, value in (("--co-authored-by", self.co_authored_by),
                            ("--reasoning-effort", self.reasoning_effort),
                            ("--claude-session", self.claude_session)):
            if value is not None:
                arguments += [flag, value]
        return arguments


def audit_prefix(key: str) -> str:
    return f"{key}{AUDIT_INFIX}"


class AuditSeal:
    """The join. Everything it reaches is handed to it; it constructs nothing."""

    def __init__(self, *, processes: Processes, files: Files, python: str) -> None:
        self._processes = processes
        self._files = files
        self._python = python

    def join(self, *, worktree: Path, key: str, builder: Path,
             attribution: Attribution) -> list[str]:
        """Merge each `<key>__audit-…` branch into `<key>`; return the joined branches in order."""
        self._check_preconditions(worktree, key)
        joined = []
        for branch in self._audit_branches(worktree, key):
            if not self._is_ancestor(worktree, branch, key):
                self._merge(worktree, key, builder, attribution, branch)
                if not self._is_ancestor(worktree, branch, key):
                    raise SealAuditsError(
                        JOIN_FAILED, f"{branch}: merged, yet not an ancestor of {key}")
            joined.append(branch)
        return joined

    def _git(self, repo: Path, *args: str) -> subprocess.CompletedProcess:
        return self._processes.run(["git", "-C", str(repo), *args], cwd=None)

    def _answer(self, code: str, repo: Path, *args: str) -> str:
        result = self._git(repo, *args)
        if result.returncode:
            raise SealAuditsError(
                code, f"{repo}: git {' '.join(args)} would not answer: {result.stderr.strip()}")
        return result.stdout

    def _merge_in_progress(self, worktree: Path) -> bool:
        result = self._git(worktree, "rev-parse", "-q", "--verify", "MERGE_HEAD")
        if result.returncode not in (0, 1):
            raise SealAuditsError(JOIN_FAILED, f"{worktree}: cannot tell whether a merge is "
                                  f"in progress: {result.stderr.strip()}")
        return result.returncode == 0

    def _check_preconditions(self, worktree: Path, key: str) -> None:
        if not self._files.is_dir(worktree):
            raise SealAuditsError(JOIN_FAILED, f"{worktree}: no such change worktree")
        if key == "main":
            raise SealAuditsError(JOIN_FAILED, "the change key is main, which is never a target")
        head = self._answer(JOIN_FAILED, worktree, "symbolic-ref", "--quiet", "HEAD").strip()
        if head != f"{HEADS}{key}":
            raise SealAuditsError(JOIN_FAILED, f"{worktree}: HEAD is {head!r}, not {HEADS}{key}")
        if self._merge_in_progress(worktree):
            raise SealAuditsError(JOIN_FAILED, f"{worktree}: a merge is already in progress")

    def _audit_branches(self, worktree: Path, key: str) -> list[str]:
        # A plain prefix test, never a git pattern: `*` would also take the bare prefix, and a
        # key holding glob characters would widen the set.
        prefix = f"{HEADS}{audit_prefix(key)}"
        refs = self._answer(JOIN_FAILED, worktree, "for-each-ref", "--format=%(refname)",
                            HEADS).splitlines()
        return sorted(ref.removeprefix(HEADS) for ref in refs
                      if ref.startswith(prefix) and len(ref) > len(prefix))

    def _is_ancestor(self, worktree: Path, branch: str, key: str) -> bool:
        result = self._git(worktree, "merge-base", "--is-ancestor", f"{HEADS}{branch}",
                           f"{HEADS}{key}")
        if result.returncode not in (0, 1):
            raise SealAuditsError(JOIN_FAILED, f"{branch}: cannot tell whether it is joined: "
                                  f"{result.stderr.strip()}")
        return result.returncode == 0

    def _merge(self, worktree: Path, key: str, builder: Path, attribution: Attribution,
               branch: str) -> None:
        commits = self._answer(JOIN_FAILED, worktree, "log", "--oneline",
                               f"{HEADS}{key}..{HEADS}{branch}").splitlines()
        suffix = branch.removeprefix(audit_prefix(key))
        argv = [self._python, str(builder), "--repo", str(worktree), "merge",
                "--branch", branch, "--target-branch", key,
                "--description", f"development-audit findings — {suffix}",
                "--branch-commits", *commits,
                "--merge-context", f"tobiishi-seal {key} — audit fan-out join",
                *attribution.builder_arguments()]
        result = self._processes.run(argv, cwd=worktree)
        if result.returncode:
            self._fail_merge(worktree, branch, result)

    def _fail_merge(self, worktree: Path, branch: str, result: subprocess.CompletedProcess) -> None:
        """Read why the merge failed, then abort it: the abort erases the evidence."""
        said = result.stderr.strip()
        if not self._merge_in_progress(worktree):
            raise SealAuditsError(JOIN_FAILED, f"{branch}: the builder refused: {said}")
        unmerged = self._git(worktree, "diff", "--name-only", "--diff-filter=U").stdout.strip()
        code = MERGE_CONFLICT if unmerged else MERGE_HOOK_FAILED
        reason = f"{branch}: {said}"
        aborted = self._git(worktree, "merge", "--abort")
        if aborted.returncode:
            reason += f"; merge --abort failed: {aborted.stderr.strip()}"
        raise SealAuditsError(code, reason)

    def remove(self, *, repo: Path, key: str, joined: Path, outcome: Path) -> list[str]:
        """Remove the branches a join reported, and their worktrees, once delivery was proved.

        Nothing changes until every check of the whole set has passed, and nothing is forced.
        """
        self._require_proved_outcome(outcome, key)
        branches = self._reported_branches(joined, key)
        paths = self._checked_set(repo, key, branches)
        for branch, path in zip(branches, paths):
            if self._checked_path(repo, branch) != path:
                raise SealAuditsError(
                    TEARDOWN_FAILED, f"{branch}: registered path changed before removal")
            self._answer(TEARDOWN_FAILED, repo, "worktree", "remove", path)
            self._answer(TEARDOWN_FAILED, repo, "branch", "-d", branch)
            self._require_gone(repo, branch, path)
        return branches

    def _read_object(self, path: Path, what: str) -> dict:
        try:
            parsed = json.loads(self._files.read_text(path))
        except (OSError, ValueError) as error:
            raise SealAuditsError(
                TEARDOWN_FAILED, f"{what} {path} is unreadable: {error}") from None
        if not isinstance(parsed, dict):
            raise SealAuditsError(TEARDOWN_FAILED, f"{what} {path} is not a JSON object")
        return parsed

    def _require_proved_outcome(self, outcome: Path, key: str) -> None:
        delivered = self._read_object(outcome, "delivery outcome")
        # `is True`, never truthiness: the string "true" and the number 1 are not proof.
        if (delivered.get("status") != "ok" or delivered.get("audit_cleanup_eligible") is not True
                or delivered.get("key") != key):
            raise SealAuditsError(TEARDOWN_FAILED, f"{outcome}: delivery is not proved for {key}")

    def _reported_branches(self, joined: Path, key: str) -> list[str]:
        report = self._read_object(joined, "join report")
        branches = report.get("joined")
        if report.get("key") != key or not isinstance(branches, list) or not all(
                isinstance(branch, str) for branch in branches):
            raise SealAuditsError(
                TEARDOWN_FAILED, f"{joined}: not this change's list of joined branches")
        return branches

    def _registrations(self, repo: Path) -> list[dict[str, str]]:
        listing = self._answer(TEARDOWN_FAILED, repo, "worktree", "list", "--porcelain", "-z")
        return [dict(field.partition(" ")[::2] for field in block.split("\0") if field)
                for block in listing.split("\0\0") if block]

    def _checked_set(self, repo: Path, key: str, branches: list[str]) -> list[str]:
        if len(set(branches)) != len(branches) or any(
                not branch.startswith(audit_prefix(key)) for branch in branches):
            raise SealAuditsError(
                TEARDOWN_FAILED, "expected unique joined audit branches for this change")
        head = self._answer(TEARDOWN_FAILED, repo, "symbolic-ref", "--quiet", "HEAD").strip()
        if head != f"{HEADS}main":
            raise SealAuditsError(
                TEARDOWN_FAILED, "audit removal requires the delivered main checkout")
        return [self._checked_path(repo, branch) for branch in branches]

    def _checked_path(self, repo: Path, branch: str) -> str:
        matches = [record for record in self._registrations(repo)
                   if record.get("branch") == f"{HEADS}{branch}"]
        if len(matches) != 1 or any(flag in matches[0] for flag in ("locked", "prunable")):
            raise SealAuditsError(
                TEARDOWN_FAILED, f"{branch}: expected one usable registered audit worktree")
        path = matches[0]["worktree"]
        if self._answer(TEARDOWN_FAILED, path, "symbolic-ref", "--quiet", "HEAD").strip() != (
                f"{HEADS}{branch}"):
            raise SealAuditsError(TEARDOWN_FAILED, f"{path}: audit branch identity changed")
        if self._answer(TEARDOWN_FAILED, path, "status", "--porcelain", "--untracked-files=all"):
            raise SealAuditsError(
                TEARDOWN_FAILED, f"{path}: audit worktree has uncommitted changes")
        self._answer(TEARDOWN_FAILED, repo, "merge-base", "--is-ancestor", f"{HEADS}{branch}",
                     f"{HEADS}main")
        return path

    def _require_gone(self, repo: Path, branch: str, path: str) -> None:
        if any(record.get("worktree") == path or record.get("branch") == f"{HEADS}{branch}"
               for record in self._registrations(repo)):
            raise SealAuditsError(TEARDOWN_FAILED, f"{branch}: audit registration survived removal")
        if self._answer(TEARDOWN_FAILED, repo, "for-each-ref", "--format=%(refname)",
                        f"{HEADS}{branch}"):
            raise SealAuditsError(TEARDOWN_FAILED, f"{branch}: audit ref survived removal")


class _Parser(argparse.ArgumentParser):
    """A parser whose usage errors are the tool's own refusals, never argparse's exit 2."""

    def __init__(self, *args: object, code: str = JOIN_FAILED, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._code = code

    def error(self, message: str) -> NoReturn:
        raise SealAuditsError(self._code, f"usage: {message}")


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="seal_audits.py", description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    join = commands.add_parser("join", code=JOIN_FAILED,
                               help="merge every audit branch of the change into it")
    join.add_argument("--worktree", required=True, type=Path)
    join.add_argument("--key", required=True)
    join.add_argument("--builder", required=True, type=Path)
    join.add_argument("--actor", required=True)
    join.add_argument("--surface", required=True)
    join.add_argument("--co-authored-by")
    join.add_argument("--reasoning-effort")
    join.add_argument("--claude-session")
    remove = commands.add_parser("remove", code=TEARDOWN_FAILED,
                                 help="remove the joined audit branches after proved delivery")
    remove.add_argument("--repo", required=True, type=Path)
    remove.add_argument("--key", required=True)
    remove.add_argument("--joined", required=True, type=Path)
    remove.add_argument("--outcome", required=True, type=Path)
    return parser


def _join(arguments: argparse.Namespace, engine: AuditSeal) -> dict:
    attribution = Attribution(
        actor=arguments.actor, surface=arguments.surface, co_authored_by=arguments.co_authored_by,
        reasoning_effort=arguments.reasoning_effort, claude_session=arguments.claude_session)
    joined = engine.join(worktree=arguments.worktree, key=arguments.key,
                         builder=arguments.builder, attribution=attribution)
    return {"key": arguments.key, "joined": joined}


def _remove(arguments: argparse.Namespace, engine: AuditSeal) -> dict:
    removed = engine.remove(repo=arguments.repo, key=arguments.key, joined=arguments.joined,
                            outcome=arguments.outcome)
    return {"key": arguments.key, "removed": removed}


_COMMANDS = {"join": _join, "remove": _remove}
_REFUSAL_CODES = {"join": JOIN_FAILED, "remove": TEARDOWN_FAILED}


def _parse(argv: list[str]) -> argparse.Namespace:
    # argparse reports an unrecognized argument through the top-level parser, whose code is the
    # join's; reading the leftovers here lets a `remove` usage error name the removal's code.
    arguments, unrecognized = build_parser().parse_known_args(argv)
    if unrecognized:
        raise SealAuditsError(_REFUSAL_CODES[arguments.command],
                              f"usage: unrecognized arguments: {' '.join(unrecognized)}")
    return arguments


def _execute(arguments: argparse.Namespace, engine: AuditSeal) -> dict:
    try:
        return _COMMANDS[arguments.command](arguments, engine)
    except OSError as error:
        # A command that cannot be started is a refusal like any other, never a traceback.
        raise SealAuditsError(_REFUSAL_CODES[arguments.command],
                              f"a command could not be started: {error}") from None


def run(argv: list[str], *, engine: AuditSeal, stdout: TextIO, stderr: TextIO) -> int:
    """Run one command against the engine it is handed; refusals become a line and exit 1."""
    try:
        report = _execute(_parse(argv), engine)
    except SealAuditsError as refusal:
        print(f"error: {refusal.code}: {refusal.reason}", file=stderr)
        return 1
    print(json.dumps(report), file=stdout)
    return 0


def build_engine() -> AuditSeal:
    """The composition root: the only place the real ports are constructed."""
    return AuditSeal(processes=Processes(), files=Files(), python=sys.executable)


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    return run(arguments, engine=build_engine(), stdout=sys.stdout, stderr=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
