"""Tests for `brief_anchor_guard.py` — the `PreToolUse` `Agent` guard.

Runs the real entry point — JSON on stdin, JSON or silence on stdout — exactly as Claude Code does
with it, following `test_written_forward_guard.py`'s shape.

Each test fabricates a small repo carrying the files a brief cites and a `.claude/agents/<name>.md`
for the target agent, because the guard resolves both against the project directory it is told about
(`CLAUDE_PROJECT_DIR`, the variable `.claude/settings.json` already passes to every hook).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

_GUARD = Path(__file__).resolve().parent / "brief_anchor_guard.py"


def _project(tmp_path: Path) -> Path:
    """A directory shaped like an instance: a cited doc, and one agent with a tool grant."""
    root = tmp_path / "instance"
    (root / "docs").mkdir(parents=True)
    (root / ".claude" / "agents").mkdir(parents=True)
    (root / "docs" / "brand.md").write_text(
        "\n".join(
            [
                "# Brand",                                    # 1
                "",                                           # 2
                "intro line",                                 # 3
                "",                                           # 4
                "the dial is delegated to the adopter",       # 5
                "and nothing above it may override that",     # 6
                "",                                           # 7
                "a closing line",                             # 8
            ]
        )
        + "\n"
    )
    (root / ".claude" / "agents" / "delegate.md").write_text(
        "---\nname: delegate\ntools: Read, Grep, Bash, mcp__perplexity, mcp__github\n---\n\nbody\n"
    )
    (root / ".claude" / "agents" / "everything.md").write_text(
        "---\nname: everything\ntools: *\n---\n\nbody\n"
    )
    return root


def _run(payload, project: Path) -> subprocess.CompletedProcess:
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project))
    return subprocess.run(
        [sys.executable, str(_GUARD)],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
    )


def _spawn(prompt: str, subagent_type: str = "delegate", tier: bool = True) -> dict:
    """A spawn of the shape the harness sends. `tier` defaults on because the fixture agent pins no
    model, and under that rule every sound brief for it names the tier — a fixture that omitted it
    would be testing citations against a brief that is invalid for another reason."""
    if tier:
        prompt += "\n\nRun on Opus, resolved for the judgement this needs."
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Agent",
        "tool_input": {
            "description": "a job",
            "prompt": prompt,
            "subagent_type": subagent_type,
        },
    }


def _denial(result: subprocess.CompletedProcess) -> str:
    assert result.stdout.strip(), "expected a deny payload, got silence"
    out = json.loads(result.stdout)
    hook = out["hookSpecificOutput"]
    assert hook["permissionDecision"] == "deny"
    return hook["permissionDecisionReason"]


def _allowed(result: subprocess.CompletedProcess) -> None:
    assert result.returncode == 0
    assert result.stdout.strip() == "", f"expected silence, got {result.stdout!r}"


# ── the anchor is what makes a citation checkable ───────────────────────────

def test_anchor_at_the_cited_lines_passes(tmp_path):
    project = _project(tmp_path)
    prompt = 'Read docs/brand.md:L5-L6 "the dial is delegated to the adopter" before you start.'
    _allowed(_run(_spawn(prompt), project))


def test_anchor_at_the_wrong_lines_denies_and_names_the_real_range(tmp_path):
    project = _project(tmp_path)
    prompt = 'Read docs/brand.md:L3-L4 "the dial is delegated to the adopter" before you start.'
    reason = _denial(_run(_spawn(prompt), project))
    assert "docs/brand.md:3-4" in reason
    assert "5" in reason, "the denial must name where the quoted text actually is"


def test_a_citation_with_no_anchor_denies(tmp_path):
    project = _project(tmp_path)
    prompt = "Read docs/brand.md:L5-L6 before you start — it delegates the dial."
    reason = _denial(_run(_spawn(prompt), project))
    assert "docs/brand.md:5-6" in reason


def test_an_unresolvable_path_is_not_asserted_on(tmp_path):
    """Measured over 584 real briefs: almost every unresolvable path is one cited relative to a
    base this guard does not have (`product-srs/SKILL.md` lives under `skills/cto/.claude/skills/`), not a
    wrong path. Unprovable, so not denied — and a dead path announces itself on the first Read."""
    project = _project(tmp_path)
    prompt = 'Read docs/absent.md:L1-L2 "some sentence that is quoted" first.'
    _allowed(_run(_spawn(prompt), project))


def test_a_path_cited_from_a_deeper_base_still_resolves(tmp_path):
    project = _project(tmp_path)
    good = 'Read brand.md:L5-L6 "the dial is delegated to the adopter" first.'
    _allowed(_run(_spawn(good), project))
    bad = 'Read brand.md:L3-L4 "the dial is delegated to the adopter" first.'
    assert "brand.md:3-4" in _denial(_run(_spawn(bad), project))


def test_a_range_past_eof_denies(tmp_path):
    project = _project(tmp_path)
    prompt = 'Read docs/brand.md:L200-L400 "the dial is delegated to the adopter" first.'
    reason = _denial(_run(_spawn(prompt), project))
    assert "docs/brand.md:200-400" in reason


def test_a_single_line_citation_is_checked_too(tmp_path):
    project = _project(tmp_path)
    good = 'See docs/brand.md:L5 "the dial is delegated to the adopter".'
    _allowed(_run(_spawn(good), project))
    bad = 'See docs/brand.md:L8 "the dial is delegated to the adopter".'
    assert "docs/brand.md:8" in _denial(_run(_spawn(bad), project))


# ── a brief may not name a tool its agent does not have ─────────────────────

def test_an_ungranted_tool_denies(tmp_path):
    project = _project(tmp_path)
    prompt = "Use mcp__reddit__find_threads to gather the discussion."
    reason = _denial(_run(_spawn(prompt), project))
    assert "mcp__reddit" in reason


def test_a_granted_tool_passes(tmp_path):
    project = _project(tmp_path)
    prompt = "Use mcp__perplexity__perplexity_research to gather the discussion."
    _allowed(_run(_spawn(prompt), project))


def test_a_wildcard_grant_allows_anything(tmp_path):
    project = _project(tmp_path)
    prompt = "Use mcp__reddit__find_threads to gather the discussion."
    _allowed(_run(_spawn(prompt, subagent_type="everything"), project))


def test_an_unknown_agent_skips_the_tool_check(tmp_path):
    project = _project(tmp_path)
    prompt = "Use mcp__reddit__find_threads to gather the discussion."
    _allowed(_run(_spawn(prompt, subagent_type="Explore"), project))


# ── assert only what can be proven ──────────────────────────────────────────

def test_a_brief_with_no_citations_passes(tmp_path):
    project = _project(tmp_path)
    _allowed(_run(_spawn("Go and look into the merge question, then report back."), project))


def test_a_bare_ambiguous_filename_is_not_asserted_on(tmp_path):
    project = _project(tmp_path)
    (project / "docs" / "sub").mkdir()
    (project / "docs" / "sub" / "brand.md").write_text("a different brand file\n")
    prompt = 'Read brand.md:L5-L6 "the dial is delegated to the adopter" first.'
    _allowed(_run(_spawn(prompt), project))


def test_a_bare_unique_filename_is_resolved_and_checked(tmp_path):
    project = _project(tmp_path)
    bad = 'Read brand.md:L3-L4 "the dial is delegated to the adopter" first.'
    assert "brand.md:3-4" in _denial(_run(_spawn(bad), project))


def test_prose_that_looks_like_a_citation_is_ignored(tmp_path):
    project = _project(tmp_path)
    _allowed(_run(_spawn("Follow Step 4:12-20 of the skill, then stop."), project))


# ── fail open, never break a session ────────────────────────────────────────

def test_a_non_agent_tool_is_ignored(tmp_path):
    project = _project(tmp_path)
    payload = {"tool_name": "Bash", "tool_input": {"command": "ls"}}
    _allowed(_run(payload, project))


def test_unparseable_stdin_exits_clean(tmp_path):
    project = _project(tmp_path)
    _allowed(_run("not json at all", project))


def test_a_missing_prompt_key_is_read_as_absent(tmp_path):
    project = _project(tmp_path)
    payload = {"tool_name": "Agent", "tool_input": {"description": "a job"}}
    _allowed(_run(payload, project))


# ── the fleet's own quoting habits, measured off 584 real briefs ────────────

def test_an_elided_quote_matches_by_its_fragments(tmp_path):
    """This fleet quotes with the middle cut out — `"**is** … **created**"`. An elided quote can
    never match as one substring, so the fragments are required in order instead."""
    project = _project(tmp_path)
    prompt = 'Read docs/brand.md:L5-L6 "the dial is delegated … may override that" first.'
    _allowed(_run(_spawn(prompt), project))
    dots = 'Read docs/brand.md:L5-L6 "the dial is delegated ... may override that" first.'
    _allowed(_run(_spawn(dots), project))


def test_fragments_out_of_order_still_deny(tmp_path):
    project = _project(tmp_path)
    prompt = 'Read docs/brand.md:L5-L6 "may override that … the dial is delegated" first.'
    assert "docs/brand.md:5-6" in _denial(_run(_spawn(prompt), project))


def test_an_unrelated_quote_before_the_real_anchor_does_not_deny(tmp_path):
    """A brief may quote something else on its way to the anchor — a placeholder, a flag, the
    caller's own words. Denying on the first quote would block a citation that is sound."""
    project = _project(tmp_path)
    prompt = (
        'See docs/brand.md:L5-L6 — the caller said "<FIXED prompt> goes here", and the file says '
        '"the dial is delegated to the adopter".'
    )
    _allowed(_run(_spawn(prompt), project))


