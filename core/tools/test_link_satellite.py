"""Contract tests for `link_satellite.py`.

Every test builds a throwaway host + satellite pair under tmp_path. They are placed as siblings
because that is the common case, but nothing here depends on it: absolute links read the same
from any position, which is the point of the form. Nothing here touches a live instance.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import link_satellite


def _make_host(root: Path, *, grouped: bool = True) -> Path:
    """A minimal host instance carrying every layer the script links. `grouped=False` builds a host
    that has created no root `skills/` yet — the absent-source case."""
    host = root / "example-host"
    claude = host / ".claude"
    (claude / "hooks").mkdir(parents=True)
    (claude / "hooks" / "resolve_core.py").write_text("# hook\n")
    (claude / "workflows").mkdir()
    (claude / "workflows" / "development.js").write_text("// workflow\n")
    (claude / "agents").mkdir()
    (claude / "agents" / "cpo.md").write_text("agent\n")
    (claude / "settings.json").write_text("{}\n")
    if not grouped:
        return host
    # Every host skill lives in a group; the flat `.claude/skills/` holds none.
    skills = host / "skills" / "pm" / ".claude" / "skills"
    (skills / "product-prd").mkdir(parents=True)
    (skills / "product-prd" / "SKILL.md").write_text("skill\n")
    (skills / "product-prd" / "evals").mkdir()
    (skills / "product-prd" / "evals" / "evals.json").write_text("{}\n")
    return host


def _make_satellite(root: Path) -> Path:
    sat = root / "kensaiapp-probe"
    sat.mkdir()
    return sat


@pytest.fixture
def pair(tmp_path: Path) -> tuple[Path, Path]:
    return _make_satellite(tmp_path), _make_host(tmp_path)


LIVE_PREFIX = "${CLAUDE_PROJECT_DIR}/.claude/hooks/"
RESOLVE_CORE_SOURCE = Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "resolve_core.py"


def _hook_entry(script: str) -> dict:
    return {"type": "command", "command": f'python3 "{LIVE_PREFIX}{script}"'}


def _wire_hooks(host: Path) -> dict:
    """Give the host's `settings.json` a hook wiring and an owner-only key, and return the
    document written. Nothing here uses `hook_wiring` — the expectation is built independently."""
    document = {
        "permissions": {"defaultMode": "acceptEdits"},
        "hooks": {
            "SessionStart": [{"hooks": [_hook_entry("resolve_core.py"), _hook_entry("a.py")]}],
            "PreToolUse": [{"matcher": "Bash", "hooks": [_hook_entry("guard.py")]}],
        },
    }
    (host / ".claude" / "settings.json").write_text(json.dumps(document, indent=2) + "\n")
    return document


def _expected_settings(host: Path) -> str:
    """The text a satellite's `settings.json` must hold: the host's `hooks` key alone, with each
    live prefix replaced by the host's hooks directory, as the spec words it."""
    document = json.loads((host / ".claude" / "settings.json").read_text())
    kept = {"hooks": document["hooks"]} if "hooks" in document else {}
    rendered = json.dumps(kept, indent=2) + "\n"
    return rendered.replace(LIVE_PREFIX, str(host / ".claude" / "hooks") + "/")


def _skill_file(root: Path) -> Path:
    """The one mirrored skill file `_make_host` gives a producer, under `root`."""
    return root / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "SKILL.md"


def _add_root_skills_layer(host: Path, *, group: str = "g", skill: str = "x") -> Path:
    """Add a group to the host's root `skills/` layer — `skills/<group>/.claude/skills/<skill>/`,
    beside the `pm` group `_make_host` already builds. The absent-source case is
    `_make_host(grouped=False)`."""
    grouped = host / "skills" / group / ".claude" / "skills" / skill
    grouped.mkdir(parents=True)
    (grouped / "SKILL.md").write_text("grouped skill\n")
    return host / "skills"


# --------------------------------------------------------------------------------------------
# The three always-linked layers
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ["consumer", "producer"])
def test_no_toolchain_link_is_made_in_either_mode(pair, mode):
    """CP-460: nothing under `.claude/` is linked. The host still holds `hooks/`, `workflows/` and
    `agents/`, and the satellite gets no path at any of them but the written `settings.json`."""
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode=mode)

    for name in ("hooks", "workflows", "settings.json"):
        assert not (sat / ".claude" / name).is_symlink(), f"{name} must not be a symlink"
    assert not os.path.lexists(sat / ".claude" / "hooks")
    assert not os.path.lexists(sat / ".claude" / "workflows")
    assert (host / ".claude" / "agents" / "cpo.md").exists()
    assert not os.path.lexists(sat / ".claude" / "agents")


def test_settings_json_is_written_as_a_regular_file_with_only_hooks(pair):
    """CP-459: the host's `hooks` and `permissions`; the satellite's file is regular, holds `hooks`
    alone, and every hook command names the host's own hooks directory."""
    sat, host = pair
    _wire_hooks(host)

    link_satellite.link_satellite(sat, host, skills_mode="consumer")

    written = sat / ".claude" / "settings.json"
    assert written.is_file() and not written.is_symlink()
    document = json.loads(written.read_text())
    assert list(document) == ["hooks"]
    commands = [
        hook["command"]
        for group in document["hooks"].values()
        for entry in group
        for hook in entry["hooks"]
    ]
    assert commands and all(str(host / ".claude" / "hooks") + "/" in c for c in commands)
    assert LIVE_PREFIX not in written.read_text()
    assert written.read_text() == _expected_settings(host)


def test_a_host_with_no_hooks_key_gives_an_empty_object(pair):
    sat, host = pair
    (host / ".claude" / "settings.json").write_text(json.dumps({"permissions": {}}))

    link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert json.loads((sat / ".claude" / "settings.json").read_text()) == {}


def test_links_are_absolute(pair):
    """Absolute is the only form: a link carries the host's full path, so it reads the same from
    anywhere and does not depend on where the satellite sits. The written hook commands carry the
    same absolute path."""
    sat, host = pair
    _wire_hooks(host)
    link_satellite.link_satellite(sat, host, skills_mode="producer")

    raw = os.readlink(_skill_file(sat))
    assert os.path.isabs(raw)
    assert raw == str(_skill_file(host))
    assert str(host / ".claude" / "hooks") + "/resolve_core.py" in (
        sat / ".claude" / "settings.json"
    ).read_text()


def test_producer_links_are_absolute_at_depth(pair):
    """Depth is where the relative form used to grow a `../` per level. Absolute does not."""
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="producer")

    nested = sat / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "evals" / "evals.json"
    raw = os.readlink(nested)
    assert os.path.isabs(raw)
    assert raw == str(host / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "evals" / "evals.json")


def test_a_satellite_outside_the_hosts_tree_is_linked_normally(tmp_path):
    """The case that retired the relative form: example-8792fa lives under a different root entirely,
    where a relative link would be a five-level `../` climb protecting nothing."""
    host = _make_host(tmp_path / "projects" / "kensai")
    _wire_hooks(host)
    far = tmp_path / "work" / "private" / "kensaiapp" / "example-8792fa"
    far.mkdir(parents=True)

    report = link_satellite.link_satellite(far, host, skills_mode="consumer")
    assert not report.needs_attention
    assert (far / ".claude" / "settings.json").read_text() == _expected_settings(host)


