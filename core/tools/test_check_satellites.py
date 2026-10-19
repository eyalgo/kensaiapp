"""Contract tests for `check_satellites.py`.

Every test builds a throwaway instance root under `tmp_path` — a roster, a host `.claude/`, and
however many satellites the case needs. Nothing here reads or touches a live instance, which is
also the property the tool itself has to hold: it is a check, and a check that writes is not one.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import check_satellites
import link_satellite


ROSTER = """\
# Satellites of this host

Prose the parser must ignore, including a stray table:

| kind | what it is for | signature |
|---|---|---|
| consumer | builds its own product | **no skills layer** |
| producer | its output is evidence | a root `skills/` that is a **real directory** |

## Consumers — build their own product here; nothing flows back

| satellite | path |
|---|---|
| `kensaiapp-one` | {one} |

## Producers — their output is evidence about this host; read them for it

| satellite | path |
|---|---|
| `kensaiapp-two` | {two} |
"""


ROUTING = "# routing\n\n@kensaiapp.md\n"
ENTRY = "@AGENTS.md\n"


def _write_instruction_files(root: Path) -> None:
    """The two root files every instance holds: the template-owned routing and its own identity."""
    (root / "AGENTS.md").write_text(ROUTING)
    (root / "CLAUDE.md").write_text(ENTRY)
    (root / "kensaiapp.md").write_text("# an instance\n")


def _write_roster(instance: Path, **paths: Path) -> None:
    system = instance / "system"
    system.mkdir(parents=True, exist_ok=True)
    (system / "satellites.md").write_text(
        ROSTER.format(**{k: str(v) for k, v in paths.items()})
    )


@pytest.fixture
def instance(tmp_path: Path) -> Path:
    """An instance root with a host `.claude/` and a roster naming two satellites."""
    root = tmp_path / "example-host"
    claude = root / ".claude"
    for layer in ("hooks", "workflows", "agents"):
        (claude / layer).mkdir(parents=True)
        (claude / layer / "thing.txt").write_text("shared\n")
    (claude / "settings.json").write_text("{}\n")
    grouped = root / "skills" / "g" / ".claude" / "skills" / "a-skill"
    grouped.mkdir(parents=True)
    (grouped / "SKILL.md").write_text("skill\n")
    (root / "core" / "templates").mkdir(parents=True)
    (root / "core" / "templates" / "agents_md_template.md").write_text(ROUTING)
    (root / "core" / "templates" / "claude_md_template.md").write_text(ENTRY)
    _write_instruction_files(root)
    _write_roster(root, one=tmp_path / "kensaiapp-one", two=tmp_path / "kensaiapp-two")
    return root


# --------------------------------------------------------------------------------------------
# Cycle 1 — the roster is read, and the kind comes with it
# --------------------------------------------------------------------------------------------


def test_reads_every_satellite_from_both_sections(instance):
    """The roster's two sections are the two `--skills-mode` answers; a row's section IS its kind."""
    entries = check_satellites.read_roster(instance)

    assert [e.name for e in entries] == ["kensaiapp-one", "kensaiapp-two"]
    assert [e.kind for e in entries] == ["consumer", "producer"]


def test_a_rows_path_is_taken_verbatim_because_placement_is_free(instance, tmp_path):
    """A satellite may live anywhere, so the path is read from the roster and never computed
    from the host's position."""
    entries = check_satellites.read_roster(instance)

    assert entries[0].path == tmp_path / "kensaiapp-one"
    assert entries[1].path == tmp_path / "kensaiapp-two"


def test_the_kinds_table_in_the_preamble_is_not_read_as_a_roster_row(instance):
    """`satellites.md` carries a second table with the same leading-pipe shape. A parser keyed on
    that shape alone reads its two rows as satellites named `consumer` and `producer`."""
    names = [e.name for e in check_satellites.read_roster(instance)]

    assert "consumer" not in names and "producer" not in names


