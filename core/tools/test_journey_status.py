"""Tests for `journey_status.py` — the walk/model layer (`scan`) and the render layer.

Fixture instance trees are built under `tmp_path` for every behaviour except the live-smoke case,
which reads this repo's own working root on purpose — see its name and docstring below.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

import journey_status as js


# ---------------------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------------------


def _write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _instance(tmp_path: Path, name: str = "dev") -> Path:
    """A minimal, complete instance root: `system/nemawashi/` + `system/shukuba/`, no projects."""
    root = tmp_path / name
    _write(root / "system" / "nemawashi" / "README.md", "# Seedbed\n")
    _write(root / "system" / "shukuba" / "README.md", "# Router\n")
    (root / "system" / "shukuba" / "trail").mkdir(parents=True, exist_ok=True)
    return root


def _project(root: Path, name: str) -> Path:
    """A project's `journey/` with the three empty subfolders (`nemawashi`, `shukuba`, `tobiishi`)."""
    journey = root / "system" / "projects" / name / "journey"
    (journey / "nemawashi").mkdir(parents=True, exist_ok=True)
    (journey / "shukuba").mkdir(parents=True, exist_ok=True)
    (journey / "tobiishi").mkdir(parents=True, exist_ok=True)
    return journey


def _seed_text(title: str, done: int = 0, pending: int = 0) -> str:
    lines = [f"# {title}", ""]
    lines += ["- [x] done item"] * done
    lines += ["- [ ] pending item"] * pending
    return "\n".join(lines) + "\n"


def _tree_hash(root: Path) -> str:
    """A hash of every file's relative path and bytes under `root`, for the read-only gate."""
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(root)).encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _find_project(model: js.InstanceModel, name: str) -> js.ProjectStatus:
    for project in model.projects:
        if project.name == name:
            return project
    raise AssertionError(f"no project named {name!r} in {[p.name for p in model.projects]}")


# ---------------------------------------------------------------------------------------
# Instance level
# ---------------------------------------------------------------------------------------


def test_instance_nemawashi_counts_root_seeds_unpicked_and_trail(tmp_path):
    root = _instance(tmp_path)
    _write(root / "system" / "nemawashi" / "2026-08-01_seed-one.md", _seed_text("Seed one"))
    _write(root / "system" / "nemawashi" / "2026-08-02_seed-two.md", _seed_text("Seed two"))
    _write(root / "system" / "nemawashi" / "unpicked" / "2026-07-01_candidate.md", "# Candidate\n")
    _write(root / "system" / "nemawashi" / "trail" / "2026-06-01_done.md", "# Done\n")

    model = js.scan(root)

    assert model.nemawashi.root_seed_count == 2
    assert model.nemawashi.unpicked_count == 1
    assert model.nemawashi.trail_count == 1


def test_the_drop_bin_is_counted_separately_from_the_trail(tmp_path):
    """A killed seed is not a walked one, so a reporter that folds the two says the seedbed finished
    work it never started. Both levels, because both have the bin."""
    root = _instance(tmp_path)
    _write(root / "system" / "nemawashi" / "trail" / "2026-06-01_walked.md", "# Walked\n")
    _write(root / "system" / "nemawashi" / "drop" / "2026-06-02_killed.md", "# Killed\n")
    _write(root / "system" / "nemawashi" / "drop" / "2026-06-03_killed.md", "# Killed too\n")
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "drop" / "2026-06-04_killed.md", "# Killed\n")

    model = js.scan(root)

    assert model.nemawashi.trail_count == 1
    assert model.nemawashi.drop_count == 2
    assert _find_project(model, "alpha").nemawashi.drop_count == 1


def test_a_missing_drop_bin_counts_zero_rather_than_failing(tmp_path):
    """A seedbed without the bin counts zero rather than raising — the bin is a `[create]` stub, so
    any seedbed stamped before it existed is missing it until something writes there."""
    root = _instance(tmp_path)
    _project(root, "alpha")

    model = js.scan(root)

    assert model.nemawashi.drop_count == 0
    assert _find_project(model, "alpha").nemawashi.drop_count == 0


def test_instance_shukuba_counts_trail(tmp_path):
    root = _instance(tmp_path)
    _write(root / "system" / "shukuba" / "trail" / "2026-07-01_station.md", "# Station\n")
    _write(root / "system" / "shukuba" / "trail" / "2026-07-02_station.md", "# Station 2\n")

    model = js.scan(root)

    assert model.shukuba.trail_count == 2


def test_readme_never_counted_as_a_seed_at_instance_level(tmp_path):
    root = _instance(tmp_path)

    model = js.scan(root)

    assert model.nemawashi.root_seed_count == 0


# ---------------------------------------------------------------------------------------
# Project discovery
# ---------------------------------------------------------------------------------------


def test_project_discovery_finds_every_directory_with_a_journey(tmp_path):
    root = _instance(tmp_path)
    _project(root, "alpha")
    _project(root, "beta")

    model = js.scan(root)

    assert sorted(p.name for p in model.projects) == ["alpha", "beta"]


def test_project_discovery_skips_a_directory_with_no_journey(tmp_path):
    root = _instance(tmp_path)
    _project(root, "alpha")
    (root / "system" / "projects" / "no-journey-here").mkdir(parents=True)

    model = js.scan(root)

    assert [p.name for p in model.projects] == ["alpha"]


