#!/usr/bin/env python3
"""drop.py — the mechanics half of `tobiishi-drop`.

The skill's prose (`SKILL.md`) holds the posture gate and the order of the calls, and commits. This
file decides whether a drop may be made, moves the unit, marks the PM context, closes the change's
worktrees and states where the journey stands. Three commands, run in this order with the commit
between `apply` and `close`:

    check <project> <key> <reason>  — the drop may be made at all: a reason was given, the key is an
                                      open unit, and no worktree it would close holds uncommitted
                                      work. Prints the worktrees `close` will remove.
    apply <project> <key>           — moves `tobiishi/<key>/` to `tobiishi/drop/<key>/` and marks
                                      the PM context. Prints every path the commit must declare,
                                      then one line saying whether the context was marked.
    close <project> <key>           — removes the change's worktrees, never a branch, and prints
                                      the report: the key and its new path, each worktree closed
                                      and branch kept, the context mark, and where the journey
                                      stands.

WHY THE ORDER IS CHECK, APPLY, COMMIT, CLOSE: every check runs before any effect, so one dirty
worktree stops the whole drop. The record on `main` comes before the teardown, the order the seal
uses, so a teardown that fails leaves a dropped unit with a live worktree and says so, and never a
removed worktree for a drop that did not commit.

Every refusal is printed and exits 1; a refusal changes nothing. The instance root and the git
runner are given, never derived, so each function is testable at its seam.

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

__version__ = "1.0.1"

Git = Callable[[Path, list[str]], str]

_BINS = {"trail", "drop"}
_PRODUCT_PATH = re.compile(r"^\**Product path:\**[ \t]*(\S+)", re.MULTILINE)
_SEEDBED_FIXTURES = {"README.md", "unpicked", "trail", "drop"}
_SHUKUBA_FIXTURES = {"README.md", "parked", "trail"}
_UNCHECKED_ITEM = re.compile(r"^[ \t]*- \[ \][ \t]*(.*?)[ \t]*$", re.MULTILINE)
_CHECKED_ITEM = re.compile(r"^[ \t]*- \[[xX]\]", re.MULTILINE)
_CURRENT_CHANGE_HEADING = "## Current change — PM view"
_STATUS_PREFIX = "**Status:**"
_DROPPED_STATUS_LINE = "**Status:** Dropped"


@dataclass(frozen=True)
class Worktree:
    repo: Path
    path: Path
    branch: str | None
    sha: str


@dataclass(frozen=True)
class ContextStatus:
    """Where `CONTEXT_PM.md`'s Status line for this unit is, or the `reason` it has none."""

    path: Path
    lines: tuple[str, ...]
    index: int
    reason: str


@dataclass(frozen=True)
class Applied:
    paths: tuple[str, ...]
    context_line: str


class Refused(Exception):
    """A drop, or a step of one, that may not be made, with the reason."""


def run_git(root: Path, args: list[str]) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout


def _tobiishi(root: Path, project: str) -> Path:
    path = root / "system" / "projects" / project / "journey" / "tobiishi"
    if not path.is_dir():
        raise Refused(f"no tobiishi folder at {path}")
    return path


def _require_open_unit(tobiishi: Path, key: str) -> None:
    """Refuse a key that is not a folder directly under `tobiishi/`, other than the two bins."""
    a_unit_name = bool(key) and key not in _BINS and Path(key).name == key
    if a_unit_name and (tobiishi / "trail" / key).exists():
        raise Refused(f"{key} is sealed — it sits in tobiishi/trail/ and is not an open unit")
    if a_unit_name and (tobiishi / "drop" / key).exists():
        raise Refused(f"{key} is already dropped — it sits in tobiishi/drop/")
    if not a_unit_name or not (tobiishi / key).is_dir():
        raise Refused(f"no such open unit: {key!r} is not a folder directly under tobiishi/")


def _listed(repo: Path, git: Git) -> list[Worktree]:
    """Every worktree of `repo`, read from `git worktree list --porcelain`."""
    worktrees = []
    for block in git(repo, ["worktree", "list", "--porcelain"]).strip().split("\n\n"):
        fields = dict(line.split(" ", 1) for line in block.splitlines() if " " in line)
        if "worktree" not in fields:
            continue
        branch = fields.get("branch", "").removeprefix("refs/heads/") or None
        worktrees.append(
            Worktree(repo, Path(fields["worktree"]).resolve(), branch, fields.get("HEAD", ""))
        )
    return worktrees