def test_a_roster_that_does_not_exist_is_an_error_naming_the_path(tmp_path):
    """A host with no roster is a caller mistake — usually the wrong `--instance-root` — and it
    must say which file it looked for rather than reporting an empty, healthy roster."""
    with pytest.raises(SystemExit) as excinfo:
        check_satellites.read_roster(tmp_path / "not-an-instance")

    assert "satellites.md" in str(excinfo.value)


# --------------------------------------------------------------------------------------------
# Cycle 2 — the fan-out: exit codes, what is named, and that nothing is written
# --------------------------------------------------------------------------------------------


def _link(instance: Path, satellite: Path, kind: str) -> None:
    """Bring one satellite level, using the linker itself rather than a hand-built shape."""
    satellite.mkdir(parents=True, exist_ok=True)
    link_satellite.link_satellite(satellite, instance, skills_mode=kind)
    _write_instruction_files(satellite)


def test_a_level_roster_exits_zero(instance, tmp_path, capsys):
    _link(instance, tmp_path / "kensaiapp-one", "consumer")
    _link(instance, tmp_path / "kensaiapp-two", "producer")

    assert check_satellites.main(["--instance-root", str(instance)]) == 0
    out = capsys.readouterr().out
    assert "agent overrides" not in out
    assert not any(line.endswith(".claude/agents") for line in out.splitlines())


def test_a_missing_layer_exits_one_and_names_the_satellite_and_the_layer(instance, tmp_path, capsys):
    _link(instance, tmp_path / "kensaiapp-one", "consumer")
    _link(instance, tmp_path / "kensaiapp-two", "producer")
    (tmp_path / "kensaiapp-one" / ".claude" / "settings.json").unlink()

    code = check_satellites.main(["--instance-root", str(instance)])
    out = capsys.readouterr().out

    assert code == 1
    assert "kensaiapp-one" in out
    assert "settings.json" in out


def test_it_writes_nothing_so_the_drift_it_reports_is_still_there_afterwards(instance, tmp_path):
    """A check that quietly repairs is a check nobody can run to find out the truth."""
    sat = tmp_path / "kensaiapp-one"
    _link(instance, sat, "consumer")
    _link(instance, tmp_path / "kensaiapp-two", "producer")
    (sat / ".claude" / "settings.json").write_text("stale\n")

    check_satellites.main(["--instance-root", str(instance)])

    assert (sat / ".claude" / "settings.json").read_text() == "stale\n"


def test_the_verdict_line_counts_settings_to_write_and_links_to_remove(instance, tmp_path, capsys):
    sat = tmp_path / "kensaiapp-one"
    _link(instance, sat, "consumer")
    _link(instance, tmp_path / "kensaiapp-two", "producer")
    (sat / ".claude" / "settings.json").write_text("stale\n")
    (sat / ".claude" / "workflows").symlink_to(instance / ".claude" / "workflows")

    assert check_satellites.main(["--instance-root", str(instance), "--quiet"]) == 1

    assert (
        "DRIFT kensaiapp-one (consumer) — 0 unlinked, 0 to repoint, 1 settings to write, "
        "1 links to remove, 0 conflicts, 0 dangling, 0 dir-symlinks"
    ) in capsys.readouterr().out.splitlines()


def test_a_level_satellite_reads_ok_with_both_new_counts_at_zero(instance, tmp_path, capsys):
    _link(instance, tmp_path / "kensaiapp-one", "consumer")
    _link(instance, tmp_path / "kensaiapp-two", "producer")

    assert check_satellites.main(["--instance-root", str(instance), "--quiet"]) == 0

    out = capsys.readouterr().out
    assert "ok    kensaiapp-one (consumer) — 0 unlinked, 0 to repoint, 0 settings" in out
    assert "0 settings to write, 0 links to remove, 0 conflicts" in out


