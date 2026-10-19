"""Contract tests for `pin.py` — making and finding a pin (Task 1).

Isolation: every test builds its own throwaway host under `tmp_path` and makes pins into a
sibling `tmp_path` directory, so nothing here touches the real `~/.kensaiapp/pins/`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import pin

_PIN_PY = Path(__file__).parent / "pin.py"


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True)


def _init_git_host(root: Path) -> Path:
    """A throwaway host that is a real git work tree, with tracked, edited, untracked and
    ignored files across the three trees plus a `system/` file that belongs to none of them."""
    root.mkdir()
    _git("init", "-q", cwd=root)
    _git("config", "user.email", "host@example.com", cwd=root)
    _git("config", "user.name", "Host", cwd=root)

    (root / "core" / "tools").mkdir(parents=True)
    (root / "core" / "tools" / "tool.py").write_text("print('tracked')\n")
    (root / ".claude" / "skills" / "example").mkdir(parents=True)
    (root / ".claude" / "skills" / "example" / "SKILL.md").write_text("tracked skill\n")
    (root / "skills" / "grp" / ".claude" / "skills" / "g").mkdir(parents=True)
    (root / "skills" / "grp" / ".claude" / "skills" / "g" / "SKILL.md").write_text("grouped\n")
    (root / "system").mkdir()
    (root / "system" / "not_a_pin_tree.md").write_text("outside the three trees\n")
    (root / ".gitignore").write_text("core/ignored.log\n")

    _git("add", "-A", cwd=root)
    _git("commit", "-q", "-m", "initial", cwd=root)

    # An uncommitted edit to an already-tracked file — arrives edited, not at its committed blob.
    (root / "core" / "tools" / "tool.py").write_text("print('tracked and edited')\n")

    # An untracked, not-ignored file — arrives.
    (root / "core" / "tools" / "untracked.py").write_text("print('untracked')\n")

    # A file `.gitignore` matches — never arrives.
    (root / "core" / "ignored.log").write_text("noise\n")

    return root


@pytest.fixture
def pins_home(tmp_path):
    home = tmp_path / "pins"
    home.mkdir()
    return home


class TestMake:
    def test_make_copies_the_three_trees_as_they_stand(self, tmp_path, pins_home):
        host = _init_git_host(tmp_path / "host")

        made = pin.make(host, pins_home)

        assert (
            made.root / "core" / "tools" / "tool.py"
        ).read_text() == "print('tracked and edited')\n"
        assert (
            made.root / "core" / "tools" / "untracked.py"
        ).read_text() == "print('untracked')\n"

    def test_make_leaves_out_ignored_files(self, tmp_path, pins_home):
        host = _init_git_host(tmp_path / "host")

        made = pin.make(host, pins_home)

        assert not (made.root / "core" / "ignored.log").exists()

    def test_make_copies_nothing_outside_core_claude_and_skills(self, tmp_path, pins_home):
        host = _init_git_host(tmp_path / "host")

        made = pin.make(host, pins_home)

        assert not (made.root / "system").exists()

    def test_make_keeps_the_executable_bit(self, tmp_path, pins_home):
        host = _init_git_host(tmp_path / "host")
        launcher_dir = host / "core" / "launchers" / "example"
        launcher_dir.mkdir(parents=True)
        launcher_sh = launcher_dir / "launcher.sh"
        launcher_sh.write_text("#!/usr/bin/env bash\necho hi\n")
        launcher_sh.chmod(0o755)
        _git("add", "-A", cwd=host)
        _git("commit", "-q", "-m", "add launcher", cwd=host)

        made = pin.make(host, pins_home)

        copied = made.root / "core" / "launchers" / "example" / "launcher.sh"
        assert os.access(copied, os.X_OK)

    def test_make_copies_a_non_git_host_whole(self, tmp_path, pins_home):
        host = tmp_path / "host"
        (host / "core" / "tools").mkdir(parents=True)
        (host / "core" / "tools" / "tool.py").write_text("print('whole')\n")
        (host / ".claude" / "skills" / "example").mkdir(parents=True)
        (host / ".claude" / "skills" / "example" / "SKILL.md").write_text("skill\n")

        made = pin.make(host, pins_home)

        assert (made.root / "core" / "tools" / "tool.py").read_text() == "print('whole')\n"
        assert (
            made.root / ".claude" / "skills" / "example" / "SKILL.md"
        ).read_text() == "skill\n"

    def test_make_writes_its_manifest_naming_the_source_host(self, tmp_path, pins_home):
        host = _init_git_host(tmp_path / "host")

        made = pin.make(host, pins_home)

        manifest = json.loads((made.root / "pin.json").read_text())
        assert manifest["source_host_root"] == str(host.resolve())
        assert manifest["id"] == made.id

    def test_two_makes_are_two_pins(self, tmp_path, pins_home):
        host = _init_git_host(tmp_path / "host")

        first = pin.make(host, pins_home)
        second = pin.make(host, pins_home)

        assert first.root != second.root

    def test_make_records_the_host_head_as_source_head(self, tmp_path, pins_home):
        host = _init_git_host(tmp_path / "host")
        head = subprocess.run(
            ["git", "-C", str(host), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

        made = pin.make(host, pins_home)

        assert made.source_head == head
        manifest = json.loads((made.root / "pin.json").read_text())
        assert manifest["source_head"] == head

    def test_make_omits_source_head_for_a_non_git_host(self, tmp_path, pins_home):
        host = tmp_path / "host"
        (host / "core" / "tools").mkdir(parents=True)
        (host / "core" / "tools" / "tool.py").write_text("print('whole')\n")

        made = pin.make(host, pins_home)

        assert made.source_head is None
        manifest = json.loads((made.root / "pin.json").read_text())
        assert "source_head" not in manifest


def _non_git_host(root: Path) -> Path:
    (root / "core" / "tools").mkdir(parents=True)
    (root / "core" / "tools" / "tool.py").write_text("print('whole')\n")
    (root / "core" / "ignored.log").write_text("no ignore rules apply\n")
    (root / ".claude" / "skills" / "example").mkdir(parents=True)
    (root / ".claude" / "skills" / "example" / "SKILL.md").write_text("skill\n")
    (root / "system").mkdir()
    (root / "system" / "outside.md").write_text("outside the three trees\n")
    return root


class TestHostFiles:
    @pytest.mark.parametrize("make_host", [_init_git_host, _non_git_host], ids=["git", "non-git"])
    def test_host_files_lists_exactly_what_make_copies(self, tmp_path, pins_home, make_host):
        host = make_host(tmp_path / "host")

        listed = set(pin.host_files(host))
        made = pin.make(host, pins_home)

        copied = {
            str(path.relative_to(made.root))
            for path in made.root.rglob("*")
            if path.is_file() and path != made.root / "pin.json"
        }
        assert listed == copied
        assert listed  # a vacuous equality of two empty sets proves nothing

    def test_host_files_on_a_git_host_holds_the_edited_and_untracked_and_leaves_out_the_rest(
        self, tmp_path
    ):
        host = _init_git_host(tmp_path / "host")

        listed = set(pin.host_files(host))

        assert "core/tools/tool.py" in listed  # edited, uncommitted
        assert "core/tools/untracked.py" in listed
        assert "core/ignored.log" not in listed
        assert not any(relpath.startswith("system/") for relpath in listed)

    def test_tree_files_lists_every_file_under_the_three_trees_ignored_ones_included(
        self, tmp_path
    ):
        host = _init_git_host(tmp_path / "host")

        walked = set(pin.tree_files(host))

        assert "core/ignored.log" in walked
        assert set(pin.host_files(host)) <= walked
        assert not any(relpath.startswith("system/") for relpath in walked)


class TestManifestGate:
    def test_a_pin_without_its_manifest_is_not_a_pin(self, tmp_path, pins_home):
        incomplete = pins_home / "incomplete"
        (incomplete / "core").mkdir(parents=True)

        assert pin.of_core(incomplete / "core") is None
        with pytest.raises(pin.PinMissing):
            pin.inherited({"KENSAIAPP_PIN": str(incomplete)})

    def test_of_core_finds_the_pin_a_core_belongs_to(self, tmp_path, pins_home):
        host = _init_git_host(tmp_path / "host")
        made = pin.make(host, pins_home)

        assert pin.of_core(made.root / "core") == made
        assert pin.of_core(host / "core") is None

    def test_of_core_reads_none_source_head_for_an_older_manifest(self, tmp_path, pins_home):
        # A pin written before `source_head` existed — `pin.json` carries no such key at all.
        # `of_core` must not choke on the missing key; it reads back `source_head=None`.
        root = pins_home / "old-pin"
        (root / "core").mkdir(parents=True)
        (root / "pin.json").write_text(json.dumps({
            "id": "old-pin",
            "source_host_root": str(tmp_path / "host"),
            "created": "2026-01-01T00:00:00+00:00",
        }))

        found = pin.of_core(root / "core")

        assert found is not None
        assert found.source_head is None

    def test_inherited_is_none_when_nothing_is_inherited(self):
        assert pin.inherited({}) is None

    def test_inherited_raises_when_the_named_pin_is_gone(self, tmp_path):
        with pytest.raises(pin.PinMissing):
            pin.inherited({"KENSAIAPP_PIN": str(tmp_path / "nowhere")})


class TestPinsHome:
    def test_pins_home_defaults_under_the_home_directory(self, tmp_path):
        home = pin.pins_home({"HOME": str(tmp_path)})

        assert home == tmp_path / ".kensaiapp" / "pins"
        assert home.is_dir()

    def test_pins_home_honours_its_override(self, tmp_path):
        override = tmp_path / "elsewhere"

        home = pin.pins_home({"HOME": str(tmp_path), "KENSAIAPP_PINS_HOME": str(override)})

        assert home == override
        assert home.is_dir()


def _init_ownership_host(root: Path) -> Path:
    """A throwaway host holding one flat skill, one grouped skill, one agent and one workflow —
    the names `owned_entries` and `agent_file` are exercised against."""
    root.mkdir()
    (root / "core").mkdir()
    (root / ".claude" / "skills" / "host-skill").mkdir(parents=True)
    (root / ".claude" / "skills" / "host-skill" / "SKILL.md").write_text("host skill\n")
    (root / ".claude" / "skills" / "shared-name").mkdir(parents=True)
    (root / ".claude" / "skills" / "shared-name" / "SKILL.md").write_text("host's shared-name\n")
    (root / ".claude" / "agents" / "host-agent.md").parent.mkdir(parents=True)
    (root / ".claude" / "agents" / "host-agent.md").write_text("host agent\n")
    (root / ".claude" / "workflows" / "host-workflow.js").parent.mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "workflows" / "host-workflow.js").write_text("host workflow\n")
    (root / "skills" / "grp" / ".claude" / "skills" / "grouped-skill").mkdir(parents=True)
    (root / "skills" / "grp" / ".claude" / "skills" / "grouped-skill" / "SKILL.md").write_text(
        "grouped\n"
    )
    return root


class TestOwnedEntries:
    def test_in_the_host_itself_every_entry_comes_from_the_pin(self, tmp_path, pins_home):
        host = _init_ownership_host(tmp_path / "host")
        made = pin.make(host, pins_home)

        skills = pin.owned_entries(made, host, pin.Kind.SKILLS)
        agents = pin.owned_entries(made, host, pin.Kind.AGENTS)
        workflows = pin.owned_entries(made, host, pin.Kind.WORKFLOWS)

        assert made.root in skills["host-skill"].parents
        assert made.root in agents["host-agent"].parents
        assert made.root in workflows["host-workflow"].parents

    def test_a_satellite_whose_claude_dirs_link_into_the_host_gets_the_pin(
        self, tmp_path, pins_home
    ):
        host = _init_ownership_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        sat = tmp_path / "sat"
        (sat / ".claude").mkdir(parents=True)
        (sat / ".claude" / "skills").symlink_to(host / ".claude" / "skills")

        skills = pin.owned_entries(made, sat, pin.Kind.SKILLS)

        assert made.root in skills["host-skill"].parents

    def test_an_instance_that_holds_its_own_skill_gets_its_own(self, tmp_path, pins_home):
        host = _init_ownership_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        sat = tmp_path / "sat"
        own_skill = sat / ".claude" / "skills" / "own-skill"
        own_skill.mkdir(parents=True)
        (own_skill / "SKILL.md").write_text("sat's own\n")

        skills = pin.owned_entries(made, sat, pin.Kind.SKILLS)

        assert skills["own-skill"] == own_skill

    def test_an_instance_owned_name_is_never_also_served_from_the_pin(self, tmp_path, pins_home):
        host = _init_ownership_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        sat = tmp_path / "sat"
        own_shared = sat / ".claude" / "skills" / "shared-name"
        own_shared.mkdir(parents=True)
        (own_shared / "SKILL.md").write_text("sat's own shared-name\n")

        skills = pin.owned_entries(made, sat, pin.Kind.SKILLS)

        assert skills["shared-name"] == own_shared
        assert len([name for name in skills if name == "shared-name"]) == 1

    def test_grouped_host_skills_are_owned_entries(self, tmp_path, pins_home):
        host = _init_ownership_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        sat = tmp_path / "sat"
        sat.mkdir()

        skills = pin.owned_entries(
            made, sat, pin.Kind.SKILLS, groups=pin.granted_groups(made, ["grouped-skill"])
        )

        assert made.root in skills["grouped-skill"].parents


def _write_skill(skill_dir: Path, depends_on: str | None = None) -> None:
    """A SKILL.md under `skill_dir`, with a `metadata:` map carrying `depends-on:` when given."""
    skill_dir.mkdir(parents=True)
    lines = [
        "---",
        f"name: {skill_dir.name}",
        "description: a skill",
        "metadata:",
        "  version: 1.0.0",
    ]
    if depends_on is not None:
        lines.append(f"  depends-on: {depends_on}")
    lines += ["---", "", "body"]
    (skill_dir / "SKILL.md").write_text("\n".join(lines) + "\n")


def _grouped_host(root: Path, groups: dict[str, dict[str, str | None]]) -> Path:
    """A host with one flat skill (`flat-skill`) and, per group, its skills mapped to the
    `depends-on:` value each carries (`None` for no line)."""
    root.mkdir()
    (root / "core").mkdir()
    _write_skill(root / ".claude" / "skills" / "flat-skill")
    (root / ".claude" / "agents").mkdir(parents=True)
    (root / ".claude" / "agents" / "some-agent.md").write_text("an agent\n")
    for group, skills in groups.items():
        for name, depends_on in skills.items():
            _write_skill(root / "skills" / group / ".claude" / "skills" / name, depends_on)
    return root


class TestGrantedGroups:
    def test_one_name_reaches_every_holding_group_and_each_dependency(self, tmp_path, pins_home):
        host = _grouped_host(
            tmp_path / "host",
            {
                "a": {"shared-skill": "dependency-a"},
                "b": {"shared-skill": "dependency-b"},
                "c": {"dependency-a": None},
                "d": {"dependency-b": None},
                "unrelated": {"other-skill": None},
            },
        )
        made = pin.make(host, pins_home)

        assert pin.granted_groups(made, ["shared-skill"]) == frozenset({"a", "b", "c", "d"})

    def test_a_granted_skill_reaches_its_own_group(self, tmp_path, pins_home):
        host = _grouped_host(
            tmp_path / "host", {"a": {"skill-in-a": None}, "b": {"skill-in-b": None}}
        )
        made = pin.make(host, pins_home)

        assert pin.granted_groups(made, ["skill-in-a"]) == frozenset({"a"})

    def test_depends_on_reaches_another_group(self, tmp_path, pins_home):
        host = _grouped_host(
            tmp_path / "host", {"a": {"skill-in-a": "skill-in-b"}, "b": {"skill-in-b": None}}
        )
        made = pin.make(host, pins_home)

        assert pin.granted_groups(made, ["skill-in-a"]) == frozenset({"a", "b"})

    def test_depends_on_is_followed_transitively(self, tmp_path, pins_home):
        host = _grouped_host(
            tmp_path / "host",
            {
                "a": {"skill-in-a": "skill-in-b"},
                "b": {"skill-in-b": "skill-in-c"},
                "c": {"skill-in-c": None},
            },
        )
        made = pin.make(host, pins_home)

        assert pin.granted_groups(made, ["skill-in-a"]) == frozenset({"a", "b", "c"})

    def test_a_depends_on_cycle_ends(self, tmp_path, pins_home):
        host = _grouped_host(
            tmp_path / "host",
            {"a": {"skill-in-a": "skill-in-b"}, "b": {"skill-in-b": "skill-in-a"}},
        )
        made = pin.make(host, pins_home)

        assert pin.granted_groups(made, ["skill-in-a"]) == frozenset({"a", "b"})

    def test_a_flat_an_agent_or_an_unknown_name_adds_no_group(self, tmp_path, pins_home):
        host = _grouped_host(
            tmp_path / "host",
            {"a": {"skill-in-a": "flat-skill, some-agent, no-such-skill"}},
        )
        made = pin.make(host, pins_home)

        assert pin.granted_groups(made, ["skill-in-a"]) == frozenset({"a"})

    def test_a_flat_skill_granted_reaches_no_group(self, tmp_path, pins_home):
        host = _grouped_host(tmp_path / "host", {"a": {"skill-in-a": None}})
        made = pin.make(host, pins_home)

        assert pin.granted_groups(made, ["flat-skill"]) == frozenset()

    def test_depends_on_with_several_names_reaches_each(self, tmp_path, pins_home):
        host = _grouped_host(
            tmp_path / "host",
            {
                "a": {"skill-in-a": "skill-in-b,  skill-in-c"},
                "b": {"skill-in-b": None},
                "c": {"skill-in-c": None},
            },
        )
        made = pin.make(host, pins_home)

        assert pin.granted_groups(made, ["skill-in-a"]) == frozenset({"a", "b", "c"})

    def test_a_depends_on_line_in_the_body_is_not_a_dependency(self, tmp_path, pins_home):
        host = _grouped_host(
            tmp_path / "host", {"a": {"skill-in-a": None}, "b": {"skill-in-b": None}}
        )
        skill_md = host / "skills" / "a" / ".claude" / "skills" / "skill-in-a" / "SKILL.md"
        skill_md.write_text(skill_md.read_text() + "  depends-on: skill-in-b\n")
        made = pin.make(host, pins_home)

        assert pin.granted_groups(made, ["skill-in-a"]) == frozenset({"a"})


class TestOwnedEntriesUnderAGrant:
    def test_no_groups_lists_flat_and_instance_skills_and_no_grouped_one(self, tmp_path, pins_home):
        host = _grouped_host(tmp_path / "host", {"a": {"skill-in-a": None}})
        made = pin.make(host, pins_home)
        sat = tmp_path / "sat"
        _write_skill(sat / ".claude" / "skills" / "own-skill")

        skills = pin.owned_entries(made, sat, pin.Kind.SKILLS)

        assert sorted(skills) == ["flat-skill", "own-skill"]

    def test_one_group_lists_only_that_groups_skills(self, tmp_path, pins_home):
        host = _grouped_host(
            tmp_path / "host",
            {"a": {"skill-in-a": None, "peer-in-a": None}, "b": {"skill-in-b": None}},
        )
        made = pin.make(host, pins_home)
        sat = tmp_path / "sat"
        sat.mkdir()

        skills = pin.owned_entries(made, sat, pin.Kind.SKILLS, groups=frozenset({"a"}))

        assert sorted(skills) == ["flat-skill", "peer-in-a", "skill-in-a"]

    def test_groups_filter_skills_only(self, tmp_path, pins_home):
        host = _grouped_host(tmp_path / "host", {"a": {"skill-in-a": None}})
        workflows = host / ".claude" / "workflows"
        workflows.mkdir()
        (workflows / "pinned-workflow.js").write_text("export const meta = {};\n")
        made = pin.make(host, pins_home)
        sat = tmp_path / "sat"
        own_workflows = sat / ".claude" / "workflows"
        own_workflows.mkdir(parents=True)
        (own_workflows / "own-workflow.js").write_text("export const meta = {};\n")

        for groups in (frozenset(), frozenset({"a"}), frozenset({"unknown"})):
            assert sorted(pin.owned_entries(made, sat, pin.Kind.AGENTS, groups)) == ["some-agent"]
            assert sorted(pin.owned_entries(made, sat, pin.Kind.WORKFLOWS, groups)) == [
                "own-workflow", "pinned-workflow",
            ]
        assert pin.agent_file(made, sat, "some-agent") is not None

    def test_instance_skill_still_wins_by_name_under_a_grant(self, tmp_path, pins_home):
        host = _grouped_host(tmp_path / "host", {"a": {"skill-in-a": None}})
        made = pin.make(host, pins_home)
        sat = tmp_path / "sat"
        own = sat / ".claude" / "skills" / "skill-in-a"
        _write_skill(own)

        skills = pin.owned_entries(made, sat, pin.Kind.SKILLS, groups=frozenset({"a"}))

        assert skills["skill-in-a"] == own


class TestAgentFile:
    def test_agent_file_is_the_pinned_one_for_a_host_agent(self, tmp_path, pins_home):
        host = _init_ownership_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        sat = tmp_path / "sat"
        sat.mkdir()

        found = pin.agent_file(made, sat, "host-agent")

        assert found == made.root / ".claude" / "agents" / "host-agent.md"

    def test_agent_file_is_the_instances_own_when_it_holds_one(self, tmp_path, pins_home):
        host = _init_ownership_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        sat = tmp_path / "sat"
        own_agent = sat / ".claude" / "agents" / "sat-agent.md"
        own_agent.parent.mkdir(parents=True)
        own_agent.write_text("sat's own agent\n")

        found = pin.agent_file(made, sat, "sat-agent")

        assert found == own_agent

    def test_agent_file_is_none_when_neither_holds_it(self, tmp_path, pins_home):
        host = _init_ownership_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        sat = tmp_path / "sat"
        sat.mkdir()

        assert pin.agent_file(made, sat, "nobody-has-this") is None

    def test_agent_file_with_no_pin_is_the_instances_own(self, tmp_path):
        sat = tmp_path / "sat"
        own_agent = sat / ".claude" / "agents" / "sat-agent.md"
        own_agent.parent.mkdir(parents=True)
        own_agent.write_text("sat's own agent\n")

        found = pin.agent_file(None, sat, "sat-agent")

        assert found == own_agent

    def test_agent_file_with_no_pin_is_none_when_the_instance_holds_none(self, tmp_path):
        sat = tmp_path / "sat"
        (sat / ".claude" / "agents").mkdir(parents=True)

        assert pin.agent_file(None, sat, "nobody-has-this") is None

    def test_agent_file_with_no_pin_is_none_without_an_agents_dir(self, tmp_path):
        sat = tmp_path / "sat"
        sat.mkdir()

        assert pin.agent_file(None, sat, "nobody-has-this") is None


def _write_agent(path: Path) -> Path:
    """An agent file at `path` — a frontmatter naming it, so the file is a real agent."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nname: {path.stem}\n---\n", encoding="utf-8")
    return path