def _product_repo(root: Path, project: str, git: Git) -> Path | None:
    """The product's own repo, when `project.md` `Product path:` is absolute and present."""
    card = root / "system" / "projects" / project / "project.md"
    if not card.is_file():
        return None
    declared = _PRODUCT_PATH.search(card.read_text(encoding="utf-8"))
    if declared is None or not declared.group(1).startswith("/"):
        return None
    product_path = Path(declared.group(1))
    if not product_path.is_dir():
        return None
    return Path(git(product_path, ["rev-parse", "--show-toplevel"]).strip()).resolve()


def _worktrees(root: Path, project: str, key: str, git: Git) -> list[Worktree]:
    """The change's worktrees: the instance's, each audit one, and the product repo's."""
    folder = (root / ".worktrees").resolve()
    found = [
        wt
        for wt in _listed(root, git)
        if wt.path.parent == folder
        and (wt.path.name == key or wt.path.name.startswith(f"{key}__audit-"))
    ]
    product = _product_repo(root, project, git)
    if product is not None:
        product_folder = product / ".worktrees"
        found += [wt for wt in _listed(product, git) if wt.path == product_folder / key]
    return found


def check(root: Path, project: str, key: str, reason: str, git: Git) -> list[Worktree]:
    """Refuse unless the drop may be made now; return the worktrees `close` will remove."""
    if not reason.strip():
        raise Refused("the reason is missing — say why the unit is dropped")
    _require_open_unit(_tobiishi(root, project), key)
    worktrees = _worktrees(root, project, key, git)
    unclean = [wt for wt in worktrees if git(wt.path, ["status", "--porcelain"]).strip()]
    if unclean:
        named = "\n".join(f"  {wt.path}" for wt in unclean)
        raise Refused(
            "uncommitted changes in a worktree this drop would close — commit or discard them "
            f"first, nothing is discarded here:\n{named}"
        )
    return worktrees


def _names_key(text: str, key: str) -> bool:
    """`key` appears as a whole key, not as the prefix or the tail of a longer one — a unit
    `<key>-follow-up` is a different unit, and marking its status would mislabel it."""
    return re.search(rf"(?<![\w-]){re.escape(key)}(?![\w-])", text) is not None


def _find_status(root: Path, project: str, key: str) -> ContextStatus:
    """Locate the `**Status:**` line CP-142 rewrites, or say why the mark does not apply."""
    path = root / "system" / "projects" / project / "contexts" / "CONTEXT_PM.md"
    if not path.is_file():
        return ContextStatus(path, (), -1, "there is no CONTEXT_PM.md")
    lines = tuple(path.read_bytes().decode("utf-8").splitlines(keepends=True))
    heading = next(
        (i for i, line in enumerate(lines) if line.rstrip() == _CURRENT_CHANGE_HEADING), None
    )
    if heading is None:
        return ContextStatus(path, lines, -1, f"it has no `{_CURRENT_CHANGE_HEADING}` section")
    end = next(
        (i for i in range(heading + 1, len(lines)) if lines[i].startswith("## ")), len(lines)
    )
    if not _names_key("".join(lines[heading + 1 : end]), key):
        return ContextStatus(path, lines, -1, "its current change is not this unit")
    status = next(
        (i for i in range(heading + 1, end) if lines[i].startswith(_STATUS_PREFIX)), None
    )
    if status is None:
        return ContextStatus(path, lines, -1, "its current change has no **Status:** line")
    return ContextStatus(path, lines, status, "")


def _mark_context(root: Path, project: str, key: str) -> ContextStatus:
    """Rewrite the one `**Status:**` line to Dropped; every other byte is copied through."""
    found = _find_status(root, project, key)
    if found.reason:
        return found
    line = found.lines[found.index]
    ending = line[len(line.rstrip("\r\n")) :]
    rewritten = list(found.lines)
    rewritten[found.index] = _DROPPED_STATUS_LINE + ending
    found.path.write_bytes("".join(rewritten).encode("utf-8"))
    return found


def _context_line(root: Path, found: ContextStatus) -> str:
    if found.reason:
        return f"context: not marked — {found.reason}"
    return f"context: marked — {found.path.relative_to(root)}"