def test_a_rostered_satellite_that_is_not_on_disk_is_reported_not_raised(instance, tmp_path, capsys):
    """A satellite may be moved or not yet cloned. That is a finding about the roster, and the
    remaining satellites still get checked."""
    _link(instance, tmp_path / "kensaiapp-two", "producer")

    code = check_satellites.main(["--instance-root", str(instance)])
    out = capsys.readouterr().out

    assert code == 1
    assert "kensaiapp-one" in out
    assert "kensaiapp-two" in out


def test_every_satellite_gets_a_summary_line_so_the_roster_fits_on_a_screen(instance, tmp_path, capsys):
    """The reason it is cheap to run often: the verdict is readable without the detail under it."""
    _link(instance, tmp_path / "kensaiapp-one", "consumer")
    _link(instance, tmp_path / "kensaiapp-two", "producer")

    check_satellites.main(["--instance-root", str(instance)])
    lines = [l for l in capsys.readouterr().out.splitlines() if l.startswith(("ok ", "DRIFT "))]

    assert len(lines) == 3  # one per rostered satellite, and the host's own
    assert lines[-1].startswith("ok    example-host (host)")


# --------------------------------------------------------------------------------------------
# Cycle 3 — the skills root's shape, which the linker detects but misdiagnoses
# --------------------------------------------------------------------------------------------


def test_the_linker_reports_a_symlinked_producer_skills_root_as_host_file_conflicts(instance, tmp_path):
    """Measured, not assumed — and it is why the shape line below is worth having.

    A producer whose root `skills/` is a symlink is caught: `_link_tree` recurses THROUGH the
    link and every host file resolves to a real file, so each is reported as a conflict. But a
    conflict means "the satellite holds its own real file here", which is the opposite of what
    happened — those are the HOST's files, seen through a link, and a producer's eval writes will
    land on them. Detection is not diagnosis.
    """
    producer = tmp_path / "kensaiapp-two"
    producer.mkdir()
    link_satellite.link_satellite(producer, instance, skills_mode="producer")
    shutil.rmtree(producer / "skills")
    (producer / "skills").symlink_to(instance / "skills")  # the wrong shape

    report = link_satellite.link_satellite(
        producer, instance, skills_mode="producer", check=True
    )

    assert report.conflicts and not report.dir_links
    assert all("skills/" in path for path in report.conflicts)


def test_a_producer_whose_skills_root_is_a_symlink_is_named_as_that(instance, tmp_path, capsys):
    _link(instance, tmp_path / "kensaiapp-one", "consumer")
    producer = tmp_path / "kensaiapp-two"
    producer.mkdir()
    link_satellite.link_satellite(producer, instance, skills_mode="consumer")
    (producer / "skills").symlink_to(instance / "skills")  # the wrong shape

    code = check_satellites.main(["--instance-root", str(instance), "--quiet"])
    out = capsys.readouterr().out

    assert code == 1
    assert "kensaiapp-two" in out
    assert "skills root is a symlink" in out


def test_a_consumer_holding_a_root_skills_directory_is_named_as_that(instance, tmp_path, capsys):
    """The inverse signature. `satellites.md` § The two kinds states both, so both are checkable."""
    _link(instance, tmp_path / "kensaiapp-two", "producer")
    consumer = tmp_path / "kensaiapp-one"
    consumer.mkdir()
    link_satellite.link_satellite(consumer, instance, skills_mode="producer")  # wrong mode

    code = check_satellites.main(["--instance-root", str(instance), "--quiet"])
    out = capsys.readouterr().out

    assert code == 1
    # The root layer is the one named — the shape line is indented six spaces, so this cannot
    # be satisfied by a `.claude/skills` line.
    assert "      skills is present, and a consumer holds no skills layer" in out


