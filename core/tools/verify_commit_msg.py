#!/usr/bin/env python3
"""verify_commit_msg.py — pure, stdlib-only commit-msg trailer presence-check.

Invoked by the git `commit-msg` hook shim (`core/githooks/commit-msg`) with
`argv[1]` = the path to the commit-message file git is about to use. Reads
that file, detects whether the in-progress git operation is an ordinary
commit or a `--no-ff` merge (`git rev-parse -q --verify MERGE_HEAD`), and
checks the required trailer *keys* for that operation are present. Exits 0
when every required key is present; exits non-zero and writes guidance to
stderr naming the missing key(s) when one is not.

This module never opens the message file for writing — it only ever reads
it. It presence-checks trailer *keys*; it does not re-implement the trailer
*format* (values, shape, canonical order), which stays the single
responsibility of `core/tools/commit_builder.py` and
`core/doctrine/governance/commit_format.md`.

Required-block trailer set (single home of this fact):
  commit op -> Role:, Surface:
  merge op  -> Merge-Authorized:, Surface:
The directional trailer (Shukuba:/Michi:) is never required on either op —
per doctrine (`commit_format.md` §Directional trailer) it never blocks a
commit; a pure check honours that by not gating on it.

Stdlib-only imports.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Literal

__version__ = "1.0.0"

Op = Literal["commit", "merge"]

REQUIRED_TRAILERS: dict[Op, tuple[str, ...]] = {
    "commit": ("Role:", "Surface:"),
    "merge": ("Merge-Authorized:", "Surface:"),
}


MERGE_MARKER = "Merge-Authorized:"


def _detect_op(message: str = "", cwd: str | None = None) -> Op:
    """Two signals, because one is not enough.

    `MERGE_HEAD` resolves -> a `--no-ff` merge is in progress. Verified
    empirically (git 2.50.1): the `commit-msg` hook fires on `--no-ff` merges and
    `MERGE_HEAD` is visible then (version floor: git 2.24, which is when
    `commit-msg` started firing on merges).

    That signal is absent on `git commit --amend`, because the merge is already
    made -- which is how a correct merge message came to be refused for a missing
    `Role:`, a trailer a merge must not carry. **Git state cannot supply the
    missing signal:** measured 2026-09-05, an amend of a merge and an ordinary
    commit made straight after one are identical -- `MERGE_HEAD` absent,
    `GIT_REFLOG_ACTION` empty, `HEAD` carrying two parents in both.

    So the second signal is the message's own `Merge-Authorized:` line. That
    stays inside this module's domain -- it presence-checks trailer keys, and
    this is one -- and it deliberately does **not** read the subject line, whose
    `merge: ...` shape belongs to `commit_builder.py` rather than to doctrine.
    Reading it here would import that module's format, which the docstring above
    says this one does not do.

    Known limit: a message carrying no trailers at all cannot be classified by
    its trailers, so a trailer-less amended merge is checked against the commit
    set. It is still blocked; only the guidance is off.
    """
    if any(line.startswith(MERGE_MARKER) for line in message.splitlines()):
        return "merge"
    result = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"],
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return "merge" if result.returncode == 0 else "commit"


def _missing_trailers(message: str, op: Op) -> list[str]:
    """A required key is present when some line in the message starts with
    it (e.g. a line starting `Role:`)."""
    lines = message.splitlines()
    return [
        key
        for key in REQUIRED_TRAILERS[op]
        if not any(line.startswith(key) for line in lines)
    ]


def _guidance(missing: list[str]) -> str:
    names = ", ".join(missing)
    return (
        f"commit-msg: missing required trailer(s): {names}\n"
        "Construct the message through core/tools/commit_builder.py, or "
        "add the trailer(s) by hand per "
        "core/doctrine/governance/commit_format.md.\n"
    )


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    message_path = argv[0]

    with open(message_path, "r", encoding="utf-8") as fh:  # read-only, never write
        message = fh.read()

    op = _detect_op(message)
    missing = _missing_trailers(message, op)

    if missing:
        sys.stderr.write(_guidance(missing))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
