"""The three seat groups reach a default session through tracked relative links.

A Claude Code session started at the host root, with no directory added, finds an agent in
`.claude/agents/` and a skill in `.claude/skills/`, and follows a link in either. So the host
carries one link per seat agent and one per skill of the three seat groups — `skills/pm/`,
`skills/principal-pm/` and `skills/scrum-master/` — and nothing else.

Every check here reads the repository on disk and its git index. The set of skills is read from
the groups, never listed here: a list of seventeen goes stale the first time an eighteenth skill
lands in a group, and the check that holds the links to the groups must fail until it is linked.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SEAT_GROUPS = ("pm", "principal-pm", "scrum-master")
FLAT_SKILLS = REPO / ".claude" / "skills"
FLAT_AGENTS = REPO / ".claude" / "agents"
SYMLINK_MODE = "120000"


def _group_skills(group: str) -> list[Path]:
    skills = REPO / "skills" / group / ".claude" / "skills"
    return sorted(path for path in skills.iterdir() if path.is_dir())


def _seat_links() -> list[Path]:
    """Every link the host is expected to carry: three agent links and one per seat skill."""
    links = [FLAT_AGENTS / f"{group}.md" for group in SEAT_GROUPS]
    links += [FLAT_SKILLS / skill.name for group in SEAT_GROUPS for skill in _group_skills(group)]
    return links


def test_every_skill_in_a_seat_group_has_a_link_that_resolves_to_it():
    for group in SEAT_GROUPS:
        for skill in _group_skills(group):
            link = FLAT_SKILLS / skill.name
            assert link.is_symlink(), f"{link.relative_to(REPO)} is not a link to {skill.name}"
            assert link.resolve() == skill.resolve(), (
                f"{link.relative_to(REPO)} resolves to {link.resolve()}, not to {skill}"
            )


def test_each_seat_agent_link_resolves_to_the_groups_agent_file():
    for group in SEAT_GROUPS:
        link = FLAT_AGENTS / f"{group}.md"
        group_file = REPO / "skills" / group / ".claude" / "agents" / f"{group}.md"
        assert link.is_symlink(), f"{link.relative_to(REPO)} is not a link"
        assert link.resolve() == group_file.resolve()


def test_nothing_else_is_linked():
    expected_skills = {link.name for link in _seat_links() if link.parent == FLAT_SKILLS}
    assert {entry.name for entry in FLAT_SKILLS.iterdir()} == expected_skills

    expected_agents = {f"{group}.md" for group in SEAT_GROUPS}
    markdown_agents = {entry.name for entry in FLAT_AGENTS.iterdir() if entry.suffix == ".md"}
    assert markdown_agents == expected_agents


def test_every_link_target_is_relative_and_stays_inside_the_repository():
    for link in _seat_links():
        target = os.readlink(link)
        assert not os.path.isabs(target), f"{link.relative_to(REPO)} points at {target}"
        resolved = link.resolve()
        assert REPO.resolve() in resolved.parents, (
            f"{link.relative_to(REPO)} leaves the repository: {resolved}"
        )


def test_every_link_is_tracked_as_a_link_in_the_index():
    listing = subprocess.run(
        ["git", "-C", str(REPO), "ls-files", "-s", "--", ".claude/agents", ".claude/skills"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    modes = {}
    for line in listing.splitlines():
        meta, path = line.split("\t", 1)
        modes[path] = meta.split()[0]
    for link in _seat_links():
        relpath = link.relative_to(REPO).as_posix()
        assert modes.get(relpath) == SYMLINK_MODE, (
            f"{relpath} is not a tracked link: {modes.get(relpath)}"
        )


def test_no_settings_file_holds_the_reach():
    """The reach is made by the links alone: the tracked `settings.json` names no directory."""
    text = (REPO / ".claude" / "settings.json").read_text()
    assert "additionalDirectories" not in text
    assert "add-dir" not in text