def test_a_consumer_left_with_its_old_claude_skills_link_is_named(instance, tmp_path, capsys):
    """The link every consumer carried before each host skill was grouped. The linker never
    removes what an earlier run made, and the link still resolves while the host's flat folder
    exists on disk — so only this line names it."""
    _link(instance, tmp_path / "kensaiapp-two", "producer")
    consumer = tmp_path / "kensaiapp-one"
    _link(instance, consumer, "consumer")
    (instance / ".claude" / "skills").mkdir()
    (consumer / ".claude" / "skills").symlink_to(instance / ".claude" / "skills")

    code = check_satellites.main(["--instance-root", str(instance), "--quiet"])
    out = capsys.readouterr().out

    assert code == 1
    assert ".claude/skills is present, and a consumer holds no skills layer" in out


def test_a_correctly_shaped_roster_carries_no_shape_line(instance, tmp_path, capsys):
    """The half that keeps the check worth reading: a correct roster says so and says nothing else."""
    _link(instance, tmp_path / "kensaiapp-one", "consumer")
    _link(instance, tmp_path / "kensaiapp-two", "producer")

    assert check_satellites.main(["--instance-root", str(instance), "--quiet"]) == 0
    out = capsys.readouterr().out
    assert "skills root is" not in out
    assert "holds no skills layer" not in out


# --------------------------------------------------------------------------------------------
# The instruction files — routed by AGENTS.md, described by kensaiapp.md, entered through CLAUDE.md
# --------------------------------------------------------------------------------------------


def _level(instance: Path, tmp_path: Path) -> None:
    _link(instance, tmp_path / "kensaiapp-one", "consumer")
    _link(instance, tmp_path / "kensaiapp-two", "producer")


@pytest.mark.parametrize("missing", ["AGENTS.md", "CLAUDE.md", "kensaiapp.md"])
def test_a_missing_instruction_file_is_named(instance, tmp_path, capsys, missing):
    _level(instance, tmp_path)
    (tmp_path / "kensaiapp-two" / missing).unlink()

    assert check_satellites.main(["--instance-root", str(instance), "--quiet"]) == 1
    out = capsys.readouterr().out
    assert "DRIFT kensaiapp-two" in out
    assert f"{missing} is missing" in out


def test_an_agents_md_that_left_the_template_is_named(instance, tmp_path, capsys):
    _level(instance, tmp_path)
    (tmp_path / "kensaiapp-one" / "AGENTS.md").write_text("# a loader map someone edited\n")

    assert check_satellites.main(["--instance-root", str(instance), "--quiet"]) == 1
    assert "AGENTS.md differs from agents_md_template.md" in capsys.readouterr().out


def test_the_host_is_read_too_and_gets_its_own_line(instance, tmp_path, capsys):
    _level(instance, tmp_path)

    assert check_satellites.main(["--instance-root", str(instance), "--quiet"]) == 0
    assert "ok    example-host (host) — instruction files" in capsys.readouterr().out

    (instance / "CLAUDE.md").unlink()
    assert check_satellites.main(["--instance-root", str(instance), "--quiet"]) == 1
    out = capsys.readouterr().out
    assert "DRIFT example-host (host) — instruction files" in out
    assert "CLAUDE.md is missing" in out


def test_a_claude_md_that_says_more_than_the_import_is_named(instance, tmp_path, capsys):
    _level(instance, tmp_path)
    (tmp_path / "kensaiapp-one" / "CLAUDE.md").write_text("@AGENTS.md\n\nA rule someone added here.\n")

    assert check_satellites.main(["--instance-root", str(instance), "--quiet"]) == 1
    assert "CLAUDE.md differs from claude_md_template.md" in capsys.readouterr().out


# --------------------------------------------------------------------------------------------
# The overlays — every loader-map row reaches an overlay that extends its own seat's loader
# --------------------------------------------------------------------------------------------

MAP = "- `content-manager:` → system/loaders/content_manager.md\n"


