"""Layer-6 walk of the fakes: every contract has one fake and a suite run against the real one and the fake.

Checks SRS NFR-10 and NFR-11: the tests are plain enough to read cold, and each contract's stand-in
is written once and verified. NFDR QC-64 and RN-65 are the clauses, and NFDR § 9 has a layer-6 walk
fail on a directory that holds no module. The walk reads the method names off the `Protocol`
classes in application/contracts.py, so a third contract is bound the day it lands. It reads every
module under tests/, tests/e2e/ included, and the fakes in tests/fakes.py. The suites it asks for
are the ones in tests/integration/test_saver_contract.py and tests/integration/test_clock_contract.py.
Each failure case builds a small product tree under a temporary directory, with a contract `Pinger`
that has the one method `ping`, so the walk is shown to fail on exactly the departure it names.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import SourceWalk

PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent
SUPPORT_MODULE = Path("tests") / "fakes.py"
CONTRACTS_MODULE = Path("application") / "contracts.py"
TESTS_FOLDER = "tests"
CACHE_FOLDER = "__pycache__"
PROTOCOL = "Protocol"
TEST_PREFIX = "test_"


@dataclass(frozen=True)
class WalkedModule:
    """One module under tests/: where it is, from the product root, and its syntax tree."""

    path: Path
    tree: ast.Module

    def classes(self) -> Iterator[ast.ClassDef]:
        return (node for node in ast.walk(self.tree) if isinstance(node, ast.ClassDef))


def base_names(node: ast.ClassDef) -> set[str]:
    """The name each base spells, as a bare name or as the attribute of one."""
    return {
        base.id if isinstance(base, ast.Name) else base.attr
        for base in node.bases
        if isinstance(base, ast.Name | ast.Attribute)
    }


def names_in(node: ast.AST) -> set[str]:
    """Every bare name and every attribute name in a subtree."""
    return {
        child.id if isinstance(child, ast.Name) else child.attr
        for child in ast.walk(node)
        if isinstance(child, ast.Name | ast.Attribute)
    }


def methods_of(node: ast.ClassDef) -> set[str]:
    return {
        member.name
        for member in node.body
        if isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def contract_methods(walk: SourceWalk) -> set[str]:
    """Method names, without a leading underscore, of every `Protocol` class in the contracts file."""
    contracts = [module for module in walk.modules() if module.path == CONTRACTS_MODULE]
    return {
        method
        for module in contracts
        for node in ast.walk(module.tree)
        if isinstance(node, ast.ClassDef) and PROTOCOL in base_names(node)
        for method in methods_of(node)
        if not method.startswith("_")
    }


def real_implementations(walk: SourceWalk, method: str) -> set[str]:
    """Classes in the source walk that define the method and are not themselves a `Protocol`."""
    return {
        node.name
        for module in walk.modules()
        for node in ast.walk(module.tree)
        if isinstance(node, ast.ClassDef)
        and method in methods_of(node)
        and PROTOCOL not in base_names(node)
    }


def modules_under_tests(root: Path) -> list[WalkedModule]:
    folder = root / TESTS_FOLDER
    return [
        WalkedModule(path.relative_to(root), ast.parse(path.read_text(encoding="utf-8")))
        for path in sorted(folder.rglob("*.py"))
        if CACHE_FOLDER not in path.relative_to(root).parts
    ]


def runs_both_ways(modules: list[WalkedModule], fakes: set[str], reals: set[str]) -> bool:
    """A class with a `test_` method has one subclass naming a fake and another naming a real one."""
    every_class = [node for module in modules for node in module.classes()]
    for suite in every_class:
        if not any(name.startswith(TEST_PREFIX) for name in methods_of(suite)):
            continue
        subclasses = [node for node in every_class if suite.name in base_names(node)]
        with_fake = [node for node in subclasses if names_in(node) & fakes]
        with_real = [node for node in subclasses if names_in(node) & reals]
        if any(one is not other for one in with_fake for other in with_real):
            return True
    return False


def contract_findings(root: Path, walk: SourceWalk) -> list[str]:
    """Every departure from: one fake per contract, kept in `tests/fakes.py`, with a suite run both ways."""
    methods = contract_methods(walk)
    if not methods:
        return [f"{CONTRACTS_MODULE.as_posix()}: no `{PROTOCOL}` class defines a contract method"]
    modules = modules_under_tests(root)
    if not modules:
        return [f"{TESTS_FOLDER}/: no module to walk under {root}"]
    support = [module for module in modules if module.path == SUPPORT_MODULE]
    if not support:
        return [f"{SUPPORT_MODULE.as_posix()}: the test-support module is missing"]
    fake_classes = list(support[0].classes())
    fake_names = {node.name for node in fake_classes}

    findings: list[str] = []
    for module in modules:
        if module.path == SUPPORT_MODULE:
            continue
        where = module.path.as_posix()
        for node in module.classes():
            for method in sorted(methods_of(node) & methods):
                findings.append(
                    f"{where}:{node.lineno}: class {node.name} defines `{method}`,"
                    f" a contract method kept only in {SUPPORT_MODULE.as_posix()}"
                )
            for name in sorted(base_names(node) & fake_names):
                findings.append(
                    f"{where}:{node.lineno}: class {node.name} has the fake {name} as its base"
                )
    for method in sorted(methods):
        fakes = {node.name for node in fake_classes if method in methods_of(node)}
        if not fakes:
            findings.append(f"{SUPPORT_MODULE.as_posix()}: no fake defines `{method}`")
        elif not runs_both_ways(modules, fakes, real_implementations(walk, method)):
            findings.append(
                f"{TESTS_FOLDER}/: no suite for `{method}` runs against both the fake and a real one"
            )
    return findings


def test_the_product_keeps_every_contract_with_one_fake_and_a_suite_run_both_ways(walk_of) -> None:
    assert contract_findings(PRODUCT_ROOT, walk_of()) == []


PINGER_CONTRACT = """\
from typing import Protocol