def test_no_projects_directory_yields_zero_projects_and_still_scans(tmp_path):
    root = _instance(tmp_path)

    model = js.scan(root)

    assert model.projects == []
    assert js.render(model)  # renders without raising


# ---------------------------------------------------------------------------------------
# Folder-seed — a seed is `<slug>.md` or `<slug>/seed.md`, wherever a file-seed is counted
# ---------------------------------------------------------------------------------------


def _folder_seed(parent: Path, slug: str, title: str, done: int = 0, pending: int = 0) -> Path:
    """Write a folder-seed's `seed.md`, returning the folder."""
    folder = parent / slug
    _write(folder / "seed.md", _seed_text(title, done=done, pending=pending))
    return folder


def test_a_folder_seed_at_a_project_root_reads_active_with_its_seed_mds_title_and_checklist(
    tmp_path,
):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _folder_seed(
        journey / "nemawashi", "2026-08-01_the-folder-seed", "The folder seed", done=3, pending=2
    )

    model = js.scan(root)
    nemawashi = _find_project(model, "alpha").nemawashi

    assert nemawashi.state is js.NemawashiState.ACTIVE
    assert nemawashi.seed_title == "The folder seed"
    assert nemawashi.checklist_done == 3
    assert nemawashi.checklist_total == 5


def test_a_folder_seed_at_the_instance_root_reads_active_the_same_way(tmp_path):
    root = _instance(tmp_path)
    _folder_seed(
        root / "system" / "nemawashi", "2026-08-01_instance-folder-seed", "Instance folder seed"
    )

    assert js.scan(root).nemawashi.state is js.NemawashiState.ACTIVE


def test_one_file_seed_and_one_folder_seed_at_a_root_count_two_and_trip_the_pick_invariant(
    tmp_path,
):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "2026-08-01_a.md", _seed_text("A"))
    _folder_seed(journey / "nemawashi", "2026-08-02_b", "B")

    model = js.scan(root)
    nemawashi = _find_project(model, "alpha").nemawashi
    hits = [v for v in model.violations if v.check == 1]

    assert nemawashi.root_seed_count == 2
    assert nemawashi.state is js.NemawashiState.NO_PICK
    assert len(hits) == 1
    assert hits[0].where == "alpha"