def _overlay(root: Path, stem: str, extends: str) -> None:
    loaders = root / "system" / "loaders"
    loaders.mkdir(parents=True, exist_ok=True)
    (loaders / f"{stem}.md").write_text(
        f"# overlay\n\nExtends `<CORE>/roles/loaders/{extends}_global.md` (role posture).\n")


def _global(host: Path, stem: str) -> None:
    loaders = host / "core" / "roles" / "loaders"
    loaders.mkdir(parents=True, exist_ok=True)
    (loaders / f"{stem}_global.md").write_text("# loader\n")


def test_a_loader_map_row_with_no_overlay_is_named(instance, tmp_path):
    (tmp_path / "sat").mkdir()
    (tmp_path / "sat" / "AGENTS.md").write_text(MAP)
    _global(instance, "content_manager")

    assert check_satellites.overlay_problems(tmp_path / "sat", instance) == (
        "system/loaders/content_manager.md is missing — the `content-manager:` prefix resolves "
        "to nothing",)


def test_an_overlay_left_extending_another_seats_loader_is_named(instance, tmp_path):
    # The shape a seat rename leaves: the file renamed, its Extends line still on the old seat.
    (tmp_path / "sat").mkdir()
    (tmp_path / "sat" / "AGENTS.md").write_text(MAP)
    _global(instance, "content_manager")
    _global(instance, "content_editor")
    _overlay(tmp_path / "sat", "content_manager", "content_editor")

    assert check_satellites.overlay_problems(tmp_path / "sat", instance) == (
        "system/loaders/content_manager.md extends content_editor_global.md, not "
        "content_manager_global.md",)


def test_an_overlay_extending_a_loader_this_core_lacks_is_named(instance, tmp_path):
    (tmp_path / "sat").mkdir()
    (tmp_path / "sat" / "AGENTS.md").write_text(MAP)
    _overlay(tmp_path / "sat", "content_manager", "content_manager")

    assert check_satellites.overlay_problems(tmp_path / "sat", instance) == (
        "system/loaders/content_manager.md extends content_manager_global.md, which this core "
        "does not hold",)


def test_a_level_overlay_set_has_no_problems(instance, tmp_path):
    (tmp_path / "sat").mkdir()
    (tmp_path / "sat" / "AGENTS.md").write_text(MAP)
    _global(instance, "content_manager")
    _overlay(tmp_path / "sat", "content_manager", "content_manager")

    assert check_satellites.overlay_problems(tmp_path / "sat", instance) == ()


def test_an_overlay_problem_drifts_the_satellite(instance, tmp_path, capsys):
    _level(instance, tmp_path)
    for root in (instance, tmp_path / "kensaiapp-one", tmp_path / "kensaiapp-two"):
        (root / "AGENTS.md").write_text(ROUTING + MAP)
    (instance / "core" / "templates" / "agents_md_template.md").write_text(ROUTING + MAP)
    _global(instance, "content_manager")
    for root in (instance, tmp_path / "kensaiapp-two"):
        _overlay(root, "content_manager", "content_manager")

    assert check_satellites.main(["--instance-root", str(instance), "--quiet"]) == 1
    out = capsys.readouterr().out
    assert "DRIFT kensaiapp-one" in out
    assert "system/loaders/content_manager.md is missing" in out
    assert "ok    kensaiapp-two" in out


# --------------------------------------------------------------------------------------------
# The agents folder — a satellite's own, read by this file alone
# --------------------------------------------------------------------------------------------

OK_ONE = (
    "ok    kensaiapp-one (consumer) — 0 unlinked, 0 to repoint, 0 settings to write, "
    "0 links to remove, 0 conflicts, 0 dangling, 0 dir-symlinks"
)
OK_TWO = (
    "ok    kensaiapp-two (producer) — 0 unlinked, 0 to repoint, 0 settings to write, "
    "0 links to remove, 0 conflicts, 0 dangling, 0 dir-symlinks"
)
LEFTOVER_LINK = (
    "      .claude/agents is a symlink, and a satellite's agents folder is its own — writes "
    "through it land in the link's target; removing it is a commit in the satellite"
)


