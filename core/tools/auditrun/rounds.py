"""rounds.py — resolve which `evidence/v*/` round `launch-audit.sh` audits.

Pure logic: reads only the evidence directory listing, never launches anything. Mirrors
`launch-fix-author.sh:101-110`'s numeric-component sort (`v3.17.0` beats `v3.4.0` — a lexical
sort gets that pair backwards, which is the whole reason this is not a one-line `ls | tail`) but
INVERTS its `audit.md` predicate: the default selection is the newest round that does NOT yet
have an `audit.md` (fix-author's default is the newest round that DOES), and the same predicate
read the other way is the refuse-to-overwrite guard on an explicit version.

`AuditRoundError` covers every "no valid target" case; the launcher converts it to a `die()`
before any run launches, so the message is written for a caller reading it off stderr.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

_VERSION_RE = re.compile(r"v(\d+)\.(\d+)\.(\d+)")

VersionTuple = tuple[int, int, int]


@dataclass(frozen=True)
class AuditTarget:
    """The round `launch-audit.sh` audits, and what it needs to interpolate into the fixed
    prompt: the resolved round's directory, and the prior round's directory (or `None`) for
    the audit's cross-version comparison passes."""

    version: str          # no leading "v", e.g. "1.1.0"
    round_dir: str         # abs path to evidence/v<version>/
    prior_dir: str | None  # abs path to the next-newest round strictly below; None if earliest


class AuditRoundError(Exception):
    """Raised for every "no valid target" case — the launcher converts it to `die()` before
    any run launches."""


def _numeric_rounds(evidence_dir: str) -> list[tuple[VersionTuple, str]]:
    """`(version_tuple, dirname)` for every `v<N>.<N>.<N>` entry directly under `evidence_dir`.

    Non-matching entries (stray files, a malformed dirname) are silently skipped — `evidence/`
    is the launcher's own vault, so anything else in it is not this module's concern.
    """
    try:
        entries = os.listdir(evidence_dir)
    except OSError:
        return []
    rounds = []
    for name in entries:
        match = _VERSION_RE.fullmatch(name)
        if match:
            rounds.append((tuple(int(group) for group in match.groups()), name))
    return rounds


def _has_audit(evidence_dir: str, dirname: str) -> bool:
    return os.path.isfile(os.path.join(evidence_dir, dirname, "audit.md"))


def _prior_dirname_below(rounds: list[tuple[VersionTuple, str]], resolved: VersionTuple) -> str | None:
    """The dirname of the next-newest round strictly below `resolved` (numeric order), or
    `None` when `resolved` is the earliest."""
    below = [candidate for candidate in rounds if candidate[0] < resolved]
    if not below:
        return None
    return max(below, key=lambda candidate: candidate[0])[1]


def resolve_target(evidence_dir: str, explicit_version: str | None) -> AuditTarget:
    """The one entry point: resolve which round to audit, and its prior round.

    No `explicit_version`: the newest round with no `audit.md` — the un-audited round. Raises
    `AuditRoundError` when every round already holds one (nothing to audit).

    `explicit_version` given (a leading "v" is accepted and stripped): that exact round. Raises
    `AuditRoundError` when it names no round, or when the resolved round already holds an
    `audit.md` (the refuse-to-overwrite guard — delete it yourself, deliberately).
    """
    rounds = _numeric_rounds(evidence_dir)

    if explicit_version is not None:
        version = explicit_version[1:] if explicit_version.startswith("v") else explicit_version
        dirname = f"v{version}"
        matching = [candidate for candidate in rounds if candidate[1] == dirname]
        if not matching:
            raise AuditRoundError(f"no round {dirname} under {evidence_dir}")
        if _has_audit(evidence_dir, dirname):
            raise AuditRoundError(
                f"round {dirname} already has an audit.md at {evidence_dir}/{dirname}/audit.md "
                f"— delete it yourself if you mean to re-audit from scratch"
            )
        resolved = matching[0][0]
    else:
        unaudited = [candidate for candidate in rounds if not _has_audit(evidence_dir, candidate[1])]
        if not unaudited:
            raise AuditRoundError(f"nothing to audit under {evidence_dir} — every round already has an audit.md")
        resolved, dirname = max(unaudited, key=lambda candidate: candidate[0])
        version = dirname[1:]

    round_dir = os.path.abspath(os.path.join(evidence_dir, dirname))
    prior_dirname = _prior_dirname_below(rounds, resolved)
    prior_dir = os.path.abspath(os.path.join(evidence_dir, prior_dirname)) if prior_dirname else None

    return AuditTarget(version=version, round_dir=round_dir, prior_dir=prior_dir)
