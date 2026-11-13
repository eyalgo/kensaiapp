"""Layer-6 pin checks: every dependency is pinned exactly, and `uv.lock` fixes each at its pin.

Checks SRS NFR-9 (the product can be rebuilt as it was). Change spec rules CP-28 and CP-662, and
NFDR QC-39 and QC-59, are the ones each root test names. CP-773 to CP-778 hold the same bar over
the Behave folder's `.behave/pyproject.toml`, in `behave_findings`, and CP-779 runs each case on a
copy of the product in `tmp_path`. `EXACT` refuses a wildcard version for both sets (CP-773).
"""

from __future__ import annotations

import re
import shutil
import tomllib
from pathlib import Path

import pytest

PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent
EXACT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*(\[[A-Za-z0-9,._-]+\])?==[^=<>!~,;*\s]+")


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


BEHAVE_FOLDER = ".behave"
MANIFEST_UNREADABLE = "manifest missing or not readable TOML"
NOTHING_DECLARED = "manifest declares no dependency"
NOT_PINNED_EXACTLY = "requirement not pinned exactly"


def read_toml(path: Path) -> dict | None:
    """The file's TOML, or None when it is not a regular file or cannot be read as TOML."""
    if not path.is_file():
        return None
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None


def behave_findings(product: Path) -> list[str]:
    """One finding per failure of QC-39's checks over the Behave folder under `product`."""
    behave = product / BEHAVE_FOLDER
    if not behave.exists():
        return []
    document = read_toml(behave / "pyproject.toml")
    if document is None:
        return [f"{MANIFEST_UNREADABLE}: {BEHAVE_FOLDER}/pyproject.toml"]
    declared = declared_dependencies(document)
    if not declared:
        return [f"{NOTHING_DECLARED}: {BEHAVE_FOLDER}/pyproject.toml"]
    return [f"{NOT_PINNED_EXACTLY}: {entry}" for entry in declared if not EXACT.fullmatch(entry)]


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


def test_the_exact_pattern_refuses_a_wildcard_version() -> None:
    """CP-773: `==1.*` names a series, not one version, so it is no exact pin."""
    assert EXACT.fullmatch("httpx==1.*") is None
    assert EXACT.fullmatch("httpx[http2]==1.*") is None
    assert EXACT.fullmatch("httpx==0.28.1")


COPY_LEAVES_OUT = (".venv", ".pytest_cache", "__pycache__")


@pytest.fixture
def product_copy(tmp_path: Path) -> Path:
    """A copy of the product in `tmp_path`, so a case edits only the copy's `.behave/`."""
    copy = tmp_path / "product"
    shutil.copytree(PRODUCT_ROOT, copy, ignore=shutil.ignore_patterns(*COPY_LEAVES_OUT))
    return copy


def write_manifest(product: Path, text: str) -> None:
    (product / ".behave" / "pyproject.toml").write_text(text, encoding="utf-8")


def test_the_behave_folder_of_the_product_holds_every_pin() -> None:
    """QC-39, CP-773 and CP-774 on the product's own tree."""
    assert behave_findings(PRODUCT_ROOT) == []


@pytest.mark.parametrize(
    ("manifest", "entry"),
    [
        pytest.param(
            '[project]\nname = "x"\ndependencies = ["httpx>=0.28"]\n',
            "httpx>=0.28",
            id="floor-in-project-dependencies",
        ),
        pytest.param(
            '[dependency-groups]\ndev = ["behave"]\n',
            "behave",
            id="bare-name-in-dependency-groups",
        ),
        pytest.param(
            '[project.optional-dependencies]\nweb = ["httpx~=0.28.1"]\n',
            "httpx~=0.28.1",
            id="compatible-release-in-optional-dependencies",
        ),
        pytest.param(
            '[project.optional-dependencies]\nweb = ["httpx==1.*"]\n',
            "httpx==1.*",
            id="wildcard-in-optional-dependencies",
        ),
        pytest.param(
            '[build-system]\nrequires = ["hatchling==1.27.0,<2"]\n',
            "hatchling==1.27.0,<2",
            id="second-specifier-in-build-system-requires",
        ),
    ],
)
def test_a_requirement_not_pinned_exactly_is_found(
    product_copy: Path, manifest: str, entry: str
) -> None:
    """CP-773: the finding names the entry that is not an exact pin."""
    write_manifest(product_copy, manifest)
    findings = behave_findings(product_copy)
    assert any(NOT_PINNED_EXACTLY in finding and entry in finding for finding in findings)


def make_manifest_absent(product: Path) -> None:
    (product / ".behave" / "pyproject.toml").unlink()


def make_behave_a_plain_file(product: Path) -> None:
    shutil.rmtree(product / ".behave")
    (product / ".behave").write_text("not a folder\n", encoding="utf-8")


def make_manifest_unreadable(product: Path) -> None:
    write_manifest(product, "dependencies = [unterminated\n")


@pytest.mark.parametrize(
    "damage",
    [
        pytest.param(make_manifest_absent, id="no-pyproject"),
        pytest.param(make_behave_a_plain_file, id="behave-is-a-plain-file"),
        pytest.param(make_manifest_unreadable, id="pyproject-is-not-toml"),
    ],
)
def test_a_missing_or_unreadable_manifest_is_found(product_copy: Path, damage) -> None:
    """CP-774: a manifest that cannot be read checks nothing, so it is a finding."""
    damage(product_copy)
    assert any(MANIFEST_UNREADABLE in finding for finding in behave_findings(product_copy))


def test_a_manifest_declaring_nothing_is_found(product_copy: Path) -> None:
    """CP-777: a manifest that declares no dependency would pass with nothing checked."""
    write_manifest(product_copy, '[project]\nname = "x"\ndependencies = []\n')
    assert any(NOTHING_DECLARED in finding for finding in behave_findings(product_copy))


def test_an_absent_behave_folder_finds_nothing(product_copy: Path) -> None:
    """CP-778: QC-1 lets the folder be absent, and then the Behave checks read nothing."""
    shutil.rmtree(product_copy / ".behave")
    assert behave_findings(product_copy) == []