def test_markdown_emphasis_does_not_break_a_sound_quote(tmp_path):
    """Found by running the guard against a real citation of `commit_format.md`, which reads
    `the instance has **no Shukuba of its own**`. A brief quotes the sentence, not the markup."""
    project = _project(tmp_path)
    (project / "docs" / "emphasis.md").write_text(
        "# T\n\nthe instance has **no Shukuba of its own** — it steers by its `michi`\n"
    )
    prompt = 'Read docs/emphasis.md:L3 "the instance has no Shukuba of its own" first.'
    _allowed(_run(_spawn(prompt), project))


# ── the tier a no-pin agent runs on must be in its brief ────────────────────
# Measured over 584 real briefs: `delegate` is the only agent with no pinned model, it was spawned
# 58 times, and **all 58 passed `model` in the call** — while only 21 named the tier in the prompt.
# So the choice is not hidden, it is simply never told to the agent, which is what both reports mean
# by "The brief named no tier" (`delegate_contract.md:41`: "If your task prompt did not name your
# tier, say so in your report"). A pinned agent is out of scope: its tier is a fact of its own file.

def _pinned_agent(project: Path, name: str = "developer", model: str = "sonnet") -> None:
    (project / ".claude" / "agents" / f"{name}.md").write_text(
        f"---\nname: {name}\nmodel: {model}\ntools: Read, Bash\n---\n\nbody\n"
    )