def test_a_relative_host_path_is_refused(pair, monkeypatch):
    """An absolute link cannot be written from a relative host path — refused, not guessed at."""
    sat, host = pair
    monkeypatch.chdir(host.parent)
    with pytest.raises(SystemExit):
        link_satellite.link_satellite(sat, Path(host.name), skills_mode="consumer")


# --------------------------------------------------------------------------------------------
# skills/ — the layer with two answers
# --------------------------------------------------------------------------------------------


def test_consumer_gets_no_skills_link(pair):
    """Every host skill lives in a group and a consumer's launchers grant the group from the host,
    so a consumer is given no skills layer at all — neither the flat `.claude/skills` nor the root
    `skills/`."""
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="consumer")
    assert not os.path.lexists(sat / ".claude" / "skills")
    assert not os.path.lexists(sat / "skills")


def test_producer_skills_directories_are_real_so_artifacts_stay_local(pair):
    """The sharp edge: under a directory symlink, `skill-evals` writing to
    `<skill>/evals/workspace/` lands in the HOST. A producer needs real directories at every
    depth so the write stays in the satellite."""
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="producer")

    skills = sat / "skills" / "pm" / ".claude" / "skills"
    assert skills.is_dir() and not skills.is_symlink()
    assert (skills / "product-prd").is_dir() and not (skills / "product-prd").is_symlink()
    evals = skills / "product-prd" / "evals"
    assert evals.is_dir() and not evals.is_symlink(), "evals/ must be real or writes hit the host"

    # Prove it: a write into the producer's evals tree does not appear in the host.
    (evals / "workspace").mkdir()
    (evals / "workspace" / "iteration-1.md").write_text("round\n")
    assert not (host / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "evals" / "workspace").exists()


def test_producer_files_are_symlinks_at_every_depth(pair):
    """Real directories, symlinked files — so shared content still has one source."""
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="producer")

    top = sat / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "SKILL.md"
    nested = sat / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "evals" / "evals.json"
    assert top.is_symlink() and top.read_text() == "skill\n"
    assert nested.is_symlink() and nested.read_text() == "{}\n"

    # An edit in the host is seen through the link — that is the no-drift property.
    (host / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "SKILL.md").write_text("edited\n")
    assert top.read_text() == "edited\n"


def test_pycache_is_not_linked(pair):
    sat, host = pair
    (host / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "__pycache__").mkdir()
    (host / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "__pycache__" / "x.pyc").write_text("x")
    link_satellite.link_satellite(sat, host, skills_mode="producer")
    assert not (sat / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "__pycache__").exists()


def test_the_hosts_eval_workspace_is_never_mirrored(pair):
    """`evals/workspace/` is the producer's OWN output — gitignored, one round per iteration.
    Mirroring the host's rounds would hand the satellite another instance's measurements."""
    sat, host = pair
    workspace = host / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "evals" / "workspace"
    (workspace / "iteration-1").mkdir(parents=True)
    (workspace / "iteration-1" / "benchmark.json").write_text("{}\n")

    link_satellite.link_satellite(sat, host, skills_mode="producer")
    assert not (sat / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "evals" / "workspace").exists()
    # The fixtures beside it ARE shared — they are the case, not the measurement.
    assert (sat / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "evals" / "evals.json").is_symlink()


def test_a_directory_symlink_in_producer_mode_is_reported_distinctly(pair):
    """The hand-built shape: subfolders linked as whole directories. In producer mode that means
    a skill-evals round writes into the host — so it is reported apart from a plain conflict."""
    sat, host = pair
    skill_dir = sat / "skills" / "pm" / ".claude" / "skills" / "product-prd"
    skill_dir.mkdir(parents=True)
    (skill_dir / "evals").symlink_to(host / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "evals")

    report = link_satellite.link_satellite(sat, host, skills_mode="producer")
    assert any(str(skill_dir / "evals") == p for p in report.dir_links)
    assert not report.conflicts
    assert report.needs_attention
    assert (skill_dir / "evals").is_symlink(), "reported, not silently replaced"


# --------------------------------------------------------------------------------------------
# The agents folder is the satellite's own — the linker has no opinion of it
# --------------------------------------------------------------------------------------------


def _argv(sat: Path, host: Path, *extra: str) -> list[str]:
    return ["--satellite", str(sat), "--host", str(host), "--skills-mode", "consumer", *extra]


def test_check_reports_the_written_file_correct_and_no_conflicts(pair, capsys):
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="consumer")
    capsys.readouterr()

    assert link_satellite.main(_argv(sat, host, "--check")) == 0
    out = capsys.readouterr().out
    assert "already correct: 1" in out
    assert "conflicts: 0" in out


def test_real_agents_dir_is_no_conflict(pair, capsys):
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="consumer")
    (sat / ".claude" / "agents").mkdir()
    (sat / ".claude" / "agents" / "pm.md").write_text("own agent\n")
    capsys.readouterr()

    assert link_satellite.main(_argv(sat, host, "--check")) == 0
    out = capsys.readouterr().out
    assert "[conflict]" not in out
    assert ".claude/agents" not in out


def test_leftover_agents_link_is_untouched(pair, capsys):
    sat, host = pair
    (sat / ".claude").mkdir()
    link = sat / ".claude" / "agents"
    link.symlink_to(host / ".claude" / "agents")
    before = os.readlink(link)

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert os.readlink(link) == before
    assert link.is_dir()
    path = str(link)
    for entries in (
        report.created,
        report.repointed,
        report.already,
        report.dangling,
        report.conflicts,
        report.dir_links,
        report.skipped,
    ):
        assert path not in entries
    assert ".claude/agents" not in report.render(check=False)


def test_dangling_agents_link_is_reported(pair):
    sat, host = pair
    (sat / ".claude").mkdir()
    link = sat / ".claude" / "agents"
    link.symlink_to(sat / "nowhere")

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert str(link) in report.dangling
    assert f"[dangling] {link}" in report.render(check=False)


def test_dangling_entry_inside_real_agents_dir_is_reported(pair):
    sat, host = pair
    agents = sat / ".claude" / "agents"
    agents.mkdir(parents=True)
    gone = agents / "gone.md"
    gone.symlink_to(sat / "nowhere.md")

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert str(gone) in report.dangling


# --------------------------------------------------------------------------------------------
# Re-runnability — the reason this is a script and not inline shell
# --------------------------------------------------------------------------------------------


def test_rerun_is_idempotent(pair):
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="consumer")
    second = link_satellite.link_satellite(sat, host, skills_mode="consumer")
    assert second.created == []
    assert second.repointed == [], "the form it just wrote is the form it wants"
    assert second.written == [] and second.removed == []
    assert len(second.already) == 1  # settings.json


def test_rerun_adds_a_skill_created_in_the_host_after_the_first_run(pair):
    """The whole reason re-runnability matters: a file symlink carries nothing about something
    created later, and nothing fails when it is missing."""
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="producer")

    new_skill = host / "skills" / "pm" / ".claude" / "skills" / "brand-new"
    new_skill.mkdir()
    (new_skill / "SKILL.md").write_text("new\n")

    report = link_satellite.link_satellite(sat, host, skills_mode="producer")
    landed = sat / "skills" / "pm" / ".claude" / "skills" / "brand-new" / "SKILL.md"
    assert landed.is_symlink() and landed.read_text() == "new\n"
    assert any("brand-new" in p for p in report.created)