def test_a_folder_seed_under_unpicked_trail_and_drop_counts_toward_each_bin(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _folder_seed(journey / "nemawashi" / "unpicked", "2026-07-01_candidate", "Candidate")
    _folder_seed(journey / "nemawashi" / "trail", "2026-06-01_walked", "Walked")
    _folder_seed(journey / "nemawashi" / "drop", "2026-06-02_killed", "Killed")

    model = js.scan(root)
    nemawashi = _find_project(model, "alpha").nemawashi

    assert nemawashi.unpicked_count == 1
    assert nemawashi.trail_count == 1
    assert nemawashi.drop_count == 1


def test_a_folder_with_no_seed_md_is_not_a_seed(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    (journey / "nemawashi" / "2026-08-01_empty-folder").mkdir(parents=True)

    model = js.scan(root)
    nemawashi = _find_project(model, "alpha").nemawashi

    assert nemawashi.state is js.NemawashiState.EMPTY
    assert nemawashi.root_seed_count == 0


# ---------------------------------------------------------------------------------------
# Nemawashi state
# ---------------------------------------------------------------------------------------


def test_nemawashi_one_root_seed_is_active_with_title_and_checklist(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(
        journey / "nemawashi" / "2026-08-01_the-seed.md",
        _seed_text("The active seed", done=2, pending=5),
    )

    model = js.scan(root)
    nemawashi = _find_project(model, "alpha").nemawashi

    assert nemawashi.state is js.NemawashiState.ACTIVE
    assert nemawashi.seed_title == "The active seed"
    assert nemawashi.checklist_done == 2
    assert nemawashi.checklist_total == 7


def test_a_seed_whose_open_items_are_all_nested_does_not_read_finished(tmp_path):
    """An item indented under another is still an item — `core/templates/project-templates/
    setup_seed_template.md` stamps four of them into every define-the-product seed, so a count anchored
    on a line start renders those seeds finished while their nested work is untouched."""
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(
        journey / "nemawashi" / "2026-08-01_the-seed.md",
        "# The nested seed\n\n"
        "- [x] 1. a top-level item\n"
        "- [x] 2. another top-level item\n"
        "  - [ ] 2\u21b3. nested under it, still open\n"
        "  - [ ] 2\u21b3. and another\n",
    )

    model = js.scan(root)
    nemawashi = _find_project(model, "alpha").nemawashi

    assert (nemawashi.checklist_done, nemawashi.checklist_total) == (2, 4)
    assert nemawashi.checklist_done != nemawashi.checklist_total


def test_nemawashi_zero_root_seeds_is_empty(tmp_path):
    root = _instance(tmp_path)
    _project(root, "alpha")

    model = js.scan(root)
    nemawashi = _find_project(model, "alpha").nemawashi

    assert nemawashi.state is js.NemawashiState.EMPTY
    assert nemawashi.seed_title is None


def test_nemawashi_more_than_one_root_seed_is_no_pick(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "2026-08-01_a.md", _seed_text("A"))
    _write(journey / "nemawashi" / "2026-08-02_b.md", _seed_text("B"))

    model = js.scan(root)
    nemawashi = _find_project(model, "alpha").nemawashi

    assert nemawashi.state is js.NemawashiState.NO_PICK
    assert nemawashi.seed_title is None


def test_nemawashi_zero_root_seeds_over_a_full_pool_is_no_pick(tmp_path):
    """The row that shipped wrong. Under displacement an empty root meant an empty seedbed, because
    every candidate sat at the root. Under the reversal the pool lives in `unpicked/`, so an empty root
    means *nothing is picked* — and a seedbed holding 27 candidates reporting `empty` tells a reader the
    opposite of its state."""
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "unpicked" / "2026-08-01_a.md", _seed_text("A"))
    _write(journey / "nemawashi" / "unpicked" / "2026-08-02_b.md", _seed_text("B"))

    model = js.scan(root)
    nemawashi = _find_project(model, "alpha").nemawashi

    assert nemawashi.state is js.NemawashiState.NO_PICK
    assert nemawashi.root_seed_count == 0
    assert nemawashi.unpicked_count == 2
    assert nemawashi.seed_title is None


def test_nemawashi_empty_means_the_whole_seedbed_including_the_pool(tmp_path):
    """`empty` is now the narrower claim: nothing at the root *and* nothing in the pool. An `unpicked/`
    that exists but holds nothing is still empty — the folder is a `[create]` stub, not a candidate."""
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    (journey / "nemawashi" / "unpicked").mkdir(parents=True, exist_ok=True)

    model = js.scan(root)
    nemawashi = _find_project(model, "alpha").nemawashi

    assert nemawashi.state is js.NemawashiState.EMPTY
    assert nemawashi.unpicked_count == 0


def test_nemawashi_one_root_seed_is_active_however_full_the_pool(tmp_path):
    """The pool's size says nothing about whether an idea is active — only the root does."""
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "2026-08-03_c.md", _seed_text("C"))
    for i in range(5):
        _write(journey / "nemawashi" / "unpicked" / f"2026-08-0{i}_x.md", _seed_text(f"X{i}"))

    model = js.scan(root)
    nemawashi = _find_project(model, "alpha").nemawashi

    assert nemawashi.state is js.NemawashiState.ACTIVE
    assert nemawashi.seed_title == "C"
    assert nemawashi.unpicked_count == 5


def test_instance_nemawashi_carries_the_same_three_states_as_a_project(tmp_path):
    """`2026-08-19_the-model-inverts` removed the instance seedbed's exemption from check 1, so the
    instance has a pick like any seedbed. It reported counts and no state, which left the one thing a
    reader wants — is an idea active here — answerable only by arithmetic."""
    root = _instance(tmp_path)
    for i in range(3):
        _write(root / "system" / "nemawashi" / "unpicked" / f"2026-08-0{i}_s.md", _seed_text(f"S{i}"))

    assert js.scan(root).nemawashi.state is js.NemawashiState.NO_PICK

    _write(root / "system" / "nemawashi" / "2026-08-09_active.md", _seed_text("Active one"))
    assert js.scan(root).nemawashi.state is js.NemawashiState.ACTIVE


def test_instance_nemawashi_with_nothing_anywhere_is_empty(tmp_path):
    root = _instance(tmp_path)

    assert js.scan(root).nemawashi.state is js.NemawashiState.EMPTY


def test_nemawashi_readme_at_project_root_is_not_counted_as_a_seed(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "README.md", "# Seedbed\n")

    model = js.scan(root)
    nemawashi = _find_project(model, "alpha").nemawashi

    assert nemawashi.state is js.NemawashiState.EMPTY
    assert nemawashi.root_seed_count == 0


# ---------------------------------------------------------------------------------------
# Shukuba state
# ---------------------------------------------------------------------------------------


def test_shukuba_one_open_station_reports_open_state_and_title(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "shukuba" / "2026-08-01_the-station.md", "# The open station\n")

    model = js.scan(root)
    shukuba = _find_project(model, "alpha").shukuba

    assert shukuba.state is js.ShukubaState.OPEN
    assert shukuba.station_title == "The open station"


def test_shukuba_zero_open_stations_is_none_open(tmp_path):
    root = _instance(tmp_path)
    _project(root, "alpha")

    model = js.scan(root)
    shukuba = _find_project(model, "alpha").shukuba

    assert shukuba.state is js.ShukubaState.NONE_OPEN
    assert shukuba.station_title is None


def test_shukuba_counts_parked_and_trail(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "shukuba" / "parked" / "2026-07-01_parked.md", "# Parked\n")
    _write(journey / "shukuba" / "trail" / "2026-07-01_done.md", "# Done\n")
    _write(journey / "shukuba" / "trail" / "2026-07-02_done.md", "# Done 2\n")

    model = js.scan(root)
    shukuba = _find_project(model, "alpha").shukuba

    assert shukuba.parked_count == 1
    assert shukuba.trail_count == 2


def test_shukuba_readme_is_not_counted_as_an_open_station(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "shukuba" / "README.md", "# Router\n")

    model = js.scan(root)
    shukuba = _find_project(model, "alpha").shukuba

    assert shukuba.state is js.ShukubaState.NONE_OPEN


# ---------------------------------------------------------------------------------------
# Tobiishi state
# ---------------------------------------------------------------------------------------


def test_tobiishi_active_change_reports_change_request_presence(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "tobiishi" / "2026-08-01_a-change" / "change_request.md", "# Change\n")
    (journey / "tobiishi" / "2026-08-02_no-request").mkdir(parents=True)

    model = js.scan(root)
    tobiishi = _find_project(model, "alpha").tobiishi
    by_name = {c.name: c.has_change_request for c in tobiishi.changes}

    assert by_name == {
        "2026-08-01_a-change": True,
        "2026-08-02_no-request": False,
    }


def test_tobiishi_trail_is_counted_and_excluded_from_active_changes(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    (journey / "tobiishi" / "trail" / "2026-07-01_past-change").mkdir(parents=True)
    (journey / "tobiishi" / "trail" / "2026-07-02_past-change").mkdir(parents=True)

    model = js.scan(root)
    tobiishi = _find_project(model, "alpha").tobiishi

    assert tobiishi.trail_count == 2
    assert tobiishi.changes == []


def _tobiishi_block_lines(root):
    lines = js.render(js.scan(root)).splitlines()
    start = lines.index("<h3>Tobiishi</h3>")
    return lines[start + 1 : lines.index("</div>", start)]


def test_tobiishi_drop_is_counted_and_never_an_active_change(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    (journey / "tobiishi" / "trail" / "2026-07-01_a").mkdir(parents=True)
    (journey / "tobiishi" / "drop" / "2026-07-02_b").mkdir(parents=True)
    (journey / "tobiishi" / "drop" / "2026-07-03_c").mkdir(parents=True)

    tobiishi = _find_project(js.scan(root), "alpha").tobiishi

    assert tobiishi.changes == []
    assert tobiishi.trail_count == 1
    assert tobiishi.drop_count == 2
    assert _tobiishi_block_lines(root) == [
        "<p>no active change</p>",
        "<p>trail: 1</p>",
        "<p>drop: 2</p>",
    ]


def test_tobiishi_without_drop_counts_zero(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    (journey / "tobiishi" / "trail" / "2026-07-01_a").mkdir(parents=True)

    assert _find_project(js.scan(root), "alpha").tobiishi.drop_count == 0
    assert _tobiishi_block_lines(root)[-1] == "<p>drop: 0</p>"


def test_tobiishi_drop_beside_an_open_change_lists_only_the_change(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "tobiishi" / "2026-09-19_x" / "change_request.md", "# Change\n")
    (journey / "tobiishi" / "drop" / "2026-07-02_b").mkdir(parents=True)

    tobiishi = _find_project(js.scan(root), "alpha").tobiishi

    assert [c.name for c in tobiishi.changes] == ["2026-09-19_x"]
    block = _tobiishi_block_lines(root)
    assert "<p>2026-09-19_x</p>" in block
    assert "<p>drop</p>" not in block
    assert "<p>drop: 1</p>" in block


# ---------------------------------------------------------------------------------------
# Absent folders read as zero
# ---------------------------------------------------------------------------------------


def test_absent_unpicked_trail_and_parked_scan_as_zero_without_exception(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "2026-08-01_seed.md", _seed_text("Seed"))

    model = js.scan(root)
    project = _find_project(model, "alpha")

    assert project.nemawashi.unpicked_count == 0
    assert project.nemawashi.trail_count == 0
    assert project.shukuba.parked_count == 0
    assert project.shukuba.trail_count == 0
    assert project.tobiishi.trail_count == 0


# ---------------------------------------------------------------------------------------
# Check 1 — the pick invariant
# ---------------------------------------------------------------------------------------


def test_check1_no_violation_when_unpicked_nonempty_and_exactly_one_root_seed(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "2026-08-01_seed.md", _seed_text("Seed"))
    _write(journey / "nemawashi" / "unpicked" / "2026-07-01_candidate.md", "# Candidate\n")

    model = js.scan(root)

    assert [v for v in model.violations if v.check == 1] == []


def test_check1_no_violation_when_root_is_empty_and_unpicked_is_nonempty(tmp_path):
    """Inverts: root 0 with a non-empty `unpicked/` is now legal — Examples row 2 (T2/T3)."""
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "unpicked" / "2026-07-01_candidate.md", "# Candidate\n")

    model = js.scan(root)

    assert [v for v in model.violations if v.check == 1] == []


def test_check1_violation_when_root_has_two_seeds_and_unpicked_is_nonempty(tmp_path):
    """The violation survives, but its cause is the root count, not `unpicked/` — Examples row 4 (T6)."""
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "2026-08-01_a.md", _seed_text("A"))
    _write(journey / "nemawashi" / "2026-08-02_b.md", _seed_text("B"))
    _write(journey / "nemawashi" / "unpicked" / "2026-07-01_candidate.md", "# Candidate\n")

    model = js.scan(root)
    hits = [v for v in model.violations if v.check == 1]

    assert len(hits) == 1
    assert hits[0].where == "alpha"
    assert "2" in hits[0].message


def test_check1_no_violation_when_unpicked_empty_and_one_root_seed(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "2026-08-01_seed.md", _seed_text("Seed"))
    (journey / "nemawashi" / "unpicked").mkdir(parents=True)

    model = js.scan(root)

    assert [v for v in model.violations if v.check == 1] == []


def test_check1_violation_fires_at_instance_level_when_root_has_more_than_one_seed(tmp_path):
    """Becomes its opposite: check 1 now applies to the instance seedbed too — Examples row 5 (T4)."""
    root = _instance(tmp_path)
    for i in range(13):
        _write(root / "system" / "nemawashi" / f"2026-08-{i:02d}_seed.md", _seed_text(f"Seed {i}"))
    _write(root / "system" / "nemawashi" / "unpicked" / "candidate.md", "# Candidate\n")

    model = js.scan(root)
    hits = [v for v in model.violations if v.check == 1]

    assert len(hits) == 1
    assert hits[0].where == "system/nemawashi/"


def test_check1_no_violation_at_instance_level_when_root_is_empty_and_unpicked_nonempty(tmp_path):
    """T4 extends check 1 to the instance, so T2/T3 must hold there too — the likeliest wrong
    implementation copies the old project-level `root != 1` shape, which every other test here
    would still pass."""
    root = _instance(tmp_path)
    _write(root / "system" / "nemawashi" / "unpicked" / "candidate.md", "# Candidate\n")

    model = js.scan(root)

    assert [v for v in model.violations if v.check == 1] == []


def test_check1_no_violation_at_instance_level_when_root_has_exactly_one_seed(tmp_path):
    """M8 read at the instance: the model is identical at both levels, so a root holding
    **exactly one** seed is the instance's normal *active* shape (M2), not a violation.

    The instance's legal shapes are asserted at 0 seeds and its violations at 2 and 13; the
    one root count in between — the only count that means "an idea is active here" — had no
    assertion. An implementation that flagged any seed at the instance root (`>= 1`, the
    shape a session reaches for when it reads T4 as "the instance is now checked" without
    M8's "the same way") passes every other test in this file, including the live smoke,
    whose instance root holds 13 today so `>= 1` and `> 1` agree there.
    """
    root = _instance(tmp_path)
    _write(root / "system" / "nemawashi" / "2026-08-01_active.md", _seed_text("Active"))
    _write(root / "system" / "nemawashi" / "unpicked" / "candidate.md", "# Candidate\n")

    model = js.scan(root)

    assert [v for v in model.violations if v.check == 1] == []


def test_check1_violation_when_root_has_two_seeds_and_unpicked_is_absent(tmp_path):
    """T1's non-consultation clause: `unpicked/`'s contents are never read. Not in the Examples
    table — without this test, `root > 1 and unpicked > 0` would pass every other assertion here."""
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "2026-08-01_a.md", _seed_text("A"))
    _write(journey / "nemawashi" / "2026-08-02_b.md", _seed_text("B"))

    model = js.scan(root)
    hits = [v for v in model.violations if v.check == 1]

    assert len(hits) == 1
    assert hits[0].where == "alpha"


def test_check1_no_violation_when_root_is_empty_and_unpicked_is_empty(tmp_path):
    """Examples row 3 — today only the *state* is asserted for this shape, never the violation set."""
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    (journey / "nemawashi" / "unpicked").mkdir(parents=True)

    model = js.scan(root)

    assert [v for v in model.violations if v.check == 1] == []


def test_violation_message_names_the_seedbed_and_the_root_seed_count(tmp_path):
    """T6 at both levels — a reader acts on the message without re-walking the tree."""
    root = _instance(tmp_path)
    for i in range(2):
        _write(root / "system" / "nemawashi" / f"2026-08-{i:02d}_seed.md", _seed_text(f"Seed {i}"))
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "2026-08-01_a.md", _seed_text("A"))
    _write(journey / "nemawashi" / "2026-08-02_b.md", _seed_text("B"))

    model = js.scan(root)
    hits = [v for v in model.violations if v.check == 1]

    assert len(hits) == 2
    instance_hit = next(v for v in hits if v.where == "system/nemawashi/")
    project_hit = next(v for v in hits if v.where == "alpha")
    assert "system/nemawashi/" in instance_hit.message and "2" in instance_hit.message
    assert "alpha" in project_hit.message and "2" in project_hit.message


