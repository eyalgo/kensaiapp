"""Layer-6 pin checks: every dependency is pinned exactly, and `uv.lock` fixes each at its pin.

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


def normalized(name: str) -> str:
    """A name as the packaging specification compares it: lowercase, with runs of `._-` as `-`."""
    return re.sub(r"[-_.]+", "-", name).lower()


def test_uv_lock_fixes_every_declared_dependency_at_its_declared_version():
    """QC-39, CP-662."""
    lock = PRODUCT_ROOT / "uv.lock"
    assert lock.is_file()
    packages = tomllib.loads(lock.read_text(encoding="utf-8")).get("package", [])
    assert packages, "uv.lock holds no package record"
    locked = {(normalized(package["name"]), package.get("version")) for package in packages}
    declared = declared_dependencies(manifest())
    assert [entry for entry in declared if not EXACT.fullmatch(entry)] == []
    wanted = []
    for entry in declared:
        name, version = entry.split("==", 1)
        wanted.append((normalized(name.partition("[")[0]), version))
    assert [pair for pair in wanted if pair not in locked] == []


def test_requires_python_is_3_11() -> None:
    """QC-59."""
    assert manifest()["project"]["requires-python"] == ">=3.11"


def test_the_exact_pattern_refuses_a_range_and_accepts_a_pin() -> None:
    """The check can fail: a floor, a compatible release and an unpinned name are refused."""
    for loose in ("pytest>=9", "pytest~=9.1", "pytest", "pytest==9.*,<10", "pytest>=9,==9.1.1"):
        assert EXACT.fullmatch(loose) is None, loose
    assert EXACT.fullmatch("pytest==9.1.1")
    assert EXACT.fullmatch("typing_extensions==4.16.0")