def test_dangling_link_is_reported_not_removed(pair):
    """A dangling link may point at something deleted from the host on purpose. Reporting is the
    contract; deciding is the owner's."""
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="producer")
    (host / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "SKILL.md").unlink()

    report = link_satellite.link_satellite(sat, host, skills_mode="producer")
    stale = sat / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "SKILL.md"
    assert stale.is_symlink(), "the link must still be there — reported, not removed"
    assert any(str(stale) == p for p in report.dangling)


def test_a_real_file_is_never_overwritten(pair):
    """A satellite legitimately holds its own real files. Replacing one with a link would
    destroy per-instance data, so a real file at a link path is a reported conflict. `.claude/`
    has no link path left; a producer's mirrored skill file is where the rule still applies."""
    sat, host = pair
    mine = _skill_file(sat)
    mine.parent.mkdir(parents=True)
    mine.write_text("MINE\n")

    report = link_satellite.link_satellite(sat, host, skills_mode="producer")
    assert mine.read_text() == "MINE\n"
    assert str(mine) in report.conflicts


def test_producer_evidence_directory_survives_a_rerun(pair):
    """A producer's own output sits beside the linked content. Re-running must not disturb it."""
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="producer")
    evidence = sat / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "evidence"
    evidence.mkdir()
    (evidence / "round-1.md").write_text("kept\n")

    link_satellite.link_satellite(sat, host, skills_mode="producer")
    assert (evidence / "round-1.md").read_text() == "kept\n"


# --------------------------------------------------------------------------------------------
# Converging a satellite linked before absolute-only
# --------------------------------------------------------------------------------------------


def _relink_relative(link_path: Path, target: Path) -> None:
    """Put back the form this script used to write, to link_path's own parent."""
    if link_path.is_symlink():
        link_path.unlink()
    link_path.parent.mkdir(parents=True, exist_ok=True)
    link_path.symlink_to(os.path.relpath(target, start=link_path.parent))


def test_a_relative_link_is_repointed_to_absolute(pair):
    """The convergence case. A satellite linked before absolute-only holds links that resolve
    correctly and read relative; re-running is what converts them, so no hand-repoint is needed."""
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="producer")
    skill = _skill_file(sat)
    _relink_relative(skill, _skill_file(host))
    assert not os.path.isabs(os.readlink(skill))

    report = link_satellite.link_satellite(sat, host, skills_mode="producer")

    assert any(str(skill) == p for p in report.repointed)
    assert report.created == []
    assert os.readlink(skill) == str(_skill_file(host))
    assert skill.read_text() == "skill\n", "still reaches the host"


def test_repointing_is_reported_as_drift_by_check_and_changes_nothing(pair):
    """`--check` has to see a wrong-form link, or a drift gate would pass a satellite that is
    still on the old form."""
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="producer")
    skill = _skill_file(sat)
    _relink_relative(skill, _skill_file(host))

    report = link_satellite.link_satellite(sat, host, skills_mode="producer", check=True)
    assert report.would_change
    assert not os.path.isabs(os.readlink(skill)), "--check changes nothing"

    argv = ["--satellite", str(sat), "--host", str(host), "--skills-mode", "producer"]
    assert link_satellite.main(argv + ["--check"]) == 1


def test_an_absolute_link_written_through_another_path_is_left_alone(pair):
    """Two absolute paths can differ textually and both be right — `/var` -> `/private/var` is
    the everyday case. The test is the form, not string equality, so this is not churned."""
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="producer")
    skill = _skill_file(sat)
    detour = host.parent / "detour"
    detour.symlink_to(host)
    skill.unlink()
    detour_target = detour / _skill_file(host).relative_to(host)
    skill.symlink_to(detour_target)

    report = link_satellite.link_satellite(sat, host, skills_mode="producer")
    assert report.repointed == []
    assert os.readlink(skill) == str(detour_target), "left as written"


def test_a_link_pointing_somewhere_else_is_still_a_conflict(pair):
    """Repointing is scoped to the form. A link aimed at a different target may be a deliberate
    override, and this script still refuses to decide that."""
    sat, host = pair
    other = host.parent / "elsewhere" / "SKILL.md"
    other.parent.mkdir(parents=True)
    other.write_text("other\n")
    skill = _skill_file(sat)
    skill.parent.mkdir(parents=True)
    skill.symlink_to(other)

    report = link_satellite.link_satellite(sat, host, skills_mode="producer")
    assert str(skill) in report.conflicts
    assert report.repointed == []
    assert os.readlink(skill) == str(other)


def test_repointing_leaves_no_staging_link_behind(pair):
    """The swap is create-then-rename so the path is never empty; the staging name must not
    survive it."""
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="producer")
    skill = _skill_file(sat)
    _relink_relative(skill, _skill_file(host))

    link_satellite.link_satellite(sat, host, skills_mode="producer")
    leftovers = [p.name for p in skill.parent.iterdir() if "relink-tmp" in p.name]
    assert leftovers == []


def test_a_relative_link_is_repointed_at_depth_in_producer_mode(pair):
    """The 83-link case: a producer's per-file links convert the same way, shape untouched."""
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="producer")
    nested = sat / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "evals" / "evals.json"
    _relink_relative(nested, host / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "evals" / "evals.json")

    report = link_satellite.link_satellite(sat, host, skills_mode="producer")

    assert any(str(nested) == p for p in report.repointed)
    assert os.path.isabs(os.readlink(nested))
    assert nested.read_text() == "{}\n"
    evals = sat / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "evals"
    assert evals.is_dir() and not evals.is_symlink(), "the producer shape is untouched"


# --------------------------------------------------------------------------------------------
# --check, the drift gate
# --------------------------------------------------------------------------------------------


def test_check_creates_nothing(pair):
    sat, host = pair
    report = link_satellite.link_satellite(sat, host, skills_mode="consumer", check=True)
    assert report.would_change
    assert not (sat / ".claude" / "settings.json").exists()


def test_check_exits_one_on_drift_and_zero_when_level(pair, capsys):
    sat, host = pair
    argv = ["--satellite", str(sat), "--host", str(host), "--skills-mode", "consumer"]

    assert link_satellite.main(argv + ["--check"]) == 1
    assert link_satellite.main(argv) == 0
    assert link_satellite.main(argv + ["--check"]) == 0
    capsys.readouterr()


# --------------------------------------------------------------------------------------------
# Invocation guards
# --------------------------------------------------------------------------------------------


def test_host_without_a_claude_layer_is_refused(tmp_path):
    sat = _make_satellite(tmp_path)
    bare = tmp_path / "not-an-instance"
    bare.mkdir()
    with pytest.raises(SystemExit):
        link_satellite.link_satellite(sat, bare, skills_mode="consumer")


def test_satellite_and_host_may_not_be_the_same_directory(pair):
    _, host = pair
    with pytest.raises(SystemExit):
        link_satellite.main(
            ["--satellite", str(host), "--host", str(host), "--skills-mode", "consumer"]
        )


def test_unknown_skills_mode_is_refused(pair):
    sat, host = pair
    with pytest.raises(SystemExit):
        link_satellite.link_satellite(sat, host, skills_mode="whatever")


