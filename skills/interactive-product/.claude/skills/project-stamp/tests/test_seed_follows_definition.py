"""The setup seed is the one the card's Definition: names, and a no-code product is never `full`.

Intent source: the owner, 2026-11-02 — software asks for the definition and takes any of the three;
no-code takes prd-and-finish-line or none, never full; setup stamps the seed the answer names. The
templates are core/templates/project-templates/setup_seed_template.md (full) and
setup_seed_prd_and_finish_line_template.md (prd-and-finish-line); none stamps no seed.
"""

from pathlib import Path

import pytest

SEED_DATE = "2026-01-02"
SEED = f"journey/nemawashi/{SEED_DATE}_define-the-product.md"
# Stations only the full chain walks. Named by their skills, which a prd-and-finish-line seed never names.
FULL_ONLY = ["product-srs", "product-uxd", "product-design", "product-content", "product-sdd"]


def _project(root) -> Path:
    return Path(root) / "system" / "projects" / "demo"


def _stamp(run, *flags):
    return run("demo", "--placement", "internal", "--date", SEED_DATE, *flags)


def _seed(run) -> str:
    return (_project(run.root) / SEED).read_text(encoding="utf-8")


def _ideas(run) -> list[str]:
    seedbed = _project(run.root) / "journey" / "nemawashi"
    return sorted(p.name for p in seedbed.iterdir() if p.is_file() and p.name != "README.md")


def _stations(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("- [ ] ")]


def test_full_stamps_the_whole_definition_seed(run):
    result = _stamp(run, "--type", "software", "--definition", "full")
    assert result.returncode == 0, result.stderr
    seed = _seed(run)
    assert all(skill in seed for skill in FULL_ONLY)
    assert seed.startswith("# Seed — define demo: PRD → finish line → (SRS ∥ EXPERIENCE) → SDD")


@pytest.mark.parametrize("project_type", ["software", "no-code"])
def test_prd_and_finish_line_stamps_a_seed_that_ends_at_the_finish_line(run, project_type):
    result = _stamp(run, "--type", project_type, "--definition", "prd-and-finish-line")
    assert result.returncode == 0, result.stderr
    seed = _seed(run)
    assert seed.startswith("# Seed — define demo: PRD → finish line\n")
    stations = _stations(seed)
    assert len(stations) == 2, stations
    assert "**product-prd**" in stations[0] and "**project-finish-line**" in stations[1]
    # no later station, and no forward reference to one
    for word in FULL_ONLY + ["SRS", "SDD", "EXPERIENCE", "UXD"]:
        assert word not in seed, f"a prd-and-finish-line seed names {word}"
    assert "This seed ends at the finish line." in seed
    assert "<project>" not in seed


def test_no_code_with_no_flag_is_prd_and_finish_line_and_stamps_its_seed(run):
    result = _stamp(run, "--type", "no-code")
    assert result.returncode == 0, result.stderr
    assert len(_stations(_seed(run))) == 2


@pytest.mark.parametrize("project_type", ["software", "no-code"])
def test_none_stamps_no_definition_seed(run, project_type):
    result = _stamp(run, "--type", project_type, "--definition", "none")
    assert result.returncode == 0, result.stderr
    assert _ideas(run) == []
    assert SEED not in result.stdout
    # the rest of the seedbed is still there for the work that comes
    assert (_project(run.root) / "journey" / "nemawashi" / "README.md").is_file()
    assert (_project(run.root) / "journey" / "nemawashi" / "unpicked" / ".gitkeep").is_file()


def test_a_no_code_product_is_never_full(run):
    result = _stamp(run, "--type", "no-code", "--definition", "full")
    assert result.returncode == 2
    assert "a no-code product cannot be defined 'full'" in result.stderr
    assert "prd-and-finish-line or none" in result.stderr
    assert not _project(run.root).exists()


def test_the_older_value_is_not_stamped(run):
    """`prd-agari` is the value's retired name, and the stamp never writes it."""
    result = _stamp(run, "--type", "no-code", "--definition", "prd-agari")
    assert result.returncode == 2
    assert not _project(run.root).exists()