# ---------------------------------------------------------------------------------------
# Check 2 — at most one open station
# ---------------------------------------------------------------------------------------


def test_check2_violation_when_two_stations_are_open(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "2026-08-01_seed.md", _seed_text("Seed"))
    _write(journey / "shukuba" / "2026-08-01_station-a.md", "# Station A\n")
    _write(journey / "shukuba" / "2026-08-02_station-b.md", "# Station B\n")

    model = js.scan(root)
    hits = [v for v in model.violations if v.check == 2]

    assert len(hits) == 1
    assert hits[0].where == "alpha"


def test_check2_no_violation_when_one_station_is_open(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "2026-08-01_seed.md", _seed_text("Seed"))
    _write(journey / "shukuba" / "2026-08-01_station-a.md", "# Station A\n")

    model = js.scan(root)

    assert [v for v in model.violations if v.check == 2] == []


# ---------------------------------------------------------------------------------------
# Check 3 — a station is open only while a seed is active
# ---------------------------------------------------------------------------------------


def test_check3_violation_when_station_open_and_nemawashi_is_no_pick(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "2026-08-01_a.md", _seed_text("A"))
    _write(journey / "nemawashi" / "2026-08-02_b.md", _seed_text("B"))
    _write(journey / "shukuba" / "2026-08-01_station.md", "# Station\n")

    model = js.scan(root)
    hits = [v for v in model.violations if v.check == 3]

    assert len(hits) == 1
    assert hits[0].where == "alpha"