# --------------------------------------------------------------------------------------------
# skills/ — the fifth layer, one level above `.claude/`, for skill groups moved out of it
# --------------------------------------------------------------------------------------------



def test_root_skills_consumer_is_never_linked(pair):
    """Consumer mode: the root `skills/` is not linked — the launchers a consumer runs find
    grouped skills under the host root — and nothing is reported about it, since nothing is owed."""
    sat, host = pair
    _add_root_skills_layer(host)
    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert not os.path.lexists(sat / "skills")
    assert str(sat / "skills") not in report.created
    assert not report.skipped


def test_root_skills_consumer_link_left_by_an_earlier_run_is_left_alone(pair):
    """A consumer linked before this change keeps its link until someone removes it there: the
    script neither deletes it nor walks through it into the host."""
    sat, host = pair
    _add_root_skills_layer(host)
    (sat / "skills").symlink_to(host / "skills")
    host_dangling = host / "skills" / "g" / ".claude" / "skills" / "x" / "dangling-in-host"
    host_dangling.symlink_to(host / "skills" / "does-not-exist")

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert (sat / "skills").is_symlink()
    assert not report.dangling
    assert not report.needs_attention

def test_root_skills_producer_mirrors_real_dirs_and_file_symlinks(pair):
    """Producer mode: real directories at every depth, files symlinked, so a write anywhere in
    the tree lands in the satellite."""
    sat, host = pair
    _add_root_skills_layer(host)
    link_satellite.link_satellite(sat, host, skills_mode="producer")

    root = sat / "skills"
    assert root.is_dir() and not root.is_symlink()
    nested_dir = root / "g" / ".claude" / "skills" / "x"
    assert nested_dir.is_dir() and not nested_dir.is_symlink()
    skill_md = nested_dir / "SKILL.md"
    assert skill_md.is_symlink()
    assert os.path.isabs(os.readlink(skill_md))
    assert os.readlink(skill_md) == str(
        host / "skills" / "g" / ".claude" / "skills" / "x" / "SKILL.md"
    )



def test_the_two_skills_layers_are_pinned_by_what_they_resolve_to(tmp_path):
    """Condition 6 / trap 4: `.claude/skills` and the root `skills/` are the same word at two
    paths. The flat one is linked in neither mode; the root one is the producer's alone, mirrored
    from the host's root. Linking the wrong one fails exactly this test. The host is given a flat
    folder holding something, so a flat link in either mode would have something to show."""
    host = _make_host(tmp_path)
    _add_root_skills_layer(host)
    stray = host / ".claude" / "skills" / "stray"
    stray.mkdir(parents=True)
    (stray / "SKILL.md").write_text("flat\n")
    consumer = tmp_path / "kensaiapp-consumer"
    consumer.mkdir()
    producer = tmp_path / "kensaiapp-producer"
    producer.mkdir()
    link_satellite.link_satellite(consumer, host, skills_mode="consumer")
    link_satellite.link_satellite(producer, host, skills_mode="producer")

    assert not os.path.lexists(consumer / ".claude" / "skills")
    assert not os.path.lexists(producer / ".claude" / "skills")
    grouped = Path("g") / ".claude" / "skills" / "x" / "SKILL.md"
    assert os.readlink(producer / "skills" / grouped) == str(host / "skills" / grouped)

def test_root_skills_evals_workspace_is_never_mirrored_at_depth(pair):
    """Condition 4: `SKIP_UNDER` still holds one level up, inside the new root."""
    sat, host = pair
    grouped = host / "skills" / "g" / ".claude" / "skills" / "x"
    (grouped / "evals" / "workspace" / "iteration-1").mkdir(parents=True)
    (grouped / "evals" / "workspace" / "iteration-1" / "benchmark.json").write_text("{}\n")
    (grouped / "evals" / "evals.json").write_text("{}\n")

    link_satellite.link_satellite(sat, host, skills_mode="producer")

    sat_grouped = sat / "skills" / "g" / ".claude" / "skills" / "x"
    assert not (sat_grouped / "evals" / "workspace").exists()
    assert (sat_grouped / "evals" / "evals.json").is_symlink()


def test_a_write_into_root_skills_producer_evals_path_stays_local(pair):
    """A write into the new layer's eval workspace stays in the satellite — the new layer's
    mirror of `test_producer_skills_directories_are_real_so_artifacts_stay_local`. This host's
    evals/ deliberately holds no `workspace` yet, unlike the fixture above."""
    sat, host = pair
    grouped = host / "skills" / "g" / ".claude" / "skills" / "x"
    (grouped / "evals").mkdir(parents=True)
    (grouped / "evals" / "evals.json").write_text("{}\n")

    link_satellite.link_satellite(sat, host, skills_mode="producer")

    sat_evals = sat / "skills" / "g" / ".claude" / "skills" / "x" / "evals"
    assert sat_evals.is_dir() and not sat_evals.is_symlink(), "the link must have created this"
    (sat_evals / "workspace" / "iteration-1").mkdir(parents=True)
    (sat_evals / "workspace" / "iteration-1" / "round.json").write_text("{}\n")

    assert not (grouped / "evals" / "workspace").exists()


def test_root_skills_producer_creates_no_copies(pair):
    """Condition 5 / trap 3, producer side: every non-directory entry under the new root is a
    symlink, every directory is real — walking it proves it, because in producer mode every real
    entry belongs to the satellite."""
    sat, host = pair
    _add_root_skills_layer(host)
    link_satellite.link_satellite(sat, host, skills_mode="producer")

    root = sat / "skills"
    assert root.is_dir() and not root.is_symlink(), "the link must have created this"
    walked_any = False
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        walked_any = True
        for name in filenames:
            p = Path(dirpath) / name
            assert p.is_symlink(), f"{p} is a real file, not a symlink"
        for name in dirnames:
            p = Path(dirpath) / name
            assert p.is_dir() and not p.is_symlink(), f"{p} should be a real directory"
    assert walked_any, "the mirrored tree must have real content to walk"



def test_root_skills_absent_source_agrees_across_modes(tmp_path):
    """An absent host `skills/`: neither mode leaves anything in the satellite. Only the producer,
    which would have linked the layer, reports the skip."""
    host = _make_host(tmp_path, grouped=False)
    sat_consumer = tmp_path / "kensaiapp-consumer"
    sat_consumer.mkdir()
    sat_producer = tmp_path / "kensaiapp-producer"
    sat_producer.mkdir()

    consumer_report = link_satellite.link_satellite(sat_consumer, host, skills_mode="consumer")
    producer_report = link_satellite.link_satellite(sat_producer, host, skills_mode="producer")

    assert not os.path.lexists(sat_consumer / "skills")
    assert not os.path.lexists(sat_producer / "skills")
    assert not consumer_report.skipped and bool(producer_report.skipped)


def test_root_skills_absent_source_exits_zero_via_main_both_modes(tmp_path, capsys):
    """This is the mechanism condition 2 rides on: a satellite must still be spawnable when the
    host has not created its root `skills/` yet. Tied to the report actually naming the skip
    (A2), not just to the exit code, so this fails before the report category exists."""
    host = _make_host(tmp_path)
    for mode in ("consumer", "producer"):
        sat = tmp_path / f"kensaiapp-{mode}"
        sat.mkdir()
        argv = ["--satellite", str(sat), "--host", str(host), "--skills-mode", mode]
        assert link_satellite.main(argv) == 0
        out = capsys.readouterr().out
        if mode == "producer":
            assert "skip" in out.lower(), "the absent root skills/ must be named in the report"