def test_a_no_pin_agent_told_its_tier_passes(tmp_path):
    project = _project(tmp_path)
    payload = _spawn("Run on Opus 5 (1M context), picked for the judgement. Then do the job.")
    payload["tool_input"]["model"] = "opus"
    _allowed(_run(payload, project))


def test_a_no_pin_agent_not_told_its_tier_denies(tmp_path):
    project = _project(tmp_path)
    payload = _spawn("Do the job and report back.", tier=False)
    payload["tool_input"]["model"] = "opus"
    reason = _denial(_run(payload, project))
    assert "opus" in reason.lower()
    assert "delegate" in reason


def test_a_hidden_choice_denies_too(tmp_path):
    """No pin, no `model` in the call, no tier in the brief. `delegate_contract.md:39-41`: "A
    spawner that does not pass a model has not chosen one; it has hidden the choice.\""""
    project = _project(tmp_path)
    reason = _denial(_run(_spawn("Do the job and report back.", tier=False), project))
    assert "delegate" in reason


def test_a_pinned_agent_is_out_of_scope(tmp_path):
    project = _project(tmp_path)
    _pinned_agent(project)
    payload = _spawn("Do the job and report back.", subagent_type="developer", tier=False)
    _allowed(_run(payload, project))


def _agent_without_a_model(project: Path, name: str) -> None:
    (project / ".claude" / "agents" / f"{name}.md").write_text(
        f"---\nname: {name}\ntools: Read, Bash\n---\n\nbody\n"
    )