def test_check3_violation_when_station_open_and_nemawashi_is_empty(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "shukuba" / "2026-08-01_station.md", "# Station\n")

    model = js.scan(root)
    hits = [v for v in model.violations if v.check == 3]

    assert len(hits) == 1
    assert hits[0].where == "alpha"


def test_check3_no_violation_when_station_open_and_a_seed_is_active(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "2026-08-01_seed.md", _seed_text("Seed"))
    _write(journey / "shukuba" / "2026-08-01_station.md", "# Station\n")

    model = js.scan(root)

    assert [v for v in model.violations if v.check == 3] == []


# ---------------------------------------------------------------------------------------
# Check 4 — a tobiishi change folder holds a change_request.md
# ---------------------------------------------------------------------------------------


def test_check4_violation_when_a_change_folder_has_no_change_request(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    (journey / "tobiishi" / "2026-08-01_a-change").mkdir(parents=True)

    model = js.scan(root)
    hits = [v for v in model.violations if v.check == 4]

    assert len(hits) == 1
    assert hits[0].where == "alpha"


def test_check4_no_violation_when_change_folder_has_a_change_request(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "tobiishi" / "2026-08-01_a-change" / "change_request.md", "# Change\n")

    model = js.scan(root)

    assert [v for v in model.violations if v.check == 4] == []


# ---------------------------------------------------------------------------------------
# Product path
# ---------------------------------------------------------------------------------------


def test_product_path_is_read_from_project_md(tmp_path):
    root = _instance(tmp_path)
    _project(root, "alpha")
    _write(
        root / "system" / "projects" / "alpha" / "project.md",
        "# Project Context — alpha\n\n"
        "**Product path:** core/tools   <!-- a comment -->\n",
    )

    model = js.scan(root)

    assert _find_project(model, "alpha").product_path == "core/tools"


def test_product_path_absent_project_md_is_not_an_error(tmp_path):
    root = _instance(tmp_path)
    _project(root, "alpha")

    model = js.scan(root)

    assert _find_project(model, "alpha").product_path is None


# ---------------------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------------------


def test_render_is_self_contained_and_references_no_external_host(tmp_path):
    """Self-contained means *no* external asset, not merely no literal `<script src`.

    The canonical external stylesheet is `<link rel="stylesheet" href="...">`, whose text
    never contains the substring `<link href`, and a relative `href="style.css"` carries no
    scheme either — so substring checks on those two spellings alone would pass a page that
    loads an external stylesheet. Assert the property instead: no `<link>` element at all,
    and every `src`/`href` in the document is a fragment or an inline `data:` URI.
    """
    root = _instance(tmp_path)
    _project(root, "alpha")

    model = js.scan(root)
    page = js.render(model)

    assert "<script src" not in page
    assert "<link" not in page
    assert "http://" not in page
    assert "https://" not in page

    refs = re.findall(r"""\b(?:src|href)\s*=\s*["']([^"']*)["']""", page)
    external = [r for r in refs if not (r.startswith("#") or r.startswith("data:"))]
    assert external == [], f"page references assets outside itself: {external}"


def test_render_includes_each_projects_name(tmp_path):
    root = _instance(tmp_path)
    _project(root, "alpha")
    _project(root, "beta")

    model = js.scan(root)
    page = js.render(model)

    assert "alpha" in page
    assert "beta" in page


def test_render_marks_a_violation_with_distinguishing_markup_not_just_text(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "2026-08-01_a.md", _seed_text("A"))
    _write(journey / "nemawashi" / "2026-08-02_b.md", _seed_text("B"))

    model = js.scan(root)
    page = js.render(model)

    assert model.violations  # the fixture carries a check-1 hit (root holds 2 seeds)
    assert "violation" in page.lower()
    # a class or similarly-named marker, not merely the word "violation" appearing in prose
    assert 'class="violation' in page or "class='violation" in page


# ---------------------------------------------------------------------------------------
# Read-only
# ---------------------------------------------------------------------------------------


def test_scan_and_render_leave_the_fixture_tree_byte_identical(tmp_path):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "2026-08-01_seed.md", _seed_text("Seed", done=1, pending=1))
    _write(journey / "shukuba" / "2026-08-01_station.md", "# Station\n")
    _write(journey / "tobiishi" / "2026-08-01_a-change" / "change_request.md", "# Change\n")

    before = _tree_hash(root)
    model = js.scan(root)
    js.render(model)
    after = _tree_hash(root)

    assert before == after


