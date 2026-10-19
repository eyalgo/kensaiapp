"""Layer-6 reach walks: what each part's code may touch, and what no test may patch (nfdr § 1.3).

Checks SRS NFR-2 (saved data is written in one place), NFR-4 and NFR-8, and acceptance criterion
AC-13 (the date comes from a clock handed in). NFDR QC-9, QC-20, QC-28, QC-37, QC-42, QC-44, QC-45
and QC-61 are the ones each test names. Each walk reads every module outside tests/ as a syntax tree
and fails when its part holds no module.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PARTS = {"domain", "application", "persistence", "web", "main", "errors"}
CLOCK_READS = ("datetime.now", "datetime.today", "date.today", "time.time", "time.localtime")
WRITES = ("os.replace", "os.rename", "os.remove", "os.unlink")
WRITE_MODE_LETTERS = set("wax+")
EXECUTING_READERS = ("pickle", "marshal", "shelve")
LENGTH_LITERALS = (200, 4000, "200", "4000")
STREAMS = ("sys.stdout", "sys.stderr", "sys.stdin")
OPERATING_SYSTEM_CHECKS = ("sys.platform", "os.name")
TESTS_DIRECTORY = Path(__file__).resolve().parent.parent
PATCHERS = ("monkeypatch.setattr", "mock.patch", "patch", "patch.object", "mock.patch.object")


def _imports(module, banned: tuple[str, ...]) -> list[str]:
    return [
        f"{module.path}: {name}"
        for name in module.imported()
        if any(name == b or name.startswith(b + ".") for b in banned)
    ]


def _ends_with(name: str, endings: tuple[str, ...]) -> bool:
    return any(name == e or name.endswith("." + e) for e in endings)


def domain_input_output(walk) -> list[str]:
    found = []
    for module in walk.modules("domain"):
        found += _imports(module, ("html",))
        for name, _call in module.calls():
            if name in {"open", "print", "input"} or _ends_with(name, CLOCK_READS):
                found.append(f"{module.path}: {name}")
    return found


def clock_reads(walk) -> list[str]:
    found = []
    for part in ("domain", "application", "persistence", "web"):
        for module in walk.modules(part):
            found += [
                f"{module.path}: {name}"
                for name, _call in module.calls()
                if _ends_with(name, CLOCK_READS)
            ]
    return found


def _opens_for_writing(name: str, call: ast.Call) -> bool:
    if name == "open":
        positions = [1]
    elif name.endswith(".open"):
        positions = [0]
    else:
        return False
    candidates = [call.args[i] for i in positions if len(call.args) > i]
    candidates += [keyword.value for keyword in call.keywords if keyword.arg == "mode"]
    return any(
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and WRITE_MODE_LETTERS & set(node.value)
        for node in candidates
    )


def file_writes_outside_persistence(walk) -> list[str]:
    found = []
    for part in sorted(PARTS - {"persistence"}):
        for module in walk.modules(part):
            for name, call in module.calls():
                is_write = (
                    name in WRITES
                    or name.endswith((".write_text", ".write_bytes"))
                    or _opens_for_writing(name, call)
                )
                if is_write:
                    found.append(f"{module.path}: {name}")
    return found


def default_location_outside_main(walk) -> list[str]:
    found = []
    for part in sorted(PARTS - {"persistence", "main"}):
        for module in walk.modules(part):
            found += [
                f"{module.path}: DEFAULT_LOCATION"
                for node in ast.walk(module.tree)
                if isinstance(node, ast.Name) and node.id == "DEFAULT_LOCATION"
            ]
    return found


def console_writers(walk) -> dict[str, set[str]]:
    """The modules that write to the console, grouped by part."""
    writers: dict[str, set[str]] = {}
    for module in walk.modules():
        uses = any(name == "print" for name, _call in module.calls()) or any(
            isinstance(node, ast.Attribute) and ast.unparse(node) in STREAMS
            for node in ast.walk(module.tree)
        )
        if uses:
            writers.setdefault(module.part, set()).add(str(module.path))
    return writers


def executing_readers(walk) -> list[str]:
    found = []
    for module in walk.modules():
        found += _imports(module, EXECUTING_READERS)
        found += [
            f"{module.path}: {name}" for name, _call in module.calls() if name in {"eval", "exec"}
        ]
    return found


def length_literals_outside_domain(walk) -> list[str]:
    found = []
    for part in sorted(PARTS - {"domain"}):
        for module in walk.modules(part):
            found += [
                f"{module.path}:{node.lineno}: {node.value!r}"
                for node in ast.walk(module.tree)
                if isinstance(node, ast.Constant)
                and not isinstance(node.value, bool)
                and isinstance(node.value, (int, str))
                and node.value in LENGTH_LITERALS
            ]
    return found


def operating_system_checks(walk) -> list[str]:
    found = []
    for module in walk.modules():
        found += _imports(module, ("msvcrt", "winreg"))
        for node in ast.walk(module.tree):
            if isinstance(node, ast.Attribute) and ast.unparse(node) in OPERATING_SYSTEM_CHECKS:
                found.append(f"{module.path}: {ast.unparse(node)}")
        found += [
            f"{module.path}: {name}" for name, _call in module.calls() if name == "platform.system"
        ]
    return found


def patches_of_a_product_module(source: str) -> list[str]:
    """Calls in one test module that patch a name inside a product module."""
    tree = ast.parse(source)
    product_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            if node.module.split(".")[0] in PARTS:
                product_names |= {alias.asname or alias.name for alias in node.names}
                product_names.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            product_names |= {
                (alias.asname or alias.name).split(".")[0]
                for alias in node.names
                if alias.name.split(".")[0] in PARTS
            }
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        called = ast.unparse(node.func)
        if called not in PATCHERS or not node.args:
            continue
        target = node.args[0]
        aimed = (
            isinstance(target, ast.Constant)
            and isinstance(target.value, str)
            and target.value.split(".")[0] in PARTS
        ) or ast.unparse(target).split(".")[0] in product_names
        if aimed:
            found.append(f"{called}({ast.unparse(target)})")
    return found


def test_domain_does_no_input_output_and_reads_no_clock(walk_of) -> None:
    """QC-20."""
    assert domain_input_output(walk_of()) == []


def test_default_location_and_clock_are_reached_only_where_the_clauses_allow(walk_of) -> None:
    """QC-42: only persistence writes a file, and only main names where. QC-44: no clock read."""
    assert file_writes_outside_persistence(walk_of()) == []
    assert default_location_outside_main(walk_of()) == []
    assert clock_reads(walk_of()) == []


def test_print_and_std_streams_appear_only_in_main_and_one_web_module(walk_of) -> None:
    """QC-45."""
    writers = console_writers(walk_of())
    assert set(writers) <= {"main", "web"}
    assert len(writers.get("web", set())) <= 1


def test_no_executing_reader_is_used(walk_of) -> None:
    """QC-37."""
    assert executing_readers(walk_of()) == []


def test_no_test_patches_a_product_module() -> None:
    """QC-28: every test module, this one included."""
    found = []
    for path in sorted(TESTS_DIRECTORY.rglob("*.py")):
        if ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        found += [
            f"{path.relative_to(TESTS_DIRECTORY)}: {patch}"
            for patch in patches_of_a_product_module(path.read_text(encoding="utf-8"))
        ]
    assert found == []


def test_no_length_literal_of_200_or_4000_outside_domain(walk_of) -> None:
    """QC-9."""
    assert length_literals_outside_domain(walk_of()) == []


def test_qc_61_holds(walk_of) -> None:
    """QC-61: no module outside tests/ checks the operating system or imports a Windows module."""
    assert operating_system_checks(walk_of()) == []


def test_each_walk_fails_when_its_directory_holds_no_module(walk_of, tmp_path: Path) -> None:
    empty = walk_of(tmp_path)
    for walk in (
        domain_input_output,
        clock_reads,
        file_writes_outside_persistence,
        default_location_outside_main,
        console_writers,
        executing_readers,
        length_literals_outside_domain,
        operating_system_checks,
    ):
        with pytest.raises(AssertionError):
            walk(empty)


def test_each_walk_finds_a_violation_planted_where_it_looks(walk_of, tmp_path: Path) -> None:
    """The walks can fail: one planted violation per clause is reported."""
    planted = {
        "domain/bad.py": (
            "import html\nimport time\nopen('x')\nprint('x')\ntime.time()\n"
            "import pickle\neval('1')\nx = 200\nimport os\nos.name\n"
        ),
        "application/bad.py": "from datetime import datetime\nx = 4000\ndatetime.now()\n",
        "persistence/bad.py": "x = 1\n",
        "web/bad.py": "import sys\nsys.stderr.write('x')\nimport msvcrt\n",
        "web/other.py": "print('x')\n",
        "main.py": "import os\nopen('f', 'w')\nos.replace('a', 'b')\nDEFAULT_LOCATION\n",
        "errors.py": "from pathlib import Path\nPath('f').write_text('x')\nimport platform\n",
    }
    for relative, source in planted.items():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    walk = walk_of(tmp_path)
    assert domain_input_output(walk)
    assert clock_reads(walk)
    assert file_writes_outside_persistence(walk)
    (tmp_path / "web" / "uses_location.py").write_text("DEFAULT_LOCATION\n", encoding="utf-8")
    assert default_location_outside_main(walk_of(tmp_path))
    assert len(console_writers(walk).get("web", set())) == 2
    assert executing_readers(walk)
    assert length_literals_outside_domain(walk)
    assert operating_system_checks(walk)
    assert patches_of_a_product_module(
        "import main\ndef test(monkeypatch):\n    monkeypatch.setattr(main, 'x', 1)\n"
    )
    assert patches_of_a_product_module(
        "def test(monkeypatch):\n    monkeypatch.setattr('persistence.saved_data.os', 1)\n"
    )
    assert (
        patches_of_a_product_module(
            "import os\ndef test(monkeypatch):\n    monkeypatch.setattr(os, 'getcwd', 1)\n"
        )
        == []
    )