class Pinger(Protocol):
    def ping(self) -> None: ...
"""

REAL_PINGER = """\
class RealPinger:
    def ping(self) -> None:
        return None
"""

FAKE_PINGER = """\
class FakePinger:
    def __init__(self) -> None:
        self.pings = 0

    def ping(self) -> None:
        self.pings += 1
"""

PINGER_SUITE = """\
from application.real_pinger import RealPinger
from tests.fakes import FakePinger


class PingerContract:
    def make(self):
        raise NotImplementedError

    def test_a_ping_is_accepted(self) -> None:
        assert self.make().ping() is None


class TestRealPingerKeepsTheContract(PingerContract):
    def make(self):
        return RealPinger()


class TestFakePingerKeepsTheContract(PingerContract):
    def make(self):
        return FakePinger()
"""

SUITE_PATH = "tests/integration/test_pinger_contract.py"
TREE = {
    "application/contracts.py": PINGER_CONTRACT,
    "application/real_pinger.py": REAL_PINGER,
    "tests/fakes.py": FAKE_PINGER,
    SUITE_PATH: PINGER_SUITE,
}


def plant(root: Path, replacing: dict[str, str | None] | None = None) -> Path:
    """The passing `Pinger` tree, with each file named in `replacing` changed, or gone for None."""
    files = {**TREE, **(replacing or {})}
    for relative, content in files.items():
        if content is None:
            continue
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


def findings_of(root: Path, walk_of: Callable[[Path | None], object]) -> list[str]:
    return contract_findings(root, walk_of(root))


def test_a_pinger_tree_that_keeps_the_rule_has_no_finding(walk_of, tmp_path: Path) -> None:
    assert findings_of(plant(tmp_path), walk_of) == []


def test_a_contracts_file_with_no_method_is_a_finding(walk_of, tmp_path: Path) -> None:
    empty = "from typing import Protocol\n\n\nclass Pinger(Protocol): ...\n"

    found = findings_of(plant(tmp_path, {"application/contracts.py": empty}), walk_of)

    assert len(found) == 1
    assert "contracts" in found[0]


def test_a_class_outside_the_support_module_that_defines_a_contract_method_is_a_finding(
    walk_of, tmp_path: Path
) -> None:
    stray = "class Stray:\n    def ping(self) -> None:\n        return None\n"

    found = findings_of(plant(tmp_path, {"tests/integration/test_stray.py": stray}), walk_of)

    assert len(found) == 1
    assert "tests/integration/test_stray.py:1" in found[0]


def test_a_class_outside_the_support_module_whose_base_is_the_fake_is_a_finding(
    walk_of, tmp_path: Path
) -> None:
    bare = "from tests.fakes import FakePinger\n\n\nclass Loud(FakePinger):\n    pass\n"
    attribute = "from tests import fakes\n\n\nclass Loud(fakes.FakePinger):\n    pass\n"

    for source in (bare, attribute):
        found = findings_of(plant(tmp_path, {"tests/integration/test_loud.py": source}), walk_of)

        assert len(found) == 1
        assert "tests/integration/test_loud.py:4" in found[0]


def test_a_missing_support_module_is_a_finding(walk_of, tmp_path: Path) -> None:
    found = findings_of(plant(tmp_path, {"tests/fakes.py": None}), walk_of)

    assert len(found) == 1
    assert "tests/fakes.py" in found[0]


def test_a_contract_with_no_fake_in_the_support_module_is_a_finding(
    walk_of, tmp_path: Path
) -> None:
    found = findings_of(
        plant(tmp_path, {"tests/fakes.py": "class FakeOther:\n    pass\n"}), walk_of
    )

    assert len(found) == 1
    assert "ping" in found[0]


def test_a_contract_with_a_suite_run_only_against_the_fake_is_a_finding(
    walk_of, tmp_path: Path
) -> None:
    fake_only = PINGER_SUITE.replace("RealPinger()", "FakePinger()")

    found = findings_of(plant(tmp_path, {SUITE_PATH: fake_only}), walk_of)

    assert len(found) == 1
    assert "ping" in found[0]


def test_a_tests_directory_with_no_module_is_a_finding(walk_of, tmp_path: Path) -> None:
    plant(tmp_path, {"tests/fakes.py": None, SUITE_PATH: None})
    (tmp_path / "tests").mkdir(exist_ok=True)

    found = findings_of(tmp_path, walk_of)

    assert len(found) == 1
    assert "no module" in found[0]
