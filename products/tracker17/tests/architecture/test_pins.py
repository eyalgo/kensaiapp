"""Layer-6 pin checks: every dependency is pinned exactly, and the lock file is exact.

Checks SRS NFR-9 (the product can be rebuilt as it was). Change spec rule CP-28 and NFDR QC-39 and
QC-59 are the ones each test names.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent
EXACT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*(\[[A-Za-z0-9,._-]+\])?==[^=<>!~,;\s]+")


def manifest() -> dict:
    return tomllib.loads((PRODUCT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def declared_dependencies(document: dict) -> list[str]:
    """Every requirement string in every dependency list the manifest holds."""
    found = list(document.get("project", {}).get("dependencies", []))
    for extra in document.get("project", {}).get("optional-dependencies", {}).values():
        found += extra
    for group in document.get("dependency-groups", {}).values():
        found += [entry for entry in group if isinstance(entry, str)]
    found += document.get("build-system", {}).get("requires", [])
    return found


def test_every_declared_dependency_is_pinned_exactly() -> None:
    """QC-39, CP-28."""
    dependencies = declared_dependencies(manifest())
    assert dependencies, "the manifest declares no dependency, so there is nothing to pin"
    assert [entry for entry in dependencies if not EXACT.fullmatch(entry)] == []


def test_the_lock_file_exists_and_every_line_is_exact() -> None:
    lock = PRODUCT_ROOT / "tests" / "requirements.txt"
    assert lock.is_file()
    lines = [
        line.strip()
        for line in lock.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert lines
    assert [line for line in lines if not EXACT.fullmatch(line)] == []
    locked = {line.split("==")[0].lower() for line in lines}
    declared = {re.split(r"[=\[]", entry)[0].lower() for entry in declared_dependencies(manifest())}
    assert declared <= locked


def test_requires_python_is_3_11() -> None:
    """QC-59."""
    assert manifest()["project"]["requires-python"] == ">=3.11"


def test_the_exact_pattern_refuses_a_range_and_accepts_a_pin() -> None:
    """The check can fail: a floor, a compatible release and an unpinned name are refused."""
    for loose in ("pytest>=9", "pytest~=9.1", "pytest", "pytest==9.*,<10", "pytest>=9,==9.1.1"):
        assert EXACT.fullmatch(loose) is None, loose
    assert EXACT.fullmatch("pytest==9.1.1")
    assert EXACT.fullmatch("typing_extensions==4.16.0")