def _group_agent(root: Path, name: str, group: str | None = None) -> Path:
    """The grouped agent file `name` under `root`, in `group` (default: the group of its own
    name)."""
    return _write_agent(root / "skills" / (group or name) / ".claude" / "agents" / f"{name}.md")


def _agent_file_cli(
    tmp_path: Path, pins_home: Path, *, pin_arg: str, instance_root: str, name: str,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_PIN_PY), "agent-file", "--pin", pin_arg,
         "--instance-root", instance_root, "--name", name],
        capture_output=True, text=True, cwd=cwd,
        env={**os.environ, "HOME": str(tmp_path), "KENSAIAPP_PINS_HOME": str(pins_home)},
    )


class TestGroupedAgents:
    """Agents live at `skills/<group>/.claude/agents/<name>.md`. CP-36 to CP-40."""

    def test_agent_file_pinned_answers_group_path(self, tmp_path, pins_home):
        host = tmp_path / "host"
        _group_agent(host, "pm")
        (host / "core").mkdir()
        made = pin.make(host, pins_home)

        found = _agent_file_cli(
            tmp_path, pins_home, pin_arg=str(made.root), instance_root=str(host), name="pm"
        )

        assert found.returncode == 0
        assert found.stdout.strip() == str(
            made.root / "skills" / "pm" / ".claude" / "agents" / "pm.md"
        )

    def test_agent_file_unpinned_answers_group_path_relative(self, tmp_path, pins_home):
        instance = tmp_path / "instance"
        _group_agent(instance, "qa")

        found = _agent_file_cli(
            tmp_path, pins_home, pin_arg="", instance_root=".", name="qa", cwd=instance
        )

        assert found.returncode == 0
        assert found.stdout.strip() == "skills/qa/.claude/agents/qa.md"

    def test_agent_file_unpinned_falls_back_to_host_groups(self, tmp_path):
        host = tmp_path / "host"
        group_file = _group_agent(host, "pm")
        instance = tmp_path / "instance"
        instance.mkdir()

        found = pin.agent_file(None, instance, "pm", host_root=host)

        assert found == group_file

    def test_agent_file_cli_unpinned_reaches_its_own_hosts_groups(self, tmp_path, pins_home):
        """No pin, an instance holding no `skills/`: the CLI answers from the groups of the host
        `pin.py` sits in, so a consumer satellite's dry run still finds the agent."""
        instance = tmp_path / "instance"
        instance.mkdir()
        host = _PIN_PY.resolve().parents[2]

        found = _agent_file_cli(
            tmp_path, pins_home, pin_arg="", instance_root=str(instance), name="pm"
        )

        assert found.returncode == 0, found.stderr
        assert found.stdout.strip() == str(host / "skills" / "pm" / ".claude" / "agents" / "pm.md")

    def test_instance_own_agent_wins_pinned_and_unpinned(self, tmp_path, pins_home):
        host = tmp_path / "host"
        _group_agent(host, "pm")
        (host / "core").mkdir()
        made = pin.make(host, pins_home)
        instance = tmp_path / "instance"
        _group_agent(instance, "pm")
        own = _write_agent(instance / ".claude" / "agents" / "pm.md")

        assert pin.agent_file(made, instance, "pm") == own
        assert pin.agent_file(None, instance, "pm", host_root=host) == own

    def test_satellite_link_to_host_is_never_the_instance_own(self, tmp_path, pins_home):
        host = tmp_path / "host"
        _group_agent(host, "pm")
        (host / ".claude" / "agents").mkdir(parents=True)
        (host / ".claude" / "agents" / ".gitkeep").write_text("")
        # A stray flat `pm.md` in the host: the link reaches it, so only the host-ownership rule
        # keeps the link's copy from answering as the satellite's own.
        _write_agent(host / ".claude" / "agents" / "pm.md")
        (host / "core").mkdir()
        made = pin.make(host, pins_home)
        satellite = tmp_path / "satellite"
        (satellite / ".claude").mkdir(parents=True)
        (satellite / ".claude" / "agents").symlink_to(host / ".claude" / "agents")

        found = _agent_file_cli(
            tmp_path, pins_home, pin_arg=str(made.root), instance_root=str(satellite), name="pm"
        )

        assert found.returncode == 0
        assert found.stdout.strip() == str(
            made.root / "skills" / "pm" / ".claude" / "agents" / "pm.md"
        )

    def test_unpinned_host_flat_file_through_link_is_skipped(self, tmp_path):
        host = tmp_path / "host"
        group_file = _group_agent(host, "pm")
        _write_agent(host / ".claude" / "agents" / "pm.md")
        satellite = tmp_path / "satellite"
        (satellite / ".claude").mkdir(parents=True)
        (satellite / ".claude" / "agents").symlink_to(host / ".claude" / "agents")

        found = pin.agent_file(None, satellite, "pm", host_root=host)

        assert found == group_file

    def test_agent_file_unknown_name_prints_nothing_exit_1(self, tmp_path, pins_home):
        host = tmp_path / "host"
        _group_agent(host, "pm")
        (host / "core").mkdir()
        made = pin.make(host, pins_home)

        pinned = _agent_file_cli(
            tmp_path, pins_home, pin_arg=str(made.root), instance_root=str(host), name="ghost"
        )
        unpinned = _agent_file_cli(
            tmp_path, pins_home, pin_arg="", instance_root=str(host), name="ghost"
        )

        for result in (pinned, unpinned):
            assert result.returncode == 1
            assert result.stdout == ""

    def test_owned_entries_agents_ignore_non_md_files(self, tmp_path, pins_home):
        host = tmp_path / "host"
        _group_agent(host, "pm")
        _group_agent(host, "qa")
        (host / ".claude" / "agents").mkdir(parents=True)
        (host / ".claude" / "agents" / ".gitkeep").write_text("")
        (host / "core").mkdir()
        made = pin.make(host, pins_home)
        instance = tmp_path / "instance"
        (instance / ".claude" / "agents").mkdir(parents=True)
        (instance / ".claude" / "agents" / "notes.txt").write_text("not an agent\n")
        (instance / ".claude" / "agents" / ".gitkeep").write_text("")

        agents = pin.owned_entries(made, instance, pin.Kind.AGENTS)

        assert sorted(agents) == ["pm", "qa"]

    def test_owned_entries_agents_ignore_group_grant(self, tmp_path, pins_home):
        host = tmp_path / "host"
        _group_agent(host, "pm")
        _write_skill(host / "skills" / "pm" / ".claude" / "skills" / "pm-skill")
        _group_agent(host, "qa")
        _write_skill(host / "skills" / "only-skills" / ".claude" / "skills" / "lone-skill")
        (host / "core").mkdir()
        made = pin.make(host, pins_home)
        instance = tmp_path / "instance"
        instance.mkdir()

        for groups in (frozenset(), frozenset({"pm"}), frozenset({"unknown"})):
            assert sorted(pin.owned_entries(made, instance, pin.Kind.AGENTS, groups)) == [
                "pm", "qa",
            ]

    def test_flat_pin_agent_still_listed_beside_groups(self, tmp_path, pins_home):
        host = tmp_path / "host"
        _write_agent(host / ".claude" / "agents" / "flat-one.md")
        _group_agent(host, "grouped-one")
        (host / "core").mkdir()
        made = pin.make(host, pins_home)
        instance = tmp_path / "instance"
        instance.mkdir()

        agents = pin.owned_entries(made, instance, pin.Kind.AGENTS)

        assert sorted(agents) == ["flat-one", "grouped-one"]

    def test_same_name_in_two_groups_last_sorted_wins(self, tmp_path, pins_home):
        host = tmp_path / "host"
        _group_agent(host, "dup", group="alpha")
        _group_agent(host, "dup", group="beta")
        (host / "core").mkdir()
        made = pin.make(host, pins_home)
        instance = tmp_path / "instance"
        instance.mkdir()

        agents = pin.owned_entries(made, instance, pin.Kind.AGENTS)

        assert agents["dup"] == made.root / "skills" / "beta" / ".claude" / "agents" / "dup.md"


