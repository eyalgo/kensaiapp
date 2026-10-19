"""The §2 tree it must create, the project.md bindings, and what it must NOT create.

Intent source: project-stamp SKILL.md "What it creates (and what it must not)"
and kensaiapp_structure.md §2.
"""

from pathlib import Path

# Pinned so the seed's <YYYY-MM-DD>_ filename is predictable in assertions.
SEED_DATE = "2026-01-02"
SEED = f"journey/nemawashi/{SEED_DATE}_define-the-product.md"

# The exact per-project tree §2 prescribes, for a project named "demo".
EXPECTED_TREE = [
    "project.md",
    "agari.md",
    "doctrine/demo_doctrine.md",
    "doctrine/ai_responsibility.md",
    "journey/nemawashi/README.md",
    SEED,
    "journey/nemawashi/unpicked/.gitkeep",
    "journey/nemawashi/trail/.gitkeep",
    "journey/nemawashi/drop/.gitkeep",
    "journey/shukuba/README.md",
    "journey/shukuba/parked/.gitkeep",
    "journey/shukuba/trail/.gitkeep",
    "journey/tobiishi/trail/.gitkeep",
    "contexts/CONTEXT_PM.md",
]

# The definition chain the seed recommends, in order. Each entry is the station's *skill*
# name — "UXD" as a bare word also appears in the seed's title, so matching on it would
# assert nothing about where the station sits.
SEED_STATIONS = [
    "product-prd",
    "project-agari",
    "product-srs",
    "product-uxd",
    "product-design",
    "product-sdd",
]


def _project_dir(root):
    return Path(root) / "system" / "projects" / "demo"


def _scaffold_internal(run):
    return run(
        "demo",
        "--placement", "internal",
        "--execution-type", "headless",
        "--test-command", "pytest tests/",
        "--date", SEED_DATE,
    )


def test_internal_creates_full_section2_tree(run):
    result = _scaffold_internal(run)
    assert result.returncode == 0, result.stderr
    proj = _project_dir(run.root)
    for rel in EXPECTED_TREE:
        assert (proj / rel).exists(), (
            f"missing {rel}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def test_internal_binds_default_products_path_and_exec_fields(run):
    result = _scaffold_internal(run)
    assert result.returncode == 0, result.stderr
    project_md = (_project_dir(run.root) / "project.md").read_text(encoding="utf-8")
    # internal placement → Product path defaults to products/<name>
    assert "products/demo" in project_md
    # the execution fields the caller passed are stamped in
    assert "headless" in project_md
    assert "pytest tests/" in project_md


def test_creates_no_product_docs_or_code(run):
    result = _scaffold_internal(run)
    assert result.returncode == 0, result.stderr
    proj = _project_dir(run.root)
    # the scaffolder only points at the product; it must never author its docs/code
    assert not (proj / "docs").exists()
    assert not (Path(run.root) / "products" / "demo").exists()


def test_creates_no_brand_doctrine(run):
    """The project brand doctrine left the per-project layer with the other twelve (`a29cfc6`), so
    the scaffolder must not stamp one. EXPECTED_TREE cannot carry this: it is asserted as a **subset**
    (`for rel in EXPECTED_TREE: assert (proj / rel).exists()`), so dropping an entry from it proves
    nothing — a scaffolder that still stamped the file would pass every assertion in this file. The
    absence is only pinned by asserting it."""
    result = _scaffold_internal(run)
    assert result.returncode == 0, result.stderr
    assert not (_project_dir(run.root) / "doctrine" / "brand.md").exists()


def test_setup_seed_names_the_definition_chain_in_order(run):
    result = _scaffold_internal(run)
    assert result.returncode == 0, result.stderr
    seed = (_project_dir(run.root) / SEED).read_text(encoding="utf-8")
    # every station is named, and in the order the chain is walked
    positions = [seed.find(station) for station in SEED_STATIONS]
    for station, pos in zip(SEED_STATIONS, positions):
        assert pos != -1, f"seed does not name station {station}"
    assert positions == sorted(positions), f"stations out of order: {positions}"
    # the project token is substituted, not left in the stamped file
    assert "<project>" not in seed
    assert "demo" in seed


def test_pm_context_is_stamped_as_an_empty_placeholder(run):
    """§2 lists contexts/CONTEXT_PM.md as created at scaffold time. It is the only per-role
    context a kensaiapp has, and the change lifecycle writes it — so what is created here is
    the placeholder, with the project token substituted and no change recorded in it yet."""
    result = _scaffold_internal(run)
    assert result.returncode == 0, result.stderr
    ctx = (_project_dir(run.root) / "contexts" / "CONTEXT_PM.md").read_text(encoding="utf-8")
    assert "<name>" not in ctx
    assert "demo" in ctx
    # created empty of content: the placeholder notice stands until tobiishi-open overwrites it
    assert "PLACEHOLDER" in ctx


def test_setup_seed_is_the_only_idea_at_the_seedbed_root(run):
    """One active idea at the root — the seedbed's invariant, true from creation."""
    result = _scaffold_internal(run)
    assert result.returncode == 0, result.stderr
    seedbed = _project_dir(run.root) / "journey" / "nemawashi"
    ideas = [p.name for p in seedbed.iterdir() if p.is_file() and p.name != "README.md"]
    assert ideas == [f"{SEED_DATE}_define-the-product.md"], ideas


def test_newborn_seedbed_has_an_empty_candidate_pool(run):
    """The other half of "born with its setup seed active and an empty `unpicked/`".

    The sibling above pins the root; nothing pinned the pool. Under the inverted model the two
    together are the claim — a root of exactly one and a pool of none is what "active" looks
    like, and a scaffolder that also seeded a candidate into `unpicked/` (or stamped the setup
    seed there instead of *as well*) would pass every other assertion in this file. `.gitkeep`
    is scaffold's own and is not a candidate.
    """
    result = _scaffold_internal(run)
    assert result.returncode == 0, result.stderr
    unpicked = _project_dir(run.root) / "journey" / "nemawashi" / "unpicked"
    assert unpicked.is_dir()
    candidates = [p.name for p in unpicked.iterdir() if p.name != ".gitkeep"]
    assert candidates == [], candidates


def test_success_output_lists_core_and_created_files(run):
    result = _scaffold_internal(run)
    assert result.returncode == 0, result.stderr
    # on success it reports the resolved <CORE> and the files it created
    assert str(run.core) in result.stdout
    assert "project.md" in result.stdout