# ---------------------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------------------


def _busy_instance(tmp_path: Path) -> Path:
    """An instance rich enough for ordering to matter: several projects created out of
    alphabetical order, each with multiple seeds, stations, candidates and change folders,
    and carrying hits from all four checks."""
    root = _instance(tmp_path)
    for i in range(3):
        _write(root / "system" / "nemawashi" / f"2026-08-0{i}_instance-seed.md", _seed_text(f"I{i}"))

    # created deliberately out of alphabetical order
    for name in ("charlie", "alpha", "delta", "bravo"):
        journey = _project(root, name)
        _write(journey / "nemawashi" / "unpicked" / "2026-07-01_one.md", "# One\n")
        _write(journey / "nemawashi" / "unpicked" / "2026-07-02_two.md", "# Two\n")
        _write(journey / "shukuba" / "trail" / "2026-06-01_reached.md", "# Reached\n")

    # charlie: clean — one active seed, one open station, one well-formed change
    charlie = root / "system" / "projects" / "charlie" / "journey"
    _write(charlie / "nemawashi" / "2026-08-01_seed.md", _seed_text("Charlie seed", done=3, pending=4))
    _write(charlie / "shukuba" / "2026-08-01_station.md", "# Charlie station\n")
    _write(charlie / "tobiishi" / "2026-08-01_change" / "change_request.md", "# CR\n")

    # alpha: check 3 — no active idea (root 0, unpicked/ 2 no longer matters, T1), and a station open anyway
    alpha = root / "system" / "projects" / "alpha" / "journey"
    _write(alpha / "shukuba" / "2026-08-01_orphan-station.md", "# Orphan station\n")

    # delta: check 2 — two stations open against one active seed
    delta = root / "system" / "projects" / "delta" / "journey"
    _write(delta / "nemawashi" / "2026-08-01_seed.md", _seed_text("Delta seed"))
    _write(delta / "shukuba" / "2026-08-01_a.md", "# A\n")
    _write(delta / "shukuba" / "2026-08-02_b.md", "# B\n")

    # bravo: check 4 — change folders (created out of order) one of which has no request
    bravo = root / "system" / "projects" / "bravo" / "journey"
    _write(bravo / "nemawashi" / "2026-08-01_seed.md", _seed_text("Bravo seed"))
    (bravo / "tobiishi" / "2026-08-09_zulu").mkdir(parents=True)
    _write(bravo / "tobiishi" / "2026-08-02_kilo" / "change_request.md", "# CR\n")
    (bravo / "tobiishi" / "trail" / "2026-05-01_sealed").mkdir(parents=True)
    return root


