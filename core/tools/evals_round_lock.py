#!/usr/bin/env python3
"""The skill-evals round lock — one holder at a time, across every worktree of a repo.

WHAT IT IS FOR
    A skill-evals round is expensive: product-srs iteration-12 measured 3.6M billed tokens for a
    single with-skill executor, and a five-case round runs ten of them. On 2026-07-26 two rounds were
    launched in parallel and both died on the account session limit, losing the reasoning as well as
    the numbers. This lock is how a launcher refuses to start a second one.

    It also answers a second question the same way: whether it is safe to EDIT a skill right now.
    Editing a skill while it is being benchmarked corrupts the measurement, so `launch-eval-fix`
    reads this lock too and stands down while a round holds it.

WHERE IT LIVES
    In the repo's COMMON git dir (`git rev-parse --git-common-dir`) — the one directory every linked
    worktree of a repo agrees on. That is the deliberate mirror of `skill-evals/scripts/fixture_guard.py`,
    which uses the per-worktree `--absolute-git-dir` precisely so linked worktrees never share a lock:
    same mechanism, opposite intent. That one protects a per-checkout fixture tree; this one protects a
    per-account budget, and an account does not care which directory you are standing in.

    `KENSAIAPP_EVALS_LOCK` overrides the path, for tests and for anyone wanting a wider scope.

WHY IT IDENTIFIES BY AGENT ID
    The obvious guard — look for a running agent whose name matches the launch prompt — does not work.
    Claude Code RENAMES a background agent shortly after launch: a round launched with a prompt opening
    "run the skill-evals benchmark for the ..." was listed minutes later as "run skill-evals benchmark
    product-prd", and nothing in `claude agents --json` preserves the original prompt (verified against
    a live round, 2026-07-27). There is no stable string to match on, so the lock records the id.

WHY IT IS SELF-HEALING
    The lock names an agent id, and `holder` reports it held ONLY while that id is still `working`.
    Anything else — finished, killed, aged out of the list, machine rebooted — is stale, and `holder`
    clears it as it passes. A lock that has to be cleared by hand is a lock that gets cleared by hand
    at the wrong moment, which is worse than no lock at all.

USAGE
    evals_round_lock.py path                     print the lock path for this repo
    evals_round_lock.py holder                   print "<id> <skill> <cwd>" if held, nothing if free
                                                 (clears the lock as a side effect when it is stale)
    evals_round_lock.py write --agent-id ID --skill S --cwd D --iteration N
    evals_round_lock.py clear
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

__version__ = "1.0.0"

SCHEMA_VERSION = 1
LOCK_BASENAME = "kensaiapp-skill-evals-round.json"


def lock_path(repo: str | None = None) -> Path:
    """The lock's path: the env override, else the repo's common git dir.

    `--git-common-dir` may answer relatively (plain ".git" from the repo root), so the result is
    resolved against the repo before use — an unresolved relative path would put the lock wherever
    the caller happened to be standing, which defeats the whole point of a shared location.
    """
    override = os.environ.get("KENSAIAPP_EVALS_LOCK")
    if override:
        return Path(override)
    root = Path(repo or os.getcwd())
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        out = ".git"
    common = Path(out)
    if not common.is_absolute():
        common = root / common
    return common / LOCK_BASENAME


def agent_state(agent_id: str) -> str | None:
    """The state `claude agents` reports for one id, or None if it cannot say.

    None is returned both for "not in the list" and for "the list could not be read", and the caller
    treats both as not-working. That is deliberate: an unreadable agent list is not a reason to hold a
    launch, because the failure has nothing to do with whether the account is busy.
    """
    try:
        out = subprocess.run(
            ["claude", "agents", "--json", "--all"],
            capture_output=True, text=True, timeout=30,
        ).stdout
        agents = json.loads(out)
    except Exception:
        return None
    for a in agents or []:
        if a.get("id") == agent_id:
            return a.get("state")
    return None


def read_lock(path: Path) -> dict | None:
    try:
        with path.open() as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def holder(path: Path) -> dict | None:
    """The round currently holding the lock, or None — clearing a stale lock on the way past."""
    data = read_lock(path)
    if not data:
        return None
    agent_id = data.get("agent_id")
    if not agent_id or agent_state(agent_id) != "working":
        path.unlink(missing_ok=True)
        return None
    return data


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", default=None, help="repo to resolve the lock for (default: cwd)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("path", help="print the lock path")
    sub.add_parser("holder", help="print the holding round, or nothing; clears a stale lock")
    w = sub.add_parser("write", help="record the round that now holds the lock")
    w.add_argument("--agent-id", required=True)
    w.add_argument("--skill", required=True)
    w.add_argument("--cwd", required=True)
    w.add_argument("--iteration", type=int, required=True)
    sub.add_parser("clear", help="remove the lock")
    args = p.parse_args(argv)

    path = lock_path(args.repo)

    if args.cmd == "path":
        print(path)
        return 0

    if args.cmd == "holder":
        held = holder(path)
        if held:
            print(held.get("agent_id", "?"), held.get("skill", "?"), held.get("cwd", "?"))
        return 0

    if args.cmd == "write":
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as fh:
            json.dump({
                "schema_version": SCHEMA_VERSION,
                "agent_id": args.agent_id,
                "skill": args.skill,
                "cwd": args.cwd,
                "iteration": args.iteration,
            }, fh)
        return 0

    if args.cmd == "clear":
        path.unlink(missing_ok=True)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