def _agents_dir(tmp_path: Path, name: str = "kensaiapp-one") -> Path:
    agents = tmp_path / name / ".claude" / "agents"
    agents.mkdir(parents=True)
    return agents


def _lines(capsys) -> list[str]:
    return capsys.readouterr().out.splitlines()


@pytest.mark.parametrize(
    ("name", "headline"), [("kensaiapp-one", OK_ONE), ("kensaiapp-two", OK_TWO)]
)
def test_real_agents_pm_is_an_override_not_a_conflict(instance, tmp_path, capsys, name, headline):
    _level(instance, tmp_path)
    (_agents_dir(tmp_path, name) / "pm.md").write_text("own agent\n")

    assert check_satellites.main(["--instance-root", str(instance)]) == 0
    lines = _lines(capsys)
    assert lines[lines.index(headline) + 1] == "      agent overrides: pm"
    assert not any("[conflict]" in line for line in lines)


def test_overrides_listed_sorted_once_under_quiet(instance, tmp_path, capsys):
    _level(instance, tmp_path)
    agents = _agents_dir(tmp_path)
    for name in ("tech-lead", "pm", "architect"):
        (agents / f"{name}.md").write_text("own\n")

    assert check_satellites.main(["--instance-root", str(instance), "--quiet"]) == 0
    lines = _lines(capsys)
    assert lines.count("      agent overrides: architect, pm, tech-lead") == 1
    assert sum("agent overrides" in line for line in lines) == 1


def test_override_order_is_byte_order(instance, tmp_path, capsys):
    _level(instance, tmp_path)
    agents = _agents_dir(tmp_path)
    for name in ("Zeta", "alpha"):
        (agents / f"{name}.md").write_text("own\n")

    check_satellites.main(["--instance-root", str(instance), "--quiet"])
    assert "      agent overrides: Zeta, alpha" in _lines(capsys)


def test_symlinked_agent_file_is_listed(instance, tmp_path, capsys):
    _level(instance, tmp_path)
    target = tmp_path / "kensaiapp-one" / "elsewhere.txt"
    target.write_text("own\n")
    (_agents_dir(tmp_path) / "pm.md").symlink_to(target)

    check_satellites.main(["--instance-root", str(instance), "--quiet"])
    assert "      agent overrides: pm" in _lines(capsys)


def test_non_agent_entries_are_not_listed(instance, tmp_path, capsys):
    _level(instance, tmp_path)
    agents = _agents_dir(tmp_path)
    for name in (".gitkeep", "notes.txt", ".hidden.md"):
        (agents / name).write_text("x\n")
    (agents / "sub").mkdir()
    (agents / "sub" / "x.md").write_text("x\n")
    (agents / "team.md").mkdir()  # named like an agent file, but a directory is not a file

    assert check_satellites.main(["--instance-root", str(instance)]) == 0
    lines = _lines(capsys)
    assert OK_ONE in lines
    assert not any("agent overrides" in line for line in lines)
    assert not any(".claude/agents" in line for line in lines)


def test_dangling_entry_is_not_an_override_but_still_reported(instance, tmp_path, capsys):
    _level(instance, tmp_path)
    agents = _agents_dir(tmp_path)
    (agents / "pm.md").write_text("own\n")
    (agents / "gone.md").symlink_to(tmp_path / "kensaiapp-one" / "missing.md")

    check_satellites.main(["--instance-root", str(instance)])
    lines = _lines(capsys)
    assert "      agent overrides: pm" in lines
    assert any(
        line.strip().startswith("[dangling]") and ".claude/agents/gone.md" in line
        for line in lines
    )