def test_render_is_deterministic_over_an_unchanged_fixture_with_pinned_generated_at(tmp_path):
    """Determinism only has teeth on a tree big enough to be ordered wrongly.

    A single-project fixture is byte-identical across runs whatever the walk does with
    `iterdir()`, so it cannot tell a sorted walk from an arbitrary one. This uses the busy
    fixture — four projects created out of alphabetical order, multiple seeds, stations and
    change folders, violations from all four checks — so an unsorted walk can differ.
    """
    root = _busy_instance(tmp_path)
    pinned = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)

    first = js.render(js.scan(root, generated_at=pinned))
    second = js.render(js.scan(root, generated_at=pinned))

    assert first == second


def test_scan_orders_projects_and_changes_by_name_not_by_filesystem_order(tmp_path):
    """The ordering the deterministic bytes rest on, asserted directly."""
    root = _busy_instance(tmp_path)

    model = js.scan(root)

    assert [p.name for p in model.projects] == ["alpha", "bravo", "charlie", "delta"]
    bravo = _find_project(model, "bravo")
    assert [c.name for c in bravo.tobiishi.changes] == ["2026-08-02_kilo", "2026-08-09_zulu"]
    # `scan` checks the instance seedbed before the project loop, so its check-1 hit is first —
    # the fixture's 3 instance root seeds now trip check 1 (T4), where the old project-scoped
    # check never looked. Then project by project, in sorted-project order:
    #   alpha   — 0 root seeds (unpicked=2 no longer matters, T1): no check 1; a station open
    #             while empty (check 3)
    #   bravo   — one active seed, so no check 1; one change folder with no request (check 4)
    #   charlie — one active seed, one open station, a well-formed change: clean
    #   delta   — one active seed, but two stations open (check 2)
    assert [(v.check, v.where) for v in model.violations] == [
        (1, "system/nemawashi/"),
        (3, "alpha"),
        (4, "bravo"),
        (2, "delta"),
    ]


# ---------------------------------------------------------------------------------------
# The instance router is not a project shukuba (plan § Trap fences, 4)
# ---------------------------------------------------------------------------------------


def test_instance_shukuba_root_file_is_never_an_open_station_and_raises_no_violation(tmp_path):
    """`system/shukuba/` is a router, not a walked station — no `parked/`, never crossed by Tobiishi.

    A file sitting at its root must therefore not be read with the project shukuba's shape:
    it is not an open station, and checks 2 and 3 (which exist only for a walked station)
    must not fire on it. This is what would break if the two scans were ever unified.

    The T5 fence: extended, this fixture also seeds >1 instance-seedbed root seeds, so check 1
    fires (T4) — proving the extension did not drag checks 2/3 along with it.
    """
    root = _instance(tmp_path)
    _write(root / "system" / "shukuba" / "2026-08-01_router-note.md", "# A file at the router\n")
    _write(root / "system" / "nemawashi" / "2026-08-01_a.md", _seed_text("A"))
    _write(root / "system" / "nemawashi" / "2026-08-02_b.md", _seed_text("B"))

    model = js.scan(root)

    assert len(model.violations) == 1
    assert model.violations[0].check == 1
    assert model.violations[0].where == "system/nemawashi/"
    assert not hasattr(model.shukuba, "state")
    assert not hasattr(model.shukuba, "parked_count")
    assert model.shukuba.trail_count == 0


