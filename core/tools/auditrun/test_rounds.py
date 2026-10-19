"""Contract tests for `auditrun/rounds.py` — the audit launcher's round-resolution logic.

Pure logic, no launching: given an `evidence/` directory of `v<major>.<minor>.<patch>/` rounds,
`resolve_target` picks which round `launch-audit.sh` audits (newest un-audited, or an explicit
version), the round strictly below it (for the cross-version comparison passes), and raises
`AuditRoundError` for every "no valid target" case so the launcher can convert it to a `die()`
before any run launches. Numeric-component ordering (not lexical) is the whole reason this is a
tested module rather than a one-line `ls | tail` — `v3.17.0` must beat `v3.4.0`, which a lexical
sort gets backwards.

`sys.path.insert` mirrors the `coldread/`-package idiom (`coldread/test_manifest.py`): explicit even though `core/tools/conftest.py` already puts this
directory on `sys.path`, so the file collects correctly regardless of how pytest was invoked.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # core/tools on path

from auditrun.rounds import AuditRoundError, AuditTarget, resolve_target


def _make_round(evidence_dir: Path, version: str, *, audited: bool) -> Path:
    d = evidence_dir / f"v{version}"
    d.mkdir(parents=True)
    if audited:
        (d / "audit.md").write_text(f"# Audit — v{version}\n")
    return d


# --- default selection: newest un-audited round -------------------------------


def test_newest_unaudited_round_is_chosen(tmp_path):
    _make_round(tmp_path, "1.0.0", audited=True)
    _make_round(tmp_path, "1.1.0", audited=False)

    target = resolve_target(str(tmp_path), None)

    assert target.version == "1.1.0"


def test_newest_is_numeric_not_lexical(tmp_path):
    """v3.17.0 beats v3.4.0 — a lexical sort gets this pair backwards."""
    _make_round(tmp_path, "3.4.0", audited=False)
    _make_round(tmp_path, "3.17.0", audited=False)

    target = resolve_target(str(tmp_path), None)

    assert target.version == "3.17.0"


def test_no_unaudited_round_raises(tmp_path):
    _make_round(tmp_path, "1.0.0", audited=True)
    _make_round(tmp_path, "2.0.0", audited=True)

    with pytest.raises(AuditRoundError, match="nothing to audit"):
        resolve_target(str(tmp_path), None)


# --- explicit version override -------------------------------------------------


def test_explicit_version_selects_that_round(tmp_path):
    _make_round(tmp_path, "1.0.0", audited=False)
    _make_round(tmp_path, "2.0.0", audited=False)

    target = resolve_target(str(tmp_path), "1.0.0")

    assert target.version == "1.0.0"


def test_explicit_version_accepts_leading_v(tmp_path):
    _make_round(tmp_path, "1.0.0", audited=False)

    target = resolve_target(str(tmp_path), "v1.0.0")

    assert target.version == "1.0.0"


def test_explicit_version_already_audited_refuses(tmp_path):
    _make_round(tmp_path, "1.0.0", audited=True)

    with pytest.raises(AuditRoundError, match="delete it yourself"):
        resolve_target(str(tmp_path), "1.0.0")


def test_explicit_version_naming_no_round_raises(tmp_path):
    _make_round(tmp_path, "1.0.0", audited=False)

    with pytest.raises(AuditRoundError):
        resolve_target(str(tmp_path), "2.0.0")


# --- prior-round resolution -----------------------------------------------------


def test_prior_dir_is_next_newest_below(tmp_path):
    _make_round(tmp_path, "3.4.0", audited=False)
    _make_round(tmp_path, "3.17.0", audited=False)

    target = resolve_target(str(tmp_path), "3.17.0")

    assert target.prior_dir == str((tmp_path / "v3.4.0").resolve())


def test_prior_absent_when_earliest(tmp_path):
    _make_round(tmp_path, "1.0.0", audited=False)

    target = resolve_target(str(tmp_path), "1.0.0")

    assert target.prior_dir is None


# --- target shape ---------------------------------------------------------------


def test_target_shape(tmp_path):
    _make_round(tmp_path, "1.0.0", audited=False)
    _make_round(tmp_path, "2.0.0", audited=False)

    target = resolve_target(str(tmp_path), "2.0.0")

    assert isinstance(target, AuditTarget)
    assert target.version == "2.0.0"
    assert not target.version.startswith("v")
    assert Path(target.round_dir).is_absolute()
    assert Path(target.round_dir) == (tmp_path / "v2.0.0").resolve()
    assert Path(target.prior_dir).is_absolute()
    assert Path(target.prior_dir) == (tmp_path / "v1.0.0").resolve()