def _init_launcher_host(root: Path) -> Path:
    """A throwaway host with two launchers under `core/launchers/`, non-git so `make` copies the
    whole tree — same-launcher equivalence needs nothing from the git-vs-whole make path."""
    root.mkdir()
    for name in ("skill", "other"):
        launcher_dir = root / "core" / "launchers" / name
        launcher_dir.mkdir(parents=True)
        (launcher_dir / "launcher.sh").write_text("#!/usr/bin/env bash\necho hi\n")
    return root


class TestRunEnv:
    def test_run_env_names_the_pin_and_its_githooks(self, tmp_path, pins_home):
        host = _init_launcher_host(tmp_path / "host")
        made = pin.make(host, pins_home)

        env = pin.run_env(made, {})

        assert env["KENSAIAPP_PIN"] == str(made.root)
        assert env["GIT_CONFIG_COUNT"] == "1"
        assert env["GIT_CONFIG_KEY_0"] == "core.hooksPath"
        assert env["GIT_CONFIG_VALUE_0"] == str(made.root / "core" / "githooks")

    def test_run_env_appends_after_an_inherited_git_config_count(self, tmp_path, pins_home):
        host = _init_launcher_host(tmp_path / "host")
        made = pin.make(host, pins_home)

        env = pin.run_env(
            made,
            {
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "user.name",
                "GIT_CONFIG_VALUE_0": "Caller",
            },
        )

        assert env["GIT_CONFIG_COUNT"] == "2"
        assert env["GIT_CONFIG_KEY_0"] == "user.name"
        assert env["GIT_CONFIG_VALUE_0"] == "Caller"
        assert env["GIT_CONFIG_KEY_1"] == "core.hooksPath"
        assert env["GIT_CONFIG_VALUE_1"] == str(made.root / "core" / "githooks")

    def test_run_env_hooks_path_overrides_the_repos_own_config(self, tmp_path, pins_home):
        host = _init_launcher_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        scratch = tmp_path / "scratch"
        scratch.mkdir()
        _git("init", "-q", cwd=scratch)
        _git("config", "core.hooksPath", str(tmp_path / "local-hooks"), cwd=scratch)

        env = pin.run_env(made, {})
        full_env = {**os.environ, **env}
        result = subprocess.run(
            ["git", "config", "--get", "core.hooksPath"],
            cwd=str(scratch),
            capture_output=True,
            text=True,
            env=full_env,
            check=True,
        )

        assert result.stdout.strip() == str(made.root / "core" / "githooks")