def test_root_skills_absent_source_check_claims_no_drift_both_modes(tmp_path):
    """Isolated to the new layer's own drift: the satellite is first brought level for real (the
    three `.claude/` layers settle to `already`), so the only thing left for `--check` to see is
    the absent root `skills/` — which must not itself count as drift. Tied to `report.skipped`
    directly, not just the exit code, since a run with no root-skills handling at all would also
    exit 0 here and prove nothing."""
    host = _make_host(tmp_path, grouped=False)
    for mode in ("producer",):
        sat = tmp_path / f"kensaiapp-{mode}-check"
        sat.mkdir()
        link_satellite.link_satellite(sat, host, skills_mode=mode)  # settle everything else
        report = link_satellite.link_satellite(sat, host, skills_mode=mode, check=True)
        assert report.skipped, "the absent root skills/ must show up in the check report too"
        assert not report.would_change
        assert not report.needs_attention
        assert not os.path.lexists(sat / "skills")


def test_root_skills_absent_source_skip_is_reported_and_does_not_flip_the_exit_code(tmp_path):
    """A2: an absent host `skills/` is reported, not silent — the report entry names the layer
    and the host path it looked for — but it must not feed `would_change` or `needs_attention`,
    or the absent-source exit-0 behaviours above would break. Isolated the same way as the test
    above: two real runs settle every other layer, so the third run's (and the `--check` run's)
    report carries only the skip. Reported identically under `--check` and a real run
    (condition 3)."""
    host = _make_host(tmp_path, grouped=False)
    sat = _make_satellite(tmp_path)
    link_satellite.link_satellite(sat, host, skills_mode="producer")  # settles the .claude layers
    real_report = link_satellite.link_satellite(sat, host, skills_mode="producer")  # idempotent

    assert real_report.skipped, "the skip must be reported, not silent"
    assert any(str(host / "skills") in entry for entry in real_report.skipped)
    assert not real_report.would_change
    assert not real_report.needs_attention

    check_report = link_satellite.link_satellite(sat, host, skills_mode="producer", check=True)
    assert check_report.skipped == real_report.skipped
    assert not check_report.would_change
    assert not check_report.needs_attention

    real_skip_lines = [
        line for line in real_report.render(check=False).splitlines() if "skip" in line.lower()
    ]
    check_skip_lines = [
        line for line in check_report.render(check=True).splitlines() if "skip" in line.lower()
    ]
    assert real_skip_lines == check_skip_lines


# --------------------------------------------------------------------------------------------
# The dangling walk over the new layer (condition 3)
# --------------------------------------------------------------------------------------------


def test_root_skills_producer_host_side_deletion_is_reported_dangling(pair):
    """Producer: a host-side deletion under the new layer surfaces as a reported dangling link,
    still on disk — condition 3, and condition 8's reported-never-removed property one level up."""
    sat, host = pair
    _add_root_skills_layer(host)
    link_satellite.link_satellite(sat, host, skills_mode="producer")
    (host / "skills" / "g" / ".claude" / "skills" / "x" / "SKILL.md").unlink()

    report = link_satellite.link_satellite(sat, host, skills_mode="producer")
    stale = sat / "skills" / "g" / ".claude" / "skills" / "x" / "SKILL.md"
    assert stale.is_symlink(), "the link must still be there — reported, not removed"
    assert any(str(stale) == p for p in report.dangling)


def test_root_skills_dangling_report_is_the_same_under_check(pair):
    sat, host = pair
    _add_root_skills_layer(host)
    link_satellite.link_satellite(sat, host, skills_mode="producer")
    (host / "skills" / "g" / ".claude" / "skills" / "x" / "SKILL.md").unlink()
    link_satellite.link_satellite(sat, host, skills_mode="producer")  # settle the dangling link

    before = sorted((sat / "skills").rglob("*"))
    report = link_satellite.link_satellite(sat, host, skills_mode="producer", check=True)
    after = sorted((sat / "skills").rglob("*"))

    stale = sat / "skills" / "g" / ".claude" / "skills" / "x" / "SKILL.md"
    assert any(str(stale) == p for p in report.dangling)
    assert before == after, "--check changes nothing"




def test_a_dangling_link_in_the_root_layer_is_counted_once(pair):
    """`_link_one` reports it while mirroring, and the dangling walk over the same layer meets it
    again — the walk's own dedup keeps it to one line."""
    sat, host = pair
    link_satellite.link_satellite(sat, host, skills_mode="producer")
    (host / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "SKILL.md").unlink()

    report = link_satellite.link_satellite(sat, host, skills_mode="producer")
    stale = sat / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "SKILL.md"
    assert report.dangling.count(str(stale)) == 1



def test_a_consumers_old_claude_skills_link_is_reported_dangling_once_the_flat_folder_is_gone(pair):
    """Every consumer carried a `.claude/skills` link into the host's flat folder before every host
    skill was grouped. The linker no longer makes one and never removes one — removing it is a
    commit in the satellite. Once the host's flat folder is gone the link dangles, and the
    `.claude/` walk reports it: that report is the cue the docstring promises."""
    sat, host = pair
    flat = host / ".claude" / "skills"
    flat.mkdir()
    (sat / ".claude").mkdir()
    (sat / ".claude" / "skills").symlink_to(flat)

    resolving = link_satellite.link_satellite(sat, host, skills_mode="consumer")
    assert not resolving.dangling, "while the flat folder exists the link resolves"

    flat.rmdir()
    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    link = sat / ".claude" / "skills"
    assert link.is_symlink(), "reported, never removed"
    assert report.dangling == [str(link)]
    assert report.needs_attention


def test_a_producers_old_flat_mirror_is_reported_dangling_and_never_extended(pair):
    """A producer linked before every host skill was grouped holds `.claude/skills` as a real tree
    of file links into the host's flat folder, beside its own eval output. Once those host files
    are gone, each link is reported dangling, the producer's own files are untouched, and nothing
    new is linked under `.claude/skills` — the grouped skills arrive under the root `skills/`."""
    sat, host = pair
    old = sat / ".claude" / "skills" / "product-prd"
    old.mkdir(parents=True)
    (old / "SKILL.md").symlink_to(host / ".claude" / "skills" / "product-prd" / "SKILL.md")
    (old / "evidence").mkdir()
    (old / "evidence" / "round-1.md").write_text("kept\n")

    report = link_satellite.link_satellite(sat, host, skills_mode="producer")

    assert report.dangling.count(str(old / "SKILL.md")) == 1
    assert (old / "SKILL.md").is_symlink(), "reported, never removed"
    assert (old / "evidence" / "round-1.md").read_text() == "kept\n"
    flat_root = str(sat / ".claude" / "skills")
    assert not any(p.startswith(flat_root) for p in report.created)
    assert (sat / "skills" / "pm" / ".claude" / "skills" / "product-prd" / "SKILL.md").is_symlink()