def test_a_non_delegate_spawn_naming_no_tier_is_not_denied(tmp_path):
    """No agent file carries a `model:` line any more (a run's intelligence is its skill's), so
    "no pinned model" no longer marks an agent as `delegate`. The per-run tier is that slot's by
    design; every other agent runs on what its spawner or its skill's file gives it."""
    project = _project(tmp_path)
    _agent_without_a_model(project, "pm")
    payload = _spawn("Do the job and report back.", subagent_type="pm", tier=False)
    _allowed(_run(payload, project))
    payload["tool_input"]["model"] = "opus"
    _allowed(_run(payload, project))


def test_a_delegate_spawn_naming_no_tier_is_still_denied(tmp_path):
    project = _project(tmp_path)

    with_model = _spawn("Do the job and report back.", tier=False)
    with_model["tool_input"]["model"] = "opus"
    reason = _denial(_run(with_model, project))
    assert "this run is spawned on `opus`" in reason and "`delegate` pins no model" in reason

    without_model = _spawn("Do the job and report back.", tier=False)
    reason = _denial(_run(without_model, project))
    assert "no tier named, and none passed" in reason and "`delegate`" in reason


def test_an_unknown_agent_is_out_of_scope_for_the_tier_check(tmp_path):
    project = _project(tmp_path)
    _allowed(_run(_spawn("Do the job.", subagent_type="Explore", tier=False), project))


# ── an agent is found in its group ──────────────────────────────────────────
#
# The agents live at `skills/<group>/.claude/agents/<name>.md`. The guard reads them from the
# project, then from the host the hook file sits in. Each test copies the guard into a throwaway
# host, so what the real repo holds never answers for the fixture.

def _group_agent(root: Path, name: str, tools: str = "Read, Grep") -> None:
    path = root / "skills" / name / ".claude" / "agents" / f"{name}.md"
    path.parent.mkdir(parents=True)
    path.write_text(f"---\nname: {name}\ntools: {tools}\n---\n\nbody\n")


def _hook_host(tmp_path: Path) -> Path:
    """An empty host holding only a copy of the guard, so the hook host is this directory."""
    host = tmp_path / "host"
    hooks = host / ".claude" / "hooks"
    hooks.mkdir(parents=True)
    (hooks / _GUARD.name).write_text(_GUARD.read_text())
    return host


def _run_in_host(payload, project: Path, host: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project))
    return subprocess.run(
        [sys.executable, str(host / ".claude" / "hooks" / _GUARD.name)],
        input=json.dumps(payload), capture_output=True, text=True, env=env,
    )


def _bare_project(tmp_path: Path) -> Path:
    project = tmp_path / "instance"
    project.mkdir()
    return project


def test_grouped_delegate_brief_without_tier_is_denied(tmp_path):
    host = _hook_host(tmp_path)
    project = _bare_project(tmp_path)
    _group_agent(project, "delegate")
    payload = _spawn("Do the job and report back.", tier=False)
    payload["tool_input"]["model"] = "sonnet"

    reason = _denial(_run_in_host(payload, project, host))

    assert "no tier named" in reason and "`delegate`" in reason


