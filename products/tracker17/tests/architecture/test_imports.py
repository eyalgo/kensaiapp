"""Layer-6 import walks: which part may import which, and nothing third-party (docs/nfdr.md § 1.2).

Checks SRS NFR-9 (the code keeps its parts apart, so one can be read and changed alone) and
acceptance criterion AC-5. NFDR QC-13 to QC-19 and QC-43 are the ones each test names. Each walk
reads every module outside tests/ as a syntax tree and fails when its part holds no module.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import pytest

PARTS = {"domain", "application", "persistence", "web", "main", "errors"}
ALLOWED_PARTS = {
    "domain": {"domain", "errors"},
    "application": {"application", "domain", "errors"},
    "persistence": {"persistence", "domain", "errors"},
    "web": {"web", "application", "errors"},
    "main": {"domain", "application", "persistence", "web", "errors"},
    "errors": {"errors"},
}
BANNED_EVERYWHERE = ("http.client", "urllib.request", "ftplib", "smtplib")
WEB_ONLY = ("socket", "socketserver", "http.server")


def _is(name: str, banned: str) -> bool:
    return name == banned or name.startswith(banned + ".")


def violations(walk, part: str) -> list[str]:
    """Every import in the part that its clause forbids, as `path: name`."""
    found = []
    for module in walk.modules(part):
        for name in module.imported():
            top = name.split(".")[0]
            if top in PARTS:
                if top not in ALLOWED_PARTS[part]:
                    found.append(f"{module.path}: {name}")
            elif top == "tests" or top not in sys.stdlib_module_names:
                found.append(f"{module.path}: {name}")
    return found


def test_domain_imports_only_errors_and_the_standard_library(walk_of) -> None:
    """QC-13."""
    assert violations(walk_of(), "domain") == []


def test_application_imports_only_domain_and_errors(walk_of) -> None:
    """QC-14."""
    assert violations(walk_of(), "application") == []


def test_persistence_imports_only_domain_and_errors(walk_of) -> None:
    """QC-15."""
    assert violations(walk_of(), "persistence") == []


def test_web_imports_only_application_and_errors(walk_of) -> None:
    """QC-16."""
    assert violations(walk_of(), "web") == []


def test_main_imports_the_four_parts_and_errors_and_nothing_from_tests(walk_of) -> None:
    """QC-17."""
    assert violations(walk_of(), "main") == []
    imported = {name.split(".")[0] for name in walk_of().modules("main")[0].imported()}
    assert {"domain", "application", "persistence", "web"} <= imported


def test_errors_imports_no_part(walk_of) -> None:
    """QC-18."""
    assert violations(walk_of(), "errors") == []
    for module in walk_of().modules("errors"):
        assert {name.split(".")[0] for name in module.imported()} & (PARTS - {"errors"}) == set()


def test_nothing_outside_tests_imports_third_party_or_tests(walk_of) -> None:
    """QC-19, QC-43: and only web touches a socket or a server, and nothing reaches out."""
    for part in sorted(PARTS):
        assert violations(walk_of(), part) == [], part
    for module in walk_of().modules():
        for name in module.imported():
            assert not any(_is(name, banned) for banned in BANNED_EVERYWHERE), (module.path, name)
            if module.part != "web":
                assert not any(_is(name, banned) for banned in WEB_ONLY), (module.path, name)


def test_each_walk_fails_when_its_directory_holds_no_module(
    walk_of: Callable[[Path | None], object], tmp_path: Path
) -> None:
    for part in sorted(PARTS):
        with pytest.raises(AssertionError):
            walk_of(tmp_path).modules(part)


def test_each_walk_finds_a_violation_planted_in_its_part(walk_of, tmp_path: Path) -> None:
    """The walks can fail: a forbidden import planted in a part is reported."""
    planted = {
        "domain": "from web import pages\n",
        "application": "import persistence\n",
        "persistence": "from application import Tracker\n",
        "web": "from domain import Project\n",
        "main": "import requests\n",
        "errors": "from domain import Project\n",
    }
    for part, source in planted.items():
        target = tmp_path / (f"{part}.py" if part in {"main", "errors"} else f"{part}/bad.py")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    for part in planted:
        assert violations(walk_of(tmp_path), part), part
    (tmp_path / "domain" / "tests_import.py").write_text("import tests\n", encoding="utf-8")
    assert any("tests" in found for found in violations(walk_of(tmp_path), "domain"))