def test_root_skills_absent_source_dangling_walk_is_safe_both_modes_and_under_check(tmp_path):
    """The second `_report_dangling_below` call must be safe on a layer that does not exist —
    `_report_dangling_below`'s own early return, not a guard this task adds. One satellite per
    combination — switching `--skills-mode` on the same satellite is its own kind of drift and
    is not what this behaviour is about."""
    host = _make_host(tmp_path)
    for mode, check in (("consumer", False), ("producer", False), ("consumer", True)):
        sat = tmp_path / f"kensaiapp-{mode}-{check}"
        sat.mkdir()
        report = link_satellite.link_satellite(sat, host, skills_mode=mode, check=check)
        assert not report.dangling
        assert not report.needs_attention


# --------------------------------------------------------------------------------------------
# Condition 3, with the source present, and condition 2's real gate — added by the integrity pass
# --------------------------------------------------------------------------------------------


def test_root_skills_producer_check_reports_what_the_real_run_does_and_writes_nothing(pair):
    """Condition 3 with the source PRESENT: `--check` is the gate the second station runs against
    live satellites, so what it says about the new layer must be exactly what a real run does.
    Read off one satellite so the two reports are directly comparable — which only works because
    the `--check` pass leaves the tree untouched, and that is half of what is being asserted."""
    sat, host = pair
    _add_root_skills_layer(host)

    dry = link_satellite.link_satellite(sat, host, skills_mode="producer", check=True)
    assert not os.path.lexists(sat / "skills"), "--check must not create the new layer"

    wet = link_satellite.link_satellite(sat, host, skills_mode="producer")

    assert str(sat / "skills" / "g" / ".claude" / "skills" / "x" / "SKILL.md") in wet.created
    assert dry.created == wet.created
    assert dry.dangling == wet.dangling == []
    assert dry.conflicts == wet.conflicts == []
    assert dry.skipped == wet.skipped == []



def test_root_skills_absent_source_check_exits_zero_through_main_both_modes(tmp_path, capsys):
    """Condition 2's gate as `spawn_satellite.py` actually runs it: step 7 invokes
    `link_satellite.py --check` as a subprocess and raises on anything but 0, so the code `main`
    returns — not `would_change` on an in-process report — is what decides whether a satellite can
    be spawned against a host that has not created its root `skills/` yet. Tied to the skip
    appearing in the rendered output too, or a script that knew nothing of the layer would pass
    this as well."""
    host = _make_host(tmp_path, grouped=False)
    for mode in ("producer",):
        sat = tmp_path / f"kensaiapp-{mode}-main-check"
        sat.mkdir()
        argv = ["--satellite", str(sat), "--host", str(host), "--skills-mode", mode]
        assert link_satellite.main(argv) == 0  # settle every other layer for real
        capsys.readouterr()

        assert link_satellite.main(argv + ["--check"]) == 0
        out = capsys.readouterr().out
        assert "skip" in out.lower(), "--check must name the layer it skipped, as a real run does"
        assert str(host / "skills") in out
        assert not os.path.lexists(sat / "skills")


# --------------------------------------------------------------------------------------------
# The written settings.json, and the links an earlier version made (CP-459 to CP-466)
# --------------------------------------------------------------------------------------------


def _level(sat: Path, host: Path, mode: str = "consumer") -> None:
    link_satellite.link_satellite(sat, host, skills_mode=mode)


@pytest.mark.parametrize("name", ["hooks", "workflows"])
def test_a_hooks_or_workflows_link_into_the_host_is_removed(pair, name):
    sat, host = pair
    link = sat / ".claude" / name
    link.parent.mkdir(parents=True)
    link.symlink_to(host / ".claude" / name)

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert not os.path.lexists(link)
    assert report.removed == [str(link)]
    assert str(link) not in report.conflicts


def test_a_relative_link_into_the_host_is_removed_too(pair):
    """"Points into the host" is decided on the link's text made absolute against its own
    directory, so a relative text is read the same as an absolute one."""
    sat, host = pair
    link = sat / ".claude" / "workflows"
    link.parent.mkdir(parents=True)
    link.symlink_to(os.path.relpath(host / ".claude" / "workflows", start=link.parent))

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert not os.path.lexists(link)
    assert report.removed == [str(link)]


def test_a_settings_link_into_the_host_is_replaced_by_the_written_file(pair):
    sat, host = pair
    _wire_hooks(host)
    link = sat / ".claude" / "settings.json"
    link.parent.mkdir(parents=True)
    link.symlink_to(host / ".claude" / "settings.json")

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert link.is_file() and not link.is_symlink()
    assert link.read_text() == _expected_settings(host)
    assert (host / ".claude" / "settings.json").read_text() != link.read_text(), (
        "the host's own file is untouched"
    )
    assert report.written == [str(link)]


@pytest.mark.parametrize("name", ["hooks", "workflows", "settings.json"])
def test_a_dangling_link_into_the_host_is_still_removed(pair, name):
    """The target text lies under the host and the target is gone."""
    sat, host = pair
    link = sat / ".claude" / name
    link.parent.mkdir(parents=True)
    link.symlink_to(host / ".claude" / "gone" / name)

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    if name == "settings.json":
        assert link.is_file() and not link.is_symlink()
    else:
        assert not os.path.lexists(link)
        assert report.removed == [str(link)]
    assert report.dangling == []


@pytest.mark.parametrize("name", ["hooks", "workflows"])
def test_a_real_directory_is_a_conflict_and_left_alone(pair, name, capsys):
    sat, host = pair
    own = sat / ".claude" / name
    own.mkdir(parents=True)
    (own / "mine.py").write_text("# mine\n")

    code = link_satellite.main(_argv(sat, host))

    assert code == 1
    assert own.is_dir() and not own.is_symlink()
    assert sorted(p.name for p in own.iterdir()) == ["mine.py"]
    assert (own / "mine.py").read_text() == "# mine\n"
    assert f"[conflict] {own}" in capsys.readouterr().out


def test_a_real_hooks_file_is_a_conflict_and_left_alone(pair):
    sat, host = pair
    own = sat / ".claude" / "hooks"
    own.parent.mkdir(parents=True)
    own.write_text("MINE\n")

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert own.read_text() == "MINE\n"
    assert report.conflicts == [str(own)]


@pytest.mark.parametrize("name", ["hooks", "workflows", "settings.json"])
def test_a_link_outside_the_host_is_a_conflict_and_left_alone(pair, name):
    sat, host = pair
    elsewhere = host.parent / "elsewhere" / name
    elsewhere.parent.mkdir(parents=True)
    elsewhere.mkdir() if name != "settings.json" else elsewhere.write_text("{}\n")
    link = sat / ".claude" / name
    link.parent.mkdir(parents=True)
    link.symlink_to(elsewhere)

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert str(link) in report.conflicts
    assert os.readlink(link) == str(elsewhere)
    assert report.removed == []
    assert link not in [Path(p) for p in report.written]


def test_a_link_through_an_alias_of_the_host_is_removed(pair):
    """Spec Gap 5 — "points into the host" holds when the link's text names another path to the
    host but its real path lies under the host root."""
    sat, host = pair
    alias = host.parent / "host-alias"
    alias.symlink_to(host)
    link = sat / ".claude" / "hooks"
    link.parent.mkdir(parents=True)
    link.symlink_to(alias / ".claude" / "hooks")

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert not os.path.lexists(link)
    assert report.removed == [str(link)]
    assert report.conflicts == []