def test_hook_host_group_answers_when_project_holds_none(tmp_path):
    """A satellite holds no `skills/`, and its `settings.json` runs the host's hook by path."""
    host = _hook_host(tmp_path)
    _group_agent(host, "delegate")
    satellite = _bare_project(tmp_path)
    payload = _spawn("Do the job and report back.", tier=False)
    payload["tool_input"]["model"] = "sonnet"

    result = _run_in_host(payload, satellite, host)

    assert "no tier named" in _denial(result)


def test_tools_grant_check_applies_to_grouped_agent(tmp_path):
    host = _hook_host(tmp_path)
    project = _bare_project(tmp_path)
    _group_agent(project, "delegate", tools="Read, Grep")
    payload = _spawn("Use mcp__reddit__find_threads to gather the discussion.")

    reason = _denial(_run_in_host(payload, project, host))

    assert "mcp__reddit" in reason and "Read, Grep" in reason


def test_flat_agent_still_resolves_first(tmp_path):
    host = _hook_host(tmp_path)
    project = _bare_project(tmp_path)
    (project / ".claude" / "agents").mkdir(parents=True)
    (project / ".claude" / "agents" / "delegate.md").write_text(
        "---\nname: delegate\ntools: Read, mcp__reddit\n---\n\nbody\n"
    )
    _group_agent(project, "delegate", tools="Read")
    payload = _spawn("Use mcp__reddit__find_threads to gather the discussion.")

    _allowed(_run_in_host(payload, project, host))


def test_unknown_agent_admitted_without_output(tmp_path):
    host = _hook_host(tmp_path)
    project = _bare_project(tmp_path)
    _group_agent(project, "delegate")
    _group_agent(host, "qa")
    payload = _spawn("Use mcp__reddit__find_threads to gather the discussion.", "ghost", tier=False)

    _allowed(_run_in_host(payload, project, host))


def test_a_name_two_groups_hold_reads_the_file_pin_answers(tmp_path):
    """Two groups hold `delegate`: the guard reads the file `pin.py` loads — the last group in
    name order, compared group by group, so `a` comes before `a-b` — never the order of the joined
    path strings, where `a-b/…` sorts before `a/…`. Only `a-b`'s copy lacks the grant used."""
    host = _hook_host(tmp_path)
    project = _bare_project(tmp_path)
    for group, tools in (("a", "Read, mcp__reddit"), ("a-b", "Read")):
        path = project / "skills" / group / ".claude" / "agents" / "delegate.md"
        path.parent.mkdir(parents=True)
        path.write_text(f"---\nname: delegate\ntools: {tools}\n---\n\nbody\n")
    payload = _spawn("Use mcp__reddit__find_threads to gather the discussion.")

    reason = _denial(_run_in_host(payload, project, host))

    assert "mcp__reddit" in reason and "Read" in reason


import pytest as _pytest  # noqa: E402


@_pytest.mark.parametrize(
    "phrasing,names_a_tier",
    [
        ("Run on Opus 5 (1M context) for this.", True),
        ("run on fable, it is cheap", True),
        ("The tier is claude-opus-5[1m].", True),
        ("Use Sonnet 5 — the work is mechanical.", True),
        ("Query mcp__claude-design for the project.", False),   # an MCP server, not a model
        ("Write to /private/tmp/claude-501/scratch.", False),   # a path, not a model
        ("Just go and do the job.", False),
    ],
)
def test_the_tier_vocabulary_is_the_one_the_fleet_writes(tmp_path, phrasing, names_a_tier):
    """`claude-design` and `claude-501` both appear in real briefs and are not models. A bare
    `claude-*` pattern would read them as a named tier and wave the brief through."""
    project = _project(tmp_path)
    payload = _spawn(phrasing, tier=False)
    payload["tool_input"]["model"] = "opus"
    result = _run(payload, project)
    if names_a_tier:
        _allowed(result)
    else:
        assert "delegate" in _denial(result)
