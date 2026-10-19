"""Contract tests for `spawn_satellite.py`.

Every test builds a throwaway host + satellite pair under `tmp_path`, positioned as siblings —
the placement `shared_core_instance.md` requires and `spawn_satellite.py` enforces — so the
location assertions match what a real spawn produces. Nothing here touches a live instance.
Writing bar mirrors `test_link_satellite.py`.
"""

from __future__ import annotations

import datetime
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import check_vendor_neutrality
import link_satellite
import spawn_satellite


# --------------------------------------------------------------------------------------------
# Fixture host — a minimal but real host tree: `.claude/`, `.env.example`,
# `.providers.toml.example`, `core/templates/`
# (a trimmed copy of the real templates so tests don't depend on the host's own tree),
# and the two delegated tools (`link_satellite.py`, `project-stamp`) as real, runnable files.
# --------------------------------------------------------------------------------------------


REAL_CORE_TOOLS = Path(__file__).parent
REAL_TEMPLATES = REAL_CORE_TOOLS.parent / "templates"
REAL_PROJECT_STAMP = (
    REAL_CORE_TOOLS.parent.parent
    / "skills" / "interactive-product" / ".claude" / "skills" / "project-stamp" / "scripts"
)


def _stamper_token_files() -> list[tuple[str, str]]:
    """`stamp_project.py`'s own `TOKEN_FILES`, read from the module rather than copied.

    The fixture below needs to know which templates the stamper opens. That set is the stamper's to
    declare, and a second list here would be a copy free to drift — `single_source.md`'s rule, and
    the drift it names is exactly what happened: a template added to `TOKEN_FILES` on 2026-09-02
    left this fixture short by one file and took seven tests with it.
    """
    spec = importlib.util.spec_from_file_location(
        "_stamp_project_for_fixture", REAL_PROJECT_STAMP / "stamp_project.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.TOKEN_FILES)


def _make_host(root: Path) -> Path:
    """A host carrying every layer spawn_satellite.py reads or delegates to — the real
    templates and the real link_satellite.py / stamp_project.py, so the fixture proves
    against the actual tools this script must not reimplement."""
    host = root / "example-host"
    claude = host / ".claude"
    (claude / "hooks").mkdir(parents=True)
    (claude / "hooks" / "resolve_core.py").write_text("# hook\n")
    (claude / "workflows").mkdir()
    (claude / "agents").mkdir()
    (claude / "settings.json").write_text("{}\n")
    skills_dir = claude / "skills"
    skills_dir.mkdir()

    core = host / "core"
    tools = core / "tools"
    tools.mkdir(parents=True)
    (tools / "link_satellite.py").write_text(
        (REAL_CORE_TOOLS / "link_satellite.py").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tools / "commit_builder.py").write_text(
        (REAL_CORE_TOOLS / "commit_builder.py").read_text(encoding="utf-8"), encoding="utf-8"
    )

    templates = core / "templates"
    templates.mkdir()
    for name in (
        "agents_md_template.md",
        "kensaiapp_md_template.md",
        "claude_md_template.md",
        "gitignore_template.md",
        "claude_design_instructions_template.md",
        "michi_template.md",
        "nemawashi_template.md",
        "instance_setup_seed_template.md",
        "system_shukuba_template.md",
        "kensaiapp_doctrine_template.md",
        "ai_responsibility_template.md",
        "doctrine_structure_template.md",
    ):
        (templates / name).write_text((REAL_TEMPLATES / name).read_text(encoding="utf-8"), encoding="utf-8")
    role_templates = templates / "role-templates"
    role_templates.mkdir()
    for name in ("overlay_template.md", "pm_overlay_template.md", "cross_role_template.md"):
        (role_templates / name).write_text(
            (REAL_TEMPLATES / "role-templates" / name).read_text(encoding="utf-8"), encoding="utf-8"
        )

    project_stamp = claude / "skills" / "project-stamp" / "scripts"
    project_stamp.mkdir(parents=True)
    (project_stamp / "stamp_project.py").write_text(
        (REAL_PROJECT_STAMP / "stamp_project.py").read_text(encoding="utf-8"), encoding="utf-8"
    )
    # stamp_project.py reads templates too, and WHICH ones is DERIVED from its own TOKEN_FILES
    # rather than hand-listed here. A hand list is a copy of that declaration: add a template to the
    # stamper and this fixture silently lacks it, so every test that stamps a project dies on a
    # FileNotFoundError naming a path nobody wrote. That is not hypothetical — it is what a template
    # added on 2026-09-02 did to seven tests in this file. Reading the declaration means the fixture
    # cannot fall behind it.
    stamper_templates = [rel for rel, _dest in _stamper_token_files()]
    # `project_template.md` is the one template the stamper reads OUTSIDE `TOKEN_FILES`: that list
    # is the plain-token-replace set, and `project.md` is built by field substitution instead, to
    # keep the template's inline comments (`stamp_project.py`, the comment above `TOKEN_FILES`). So
    # it is named here rather than derived — the only hand-named entry, and it carries its reason.
    stamper_templates.append("project_template.md")
    for template_rel in stamper_templates:
        target = templates / template_rel
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            (REAL_TEMPLATES / template_rel).read_text(encoding="utf-8"), encoding="utf-8"
        )
    (templates / "project-templates").mkdir(exist_ok=True)
    (templates / "project-templates" / "agari_template.md").write_text(
        (REAL_TEMPLATES / "project-templates" / "agari_template.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    (host / ".env.example").write_text("CORE=core/\n", encoding="utf-8")
    (host / ".providers.toml.example").write_text(
        '[documents]\nDESIGN = "claude"\n', encoding="utf-8"
    )

    subprocess.run(["git", "init", "-q", "-b", "main", str(host)], check=True)
    subprocess.run(["git", "-C", str(host), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(host), "config", "user.email", "test@example.com"], check=True)
    return host


@pytest.fixture
def host(tmp_path: Path) -> Path:
    return _make_host(tmp_path)


def _argv(*, name: str, location: Path, host: Path, skills_mode: str = "consumer", **extra) -> list[str]:
    argv = [
        "--name", name,
        "--location", str(location),
        "--host", str(host),
        "--skills-mode", skills_mode,
    ]
    for flag, value in extra.items():
        key = f"--{flag.replace('_', '-')}"
        if value is True:
            argv.append(key)
        elif value is not None:
            argv.extend([key, str(value)])
    return argv


# --------------------------------------------------------------------------------------------
# Task 1 — CLI contract and the refusals that run before anything is created
# --------------------------------------------------------------------------------------------


def test_refuses_when_target_already_exists(host: Path):
    location = host.parent
    (location / "kensaiapp-probe").mkdir()

    args = spawn_satellite._build_arg_parser().parse_args(
        _argv(name="kensaiapp-probe", location=location, host=host)
    )
    with pytest.raises(SystemExit, match="kensaiapp-probe"):
        spawn_satellite.resolve_plan(args)
    assert not (location / "kensaiapp-probe" / "AGENTS.md").exists()


def test_accepts_location_outside_hosts_parent(host: Path, tmp_path: Path):
    """A satellite may live anywhere — `shared_core_instance.md` retired the beside-the-host
    placement rule, because the absolute links resolve from any location. `example-8792fa`, under
    `~/work/private` against a host under `~/projects/kensai`, is the live case."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()

    args = spawn_satellite._build_arg_parser().parse_args(
        _argv(name="kensaiapp-probe", location=elsewhere, host=host)
    )
    plan = spawn_satellite.resolve_plan(args)

    assert plan.satellite == elsewhere / "kensaiapp-probe"


def test_refuses_when_location_does_not_exist(host: Path, tmp_path: Path):
    """Placement is free, but the parent has to be real: the satellite directory is created with
    parents, so a typo'd path would stand an instance up in a tree nobody meant."""
    missing = tmp_path / "no-such-dir"

    args = spawn_satellite._build_arg_parser().parse_args(
        _argv(name="kensaiapp-probe", location=missing, host=host)
    )
    with pytest.raises(SystemExit, match=str(missing)):
        spawn_satellite.resolve_plan(args)


def test_refuses_when_host_has_no_claude_dir(tmp_path: Path):
    bare = tmp_path / "not-an-instance"
    bare.mkdir()
    location = tmp_path

    args = spawn_satellite._build_arg_parser().parse_args(
        _argv(name="kensaiapp-probe", location=location, host=bare)
    )
    with pytest.raises(SystemExit, match=str(bare / ".claude")):
        spawn_satellite.resolve_plan(args)


def test_refuses_unknown_skills_mode(host: Path):
    with pytest.raises(SystemExit):
        spawn_satellite._build_arg_parser().parse_args(
            _argv(name="kensaiapp-probe", location=host.parent, host=host, skills_mode="whatever")
        )


def test_resolves_a_fresh_target_cleanly(host: Path):
    args = spawn_satellite._build_arg_parser().parse_args(
        _argv(name="kensaiapp-probe", location=host.parent, host=host)
    )
    plan = spawn_satellite.resolve_plan(args)
    assert plan.name == "kensaiapp-probe"
    assert plan.satellite == host.parent / "kensaiapp-probe"
    assert plan.host == host
    assert plan.skills_mode == "consumer"


def test_resume_is_allowed_when_env_marks_it_our_own_satellite(host: Path):
    """The Task 1 refusal and Task 8's idempotence both hold: an occupied path with nothing
    recognizable refuses (above); an occupied path this tool already stamped (has `.env`)
    resumes instead."""
    satellite = host.parent / "kensaiapp-probe"
    satellite.mkdir()
    (satellite / ".env").write_text(f"CORE={host}/core\n", encoding="utf-8")

    args = spawn_satellite._build_arg_parser().parse_args(
        _argv(name="kensaiapp-probe", location=host.parent, host=host)
    )
    plan = spawn_satellite.resolve_plan(args)
    assert plan.satellite == satellite


def _plan(host: Path, *, name: str = "kensaiapp-probe", **extra) -> "spawn_satellite.SpawnPlan":
    args = spawn_satellite._build_arg_parser().parse_args(
        _argv(name=name, location=host.parent, host=host, **extra)
    )
    return spawn_satellite.resolve_plan(args)


# --------------------------------------------------------------------------------------------
# Task 2 — create the instance and bind <CORE>
# --------------------------------------------------------------------------------------------


def test_creates_directory_and_git_inits_with_main_branch(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    assert plan.satellite.is_dir()
    head = (plan.satellite / ".git" / "HEAD").read_text(encoding="utf-8")
    assert "main" in head


def test_no_git_skips_git_init(host: Path):
    plan = _plan(host, no_git=True)
    spawn_satellite.spawn(plan, check=False)

    assert plan.satellite.is_dir()
    assert not (plan.satellite / ".git").exists()


def test_copies_hosts_env_example_verbatim(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    assert (plan.satellite / ".env.example").read_text(encoding="utf-8") == (
        host / ".env.example"
    ).read_text(encoding="utf-8")


def test_copies_hosts_providers_example_verbatim(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    assert (plan.satellite / ".providers.toml.example").read_bytes() == (
        host / ".providers.toml.example"
    ).read_bytes()


def test_an_existing_providers_example_is_kept(host: Path):
    plan = _plan(host)
    plan.satellite.mkdir()
    (plan.satellite / ".env").write_text(f"CORE={host}/core\n", encoding="utf-8")
    (plan.satellite / ".providers.toml.example").write_text("MY OWN\n", encoding="utf-8")

    report = spawn_satellite.spawn(plan, check=False)

    assert (plan.satellite / ".providers.toml.example").read_text(encoding="utf-8") == "MY OWN\n"
    assert str(plan.satellite / ".providers.toml.example") in report.already
    assert str(plan.satellite / ".providers.toml.example") not in report.created


def test_a_host_without_a_providers_example_is_refused(host: Path):
    (host / ".providers.toml.example").unlink()
    plan = _plan(host)

    with pytest.raises(SystemExit, match=str(host / ".providers.toml.example")):
        spawn_satellite.spawn(plan, check=False)


def test_the_spawn_writes_no_live_provider_file(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    assert not (plan.satellite / ".providers.toml").exists()


def test_check_mode_writes_no_providers_example(host: Path):
    plan = _plan(host)
    report = spawn_satellite.spawn(plan, check=True)

    assert str(plan.satellite / ".providers.toml.example") in report.created
    assert not (plan.satellite / ".providers.toml.example").exists()


def test_writes_env_with_absolute_core_binding(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    env_text = (plan.satellite / ".env").read_text(encoding="utf-8")
    assert f"CORE={host / 'core'}" in env_text
    assert os.path.isabs((host / "core").as_posix())


def test_creates_no_core_directory_in_the_satellite(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    assert not (plan.satellite / "core").exists()


def test_check_creates_nothing_for_task_2(host: Path):
    plan = _plan(host)
    report = spawn_satellite.spawn(plan, check=True)

    assert not plan.satellite.exists()
    assert report.would_change


# --------------------------------------------------------------------------------------------
# Task 3 — stamp the instance's own §1 files
# --------------------------------------------------------------------------------------------


def test_kensaiapp_md_names_the_satellite_not_the_host(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    text = (plan.satellite / "kensaiapp.md").read_text(encoding="utf-8")
    assert text.splitlines()[0] == "# kensaiapp-probe"
    assert "example-host" not in text.splitlines()[0]


def test_agents_md_is_the_template_verbatim_and_names_no_instance(host: Path):
    """The routing file is the same bytes in every instance, which is what lets a resume rewrite
    it: the satellite's name appears nowhere in it, and it points at the identity file beside it
    both in prose and as a bare import line."""
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    text = (plan.satellite / "AGENTS.md").read_text(encoding="utf-8")
    template = (host / "core" / "templates" / "agents_md_template.md").read_text(encoding="utf-8")
    assert text == template
    assert "kensaiapp-probe" not in text
    assert "@kensaiapp.md" in text.splitlines()


def test_claude_md_is_one_line_importing_agents_md(host: Path):
    """Claude Code's entry point says nothing of its own: it is the bare import that leads to the
    routing file, so the harness loads `AGENTS.md` through it instead of falling back to it."""
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    assert (plan.satellite / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"


def test_a_claude_md_that_grew_is_rewritten_to_the_import(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)
    (plan.satellite / "CLAUDE.md").write_text("@AGENTS.md\n\nA rule someone added here.\n", encoding="utf-8")

    report = spawn_satellite.spawn(plan, check=False)

    assert (plan.satellite / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
    assert str(plan.satellite / "CLAUDE.md") in report.updated


def test_claude_design_brief_lands_at_the_root_naming_the_satellite(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    text = (plan.satellite / "claude-design-instructions.md").read_text(encoding="utf-8")
    assert "This repository is **kensaiapp-probe**." in text
    assert "<instance>" not in text


def test_claude_design_brief_names_no_product_and_no_input_filename(host: Path):
    """The two properties the example-8792fa brief was rewritten to hold (`0a06116`): it resolves the
    product it is told from `system/projects/<name>/project.md`, and it names folders rather than
    files. A placeholder product name or a document filename here would put both back."""
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    text = (plan.satellite / "claude-design-instructions.md").read_text(encoding="utf-8")
    assert "system/projects/<name>/project.md" in text
    for filename in ("PRD.md", "SRS.md", "UXD.md", "DESIGN.md", "CONTENT.md"):
        assert filename not in text, filename


def test_claude_design_brief_points_at_no_path_outside_the_connected_folder(host: Path):
    """The `Create here` route links this folder and copies selected files out of it, so a path
    leading anywhere else is a string in a file rather than a link anything follows. A `<CORE>`
    token or an absolute host path here would resolve for one route and be dead for the other."""
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    text = (plan.satellite / "claude-design-instructions.md").read_text(encoding="utf-8")
    assert "<CORE>" not in text
    assert "core/" not in text
    assert "/Users/" not in text


def test_gitignore_contains_only_the_fenced_block(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    text = (plan.satellite / ".gitignore").read_text(encoding="utf-8")
    assert "```" not in text
    assert "# .gitignore template" not in text
    assert "__pycache__/" in text
    assert ".claude/settings.local.json" in text


def test_michi_and_nemawashi_readme_name_the_satellite(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    michi = (plan.satellite / "system" / "michi.md").read_text(encoding="utf-8")
    assert "kensaiapp-probe's Way(s)" in michi

    nemawashi = (plan.satellite / "system" / "nemawashi" / "README.md").read_text(encoding="utf-8")
    assert "kensaiapp-probe's seedbed" in nemawashi


def test_nemawashi_drop_lands_as_a_tracked_gitkeep_stub(host: Path):
    """The manifest declares `system/nemawashi/drop/` a `[create]` directory stub, so a spawn that
    writes the other two bins and not this one leaves a row of the manifest standing over nothing."""
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    gitkeep = plan.satellite / "system" / "nemawashi" / "drop" / ".gitkeep"
    assert gitkeep.is_file()
    assert gitkeep.read_text(encoding="utf-8") == ""


def test_nemawashi_trail_directory_exists(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    assert (plan.satellite / "system" / "nemawashi" / "trail").is_dir()
    assert (plan.satellite / "system" / "nemawashi" / "unpicked").is_dir()


def test_nemawashi_trail_and_unpicked_land_as_tracked_gitkeep_stubs(host: Path):
    """A bare `mkdir` is never tracked by git, so an empty directory does not survive a clone —
    `git status --porcelain` is blind to it, which is why `test_genesis_commit_staged_set_covers_
    everything_created` cannot catch the omission on its own. `.gitkeep` is the stub convention
    `stamp_project.py` already uses for the equivalent project-level directories."""
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    trail_gitkeep = plan.satellite / "system" / "nemawashi" / "trail" / ".gitkeep"
    unpicked_gitkeep = plan.satellite / "system" / "nemawashi" / "unpicked" / ".gitkeep"

    assert trail_gitkeep.is_file()
    assert trail_gitkeep.read_text(encoding="utf-8") == ""
    assert unpicked_gitkeep.is_file()
    assert unpicked_gitkeep.read_text(encoding="utf-8") == ""

    tracked = subprocess.run(
        ["git", "-C", str(plan.satellite), "ls-files"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "system/nemawashi/trail/.gitkeep" in tracked
    assert "system/nemawashi/unpicked/.gitkeep" in tracked


def test_second_run_over_a_satellite_missing_the_unpicked_gitkeep_creates_exactly_that_file(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)
    (plan.satellite / "system" / "nemawashi" / "unpicked" / ".gitkeep").unlink()

    report = spawn_satellite.spawn(plan, check=False)
    assert report.created == [str(plan.satellite / "system" / "nemawashi" / "unpicked" / ".gitkeep")]
    assert (plan.satellite / "system" / "nemawashi" / "unpicked" / ".gitkeep").exists()


def test_mkdir_if_missing_no_longer_exists(host: Path):
    assert not hasattr(spawn_satellite, "_mkdir_if_missing")


def test_setup_seed_lands_in_the_seedbed_naming_the_satellite(host: Path):
    """The instance-altitude twin of the setup seed `project-stamp` stamps: a new instance's
    seedbed is never empty, and the sequence `setting_up_an_instance.md` owns is never re-typed
    from memory."""
    plan = _plan(host, date="2026-08-17")
    spawn_satellite.spawn(plan, check=False)

    seed = plan.satellite / "system" / "nemawashi" / "2026-08-17_instance-setup.md"
    assert seed.is_file()
    text = seed.read_text(encoding="utf-8")
    assert "set up kensaiapp-probe" in text
    assert "<instance>" not in text

    # The three steps that follow the stamp, unwalked — step 1 IS this stamp, so it is not here.
    assert "- [ ] 1. **kensaiapp-michi**" in text
    assert "- [ ] 2. **kensaiapp-writing-bar**" in text
    assert "- [ ] 3. **experience-visual**" in text
    assert "- [ ] 4. **experience-voice**" in text

    tracked = subprocess.run(
        ["git", "-C", str(plan.satellite), "ls-files"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "system/nemawashi/2026-08-17_instance-setup.md" in tracked


def test_stamped_setup_seed_carries_no_template_metadata(host: Path):
    """Script-facing format, per `core/templates/README.md` § Adding a script-facing template:
    the bytes land in the instance, so anything the template says about itself lands too."""
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    seed = next((plan.satellite / "system" / "nemawashi").glob("*_instance-setup.md"))
    text = seed.read_text(encoding="utf-8")
    assert "<!--" not in text and "-->" not in text
    assert not text.startswith("---")
    assert "version:" not in text
    assert text.startswith("# Seed — set up kensaiapp-probe")


def test_setup_seed_defaults_to_todays_date(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    today = datetime.date.today().isoformat()
    assert (plan.satellite / "system" / "nemawashi" / f"{today}_instance-setup.md").is_file()


def test_a_later_rerun_does_not_stamp_a_second_setup_seed(host: Path):
    """The one write that cannot key on an exact path. A resume made on a later day would key on
    `<that day>_instance-setup.md`, which the first run never wrote — so a plain create-if-missing
    would stamp a second seed beside the first, and the seedbed's one-idea-per-file pick would be
    looking at two."""
    plan = _plan(host, date="2026-08-17")
    spawn_satellite.spawn(plan, check=False)
    seedbed = plan.satellite / "system" / "nemawashi"

    report = spawn_satellite.spawn(_plan(host, date="2026-09-01"), check=False)

    assert [p.name for p in sorted(seedbed.glob("*_instance-setup.md"))] == [
        "2026-08-17_instance-setup.md"
    ]
    assert not any("2026-09-01" in path for path in report.created)
    assert str(seedbed / "2026-08-17_instance-setup.md") in report.already


@pytest.mark.parametrize("bin_", ["unpicked", "trail", "drop"])
def test_a_setup_seed_already_picked_past_or_walked_is_not_resurrected(host: Path, bin_: str):
    """`unpicked/` means it was picked and later un-picked; `trail/` means it was walked; `drop/`
    means it was killed. Any of the three means the instance has its setup seed and a re-run must
    not put a fresh one back at the root — a bin the glob does not search resurrects it silently."""
    plan = _plan(host, date="2026-08-17")
    spawn_satellite.spawn(plan, check=False)

    seedbed = plan.satellite / "system" / "nemawashi"
    moved = seedbed / bin_ / "2026-08-17_instance-setup.md"
    (seedbed / "2026-08-17_instance-setup.md").rename(moved)

    report = spawn_satellite.spawn(_plan(host, date="2026-09-01"), check=False)

    assert not list(seedbed.glob("*_instance-setup.md"))
    assert moved.is_file()
    assert str(moved) in report.already


def test_check_writes_no_setup_seed(host: Path):
    plan = _plan(host, date="2026-08-17")
    report = spawn_satellite.spawn(plan, check=True)

    assert str(plan.satellite / "system" / "nemawashi" / "2026-08-17_instance-setup.md") in report.created
    assert not (plan.satellite / "system" / "nemawashi").exists()


def test_stamped_nemawashi_readme_carries_no_template_metadata(host: Path):
    """`nemawashi_template.md` was made script-facing at unit 1's `ab1adec` regression; the
    stamper (`:410`) does no stripping, so any metadata left in the template lands verbatim in a
    spawned satellite's seedbed README. These are the same five properties the role layer already
    guards (`test_no_stamped_role_file_contains_an_html_comment_block`,
    `test_no_stamped_role_file_begins_with_a_blank_line`), with no instance-file counterpart until
    now."""
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    nemawashi = (plan.satellite / "system" / "nemawashi" / "README.md").read_text(encoding="utf-8")
    assert "<!--" not in nemawashi and "-->" not in nemawashi
    assert not nemawashi.startswith("---")
    assert "version:" not in nemawashi
    assert not nemawashi.startswith("\n")
    assert nemawashi.startswith("# 根回し Nemawashi — kensaiapp-probe's seedbed")
    assert "Stamped into" not in nemawashi


def test_instance_doctrine_holds_exactly_the_three_stamped_files(host: Path):
    """`kensaiapp_structure.md` § Instance-shared doctrine prescribes three files under `system/doctrine/` — the domain
    doctrine, AI responsibility, and doctrine structure. The spawner is the only writer of that
    folder, so what it stamps *is* the set. Asserting that the three exist would pass on a fourth,
    so this reads the folder back instead of naming what it expects to find."""
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    doctrine_dir = plan.satellite / "system" / "doctrine"
    assert sorted(p.name for p in doctrine_dir.iterdir()) == [
        "ai_responsibility.md",
        "doctrine_structure.md",
        "kensaiapp_doctrine.md",
    ]


def test_doctrine_files_take_the_generic_word_never_the_instance_name(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    doctrine_dir = plan.satellite / "system" / "doctrine"
    kensaiapp_doctrine = (doctrine_dir / "kensaiapp_doctrine.md").read_text(encoding="utf-8")
    assert kensaiapp_doctrine.startswith("# kensaiapp — domain doctrine")
    assert "kensaiapp-probe" not in kensaiapp_doctrine

    ai_responsibility = (doctrine_dir / "ai_responsibility.md").read_text(encoding="utf-8")
    assert "# AI responsibility — kensaiapp" in ai_responsibility
    assert "kensaiapp-probe" not in ai_responsibility

    doctrine_structure = (doctrine_dir / "doctrine_structure.md").read_text(encoding="utf-8")
    assert "# Doctrine structure — kensaiapp" in doctrine_structure
    assert "kensaiapp-probe" not in doctrine_structure


def test_missing_template_is_a_loud_failure_naming_the_path(host: Path):
    (host / "core" / "templates" / "agents_md_template.md").unlink()
    plan = _plan(host)

    with pytest.raises(SystemExit, match="agents_md_template.md"):
        spawn_satellite.spawn(plan, check=False)


def test_check_writes_nothing_for_task_3(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=True)

    assert not (plan.satellite / "AGENTS.md").exists()
    assert not (plan.satellite / "CLAUDE.md").exists()
    assert not (plan.satellite / "kensaiapp.md").exists()
    assert not (plan.satellite / "system").exists()


def test_shukuba_readme_names_the_satellite(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    shukuba = (plan.satellite / "system" / "shukuba" / "README.md").read_text(encoding="utf-8")
    assert shukuba.startswith("# 宿場 Shukuba — kensaiapp-probe's router station")
    assert "example-host" not in shukuba


def test_stamped_shukuba_readme_carries_no_template_metadata(host: Path):
    """`system_shukuba_template.md` is new (unit 1, `48cb383`) and this change is what first made
    the stamper read it (`spawn_satellite.py:416`) — the same five metadata properties Task 1
    established for the seedbed README, now true of the router station's."""
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    shukuba = (plan.satellite / "system" / "shukuba" / "README.md").read_text(encoding="utf-8")
    assert "<!--" not in shukuba and "-->" not in shukuba
    assert not shukuba.startswith("---")
    assert "version:" not in shukuba
    assert not shukuba.startswith("\n")
    assert "Stamped into" not in shukuba


def test_shukuba_trail_directory_lands_as_a_tracked_gitkeep_stub(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    gitkeep = plan.satellite / "system" / "shukuba" / "trail" / ".gitkeep"
    assert gitkeep.is_file()
    assert gitkeep.read_text(encoding="utf-8") == ""
    assert (plan.satellite / "system" / "shukuba" / "trail").is_dir()

    tracked = subprocess.run(
        ["git", "-C", str(plan.satellite), "ls-files"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "system/shukuba/README.md" in tracked
    assert "system/shukuba/trail/.gitkeep" in tracked


def test_check_writes_nothing_for_the_router_station(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=True)

    assert not (plan.satellite / "system").exists()


def test_missing_shukuba_template_is_a_loud_failure_naming_the_path(host: Path):
    (host / "core" / "templates" / "system_shukuba_template.md").unlink()
    plan = _plan(host)

    with pytest.raises(SystemExit, match="system_shukuba_template.md"):
        spawn_satellite.spawn(plan, check=False)


# --------------------------------------------------------------------------------------------
# Task 4 — stamp the role layer
# --------------------------------------------------------------------------------------------

# Derived from ROLE_TITLES rather than listed, because a hardcoded copy goes stale silently: every
# assertion below iterates it, so a role missing from the list is simply not tested rather than
# failing. It held ten entries and omitted `principal_pm` and `principal_architect` until this was
# derived — an unresolved token in either stamped overlay would have shipped uncaught.
ROLE_LAYER_FILES = [f"{role}.md" for role in spawn_satellite.ROLE_TITLES] + ["pm.md"]


def test_every_role_layer_file_exists_and_names_the_satellite(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    loaders = plan.satellite / "system" / "loaders"
    for fname in ROLE_LAYER_FILES:
        text = (loaders / fname).read_text(encoding="utf-8")
        title_line = next(line for line in text.splitlines() if line.startswith("# "))
        assert "kensaiapp-probe" in title_line, fname

    cross_role = (plan.satellite / "system" / "CROSS_ROLE.md").read_text(encoding="utf-8")
    assert "kensaiapp-probe" in cross_role.splitlines()[0]


def test_extends_line_points_at_each_roles_own_global_loader(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    loaders = plan.satellite / "system" / "loaders"
    for role in spawn_satellite.ROLE_TITLES:
        text = (loaders / f"{role}.md").read_text(encoding="utf-8")
        assert f"<CORE>/roles/loaders/{role}_global.md" in text

    pm_text = (loaders / "pm.md").read_text(encoding="utf-8")
    assert "<CORE>/roles/loaders/pm_global.md" in pm_text


REAL_GLOBAL_LOADERS = REAL_CORE_TOOLS.parent / "roles" / "loaders"


def test_every_stamped_overlay_extends_a_global_loader_this_core_holds():
    # The test above proves the Extends line repeats the ROLE_TITLES key, which is true of any key
    # at all — a key left on a retired seat's name stamps an overlay extending a loader that is
    # gone, and passes it. A key is the global loader's filename stem, so the file must exist.
    for role in list(spawn_satellite.ROLE_TITLES) + ["pm"]:
        assert (REAL_GLOBAL_LOADERS / f"{role}_global.md").is_file(), role


def test_a_spawned_satellite_is_born_with_the_content_editor_overlay(host: Path):
    # The tests above iterate ROLE_TITLES, so they hold any title the row carries. This one pins
    # what a satellite is born with for this seat: its title names Content Editor, and it extends
    # the seat's own global loader.
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    text = (plan.satellite / "system" / "loaders" / "content_editor.md").read_text(encoding="utf-8")
    title_line = next(line for line in text.splitlines() if line.startswith("# "))
    assert "Content Editor" in title_line
    assert "<CORE>/roles/loaders/content_editor_global.md" in text



def test_a_stamped_overlay_names_its_posture_by_title_not_by_filename(host: Path):
    # `<role>` is the filename stem, so a closing line built from it read "the global
    # content_editor posture governs" in every satellite. The line names the seat as a reader does.
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    loaders = plan.satellite / "system" / "loaders"
    for role, title in spawn_satellite.ROLE_TITLES.items():
        text = (loaders / f"{role}.md").read_text(encoding="utf-8")
        assert f"None yet — the global {title} posture governs." in text, role


LOADER_MAP_ROW = re.compile(r"^- `([a-z-]+):`\s+→\s+system/loaders/(\S+)\.md\s*$", re.MULTILINE)


def test_every_loader_map_row_in_the_stamped_agents_md_reaches_a_stamped_overlay(host: Path):
    # The template states the map's rule: a `<role>:` prefix routes to `system/loaders/<role>.md`,
    # and every prefix but the `ppm:` alias spells its own loader file. AGENTS.md and the overlays
    # come from two different sources — the template and ROLE_TITLES — so only a spawn shows a
    # row naming an overlay the stamper never writes.
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    rows = LOADER_MAP_ROW.findall((plan.satellite / "AGENTS.md").read_text(encoding="utf-8"))
    loaders = plan.satellite / "system" / "loaders"
    assert {stem for _prefix, stem in rows} == {Path(fname).stem for fname in ROLE_LAYER_FILES}
    for prefix, stem in rows:
        assert prefix.replace("-", "_") == stem, prefix
        assert (loaders / f"{stem}.md").is_file(), prefix


def test_pm_carries_context_read_the_others_do_not(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    loaders = plan.satellite / "system" / "loaders"
    pm_text = (loaders / "pm.md").read_text(encoding="utf-8")
    assert "CONTEXT_PM.md" in pm_text
    assert "No on-invocation context read." not in pm_text

    for role in spawn_satellite.ROLE_TITLES:
        text = (loaders / f"{role}.md").read_text(encoding="utf-8")
        assert "No on-invocation context read." in text
        assert "CONTEXT_PM.md" not in text


def test_no_stamped_role_file_contains_an_html_comment_block(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    loaders = plan.satellite / "system" / "loaders"
    for fname in ROLE_LAYER_FILES:
        text = (loaders / fname).read_text(encoding="utf-8")
        assert "<!--" not in text and "-->" not in text
    cross_role = (plan.satellite / "system" / "CROSS_ROLE.md").read_text(encoding="utf-8")
    assert "<!--" not in cross_role and "-->" not in cross_role


def test_stamped_overlays_pin_version_1_0_0(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    loaders = plan.satellite / "system" / "loaders"
    for fname in ROLE_LAYER_FILES:
        text = (loaders / fname).read_text(encoding="utf-8")
        assert text.startswith('---\nversion: "1.0.0"\n---\n')


def test_no_stamped_role_file_begins_with_a_blank_line(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    loaders = plan.satellite / "system" / "loaders"
    for fname in ROLE_LAYER_FILES:
        text = (loaders / fname).read_text(encoding="utf-8")
        assert not text.startswith("\n"), fname
    cross_role = (plan.satellite / "system" / "CROSS_ROLE.md").read_text(encoding="utf-8")
    assert not cross_role.startswith("\n")
    assert cross_role.startswith("# Cross-role contract — kensaiapp-probe")


def test_check_writes_nothing_for_task_4(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=True)

    assert not (plan.satellite / "system" / "loaders").exists()
    assert not (plan.satellite / "system" / "CROSS_ROLE.md").exists()


# --------------------------------------------------------------------------------------------
# Task 5 — the satellite's own settings.local.json
# --------------------------------------------------------------------------------------------


def test_settings_local_written_fresh_with_empty_allow(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    data = json.loads((plan.satellite / ".claude" / "settings.local.json").read_text(encoding="utf-8"))
    assert data["permissions"]["allow"] == []


def test_settings_local_grants_absolute_product_path(host: Path, tmp_path: Path):
    product = tmp_path / "external-product"
    plan = _plan(host, project="demo", product_path=str(product))
    spawn_satellite.spawn(plan, check=False)

    data = json.loads((plan.satellite / ".claude" / "settings.local.json").read_text(encoding="utf-8"))
    assert data["permissions"]["additionalDirectories"] == [os.path.normpath(str(product))]


def test_settings_local_empty_directories_for_relative_product_path(host: Path):
    plan = _plan(host, project="demo", product_path="products/demo")
    spawn_satellite.spawn(plan, check=False)

    data = json.loads((plan.satellite / ".claude" / "settings.local.json").read_text(encoding="utf-8"))
    assert data["permissions"]["additionalDirectories"] == []


def test_hosts_settings_local_is_never_read(host: Path):
    (host / ".claude" / "settings.local.json").write_text('{"permissions": {"allow": ["poison"]}}\n')
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    data = json.loads((plan.satellite / ".claude" / "settings.local.json").read_text(encoding="utf-8"))
    assert data["permissions"]["allow"] == []


def test_check_writes_nothing_for_task_5(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=True)

    assert not (plan.satellite / ".claude" / "settings.local.json").exists()


# --------------------------------------------------------------------------------------------
# Task 6 — delegate the linking and the first project
# --------------------------------------------------------------------------------------------


def test_delegates_linking_to_link_satellite(host: Path):
    (host / ".claude" / "settings.json").write_text(
        json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": (
            'python3 "${CLAUDE_PROJECT_DIR}/.claude/hooks/resolve_core.py"'
        )}]}]}})
    )
    plan = _plan(host, skills_mode="consumer")
    spawn_satellite.spawn(plan, check=False)

    claude = plan.satellite / ".claude"
    written = claude / "settings.json"
    assert written.is_file() and not written.is_symlink()
    command = json.loads(written.read_text())["hooks"]["Stop"][0]["hooks"][0]["command"]
    assert command == f'python3 "{host / ".claude" / "hooks"}/resolve_core.py"'
    assert not os.path.lexists(claude / "hooks")


def test_spawned_consumer_holds_no_root_skills_layer_when_the_host_carries_one(host: Path):
    """A consumer's launchers find grouped skills under the host root, so `link_satellite.py`
    gives it no root `skills/` layer, whatever the host carries."""
    grouped = host / "skills" / "g" / ".claude" / "skills" / "x"
    grouped.mkdir(parents=True)
    (grouped / "SKILL.md").write_text("grouped skill\n")

    plan = _plan(host, skills_mode="consumer")
    spawn_satellite.spawn(plan, check=False)

    assert not os.path.lexists(plan.satellite / "skills")


def test_delegates_project_stamp_when_project_given(host: Path):
    plan = _plan(host, project="demo")
    spawn_satellite.spawn(plan, check=False)

    project_md = plan.satellite / "system" / "projects" / "demo" / "project.md"
    assert project_md.exists()


# --- project-stamp resolves through skill_path, rooted at plan.host --------------------------
# `_invoke_stamp_project` must resolve `project-stamp` through `skill_path`, rooted at the
# HOST (never the satellite), so a host whose only copy is grouped still delegates, and a missing
# or duplicated copy on the host fails loudly rather than a bare hand-built path silently missing
# it.


def _relocate_project_stamp_to_group(host: Path, group: str = "g") -> None:
    """Move the host's flat `project-stamp` skill under `skills/<group>/.claude/skills/` —
    the grouped mirror of `_make_host`'s flat placement, with no flat copy left behind."""
    flat = host / ".claude" / "skills" / "project-stamp"
    grouped = host / "skills" / group / ".claude" / "skills" / "project-stamp"
    grouped.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(flat), str(grouped))


def test_delegates_project_stamp_when_the_host_is_grouped(tmp_path: Path):
    host = _make_host(tmp_path)
    _relocate_project_stamp_to_group(host)
    assert not (host / ".claude" / "skills" / "project-stamp").exists()

    plan = _plan(host, project="demo")
    spawn_satellite.spawn(plan, check=False)

    project_md = plan.satellite / "system" / "projects" / "demo" / "project.md"
    assert project_md.exists()


def test_project_stamp_not_found_on_host_raises_system_exit(tmp_path: Path):
    host = _make_host(tmp_path)
    shutil.rmtree(host / ".claude" / "skills" / "project-stamp")
    plan = _plan(host, project="demo")

    with pytest.raises(SystemExit, match="project-stamp"):
        spawn_satellite.spawn(plan, check=False)

    assert not (plan.satellite / "system" / "projects" / "demo").exists()


def test_project_stamp_two_copies_on_host_raises_system_exit_listing_both(tmp_path: Path):
    host = _make_host(tmp_path)
    shutil.rmtree(host / ".claude" / "skills" / "project-stamp")
    for group in ("a", "b"):
        grouped = host / "skills" / group / ".claude" / "skills" / "project-stamp" / "scripts"
        grouped.mkdir(parents=True)
        (grouped / "stamp_project.py").write_text(
            (REAL_PROJECT_STAMP / "stamp_project.py").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    plan = _plan(host, project="demo")

    with pytest.raises(SystemExit) as excinfo:
        spawn_satellite.spawn(plan, check=False)

    message = str(excinfo.value)
    assert str(host / "skills" / "a" / ".claude" / "skills" / "project-stamp") in message
    assert str(host / "skills" / "b" / ".claude" / "skills" / "project-stamp") in message
    assert not (plan.satellite / "system" / "projects" / "demo").exists()


def test_project_stamp_resolves_against_the_host_never_the_satellite(tmp_path: Path):
    # The skill is resolved on the HOST. A copy sitting in the satellite must not satisfy the
    # resolution — the satellite is where the stamper *runs*, never where the skill is found.
    host = _make_host(tmp_path)
    shutil.rmtree(host / ".claude" / "skills" / "project-stamp")
    plan = _plan(host, project="demo")
    satellite_copy = plan.satellite / ".claude" / "skills" / "project-stamp" / "scripts"
    satellite_copy.mkdir(parents=True)
    (satellite_copy / "stamp_project.py").write_text(
        (REAL_PROJECT_STAMP / "stamp_project.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as excinfo:
        spawn_satellite._invoke_stamp_project(plan)

    message = str(excinfo.value)
    assert "project-stamp" in message
    assert str(host) in message
    assert not (plan.satellite / "system" / "projects" / "demo").exists()


def test_no_project_flag_scaffolds_nothing(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    assert not (plan.satellite / "system" / "projects").exists()


def test_scaffold_placement_is_external_for_absolute_product_path(host: Path, tmp_path: Path):
    product = tmp_path / "external-product"
    plan = _plan(host, project="demo", product_path=str(product))
    spawn_satellite.spawn(plan, check=False)

    project_md = (plan.satellite / "system" / "projects" / "demo" / "project.md").read_text(
        encoding="utf-8"
    )
    assert str(product) in project_md


def test_a_delegated_tools_non_zero_exit_aborts_and_surfaces_its_message(host: Path):
    plan = _plan(host, project="bad/name")

    with pytest.raises(SystemExit, match="invalid project name"):
        spawn_satellite.spawn(plan, check=False)


def test_neither_delegated_tool_is_invoked_under_check(host: Path):
    plan = _plan(host, project="demo")
    spawn_satellite.spawn(plan, check=True)

    assert not (plan.satellite / ".claude" / "settings.json").exists()
    assert not (plan.satellite / "system" / "projects").exists()


# --------------------------------------------------------------------------------------------
# Task 7 — verify what was produced, then commit it
# --------------------------------------------------------------------------------------------


def test_link_satellite_check_passes_against_the_produced_satellite(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)
    # No exception is the assertion — _verify() calls link_satellite.py --check itself and
    # raises SystemExit on anything but a clean 0.
    spawn_satellite._verify(plan)


def test_verify_fails_loudly_if_core_dir_exists(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)
    (plan.satellite / "core").mkdir()

    with pytest.raises(SystemExit, match="core/"):
        spawn_satellite._verify(plan)


def test_verify_fails_loudly_on_a_literal_core_path_in_a_role_loader(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)
    loader = plan.satellite / "system" / "loaders" / "developer.md"
    loader.write_text(loader.read_text(encoding="utf-8") + "\nSee core/tools/foo.py.\n", encoding="utf-8")

    with pytest.raises(SystemExit, match=str(loader)):
        spawn_satellite._verify(plan)


def test_verify_fails_loudly_on_a_tilde_claude_path_in_a_role_loader(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)
    loader = plan.satellite / "system" / "loaders" / "developer.md"
    loader.write_text(loader.read_text(encoding="utf-8") + "\nSee ~/.claude/foo.\n", encoding="utf-8")

    with pytest.raises(SystemExit, match=str(loader)):
        spawn_satellite._verify(plan)


def test_verify_does_not_false_positive_on_agents_mds_own_prose(host: Path):
    """AGENTS.md legitimately mentions `~/.claude/CLAUDE.md` in prose — it is not one of the
    core-referencing files the manifest's drift-check applies to (that set is skills / prompts /
    loaders / CONTEXT_PM / CROSS_ROLE / agents), so it must not trip this check."""
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)
    agents_md = (plan.satellite / "AGENTS.md").read_text(encoding="utf-8")
    assert "~/.claude" in agents_md
    spawn_satellite._verify(plan)  # must not raise


def test_verify_fails_loudly_on_a_missing_role_loader(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)
    loader = plan.satellite / "system" / "loaders" / "developer.md"
    loader.unlink()

    with pytest.raises(SystemExit, match=str(loader)):
        spawn_satellite._verify(plan)


def test_verify_passes_when_every_overlay_names_the_satellite(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)
    spawn_satellite._verify(plan)  # must not raise: correct baseline


def test_verify_fails_loudly_if_an_overlay_names_the_host(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)
    loader = plan.satellite / "system" / "loaders" / "developer.md"
    loader.write_text(loader.read_text(encoding="utf-8").replace("kensaiapp-probe", host.name), encoding="utf-8")

    with pytest.raises(SystemExit, match=str(loader)):
        spawn_satellite._verify(plan)


def test_genesis_commit_lands_with_role_meta(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False, co_authored_by="Claude Sonnet 5 <noreply@anthropic.com>")

    log = subprocess.run(
        ["git", "-C", str(plan.satellite), "log", "-1", "--format=%B"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "Role: Meta" in log
    assert "Surface: Claude Code" in log
    assert "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>" in log
    assert "Michi: none" in log


def test_genesis_commit_staged_set_covers_everything_created(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    status = subprocess.run(
        ["git", "-C", str(plan.satellite), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    ).stdout
    # Nothing uncommitted except gitignored per-machine files (.env, settings.local.json), which
    # git status --porcelain omits entirely once .gitignore excludes them.
    assert status.strip() == ""


def test_genesis_staged_set_carries_the_settings_the_linker_wrote(host: Path):
    """CP-468 — the satellite's `.claude/` holds the written `settings.json`, so the genesis
    commit's staged set names `.claude` on the linker's say alone, whatever else the spawn's own
    record holds there. Before this change the linker's link was a `created` entry; its write is
    now a `written` one."""
    plan = _plan(host)
    link_report = link_satellite.Report(
        written=[str(plan.satellite / ".claude" / "settings.json")]
    )

    add_paths = spawn_satellite._derive_add_paths(plan, spawn_satellite.Report(), link_report)

    assert add_paths == [".claude"]


def _make_host_with_root_skills(tmp_path: Path) -> Path:
    """A host whose root `skills/` is real — `skills/<group>/.claude/skills/<name>/`, the shape
    a skill group takes once it has moved out of `.claude/skills`. No host carries this today
    (re-checked 2026-08-25: this worktree, the main checkout, and all three satellites lack a
    root `skills/`), so a genesis-commit test run against a fixture host that also lacks one would
    pass whether or not the root layer is staged. This is the fixture that makes the assertion
    below able to fail."""
    host = _make_host(tmp_path)
    grouped = host / "skills" / "g" / ".claude" / "skills" / "x"
    grouped.mkdir(parents=True)
    (grouped / "SKILL.md").write_text("grouped skill\n", encoding="utf-8")
    return host


@pytest.mark.parametrize("skills_mode", ["producer"])
def test_genesis_commit_stages_the_root_skills_layer_when_the_host_carries_one(
    tmp_path: Path, skills_mode: str
):
    """The genesis commit carries every top-level entry the run created — including one the
    spawn never writes itself, that only `link_satellite.py` creates. `.claude` already rides a
    fixed tuple entry; the root `skills/` layer does not, so this is the case a hardcoded list
    silently drops. Only a producer is given the layer (a real tree, so `git ls-files` lists a
    `skills/...` prefix); a consumer gets none, which the test above pins."""
    host = _make_host_with_root_skills(tmp_path)
    plan = _plan(host, skills_mode=skills_mode)
    spawn_satellite.spawn(plan, check=False)

    tracked = subprocess.run(
        ["git", "-C", str(plan.satellite), "ls-files"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert any(p == "skills" or p.startswith("skills/") for p in tracked), (
        f"root 'skills' layer was created but not staged in the genesis commit; tracked={tracked}"
    )

    status = subprocess.run(
        ["git", "-C", str(plan.satellite), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert status.strip() == ""


# --------------------------------------------------------------------------------------------
# Task 8 — idempotence across the whole script
# --------------------------------------------------------------------------------------------


def test_second_run_over_a_complete_satellite_creates_nothing_and_exits_zero(host: Path):
    argv = _argv(name="kensaiapp-probe", location=host.parent, host=host)
    assert spawn_satellite.main(argv) == 0

    log_before = subprocess.run(
        ["git", "-C", str(host.parent / "kensaiapp-probe"), "log", "--oneline"],
        capture_output=True, text=True, check=True,
    ).stdout

    assert spawn_satellite.main(argv) == 0

    log_after = subprocess.run(
        ["git", "-C", str(host.parent / "kensaiapp-probe"), "log", "--oneline"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert log_before == log_after  # no second genesis/empty commit landed


def test_second_run_over_a_satellite_missing_one_file_creates_exactly_that_file(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)
    (plan.satellite / "system" / "michi.md").unlink()

    report = spawn_satellite.spawn(plan, check=False)
    assert report.created == [str(plan.satellite / "system" / "michi.md")]
    assert (plan.satellite / "system" / "michi.md").exists()


def test_a_real_file_at_a_stamped_path_is_reported_and_never_overwritten(host: Path):
    plan = _plan(host)
    plan.satellite.mkdir()
    (plan.satellite / ".env").write_text(f"CORE={host}/core\n", encoding="utf-8")
    (plan.satellite / "kensaiapp.md").write_text("MY OWN CONTENT\n", encoding="utf-8")

    report = spawn_satellite.spawn(plan, check=False)

    assert (plan.satellite / "kensaiapp.md").read_text(encoding="utf-8") == "MY OWN CONTENT\n"
    assert str(plan.satellite / "kensaiapp.md") in report.already
    assert str(plan.satellite / "kensaiapp.md") not in report.created
    assert str(plan.satellite / "kensaiapp.md") not in report.updated


def test_a_drifted_agents_md_is_rewritten_from_the_template_and_reported(host: Path):
    """The one overwriting write: `AGENTS.md` holds nothing an instance authored, so a resume
    over a copy that differs from the template restores the template and says so."""
    plan = _plan(host)
    plan.satellite.mkdir()
    (plan.satellite / ".env").write_text(f"CORE={host}/core\n", encoding="utf-8")
    (plan.satellite / "AGENTS.md").write_text("A STALE LOADER MAP\n", encoding="utf-8")

    report = spawn_satellite.spawn(plan, check=False)

    template = (host / "core" / "templates" / "agents_md_template.md").read_text(encoding="utf-8")
    assert (plan.satellite / "AGENTS.md").read_text(encoding="utf-8") == template
    assert str(plan.satellite / "AGENTS.md") in report.updated
    assert str(plan.satellite / "AGENTS.md") not in report.created


def test_check_reports_a_drifted_agents_md_and_leaves_it(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)
    (plan.satellite / "AGENTS.md").write_text("A STALE LOADER MAP\n", encoding="utf-8")

    report = spawn_satellite.spawn(plan, check=True)

    assert (plan.satellite / "AGENTS.md").read_text(encoding="utf-8") == "A STALE LOADER MAP\n"
    assert report.updated == [str(plan.satellite / "AGENTS.md")]
    assert report.would_change


def test_an_agents_md_equal_to_the_template_is_already_present(host: Path):
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    report = spawn_satellite.spawn(plan, check=True)

    assert str(plan.satellite / "AGENTS.md") in report.already
    assert report.updated == []


def test_check_after_a_complete_run_exits_zero(host: Path):
    argv = _argv(name="kensaiapp-probe", location=host.parent, host=host)
    assert spawn_satellite.main(argv) == 0
    assert spawn_satellite.main(argv + ["--check"]) == 0


def test_check_against_a_satellite_missing_a_file_exits_one(host: Path):
    argv = _argv(name="kensaiapp-probe", location=host.parent, host=host)
    assert spawn_satellite.main(argv) == 0
    (host.parent / "kensaiapp-probe" / "system" / "michi.md").unlink()
    assert spawn_satellite.main(argv + ["--check"]) == 1


# --------------------------------------------------------------------------------------------
# Verification before the closing commit — the leak test. A template cannot carry a sibling
# instance's facts; this proves the script didn't reintroduce a path that could (the withdrawn
# `kensaiapp-spawn`'s whole failure — `SKILL.md:132`'s "start from the host's, then rewrite the
# instance-specific sentences" carried the host's own facts into a fresh instance).
# --------------------------------------------------------------------------------------------

# The host's own facts, plus every product and declared name the neutrality check knows — read
# from the live host rather than written here, since a name written into this file is itself the
# leak the check exists to catch.
_HOST = Path(__file__).resolve().parents[2]
LEAK_WORDS = (
    "product-definition", "trading", "example-host", "example-product", "open-source tools",
    *sorted(
        check_vendor_neutrality.product_name_sources(_HOST).names
        | check_vendor_neutrality._declared_names(_HOST)
    ),
)


# This test carried one pinned exception until `setup_seed_template.md` was fixed: that template
# cited `system/projects/product-definition/…` — the HOST's own project — and project-stamp
# stamped it verbatim into every satellite's first project seed. The exception is gone because the
# defect is, and an exception that outlives its defect stops guarding the case it names.
# `core/tools/test_templates_are_instance_neutral.py` now holds the general form, so the next
# template to lose the property fails there rather than being pinned here.


def test_a_full_stamp_carries_none_of_the_hosts_own_facts(host: Path, tmp_path: Path):
    """Scoped to what a spawn produces, minus `.env`/`.env.example` — their `CORE=<host>/core`
    binding legitimately names the host; that is the mechanism, not a leak."""
    plan = _plan(host, project="demo")
    spawn_satellite.spawn(plan, check=False)

    excluded_files = {plan.satellite / ".env", plan.satellite / ".env.example"}

    offenders = []
    for path in plan.satellite.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        if ".git" in path.parts or path in excluded_files:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for word in LEAK_WORDS:
            if word in text:
                offenders.append((str(path), word))

    assert offenders == []


# --------------------------------------------------------------------------------------------
# Integrity pass — behaviours the plan states that had no test of their own, or whose test
# could not have failed if the code had done the other thing. Each is derived from the plan's
# stated behaviour, never from reading spawn_satellite.py.
# --------------------------------------------------------------------------------------------


def test_check_prints_the_resolved_plan(host: Path, capsys):
    """Task 1: `--check` *prints the resolved plan*. The other --check tests all assert what is
    NOT created; nothing asserted the printing half, which is the only output an operator gets
    from a run that deliberately does nothing."""
    argv = _argv(name="kensaiapp-probe", location=host.parent, host=host) + ["--check"]
    spawn_satellite.main(argv)

    out = capsys.readouterr().out
    assert "kensaiapp-probe" in out
    assert str(host) in out
    assert str(host.parent / "kensaiapp-probe") in out
    assert "consumer" in out


def test_location_refusal_says_why_not_just_that_it_is_invalid(host: Path, tmp_path: Path):
    """Task 1: the location refusal's message 'says that, not "invalid location"' — it must name
    the offending path AND what was wrong with it. Matching only the value cannot tell two
    different refusal messages apart.

    It must also not cite either retired rationale. `relative` went when links became absolute;
    `beside` went when `shared_core_instance.md` freed placement. A refusal that still explains
    itself by a rule the system no longer holds is worse than a terse one."""
    missing = tmp_path / "no-such-dir"
    args = spawn_satellite._build_arg_parser().parse_args(
        _argv(name="kensaiapp-probe", location=missing, host=host)
    )

    with pytest.raises(SystemExit) as excinfo:
        spawn_satellite.resolve_plan(args)

    message = str(excinfo.value)
    assert str(missing) in message
    assert "existing directory" in message
    assert "relative" not in message, "the relative-link rationale is retired; do not cite it"
    assert "beside" not in message, "the beside-the-host placement rule is retired; do not cite it"


def test_a_refusal_exits_non_zero_at_the_process_level(host: Path, tmp_path: Path):
    """Task 1: 'A refusal exits non-zero and names the offending value.' In-process
    `pytest.raises(SystemExit)` proves neither — a `SystemExit` is raised on the success path
    too, and its exit *code* is what a caller (a skill, a shell, CI) actually reads."""
    missing = tmp_path / "no-such-dir"
    result = subprocess.run(
        [sys.executable, str(REAL_CORE_TOOLS / "spawn_satellite.py")]
        + _argv(name="kensaiapp-probe", location=missing, host=host),
        capture_output=True, text=True,
    )

    assert result.returncode != 0
    assert str(missing) in result.stderr


def test_consumer_mode_links_no_skills_layer(host: Path):
    """Task 6: link_satellite.py is invoked with 'the answered --skills-mode'. The two answers
    produce observably different skills layers; asserting only that linking happened (a hooks
    symlink) would pass just as well if the mode were hardcoded. A consumer gets none."""
    _relocate_project_stamp_to_group(host)
    plan = _plan(host, skills_mode="consumer")
    spawn_satellite.spawn(plan, check=False)

    assert not os.path.lexists(plan.satellite / ".claude" / "skills")
    assert not os.path.lexists(plan.satellite / "skills")


def test_producer_mode_is_forwarded_and_yields_real_directories(host: Path):
    """Task 6, the other answer: producer means the host's root `skills/` mirrored as real
    directories + file symlinks, so a write lands in the satellite. This is red if
    `--skills-mode` is dropped or pinned to consumer."""
    _relocate_project_stamp_to_group(host)
    plan = _plan(host, skills_mode="producer")
    spawn_satellite.spawn(plan, check=False)

    skills = plan.satellite / "skills" / "g" / ".claude" / "skills"
    assert skills.is_dir() and not skills.is_symlink()
    scripts = skills / "project-stamp" / "scripts"
    assert scripts.is_dir() and not scripts.is_symlink()
    assert (scripts / "stamp_project.py").is_symlink()


@pytest.mark.parametrize("skills_mode", ["consumer", "producer"])
def test_spawned_satellite_has_no_agents_path(host: Path, skills_mode: str):
    """CP-440: a spawned satellite gets no `.claude/agents` in either skills mode, while its own
    `link_satellite.py --check` verification (inside `spawn`) passed, and it holds the written
    `settings.json` and no `hooks`, `workflows` or `settings.json` link (CP-468)."""
    if skills_mode == "producer":
        _relocate_project_stamp_to_group(host)
    plan = _plan(host, skills_mode=skills_mode)
    spawn_satellite.spawn(plan, check=False)

    claude = plan.satellite / ".claude"
    assert not os.path.lexists(claude / "agents")
    written = claude / "settings.json"
    assert written.is_file() and not written.is_symlink()
    for layer in ("hooks", "workflows"):
        assert not os.path.lexists(claude / layer)


def test_scaffold_placement_is_internal_for_a_relative_product_path(host: Path):
    """Task 6: '--placement internal when it is not [absolute]'. Only the external half was
    asserted. stamp_project.py refuses external placement with a relative path, so a wrong
    placement here aborts the run — which makes this a real discriminator, not a smoke test."""
    plan = _plan(host, project="demo", product_path="products/demo")
    spawn_satellite.spawn(plan, check=False)

    project_md = (plan.satellite / "system" / "projects" / "demo" / "project.md").read_text(
        encoding="utf-8"
    )
    assert "products/demo" in project_md


def test_a_link_satellite_failure_aborts_and_surfaces_its_own_message(host: Path):
    """Task 6: 'A non-zero exit from **either** aborts the run and surfaces that tool's own
    message unaltered.' Only the stamp_project half was covered."""
    plan = _plan(host)
    shutil.rmtree(host / ".claude")

    with pytest.raises(SystemExit) as excinfo:
        spawn_satellite.spawn(plan, check=False)

    message = str(excinfo.value)
    assert "link_satellite.py" in message
    assert "host has no .claude/ layer" in message  # the delegate's own words, unaltered


def test_stamped_overlay_version_is_pinned_not_inherited(host: Path):
    """Task 4: 'Each stamped overlay's frontmatter `version` is `1.0.0`, **regardless of the
    template's own**.' The shipped templates already say 1.0.0, so asserting 1.0.0 against them
    cannot tell a pin apart from a copy. Move the template's version and the assertion bites."""
    role_templates = host / "core" / "templates" / "role-templates"
    for name in ("overlay_template.md", "pm_overlay_template.md"):
        path = role_templates / name
        path.write_text(
            path.read_text(encoding="utf-8").replace('version: "1.0.0"', 'version: "9.9.9"'),
            encoding="utf-8",
        )

    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    loaders = plan.satellite / "system" / "loaders"
    for fname in ROLE_LAYER_FILES:
        text = (loaders / fname).read_text(encoding="utf-8")
        assert text.startswith('---\nversion: "1.0.0"\n---\n'), fname
        assert "9.9.9" not in text, fname


def test_no_substitution_token_survives_unresolved_in_a_stamped_file(host: Path):
    """Tasks 3 and 4: every stamped file carries the template's tokens *resolved*. The
    per-file tests each assert one resolved token in one place; a second occurrence elsewhere in
    the same template would ship as a literal `<instance>` and nothing would notice.

    Scoped to the three substitution tokens the templates' own metadata names. `<name>`,
    `<project>` and `<role>` also appear in AGENTS.md / CROSS_ROLE.md prose as deliberate generic
    path patterns (`system/projects/<name>/project.md`) — the live instances carry them, so they
    are content, not unresolved tokens."""
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    loaders = plan.satellite / "system" / "loaders"
    doctrine = plan.satellite / "system" / "doctrine"
    targets = [
        plan.satellite / "AGENTS.md",
        plan.satellite / "kensaiapp.md",
        plan.satellite / ".gitignore",
        plan.satellite / "system" / "michi.md",
        plan.satellite / "system" / "nemawashi" / "README.md",
        plan.satellite / "system" / "shukuba" / "README.md",
        plan.satellite / "system" / "CROSS_ROLE.md",
        doctrine / "kensaiapp_doctrine.md",
        doctrine / "ai_responsibility.md",
        doctrine / "doctrine_structure.md",
    ] + [loaders / fname for fname in ROLE_LAYER_FILES]

    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert "<instance>" not in text, path
        assert "<scope>" not in text, path

    for fname in ROLE_LAYER_FILES:
        assert "<Role Title>" not in (loaders / fname).read_text(encoding="utf-8"), fname


def test_second_run_over_a_complete_satellite_creates_nothing_in_the_report(host: Path):
    """Task 8: 'A second run over a complete satellite **creates nothing** and exits 0.' The
    existing test reads that off an unchanged git log, which an overwrite with identical content
    would also satisfy. The report is where "created nothing" is actually stated."""
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    report = spawn_satellite.spawn(plan, check=False)

    assert report.created == []
    assert not report.would_change


# --------------------------------------------------------------------------------------------
# Code integrity — behaviours the plan states that had no assertion. The plan's own oracle, the
# stamped journey READMEs against this instance's own, reads this instance's `system/` and is
# `system/tests/test_instance_spawn_satellite.py`.
# --------------------------------------------------------------------------------------------


def test_no_directory_the_stamper_creates_under_system_is_left_empty(host: Path):
    """§ The directory stubs: 'every journey directory this stamper creates gets a `.gitkeep`',
    because git does not track an empty directory and the path would not survive a clone. Stated
    as a property over the whole stamped tree rather than per known path, so a future bare
    `mkdir` under `system/` is caught by the same assertion that catches today's."""
    plan = _plan(host)
    spawn_satellite.spawn(plan, check=False)

    system = plan.satellite / "system"
    empty = sorted(
        str(path.relative_to(plan.satellite))
        for path in system.rglob("*")
        if path.is_dir() and not any(path.iterdir())
    )

    assert empty == []


def test_every_file_the_stamper_creates_under_system_is_tracked_by_git(host: Path):
    """The genesis commit stages the `system` prefix, so a created path under it is tracked —
    unless it is an empty directory, which git cannot track at all. That is the whole reason the
    stubs are `.gitkeep` files, so the tracked set is where it is proven."""
    plan = _plan(host)
    report = spawn_satellite.spawn(plan, check=False)

    tracked = set(
        subprocess.run(
            ["git", "-C", str(plan.satellite), "ls-files"],
            capture_output=True, text=True, check=True,
        ).stdout.split()
    )

    created_under_system = sorted(
        str(Path(path).relative_to(plan.satellite))
        for path in report.created
        if Path(path).is_relative_to(plan.satellite / "system")
    )
    assert created_under_system, "the stamper created nothing under system/ — fixture is wrong"
    assert [path for path in created_under_system if path not in tracked] == []
