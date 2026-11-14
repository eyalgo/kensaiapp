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

from collections.abc import Callable
from pathlib import Path

PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent
SUPPORT_MODULE = Path("tests") / "fakes.py"
CONTRACTS_MODULE = Path("application") / "contracts.py"


def contract_findings(root: Path, walk) -> list[str]:  # type: ignore[no-untyped-def]
    raise NotImplementedError


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