def test_override_does_not_change_the_drift_verdict(instance, tmp_path, capsys):
    _level(instance, tmp_path)
    (_agents_dir(tmp_path) / "pm.md").write_text("own\n")
    agents_md = tmp_path / "kensaiapp-one" / "AGENTS.md"
    agents_md.write_text("# edited\n")

    assert check_satellites.main(["--instance-root", str(instance), "--quiet"]) == 1
    lines = _lines(capsys)
    drift = next(i for i, line in enumerate(lines) if line.startswith("DRIFT kensaiapp-one"))
    assert lines[drift + 1] == "      AGENTS.md differs from agents_md_template.md — re-stamp it"
    assert lines[drift + 2] == "      agent overrides: pm"

    agents_md.write_text(ROUTING)
    assert check_satellites.main(["--instance-root", str(instance), "--quiet"]) == 0


@pytest.mark.parametrize("quiet", [False, True])
def test_resolving_agents_symlink_is_drift(instance, tmp_path, capsys, quiet):
    """The host's folder holds an agent file, so "no override line" proves the link's target was
    never read — a host holding only `thing.txt` would list nothing either way."""
    _level(instance, tmp_path)
    (instance / ".claude" / "agents" / "cpo.md").write_text("host agent\n")
    link = tmp_path / "kensaiapp-one" / ".claude" / "agents"
    link.symlink_to(instance / ".claude" / "agents")
    argv = ["--instance-root", str(instance)] + (["--quiet"] if quiet else [])

    assert check_satellites.main(argv) == 1
    lines = _lines(capsys)
    drift = next(i for i, line in enumerate(lines) if line.startswith("DRIFT kensaiapp-one"))
    assert lines[drift + 1] == LEFTOVER_LINK
    assert not any("agent overrides" in line for line in lines)
    assert link.is_symlink()


def test_dangling_agents_symlink_is_drift(instance, tmp_path, capsys):
    _level(instance, tmp_path)
    link = tmp_path / "kensaiapp-one" / ".claude" / "agents"
    link.symlink_to(tmp_path / "nowhere")

    assert check_satellites.main(["--instance-root", str(instance)]) == 1
    lines = _lines(capsys)
    assert LEFTOVER_LINK in lines
    assert any(
        line.strip().startswith("[dangling]") and line.split(" — ")[0].endswith(".claude/agents")
        for line in lines
    )


def _first(lines: list[str], predicate) -> int:
    return next(i for i, line in enumerate(lines) if predicate(line))


def _is_detail(line: str) -> bool:
    return line.strip().startswith("[")


def test_override_line_comes_before_the_linkers_detail(instance, tmp_path, capsys):
    """CP-441: the override line is part of the headline, so on a drifted satellite it precedes
    the linker's detail block rather than following it."""
    _level(instance, tmp_path)
    agents = _agents_dir(tmp_path)
    (agents / "pm.md").write_text("own\n")
    (agents / "gone.md").symlink_to(tmp_path / "kensaiapp-one" / "missing.md")

    check_satellites.main(["--instance-root", str(instance)])
    lines = _lines(capsys)
    drift = _first(lines, lambda line: line.startswith("DRIFT kensaiapp-one"))
    override = lines.index("      agent overrides: pm")
    assert drift < override < _first(lines, _is_detail)


def test_leftover_link_line_comes_before_the_linkers_detail(instance, tmp_path, capsys):
    """CP-444: the leftover-link line sits where CP-441's does — beneath the headline, ahead of
    the linker's `[dangling]` detail for the same path."""
    _level(instance, tmp_path)
    (tmp_path / "kensaiapp-one" / ".claude" / "agents").symlink_to(tmp_path / "nowhere")

    check_satellites.main(["--instance-root", str(instance)])
    lines = _lines(capsys)
    drift = _first(lines, lambda line: line.startswith("DRIFT kensaiapp-one"))
    assert lines[drift + 1] == LEFTOVER_LINK
    assert drift + 1 < _first(lines, _is_detail)