def apply(root: Path, project: str, key: str, git: Git) -> Applied:
    """Move the unit into `tobiishi/drop/` and mark the context; stage nothing but the rename."""
    tobiishi = _tobiishi(root, project)
    _require_open_unit(tobiishi, key)
    old = (tobiishi / key).relative_to(root)
    new = (tobiishi / "drop" / key).relative_to(root)
    tracked = [p for p in git(root, ["ls-files", "-z", "--", str(old)]).split("\0") if p]
    (root / new).parent.mkdir(exist_ok=True)
    git(root, ["mv", str(old), str(new)])
    paths = [path for file in tracked for path in (file, str(new / Path(file).relative_to(old)))]
    marked = _mark_context(root, project, key)
    if not marked.reason:
        paths.append(str(marked.path.relative_to(root)))
    return Applied(tuple(paths), _context_line(root, marked))


def _visible(folder: Path, fixtures: set[str]) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(
        p for p in folder.iterdir() if not p.name.startswith(".") and p.name not in fixtures
    )


def _standing(root: Path, project: str) -> list[str]:
    """Where the journey stands after a drop: the station is still open, the seed untouched."""
    journey = root / "system" / "projects" / project / "journey"
    stations = _visible(journey / "shukuba", _SHUKUBA_FIXTURES)
    station = (
        f"station: {stations[0].name} — the station is still open"
        if stations
        else "station: no station is open"
    )
    seeds = _visible(journey / "nemawashi", _SEEDBED_FIXTURES)
    if not seeds:
        return [station, "seed: no active seed"]
    if len(seeds) > 1:
        names = ", ".join(p.name for p in seeds)
        return [station, f"seed: the seedbed root holds more than one item — {names}"]
    seed = seeds[0]
    text = (seed / "seed.md" if seed.is_dir() else seed).read_text(encoding="utf-8")
    unchecked = _UNCHECKED_ITEM.findall(text)
    if unchecked:
        count = len(unchecked)
        noun, verb = ("item", "remains") if count == 1 else ("items", "remain")
        left = f"{count} unchecked {noun} {verb}"
        return [station, f"seed: {seed.name} — {left}; next: {unchecked[0]}"]
    if _CHECKED_ITEM.search(text):
        owed = "no item remains; the retire is owed to the Scrum Master (nemawashi-retire)"
        return [station, f"seed: {seed.name} — {owed}"]
    return [station, f"seed: {seed.name} carries no checklist — there is no route to count"]


def close(root: Path, project: str, key: str, git: Git) -> list[str]:
    """Remove the change's worktrees, keep every branch; return the report in CP-144's order."""
    dropped = _tobiishi(root, project) / "drop" / key
    if not dropped.is_dir():
        raise Refused(f"{key} is not in tobiishi/drop/ — run apply, and commit, before close")
    report = [f"dropped: {key} → {dropped.relative_to(root)}"]
    worktrees = _worktrees(root, project, key, git)
    if not worktrees:
        report.append("worktrees: nothing to close — no worktree existed")
    for worktree in worktrees:
        git(worktree.repo, ["worktree", "remove", str(worktree.path)])
        kept = f"{worktree.branch} at {worktree.sha}" if worktree.branch else "none — detached"
        report += [f"worktree closed: {worktree.path}", f"branch kept: {kept}"]
    found = _find_status(root, project, key)
    if not found.reason and found.lines[found.index].rstrip("\r\n") != _DROPPED_STATUS_LINE:
        found = replace(found, reason="its Status line does not read Dropped")
    return [*report, _context_line(root, found), *_standing(root, project)]


def dispatch(argv: list[str] | None, git: Git) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", required=True, type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    check_parser = sub.add_parser("check")
    check_parser.add_argument("project")
    check_parser.add_argument("key")
    check_parser.add_argument("reason")
    for name in ("apply", "close"):
        step = sub.add_parser(name)
        step.add_argument("project")
        step.add_argument("key")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "check":
            worktrees = check(root, args.project, args.key, args.reason, git)
            closing = "\n".join(f"would close: {wt.path}" for wt in worktrees)
            print(closing or "no worktree to close")
        elif args.command == "apply":
            applied = apply(root, args.project, args.key, git)
            print("\n".join([*applied.paths, applied.context_line]))
        else:
            print("\n".join(close(root, args.project, args.key, git)))
    except Refused as refusal:
        print(f"error: {refusal}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as failure:
        command = " ".join(failure.cmd[3:])
        print(f"error: git {command} failed: {failure.stderr.strip()}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    """The composition root: the only place the real git runner is chosen."""
    return dispatch(argv, run_git)


if __name__ == "__main__":
    sys.exit(main())