class TestSameLauncher:
    def test_same_launcher_accepts_the_live_absolute_path(self, tmp_path, pins_home):
        host = _init_launcher_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        written = str(host / "core" / "launchers" / "skill" / "launcher.sh")
        expected = str(made.core / "launchers" / "skill" / "launcher.sh")

        assert pin.same_launcher(written, expected, core_dir=made.core, instance_root=host)

    def test_same_launcher_accepts_a_relative_core_launchers_path(self, tmp_path, pins_home):
        host = _init_launcher_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        written = "core/launchers/skill/launcher.sh"
        expected = str(made.core / "launchers" / "skill" / "launcher.sh")

        assert pin.same_launcher(written, expected, core_dir=made.core, instance_root=host)

    def test_same_launcher_accepts_another_pin_of_the_same_host(self, tmp_path, pins_home):
        host = _init_launcher_host(tmp_path / "host")
        first = pin.make(host, pins_home)
        second = pin.make(host, pins_home)
        written = str(second.core / "launchers" / "skill" / "launcher.sh")
        expected = str(first.core / "launchers" / "skill" / "launcher.sh")

        assert pin.same_launcher(written, expected, core_dir=first.core, instance_root=host)

    def test_same_launcher_resolves_core_placeholder(self, tmp_path, pins_home):
        host = _init_launcher_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        written = "<CORE>/launchers/skill/launcher.sh"
        expected = str(made.core / "launchers" / "skill" / "launcher.sh")

        assert pin.same_launcher(written, expected, core_dir=made.core, instance_root=host)

    def test_same_launcher_accepts_a_pruned_pin_of_this_runs_pins_home(self, tmp_path, pins_home):
        """A report outlives the pin its Command was written under; the prune leaves no
        `pin.json` to name the source, so the tail below `core/` is what is compared."""
        host = _init_launcher_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        pruned = pins_home / "20261007T081759Z-q7vsml"
        written = str(pruned / "core" / "launchers" / "skill" / "launcher.sh")
        expected = str(made.core / "launchers" / "skill" / "launcher.sh")

        assert pin.same_launcher(written, expected, core_dir=made.core, instance_root=host)

    def test_same_launcher_refuses_another_launcher_in_a_pruned_pin(self, tmp_path, pins_home):
        host = _init_launcher_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        pruned = pins_home / "20261007T081759Z-q7vsml"
        written = str(pruned / "core" / "launchers" / "other" / "launcher.sh")
        expected = str(made.core / "launchers" / "skill" / "launcher.sh")

        assert not pin.same_launcher(written, expected, core_dir=made.core, instance_root=host)

    def test_same_launcher_refuses_a_missing_core_outside_the_pins_home(self, tmp_path, pins_home):
        host = _init_launcher_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        written = str(tmp_path / "gone" / "core" / "launchers" / "skill" / "launcher.sh")
        expected = str(made.core / "launchers" / "skill" / "launcher.sh")

        assert not pin.same_launcher(written, expected, core_dir=made.core, instance_root=host)

    def test_same_launcher_refuses_a_standing_pin_of_another_host(self, tmp_path, pins_home):
        host = _init_launcher_host(tmp_path / "host")
        other = _init_launcher_host(tmp_path / "other")
        made = pin.make(host, pins_home)
        foreign = pin.make(other, pins_home)
        written = str(foreign.core / "launchers" / "skill" / "launcher.sh")
        expected = str(made.core / "launchers" / "skill" / "launcher.sh")

        assert not pin.same_launcher(written, expected, core_dir=made.core, instance_root=host)

    def test_same_launcher_refuses_a_different_launcher(self, tmp_path, pins_home):
        host = _init_launcher_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        written = str(made.core / "launchers" / "other" / "launcher.sh")
        expected = str(made.core / "launchers" / "skill" / "launcher.sh")

        assert not pin.same_launcher(written, expected, core_dir=made.core, instance_root=host)

    def test_same_launcher_refuses_a_path_outside_the_hosts_launchers(self, tmp_path, pins_home):
        host = _init_launcher_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        written = str(tmp_path / "elsewhere" / "launcher.sh")
        expected = str(made.core / "launchers" / "skill" / "launcher.sh")

        assert not pin.same_launcher(written, expected, core_dir=made.core, instance_root=host)

    def test_same_launcher_accepts_a_launcher_file_that_is_itself_a_symlink_elsewhere(
        self, tmp_path, pins_home
    ):
        """`written` and `expected` name the identical file, and that file is a symlink to
        somewhere entirely outside `core_dir` — a real shape (a test's own performance-linked
        stub), not a hypothetical one: `resolve()` follows the symlink past `core_dir` before
        either side's tail can be computed, and two names for the one real file are the same
        launcher whether or not the file they land on sits under any core or pin tree at all."""
        host = _init_launcher_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        launcher = made.core / "launchers" / "skill" / "launcher.sh"
        elsewhere = tmp_path / "warm" / "stub-abc123"
        elsewhere.parent.mkdir(parents=True)
        elsewhere.write_text("#!/usr/bin/env bash\n")
        launcher.unlink()
        launcher.symlink_to(elsewhere)
        written = str(launcher)
        expected = str(launcher)

        assert pin.same_launcher(written, expected, core_dir=made.core, instance_root=host)