# ---------------------------------------------------------------------------------------
# CLI — the only write in the tool, and it lands nowhere else
# ---------------------------------------------------------------------------------------


def test_main_writes_only_the_out_page_and_leaves_the_scanned_tree_untouched(tmp_path, capsys):
    """Trap fence 5: read-only, always — the `--out` page is the tool's one and only write."""
    root = _busy_instance(tmp_path)
    out = tmp_path / "elsewhere" / "page.html"

    before = _tree_hash(root)
    exit_code = js.main(["--repo", str(root), "--out", str(out)])
    capsys.readouterr()

    assert exit_code == 0
    assert out.is_file()
    assert out.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
    assert _tree_hash(root) == before


def test_main_defaults_out_to_system_logs_journey_status_html(tmp_path, capsys):
    """The default the plan names: `<repo>/system/logs/journey_status.html`."""
    root = _instance(tmp_path)
    _project(root, "alpha")

    exit_code = js.main(["--repo", str(root)])
    capsys.readouterr()

    assert exit_code == 0
    assert (root / "system" / "logs" / "journey_status.html").is_file()


def test_main_defaults_repo_to_the_current_working_directory(tmp_path, capsys, monkeypatch):
    """`--repo` defaults to cwd, so the tool run from any instance root describes that root."""
    root = _busy_instance(tmp_path)
    out = tmp_path / "page.html"
    monkeypatch.chdir(root)

    assert js.main(["--out", str(out)]) == 0
    capsys.readouterr()

    page = out.read_text(encoding="utf-8")
    assert root.name in page
    assert "charlie" in page


# ---------------------------------------------------------------------------------------
# Live smoke — reads this repo's own working root, on purpose
# ---------------------------------------------------------------------------------------


def test_live_smoke_scan_of_this_repo_reports_every_project_and_a_migration_stable_check1_shape():
    """Depends on live repo state, not a fixture — see the plan's own note (`ad_hoc_plan.md`
    Task 1, "Live smoke, marked as such"). Under the new model (`root_seed_count > 1`), check 1
    fires for `system/nemawashi/` and several projects whose root holds more than one seed
    today — this instance's own migration off the retired model is the **next** Tobiishi (T7),
    so the violating count itself is not hard-coded here; only the shape (a check-1 hit iff
    root > 1, every seedbed, instance included) and one named negative survive migration.
    """
    repo_root = Path(__file__).resolve().parents[2]

    model = js.scan(repo_root)

    # Derived from disk, not pinned. A literal count made this test fail the day a twelfth project
    # was scaffolded (`product-planning`, 2026-08-24) — which is the defect the docstring above says
    # this test avoids for its other assertion, and did not avoid here. The scanner still has to find
    # *every* project; it just no longer has to find a number someone remembered to update.
    on_disk = {d.name for d in (repo_root / "system" / "projects").iterdir() if d.is_dir()}
    assert {p.name for p in model.projects} == on_disk

    check1_hits = {v.where for v in model.violations if v.check == 1}
    seedbeds: dict[str, int] = {"system/nemawashi/": model.nemawashi.root_seed_count}
    seedbeds.update({p.name: p.nemawashi.root_seed_count for p in model.projects})

    for where, root_seed_count in seedbeds.items():
        assert (where in check1_hits) == (root_seed_count > 1), (
            f"{where}: hit={where in check1_hits}, root_seed_count={root_seed_count}"
        )

    # example-6b5d3e's root holds exactly one seed today (the flip's intended effect) — no hit,
    # which is the legal-shape flip TL Review Note 5 / design Note 5 name as intended, not a red.
    assert "example-6b5d3e" not in check1_hits


# --- integrity review: Task 1 — `README.md` stays excluded beside a folder-seed -------------------
#
# Written from `shukuba-refine-runs-and-its-seed-becomes-a-folder.md` § Task 1, not from the code.


def test_a_project_root_holding_readme_and_one_folder_seed_reads_active_with_one_root_seed(
    tmp_path,
):
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    _write(journey / "nemawashi" / "README.md", "# Seedbed\n")
    _folder_seed(
        journey / "nemawashi", "2026-08-01_the-folder-seed", "The folder seed", done=1, pending=1
    )

    nemawashi = _find_project(js.scan(root), "alpha").nemawashi

    assert nemawashi.state is js.NemawashiState.ACTIVE
    assert nemawashi.root_seed_count == 1
    assert nemawashi.seed_title == "The folder seed"


def test_a_folder_seeds_report_files_do_not_change_its_checklist_or_count(tmp_path):
    """Only `seed.md` is the seed: a report inside the folder carrying its own checkboxes is not
    read."""
    root = _instance(tmp_path)
    journey = _project(root, "alpha")
    folder = _folder_seed(journey / "nemawashi", "2026-08-01_s", "S", done=1, pending=2)
    _write(folder / "2026-08-05_unit_report.md", "# Report\n\n## Stations\n\n- [x] a\n- [x] b\n")

    nemawashi = _find_project(js.scan(root), "alpha").nemawashi

    assert nemawashi.root_seed_count == 1
    assert (nemawashi.checklist_done, nemawashi.checklist_total) == (1, 3)
    assert nemawashi.seed_title == "S"
