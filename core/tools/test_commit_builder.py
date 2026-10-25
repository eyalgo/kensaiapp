"""Characterization tests for `commit_builder.py` — pin *today's* canonical
commit/merge format and the `AGENT_ROLE` actor->Role mapping through the new
construction path. Nothing new is asserted here; these tests exist so the
builder's output is proven equal to the hand-authored format it replaces
(`core/doctrine/governance/commit_format.md`, `.claude/skills/_shared/merge-format.md`),
not just plausible. The commit format's prose single source is
`core/doctrine/governance/commit_format.md`; the merge format has no separate
prose file — the builder's `merge` op is its single source (the former
`.claude/skills/_shared/merge-format.md` retired 2026-07-08).

Tests exercise the builder by importing its assembly function and
`AGENT_ROLE` directly (see `conftest.py` — this directory is a flat stdlib
module set, no package). The retired inject-and-block hook
(`.claude/hooks/enforce_commit_role.py`) that a builder-completed commit
used to be proven against is gone — that same assertion ("a builder-made
commit passes enforcement") now lives in
`core/tools/test_verify_commit_msg.py::test_passes_builder_made_commit`,
against the git-layer `commit-msg` checker that replaced it.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

import agent_run
import commit_builder
import pin

BUILDER = Path(__file__).parent / "commit_builder.py"

CO_AUTHORED_BY = "Claude Sonnet 5 <noreply@anthropic.com>"


# ── canonical commit trailer order ──────────────────────────────────────────

def test_commit_trailers_in_canonical_order():
    message = commit_builder.build_message(
        "commit",
        subject="developer: task 1 — the builder",
        body="Implements the one executable.",
        actor="developer",
        directional="Shukuba: commit-builder — progress: builds it",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
    )
    trailer_block = message.split("\n\n")[-1]
    assert trailer_block.splitlines() == [
        "Shukuba: commit-builder — progress: builds it",
        "Role: Developer",
        "Surface: Claude Code",
        f"Co-Authored-By: {CO_AUTHORED_BY}",
    ]


# ── Claude-Session: — the conversation that produced the commit ────────────
# The neighbour of Co-Authored-By:, which names the model where this names the
# session. Optional on both ops, and — unlike the three *-Version: trailers —
# present on `merge` too: a merge is made in a session exactly as a commit is,
# and the authorizer is a role rather than a reason to drop the link.

SESSION_URL = "https://claude.ai/code/session_01LprRdLTUV4ymkZdjQDuNer"


def test_claude_session_sits_directly_after_co_authored_by():
    message = commit_builder.build_message(
        "commit",
        subject="developer: task 1 — the builder",
        body="Implements the one executable.",
        actor="developer",
        directional="Shukuba: commit-builder — progress: builds it",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
        claude_session=SESSION_URL,
    )
    trailer_block = message.split("\n\n")[-1]
    assert trailer_block.splitlines() == [
        "Shukuba: commit-builder — progress: builds it",
        "Role: Developer",
        "Surface: Claude Code",
        f"Co-Authored-By: {CO_AUTHORED_BY}",
        f"Claude-Session: {SESSION_URL}",
    ]


def test_claude_session_precedes_the_provenance_lines():
    # Which model and which conversation belong together; what machinery ran
    # is the next question, not an interruption of this one.
    message = commit_builder.build_message(
        "commit",
        subject="s",
        body="b",
        role="Product",
        directional="Michi: sharpen-by-living — serves: it",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
        claude_session=SESSION_URL,
        skill_version="a-skill@1.0.0 " + "d" * 40,
        prompt_version="a_prompt@1.0.0 " + "e" * 40,
    )
    lines = message.split("\n\n")[-1].splitlines()
    assert lines.index(f"Claude-Session: {SESSION_URL}") < lines.index(
        "Skill-Version: a-skill@1.0.0 " + "d" * 40
    )


def test_no_claude_session_line_when_none():
    # A run with no session URL to give does not invent one, and the absence
    # is a clean omission rather than an empty trailer.
    message = commit_builder.build_message(
        "commit",
        subject="s",
        body="b",
        role="Product",
        directional="Michi: sharpen-by-living — serves: it",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
    )
    assert "Claude-Session:" not in message


# ── Reasoning-Effort: — resolved runtime attribution ───────────────────────

@pytest.mark.parametrize("effort", ("low", "medium", "high", "xhigh", "max"))
def test_commit_places_each_reasoning_effort_in_canonical_order(effort):
    message = commit_builder.build_message(
        "commit", subject="s", actor="developer",
        directional="Shukuba: proto — progress: x", surface="Codex",
        co_authored_by="gpt-5.6-terra <noreply@openai.com>",
        reasoning_effort=effort, claude_session=SESSION_URL,
        skill_version="skill@1.0.0 " + "a" * 40,
    )

    assert message.split("\n\n")[-1].splitlines() == [
        "Shukuba: proto — progress: x",
        "Role: Developer",
        "Surface: Codex",
        "Co-Authored-By: gpt-5.6-terra <noreply@openai.com>",
        f"Reasoning-Effort: {effort}",
        f"Claude-Session: {SESSION_URL}",
        "Skill-Version: skill@1.0.0 " + "a" * 40,
    ]


def test_merge_places_reasoning_effort_without_commit_provenance():
    message = commit_builder.build_message(
        "merge", actor="pm", branch="topic", target_branch="main", description="d",
        merge_context="ctx", surface="Codex",
        co_authored_by="gpt-5.6-sol <noreply@openai.com>",
        reasoning_effort="medium", claude_session=SESSION_URL,
        skill_version="ignored@1.0.0 " + "a" * 40,
    )

    assert message.split("\n\n")[-1].splitlines() == [
        "Merge-Authorized: PM — ctx",
        "Surface: Codex",
        "Co-Authored-By: gpt-5.6-sol <noreply@openai.com>",
        "Reasoning-Effort: medium",
        f"Claude-Session: {SESSION_URL}",
    ]


def test_advance_places_reasoning_effort_after_surface_without_a_co_author():
    message = commit_builder.build_message(
        "advance", actor="developer", from_ref="main", branch="topic",
        taken_sha="a" * 40, surface="Codex", reasoning_effort="high",
    )

    assert message.split("\n\n")[-1].splitlines() == [
        f"Merge-Authorized: Developer — takes main at {'a' * 40}",
        "Surface: Codex",
        "Reasoning-Effort: high",
    ]


@pytest.mark.parametrize("operation", ("commit", "merge", "advance"))
def test_every_builder_operation_exposes_the_reasoning_effort_choices(operation, capsys):
    with pytest.raises(SystemExit) as raised:
        commit_builder.main([operation, "--help"])
    assert raised.value.code == 0
    assert "--reasoning-effort {low,medium,high,xhigh,max}" in capsys.readouterr().out


@pytest.mark.parametrize("operation", ("commit", "merge", "advance"))
def test_every_builder_operation_refuses_an_unknown_reasoning_effort_before_git(operation):
    parser = commit_builder._build_arg_parser()
    with pytest.raises(SystemExit) as raised:
        parser.parse_args([operation, "--reasoning-effort", "extreme"])
    assert raised.value.code == 2


# The smallest argv each operation's parser accepts, so a level can be offered to the real
# `--reasoning-effort` flag rather than handed to `build_message` past the parser that admits it.
_PARSEABLE_ARGV = {
    "commit": [
        "commit", "--subject", "s", "--actor", "developer",
        "--directional", "Shukuba: proto — progress: x", "--surface", "Codex",
    ],
    "merge": [
        "merge", "--branch", "topic", "--target-branch", "main", "--description", "d",
        "--actor", "pm", "--merge-context", "ctx", "--surface", "Codex",
    ],
    "advance": ["advance", "--from", "main", "--actor", "developer", "--surface", "Codex"],
}

_MESSAGE_FIELDS = {
    "commit": dict(
        subject="s", actor="developer", directional="Shukuba: proto — progress: x",
    ),
    "merge": dict(
        actor="pm", branch="topic", target_branch="main", description="d", merge_context="ctx",
    ),
    "advance": dict(actor="developer", from_ref="main", branch="topic", taken_sha="a" * 40),
}


def _admitted_reasoning_effort(operation, level):
    """The level as the operation's own parser hands it on — `SystemExit` when it refuses it."""
    parser = commit_builder._build_arg_parser()
    return parser.parse_args(
        [*_PARSEABLE_ARGV[operation], "--reasoning-effort", level]
    ).reasoning_effort


@pytest.mark.parametrize("operation", ("commit", "merge", "advance"))
@pytest.mark.parametrize(
    "co_authored_by,line_before",
    (
        (CO_AUTHORED_BY, f"Co-Authored-By: {CO_AUTHORED_BY}"),
        (None, "Surface: Codex"),
    ),
    ids=("after-co-authored-by", "after-surface"),
)
def test_every_operation_accepts_max_and_writes_one_max_trailer(
    operation, co_authored_by, line_before
):
    message = commit_builder.build_message(
        operation, surface="Codex", co_authored_by=co_authored_by,
        reasoning_effort=_admitted_reasoning_effort(operation, "max"),
        **_MESSAGE_FIELDS[operation],
    )
    lines = message.split("\n\n")[-1].splitlines()

    assert lines.count("Reasoning-Effort: max") == 1
    assert sum(line.startswith("Reasoning-Effort:") for line in lines) == 1
    assert lines[lines.index("Reasoning-Effort: max") - 1] == line_before


@pytest.mark.parametrize("operation", ("commit", "merge", "advance"))
@pytest.mark.parametrize("effort", list(agent_run.Effort), ids=lambda effort: effort.value)
def test_every_agent_run_effort_value_is_admitted_by_each_operation(operation, effort):
    # The builder states its own set rather than importing the launcher's vocabulary
    # (`agent_run.Effort`), so this is what holds the two together: a level a launch can
    # resolve is a level the builder can record.
    assert _admitted_reasoning_effort(operation, effort.value) == effort.value


_REPO_ROOT = Path(__file__).resolve().parents[2]


def _reasoning_effort_section():
    """`commit_format.md` § `Reasoning-Effort:` trailer, heading to the next heading."""
    doctrine = (
        _REPO_ROOT / "core" / "doctrine" / "governance" / "commit_format.md"
    ).read_text(encoding="utf-8")
    start = doctrine.index("### `Reasoning-Effort:` trailer")
    return doctrine[start:doctrine.index("\n### ", start + 1)]


def test_commit_format_shape_line_names_exactly_the_builders_admitted_set():
    section = _reasoning_effort_section()
    shape_lines = [line for line in section.splitlines() if line.startswith("**Shape:**")]
    assert len(shape_lines) == 1
    named = shape_lines[0].split("exactly one of", 1)[1].split(".", 1)[0]

    assert tuple(re.findall(r"`([a-z]+)`", named)) == commit_builder.REASONING_EFFORT_LEVELS
    assert "records `Reasoning-Effort: max`" in section


# A statement of the level set that stops at `xhigh`. The gaps are the ones the five statements
# found on 2026-09-30 needed (`", "`, `` `, ` ``, ` | `, `, or `), with room to spare; `max` is
# looked for within the same reach after `xhigh`, so `xhigh | max` and ``xhigh`, or `max`` pass.
_FOUR_LEVEL_STATEMENT = re.compile(r"low.{1,12}medium.{1,12}high.{1,14}xhigh(?!.{0,14}max)")
_SWEPT_ROOTS = (Path("core"),)


def _four_level_statements():
    """Every `path:line` under the swept roots that states the level set as four — walked from
    disk, so a statement added tomorrow is held to the rule the day it lands."""
    found = []
    for root in _SWEPT_ROOTS:
        for path in sorted((_REPO_ROOT / root).rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts or path.name.startswith("test_"):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for number, line in enumerate(text.splitlines(), start=1):
                if _FOUR_LEVEL_STATEMENT.search(line):
                    found.append(f"{path.relative_to(_REPO_ROOT)}:{number}")
    return found


def test_no_statement_of_the_level_set_names_four_levels():
    assert _four_level_statements() == []


def test_the_four_level_sweep_reads_a_five_level_statement_as_complete():
    # The sweep's own discrimination: it must catch each spelling the tree used for four levels
    # and pass the same spelling once `max` follows, or a clean result above proves nothing.
    four = (
        'choices=("low", "medium", "high", "xhigh"),',
        "exactly one of `low`, `medium`, `high`, or `xhigh`.",
        "Reasoning-Effort: <low | medium | high | xhigh>",
    )
    five = (
        'choices=("low", "medium", "high", "xhigh", "max"),',
        "exactly one of `low`, `medium`, `high`, `xhigh`, or `max`.",
        "Reasoning-Effort: <low | medium | high | xhigh | max>",
    )

    assert all(_FOUR_LEVEL_STATEMENT.search(statement) for statement in four)
    assert not any(_FOUR_LEVEL_STATEMENT.search(statement) for statement in five)


def test_absent_reasoning_effort_preserves_each_pre_change_message():
    commit = commit_builder.build_message(
        "commit", subject="s", actor="developer", directional="Shukuba: proto — progress: x",
        surface="Codex", co_authored_by="gpt-5.6-terra <noreply@openai.com>",
    )
    merge = commit_builder.build_message(
        "merge", actor="pm", branch="topic", target_branch="main", description="d",
        merge_context="ctx", surface="Codex",
    )
    advance = commit_builder.build_message(
        "advance", actor="developer", from_ref="main", branch="topic",
        taken_sha="a" * 40, surface="Codex",
    )

    assert commit == (
        "s\n\n"
        "Shukuba: proto — progress: x\n"
        "Role: Developer\n"
        "Surface: Codex\n"
        "Co-Authored-By: gpt-5.6-terra <noreply@openai.com>"
    )
    assert merge == (
        "merge: topic → main — d\n\n"
        "Merge-Authorized: PM — ctx\n"
        "Surface: Codex"
    )
    assert advance == (
        "merge: main → topic — take main's advance\n\n"
        f"Merge-Authorized: Developer — takes main at {'a' * 40}\n"
        "Surface: Codex"
    )


def test_reasoning_effort_preserves_existing_trailer_values_and_relative_order():
    message = commit_builder.build_message(
        "commit", subject="s", actor="developer", directional="Shukuba: proto — progress: x",
        surface="Codex", co_authored_by="gpt-5.6-terra <noreply@openai.com>",
        reasoning_effort="low", claude_session=SESSION_URL,
        workflow_version="workflow@1.0.0 " + "b" * 40,
    )
    lines = message.split("\n\n")[-1].splitlines()

    assert lines == [
        "Shukuba: proto — progress: x",
        "Role: Developer",
        "Surface: Codex",
        "Co-Authored-By: gpt-5.6-terra <noreply@openai.com>",
        "Reasoning-Effort: low",
        f"Claude-Session: {SESSION_URL}",
        "Workflow-Version: workflow@1.0.0 " + "b" * 40,
    ]


# --- a committer with no model behind it ----------------------------------
#
# Every caller until now was an AI session, so `Co-Authored-By:` always had a
# real value and the flag was required. `core/launchers/product-skeleton/` is
# the first committer that runs no model at all — a deterministic copier the
# owner invokes, whose header states "No `claude`, no `--agent`, no
# `--permission-mode`, no prompt". It has no model to name, and naming one
# would put a model's signature on bytes it never saw.
#
# Doctrine already allows the absence: `commit_format.md` § Role and its
# trailer block make `Role:` and `Surface:` the enforced set, and
# `verify_commit_msg.py` presence-checks exactly those two. Only this
# builder's CLI insisted. So the line becomes omittable, and its absence
# positively means no model authored the commit. The owner's call, 2026-09-03.


def test_no_co_authored_by_line_when_none():
    message = commit_builder.build_message(
        "commit",
        subject="s",
        body="b",
        role="Product",
        directional="Agari: example-product — progress: it",
        surface="product-skeleton",
    )
    assert "Co-Authored-By:" not in message


def test_a_model_less_commit_still_carries_the_two_enforced_trailers():
    message = commit_builder.build_message(
        "commit",
        subject="s",
        body="b",
        role="Product",
        directional="Agari: example-product — progress: it",
        surface="product-skeleton",
    )
    assert message.split("\n\n")[-1].splitlines() == [
        "Agari: example-product — progress: it",
        "Role: Product",
        "Surface: product-skeleton",
    ]


def test_a_model_less_merge_omits_the_line_too():
    message = commit_builder.build_message(
        "merge",
        actor="pm",
        branch="b",
        target_branch="main",
        description="d",
        merge_context="ctx",
        surface="product-skeleton",
    )
    assert "Co-Authored-By:" not in message
    assert "Surface: product-skeleton" in message


def test_claude_session_still_places_correctly_with_no_co_author():
    """The session line is defined as sitting directly after `Co-Authored-By:`.
    With no such line it follows `Surface:` — placement degrades, the trailer
    does not go missing."""
    message = commit_builder.build_message(
        "commit",
        subject="s",
        body="b",
        role="Product",
        directional="Agari: example-product — progress: it",
        surface="product-skeleton",
        claude_session=SESSION_URL,
    )
    assert message.split("\n\n")[-1].splitlines() == [
        "Agari: example-product — progress: it",
        "Role: Product",
        "Surface: product-skeleton",
        f"Claude-Session: {SESSION_URL}",
    ]


def test_the_cli_accepts_a_commit_with_no_co_authored_by(tmp_path):
    repo = tmp_path
    _init_repo(repo)
    (repo / "a.txt").write_text("hi\n")

    code = commit_builder.main(
        [
            "--repo", str(repo), "commit",
            "--add", "a.txt",
            "--subject", "skeleton: the frame",
            "--role", "Product",
            "--directional", "Agari: example-product — progress: it",
            "--surface", "product-skeleton",
        ]
    )

    assert code == 0
    message = subprocess.run(
        ["git", "-C", str(repo), "log", "-1", "--format=%B"],
        capture_output=True, text=True,
    ).stdout
    assert "Surface: product-skeleton" in message
    assert "Co-Authored-By:" not in message


def test_an_explicit_co_authored_by_is_still_placed(tmp_path):
    """The omission is an option, not a removal — every existing caller keeps
    the line exactly where it was."""
    message = commit_builder.build_message(
        "commit",
        subject="s",
        body="b",
        role="Product",
        directional="Agari: example-product — progress: it",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
    )
    assert f"Co-Authored-By: {CO_AUTHORED_BY}" in message


def test_merge_carries_claude_session():
    # The one place this differs from Skill-Version: and its siblings, which
    # the merge path ignores outright.
    message = commit_builder.build_message(
        "merge",
        actor="pm",
        branch="feature",
        target_branch="main",
        description="thing",
        branch_commits=["abc1234 do the thing"],
        merge_context="manual",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
        claude_session=SESSION_URL,
    )
    trailer_block = message.split("\n\n")[-1]
    assert trailer_block.splitlines()[-1] == f"Claude-Session: {SESSION_URL}"


# ── Skill-Version: provenance trailer — placement only (build_message stays
#    pure; it positions the finished value, it does not resolve it) ─────────

def test_skill_version_line_present_and_last():
    message = commit_builder.build_message(
        "commit",
        subject="developer: task 1 — the builder",
        body="Implements the one executable.",
        actor="developer",
        directional="Shukuba: commit-builder — progress: builds it",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
        skill_version="development-design@1.8.0 " + "a" * 40,
    )
    trailer_block = message.split("\n\n")[-1]
    assert trailer_block.splitlines() == [
        "Shukuba: commit-builder — progress: builds it",
        "Role: Developer",
        "Surface: Claude Code",
        f"Co-Authored-By: {CO_AUTHORED_BY}",
        "Skill-Version: development-design@1.8.0 " + "a" * 40,
    ]


def test_no_skill_version_line_when_none():
    # Both the explicit None and the omitted-parameter default land here.
    for kwargs in ({"skill_version": None}, {}):
        message = commit_builder.build_message(
            "commit",
            subject="work",
            actor="developer",
            directional="Shukuba: proto — progress: x",
            surface="Claude Code",
            co_authored_by=CO_AUTHORED_BY,
            **kwargs,
        )
        assert "Skill-Version:" not in message


def test_merge_ignores_skill_version():
    message = commit_builder.build_message(
        "merge",
        actor="pm",
        branch="feature",
        target_branch="main",
        description="thing",
        branch_commits=["abc1234 do the thing"],
        merge_context="manual",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
        skill_version="anything@1.0.0 " + "b" * 40,
    )
    assert "Skill-Version:" not in message


# ── Prompt-Version: provenance trailer — placement only ────────────────────
# The sibling of Skill-Version:, for output produced by a prompt a session
# read directly. Same pure/impure split: build_message positions a finished
# value it does not resolve. The two are independent facts — which skill ran,
# which prompt ran — so both may appear, either may appear alone, and neither
# implies the other. Prompt-Version: is last when present.

def test_prompt_version_line_present_and_last():
    message = commit_builder.build_message(
        "commit",
        subject="cto: the instance states its domain doctrine",
        body="Read the prompt, wrote the file.",
        role="CTO",
        directional="Shukuba: doctrine — progress: states it",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
        prompt_version="cto_create_domain_doctrine@1.0.0 " + "c" * 40,
    )
    trailer_block = message.split("\n\n")[-1]
    assert trailer_block.splitlines() == [
        "Shukuba: doctrine — progress: states it",
        "Role: CTO",
        "Surface: Claude Code",
        f"Co-Authored-By: {CO_AUTHORED_BY}",
        "Prompt-Version: cto_create_domain_doctrine@1.0.0 " + "c" * 40,
    ]


def test_both_provenance_lines_appear_skill_then_prompt():
    # A thin skill over a fat prompt records both, in a fixed order: the
    # skill line first (it kept the position it has always had), the prompt
    # line last. Order is a fact of build_message's explicit sequence.
    message = commit_builder.build_message(
        "commit",
        subject="cpo: draft the PRD",
        actor="cpo",
        directional="Agari: thing — progress: drafts it",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
        skill_version="product-prd@4.11.0 " + "a" * 40,
        prompt_version="cpo_create_prd@2.5.0 " + "c" * 40,
    )
    assert message.split("\n\n")[-1].splitlines()[-2:] == [
        "Skill-Version: product-prd@4.11.0 " + "a" * 40,
        "Prompt-Version: cpo_create_prd@2.5.0 " + "c" * 40,
    ]


def test_no_prompt_version_line_when_none():
    # Both the explicit None and the omitted-parameter default land here.
    for kwargs in ({"prompt_version": None}, {}):
        message = commit_builder.build_message(
            "commit",
            subject="work",
            actor="developer",
            directional="Shukuba: proto — progress: x",
            surface="Claude Code",
            co_authored_by=CO_AUTHORED_BY,
            **kwargs,
        )
        assert "Prompt-Version:" not in message


def test_merge_ignores_prompt_version():
    # Same reason the merge path ignores Skill-Version: — a merge is authored
    # by the merge authorizer, not by a producing artifact.
    message = commit_builder.build_message(
        "merge",
        actor="pm",
        branch="feature",
        target_branch="main",
        description="thing",
        branch_commits=["abc1234 do the thing"],
        merge_context="manual",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
        prompt_version="anything@1.0.0 " + "c" * 40,
    )
    assert "Prompt-Version:" not in message


# ── resolve_skill_version — the impure, explicit-only resolver ──────────────
# Provenance is stamped IFF the caller passes an explicit skill name; the
# retired actor-derivation (`ACTOR_SKILL`) is gone. All file-read and
# git-subprocess work for the provenance value lives here, never in
# build_message (which stays pure). Uses the same throwaway-repo helpers
# (_init_repo, defined further down) the execution-half tests already use.

def _add_skill_fixture(path: Path, name: str, version: str | None = "1.8.0") -> None:
    """Create and commit a `.claude/skills/<name>/SKILL.md` fixture inside a
    throwaway repo — the shape `resolve_skill_version` reads. `version=None`
    writes frontmatter with no `version:` line, for the unresolvable case."""
    skill_dir = path / ".claude" / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    version_line = f'  version: "{version}"\n' if version is not None else ""
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        "description: fixture skill for resolve_skill_version tests\n"
        "metadata:\n"
        f"{version_line}"
        "---\n\n"
        f"# {name}\n\nFixture only.\n"
    )
    subprocess.run(
        ["git", "-C", str(path), "add", str(skill_dir.relative_to(path))],
        check=True, capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "commit", "-q", "-m", f"fixture: add {name} skill"],
        check=True, capture_output=True, text=True,
    )


def test_resolve_skill_version_format_and_full_sha(tmp_path):
    _init_repo(tmp_path)
    _add_skill_fixture(tmp_path, "development-design", version="1.8.0")

    result = commit_builder.resolve_skill_version(str(tmp_path), "development-design")

    # Shape only — name@semver, single space, full-length 40-hex SHA (never
    # abbreviated). Not an exact-version assertion: a fixture skill's version
    # is arbitrary, and this must not couple to a live skill's real version.
    assert result is not None
    assert re.match(r"^development-design@\d+\.\d+\.\d+ [0-9a-f]{40}$", result)


def test_resolve_skill_version_no_skill_name_returns_none(tmp_path):
    # Explicit-only: with no skill_name the value is None regardless of what
    # skill sources exist on disk — the skill-less commit path (--role, or a
    # bare --actor with no --skill). A SKILL.md fixture present must NOT resolve
    # without an explicit name (the exact case that returned development-design@…
    # under the retired actor-derivation). Both the omitted-arg default and an
    # explicit None land here.
    _init_repo(tmp_path)
    _add_skill_fixture(tmp_path, "development-design", version="1.8.0")
    assert commit_builder.resolve_skill_version(str(tmp_path)) is None
    assert commit_builder.resolve_skill_version(str(tmp_path), None) is None


def test_resolve_skill_version_unresolvable_returns_none(tmp_path):
    # An explicit skill_name whose source cannot be read — never fabricate a
    # value, never raise. Two sub-cases: SKILL.md absent, and SKILL.md
    # present but carrying no version: line.
    _init_repo(tmp_path)

    # (a) skill source entirely absent
    assert commit_builder.resolve_skill_version(str(tmp_path), "development-design") is None

    # (b) SKILL.md present, no version: line in its frontmatter
    _add_skill_fixture(tmp_path, "development-design", version=None)
    assert commit_builder.resolve_skill_version(str(tmp_path), "development-design") is None


def test_resolve_skill_version_uncommitted_source_returns_none(tmp_path):
    # The third unresolvable sub-case from the intent: an explicit skill whose
    # SKILL.md is present AND carries a version: line, but whose source has no
    # committed revision (nothing in git touches .claude/skills/<name>/). The
    # semver resolves from disk, but there is no source SHA — so the value is
    # None, never fabricated and never raised. This pins the `sha is None`
    # branch that the absent / no-version sub-cases (which stop at semver=None)
    # do not reach.
    _init_repo(tmp_path)
    skill_dir = tmp_path / ".claude" / "skills" / "development-design"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        '---\nname: development-design\nmetadata:\n  version: "1.8.0"\n---\n\n# x\n'
    )
    # Deliberately NOT staged/committed — the SKILL.md is readable from disk
    # (semver resolves) but git log finds no revision for the skill path.
    assert commit_builder.resolve_skill_version(
        str(tmp_path), "development-design"
    ) is None


def test_resolve_skill_version_signature_drops_actor():
    # The intent retires the actor parameter: the signature is
    # resolve_skill_version(skill_repo, skill_name=None) — no `actor`. Pinning
    # the parameter list guards against the derivation being reintroduced
    # through the signature (a companion to the ACTOR_SKILL-deletion assertion).
    import inspect

    params = list(inspect.signature(commit_builder.resolve_skill_version).parameters)
    assert params == ["skill_repo", "skill_name"]
    assert "actor" not in params


# ── resolve_skill_version — the grouped layout ───────────────────────────────
# `resolve_skill_version` must resolve through `skill_path`, so a skill whose only copy lives
# under the grouped layout (`skills/<group>/.claude/skills/<name>`) still stamps
# `Skill-Version:`. Each fixture here builds ONLY the grouped shape — no flat path at all — so a
# passing test proves the grouped path was actually walked, never a flat fallback.

def _add_grouped_skill_fixture(
    path: Path, group: str, name: str, version: str | None = "1.8.0"
) -> None:
    """Create and commit a `skills/<group>/.claude/skills/<name>/SKILL.md` fixture — the
    grouped mirror of `_add_skill_fixture`, with no flat branch at all."""
    skill_dir = path / "skills" / group / ".claude" / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    version_line = f'  version: "{version}"\n' if version is not None else ""
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        "description: fixture skill for resolve_skill_version tests\n"
        "metadata:\n"
        f"{version_line}"
        "---\n\n"
        f"# {name}\n\nFixture only.\n"
    )
    subprocess.run(
        ["git", "-C", str(path), "add", str(skill_dir.relative_to(path))],
        check=True, capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "commit", "-q", "-m", f"fixture: add grouped {name} skill"],
        check=True, capture_output=True, text=True,
    )


def test_resolve_skill_version_resolves_a_grouped_skill(tmp_path):
    _init_repo(tmp_path)
    _add_grouped_skill_fixture(tmp_path, "g", "d", version="2.1.0")
    assert not (tmp_path / ".claude" / "skills").exists()

    result = commit_builder.resolve_skill_version(str(tmp_path), "d")

    assert result is not None
    assert re.match(r"^d@2\.1\.0 [0-9a-f]{40}$", result)


def test_resolve_skill_version_grouped_sha_is_the_adding_commit_not_head(tmp_path):
    _init_repo(tmp_path)
    _add_grouped_skill_fixture(tmp_path, "g", "d", version="2.1.0")
    adding_sha = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()

    (tmp_path / "unrelated.txt").write_text("unrelated\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "unrelated.txt"],
                    check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "unrelated"],
                    check=True, capture_output=True, text=True)

    result = commit_builder.resolve_skill_version(str(tmp_path), "d")

    assert result == f"d@2.1.0 {adding_sha}"


def test_resolve_skill_version_flat_still_resolves_unchanged(tmp_path):
    # test_resolve_skill_version_format_and_full_sha and its three neighbours already pin this;
    # one more inline check that flat resolution was not disturbed by the grouped adoption.
    _init_repo(tmp_path)
    _add_skill_fixture(tmp_path, "development-design", version="1.8.0")

    result = commit_builder.resolve_skill_version(str(tmp_path), "development-design")

    assert result is not None
    assert re.match(r"^development-design@1\.8\.0 [0-9a-f]{40}$", result)


def test_resolve_skill_version_two_grouped_copies_is_ambiguous_returns_none(tmp_path):
    _init_repo(tmp_path)
    _add_grouped_skill_fixture(tmp_path, "a", "d", version="1.0.0")
    _add_grouped_skill_fixture(tmp_path, "b", "d", version="1.0.0")

    assert commit_builder.resolve_skill_version(str(tmp_path), "d") is None


def test_resolve_skill_version_grouped_uncommitted_source_returns_none(tmp_path):
    _init_repo(tmp_path)
    skill_dir = tmp_path / "skills" / "g" / ".claude" / "skills" / "d"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        '---\nname: d\nmetadata:\n  version: "1.0.0"\n---\n\n# d\n'
    )
    # Deliberately not staged/committed.

    assert commit_builder.resolve_skill_version(str(tmp_path), "d") is None


def test_resolve_skill_version_grouped_no_version_line_returns_none(tmp_path):
    _init_repo(tmp_path)
    _add_grouped_skill_fixture(tmp_path, "g", "d", version=None)

    assert commit_builder.resolve_skill_version(str(tmp_path), "d") is None


def test_no_docstring_claims_the_skill_source_always_lives_at_flat():
    import inspect

    source = inspect.getsource(commit_builder)
    assert "always lives at" not in source


# ── resolve_skill_version / resolve_prompt_version — under a pin ───────────
# A pinned run (`pin.py`) resolves `instance_repo_root()` to the pin's own directory, which is a
# plain copy — not a git repo. `resolve_skill_version` / `resolve_prompt_version` must still find
# a SHA, by redirecting the `git log` to the pin's `source_host_root`, restricted to the
# `source_head` recorded when the pin was made.

def _init_pin_host(tmp_path: Path) -> Path:
    host = tmp_path / "host"
    host.mkdir()
    _init_repo(host)
    return host


def test_resolve_skill_version_under_a_pin_resolves_against_source_head(tmp_path):
    host = _init_pin_host(tmp_path)
    _add_skill_fixture(host, "development-design", version="1.8.0")
    adding_sha = subprocess.run(
        ["git", "-C", str(host), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    pins_home = tmp_path / "pins"
    pins_home.mkdir()
    made = pin.make(host, pins_home)

    result = commit_builder.resolve_skill_version(str(made.root), "development-design")

    assert result == f"development-design@1.8.0 {adding_sha}"


def test_resolve_skill_version_under_a_pin_ignores_a_later_host_commit(tmp_path):
    host = _init_pin_host(tmp_path)
    _add_skill_fixture(host, "development-design", version="1.8.0")
    pins_home = tmp_path / "pins"
    pins_home.mkdir()
    made = pin.make(host, pins_home)
    before = commit_builder.resolve_skill_version(str(made.root), "development-design")

    # A commit that touches the very skill directory, landed on the host AFTER the pin was
    # made — must not change what the still-running pinned session resolves.
    (host / ".claude" / "skills" / "development-design" / "SKILL.md").write_text(
        '---\nname: development-design\nmetadata:\n  version: "1.8.0"\n---\n\n# changed\n'
    )
    subprocess.run(
        ["git", "-C", str(host), "add", ".claude/skills/development-design/SKILL.md"],
        check=True, capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "-C", str(host), "commit", "-q", "-m", "post-pin edit"],
        check=True, capture_output=True, text=True,
    )

    after = commit_builder.resolve_skill_version(str(made.root), "development-design")

    assert after == before


def test_resolve_skill_version_under_a_pin_with_no_source_head_returns_none(tmp_path):
    # A pin made from a host that is not a git work tree carries no `source_head` at all — there
    # is nowhere for `_pin_git_source` to resolve a revision from, and it must not guess.
    host = tmp_path / "host"
    _add_skill_fixture_no_git(host, "development-design", version="1.8.0")
    pins_home = tmp_path / "pins"
    pins_home.mkdir()
    made = pin.make(host, pins_home)
    assert made.source_head is None

    assert commit_builder.resolve_skill_version(str(made.root), "development-design") is None


def _add_skill_fixture_no_git(path: Path, name: str, version: str = "1.8.0") -> None:
    """The non-git twin of `_add_skill_fixture` — writes the SKILL.md fixture with no repo at
    all, for the "host was never a git work tree" pin case."""
    skill_dir = path / ".claude" / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        "metadata:\n"
        f'  version: "{version}"\n'
        "---\n\n"
        f"# {name}\n\nFixture only.\n"
    )


def test_resolve_prompt_version_under_a_pin_resolves_against_source_head(tmp_path):
    host = _init_pin_host(tmp_path)
    _add_prompt_fixture(host, "cto_create_srs", version="3.5.0")
    adding_sha = subprocess.run(
        ["git", "-C", str(host), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    pins_home = tmp_path / "pins"
    pins_home.mkdir()
    made = pin.make(host, pins_home)

    result = commit_builder.resolve_prompt_version(str(made.root), "cto_create_srs")

    assert result == f"cto_create_srs@3.5.0 {adding_sha}"


def test_resolve_prompt_version_under_a_pin_ignores_a_later_host_commit(tmp_path):
    host = _init_pin_host(tmp_path)
    _add_prompt_fixture(host, "cto_create_srs", version="3.5.0")
    pins_home = tmp_path / "pins"
    pins_home.mkdir()
    made = pin.make(host, pins_home)
    before = commit_builder.resolve_prompt_version(str(made.root), "cto_create_srs")

    (host / "core" / "prompts" / "cto_create_srs.md").write_text(
        '---\nversion: "3.5.0"\n---\n\n# changed\n'
    )
    subprocess.run(
        ["git", "-C", str(host), "add", "core/prompts/cto_create_srs.md"],
        check=True, capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "-C", str(host), "commit", "-q", "-m", "post-pin edit"],
        check=True, capture_output=True, text=True,
    )

    after = commit_builder.resolve_prompt_version(str(made.root), "cto_create_srs")

    assert after == before


def test_resolve_prompt_version_under_a_pin_with_no_source_head_returns_none(tmp_path):
    host = tmp_path / "host"
    prompts_dir = host / "core" / "prompts"
    prompts_dir.mkdir(parents=True)
    (prompts_dir / "cto_create_srs.md").write_text('---\nversion: "3.5.0"\n---\n\n# x\n')
    pins_home = tmp_path / "pins"
    pins_home.mkdir()
    made = pin.make(host, pins_home)
    assert made.source_head is None

    assert commit_builder.resolve_prompt_version(str(made.root), "cto_create_srs") is None


# ── resolve_prompt_version — the same resolver shape, one directory over ───
# A prompt is a FILE (`core/prompts/<name>.md`) where a skill is a directory,
# so only the SHA read differs; the frontmatter reader is already generic and
# is reused as-is. The flag takes a bare NAME, not a path: --repo is often not
# the instance, and there is exactly one core/prompts/ on the machine, so a
# name has one resolution from anywhere.

def _add_prompt_fixture(path: Path, name: str, version: str | None = "1.4.0") -> None:
    """Create and commit a `core/prompts/<name>.md` fixture inside a throwaway
    repo — the shape `resolve_prompt_version` reads. `version=None` writes
    frontmatter with no `version:` line, for the unresolvable case."""
    prompts_dir = path / "core" / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    version_line = f'version: "{version}"\n' if version is not None else ""
    (prompts_dir / f"{name}.md").write_text(
        "---\n"
        f"{version_line}"
        "---\n\n"
        f"# {name}\n\nFixture only.\n"
    )
    subprocess.run(
        ["git", "-C", str(path), "add", f"core/prompts/{name}.md"],
        check=True, capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "commit", "-q", "-m", f"fixture: add {name} prompt"],
        check=True, capture_output=True, text=True,
    )


def test_resolve_prompt_version_format_and_full_sha(tmp_path):
    _init_repo(tmp_path)
    _add_prompt_fixture(tmp_path, "cto_create_srs", version="3.5.0")

    result = commit_builder.resolve_prompt_version(str(tmp_path), "cto_create_srs")

    # Shape only — name@semver, single space, full-length 40-hex SHA (never
    # abbreviated). Not an exact-version assertion: a fixture prompt's version
    # is arbitrary, and this must not couple to a live prompt's real version.
    assert result is not None
    assert re.match(r"^cto_create_srs@\d+\.\d+\.\d+ [0-9a-f]{40}$", result)


def test_resolve_prompt_version_no_prompt_name_returns_none(tmp_path):
    # Explicit-only, born with the property Skill-Version: had to be corrected
    # into: with no prompt_name the value is None regardless of what prompt
    # sources exist on disk. Nothing is ever inferred from the actor.
    _init_repo(tmp_path)
    _add_prompt_fixture(tmp_path, "cto_create_srs", version="3.5.0")
    assert commit_builder.resolve_prompt_version(str(tmp_path)) is None
    assert commit_builder.resolve_prompt_version(str(tmp_path), None) is None


def test_resolve_prompt_version_unresolvable_returns_none(tmp_path):
    # An explicit prompt_name whose source cannot be read — never fabricate a
    # value, never raise. Two sub-cases: the file absent, and the file present
    # but carrying no version: line.
    _init_repo(tmp_path)

    # (a) prompt source entirely absent
    assert commit_builder.resolve_prompt_version(str(tmp_path), "cto_create_srs") is None

    # (b) prompt present, no version: line in its frontmatter
    _add_prompt_fixture(tmp_path, "cto_create_srs", version=None)
    assert commit_builder.resolve_prompt_version(str(tmp_path), "cto_create_srs") is None


def test_resolve_prompt_version_uncommitted_source_returns_none(tmp_path):
    # The third unresolvable sub-case: the prompt is present AND carries a
    # version: line, but has no committed revision. The semver resolves from
    # disk, but there is no source SHA — so the value is None. Pins the
    # `sha is None` branch the other two sub-cases stop short of.
    _init_repo(tmp_path)
    prompts_dir = tmp_path / "core" / "prompts"
    prompts_dir.mkdir(parents=True)
    (prompts_dir / "cto_create_srs.md").write_text('---\nversion: "3.5.0"\n---\n\n# x\n')
    # Deliberately NOT staged/committed.
    assert commit_builder.resolve_prompt_version(str(tmp_path), "cto_create_srs") is None


def test_resolve_prompt_version_names_the_prompt_not_another(tmp_path):
    # Two prompts on disk, so a wrong resolution would still find *a* prompt —
    # the assertion pins the NAME, catching resolution of the wrong one.
    _init_repo(tmp_path)
    _add_prompt_fixture(tmp_path, "cto_create_srs", version="3.5.0")
    _add_prompt_fixture(tmp_path, "declare_loader_domain", version="1.0.0")

    result = commit_builder.resolve_prompt_version(str(tmp_path), "declare_loader_domain")

    assert result is not None
    assert result.startswith("declare_loader_domain@"), result


def test_resolve_prompt_version_sha_tracks_the_prompt_not_head(tmp_path):
    # The SHA is the prompt file's last-modifying commit, never repo HEAD —
    # HEAD moves on every commit and would carry no drift signal. Commit
    # something unrelated afterwards and the value must not move.
    _init_repo(tmp_path)
    _add_prompt_fixture(tmp_path, "cto_create_srs", version="3.5.0")
    before = commit_builder.resolve_prompt_version(str(tmp_path), "cto_create_srs")

    (tmp_path / "unrelated.txt").write_text("unrelated\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "unrelated.txt"],
                   check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "unrelated"],
                   check=True, capture_output=True, text=True)

    after = commit_builder.resolve_prompt_version(str(tmp_path), "cto_create_srs")
    head = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    assert after == before
    assert after is not None and not after.endswith(head)


# ── a prompt that lives inside a skill folder — `<skill>/<prompt>` ─────────
# The slash selects it: the skill resolves through skill_path, the prompt is
# `<skill dir>/prompts/<prompt>.md`. A bare name keeps core/prompts/ exactly.

def _commit_all(path: Path, message: str) -> str:
    subprocess.run(["git", "-C", str(path), "add", "-A"],
                   check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(path), "commit", "-q", "-m", message],
                   check=True, capture_output=True, text=True)
    return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()


def _add_skill_prompt_fixture(path: Path, skill: str, prompt: str, version: str = "1.0.0") -> str:
    skill_dir = path / ".claude" / "skills" / skill
    (skill_dir / "prompts").mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f'---\nname: {skill}\nmetadata:\n  version: "2.0.0"\n---\n\n# {skill}\n'
    )
    (skill_dir / "prompts" / f"{prompt}.md").write_text(
        f'---\nversion: "{version}"\n---\n\nFixture only.\n'
    )
    return _commit_all(path, f"fixture: add {skill}/{prompt}")


def test_resolve_prompt_version_skill_folder_prompt(tmp_path):
    _init_repo(tmp_path)
    sha = _add_skill_prompt_fixture(tmp_path, "nemo", "thin", version="1.0.0")

    assert commit_builder.resolve_prompt_version(str(tmp_path), "nemo/thin") == f"nemo/thin@1.0.0 {sha}"


def test_resolve_prompt_version_skill_folder_sha_tracks_the_prompt_not_the_skill(tmp_path):
    _init_repo(tmp_path)
    sha = _add_skill_prompt_fixture(tmp_path, "nemo", "thin")
    (tmp_path / ".claude" / "skills" / "nemo" / "SKILL.md").write_text("---\nname: nemo\n---\nchanged\n")
    _commit_all(tmp_path, "edit the skill, not the prompt")

    assert commit_builder.resolve_prompt_version(str(tmp_path), "nemo/thin") == f"nemo/thin@1.0.0 {sha}"


def test_resolve_prompt_version_bare_name_never_reaches_a_skill_folder(tmp_path):
    _init_repo(tmp_path)
    _add_skill_prompt_fixture(tmp_path, "nemo", "thin")

    assert commit_builder.resolve_prompt_version(str(tmp_path), "thin") is None


@pytest.mark.parametrize("name", ["ghost/thin", "nemo/absent", "nemo/", "/thin", "nemo/thin/extra"])
def test_resolve_prompt_version_skill_folder_unresolvable_returns_none(tmp_path, name):
    _init_repo(tmp_path)
    _add_skill_prompt_fixture(tmp_path, "nemo", "thin")

    assert commit_builder.resolve_prompt_version(str(tmp_path), name) is None


def test_actor_skill_map_is_deleted():
    # The actor->skill derivation is retired; provenance is explicit --skill
    # only. The map's continued existence would mean the derivation could be
    # reintroduced silently, so its absence is asserted directly.
    assert not hasattr(commit_builder, "ACTOR_SKILL")


# ── every producing skill NAME resolves when passed explicitly ──────────────
# The producing skills the pipeline records provenance for (the six change-pipeline
# stages + the two executive-tier skills product-prd, product-srs).
# This replaces the retired actor->skill derivation coverage: there is no
# ACTOR_SKILL map to mistype now, so what remains worth pinning is that each
# producing skill NAME resolves to a well-formed value when named explicitly.
# The list is hard-coded from the spec (deliberately not read off any module
# map) so it stays a real, independent assertion of the resolver's shape.
PRODUCING_SKILLS = [
    "product-prd",
    "product-srs",
    "development-specs",
    "development-design",
    "development-plan",
    "development-implementation",
    "development-code-integrity",
    "development-audit",
]


@pytest.mark.parametrize("skill_name", PRODUCING_SKILLS)
def test_each_producing_skill_name_resolves(tmp_path, skill_name):
    _init_repo(tmp_path)
    _add_skill_fixture(tmp_path, skill_name, version="1.0.0")
    result = commit_builder.resolve_skill_version(str(tmp_path), skill_name)
    assert result is not None, (
        f"producing skill {skill_name!r} did not resolve to a value"
    )
    assert result.startswith(f"{skill_name}@")


# ── the resolver tracks the NAMED skill, not another present on disk ─────────
# Two producing skills exist on disk; the resolver must resolve the NAMED one,
# never whichever it happens to find. (Formerly framed as "explicit --skill
# overrides the actor default"; the actor derivation is retired, so what remains
# worth pinning is that the value tracks the passed name exactly.)

def test_resolve_skill_version_resolves_named_skill_not_another(tmp_path):
    _init_repo(tmp_path)
    _add_skill_fixture(tmp_path, "product-srs", version="2.0.0")
    _add_skill_fixture(tmp_path, "product-sdd-write", version="1.0.0")
    result = commit_builder.resolve_skill_version(str(tmp_path), "product-sdd-write")
    assert result is not None
    assert result.startswith("product-sdd-write@")
    assert re.match(r"^product-sdd-write@\d+\.\d+\.\d+ [0-9a-f]{40}$", result)


def test_resolve_skill_version_named_skill_unresolvable_returns_none(tmp_path):
    # A named skill whose source can't be read is None — never a fabrication,
    # and never a fall-back to some other skill that happens to exist on disk.
    _init_repo(tmp_path)
    _add_skill_fixture(tmp_path, "product-srs", version="2.0.0")  # a different skill, present
    assert commit_builder.resolve_skill_version(
        str(tmp_path), "product-sdd-write"
    ) is None


def test_resolve_skill_version_sha_tracks_skill_source_not_head(tmp_path):
    # The SHA must identify the SKILL's source revision, not the repo HEAD.
    # The intent's drift signal ("version didn't bump but SHA changed") only
    # works if the SHA moves with the skill's own source and stays put on
    # unrelated commits — a repo-HEAD SHA would change on every commit and
    # carry no signal. Commit the skill fixture (capture its commit), then make
    # an UNRELATED commit that moves HEAD without touching the skill source;
    # the resolved SHA must still be the skill's commit, never the new HEAD.
    _init_repo(tmp_path)
    _add_skill_fixture(tmp_path, "development-design", version="1.8.0")

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    skill_sha = git("rev-parse", "HEAD")
    (tmp_path / "unrelated.txt").write_text("unrelated\n")
    git("add", "unrelated.txt")
    git("commit", "-q", "-m", "unrelated: move HEAD without touching the skill")
    head_sha = git("rev-parse", "HEAD")
    assert skill_sha != head_sha  # sanity: HEAD really moved past the skill commit

    result = commit_builder.resolve_skill_version(str(tmp_path), "development-design")
    assert result == f"development-design@1.8.0 {skill_sha}"
    assert not result.endswith(head_sha)


# ── actor -> Role derivation via AGENT_ROLE ─────────────────────────────────

@pytest.mark.parametrize("actor,role", commit_builder.AGENT_ROLE.items())
def test_role_derived_from_actor_via_agent_role(actor, role):
    message = commit_builder.build_message(
        "commit",
        subject="work",
        actor=actor,
        directional="Shukuba: proto — progress: x",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
    )
    assert f"Role: {role}" in message


def test_role_derived_without_hook_payload():
    # No agent_type / hook payload anywhere in this call — the explicit actor
    # argument alone drives the derivation (the request's crux).
    message = commit_builder.build_message(
        "commit",
        subject="work",
        actor="tech-lead",
        directional="Shukuba: proto — progress: x",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
    )
    assert "Role: Tech Lead" in message


def test_unknown_actor_refuses_to_build():
    with pytest.raises(commit_builder.UnknownActorError):
        commit_builder.build_message(
            "commit",
            subject="work",
            actor="some-future-agent",
            directional="Shukuba: proto — progress: x",
            surface="Claude Code",
            co_authored_by=CO_AUTHORED_BY,
        )


def test_unknown_actor_cli_exits_nonzero(tmp_path):
    # Coverage add (Step 1b): the CLI-level refusal path, not just the raise.
    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "work",
        "--actor", "some-future-agent",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])
    assert exit_code != 0


# ── interactive --role: Role: supplied verbatim, no actor derivation ────────

def test_role_used_verbatim_when_given():
    # An interactive caller (shukuba-park) has no subagent identity — it
    # passes its posture Role: directly. "Product" is not an AGENT_ROLE value
    # (that map has "Product Owner"), so this also proves the value bypasses
    # derivation entirely rather than being mapped.
    message = commit_builder.build_message(
        "commit",
        subject="retire: shukuba/thing → trail/",
        role="Product",
        directional="Shukuba: thing — progress: reached, retired to trail",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
    )
    assert "Role: Product" in message


def test_role_flag_lands_verbatim_through_cli(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "retire: shukuba/thing → trail/",
        "--role", "Product",
        "--add", "work.txt",
        "--directional", "Shukuba: thing — progress: reached, retired to trail",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    trailer_block = _commit_body(tmp_path).strip().split("\n\n")[-1]
    assert trailer_block.splitlines() == [
        "Shukuba: thing — progress: reached, retired to trail",
        "Role: Product",
        "Surface: Claude Code",
        f"Co-Authored-By: {CO_AUTHORED_BY}",
    ]


def test_actor_and_role_are_mutually_exclusive(tmp_path):
    # The CLI forbids passing both — exactly one identity channel.
    with pytest.raises(SystemExit):
        commit_builder.main([
            "--repo", str(tmp_path),
            "commit",
            "--subject", "work",
            "--actor", "pm",
            "--role", "Product",
            "--directional", "Shukuba: x — none — y",
            "--surface", "Claude Code",
            "--co-authored-by", CO_AUTHORED_BY,
        ])


def test_neither_actor_nor_role_errors(tmp_path):
    # The identity group is required — omitting both is a CLI error.
    with pytest.raises(SystemExit):
        commit_builder.main([
            "--repo", str(tmp_path),
            "commit",
            "--subject", "work",
            "--directional", "Shukuba: x — none — y",
            "--surface", "Claude Code",
            "--co-authored-by", CO_AUTHORED_BY,
        ])


# ── merge block replaces Role:/directional with Merge-Authorized: ──────────

def test_merge_block_replaces_role_and_directional_with_merge_authorized():
    message = commit_builder.build_message(
        "merge",
        actor="pm",
        branch="2026-07-07_commit-builder",
        target_branch="main",
        description="build the one commit builder",
        branch_commits=["abc1234 developer: task 1", "def5678 developer: task 2"],
        merge_context="/development 2026-07-07_commit-builder (PoC: green suite)",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
    )
    assert message.startswith(
        "merge: 2026-07-07_commit-builder → main — build the one commit builder"
    )
    assert "-> abc1234 developer: task 1" in message
    assert "-> def5678 developer: task 2" in message
    # The `pm` merge actor derives `Merge-Authorized: PM` (automated seal, no
    # human gate); the caller-supplied context follows the ` — ` separator.
    assert (
        "Merge-Authorized: PM — /development 2026-07-07_commit-builder (PoC: green suite)"
        in message
    )
    assert "Role:" not in message
    assert "Shukuba:" not in message
    assert "Michi:" not in message


# ── merge authorizer derived from the merge actor via MERGE_AUTHORIZER ──────

@pytest.mark.parametrize("actor,authorizer", commit_builder.MERGE_AUTHORIZER.items())
def test_merge_authorizer_derived_from_actor(actor, authorizer):
    message = commit_builder.build_message(
        "merge",
        actor=actor,
        branch="feature",
        target_branch="main",
        description="thing",
        branch_commits=["abc1234 do the thing"],
        merge_context="/development <key> (PoC: green suite)",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
    )
    assert f"Merge-Authorized: {authorizer} — /development <key> (PoC: green suite)" in message


def test_an_interactive_merge_may_be_authorized_by_product():
    # The merge path had no equivalent of the commit path's `--role`: a merge the owner directed
    # could only be recorded by borrowing an actor that did not do the authorizing. Doctrine already
    # named the value — commit_format.md: "a future interactive, human-gated merge would derive
    # Merge-Authorized: Product".
    message = commit_builder.build_message(
        "merge",
        authorizer="Product",
        branch="feature",
        target_branch="main",
        description="thing",
        branch_commits=["abc1234 do the thing"],
        merge_context="owner-directed",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
    )
    assert "Merge-Authorized: Product — owner-directed" in message


def test_the_interactive_authorizer_is_a_closed_set_not_a_free_string():
    # `--role` on the commit path is verbatim and unvalidated, and that is fine there. Here it is not:
    # MERGE_AUTHORIZER's entire value is being a closed, deliberately narrow list, and an unchecked
    # verbatim flag would dissolve that in one argument — any caller could write anything.
    with pytest.raises(commit_builder.UnknownActorError):
        commit_builder.build_message(
            "merge",
            authorizer="Supreme Overlord",
            branch="feature",
            target_branch="main",
            description="thing",
            branch_commits=[],
            merge_context="ctx",
            surface="Claude Code",
            co_authored_by=CO_AUTHORED_BY,
        )


def test_product_is_on_the_interactive_axis_not_the_actor_axis():
    # Why `Product` is not simply a MERGE_AUTHORIZER row: that table is keyed by subagent agent_type
    # and its rows must be spelled as that actor's own Role. There is no `product` agent. Putting it
    # there would break the strict-subset property below, which is the thing carrying the policy.
    assert "Product" in commit_builder.INTERACTIVE_MERGE_AUTHORIZERS
    assert "product" not in commit_builder.MERGE_AUTHORIZER
    assert "product" not in commit_builder.AGENT_ROLE


def test_merge_authorizer_is_narrower_than_agent_role():
    # The table's meaning is in what it omits, and an omission has no line to read — without this
    # test, a deliberate exclusion is indistinguishable from someone forgetting a row, and the next
    # person to hit `UnknownActorError` "fixes" it by adding the actor.
    #
    # Every merge authorizer must also be a valid commit actor (one vocabulary, no second spelling),
    # but the reverse must NOT hold: the set of identities that may authorize a merge to main is
    # deliberately smaller than the set that may author a commit.
    assert set(commit_builder.MERGE_AUTHORIZER) < set(commit_builder.AGENT_ROLE), (
        "MERGE_AUTHORIZER must be a strict subset of AGENT_ROLE — if it grew to match, the table "
        "stopped expressing a policy and became duplication"
    )
    for actor, authorizer in commit_builder.MERGE_AUTHORIZER.items():
        assert commit_builder.AGENT_ROLE[actor] == authorizer, (
            f"{actor!r} spells its authorizer differently from its Role — one identity, one name"
        )


def test_cdo_is_a_commit_actor_but_not_a_merge_authorizer():
    # The CDO is an executive-tier originator — it authors the UXD and the design language, so it
    # commits under its own Role the way CPO and CTO do. It does not merge: merging to main is
    # `tobiishi-seal`'s terminal step, run as `pm`. Pinned explicitly because the parametrized
    # AGENT_ROLE test would pass for any spelling of the value, and because the exclusion from
    # MERGE_AUTHORIZER is a policy an omission cannot state on its own.
    assert commit_builder.AGENT_ROLE["cdo"] == "CDO"
    assert "cdo" not in commit_builder.MERGE_AUTHORIZER


def test_content_manager_commit_standing():
    # A delivery-tier originator: it owns the product's words and authors CONTENT.md, so it commits
    # under its own Role. It does not merge — merging to main is `tobiishi-seal`'s terminal step, run
    # as `pm`. Pinned explicitly for the same two reasons as the CDO above, plus one of its own: the
    # key is the agent's `name:`, which is hyphenated, while this role's loader filenames are
    # underscored. A key spelled `content_manager` here would look right and raise at the commit step.
    assert commit_builder.AGENT_ROLE["content-manager"] == "Content Manager"
    assert "content-manager" not in commit_builder.MERGE_AUTHORIZER


def test_content_editor_commit_standing():
    # A delivery-tier originator: it writes the text one change publishes, so it commits under its
    # own Role. It may author a commit and may not authorize a merge — merging to main is
    # `tobiishi-seal`'s terminal step, run as `pm`. Pinned explicitly because the parametrized
    # AGENT_ROLE test would pass for any spelling of the value. The key is the agent's hyphenated
    # `name:`, while this role's loader filenames are underscored; a key spelled `content_editor`
    # would look right and raise at the commit step.
    assert commit_builder.AGENT_ROLE["content-editor"] == "Content Editor"
    assert "content-editor" not in commit_builder.MERGE_AUTHORIZER


def test_a_content_editor_merge_refuses_to_build():
    # The refusal itself, not only the table's omission: a merge built as `content-editor` must
    # raise before any message exists. The membership test above would stay green if the merge path
    # ever fell back to AGENT_ROLE for an actor it cannot find.
    with pytest.raises(commit_builder.UnknownActorError):
        commit_builder.build_message(
            "merge",
            actor="content-editor",
            branch="feature",
            target_branch="main",
            description="thing",
            branch_commits=["abc1234 do the thing"],
            merge_context="ctx",
            surface="Claude Code",
            co_authored_by=CO_AUTHORED_BY,
        )


def test_a_content_editor_commit_lands_its_role_through_the_cli(tmp_path):
    # The seat is committable end to end: the CLI, not only build_message, lands a real commit
    # whose trailer names the seat — the spec's own scratch-repo example.
    _init_repo(tmp_path)

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "content-editor: the change's text",
        "--actor", "content-editor",
        "--allow-empty",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    assert "Role: Content Editor" in _commit_body(tmp_path).splitlines()


def test_a_content_editor_merge_is_refused_through_the_cli(tmp_path, capsys):
    # The refusal as the spec states it: the exact line on stderr, exit 1, and no merge made.
    main_branch = _init_repo(tmp_path)

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args], capture_output=True, text=True, check=True,
        ).stdout.strip()

    git("checkout", "-qb", "feature")
    git("commit", "-q", "--allow-empty", "-m", "feature: work")
    git("checkout", "-q", main_branch)
    head_before = git("rev-parse", "HEAD")
    argv = _merge_argv(tmp_path, main_branch)
    argv[argv.index("--actor") + 1] = "content-editor"
    bump = argv.index("--bump")
    del argv[bump:bump + 2]

    exit_code = commit_builder.main(argv)

    assert exit_code == 1
    assert capsys.readouterr().err.strip() == (
        "commit_builder: unknown merge actor 'content-editor' has no MERGE_AUTHORIZER mapping — "
        "refusing to build a merge with no derivable Merge-Authorized:"
    )
    assert git("rev-parse", "HEAD") == head_before  # no merge was made
    assert not (tmp_path / ".git" / "MERGE_HEAD").exists()


def test_scrum_master_is_a_commit_actor_but_not_a_merge_authorizer():
    # A delivery-tier process seat, so it commits under its own Role like the CDO and Content
    # Manager above. It does not merge —
    # merging to main is `tobiishi-seal`'s terminal step, run as `pm`. Pinned explicitly for the
    # same two reasons as those two: the parametrized AGENT_ROLE test would pass for any spelling
    # of the value, and the exclusion from MERGE_AUTHORIZER is a policy an omission cannot state
    # on its own. The key is the agent's hyphenated `name:` ("scrum-master"), while this role's
    # loader filenames are underscored ("scrum_master_global.md").
    assert commit_builder.AGENT_ROLE["scrum-master"] == "Scrum Master"
    assert "scrum-master" not in commit_builder.MERGE_AUTHORIZER


def test_a_scrum_master_merge_refuses_to_build():
    # The refusal itself, not only the table's omission: a merge built as `scrum-master` must raise
    # before any message exists. The membership test above would stay green if the merge path ever
    # fell back to AGENT_ROLE for an actor it cannot find.
    with pytest.raises(commit_builder.UnknownActorError):
        commit_builder.build_message(
            "merge",
            actor="scrum-master",
            branch="feature",
            target_branch="main",
            description="thing",
            branch_commits=["abc1234 do the thing"],
            merge_context="ctx",
            surface="Claude Code",
            co_authored_by=CO_AUTHORED_BY,
        )


def test_a_developer_may_not_authorize_a_merge():
    # The specific exclusion the table exists to state: a developer does not merge its own branch.
    # The senior-engineer runs development-code-integrity over it and merges on that pass. If this
    # test ever fails because `developer` was added, the worker/reviewer split has been dissolved in
    # a one-line data change — which is exactly how it would happen.
    assert "developer" in commit_builder.AGENT_ROLE, "developer must remain a valid commit actor"
    assert "developer" not in commit_builder.MERGE_AUTHORIZER

    with pytest.raises(commit_builder.UnknownActorError):
        commit_builder.build_message(
            "merge",
            actor="developer",
            branch="feature",
            target_branch="main",
            description="thing",
            branch_commits=["abc1234 do the thing"],
            merge_context="ctx",
            surface="Claude Code",
            co_authored_by=CO_AUTHORED_BY,
        )


def test_unknown_merge_actor_refuses_to_build():
    with pytest.raises(commit_builder.UnknownActorError):
        commit_builder.build_message(
            "merge",
            actor="architect",  # a valid commit actor, but no merge authorizer
            branch="feature",
            target_branch="main",
            description="thing",
            branch_commits=["abc1234 do the thing"],
            merge_context="manual",
            surface="Claude Code",
            co_authored_by=CO_AUTHORED_BY,
        )


# ── one code path serves both ops ───────────────────────────────────────────

def test_one_code_path_serves_commit_and_merge():
    commit_message = commit_builder.build_message(
        "commit",
        subject="work",
        actor="developer",
        directional="Shukuba: proto — progress: x",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
    )
    merge_message = commit_builder.build_message(
        "merge",
        actor="pm",
        branch="feature",
        target_branch="main",
        description="thing",
        branch_commits=["abc1234 do the thing"],
        merge_context="manual",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
    )
    assert "Role: Developer" in commit_message
    assert "Merge-Authorized: PM — manual" in merge_message
    # Guard against a future fork into two separate builder functions — the
    # Complex-task hint requires one entry point, op-parameterized, not two.
    assert not hasattr(commit_builder, "build_commit_message")
    assert not hasattr(commit_builder, "build_merge_message")


# ── CLI smoke (Task 1 verification gate) ────────────────────────────────────

def test_help_exits_cleanly():
    proc = subprocess.run(
        [sys.executable, str(BUILDER), "--help"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "usage" in proc.stdout.lower()


# ── the builder RUNS the git op (execution half, both ops) ──────────────────
# Intent: change_spec §Request/§Structural Goal + tl_instruction §Task 1 —
# "one code path serves both `git commit` and `git merge --no-ff` … and runs
# the git op." The assembly tests above pin the *message*; these pin that the
# builder actually invokes git end-to-end and the constructed commit/merge
# lands with the canonical trailers. This is also the verifiable proof-of-done
# (a real commit constructed *through* the builder), which prose assertion
# alone could not give a downstream reader.

def _init_repo(path: Path) -> str:
    """Init a throwaway git repo with a first commit; return its branch name."""
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    git("init", "-q")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.com")
    git("config", "commit.gpgsign", "false")
    (path / "seed.txt").write_text("seed\n")
    # An instance's identity: what makes the tree's `core/`, `.claude/`,
    # `skills/` and `system/` kensaiapp's own artifacts (`_is_kensaiapp_path`).
    (path / "kensaiapp.md").write_text("# throwaway instance\n")
    git("add", "seed.txt", "kensaiapp.md")
    git("commit", "-q", "-m", "seed")
    return git("rev-parse", "--abbrev-ref", "HEAD")


def _commit_body(path: Path, ref: str = "HEAD") -> str:
    return subprocess.run(
        ["git", "-C", str(path), "log", "-1", "--format=%B", ref],
        capture_output=True, text=True, check=True,
    ).stdout


def test_commit_op_runs_git_and_lands_canonical_trailers(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    # main() resolves Skill-Version against the instance repo (where the skill
    # source lives), never --repo. Pin it to the throwaway repo so this test
    # stays hermetic: tmp_path carries no .claude/skills/, so a producing actor
    # still resolves to None and the 4-line trailer block holds.
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: real commit through the builder",
        "--body", "Proof the builder runs the git op.",
        "--actor", "developer",
        "--add", "work.txt",
        "--directional", "Shukuba: commit-builder — progress: builds it",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    body = _commit_body(tmp_path)
    trailer_block = body.strip().split("\n\n")[-1]
    assert trailer_block.splitlines() == [
        "Shukuba: commit-builder — progress: builds it",
        "Role: Developer",
        "Surface: Claude Code",
        f"Co-Authored-By: {CO_AUTHORED_BY}",
    ]


def test_commit_op_allow_empty_makes_empty_marker_commit(tmp_path, monkeypatch):
    # development-implementation's closing commit is an empty marker
    # (`git commit --allow-empty`) — nothing staged. The builder must be able
    # to make it, so every producer (implementation included) routes through
    # the one builder. Without --allow-empty git refuses an empty commit.
    _init_repo(tmp_path)  # clean tree, nothing staged
    # Pin skill resolution to the throwaway repo (see the note above) — no
    # .claude/skills/ here, so the marker commit stays at the 4-line block.
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: <key> — implementation complete",
        "--body", "Developer Review Notes: none.",
        "--actor", "developer",
        "--directional", "Shukuba: proto — progress: closing marker",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
        "--allow-empty",
    ])

    assert exit_code == 0
    # An empty commit: its tree equals its parent's — no file changes.
    diff = subprocess.run(
        ["git", "-C", str(tmp_path), "diff", "--stat", "HEAD~1", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert diff == ""
    trailer_block = _commit_body(tmp_path).strip().split("\n\n")[-1]
    assert trailer_block.splitlines() == [
        "Shukuba: proto — progress: closing marker",
        "Role: Developer",
        "Surface: Claude Code",
        f"Co-Authored-By: {CO_AUTHORED_BY}",
    ]


def test_commit_op_without_allow_empty_refuses_empty_commit(tmp_path):
    # The flag is opt-in: without it, an empty tree still refuses (git's
    # default), so the marker-commit capability can't fire by accident.
    _init_repo(tmp_path)  # clean tree, nothing staged

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "work",
        "--actor", "developer",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0


def _feature_repo_with_versioned_file(tmp_path: Path, version: str = "1.0.0") -> Path:
    _init_repo(tmp_path)
    subprocess.run(
        ["git", "-C", str(tmp_path), "branch", "-M", "main"], check=True
    )
    target = tmp_path / "core/versioned.py"
    target.parent.mkdir(exist_ok=True)
    target.write_text(f'__version__ = "{version}"\n', encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "core/versioned.py"], check=True
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "add versioned file"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "checkout", "-q", "-b", "feature"],
        check=True,
    )
    return target


def _product_commit(repo: Path, *paths: str) -> int:
    return commit_builder.main([
        "--repo", str(repo),
        "commit",
        "--subject", "product: change the artifact",
        "--role", "Product",
        "--directional", "Michi: none — exercise the branch marker gate",
        "--surface", "Codex",
        "--add", *paths,
    ])


def test_feature_commit_refuses_an_existing_artifact_version_bump(
    tmp_path, capsys
):
    target = _feature_repo_with_versioned_file(tmp_path)
    target.write_text('__version__ = "1.1.0"\n', encoding="utf-8")
    head_before = _base_sha(tmp_path)

    exit_code = _product_commit(tmp_path, "core/versioned.py")

    assert exit_code == 1
    assert _base_sha(tmp_path) == head_before
    error = capsys.readouterr().err
    assert "version markers move only in the landing commit on main" in error
    assert "core/versioned.py: 1.0.0 -> 1.1.0" in error


def test_feature_commit_allows_content_change_with_an_unchanged_marker(tmp_path):
    target = _feature_repo_with_versioned_file(tmp_path)
    target.write_text(
        '"""Changed behaviour."""\n__version__ = "1.0.0"\n',
        encoding="utf-8",
    )

    exit_code = _product_commit(tmp_path, "core/versioned.py")

    assert exit_code == 0


def test_feature_commit_allows_a_new_artifact_at_creation_version(tmp_path):
    _feature_repo_with_versioned_file(tmp_path)
    added = tmp_path / "core/added.py"
    added.write_text('__version__ = "1.0.0"\n', encoding="utf-8")

    exit_code = _product_commit(tmp_path, "core/added.py")

    assert exit_code == 0


def test_feature_commit_refuses_a_new_artifact_above_creation_version(
    tmp_path, capsys
):
    _feature_repo_with_versioned_file(tmp_path)
    added = tmp_path / "core/added.py"
    added.write_text('__version__ = "1.2.0"\n', encoding="utf-8")

    exit_code = _product_commit(tmp_path, "core/added.py")

    assert exit_code == 1
    assert "new artifact starts at 1.0.0, found 1.2.0" in capsys.readouterr().err


def test_feature_commit_preserves_a_renamed_artifacts_existing_version(tmp_path):
    target = _feature_repo_with_versioned_file(tmp_path, version="2.3.0")
    renamed = tmp_path / "core/renamed.py"
    subprocess.run(
        ["git", "-C", str(tmp_path), "mv", "core/versioned.py", "core/renamed.py"], check=True
    )

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "product: rename the artifact",
        "--role", "Product",
        "--directional", "Michi: none — exercise the branch marker gate",
        "--surface", "Codex",
        "--staged", "core/versioned.py", "core/renamed.py",
    ])

    assert exit_code == 0


def test_feature_commit_is_not_refused_for_a_bump_main_made_meanwhile(tmp_path):
    """The branch is merely behind. On 2026-09-22 this refused every commit on a live change
    branch — including its empty pause commits — whenever another session landed a bump in a file
    the branch never opened, and the runs answered by rebasing mid-walk (seven times in one walk).
    The guard judges what the branch itself changed, which is nothing here."""
    target = _feature_repo_with_versioned_file(tmp_path)
    subprocess.run(["git", "-C", str(tmp_path), "checkout", "-q", "main"], check=True)
    target.write_text('__version__ = "1.1.0"\n', encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-qam", "main: bump"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "checkout", "-q", "feature"], check=True)
    untouched = tmp_path / "other.py"
    untouched.write_text("print('branch work')\n", encoding="utf-8")

    exit_code = _product_commit(tmp_path, "other.py")

    assert exit_code == 0


def test_feature_commit_still_refuses_its_own_bump_while_main_moved(tmp_path, capsys):
    target = _feature_repo_with_versioned_file(tmp_path)
    subprocess.run(["git", "-C", str(tmp_path), "checkout", "-q", "main"], check=True)
    target.write_text('__version__ = "1.1.0"\n', encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-qam", "main: bump"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "checkout", "-q", "feature"], check=True)
    target.write_text('__version__ = "9.9.9"\n', encoding="utf-8")

    exit_code = _product_commit(tmp_path, "core/versioned.py")

    assert exit_code == 1
    assert "1.0.0 -> 9.9.9" in capsys.readouterr().err


def test_main_commit_may_move_a_marker_directly(tmp_path):
    target = _feature_repo_with_versioned_file(tmp_path)
    subprocess.run(
        ["git", "-C", str(tmp_path), "checkout", "-q", "main"], check=True
    )
    target.write_text('__version__ = "1.1.0"\n', encoding="utf-8")

    exit_code = _product_commit(tmp_path, "core/versioned.py")

    assert exit_code == 0


def test_merge_op_runs_git_no_ff_and_creates_merge_commit(tmp_path):
    main_branch = _init_repo(tmp_path)

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    git("checkout", "-q", "-b", "feature")
    (tmp_path / "feature.txt").write_text("feature\n")
    git("add", "feature.txt")
    git("commit", "-q", "-m", "feature: add a thing")
    git("checkout", "-q", main_branch)

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "merge",
        "--branch", "feature",
        "--target-branch", main_branch,
        "--description", "bring in the feature",
        "--branch-commits", "feature: add a thing",
        "--actor", "pm",
        "--merge-context", "manual",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    # A real --no-ff merge commit: two parents.
    parents = git("rev-list", "--parents", "-n", "1", "HEAD").split()
    assert len(parents) == 3  # self + two parents
    body = _commit_body(tmp_path)
    assert body.startswith(f"merge: feature → {main_branch} — bring in the feature")
    assert "-> feature: add a thing" in body
    assert "Merge-Authorized: PM — manual" in body
    assert "Role:" not in body
    assert "Shukuba:" not in body


# ── Codex model attribution — real commit and merge carry the assigned model ─
# `codex-assigned-model-attribution` changes what the runtime hands the
# builder, never the builder itself: `build_message` already places a
# caller-supplied `co_authored_by` in canonical order for both operations
# (§ Blast Radius). These prove a concrete Codex model reaches a real commit
# and a real merge unchanged, alongside the retained Claude and model-less
# real-operation paths and the staged-set guard.

def test_codex_model_commit_lands_canonical_trailers(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: real commit through the builder",
        "--body", "Proof a Codex model reaches a real commit.",
        "--actor", "developer",
        "--add", "work.txt",
        "--directional", "Shukuba: commit-builder — progress: builds it",
        "--surface", "Codex",
        "--co-authored-by", "gpt-5.6-terra <noreply@openai.com>",
    ])

    assert exit_code == 0
    body = _commit_body(tmp_path)
    assert body.count("Surface: Codex") == 1
    assert body.count("Co-Authored-By: gpt-5.6-terra <noreply@openai.com>") == 1
    trailer_block = body.strip().split("\n\n")[-1]
    assert trailer_block.splitlines() == [
        "Shukuba: commit-builder — progress: builds it",
        "Role: Developer",
        "Surface: Codex",
        "Co-Authored-By: gpt-5.6-terra <noreply@openai.com>",
    ]


def test_codex_model_merge_lands_canonical_trailers(tmp_path):
    main_branch = _init_repo(tmp_path)

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    git("checkout", "-q", "-b", "feature")
    (tmp_path / "feature.txt").write_text("feature\n")
    git("add", "feature.txt")
    git("commit", "-q", "-m", "feature: add a thing")
    git("checkout", "-q", main_branch)

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "merge",
        "--branch", "feature",
        "--target-branch", main_branch,
        "--description", "bring in the feature",
        "--branch-commits", "feature: add a thing",
        "--actor", "pm",
        "--merge-context", "manual",
        "--surface", "Codex",
        "--co-authored-by", "gpt-5.6-sol <noreply@openai.com>",
    ])

    assert exit_code == 0
    parents = git("rev-list", "--parents", "-n", "1", "HEAD").split()
    assert len(parents) == 3  # self + two parents
    body = _commit_body(tmp_path)
    assert body.count("Surface: Codex") == 1
    assert body.count("Co-Authored-By: gpt-5.6-sol <noreply@openai.com>") == 1
    trailer_lines = body.strip().splitlines()
    merge_line = next(i for i, line in enumerate(trailer_lines)
                       if line.startswith("Merge-Authorized:"))
    assert trailer_lines[merge_line + 1] == "Surface: Codex"
    assert trailer_lines[merge_line + 2] == "Co-Authored-By: gpt-5.6-sol <noreply@openai.com>"


def test_claude_and_model_less_builder_paths_remain_unchanged(tmp_path, monkeypatch):
    main_branch = _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)

    # A real Claude-attributed commit keeps its supplied attribution.
    (tmp_path / "work.txt").write_text("work\n")
    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: real commit through the builder",
        "--actor", "developer",
        "--add", "work.txt",
        "--directional", "Shukuba: commit-builder — progress: builds it",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])
    assert exit_code == 0
    assert f"Co-Authored-By: {CO_AUTHORED_BY}" in _commit_body(tmp_path)

    # A real deterministic (model-less) commit still carries no
    # `Co-Authored-By:` at all.
    (tmp_path / "deterministic.txt").write_text("no model\n")
    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "skeleton: the frame",
        "--role", "Product",
        "--add", "deterministic.txt",
        "--directional", "Agari: example-product — progress: it",
        "--surface", "product-skeleton",
    ])
    assert exit_code == 0
    assert "Co-Authored-By:" not in _commit_body(tmp_path)

    # A real deterministic (model-less) merge also carries no line.
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    git("checkout", "-q", "-b", "feature")
    (tmp_path / "feature.txt").write_text("feature\n")
    git("add", "feature.txt")
    git("commit", "-q", "-m", "feature: add a thing")
    git("checkout", "-q", main_branch)

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "merge",
        "--branch", "feature",
        "--target-branch", main_branch,
        "--description", "bring in the feature",
        "--branch-commits", "feature: add a thing",
        "--actor", "pm",
        "--merge-context", "manual",
        "--surface", "product-skeleton",
    ])
    assert exit_code == 0
    assert "Co-Authored-By:" not in _commit_body(tmp_path)


def test_codex_model_attribution_does_not_bypass_the_staged_set_guard(tmp_path, capsys):
    # The observed-incident shape, repeated with Codex model attribution
    # supplied: an undeclared foreign path in the index must still refuse the
    # commit, regardless of what attribution the caller passes.
    _init_repo(tmp_path)
    (tmp_path / "foreign.txt").write_text("someone else's work\n")
    _git_raw(tmp_path, "add", "foreign.txt")
    (tmp_path / "own.txt").write_text("mine\n")
    head_before = _git_raw(tmp_path, "rev-parse", "HEAD").strip()
    staged_before = _git_raw(tmp_path, "show", ":foreign.txt")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: my own change",
        "--actor", "developer",
        "--add", "own.txt",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Codex",
        "--co-authored-by", "gpt-5.6-terra <noreply@openai.com>",
    ])

    assert exit_code != 0
    assert _git_raw(tmp_path, "rev-parse", "HEAD").strip() == head_before
    assert _git_raw(tmp_path, "show", ":foreign.txt") == staged_before
    stderr = capsys.readouterr().err
    assert "foreign.txt" in stderr


# ── Skill-Version: provenance — end-to-end through main()'s commit path ─────
# main() wires resolve_skill_version into the commit op only; the merge op
# never reads it. Resolution runs against the *instance* repo (where the skill
# source lives), never --repo — for an external product the commit-target repo
# holds no `.claude/skills/`. The main() tests that exercise this pin
# `instance_repo_root` to their throwaway repo via monkeypatch, so tmp_path
# controls skill presence. Under the explicit-only contract, the provenance
# line appears IFF the caller passes --skill AND that skill's source resolves:
# the execution-half tests above pass a producing actor (`developer`) with NO
# --skill and stay at the 4-line trailer block; the with-skill test below adds
# the SKILL.md fixture and passes --skill to make the line appear.

def test_end_to_end_actor_without_skill_omits_line(tmp_path, monkeypatch):
    # Explicit-only: a producing actor that passes NO --skill lands no
    # Skill-Version line, even with that actor's former default skill present on
    # disk. This is the exact case the retired actor-derivation stamped falsely.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    _add_skill_fixture(tmp_path, "development-implementation", version="1.7.0")
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: real commit through the builder",
        "--body", "No --skill, so no provenance line.",
        "--actor", "developer",
        "--add", "work.txt",
        "--directional", "Shukuba: commit-builder — progress: builds it",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    assert "Skill-Version:" not in _commit_body(tmp_path)


def test_end_to_end_explicit_skill_lands_line(tmp_path, monkeypatch):
    # An explicit --skill lands the provenance line last in the trailer block.
    _init_repo(tmp_path)
    # Pin skill resolution to the throwaway repo so the fixture below is the
    # one main() reads — resolution follows the instance repo, not --repo.
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    _add_skill_fixture(tmp_path, "development-implementation", version="1.7.0")
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: real commit through the builder",
        "--body", "Explicit --skill wires the provenance line.",
        "--actor", "developer",
        "--skill", "development-implementation",
        "--add", "work.txt",
        "--directional", "Shukuba: commit-builder — progress: builds it",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    body = _commit_body(tmp_path)
    matches = re.findall(r"^Skill-Version: .*$", body, flags=re.MULTILINE)
    assert len(matches) == 1
    assert re.match(
        r"^Skill-Version: development-implementation@\d+\.\d+\.\d+ [0-9a-f]{40}$",
        matches[0],
    )
    trailer_block = body.strip().split("\n\n")[-1]
    assert trailer_block.splitlines()[-1] == matches[0]


def test_end_to_end_explicit_skill_names_the_producing_skill(tmp_path, monkeypatch):
    # --actor cto --skill product-sdd-write must stamp product-sdd-write — the
    # skill actually named — not some other producing skill the cto also owns.
    # This is the exact commit the product-sdd-write check makes: a cto subagent
    # running product-sdd-write against an external product.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    # Both skills the cto owns exist on disk, so a wrong resolution would still
    # find *a* skill — the assertion pins the NAME, catching resolution of the
    # wrong one.
    _add_skill_fixture(tmp_path, "product-srs", version="2.0.0")
    _add_skill_fixture(tmp_path, "product-sdd-write", version="1.0.0")
    (tmp_path / "SDD.md").write_text("# SDD\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "cto: draft the example-product SDD (round 1)",
        "--body", "Proof --skill names the producing skill exactly.",
        "--actor", "cto",
        "--skill", "product-sdd-write",
        "--add", "SDD.md",
        "--directional", "Shukuba: product-sdd-write — progress: checks it",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    body = _commit_body(tmp_path)
    matches = re.findall(r"^Skill-Version: .*$", body, flags=re.MULTILINE)
    assert len(matches) == 1
    assert re.match(
        r"^Skill-Version: product-sdd-write@\d+\.\d+\.\d+ [0-9a-f]{40}$",
        matches[0],
    ), f"expected product-sdd-write, got {matches[0]!r}"


def test_end_to_end_non_producing_actor_omits_line(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "retire: shukuba/thing → trail/",
        "--role", "Product",
        "--add", "work.txt",
        "--directional", "Shukuba: thing — progress: reached, retired to trail",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    body = _commit_body(tmp_path)
    assert "Skill-Version:" not in body


# ── Prompt-Version: provenance — end-to-end through main()'s commit path ───
# Same wiring as Skill-Version:, same instance-not---repo resolution, and the
# two flags are independent — passing one says nothing about the other.

def test_end_to_end_explicit_prompt_lands_line(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    _add_prompt_fixture(tmp_path, "cto_create_domain_doctrine", version="1.0.0")
    (tmp_path / "doctrine.md").write_text("# doctrine\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "cto: the instance states its domain doctrine",
        "--body", "Explicit --prompt wires the provenance line.",
        "--role", "CTO",
        "--prompt", "cto_create_domain_doctrine",
        "--add", "doctrine.md",
        "--directional", "Shukuba: doctrine — progress: states it",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    body = _commit_body(tmp_path)
    matches = re.findall(r"^Prompt-Version: .*$", body, flags=re.MULTILINE)
    assert len(matches) == 1
    assert re.match(
        r"^Prompt-Version: cto_create_domain_doctrine@\d+\.\d+\.\d+ [0-9a-f]{40}$",
        matches[0],
    )
    trailer_block = body.strip().split("\n\n")[-1]
    assert trailer_block.splitlines()[-1] == matches[0]
    # Independent facts: a prompt commit that ran no skill carries no skill line.
    assert "Skill-Version:" not in body


def test_end_to_end_both_flags_land_both_lines(tmp_path, monkeypatch):
    # The thin-skill-over-fat-prompt shape: both lines, skill then prompt.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    _add_skill_fixture(tmp_path, "product-prd", version="4.11.0")
    _add_prompt_fixture(tmp_path, "cpo_create_prd", version="2.5.0")
    (tmp_path / "PRD.md").write_text("# PRD\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "cpo: draft the PRD",
        "--body", "Both flags, both lines.",
        "--actor", "cpo",
        "--skill", "product-prd",
        "--prompt", "cpo_create_prd",
        "--add", "PRD.md",
        "--directional", "Agari: thing — progress: drafts it",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    trailers = _commit_body(tmp_path).strip().split("\n\n")[-1].splitlines()
    assert re.match(r"^Skill-Version: product-prd@\d+\.\d+\.\d+ [0-9a-f]{40}$", trailers[-2])
    assert re.match(r"^Prompt-Version: cpo_create_prd@\d+\.\d+\.\d+ [0-9a-f]{40}$", trailers[-1])


def test_end_to_end_no_prompt_flag_omits_line(tmp_path, monkeypatch):
    # A prompt present on disk does not stamp itself — explicit-only.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    _add_prompt_fixture(tmp_path, "cto_create_domain_doctrine", version="1.0.0")
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "retire: shukuba/thing → trail/",
        "--role", "Product",
        "--add", "work.txt",
        "--directional", "Shukuba: thing — progress: reached, retired to trail",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    assert "Prompt-Version:" not in _commit_body(tmp_path)


def test_end_to_end_prompt_resolves_against_instance_not_repo(tmp_path, monkeypatch):
    # The reason the flag takes a name: the commit target is often NOT the
    # instance (an external product), and the prompt source lives only in the
    # instance. The line must resolve from the instance while the commit lands
    # in the product repo.
    instance = tmp_path / "instance"
    product = tmp_path / "product"
    instance.mkdir()
    product.mkdir()
    _init_repo(instance)
    _init_repo(product)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: instance)
    _add_prompt_fixture(instance, "cto_create_srs", version="3.5.0")
    (product / "SRS.md").write_text("# SRS\n")

    exit_code = commit_builder.main([
        "--repo", str(product),
        "commit",
        "--subject", "cto: draft the SRS",
        "--body", "Prompt source is in the instance; the commit lands here.",
        "--role", "CTO",
        "--prompt", "cto_create_srs",
        "--add", "SRS.md",
        "--directional", "Agari: thing — progress: drafts it",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    body = _commit_body(product)
    assert re.search(
        r"^Prompt-Version: cto_create_srs@3\.5\.0 [0-9a-f]{40}$", body, flags=re.MULTILINE
    ), body


# ── --rm / --add: staging inside the builder, via `git -C` ──────────────────
# The builder stages the commit itself so a caller emits ONE allow-listed
# `python3 commit_builder.py` call — never a `cd <repo> && git rm && git add`
# compound. That compound tripped the harness's "cd-then-git can run untrusted
# hooks" guard and halted an autonomous product-prd run mid-commit (the exact
# regression these tests pin against). All staging is `git -C <repo> …`, which
# does not trip the guard.

def _name_status(path: Path, ref: str = "HEAD") -> str:
    """The name-status of a single commit — `D\\tpath`, `M\\tpath`, `A\\tpath`."""
    return subprocess.run(
        ["git", "-C", str(path), "show", "--name-status", "--format=", ref],
        capture_output=True, text=True, check=True,
    ).stdout


def _working_tree_clean(path: Path) -> bool:
    return subprocess.run(
        ["git", "-C", str(path), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    ).stdout.strip() == ""


def test_commit_op_add_stages_unstaged_modification(tmp_path, monkeypatch):
    # An unstaged modification the caller never `git add`ed lands in the commit
    # because --add stages it inside the builder.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    (tmp_path / "seed.txt").write_text("seed changed\n")  # modified, NOT staged

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "cpo: draft the PRD",
        "--actor", "cpo",
        "--add", "seed.txt",
        "--directional", "Shukuba: prd — progress: drafted",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    assert "M\tseed.txt" in _name_status(tmp_path)
    assert _working_tree_clean(tmp_path)  # nothing left unstaged


def test_commit_op_rm_stages_removal(tmp_path, monkeypatch):
    # --rm stages a deletion (and removes the working copy), so the file is gone
    # from the tree in the resulting commit — the open-issues deletion shape.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    (tmp_path / "open_issues.md").write_text("open\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "open_issues.md"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "add open issues"], check=True
    )

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "cpo: close the round clean",
        "--actor", "cpo",
        "--rm", "open_issues.md",
        "--directional", "Shukuba: prd — progress: round closed",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    assert not (tmp_path / "open_issues.md").exists()
    assert "D\topen_issues.md" in _name_status(tmp_path)


def test_commit_op_rm_and_add_together_is_the_clean_round_commit(tmp_path, monkeypatch):
    # The exact product-prd clean-round finishing commit: delete
    # docs/PRD_open_issues.md AND stage the updated docs/PRD.md in ONE builder
    # call. This is what replaces the `cd <repo> && git rm … && git add …`
    # compound that halted the run — both changes land in a single commit.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "PRD.md").write_text("v1\n")
    (docs / "PRD_open_issues.md").write_text("open\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "docs"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "seed prd + open issues"],
        check=True,
    )
    (docs / "PRD.md").write_text("v2\n")  # round's PRD update, unstaged

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "cpo: fold owner answers, close round clean",
        "--actor", "cpo",
        "--rm", "docs/PRD_open_issues.md",
        "--add", "docs/PRD.md",
        "--directional", "Shukuba: prd — progress: round closed",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    assert not (docs / "PRD_open_issues.md").exists()
    names = _name_status(tmp_path)
    assert "D\tdocs/PRD_open_issues.md" in names
    assert "M\tdocs/PRD.md" in names
    assert _working_tree_clean(tmp_path)


def test_commit_op_add_stages_only_named_not_other_dirty_files(tmp_path, monkeypatch):
    # "Stage only what you touch": a dirty file the caller did NOT pass to --add
    # must stay OUT of the commit and stay dirty. This is the regression guard
    # against a `git add -A` / --add-all shape that sweeps the whole worktree —
    # the reason --add-all was rejected: staging must be by named path only.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    (tmp_path / "named.txt").write_text("named\n")      # will be --add-ed
    (tmp_path / "other.txt").write_text("unrelated\n")  # dirty, NOT named

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "cpo: draft the PRD",
        "--actor", "cpo",
        "--add", "named.txt",
        "--directional", "Shukuba: prd — progress: drafted",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    names = _name_status(tmp_path)
    assert "A\tnamed.txt" in names            # the named file landed
    assert "other.txt" not in names           # the un-named file did NOT
    assert not _working_tree_clean(tmp_path)  # other.txt is still dirty


def test_commit_op_rm_failure_bails_without_committing(tmp_path, monkeypatch):
    # A staging failure (git rm on a nonexistent path) must return non-zero and
    # make NO commit — a staging failure never yields a partial commit.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)

    def head(path: Path) -> str:
        return subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    head_before = head(tmp_path)
    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "cpo: close the round clean",
        "--actor", "cpo",
        "--rm", "does_not_exist.md",
        "--directional", "Shukuba: prd — progress: round closed",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    assert head(tmp_path) == head_before  # no commit landed


def test_stage_helpers_empty_lists_are_noops():
    # The defaults ([] for both) must be pure no-ops that never invoke git.
    # This no longer means "callers that stage themselves are unchanged" —
    # under the staged-set guard (below), a caller that stages outside the
    # builder must now DECLARE what it staged via --staged (or wave the
    # whole check with --take-index); an undeclared pre-stage refuses. What
    # stays true is narrower: passing no --add/--rm paths triggers no git
    # call from these two helpers. No repo needed: an empty list returns 0
    # before any subprocess.
    assert commit_builder._run_git_rm("/nonexistent-repo", []) == 0
    assert commit_builder._run_git_add("/nonexistent-repo", []) == 0


# ── the staged-set guard: the builder commits only what its caller declared ─
# Before this task, `_run_git_commit` ran a plain, unscoped `git commit` —
# every entry sitting in the index at commit time landed, including a path a
# concurrent session staged moments earlier in the same worktree (the
# recorded incident, `docs/proposals/commit-builder-index-scope/rationale.md`
# § The observed incidents). The guard below closes the pre-staged class:
# every staged path must be covered by --add ∪ --rm ∪ --staged, or the
# commit refuses, commits nothing, and names the uncovered path(s).
# `--take-index` is the owner-decided escape hatch for interactive
# hand-staging (rationale.md § Owner decisions, 1) — it accepts the whole
# index as-is and skips the check entirely, for that one call.

def _git_raw(path: Path, *args: str) -> str:
    """Run a raw git op directly against the repo — used to simulate content
    staged OUTSIDE the builder: a concurrent session's `git add` (the
    incident shape), or a `git mv` the caller is about to declare via
    --staged (the sanctioned pre-stage pattern)."""
    return subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True, text=True, check=True,
    ).stdout


def _tracked_paths(path: Path, ref: str = "HEAD") -> set[str]:
    """The full set of paths tracked in `ref`'s tree — used to prove a
    rename actually landed (old path gone, new path present) without
    depending on git's rename-detection heuristic in `--name-status`.

    `-z` for the same reason `_read_staged_paths` needs it: git's default
    output is for display, so it C-quotes any non-ASCII name (and a plain
    `.split()` would additionally break a path containing a space). NUL
    separation gives the raw paths these assertions compare against."""
    return set(
        subprocess.run(
            ["git", "-C", str(path), "ls-tree", "-r", "--name-only", "-z", ref],
            capture_output=True, text=True, check=True,
        ).stdout.split("\0")
    ) - {""}


def test_observed_incident_refuses(tmp_path, capsys):
    # The exact recorded incident: a concurrent session stages a foreign file
    # (a raw `git add`, nothing to do with this call), then the builder runs
    # with --add naming only its own file. Before the guard this committed
    # both, silently. The guard must refuse, make no commit, and name the
    # foreign path.
    _init_repo(tmp_path)
    (tmp_path / "foreign.txt").write_text("someone else's work\n")
    _git_raw(tmp_path, "add", "foreign.txt")
    (tmp_path / "own.txt").write_text("mine\n")
    head_before = _git_raw(tmp_path, "rev-parse", "HEAD").strip()

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: my own change",
        "--actor", "developer",
        "--add", "own.txt",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    assert _git_raw(tmp_path, "rev-parse", "HEAD").strip() == head_before
    stderr = capsys.readouterr().err
    assert "foreign.txt" in stderr


def test_empty_marker_sweep_refuses(tmp_path, capsys):
    # The empty-marker shape (nothing named, --allow-empty — the closing
    # marker every development-implementation run makes) with a
    # foreign file pre-staged: before the guard this swept the foreign file
    # into a commit that claimed to be empty. The guard must refuse it too.
    _init_repo(tmp_path)
    (tmp_path / "foreign.txt").write_text("someone else's work\n")
    _git_raw(tmp_path, "add", "foreign.txt")
    head_before = _git_raw(tmp_path, "rev-parse", "HEAD").strip()

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: <key> — implementation complete",
        "--actor", "developer",
        "--allow-empty",
        "--directional", "Shukuba: proto — progress: closing marker",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    assert _git_raw(tmp_path, "rev-parse", "HEAD").strip() == head_before
    stderr = capsys.readouterr().err
    assert "foreign.txt" in stderr


def test_declared_prestage_commits_rename_and_added_file(tmp_path, monkeypatch):
    # The sanctioned pre-stage pattern: a rename staged by `git mv`, declared
    # via --staged with both halves, plus an --add file for something else
    # edited in the same commit — exit 0; the commit contains the rename AND
    # the added file; nothing else.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    (tmp_path / "old.md").write_text("content\n")
    _git_raw(tmp_path, "add", "old.md")
    _git_raw(tmp_path, "commit", "-q", "-m", "seed old.md")
    _git_raw(tmp_path, "mv", "old.md", "new.md")
    (tmp_path / "extra.txt").write_text("extra\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "pm: retire old -> new",
        "--actor", "pm",
        "--staged", "old.md", "new.md",
        "--add", "extra.txt",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    tracked = _tracked_paths(tmp_path)
    assert "new.md" in tracked
    assert "old.md" not in tracked
    assert "extra.txt" in tracked
    assert "seed.txt" in tracked  # the repo's untouched pre-existing file


def test_directory_prefix_coverage_commits_folder_move(tmp_path, monkeypatch):
    # A `git mv` of a whole folder, declared as --staged <old-folder>
    # <new-folder> (not every file underneath, one entry per side) — commits.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    folder = tmp_path / "docs" / "proposals" / "x"
    folder.mkdir(parents=True)
    (folder / "plan.md").write_text("plan\n")
    _git_raw(tmp_path, "add", "docs")
    _git_raw(tmp_path, "commit", "-q", "-m", "seed docs/proposals/x")
    _git_raw(tmp_path, "mv", "docs/proposals/x", "docs/proposals/y")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "pm: retire docs/proposals/x -> y",
        "--actor", "pm",
        "--staged", "docs/proposals/x", "docs/proposals/y",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    tracked = _tracked_paths(tmp_path)
    assert "docs/proposals/y/plan.md" in tracked
    assert "docs/proposals/x/plan.md" not in tracked


def test_directory_prefix_requires_slash_boundary_not_string_prefix(tmp_path, capsys):
    # A prefix that matches only as a string, not at a `/` boundary
    # (--staged docs/prop against docs/proposals/x/plan.md), must NOT cover —
    # the guard refuses instead of silently treating a string-prefix hit as
    # a real directory declaration.
    _init_repo(tmp_path)
    folder = tmp_path / "docs" / "proposals" / "x"
    folder.mkdir(parents=True)
    (folder / "plan.md").write_text("plan\n")
    _git_raw(tmp_path, "add", "docs")
    _git_raw(tmp_path, "commit", "-q", "-m", "seed docs/proposals/x")
    _git_raw(tmp_path, "mv", "docs/proposals/x", "docs/proposals/y")
    head_before = _git_raw(tmp_path, "rev-parse", "HEAD").strip()

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "pm: retire docs/proposals/x -> y",
        "--actor", "pm",
        "--staged", "docs/prop", "docs/proposals/y",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    assert _git_raw(tmp_path, "rev-parse", "HEAD").strip() == head_before
    stderr = capsys.readouterr().err
    assert "docs/proposals/x/plan.md" in stderr


def test_directory_prefix_with_trailing_slash_covers(tmp_path, monkeypatch):
    # The same folder move, declared with the trailing slash a caller naturally
    # types for a directory. `docs/proposals/x/` names exactly what
    # `docs/proposals/x` names, so it covers the same staged paths — before this
    # was fixed the guard built `docs/proposals/x//` and matched nothing, so the
    # declaration was rejected as matching-nothing AND its paths reported
    # undeclared: two refusals for one correct call.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    folder = tmp_path / "docs" / "proposals" / "x"
    folder.mkdir(parents=True)
    (folder / "plan.md").write_text("plan\n")
    _git_raw(tmp_path, "add", "docs")
    _git_raw(tmp_path, "commit", "-q", "-m", "seed docs/proposals/x")
    _git_raw(tmp_path, "mv", "docs/proposals/x", "docs/proposals/y")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "pm: retire docs/proposals/x -> y",
        "--actor", "pm",
        "--staged", "docs/proposals/x/", "docs/proposals/y/",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    tracked = _tracked_paths(tmp_path)
    assert "docs/proposals/y/plan.md" in tracked
    assert "docs/proposals/x/plan.md" not in tracked


def test_trailing_slash_does_not_widen_coverage(tmp_path, monkeypatch):
    # Normalising the slash must not turn a declaration into a wildcard: a
    # sibling whose name merely starts with the declared string stays
    # undeclared, exactly as it does without the slash.
    assert commit_builder._covers("docs/prop/", "docs/prop/x.md") is True
    assert commit_builder._covers("docs/prop/", "docs/proposals/x.md") is False
    assert commit_builder._covers("docs/prop", "docs/proposals/x.md") is False
    assert commit_builder._covers("a/b.md/", "a/b.md") is True


def test_staged_declaration_matching_nothing_refuses(tmp_path, capsys):
    # --staged <path> where nothing is staged at or under <path> — a stale or
    # wrong declaration (the move it names never happened) — refuses, names
    # the declaration, and makes no commit. Distinct from the uncovered-path
    # case: here the caller's OWN --add file is fully covered, but the
    # declared --staged path is a dangling promise.
    _init_repo(tmp_path)
    (tmp_path / "own.txt").write_text("mine\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: my own change",
        "--actor", "developer",
        "--add", "own.txt",
        "--staged", "never-moved.md",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    stderr = capsys.readouterr().err
    assert "never-moved.md" in stderr
    assert "match" in stderr.lower()


def test_take_index_accepts_whole_index(tmp_path, monkeypatch):
    # The escape hatch really is whole-index acceptance, not a softer check:
    # the foreign pre-staged file again, builder called with --take-index and
    # its own --add file — exit 0, the commit contains BOTH.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    (tmp_path / "foreign.txt").write_text("someone else's work\n")
    _git_raw(tmp_path, "add", "foreign.txt")
    (tmp_path / "own.txt").write_text("mine\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: my own change",
        "--actor", "developer",
        "--add", "own.txt",
        "--take-index",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    names = _name_status(tmp_path)
    assert "A\tforeign.txt" in names
    assert "A\town.txt" in names


def test_take_index_composes_with_allow_empty_marker(tmp_path, monkeypatch):
    # --take-index + clean index + --allow-empty → an empty commit, exactly
    # as the clean-marker case; the hatch does not manufacture content.
    _init_repo(tmp_path)  # clean tree, nothing staged
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: <key> — implementation complete",
        "--actor", "developer",
        "--take-index",
        "--allow-empty",
        "--directional", "Shukuba: proto — progress: closing marker",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    diff = subprocess.run(
        ["git", "-C", str(tmp_path), "diff", "--stat", "HEAD~1", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert diff == ""


def test_refusal_names_staged_and_take_index_and_stop_and_look(tmp_path, capsys):
    # The refusal is actionable — pinned, not hoped. It must list every
    # uncovered staged path and name both ways out BY FLAG NAME (--staged,
    # --take-index), plus the third possibility: if the path is not yours,
    # stop and look, another session staged it.
    _init_repo(tmp_path)
    (tmp_path / "foreign.txt").write_text("someone else's work\n")
    _git_raw(tmp_path, "add", "foreign.txt")
    (tmp_path / "own.txt").write_text("mine\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: my own change",
        "--actor", "developer",
        "--add", "own.txt",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    stderr = capsys.readouterr().err
    assert "--staged" in stderr
    assert "--take-index" in stderr
    assert "stop and look" in stderr.lower()


def test_unmigrated_mover_shape_refuses_actionably(tmp_path, capsys):
    # A journey mover's `git mv <file>` followed by the builder with NO
    # staging flags at all — the shape the retire skills were written against
    # before they declared their renames, and the shape any hand-driven `git
    # mv` + builder call still has. Whoever hits the refusal must be able to
    # fix the call in one step without reading the builder's source: both
    # rename halves named, both remedies offered. (The migrated shape — a
    # `--staged` naming both halves — is
    # `skills/scrum-master/.claude/skills/shukuba-retire/SKILL.md` Step 5, covered below by
    # test_declared_prestage_of_a_non_ascii_rename_commits.)
    _init_repo(tmp_path)
    (tmp_path / "thing.md").write_text("content\n")
    _git_raw(tmp_path, "add", "thing.md")
    _git_raw(tmp_path, "commit", "-q", "-m", "seed thing.md")
    (tmp_path / "trail").mkdir()
    _git_raw(tmp_path, "mv", "thing.md", "trail/thing.md")
    head_before = _git_raw(tmp_path, "rev-parse", "HEAD").strip()

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "retire: thing -> trail/",
        "--role", "Product",
        "--directional", "Shukuba: thing — progress: reached, retired to trail",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    assert _git_raw(tmp_path, "rev-parse", "HEAD").strip() == head_before
    stderr = capsys.readouterr().err
    assert "thing.md" in stderr
    assert "trail/thing.md" in stderr
    assert "--staged" in stderr
    assert "--take-index" in stderr


def test_refusal_performs_no_rollback_and_leaves_index_intact(tmp_path):
    # HEAD unchanged, and the index is left exactly as the check saw it (the
    # builder's own --add staging included) — the refusal path never runs
    # `git reset`. The caller can inspect what was found.
    _init_repo(tmp_path)
    (tmp_path / "foreign.txt").write_text("someone else's work\n")
    _git_raw(tmp_path, "add", "foreign.txt")
    (tmp_path / "own.txt").write_text("mine\n")
    head_before = _git_raw(tmp_path, "rev-parse", "HEAD").strip()

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: my own change",
        "--actor", "developer",
        "--add", "own.txt",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    assert _git_raw(tmp_path, "rev-parse", "HEAD").strip() == head_before
    staged = set(_git_raw(tmp_path, "diff", "--cached", "--name-only").split())
    assert staged == {"foreign.txt", "own.txt"}


def test_guard_and_hatch_absent_from_merge_parser(tmp_path):
    # The merge op takes neither --staged nor --take-index and performs no
    # staged-set check — the guard and the hatch exist only on the commit
    # path.
    with pytest.raises(SystemExit):
        commit_builder.main([
            "--repo", str(tmp_path),
            "merge",
            "--branch", "feature",
            "--target-branch", "main",
            "--description", "thing",
            "--staged", "x",
            "--actor", "pm",
            "--merge-context", "manual",
            "--surface", "Claude Code",
            "--co-authored-by", CO_AUTHORED_BY,
        ])


def test_module_and_flag_help_state_the_boundaries():
    # The guard narrows the race; it does not close it. --take-index waives
    # it entirely. A later reader must not build on a guarantee that does
    # not exist (rationale.md § Concurrency reality check).
    proc = subprocess.run(
        [sys.executable, str(BUILDER), "commit", "--help"],
        capture_output=True, text=True, check=True,
    )
    help_text = proc.stdout.lower()
    assert "--staged" in help_text
    assert "--take-index" in help_text
    combined = ((commit_builder.__doc__ or "").lower() + help_text).replace("**", "")
    assert "does not close" in combined
    assert "waive" in combined


def test_omitted_staging_and_hatch_flags_default_to_empty_and_off(tmp_path):
    # An omitted flag still defaults to [] (and --take-index defaults off) —
    # locks the argparse wiring directly, independent of the accumulate fix
    # (Task 2) that also touches these declarations.
    args = commit_builder._build_arg_parser().parse_args([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "work",
        "--actor", "developer",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])
    assert args.add_paths == []
    assert args.rm_paths == []
    assert args.staged_paths == []
    assert args.take_index is False


def test_end_to_end_merge_omits_line(tmp_path):
    main_branch = _init_repo(tmp_path)

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    git("checkout", "-q", "-b", "feature")
    (tmp_path / "feature.txt").write_text("feature\n")
    git("add", "feature.txt")
    git("commit", "-q", "-m", "feature: add a thing")
    git("checkout", "-q", main_branch)

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "merge",
        "--branch", "feature",
        "--target-branch", main_branch,
        "--description", "bring in the feature",
        "--branch-commits", "feature: add a thing",
        "--actor", "pm",
        "--merge-context", "manual",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    body = _commit_body(tmp_path)
    assert "Skill-Version:" not in body


# ── Task 2: repeated staging flags accumulate instead of keeping the last ───
# `--add`, `--rm`, `--staged`, and `--branch-commits` were all `nargs="*"`
# with the plain `store` action, so a repeated flag silently replaced the
# earlier occurrence — the caller's dropped paths were never staged, never
# committed, and nothing failed (the trap
# `core/doctrine/governance/commit_via_builder.md` documents in prose).
# The staged-set guard (Task 1) cannot catch this: a dropped path is simply
# absent from the index, so the declaration and the staged set stay
# consistent while the commit is silently partial. Both call shapes must now
# be correct: `--add a b` and `--add a --add b` both stage `a` and `b`.

def test_repeated_add_flags_accumulate_and_commit_both(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    (tmp_path / "a.txt").write_text("a\n")
    (tmp_path / "b.txt").write_text("b\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: add both via repeated flags",
        "--actor", "developer",
        "--add", "a.txt",
        "--add", "b.txt",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    names = _name_status(tmp_path)
    assert "A\ta.txt" in names
    assert "A\tb.txt" in names
    assert _working_tree_clean(tmp_path)


def test_repeated_rm_flags_stage_both_deletions(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    (tmp_path / "x.txt").write_text("x\n")
    (tmp_path / "y.txt").write_text("y\n")
    _git_raw(tmp_path, "add", "x.txt", "y.txt")
    _git_raw(tmp_path, "commit", "-q", "-m", "seed x.txt + y.txt")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: remove both via repeated flags",
        "--actor", "developer",
        "--rm", "x.txt",
        "--rm", "y.txt",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    names = _name_status(tmp_path)
    assert "D\tx.txt" in names
    assert "D\ty.txt" in names


def test_repeated_staged_flags_declare_both_for_the_guard(tmp_path, monkeypatch):
    # Both --staged occurrences must accumulate so the guard sees both
    # declarations — otherwise a rename declared across two --staged flags
    # would refuse on whichever half the earlier occurrence dropped.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    (tmp_path / "old.md").write_text("content\n")
    _git_raw(tmp_path, "add", "old.md")
    _git_raw(tmp_path, "commit", "-q", "-m", "seed old.md")
    _git_raw(tmp_path, "mv", "old.md", "new.md")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "pm: retire old -> new",
        "--actor", "pm",
        "--staged", "old.md",
        "--staged", "new.md",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    tracked = _tracked_paths(tmp_path)
    assert "new.md" in tracked
    assert "old.md" not in tracked


def test_a_repo_that_is_a_subdirectory_declares_paths_relative_to_it(tmp_path, monkeypatch):
    # `git -C <sub> add x` stages `<sub>/x`, but the staged set is read back
    # from the repo root — so a declaration relative to --repo must be read
    # the same way, or every commit from a product inside the instance repo
    # is refused (product-skeleton, tracker17, 2026-10-07).
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    product = tmp_path / "products" / "demo"
    (product / "tests").mkdir(parents=True)
    (product / "main.py").write_text("print()\n")
    (product / "tests" / "conftest.py").write_text("\n")

    exit_code = commit_builder.main([
        "--repo", str(product),
        "commit",
        "--subject", "skeleton: demo",
        "--role", "Product",
        "--add", "main.py", "tests/conftest.py",
        "--directional", "Agari: none",
        "--surface", "product-skeleton",
    ])

    assert exit_code == 0
    tracked = _tracked_paths(tmp_path)
    assert "products/demo/main.py" in tracked
    assert "products/demo/tests/conftest.py" in tracked


def test_a_subdirectory_repo_still_refuses_staged_work_outside_it(tmp_path, monkeypatch):
    # The prefix applies to declarations only: the guard still reads the
    # whole index, so another session's staged file elsewhere is refused.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    product = tmp_path / "products" / "demo"
    product.mkdir(parents=True)
    (product / "main.py").write_text("print()\n")
    (tmp_path / "foreign.md").write_text("someone else's\n")
    _git_raw(tmp_path, "add", "foreign.md")

    exit_code = commit_builder.main([
        "--repo", str(product),
        "commit",
        "--subject", "skeleton: demo",
        "--role", "Product",
        "--add", "main.py",
        "--directional", "Agari: none",
        "--surface", "product-skeleton",
    ])

    assert exit_code != 0
    assert "products/demo/main.py" not in _tracked_paths(tmp_path)


def test_repeated_branch_commits_flags_land_both_dash_lines(tmp_path):
    main_branch = _init_repo(tmp_path)

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    git("checkout", "-q", "-b", "feature")
    (tmp_path / "feature.txt").write_text("feature\n")
    git("add", "feature.txt")
    git("commit", "-q", "-m", "feature: add a thing")
    git("checkout", "-q", main_branch)

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "merge",
        "--branch", "feature",
        "--target-branch", main_branch,
        "--description", "bring in the feature",
        "--branch-commits", "l1",
        "--branch-commits", "l2",
        "--actor", "pm",
        "--merge-context", "manual",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    body = _commit_body(tmp_path)
    assert "-> l1" in body
    assert "-> l2" in body


def test_single_flag_multi_path_form_unchanged(tmp_path, monkeypatch):
    # The plan's rationale asserts an existing test already pins `--add a b`
    # (multiple paths under one flag occurrence) — verified false this
    # session (no call site in the pre-existing suite passed more than one
    # path in a single --add/--rm occurrence). Added directly so the
    # behaviour — still correct, and the documented house style — has real
    # coverage instead of an assumed one (Implementer Review Notes).
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    (tmp_path / "a.txt").write_text("a\n")
    (tmp_path / "b.txt").write_text("b\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: add both via one flag",
        "--actor", "developer",
        "--add", "a.txt", "b.txt",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    names = _name_status(tmp_path)
    assert "A\ta.txt" in names
    assert "A\tb.txt" in names


# ── the guard reads paths, not git's display encoding ───────────────────────
# The guard's contract is "refuse what the caller did NOT declare"
# (docs/proposals/commit-builder-index-scope/ad_hoc_plan.md:202-205, :41-46),
# with coverage semantics "applied uniformly to all three declaring flag
# sets" (:221). A path the caller DID declare must therefore commit —
# whatever characters its name happens to contain. This matters here and not
# in the abstract: this repo's own vocabulary is Japanese (宿場 / 飛び石 /
# 根回し / 上がり), so a journey file named in kana is an ordinary artifact,
# and `shukuba-retire` moving one is precisely the shape
# the deferred migration prescribes `--staged <old> <new>` for
# (rationale.md:339-341).

def test_add_of_a_non_ascii_path_is_covered_by_its_own_flag(tmp_path, monkeypatch):
    # The builder stages the path itself via --add, so the declaration and
    # the staged set are the same path by construction — the guard must pass
    # and the commit must land (ad_hoc_plan.md:202-205: cover by
    # --add ∪ --rm ∪ --staged; :221: uniform coverage semantics).
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    (tmp_path / "見本.md").write_text("a specimen\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: add a kana-named artifact",
        "--actor", "developer",
        "--add", "見本.md",
        "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    assert "見本.md" in _tracked_paths(tmp_path)


def test_declared_prestage_of_a_non_ascii_rename_commits(tmp_path, monkeypatch):
    # The retire skills' migrated call shape (rationale.md:339-341) on a
    # kana-named file: `git mv` the file into trail/, declare both halves via
    # --staged. This is behaviour "The declared pre-stage commits"
    # (ad_hoc_plan.md:245-247) — the declaration is complete and exact, so
    # the guard must pass. Refusing here would be a refusal with no remedy:
    # --staged IS the remedy, and the only remaining flag, --take-index,
    # waives the guard wholesale rather than satisfying it.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    (tmp_path / "見本.md").write_text("a specimen\n")
    _git_raw(tmp_path, "add", "見本.md")
    _git_raw(tmp_path, "commit", "-q", "-m", "seed 見本.md")
    (tmp_path / "trail").mkdir()
    _git_raw(tmp_path, "mv", "見本.md", "trail/見本.md")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "retire: 見本 -> trail/",
        "--role", "Product",
        "--staged", "見本.md", "trail/見本.md",
        "--directional", "Shukuba: 見本 — progress: reached, retired to trail",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    tracked = _tracked_paths(tmp_path)
    assert "trail/見本.md" in tracked
    assert "見本.md" not in tracked


# ── `--bump`: the version lands INSIDE the merge commit ─────────────────────
# `versioning.md` § *Bump semantics* moved the bump off the branch:
# a branch never edits a `version:` line, and the commit that *lands* the edit
# on main sets the number. For branch work that commit is the merge — and it
# has to be the merge itself, because `tobiishi-seal/SKILL.md:50` requires that
# "Nothing commits to `main` after the merge" (first-parent history stays at 2
# commits per change). So the builder merges with `--no-commit`, bumps, and
# commits — one merge commit carrying both the branch and the bump.

def _versioned(path: Path, version: str, body: str = "body\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'---\nversion: "{version}"\n---\n\n{body}')


@pytest.mark.parametrize(
    "current,level,expected",
    [
        ("1.42.0", "patch", "1.42.1"),
        ("1.42.0", "minor", "1.43.0"),
        ("1.42.0", "major", "2.0.0"),
        ("4.1.9", "minor", "4.2.0"),
    ],
)
def test_bump_levels(current, level, expected):
    assert commit_builder._bumped(current, level) == expected


def test_merge_bump_lands_inside_the_merge_commit(tmp_path):
    main_branch = _init_repo(tmp_path)

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    doctrine = tmp_path / "core/doctrine.md"
    _versioned(doctrine, "1.42.0")
    git("add", "core/doctrine.md")
    git("commit", "-q", "-m", "seed the doctrine file")

    git("checkout", "-q", "-b", "feature")
    _versioned(doctrine, "1.42.0", "body\nan added rule\n")  # version untouched
    git("commit", "-qam", "feature: add a rule, without touching the counter")
    git("checkout", "-q", main_branch)

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "merge",
        "--branch", "feature",
        "--target-branch", main_branch,
        "--description", "bring in the rule",
        "--branch-commits", "feature: add a rule",
        "--actor", "pm",
        "--merge-context", "manual",
        "--bump", "core/doctrine.md=minor",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    assert 'version: "1.43.0"' in doctrine.read_text()
    assert "an added rule" in doctrine.read_text()
    # One merge commit carries both: two parents, and the bump in its own diff.
    assert len(git("rev-list", "--parents", "-1", "HEAD").split()) == 3
    assert "core/doctrine.md" in git("show", "--format=", "--name-only", "HEAD")
    # Nothing committed to main after the merge.
    assert git("status", "--porcelain") == ""


def test_merge_without_bump_touches_no_version(tmp_path):
    main_branch = _init_repo(tmp_path)

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    doctrine = tmp_path / "doctrine.md"
    _versioned(doctrine, "1.42.0")
    git("add", "doctrine.md")
    git("commit", "-q", "-m", "seed")
    git("checkout", "-q", "-b", "feature")
    (tmp_path / "other.txt").write_text("other\n")
    git("add", "other.txt")
    git("commit", "-q", "-m", "feature: unrelated")
    git("checkout", "-q", main_branch)

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "merge",
        "--branch", "feature",
        "--target-branch", main_branch,
        "--description", "unrelated",
        "--branch-commits", "feature: unrelated",
        "--actor", "pm",
        "--merge-context", "manual",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    assert 'version: "1.42.0"' in doctrine.read_text()


@pytest.mark.parametrize(
    "spec",
    [
        "doctrine.md=sideways",   # not a semver level
        "doctrine.md",            # no level at all
        "absent.md=minor",        # no such file
        "plain.md=minor",         # a file with no frontmatter version:
    ],
)
def test_merge_refuses_an_unusable_bump_before_merging(tmp_path, spec, capsys):
    main_branch = _init_repo(tmp_path)

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    _versioned(tmp_path / "doctrine.md", "1.42.0")
    (tmp_path / "plain.md").write_text("no frontmatter here\n")
    git("add", "doctrine.md", "plain.md")
    git("commit", "-q", "-m", "seed")
    git("checkout", "-q", "-b", "feature")
    (tmp_path / "other.txt").write_text("other\n")
    git("add", "other.txt")
    git("commit", "-q", "-m", "feature: unrelated")
    git("checkout", "-q", main_branch)
    before = git("rev-parse", "HEAD")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "merge",
        "--branch", "feature",
        "--target-branch", main_branch,
        "--description", "unrelated",
        "--branch-commits", "feature: unrelated",
        "--actor", "pm",
        "--merge-context", "manual",
        "--bump", spec,
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    # Refused before the merge ran — main is untouched, no merge left half-done.
    assert git("rev-parse", "HEAD") == before
    assert git("status", "--porcelain") == ""
    assert "commit_builder" in capsys.readouterr().err


# ── a --bump merge that CONFLICTS ends in a stated state, and resumes ───────
# `2026-08-21_a-conflicted-merge-ends-somewhere-stated`. Before this station,
# `_run_git_merge`'s two-phase (--bump) branch ran `git merge --no-ff
# --no-commit` and, on a conflict (a non-zero return code), returned
# immediately — `_apply_bumps` and `_run_git_commit` below it never ran. The
# caller was left mid-merge with no message and no bump, and no subcommand
# that resumed: re-running `merge` would hit git's own "you have not
# concluded your merge (MERGE_HEAD exists)" refusal, so the bump was silently
# lost unless the caller hand-authored the finish.
#
# The shape chosen here is RESUME (of the seed's three permitted shapes,
# `2026-08-21_a-conflicted-merge-drops-out-of-the-builder.md` stations item
# 1): a conflict leaves the merge exactly where git left it (conflict
# markers, `MERGE_HEAD` resolving, nothing committed) and printed guidance —
# and re-running the IDENTICAL commit_builder command a second time, once the
# caller has resolved and `git add`-ed the conflicting paths, detects the
# in-progress merge and finishes it: applies the bump and lands the commit,
# with no re-derivation of the format. The two losing shapes: "refuse to
# start" cannot know a merge will conflict without attempting it (attempting
# it *is* this shape once you keep the result rather than aborting it), and
# would either duplicate this shape or throw away the caller's already-done
# conflict resolution on the retry; "fail loudly with the exact command"
# degenerates to this shape too, because the command that finishes the job is
# always the SAME command re-run — there is no second, different command to
# print that isn't just this one again.

def test_merge_bump_conflict_leaves_a_resumable_state_then_resumes(tmp_path):
    main_branch = _init_repo(tmp_path)

    def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=check,
        )

    def git_out(*args: str) -> str:
        return git(*args).stdout.strip()

    doctrine = tmp_path / "core/doctrine.md"
    _versioned(doctrine, "1.42.0")
    registry = tmp_path / "core/registry.md"
    registry.write_text("base row\n")
    git("add", "core/doctrine.md", "core/registry.md")
    git("commit", "-q", "-m", "seed the doctrine + registry files")

    git("checkout", "-q", "-b", "feature")
    registry.write_text("feature's row\n")
    git("commit", "-qam", "feature: add a row")
    git("checkout", "-q", main_branch)
    registry.write_text("main's row\n")
    git("commit", "-qam", "main: add a different row to the same spot")

    merge_args = [
        "--repo", str(tmp_path),
        "merge",
        "--branch", "feature",
        "--target-branch", main_branch,
        "--description", "bring in the row",
        "--branch-commits", "feature: add a row",
        "--actor", "pm",
        "--merge-context", "manual",
        "--bump", "core/doctrine.md=minor",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ]

    # First call: the merge conflicts.
    exit_code = commit_builder.main(merge_args)

    assert exit_code != 0
    # Left mid-merge on purpose — MERGE_HEAD resolves.
    assert git("rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).returncode == 0
    # Nothing committed: HEAD is still main's own tip commit.
    assert "main: add a different row" in _commit_body(tmp_path)
    # The bump was NOT silently applied on a merge that never landed.
    assert 'version: "1.42.0"' in doctrine.read_text()
    # The conflict markers are on disk, unresolved — the builder did not touch them.
    assert "<<<<<<<" in registry.read_text()

    # The caller resolves the conflict by hand (the one thing the builder
    # never does) and stages it.
    registry.write_text("feature's row\nmain's row\n")
    git("add", "core/registry.md")

    # Second call: the IDENTICAL command, re-run. This is the resume.
    exit_code = commit_builder.main(merge_args)

    assert exit_code == 0
    assert git("rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).returncode != 0
    assert 'version: "1.43.0"' in doctrine.read_text()
    # One merge commit carries both the resolved merge and the bump: two parents.
    assert len(git_out("rev-list", "--parents", "-1", "HEAD").split()) == 3
    body = _commit_body(tmp_path)
    assert body.startswith(f"merge: feature → {main_branch} — bring in the row")
    assert "Merge-Authorized: PM — manual" in body
    assert "core/doctrine.md" in git_out("show", "--format=", "--name-only", "HEAD")
    assert "core/registry.md" in git_out("show", "--format=", "--name-only", "HEAD")
    # Nothing left uncommitted.
    assert git_out("status", "--porcelain") == ""


def test_merge_conflict_prints_a_resume_instruction_not_a_reformat_hint(tmp_path, capsys):
    main_branch = _init_repo(tmp_path)

    def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=check,
        )

    doctrine = tmp_path / "core/doctrine.md"
    _versioned(doctrine, "1.42.0")
    registry = tmp_path / "core/registry.md"
    registry.write_text("base row\n")
    git("add", "core/doctrine.md", "core/registry.md")
    git("commit", "-q", "-m", "seed")

    git("checkout", "-q", "-b", "feature")
    registry.write_text("feature's row\n")
    git("commit", "-qam", "feature: add a row")
    git("checkout", "-q", main_branch)
    registry.write_text("main's row\n")
    git("commit", "-qam", "main: add a different row")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "merge",
        "--branch", "feature",
        "--target-branch", main_branch,
        "--description", "bring in the row",
        "--branch-commits", "feature: add a row",
        "--actor", "pm",
        "--merge-context", "manual",
        "--bump", "core/doctrine.md=minor",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    stderr = capsys.readouterr().err
    assert "commit_builder" in stderr
    assert "re-run" in stderr.lower()
    # Told not to hand-finish it with plain git — that is the exact failure
    # mode this station exists to close.
    assert "git commit" in stderr


def test_merge_conflict_with_no_bump_is_unchanged_by_the_resume_logic(tmp_path):
    # Guardrail: "No change to the commit path" / byte-identical non-bump
    # behaviour. A conflicting merge with NO --bump takes the one-shot `git
    # merge --no-ff branch -m message` path, untouched by this station —
    # `_merge_in_progress` is never consulted there.
    main_branch = _init_repo(tmp_path)

    def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=check,
        )

    registry = tmp_path / "registry.md"
    registry.write_text("base row\n")
    git("add", "registry.md")
    git("commit", "-q", "-m", "seed")

    git("checkout", "-q", "-b", "feature")
    registry.write_text("feature's row\n")
    git("commit", "-qam", "feature: add a row")
    git("checkout", "-q", main_branch)
    registry.write_text("main's row\n")
    git("commit", "-qam", "main: add a different row")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "merge",
        "--branch", "feature",
        "--target-branch", main_branch,
        "--description", "bring in the row",
        "--branch-commits", "feature: add a row",
        "--actor", "pm",
        "--merge-context", "manual",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    assert git("rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).returncode == 0


# ── the resume applies each bump exactly once, and merges what it names ─────
# `2026-08-21_a-conflicted-merge-ends-somewhere-stated` § Guardrail: "Do not
# weaken the `--bump` contract to dodge the problem. Dropping the bump on a
# conflict, or making it idempotent, is the deviation `versioning.md` says a
# merge must surface rather than absorb." Idempotence being off the table is
# what makes bump-once a *control-flow* obligation: `_apply_bumps` reads the
# version currently in the file and writes one level up, so every extra time
# it runs moves the marker another level. A resume is a second run of the
# same command by construction — so the invariant these tests pin is that a
# bump exists on disk only inside a merge commit that landed. A resume that
# does not land must leave the marker exactly where it found it, or the next
# re-run bumps from the moved value and the marker ends two levels up, which
# is the silent wrong number § What it is calls "the exposure".
#
# And § Reached when 2 — "a caller following the tool's own output lands a
# merge commit carrying the correct trailers **and** the bump" — is a claim
# about a *correct* record. `_merge_in_progress` keys on repository state
# alone, so it says nothing about whether the merge in progress is the one
# this invocation names; a merge commit whose subject names one branch while
# its second parent is another is not the correct trailers, and no hook can
# catch it because the format is valid.

def _merge_probe_repo(tmp_path, extra_branch: bool = False) -> tuple[str, callable]:
    """A repo whose `feature` (and optionally `other`) branch conflicts with
    the checked-out branch on `registry.md`, plus a clean versioned
    `doctrine.md` for the `--bump` to land in."""
    main_branch = _init_repo(tmp_path)

    def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=check,
        )

    _versioned(tmp_path / "core/doctrine.md", "1.42.0")
    (tmp_path / "core/registry.md").write_text("base row\n")
    git("add", "core/doctrine.md", "core/registry.md")
    git("commit", "-q", "-m", "seed the doctrine + registry files")

    git("checkout", "-q", "-b", "feature")
    (tmp_path / "core/registry.md").write_text("feature's row\n")
    git("commit", "-qam", "feature: add a row")
    git("checkout", "-q", main_branch)
    if extra_branch:
        git("checkout", "-q", "-b", "other")
        (tmp_path / "core/registry.md").write_text("other's row\n")
        git("commit", "-qam", "other: add a row")
        git("checkout", "-q", main_branch)
    (tmp_path / "core/registry.md").write_text("main's row\n")
    git("commit", "-qam", "main: add a different row to the same spot")
    return main_branch, git


def _merge_argv(tmp_path, main_branch: str, branch: str = "feature") -> list[str]:
    return [
        "--repo", str(tmp_path),
        "merge",
        "--branch", branch,
        "--target-branch", main_branch,
        "--description", "bring in the row",
        "--branch-commits", f"{branch}: add a row",
        "--actor", "pm",
        "--merge-context", "manual",
        "--bump", "core/doctrine.md=minor",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ]


def test_a_resumed_merge_applies_its_bump_exactly_once(tmp_path):
    """A resume that cannot land must not move the marker. The caller here
    does what the hint's own step 2 anticipates going wrong — resolves the
    file in the editor and re-runs before staging it — so the commit is
    refused by git for unmerged paths. The bump must not survive that."""
    main_branch, git = _merge_probe_repo(tmp_path)
    doctrine = tmp_path / "core/doctrine.md"
    argv = _merge_argv(tmp_path, main_branch)

    assert commit_builder.main(argv) != 0
    assert 'version: "1.42.0"' in doctrine.read_text()

    # Resolved on disk, not staged — the re-run cannot land the commit.
    (tmp_path / "core/registry.md").write_text("feature's row\nmain's row\n")
    assert commit_builder.main(argv) != 0
    assert 'version: "1.42.0"' in doctrine.read_text(), (
        "a resume that did not land left its bump applied — the next re-run "
        "bumps again from the moved value"
    )

    # Now staged, so this re-run lands — and the marker moves exactly one level.
    git("add", "core/registry.md")
    assert commit_builder.main(argv) == 0
    assert 'version: "1.43.0"' in doctrine.read_text()
    assert len(
        git("rev-list", "--parents", "-1", "HEAD").stdout.split()
    ) == 3


def test_a_bump_is_not_left_applied_when_the_merge_commit_is_refused(tmp_path):
    """The same invariant on a merge that never conflicts at all: the
    two-phase merge stages the bump and then commits, and that commit can be
    refused by a hook (this instance runs a `pre-commit` hook, and git
    invokes it for the ordinary commit that concludes a `--no-commit`
    merge). A refused commit must leave the marker where it was, so the
    re-run that follows the hook being satisfied applies the bump once, not
    twice."""
    main_branch = _init_repo(tmp_path)

    def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=check,
        )

    doctrine = tmp_path / "core/doctrine.md"
    _versioned(doctrine, "1.42.0")
    git("add", "core/doctrine.md")
    git("commit", "-q", "-m", "seed the doctrine file")

    # The two branches touch different files, so the merge itself is clean —
    # the refusal under test is the hook's, not a conflict's.
    git("checkout", "-q", "-b", "feature")
    (tmp_path / "core/theirs.md").write_text("theirs\n")
    git("add", "core/theirs.md")
    git("commit", "-q", "-m", "feature: add a file of its own")
    git("checkout", "-q", main_branch)
    (tmp_path / "core/ours.md").write_text("ours\n")
    git("add", "core/ours.md")
    git("commit", "-q", "-m", "main: add a different file")

    hooks = tmp_path / "githooks"
    hooks.mkdir()
    hook = hooks / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    git("config", "core.hooksPath", str(hooks))

    argv = _merge_argv(tmp_path, main_branch)
    assert commit_builder.main(argv) != 0
    assert git("rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).returncode == 0
    assert 'version: "1.42.0"' in doctrine.read_text(), (
        "the bump outlived a commit that was refused"
    )

    hook.write_text("#!/bin/sh\nexit 0\n")
    assert commit_builder.main(argv) == 0
    assert 'version: "1.43.0"' in doctrine.read_text()


def test_a_resume_refuses_a_merge_in_progress_of_another_branch(tmp_path, capsys):
    """`--branch` names what this command merges. A merge left in progress by
    someone else — or by an earlier invocation naming a different branch — is
    not that merge, and finishing it would land a commit whose subject names
    one branch and whose second parent is another."""
    main_branch, git = _merge_probe_repo(tmp_path, extra_branch=True)
    doctrine = tmp_path / "core/doctrine.md"

    # A merge this tool never started, conflicted and then resolved by hand.
    git("merge", "--no-ff", "--no-commit", "other", check=False)
    (tmp_path / "core/registry.md").write_text("other's row\nmain's row\n")
    git("add", "core/registry.md")
    head_before = git("rev-parse", "HEAD").stdout.strip()

    exit_code = commit_builder.main(_merge_argv(tmp_path, main_branch, branch="feature"))

    assert exit_code != 0
    assert git("rev-parse", "HEAD").stdout.strip() == head_before, (
        "landed a merge commit for a merge it did not start"
    )
    assert git("rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).returncode == 0
    assert 'version: "1.42.0"' in doctrine.read_text()
    stderr = capsys.readouterr().err
    assert "commit_builder" in stderr
    assert "feature" in stderr


# ── _directional_referent — parse a --directional line into the one referent
#    that has to resolve, or None ("nothing to check here"). Pure — no
#    filesystem, no git. ────────────────────────────────────────────────────

def test_directional_referent_shukuba_with_progress():
    assert commit_builder._directional_referent(
        "Shukuba: commit-builder — progress: builds it"
    ) == ("Shukuba", "commit-builder")


def test_directional_referent_agari_with_progress():
    assert commit_builder._directional_referent(
        "Agari: tools — progress: x"
    ) == ("Agari", "tools")


def test_directional_referent_michi_with_serves():
    assert commit_builder._directional_referent(
        "Michi: sharpen-by-living — serves: x"
    ) == ("Michi", "sharpen-by-living")


def test_directional_referent_agari_none_is_not_a_referent():
    assert commit_builder._directional_referent("Agari: none — did a thing") is None


def test_directional_referent_michi_none_is_not_a_referent():
    assert commit_builder._directional_referent("Michi: none — did a thing") is None


def test_directional_referent_shukuba_none_is_not_a_referent():
    # Retired by `commit_format.md` in favour of `Agari:`; it names no referent.
    assert commit_builder._directional_referent(
        "Shukuba: none — sealed 2026-08-01_x"
    ) is None


def test_directional_referent_shukuba_bare_progress_is_not_a_referent():
    # No referent to resolve; `_unnamed_referent_refusal` refuses the shape.
    assert commit_builder._directional_referent(
        "Shukuba: progress: sealed 2026-08-01_x"
    ) is None


def test_directional_referent_michi_aside_is_not_a_referent():
    assert commit_builder._directional_referent("Michi: aside: hygiene") is None


def test_directional_referent_shukuba_aside_is_not_a_referent():
    assert commit_builder._directional_referent("Shukuba: aside: parked") is None


def test_directional_referent_bare_reading_with_no_colon_is_not_a_referent():
    assert commit_builder._directional_referent("Shukuba: progress — x") is None


def test_directional_referent_role_trailer_is_not_a_directional():
    assert commit_builder._directional_referent("Role: Developer") is None


def test_directional_referent_merge_authorized_trailer_is_not_a_directional():
    assert commit_builder._directional_referent("Merge-Authorized: PM — x") is None


def test_directional_referent_empty_string():
    assert commit_builder._directional_referent("") is None


def test_directional_referent_shukuba_with_nothing_after_colon():
    assert commit_builder._directional_referent("Shukuba:") is None


def test_directional_referent_shukuba_colon_then_only_whitespace():
    assert commit_builder._directional_referent("Shukuba:    ") is None


def test_directional_referent_form_not_at_line_start_is_ignored():
    assert commit_builder._directional_referent("see Shukuba: x") is None


def test_directional_referent_tolerates_leading_whitespace():
    assert commit_builder._directional_referent(
        "  Shukuba: commit-builder — progress: builds it"
    ) == ("Shukuba", "commit-builder")


def test_directional_referent_dated_stem_returned_whole():
    assert commit_builder._directional_referent(
        "Shukuba: 2026-07-08_migrate-scripts-to-tools — progress: x"
    ) == ("Shukuba", "2026-07-08_migrate-scripts-to-tools")


def test_directional_skip_tokens_constant_is_progress_aside_serves():
    # Named module-level constant so this pins it directly, rather than only
    # through _directional_referent's behaviour.
    assert commit_builder._DIRECTIONAL_SKIP_TOKENS == frozenset(
        {"progress", "aside", "serves"}
    )


# ── _resolve_agari / _resolve_michi — does the referent a --directional line
#    names actually exist in the tree the commit lands in? Three-valued:
#    RESOLVES / MISSING / UNCHECKABLE — MISSING is the only one that may ever
#    refuse a commit (Task 4). Root is `--repo`, never instance_repo_root() —
#    a journey referent lives in whichever tree the commit is landing in. ────

def _write_agari(projects_root: Path, name: str) -> None:
    project_dir = projects_root / name
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "agari.md").write_text(f"# Agari — {name}\n")


def test_resolve_agari_present_resolves(tmp_path):
    _write_agari(tmp_path / "system" / "projects", "doctrine")
    assert (
        commit_builder._resolve_agari(str(tmp_path), "doctrine")
        == commit_builder.DirectionalResolution.RESOLVES
    )


def test_resolve_agari_project_dir_present_agari_absent_is_missing(tmp_path):
    (tmp_path / "system" / "projects" / "doctrine").mkdir(parents=True)
    assert (
        commit_builder._resolve_agari(str(tmp_path), "doctrine")
        == commit_builder.DirectionalResolution.MISSING
    )


def test_resolve_agari_no_projects_root_is_uncheckable(tmp_path):
    assert (
        commit_builder._resolve_agari(str(tmp_path), "doctrine")
        == commit_builder.DirectionalResolution.UNCHECKABLE
    )


def test_resolve_agari_observed_incident_versioning_against_doctrine_only_tree(tmp_path):
    # 06962bb0's actual trailer: `Agari: versioning` in a tree whose only
    # project is `doctrine` — the incident this whole plan exists for.
    _write_agari(tmp_path / "system" / "projects", "doctrine")
    assert (
        commit_builder._resolve_agari(str(tmp_path), "versioning")
        == commit_builder.DirectionalResolution.MISSING
    )


def test_resolve_agari_token_with_dotdot_never_escapes_projects_dir(tmp_path):
    # A file that really exists one level above system/projects/ — proves
    # a `..` token can't be used to read it.
    (tmp_path / "system" / "projects").mkdir(parents=True)
    (tmp_path / "system" / "agari.md").write_text("# not a project\n")
    assert (
        commit_builder._resolve_agari(str(tmp_path), "../")
        == commit_builder.DirectionalResolution.MISSING
    )


def test_resolve_agari_token_with_slash_never_escapes_projects_dir(tmp_path):
    # A decoy agari.md sitting exactly where `../doctrine` would resolve to
    # (one level above system/projects/) — proves the containment check
    # catches it even when a real file sits at the escaped path.
    (tmp_path / "system" / "projects").mkdir(parents=True)
    _write_agari(tmp_path / "system", "doctrine")
    assert (
        commit_builder._resolve_agari(str(tmp_path), "../doctrine")
        == commit_builder.DirectionalResolution.MISSING
    )


def _write_michi(system_dir: Path, slugs: list[str]) -> None:
    system_dir.mkdir(parents=True, exist_ok=True)
    body = "# 道 Michi\n\n"
    for i, slug in enumerate(slugs, start=1):
        body += f"## Way {i} — a Way  (slug: `{slug}`)\n\n"
    (system_dir / "michi.md").write_text(body)


def test_resolve_michi_declared_way_resolves(tmp_path):
    _write_michi(tmp_path / "system", ["sharpen-by-living", "nothing-unproven"])
    assert (
        commit_builder._resolve_michi(str(tmp_path), "sharpen-by-living")
        == commit_builder.DirectionalResolution.RESOLVES
    )


def test_resolve_michi_undeclared_way_is_missing(tmp_path):
    _write_michi(tmp_path / "system", ["sharpen-by-living"])
    assert (
        commit_builder._resolve_michi(str(tmp_path), "not-a-real-way")
        == commit_builder.DirectionalResolution.MISSING
    )


def test_resolve_michi_file_absent_is_uncheckable(tmp_path):
    assert (
        commit_builder._resolve_michi(str(tmp_path), "sharpen-by-living")
        == commit_builder.DirectionalResolution.UNCHECKABLE
    )


def test_resolve_michi_placeholder_with_no_ways_is_uncheckable_not_missing(tmp_path):
    # A fresh instance before kensaiapp-michi has run — every commit must
    # not be refused just because the Michi hasn't been declared yet.
    system_dir = tmp_path / "system"
    system_dir.mkdir(parents=True)
    (system_dir / "michi.md").write_text(
        "# 道 Michi — <instance>'s Way(s)\n\n"
        "> PLACEHOLDER — declare at instance setup.\n"
    )
    assert (
        commit_builder._resolve_michi(str(tmp_path), "sharpen-by-living")
        == commit_builder.DirectionalResolution.UNCHECKABLE
    )


def test_resolve_michi_real_stamped_placeholder_is_uncheckable_not_missing(tmp_path):
    # The placeholder a fresh instance ACTUALLY carries — `spawn_satellite.py`
    # stamps `core/templates/michi_template.md` into `system/michi.md`,
    # substituting `<instance>` and nothing else, so the template's own
    # example marker lands verbatim. It declares no Ways, so every referent
    # against it is UNCHECKABLE: an instance before `kensaiapp-michi` has run
    # must not have every commit refused.
    template = (Path(__file__).parent.parent / "templates" / "michi_template.md").read_text(
        encoding="utf-8"
    )
    system_dir = tmp_path / "system"
    system_dir.mkdir(parents=True)
    (system_dir / "michi.md").write_text(template.replace("<instance>", "kensaiapp-fresh"))
    assert (
        commit_builder._resolve_michi(str(tmp_path), "sharpen-by-living")
        == commit_builder.DirectionalResolution.UNCHECKABLE
    )


def test_resolve_michi_several_ways_each_slug_resolves(tmp_path):
    slugs = ["sharpen-by-living", "nothing-unproven", "production-grade", "fit-to-publish"]
    _write_michi(tmp_path / "system", slugs)
    for slug in slugs:
        assert (
            commit_builder._resolve_michi(str(tmp_path), slug)
            == commit_builder.DirectionalResolution.RESOLVES
        )


def test_resolve_michi_slug_only_in_prose_with_no_marker_is_missing(tmp_path):
    system_dir = tmp_path / "system"
    _write_michi(system_dir, ["sharpen-by-living"])
    with (system_dir / "michi.md").open("a") as fh:
        fh.write("\nSee also the mention of `nothing-unproven` in this prose, with no marker.\n")
    assert (
        commit_builder._resolve_michi(str(tmp_path), "nothing-unproven")
        == commit_builder.DirectionalResolution.MISSING
    )


# ── _resolve_shukuba — the referent that legitimately sits in three
#    different folders (root/trail/parked) under any project, written two
#    different ways (bare slug or the full <date>_<slug> stem). Never
#    searches system/shukuba/, the instance router. ─────────────────────────

def _write_station(
    shukuba_dir: Path, stem: str, lifecycle: str | None = None
) -> None:
    """Write a station `.md` file at `shukuba_dir` (root) or one of its
    lifecycle subfolders (`trail`, `parked`)."""
    target_dir = shukuba_dir if lifecycle is None else shukuba_dir / lifecycle
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / f"{stem}.md").write_text(f"# station — {stem}\n")


def test_resolve_shukuba_bare_slug_at_root_resolves(tmp_path):
    shukuba = tmp_path / "system" / "projects" / "p" / "journey" / "shukuba"
    _write_station(shukuba, "2026-08-24_x")
    assert (
        commit_builder._resolve_shukuba(str(tmp_path), "x")
        == commit_builder.DirectionalResolution.RESOLVES
    )


def test_resolve_shukuba_full_dated_stem_at_root_resolves(tmp_path):
    shukuba = tmp_path / "system" / "projects" / "p" / "journey" / "shukuba"
    _write_station(shukuba, "2026-08-24_x")
    assert (
        commit_builder._resolve_shukuba(str(tmp_path), "2026-08-24_x")
        == commit_builder.DirectionalResolution.RESOLVES
    )


def test_resolve_shukuba_station_only_in_trail_resolves_the_close_case(tmp_path):
    shukuba = tmp_path / "system" / "projects" / "p" / "journey" / "shukuba"
    _write_station(shukuba, "2026-08-24_x", lifecycle="trail")
    assert (
        commit_builder._resolve_shukuba(str(tmp_path), "x")
        == commit_builder.DirectionalResolution.RESOLVES
    )


def test_resolve_shukuba_station_only_in_parked_resolves_the_park_case(tmp_path):
    shukuba = tmp_path / "system" / "projects" / "p" / "journey" / "shukuba"
    _write_station(shukuba, "2026-08-24_x", lifecycle="parked")
    assert (
        commit_builder._resolve_shukuba(str(tmp_path), "x")
        == commit_builder.DirectionalResolution.RESOLVES
    )


def test_resolve_shukuba_no_matching_station_is_missing(tmp_path):
    shukuba = tmp_path / "system" / "projects" / "p" / "journey" / "shukuba"
    _write_station(shukuba, "2026-08-24_x")
    assert (
        commit_builder._resolve_shukuba(str(tmp_path), "not-a-real-slug")
        == commit_builder.DirectionalResolution.MISSING
    )


def test_resolve_shukuba_resolves_regardless_of_which_project_owns_it(tmp_path):
    # Existence, not ownership — the search spans every project.
    shukuba = tmp_path / "system" / "projects" / "some-other-project" / "journey" / "shukuba"
    _write_station(shukuba, "2026-08-24_x")
    assert (
        commit_builder._resolve_shukuba(str(tmp_path), "x")
        == commit_builder.DirectionalResolution.RESOLVES
    )


def test_resolve_shukuba_readme_at_root_is_never_a_station(tmp_path):
    shukuba = tmp_path / "system" / "projects" / "p" / "journey" / "shukuba"
    shukuba.mkdir(parents=True)
    (shukuba / "README.md").write_text("placeholder\n")
    assert (
        commit_builder._resolve_shukuba(str(tmp_path), "README")
        == commit_builder.DirectionalResolution.MISSING
    )


def test_resolve_shukuba_instance_router_is_never_searched(tmp_path):
    # A file at system/shukuba/<token>.md and nowhere else — the router is
    # not searched; Shukuba: names a project's station only.
    router = tmp_path / "system" / "shukuba"
    router.mkdir(parents=True)
    (router / "x.md").write_text("# router station\n")
    (tmp_path / "system" / "projects").mkdir(parents=True)
    assert (
        commit_builder._resolve_shukuba(str(tmp_path), "x")
        == commit_builder.DirectionalResolution.MISSING
    )


def test_resolve_shukuba_project_with_no_shukuba_folder_is_skipped_not_raised(tmp_path):
    (tmp_path / "system" / "projects" / "bare-project").mkdir(parents=True)
    assert (
        commit_builder._resolve_shukuba(str(tmp_path), "x")
        == commit_builder.DirectionalResolution.MISSING
    )


def test_resolve_shukuba_no_projects_root_is_uncheckable(tmp_path):
    assert (
        commit_builder._resolve_shukuba(str(tmp_path), "x")
        == commit_builder.DirectionalResolution.UNCHECKABLE
    )


def test_resolve_shukuba_token_with_dotdot_or_slash_is_missing_not_a_read(tmp_path):
    shukuba = tmp_path / "system" / "projects" / "p" / "journey" / "shukuba"
    _write_station(shukuba, "2026-08-24_x")
    assert (
        commit_builder._resolve_shukuba(str(tmp_path), "../x")
        == commit_builder.DirectionalResolution.MISSING
    )
    assert (
        commit_builder._resolve_shukuba(str(tmp_path), "p/journey/shukuba/2026-08-24_x")
        == commit_builder.DirectionalResolution.MISSING
    )


def test_resolve_shukuba_non_md_file_matching_the_token_is_missing(tmp_path):
    shukuba = tmp_path / "system" / "projects" / "p" / "journey" / "shukuba"
    shukuba.mkdir(parents=True)
    (shukuba / "x.txt").write_text("not a station\n")
    assert (
        commit_builder._resolve_shukuba(str(tmp_path), "x")
        == commit_builder.DirectionalResolution.MISSING
    )


# ── _directional_refusal — the parser and the three resolvers composed into
#    the builder's house refusal shape: a message to print, or None to
#    proceed. Refuses on MISSING, and on a Shukuba:/Agari: line with a
#    reading where its station or project belongs; RESOLVES, UNCHECKABLE and
#    an unparseable directional all proceed. ─────────────────────────────────

_REFUSAL_PREFIX = "commit_builder: refusing to commit —"


def test_directional_refusal_none_when_unparseable():
    assert commit_builder._directional_refusal(".", "Role: Developer") is None


def test_directional_refusal_none_when_reading_not_a_referent(tmp_path):
    assert commit_builder._directional_refusal(
        str(tmp_path), "Shukuba: none — x"
    ) is None


@pytest.mark.parametrize("directional", [
    "Shukuba: progress: check-names-invalid-metric-values",
    "Shukuba: aside: hygiene",
    "Shukuba: progress — x",
    "Agari: progress: defines the done",
    "Agari: aside: hygiene",
])
def test_directional_refusal_when_shukuba_or_agari_names_nothing(tmp_path, directional):
    # The 2026-10-24 tobiishi-open commit in a satellite wrote the first line,
    # and the panel could not place the change under its station. A Shukuba:
    # or Agari: line names its station or project before its reading.
    refusal = commit_builder._directional_refusal(str(tmp_path), directional)
    assert refusal is not None
    assert refusal.splitlines()[0].startswith(_REFUSAL_PREFIX)
    form = directional.split(":")[0]
    assert "names no " in refusal
    assert f"{form}: <" in refusal


def test_directional_refusal_shukuba_naming_nothing_names_the_agari_fallback(tmp_path):
    # A committer who wrote `Shukuba: aside:` may have no station open; the
    # refusal names the line doctrine gives that case, not only a station.
    refusal = commit_builder._directional_refusal(str(tmp_path), "Shukuba: aside: hygiene")
    assert "Agari: <project> — " in refusal
    agari_refusal = commit_builder._directional_refusal(str(tmp_path), "Agari: aside: hygiene")
    assert "With no station open" not in agari_refusal


@pytest.mark.parametrize("directional", [
    "Michi: aside: hygiene",
    "Agari: none — x",
])
def test_directional_refusal_none_for_the_forms_that_name_nothing_legally(tmp_path, directional):
    assert commit_builder._directional_refusal(str(tmp_path), directional) is None


def test_directional_refusal_none_when_resolves(tmp_path):
    _write_agari(tmp_path / "system" / "projects", "doctrine")
    assert commit_builder._directional_refusal(
        str(tmp_path), "Agari: doctrine — progress: x"
    ) is None


def test_directional_refusal_none_when_uncheckable(tmp_path):
    # No system/projects/ at all — an external product repo.
    assert commit_builder._directional_refusal(
        str(tmp_path), "Agari: doctrine — progress: x"
    ) is None


def test_directional_refusal_message_when_missing(tmp_path):
    (tmp_path / "system" / "projects" / "doctrine").mkdir(parents=True)
    refusal = commit_builder._directional_refusal(
        str(tmp_path), "Agari: versioning — progress: x"
    )
    assert refusal is not None
    assert refusal != ""


def test_directional_refusal_first_line_has_the_house_prefix(tmp_path):
    (tmp_path / "system" / "projects" / "doctrine").mkdir(parents=True)
    refusal = commit_builder._directional_refusal(
        str(tmp_path), "Agari: versioning — progress: x"
    )
    assert refusal.splitlines()[0].startswith(_REFUSAL_PREFIX)


def test_directional_refusal_agari_names_form_and_referent_and_path(tmp_path):
    (tmp_path / "system" / "projects" / "doctrine").mkdir(parents=True)
    refusal = commit_builder._directional_refusal(
        str(tmp_path), "Agari: versioning — progress: x"
    )
    assert "Agari" in refusal
    assert "versioning" in refusal
    assert "system/projects/versioning/agari.md" in refusal


def test_directional_refusal_michi_names_form_and_referent_and_path(tmp_path):
    _write_michi(tmp_path / "system", ["sharpen-by-living"])
    refusal = commit_builder._directional_refusal(
        str(tmp_path), "Michi: not-a-real-way — serves: x"
    )
    assert refusal is not None
    assert "Michi" in refusal
    assert "not-a-real-way" in refusal
    assert "system/michi.md" in refusal


def test_directional_refusal_shukuba_names_form_referent_and_all_three_folders(tmp_path):
    (tmp_path / "system" / "projects" / "p").mkdir(parents=True)
    refusal = commit_builder._directional_refusal(
        str(tmp_path), "Shukuba: not-a-real-slug — progress: x"
    )
    assert refusal is not None
    assert "Shukuba" in refusal
    assert "not-a-real-slug" in refusal
    assert "journey/shukuba" in refusal
    assert "trail" in refusal
    assert "parked" in refusal


def test_directional_refusal_never_says_directional_required_or_removable(tmp_path):
    (tmp_path / "system" / "projects" / "doctrine").mkdir(parents=True)
    refusal = commit_builder._directional_refusal(
        str(tmp_path), "Agari: versioning — progress: x"
    )
    lowered = refusal.lower()
    assert "required" not in lowered
    assert "remove" not in lowered


# ── wiring — _directional_refusal on the CLI commit path, run BEFORE any
#    staging so a refusal leaves the index and the working tree exactly as
#    it found them. Runs regardless of --take-index/--allow-empty; the merge
#    op is untouched (it takes no --directional). ───────────────────────────

def test_directional_wiring_cli_bad_agari_refuses_and_names_referent(tmp_path, capsys):
    _init_repo(tmp_path)
    (tmp_path / "system" / "projects" / "doctrine").mkdir(parents=True)
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: work",
        "--actor", "developer",
        "--add", "work.txt",
        "--directional", "Agari: versioning — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    assert "versioning" in capsys.readouterr().err


def test_directional_wiring_cli_refusal_leaves_add_unstaged_and_head_unmoved(tmp_path):
    head_before = _init_repo(tmp_path)
    head_sha_before = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    (tmp_path / "system" / "projects" / "doctrine").mkdir(parents=True)
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: work",
        "--actor", "developer",
        "--add", "work.txt",
        "--directional", "Agari: versioning — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    staged = subprocess.run(
        ["git", "-C", str(tmp_path), "diff", "--cached", "--name-only"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "work.txt" not in staged
    head_sha_after = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert head_sha_after == head_sha_before
    assert head_before  # branch name sanity


def test_directional_wiring_cli_refusal_leaves_rm_target_on_disk_and_tracked(tmp_path):
    _init_repo(tmp_path)

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    (tmp_path / "keep.txt").write_text("keep\n")
    git("add", "keep.txt")
    git("commit", "-q", "-m", "add keep.txt")
    (tmp_path / "system" / "projects" / "doctrine").mkdir(parents=True)

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: work",
        "--actor", "developer",
        "--rm", "keep.txt",
        "--directional", "Agari: versioning — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    assert (tmp_path / "keep.txt").is_file()
    tracked = git("ls-files", "keep.txt")
    assert tracked == "keep.txt"


def test_directional_wiring_cli_good_referent_lands_canonical_trailers(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    _write_agari(tmp_path / "system" / "projects", "tools")
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: real commit through the builder",
        "--body", "Proof the wiring doesn't disturb a resolving referent.",
        "--actor", "developer",
        "--add", "work.txt",
        "--directional", "Agari: tools — progress: builds it",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    body = _commit_body(tmp_path)
    trailer_block = body.strip().split("\n\n")[-1]
    assert trailer_block.splitlines() == [
        "Agari: tools — progress: builds it",
        "Role: Developer",
        "Surface: Claude Code",
        f"Co-Authored-By: {CO_AUTHORED_BY}",
    ]


@pytest.mark.parametrize("directional", [
    "Agari: tools — progress: defines the done",
    "Agari: tools — aside: hygiene",
    "Agari: none — stamps the project",
    "Michi: sharpen — serves: walks the Way",
    "Michi: aside: hygiene",
    "Michi: none — stamps the instance",
])
def test_directional_wiring_cli_no_open_station_commits_with_agari_or_michi(
        tmp_path, monkeypatch, directional):
    # With no station open, a commit names the project's Agari or the
    # instance's Michi instead; refusing a Shukuba: line that names no
    # station must leave every one of those forms committing.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    _write_agari(tmp_path / "system" / "projects", "tools")
    shukuba = tmp_path / "system" / "projects" / "tools" / "journey" / "shukuba"
    shukuba.mkdir(parents=True)
    (shukuba / "README.md").write_text("# Shukuba\n")
    _write_michi(tmp_path / "system", ["sharpen"])
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: work",
        "--actor", "developer",
        "--add", "work.txt",
        "--directional", directional,
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    trailer_block = _commit_body(tmp_path).strip().split("\n\n")[-1]
    assert trailer_block.splitlines()[0] == directional


def test_directional_wiring_cli_no_system_dir_at_all_is_never_refused(tmp_path):
    # The shape every other CLI test in this file uses — no system/projects/
    # at all means UNCHECKABLE, never a refusal. This is why the whole
    # existing suite stays green under this wiring.
    _init_repo(tmp_path)
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: work",
        "--actor", "developer",
        "--add", "work.txt",
        "--directional", "Agari: nonexistent-project — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0


def test_directional_wiring_cli_bad_shukuba_refuses(tmp_path, capsys):
    _init_repo(tmp_path)
    (tmp_path / "system" / "projects" / "p").mkdir(parents=True)
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: work",
        "--actor", "developer",
        "--add", "work.txt",
        "--directional", "Shukuba: not-a-real-slug — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    assert "not-a-real-slug" in capsys.readouterr().err


def test_directional_wiring_cli_shukuba_naming_no_station_refuses(tmp_path, capsys):
    _init_repo(tmp_path)
    head = ["git", "-C", str(tmp_path), "rev-parse", "HEAD"]
    head_before = subprocess.run(head, capture_output=True, text=True, check=True).stdout
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "pm: open the change",
        "--actor", "pm",
        "--add", "work.txt",
        "--directional", "Shukuba: progress: check-names-invalid-metric-values",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    assert "names no station" in capsys.readouterr().err
    assert subprocess.run(head, capture_output=True, text=True, check=True).stdout == head_before


def test_directional_wiring_cli_bad_michi_refuses(tmp_path, capsys):
    _init_repo(tmp_path)
    _write_michi(tmp_path / "system", ["sharpen-by-living"])
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: work",
        "--actor", "developer",
        "--add", "work.txt",
        "--directional", "Michi: not-a-real-way — serves: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    assert "not-a-real-way" in capsys.readouterr().err


def test_directional_wiring_cli_shukuba_trail_station_commits_cleanly(tmp_path):
    # The end-to-end close case: shukuba-retire moves the station to trail/
    # BEFORE calling the builder — a root-only check would refuse this.
    _init_repo(tmp_path)
    shukuba = tmp_path / "system" / "projects" / "p" / "journey" / "shukuba"
    _write_station(shukuba, "2026-08-24_x", lifecycle="trail")
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: close shukuba: x",
        "--actor", "developer",
        "--add", "work.txt",
        "--directional", "Shukuba: x — progress: reached, closed to trail",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0


def test_directional_wiring_cli_allow_empty_with_bad_referent_is_refused(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "system" / "projects" / "doctrine").mkdir(parents=True)

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: <key> — implementation complete",
        "--actor", "developer",
        "--directional", "Agari: versioning — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
        "--allow-empty",
    ])

    assert exit_code != 0


def test_directional_wiring_cli_take_index_does_not_waive_this_check(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "system" / "projects" / "doctrine").mkdir(parents=True)
    (tmp_path / "work.txt").write_text("work\n")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "work.txt"],
        capture_output=True, text=True, check=True,
    )

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: work",
        "--actor", "developer",
        "--directional", "Agari: versioning — progress: x",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
        "--take-index",
    ])

    assert exit_code != 0


def test_directional_wiring_merge_op_still_takes_no_directional():
    # The merge parser never grew a --directional — this wiring lives on the
    # commit branch of main() only.
    args = commit_builder._build_arg_parser().parse_args([
        "merge",
        "--branch", "x", "--target-branch", "y", "--description", "z",
        "--actor", "pm", "--merge-context", "m",
        "--surface", "s", "--co-authored-by", "c",
    ])
    assert not hasattr(args, "directional")


def test_directional_wiring_help_mentions_referent_resolution():
    proc = subprocess.run(
        [sys.executable, str(BUILDER), "commit", "--help"],
        capture_output=True, text=True, check=True,
    )
    help_text = proc.stdout.lower()
    assert "resolved" in help_text
    assert "none" in help_text and "progress" in help_text


# ── Workflow-Version: — the third provenance trailer (2026-08-25) ──────────
#
# Its siblings' tests are mirrored deliberately, because the contract is meant
# to be identical everywhere except the read. What is NOT a mirror is the
# marker group at the end: a workflow declares its version in a comment below
# its `meta` block, and getting that wrong is the only way this trailer can
# fail in a way the other two cannot.


def _add_workflow_fixture(
    path: Path, name: str, version: str | None = "1.0.0", *, marker_above_meta: bool = False
) -> None:
    """Create and commit a `.claude/workflows/<name>.js` fixture — the shape
    `resolve_workflow_version` reads. `version=None` writes a workflow with no
    marker at all, for the unresolvable case. `marker_above_meta` writes the
    marker in the position `versioning.md` forbids, so a test can pin that the
    resolver reads it wherever it sits while the doctrine's placement rule is
    enforced by the workflow tests rather than by this reader."""
    wf_dir = path / ".claude" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    marker = f"// Version: {version}\n" if version is not None else ""
    meta = f"export const meta = {{ name: '{name}', description: 'fixture' }}\n"
    body = (marker + meta) if marker_above_meta else (meta + "\n" + marker)
    (wf_dir / f"{name}.js").write_text(body + "\nlog('fixture')\n")
    subprocess.run(
        ["git", "-C", str(path), "add", f".claude/workflows/{name}.js"],
        check=True, capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "commit", "-q", "-m", f"fixture: add {name} workflow"],
        check=True, capture_output=True, text=True,
    )


def test_workflow_version_line_present_and_last():
    message = commit_builder.build_message(
        "commit",
        subject="the conversation produced a design",
        body="A workflow held the loop.",
        role="CTO",
        directional="Shukuba: s — progress: p",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
        workflow_version="sdd-conversation@1.0.0 " + "d" * 40,
    )
    trailer_block = message.split("\n\n")[-1]
    assert trailer_block.splitlines() == [
        "Shukuba: s — progress: p",
        "Role: CTO",
        "Surface: Claude Code",
        f"Co-Authored-By: {CO_AUTHORED_BY}",
        "Workflow-Version: sdd-conversation@1.0.0 " + "d" * 40,
    ]


def test_all_three_provenance_lines_appear_in_order():
    # Three independent facts — which skill ran, which prompt it followed,
    # which workflow drove it — and a capability can genuinely have all three.
    # The order is build_message's explicit sequence, not an accident.
    message = commit_builder.build_message(
        "commit",
        subject="cto: a turn in the conversation",
        body="Skill, prompt and workflow all ran.",
        actor="cto",
        directional="Shukuba: s — progress: p",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
        skill_version="product-sdd@2.0.0 " + "a" * 40,
        prompt_version="sdd_conversation@1.3.0 " + "b" * 40,
        workflow_version="sdd-conversation@1.0.0 " + "c" * 40,
    )
    trailers = message.split("\n\n")[-1].splitlines()
    assert trailers[-3].startswith("Skill-Version: ")
    assert trailers[-2].startswith("Prompt-Version: ")
    assert trailers[-1].startswith("Workflow-Version: ")


def test_no_workflow_version_line_when_none():
    message = commit_builder.build_message(
        "commit",
        subject="a hand-authored commit",
        body="No workflow drove this.",
        role="PM",
        directional="Agari: p — progress: x",
        surface="Claude Code",
        co_authored_by=CO_AUTHORED_BY,
    )
    assert "Workflow-Version:" not in message


def test_merge_ignores_workflow_version():
    # A merge is authored by its authorizer, never by a producing component.
    message = commit_builder.build_message(
        "merge",
        branch="b", target_branch="main", description="d",
        authorizer="Product", merge_context="ctx",
        surface="Claude Code", co_authored_by=CO_AUTHORED_BY,
        workflow_version="sdd-conversation@1.0.0 " + "d" * 40,
    )
    assert "Workflow-Version:" not in message


def test_resolve_workflow_version_format_and_full_sha(tmp_path):
    _init_repo(tmp_path)
    _add_workflow_fixture(tmp_path, "sdd-conversation", version="2.1.0")

    result = commit_builder.resolve_workflow_version(str(tmp_path), "sdd-conversation")

    assert result is not None
    assert re.match(r"^sdd-conversation@\d+\.\d+\.\d+ [0-9a-f]{40}$", result)


def test_resolve_workflow_version_no_name_returns_none(tmp_path):
    # Explicit-only. Nothing is inferred from the actor or from what is on disk.
    _init_repo(tmp_path)
    _add_workflow_fixture(tmp_path, "sdd-conversation")
    assert commit_builder.resolve_workflow_version(str(tmp_path)) is None
    assert commit_builder.resolve_workflow_version(str(tmp_path), None) is None


def test_resolve_workflow_version_unresolvable_returns_none(tmp_path):
    # Never fabricate, never raise. (a) absent; (b) present with no marker.
    _init_repo(tmp_path)
    assert commit_builder.resolve_workflow_version(str(tmp_path), "sdd-conversation") is None
    _add_workflow_fixture(tmp_path, "sdd-conversation", version=None)
    assert commit_builder.resolve_workflow_version(str(tmp_path), "sdd-conversation") is None


def test_resolve_workflow_version_uncommitted_source_returns_none(tmp_path):
    # Present AND marked, but with no committed revision: the semver resolves
    # from disk and there is no source SHA, so the value is None.
    _init_repo(tmp_path)
    wf_dir = tmp_path / ".claude" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "sdd-conversation.js").write_text(
        "export const meta = { name: 'x' }\n\n// Version: 1.0.0\n"
    )
    # Deliberately NOT staged/committed.
    assert commit_builder.resolve_workflow_version(str(tmp_path), "sdd-conversation") is None


def test_resolve_workflow_version_names_the_workflow_not_another(tmp_path):
    # Two on disk, so a wrong resolution would still find *a* workflow.
    _init_repo(tmp_path)
    _add_workflow_fixture(tmp_path, "development", version="1.0.0")
    _add_workflow_fixture(tmp_path, "sdd-conversation", version="2.1.0")

    result = commit_builder.resolve_workflow_version(str(tmp_path), "sdd-conversation")

    assert result is not None
    assert result.startswith("sdd-conversation@"), result


def test_resolve_workflow_version_sha_tracks_the_workflow_not_head(tmp_path):
    # The SHA is the workflow's last-modifying commit, never repo HEAD.
    _init_repo(tmp_path)
    _add_workflow_fixture(tmp_path, "sdd-conversation", version="2.1.0")
    before = commit_builder.resolve_workflow_version(str(tmp_path), "sdd-conversation")
    (tmp_path / "unrelated.txt").write_text("x\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "unrelated.txt"],
                   check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "unrelated"],
                   check=True, capture_output=True, text=True)
    after = commit_builder.resolve_workflow_version(str(tmp_path), "sdd-conversation")
    assert before == after


# ── The marker group — the only part that is not a mirror of the siblings ──


def test_workflow_marker_is_read_below_the_meta_block(tmp_path):
    # The doctrine's placement — `versioning.md` requires the marker BELOW
    # `meta`, because the workflow tests execute the real bytes through an
    # anchored replace that anything above the block would no-op. The fixture
    # helper writes it there by default; this pins that the reader finds it.
    _init_repo(tmp_path)
    _add_workflow_fixture(tmp_path, "sdd-conversation", version="3.2.1")
    result = commit_builder.resolve_workflow_version(str(tmp_path), "sdd-conversation")
    assert result is not None and result.startswith("sdd-conversation@3.2.1 ")


def test_workflow_frontmatter_is_not_a_marker(tmp_path):
    # A workflow carrying a frontmatter-shaped `version:` line and no comment
    # marker resolves to nothing. The two readers are separate on purpose, and
    # reusing the frontmatter one here would have silently "worked" on a file
    # that does not follow the convention.
    _init_repo(tmp_path)
    wf_dir = tmp_path / ".claude" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "odd.js").write_text('---\nversion: "9.9.9"\n---\nexport const meta = {}\n')
    subprocess.run(["git", "-C", str(tmp_path), "add", ".claude/workflows/odd.js"],
                   check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "odd"],
                   check=True, capture_output=True, text=True)
    assert commit_builder.resolve_workflow_version(str(tmp_path), "odd") is None


def test_workflow_marker_first_match_wins(tmp_path):
    # No delimiter bounds the scan, so a later mention must not override the
    # real marker. First whole-line match wins.
    _init_repo(tmp_path)
    wf_dir = tmp_path / ".claude" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "two.js").write_text(
        "export const meta = {}\n\n// Version: 1.2.3\n\n"
        "// Historical note, do not read as the marker:\n// Version: 9.9.9\n"
    )
    subprocess.run(["git", "-C", str(tmp_path), "add", ".claude/workflows/two.js"],
                   check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "two"],
                   check=True, capture_output=True, text=True)
    result = commit_builder.resolve_workflow_version(str(tmp_path), "two")
    assert result is not None and result.startswith("two@1.2.3 "), result


def test_end_to_end_explicit_workflow_lands_line(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    _add_workflow_fixture(tmp_path, "sdd-conversation", version="1.0.0")
    (tmp_path / "SDD.md").write_text("# SDD\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "cto: the SDD lands out of the conversation",
        "--body", "Explicit --workflow wires the provenance line.",
        "--role", "CTO",
        "--workflow", "sdd-conversation",
        "--add", "SDD.md",
        "--directional", "Shukuba: s — progress: p",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    body = _commit_body(tmp_path)
    matches = re.findall(r"^Workflow-Version: .*$", body, flags=re.MULTILINE)
    assert len(matches) == 1
    assert re.match(
        r"^Workflow-Version: sdd-conversation@\d+\.\d+\.\d+ [0-9a-f]{40}$", matches[0]
    )
    assert body.strip().split("\n\n")[-1].splitlines()[-1] == matches[0]
    # Independent facts: no skill and no prompt ran, so neither line appears.
    assert "Skill-Version:" not in body
    assert "Prompt-Version:" not in body


def test_end_to_end_no_workflow_flag_omits_line(tmp_path, monkeypatch):
    # A workflow present on disk does not stamp itself — explicit-only.
    _init_repo(tmp_path)
    monkeypatch.setattr(commit_builder, "instance_repo_root", lambda: tmp_path)
    _add_workflow_fixture(tmp_path, "sdd-conversation", version="1.0.0")
    (tmp_path / "f.md").write_text("x\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path), "commit",
        "--subject", "a commit with no workflow named",
        "--body", "b", "--role", "PM",
        "--add", "f.md",
        "--directional", "Agari: p — progress: x",
        "--surface", "Claude Code", "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code == 0
    assert "Workflow-Version:" not in _commit_body(tmp_path)


# ── --bump reaches every marker form, not frontmatter alone ─────────────────
# `2026-08-28_a-rule-with-no-surface-for-43-files` / station
# `the-merge-can-move-every-marker`. `versioning.md` binds every versioned
# artifact to the same rule — "A branch never edits a version marker" (:100-104)
# — and says the digits are "one set whatever the marker's form" (:130-131).
# The tool reached one form of four, so the rule reached no executable in the
# instance: 23 Python files carrying `__version__`, 22 carrying a `# Version:`
# header comment, and 4 workflows carrying `// Version:`.
#
# THE SHELL FORM IS A CHANGELOG STACK, AND THAT IS WHY IT PREPENDS. Measured on
# `ce4ecb63`: 19 of the 22 header-comment files carry two or more `# Version:`
# lines, newest-first (`core/launchers/cold-read/test_cold_read.py:199-201`
# states the convention), and 20 of 22 topmost lines carry an `— description`
# naming what THAT version changed. Rewriting the digits in place would relabel
# an old note with a new number in 20 files, unreviewed, at merge time. So a
# shell bump prepends a new entry above the current one and leaves the stack
# below it untouched — which is what `cd669155` did by hand. Python and
# workflow markers are one bare line each and rewrite in place.

def _python_module(path: Path, version: str, preamble: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'"""A module."""\n{preamble}\n__version__ = "{version}"\n\n'
        "def f():\n    return 1\n"
    )


def _shell_script(path: Path, entries: list[tuple[str, str]]) -> None:
    """A shell file with its `# Version:` stack, newest-first."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["#!/usr/bin/env bash", "#", "# thing.sh — a thing.", "#"]
    lines += [f"# Version: {v} — {d}" for v, d in entries]
    lines += ["", 'echo "hi"']
    path.write_text("\n".join(lines) + "\n")


def _workflow_script(path: Path, version: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "export const meta = {\n  name: 'x',\n}\n\n"
        f"// Version: {version}\n\nconsole.log(1)\n"
    )


def test_read_marker_semver_reads_every_form(tmp_path):
    _versioned(tmp_path / "doctrine.md", "1.2.0")
    _python_module(tmp_path / "tool.py", "2.3.4")
    _shell_script(tmp_path / "script.sh", [("3.4.5", "the newest thing")])
    _workflow_script(tmp_path / "flow.js", "4.5.6")

    assert commit_builder._read_marker_semver(tmp_path / "doctrine.md") == (
        "frontmatter", "1.2.0"
    )
    assert commit_builder._read_marker_semver(tmp_path / "tool.py") == (
        "python", "2.3.4"
    )
    assert commit_builder._read_marker_semver(tmp_path / "script.sh") == (
        "shell", "3.4.5"
    )
    assert commit_builder._read_marker_semver(tmp_path / "flow.js") == (
        "workflow", "4.5.6"
    )


def test_read_marker_semver_takes_the_topmost_shell_entry(tmp_path):
    # Newest-first: the stack's head is the live version, and an older entry
    # further down must never win.
    _shell_script(
        tmp_path / "script.sh",
        [("1.5.0", "newest"), ("1.4.0", "older"), ("1.0.0", "oldest")],
    )
    assert commit_builder._read_marker_semver(tmp_path / "script.sh") == (
        "shell", "1.5.0"
    )


def test_read_marker_semver_is_none_when_no_form_matches(tmp_path):
    (tmp_path / "plain.md").write_text("no marker of any kind here\n")
    assert commit_builder._read_marker_semver(tmp_path / "plain.md") is None
    assert commit_builder._read_marker_semver(tmp_path / "absent.md") is None


def test_read_marker_semver_prefers_frontmatter_over_a_body_lookalike(tmp_path):
    # A doctrine file documenting the Python marker carries a line that the
    # python reader would match. Frontmatter is checked first and anchored at
    # line 1, so the file's real marker wins.
    (tmp_path / "doc.md").write_text(
        '---\nversion: "1.0.0"\n---\n\nThe Python form is:\n\n'
        '__version__ = "9.9.9"\n'
    )
    assert commit_builder._read_marker_semver(tmp_path / "doc.md") == (
        "frontmatter", "1.0.0"
    )


def _merge_with_bump(tmp_path, main_branch, spec, description="bring it in"):
    """Merge `feature` into the checked-out branch with one --bump spec."""
    return commit_builder.main([
        "--repo", str(tmp_path),
        "merge",
        "--branch", "feature",
        "--target-branch", main_branch,
        "--description", description,
        "--branch-commits", "feature: the edit",
        "--actor", "pm",
        "--merge-context", "manual",
        "--bump", spec,
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])


def _branch_with_edit(tmp_path, filename: str, edit) -> str:
    """Seed `filename`, branch, apply `edit` on the branch, return to the
    target branch. The branch never touches the marker — that is the rule."""
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    main_branch = _init_repo(tmp_path)
    git("add", filename)
    git("commit", "-q", "-m", f"seed {filename}")
    git("checkout", "-q", "-b", "feature")
    edit()
    git("commit", "-qam", "feature: the edit, marker untouched")
    git("checkout", "-q", main_branch)
    return main_branch


def test_merge_bump_moves_a_python_version(tmp_path):
    tool = tmp_path / "core/tool.py"
    _python_module(tool, "1.0.0")
    main_branch = _branch_with_edit(
        tmp_path, "core/tool.py",
        lambda: _python_module(tool, "1.0.0", preamble="\n# an added behaviour\n"),
    )

    assert _merge_with_bump(tmp_path, main_branch, "core/tool.py=minor") == 0
    text = tool.read_text()
    assert '__version__ = "1.1.0"' in text
    assert "an added behaviour" in text
    assert '__version__ = "1.0.0"' not in text
    # Inside the merge commit: two parents, and the file in its own diff.
    show = subprocess.run(
        ["git", "-C", str(tmp_path), "show", "--format=", "--name-only", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "core/tool.py" in show
    parents = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-list", "--parents", "-1", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert len(parents) == 3


def test_merge_bump_reads_a_file_the_branch_renamed_at_its_new_path(tmp_path):
    """A --bump path that is absent on the target until the merge brings it — a rename the branch
    made — is checked against the branch's copy, then bumped after the merge. Before, the
    up-front check read the target's working tree, found no file, and refused the merge
    (2026-10-12, a satellite seal: a module renamed into a package directory)."""
    tool = tmp_path / "core/tool.py"
    _python_module(tool, "1.0.0")

    def rename_and_edit():
        moved = tmp_path / "core" / "pkg" / "tool.py"
        moved.parent.mkdir(parents=True)
        subprocess.run(["git", "-C", str(tmp_path), "mv", "core/tool.py", "core/pkg/tool.py"], check=True)
        _python_module(moved, "1.0.0", preamble="\n# an added behaviour\n")
        subprocess.run(["git", "-C", str(tmp_path), "add", "core/pkg/tool.py"], check=True)

    main_branch = _branch_with_edit(tmp_path, "core/tool.py", rename_and_edit)

    assert _merge_with_bump(tmp_path, main_branch, "core/pkg/tool.py=minor") == 0
    text = (tmp_path / "core" / "pkg" / "tool.py").read_text()
    assert '__version__ = "1.1.0"' in text
    assert "an added behaviour" in text
    assert not tool.exists()


def test_merge_still_refuses_a_bump_path_absent_on_both_sides(tmp_path, capsys):
    tool = tmp_path / "core/tool.py"
    _python_module(tool, "1.0.0")
    main_branch = _branch_with_edit(
        tmp_path, "core/tool.py",
        lambda: _python_module(tool, "1.0.0", preamble="\n# an added behaviour\n"),
    )

    assert _merge_with_bump(tmp_path, main_branch, "core/nowhere.py=minor") == 1
    assert "core/nowhere.py=minor — no version marker" in capsys.readouterr().err


def test_merge_bump_moves_a_workflow_marker(tmp_path):
    flow = tmp_path / "core/flow.js"
    _workflow_script(flow, "1.0.1")
    main_branch = _branch_with_edit(
        tmp_path, "core/flow.js", lambda: flow.write_text(
            flow.read_text().replace("console.log(1)", "console.log(2)")
        ),
    )

    assert _merge_with_bump(tmp_path, main_branch, "core/flow.js=patch") == 0
    text = flow.read_text()
    assert "// Version: 1.0.2" in text
    assert "// Version: 1.0.1" not in text
    assert "console.log(2)" in text
    # The marker stays below the meta block, where the workflow tests need it.
    assert text.index("export const meta") < text.index("// Version:")


def _plugin_manifest(path: Path, version: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "{\n"
        '  "name": "sample-mod",\n'
        f'  "version": "{version}",\n'
        '  "description": "an invented mod"\n'
        "}\n"
    )


def test_merge_bump_moves_a_plugin_manifest_version(tmp_path):
    manifest = tmp_path / "core/plugin.json"
    _plugin_manifest(manifest, "1.0.0")
    main_branch = _branch_with_edit(
        tmp_path, "core/plugin.json", lambda: manifest.write_text(
            manifest.read_text().replace("an invented mod", "an edited mod")
        ),
    )

    assert _merge_with_bump(tmp_path, main_branch, "core/plugin.json=minor") == 0
    text = manifest.read_text()
    assert '"version": "1.1.0",' in text
    assert '"1.0.0"' not in text
    assert "an edited mod" in text


def test_markers_reports_the_plugin_form(tmp_path, capsys):
    target = tmp_path / "plugin.json"
    _plugin_manifest(target, "2.3.4")

    assert commit_builder.main(["markers", str(target)]) == 0
    assert capsys.readouterr().out.strip("\n") == f"{target}: plugin line 3 semver 2.3.4"


def test_a_plugin_marker_is_the_top_level_version_not_a_nested_one(tmp_path):
    # The nested value equals the top-level one, so only the depth tells them apart.
    target = tmp_path / "plugin.json"
    target.write_text(
        "{\n"
        '  "dependencies": {\n'
        '    "version": "1.2.0"\n'
        "  },\n"
        '  "version": "1.2.0"\n'
        "}\n"
    )

    assert commit_builder._locate_marker(target) == ("plugin", 4, "1.2.0")


def test_merge_bump_of_a_plugin_moves_its_own_version_not_a_nested_one(tmp_path):
    manifest = tmp_path / "core/plugin.json"
    manifest.parent.mkdir()
    manifest.write_text(
        '{"dependencies": {"version": "1.0.0"}, "version": "1.0.0", "name": "m"}\n'
    )
    main_branch = _branch_with_edit(
        tmp_path, "core/plugin.json", lambda: manifest.write_text(
            manifest.read_text().replace('"m"', '"m2"')
        ),
    )

    assert _merge_with_bump(tmp_path, main_branch, "core/plugin.json=patch") == 0
    assert manifest.read_text() == (
        '{"dependencies": {"version": "1.0.0"}, "version": "1.0.1", "name": "m2"}\n'
    )


@pytest.mark.parametrize("text", [
    '{"name": "m", "version": "1.0.0"}',
    '{\n  "version" : "1.0.0"\n}',
    '{\n  "version": "1.0.0", "name": "m"\n}',
])
def test_a_plugin_marker_is_read_in_any_layout(tmp_path, text):
    target = tmp_path / "plugin.json"
    target.write_text(text)

    located = commit_builder._locate_marker(target)
    assert located is not None and located[0::2] == ("plugin", "1.0.0")


@pytest.mark.parametrize("text", [
    '{"version": "1.0"}',
    '["version", "1.0.0"]',
    '{"name": "m"}',
])
def test_a_plugin_manifest_without_a_top_level_semver_carries_no_marker(tmp_path, text):
    target = tmp_path / "plugin.json"
    target.write_text(text)

    assert commit_builder._locate_marker(target) is None


def test_a_json_file_not_named_plugin_json_carries_no_marker(tmp_path):
    target = tmp_path / "package.json"
    _plugin_manifest(target, "1.0.0")

    assert commit_builder._locate_marker(target) is None


def test_a_plugin_manifest_that_does_not_parse_carries_no_marker(tmp_path):
    target = tmp_path / "plugin.json"
    target.write_text('{\n  "version": "1.0.0",\n')

    assert commit_builder._locate_marker(target) is None


def test_merge_bump_prepends_a_shell_entry_and_keeps_the_old_one(tmp_path):
    script = tmp_path / "core/script.sh"
    _shell_script(script, [("1.4.0", "the previous change")])
    before_line = "# Version: 1.4.0 — the previous change"
    main_branch = _branch_with_edit(
        tmp_path, "core/script.sh", lambda: script.write_text(
            script.read_text().replace('echo "hi"', 'echo "hello"')
        ),
    )

    assert _merge_with_bump(
        tmp_path, main_branch, "core/script.sh=minor",
        description="the greeting is spelled out",
    ) == 0
    lines = script.read_text().splitlines()
    # The new entry sits directly above the old one, and carries the merge's
    # own description — never the old entry's, which belongs to 1.4.0.
    assert "# Version: 1.5.0 — the greeting is spelled out" in lines
    assert before_line in lines, "the previous entry was rewritten, not kept"
    assert lines.index("# Version: 1.5.0 — the greeting is spelled out") == (
        lines.index(before_line) - 1
    )
    assert 'echo "hello"' in script.read_text()


def test_a_shell_bump_folds_a_multiline_description_onto_one_line(tmp_path):
    # A comment line is one line. A description carrying a newline would break
    # the file it is written into, so whitespace is collapsed rather than
    # refused — the merge's `--description` is specified as one line, and this
    # is the guard for when it is not.
    script = tmp_path / "core/script.sh"
    _shell_script(script, [("1.0.0", "first")])
    main_branch = _branch_with_edit(
        tmp_path, "core/script.sh", lambda: script.write_text(
            script.read_text() + 'echo "more"\n'
        ),
    )

    assert _merge_with_bump(
        tmp_path, main_branch, "core/script.sh=patch",
        description="two lines\nbecome one",
    ) == 0
    assert "# Version: 1.0.1 — two lines become one" in script.read_text().splitlines()


def test_merge_bump_of_a_python_module_leaves_a_matching_string_alone(tmp_path):
    # The old `_apply_bumps` did a whole-file `text.replace('"<current>"', …, 1)`
    # — safe for frontmatter, which is always first, and wrong for a module
    # whose docstring quotes the same value above the marker. The rewrite is
    # line-targeted, on the line the reader matched.
    tool = tmp_path / "core/tool.py"
    _python_module(tool, "1.0.0", preamble='\nEXAMPLE = "1.0.0"  # not the marker\n')
    main_branch = _branch_with_edit(
        tmp_path, "core/tool.py", lambda: tool.write_text(
            tool.read_text().replace("return 1", "return 2")
        ),
    )

    assert _merge_with_bump(tmp_path, main_branch, "core/tool.py=major") == 0
    text = tool.read_text()
    assert 'EXAMPLE = "1.0.0"  # not the marker' in text
    assert '__version__ = "2.0.0"' in text


def test_bump_refusal_names_every_form_it_looked_for(tmp_path, capsys):
    # A file carrying no marker of ANY form still refuses, before the merge
    # runs — and the refusal says which five forms were looked for, so the
    # caller can tell "wrong path" from "this file carries no marker".
    plain = tmp_path / "core/plain.md"
    plain.parent.mkdir()
    plain.write_text("no marker of any kind\n")
    main_branch = _branch_with_edit(
        tmp_path, "core/plain.md",
        lambda: plain.write_text("no marker of any kind, edited\n"),
    )

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    before = git("rev-parse", "HEAD")

    assert _merge_with_bump(tmp_path, main_branch, "core/plain.md=minor") != 0
    err = capsys.readouterr().err
    for form in ("version:", "__version__", "// Version:", "# Version:", "plugin.json"):
        assert form in err, f"the refusal never names the {form!r} form"
    assert git("rev-parse", "HEAD") == before


# ── the reach is proved against the instance, not against fixtures ──────────
# The seed's checklist item says "prove it against files of all three forms".
# A fixture proves the reader parses a shape someone wrote for it; only the
# real set proves the rule reaches the files it is about — and it stays true
# when a file is added, which a hard-coded count would not.

def _marker_carrying_executables() -> list[str]:
    """Every tracked file in the instance carrying one of the three forms the
    merge could not reach. A test file is excluded by rule, not by
    convenience: `versioning.md` § Where the test lands gives test files no
    marker ("a test is proven by running"), so a match inside one is a fixture
    string — `.claude/hooks/test_manifest_salience.py:21` is exactly that."""
    root = commit_builder.instance_repo_root()
    found: set[str] = set()
    for pattern in (r"^__version__ = \"", r"^# Version: ", r"^// Version: "):
        result = subprocess.run(
            ["git", "-C", str(root), "grep", "-l", "-E", pattern],
            capture_output=True, text=True,
        )
        found.update(
            line for line in result.stdout.splitlines()
            if line and not Path(line).name.startswith("test_")
        )
    # A mod's marker is its manifest's `"version"`, found by the file's name.
    manifests = subprocess.run(
        ["git", "-C", str(root), "ls-files", "*/.claude-plugin/plugin.json"],
        capture_output=True, text=True,
    )
    found.update(line for line in manifests.stdout.splitlines() if line)
    return sorted(found)


def test_every_executable_marker_in_the_instance_is_reachable():
    root = commit_builder.instance_repo_root()
    executables = _marker_carrying_executables()
    # The measured set on `ce4ecb63`: 23 Python + 22 header-comment + 4
    # workflows. A floor, not an equality — files get added.
    assert len(executables) >= 45, len(executables)
    unreachable = [
        path for path in executables
        if commit_builder._read_marker_semver(root / path) is None
    ]
    assert unreachable == [], (
        f"{len(unreachable)} marker-carrying files the merge still cannot "
        f"move: {unreachable}"
    )


def test_all_five_forms_are_represented_by_real_files_in_the_instance():
    # Guards the test above from passing vacuously if a form disappears from
    # the tree: each form must still be represented by a real file. The
    # frontmatter arm is this station's own subject, so it anchors there.
    root = commit_builder.instance_repo_root()
    forms = set()
    for path in _marker_carrying_executables():
        marker = commit_builder._read_marker_semver(root / path)
        if marker is not None:
            forms.add(marker[0])
    assert {"python", "shell", "workflow", "plugin"} <= forms, forms
    assert commit_builder._read_marker_semver(
        root / "core/doctrine/governance/versioning.md"
    )[0] == "frontmatter"


def test_merge_refuses_a_blank_branch_commit_entry():
    """A blank entry is refused, not dropped, so the caller's bug is visible.

    `ea557199` on `main` carries a body that is one `-> ` and nothing else. The
    caller built its list with the bash-only `mapfile`, which under zsh leaves the
    array unset, and `"${ARR[@]}"` on an unset array expands to a single empty
    string rather than to no arguments — so the builder received `[""]`.

    Dropping it silently would have produced a merge with no commit list and no
    signal, from a caller that believed it passed eleven. The visible `-> ` is what
    exposed the defect; refusing keeps that visibility and moves it earlier.
    """
    with pytest.raises(ValueError, match="branch_commits"):
        commit_builder.build_message(
            "merge",
            actor="pm",
            branch="2026-07-07_commit-builder",
            target_branch="main",
            description="build the one commit builder",
            branch_commits=[""],
            merge_context="/development 2026-07-07_commit-builder (PoC: green suite)",
            surface="Claude Code",
            co_authored_by=CO_AUTHORED_BY,
        )


def test_merge_refuses_a_whitespace_only_branch_commit_entry():
    with pytest.raises(ValueError, match="branch_commits"):
        commit_builder.build_message(
            "merge",
            actor="pm",
            branch="2026-07-07_commit-builder",
            target_branch="main",
            description="build the one commit builder",
            branch_commits=["abc1234 developer: task 1", "   "],
            merge_context="/development 2026-07-07_commit-builder (PoC: green suite)",
            surface="Claude Code",
            co_authored_by=CO_AUTHORED_BY,
        )


def test_merge_with_no_branch_commits_still_has_an_empty_body():
    """The empty-*list* path was always correct; the fix must not disturb it."""
    for empty in (None, []):
        message = commit_builder.build_message(
            "merge",
            actor="pm",
            branch="2026-07-07_commit-builder",
            target_branch="main",
            description="build the one commit builder",
            branch_commits=empty,
            merge_context="/development 2026-07-07_commit-builder (PoC: green suite)",
            surface="Claude Code",
            co_authored_by=CO_AUTHORED_BY,
        )
        assert "->" not in message
        assert "Merge-Authorized: PM" in message


# ── `markers` subcommand — a third op beside `commit` and `merge`, printing
#    each path's version marker straight out of `_locate_marker` — never a
#    second lookup (station `2026-09-08_the-builder-answers-a-files-marker`,
#    Reached-when 1-3) ─────────────────────────────────────────────────────

def test_markers_reports_one_path_form_line_and_semver(tmp_path, capsys):
    target = tmp_path / "a.md"
    target.write_text('---\nversion: "1.2.3"\n---\n# Title\n')

    exit_code = commit_builder.main(["markers", str(target)])

    assert exit_code == 0
    out = capsys.readouterr().out
    form, index, semver = commit_builder._locate_marker(target)
    assert form == "frontmatter"
    assert semver == "1.2.3"
    assert str(target) in out
    assert form in out
    assert semver in out
    # The REPORTED line is 1-based — what `grep -n`, an editor, and every
    # `path:line` citation in the doctrine mean. `_locate_marker` returns a
    # 0-based index (its own docstring says "line index"), so the report adds
    # one. Asserting `str(index) in out` instead would pass by accident here:
    # index is 1 and "1" occurs inside the semver "1.2.3".
    assert f"line {index + 1}" in out


def test_markers_reported_line_agrees_with_grep_n(tmp_path, capsys):
    """The whole point of the subcommand is that a session stops grepping and
    asks the builder instead. If the two disagree about the line, there are
    still two answers standing — the defect the seed set out to remove. Marker
    sits on file line 5, deep enough that no off-by-one reads as plausible."""
    target = tmp_path / "deep.md"
    target.write_text('---\ntitle: x\nkind: y\nnote: z\nversion: "4.5.6"\n---\n# Body\n')

    exit_code = commit_builder.main(["markers", str(target)])

    assert exit_code == 0
    out = capsys.readouterr().out
    grep_n = next(
        i for i, line in enumerate(target.read_text().splitlines(), start=1)
        if line.startswith("version:")
    )
    assert grep_n == 5
    assert f"line {grep_n}" in out


def test_markers_reports_several_paths_one_row_each_in_order(tmp_path, capsys):
    first = tmp_path / "a.py"
    first.write_text('__version__ = "1.0.0"\n')
    second = tmp_path / "b.py"
    second.write_text('__version__ = "2.0.0"\n')

    exit_code = commit_builder.main(["markers", str(first), str(second)])

    assert exit_code == 0
    lines = capsys.readouterr().out.strip("\n").split("\n")
    assert len(lines) == 2
    assert str(first) in lines[0] and "1.0.0" in lines[0]
    assert str(second) in lines[1] and "2.0.0" in lines[1]


def test_markers_values_come_from_locate_marker_not_rederived(tmp_path, capsys):
    """A shell-form marker is the sharpest case: `_locate_marker` walks a
    changelog stack and returns the *topmost* entry, per its own docstring
    (`commit_builder.py:1046-1050`). A CLI that re-scanned the file with its
    own logic could easily pick a different entry; asserting byte-equality
    against the resolver's own return value is what pins that it never does."""
    target = tmp_path / "run.sh"
    target.write_text(
        "#!/bin/sh\n# Version: 2.0.0 — second\n# Version: 1.0.0 — first\necho hi\n"
    )

    exit_code = commit_builder.main(["markers", str(target)])

    assert exit_code == 0
    form, index, semver = commit_builder._locate_marker(target)
    assert form == "shell"
    out = capsys.readouterr().out.strip("\n")
    assert out == f"{target}: {form} line {index + 1} semver {semver}"


def test_markers_reports_the_workflow_form(tmp_path, capsys):
    """The fourth of `MARKER_FORMS` — the other three (frontmatter, python,
    shell) are covered above, and reached-when 1 asks for the form of any
    marker the resolver reads. A saved Workflow script carries a
    `// Version: x.y.z` comment below its `meta` block."""
    target = tmp_path / "flow.js"
    target.write_text("const meta = {};\n// Version: 1.4.0\nrun();\n")

    exit_code = commit_builder.main(["markers", str(target)])

    assert exit_code == 0
    located = commit_builder._locate_marker(target)
    assert located == ("workflow", 1, "1.4.0")
    form, index, semver = located
    out = capsys.readouterr().out.strip("\n")
    assert out == f"{target}: {form} line {index + 1} semver {semver}"


def test_markers_resolves_what_the_obvious_grep_cannot(capsys):
    """Reached-when 2, as the plan states it: **the subcommand's own** count
    equals the indented-anchor count and exceeds the `^version:` one. A
    skill's marker sits indented inside its frontmatter, so
    `grep -l '^version:'` misses every one of them.

    The two relations are asserted against the rows the subcommand printed,
    never grep against grep — a comparison between two greps is a property of
    the tree that holds whatever `markers` prints, so it would stay green
    against a subcommand that resolved nothing at all. No absolute number is
    pinned either: the plan calls the count "a property of the tree" that
    "may move"."""
    repo = Path(__file__).parent.parent.parent
    # Both layouts: the flat `.claude/skills/` root holds almost nothing once the groups moved out,
    # so reading it alone would leave this comparison standing on one file.
    paths = sorted(
        str(p)
        for pattern in (".claude/skills/*/SKILL.md", "skills/*/.claude/skills/*/SKILL.md")
        for p in repo.glob(pattern)
    )
    assert paths, "no SKILL.md files found under either skills layout — fixture drift"

    exit_code = commit_builder.main(["markers", *paths])

    assert exit_code == 0
    rows = capsys.readouterr().out.strip("\n").split("\n")
    assert len(rows) == len(paths)
    resolved = sorted(
        row.split(": ", 1)[0] for row in rows if not row.endswith(": no marker")
    )
    indented = sorted(subprocess.run(
        ["grep", "-l", "^  version:", *paths],
        capture_output=True, text=True,
    ).stdout.splitlines())
    obvious = subprocess.run(
        ["grep", "-l", "^version:", *paths],
        capture_output=True, text=True,
    ).stdout.splitlines()
    assert resolved == indented
    assert len(resolved) > len(obvious)


# ── Task 3 — a marker-less path is an answer, not an error ─────────────────
# `_locate_marker` already returns None for an absent, unreadable, or
# marker-less file (its own docstring, commit_builder.py:1035-1037) and
# `_markers_report` (task 2) reports each the same way — these tests lock
# that guarantee with its own coverage rather than leaving it as an
# untested consequence of task 2's design.

def test_markers_reports_a_marker_less_file_without_raising(tmp_path, capsys):
    target = tmp_path / "plain.txt"
    target.write_text("no marker in here\n")

    exit_code = commit_builder.main(["markers", str(target)])

    assert exit_code == 0
    out = capsys.readouterr().out.strip("\n")
    assert commit_builder._locate_marker(target) is None
    assert out == f"{target}: no marker"


def test_markers_reports_an_absent_path_without_raising(tmp_path, capsys):
    target = tmp_path / "does-not-exist.py"

    exit_code = commit_builder.main(["markers", str(target)])

    assert exit_code == 0
    out = capsys.readouterr().out.strip("\n")
    assert commit_builder._locate_marker(target) is None
    assert out == f"{target}: no marker"


def test_markers_reports_an_unreadable_path_without_raising(tmp_path, capsys):
    target = tmp_path / "locked.py"
    target.write_text('__version__ = "1.0.0"\n')
    target.chmod(0o000)
    try:
        exit_code = commit_builder.main(["markers", str(target)])
    finally:
        target.chmod(0o644)

    assert exit_code == 0
    out = capsys.readouterr().out.strip("\n")
    assert out == f"{target}: no marker"


def test_markers_reports_a_mixed_list_without_short_circuiting(tmp_path, capsys):
    """An obvious edge case the plan's behaviours don't spell out (Step 1b):
    a found marker and an absent path in the same call must not make the
    command stop at the first miss — every path given is answered, in
    order."""
    found = tmp_path / "found.py"
    found.write_text('__version__ = "3.0.0"\n')
    missing = tmp_path / "missing.py"

    exit_code = commit_builder.main(["markers", str(found), str(missing)])

    assert exit_code == 0
    lines = capsys.readouterr().out.strip("\n").split("\n")
    assert len(lines) == 2
    assert "3.0.0" in lines[0]
    assert lines[1] == f"{missing}: no marker"


# ── Task 1 — resolve a marker as it stood at a ref (`_locate_marker_at_ref`) ─
# station `2026-09-08_the-builder-answers-what-a-branch-moved`, Reached-when 3:
# the base-side answer is `_locate_marker` run against the blob at that ref,
# never re-implemented.

def test_locate_marker_at_ref_answers_the_marker_as_it_stood_there(tmp_path):
    _init_repo(tmp_path)
    target = tmp_path / "a.py"
    target.write_text('__version__ = "1.0.0"\n')
    subprocess.run(["git", "-C", str(tmp_path), "add", "a.py"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "add a.py at 1.0.0"],
        check=True,
    )
    first_sha = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    target.write_text('__version__ = "2.0.0"\n')
    subprocess.run(["git", "-C", str(tmp_path), "add", "a.py"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "bump a.py to 2.0.0"],
        check=True,
    )

    located = commit_builder._locate_marker_at_ref(str(tmp_path), "a.py", first_sha)

    assert located == ("python", 0, "1.0.0")


def test_locate_marker_at_ref_never_re_derives_locate_markers_answer(tmp_path):
    """The whole point of task 1 is that the base-side read goes *through*
    `_locate_marker`, never a second implementation of its logic. Pinned by
    byte-identical equality against `_locate_marker`'s own answer for the
    same bytes read directly, not merely by the `git diff` gate on the
    function bodies."""
    _init_repo(tmp_path)
    target = tmp_path / "deep.md"
    content = '---\ntitle: x\nkind: y\nnote: z\nversion: "4.5.6"\n---\n# Body\n'
    target.write_text(content)
    subprocess.run(["git", "-C", str(tmp_path), "add", "deep.md"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "add deep.md"], check=True,
    )
    ref = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    located = commit_builder._locate_marker_at_ref(str(tmp_path), "deep.md", ref)

    twin = tmp_path / "twin.md"
    twin.write_text(content)
    assert located == commit_builder._locate_marker(twin)


def test_locate_marker_at_ref_answers_no_marker_for_a_path_absent_at_that_ref(tmp_path):
    _init_repo(tmp_path)
    first_sha = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    new_file = tmp_path / "new.py"
    new_file.write_text('__version__ = "1.0.0"\n')
    subprocess.run(["git", "-C", str(tmp_path), "add", "new.py"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "add new.py"], check=True,
    )

    located = commit_builder._locate_marker_at_ref(str(tmp_path), "new.py", first_sha)

    assert located is None


def test_locate_marker_at_ref_refuses_an_unresolvable_ref_by_name(tmp_path):
    _init_repo(tmp_path)

    with pytest.raises(commit_builder.UnknownRefError) as exc_info:
        commit_builder._locate_marker_at_ref(str(tmp_path), "a.py", "not-a-real-ref")

    assert "not-a-real-ref" in str(exc_info.value)


# ── Task 2 — `markers --base <ref>`: name what moved, exit non-zero ─────────
# station `2026-09-08_the-builder-answers-what-a-branch-moved`, Reached-when
# 1, 2 and 5: a file's marker being edited is what counts — gained, lost, or
# a changed semver — never merely the file changing; the exit code is the
# load-bearing half, since a gate reads it rather than parsing text.

def _base_sha(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _stage(repo: Path, *paths: str) -> None:
    subprocess.run(["git", "-C", str(repo), "add", *paths], check=True)


def test_markers_base_names_a_file_that_gained_a_marker(tmp_path, capsys):
    _init_repo(tmp_path)
    (tmp_path / "core").mkdir()
    base = _base_sha(tmp_path)
    gained = tmp_path / "core/gained.py"
    gained.write_text('__version__ = "1.0.0"\n')
    _stage(tmp_path, "core/gained.py")

    exit_code = commit_builder.main(["--repo", str(tmp_path), "markers", "--base", base])

    assert exit_code != 0
    out = capsys.readouterr().out
    assert "core/gained.py" in out
    assert "no marker" in out
    assert "1.0.0" in out


def test_markers_base_names_a_file_that_lost_its_marker(tmp_path, capsys):
    _init_repo(tmp_path)
    (tmp_path / "core").mkdir()
    losing = tmp_path / "core/losing.py"
    losing.write_text('__version__ = "1.0.0"\n')
    _stage(tmp_path, "core/losing.py")
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "add losing.py"], check=True,
    )
    base = _base_sha(tmp_path)
    losing.write_text('# no marker anymore\n')
    _stage(tmp_path, "core/losing.py")

    exit_code = commit_builder.main(["--repo", str(tmp_path), "markers", "--base", base])

    assert exit_code != 0
    out = capsys.readouterr().out
    assert "core/losing.py" in out
    assert "1.0.0" in out
    assert "no marker" in out


def test_markers_base_names_a_file_whose_semver_changed(tmp_path, capsys):
    _init_repo(tmp_path)
    (tmp_path / "core").mkdir()
    bumped = tmp_path / "core/bumped.py"
    bumped.write_text('__version__ = "1.0.0"\n')
    _stage(tmp_path, "core/bumped.py")
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "add bumped.py"], check=True,
    )
    base = _base_sha(tmp_path)
    bumped.write_text('__version__ = "2.0.0"\n')
    _stage(tmp_path, "core/bumped.py")

    exit_code = commit_builder.main(["--repo", str(tmp_path), "markers", "--base", base])

    assert exit_code != 0
    out = capsys.readouterr().out
    assert "core/bumped.py" in out
    assert "1.0.0" in out
    assert "2.0.0" in out


def test_markers_base_reports_nothing_and_exits_zero_when_nothing_changed(tmp_path, capsys):
    _init_repo(tmp_path)
    base = _base_sha(tmp_path)

    exit_code = commit_builder.main(["--repo", str(tmp_path), "markers", "--base", base])

    assert exit_code == 0
    assert capsys.readouterr().out == ""


def test_markers_base_is_silent_when_content_changed_but_the_marker_did_not(tmp_path, capsys):
    """The rule is about the marker being edited, not the file changing at
    all — a docstring edit above an unmoved `__version__` line is not a
    moved marker."""
    _init_repo(tmp_path)
    steady = tmp_path / "steady.py"
    steady.write_text('__version__ = "1.0.0"\n')
    _stage(tmp_path, "steady.py")
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "add steady.py"], check=True,
    )
    base = _base_sha(tmp_path)
    steady.write_text('"""an unrelated docstring edit"""\n__version__ = "1.0.0"\n')
    _stage(tmp_path, "steady.py")

    exit_code = commit_builder.main(["--repo", str(tmp_path), "markers", "--base", base])

    assert exit_code == 0
    assert capsys.readouterr().out == ""


def test_markers_refuses_combining_base_with_explicit_paths(tmp_path, capsys):
    _init_repo(tmp_path)
    base = _base_sha(tmp_path)

    exit_code = commit_builder.main(
        ["--repo", str(tmp_path), "markers", "--base", base, "some/path.py"]
    )

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "commit_builder:" in err


def test_markers_refuses_with_neither_base_nor_paths(tmp_path, capsys):
    exit_code = commit_builder.main(["--repo", str(tmp_path), "markers"])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "commit_builder:" in err


def test_markers_base_refuses_an_unresolvable_ref_through_main(tmp_path, capsys):
    _init_repo(tmp_path)

    exit_code = commit_builder.main(
        ["--repo", str(tmp_path), "markers", "--base", "not-a-real-ref"]
    )

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "commit_builder:" in err
    assert "not-a-real-ref" in err


def test_markers_with_explicit_paths_and_no_base_is_unchanged(tmp_path, capsys):
    """Guardrail: station 1's surface is untouched by `--base`'s arrival."""
    target = tmp_path / "a.py"
    target.write_text('__version__ = "1.0.0"\n')

    exit_code = commit_builder.main(["markers", str(target)])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert f"{target}: python line 1 semver 1.0.0" in out


# ── code-integrity — the changed set is discovered, so it is not all text ───
# station `2026-09-08_the-builder-answers-what-a-branch-moved`. `markers
# <paths>` is handed its files by a caller; `--base` **walks the files
# changed** between the ref and the working tree (task 2's intent), so it
# meets whatever the branch touched — a PNG, a `.ico`, a latin-1 fixture. A
# file that is not decodable text carries no version marker in any of
# `MARKER_FORMS`, so it is "no marker" on both sides and did not move.
# Reached-when 2 makes the exit code load-bearing — "usable as a gate without
# parsing output" — and `languages/python/errors_logging.md` § The cut binds
# the entry point: "Never a traceback."

def _write_binary(path: Path) -> None:
    path.write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe\x00not utf-8")


def test_markers_base_survives_a_binary_file_in_the_changed_set(tmp_path, capsys):
    """Reached-when 2: a branch that added an image and moved no marker is
    clean — no names, exit 0 — not a traceback out of `main()`."""
    _init_repo(tmp_path)
    base = _base_sha(tmp_path)
    _write_binary(tmp_path / "logo.png")
    _stage(tmp_path, "logo.png")

    exit_code = commit_builder.main(["--repo", str(tmp_path), "markers", "--base", base])

    assert exit_code == 0
    assert capsys.readouterr().out == ""


def test_markers_base_still_names_a_moved_marker_beside_a_binary_file(tmp_path, capsys):
    """The undecodable file must not stop the walk before the file that did
    move — `_moved_markers` reports every path in the changed set, and git's
    order puts `logo.png` first."""
    _init_repo(tmp_path)
    (tmp_path / "core").mkdir()
    bumped = tmp_path / "core/zz_bumped.py"
    bumped.write_text('__version__ = "1.0.0"\n')
    _stage(tmp_path, "core/zz_bumped.py")
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "add zz_bumped.py"],
        check=True,
    )
    base = _base_sha(tmp_path)
    _write_binary(tmp_path / "logo.png")
    bumped.write_text('__version__ = "2.0.0"\n')
    _stage(tmp_path, "logo.png", "core/zz_bumped.py")

    exit_code = commit_builder.main(["--repo", str(tmp_path), "markers", "--base", base])

    assert exit_code != 0
    out = capsys.readouterr().out
    assert "zz_bumped.py: 1.0.0 -> 2.0.0" in out
    assert "logo.png" not in out


def test_locate_marker_at_ref_answers_no_marker_for_a_binary_blob(tmp_path):
    """The base side meets the same set: `_locate_marker_at_ref`'s own
    contract is "a question about the past gets an answer, not a traceback",
    and a blob that is not decodable text carries no marker."""
    _init_repo(tmp_path)
    _write_binary(tmp_path / "logo.png")
    _stage(tmp_path, "logo.png")
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "add logo.png"], check=True,
    )
    ref = _base_sha(tmp_path)

    assert commit_builder._locate_marker_at_ref(str(tmp_path), "logo.png", ref) is None


# ── a binary in a branch's diff — every commit on the branch walks it ───────
# example-0615e7 `2026-09-23_the-native-shell` deferred six tasks on this: the branch
# marker guard reads each changed path through `_read_marker_semver`, so the
# first binary the branch added (`example-0615e7-mac/icon.icns`) ended every commit
# with a `UnicodeDecodeError`. Not decodable is "no marker", on every caller.

def test_a_feature_commit_that_adds_a_binary_file_lands(tmp_path):
    main_branch = _init_repo(tmp_path)
    subprocess.run(
        ["git", "-C", str(tmp_path), "branch", "-M", main_branch, "main"], check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "checkout", "-q", "-b", "feature"], check=True,
    )
    _write_binary(tmp_path / "icon.icns")

    assert _product_commit(tmp_path, "icon.icns") == 0


def test_markers_answers_no_marker_for_a_binary_path(tmp_path, capsys):
    target = tmp_path / "logo.png"
    _write_binary(target)

    exit_code = commit_builder.main(["markers", str(target)])

    assert exit_code == 0
    assert f"{target}: no marker" in capsys.readouterr().out


# ── code-integrity — "between `<ref>` and the working tree" means the tree ──
# Task 2's intent names the working tree, not the index; every task-2 test
# above stages its edit, so the unstaged half of that phrase is unproven.

def test_markers_base_names_an_unstaged_working_tree_marker_edit(tmp_path, capsys):
    _init_repo(tmp_path)
    (tmp_path / "core").mkdir()
    bumped = tmp_path / "core/bumped.py"
    bumped.write_text('__version__ = "1.0.0"\n')
    _stage(tmp_path, "core/bumped.py")
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "add bumped.py"], check=True,
    )
    base = _base_sha(tmp_path)
    bumped.write_text('__version__ = "1.1.0"\n')  # edited, never staged

    exit_code = commit_builder.main(["--repo", str(tmp_path), "markers", "--base", base])

    assert exit_code != 0
    assert "bumped.py: 1.0.0 -> 1.1.0" in capsys.readouterr().out


# ── the `advance` op — a branch takes a named ref's advance ─────────────────
# CP-115..CP-125 (change_spec.md). A branch-authorized `--no-ff` merge of a
# named ref's commit into the checked-out branch, via `commit_builder.py
# advance --from <ref>`.

def _advance_repo(tmp_path: Path) -> tuple[str, callable]:
    """`main_branch` at one commit, `feature` checked out with no commits of its own —
    the base fixture most advance tests build on."""
    main_branch = _init_repo(tmp_path)

    def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=check,
        )

    git("checkout", "-q", "-b", "feature")
    return main_branch, git


def _advance_argv(tmp_path: Path, from_ref: str, actor: str = "developer") -> list[str]:
    return [
        "--repo", str(tmp_path),
        "advance",
        "--from", from_ref,
        "--actor", actor,
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ]


def test_advance_lands_a_two_parent_merge_of_the_ref_into_the_branch(tmp_path):
    # CP-115.
    main_branch, git = _advance_repo(tmp_path)
    feature_before = git("rev-parse", "HEAD").stdout.strip()
    git("checkout", "-q", main_branch)
    (tmp_path / "m.txt").write_text("m\n")
    git("add", "m.txt")
    git("commit", "-q", "-m", "main row")
    main_tip = git("rev-parse", main_branch).stdout.strip()
    git("checkout", "-q", "feature")

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch))

    assert exit_code == 0
    parents = git("rev-list", "--parents", "-n", "1", "HEAD").stdout.split()
    assert parents[1:] == [feature_before, main_tip]
    assert git("rev-parse", main_branch).stdout.strip() == main_tip  # main did not move


def test_advance_makes_a_merge_commit_even_when_the_branch_could_fast_forward(tmp_path):
    # CP-115: the branch has no commits of its own — a plain merge would fast-forward.
    main_branch, git = _advance_repo(tmp_path)
    git("checkout", "-q", main_branch)
    (tmp_path / "m.txt").write_text("m\n")
    git("add", "m.txt")
    git("commit", "-q", "-m", "main row")
    git("checkout", "-q", "feature")

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch))

    assert exit_code == 0
    parents = git("rev-list", "--parents", "-n", "1", "HEAD").stdout.split()
    assert len(parents) == 3


def test_advance_message_is_the_merge_shape_pointed_into_the_branch(tmp_path):
    # CP-116.
    main_branch, git = _advance_repo(tmp_path)
    git("checkout", "-q", main_branch)
    (tmp_path / "m.txt").write_text("m\n")
    git("add", "m.txt")
    git("commit", "-q", "-m", "main row")
    main_tip = git("rev-parse", main_branch).stdout.strip()
    git("checkout", "-q", "feature")

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch))

    assert exit_code == 0
    body = _commit_body(tmp_path)
    assert body.startswith(f"merge: {main_branch} → feature — take {main_branch}'s advance")
    trailer_block = body.strip().split("\n\n")[-1]
    assert trailer_block.splitlines() == [
        f"Merge-Authorized: Developer — takes {main_branch} at {main_tip}",
        "Surface: Claude Code",
        f"Co-Authored-By: {CO_AUTHORED_BY}",
    ]


def test_advance_message_carries_no_role_directional_or_provenance_lines(tmp_path):
    # CP-116.
    main_branch, git = _advance_repo(tmp_path)
    git("checkout", "-q", main_branch)
    (tmp_path / "m.txt").write_text("m\n")
    git("add", "m.txt")
    git("commit", "-q", "-m", "main row")
    git("checkout", "-q", "feature")

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch))

    assert exit_code == 0
    body = _commit_body(tmp_path)
    assert "Role:" not in body
    assert "Shukuba:" not in body
    assert "Agari:" not in body
    assert "Michi:" not in body
    assert "Skill-Version:" not in body
    assert "Prompt-Version:" not in body
    assert "Workflow-Version:" not in body


def test_advance_omits_co_authored_by_and_claude_session_when_not_given(tmp_path):
    # CP-116.
    main_branch, git = _advance_repo(tmp_path)
    git("checkout", "-q", main_branch)
    (tmp_path / "m.txt").write_text("m\n")
    git("add", "m.txt")
    git("commit", "-q", "-m", "main row")
    git("checkout", "-q", "feature")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path), "advance", "--from", main_branch,
        "--actor", "developer", "--surface", "Claude Code",
    ])

    assert exit_code == 0
    body = _commit_body(tmp_path)
    assert "Co-Authored-By:" not in body
    assert "Claude-Session:" not in body


@pytest.mark.parametrize("actor,role", commit_builder.AGENT_ROLE.items())
def test_every_commit_actor_may_authorize_an_advance(tmp_path, actor, role):
    # CP-117.
    main_branch, git = _advance_repo(tmp_path)
    git("checkout", "-q", main_branch)
    (tmp_path / "m.txt").write_text("m\n")
    git("add", "m.txt")
    git("commit", "-q", "-m", "main row")
    git("checkout", "-q", "feature")

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch, actor=actor))

    assert exit_code == 0
    assert f"Merge-Authorized: {role} — takes {main_branch} at" in _commit_body(tmp_path)


def test_an_interactive_advance_may_be_authorized_by_product(tmp_path):
    # CP-117.
    main_branch, git = _advance_repo(tmp_path)
    git("checkout", "-q", main_branch)
    (tmp_path / "m.txt").write_text("m\n")
    git("add", "m.txt")
    git("commit", "-q", "-m", "main row")
    git("checkout", "-q", "feature")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path), "advance", "--from", main_branch,
        "--authorizer", "Product", "--surface", "Claude Code",
    ])

    assert exit_code == 0
    assert f"Merge-Authorized: Product — takes {main_branch} at" in _commit_body(tmp_path)


def test_advance_refuses_an_unknown_actor_and_an_unknown_authorizer(tmp_path, capsys):
    # CP-117.
    main_branch, git = _advance_repo(tmp_path)
    git("checkout", "-q", main_branch)
    (tmp_path / "m.txt").write_text("m\n")
    git("add", "m.txt")
    git("commit", "-q", "-m", "main row")
    git("checkout", "-q", "feature")
    head_before = git("rev-parse", "HEAD").stdout.strip()
    index_before = git("diff", "--cached", "--name-only").stdout

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch, actor="bogus"))

    assert exit_code == 1
    assert "bogus" in capsys.readouterr().err
    assert git("rev-parse", "HEAD").stdout.strip() == head_before
    assert git("diff", "--cached", "--name-only").stdout == index_before
    assert git("status", "--porcelain").stdout.strip() == ""

    exit_code = commit_builder.main([
        "--repo", str(tmp_path), "advance", "--from", main_branch,
        "--authorizer", "Nobody", "--surface", "Claude Code",
    ])

    assert exit_code == 1
    assert "Nobody" in capsys.readouterr().err
    assert git("rev-parse", "HEAD").stdout.strip() == head_before
    assert git("status", "--porcelain").stdout.strip() == ""


def test_merge_still_refuses_a_developer_authorizer_after_advance_exists(tmp_path):
    # CP-117 — the merge verb itself is unchanged by this task.
    main_branch = _init_repo(tmp_path)

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    git("checkout", "-q", "-b", "feature")
    (tmp_path / "feature.txt").write_text("feature\n")
    git("add", "feature.txt")
    git("commit", "-q", "-m", "feature: add a thing")
    git("checkout", "-q", main_branch)

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "merge",
        "--branch", "feature",
        "--target-branch", main_branch,
        "--description", "bring in the feature",
        "--branch-commits", "feature: add a thing",
        "--actor", "developer",
        "--merge-context", "manual",
        "--surface", "Claude Code",
    ])

    assert exit_code != 0


def test_advance_with_nothing_to_take_exits_zero_and_commits_nothing(tmp_path, capsys):
    # CP-118.
    main_branch, git = _advance_repo(tmp_path)
    head_before = git("rev-parse", "HEAD").stdout.strip()
    short = git("rev-parse", "--short", main_branch).stdout.strip()

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch))

    assert exit_code == 0
    assert (
        capsys.readouterr().out.strip()
        == f"commit_builder: feature already holds {main_branch} ({short}) — nothing to take"
    )
    assert git("rev-parse", "HEAD").stdout.strip() == head_before


def test_advance_refuses_on_a_detached_head(tmp_path, capsys):
    # CP-119.
    main_branch, git = _advance_repo(tmp_path)
    git("checkout", "-q", "--detach", "feature")
    head_before = git("rev-parse", "HEAD").stdout.strip()

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch))

    assert exit_code == 1
    assert "detached" in capsys.readouterr().err
    assert git("rev-parse", "HEAD").stdout.strip() == head_before


def test_advance_refuses_when_the_branch_is_the_ref_itself(tmp_path, capsys):
    # CP-119.
    main_branch, git = _advance_repo(tmp_path)
    git("checkout", "-q", main_branch)
    head_before = git("rev-parse", "HEAD").stdout.strip()

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch))

    assert exit_code == 1
    assert main_branch in capsys.readouterr().err
    assert git("rev-parse", "HEAD").stdout.strip() == head_before


def test_advance_refuses_an_unresolvable_ref(tmp_path, capsys):
    # CP-120.
    main_branch, git = _advance_repo(tmp_path)
    head_before = git("rev-parse", "HEAD").stdout.strip()

    exit_code = commit_builder.main(_advance_argv(tmp_path, "does-not-exist"))

    assert exit_code == 1
    assert "does-not-exist" in capsys.readouterr().err
    assert git("rev-parse", "HEAD").stdout.strip() == head_before


def test_advance_refuses_a_staged_index_naming_each_path(tmp_path, capsys):
    # CP-121.
    main_branch, git = _advance_repo(tmp_path)
    git("checkout", "-q", main_branch)
    (tmp_path / "m.txt").write_text("m\n")
    git("add", "m.txt")
    git("commit", "-q", "-m", "main row")
    git("checkout", "-q", "feature")
    (tmp_path / "a.txt").write_text("a\n")
    (tmp_path / "b.txt").write_text("b\n")
    git("add", "a.txt", "b.txt")

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch))

    assert exit_code == 1
    stderr = capsys.readouterr().err
    assert "a.txt" in stderr
    assert "b.txt" in stderr
    assert git("rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).returncode != 0
    assert set(git("diff", "--cached", "--name-only").stdout.split()) == {"a.txt", "b.txt"}


def test_advance_conflict_leaves_the_merge_in_progress_with_the_resume_instruction(
    tmp_path, capsys
):
    # CP-122.
    main_branch, git = _advance_repo(tmp_path)
    (tmp_path / "reg.txt").write_text("feature row\n")
    git("add", "reg.txt")
    git("commit", "-q", "-m", "feature row")
    git("checkout", "-q", main_branch)
    (tmp_path / "reg.txt").write_text("main row\n")
    git("add", "reg.txt")
    git("commit", "-q", "-m", "main row")
    git("checkout", "-q", "feature")

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch))

    assert exit_code != 0
    stderr = capsys.readouterr().err
    assert "resolve" in stderr.lower()
    assert "git add" in stderr
    assert "re-run" in stderr.lower()
    assert git("rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).returncode == 0


def test_advance_rerun_after_resolving_lands_the_advance_commit(tmp_path):
    # CP-123.
    main_branch, git = _advance_repo(tmp_path)
    (tmp_path / "reg.txt").write_text("feature row\n")
    git("add", "reg.txt")
    git("commit", "-q", "-m", "feature row")
    git("checkout", "-q", main_branch)
    (tmp_path / "reg.txt").write_text("main row\n")
    git("add", "reg.txt")
    git("commit", "-q", "-m", "main row")
    main_tip = git("rev-parse", main_branch).stdout.strip()
    git("checkout", "-q", "feature")
    commit_builder.main(_advance_argv(tmp_path, main_branch))

    (tmp_path / "reg.txt").write_text("resolved\n")
    git("add", "reg.txt")
    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch))

    assert exit_code == 0
    body = _commit_body(tmp_path)
    assert body.startswith(f"merge: {main_branch} → feature — take {main_branch}'s advance")
    assert f"Merge-Authorized: Developer — takes {main_branch} at {main_tip}" in body
    parents = git("rev-list", "--parents", "-n", "1", "HEAD").stdout.split()
    assert len(parents) == 3


def test_advance_resume_after_the_ref_moved_names_the_commit_actually_merged(tmp_path):
    # CP-123.
    main_branch, git = _advance_repo(tmp_path)
    (tmp_path / "reg.txt").write_text("feature row\n")
    git("add", "reg.txt")
    git("commit", "-q", "-m", "feature row")
    git("checkout", "-q", main_branch)
    (tmp_path / "reg.txt").write_text("main row 1\n")
    git("add", "reg.txt")
    git("commit", "-q", "-m", "main row 1")
    first_main_tip = git("rev-parse", main_branch).stdout.strip()
    git("checkout", "-q", "feature")
    commit_builder.main(_advance_argv(tmp_path, main_branch))

    # main advances again while the conflict is open — via plumbing, since it is not
    # checked out anywhere and the working feature branch is mid-conflict.
    new_tree = git("rev-parse", f"{first_main_tip}^{{tree}}").stdout.strip()
    new_commit = git(
        "commit-tree", "-p", first_main_tip, "-m", "main row 2", new_tree
    ).stdout.strip()
    git("update-ref", f"refs/heads/{main_branch}", new_commit)

    (tmp_path / "reg.txt").write_text("resolved\n")
    git("add", "reg.txt")
    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch))

    assert exit_code == 0
    body = _commit_body(tmp_path)
    assert f"Merge-Authorized: Developer — takes {main_branch} at {first_main_tip}" in body
    assert new_commit not in body


def test_advance_refuses_a_foreign_merge_in_progress(tmp_path, capsys):
    # CP-123.
    main_branch, git = _advance_repo(tmp_path)
    git("checkout", "-q", "-b", "other")
    (tmp_path / "reg.txt").write_text("other row\n")
    git("add", "reg.txt")
    git("commit", "-q", "-m", "other row")
    other_tip = git("rev-parse", "other").stdout.strip()
    git("checkout", "-q", "feature")
    git("checkout", "-q", main_branch)
    (tmp_path / "m.txt").write_text("m\n")
    git("add", "m.txt")
    git("commit", "-q", "-m", "main row")
    git("checkout", "-q", "feature")
    git("merge", "--no-ff", "--no-commit", "other", check=False)

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch))

    assert exit_code == 1
    assert other_tip[:7] in capsys.readouterr().err
    assert git("rev-parse", "MERGE_HEAD").stdout.strip() == other_tip


def test_advance_taking_a_bumped_marker_lands(tmp_path):
    # CP-124.
    versioned = tmp_path / "versioned.py"
    versioned.write_text('__version__ = "1.0.0"\n')

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=True,
        )

    _init_repo(tmp_path)
    git("add", "versioned.py")
    git("commit", "-q", "-m", "add versioned.py")
    main_branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    git("checkout", "-q", "-b", "feature")
    git("checkout", "-q", main_branch)
    versioned.write_text('__version__ = "1.1.0"\n')
    git("commit", "-qam", "main: bump version")
    git("checkout", "-q", "feature")

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch))

    assert exit_code == 0
    assert '__version__ = "1.1.0"' in versioned.read_text()


def test_a_commit_after_an_advance_is_not_refused_by_the_marker_guard(tmp_path):
    # CP-124.
    _init_repo(tmp_path)
    versioned = tmp_path / "versioned.py"
    versioned.write_text('__version__ = "1.0.0"\n')

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=True,
        )

    git("add", "versioned.py")
    git("commit", "-q", "-m", "seed")
    main_branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    git("checkout", "-q", "-b", "feature")
    git("checkout", "-q", main_branch)
    versioned.write_text('__version__ = "1.1.0"\n')
    git("commit", "-qam", "main: bump version")
    git("checkout", "-q", "feature")
    assert commit_builder.main(_advance_argv(tmp_path, main_branch)) == 0

    (tmp_path / "other.py").write_text("print(1)\n")
    exit_code = _product_commit(tmp_path, "other.py")

    assert exit_code == 0


def test_a_developer_advance_lands_through_the_real_commit_msg_hook(tmp_path):
    # CP-125.
    hooks = Path(__file__).parent.parent / "githooks"
    main_branch, git = _advance_repo(tmp_path)
    git("checkout", "-q", main_branch)
    (tmp_path / "m.txt").write_text("m\n")
    git("add", "m.txt")
    git("commit", "-q", "-m", "main row")
    git("checkout", "-q", "feature")
    git("config", "core.hooksPath", str(hooks))

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch))

    assert exit_code == 0
    body = _commit_body(tmp_path)
    assert "Merge-Authorized:" in body
    assert "Surface:" in body


# ── code-integrity additions (development-code-integrity, 2026-09-23) ───────
# Each is read off change_spec.md / tl_instruction.md, never off the implementation.

def _main_gains_a_commit(git, main_branch: str, tmp_path: Path) -> str:
    git("checkout", "-q", main_branch)
    (tmp_path / "m.txt").write_text("m\n")
    git("add", "m.txt")
    git("commit", "-q", "-m", "main row")
    git("checkout", "-q", "feature")
    return git("rev-parse", main_branch).stdout.strip()


def test_advance_message_is_exactly_subject_empty_body_and_four_trailers_in_order(tmp_path):
    # CP-116: "subject …, an empty body, then the trailers in this order — Merge-Authorized:,
    # Surface:, then Co-Authored-By: and Claude-Session:". The whole message, not its pieces:
    # no body paragraph between subject and trailers, and Claude-Session: last.
    main_branch, git = _advance_repo(tmp_path)
    main_tip = _main_gains_a_commit(git, main_branch, tmp_path)
    session = "https://claude.ai/code/session_x"

    exit_code = commit_builder.main(
        _advance_argv(tmp_path, main_branch) + ["--claude-session", session]
    )

    assert exit_code == 0
    assert _commit_body(tmp_path).rstrip("\n") == "\n".join([
        f"merge: {main_branch} → feature — take {main_branch}'s advance",
        "",
        f"Merge-Authorized: Developer — takes {main_branch} at {main_tip}",
        "Surface: Claude Code",
        f"Co-Authored-By: {CO_AUTHORED_BY}",
        f"Claude-Session: {session}",
    ])


def test_advance_with_nothing_to_take_when_the_branch_is_ahead_of_the_ref(tmp_path, capsys):
    # CP-118: "already in the branch's history" — not only equal to the branch's tip. The
    # branch carries its own commit beyond the ref, and the ref has nothing new.
    main_branch, git = _advance_repo(tmp_path)
    (tmp_path / "f.txt").write_text("f\n")
    git("add", "f.txt")
    git("commit", "-q", "-m", "feature row")
    head_before = git("rev-parse", "HEAD").stdout.strip()
    short = git("rev-parse", "--short", main_branch).stdout.strip()

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch))

    assert exit_code == 0
    assert (
        capsys.readouterr().out.strip()
        == f"commit_builder: feature already holds {main_branch} ({short}) — nothing to take"
    )
    assert git("rev-parse", "HEAD").stdout.strip() == head_before


@pytest.mark.parametrize("identity", [
    ["--actor", "developer", "--authorizer", "Product"],
    [],
])
def test_advance_takes_exactly_one_of_actor_or_authorizer(tmp_path, identity):
    # CP-117: "The authorizer is given by exactly one of --actor or --authorizer." Both, or
    # neither, lands nothing.
    main_branch, git = _advance_repo(tmp_path)
    _main_gains_a_commit(git, main_branch, tmp_path)
    head_before = git("rev-parse", "HEAD").stdout.strip()

    with pytest.raises(SystemExit) as exc:
        commit_builder.main([
            "--repo", str(tmp_path), "advance", "--from", main_branch,
            *identity, "--surface", "Claude Code",
        ])

    assert exc.value.code != 0
    assert git("rev-parse", "HEAD").stdout.strip() == head_before
    assert git("rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).returncode != 0


def test_advance_resume_with_an_unknown_actor_refuses_and_keeps_the_merge(tmp_path, capsys):
    # CP-117 × CP-123: an unknown value refuses with the repo unchanged — mid-conflict too,
    # so the caller's resolution and the merge in progress both survive the refusal.
    main_branch, git = _advance_repo(tmp_path)
    (tmp_path / "reg.txt").write_text("feature row\n")
    git("add", "reg.txt")
    git("commit", "-q", "-m", "feature row")
    git("checkout", "-q", main_branch)
    (tmp_path / "reg.txt").write_text("main row\n")
    git("add", "reg.txt")
    git("commit", "-q", "-m", "main row")
    main_tip = git("rev-parse", main_branch).stdout.strip()
    git("checkout", "-q", "feature")
    commit_builder.main(_advance_argv(tmp_path, main_branch))
    (tmp_path / "reg.txt").write_text("resolved\n")
    git("add", "reg.txt")
    head_before = git("rev-parse", "HEAD").stdout.strip()
    capsys.readouterr()

    exit_code = commit_builder.main(_advance_argv(tmp_path, main_branch, actor="bogus"))

    assert exit_code == 1
    assert "bogus" in capsys.readouterr().err
    assert git("rev-parse", "HEAD").stdout.strip() == head_before
    assert git("rev-parse", "MERGE_HEAD").stdout.strip() == main_tip
    assert (tmp_path / "reg.txt").read_text() == "resolved\n"


# ── `--reasoning-effort max` through the real operations ───────────────────
# The cases above hand `build_message` a level the parser admitted. These run each operation's
# own entry point against a throwaway repository and read the commit it made, so a `max` that
# parses and is then dropped on the way to the message cannot pass.


def _reasoning_effort_lines_and_the_line_before(repo: Path) -> tuple[list[str], str]:
    lines = _commit_body(repo).strip().split("\n\n")[-1].splitlines()
    effort_lines = [line for line in lines if line.startswith("Reasoning-Effort:")]
    return effort_lines, lines[lines.index(effort_lines[0]) - 1]


_MAX_AFTER_CO_AUTHOR = (["Reasoning-Effort: max"], f"Co-Authored-By: {CO_AUTHORED_BY}")


def test_commit_run_at_max_lands_one_max_trailer_after_co_authored_by(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path), "commit", "--subject", "work", "--role", "Product",
        "--add", "work.txt", "--directional", "Shukuba: proto — progress: x",
        "--surface", "Claude Code", "--co-authored-by", CO_AUTHORED_BY,
        "--reasoning-effort", "max",
    ])

    assert exit_code == 0
    assert _reasoning_effort_lines_and_the_line_before(tmp_path) == _MAX_AFTER_CO_AUTHOR


def test_merge_run_at_max_lands_one_max_trailer_after_co_authored_by(tmp_path):
    main_branch, git = _advance_repo(tmp_path)
    (tmp_path / "f.txt").write_text("f\n")
    git("add", "f.txt")
    git("commit", "-q", "-m", "feature row")
    git("checkout", "-q", main_branch)

    exit_code = commit_builder.main([
        "--repo", str(tmp_path), "merge", "--branch", "feature",
        "--target-branch", main_branch, "--description", "bring in the row",
        "--actor", "pm", "--merge-context", "manual", "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY, "--reasoning-effort", "max",
    ])

    assert exit_code == 0
    assert _reasoning_effort_lines_and_the_line_before(tmp_path) == _MAX_AFTER_CO_AUTHOR


def test_advance_run_at_max_lands_one_max_trailer_after_co_authored_by(tmp_path):
    main_branch, git = _advance_repo(tmp_path)
    git("checkout", "-q", main_branch)
    (tmp_path / "m.txt").write_text("m\n")
    git("add", "m.txt")
    git("commit", "-q", "-m", "main row")
    git("checkout", "-q", "feature")

    exit_code = commit_builder.main(
        [*_advance_argv(tmp_path, main_branch), "--reasoning-effort", "max"]
    )

    assert exit_code == 0
    assert _reasoning_effort_lines_and_the_line_before(tmp_path) == _MAX_AFTER_CO_AUTHOR


# Read-only delivery preflight: real CLI and complete repository observations.
def _check_snapshot(repo):
    commands = (
        ("show-ref",), ("status", "--porcelain"), ("ls-files", "--stage"),
        ("worktree", "list", "--porcelain"), ("rev-parse", "-q", "--verify", "MERGE_HEAD"),
    )
    observations = []
    for command in commands:
        result = subprocess.run(
            ["git", "-C", str(repo), *command], capture_output=True,
        )
        observations.append((result.returncode, result.stdout, result.stderr))
    files = {str(p.relative_to(repo)): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    return observations, files


def _check_cli(repo, args):
    return subprocess.run(
        [sys.executable, str(BUILDER), *args], capture_output=True, text=True,
    )


def test_merge_check_accepts_without_effects(tmp_path):
    branch, _ = _merge_probe_repo(tmp_path)
    before = _check_snapshot(tmp_path)
    result = _check_cli(tmp_path, [*_merge_argv(tmp_path, branch), "--check-only"])
    assert result.returncode == 0, result.stderr
    assert _check_snapshot(tmp_path) == before


def test_merge_check_does_not_run_commit_hooks(tmp_path):
    branch, _ = _merge_probe_repo(tmp_path)
    hook = tmp_path / ".git/hooks/commit-msg"
    hook.write_text("#!/bin/sh\nexit 42\n")
    hook.chmod(0o755)
    before = _check_snapshot(tmp_path)
    result = _check_cli(tmp_path, [*_merge_argv(tmp_path, branch), "--check-only"])
    assert result.returncode == 0, result.stderr
    assert _check_snapshot(tmp_path) == before


@pytest.mark.parametrize("flag,value", [("--actor", "unknown"), ("--authorizer", "Developer")])
def test_merge_check_refuses_invalid_identity_without_effects(tmp_path, flag, value):
    branch, _ = _merge_probe_repo(tmp_path)
    args = _merge_argv(tmp_path, branch)
    index = args.index("--actor")
    args[index:index + 2] = [flag, value]
    before = _check_snapshot(tmp_path)
    result = _check_cli(tmp_path, [*args, "--check-only"])
    assert result.returncode == 1
    assert "commit_builder:" in result.stderr
    assert "unrecognized arguments" not in result.stderr
    assert _check_snapshot(tmp_path) == before


@pytest.mark.parametrize("spec", ["absent.py=minor", "doctrine.md=bad", "bad", "bad.py=patch"])
def test_merge_check_refuses_unusable_bump_without_effects(tmp_path, spec):
    branch, _ = _merge_probe_repo(tmp_path)
    (tmp_path / "bad.py").write_text('__version__ = "broken"\n')
    args = _merge_argv(tmp_path, branch)
    args[args.index("--bump") + 1] = spec
    before = _check_snapshot(tmp_path)
    result = _check_cli(tmp_path, [*args, "--check-only"])
    assert result.returncode == 1
    assert "unusable --bump" in result.stderr
    assert _check_snapshot(tmp_path) == before


@pytest.mark.parametrize("entry", ["", "   "])
def test_merge_check_refuses_blank_commit_entry_without_effects(tmp_path, entry):
    branch, _ = _merge_probe_repo(tmp_path)
    args = _merge_argv(tmp_path, branch)
    args[args.index("--branch-commits") + 1] = entry
    before = _check_snapshot(tmp_path)
    result = _check_cli(tmp_path, [*args, "--check-only"])
    assert result.returncode == 1
    assert "blank entry" in result.stderr and "Traceback" not in result.stderr
    assert _check_snapshot(tmp_path) == before


@pytest.mark.parametrize("mode", ["valid", "identity", "commits", "bump"])
def test_merge_check_and_merge_validate_the_same_inputs(tmp_path, mode):
    valid = mode == "valid"
    results = []
    for name, check in [("check", True), ("merge", False)]:
        repo = tmp_path / name
        repo.mkdir()
        branch = _init_repo(repo)
        subprocess.run(["git", "-C", str(repo), "checkout", "-qb", "feature"], check=True)
        (repo / "new").write_text("change")
        subprocess.run(["git", "-C", str(repo), "add", "new"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "change"], check=True)
        subprocess.run(["git", "-C", str(repo), "checkout", "-q", branch], check=True)
        args = _merge_argv(repo, branch)
        index = args.index("--bump")
        del args[index:index + 2]
        if mode == "identity":
            args[args.index("--actor") + 1] = "unknown"
        elif mode == "commits":
            args[args.index("--branch-commits") + 1] = " "
        elif mode == "bump":
            args.extend(["--bump", "absent.py=minor"])
        result = _check_cli(repo, [*args, *(["--check-only"] if check else [])])
        results.append(result.returncode)
        if valid and not check:
            assert len(_git_raw(repo, "rev-list", "--parents", "-n", "1", "HEAD").split()) == 3
    assert results == ([0, 0] if valid else [1, 1])


@pytest.mark.parametrize("optional", [[], ["--reasoning-effort", "max", "--claude-session", "literal",
    "--branch-commits", "one", "two", "--bump", "core/doctrine.md=patch"]])
def test_merge_check_accepts_supplied_optional_metadata(tmp_path, optional):
    branch, _ = _merge_probe_repo(tmp_path)
    before = _check_snapshot(tmp_path)
    result = _check_cli(tmp_path, [*_merge_argv(tmp_path, branch), *optional, "--check-only"])
    assert result.returncode == 0, result.stderr
    assert _check_snapshot(tmp_path) == before


@pytest.mark.parametrize("extra", [["--reasoning-effort", "invalid"], []])
def test_merge_check_retains_usage_errors(tmp_path, extra):
    _init_repo(tmp_path)
    before = _check_snapshot(tmp_path)
    result = _check_cli(tmp_path, ["--repo", str(tmp_path), "merge", "--check-only", *extra])
    assert result.returncode == 2
    assert "usage:" in result.stderr
    assert _check_snapshot(tmp_path) == before


# ── a verified verbatim copy keeps its version (--copied-from) ─────────────

_COPY_BYTES = '__version__ = "2.3.0"\nVALUE = 1\n'


def _copy_source_repo(tmp_path: Path, files: dict[str, str]) -> tuple[Path, str]:
    """A second throwaway repository holding `files`; returns it and its commit sha."""
    source = tmp_path / "source"
    source.mkdir()
    _init_repo(source)
    for relative, text in files.items():
        (source / relative).parent.mkdir(parents=True, exist_ok=True)
        (source / relative).write_text(text, encoding="utf-8")
    subprocess.run(["git", "-C", str(source), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(source), "commit", "-q", "-m", "source files"], check=True)
    return source, _base_sha(source)


def _add_to_branch(repo: Path, relative: str, text: str) -> None:
    (repo / relative).write_text(text, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", relative], check=True)


def test_guard_passes_an_added_copy_identical_to_a_file_at_the_source(tmp_path):
    receiving = tmp_path / "receiving"
    receiving.mkdir()
    _feature_repo_with_versioned_file(receiving)
    source, sha = _copy_source_repo(tmp_path, {"lib/run_usage.py": _COPY_BYTES})
    _add_to_branch(receiving, "core/run_usage.py", _COPY_BYTES)

    refusal = commit_builder._branch_marker_refusal(
        str(receiving), "main", [(str(source), sha)]
    )

    assert refusal is None


def test_guard_refuses_a_copy_one_byte_away_from_the_source(tmp_path):
    receiving = tmp_path / "receiving"
    receiving.mkdir()
    _feature_repo_with_versioned_file(receiving)
    source, sha = _copy_source_repo(tmp_path, {"lib/run_usage.py": _COPY_BYTES})
    _add_to_branch(receiving, "core/run_usage.py", _COPY_BYTES.replace("VALUE = 1", "VALUE = 2"))

    refusal = commit_builder._branch_marker_refusal(
        str(receiving), "main", [(str(source), sha)]
    )

    assert refusal is not None
    assert "core/run_usage.py" in refusal
    assert "found 2.3.0" in refusal
    assert "no declared source holds a file with the same bytes" in refusal


def test_guard_refuses_an_added_file_with_no_match_at_the_source(tmp_path):
    receiving = tmp_path / "receiving"
    receiving.mkdir()
    _feature_repo_with_versioned_file(receiving)
    source, sha = _copy_source_repo(tmp_path, {"other.txt": "unrelated\n"})
    _add_to_branch(receiving, "core/run_usage.py", _COPY_BYTES)

    refusal = commit_builder._branch_marker_refusal(
        str(receiving), "main", [(str(source), sha)]
    )

    assert refusal is not None
    assert "core/run_usage.py" in refusal
    assert "no declared source holds a file with the same bytes" in refusal


def test_guard_names_a_source_that_does_not_resolve(tmp_path):
    receiving = tmp_path / "receiving"
    receiving.mkdir()
    _feature_repo_with_versioned_file(receiving)
    source, _ = _copy_source_repo(tmp_path, {"lib/run_usage.py": _COPY_BYTES})
    _add_to_branch(receiving, "core/run_usage.py", _COPY_BYTES)
    absent_sha = "0" * 40

    for declared in ((str(source), absent_sha), (str(tmp_path / "gone"), absent_sha)):
        refusal = commit_builder._branch_marker_refusal(str(receiving), "main", [declared])

        assert refusal is not None
        assert "core/run_usage.py" in refusal
        assert declared[0] in refusal
        assert "no longer resolves" in refusal


def test_guard_passes_a_copy_on_one_source_when_another_does_not_resolve(tmp_path):
    receiving = tmp_path / "receiving"
    receiving.mkdir()
    _feature_repo_with_versioned_file(receiving)
    source, sha = _copy_source_repo(tmp_path, {"lib/run_usage.py": _COPY_BYTES})
    _add_to_branch(receiving, "core/run_usage.py", _COPY_BYTES)

    for sources in (
        [(str(tmp_path / "gone"), "0" * 40), (str(source), sha)],
        [(str(source), sha), (str(tmp_path / "gone"), "0" * 40)],
    ):
        assert commit_builder._branch_marker_refusal(str(receiving), "main", sources) is None


def test_guard_still_refuses_an_edited_marker_on_an_existing_artifact_with_a_source_declared(
    tmp_path,
):
    receiving = tmp_path / "receiving"
    receiving.mkdir()
    target = _feature_repo_with_versioned_file(receiving)
    new_bytes = '__version__ = "2.3.0"\n'
    source, sha = _copy_source_repo(tmp_path, {"lib/versioned.py": new_bytes})
    target.write_text(new_bytes, encoding="utf-8")
    subprocess.run(["git", "-C", str(receiving), "add", "core/versioned.py"], check=True)

    refusal = commit_builder._branch_marker_refusal(
        str(receiving), "main", [(str(source), sha)]
    )

    assert refusal is not None
    assert "core/versioned.py: 1.0.0 -> 2.3.0" in refusal


def test_guard_still_refuses_a_rename_that_changes_the_marker_with_a_source_declared(tmp_path):
    receiving = tmp_path / "receiving"
    receiving.mkdir()
    target = _feature_repo_with_versioned_file(receiving)
    padding = "".join(f"LINE_{number} = {number}\n" for number in range(12))
    subprocess.run(["git", "-C", str(receiving), "checkout", "-q", "main"], check=True)
    target.write_text('__version__ = "1.0.0"\n' + padding, encoding="utf-8")
    subprocess.run(["git", "-C", str(receiving), "commit", "-qam", "main: pad"], check=True)
    subprocess.run(["git", "-C", str(receiving), "checkout", "-q", "-B", "feature"], check=True)
    new_bytes = '__version__ = "2.3.0"\n' + padding
    source, sha = _copy_source_repo(tmp_path, {"lib/versioned.py": new_bytes})
    subprocess.run(["git", "-C", str(receiving), "mv", "core/versioned.py", "core/renamed.py"], check=True)
    (receiving / "core/renamed.py").write_text(new_bytes, encoding="utf-8")
    subprocess.run(["git", "-C", str(receiving), "add", "core/renamed.py"], check=True)

    refusal = commit_builder._branch_marker_refusal(
        str(receiving), "main", [(str(source), sha)]
    )

    assert refusal is not None
    assert "core/versioned.py -> core/renamed.py: 1.0.0 -> 2.3.0" in refusal


def test_guard_with_no_sources_refuses_above_creation_version_and_names_the_flag(
    tmp_path,
):
    _feature_repo_with_versioned_file(tmp_path)
    _add_to_branch(tmp_path, "core/added.py", '__version__ = "1.2.0"\n')

    refusal = commit_builder._branch_marker_refusal(str(tmp_path), "main")

    assert refusal is not None
    assert "core/added.py: new artifact starts at 1.0.0, found 1.2.0" in refusal
    assert "and no declared source" not in refusal
    assert "--copied-from <repo> <revision>" in refusal


def test_guard_hint_is_absent_when_only_an_edited_marker_is_refused(tmp_path):
    target = _feature_repo_with_versioned_file(tmp_path)
    target.write_text('__version__ = "1.1.0"\n', encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "core/versioned.py"], check=True)

    refusal = commit_builder._branch_marker_refusal(str(tmp_path), "main")

    assert refusal is not None
    assert "--copied-from" not in refusal


_COPY_CONFIG_KEY = "branch.feature.kensaiappCopySource"


def _copy_commit(repo: Path, paths: list[str], *declared: tuple[str, str]) -> int:
    flags = [part for pair in declared for part in ("--copied-from", *pair)]
    return commit_builder.main([
        "--repo", str(repo),
        "commit",
        "--subject", "product: copy a file",
        "--role", "Product",
        "--directional", "Michi: none — exercise the copy declaration",
        "--surface", "Codex",
        "--add", *paths,
        *flags,
    ])


def _recorded_sources(repo: Path, key: str = _COPY_CONFIG_KEY) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "config", "--get-all", key], capture_output=True, text=True
    )
    return result.stdout.splitlines()


def _copy_fixture(tmp_path: Path) -> tuple[Path, Path, str]:
    """A feature-branch repository, a source repository holding the file, and the source sha."""
    receiving = tmp_path / "receiving"
    receiving.mkdir()
    _feature_repo_with_versioned_file(receiving)
    source, sha = _copy_source_repo(tmp_path, {"lib/run_usage.py": _COPY_BYTES})
    (receiving / "core/run_usage.py").write_text(_COPY_BYTES, encoding="utf-8")
    return receiving, source, sha


def _staged_names(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "diff", "--cached", "--name-only"],
        capture_output=True, text=True, check=True,
    ).stdout


def test_commit_with_copied_from_lands_a_verified_copy(tmp_path):
    receiving, source, sha = _copy_fixture(tmp_path)

    exit_code = _copy_commit(receiving, ["core/run_usage.py"], (str(source), sha))

    assert exit_code == 0
    shown = subprocess.run(
        ["git", "-C", str(receiving), "show", "HEAD:core/run_usage.py"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert shown == _COPY_BYTES


def test_a_later_commit_on_the_branch_needs_no_redeclaration(tmp_path):
    receiving, source, sha = _copy_fixture(tmp_path)
    assert _copy_commit(receiving, ["core/run_usage.py"], (str(source), sha)) == 0
    (receiving / "other.py").write_text("print('later work')\n", encoding="utf-8")

    assert _copy_commit(receiving, ["other.py"]) == 0


def test_a_later_edit_to_the_copy_is_refused(tmp_path, capsys):
    receiving, source, sha = _copy_fixture(tmp_path)
    assert _copy_commit(receiving, ["core/run_usage.py"], (str(source), sha)) == 0
    (receiving / "core/run_usage.py").write_text(
        _COPY_BYTES.replace("VALUE = 1", "VALUE = 2"), encoding="utf-8"
    )

    exit_code = _copy_commit(receiving, ["core/run_usage.py"])

    assert exit_code == 1
    assert "core/run_usage.py" in capsys.readouterr().err


def test_an_unresolvable_copy_source_is_refused_before_staging(tmp_path, capsys):
    receiving, source, sha = _copy_fixture(tmp_path)
    head_before = _base_sha(receiving)

    for repo_arg, revision, reason in (
        (str(source), "0" * 40, "names no commit in"),
        (str(tmp_path / "not-a-repo"), sha, "is not a git repository"),
    ):
        exit_code = _copy_commit(receiving, ["core/run_usage.py"], (repo_arg, revision))

        assert exit_code == 1
        error = capsys.readouterr().err
        assert f"--copied-from '{repo_arg}' '{revision}' does not resolve" in error
        assert reason in error
        assert _staged_names(receiving) == ""
        assert _base_sha(receiving) == head_before
        assert _recorded_sources(receiving) == []


def test_a_declaration_on_main_is_refused(tmp_path, capsys):
    receiving, source, sha = _copy_fixture(tmp_path)
    subprocess.run(["git", "-C", str(receiving), "checkout", "-q", "main"], check=True)
    head_before = _base_sha(receiving)

    exit_code = _copy_commit(receiving, ["core/run_usage.py"], (str(source), sha))

    assert exit_code == 1
    assert "--copied-from is declared on main" in capsys.readouterr().err
    assert _staged_names(receiving) == ""
    assert _base_sha(receiving) == head_before
    assert _recorded_sources(receiving, "branch.main.kensaiappCopySource") == []


def test_a_declaration_on_a_detached_head_is_refused(tmp_path, capsys):
    receiving, source, sha = _copy_fixture(tmp_path)
    subprocess.run(["git", "-C", str(receiving), "checkout", "-q", "--detach"], check=True)

    exit_code = _copy_commit(receiving, ["core/run_usage.py"], (str(source), sha))

    assert exit_code == 1
    assert "HEAD is detached" in capsys.readouterr().err
    assert _staged_names(receiving) == ""
    assert _recorded_sources(receiving) == []


def test_a_repeated_declaration_is_recorded_once(tmp_path):
    receiving, source, sha = _copy_fixture(tmp_path)
    assert _copy_commit(receiving, ["core/run_usage.py"], (str(source), sha)) == 0
    (receiving / "other.py").write_text("print('later work')\n", encoding="utf-8")

    assert _copy_commit(receiving, ["other.py"], (str(source), sha)) == 0

    assert _recorded_sources(receiving) == [f"{sha} {source}"]


def test_the_declared_revision_is_fixed_at_the_commit_it_named(tmp_path):
    receiving, source, sha = _copy_fixture(tmp_path)
    source_branch = subprocess.run(
        ["git", "-C", str(source), "branch", "--show-current"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert _copy_commit(receiving, ["core/run_usage.py"], (str(source), source_branch)) == 0
    (source / "lib" / "run_usage.py").write_text("changed at the tip\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(source), "commit", "-qam", "tip moves"], check=True)
    (receiving / "other.py").write_text("print('later work')\n", encoding="utf-8")

    assert _copy_commit(receiving, ["other.py"]) == 0
    assert _recorded_sources(receiving) == [f"{sha} {source}"]


def test_deleting_the_branch_drops_its_declaration(tmp_path):
    receiving, source, sha = _copy_fixture(tmp_path)
    assert _copy_commit(receiving, ["core/run_usage.py"], (str(source), sha)) == 0
    assert _recorded_sources(receiving) != []
    subprocess.run(["git", "-C", str(receiving), "checkout", "-q", "main"], check=True)
    subprocess.run(["git", "-C", str(receiving), "branch", "-D", "feature"], check=True)

    assert _recorded_sources(receiving) == []


# ── code integrity: the intent's cases the first pass left untested ────────


def test_guard_judges_an_added_copy_by_the_bytes_the_commit_carries(tmp_path):
    """The staged blob is what lands, so it is what gets compared — a working tree restored to the
    source's bytes must not carry a staged edit through (request § What must not be weakened)."""
    receiving = tmp_path / "receiving"
    receiving.mkdir()
    _feature_repo_with_versioned_file(receiving)
    source, sha = _copy_source_repo(tmp_path, {"lib/run_usage.py": _COPY_BYTES})
    _add_to_branch(receiving, "core/run_usage.py", _COPY_BYTES.replace("VALUE = 1", "VALUE = 2"))
    (receiving / "core/run_usage.py").write_text(_COPY_BYTES, encoding="utf-8")

    refusal = commit_builder._branch_marker_refusal(
        str(receiving), "main", [(str(source), sha)]
    )

    assert refusal is not None
    assert "core/run_usage.py" in refusal
    assert "no declared source holds a file with the same bytes" in refusal


def test_a_later_commit_is_judged_by_the_copy_it_carries_not_an_unstaged_edit(tmp_path):
    """A later commit that does not carry an edit to the copy still lands (CP-565): the copy's
    committed bytes are the verified ones."""
    receiving, source, sha = _copy_fixture(tmp_path)
    assert _copy_commit(receiving, ["core/run_usage.py"], (str(source), sha)) == 0
    (receiving / "core/run_usage.py").write_text(
        _COPY_BYTES.replace("VALUE = 1", "VALUE = 2"), encoding="utf-8"
    )
    (receiving / "other.py").write_text("print('later work')\n", encoding="utf-8")

    assert _copy_commit(receiving, ["other.py"]) == 0


def test_one_unresolvable_pair_records_none_of_the_declared_pairs(tmp_path, capsys):
    receiving, source, sha = _copy_fixture(tmp_path)
    head_before = _base_sha(receiving)

    exit_code = _copy_commit(
        receiving, ["core/run_usage.py"], (str(source), sha), (str(source), "0" * 40)
    )

    assert exit_code == 1
    assert f"--copied-from '{source}' '{'0' * 40}' does not resolve" in capsys.readouterr().err
    assert _recorded_sources(receiving) == []
    assert _staged_names(receiving) == ""
    assert _base_sha(receiving) == head_before


def test_the_flag_repeated_on_one_commit_records_each_source(tmp_path):
    receiving, source, sha = _copy_fixture(tmp_path)
    (tmp_path / "second").mkdir()
    other, other_sha = _copy_source_repo(tmp_path / "second", {"unrelated.txt": "x\n"})

    exit_code = _copy_commit(
        receiving, ["core/run_usage.py"], (str(other), other_sha), (str(source), sha)
    )

    assert exit_code == 0
    assert _recorded_sources(receiving) == [f"{other_sha} {other}", f"{sha} {source}"]


def test_guard_matches_a_copy_anywhere_in_a_source_named_by_a_subdirectory(tmp_path):
    """CP-566 'at any path there': a repository path given as one of its subdirectories still
    offers every file at the revision."""
    receiving = tmp_path / "receiving"
    receiving.mkdir()
    _feature_repo_with_versioned_file(receiving)
    source, sha = _copy_source_repo(
        tmp_path, {"lib/run_usage.py": _COPY_BYTES, "docs/readme.md": "docs\n"}
    )
    _add_to_branch(receiving, "core/run_usage.py", _COPY_BYTES)

    refusal = commit_builder._branch_marker_refusal(
        str(receiving), "main", [(str(source / "docs"), sha)]
    )

    assert refusal is None


# ── whose markers these are — kensaiapp's, never a product's ────────────────
# `versioning.md` § Whose artifacts. 2026-10-19: a product's change unit was
# refused the fix its task asked for — setting two `__version__` strings to the
# distribution's own — and every seal before it had bumped those lines as if
# they were kensaiapp markers. The guard, `--bump` and `markers --base` judge
# kensaiapp's four layers of an instance only.

def _scope_repo(tmp_path: Path, files: dict[str, str], instance: bool) -> None:
    """A repo on `main` holding `files` — an instance, or with `kensaiapp.md`
    removed a product repository — then checked out on `feature`."""
    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True,
                       capture_output=True)

    _init_repo(tmp_path)  # seeds `kensaiapp.md`: every throwaway repo starts as an instance
    git("branch", "-M", "main")
    if not instance:
        git("rm", "-q", "kensaiapp.md")
    for relative, text in files.items():
        (tmp_path / relative).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / relative).write_text(text, encoding="utf-8")
    git("add", *files)
    git("commit", "-q", "-m", "seed the scope fixture")
    git("checkout", "-q", "-b", "feature")


def _scope_commit(repo: Path, *paths: str) -> int:
    return commit_builder.main([
        "--repo", str(repo),
        "commit",
        "--subject", "developer: set the version",
        "--role", "Product",
        "--directional", "Michi: none — exercise whose markers these are",
        "--surface", "Codex",
        "--add", *paths,
    ])


@pytest.mark.parametrize("instance, path, expected", [
    (True, "core/tools/x.py", True),
    (True, ".claude/hooks/x.py", True),
    (True, "skills/pm/.claude/skills/s/SKILL.md", True),
    (True, "system/loaders/pm.md", True),
    (True, "products/app/app/__init__.py", False),
    (True, "docs/findings/f.md", False),
    (True, "corefoo/x.py", False),
    (True, "x.py", False),
    (False, "core/tools/x.py", False),
    (False, "app/__init__.py", False),
])
def test_is_kensaiapp_path_reads_the_instance_and_the_layer(tmp_path, instance, path, expected):
    if instance:
        (tmp_path / "kensaiapp.md").write_text("# an instance\n")

    assert commit_builder._is_kensaiapp_path(str(tmp_path), path) is expected


def test_a_product_repo_branch_may_set_its_own_version(tmp_path):
    """The recorded case: a product's task sets `__version__` 1.6.0 -> 0.1.0."""
    _scope_repo(tmp_path, {"app/stream.py": '__version__ = "1.6.0"\n'}, instance=False)
    (tmp_path / "app/stream.py").write_text('__version__ = "0.1.0"\n')

    assert _scope_commit(tmp_path, "app/stream.py") == 0


def test_a_product_repo_with_a_core_folder_is_still_a_product(tmp_path):
    _scope_repo(tmp_path, {"core/__init__.py": '__version__ = "2.0.0"\n'}, instance=False)
    (tmp_path / "core/__init__.py").write_text('__version__ = "2.1.0"\n')

    assert _scope_commit(tmp_path, "core/__init__.py") == 0


def test_an_internal_product_under_products_may_set_its_own_version(tmp_path):
    _scope_repo(
        tmp_path, {"products/app/app/__init__.py": '__version__ = "1.0.0"\n'}, instance=True
    )
    (tmp_path / "products/app/app/__init__.py").write_text('__version__ = "3.0.0"\n')

    assert _scope_commit(tmp_path, "products/app/app/__init__.py") == 0


def test_an_instance_layer_marker_is_still_refused_beside_a_product_edit(tmp_path, capsys):
    _scope_repo(tmp_path, {
        "core/tools/tool.py": '__version__ = "1.0.0"\n',
        "products/app/app/__init__.py": '__version__ = "1.0.0"\n',
    }, instance=True)
    (tmp_path / "core/tools/tool.py").write_text('__version__ = "1.1.0"\n')
    (tmp_path / "products/app/app/__init__.py").write_text('__version__ = "0.1.0"\n')

    exit_code = _scope_commit(tmp_path, "core/tools/tool.py", "products/app/app/__init__.py")

    assert exit_code == 1
    error = capsys.readouterr().err
    assert "core/tools/tool.py: 1.0.0 -> 1.1.0" in error
    assert "products/app" not in error


def test_merge_refuses_a_bump_on_a_product_path(tmp_path, capsys):
    _scope_repo(tmp_path, {"app/__init__.py": '__version__ = "1.6.0"\n'}, instance=False)
    (tmp_path / "app/__init__.py").write_text('"""Changed."""\n__version__ = "1.6.0"\n')
    assert _scope_commit(tmp_path, "app/__init__.py") == 0
    subprocess.run(["git", "-C", str(tmp_path), "checkout", "-q", "main"], check=True)
    head_before = _base_sha(tmp_path)

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "merge",
        "--branch", "feature",
        "--target-branch", "main",
        "--description", "bring it in",
        "--branch-commits", "feature: the edit",
        "--actor", "pm",
        "--merge-context", "manual",
        "--bump", "app/__init__.py=minor",
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
    ])

    assert exit_code != 0
    assert _base_sha(tmp_path) == head_before
    assert "app/__init__.py=minor — not a kensaiapp artifact" in capsys.readouterr().err
    assert '__version__ = "1.6.0"' in (tmp_path / "app/__init__.py").read_text()


def test_markers_base_leaves_a_product_path_out(tmp_path, capsys):
    _scope_repo(tmp_path, {
        "core/tools/tool.py": '__version__ = "1.0.0"\n',
        "products/app/app/__init__.py": '__version__ = "1.0.0"\n',
    }, instance=True)
    base = _base_sha(tmp_path)
    (tmp_path / "core/tools/tool.py").write_text('__version__ = "1.1.0"\n')
    (tmp_path / "products/app/app/__init__.py").write_text('__version__ = "0.1.0"\n')

    exit_code = commit_builder.main(["--repo", str(tmp_path), "markers", "--base", base])

    assert exit_code != 0
    out = capsys.readouterr().out
    assert "core/tools/tool.py: 1.0.0 -> 1.1.0" in out
    assert "products/app" not in out


def test_the_guard_still_refuses_with_repo_at_a_subdirectory_of_an_instance(tmp_path):
    """`--repo` may name a subdirectory (`_repo_prefix`). The identity is read at the work tree's
    top, so an instance seen from `products/app` is still an instance."""
    _scope_repo(tmp_path, {
        "core/tools/tool.py": '__version__ = "1.0.0"\n',
        "products/app/README.md": "app\n",
    }, instance=True)
    (tmp_path / "core/tools/tool.py").write_text('__version__ = "1.0.1"\n')
    _stage(tmp_path, "core/tools/tool.py")

    assert commit_builder._branch_marker_refusal(str(tmp_path / "products/app")) is not None


def test_merge_refuses_a_bump_that_climbs_out_of_a_layer(tmp_path, capsys):
    _scope_repo(
        tmp_path, {"products/app/app/__init__.py": '__version__ = "1.0.0"\n'}, instance=True
    )

    refusal = commit_builder._bump_refusal(
        str(tmp_path), ["core/../products/app/app/__init__.py=minor"]
    )

    assert refusal is not None and "not a kensaiapp artifact" in refusal


def test_the_guard_refuses_a_marker_change_renamed_out_of_a_layer(tmp_path, capsys):
    body = "".join(f"line {n}\n" for n in range(40))  # enough shared bytes to read as a rename
    _scope_repo(
        tmp_path, {"core/tools/tool.py": f'__version__ = "1.0.0"\n{body}'}, instance=True
    )
    (tmp_path / "products/app").mkdir(parents=True)
    subprocess.run(["git", "-C", str(tmp_path), "mv", "core/tools/tool.py",
                    "products/app/tool.py"], check=True)
    (tmp_path / "products/app/tool.py").write_text(f'__version__ = "2.0.0"\n{body}')
    _stage(tmp_path, "products/app/tool.py")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path),
        "commit",
        "--subject", "developer: move the tool",
        "--role", "Product",
        "--directional", "Michi: none — exercise whose markers these are",
        "--surface", "Codex",
        "--staged", "core/tools/tool.py", "products/app/tool.py",
    ])

    assert exit_code == 1
    assert "1.0.0 -> 2.0.0" in capsys.readouterr().err


# ── --body-file: a body that belongs to the run that wrote it ───────────────
# `commit` reads its body from a file the run made, and removes that file once the commit lands.
# Every refusal, a failed staging and a rejected commit leave it where it was.

def _git_out(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout


def _head(repo: Path) -> str:
    return _git_out(repo, "rev-parse", "HEAD").strip()


def _commit_argv(repo: Path, *extra: str, subject: str = "developer: work",
                 directional: str = "Michi: none — exercise the body file") -> list[str]:
    return [
        "--repo", str(repo),
        "commit",
        "--subject", subject,
        "--actor", "developer",
        "--directional", directional,
        "--surface", "Claude Code",
        "--co-authored-by", CO_AUTHORED_BY,
        *extra,
    ]


def _new_file(repo: Path, name: str = "work.txt") -> str:
    (repo / name).write_text("work\n")
    return name


def _body_file(directory: Path, text: str, name: str = "body.txt") -> Path:
    path = directory / name
    path.write_bytes(text.encode())
    return path


@pytest.mark.parametrize("file_text, inline_text", [
    ("Fixes `x`.\n\n", "Fixes `x`."),
    ("a $(echo hi) b\n\n\nc  \n", "a $(echo hi) b\n\n\nc  "),
    ("first\r\nsecond\r\n\r\nthird\n\n\n", "first\r\nsecond\r\n\r\nthird"),
    ("  indented\n\twith a tab\n", "  indented\n\twith a tab"),
    ("", ""),
    ("no final newline", "no final newline"),
])
def test_body_file_commits_the_same_message_as_inline_body(tmp_path, file_text, inline_text):
    inline_repo, file_repo = tmp_path / "inline", tmp_path / "file"
    for repo in (inline_repo, file_repo):
        repo.mkdir()
        _init_repo(repo)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    source = _body_file(scratch, file_text)

    assert commit_builder.main(_commit_argv(
        inline_repo, "--add", _new_file(inline_repo), "--body", inline_text)) == 0
    assert commit_builder.main(_commit_argv(
        file_repo, "--add", _new_file(file_repo), "--body-file", str(source))) == 0

    assert _commit_body(file_repo) == _commit_body(inline_repo)
    if file_text.startswith("Fixes"):
        assert "Fixes `x`.\n\nShukuba" not in _commit_body(file_repo)
        assert _commit_body(file_repo).startswith("developer: work\n\nFixes `x`.\n\n")


@pytest.mark.parametrize("file_text", ["", "x\n", "x", "x\n\n\n"])
def test_successful_commit_removes_only_its_body_file(tmp_path, file_text):
    _init_repo(tmp_path)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    source = _body_file(scratch, file_text)
    other = _body_file(scratch, file_text, name="other.txt")

    assert commit_builder.main(_commit_argv(
        tmp_path, "--add", _new_file(tmp_path), "--body-file", str(source))) == 0

    assert not source.exists()
    assert other.read_bytes() == file_text.encode()


def test_body_flags_conflict_even_when_inline_body_is_empty(tmp_path, capsys):
    _init_repo(tmp_path)
    source = _body_file(tmp_path, "the body\n")
    before = _head(tmp_path)
    _new_file(tmp_path)

    for inline in ("x", ""):
        capsys.readouterr()
        exit_code = commit_builder.main(_commit_argv(
            tmp_path, "--add", "work.txt", "--body", inline, "--body-file", str(source)))
        stderr = capsys.readouterr().err

        assert exit_code != 0
        assert stderr.splitlines()[0] == (
            "commit_builder: refusing to commit — --body and --body-file were both given.")
        assert f"The body file '{source}' is left in place." in stderr
        assert _head(tmp_path) == before
        assert _git_out(tmp_path, "diff", "--cached", "--name-only") == ""
        assert source.read_bytes() == b"the body\n"


def test_missing_or_unreadable_body_file_refuses_before_staging(tmp_path, capsys):
    _init_repo(tmp_path)
    before = _head(tmp_path)
    _new_file(tmp_path)

    missing = tmp_path / "nonexistent" / "body"
    exit_code = commit_builder.main(_commit_argv(
        tmp_path, "--add", "work.txt", "--body-file", str(missing)))
    stderr = capsys.readouterr().err
    assert exit_code != 0
    assert stderr.splitlines()[0] == (
        f"commit_builder: refusing to commit — the body file '{missing}' does not exist.")
    assert "Nothing was staged and no commit was made." in stderr

    def unreadable(path: str) -> str:
        raise PermissionError(13, "Permission denied", path)

    present = _body_file(tmp_path, "text\n")
    exit_code = commit_builder.main(
        _commit_argv(tmp_path, "--add", "work.txt", "--body-file", str(present)),
        read_body_file=unreadable)
    stderr = capsys.readouterr().err
    assert exit_code != 0
    assert stderr.splitlines()[0] == (
        f"commit_builder: refusing to commit — the body file '{present}' cannot be read: "
        "Permission denied.")
    assert "The body file is left in place." in stderr

    exit_code = commit_builder.main(_commit_argv(
        tmp_path, "--add", "work.txt", "--body-file", str(tmp_path)))
    assert exit_code != 0
    assert f"the body file '{tmp_path}' cannot be read: " in capsys.readouterr().err

    assert _head(tmp_path) == before
    assert _git_out(tmp_path, "diff", "--cached", "--name-only") == ""
    assert present.read_bytes() == b"text\n"


def test_an_undecodable_body_file_is_refused_as_unreadable_and_left_in_place(tmp_path, capsys):
    _init_repo(tmp_path)
    source = tmp_path / "body.bin"
    source.write_bytes(b"\xff\xfe not text")
    _new_file(tmp_path)

    exit_code = commit_builder.main(_commit_argv(
        tmp_path, "--add", "work.txt", "--body-file", str(source)))

    assert exit_code != 0
    assert f"the body file '{source}' cannot be read: " in capsys.readouterr().err
    assert source.read_bytes() == b"\xff\xfe not text"


def _marker_refusal_repo(tmp_path: Path) -> Path:
    _scope_repo(tmp_path, {"core/tools/x.py": '__version__ = "1.0.0"\n'}, instance=True)
    (tmp_path / "core/tools/x.py").write_text('__version__ = "1.1.0"\n')
    return tmp_path


@pytest.mark.parametrize("refusal", ["staged-set guard", "bad directional", "branch marker"])
def test_builder_refusals_retain_body_file(tmp_path, refusal):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    directional = "Michi: none — exercise the body file"
    if refusal == "branch marker":
        _marker_refusal_repo(repo)
        add = "core/tools/x.py"
    else:
        _init_repo(repo)
        add = _new_file(repo)
    if refusal == "staged-set guard":
        (repo / "foreign.txt").write_text("someone else's\n")
        subprocess.run(["git", "-C", str(repo), "add", "foreign.txt"], check=True)
    if refusal == "bad directional":
        (repo / "system" / "projects" / "doctrine").mkdir(parents=True)
        directional = "Agari: versioning — progress: x"
    source = _body_file(scratch, "keep me `safe`\n")
    before = _head(repo)

    exit_code = commit_builder.main(_commit_argv(
        repo, "--add", add, "--body-file", str(source), directional=directional))

    assert exit_code != 0
    assert _head(repo) == before
    assert source.read_bytes() == b"keep me `safe`\n"


@pytest.mark.parametrize("staging", ["add", "rm"])
def test_failed_staging_retains_body_file_and_creates_no_commit(tmp_path, staging):
    _init_repo(tmp_path)
    source = _body_file(tmp_path, "body\n")
    before = _head(tmp_path)

    exit_code = commit_builder.main(_commit_argv(
        tmp_path, f"--{staging}", "no-such-path.txt", "--body-file", str(source)))

    assert exit_code != 0
    assert _head(tmp_path) == before
    assert source.read_bytes() == b"body\n"


def test_commit_hook_rejection_retains_body_file(tmp_path):
    _init_repo(tmp_path)
    hook = tmp_path / ".git" / "hooks" / "commit-msg"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    source = _body_file(tmp_path, "rejected body\n")
    before = _head(tmp_path)

    exit_code = commit_builder.main(_commit_argv(
        tmp_path, "--add", _new_file(tmp_path), "--body-file", str(source)))

    assert exit_code != 0
    assert _head(tmp_path) == before
    assert source.read_bytes() == b"rejected body\n"


def test_a_body_file_that_cannot_be_removed_is_reported_after_the_commit_lands(
        tmp_path, capsys, monkeypatch):
    _init_repo(tmp_path)
    source = _body_file(tmp_path, "body\n")

    def refuse(path):
        raise PermissionError(13, "Permission denied", str(path))

    monkeypatch.setattr(commit_builder.os, "remove", refuse)
    exit_code = commit_builder.main(_commit_argv(
        tmp_path, "--add", _new_file(tmp_path), "--body-file", str(source)))

    assert exit_code == 0
    assert _commit_body(tmp_path).startswith("developer: work\n\nbody\n\n")
    assert capsys.readouterr().err.splitlines() == [
        f"commit_builder: the commit landed, but the body file '{source}' could not be removed: "
        "Permission denied.",
        "Remove it by hand. It holds the body of the commit that just landed and is not needed "
        "again.",
    ]


def test_legacy_inline_body_has_no_file_cleanup(tmp_path):
    _init_repo(tmp_path)
    source = _body_file(tmp_path, "from a file the builder was never given\n")

    for index, body_args in enumerate(([], ["--body", ""],
                                       ["--body", source.read_text().rstrip("\n")])):
        name = _new_file(tmp_path, f"work{index}.txt")
        assert commit_builder.main(_commit_argv(tmp_path, "--add", name, *body_args)) == 0

    assert source.read_bytes() == b"from a file the builder was never given\n"
    assert _commit_body(tmp_path).startswith(
        "developer: work\n\nfrom a file the builder was never given\n\n")


@pytest.mark.parametrize("operation", [
    ["merge", "--branch", "b", "--target-branch", "main", "--description", "d",
     "--merge-context", "c", "--actor", "developer", "--surface", "Claude Code"],
    ["advance", "--from", "main", "--actor", "developer", "--surface", "Claude Code"],
    ["markers", "some/path"],
])
def test_body_file_does_not_extend_other_builder_operations(tmp_path, operation, capsys):
    with pytest.raises(SystemExit) as raised:
        commit_builder.main(["--repo", str(tmp_path), *operation, "--body-file", "x"])

    assert raised.value.code == 2
    assert "--body-file" in capsys.readouterr().err


# ── a closing marker matches this change's last gate run ────────────────────
# A commit whose subject says `implementation complete` is compared, before anything is staged,
# with what the gate tool last printed for the change the commit is on: its `Environment:` lines
# and its `Failing:` lines. With no gate run on record the builder commits as it always did.

import gate_suite  # noqa: E402  (this section's own collaborator)

CHANGE_KEY = "2026-10-22_x"
MARKER_SUBJECT = f"developer: {CHANGE_KEY} — implementation complete"
GATE_ENVIRONMENT = "Environment: container — python:3.12, arm64"
OTHER_ENVIRONMENT = "Environment: owners-mac — no CI"
REFUSAL_FIRST_LINE = (
    "commit_builder: refusing to commit — the closing marker does not match this change's "
    "last gate run.")


def _change_repo(path: Path, key: str = CHANGE_KEY) -> Path:
    """A throwaway repo checked out on the change branch `key`."""
    path.mkdir(parents=True, exist_ok=True)
    _init_repo(path)
    subprocess.run(["git", "-C", str(path), "checkout", "-q", "-b", key], check=True)
    return path


def _gate_store(tmp_path: Path) -> gate_suite.FileRunRecords:
    return gate_suite.FileRunRecords(tmp_path / "gate-runs")


def _record_gate_run(store, repo: Path, *, key: str = CHANGE_KEY,
                     environment: str | None = GATE_ENVIRONMENT, status: int = 0,
                     stdout: str | None = None, stderr: str = "", also=()) -> None:
    printed = stdout if stdout is not None else (
        (f"{environment}\n" if environment else "") + "5 passed\n")
    store.publish(
        gate_suite.GateRun(key=key, checkout=str(repo), environment_line=environment,
                           stdout=printed, stderr=stderr, status=status),
        [str(repo), *map(str, also)])


def _marker_body(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def _close(repo: Path, store, body_args: list[str], *extra: str,
           subject: str = MARKER_SUBJECT, allow_empty: bool = True) -> int:
    flags = [*extra, *(["--allow-empty"] if allow_empty else [])]
    return commit_builder.main(
        _commit_argv(repo, *flags, *body_args, subject=subject), gate_run_records=store)


def _refusal_lines(capsys) -> list[str]:
    return capsys.readouterr().err.splitlines()


def _state(repo: Path) -> tuple[str, str, str]:
    return (_head(repo), _git_out(repo, "diff", "--cached", "--name-only"),
            _git_out(repo, "status", "--porcelain"))


@pytest.mark.parametrize("route", ["inline", "file"])
def test_matching_green_marker_commits_with_either_body_input(tmp_path, route):
    body = _marker_body("Suite: green", GATE_ENVIRONMENT, "", "Developer Review Notes: none.")
    store = _gate_store(tmp_path)
    recorded, twin = _change_repo(tmp_path / "recorded"), _change_repo(tmp_path / "twin")
    _record_gate_run(store, recorded)
    source = _body_file(tmp_path, body)

    args = ["--body-file", str(source)] if route == "file" else ["--body", body.rstrip("\n")]
    assert _close(recorded, store, args) == 0
    assert _close(twin, _gate_store(tmp_path / "empty"),
                  ["--body", body.rstrip("\n")]) == 0

    assert _commit_body(recorded) == _commit_body(twin)
    assert source.exists() is (route == "inline")


@pytest.mark.parametrize("take_index", [False, True])
@pytest.mark.parametrize("marker_lines, shown", [
    ([OTHER_ENVIRONMENT], [OTHER_ENVIRONMENT]),
    (["Suite: green"], None),
])
def test_marker_environment_mismatch_refuses_without_mutation(
        tmp_path, capsys, take_index, marker_lines, shown):
    repo, store = _change_repo(tmp_path / "repo"), _gate_store(tmp_path)
    _record_gate_run(store, repo)
    (repo / "staged.txt").write_text("staged\n")
    subprocess.run(["git", "-C", str(repo), "add", "staged.txt"], check=True)
    (repo / "candidate.txt").write_text("candidate\n")
    source = _body_file(tmp_path, _marker_body("Suite: green", *marker_lines))
    before = _state(repo)
    flags = ["--take-index"] if take_index else ["--staged", "staged.txt"]

    exit_code = _close(repo, store, ["--body-file", str(source)], "--add", "candidate.txt",
                       *flags, allow_empty=False)
    lines = _refusal_lines(capsys)

    assert exit_code != 0
    assert lines[0] == REFUSAL_FIRST_LINE
    if shown is None:
        assert lines[1:3] == ["The marker has no Environment: line. The gate run printed:",
                              f"  {GATE_ENVIRONMENT}"]
    else:
        assert lines[1:4] == ["The marker's Environment: line differs from the one the gate "
                              "run printed.", f"  marker:   {OTHER_ENVIRONMENT}",
                              f"  gate run: {GATE_ENVIRONMENT}"]
    assert lines[-3:-1] == [
        "Nothing was staged and no commit was made. HEAD and the index are as they were.",
        f"The body file '{source}' is left in place."]
    assert "Ways out: take the Environment: line" in lines[-1]
    assert _state(repo)[:2] == before[:2]
    assert (repo / "candidate.txt").exists()
    assert source.read_bytes() == _marker_body("Suite: green", *marker_lines).encode()


def test_marker_refusal_records_no_copy_declaration(tmp_path, capsys):
    repo, store = _change_repo(tmp_path / "repo"), _gate_store(tmp_path)
    source_repo, sha = _copy_source_repo(tmp_path, {"lib/x.py": "x\n"})
    _record_gate_run(store, repo)
    (repo / "x.py").write_text("x\n")

    exit_code = _close(
        repo, store, ["--body", _marker_body(OTHER_ENVIRONMENT)], "--add", "x.py",
        "--copied-from", str(source_repo), sha, allow_empty=False)

    assert exit_code != 0
    assert _recorded_sources(repo, commit_builder._copy_source_key(CHANGE_KEY)) == []
    assert _git_out(repo, "diff", "--cached", "--name-only") == ""


def test_all_environment_declarations_must_match(tmp_path, capsys):
    repo, store = _change_repo(tmp_path / "repo"), _gate_store(tmp_path)
    _record_gate_run(store, repo)

    several = _marker_body(f"**`{GATE_ENVIRONMENT}`**", f"  _{GATE_ENVIRONMENT}_  ",
                           GATE_ENVIRONMENT)
    assert _close(repo, store, ["--body", several]) == 0

    other = _change_repo(tmp_path / "other")
    _record_gate_run(store, other)
    wrapped_bad = f"**`{OTHER_ENVIRONMENT}`**"
    before = _state(other)
    exit_code = _close(other, store,
                       ["--body", _marker_body(GATE_ENVIRONMENT, wrapped_bad, GATE_ENVIRONMENT)])
    lines = _refusal_lines(capsys)
    assert exit_code != 0 and _state(other) == before
    assert f"  marker:   {wrapped_bad}" in lines
    assert f"  marker:   {GATE_ENVIRONMENT}" not in lines

    mention = _change_repo(tmp_path / "mention")
    _record_gate_run(store, mention)
    away = f"See {GATE_ENVIRONMENT} for the run"
    assert _close(mention, store, ["--body", _marker_body(away)]) != 0
    assert "The marker has no Environment: line. The gate run printed:" in _refusal_lines(capsys)


def test_green_gate_rejects_every_failure_declaration(tmp_path, capsys):
    repo, store = _change_repo(tmp_path / "repo"), _gate_store(tmp_path)
    _record_gate_run(store, repo, status=0,
                     stdout=f"{GATE_ENVIRONMENT}\ntests/test_a.py::test_one PASSED\n")
    first, second = "Failing: tests/test_a.py::test_one — task 1", "**Failing: tests/other.py**"
    before = _state(repo)

    exit_code = _close(repo, store,
                       ["--body", _marker_body(GATE_ENVIRONMENT, first, second)])
    lines = _refusal_lines(capsys)

    assert exit_code != 0 and _state(repo) == before
    at = lines.index("The gate run exited 0, so the marker must carry no Failing: line. "
                     "It carries:")
    assert lines[at + 1:at + 3] == [f"  {first}", f"  {second}"]


def test_red_gate_accepts_only_literal_reported_case_ids(tmp_path, capsys):
    stdout = (f"{GATE_ENVIRONMENT}\nFAILED tests/test_a.py::test_one - boom\n"
              "case a — b broke\n tests/test_[x].py::t\n")
    ok = ["Failing: tests/test_a.py::test_one — task 1",
          "Failing: tests/test_c.py::test_three",
          "Failing:   tests/test_a.py::test_one   — task 2",
          "Failing: case a — b — task 3",
          "**Failing: tests/test_[x].py::t — task 4**"]
    repo, store = _change_repo(tmp_path / "ok"), _gate_store(tmp_path)
    _record_gate_run(store, repo, status=1, stdout=stdout,
                     stderr="ERROR tests/test_c.py::test_three\n")
    assert _close(repo, store, ["--body", _marker_body(GATE_ENVIRONMENT, *ok)]) == 0

    bad = ["Failing: tests/test_b.py::test_two — task 5",
           "Failing: tests/*.py::test_one — task 6",
           "Failing: case a — c — task 7",
           "Failing:"]
    other = _change_repo(tmp_path / "bad")
    _record_gate_run(store, other, status=1, stdout=stdout,
                     stderr="ERROR tests/test_c.py::test_three\n")
    before = _state(other)
    exit_code = _close(other, store, ["--body", _marker_body(GATE_ENVIRONMENT, *bad)])
    lines = _refusal_lines(capsys)

    assert exit_code != 0 and _state(other) == before
    at = lines.index("These Failing: lines name a case that appears nowhere in the gate run's "
                     "output:")
    assert lines[at + 1:at + 9] == [
        f"  {bad[0]}", "    case id looked for: tests/test_b.py::test_two",
        f"  {bad[1]}", "    case id looked for: tests/*.py::test_one",
        f"  {bad[2]}", "    case id looked for: case a — c",
        f"  {bad[3]}", "    case id looked for: "]


# Only the first run of consecutive `Environment:` / `Failing:` lines is the marker's declaration
# (CP-854, CP-855): a later prose line opening with the quoted prefix is not read.

MENTION_OF_ENVIRONMENT = "`Environment:` lines are the bare lines at the top of this record."
MENTION_OF_FAILING = "`Failing:` lines name each failing case, one per line."


def test_a_marker_block_followed_by_a_wrapped_environment_mention_commits(tmp_path):
    repo, store = _change_repo(tmp_path / "repo"), _gate_store(tmp_path)
    _record_gate_run(store, repo)

    body = _marker_body("Suite: green", GATE_ENVIRONMENT, "", "The marker's head is read by the",
                        MENTION_OF_ENVIRONMENT)

    assert _close(repo, store, ["--body", body]) == 0


def test_a_mismatching_environment_line_inside_the_run_is_still_refused(tmp_path, capsys):
    repo, store = _change_repo(tmp_path / "repo"), _gate_store(tmp_path)
    _record_gate_run(store, repo)
    before = _state(repo)

    exit_code = _close(repo, store, ["--body", _marker_body(
        "Suite: green", GATE_ENVIRONMENT, OTHER_ENVIRONMENT, "", MENTION_OF_ENVIRONMENT)])
    lines = _refusal_lines(capsys)

    assert exit_code != 0 and _state(repo) == before
    assert lines[0] == REFUSAL_FIRST_LINE
    assert f"  marker:   {OTHER_ENVIRONMENT}" in lines
    assert f"  gate run: {GATE_ENVIRONMENT}" in lines


def test_an_environment_line_after_the_run_is_not_read_even_if_it_mismatches(tmp_path):
    repo, store = _change_repo(tmp_path / "repo"), _gate_store(tmp_path)
    _record_gate_run(store, repo)

    body = _marker_body("Suite: green", GATE_ENVIRONMENT, "", "A note.", OTHER_ENVIRONMENT)

    assert _close(repo, store, ["--body", body]) == 0


def test_a_failing_mention_after_the_run_on_a_red_gate_commits(tmp_path):
    repo, store = _change_repo(tmp_path / "repo"), _gate_store(tmp_path)
    _record_gate_run(store, repo, status=1,
                     stdout=f"{GATE_ENVIRONMENT}\nFAILED tests/test_a.py::test_one - boom\n")

    body = _marker_body(GATE_ENVIRONMENT, "Failing: tests/test_a.py::test_one — task 1", "",
                        "Every red case is named; the", MENTION_OF_FAILING)

    assert _close(repo, store, ["--body", body]) == 0


def test_a_failing_mention_that_opens_a_green_markers_only_block_is_still_refused(
        tmp_path, capsys):
    # The rule's limit (change_spec.md, Out of Scope): with no real `Failing:` line before it, a
    # prose line opening with the quoted prefix is the first match and starts the run.
    repo, store = _change_repo(tmp_path / "repo"), _gate_store(tmp_path)
    _record_gate_run(store, repo, status=0)

    exit_code = _close(repo, store, ["--body", _marker_body(
        "Suite: green", GATE_ENVIRONMENT, "", MENTION_OF_FAILING)])

    assert exit_code != 0
    assert ("The gate run exited 0, so the marker must carry no Failing: line. It carries:"
            in _refusal_lines(capsys))


def test_a_failing_line_inside_the_run_naming_an_absent_case_is_still_refused(tmp_path, capsys):
    repo, store = _change_repo(tmp_path / "repo"), _gate_store(tmp_path)
    _record_gate_run(store, repo, status=1,
                     stdout=f"{GATE_ENVIRONMENT}\nFAILED tests/test_a.py::test_one - boom\n")
    before = _state(repo)

    exit_code = _close(repo, store, ["--body", _marker_body(
        GATE_ENVIRONMENT, "Failing: tests/test_a.py::test_one — task 1",
        "Failing: tests/test_gone.py::test_two — task 2", "", MENTION_OF_FAILING)])
    lines = _refusal_lines(capsys)

    assert exit_code != 0 and _state(repo) == before
    at = lines.index("These Failing: lines name a case that appears nowhere in the gate run's "
                     "output:")
    assert lines[at + 1:at + 3] == ["  Failing: tests/test_gone.py::test_two — task 2",
                                    "    case id looked for: tests/test_gone.py::test_two"]


def test_marker_refusal_reports_all_failed_checks(tmp_path, capsys):
    repo, store = _change_repo(tmp_path / "repo"), _gate_store(tmp_path)
    _record_gate_run(store, repo, status=2, stdout=f"{GATE_ENVIRONMENT}\nFAILED t.py::good\n")

    exit_code = _close(repo, store, ["--body", _marker_body(
        OTHER_ENVIRONMENT, "Failing: t.py::good — task 1", "Failing: t.py::gone — task 2",
        "Failing: t.py::also_gone")])
    lines = _refusal_lines(capsys)

    assert exit_code != 0
    assert lines[0] == REFUSAL_FIRST_LINE
    assert f"  marker:   {OTHER_ENVIRONMENT}" in lines
    assert "  Failing: t.py::gone — task 2" in lines
    assert "  Failing: t.py::also_gone" in lines
    assert "  Failing: t.py::good — task 1" not in lines
    assert lines.count("    case id looked for: t.py::gone") == 1
    assert lines.count("    case id looked for: t.py::also_gone") == 1


def test_matching_refused_gate_environment_can_commit(tmp_path):
    repo, store = _change_repo(tmp_path / "repo"), _gate_store(tmp_path)
    refused = "Environment: unresolved — the CI file is unreadable"
    _record_gate_run(store, repo, environment=refused, status=1, stdout=f"{refused}\n",
                     stderr="why\n")

    assert _close(repo, store, ["--body", _marker_body("Suite: red", refused)]) == 0


def test_marker_uses_latest_completed_run_at_any_gate(tmp_path, capsys):
    repo, store = _change_repo(tmp_path / "repo"), _gate_store(tmp_path)
    _record_gate_run(store, repo, environment=OTHER_ENVIRONMENT)
    _record_gate_run(store, repo, environment=GATE_ENVIRONMENT, status=3,
                     stdout=f"{GATE_ENVIRONMENT}\nFAILED a::b\n")

    assert _close(repo, store, ["--body", _marker_body(OTHER_ENVIRONMENT)]) != 0
    assert f"  gate run: {GATE_ENVIRONMENT}" in _refusal_lines(capsys)
    assert _close(repo, store, ["--body", _marker_body(GATE_ENVIRONMENT, "Failing: a::b")]) == 0


def test_marker_ignores_other_changes_gate_records(tmp_path):
    store = _gate_store(tmp_path)
    stale = _marker_body(OTHER_ENVIRONMENT, "Suite: red", "Failing: t.py::x — task 1")

    other_key = _change_repo(tmp_path / "other-key")
    _record_gate_run(store, other_key, key="another-change")
    assert _close(other_key, store, ["--body", stale]) == 0

    other_instance = _change_repo(tmp_path / "other-instance")
    elsewhere = _change_repo(tmp_path / "elsewhere")
    _record_gate_run(store, elsewhere)
    assert _close(other_instance, store, ["--body", stale]) == 0


def test_marker_resolves_aliases_and_the_separate_code_checkout(tmp_path, capsys):
    store = _gate_store(tmp_path)
    pipeline = _change_repo(tmp_path / "pipeline")
    code = _change_repo(tmp_path / "code")
    _record_gate_run(store, pipeline, also=[code])
    link = tmp_path / "code-link"
    link.symlink_to(code)

    assert _close(link, store, ["--body", _marker_body(OTHER_ENVIRONMENT)]) != 0
    assert f"  gate run: {GATE_ENVIRONMENT}" in _refusal_lines(capsys)
    assert _close(code, store, ["--body", _marker_body(GATE_ENVIRONMENT)]) == 0


def test_a_subdirectory_repo_argument_is_compared_at_its_worktree_root(tmp_path, capsys):
    store = _gate_store(tmp_path)
    repo = _change_repo(tmp_path / "repo")
    (repo / "sub").mkdir()
    _record_gate_run(store, repo)

    assert _close(repo / "sub", store, ["--body", _marker_body(OTHER_ENVIRONMENT)]) != 0
    assert _refusal_lines(capsys)[0] == REFUSAL_FIRST_LINE


def test_nonclosing_and_no_record_markers_retain_existing_behaviour(tmp_path):
    store = _gate_store(tmp_path)
    stale = _marker_body(OTHER_ENVIRONMENT, "Failing: t.py::x")

    paused = _change_repo(tmp_path / "paused")
    _record_gate_run(store, paused)
    assert _close(paused, store, ["--body", stale],
                  subject=f"developer: {CHANGE_KEY} — implementation paused after task 2") == 0

    empty = _change_repo(tmp_path / "empty")
    assert _close(empty, store, ["--body", "Developer Review Notes: none."]) == 0

    taken = _change_repo(tmp_path / "taken")
    (taken / "staged.txt").write_text("s\n")
    subprocess.run(["git", "-C", str(taken), "add", "staged.txt"], check=True)
    assert _close(taken, store, ["--body", stale], "--take-index", allow_empty=False) == 0


def test_marker_check_does_not_expand_suite_or_failure_contract(tmp_path):
    store = _gate_store(tmp_path)
    nonzero = dict(status=1, stdout=f"{GATE_ENVIRONMENT}\nFAILED a::b\nFAILED a::c\n")

    omitted = _change_repo(tmp_path / "omitted")
    _record_gate_run(store, omitted, **nonzero)
    assert _close(omitted, store, ["--body", _marker_body("Suite: red", GATE_ENVIRONMENT)]) == 0

    subset = _change_repo(tmp_path / "subset")
    _record_gate_run(store, subset, **nonzero)
    assert _close(subset, store, ["--body", _marker_body(
        "Suite: green", GATE_ENVIRONMENT, "Failing: a::b")]) == 0


def test_a_commit_without_a_gate_record_store_reads_the_real_default(tmp_path, monkeypatch):
    repo = _change_repo(tmp_path / "repo")
    real = _gate_store(tmp_path)
    _record_gate_run(real, repo)
    monkeypatch.setattr(gate_suite, "default_run_records", lambda: real)

    assert commit_builder.main(_commit_argv(
        repo, "--allow-empty", "--body", _marker_body(OTHER_ENVIRONMENT),
        subject=MARKER_SUBJECT)) != 0


# ── the refusals' words, whole (change_text.md § The builder's refusal messages) ─────────────
# Each refusal is published text, printed line by line exactly as written; these pin every line,
# not only the first, so a reworded or dropped line is a red test rather than a quiet drift.

MARKER_WAYS_OUT = (
    "Ways out: take the Environment: line and each failing case id from this change's last gate "
    "run, then commit again. If the body was read from a file, check that this run wrote it. A "
    "body another change left behind carries that change's lines, not this one's.")
NOTHING_STAGED_MARKER = (
    "Nothing was staged and no commit was made. HEAD and the index are as they were.")
NO_GATE_ENVIRONMENT = "(the gate run printed no Environment: line)"


def test_the_body_file_refusals_print_their_whole_text(tmp_path, capsys):
    _init_repo(tmp_path)
    _new_file(tmp_path)
    source = _body_file(tmp_path, "the body\n")

    assert commit_builder.main(_commit_argv(
        tmp_path, "--add", "work.txt", "--body", "", "--body-file", str(source))) != 0
    assert _refusal_lines(capsys) == [
        "commit_builder: refusing to commit — --body and --body-file were both given.",
        "A commit takes its body from one of the two, so the builder will not guess which one "
        "you meant.",
        f"Nothing was staged and no commit was made. The body file '{source}' is left in place.",
        'Ways out: pass only one of the two. An empty --body "" still counts as given.',
    ]

    missing = tmp_path / "gone" / "body"
    assert commit_builder.main(_commit_argv(
        tmp_path, "--add", "work.txt", "--body-file", str(missing))) != 0
    assert _refusal_lines(capsys) == [
        f"commit_builder: refusing to commit — the body file '{missing}' does not exist.",
        "Nothing was staged and no commit was made.",
        "Ways out: check the path given to --body-file. The builder removes a body file once its "
        "commit lands, so if this path was already used for a commit, write the body to a new "
        "file from mktemp.",
    ]

    def unreadable(path: str) -> str:
        raise PermissionError(13, "Permission denied", path)

    assert commit_builder.main(
        _commit_argv(tmp_path, "--add", "work.txt", "--body-file", str(source)),
        read_body_file=unreadable) != 0
    assert _refusal_lines(capsys) == [
        f"commit_builder: refusing to commit — the body file '{source}' cannot be read: "
        "Permission denied.",
        "Nothing was staged and no commit was made. The body file is left in place.",
        "Ways out: make the file readable as text, or write the body to a new file from mktemp.",
    ]
    assert source.read_bytes() == b"the body\n"


def test_a_marker_refusal_from_a_body_file_prints_its_whole_text(tmp_path, capsys):
    repo, store = _change_repo(tmp_path / "repo"), _gate_store(tmp_path)
    _record_gate_run(store, repo, status=0)
    wrapped = f"**{OTHER_ENVIRONMENT}**"
    failing = "Failing: tests/test_a.py::test_one — task 1"
    source = _body_file(tmp_path, _marker_body("Suite: green", wrapped, failing))

    assert _close(repo, store, ["--body-file", str(source)]) != 0

    assert _refusal_lines(capsys) == [
        REFUSAL_FIRST_LINE,
        "The marker's Environment: line differs from the one the gate run printed.",
        f"  marker:   {wrapped}",
        f"  gate run: {GATE_ENVIRONMENT}",
        "The gate run exited 0, so the marker must carry no Failing: line. It carries:",
        f"  {failing}",
        NOTHING_STAGED_MARKER,
        f"The body file '{source}' is left in place.",
        MARKER_WAYS_OUT,
    ]


def test_an_inline_marker_refusal_names_no_body_file(tmp_path, capsys):
    repo, store = _change_repo(tmp_path / "repo"), _gate_store(tmp_path)
    _record_gate_run(store, repo, status=1, stdout=f"{GATE_ENVIRONMENT}\nFAILED a::b\n")

    body = _marker_body("Suite: red", "Failing: a::c — task 1")
    assert _close(repo, store, ["--body", body]) != 0

    assert _refusal_lines(capsys) == [
        REFUSAL_FIRST_LINE,
        "The marker has no Environment: line. The gate run printed:",
        f"  {GATE_ENVIRONMENT}",
        "These Failing: lines name a case that appears nowhere in the gate run's output:",
        "  Failing: a::c — task 1",
        "    case id looked for: a::c",
        NOTHING_STAGED_MARKER,
        MARKER_WAYS_OUT,
    ]


def test_a_gate_run_that_printed_no_environment_line_is_shown_as_such(tmp_path, capsys):
    # A run that stopped on a handled error after its checkout was known is on record with no
    # `Environment:` line (gate_suite `_main_run`). CP-758 still holds the marker to it: a marker
    # line has no printed line to match, and a marker with none "differs" by the rule's own words.
    store = _gate_store(tmp_path)
    declared = _change_repo(tmp_path / "declared")
    _record_gate_run(store, declared, environment=None, status=2, stdout="",
                     stderr="gate_suite: the inputs file is malformed\n")
    assert _close(declared, store, ["--body", _marker_body(GATE_ENVIRONMENT)]) != 0
    assert _refusal_lines(capsys)[1:4] == [
        "The marker's Environment: line differs from the one the gate run printed.",
        f"  marker:   {GATE_ENVIRONMENT}",
        f"  gate run: {NO_GATE_ENVIRONMENT}",
    ]

    bare = _change_repo(tmp_path / "bare")
    _record_gate_run(store, bare, environment=None, status=2, stdout="",
                     stderr="gate_suite: the inputs file is malformed\n")
    before = _state(bare)
    assert _close(bare, store, ["--body", _marker_body("Suite: red")]) != 0
    assert _refusal_lines(capsys)[1:3] == [
        "The marker has no Environment: line. The gate run printed:",
        f"  {NO_GATE_ENVIRONMENT}",
    ]
    assert _state(bare) == before


# ── a closing marker against a run of several containers (change_text.md § The closing-marker
# refusal messages) ──────────────────────────────────────────────────────────────────────────────
# A run that printed two or more `Environment:` lines is closed by a marker that carries every one
# of them: the builder compares the marker's lines with the run's as sets, names each line missing
# and each line the run did not print, and changes nothing when it refuses.

CELLS = [f"Environment: container — python:{tag}, arm64" for tag in ("3.11", "3.12", "3.13")]
MATRIX_WAYS_OUT = (
    "Ways out: take every Environment: line and each failing case id from this change's last "
    "gate run, then commit again. If the body was read from a file, check that this run wrote it. "
    "A body another change left behind carries that change's lines, not this one's.")


def _record_matrix_run(store, repo: Path, lines=CELLS, *, status: int = 0,
                       stdout: str | None = None, stderr: str = "",
                       key: str = CHANGE_KEY) -> None:
    printed = stdout if stdout is not None else (
        "".join(f"{line}\n" for line in lines) + "5 passed\n")
    store.publish(
        gate_suite.GateRun(key=key, checkout=str(repo), environment_line=None, stdout=printed,
                           stderr=stderr, status=status, environment_lines=tuple(lines)),
        [str(repo)])


def _matrix_close(tmp_path, name: str, body: str, route: str = "inline", *extra: str,
                  stdout: str | None = None, stderr: str = "", status: int = 0, record=None):
    repo, store = _change_repo(tmp_path / name), _gate_store(tmp_path / name)
    if record is not None:
        record(store, repo)
    else:
        _record_matrix_run(store, repo, stdout=stdout, stderr=stderr, status=status)
    source = _body_file(tmp_path, body, name=f"{name}.txt")
    args = ["--body-file", str(source)] if route == "file" else ["--body", body.rstrip("\n")]
    return repo, source, _close(repo, store, args, *extra)


@pytest.mark.parametrize("route", ["inline", "file"])
def test_three_cell_marker_matches_and_missing_or_different_cell_never_commits(
        tmp_path, capsys, route):
    repo, source, exit_code = _matrix_close(
        tmp_path, "whole", _marker_body("Suite: green", *CELLS), route)
    assert exit_code == 0 and all(line in _commit_body(repo) for line in CELLS)
    assert _git_out(repo, "log", "-1", "--format=%s").strip() == MARKER_SUBJECT
    assert source.exists() is (route == "inline")

    different = [CELLS[0], CELLS[1], "Environment: container — python:3.14, arm64"]
    for name, lines in (("missing", CELLS[:2]), ("different", different)):
        repo, source, exit_code = _matrix_close(
            tmp_path, name, _marker_body("Suite: green", *lines), route)
        assert exit_code != 0
        assert _git_out(repo, "log", "--format=%s").count("implementation complete") == 0
        assert route == "inline" or source.exists()
    capsys.readouterr()


def test_marker_set_equality_ignores_order_duplicates_and_markup(tmp_path):
    shuffled = _marker_body(f"**`{CELLS[2]}`**", f"  _{CELLS[0]}_  ", CELLS[1], CELLS[0],
                            CELLS[2], "Suite: green")
    repo, _, exit_code = _matrix_close(tmp_path, "markup", shuffled)
    assert exit_code == 0


def _matrix_refusal(tmp_path, capsys, name, marker_lines, *, take_index=False, route="file",
                    stdout=None, stderr="", status=0, extra_lines=(), record=None):
    repo, store = _change_repo(tmp_path / name), _gate_store(tmp_path / name)
    if record is not None:
        record(store, repo)
    else:
        _record_matrix_run(store, repo, stdout=stdout, stderr=stderr, status=status)
    (repo / "staged.txt").write_text("staged\n")
    subprocess.run(["git", "-C", str(repo), "add", "staged.txt"], check=True)
    (repo / "candidate.txt").write_text("candidate\n")
    body = _marker_body("Suite: green", *marker_lines, *extra_lines)
    source = _body_file(tmp_path, body, name=f"{name}.txt")
    args = ["--body-file", str(source)] if route == "file" else ["--body", body.rstrip("\n")]
    before = _state(repo)
    index_bytes = _git_out(repo, "diff", "--cached")
    flags = ["--take-index"] if take_index else ["--staged", "staged.txt"]

    exit_code = _close(repo, store, args, "--add", "candidate.txt", *flags, allow_empty=False)
    lines = _refusal_lines(capsys)

    assert exit_code != 0 and lines[0] == REFUSAL_FIRST_LINE
    assert _state(repo)[:2] == before[:2] and _git_out(repo, "diff", "--cached") == index_bytes
    assert (repo / "candidate.txt").read_text() == "candidate\n"
    if route == "file":
        assert source.read_bytes() == body.encode()
    return lines, source


def printed(lines: list[str]) -> list[str]:
    return [f"  {line}" for line in lines]


def closing_lines(source: Path | None) -> list[str]:
    return [NOTHING_STAGED_MARKER,
            *([f"The body file '{source}' is left in place."] if source is not None else []),
            MATRIX_WAYS_OUT]


@pytest.mark.parametrize("take_index", [False, True])
def test_marker_refusal_names_every_cause_and_changes_nothing(tmp_path, capsys, take_index):
    lines, source = _matrix_refusal(tmp_path, capsys, "none", [], take_index=take_index)
    assert lines == [REFUSAL_FIRST_LINE, "The marker has no Environment: line. The gate run "
                     "printed these 3:", *printed(CELLS), *closing_lines(source)]

    lines, source = _matrix_refusal(tmp_path, capsys, "one", [CELLS[0], CELLS[2]],
                                    take_index=take_index)
    assert lines == [REFUSAL_FIRST_LINE, "These Environment: lines from the gate run are missing "
                     "from the marker:", *printed([CELLS[1]]), *closing_lines(source)]

    lines, source = _matrix_refusal(tmp_path, capsys, "several", [CELLS[1]], route="inline",
                                    take_index=take_index)
    assert lines == [REFUSAL_FIRST_LINE, "These Environment: lines from the gate run are missing "
                     "from the marker:", *printed([CELLS[0], CELLS[2]]), *closing_lines(None)]

    stray = "Environment: container — python:3.14, arm64"
    wrapped = f"**`{stray}`**"
    lines, source = _matrix_refusal(tmp_path, capsys, "extra", [*CELLS, wrapped, wrapped, stray],
                                    take_index=take_index)
    assert lines == [REFUSAL_FIRST_LINE, "These Environment: lines in the marker are not ones the "
                     "gate run printed:", *printed([wrapped, stray]), *closing_lines(source)]

    lines, source = _matrix_refusal(tmp_path, capsys, "both", [CELLS[0], stray],
                                    take_index=take_index)
    assert lines == [
        REFUSAL_FIRST_LINE, "These Environment: lines from the gate run are missing from the "
        "marker:", *printed(CELLS[1:]), "These Environment: lines in the marker are not ones the "
        "gate run printed:", *printed([stray]), *closing_lines(source)]


NOT_READY_RUN = ["Environment: container — python:3.12, arm64",
                 "Environment: not-ready — python:3.12, arm64 — the test command exited 127, "
                 "the status the shell gives a command it cannot find"]


def _record_not_ready_run(store, repo: Path) -> None:
    _record_matrix_run(store, repo, NOT_READY_RUN, status=1,
                       stdout="".join(f"{line}\n" for line in NOT_READY_RUN) + "suite out\n",
                       stderr="sh: 1: pytest: not found\n")


def test_a_marker_leaving_out_the_not_ready_line_is_refused(tmp_path, capsys):
    # CP-838: a single environment that was not ready printed two lines, and the builder refuses a
    # marker that carries the environment's own line but not the `not-ready` one.
    lines, source = _matrix_refusal(tmp_path, capsys, "left-out", NOT_READY_RUN[:1],
                                    record=_record_not_ready_run)
    assert lines == [REFUSAL_FIRST_LINE, "These Environment: lines from the gate run are missing "
                     "from the marker:", *printed(NOT_READY_RUN[1:]), *closing_lines(source)]

    repo, _, exit_code = _matrix_close(tmp_path, "both-lines",
                                       _marker_body("Suite: red", *NOT_READY_RUN),
                                       record=_record_not_ready_run)
    assert exit_code == 0 and all(line in _commit_body(repo) for line in NOT_READY_RUN)


def test_legacy_marker_refusal_text_is_unchanged(tmp_path, capsys):
    # A run of one container, or of none: the refusals read as they always did.
    repo, store = _change_repo(tmp_path / "one"), _gate_store(tmp_path / "one")
    _record_matrix_run(store, repo, [GATE_ENVIRONMENT])
    source = _body_file(tmp_path, _marker_body(OTHER_ENVIRONMENT), name="one.txt")
    assert _close(repo, store, ["--body-file", str(source)]) != 0
    assert _refusal_lines(capsys) == [
        REFUSAL_FIRST_LINE,
        "The marker's Environment: line differs from the one the gate run printed.",
        f"  marker:   {OTHER_ENVIRONMENT}", f"  gate run: {GATE_ENVIRONMENT}",
        NOTHING_STAGED_MARKER, f"The body file '{source}' is left in place.", MARKER_WAYS_OUT]

    bare, store = _change_repo(tmp_path / "bare"), _gate_store(tmp_path / "bare")
    _record_matrix_run(store, bare, [])
    assert _close(bare, store, ["--body", _marker_body("Suite: green")]) != 0
    assert _refusal_lines(capsys) == [
        REFUSAL_FIRST_LINE, "The marker has no Environment: line. The gate run printed:",
        f"  {NO_GATE_ENVIRONMENT}", NOTHING_STAGED_MARKER, MARKER_WAYS_OUT]


def test_failing_cases_are_checked_across_every_cells_streams(tmp_path, capsys):
    stdout = "".join(f"{line}\n" for line in CELLS) + "FAILED tests/a.py::one\n"
    stderr = "ERROR tests/b.py::two\n"
    ok = ["Failing: tests/a.py::one — task 1", "Failing: tests/b.py::two — task 2"]
    repo, _, exit_code = _matrix_close(
        tmp_path, "ok", _marker_body("Suite: red", *CELLS, *ok), stdout=stdout, stderr=stderr,
        status=1)
    assert exit_code == 0

    # Aggregate success rejects any Failing: line.
    lines, source = _matrix_refusal(tmp_path, capsys, "green", CELLS, extra_lines=ok[:1],
                                    stdout=stdout)
    at = lines.index("The gate run exited 0, so the marker must carry no Failing: line. "
                     "It carries:")
    assert lines[at + 1] == f"  {ok[0]}" and lines[-1] == MATRIX_WAYS_OUT

    # An absent id, a blank one, and a missing environment line are named together.
    bad = ["Failing: tests/c.py::three — task 3", "Failing:"]
    lines, source = _matrix_refusal(tmp_path, capsys, "absent", CELLS[:2], extra_lines=bad,
                                    stdout=stdout, stderr=stderr, status=1)
    assert lines == [
        REFUSAL_FIRST_LINE, "These Environment: lines from the gate run are missing from the "
        "marker:", f"  {CELLS[2]}",
        "These Failing: lines name a case that appears nowhere in the gate run's output:",
        f"  {bad[0]}", "    case id looked for: tests/c.py::three", f"  {bad[1]}",
        "    case id looked for: ", *closing_lines(source)]

    # A failing case alone on a multi-cell run still gets the plural way out.
    lines, source = _matrix_refusal(tmp_path, capsys, "case-only", CELLS, extra_lines=bad[:1],
                                    stdout=stdout, stderr=stderr, status=1)
    assert lines[-1] == MATRIX_WAYS_OUT and lines[1].startswith("These Failing: lines")


# ── a closing marker against a mixed run: containers and macOS guests (CP-801, design T13) ──────
# The run is a real completed one: the gate's own recording layer kept it, and the builder reads it
# back from that store. Only the host under the gate is a fake.

import dataclasses  # noqa: E402
import test_gate_suite as gate_tests  # noqa: E402

MIXED_CELLS = [*gate_tests.LINUX_LINES, *gate_tests.GUEST_LINES]


def _record_completed_mixed_run(store, repo: Path, *, results=None, key: str = CHANGE_KEY) -> None:
    """Run the mixed gate on the fake host with `store` as its run store, then keep what it stored
    for this change's checkout, as the gate does for a real one."""
    harness = gate_tests.mixed_harness(store=store, results=results)
    status = gate_tests.run_recorded(
        harness, inputs=gate_tests.mixed_raw(versions=gate_tests.MIXED_VERSIONS))
    stored = store.latest(gate_tests.WORKTREE, "key1")
    assert stored.environment_lines == tuple(MIXED_CELLS) and stored.status == status
    store.publish(dataclasses.replace(stored, key=key), [str(repo)])


@pytest.mark.parametrize("route", ["inline", "file"])
@pytest.mark.parametrize("failed", [False, True], ids=["passed", "completed-failed"])
def test_mixed_run_marker_with_every_declaration_commits(tmp_path, route, failed):
    # CP-801/T13: all three declarations, the one guest's among them, close the change by the
    # inline and the file route, whether the run passed or completed with a failed cell.
    results = {"guest-0": gate_suite.Completed(3, "guest-0 failed\n", "")} if failed else None
    repo, source, exit_code = _matrix_close(
        tmp_path, "mixed", _marker_body("Suite: green", *MIXED_CELLS), route,
        record=lambda store, repo: _record_completed_mixed_run(store, repo, results=results))

    assert exit_code == 0
    assert all(line in _commit_body(repo) for line in MIXED_CELLS)
    assert _git_out(repo, "log", "-1", "--format=%s").strip() == MARKER_SUBJECT
    assert source.exists() is (route == "inline")


@pytest.mark.parametrize("route", ["inline", "file"])
def test_missing_guest_version_declaration_refuses_without_mutation(tmp_path, capsys, route):
    # The guest's line is omitted and the container lines stay: the refusal names that line alone,
    # and repeating a retained line does not stand in for it.
    lost = gate_tests.GUEST_LINES[0]
    for name, lines in (("omitted", MIXED_CELLS[:2]),
                        ("repeated", [*MIXED_CELLS[:2], MIXED_CELLS[1], MIXED_CELLS[1]])):
        lines_out, source = _matrix_refusal(
            tmp_path, capsys, name, lines, route=route, record=_record_completed_mixed_run)
        assert lines_out == [
            REFUSAL_FIRST_LINE, "These Environment: lines from the gate run are missing from "
            "the marker:", *printed([lost]),
            *closing_lines(source if route == "file" else None)]


def test_a_matrix_marker_block_followed_by_a_wrapped_environment_mention_commits(tmp_path):
    # CP-854 on the several-container path, the shape the real report had: the run's lines as one
    # block, then prose whose wrapped line opens with the quoted prefix. The mention is not read,
    # so it is not a line "the gate run did not print".
    body = _marker_body("Suite: green", *CELLS, "", "The marker's head is read by the",
                        MENTION_OF_ENVIRONMENT)
    for route in ("inline", "file"):
        _, _, exit_code = _matrix_close(tmp_path, f"mention-{route}", body, route)
        assert exit_code == 0, route


def test_mixed_marker_preserves_set_comparison(tmp_path, capsys):
    # Order, repetition and the markup the builder already strips keep their meaning; a line the
    # run did not print still refuses, and is named as one.
    first, second, third = MIXED_CELLS
    shuffled = _marker_body(f"**`{third}`**", f"  _{first}_  ", second, first, second, third,
                            "Suite: green")
    _, _, exit_code = _matrix_close(tmp_path, "markup", shuffled,
                                    record=_record_completed_mixed_run)
    assert exit_code == 0

    stray = f"Environment: macos-guest {gate_tests.DASH} {gate_tests.GUEST_NAME}, toolchain 3.12"
    lines, source = _matrix_refusal(tmp_path, capsys, "extra", [*MIXED_CELLS, stray],
                                    record=_record_completed_mixed_run)
    assert lines == [REFUSAL_FIRST_LINE, "These Environment: lines in the marker are not ones the "
                     "gate run printed:", *printed([stray]), *closing_lines(source)]


# ── check-directional — a directional line judged without a commit, so a caller that commits
#    late (the seal, after its product merge) can refuse the line before anything lands. ──────

def test_check_directional_accepts_a_line_that_names_its_station(tmp_path, capsys):
    shukuba = tmp_path / "system" / "projects" / "tools" / "journey" / "shukuba"
    shukuba.mkdir(parents=True)
    (shukuba / "2026-10-24_x.md").write_text("# x\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path), "check-directional",
        "--directional", "Shukuba: 2026-10-24_x — progress: sealed",
    ])

    assert exit_code == 0
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("directional", [
    "Shukuba: progress: sealed 2026-10-24_x",
    "Shukuba: 2026-10-24_not-a-station — progress: sealed",
])
def test_check_directional_refuses_what_commit_refuses(tmp_path, capsys, directional):
    _init_repo(tmp_path)
    (tmp_path / "system" / "projects" / "tools").mkdir(parents=True)
    (tmp_path / "work.txt").write_text("work\n")

    exit_code = commit_builder.main([
        "--repo", str(tmp_path), "check-directional", "--directional", directional,
    ])
    checked = capsys.readouterr().err
    commit_exit = commit_builder.main([
        "--repo", str(tmp_path), "commit", "--subject", "pm: x", "--actor", "pm",
        "--add", "work.txt", "--directional", directional, "--surface", "Claude Code",
    ])

    assert exit_code == 1
    assert checked.startswith(_REFUSAL_PREFIX)
    assert commit_exit == 1
    assert capsys.readouterr().err == checked


def test_check_directional_changes_nothing(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "work.txt").write_text("work\n")
    status = ["git", "-C", str(tmp_path), "status", "--porcelain"]
    before = subprocess.run(status, capture_output=True, text=True, check=True).stdout

    commit_builder.main([
        "--repo", str(tmp_path), "check-directional",
        "--directional", "Shukuba: progress: x",
    ])

    assert subprocess.run(status, capture_output=True, text=True, check=True).stdout == before
