"""The 19 agents live in their groups, `skills/<name>/.claude/agents/<name>.md`, one per agent —
except `delegate`, which `interactive` holds beside `agent-invoke`, the skill that spawns it.

These read the real tree, because the property is about where the files are. The flat
`.claude/agents/` stays as a tracked, empty folder: an instance's own override lives there.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_AGENT_COUNT = 19
_AGENT_ONLY_GROUPS = ("kaizen-fix-author", "kaizen-fixer", "qa")
_DOCS_GRANT_SHAPE = "mcp__[a-z-]+-api-docs"
# An agent kept in a group not named for it, mapped to that group.
_HELD_ELSEWHERE = {"delegate": "interactive"}


def _git(*args):
    return subprocess.run(
        ["git", "-C", str(_REPO), *args], capture_output=True, text=True, check=True
    ).stdout


def _grouped_agents():
    return sorted((_REPO / "skills").glob("*/.claude/agents/*.md"))


def _group_of(agent: Path) -> str:
    return agent.parent.parent.parent.name


def test_flat_agents_dir_holds_no_md_but_is_tracked():
    flat = _REPO / ".claude" / "agents"

    assert list(flat.glob("*.md")) == []
    assert _git("ls-files", ".claude/agents").split() != [], "a fresh clone would lose the folder"


def test_exactly_19_grouped_agents_each_in_its_own_group():
    agents = _grouped_agents()

    assert len(agents) == _AGENT_COUNT
    assert all(
        _group_of(agent) == _HELD_ELSEWHERE.get(agent.stem, agent.stem) for agent in agents
    )
    assert len({agent.stem for agent in agents}) == _AGENT_COUNT
    # CP-33: no group's agents folder holds any other file, whatever its suffix.
    assert sorted((_REPO / "skills").glob("*/.claude/agents/*")) == agents


def test_agent_only_groups_hold_only_their_agent():
    for name in _AGENT_ONLY_GROUPS:
        group = _REPO / "skills" / name

        held = sorted(str(p.relative_to(group)) for p in group.rglob("*") if p.is_file())

        assert held == [f".claude/agents/{name}.md"], (name, held)
        assert not (group / ".claude" / "skills").exists(), name


def test_interactive_group_holds_delegate_beside_the_skill_that_spawns_it():
    held = _git("ls-files", "skills/interactive").split()

    assert "skills/interactive/.claude/agents/delegate.md" in held
    assert "skills/interactive/.claude/skills/agent-invoke/SKILL.md" in held
    assert not (_REPO / "skills" / "delegate").exists()


def test_no_host_file_carries_the_docs_grant():
    # `git grep` exits 1 when it finds nothing, which is the passing case here, so the exit
    # status is read rather than raised on. The grant is named by its shape, because a
    # product's own name may not appear in a file under core/.
    found = subprocess.run(
        ["git", "-C", str(_REPO), "grep", "-l", "-E", _DOCS_GRANT_SHAPE, "--", "skills", ".claude"],
        capture_output=True,
        text=True,
    )

    assert found.returncode == 1, found.stderr
    assert found.stdout == ""


def test_every_agent_file_keeps_exactly_one_tools_line():
    for agent in _grouped_agents():
        tools_lines = [
            line for line in agent.read_text().splitlines() if line.startswith("tools:")
        ]

        assert len(tools_lines) == 1, (agent.name, tools_lines)


def test_every_tools_line_is_a_clean_comma_separated_list():
    # A tool dropped from the line takes its own separator with it: no empty, doubled, leading
    # or trailing `, ` is left behind, and every tool is one bare token.
    for agent in _grouped_agents():
        line = next(
            line for line in agent.read_text().splitlines() if line.startswith("tools:")
        )

        assert line.startswith("tools: "), (agent.name, line)
        tools = line.removeprefix("tools: ").split(", ")

        assert all(tool and tool.strip() == tool and "," not in tool for tool in tools), (
            agent.name,
            line,
        )