class TestCli:
    def test_cli_agent_file_with_no_pin_reads_the_instances_own(self, tmp_path, pins_home):
        """A `--dry-run` before any pin exists on this host makes none, so the launcher has no
        `KENSAIAPP_PIN` to pass — `core/launchers/skill/launcher.sh` still has to name the agent
        file. With no pin, the instance's own is the whole answer."""
        instance = tmp_path / "instance"
        (instance / ".claude" / "agents").mkdir(parents=True)
        wanted = instance / ".claude" / "agents" / "tech-lead.md"
        wanted.write_text("---\nname: tech-lead\n---\n", encoding="utf-8")

        found = subprocess.run(
            [sys.executable, str(_PIN_PY), "agent-file", "--pin", "",
             "--instance-root", str(instance), "--name", "tech-lead"],
            capture_output=True, text=True, check=True,
            env={**os.environ, "HOME": str(tmp_path), "KENSAIAPP_PINS_HOME": str(pins_home)},
        )

        assert Path(found.stdout.strip()) == wanted

    def test_cli_agent_file_with_no_pin_and_no_instance_file_is_refused(self, tmp_path, pins_home):
        instance = tmp_path / "instance"
        (instance / ".claude" / "agents").mkdir(parents=True)

        found = subprocess.run(
            [sys.executable, str(_PIN_PY), "agent-file", "--pin", "",
             "--instance-root", str(instance), "--name", "nobody-has-this"],
            capture_output=True, text=True,
            env={**os.environ, "HOME": str(tmp_path), "KENSAIAPP_PINS_HOME": str(pins_home)},
        )

        assert found.returncode == 1
        assert found.stdout.strip() == ""

    def test_cli_make_resolve_env_agent_file_round_trip(self, tmp_path, pins_home):
        host = _init_ownership_host(tmp_path / "host")

        made = subprocess.run(
            [sys.executable, str(_PIN_PY), "make", "--host", str(host)],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "HOME": str(tmp_path), "KENSAIAPP_PINS_HOME": str(pins_home)},
        )
        pin_root = Path(made.stdout.strip())
        assert pin_root.is_dir()

        resolved = subprocess.run(
            [sys.executable, str(_PIN_PY), "resolve", "--core", str(pin_root / "core")],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ},
        )
        assert resolved.stdout.strip().splitlines() == [
            f"pin={pin_root}",
            f"source={host.resolve()}",
        ]

        env_out = subprocess.run(
            [sys.executable, str(_PIN_PY), "env", "--pin", str(pin_root)],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ},
        )
        env_lines = dict(
            line.split("=", 1) for line in env_out.stdout.strip().splitlines()
        )
        assert env_lines["KENSAIAPP_PIN"] == str(pin_root)

        agent_found = subprocess.run(
            [
                sys.executable,
                str(_PIN_PY),
                "agent-file",
                "--pin",
                str(pin_root),
                "--instance-root",
                str(host),
                "--name",
                "host-agent",
            ],
            capture_output=True,
            text=True,
            env={**os.environ},
        )
        assert agent_found.returncode == 0
        assert agent_found.stdout.strip() == str(
            pin_root / ".claude" / "agents" / "host-agent.md"
        )

        agent_missing = subprocess.run(
            [
                sys.executable,
                str(_PIN_PY),
                "agent-file",
                "--pin",
                str(pin_root),
                "--instance-root",
                str(host),
                "--name",
                "nobody",
            ],
            capture_output=True,
            text=True,
            env={**os.environ},
        )
        assert agent_missing.returncode == 1

    def test_cli_resolve_exits_3_on_a_missing_inherited_pin(self, tmp_path):
        result = subprocess.run(
            [sys.executable, str(_PIN_PY), "resolve", "--core", str(tmp_path / "not-a-core")],
            capture_output=True,
            text=True,
            env={**os.environ, "KENSAIAPP_PIN": str(tmp_path / "nowhere")},
        )

        assert result.returncode == 3
        assert "nowhere" in result.stderr