def test_a_link_into_a_sibling_sharing_the_hosts_name_prefix_is_a_conflict(pair):
    """Spec Gap 5 — "under the host root" is containment, not a shared string prefix: a sibling
    whose name begins with the host's is outside the host, so its link is left alone."""
    sat, host = pair
    sibling_hooks = host.parent / (host.name + "-other") / ".claude" / "hooks"
    sibling_hooks.mkdir(parents=True)
    link = sat / ".claude" / "hooks"
    link.parent.mkdir(parents=True)
    link.symlink_to(sibling_hooks)

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert link.is_symlink() and os.readlink(link) == str(sibling_hooks)
    assert report.conflicts == [str(link)]
    assert report.removed == []


def test_another_project_dir_reference_in_a_hook_command_is_kept(pair):
    """CP-459 — only the live hooks prefix is rewritten; every other `${CLAUDE_PROJECT_DIR}` in a
    command still names the session's own project, the satellite."""
    sat, host = pair
    command = (
        f'python3 "{LIVE_PREFIX}guard.py" --root "${{CLAUDE_PROJECT_DIR}}" '
        '--log "${CLAUDE_PROJECT_DIR}/system/log"'
    )
    (host / ".claude" / "settings.json").write_text(
        json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": command}]}]}})
    )

    _level(sat, host)

    written = json.loads((sat / ".claude" / "settings.json").read_text())
    assert written["hooks"]["Stop"][0]["hooks"][0]["command"] == (
        f'python3 "{host / ".claude" / "hooks"}/guard.py" --root "${{CLAUDE_PROJECT_DIR}}" '
        '--log "${CLAUDE_PROJECT_DIR}/system/log"'
    )


def test_a_differing_settings_file_is_rewritten(pair):
    sat, host = pair
    _wire_hooks(host)
    own = sat / ".claude" / "settings.json"
    own.parent.mkdir(parents=True)
    own.write_text('{"permissions": {"defaultMode": "plan"}}\n')

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert own.read_text() == _expected_settings(host)
    assert report.written == [str(own)]
    assert report.conflicts == []


def test_a_matching_settings_file_is_already_correct(pair):
    sat, host = pair
    _wire_hooks(host)
    _level(sat, host)
    written = sat / ".claude" / "settings.json"
    os.utime(written, ns=(1_000_000_000, 1_000_000_000))
    before = written.stat().st_mtime_ns

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert written.stat().st_mtime_ns == before, "an already-correct file is not rewritten"
    assert report.written == []
    assert str(written) in report.already


def test_the_settings_write_leaves_no_staging_file_behind(pair):
    sat, host = pair
    _level(sat, host)
    (sat / ".claude" / "settings.json").write_text("stale\n")

    _level(sat, host)

    assert sorted(p.name for p in (sat / ".claude").iterdir()) == ["settings.json"]


def test_check_writes_and_removes_nothing(pair):
    sat, host = pair
    _wire_hooks(host)
    claude = sat / ".claude"
    claude.mkdir(parents=True)
    (claude / "hooks").symlink_to(host / ".claude" / "hooks")
    (claude / "workflows").symlink_to(host / ".claude" / "workflows")
    (claude / "settings.json").write_text("stale\n")

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer", check=True)

    assert (claude / "hooks").is_symlink() and (claude / "workflows").is_symlink()
    assert (claude / "settings.json").read_text() == "stale\n"
    assert report.written == [str(claude / "settings.json")]
    assert sorted(report.removed) == sorted([str(claude / "hooks"), str(claude / "workflows")])


def test_check_leaves_a_settings_link_into_the_host_in_place(pair):
    """CP-463 — `--check` changes nothing, so a `settings.json` link into the host is reported
    as a write and stays a link."""
    sat, host = pair
    _wire_hooks(host)
    link = sat / ".claude" / "settings.json"
    link.parent.mkdir(parents=True)
    link.symlink_to(host / ".claude" / "settings.json")

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer", check=True)

    assert link.is_symlink() and os.readlink(link) == str(host / ".claude" / "settings.json")
    assert report.written == [str(link)]


def test_check_leaves_an_absent_settings_file_absent(pair):
    sat, host = pair

    report = link_satellite.link_satellite(sat, host, skills_mode="consumer", check=True)

    assert not os.path.lexists(sat / ".claude")
    assert report.written == [str(sat / ".claude" / "settings.json")]


def _drift_absent(sat: Path, host: Path) -> None:
    (sat / ".claude" / "settings.json").unlink()


def _drift_settings_link(sat: Path, host: Path) -> None:
    (sat / ".claude" / "settings.json").unlink()
    (sat / ".claude" / "settings.json").symlink_to(host / ".claude" / "settings.json")


def _drift_differing(sat: Path, host: Path) -> None:
    (sat / ".claude" / "settings.json").write_text("stale\n")


def _drift_hooks_link(sat: Path, host: Path) -> None:
    (sat / ".claude" / "hooks").symlink_to(host / ".claude" / "hooks")


def _drift_workflows_link(sat: Path, host: Path) -> None:
    (sat / ".claude" / "workflows").symlink_to(host / ".claude" / "workflows")


@pytest.mark.parametrize(
    "drift",
    [
        _drift_absent,
        _drift_settings_link,
        _drift_differing,
        _drift_hooks_link,
        _drift_workflows_link,
    ],
    ids=lambda fn: fn.__name__.removeprefix("_drift_"),
)
def test_check_exits_one_on_each_drift_kind_and_zero_when_level(pair, drift, capsys):
    sat, host = pair
    _wire_hooks(host)
    _level(sat, host)
    assert link_satellite.main(_argv(sat, host, "--check")) == 0

    drift(sat, host)
    assert link_satellite.main(_argv(sat, host, "--check")) == 1
    capsys.readouterr()

    assert link_satellite.main(_argv(sat, host)) == 0
    assert link_satellite.main(_argv(sat, host, "--check")) == 0


def test_a_hook_wired_in_the_host_after_linking_is_drift_until_rerun(pair):
    sat, host = pair
    _wire_hooks(host)
    _level(sat, host)
    document = json.loads((host / ".claude" / "settings.json").read_text())
    document["hooks"]["Stop"] = [{"hooks": [_hook_entry("later.py")]}]
    (host / ".claude" / "settings.json").write_text(json.dumps(document, indent=2) + "\n")

    assert link_satellite.main(_argv(sat, host, "--check")) == 1
    assert link_satellite.main(_argv(sat, host)) == 0
    assert link_satellite.main(_argv(sat, host, "--check")) == 0
    assert "later.py" in (sat / ".claude" / "settings.json").read_text()


def test_an_edit_to_a_hook_script_is_not_drift(pair):
    """The written commands name the host's scripts, so a script edit needs no re-run."""
    sat, host = pair
    _wire_hooks(host)
    _level(sat, host)
    (host / ".claude" / "hooks" / "resolve_core.py").write_text("# edited\n")

    assert link_satellite.main(_argv(sat, host, "--check")) == 0


def _repoint_scenario(pair) -> tuple[Path, Path]:
    """A producer with one wrong-form skill link, an absent settings file and a workflows link
    into the host: one line of each kind the report counts."""
    sat, host = pair
    _wire_hooks(host)
    link_satellite.link_satellite(sat, host, skills_mode="producer")
    _relink_relative(_skill_file(sat), _skill_file(host))
    (sat / ".claude" / "settings.json").unlink()
    (sat / ".claude" / "workflows").symlink_to(host / ".claude" / "workflows")
    return sat, host


def test_the_report_counts_and_lists_writes_and_removals_under_check(pair):
    sat, host = _repoint_scenario(pair)
    report = link_satellite.link_satellite(sat, host, skills_mode="producer", check=True)

    lines = report.render(check=True).splitlines()

    repoint = lines.index("would repoint (relative -> absolute): 1")
    assert lines[repoint + 1] == "would write settings.json: 1"
    assert lines[repoint + 2] == "would remove (no longer linked): 1"
    assert lines[repoint + 3].startswith("already correct: ")
    write_path = f"  [would write] {sat / '.claude' / 'settings.json'}"
    remove_path = f"  [would remove] {sat / '.claude' / 'workflows'}"
    repoint_path = next(i for i, line in enumerate(lines) if line.startswith("  [would repoint]"))
    assert lines.index(write_path) == repoint_path + 1
    assert lines.index(remove_path) == repoint_path + 2


def test_the_report_counts_and_lists_writes_and_removals_without_check(pair):
    sat, host = _repoint_scenario(pair)
    report = link_satellite.link_satellite(sat, host, skills_mode="producer")

    lines = report.render(check=False).splitlines()

    repoint = lines.index("repointed (relative -> absolute): 1")
    assert lines[repoint + 1] == "wrote settings.json: 1"
    assert lines[repoint + 2] == "removed (no longer linked): 1"
    assert f"  [wrote] {sat / '.claude' / 'settings.json'}" in lines
    assert f"  [removed] {sat / '.claude' / 'workflows'}" in lines


def test_the_write_path_line_comes_before_the_skipped_lines(tmp_path):
    host = _make_host(tmp_path, grouped=False)
    sat = _make_satellite(tmp_path)

    lines = link_satellite.link_satellite(
        sat, host, skills_mode="producer", check=True
    ).render(check=True).splitlines()

    write = lines.index(f"  [would write] {sat / '.claude' / 'settings.json'}")
    skipped = next(i for i, line in enumerate(lines) if line.startswith("  [skipped]"))
    assert write < skipped


def test_the_zero_counts_are_printed(pair):
    sat, host = pair
    _level(sat, host)

    out = link_satellite.link_satellite(sat, host, skills_mode="consumer").render(check=False)

    assert "wrote settings.json: 0" in out
    assert "removed (no longer linked): 0" in out
    assert "[wrote]" not in out and "[removed]" not in out


CONFLICT_NOTE = (
    "A conflict means the satellite holds its own real file where the host's would be linked. "
    "At .claude/hooks, .claude/workflows and .claude/settings.json nothing is linked any more. "
    "A conflict at one of them is a real file or directory at .claude/hooks or "
    ".claude/workflows, or a link at any of the three that points outside the host. That is "
    "legitimate for per-instance data; it is drift for shared content. Decide per path — this "
    "script will not overwrite either way."
)


def test_the_conflict_note_names_the_three_paths_that_are_no_longer_links(pair):
    sat, host = pair
    own = sat / ".claude" / "hooks"
    own.mkdir(parents=True)

    out = link_satellite.link_satellite(sat, host, skills_mode="consumer").render(check=False)

    assert "\n\n" + CONFLICT_NOTE in out
    assert out.endswith(CONFLICT_NOTE)


def test_a_host_without_settings_json_exits_two_naming_the_path(pair, capsys):
    sat, host = pair
    (host / ".claude" / "settings.json").unlink()

    code = link_satellite.main(_argv(sat, host))

    assert code == 2
    err = capsys.readouterr().err
    missing = host.resolve() / ".claude" / "settings.json"
    assert err.strip() == f"error: host has no .claude/settings.json: {missing}"
    assert not os.path.lexists(sat / ".claude"), "nothing is written"


def test_a_host_without_settings_json_is_also_refused_under_check(pair, capsys):
    sat, host = pair
    (host / ".claude" / "settings.json").unlink()

    assert link_satellite.main(_argv(sat, host, "--check")) == 2
    assert "error: host has no .claude/settings.json:" in capsys.readouterr().err


def test_the_function_refuses_a_host_without_settings_json_too(pair):
    """`spawn_satellite.py` and `check_satellites.py` call the function, not `main`."""
    sat, host = pair
    (host / ".claude" / "settings.json").unlink()

    with pytest.raises(SystemExit) as refused:
        link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert f"error: host has no .claude/settings.json: {host / '.claude' / 'settings.json'}" in str(
        refused.value
    )


def test_a_host_without_a_claude_layer_exits_two_through_main(tmp_path, capsys):
    """The exit-code line already said 2 for this; the code returned 1."""
    sat = _make_satellite(tmp_path)
    bare = tmp_path / "not-an-instance"
    bare.mkdir()

    assert link_satellite.main(_argv(sat, bare)) == 2
    assert "error: host has no .claude/ layer:" in capsys.readouterr().err


def test_the_satellite_resolves_core_from_its_own_env(pair):
    """CP-466: the written `SessionStart` command runs the host's `resolve_core.py` with
    `CLAUDE_PROJECT_DIR` set to the satellite, and it reports the `CORE=` of the satellite's own
    `.env` — not the host's `core/`."""
    sat, host = pair
    shutil.copy2(RESOLVE_CORE_SOURCE, host / ".claude" / "hooks" / "resolve_core.py")
    (host / "core").mkdir()
    document = {
        "hooks": {"SessionStart": [{"hooks": [_hook_entry("resolve_core.py")]}]},
    }
    (host / ".claude" / "settings.json").write_text(json.dumps(document, indent=2) + "\n")
    satellite_core = host.parent / "the-satellites-own-core"
    (sat / ".env").write_text(f"CORE={satellite_core}\n")
    _level(sat, host)
    written = json.loads((sat / ".claude" / "settings.json").read_text())
    command = written["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(sat)}
    env.pop("CLAUDE_ENV_FILE", None)

    done = subprocess.run(
        command,
        shell=True,
        input='{"hook_event_name": "SessionStart"}',
        env=env,
        capture_output=True,
        text=True,
        cwd=sat,
    )

    assert done.returncode == 0, done.stderr
    context = json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]
    assert f"`<CORE>` = `{satellite_core}`" in context
    assert str(host / "core") not in context


def test_a_host_settings_file_that_is_not_json_is_refused_naming_the_path(pair):
    sat, host = pair
    (host / ".claude" / "settings.json").write_text("{not json")

    with pytest.raises(SystemExit) as refused:
        link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert "is not valid JSON" in str(refused.value)
    assert str(host / ".claude" / "settings.json") in str(refused.value)
    assert not os.path.lexists(sat / ".claude" / "settings.json")


def test_a_host_settings_file_that_is_not_an_object_is_refused(pair):
    sat, host = pair
    (host / ".claude" / "settings.json").write_text("[]\n")

    with pytest.raises(SystemExit) as refused:
        link_satellite.link_satellite(sat, host, skills_mode="consumer")

    assert "is not a JSON object" in str(refused.value)
